# OS_TECH_SPEC.md

# 김포365OS 기술 명세서

## 문서 버전

```text
문서명: OS_TECH_SPEC.md
문서 버전: v0.2
최종 수정일: 2026-07-08
문서 범위: 김포365OS 기술 구현 기준, Django 앱 구조, 공통 CRUD 패턴, URL, template, 권한, DB, migration, 테스트 원칙
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                                                                                                                                                                         |
| ---- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0.2 | 2026-07-08 | 공통 CRUD 표준을 Django 제네릭 CBV로 확정. 공통 abstract base model 기준 추가. FK 삭제 정책과 User 비활성 원칙 추가. Timezone 기준 추가. 기존 Inventory 권한 구조 기반 권한 매핑 방향 추가. category choices 처리 방향 추가. 조사 의존 항목을 향후 보강 항목으로 분리 |
| v0.1 | 2026-07-08 | 김포365OS 초기 기술 명세 작성. Django 앱 구조, OS 홈, 공통 UI, placeholder, Department/Team, 권한, DB/migration, 테스트, 모듈 추가 기술 기준 정의                                                                            |

---

## 1. 문서 목적

이 문서는 김포365OS의 기술 구현 기준을 정의한다.

`OS_PRODUCT_SPEC.md`가 제품 목적과 범위를 정의하고, `OS_ARCHITECTURE.md`가 전체 구조를 정의한다면, 이 문서는 실제 Django 코드 작업 시 따라야 할 기술 기준을 정의한다.

이 문서의 목적은 다음과 같다.

```text
김포365OS의 Django 앱 구조를 정의한다.
OS 홈, 공통 UI, placeholder 구현 기준을 정의한다.
신규 운영 모듈의 공통 CRUD 구현 패턴을 정의한다.
권한, 계정, Department/Team 처리 기준을 정의한다.
DB와 migration의 기술 원칙을 정의한다.
Claude Code가 임의로 구조를 대개조하지 않도록 구현 기준을 제공한다.
```

---

## 2. 관련 문서

이 문서는 다음 문서와 함께 사용한다.

```text
CLAUDE.md
OS_WORKING_RULES.md
OS_PRODUCT_SPEC.md
OS_ARCHITECTURE.md
OS_ROADMAP.md
OS_DB_OPERATIONS.md
OS_OPERATIONS_SETUP.md
OS_TASKS.md
OS_MANUAL_QA_CHECKLIST.md
docs/modules/inventory/INVENTORY_*.md
```

문서 간 충돌 시 우선순위는 `OS_WORKING_RULES.md`를 따른다.

`CLAUDE.md`의 절대 규칙은 모든 문서보다 우선한다.

---

## 3. 기술 스택

김포365OS의 기본 기술 스택은 기존 Inventory MVP 구조를 유지한다.

```text
Backend: Django
Database: PostgreSQL
Frontend: Django Template 기반 서버 렌더링
Auth: Django 인증/권한 구조 기반
Admin: Django Admin
Environment: Windows PowerShell 기준
Local/Rehearsal Server: 8001
Production Server: 8000
```

초기 단계에서는 다음을 도입하지 않는다.

```text
SPA 프레임워크
React / Vue / Next.js
별도 API 서버
모바일 앱
복잡한 비동기 작업 큐
외부 SaaS 의존 구조
모듈별 DB 분리
```

김포365OS는 한의원 내부 운영 시스템이므로, 단순하고 유지 가능한 구조를 우선한다.

---

## 4. 현재 Django 프로젝트 구조

현재 기본 구조는 다음을 유지한다.

```text
gimpo365-os
├─ accounts/
├─ core/
├─ inventory/
├─ config/
├─ templates/
├─ static/
├─ docs/
└─ manage.py
```

각 폴더의 역할은 다음과 같다.

| 폴더           | 역할                                     |
| ------------ | -------------------------------------- |
| `config/`    | Django 프로젝트 설정, 루트 URL, settings       |
| `accounts/`  | 로그인, 사용자, 권한 관련 기능                     |
| `core/`      | OS 홈, 공통 view, placeholder, 공통 기준정보 후보 |
| `inventory/` | Inventory Module 실제 Django 앱           |
| `templates/` | 공통 및 앱별 template                       |
| `static/`    | CSS, JS, 이미지 등 정적 파일                   |
| `docs/`      | 문서 전용 폴더                               |

`inventory/` 앱은 실제 Django 앱이다.

`docs/modules/inventory/`는 문서 폴더이다.

다음 작업은 금지한다.

```text
inventory/ 앱을 docs/modules/inventory/ 아래로 이동
docs/modules/ 아래에 Django 앱 코드 생성
기존 inventory 앱 label 변경
기존 Inventory 모델을 다른 앱으로 물리 이동
```

---

## 5. 앱 역할 분리

## 5.1 `config/`

`config/`는 Django 프로젝트 설정을 담당한다.

주요 역할:

```text
settings 관리
루트 URL 연결
환경변수 로딩
앱 등록
static/media 설정
```

`config/settings.py` 또는 설정 관련 파일을 수정할 때는 `.env`와 민감정보가 Git에 포함되지 않도록 주의한다.

## 5.2 `accounts/`

`accounts/`는 사용자 계정과 권한 관련 기능을 담당한다.

주요 역할:

```text
로그인
로그아웃
사용자 권한
역할 구분
사용자 관련 공통 기능
```

초기 역할 구조는 다음을 따른다.

```text
관리자
팀장
직원
```

공용 계정과 부서 계정은 만들지 않는다.

개인 계정 원칙을 유지한다.

## 5.3 `core/`

`core/`는 김포365OS의 공통 기능을 담당한다.

초기 역할:

```text
OS 홈
공통 placeholder
공통 dashboard 후보
Department/Team 기준정보 후보
공통 view/helper
공통 권한 mixin 후보
공통 abstract base model 후보
```

초기 OS 셸 작업에서는 `core`를 중심으로 다음 기능을 구현한다.

```text
/
→ OS 홈

