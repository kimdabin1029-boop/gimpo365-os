"""ManagedItem.unit → Item.unit 데이터 이관. (P3-07.6)

각 Item 에 연결된 ManagedItem 들의 unit 이 '정확히 하나의 동일한 비어있지 않은 값'일 때만
Item.unit 에 복사한다. 추론 불가(연결 ManagedItem 없음)·빈 값·복수 값이면 migration 을
전체 실패시켜 rollback 한다(임의 값 선택 금지). 공백/대소문자 차이도 정규화하지 않는다.

거래/현재고/PK 는 건드리지 않는다(단위 저장 위치만 이동).
apps.get_model 로 과거 스냅샷 모델을 사용한다(현재 모델 직접 import 금지).
"""

from django.db import migrations


def _fmt(label, rows, limit=20):
    head = f"- {label}: {len(rows)}건"
    sample = rows[:limit]
    lines = [
        f"    Item#{r[0]} {r[1]!r}" + (f" units={r[2]}" if len(r) > 2 else "")
        for r in sample
    ]
    more = "" if len(rows) <= limit else f"\n    ... 외 {len(rows) - limit}건"
    return head + "\n" + "\n".join(lines) + more


def copy_unit_forward(apps, schema_editor):
    Item = apps.get_model("inventory", "Item")
    ManagedItem = apps.get_model("inventory", "ManagedItem")

    cannot_infer = []  # 연결 ManagedItem 없음
    empty_unit = []    # 빈 unit 포함
    conflict = []      # 복수 unit

    for item in Item.objects.all():
        mis = list(ManagedItem.objects.filter(item_id=item.pk))
        if not mis:
            cannot_infer.append((item.pk, item.name))
            continue
        # 정확한 문자열 기준. 공백/대소문자 자동 통합하지 않는다.
        units = {mi.unit for mi in mis}
        if any((u is None or str(u).strip() == "") for u in units):
            empty_unit.append((item.pk, item.name))
            continue
        if len(units) != 1:
            conflict.append((item.pk, item.name, sorted(units)))
            continue
        item.unit = next(iter(units))
        item.save(update_fields=["unit"])

    problems = []
    if cannot_infer:
        problems.append(_fmt("unit 추론 불가(연결 ManagedItem 없음)", cannot_infer))
    if empty_unit:
        problems.append(_fmt("빈 unit", empty_unit))
    if conflict:
        problems.append(_fmt("복수 unit 충돌", conflict))
    if problems:
        raise RuntimeError(
            "ManagedItem.unit → Item.unit 이관 실패. 아래 Item 을 먼저 정리하세요"
            "(자동 수정하지 않음, 전체 rollback):\n" + "\n".join(problems)
        )


def copy_unit_backward(apps, schema_editor):
    # 역방향: Item.unit → 그 Item 에 연결된 모든 ManagedItem.unit 에 복사.
    Item = apps.get_model("inventory", "Item")
    ManagedItem = apps.get_model("inventory", "ManagedItem")
    for item in Item.objects.all():
        if item.unit:
            ManagedItem.objects.filter(item_id=item.pk).update(unit=item.unit)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_item_unit"),
    ]

    operations = [
        migrations.RunPython(copy_unit_forward, copy_unit_backward),
    ]
