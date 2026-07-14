# CHECKLIST_TECH_SPEC.md

# 김포365OS Checklist Module 기술 명세서

## 문서 버전

```text
문서명: CHECKLIST_TECH_SPEC.md
문서 범위: 김포365OS Module 3 — Checklist 기술 구현 기준
문서 상태: Checklist v1 구현 완료 (Phase 3 마감, P3-07). 본 문서의 설계는 실제 구현과 일치한다.
전제 문서: OS_TECH_SPEC.md, OS_ARCHITECTURE.md, OS_WORKING_RULES.md, CHECKLIST_PRODUCT_SPEC.md, NOTICE_TECH_SPEC.md
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                       |
| ---- | ---------- | ------------------------------------------- |
| v0.2 | 2026-07-14 | Checklist v1 구현 완료 반영. §21 확정 대상 해소(실제 함수명/URL/mixin 확정) |
| v0.1 | 2026-07-13 | P3-00 Checklist v1 기술 설계 초안 (3모델·daily selector·KST) |

---

## 0. 문서 성격

이 문서는 Checklist Module을 "어떻게" 만들지 정의하는 기술 설계 문서다.

**이번 단계(P3-00)에서는 실제 코드·앱·모델·migration을 만들지 않는다.**
아래 코드 블록은 설계 초안이며, 실제 필드명/옵션은 구현 단계에서 코드 스타일에 맞춰 확정한다.

이 문서는 OS_TECH_SPEC의 공통 CRUD(§13), 공통 권한 Mixin(§14), Department+role(§16), abstract base model(§17), Timezone(§7), Checklist 기술 기준(§25)을 상속한다. Notice에서 검증된 패턴(OperationalBaseModel 상속, selectors, accounts.mixins.ManagerRequiredMixin)을 재사용한다.

---

## 1. 앱 구조

```text
권장 앱 이름: checklist  (신규 Django 앱)
위치: 프로젝트 루트의 checklist/  (docs/modules/checklist/ 는 문서 전용)
INSTALLED_APPS 등록: "checklist" 를 로컬 앱(core, accounts, inventory, notice) 뒤에 추가
```

앱 구성 파일(구현 단계 산출물):

```text
checklist/
├─ __init__.py
├─ apps.py
├─ models.py        (ChecklistItem, DepartmentChecklistItem, ChecklistRecord)
├─ selectors.py     (오늘 항목 / 누락 현황 계산)
├─ services.py      (완료/완료취소 상태 전이 — 필요 시)
├─ views.py         (CBV/FBV)
├─ urls.py          (app_name = "checklist")
├─ admin.py         (3모델 최소 등록)
├─ migrations/
└─ tests.py
templates/checklist/
```

확인된 재사용 자산:

```text
core.models.OperationalBaseModel (created_at/updated_at/created_by/updated_by/is_active, abstract)
core.Department (name, is_active, ...)
accounts.User.department (FK core.Department, SET_NULL, nullable) + role
accounts.permissions.is_manager_or_above / has_role_at_least / ROLE_RANK
accounts.mixins.ManagerRequiredMixin (P2-05)
notice/selectors.py (selector 패턴 참고)
settings: TIME_ZONE="Asia/Seoul", USE_TZ=True
```

---

## 2. URL 후보

```text
/checklists/                 → 오늘의 내 부서 체크리스트 (name: today)
/checklists/complete/        → 완료 처리 (POST, name: complete)
/checklists/uncomplete/      → 완료 취소 (POST, name: uncomplete)
/checklists/status/          → 누락 현황 (TEAM_LEADER 이상, name: status)
```

`app_name = "checklist"` namespace. 현재 `/checklists/` 는 core placeholder(`checklist_placeholder`)이므로 P3-01에서 checklist 앱으로 이관한다(Notice P2-01과 동일 방식). 정확한 URL 이름/구조는 구현 단계에서 확정.

---

## 3. 3모델 구조

Checklist는 3개 모델로 설계한다(2모델로 축소하지 않는다). Inventory의 Item ↔ ManagedItem 구조와 같은 방향이다.

```text
ChecklistItem            = 업무 항목 정의 (문구 + frequency)
DepartmentChecklistItem  = 항목을 어느 부서가 수행할지 배정
ChecklistRecord          = 특정 날짜에 부서 배정 항목을 누가 완료했는지 기록
```

---

## 4. OperationalBaseModel 상속

3개 모델 모두 `core.OperationalBaseModel`을 상속한다.

```text
상속 필드(반복 선언 금지): created_at, updated_at, created_by, updated_by, is_active
- created_by / updated_by : settings.AUTH_USER_MODEL FK, SET_NULL, null=True, blank=True (감사용)
- is_active : 논리 삭제 / 비활성 (default True)
```

주의: `is_active`, `created_at/updated_at/created_by/updated_by`를 각 모델에 다시 선언하지 않는다.

---

## 5. Model 초안 (설계, 미구현)

> 실제 필드명/옵션/제약은 구현 단계에서 확정한다.

```text
ChecklistItem(OperationalBaseModel)
- title       CharField (실행문 형태의 명확한 문구; description 없음)
- frequency   CharField choices: daily / weekly / monthly (default daily)
- timing      CharField choices: opening / specific / closing (default specific)  # P3-07.5
  (Department FK 없음, 개인 담당자 FK 없음)
  timing 은 항목 정의 속성이다. 같은 항목을 여러 부서에 배정하면 동일한 timing 을 공유하고,
  부서별로 시기가 다르면 별도 ChecklistItem 으로 정의한다. 시각(시·분) 입력 필드는 없다
  (특정 시각·상황은 title 문구로 적는다). DepartmentChecklistItem 에 timing 을 중복 선언하지 않는다.

