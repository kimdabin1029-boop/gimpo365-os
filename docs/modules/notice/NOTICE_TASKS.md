# NOTICE_TASKS.md

# 김포365OS Notice Module 작업 목록

## 문서 버전

```text
문서명: NOTICE_TASKS.md
문서 범위: 김포365OS Module 2 — Notice 구현 작업 단위 분리
문서 상태: Notice v1 구현 완료 (Phase 2 마감, P2-07)
전제 문서: NOTICE_PRODUCT_SPEC.md, NOTICE_TECH_SPEC.md, OS_WORKING_RULES.md
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                            |
| ---- | ---------- | ------------------------------------------------ |
| v0.2 | 2026-07-13 | Notice v1 구현 완료 반영(P2-01~P2-07 [x]). P2-09 Attachment Gate 보류 유지. 실제 실행 순서 매핑 주석 추가 |
| v0.1 | 2026-07-11 | P2-00 Notice 구현 작업 단위 분리 (첨부 v1.1 게이트, OperationalBaseModel P2-01.5 분리) |

---

## 완료 상태 (P2-07 마감)

```text
[x] P2-00    Notice 문서 설계
[x] P2-01    notice 앱 뼈대 + placeholder 전환
[x] P2-01.5  OperationalBaseModel 신설 (abstract, migration 없음)
[x] P2-01.6  OperationalBaseModel 문서 정합성 정리 (created_by/updated_by = SET_NULL)
[x] P2-02    Notice 모델 + migration (리허설 DB 적용)
[x] P2-03    목록/상세 조회 + selector 접근제어 (권한 없는 상세 404)
[x] P2-04    등록/수정 + MANAGER 권한 + created_by/updated_by/published_at 서버측 처리
[x] P2-05    폼 한글화·위젯·대상 부서(활성) 정리 + ManagerRequiredMixin → accounts.mixins
[x] P2-06    OS 홈 카드 실사용 전환 + sidebar 공지사항 메뉴(active)
[x] P2-07    Notice v1 QA + Phase 2 문서 마감
[ ] P2-09    Notice v1.1 Attachment Gate — 보류(구현 아님). Checklist 정착 이후 또는 로드맵 가드 개정 후 검토.
```

실제 실행 매핑 주석: 아래 §1 개요의 P2-05/P2-06 항목은 지시서 재편성으로 P2-04(등록/수정+권한),
P2-05(권한/폼/화면 정리), P2-06(실사용 진입)으로 실행되었다. 기능 범위는 동일하게 완료되었다.

---

## 0. 작업 원칙

각 작업은 다음 원칙을 따른다(OS_WORKING_RULES §6·§7).

```text
한 작업 = 한 커밋 (작업 범위 하나만)
매 작업은 돌아가는 상태로 끝난다 (check/test 통과).
문서 / 코드 / migration / DB 운영 / 배포를 한 작업에 섞지 않는다.
migration 은 별도 승인 후 리허설 DB(gimpo365os_rehearsal)에서만 적용한다.
OperationalBaseModel 은 Notice 모델보다 먼저 정리한다.
Inventory 핵심 로직·service 계층을 수정하거나 우회하지 않는다.
모호하면 추측하지 않고 다빈에게 질문한다.
```

각 작업 착수 전:

```text
git status / git branch --show-current
Select-String -Path .env -Pattern "POSTGRES_DB"  → gimpo365os_rehearsal 확인
python manage.py check
```

각 작업 종료 후:

```text
python manage.py check / test
git status / git status --ignored (민감파일 추적 여부)
```

---

## 1. 작업 단위 개요

```text
P2-00    Notice 문서 설계                          [문서]   (완료 — 상태는 위 "완료 상태" 참조)
P2-01    notice 앱 뼈대 생성 및 placeholder 전환 준비   [코드]
P2-01.5  OperationalBaseModel 신설                  [코드-only, migration 없음]
P2-02    Notice 모델 설계 및 migration               [코드+migration/승인]
P2-03    목록 / 상세 조회                            [코드]
P2-04    등록 / 수정 form                            [코드]
P2-05    권한 적용 및 부서 대상 접근제어                [코드]
P2-06    OS 홈 / sidebar 메뉴 연결                    [코드]
P2-07    check / test / smoke QA                     [QA]
P2-08    운영 문서 / Notice 기준 정리                  [문서]
P2-09    Notice v1.1 Attachment Gate 검토             [검토 게이트 — 구현 아님]
```

---

## P2-00 Notice 문서 설계  [문서]

```text
범위: docs/modules/notice/ 하위 문서 생성 (PRODUCT_SPEC / TECH_SPEC / TASKS)
산출: Notice v1 MVP 범위·권한·부서 접근제어·null department 처리 기준,
      status/is_active/is_important/category/reference_url 기준,
      OperationalBaseModel 상속 기준, placeholder 전환 계획,
      첨부 v1 제외 + v1.1 게이트 분리, 기존 OS 문서 충돌 기록.