/notices/
→ Notice placeholder 또는 Notice Module

/checklists/
→ Checklist placeholder 또는 Checklist Module

/manuals/
→ Manual placeholder 또는 Manual Module

/requests/
→ Request placeholder 또는 Request Module

/schedules/
→ Schedule placeholder 또는 Schedule Module
```

## 5.4 `inventory/`

`inventory/`는 기존 Inventory Module의 실제 Django 앱이다.

이 앱은 이미 완성된 MVP 기준 구현이며, OS 셸 작업 중 핵심 로직을 수정하지 않는다.

수정 가능한 범위:

```text
메뉴 위치
sidebar 링크
OS 홈에서 진입 링크
공통 base template 적용에 따른 최소 template 조정
표시 문구
template 오타
```

수정 금지 또는 별도 승인 필요 범위:

```text
현재고 계산
StockTransaction
입고/출고 service
초기재고
실사조정
주문/부분입고 상태 처리
reset_operational_data
check_inventory_master_data
```

위 보호 대상의 실제 코드 이름과 표현은 코드 조사 후 `CLAUDE.md`, `OS_WORKING_RULES.md`, 본 문서에서 동일 문구로 통일한다.

---

## 6. 환경 분리

김포365OS는 운영 환경과 리허설 환경을 분리한다.

```text
운영 서버: 8000
운영 DB: gimpo365_inventory

리허설 서버: 8001
리허설 DB: gimpo365os_rehearsal
```

`gimpo365-os` 작업장은 반드시 리허설 DB를 사용한다.

작업 전 다음 명령으로 DB 연결을 확인한다.

```powershell
Select-String -Path .env -Pattern "POSTGRES_DB"
```

기대값:

```env
POSTGRES_DB=gimpo365os_rehearsal
```

위험값:

```env
POSTGRES_DB=gimpo365_inventory
```

`gimpo365-os`에서 운영 DB가 확인되면 작업을 중단한다.

상세 환경 설정 절차는 `OS_OPERATIONS_SETUP.md`에서 관리한다.

---

## 7. Timezone 기준

김포365OS는 날짜와 시간을 다루는 모듈이 많다.

특히 Checklist Module은 다음 개념을 사용한다.

```text
당일 마감담당자
완료 시간
마감 일자
파트별 일일 업무 기록
```

따라서 날짜와 시간 기준을 명확히 한다.

기본 기준:

```python
TIME_ZONE = "Asia/Seoul"
USE_TZ = True
```

원칙:

```text
DB 저장은 timezone-aware 기준으로 처리한다.
사용자에게 표시되는 날짜와 시간은 KST 기준으로 한다.
"당일"의 정의는 KST 로컬 날짜 기준이다.
```

날짜 판정 시 `date.today()`를 직접 사용하지 않는다.

권장 기준:

```python
from django.utils import timezone

today = timezone.localdate()
```

이 기준은 다음 모듈이 공통으로 따른다.

```text
Checklist
Internal Request
Schedule
Attendance / Work Schedule
운영 기록이 날짜를 기준으로 분리되는 모든 모듈
```

현재 settings의 실제 `TIME_ZONE`, `USE_TZ` 값은 코드 조사 후 확인한다.

---

## 8. URL 설계 기준

초기 URL 구조는 단순하게 유지한다.

권장 URL 구조:

```text
/
→ OS 홈

/inventory/
→ Inventory Module

/notices/
→ Notice Module 또는 placeholder

/checklists/
→ Checklist Module 또는 placeholder

/manuals/
→ SOP / Manual Module 또는 placeholder

/requests/
→ Internal Request / Approval Module 또는 placeholder