DepartmentChecklistItem(OperationalBaseModel)
- item        FK ChecklistItem, on_delete=PROTECT, related_name="department_items"
- department  FK core.Department, on_delete=PROTECT, related_name="checklist_items"
- sort_order  PositiveIntegerField (부서 내 표시 순서, default 0)
- Meta.constraints: UniqueConstraint(fields=["item", "department"])

ChecklistRecord(OperationalBaseModel)
- department_item  FK DepartmentChecklistItem, on_delete=PROTECT, related_name="records"
- date             DateField (기준 날짜 = KST 로컬 날짜)
- completed_by     FK settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True, blank=True
- completed_at     DateTimeField (완료 시각)
- Meta.constraints: UniqueConstraint(fields=["department_item", "date"])
```

completed_by vs created_by:

```text
created_by/updated_by(base) = 레코드 감사(누가 만들었나/마지막 수정자).
completed_by = 실제 수행자. 완료 취소 후 재완료 시 현재 수행자로 갱신(§11).
의미가 달라 별도 필드로 둔다.
```

---

## 6. FK 및 on_delete 기준

OS_TECH_SPEC §20(책임 주체 FK는 PROTECT 또는 SET_NULL, CASCADE 금지) 준수.

```text
item (DepartmentChecklistItem → ChecklistItem)          : PROTECT
department (DepartmentChecklistItem → core.Department)   : PROTECT
department_item (ChecklistRecord → DepartmentChecklistItem): PROTECT
completed_by (ChecklistRecord → User)                   : SET_NULL, null, blank
created_by / updated_by (base)                          : SET_NULL, null, blank
```

PROTECT 의미: 기록(ChecklistRecord)이 연결된 항목/배정은 삭제되지 않는다 → 삭제 대신 is_active=False 비활성화 운영.

---

## 7. UniqueConstraint

```text
DepartmentChecklistItem: UniqueConstraint(item, department)
  → 같은 항목을 같은 부서에 두 번 배정 불가. 서로 다른 부서 배정은 허용.
ChecklistRecord: UniqueConstraint(department_item, date)
  → 같은 부서 배정 항목은 같은 기준 날짜에 완료 기록 1건만.
