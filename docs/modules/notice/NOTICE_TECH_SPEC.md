# NOTICE_TECH_SPEC.md

# 김포365OS Notice Module 기술 명세서

## 문서 버전

```text
문서명: NOTICE_TECH_SPEC.md
문서 범위: 김포365OS Module 2 — Notice 기술 구현 기준 (설계)
문서 상태: P2-00 설계 초안 (코드 미작성)
전제 문서: OS_TECH_SPEC.md, OS_ARCHITECTURE.md, OS_WORKING_RULES.md, NOTICE_PRODUCT_SPEC.md
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                      |
| ---- | ---------- | ------------------------------------------ |
| v0.1 | 2026-07-11 | P2-00 Notice v1 기술 설계 초안 (첨부 v1 제외, OperationalBaseModel 상속 기준 반영) |

---

## 0. 문서 성격

이 문서는 Notice Module을 "어떻게" 만들지 정의하는 기술 설계 문서다.

**이번 단계(P2-00)에서는 실제 코드·앱·모델·migration을 만들지 않는다.**
아래 코드 블록은 모두 설계 초안이며, 실제 필드명/옵션은 구현 단계에서 코드 스타일에 맞춰 확정한다.

이 문서는 OS_TECH_SPEC.md의 공통 CRUD 표준(§13), 공통 권한 Mixin(§14), Department+role(§16), abstract base model(§17), Notice 기술 기준(§24)을 상속한다.

---

## 1. 앱 구조 후보

```text
권장 앱 이름: notice  (신규 Django 앱)
위치: 프로젝트 루트의 notice/  (docs/modules/notice/ 는 문서 전용, 코드 금지)
INSTALLED_APPS 등록: "notice" 를 로컬 앱(core, accounts, inventory) 뒤에 추가
```

확인된 코드 사실:

```text
INSTALLED_APPS = [..., "core", "accounts", "inventory"]  (config/settings.py) — 아직 notice 없음
core/models.py 에는 Department 만 있음. OperationalBaseModel 미구현.
```

앱 구성 파일(구현 단계 산출물):

```text
notice/
├─ __init__.py
├─ apps.py
├─ models.py        (Notice, OperationalBaseModel 상속)
├─ forms.py         (NoticeForm)
├─ views.py         (CBV 4종)
├─ urls.py          (app_name = "notice")
├─ admin.py         (선택)
├─ migrations/
└─ tests.py
templates/notice/   (목록/상세/폼 template)
```

---

## 2. URL 구조

```text
/notices/            → NoticeListView    (name: list)
/notices/<pk>/       → NoticeDetailView  (name: detail)
/notices/new/        → NoticeCreateView  (name: create)
/notices/<pk>/edit/  → NoticeUpdateView  (name: update)
```

`app_name = "notice"` 로 namespace 를 둔다(`notice:list` 등).

---

## 3. View 구조

Django 제네릭 CBV를 기본 표준으로 한다(OS_TECH_SPEC §13).

```text
NoticeListView    (LoginRequiredMixin, ListView)
NoticeDetailView  (LoginRequiredMixin, DetailView)
NoticeCreateView  (MANAGER 권한 Mixin, CreateView)
NoticeUpdateView  (MANAGER 권한 Mixin, UpdateView)
```

원칙:

```text
삭제 view(DeleteView)는 v1에서 만들지 않는다(status/is_active 로 대체).
목록/상세는 접근 가능 조건(§8)으로 필터링한다.
Notice 첫 CBV 구현은 학습·검증용 표준 패턴이므로,
  각 클래스/주요 메서드 역할을 주석으로 풀어서 작성한다(OS_TECH_SPEC §24).
이 검증된 패턴을 SOP/Manual·Request 가 모델/template/form/권한대상/URL이름/메뉴위치만 교체해 재사용한다.
```

---

## 4. Template 구조

```text
templates/notice/
├─ notice_list.html      (목록: 제목/대상/중요뱃지/category/작성일)
├─ notice_detail.html    (상세: 본문 + reference_url 링크)
└─ notice_form.html      (등록/수정 공용)
```

원칙:

```text
공통 base.html 을 상속한다(OS 공통 UI).
template 에는 표현 로직만 둔다.
reference_url 은 텍스트 링크로만 표시(미리보기/임베드/썸네일 없음).
Inventory 화면이 깨지지 않도록 공통 base 변경은 하지 않는다.
```

---

## 5. Model 초안 (설계, 미구현)

> 아래는 설계 초안이다. 실제 필드명/옵션/제약은 구현 단계에서 확정한다.

```text
Notice(OperationalBaseModel 상속)
- title             CharField
- content           TextField          (OS_TECH_SPEC §24 의 body 와 명칭 정합 필요)
- target_type       choices: all / department
- target_department FK core.Department, null=True, blank=True
                    (target_type=department 일 때만 사용, form/model 에서 검증 — §8)