/schedules/
→ Attendance / Work Schedule Module 또는 placeholder
```

초기 단계에서 실제 기능이 없는 모듈은 `core`의 placeholder view로 처리할 수 있다.

예시:

```text
/notices/
→ core placeholder 또는 notice 앱

/checklists/
→ core placeholder 또는 checklist 앱

/manuals/
→ core placeholder 또는 manual 앱

/requests/
→ core placeholder 또는 request 앱

/schedules/
→ core placeholder 또는 schedule 앱
```

실제 모듈 개발이 시작되면 별도 Django 앱을 만들 수 있다.

단, 앱 생성은 `OS_ROADMAP.md`의 Phase 순서를 따른다.

---

## 9. OS 홈 구현 기준

OS 홈은 로그인 후 김포365OS의 첫 화면이다.

역할:

```text
단일 재고관리 앱이 아니라 OS라는 점을 보여준다.
현재 사용 가능한 모듈과 준비 중 모듈을 구분한다.
재고관리로 빠르게 이동할 수 있게 한다.
향후 공지사항, 체크리스트, SOP 등을 추가할 공간을 마련한다.
```

초기 OS 홈에는 다음을 표시한다.

```text
김포365OS 이름
간단한 설명
운영관리 > 재고관리 카드
공지사항 준비 중 카드
오픈/마감 체크리스트 준비 중 카드
SOP/업무 매뉴얼 준비 중 카드
내부 요청/결재 준비 중 카드
근태/근무표 준비 중 카드
```

OS 홈은 복잡한 관리자 대시보드가 아니다.

초기에는 단순한 모듈 선택 화면으로 만든다.

---

## 10. Placeholder 구현 기준

미구현 모듈은 전 직원에게 노출하되 준비 중 상태로 표시한다.

Placeholder 원칙:

```text
실제 기능처럼 보이면 안 된다.
입력 폼을 제공하지 않는다.
가짜 데이터를 보여주지 않는다.
준비 중 상태를 명확히 표시한다.
향후 구현 예정임을 안내한다.
```

권장 문구:

```text
준비 중인 모듈입니다.
현재는 사용할 수 없습니다.
```

또는:

```text
현재 미구현 상태입니다.
향후 기능이 추가될 예정입니다.
```

미구현 모듈은 직원, 팀장, 관리자 모두 확인 가능하다.

---

## 11. Template 구조 기준

공통 template 구조는 단순하게 유지한다.

권장 구조:

```text
templates/
├─ base.html
├─ includes/
│  ├─ navbar.html
│  ├─ sidebar.html
│  └─ messages.html
├─ core/
│  ├─ home.html
│  └─ placeholder.html
└─ inventory/
   └─ ...
```

기존 프로젝트 구조와 다를 경우, 기존 구조를 무리하게 대개조하지 않는다.

공통 UI 원칙:

```text
모든 주요 화면은 공통 base template을 사용한다.
상단에는 김포365OS 이름을 표시한다.
sidebar에는 모듈 메뉴를 표시한다.
Inventory Module은 운영관리 > 재고관리 위치에 표시한다.
준비 중 모듈은 준비 중 상태로 표시한다.
```

공통 template 변경 시 Inventory 화면이 깨지지 않는지 확인한다.

기존 Inventory template이 이미 공통 base template을 상속하는지 여부는 코드 조사 후 확정한다.

---

## 12. Sidebar / Navigation 기준

Sidebar는 OS의 모듈 구조를 보여주는 역할을 한다.

초기 sidebar 후보:

```text
홈

운영관리
- 재고관리

공지사항
- 공지사항 준비 중

일일업무
- 오픈/마감 체크리스트 준비 중

업무기준
- SOP / 업무 매뉴얼 준비 중

내부요청
- 내부 요청 / 결재 준비 중

