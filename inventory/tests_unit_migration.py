"""P3-07.6 데이터 이관 migration(0007) 검증.

MigrationExecutor 로 0006(확장) 상태에서 데이터를 만든 뒤 0007(복사)을 적용해:
- 동일 unit 복사 정상 / Item·ManagedItem·거래 PK·수량 보존
- 복수 unit·공백·대소문자·고아 Item → RuntimeError + 전체 rollback
을 확인한다. 실제 운영 DB 와 무관한 test DB 에서만 수행한다.
"""

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

APP = "inventory"
EXPAND = "0006_item_unit"
COPY = "0007_copy_unit_manageditem_to_item"
HEAD = "0008_remove_manageditem_unit_alter_item_unit"


class _DataMigrationBase(TransactionTestCase):
    """0006 로 되돌려 데이터 준비 → 0007 적용 흐름 헬퍼."""

    def _migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([(APP, target)])
        return executor.loader.project_state([(APP, target)]).apps

    def setUp(self):
        # 0006(확장) 상태로 이동: Item.unit nullable, ManagedItem.unit 존재
        self.old_apps = self._migrate(EXPAND)

    def tearDown(self):
        # 다음 테스트를 위해 데이터 제거 후 최신(HEAD) 스키마로 복원.
        # 상태가 섞여도 안전하도록 raw SQL 로 정리한다.
        with connection.cursor() as c:
            for table in (
                "inventory_stocktransaction",
                "inventory_cartitem",
                "inventory_orderitem",
                "inventory_order",
                "inventory_manageditem",
                "inventory_item",
            ):
                c.execute(f"DELETE FROM {table}")
        call_command("migrate", APP, HEAD, verbosity=0)

    # --- 준비 헬퍼 (0006 historical 모델 사용) ---
    def _dept(self, name="피부실"):
        Department = self.old_apps.get_model("core", "Department")
        return Department.objects.create(name=name)

    def _item(self, name, unit=None):
        Item = self.old_apps.get_model(APP, "Item")
        return Item.objects.create(name=name, category="MEDICAL_SUPPLY", unit=unit)

    def _mi(self, item, dept, unit):
        ManagedItem = self.old_apps.get_model(APP, "ManagedItem")
        return ManagedItem.objects.create(
            item=item, department=dept, unit=unit, minimum_stock=0
        )

    def _apply_copy(self):
        return self._migrate(COPY)


class UnitCopySuccessTest(_DataMigrationBase):
    def test_uniform_unit_copied_and_pks_preserved(self):
        dept1 = self._dept("피부실")
        dept2 = self._dept("치료실")
        item = self._item("거즈 5x5", unit=None)
        mi1 = self._mi(item, dept1, "BOX")
        mi2 = self._mi(item, dept2, "BOX")  # 동일 unit, 다른 부서

        # 거래 1건(PK/수량 보존 확인용)
        User = self.old_apps.get_model("accounts", "User")
        user = User.objects.create(username="mig_user")
        StockTransaction = self.old_apps.get_model(APP, "StockTransaction")
        tx = StockTransaction.objects.create(
            managed_item=mi1,
            transaction_type="IN",
            status="APPROVED",
            quantity_input=10,
            quantity_delta=10,
            created_by=user,
        )

        item_pk, mi1_pk, mi2_pk, tx_pk = item.pk, mi1.pk, mi2.pk, tx.pk

        new_apps = self._apply_copy()

        Item = new_apps.get_model(APP, "Item")
        ManagedItem = new_apps.get_model(APP, "ManagedItem")
        StockTransaction2 = new_apps.get_model(APP, "StockTransaction")

        copied = Item.objects.get(pk=item_pk)
        self.assertEqual(copied.unit, "BOX")  # 정확히 보존 복사
        # PK 보존
        self.assertTrue(ManagedItem.objects.filter(pk=mi1_pk).exists())
        self.assertTrue(ManagedItem.objects.filter(pk=mi2_pk).exists())
        # 거래 PK/수량 불변
        tx2 = StockTransaction2.objects.get(pk=tx_pk)
        self.assertEqual(tx2.quantity_input, 10)
        self.assertEqual(tx2.quantity_delta, 10)
        self.assertEqual(tx2.status, "APPROVED")


class UnitCopyConflictTest(_DataMigrationBase):
    def _assert_blocks_and_rolls_back(self):
        # 0007 적용은 RuntimeError 로 실패하고 전체 rollback → Item.unit 은 NULL 로 남는다.
        with self.assertRaises(RuntimeError):
            self._apply_copy()
        back = self._migrate(EXPAND)  # 실패했으므로 아직 0006 상태
        Item = back.get_model(APP, "Item")
        self.assertTrue(all(i.unit is None for i in Item.objects.all()))

    def test_multiple_units_block(self):
        dept1, dept2 = self._dept("피부실"), self._dept("치료실")
        item = self._item("혼합단위", unit=None)
        self._mi(item, dept1, "BOX")
        self._mi(item, dept2, "EA")  # 서로 다른 unit
        self._assert_blocks_and_rolls_back()

    def test_case_or_space_variant_block(self):
        dept1, dept2 = self._dept("피부실"), self._dept("치료실")
        item = self._item("대소문자변형", unit=None)
        self._mi(item, dept1, "BOX")
        self._mi(item, dept2, "box")  # 대소문자 차이 → 자동 통합하지 않음
        self._assert_blocks_and_rolls_back()

    def test_empty_unit_block(self):
        dept = self._dept("피부실")
        item = self._item("빈단위", unit=None)
        self._mi(item, dept, "")  # 빈 unit
        self._assert_blocks_and_rolls_back()

    def test_orphan_item_block(self):
        # 연결 ManagedItem 이 없는 Item → 추론 불가
        self._item("고아품목", unit=None)
        self._assert_blocks_and_rolls_back()
