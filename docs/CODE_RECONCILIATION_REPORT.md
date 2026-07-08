# 코드-기준표 대조 보고서 (CODE_RECONCILIATION_REPORT)

## 문서 정보

```text
문서명: CODE_RECONCILIATION_REPORT.md
작성일: 2026-07-08
조사 방식: 읽기 전용 (코드·모델·migration·설정 무수정)
대조 기준: OS_ENVIRONMENT_BASELINE.md v1.0 (2026-07-08 확정본)
대조 대상: gimpo365-os 저장소 실측 상태 (브랜치 docs/os-foundation)
```

> 이 문서는 발견 사항의 **기록**이다. 어떤 항목도 이 문서 작성 시점에 수정하지 않았다.
> 각 불일치의 처리 방향은 다빈(총괄실장)의 별도 지시로 결정한다.

---

## 0. 요약

- 기준표의 핵심 값(Python·Django·psycopg 버전, PostgreSQL 17 서비스, 실행파일 경로, `.env`의 리허설 DB 지정, 폴더 구조, Git 상태)은 **전부 실측과 일치**했다.
- 리허설 DB(`gimpo365os_rehearsal`)는 실제 접속 가능하며 migration이 적용된 상태다. 운영 DB에는 접속하지 않았다(절대 규칙 1).
- 불일치·주의 사항 **10건**을 발견했다. 이 중 우선 확인이 필요한 것은:
  - **D-01** 존재하지 않는 파일명 `OS_OPERATIONS_SETUP.md`를 문서 13곳이 참조 (실제 파일명은 `OS_OPERATION_SETUP.md`)
  - **D-03** 기준표 자체가 저장소에 없음 (single source of truth가 repo 밖 Downloads 폴더에 존재)
  - **D-05** `.env` 부재/오설정 시 코드 기본값이 **운영 DB로 조용히 연결**되는 구조

---

## 1. 일치 확인 항목 (기준표 → 실측)