근무관리
- 근태 / 근무표 준비 중
```

초기에는 메뉴를 너무 깊게 만들지 않는다.

직원이 메뉴 위치를 직관적으로 이해할 수 있어야 한다.

---

## 13. 공통 CRUD 구현 표준

신규 운영 모듈의 CRUD 화면은 Django 제네릭 CBV를 기본 표준으로 한다.

기본 CBV:

```text
ListView
DetailView
CreateView
UpdateView
```

적용 대상:

```text
Notice
SOP / Manual
Internal Request
Schedule 일부 화면
향후 문서형 또는 관리형 운영 모듈
```

기존 Inventory Module도 CBV 기반이므로, 신규 모듈도 CBV로 통일한다.

이중 표준을 만들지 않는다.

기본 원칙:

```text
목록 화면은 ListView를 기본으로 한다.
상세 화면은 DetailView를 기본으로 한다.
등록 화면은 CreateView를 기본으로 한다.
수정 화면은 UpdateView를 기본으로 한다.
삭제 화면은 초기에는 만들지 않는다.
```

관리자 전용 등록·수정 화면은 공통 권한 Mixin으로 처리한다.

모듈마다 제각각 권한 판정 로직을 쓰지 않는다.

Notice Module의 첫 구현은 학습·검증용 표준 패턴으로 작성한다.

따라서 Notice의 첫 CBV 구현에는 각 클래스가 내부적으로 어떤 역할을 하는지 주석으로 풀어서 작성한다.

이 첫 구현이 검증된 표준 패턴이 되며, SOP/Manual·Request는 다음 요소만 교체하여 재사용한다.

```text
모델
template
form
권한 대상
URL 이름
메뉴 위치
```

표준을 벗어나는 특이 화면이 필요한 경우에만 FBV 또는 custom view를 검토한다.

단, 기본값은 CBV이다.

---

## 14. 공통 권한 Mixin 기준

관리자 전용 화면, 팀장 전용 화면, 직원용 화면의 권한 처리는 공통 Mixin으로 통일한다.

기본 방향:

```text
관리자 전용 CreateView / UpdateView
팀장 확인 화면
직원 조회 화면
```

위 권한 처리를 각 view마다 직접 반복하지 않는다.

공통 권한 Mixin 후보:

```text
AdminRequiredMixin
TeamLeaderRequiredMixin
StaffRequiredMixin
DepartmentScopedMixin
```

실제 이름은 기존 Inventory 권한 구조 조사 후 확정한다.

역할과 소속을 함께 사용하는 화면은 다음 규칙을 따른다.

```text
역할 체크
+ 소속 Department/Team 필터
```

예시:

```text
팀장이 자기 팀 체크리스트만 본다
→ 팀장 역할 확인 + 해당 팀/파트 데이터 필터

관리자가 전체 체크리스트를 본다
→ 관리자 역할 확인 + 전체 조회 허용

직원이 본인 업무만 수행한다
→ 직원 역할 확인 + 본인 또는 소속 기준 필터
```

권한 Mixin은 신규 운영 모듈의 CBV 표준과 함께 사용한다.

---

## 15. 권한 구현 기준

초기 권한 구조는 단순하게 유지한다.

```text
관리자
팀장
직원
```

기본 방향은 기존 Inventory의 권한 구조를 OS 공통 권한 기준으로 채택하는 것이다.

현재 방향:

```text
ROLE_LEVEL / ROLE_PERMISSIONS 계열 구조를 우선 검토한다.
신규 권한 체계를 별도로 만들지 않는다.
기존 권한 구조를 OS 공통 권한 기준으로 확장할 수 있는지 확인한다.
```

실제 `ROLE_LEVEL`, `ROLE_PERMISSIONS`의 존재 여부, 이름, 형태는 코드 조사 후 확정한다.

권한 설계 원칙:

```text
일반 직원은 본인 업무 수행과 조회 중심
팀장은 팀 단위 확인과 일부 관리 기능
관리자는 전체 운영 상태 확인과 설정 관리
```

초기에는 Django의 기존 사용자/권한 구조를 최대한 활용한다.

새 권한 체계를 대규모로 만들지 않는다.

공용 계정과 부서 계정은 만들지 않는다.

권한 기능을 구현할 때는 다음을 피한다.

```text
지나치게 세분화된 권한
사용자가 이해하기 어려운 권한명
역할과 소속의 혼동
모듈마다 제각각인 권한 체계
```

---

## 16. Department / Team 구현 기준

Department / Team은 김포365OS의 공통 소속 기준정보이다.

역할과 소속은 분리한다.

```text
역할:
관리자, 팀장, 직원

소속:
데스크, 치료실, 피부관리실, 탕전 등
```

기본 원칙:

```text
User는 최소 하나의 주 소속을 가진다.
초기에는 1인 1주 소속을 기본으로 한다.
향후 필요 시 복수 소속을 검토할 수 있다.
Department/Team은 특정 모듈 전용으로 만들지 않는다.
Checklist 전용 Department 모델을 만들지 않는다.
```

Phase 1.5에서 다음을 확인한다.

```text
기존 Inventory MVP에 Department 또는 유사 모델이 있는지 확인
있으면 OS 공통 소속 기준으로 활용 가능한지 검토
없으면 core에 Department/Team 기준정보 신설 여부 결정
User와 Department/Team 연결 방식 결정
```

기술 원칙:

```text
가능하면 additive 변경으로 처리한다.
컬럼 rename, 테이블 rename, 앱 이동은 피한다.
기존 Department 모델을 물리 이동하지 않는다.
migration 발생 시 리허설 DB에서 먼저 검증한다.
```

---

## 17. 공통 abstract base model 기준

신규 운영 모듈이 공유할 공통 abstract base model을 둔다.

위치는 `core` 앱을 기본 후보로 한다.

후보 이름:

```python
class TimeStampedActiveModel(models.Model):
    ...
