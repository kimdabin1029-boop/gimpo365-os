# 김포365OS

김포365한의원 내부 운영 시스템이다. 기존 재고관리 MVP(`gimpo365-inventory`)를 기반으로,
병원 내부 업무를 하나의 OS로 단계적으로 통합해 나간다.

이 문서는 저장소를 처음 여는 운영자·개발자·Claude Code가 현재 프로젝트 성격을 빠르게 이해하기 위한 입구다.
상세 내용은 각 `OS_*.md` 문서로 연결한다.

---

## 1. 프로젝트 개요

- 김포365한의원 내부 운영 시스템(김포365OS)
- 기존 Inventory MVP를 기준 구현으로 삼아 OS로 확장 중
- 재고관리, 공지사항, 오픈/마감 체크리스트, SOP/업무 매뉴얼, 내부 요청/결재, 근태/근무표 등을
  단계적으로 하나의 시스템에 통합하는 것을 목표로 한다
- 운영 안정성이 기능 추가보다 항상 우선한다 (자세히는 [CLAUDE.md](CLAUDE.md), [OS_WORKING_RULES.md](OS_WORKING_RULES.md))

## 2. 현재 상태

- **Phase 1 진행 중** — OS 최소 틀 단계
- 완료: OS 홈 / 공통 shell(base·navbar·sidebar) / 운영관리 > 재고관리 메뉴 배치 / 준비 중 모듈 placeholder
- **Inventory Module은 현재 사용 가능한 기준 모듈**이다
- 나머지 모듈은 OS 홈에 "준비 중" placeholder로만 노출된다(실제 기능 없음)
- 단계별 계획은 [OS_ROADMAP.md](OS_ROADMAP.md), 작업 상태는 [OS_TASKS.md](OS_TASKS.md) 참고

## 3. 주요 모듈

| 모듈 | 상태 |
|---|---|
| 운영관리 > 재고관리 | **사용 가능** |
| 공지사항 | 준비 중 |
| 오픈/마감 체크리스트 | 준비 중 |
| SOP/업무 매뉴얼 | 준비 중 |
| 내부 요청/결재 | 준비 중 |
| 근태/근무표 | 준비 중 |

재고관리는 입고·출고·초기재고·실사조정·주문·부분입고·거래이력·재고현황·관리자 리포트·기준정보 점검을 다룬다.
재고관리 상세는 [docs/modules/inventory/](docs/modules/inventory/)의 `INVENTORY_*.md` 문서를 따른다.

## 4. 실행 전 안전 원칙

- **운영 DB에 직접 연결하지 않는다.**
- 기본 작업 DB는 **리허설 DB(`gimpo365os_rehearsal`)**다. 작업 전 `.env`의 `POSTGRES_DB` 값을 반드시 확인한다.

  ```powershell
  Select-String -Path .env -Pattern "POSTGRES_DB"
  ```

- `.env`, `.venv`, DB dump/backup, `*.sql`, `*.zip`, `pgpass.conf`, 개인정보 파일은 **커밋하지 않는다.**
- 비밀값(`SECRET_KEY`, DB·계정 비밀번호 등)을 코드·문서·커밋 메시지·로그에 남기지 않는다.
- migration은 별도 승인 없이 만들지 않는다. 파괴적 migration은 기본 금지한다.
- 환경변수 세부 항목은 저장소의 `.env.example`을 참고한다(값은 각자 채운다).

절대 규칙의 정본은 [CLAUDE.md](CLAUDE.md), 상세 작업 규칙은 [OS_WORKING_RULES.md](OS_WORKING_RULES.md)다.

## 5. 로컬 실행 요약

아래는 최소 절차다. **상세 환경 구성·리허설 DB 준비·서버 실행 절차는
[OS_OPERATIONS_SETUP.md](OS_OPERATIONS_SETUP.md), [OS_ENVIRONMENT_BASELINE.md](OS_ENVIRONMENT_BASELINE.md)를 따른다.**

```powershell
# 1) 가상환경 / 의존성
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 환경변수 (.env 는 .env.example 을 복사해 값을 채운다. 리허설 DB 를 가리켜야 한다)
Copy-Item .env.example .env

# 3) 마이그레이션 / 리허설 서버 실행 (리허설 포트 8001)
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 8001
```

- 데이터베이스는 **PostgreSQL**을 사용한다. SQLite는 사용하지 않는다.
- 로그인 후 첫 화면은 OS 홈이며, OS 홈에서 재고관리로 진입한다.
- 사용자 생성·역할/부서 지정 등 운영 계정 절차는 [OS_OPERATIONS_SETUP.md](OS_OPERATIONS_SETUP.md)를 따른다.

## 6. 테스트

테스트는 **반드시 PostgreSQL**에서 실행한다(가드 테스트 `core.tests.DatabaseEngineTest`가 이를 검증한다).

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

- 테스트 DB는 러너가 자동 생성/삭제한다.
- 테스트·QA 상세 기준은 [OS_TECH_SPEC.md](OS_TECH_SPEC.md), [OS_MANUAL_QA_CHECKLIST.md](OS_MANUAL_QA_CHECKLIST.md)를 따른다.

## 7. 문서 지도

| 문서 | 용도 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | 최상위 강제층 · 절대 규칙 정본 |
| [OS_WORKING_RULES.md](OS_WORKING_RULES.md) | 상세 작업 규칙(Git/DB/migration/문서/QA) |
| [OS_PRODUCT_SPEC.md](OS_PRODUCT_SPEC.md) | 제품·운영 기준 명세 |
| [OS_ARCHITECTURE.md](OS_ARCHITECTURE.md) | 구조 / 확장 원칙 |
| [OS_ROADMAP.md](OS_ROADMAP.md) | 우선순위 / 단계(Phase) |
| [OS_TECH_SPEC.md](OS_TECH_SPEC.md) | 구현 기준 명세 |
| [OS_ENVIRONMENT_BASELINE.md](OS_ENVIRONMENT_BASELINE.md) | 환경 기준선 |
| [OS_OPERATIONS_SETUP.md](OS_OPERATIONS_SETUP.md) | 환경 구성 · 서버 실행 · 운영 반영 절차 |
| [OS_DB_OPERATIONS.md](OS_DB_OPERATIONS.md) | DB 백업/복구/운영 반영 절차 |
| [OS_MANUAL_QA_CHECKLIST.md](OS_MANUAL_QA_CHECKLIST.md) | 수동 QA 점검 |
| [OS_TASKS.md](OS_TASKS.md) | 작업 순서 · 진행 상태 |
| [docs/CODE_RECONCILIATION_REPORT.md](docs/CODE_RECONCILIATION_REPORT.md) | 코드-문서 정합 점검 보고 |
| [docs/modules/inventory/](docs/modules/inventory/) | Inventory Module 문서(`INVENTORY_*.md`) |

> 이 저장소는 public 전제로 관리한다. 커밋 메시지·주석·문서·이슈에 직원 개인정보나 운영 상세, 비밀값을 넣지 않는다.