```

재활성화 원칙: 중복 배정/완료를 만들지 않고, 비활성 행을 재활성화한다(새 행 생성 금지 — §11).

---

## 8. frequency choices

```text
class Frequency(TextChoices): DAILY="daily", WEEKLY="weekly", MONTHLY="monthly"
default = daily
```

```text
- 모델은 3종 모두 포함하지만, v1 "오늘 항목" 판정은 daily 만 사용한다.
- weekly/monthly 반복 규칙 필드(요일/날짜/말일 처리)는 이번에 추가하지 않는다(후순위, additive).
- frequency 는 ChecklistItem 정의에 속하므로, 여러 부서 배정은 같은 frequency 를 공유한다.
```

---

## 9. daily selector 기준

"오늘 항목"은 DB에 매일 미리 생성하지 않고 selector가 계산한다.

```text
오늘 할 일(user, date=None)
= ChecklistItem.is_active=True
× ChecklistItem.frequency=daily
× DepartmentChecklistItem.is_active=True
× DepartmentChecklistItem.department == user.department
× 기준 날짜 = date or timezone.localdate()
각 항목의 완료 여부 = 해당 (department_item, date) 의 활성 ChecklistRecord 존재 여부
```

정렬 (P3-07.5):

```text
오늘 화면(get_today_checklist_items) — 미완료 우선, 같은 상태 안에서 timing → 순서:
1. is_completed          (미완료 False → 완료 True; 완료 항목이 하단)
2. timing rank           (opening → specific → closing)
3. DepartmentChecklistItem.sort_order
4. ChecklistItem.title
5. DepartmentChecklistItem.pk
→ 완료/취소 redirect 후 완료 항목이 자동으로 하단으로 이동한다. DB 조회 2쿼리 유지, 최종 정렬은 Python.

누락 현황(missing_items, 미완료만 존재):
1. timing rank  2. sort_order  3. ChecklistItem.title  4. DepartmentChecklistItem.pk
→ 집계 방식·최대 3쿼리 구조는 그대로. TIMING_ORDER = {opening:0, specific:1, closing:2}.
```

권장 selector(정확한 이름은 구현 단계 확정):

```text
checklist/selectors.py
- get_today_checklist_items(user, date=None)      # 오늘 내 부서 항목 + 완료 여부
- get_checklist_missing_status(user, date=None)   # 누락 현황(부서 범위는 role 로 결정)
```

department 없는 사용자: `user.department_id` 가 없으면 빈 결과(부서 항목 없음). Notice selector와 동일하게 `department_id` 존재를 먼저 확인한다.

---

## 10. KST localdate 기준

```text
settings: TIME_ZONE="Asia/Seoul", USE_TZ=True (확인됨)
기준 날짜는 서버 UTC 날짜가 아니라 KST 로컬 날짜다.
날짜 판정은 timezone.localdate() 를 기본으로 한다. date.today() 직접 사용 금지(OS_TECH_SPEC §7).
ChecklistRecord.date 는 DateField. completed_at 은 timezone-aware DateTimeField.
```

"당일"의 정의 = KST 로컬 날짜. 전날 완료는 오늘 목록에 넘어오지 않는다.

---

## 11. 완료/미완료 데이터 해석 · 완료 취소 정책

```text
완료   = (department_item, date) 의 활성 ChecklistRecord 존재
미완료 = 위 활성 레코드 없음
```

완료 취소(데이터 보존):

```text
- hard delete 하지 않는다.
- 완료 취소 = ChecklistRecord.is_active=False.
- 재완료 = 동일 unique 레코드(department_item, date)를 재활성화(is_active=True) +
           completed_by/completed_at 을 현재 수행자/현재 시각으로 갱신.
- 승인/반려·별도 상태 필드 추가 금지.
- 구현 시 get_or_create + 상태 전이를 services 로 감싸는 방향 검토(중복 레코드 방지).
```

이 전이는 UniqueConstraint(department_item, date)와 함께 "하루 1레코드"를 보장한다.

---

## 12. 사용자 / Department 접근제어

```text
오늘 항목(today): LoginRequiredMixin. user.department 범위의 daily 항목만.
완료/완료취소(complete/uncomplete):
  - 대상 department_item 의 department == request.user.department 인지 검증.
  - STAFF/TEAM_LEADER: 본인 부서 항목만.
  - MANAGER/ADMIN: 타 부서 완료 대행 기본 불허(§10, 예외는 P3-04 전 결정).
  - completed_by = request.user (서버측, 사용자 입력 신뢰 금지).
