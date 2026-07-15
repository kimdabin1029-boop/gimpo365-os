# ITEM_UNIT_MIGRATION_SPEC.md

Inventory 단위 소유권 정정: `ManagedItem.unit` → `Item.unit`. (P3-07.6)

```text
문서명: docs/modules/inventory/ITEM_UNIT_MIGRATION_SPEC.md
최종 수정일: 2026-07-15
대상: inventory 0006/0007/0008 migration + 단위 참조 코드 전환
```

## 1. 변경 목적

단위(unit)는 관리 부서나 보관장소에 따라 달라지는 속성이 아니라 **품목 자체에 종속되는
주문·재고관리 단위**다. 기존에 `ManagedItem.unit` 에 있던 단위를 `Item.unit` 으로 이동한다.

## 2. 확정 업무 규칙

```text
- 품목명에 제조사·규격·포장 구성을 포함한다(예: [경방]반하사심탕 연조엑스 10g*300P / A4용지 A4*500*5EA).
- unit 은 입고·출고·실사에 쓰는 주문·재고관리 단위(BOX/EA/PACK/BOTTLE/ROLL/SET 등).
- 같은 Item 을 여러 부서에서 관리해도 단위는 동일하다. 하나의 Item 에 여러 unit 은 금지.
- 부서마다 단위가 달라야 하면 Item 을 분리한다.
- 규격·포장 구성이 다르면 서로 다른 Item 으로 등록한다(별도 규격/size/package 필드 없음).
```

## 3. 기존 구조

```text
Item: name, category, specification, ...
ManagedItem: item, department, unit, minimum_stock, storage_location, default_supplier, ...
```

## 4. 목표 구조

```text
Item: name, category, unit(필수), specification, ...
ManagedItem: item, department, minimum_stock, storage_location, default_supplier, ...  (unit 없음)
단위 표시: managed_item.item.unit / managed_item.item.get_unit_display()
```

## 5. 규격 필드를 만들지 않는 이유

규격·포장 구성은 품목 식별의 일부이므로 `name` 에 포함한다. 별도 `specification`(설명용, 기존 유지)
외에 `size`/`package`/규격 필드를 신설하면 "같은 품목 다른 포장"이 한 레코드에 섞여 단위/재고
식별이 모호해진다. 규격이 다르면 별도 Item 으로 등록하는 것이 재고·주문 식별에 명확하다.

## 6. 주문단위 정의

`unit` = 해당 품목을 입고·출고·실사할 때 사용하는 주문 및 재고관리 단위. Item 필수 입력값
(null·default 없음). Admin/화면 표시명은 "주문단위".

## 7. 실제 데이터 감사 결과 (gimpo365os_prod, 읽기 전용)

```text
1차 감사: Item 203 / ManagedItem 202
  A. unit 추론 불가(연결 ManagedItem 없음): 2   ← 차단
     Item#109 '러시아 녹용(분골) 75g*8P' [MEDICINE] (ManagedItem 0, 거래 0)
     Item#110 '뉴질랜드 녹용(분골) 75g*8P' [MEDICINE] (ManagedItem 0, 거래 0)
  B. 빈 unit: 0   C. 단일 동일 unit: 201   D. 복수 unit 충돌: 0
  존재 unit 값: BOTTLE, BOX, EA, P, PACK (공백/대소문자 변형 없음)

정리: 다빈 승인 하에 잘못 입력된 고아 Item #109/#110 삭제(거래·배정 0건 재확인 후 원자적 삭제).

2차 감사(정리 후): Item 201 / ManagedItem 202
  A=0, B=0, C=201, D=0 → 충돌 0, 진행 가능.
```

## 8. 단위 충돌 처리 원칙

```text
- 공백/대소문자 차이도 자동 통합하지 않는다(정확한 문자열 기준).
- 임의로 첫 번째 unit 을 선택하지 않는다.
- 추론 불가·빈 값·복수 값이면 data migration 을 전체 실패시키고, 사람이 먼저 데이터를 정리한다.
```

## 9. Migration 단계 (inventory 0006 → 0007 → 0008)

```text
0006_item_unit                         [schema 확장]
  - Item.unit 추가(임시 null=True, default 없음). ManagedItem.unit 유지. 다른 모델 변경 없음.

0007_copy_unit_manageditem_to_item     [data 이관]
  - RunPython(forward, backward). apps.get_model 사용(현재 모델 직접 import 금지).
  - Item 별 연결 ManagedItem 의 unit 이 '정확히 하나의 동일한 비어있지 않은 값'이면 Item.unit 에 복사.
  - 추론 불가/빈 값/복수 값이면 RuntimeError → 전체 rollback(문제 Item PK·이름 출력).
  - reverse: Item.unit → 그 Item 의 모든 ManagedItem.unit 로 복사.

0008_remove_manageditem_unit_alter_item_unit   [cleanup]
  - RemoveField ManagedItem.unit + AlterField Item.unit(null=False).
```

reverse: 0008 은 ManagedItem.unit 을 되살리고(자동), 0007 reverse 가 값을 되돌린다. 단, cleanup
이후 실제 운영 적용 상황에서는 **적용 전 전체 백업**을 필수 조건으로 한다(reverse 를 유일한 복구
수단으로 의존하지 않는다).

## 10. 코드 참조 변경 범위

```text
models.py     : Item.unit 추가·Item.clean(단위 변경 금지) / ManagedItem.unit·clean 제거·__str__ 은 item.unit
admin.py      : ItemAdmin(unit 표시·필터·필수) / ManagedItemAdmin(unit 입력 제거, item_unit 읽기전용 표시+select_related)
forms.py      : ManagedItemChoiceField·stock_map 의 get_unit_display → item.get_unit_display
views.py      : 재고 엑셀 등 mi.get_unit_display → mi.item.get_unit_display
master_data_checks.py : mi.get_unit_display → mi.item.get_unit_display
templates/inventory/* : *.get_unit_display → *.item.get_unit_display (현재고/입고/출고/실사/주문/거래/장바구니/현황)
seed_alpha_inventory  : Item 생성 시 unit 입력, ManagedItem defaults 에서 unit 제거
core/factories.py     : create_item(unit=...) / create_managed_item 에서 unit 제거
```

## 11. 검증 항목

```text
- Item.unit 필수·choices / ManagedItem.unit 없음 / size·package 필드 없음 / 기존 필드 유지
- data migration: 동일 unit 복사·PK 보존 / 복수·공백·대소문자·고아 → 실패+rollback
- Item/ManagedItem/거래 PK·수량·현재고 불변
- Admin: Item unit 필수, ManagedItem unit 없음·item_unit 표시
- 단위 표시 N+1 없음(item select_related)
- 입고/출고/실사/주문/현재고/리셋 명령/Notice/Checklist 회귀 없음
```

## 12. 실제 DB 적용 절차 (이번 작업 범위 아님)

```text
1. 실데이터 감사(A/B/D=0) 재확인
2. gimpo365os_prod 전체 백업
3. python manage.py migrate inventory --plan 검토(0006→0007→0008만)
4. 다빈 승인 후 migrate 적용
5. Item.unit 채워짐·ManagedItem.unit 제거·현재고 불변 확인
```

## 13. rollback 및 백업

```text
- 적용 전 전체 백업 필수(OS_DB_OPERATIONS §3). reverse migration 은 보조 수단.
- 0007 은 reversible(양방향 복사). 0008 reverse 는 ManagedItem.unit 재생성 후 0007 reverse 로 값 복원.
- 실패·이상 시 백업본으로 복구(OS_DB_OPERATIONS §5).
```
