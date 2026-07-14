"""reset_alpha_transactions 명령 테스트 (P3-08A-01).

테스트 DB 에서만 수행한다(실제 prod/rehearsal 미접근).
검증: dry-run 무변경 / --confirm-db 안전장치 / 기준정보 보존 / Inventory 운영기록 삭제 /
현재고 0 / ChecklistRecord·Session 옵션 / 원자성(rollback) / 멱등성.
"""

from decimal import Decimal
from io import StringIO
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import override_settings

from accounts.models import Role
from checklist.models import (
    ChecklistItem,
    ChecklistRecord,
    DepartmentChecklistItem,
)
from core.factories import (
    BaseFixtureTestCase,
    approve_initial_count,
    create_item,
    create_managed_item,
    create_supplier,
)
from core.models import Department
from django.utils import timezone
from inventory.models import (
    CartItem,
    Item,
    ItemCategory,
    ManagedItem,
    Order,
    OrderItem,
    StockTransaction,
    Supplier,
)
from inventory.order_services import (
    add_to_cart,
    confirm_order,
    create_stock_in_from_order_item,
)
from inventory.selectors import get_current_stock
from notice.models import Notice

User = get_user_model()

CMD = "reset_alpha_transactions"


class _ResetAlphaBase(BaseFixtureTestCase):
    """기준정보 + Inventory 운영기록 + Checklist + Notice + Session 을 갖춘 fixture."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.sup = create_supplier(name="A업체")
        cls.item = create_item("거즈 5x5", category=ItemCategory.MEDICAL_SUPPLY)
        cls.mi = create_managed_item(
            item=cls.item,
            department=cls.dept_skin,
            default_supplier=cls.sup,
            minimum_stock=5,
        )
        approve_initial_count(cls.mi, created_by=cls.manager)

        # Checklist 기준정보 + 완료 기록
        cls.chk_item = ChecklistItem.objects.create(title="오픈 점검")
        cls.chk_assign = DepartmentChecklistItem.objects.create(
            item=cls.chk_item, department=cls.dept_skin
        )
        ChecklistRecord.objects.create(
            department_item=cls.chk_assign,
            date=timezone.localdate(),
            completed_at=timezone.now(),
            completed_by=cls.staff_skin,
        )

        # 공지사항(보존 대상)
        Notice.objects.create(title="운영 공지", content="본문")

    def setUp(self):
        # 세션 1건(멱등/옵션 테스트용). setUpTestData 밖에서 만들어도 무방.
        Session.objects.create(
            session_key="alpha-test-key",
            session_data="",
            expire_date=timezone.now() + timezone.timedelta(days=1),
        )

    def _make_inventory_records(self):
        """입고 + 주문 + 주문 기반 입고 + 장바구니 를 생성한다."""
        from inventory.services import create_stock_in

        create_stock_in(
            user=self.staff_skin, managed_item=self.mi, quantity=10,
            unit_price=Decimal("1000"),
        )
        add_to_cart(
            user=self.staff_skin, managed_item=self.mi, supplier=self.sup, quantity=5
        )
        order = confirm_order(user=self.staff_skin)[0]
        oi = order.items.first()
        create_stock_in_from_order_item(
            user=self.staff_skin, order_item=oi, quantity=2,
            unit_price=Decimal("500"), no_expiration=True,
        )
        add_to_cart(
            user=self.staff_skin, managed_item=self.mi, supplier=self.sup, quantity=3
        )

    def _db_name(self):
        return connection.settings_dict["NAME"]

    def _run(self, *args):
        out = StringIO()
        call_command(CMD, *args, stdout=out)
        return out.getvalue()


class DryRunTest(_ResetAlphaBase):
    """15.1 dry-run: 무변경 + 출력 내용."""

    def test_dry_run_changes_nothing(self):
        self._make_inventory_records()
        before = {
            "tx": StockTransaction.objects.count(),
            "order": Order.objects.count(),
            "cart": CartItem.objects.count(),
            "chk_record": ChecklistRecord.objects.count(),
            "session": Session.objects.count(),
            "stock": get_current_stock(self.mi),
        }
        out = self._run()  # 기본 dry-run
        self.assertEqual(StockTransaction.objects.count(), before["tx"])
        self.assertEqual(Order.objects.count(), before["order"])
        self.assertEqual(CartItem.objects.count(), before["cart"])
        self.assertEqual(ChecklistRecord.objects.count(), before["chk_record"])
        self.assertEqual(Session.objects.count(), before["session"])
        self.assertEqual(get_current_stock(self.mi), before["stock"])
        self.assertIn("DRY RUN", out)

    def test_dry_run_output_has_db_name_and_counts(self):
        self._make_inventory_records()
        out = self._run()
        self.assertIn(self._db_name(), out)  # 현재 DB명 출력
        self.assertIn("StockTransaction", out)  # 삭제 예정 모델
        self.assertIn("삭제 예정", out)
        self.assertIn("보존 예정", out)
        self.assertIn("전부 0", out)  # 예상 현재고

    def test_explicit_dry_run_flag_with_yes_still_no_delete(self):
        self._make_inventory_records()
        before = StockTransaction.objects.count()
        # --yes 여도 --dry-run 이면 삭제하지 않는다.
        self._run("--yes", "--dry-run", "--confirm-db", self._db_name())
        self.assertEqual(StockTransaction.objects.count(), before)


class ConfirmDbGuardTest(_ResetAlphaBase):
    """15.2 확인 옵션(--yes / --confirm-db)."""

    def test_no_yes_is_dry_run(self):
        self._make_inventory_records()
        before = StockTransaction.objects.count()
        self._run()  # 아무 옵션 없음 → dry-run
        self.assertEqual(StockTransaction.objects.count(), before)

    def test_yes_without_confirm_db_refuses(self):
        self._make_inventory_records()
        with self.assertRaises(CommandError):
            self._run("--yes")
        self.assertTrue(StockTransaction.objects.exists())  # 미삭제

    def test_yes_with_wrong_confirm_db_refuses(self):
        self._make_inventory_records()
        with self.assertRaises(CommandError):
            self._run("--yes", "--confirm-db", "gimpo365os_rehearsal_WRONG")
        self.assertTrue(StockTransaction.objects.exists())  # 미삭제

    @override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
    def test_yes_with_matching_confirm_db_executes(self):
        self._make_inventory_records()
        self.assertTrue(StockTransaction.objects.exists())
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertFalse(StockTransaction.objects.exists())  # 삭제됨


@override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
class MasterDataPreservedTest(_ResetAlphaBase):
    """15.3 기준정보 보존."""

    def test_master_data_counts_unchanged(self):
        self._make_inventory_records()
        before = {
            "Department": Department.objects.count(),
            "User": User.objects.count(),
            "Supplier": Supplier.objects.count(),
            "Item": Item.objects.count(),
            "ManagedItem": ManagedItem.objects.count(),
            "ChecklistItem": ChecklistItem.objects.count(),
            "DepartmentChecklistItem": DepartmentChecklistItem.objects.count(),
            "Notice": Notice.objects.count(),
        }
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(Department.objects.count(), before["Department"])
        self.assertEqual(User.objects.count(), before["User"])
        self.assertEqual(Supplier.objects.count(), before["Supplier"])
        self.assertEqual(Item.objects.count(), before["Item"])
        self.assertEqual(ManagedItem.objects.count(), before["ManagedItem"])
        self.assertEqual(ChecklistItem.objects.count(), before["ChecklistItem"])
        self.assertEqual(
            DepartmentChecklistItem.objects.count(),
            before["DepartmentChecklistItem"],
        )
        self.assertEqual(Notice.objects.count(), before["Notice"])

    def test_user_role_and_department_preserved(self):
        self._run("--yes", "--confirm-db", self._db_name())
        u = User.objects.get(pk=self.staff_skin.pk)
        self.assertEqual(u.role, Role.STAFF)
        self.assertEqual(u.department_id, self.dept_skin.pk)


@override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
class OperationalRecordsDeletedTest(_ResetAlphaBase):
    """15.4 Inventory 운영기록 삭제 / 15.5 현재고 0."""

    def test_all_inventory_operational_records_deleted(self):
        self._make_inventory_records()
        self.assertTrue(StockTransaction.objects.exists())
        self.assertTrue(Order.objects.exists())
        self.assertTrue(OrderItem.objects.exists())
        self.assertTrue(CartItem.objects.exists())
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(StockTransaction.objects.count(), 0)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_current_stock_zero_after_reset(self):
        self._make_inventory_records()
        self.assertGreater(get_current_stock(self.mi), Decimal("0"))
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(get_current_stock(self.mi), Decimal("0"))

    def test_complete_output_reports_zero(self):
        self._make_inventory_records()
        out = self._run("--yes", "--confirm-db", self._db_name())
        self.assertIn("COMPLETE", out)
        self.assertIn("현재고 전부 0", out)
        self.assertIn("기준정보 건수 일치: 예", out)


@override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
class ChecklistRecordOptionTest(_ResetAlphaBase):
    """15.6 ChecklistRecord 옵션."""

    def test_default_keeps_checklist_records(self):
        before = ChecklistRecord.objects.count()
        self.assertGreater(before, 0)
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(ChecklistRecord.objects.count(), before)

    def test_include_checklist_records_deletes_records_keeps_items(self):
        item_n = ChecklistItem.objects.count()
        assign_n = DepartmentChecklistItem.objects.count()
        self._run(
            "--yes", "--confirm-db", self._db_name(), "--include-checklist-records"
        )
        self.assertEqual(ChecklistRecord.objects.count(), 0)
        self.assertEqual(ChecklistItem.objects.count(), item_n)  # 항목 유지
        self.assertEqual(DepartmentChecklistItem.objects.count(), assign_n)  # 배정 유지


@override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
class SessionOptionTest(_ResetAlphaBase):
    """15.7 Session 옵션."""

    def test_default_keeps_sessions(self):
        before = Session.objects.count()
        self.assertGreater(before, 0)
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(Session.objects.count(), before)

    def test_clear_sessions_deletes_sessions_keeps_users(self):
        user_n = User.objects.count()
        self._run("--yes", "--confirm-db", self._db_name(), "--clear-sessions")
        self.assertEqual(Session.objects.count(), 0)
        self.assertEqual(User.objects.count(), user_n)  # 사용자 유지


@override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
class AtomicityTest(_ResetAlphaBase):
    """15.8 원자성: 삭제 도중 오류 → 전체 rollback."""

    def test_error_midway_rolls_back_everything(self):
        self._make_inventory_records()
        tx_before = StockTransaction.objects.count()
        order_before = Order.objects.count()
        chk_before = ChecklistRecord.objects.count()

        # 삭제 순서상 마지막 단계(ChecklistRecord)에서 강제 오류 발생.
        # 앞서 삭제된 Inventory 운영기록도 함께 rollback 되어야 한다.
        with mock.patch(
            "inventory.management.commands.reset_alpha_transactions.ChecklistRecord"
        ) as mock_cr:
            mock_cr.objects.all.return_value.delete.side_effect = RuntimeError("boom")
            with self.assertRaises(CommandError):
                self._run(
                    "--yes",
                    "--confirm-db",
                    self._db_name(),
                    "--include-checklist-records",
                )

        # 전체 복원
        self.assertEqual(StockTransaction.objects.count(), tx_before)
        self.assertEqual(Order.objects.count(), order_before)
        self.assertEqual(ChecklistRecord.objects.count(), chk_before)
        self.assertGreater(get_current_stock(self.mi), Decimal("0"))  # 현재고 복원


@override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
class IdempotencyTest(_ResetAlphaBase):
    """15.9 멱등성: 2회 실행해도 오류 없음."""

    def test_second_run_deletes_nothing_and_is_safe(self):
        self._make_inventory_records()
        self._run("--yes", "--confirm-db", self._db_name())  # 1회
        master_before = {
            "User": User.objects.count(),
            "ManagedItem": ManagedItem.objects.count(),
            "Supplier": Supplier.objects.count(),
        }

        out = self._run("--yes", "--confirm-db", self._db_name())  # 2회
        # 오류 없이 완료, 삭제 0
        self.assertEqual(StockTransaction.objects.count(), 0)
        self.assertIn("StockTransaction: 0", out)
        # 기준정보 유지 / 현재고 0
        self.assertEqual(User.objects.count(), master_before["User"])
        self.assertEqual(ManagedItem.objects.count(), master_before["ManagedItem"])
        self.assertEqual(Supplier.objects.count(), master_before["Supplier"])
        self.assertEqual(get_current_stock(self.mi), Decimal("0"))


class AllowResetGuardTest(_ResetAlphaBase):
    """P3-08A-01 보완: ALLOW_ALPHA_TRANSACTION_RESET 운영 재실행 방지 가드."""

    def test_default_setting_is_false(self):
        # 10.1 환경변수 미설정 시 기본 False (config/settings.py env.bool default=False).
        self.assertFalse(settings.ALLOW_ALPHA_TRANSACTION_RESET)

    @override_settings(ALLOW_ALPHA_TRANSACTION_RESET=False)
    def test_dry_run_allowed_when_guard_false(self):
        # 10.2 가드 False 여도 dry-run 은 허용, 데이터 무변경, 가드 상태 출력.
        self._make_inventory_records()
        before = StockTransaction.objects.count()
        out = self._run()  # dry-run
        self.assertEqual(StockTransaction.objects.count(), before)
        self.assertIn("ALLOW_ALPHA_TRANSACTION_RESET", out)
        self.assertIn("비활성", out)

    @override_settings(ALLOW_ALPHA_TRANSACTION_RESET=False)
    def test_real_execution_blocked_when_guard_false(self):
        # 10.3 가드 False + --yes + 올바른 --confirm-db → CommandError, 모든 데이터 무변경.
        self._make_inventory_records()
        before = {
            "tx": StockTransaction.objects.count(),
            "order": Order.objects.count(),
            "order_item": OrderItem.objects.count(),
            "cart": CartItem.objects.count(),
            "chk": ChecklistRecord.objects.count(),
            "session": Session.objects.count(),
            "user": User.objects.count(),
            "mi": ManagedItem.objects.count(),
            "stock": get_current_stock(self.mi),
        }
        with self.assertRaises(CommandError):
            self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(StockTransaction.objects.count(), before["tx"])
        self.assertEqual(Order.objects.count(), before["order"])
        self.assertEqual(OrderItem.objects.count(), before["order_item"])
        self.assertEqual(CartItem.objects.count(), before["cart"])
        self.assertEqual(ChecklistRecord.objects.count(), before["chk"])
        self.assertEqual(Session.objects.count(), before["session"])
        self.assertEqual(User.objects.count(), before["user"])
        self.assertEqual(ManagedItem.objects.count(), before["mi"])
        self.assertEqual(get_current_stock(self.mi), before["stock"])

    @override_settings(ALLOW_ALPHA_TRANSACTION_RESET=False)
    def test_guard_false_blocks_even_with_include_and_clear_options(self):
        # 옵션을 함께 줘도 가드 False 면 차단, ChecklistRecord·Session 무변경.
        chk_before = ChecklistRecord.objects.count()
        session_before = Session.objects.count()
        with self.assertRaises(CommandError):
            self._run(
                "--yes", "--confirm-db", self._db_name(),
                "--include-checklist-records", "--clear-sessions",
            )
        self.assertEqual(ChecklistRecord.objects.count(), chk_before)
        self.assertEqual(Session.objects.count(), session_before)

    @override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
    def test_real_execution_allowed_when_guard_true(self):
        # 10.4 가드 True + --yes + 올바른 --confirm-db → 기존 정상 삭제.
        self._make_inventory_records()
        self.assertTrue(StockTransaction.objects.exists())
        self._run("--yes", "--confirm-db", self._db_name())
        self.assertEqual(StockTransaction.objects.count(), 0)
        self.assertEqual(get_current_stock(self.mi), Decimal("0"))

    @override_settings(ALLOW_ALPHA_TRANSACTION_RESET=True)
    def test_confirm_db_still_required_even_when_guard_true(self):
        # 10.6 가드 True 여도 --confirm-db 불일치는 여전히 차단(독립 안전장치).
        self._make_inventory_records()
        with self.assertRaises(CommandError):
            self._run("--yes", "--confirm-db", "WRONG_DB_NAME")
        self.assertTrue(StockTransaction.objects.exists())  # 미삭제