```

접근제어는 selector/service에서 department 일치를 강제한다(뷰 버튼 노출만으로 신뢰하지 않음).

---

## 13. TEAM_LEADER 이상 누락 현황 권한

```text
status 화면: has_role_at_least(user, Role.TEAM_LEADER) 필요.
- TEAM_LEADER: 본인 department 누락만.
- MANAGER/ADMIN: 전체 department 누락.
- STAFF: 접근 불가(403).
```

권장: `accounts.mixins`에 `TeamLeaderRequiredMixin`을 신설할지, 뷰 내 `has_role_at_least` 검사로 둘지 P3-05에서 결정. ManagerRequiredMixin 패턴과 동일 원칙(비로그인→redirect, 권한 부족→403, raise_exception 미설정). inventory 권한 코드는 건드리지 않는다.

---

## 14. CBV 구조 후보

```text
TodayChecklistView      (LoginRequiredMixin, TemplateView 또는 ListView)  — 오늘 내 부서 항목
ChecklistCompleteView   (LoginRequiredMixin, View/FBV, POST)              — 완료 처리
ChecklistUncompleteView (LoginRequiredMixin, View/FBV, POST)             — 완료 취소
ChecklistStatusView     (TEAM_LEADER 이상, TemplateView/ListView)         — 누락 현황
```

상태 변경(완료/취소)은 POST + CSRF. GET으로 상태를 바꾸지 않는다.

---

## 15. selector / service 구조 후보

```text
checklist/selectors.py
- get_today_checklist_items(user, date=None)
- get_checklist_missing_status(user, date=None)

checklist/services.py (필요 시)
- complete_checklist_item(user, department_item, date=None)   # get_or_create + 재활성화 + completed_by/at
- uncomplete_checklist_item(user, department_item, date=None) # is_active=False
```

Inventory service 계층 규칙(상태 전이는 service 경유)과 같은 방향. 단, Inventory service는 건드리지 않는다.

---

## 16. admin 초기 설정 방식

v1은 별도 항목/배정 관리 CRUD 화면을 만들지 않고 Django admin으로 초기 설정한다.

```text
ChecklistItem admin:           list_display: title, frequency, timing, 배정 부서, is_active, updated_at
                               list_filter: frequency, timing, is_active
                               배정 부서 = 활성 배정·활성 부서만 부서명 순 표시(없으면 "미배정").
                               get_queryset 에서 활성 배정 Prefetch(to_attr) → 목록 N+1 방지.
DepartmentChecklistItem admin: item, department, sort_order, is_active, updated_at
ChecklistRecord admin:         department_item, date, completed_by, completed_at, is_active
  (readonly 중심 확인용. 임의 생성/수정은 최소화 — 완료는 OS 화면에서 처리)
```

감사 필드 처리 (P3-07.5): ChecklistItem/DepartmentChecklistItem admin 에서 created_by·updated_by·
created_at·updated_at 를 읽기 전용으로 노출한다(사용자 선택 dropdown 금지). 실제 값은 _AuditAdminMixin.
save_model 이 현재 로그인 관리자로 자동 기록한다 — 신규: created_by+updated_by, 수정: updated_by 만.
ChecklistRecord admin 은 기존 완전 읽기 전용 유지.

custom action / 파일·첨부 기능 없음.

---

## 17. migration 계획

```text
P3-01: 앱 뼈대(모델 없음) — migration 없음 목표.
P3-02: ChecklistItem / DepartmentChecklistItem / ChecklistRecord + admin 최소 등록
       → 신규 테이블 3개 추가 migration (additive).
       - 새 테이블 + FK + UniqueConstraint. 파괴적 변경 없음.
       - created_by/updated_by/completed_by = User FK 추가(additive).
       - 별도 승인 후 리허설 DB(gimpo365os_rehearsal)에서만 적용(운영 DB 격리).
       - 절차는 OS_DB_OPERATIONS §6.
