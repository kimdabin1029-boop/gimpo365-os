from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from core.factories import (
    BaseFixtureTestCase,
    create_item,
    create_managed_item,
    create_stock_transaction,
    create_supplier,
)
from inventory.models import (
    Item,
    ItemCategory,
    ManagedItem,
    Supplier,
    TransactionStatus,
    TransactionType,
    Unit,
)


class SupplierModelTest(TestCase):
    def test_name_unique(self):
        """4.2 Supplier.name unique 테스트"""
        create_supplier(name="메디칼코리아")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_supplier(name="메디칼코리아")

    def test_name_strip_normalization(self):
        """4.11 Supplier.name strip 정규화 테스트"""
        supplier = create_supplier(name="  메디칼코리아  ")
        supplier.refresh_from_db()
        self.assertEqual(supplier.name, "메디칼코리아")


class ItemModelTest(TestCase):
    def test_name_unique(self):
        """4.3 Item.name unique 테스트"""
        create_item("거즈 5x5")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_item("거즈 5x5")

    def test_specification_not_unique(self):
        """4.4 Item.specification 은 unique 기준이 아님 테스트"""
        create_item("거즈 5x5", specification="1BOX(10EA)")
        # 같은 specification 이지만 name 이 다르면 생성 가능해야 한다.
        create_item("거즈 10x10", specification="1BOX(10EA)")
        self.assertEqual(Item.objects.filter(specification="1BOX(10EA)").count(), 2)

    def test_name_strip_normalization(self):
        """4.11 Item.name strip 정규화 테스트"""
        item = create_item("  니들 30G  ")
        item.refresh_from_db()
        self.assertEqual(item.name, "니들 30G")

    # --- P3-07.6 단위 소유권: Item.unit ---
    def test_item_has_unit_field(self):
        field_names = {f.name for f in Item._meta.get_fields()}
        self.assertIn("unit", field_names)

    def test_item_unit_choices(self):
        choices = {c[0] for c in Item._meta.get_field("unit").choices}
        self.assertEqual(choices, {c[0] for c in Unit.choices})

    def test_item_unit_required_no_default(self):
        # unit 은 필수(null=False), 임의 default 없음 → 값 없이 full_clean 시 오류.
        field = Item._meta.get_field("unit")
        self.assertFalse(field.null)
        self.assertFalse(field.has_default())  # 임의 default 없음
        item = Item(name="단위없음", category=ItemCategory.GENERAL_SUPPLY)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_no_size_or_package_field_added(self):
        # 규격/포장 필드는 추가하지 않는다(규격이 다르면 별도 Item). specification 은 기존 필드로 유지.
        field_names = {f.name for f in Item._meta.get_fields()}
        self.assertNotIn("size", field_names)
        self.assertNotIn("package", field_names)
        self.assertIn("specification", field_names)  # 기존 필드 유지


class ManagedItemUnitRemovedTest(BaseFixtureTestCase):
    """P3-07.6: ManagedItem 에서 unit 제거 확인."""

    def test_manageditem_has_no_unit_field(self):
        field_names = {f.name for f in ManagedItem._meta.get_fields()}
        self.assertNotIn("unit", field_names)

    def test_manageditem_operational_fields_preserved(self):
        field_names = {f.name for f in ManagedItem._meta.get_fields()}
        for name in ("item", "department", "minimum_stock", "storage_location",
                     "default_supplier", "is_active"):
            self.assertIn(name, field_names)