- status            choices: draft / published
- is_important      BooleanField(default=False)   (중요 뱃지용, 상단 고정 아님)
- category          choices 상수 (예: general / operation / education / admin)
- reference_url     URLField(blank=True)          (선택 입력, 대표 외부 링크 1개)
- published_at      DateTimeField(null=True, blank=True)

OperationalBaseModel 에서 상속(반복 선언 금지):
- created_at, updated_at, created_by, updated_by, is_active
```

주의:

```text
created_at / updated_at / created_by / updated_by / is_active 를
Notice 에 직접 반복 선언하지 않는다. OperationalBaseModel 에서 제공한다(§7, §10).
category 에 important 를 넣지 않는다. 중요 여부는 is_important 로만 표현한다.
status(게시 상태)와 is_active(논리 삭제/비활성)의 의미를 섞지 않는다(§11).
```

Timezone: `published_at` 등 시각은 `USE_TZ=True`, `TIME_ZONE="Asia/Seoul"`(현재 settings 확인됨) 기준.

---

## 6. Form 초안

```text
NoticeForm (ModelForm)
- 필드: title, content, target_type, target_department, status, is_important, category, reference_url
- 검증:
    target_type=all        → target_department 는 null 이어야 함
    target_type=department  → target_department 필수 (§8)
- reference_url: URLField 기본 검증 사용(빈 값 허용)
- created_by / updated_by / published_at 은 view 에서 서버측 설정(사용자 입력 신뢰 금지)
```

---

## 7. 권한 기준

기존 Inventory에서 검증된 role 기반 권한을 재사용한다(OS_ARCHITECTURE §14, OS_TECH_SPEC §16).

확인된 코드 자산:

```text
accounts/permissions.py
- has_role_at_least(user, role)
- is_manager_or_above(user)   ← Notice 작성/수정 권한 판정
- ROLE_RANK (STAFF10 < TEAM_LEADER20 < MANAGER30 < ADMIN40)

inventory/views.py
- ManagerRequiredMixin(LoginRequiredMixin): MANAGER 이상만, 비로그인→로그인 redirect, 그 외 403
  (단, 현재 inventory 앱 로컬. Notice 재사용 방식은 아래 결정 필요)
```

권한 적용:

```text
조회(List/Detail): LoginRequiredMixin + 접근 가능 조건 필터(§8)
작성/수정(Create/Update): MANAGER 이상
  판정은 is_manager_or_above() 를 쓰는 공통 Mixin 으로 처리(모듈별 중복 로직 금지).
```

[결정 필요] MANAGER 권한 Mixin 위치:

```text
옵션 A(권장): inventory 의 ManagerRequiredMixin 을 accounts 또는 core 공통 위치로 승격해
             Notice·SOP·Request 가 공유. (Inventory 동작 회귀 확인 필요, 별도 작업 단위)
옵션 B: Notice 에 동일 로직 Mixin 을 두되 is_manager_or_above() 를 재사용.
→ OS_TECH_SPEC §14 "공통 권한 Mixin" 방향에 맞게 P2-05 에서 확정.
```

---

## 8. 부서 대상 공지 접근제어

부서 대상 공지는 조회 범위 제한이 있는 대상 공지다(단순 라벨 아님).

목록(List) 접근 가능 조건:

```text
일반 직원(STAFF/TEAM_LEADER):
- published + is_active=True 공지만
- 전체 공지(target_type=all) 는 전원 조회
- 부서 대상 공지(target_type=department)는 user.department_id 가 있을 때 해당 부서 공지만
- department 가 없는 일반 직원은 전체 공지만
- (선택) 작성자는 본인이 작성한 draft 조회 가능

MANAGER / ADMIN:
- draft / published 전체 조회 가능 (department 유무 무관)
```

상세(Detail) 접근:

```text
목록과 동일한 접근 가능 조건으로만 조회한다.
권한 없는 pk 접근은 404 를 권장한다(§ 아래 별도 절 참고).
```

작성/수정(Create/Update):

```text
MANAGER 이상.
```

---

## 9. null department 사용자 처리

Phase 1.5 결정에 따라 `User.department` 는 nullable 구조를 유지한다.
따라서 부서 없는 사용자의 조회 조건을 명확히 한다.

```text
department 가 없는 일반 직원은 전체 공지만 본다.
department 가 없는 사용자는 부서 대상 공지를 조회할 수 없다.
MANAGER / ADMIN 은 department 유무와 관계없이 전체 공지 관리 범위를 가진다.
```

쿼리 설계 패턴(초안):

```python
from django.db.models import Q