| 기준표 | 항목 | 기준값 | 실측 결과 | 판정 |
| --- | --- | --- | --- | --- |
| §2 | Python 버전 | 3.14.3 | `.venv\pyvenv.cfg` `version = 3.14.3`, `python --version` → 3.14.3 | 일치 |
| §2 | 가상환경 | 프로젝트 루트 `.venv` | 실재, git ignored 확인 | 일치 |
| §3 | Django | 6.0.6 | `pip freeze` Django==6.0.6, `requirements.txt` 동일 고정 | 일치 |
| §3 | psycopg / psycopg-binary | 3.3.4 | pip freeze 3.3.4 / 3.3.4, `psycopg[binary]==3.3.4` 고정 | 일치 |
| §3 | django-environ | 0.13.0 | pip freeze 0.13.0, `config/settings.py`가 `environ`으로 `.env` 로딩 | 일치 |
| §4 | PostgreSQL 서비스 | `postgresql-x64-17` Running/자동 | `Get-Service` → Running / Automatic | 일치 |
| §4 | `.env` DB 키 구성 | `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | `settings.py` `DATABASES`가 동일 5개 키를 environ으로 읽음 | 일치 |
| §4 | 단일 DB 공유 구조 | 모듈별 DB 분리 없음 | `DATABASES`에 `default` 하나만 정의 | 일치 |
| §5 | psql / pg_dump / pg_restore 경로 | `C:\Program Files\PostgreSQL\17\bin\` | 3개 실행파일 모두 `Test-Path` True | 일치 |
| §6.1 | `.env`의 `POSTGRES_DB` | `gimpo365os_rehearsal` (기대값) | `Select-String` → `POSTGRES_DB=gimpo365os_rehearsal` | 일치 |
| §6.1 | 리허설 DB 실동작 | — | `showmigrations` 접속 성공, accounts/core `0001_initial` 적용 확인 | 정상 |
| §8 | 백업 보관 폴더 | `E:\gimpo365-backup\db` | 폴더 실재 (`Test-Path` True) | 일치 |
| §9 | 현재 브랜치 | `docs/os-foundation` | `git branch --show-current` 동일 | 일치 |
| §9 | 작업 트리 | clean | `git status --short` 출력 없음 (본 보고서 생성 전 기준) | 일치 |
| §9 | ignored 확인 | `.env`, `.venv/`, `__pycache__/` | `git status --ignored` 3종 모두 ignored, `.gitignore`에 명시 | 일치 |
| §10 | 폴더 구조 | accounts/config/core/docs/inventory/scripts/static/templates + manage.py | 전부 실재. `scripts/`에는 `backup_inventory.ps1` 1개 | 일치 |

---

## 2. 불일치 · 주의 항목 (발견 기록만, 무수정)

### D-01. 존재하지 않는 문서 파일명 참조 — `OS_OPERATIONS_SETUP.md`

- 실제 파일명: **`OS_OPERATION_SETUP.md`** (단수 OPERATION, 0바이트 placeholder)
- 그러나 저장소 문서 13곳이 복수형 **`OS_OPERATIONS_SETUP.md`** 를 참조하며, 이 이름의 파일은 존재하지 않는다.
  - `CLAUDE.md` 1곳 (44행)
  - `OS_WORKING_RULES.md` 6곳 (156, 455, 528, 725, 962, 1123행)
  - `OS_ARCHITECTURE.md` 3곳 (252, 268, 1087행)
  - `OS_TECH_SPEC.md` 2곳 (53, 289행)
  - `OS_ROADMAP.md` 1곳 (87행)
- 기준표(§11)도 복수형 `OS_OPERATIONS_SETUP.md`를 사용한다.
- 함의: 파일명과 참조 중 한쪽으로 통일이 필요하다. 참조 수(13곳+기준표) 대비 실파일이 0바이트 1개이므로 **파일명을 복수형으로 rename하는 쪽이 변경량이 적다.** (결정 필요 — 본 조사에서는 수정하지 않음)

### D-02. 루트 기준 문서 4개가 0바이트 placeholder

| 파일 | 크기 | 비고 |
| --- | ---: | --- |
| `OS_DB_OPERATIONS.md` | 0 | 기준표 §11이 "4,5,6,8장 참조" 관계로 명시한 문서 |
| `OS_OPERATION_SETUP.md` | 0 | 기준표 §11이 "1~7,9장 참조" 관계로 명시한 문서 (D-01 파일명 문제 포함) |
| `OS_MANUAL_QA_CHECKLIST.md` | 0 | |
| `OS_TASKS.md` | 0 | |

- `CLAUDE.md` "작업 후 필수"와 `OS_WORKING_RULES.md` 다수 절이 이 문서들(특히 DB_OPERATIONS, OPERATIONS_SETUP)로 절차를 위임하고 있으나, 위임받은 문서가 비어 있다.
- 함의: DB 백업/복구·운영 반영 절차가 현재 문서상 어디에도 실체가 없다. 기준표가 이 공백을 메우는 선행 문서 역할.

### D-03. 기준표(OS_ENVIRONMENT_BASELINE.md) 자체가 저장소에 없음

- 확정본이 `C:\Users\kjwga\Downloads\` 에만 존재하며, 저장소 내 어떤 파일도 `ENVIRONMENT_BASELINE`을 참조하지 않는다 (전체 grep 결과 0건).
- 기준표는 스스로를 "환경의 single source of truth"로 선언하고 §11에서 4개 문서가 자신을 참조한다고 명시했으나, 저장소 기준으로는 아직 반입도 참조도 이루어지지 않았다.
- 함의: 기준표의 저장소 반입(예: 루트 또는 `docs/`)과 참조 문서 연결이 후속 작업으로 필요하다.

### D-04. 백업 스크립트와 기준표 §8의 백업 위치 불일치

- 기준표 §8: 백업 보관 위치 = `E:\gimpo365-backup\db` (실재 확인됨)
- 실제 스크립트 `scripts/backup_inventory.ps1`의 기본 백업 위치 = **`<OneDrive>\gimpo365_inventory_backups\db`** (`-BackupDir` 파라미터로 변경 가능)
- 부가 관찰: 스크립트 기본값(OneDrive)은 사실상 클라우드 사본이 생기는 경로여서, 기준표 §8의 "백업이 운영 PC와 같은 물리 장비에 있다"는 리스크 서술과 실제 스크립트 동작이 서로 다른 그림을 그린다. 어느 쪽이 현행 운영 관행인지 확인 필요.
- 스크립트의 백업 대상 기본값은 운영 DB `gimpo365_inventory`다 (백업이므로 자연스러움. 실행은 하지 않았음).

### D-05. `.env` 부재/키 누락 시 기본값이 운영 DB — 구조적 리스크

- `config/settings.py` 97행: `env("POSTGRES_DB", default="gimpo365_inventory")` — `.env`가 없거나 `POSTGRES_DB` 키가 빠지면 **운영 DB로 조용히 연결**된다.
- `.env.example` 14행도 `POSTGRES_DB=gimpo365_inventory` — 예시 파일을 그대로 복사하면 운영 DB를 가리킨다.
- 기준표 0장은 "`.env` 한 줄이 유일한 벽"이라 경고하는데, 코드 기본값과 예시 파일이 모두 그 벽의 **위험한 쪽**을 기본으로 삼고 있다.
- 이 저장소(`gimpo365-os`)의 기대값은 `gimpo365os_rehearsal`이므로, `.env.example`의 기대값 갱신 또는 settings 기본값(default 제거로 미설정 시 명시적 실패) 검토가 후보. (settings 변경은 절대 규칙상 별도 승인·별도 작업 단위 사안 — 본 조사에서는 기록만)

### D-06. OS 빌드 번호 차이 (경미)

- 기준표 §1: "Windows 10.0.26100 계열" / 실측: `10.0.26200.0`
- 실무 영향 없음. 기준표 다음 버전 갱신 시 반영 후보.

### D-07. Git 원격(remote) 없음 — 공개 여부 검증 불가

- `git remote -v` 출력 없음. 현재 순수 로컬 저장소다.
- 기준표 §9 "저장소 공개: private 기본"은 원격이 없어 검증 자체가 불가능하다. CLAUDE.md의 "public 저장소 전제" 원칙은 원격 생성 이전에도 유지되는 것으로 이해하고 본 보고서도 그 전제로 작성했다.

### D-08. 기준표 §3 패키지 표에 직접 의존성 `openpyxl` 누락 (경미)

- `requirements.txt`는 직접 의존성 4개를 고정: Django, psycopg[binary], django-environ, **openpyxl==3.1.5**
- 기준표 §3 표에는 openpyxl이 없다. (전이 의존성 asgiref 3.11.1, sqlparse 0.5.5, tzdata 2026.2, et_xmlfile 2.0.0도 설치되어 있으나 이는 기준표 취지상 생략 무방)

### D-09. OS_TECH_SPEC.md에 스택 버전 미반영 + 폴더 구조에 `scripts/` 누락 (예정된 후속)

- 기준표 §11은 `OS_TECH_SPEC.md`에 "스택 버전 확정 반영"을 예정하나, 현재 TECH_SPEC v0.2에는 버전 숫자가 전혀 없다 (스택을 "Django / PostgreSQL"로만 서술).
- TECH_SPEC §4·OS_WORKING_RULES §10의 폴더 구조 목록에는 `scripts/`가 빠져 있다 (기준표 §10이 이미 "추가 발견"으로 기록한 사항과 동일).
- 불일치라기보다 기준표 확정에 따른 **미반영 후속 작업**으로 분류.

### D-10. `.gitignore`에 dump/backup 패턴 부재 (관찰)

- `OS_WORKING_RULES.md` §9는 `*.dump`, `*.backup`, `*.zip` 등을 절대 커밋 금지로 규정하나, `.gitignore`에는 해당 패턴이 없다.
- 현재 백업 산출물이 저장소 밖(E:\gimpo365-backup, OneDrive)에 생성되므로 실위험은 낮다. 방어선 추가는 선택 사항으로 기록.

---

## 3. 검증하지 않은 항목과 사유

| 기준표 | 항목 | 사유 |
| --- | --- | --- |
| §4 | 운영 DB `gimpo365_inventory` 실존 여부 | 운영 DB에 접속하지 않음 (CLAUDE.md 절대 규칙 1. 리허설 DB 접속만으로 인스턴스 동작은 간접 확인됨) |
| §6 | 운영 8000 / 리허설 8001 포트 | 코드·설정에 포트 고정 없음. `runserver` 실행 인자로 결정되는 운영 관행이라 코드 대조 대상 아님 |
| §7 | 운영 PC·24시간 가동·네트워크 구성 | 물리/운영 사실로 코드에서 검증 불가 |
| §8 | 백업 자동화 여부(수동) | 운영 관행. 단 스케줄러 등록 여부는 미조사 (조사 범위를 저장소로 한정) |
| §9 | 저장소 public/private | 원격 없음 (D-07) |

---

## 4. 조사 중 실행한 명령 (전부 읽기 전용)

```text
Select-String -Path .env -Pattern "POSTGRES_DB"   ← 작업 전 필수 확인 (기준표 §6.1)
git branch --show-current / git status --short / git status --ignored --short
git remote -v / git log --oneline -5
Get-Content .venv\pyvenv.cfg / python --version / pip freeze
Get-Service postgresql-x64-17 / Test-Path (psql·pg_dump·pg_restore·백업 폴더)
python manage.py check          → System check identified no issues
python manage.py showmigrations → 리허설 DB 접속·적용 상태 조회 (읽기 전용)
파일 열람: settings.py, requirements.txt, .env.example, .gitignore,
          backup_inventory.ps1, OS_*.md, docs/modules/ 목록
```

- 코드·모델·migration·설정 파일은 일절 수정하지 않았다.
- `.env`는 `POSTGRES_DB` 한 줄만 확인했고 그 외 내용(비밀값)은 열람·출력하지 않았다.
- 생성한 파일은 본 보고서(`docs/CODE_RECONCILIATION_REPORT.md`) 하나뿐이다.