```

또는:

```python
class OperationalBaseModel(models.Model):
    ...
```

실제 이름은 구현 시 확정한다.

후보 필드:

```text
created_at
updated_at
created_by
updated_by
is_active
```

기본 원칙:

```text
신규 운영 모듈 모델은 공통 abstract base model을 상속한다.
모듈마다 created_at, updated_at, created_by, updated_by, is_active를 반복 선언하지 않는다.
status, Department/Team 등 일부 모듈에만 필요한 필드는 base에 넣지 않는다.
```

예시 구조:

```python
class OperationalBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
```

위 코드는 방향 예시이다.

실제 필드 옵션은 모듈별 요구와 기존 사용자 모델 구조를 확인한 뒤 확정한다.

---

## 18. DB 구조 기준

김포365OS의 Django 앱들은 하나의 PostgreSQL DB를 공유한다.

모듈별 DB 분리는 사용하지 않는다.

현재 DB 구조:

```text
운영 DB: gimpo365_inventory
리허설 DB: gimpo365os_rehearsal
```

`gimpo365_inventory`라는 이름은 Inventory Module에서 시작된 역사적 이름이다.

향후 OS 모듈 테이블도 이 DB에 추가될 수 있다.

운영 중 DB rename은 하지 않는다.

DB rename은 별도 백업, 리허설, 전환 계획 없이는 수행하지 않는다.

상세 DB 운영 절차는 `OS_DB_OPERATIONS.md`에서 관리한다.

---

## 19. Migration 기술 기준

Migration은 김포365OS 성장 과정에서 가장 큰 데이터 리스크 중 하나이다.

기본 원칙:

```text
모든 migration은 리허설 DB에서 먼저 적용한다.
운영 migration 전에는 운영 DB 백업이 필요하다.
파괴적 migration은 기본 금지한다.
가능하면 reversible migration을 작성한다.
기존 운영 데이터 보존을 최우선으로 한다.
```

허용 가능성이 높은 migration:

```text
새 앱 추가
새 모델 추가
새 테이블 추가
nullable 필드 추가
안전한 기본값이 있는 필드 추가
새 인덱스 추가
```

주의가 필요한 migration:

```text
User FK 추가
Department/Team 모델 추가
기존 테이블에 non-null 필드 추가
대량 데이터 변환
기존 데이터 기준 변경
```

기본 금지 migration:

```text
기존 컬럼 삭제
기존 컬럼 rename
기존 컬럼 type 변경
기존 테이블 삭제
운영 데이터 일괄 삭제
기존 앱 label 변경
모델의 앱 이동
```

Migration 실행 절차는 `OS_DB_OPERATIONS.md`에서 관리한다.

본 문서에는 상세 명령을 중복 작성하지 않는다.

---

## 20. 모델 설계 기준

모델은 단순하고 명확하게 설계한다.

공통 원칙:

```text
운영 기록은 삭제보다 상태 변경 또는 이력 보존을 우선한다.
created_at, updated_at 등 기본 시간 필드를 고려한다.
작성자, 수정자, 처리자 등 책임 주체를 가능한 한 User 기준으로 남긴다.
부서/파트 구분이 필요한 경우 Department/Team 기준을 사용한다.
상태값은 처음부터 과도하게 늘리지 않는다.
```

책임 주체 FK 원칙:

```text
created_by
updated_by
processed_by
approved_by
completed_by
```

위와 같은 User FK는 `on_delete=PROTECT` 또는 `SET_NULL`을 사용한다.

User FK에 `CASCADE`를 사용하지 않는다.

이유:

```text
사용자가 삭제될 때 운영 기록이 함께 삭제되면 안 된다.
퇴사자 계정도 과거 기록의 책임 주체로 남아야 한다.
마감 기록, 요청 처리 기록, 공지 작성 기록은 개인 계정에 귀속되어야 한다.
```

User는 물리 삭제하지 않는다.

퇴사자 또는 비활성 사용자는 다음 원칙을 따른다.

```text
User.is_active = False
```

개인 계정 기록 귀속이 김포365OS의 핵심이므로, 퇴사자 계정도 기록 참조를 위해 보존한다.

모델 설계 시 피할 것:

```text
처음부터 과도하게 일반화된 추상 모델
모든 모듈을 하나의 범용 테이블로 처리하는 구조
직원이 이해하기 어려운 상태값
운영 의미가 불명확한 필드명
삭제로 이력을 없애는 구조
User FK에 CASCADE 사용
```

---

## 21. 공통 필드 기준

새 모델을 만들 때 다음 필드를 검토한다.

```text
created_at
updated_at
created_by
updated_by
is_active
status
department/team
```

모든 모델에 반드시 전부 넣을 필요는 없다.

필드는 실제 운영 목적에 맞게 선택한다.

기준:

```text
누가 만들었는지 중요하면 created_by 사용
누가 수정했는지 중요하면 updated_by 사용
활성/비활성 관리가 필요하면 is_active 사용
처리 흐름이 있으면 status 사용
부서/파트 구분이 필요하면 Department/Team 연결
```

공통성이 높은 필드는 `core`의 abstract base model에 둔다.

모듈 고유 의미가 있는 필드는 각 모델에 둔다.

예시:

```text
base model에 둘 수 있는 필드:
created_at
updated_at
created_by
updated_by
is_active