q = Q(target_type="all")

if user.department_id:
    q |= Q(
        target_type="department",
        target_department_id=user.department_id,
    )

# 일반 직원 목록: published + is_active + q
# MANAGER/ADMIN: 위 q 제한 없이 전체(draft 포함) 조회
```

주의:

```text
Q(target_department=user.department) 를 단독으로 쓰지 않는다.
user.department 가 None 이면 target_department IS NULL 조건으로 번역되어
의도치 않은 공지가 노출될 수 있다. 반드시 user.department_id 존재를 먼저 확인한다.
```

---

## 10. OperationalBaseModel 상속 기준

확인된 현재 상태:

```text
OS_TECH_SPEC §17 은 core 의 공통 abstract base model(OperationalBaseModel 등)을 제안한다.
현재 core/models.py 에는 Department 만 있고 OperationalBaseModel 은 아직 구현되어 있지 않다.
```

기준:

```text
Notice 는 OperationalBaseModel 상속을 기본 방향으로 한다.
core 에 OperationalBaseModel 이 없으므로, Notice 구현 전에 먼저 신설한다(P2-01.5).
OperationalBaseModel 은 abstract base model(abstract = True)로 설계한다.
공통 필드: created_at / updated_at / created_by / updated_by / is_active
  (created_by=PROTECT, updated_by=SET_NULL 등 User FK 는 CASCADE 금지 — OS_TECH_SPEC §20)
```

migration 성격 (중요):

```text
abstract base model 자체는 별도 DB 테이블을 만들지 않는다.
→ OperationalBaseModel 신설(P2-01.5) 자체로는 migration 이 발생하지 않아야 한다.
→ migration 승인 게이트는 Notice 구체 모델을 생성하는 P2-02 에서 적용한다.
만약 P2-01.5 에서 makemigrations --check --dry-run 에 변경이 감지되면
  (예: abstract 가 아니거나 기존 모델에 상속을 붙여 필드가 바뀐 경우) 멈추고 재검토한다.
```

---

## 11. status / is_active / is_important / category / reference_url 기준

### 11.1 status

```text
status = draft / published  (하나의 상태 체계만 사용)
draft:
- 일반 직원 목록에 노출하지 않음
- 작성자 또는 MANAGER 이상 조회 가능
published:
- 대상 범위(§8)에 따라 직원에게 노출
```

### 11.2 is_active (OperationalBaseModel)

```text
status 와 의미를 섞지 않는다.
status    = 게시 상태
is_active = 논리적 삭제 또는 운영상 비활성
일반 직원 목록 기본 노출 조건: published + is_active=True
```

### 11.3 is_important

```text
중요 뱃지 표시용 boolean (default=False)
상단 고정 정렬 기능은 없음(v1 제외)
```

### 11.4 category

```text
자유 입력이 아니라 choices 상수로 시작한다(OS_TECH_SPEC §23).
category 는 공지의 분류다. 중요 여부는 is_important 로만 표현한다.
category 에 important 를 넣지 않는다.
예시 후보: general / operation / education / admin
실제 choice 이름은 OS_TECH_SPEC 과 코드 스타일에 맞춰 확정한다.
```

### 11.5 reference_url

```text
선택 입력 URLField 1개.
링크 미리보기/임베드/썸네일 없음. 서버가 대상 URL 을 fetch 하지 않음.
본문에 일반 URL 텍스트 작성 허용.
```

---

## 12. placeholder → notice 앱 전환 계획

현재 `/notices/` 는 Phase 1 placeholder 로 `core` 에 연결되어 있다.

확인된 현재 상태:

```text
config/urls.py:  path("", include("core.urls"))
core/urls.py:    path("notices/",
                     ModulePlaceholderView.as_view(extra_context={"module_name": "공지사항"}),
                     name="notice_placeholder")
core/views.py:   ModulePlaceholderView (LoginRequiredMixin, TemplateView)
```

전환 계획(P2-01에서 실행, 이번 P2-00에서는 계획만):

```text
1. config/urls.py 에 notice 앱 URL include 추가.
   권장: path("notices/", include("notice.urls"))  추가 후,
         core/urls.py 의 notices/ placeholder 행 제거.
   → URL include 위치를 한 곳으로 통일해 중복 매칭을 피한다.