P3-03 이후: 모델 변경 없이 selector/view/template 만 추가(migration 없음 목표).
P3-07.5: ChecklistItem.timing 추가 → checklist.0002_checklistitem_timing (AddField 1개, additive).
         default=specific 이라 기존 항목은 모두 specific 으로 채워진다. 리허설 DB 에만 적용.
```

---

## 18. 테스트 계획

```text
모델/제약:
- UniqueConstraint(item, department) / (department_item, date) 위반 시 IntegrityError
- OperationalBaseModel 상속 필드 존재, completed_by SET_NULL·nullable
- KST 날짜: timezone.localdate() 기준 date 저장/조회
selector:
- daily 항목만 오늘 목록에 포함(weekly/monthly 제외)
- item/department 배정 비활성 시 제외 규칙(§ PRODUCT_SPEC 7)
- department 없는 사용자 → 빈 목록
- 완료 여부 = 활성 레코드 존재
완료/취소:
- 완료 → 레코드 생성/재활성 + completed_by/at
- 완료취소 → is_active=False (hard delete 아님)
- 재완료 → 동일 unique 레코드 재활성 + completed_by 갱신
권한:
- 타 부서 완료 시도 차단
- status: STAFF 403 / TEAM_LEADER 본인 부서 / MANAGER·ADMIN 전체
회귀:
- Notice / Inventory 주요 화면 정상
```

---

## 19. Notice / Inventory 회귀 기준

```text
- checklist 앱 추가·모델 추가가 기존 앱 migration 을 발생시키지 않아야 한다(checklist 앱만).
- /checklists/ placeholder → checklist 앱 이관 시 다른 placeholder(manuals/requests/schedules) 및
  notice 진입은 그대로 유지.
- accounts.mixins/permissions 재사용은 import 만 하며 기존 로직을 변경하지 않는다.
- inventory service/권한 코드는 수정하지 않는다.
```

---

## 20. v1 제외 항목 (기술)

```text
- 개인 담당자 FK / 개인별 할 일
- 승인/반려 상태·필드, 승인자/승인시각
- FileField/ImageField, MEDIA 설정, 마감 양식 업로드·전송
- 알림/독촉/읽음확인
- weekly 요일·monthly 날짜 규칙 필드 및 판정 로직
- 공휴일 자동 제외
- 통계 대시보드
- 항목/배정 전용 OS CRUD 화면
```

---

## 21. 구현 확정 결과 (P3-07 기준 — 모두 해소)

```text
[확정] URL(checklist namespace):
       /checklists/                         name="today"    (TodayChecklistView)
       /checklists/status/                  name="status"   (ChecklistStatusView)
       /checklists/<pk>/complete/           name="complete" (CompleteChecklistItemView, POST)
       /checklists/<pk>/cancel/             name="cancel"   (CancelChecklistItemView, POST)
[확정] service 분리 = checklist/services.py:
       complete_checklist_item / cancel_checklist_item (반환 (record, changed)),
       도메인 예외 ChecklistActionNotAllowed, transaction.atomic + select_for_update.
[확정] selector = checklist/selectors.py:
       get_today_checklist_items(→TodayChecklistEntry, 최대 2쿼리),
       get_checklist_status_for_user(→DepartmentChecklistStatus, 최대 3쿼리).
[확정] status 권한 = accounts.mixins.TeamLeaderRequiredMixin (신설). 범위는 selector 가 role 로 강제.
[확정] MANAGER/ADMIN 완료 대행 = 불허(타 부서 완료 시 PermissionDenied/403).
[확정] 3모델 / frequency 필드 / daily 우선 / 승인 없음 / 첨부 없음 / 개인 담당자 없음.
[완료] P3-02 3모델 migration(checklist.0001_initial) 리허설 DB 적용.
[확정] 완료 취소 감사: is_active=False + updated_by=취소자, completed_by/at 보존.
       재완료: 같은 레코드 재활성화 + completed_by/at 갱신(created_by 유지).
```
