# 김포365OS 환경 기준표 (OS_ENVIRONMENT_BASELINE)

## 문서 정보

```text
문서명: OS_ENVIRONMENT_BASELINE.md
문서 버전: v1.0
최종 확정일: 2026-07-08
근거: 운영 PC 실측(환경기준표 워크시트) + 운영 결정값
범위: 김포365OS 개발/운영 환경의 확정된 기준값. 이후 모든 문서가 이 표를 참조한다.
```

> 이 문서는 **환경의 단일 기준(single source of truth)**이다.
> DB_OPERATIONS·OPERATIONS_SETUP 등 다른 문서는 환경값을 자체적으로 다시 적지 말고 이 표를 참조한다.
> 환경이 바뀌면 **이 문서 한 곳만** 고치고 버전을 올린다.

---

## 0. 핵심 경고 (가장 먼저 읽을 것)

운영 DB와 리허설 DB는 **같은 PostgreSQL 인스턴스(17번, 같은 host·port)** 안에 이름만 다르게 공존한다.

```text
운영   : gimpo365_inventory
리허설 : gimpo365os_rehearsal
```

→ 둘을 가르는 유일한 벽은 `.env`의 `POSTGRES_DB` 값 **한 줄**이다.
→ 서버·포트가 같으므로, `.env` 한 글자만 틀리면 리허설인 줄 알고 **운영 DB를 건드린다.**
→ 따라서 **모든 작업 전 `.env`의 `POSTGRES_DB`를 반드시 확인**한다. (아래 6.1 명령)

---

## 1. 운영체제 / 셸

| 항목 | 값 |
| --- | --- |
| OS | Windows (10.0.26100 계열) |
| 셸 | PowerShell |
| 문서 명령어 기준 | 모든 예시 명령은 PowerShell 기준으로 작성 |

---

## 2. Python / 가상환경

| 항목 | 값 |
| --- | --- |
| Python | 3.14.3 |
| 가상환경 | `.venv` 사용 (프로젝트 루트) |
| 활성화 | `.\.venv\Scripts\Activate.ps1` |
| 시스템 Python 경로 | `C:\Users\kjwga\...\Python314\python.exe` (참고용, 직접 사용 금지) |

> **원칙: 모든 Python/Django/pip 명령은 반드시 `.venv` 활성화 상태에서 실행한다.**
> 활성화되면 프롬프트 앞에 `(.venv)`가 표시된다. 미활성 시 시스템 Python이 실행되어 "No module named django" 등 오류가 난다.
> 스크립트 실행이 막히면 해당 창에서만 1회: `Set-ExecutionPolicy -Scope Process -Bypass`

---

## 3. 프레임워크 / 주요 패키지

| 패키지 | 버전 | 비고 |
| --- | --- | --- |
| Django | 6.0.6 | 최신 계열. 코드/명령 예시는 Django 6 기준 |
| psycopg | 3.3.4 | **psycopg 3.x** (구 psycopg2 아님). DB 코드·예시는 psycopg3 기준 |
| psycopg-binary | 3.3.4 | |
| django-environ | 0.13.0 | `.env` 로딩 라이브러리. settings가 이걸로 환경변수를 읽음 |

> Claude Code 작업 시 주의: 버전이 최신이므로, 구버전(psycopg2, 예전 Django) 기준 코드/예시를 쓰지 않는다.

---

## 4. 데이터베이스

| 항목 | 값 |
| --- | --- |
| DBMS | PostgreSQL 17 (서비스명 `postgresql-x64-17`, 상태 Running / 자동 시작) |
| 운영 DB | `gimpo365_inventory` |
| 리허설 DB | `gimpo365os_rehearsal` |
| 공존 구조 | 두 DB가 **같은 인스턴스**에 공존 (0장 경고 참조) |
| 앱-DB 관계 | 단일 DB 공유. 모든 Django 앱이 하나의 DB에 테이블 추가 (모듈별 DB 분리 없음) |
| `.env` DB 키 | `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` |

> `psql`은 PATH에 없음. 전체 경로로 호출한다 (아래 5).

---

## 5. PostgreSQL 실행 파일 경로 (PATH 미등록 → 전체 경로 사용)

| 도구 | 경로 |
| --- | --- |
| psql | `C:\Program Files\PostgreSQL\17\bin\psql.exe` |
| pg_dump | `C:\Program Files\PostgreSQL\17\bin\pg_dump.exe` |
| pg_restore | `C:\Program Files\PostgreSQL\17\bin\pg_restore.exe` |