2. sidebar/OS 홈에서 공지사항 링크가 가리키는 URL name 교체.
   - 기존: core:notice_placeholder (또는 실제 사용처 name)
   - 변경: notice:list
   - 구현 전, 템플릿에서 notice_placeholder 참조 위치를 grep 으로 전부 찾아 교체.
3. placeholder 제거로 인한 reverse() 실패가 없는지 check/test 로 확인.
```

주의:

```text
core 의 다른 placeholder(checklists/manuals/requests/schedules)는 건드리지 않는다.
notice placeholder 관련 라우트만 교체한다(작업 단위 분리).
이번 P2-00에서는 core placeholder 를 제거하지 않는다(지시 §16).
```

---

## 13. migration 계획

```text
P2-01:   앱 뼈대 생성(모델 없음) — migration 없음 목표.
P2-01.5: OperationalBaseModel 신설 — abstract=True, migration 없음(테이블 미생성).
          makemigrations --check --dry-run 에서 변경 미감지 확인.
P2-02:   Notice 모델(OperationalBaseModel 상속) → 신규 테이블 추가 migration (additive).
          - 새 테이블 추가 + User FK 추가(additive, reversible). 파괴적 변경 없음.
          - 별도 승인 후 리허설 DB(gimpo365os_rehearsal)에서만 적용(운영 DB 격리 절대 규칙).
          - 절차는 OS_DB_OPERATIONS §6 을 따른다.
```

---

## 14. 테스트 계획

```text
python manage.py check / test 를 각 작업 후 실행.
권한별 접근 테스트:
  - STAFF/TEAM_LEADER: 목록/상세 접근 O(공개 범위), 작성/수정 접근 시 차단
  - MANAGER/ADMIN: 작성/수정 O, draft 포함 전체 조회 O
  - 비로그인: 로그인으로 redirect
접근제어 테스트:
  - 전체 공지: 전원 조회
  - 부서 대상 공지: 해당 부서 직원만 조회, 타 부서/무소속 직원 비노출
  - department 없는 직원: 전체 공지만 조회
  - draft: 일반 직원 목록 비노출, 작성자/MANAGER 조회
  - 권한 없는 pk 상세 접근: 404
정합성 테스트: target_type=department 인데 target_department 비면 form/model 오류.
Inventory 회귀: 기존 inventory 화면 접근·주요 기능 정상.
```

---

## 15. 첨부파일 v1.1 게이트 (기술 메모)

첨부파일은 v1 제외. 향후 구현 시 필요한 기술 요소(기록용):

```text
NoticeAttachment 모델 (Notice FK)
파일 크기 제한 / 확장자 화이트리스트
다운로드 권한 검사 view — MEDIA_URL 직접 링크 공개 금지, 로그인/권한 확인 view 경유
  부서 대상 공지 첨부는 그 공지를 볼 수 있는 사용자만 다운로드 가능
MEDIA_ROOT / MEDIA_URL 설정 (현재 settings 에 미설정 — STATIC 만 있음)
media 파일 백업 정책 (OS_DB_OPERATIONS 보강 필요; DB 백업만으로 media 보존 안 됨)
환자정보/개인정보 업로드 금지
확장자 검사는 파일 위장에 취약 → content-type/파일 시그니처 검증은 후순위 보강
```

이 게이트는 Checklist 정착 이후 또는 OS_ROADMAP 8.1 가드 개정 후 별도 작업으로 진행한다.

---

## 16. MVP 제외 항목 (기술)

```text
NoticeAttachment / 파일 업로드·다운로드 view (→ v1.1)
DeleteView (물리 삭제)
댓글 / 읽음확인 / 확인률 / 알림 model·view
예약 게시(published_at 자동 스케줄러) / 만료 자동 숨김
상단 고정 정렬
리치 에디터 / HTML sanitize / 본문 이미지 / 이미지 미리보기
드래그앤드롭 업로드 / 첨부 버전관리
서버측 외부 URL fetch / 링크 미리보기
복잡한 검색
```

---

## 17. 구현 단계 확정 대상 요약

```text
[확정필요] 본문 필드명 content vs body (OS_TECH_SPEC §24 정합)
[확정필요] category choice 최종 이름 세트
[확정필요] MANAGER Mixin 승격(옵션 A) vs Notice 로컬(옵션 B)
[확정필요] 작성자 본인 draft 조회 허용 범위
[선행작업] P2-01.5 OperationalBaseModel 신설(abstract, migration 없음)
[승인게이트] P2-02 Notice 테이블 migration (리허설 한정, 별도 승인)
```
