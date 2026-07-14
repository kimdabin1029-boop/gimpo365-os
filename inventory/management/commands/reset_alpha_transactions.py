"""알파 운영기록 초기화 — 정식 운영 전환 전용 (P3-08A-01).

목적:
- gimpo365os_prod(리허설 복제본) 알파테스트 종료 후 정식 운영 시작 직전에,
  기준정보는 그대로 두고 알파테스트 중 쌓인 Inventory 운영기록만 초기화한다.
- 기준정보(부서/사용자/공급업체/품목/관리품목/체크리스트 항목·배정/공지사항)는 보존한다.

기본 삭제(Inventory 운영기록):
    StockTransaction → CartItem → OrderItem → Order  (자식 → 부모, PROTECT 안전 순서)
선택 삭제:
    --include-checklist-records  ChecklistRecord (ChecklistItem/DepartmentChecklistItem 유지)
    --clear-sessions             django_session (User 유지)

현재고 = APPROVED StockTransaction.quantity_delta 합계(계산형, 저장/캐시 필드 없음).
따라서 StockTransaction 전체 삭제만으로 모든 관리품목 현재고가 0이 된다(별도 초기화 불필요).

안전장치(정식 운영 후보 DB 전용). 실제 삭제는 아래 세 조건을 모두 만족할 때만:
- (1) --yes 가 있고 --dry-run 이 아니다.
- (2) --confirm-db 값이 현재 연결 DB명(connection.settings_dict["NAME"])과 정확히 일치한다.
- (3) settings.ALLOW_ALPHA_TRANSACTION_RESET is True (환경변수 ALLOW_ALPHA_TRANSACTION_RESET).
셋 중 하나라도 불만족이면 데이터 변경 없이 CommandError 로 차단한다(transaction 진입 전 검사).
정식 운영에서도 DB명은 계속 gimpo365os_prod 이므로, --confirm-db 만으로는 실수 재실행을 막지 못한다.
(3) 환경변수 가드는 알파 종료 시에만 일시 활성화하고 실행 후 즉시 false 로 되돌린다.
전체 삭제는 하나의 transaction.atomic 안에서 수행하며, 중간 오류 시 전체 rollback 한다.

주의:
- 이 명령은 배포 전 1회 유지보수 예외로 운영기록을 물리 삭제한다(취소 처리가 아님).
  반드시 운영 후보 DB 전체 백업 완료 후, 다빈 승인하에 실행한다.
- 기존 보호 대상 명령(reset_operational_data / check_inventory_master_data)은 수정·우회하지 않는다.
- 이 명령으로 공지사항(Notice)은 삭제하지 않는다(사람이 선별 삭제).
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from checklist.models import (
    ChecklistItem,
    ChecklistRecord,
    DepartmentChecklistItem,
)
from core.models import Department
from inventory.models import (
    CartItem,
    Item,
    ManagedItem,
    Order,
    OrderItem,
    StockTransaction,
    Supplier,
    TransactionStatus,
)
from notice.models import Notice

User = get_user_model()


class Command(BaseCommand):
    help = (
        "알파 운영기록(Inventory 거래·주문)만 초기화하고 기준정보는 보존한다. "
        "기본은 dry-run. 실제 삭제는 --yes 와 --confirm-db <연결 DB명 일치> 동시 필요. "
        "선택: --include-checklist-records, --clear-sessions."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="실제 삭제 수행. --confirm-db 와 함께여야 한다. (미지정 시 dry-run)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="삭제하지 않고 예정 건수만 출력. (기본 동작)",
        )
        parser.add_argument(
            "--confirm-db",
            dest="confirm_db",
            metavar="DBNAME",
            default=None,
            help="현재 연결된 DB명을 정확히 입력. 일치할 때만 실제 삭제 허용.",
        )
        parser.add_argument(
            "--include-checklist-records",
            action="store_true",
            help="ChecklistRecord(완료 기록)도 삭제. 항목/배정은 유지.",
        )
        parser.add_argument(
            "--clear-sessions",
            action="store_true",
            help="django_session(로그인 세션)도 삭제. 사용자 계정은 유지.",
        )

    # ------------------------------------------------------------------
    # 건수 집계 (기준정보 보존 대상 / 운영기록 삭제 대상 / 선택 삭제 대상)
    # ------------------------------------------------------------------
    def _keep_counts(self):
        # 명령 전후 건수가 동일해야 하는 절대 보존 대상.
        return {
            "Department": Department.objects.count(),
            "User": User.objects.count(),
            "Supplier": Supplier.objects.count(),
            "Item": Item.objects.count(),
            "ManagedItem": ManagedItem.objects.count(),
            "ChecklistItem": ChecklistItem.objects.count(),
            "DepartmentChecklistItem": DepartmentChecklistItem.objects.count(),
            "Notice": Notice.objects.count(),
        }

    def _delete_counts(self):
        # 기본 삭제(Inventory 운영기록). 표시·삭제 모두 자식 → 부모 순서.
        return {
            "StockTransaction": StockTransaction.objects.count(),
            "CartItem": CartItem.objects.count(),
            "OrderItem": OrderItem.objects.count(),
            "Order": Order.objects.count(),
        }

    def _optional_counts(self, options):
        return {
            "ChecklistRecord": (
                ChecklistRecord.objects.count(),
                options["include_checklist_records"],
            ),
            "Session": (
                Session.objects.count(),
                options["clear_sessions"],
            ),
        }

    def _current_db_name(self):
        return connection.settings_dict["NAME"]

    def _max_current_stock(self):
        """남아있는 APPROVED 거래 기준 최대 현재고(0이어야 정상)."""
        from django.db.models import Sum

        rows = (
            StockTransaction.objects.filter(status=TransactionStatus.APPROVED)
            .values("managed_item_id")
            .annotate(s=Sum("quantity_delta"))
        )
        return max((r["s"] or 0 for r in rows), default=0)

    # ------------------------------------------------------------------
    def handle(self, *args, **options):
        do_delete = options["yes"] and not options["dry_run"]
        db_name = self._current_db_name()

        keep = self._keep_counts()
        delete = self._delete_counts()
        optional = self._optional_counts(options)

        if not do_delete:
            self._print_dry_run(db_name, keep, delete, optional)
            return

        # 실제 삭제: 파괴적 작업 전에 모든 안전장치를 통과해야 한다(transaction 진입 전 검사).
        # (1) --confirm-db 가 현재 연결 DB명과 정확히 일치해야 한다.
        confirm_db = options["confirm_db"]
        if not confirm_db or confirm_db != db_name:
            raise CommandError(
                "실제 삭제가 거부되었습니다. "
                f"현재 연결 DB='{db_name}' 와 --confirm-db 값이 정확히 일치해야 합니다. "
                f"입력값: {confirm_db!r}. 데이터는 변경되지 않았습니다."
            )

        # (2) 운영 재실행 방지 가드: 설정이 명시적으로 True 여야 한다.
        #     정식 운영에서도 DB명은 계속 gimpo365os_prod 이므로, --confirm-db 만으로는
        #     실수 재실행을 막지 못한다. 알파 종료 시에만 ALLOW_ALPHA_TRANSACTION_RESET=true 로
        #     일시 활성화하고 실행 후 즉시 false 로 되돌린다. (DB명과 별개의 독립 가드)
        if not settings.ALLOW_ALPHA_TRANSACTION_RESET:
            raise CommandError(
                "알파 운영기록 초기화가 비활성화되어 있습니다. "
                "실행 전 ALLOW_ALPHA_TRANSACTION_RESET=true 를 명시적으로 설정해야 합니다. "
                "(정식 운영 중에는 활성화하지 않습니다.) 데이터는 변경되지 않았습니다."
            )

        deleted = self._execute_delete(options)
        self._print_complete(db_name, keep, deleted)

    # ------------------------------------------------------------------
    def _execute_delete(self, options):
        """전체를 하나의 원자적 작업으로 삭제한다. 중간 오류 시 전체 rollback."""
        deleted = {}
        stage = None
        try:
            with transaction.atomic():
                # 자식 → 부모 순서 (StockTransaction.source_order_item 이 OrderItem 을
                # PROTECT 로 참조하므로 StockTransaction 을 반드시 먼저 삭제한다).
                stage = "StockTransaction"
                deleted["StockTransaction"] = StockTransaction.objects.all().delete()[0]
                stage = "CartItem"
                deleted["CartItem"] = CartItem.objects.all().delete()[0]
                stage = "OrderItem"
                deleted["OrderItem"] = OrderItem.objects.all().delete()[0]
                stage = "Order"
                deleted["Order"] = Order.objects.all().delete()[0]
                if options["include_checklist_records"]:
                    stage = "ChecklistRecord"
                    deleted["ChecklistRecord"] = ChecklistRecord.objects.all().delete()[0]
                if options["clear_sessions"]:
                    stage = "Session"
                    deleted["Session"] = Session.objects.all().delete()[0]
        except Exception as exc:  # noqa: BLE001 — 실패 단계를 알려 재시도/조사를 돕는다
            raise CommandError(
                f"삭제 중 오류가 발생했습니다 (실패 단계: {stage}, 모델: {stage}). "
                f"transaction.atomic 로 전체 rollback 되어 데이터는 삭제되지 않았습니다. "
                f"원인: {exc}"
            ) from exc
        return deleted

    # ------------------------------------------------------------------
    # 출력
    # ------------------------------------------------------------------
    def _print_dry_run(self, db_name, keep, delete, optional):
        self.stdout.write("[reset_alpha_transactions] DRY RUN")
        self.stdout.write("")
        self.stdout.write("현재 데이터베이스:")
        self.stdout.write(f"- {db_name}")
        self.stdout.write("")
        allow = settings.ALLOW_ALPHA_TRANSACTION_RESET
        self.stdout.write("실제 실행 허용 설정:")
        self.stdout.write(
            f"- ALLOW_ALPHA_TRANSACTION_RESET: {'활성' if allow else '비활성'}"
        )
        self.stdout.write("")
        self.stdout.write("보존 예정:")
        for name, n in keep.items():
            self.stdout.write(f"- {name}: {n}")
        self.stdout.write("")
        self.stdout.write("삭제 예정:")
        for name, n in delete.items():
            self.stdout.write(f"- {name}: {n}")
        self.stdout.write("")
        self.stdout.write("선택 대상:")
        for name, (n, selected) in optional.items():
            mark = "선택됨" if selected else "미선택"
            self.stdout.write(f"- {name}: {n} ({mark})")
        self.stdout.write("")
        self.stdout.write("예상 결과:")
        self.stdout.write(f"- 관리품목 수: {keep['ManagedItem']} 유지")
        self.stdout.write("- 예상 현재고: 전부 0")
        self.stdout.write("- DB 변경: 없음")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "[dry-run] 실제 삭제를 수행하지 않았습니다. 실제 실행(환경변수 활성화 필요):\n"
                "  1) ALLOW_ALPHA_TRANSACTION_RESET=true 설정 후 새 프로세스로\n"
                f"  2) python manage.py reset_alpha_transactions --yes --confirm-db {db_name}\n"
                "  실행 후 ALLOW_ALPHA_TRANSACTION_RESET=false 로 되돌립니다."
            )
        )

    def _print_complete(self, db_name, keep_before, deleted):
        # 삭제 후 실제 값 재검증 (보존 건수 동일 / 거래 0 / 현재고 0).
        keep_after = self._keep_counts()
        tx_remaining = StockTransaction.objects.count()
        max_stock = self._max_current_stock()

        self.stdout.write("[reset_alpha_transactions] COMPLETE")
        self.stdout.write("")
        self.stdout.write(f"현재 데이터베이스: {db_name}")
        self.stdout.write("")
        self.stdout.write("삭제:")
        for name, n in deleted.items():
            self.stdout.write(f"- {name}: {n}")
        self.stdout.write("")
        self.stdout.write("보존:")
        for name, n in keep_after.items():
            self.stdout.write(f"- {name}: {n}")
        self.stdout.write("")
        self.stdout.write("검증:")
        self.stdout.write(f"- 거래기록(StockTransaction): {tx_remaining}")
        self.stdout.write(f"- 최대 현재고: {max_stock}")
        keep_ok = keep_before == keep_after
        self.stdout.write(
            f"- 기준정보 건수 일치: {'예' if keep_ok else '아니오'}"
        )
        if tx_remaining == 0 and max_stock == 0 and keep_ok:
            self.stdout.write(self.style.SUCCESS("초기화 완료. 관리품목 현재고 전부 0."))
        else:
            # 정상 경로에서는 도달하지 않는다. 방어적 안내.
            self.stdout.write(
                self.style.ERROR(
                    "경고: 초기화 후 상태가 기대와 다릅니다. 백업으로 복구 여부를 검토하세요."
                )
            )
        self.stdout.write(
            self.style.WARNING(
                "정식 운영 시작 전 각 관리품목별 실물 실사 → 최초재고 입력/승인을 진행하세요."
            )
        )
