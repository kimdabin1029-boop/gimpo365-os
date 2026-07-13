# CHECKLIST_TASKS.md

# 김포365OS Checklist Module 작업 목록

## 문서 버전

```text
문서명: CHECKLIST_TASKS.md
문서 범위: 김포365OS Module 3 — Checklist 구현 작업 단위 분리
문서 상태: P3-00 설계 초안
전제 문서: CHECKLIST_PRODUCT_SPEC.md, CHECKLIST_TECH_SPEC.md, OS_WORKING_RULES.md
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                          |
| ---- | ---------- | ------------------------------ |
| v0.1 | 2026-07-13 | P3-00 Checklist 구현 작업 단위 분리 초안 |

---

## 0. 작업 원칙

```text
한 작업 = 한 커밋 (작업 범위 하나만).
매 작업은 돌아가는 상태로 끝난다 (check/test 통과).
문서 / 코드 / migration / DB 운영 / 배포를 한 작업에 섞지 않는다.
migration 은 P3-02 에서만, 별도 승인 후 리허설 DB(gimpo365os_rehearsal)에서 적용.
모델 단계(P3-02)와 selector/view 단계(P3-03 이후)를 합치지 않는다.
Notice / Inventory 기능을 깨지 않는다. inventory 코드는 건드리지 않는다.
모호하면 추측하지 않고 다빈에게 질문한다.
```

작업 전/후 확인은 Notice(NOTICE_TASKS §0)와 동일: `.env` POSTGRES_DB=gimpo365os_rehearsal 확인,
`python manage.py check / test`, `git status --ignored`.

---

## 1. 작업 단위 개요

```text
P3-00  Checklist 큰그림 + 문서 설계                     [문서]  ← 현재 작업
P3-01  checklist 앱 뼈대 생성 + /checklists/ placeholder 이관   [코드]
P3-02  3모델 생성 및 migration                          [코드+migration/승인]
P3-03  오늘의 체크리스트 조회 (내 부서 daily, selector)      [코드]
P3-04  완료 / 취소 처리                                  [코드]
P3-05  TEAM_LEADER 이상 누락 현황                         [코드]
P3-06  OS 홈 / sidebar 실사용 진입                        [코드]
P3-07  전체 QA 및 Phase 3 마감                            [QA/문서]
P3-08  배포 후보 점검                                    [운영 점검]
```

Phase 3는 Notice보다 모델·selector가 복잡하므로 단계를 억지로 합치지 않는다.

---

## P3-00 Checklist 큰그림 + 문서 설계  [문서]

```text
범위: docs/modules/checklist/ 3종(PRODUCT_SPEC / TECH_SPEC / TASKS) 생성.
확정: 부서 단위 운영, 3모델 구조, frequency(daily/weekly/monthly, daily 우선),
      KST localdate, 완료자/완료시각, 승인 없음, 마감 양식/첨부 없음, 개인 담당자 없음,
      Django admin 초기 설정, 누락 현황(TEAM_LEADER 이상), 완료 취소 = is_active=False.
금지: 앱/모델/migration/admin/selector/view/template, placeholder 제거, OS 홈·sidebar·기존 OS 문서 수정.
완료: 문서 3종 + python manage.py check 통과 + working tree clean.
커밋: docs: add checklist module specs
```

---

## P3-01 checklist 앱 뼈대 + placeholder 이관  [코드]

```text
범위:
- checklist Django 앱 생성, INSTALLED_APPS 등록("checklist").
- /checklists/ 를 core placeholder(checklist_placeholder) → checklist 앱으로 이관
  (config/urls.py include, core/urls.py 해당 라우트 제거; Notice P2-01 방식).
- 임시 오늘 화면 또는 최소 today view (빈 목록이라도 200).
주의:
- 다른 placeholder(manuals/requests/schedules)는 유지.
- 모델 없음 → migration 없음 목표.
- OS 홈/sidebar 실사용 노출은 P3-06 에서(여기서는 라우트 이관까지만).
완료: 로그인 후 /checklists/ 가 checklist 앱 화면으로 응답, check/test 통과, migration 없음.
커밋: feature: scaffold checklist app and replace placeholder route
```

---

## P3-02 3모델 생성 및 migration  [코드 + migration, 승인 필요]

```text
이미 확정된 설계(P3-00):
- 모델 3개: ChecklistItem / DepartmentChecklistItem / ChecklistRecord
- OperationalBaseModel 상속
- frequency 필드 포함(daily/weekly/monthly), daily 로직 우선
- UniqueConstraint(item, department) / (department_item, date)
- FK on_delete: item·department·department_item = PROTECT, completed_by = SET_NULL
- 승인 기능 없음 / 마감 양식·첨부 없음 / 개인 담당자 필드 없음
범위:
- 3모델 정의 + admin 최소 등록(CHECKLIST_TECH_SPEC §16).
- makemigrations checklist → 리허설 DB migrate.
- 제약조건·KST 날짜(timezone.localdate) 기준 테스트.
migration 성격: 신규 테이블 3개 + FK + UniqueConstraint (additive, reversible). 파괴적 변경 없음.
승인: 다빈 명시적 승인 후, 리허설 DB 에서만 적용(OS_DB_OPERATIONS §6). 운영 DB 금지.
완료: 리허설 migrate 성공, check/test 통과, checklist 외 앱 migration 없음.
커밋: feature: add checklist models (migration은 별도 승인 후 리허설 적용)
```

---

## P3-03 오늘의 체크리스트 조회  [코드]

```text
범위:
- checklist/selectors.py: get_today_checklist_items(user, date=None)
  (활성 daily 항목 × 활성 부서 배정 × 사용자 department × 오늘 완료 여부)