> `bin\` 폴더의 것을 사용한다. `pgAdmin 4\runtime\` 아래 동명 파일은 사용하지 않는다.
> (선택) 매번 전체 경로가 번거로우면 향후 `C:\Program Files\PostgreSQL\17\bin`을 PATH에 추가하는 것을 검토. 지금은 전체 경로 기준으로 문서화.

---

## 6. 서버 / 포트

| 환경 | 포트 | DB | 실행 위치 |
| --- | ---: | --- | --- |
| 운영 | 8000 | `gimpo365_inventory` | 운영 PC (7장) |
| 리허설 | 8001 | `gimpo365os_rehearsal` | 동일 PC |

### 6.1 작업 전 필수 확인 명령 (PowerShell)

```powershell
Select-String -Path .env -Pattern "POSTGRES_DB"
```

- 기대값: `POSTGRES_DB=gimpo365os_rehearsal` (리허설)
- 위험값: `POSTGRES_DB=gimpo365_inventory` (운영) → 즉시 작업 중단, `.env` 재확인

---

## 7. 운영/개발 환경 (운영 결정값)

| 항목 | 값 |
| --- | --- |
| 운영 서버 PC | 행정실 내 김다빈 실장 전용 PC |
| 가동 | 24시간 상시 (개발 착수 이후) |
| 리허설 실행 PC | 운영과 **동일 PC** (8001 포트) |
| 서버 네트워크 | 유선 연결 |
| 직원 모바일 접속망 | 서버 PC와 **동일 공유기 대역** (게스트/분리망 아님) |
| 접속 주소 | 현재 서버 PC 내부 IP 사용 (`http://<내부IP>:8000`), 변경 여지 있음 |

> 네트워크 함의: 서버가 유선이고 직원 모바일이 같은 대역이므로, LAN 바인딩 방식에서 원내 모바일 접속이 자연히 가능하다. 별도 IP 화이트리스트 로직 불필요.
> 리허설이 운영과 같은 PC·같은 DB 인스턴스에 있으므로, 0장 경고(`.env` 오설정 위험)가 이 환경에서 특히 중요하다.

---

## 8. 백업 (운영 결정값)

| 항목 | 값 |
| --- | --- |
| 백업 도구 | `pg_dump` (경로는 5장) |
| 백업 보관 위치 | 운영 PC 내부 `E:\gimpo365-backup\db` |
| 자동화 | 현재 **수동** (당분간 손으로) |
| 원외 보관 | 없음 (원내 NAS 향후 구축 예정) |

> ⚠️ 현재 백업 리스크: 백업본이 **운영 PC와 같은 물리 장비(E 드라이브)**에 있다. 이 PC/디스크가 죽으면 운영 DB와 백업이 함께 소실된다.
> → 단기: 정기적으로 백업본을 외부 매체/클라우드로 복사하는 습관을 병행 권장.
> → 중기: NAS 구축 후 백업 원외 보관 자동화. (DB_OPERATIONS에서 다룸)
> → 자동화 방식(수동 → Windows 작업 스케줄러)은 DB_OPERATIONS에서 별도 설계.

---

## 9. Git / 저장소

| 항목 | 값 |
| --- | --- |
| 현재 브랜치 | `docs/os-foundation` |
| 작업 트리 | clean |
| 무시(ignored) 확인됨 | `.env`, `.venv/`, 각 앱 `__pycache__/` |
| 저장소 공개 | private 기본 (public 전제 원칙은 유지) |

> `.env`, `.venv`가 `.gitignore`에 정상 반영됨. dump/backup(`E:\gimpo365-backup`)은 저장소 밖 경로라 커밋 위험 없음.

---

## 10. 실측 확인된 폴더 구조

```text
gimpo365-os
├─ .venv/          (가상환경, git 제외)
├─ accounts/
├─ config/
├─ core/
├─ docs/
├─ inventory/
├─ scripts/        (← 워크시트에서 추가 발견. 유틸/백업 스크립트 배치 후보)
├─ static/
├─ templates/
└─ manage.py
```

> 문서(TECH_SPEC/ARCHITECTURE)가 가정한 앱 구조 전부 실재 확인.
> `scripts/`가 추가로 존재 → 백업/운영 스크립트를 여기에 두는 것을 검토(DB_OPERATIONS에서 결정).

---

## 11. 이 표를 참조하는 문서

```text
OS_DB_OPERATIONS.md      → 4,5,6,8장 (DB·백업)
OS_OPERATIONS_SETUP.md   → 1~7,9장 (환경 세팅·실행)
OS_TECH_SPEC.md          → 2,3,4장 (스택 버전 확정 반영)
OS_WORKING_RULES.md      → 0,6장 (운영 DB 격리 경고)
```

> 변경 이력: v1.0 (2026-07-08) 운영 PC 실측값 + 운영 결정값으로 최초 확정.