금지: 앱/모델/migration/URL/view/template/DB/Inventory 수정, settings 변경,
      OperationalBaseModel 구현, core placeholder 제거.
완료: 문서 생성 + python manage.py check 통과 + working tree(커밋 후) clean.
커밋: docs: add notice module specs
```

---

## P2-01 notice 앱 뼈대 생성 및 placeholder 전환 준비  [코드]

```text
범위:
- notice Django 앱 생성 (models 비어있음 또는 최소).
- INSTALLED_APPS 에 "notice" 등록.
- config/urls.py 에 notice URL include, core/urls.py 의 notices/ placeholder 라우트 교체.
- OS 홈/sidebar 의 notice 링크 name 을 notice:list 로 교체.
전제: 이 시점에 목록 view 는 최소 동작(빈 목록)이라도 200 응답.
주의:
- core 의 다른 placeholder(checklists/manuals/requests/schedules)는 건드리지 않는다.
- migration 없음(모델 없음) 목표. 앱 생성만으로 migration 발생하지 않게 한다.
완료: 로그인 후 /notices/ 가 notice 앱 화면으로 응답, check/test 통과.
커밋: feature: add notice app skeleton and replace placeholder route
```

---

## P2-01.5 OperationalBaseModel 신설  [코드-only, migration 없음]

```text
범위:
- core 에 OperationalBaseModel(abstract=True) 신설.
- 공통 필드: created_at, updated_at, created_by(SET_NULL,null), updated_by(SET_NULL,null), is_active.
성격: 코드-only 작업. abstract base model 이므로 DB 테이블 생성 없음.
검증:
- python manage.py makemigrations --check --dry-run → 변경 미감지여야 함(테이블 없음).
  변경이 감지되면(abstract 아님 등) 멈추고 재검토.
주의: 이 단계는 Notice 모델보다 먼저. migration 없음.
완료: OperationalBaseModel 정의, check 통과, migration 파일 미생성.
커밋: feature: add core OperationalBaseModel (abstract, no migration)
```

---

## P2-02 Notice 모델 설계 및 migration  [코드 + migration, 승인 필요]

```text
범위:
- Notice 모델(OperationalBaseModel 상속) 정의 (NOTICE_TECH_SPEC §5 초안 기준).
  title, content, target_type(all/department), target_department(FK, null),
  status(draft/published), is_important, category(choices), reference_url, published_at.
- target_type / target_department 정합성 검증(모델/clean).
- makemigrations → 리허설 DB 에 migrate.
migration 성격: 새 테이블 추가 + User FK 추가(OperationalBaseModel created_by/updated_by).
                additive, reversible. 파괴적 변경 없음.
승인: migration 은 다빈 명시적 승인 후, 리허설 DB 에서만 적용(OS_DB_OPERATIONS §6).
주의: 운영 DB(gimpo365_inventory) 연결/적용 금지. .env POSTGRES_DB 재확인.
완료: 리허설 DB migrate 성공, check/test 통과.
커밋: feature: add notice model (migration은 별도 승인 후 리허설 적용)
```

---

## P2-03 목록 / 상세 조회  [코드]

```text
범위:
- NoticeListView / NoticeDetailView (LoginRequiredMixin).
- 목록: 제목/대상(전체·부서)/중요뱃지/category/작성일 표시, 최신순.
- 상세: 본문 + reference_url 링크.
- 접근 필터는 P2-05 에서 강화하되, 최소한 published+is_active 노출은 이 단계 반영 가능.
- template: notice_list.html / notice_detail.html (공통 base 상속).
- 첫 CBV 는 클래스/메서드 역할 주석을 풀어서 작성(표준 패턴 학습용).
완료: 게시 공지 목록/상세 조회 가능, check/test 통과.
커밋: feature: add notice list and detail views
```

---

## P2-04 등록 / 수정 form  [코드]

```text
범위:
- NoticeCreateView / NoticeUpdateView + NoticeForm.
- 필드: title, content, target_type, target_department, status, is_important, category, reference_url.
- target_type=department 검증(대상 부서 필수), all 이면 target_department 비움.
- created_by/updated_by/published_at 서버측 설정(사용자 입력 신뢰 금지).
- notice_form.html (등록/수정 공용).
- 최소한 비-MANAGER 접근 차단은 이 단계에서 임시 반영 가능(정식 권한은 P2-05).
완료: MANAGER 가 공지 등록/수정, 목록/상세 반영 확인, check/test 통과.
커밋: feature: add notice create and update forms
```

---

## P2-05 권한 적용 및 부서 대상 접근제어  [코드]

```text
범위:
- 작성/수정: MANAGER 이상(is_manager_or_above) 공통 Mixin 으로 통일.
- MANAGER Mixin 위치(승격 옵션 A vs Notice 로컬 옵션 B) 확정·반영.
- 조회 접근제어(NOTICE_TECH_SPEC §8·§9):
    전체 공지: 전원 / 부서 공지: 해당 부서 + MANAGER·ADMIN
    department 없는 직원: 전체 공지만
    draft: 작성자/MANAGER 만
    권한 없는 pk 상세: 404