class ManagedItemModelTest(BaseFixtureTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item_gauze = create_item("거즈 5x5", category=ItemCategory.MEDICAL_SUPPLY)

    def test_department_item_unique(self):
        """4.5 ManagedItem department + item unique 테스트"""
        create_managed_item(item=self.item_gauze, department=self.dept_skin)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_managed_item(item=self.item_gauze, department=self.dept_skin)

    def test_same_item_allowed_in_different_departments(self):
        """4.6 다른 부서의 같은 Item 허용 테스트"""
        mi_skin = create_managed_item(item=self.item_gauze, department=self.dept_skin)
        mi_treatment = create_managed_item(
            item=self.item_gauze, department=self.dept_treatment
        )
        self.assertNotEqual(mi_skin.pk, mi_treatment.pk)
        self.assertEqual(
            ManagedItem.objects.filter(item=self.item_gauze).count(), 2
        )

    def test_defaults(self):
        # 단위는 Item 소유이므로 ManagedItem 에는 unit 필드가 없다. (P3-07.6)
        mi = create_managed_item(item=self.item_gauze, department=self.dept_skin)
        self.assertFalse(hasattr(mi, "unit"))
        self.assertEqual(mi.minimum_stock, 0)
        self.assertIsNone(mi.default_supplier)
        self.assertTrue(mi.is_active)


class StockTransactionConstraintTest(BaseFixtureTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item = create_item("거즈 5x5", category=ItemCategory.MEDICAL_SUPPLY)
        cls.mi = create_managed_item(item=cls.item, department=cls.dept_skin)

    def _tx(self, **kwargs):
        kwargs.setdefault("managed_item", self.mi)
        kwargs.setdefault("created_by", self.staff_skin)
        return create_stock_transaction(**kwargs)

    def test_approved_initial_count_uniqueness(self):
        """4.7 APPROVED INITIAL_COUNT 유일성 테스트"""
        self._tx(
            transaction_type=TransactionType.INITIAL_COUNT,
            status=TransactionStatus.APPROVED,
            quantity_input=10,
            quantity_delta=10,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._tx(
                    transaction_type=TransactionType.INITIAL_COUNT,
                    status=TransactionStatus.APPROVED,
                    quantity_input=5,
                    quantity_delta=5,
                )

    def test_pending_initial_count_duplicate_allowed(self):
        """4.8 PENDING INITIAL_COUNT 중복 허용 테스트"""
        self._tx(
            transaction_type=TransactionType.INITIAL_COUNT,
            status=TransactionStatus.PENDING,
            quantity_input=10,
            quantity_delta=10,
        )
        # PENDING 은 partial unique 조건(APPROVED)에 걸리지 않으므로 중복 허용
        self._tx(
            transaction_type=TransactionType.INITIAL_COUNT,
            status=TransactionStatus.PENDING,
            quantity_input=7,
            quantity_delta=7,
        )
        self.assertEqual(
            self.mi.stock_transactions.filter(
                transaction_type=TransactionType.INITIAL_COUNT,
                status=TransactionStatus.PENDING,
            ).count(),
            2,
        )

    def test_quantity_input_negative_blocked(self):
        """4.9 quantity_input 음수 차단 테스트"""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._tx(
                    transaction_type=TransactionType.IN,
                    status=TransactionStatus.APPROVED,
                    quantity_input=-1,
                    quantity_delta=-1,
                )

    def test_quantity_delta_negative_allowed(self):
        """4.10 quantity_delta 음수 허용 테스트"""
        tx = self._tx(
            transaction_type=TransactionType.OUT_USE,
            status=TransactionStatus.APPROVED,
            quantity_input=5,
            quantity_delta=-5,
        )
        self.assertEqual(tx.quantity_delta, -5)


class ItemUnitChangeTest(BaseFixtureTestCase):
    """운영 개시 후 주문단위 변경 금지. 단위 소유권이 Item 으로 이동. (P3-07.6, 구 ManagedItem 규칙)"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item = create_item("거즈 5x5", category=ItemCategory.MEDICAL_SUPPLY, unit=Unit.EA)

    def test_unit_change_allowed_without_approved_tx(self):
        """5.1 APPROVED 거래가 없으면 unit 변경 가능"""
        create_managed_item(item=self.item, department=self.dept_skin)
        self.item.unit = Unit.BOX
        self.item.full_clean()  # ValidationError 가 발생하지 않아야 한다
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.unit, Unit.BOX)

    def test_unit_change_blocked_with_approved_tx(self):
        """5.2 APPROVED 거래가 있으면 unit 변경 불가"""
        mi = create_managed_item(item=self.item, department=self.dept_skin)
        create_stock_transaction(
            managed_item=mi,
            transaction_type=TransactionType.IN,
            created_by=self.staff_skin,
            status=TransactionStatus.APPROVED,
            quantity_input=10,
            quantity_delta=10,
        )
        self.item.unit = Unit.BOX
        with self.assertRaises(ValidationError):
            self.item.full_clean()

    def test_unit_change_blocked_across_departments(self):
        """5.2b 다른 부서 ManagedItem 에 APPROVED 거래가 있어도 차단(Item 단위이므로)"""
        create_managed_item(item=self.item, department=self.dept_skin)
        mi_treat = create_managed_item(item=self.item, department=self.dept_treatment)
        create_stock_transaction(
            managed_item=mi_treat,
            transaction_type=TransactionType.IN,
            created_by=self.staff_skin,
            status=TransactionStatus.APPROVED,
            quantity_input=3,
            quantity_delta=3,
        )
        self.item.unit = Unit.BOX
        with self.assertRaises(ValidationError):
            self.item.full_clean()

    def test_unit_change_allowed_with_pending_only(self):
        """5.3 PENDING 거래만 있으면 unit 변경 가능"""
        mi = create_managed_item(item=self.item, department=self.dept_skin)
        create_stock_transaction(
            managed_item=mi,
            transaction_type=TransactionType.INITIAL_COUNT,
            created_by=self.staff_skin,
            status=TransactionStatus.PENDING,
            quantity_input=10,
            quantity_delta=10,
        )
        self.item.unit = Unit.BOX
        self.item.full_clean()  # PENDING 만 있으므로 통과해야 한다
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.unit, Unit.BOX)


class UnitAdminFormTest(BaseFixtureTestCase):
    """P3-07.6 §11: Admin 에서 unit 은 Item 에서만 입력, ManagedItem 에서는 제거·읽기전용 표시."""

    def setUp(self):
        from django.contrib import admin as dj_admin
        from django.test import RequestFactory

        from inventory.admin import ItemAdmin, ManagedItemAdmin

        self.factory = RequestFactory()
        self.item_admin = ItemAdmin(Item, dj_admin.site)
        self.mi_admin = ManagedItemAdmin(ManagedItem, dj_admin.site)

    def _request(self):
        req = self.factory.get("/admin/")
        req.user = self.admin
        return req

    def test_item_admin_form_has_required_unit(self):
        form = self.item_admin.get_form(self._request())
        self.assertIn("unit", form.base_fields)
        self.assertTrue(form.base_fields["unit"].required)  # 필수 입력

    def test_managed_item_admin_form_has_no_unit(self):
        form = self.mi_admin.get_form(self._request())
        self.assertNotIn("unit", form.base_fields)

    def test_managed_item_admin_lists_item_unit_readonly(self):
        item = create_item("냉난방 필터", unit=Unit.BOX)
        mi = create_managed_item(item=item, department=self.dept_skin)
        self.assertIn("item_unit", self.mi_admin.list_display)
        self.assertEqual(self.mi_admin.item_unit(mi), "BOX")


class UnitDisplayQueryTest(BaseFixtureTestCase):
    """P3-07.6 §12: item.unit 표시로 N+1 이 생기지 않는다(selector 가 item select_related)."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(5):
            it = create_item(f"품목{i}", unit=Unit.BOX)
            create_managed_item(item=it, department=cls.dept_skin)

    def test_no_n_plus_1_on_unit_display(self):
        from inventory.selectors import get_managed_items_with_current_stock

        qs = get_managed_items_with_current_stock(self.staff_skin)
        items = list(qs)  # 평가
        # item 은 select_related 되어 있으므로 unit 접근 시 추가 query 없음.
        with self.assertNumQueries(0):
            _ = [mi.item.get_unit_display() for mi in items]