각 모델에 둘 필드:
status
department/team
category
completed_at
due_date
```

---

## 22. 상태값 설계 기준

상태값은 단순하게 시작한다.

상태값을 만들 때는 다음을 확인한다.

```text
직원이 이해할 수 있는가
관리자가 처리 기준을 설명할 수 있는가
상태 전이가 너무 복잡하지 않은가
실제 운영에서 구분할 필요가 있는가
```

Internal Request 초기 상태값은 다음으로 제한한다.

```text
요청됨
처리중
처리완료
반려
```

다음 상태값은 후순위로 둔다.

```text
확인중
보류
```

상태값 추가는 실제 운영에서 필요성이 확인된 후 진행한다.

---

## 23. 분류 category 처리 기준

초기 category는 별도 테이블이 아니라 choices 상수로 구현한다.

기본 원칙:

```text
초기에는 choices 상수 사용
자유 문자열 category 사용 금지
별도 Category 테이블화는 후순위
```

이유:

```text
오타로 인한 분류 흔들림 방지
필터 기준 안정화
직원 교육 단순화
초기 구현 단순화
```

적용 대상:

```text
Notice category
SOP / Manual category
Internal Request category
Schedule 분류 후보
```

각 모듈은 필요한 choices를 자체 상수로 정의할 수 있다.

다만 병원 전체 공통 분류가 필요한 경우에는 `core`의 공통 choices 또는 Department/Team 기준과 연결할 수 있다.

category를 별도 테이블로 분리하는 것은 실제 운영에서 다음 필요가 확인된 후 검토한다.

```text
관리자가 분류를 직접 추가해야 함
분류별 권한이 필요함
분류가 자주 바뀜
분류별 통계가 중요해짐
```

---

## 24. Notice Module 기술 기준

Notice Module은 가장 단순한 문서형 CRUD로 시작한다.

Notice-first는 “가장 중요한 모듈이라서 먼저”가 아니다.

Notice-first의 목적은 다음과 같다.

```text
문서형 CRUD 패턴 확립
모듈 문서 → 앱 → migration → QA 흐름 확립
SOP/Manual Module에서 재사용 가능한 패턴 확보
Django 제네릭 CBV 표준 검증
공통 권한 Mixin 검증
공통 abstract base model 검증
```

Notice v1은 다음 CBV 패턴으로 구현한다.

```text
NoticeListView
NoticeDetailView
NoticeCreateView
NoticeUpdateView
```

삭제 view는 초기 구현 범위에서 제외한다.

Notice v1 후보 모델 필드:

```text
title
body
category
is_important
is_active
created_by
updated_by
created_at
updated_at
```

`category`는 초기에는 choices 상수로 구현한다.

Notice v1 초기 기능:

```text
공지 목록
공지 상세
관리자 공지 등록
관리자 공지 수정
중요 공지 표시
활성/비활성 처리
```

Notice 첫 구현의 목적은 기능 완성뿐 아니라 공통 구현 패턴 검증이다.

따라서 Notice의 첫 CBV 구현에는 주요 메서드와 클래스 역할을 주석으로 설명한다.

이 패턴은 이후 다음 모듈에서 재사용한다.

```text
SOP / Manual
Internal Request 일부 화면
향후 문서형 운영 모듈
```

Notice 후순위 기능:

```text
공지 확인 독촉
첨부파일
예약 게시
확인률 리포트
자동 알림
```

후순위 기능은 Checklist 정착 이후 검토한다.

Notice가 비대해져 Checklist 착수를 지연시키면 안 된다.

---

## 25. Checklist Module 기술 기준

Checklist Module은 김포365OS MVP의 핵심 모듈이다.

Checklist는 전 직원의 일일 사용 습관과 직접 연결된다.

Checklist 작업 전 선행 조건:

```text
OS 홈
공통 sidebar/navbar
Department/Team 소속 기준
개인 계정 원칙
리허설 DB 검증 흐름
Timezone 기준
```

Checklist 기본 기준:

```text
기록 단위: User
운영 단위: Department / Team
책임 확인 단위: 당일 마감담당자
```

초기 기능 후보:

```text
오픈 체크리스트
마감 체크리스트
파트별 체크리스트
담당자 완료 기록
완료 시간 기록
관리자 미완료 확인
```

설계 원칙:

```text
완료 기록 삭제 금지
수정 덮어쓰기보다 이력 보존 우선
반복 주기는 처음부터 과도하게 복잡하게 만들지 않음
사진 첨부, 자동 알림은 후순위
```

날짜 기준:

```text
당일 = KST 로컬 날짜
```

날짜 판정은 `timezone.localdate()` 기준을 사용한다.

---

## 26. SOP / Manual Module 기술 기준

SOP / Manual Module은 문서를 담고 관리하는 그릇을 구현하는 모듈이다.

전체 SOP 콘텐츠 작성 완료를 Phase 완료 조건으로 삼지 않는다.

초기 기능 후보:

```text
매뉴얼 목록
매뉴얼 상세
관리자 작성
관리자 수정
부서/파트별 분류
활성/비활성
최신본 관리
```

구현 기준:

```text
제네릭 CBV 사용
Notice에서 검증한 문서형 CRUD 패턴 재사용
공통 abstract base model 상속
category는 choices 상수로 시작
관리자 작성/수정은 공통 권한 Mixin 사용
```

Phase 완료 기준은 다음 수준으로 제한한다.

```text
샘플 매뉴얼 작성 가능
샘플 매뉴얼 조회 가능
샘플 매뉴얼 수정 가능
최신본 관리 가능
```

SOP 콘텐츠 작성은 별도 운영 프로젝트로 지속 진행한다.

---

## 27. Internal Request Module 기술 기준

Internal Request Module은 간단한 요청 등록과 처리상태 확인부터 시작한다.

초기 상태값:

```text
요청됨
처리중
처리완료
반려
```

초기 기능 후보:

```text
직원 요청 등록
요청 목록
요청 상세
관리자 상태 변경
처리 완료 기록
```

구현 기준:

```text
목록/상세/등록/수정 화면은 CBV를 기본으로 한다.
상태 변경은 처음부터 복잡한 workflow engine으로 만들지 않는다.
상태값은 choices 상수로 시작한다.
category는 choices 상수로 시작한다.
담당자, 처리자 등 User FK는 CASCADE를 사용하지 않는다.
```

후순위 기능:

```text
확인중
보류
결재선
첨부파일
댓글
자동 알림
처리 기한
카테고리별 담당자 지정
```

처음부터 전자결재 시스템으로 만들지 않는다.

---

## 28. Schedule Module 기술 기준

Schedule Module은 근무표와 휴가 일정을 확인하는 수준에서 시작한다.

초기 기능 후보:

```text
근무표 조회
휴가 일정 조회
관리자 일정 등록
직원별 근무 일정 확인
```

초기 제외 범위:

```text
급여 계산
법정 근태관리
출퇴근 자동 기록
노무관리 자동화
복잡한 근무 교대 최적화
```

민감 정보가 포함될 수 있으므로 권한과 개인정보 노출 범위를 별도로 검토한다.

날짜 기준은 KST 로컬 날짜를 사용한다.

---

## 29. 테스트 기준

코드 작업 후 기본 확인:

```powershell
python manage.py check
python manage.py test
```

테스트 작성 원칙:

```text
핵심 service 로직은 테스트를 우선한다.
권한이 중요한 view는 권한별 접근 테스트를 검토한다.
migration이 있는 작업은 리허설 DB에서 적용 확인한다.
Inventory 핵심 기능이 깨지지 않았는지 회귀 확인한다.
CBV 표준 패턴은 Notice 구현에서 우선 검증한다.
공통 권한 Mixin은 권한별 접근 테스트를 검토한다.
```

테스트가 실패하면 실패 원인을 확인한 뒤 수정한다.

테스트 실패 상태에서 운영 반영하지 않는다.

---

## 30. 수동 QA 기준

자동 테스트가 통과해도 최소 수동 확인이 필요하다.

OS 공통 smoke QA:

```text
로그인 가능
OS 홈 표시
Inventory Module 진입 가능
준비 중 모듈 placeholder 표시
권한별 메뉴 노출 이상 없음
리허설 DB 연결 확인
```

Inventory Module을 수정하지 않은 경우 상세 inventory QA 전체를 매번 수행하지 않는다.

다만 다음은 확인한다.

```text
Inventory 메뉴 진입 가능
재고현황 주요 화면 접근 가능
입고/출고 주요 화면 접근 가능
오류 화면 없음
```

상세 QA는 `OS_MANUAL_QA_CHECKLIST.md`와 모듈별 QA 문서를 따른다.

---

## 31. 보안 및 민감정보 기준

비밀값은 Git, 채팅, 로그, 출력, 커밋 메시지, 코드 주석에 노출하지 않는다.

비밀값 예시:

```text
.env 내용
SECRET_KEY
DB 비밀번호
계정 비밀번호
pgpass.conf 내용
NAS 접속 정보
운영 계정 정보
```

저장소는 public 전제를 따른다.

따라서 다음에도 직원 개인정보나 운영 상세를 넣지 않는다.

```text
커밋 메시지
코드 주석
이슈 텍스트
PR 설명
문서 예시 데이터
테스트 fixture
```

---

## 32. 네트워크 구현 기준

김포365OS는 원내 네트워크 사용을 기본으로 한다.

초기 구현 기준:

```text
서버를 인터넷에 직접 노출하지 않는다.
공유기 포트포워딩을 사용하지 않는다.
공인 IP 접속을 허용하지 않는다.
원내 LAN 또는 원내 Wi-Fi에서만 접속한다.
초기에는 Django 앱 레벨 IP 화이트리스트를 구현하지 않는다.
```

LAN 바인딩 방식에서 실제 접속 가능 조건은 서버 PC와 동일 서브넷의 기기이다.

게스트 Wi-Fi, 분리 Wi-Fi, AP isolation, 별도 VLAN 환경에서는 접속되지 않을 수 있다.

배포 시 원내 망 구성을 실측한다.

관리자 원격 접근이 필요한 경우에는 앱을 인터넷에 직접 노출하지 않고, VPN 또는 Tailscale 같은 사설 네트워크 방식만 검토한다.

---

## 33. 코드 스타일 기준

초기에는 기존 프로젝트 스타일을 유지한다.

대규모 코드 스타일 변경은 하지 않는다.

원칙:

```text
기존 파일 구조를 존중한다.
작은 함수와 명확한 이름을 사용한다.
비즈니스 로직은 가능하면 service 계층으로 분리한다.
view에 복잡한 로직을 과도하게 넣지 않는다.
template에는 표현 로직만 둔다.
신규 CRUD view는 제네릭 CBV를 기본으로 한다.
권한 판정은 공통 Mixin으로 모은다.
```

Inventory Module의 기존 service 계층은 우회하지 않는다.

---

## 34. 구현하지 않을 것

초기 OS 기술 범위에서 다음은 구현하지 않는다.

```text
환자 진료기록
예약 관리
차트 기능
청구 기능
CRM
복잡한 KPI 대시보드
급여 계산
노무관리 자동화
외부 SaaS 필수 연동
공용 계정
부서 계정
모듈별 DB 분리
```

---

## 35. 조사 의존 항목

다음 항목은 이번 v0.2에서 확정하지 않는다.

읽기 전용 코드 조사 결과가 나온 뒤 확정한다.

조사 결과는 `CODE_RECONCILIATION_REPORT.md`에 기록한다.

## 35.1 Inventory 보호 대상 이름 통일

현재 다음 문서에 Inventory 보호 대상 표현이 존재한다.

```text
CLAUDE.md 절대 규칙 3
OS_WORKING_RULES.md Inventory 보호 규칙
OS_TECH_SPEC.md 5.4
```

코드 조사 후 다음 항목의 실제 이름을 확인한다.

```text
StockTransaction
입고/출고 service 계층
초기재고 처리
실사조정
주문/부분입고 상태 처리
reset_operational_data
check_inventory_master_data
```

조사 후 세 문서의 표현을 동일 문구로 통일한다.

## 35.2 기존 Inventory template 상속 구조 확인

`templates/base.html` 또는 공통 base template이 기존 Inventory에서 이미 사용 중인지 확인한다.

조사 결과에 따라 다음을 확정한다.

```text
공통 base template을 이미 사용 중인지
OS 공통 base를 새로 적용해야 하는지
기존 Inventory template에 최소 조정만 필요한지
```

## 35.3 settings 실제 값 확인

다음 settings 값을 코드 조사로 확인한다.

```text
TIME_ZONE
USE_TZ
INSTALLED_APPS
AUTH_USER_MODEL
DATABASE 설정 방식
```

Timezone 기준은 `Asia/Seoul`, `USE_TZ=True`를 목표 기준으로 하되, 실제 값 확인 후 필요 시 조정한다.

## 35.4 기존 권한 구조 실제 이름 확인

기존 Inventory 권한 구조에서 다음 항목의 실제 존재 여부와 이름을 확인한다.

```text
ROLE_LEVEL
ROLE_PERMISSIONS
사용자 역할 필드
권한 helper
권한 mixin
view별 권한 처리 방식
```

조사 후 본 문서의 권한 구현 기준과 Mixin 이름을 실제 코드에 맞게 보강한다.

---

## 36. 향후 보강 필요 항목

이 문서는 초기 기술 명세서이다.

향후 다음 항목을 보강한다.

```text
CODE_RECONCILIATION_REPORT.md 작성 결과
실제 Department 모델 확인 결과
User–Department 연결 방식
OS 홈 구현 결과
Notice Module 실제 모델
Notice CBV 표준 구현 결과
공통 권한 Mixin 실제 이름
공통 abstract base model 실제 이름
Checklist Module 실제 모델
공통 template 구조
테스트 케이스 기준
운영 배포 방식
```