- TodayChecklistView (LoginRequiredMixin) + template.
- 정렬: sort_order, title. department 없는 사용자 → 빈 목록.
- 완료/미완료 표시(활성 ChecklistRecord 존재 여부). 완료 버튼 UI 는 P3-04 에서 동작 연결.
- selector 테스트(daily 한정, 비활성 제외, 무소속 빈 목록).
완료: 내 부서 오늘 항목 조회 가능, check/test 통과, migration 없음.
커밋: feature: add today checklist view
```

---

## P3-04 완료 / 취소 처리  [코드]

```text
선행 결정(P3-04 전): MANAGER/ADMIN 완료 대행 예외 허용 여부(기본 불허).
범위:
- complete/uncomplete (POST, CSRF). completed_by=request.user, completed_at 서버측.
- 완료 = (department_item, date) 레코드 생성/재활성. 취소 = is_active=False. 재완료 = 재활성 + completed_by/at 갱신.
- 부서 일치 검증(타 부서 완료 차단). 승인/반려 없음.
- 상태 전이는 services 로 감싸는 방향 검토(중복 레코드 방지, UniqueConstraint 병행).
- 완료/취소/재완료/타부서 차단 테스트.
완료: 수행자가 완료/취소 가능, 하루 1레코드 보장, check/test 통과, migration 없음.
커밋: feature: add checklist complete and uncomplete
```

---

## P3-05 TEAM_LEADER 이상 누락 현황  [코드]

```text
범위:
- get_checklist_missing_status(user, date=None): TEAM_LEADER=본인 부서 / MANAGER·ADMIN=전체.
- ChecklistStatusView (TEAM_LEADER 이상; STAFF 403). 권한은 has_role_at_least(Role.TEAM_LEADER)
  또는 accounts.mixins 에 TeamLeaderRequiredMixin 신설(결정).
- 승인 기능 없음(누락 확인만).
- 권한별 접근·범위 테스트.
완료: 누락 현황 표시, 권한별 접근 테스트 통과, check/test 통과, migration 없음.
커밋: feature: add checklist missing status view
```

---

## P3-06 OS 홈 / sidebar 실사용 진입  [코드]

```text
범위:
- OS 홈 체크리스트 카드 준비 중 해제 → 실사용(오늘 체크리스트) 진입 (Notice P2-06 방식).
- sidebar 에 체크리스트 메뉴 추가(namespace=='checklist' active).
- 나머지 준비 중 모듈(SOP/요청/근태)은 유지.
완료: OS 홈/sidebar 에서 체크리스트 진입 가능, 다른 준비중 유지, check/test 통과.
커밋: feature: expose checklist as active module
```

---

## P3-07 전체 QA 및 Phase 3 마감  [QA/문서]

```text
범위:
- 전체 QA(오늘 조회/완료·취소/누락 현황/권한/KST 날짜) + Notice·Inventory 회귀.
- OS_TASKS.md Phase 3 완료 반영, Checklist 문서 상태 갱신, 운영 기준 정리.
완료: QA 통과 기록, 문서 마감, working tree clean.
커밋: docs: close checklist phase 3
```

---

## P3-08 배포 후보 점검  [운영 점검]

```text
범위(코드 아님, 점검·문서 중심):
- 내부망 접속(원내 바인딩/방화벽), 계정/부서/권한 점검.
- 백업/복구 절차(OS_DB_OPERATIONS), 리허설→운영 반영 절차(OS_OPERATIONS_SETUP) 확인.
- 리허설 잔여 테스트 데이터 정리 여부(다빈 확인).
전제: MVP 컷라인(Inventory + Notice + Checklist) 도달 → 배포 후보 상태.
```

---

## 2. 승인·리스크 게이트 요약

```text
migration(P3-02): 다빈 명시적 승인 + 리허설 DB 한정. 신규 테이블 3개(additive).
완료 대행 예외(P3-04): 기본 불허, 필요 시 P3-04 전 별도 결정.
누락 현황 권한 mixin(P3-05): TeamLeaderRequiredMixin 신설 vs 뷰 내 검사 — 결정 후 진행.
운영 반영: 리허설 검증 → 백업 → 승인 후. Claude Code 임의 반영 금지.
inventory 코드: 이번 Phase 내내 수정 금지.
```