- 쿼리는 user.department_id 존재를 먼저 확인(None 단독 조건 금지).
- 권한/접근제어 테스트 작성.
주의: Inventory 의 ManagerRequiredMixin 승격 시 Inventory 회귀 확인(별도 주의).
완료: 권한별·접근제어 테스트 통과, check/test 통과.
커밋: feature: apply notice permissions and department access control
```

---

## P2-06 OS 홈 / sidebar 메뉴 연결  [코드]

```text
범위:
- OS 홈 카드/sidebar 의 "공지사항"을 준비중 → 실제 notice:list 진입으로 전환.
- 준비 중 표시 제거(공지사항 한정). 다른 준비중 모듈 표시는 유지.
완료: OS 홈/sidebar 에서 공지사항 진입 가능, 다른 모듈 placeholder 정상, check/test 통과.
커밋: feature: link notice module in os home and sidebar
```

---

## P2-07 check / test / smoke QA  [QA]

```text
범위:
- python manage.py check / test 전체 통과 확인.
- OS 공통 smoke QA: 로그인 / OS 홈 / Inventory 진입 / 준비중 placeholder /
  권한별 메뉴 노출 / 리허설 DB 연결.
- Notice smoke: 목록/상세/등록/수정/게시상태/부서 접근제어/404/권한별 접근.
- Inventory 회귀: 재고현황·입고·출고 주요 화면 접근, 오류 화면 없음.
완료: 모든 항목 이상 없음 기록.
커밋: (코드 변경 있으면) chore: notice qa fixups / (없으면 커밋 없음)
```

---

## P2-08 운영 문서 / Notice 기준 정리  [문서]

```text
범위:
- Notice 운영 기준·권한·접근제어 요약 정리(운영 안내용).
- 필요 시 NOTICE_MANUAL_QA_CHECKLIST.md 신설 검토.
- (첨부 관련 OS_DB_OPERATIONS media 백업 보강은 v1 범위 아님 → P2-09 게이트에서 다룸)
주의: 문서 작업과 코드 작업을 섞지 않는다.
완료: Notice 운영 기준 문서화.
커밋: docs: add notice operations notes
```

---

## P2-09 Notice v1.1 Attachment Gate 검토  [검토 게이트 — 구현 아님]

```text
성격: 구현 작업이 아니라 검토 게이트다.
범위:
- 첨부파일 도입 필요성/리스크 재검토(JANDI 한계 보완 vs 로드맵 가드).
- 조기 도입 시 OS_ROADMAP 8.1 가드 개정 필요 여부 판단.
- 도입 결정 시 필요한 설계(NOTICE_PRODUCT_SPEC §11, NOTICE_TECH_SPEC §15):
    NoticeAttachment 모델 / 크기·확장자 제한 / 다운로드 권한 view /
    MEDIA_ROOT·MEDIA_URL / media 백업 정책(OS_DB_OPERATIONS 보강) /
    환자·개인정보 업로드 금지 / 부서 공지 첨부 다운로드 접근제어.
전제:
- 기본 로드맵상 Checklist 정착 이후 검토.
- 첨부 구현은 이 게이트 통과 후 별도 작업으로 진행한다.
완료: 첨부 도입 여부/시점/선행조건이 문서로 정리됨(구현 착수 아님).
커밋: docs: record notice v1.1 attachment gate decision
```

---

## 2. 승인·리스크 게이트 요약

```text
OperationalBaseModel 신설(P2-01.5): abstract=True, migration 없어야 함(dry-run 검증).
migration 적용(P2-02): 다빈 명시적 승인 + 리허설 DB 한정.
MANAGER Mixin 승격(P2-05): Inventory 회귀 리스크 → 별도 주의/확인.
첨부(P2-09): 검토 게이트. 구현은 Checklist 정착 후 또는 로드맵 개정 후 별도 작업.
운영 반영: 리허설 검증 → 백업 → 승인 후. Claude Code 임의 반영 금지.
```
