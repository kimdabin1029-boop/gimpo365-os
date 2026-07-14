# OS_OPERATIONS_SETUP.md

# 김포365OS 운영/환경 세팅 문서

## 문서 버전

```text
문서명: OS_OPERATIONS_SETUP.md
문서 버전: v0.2
최종 수정일: 2026-07-08
문서 범위: 김포365OS 로컬/리허설/운영 환경 세팅 및 서버 실행 절차
근거: OS_ENVIRONMENT_BASELINE.md v1.0
```

## 변경 이력

| 버전 | 수정일 | 변경 요약 |
| --- | --- | --- |
| v0.2 | 2026-07-08 | 검토 반영: 운영/리허설 .env 전환 위험 명시, settings 실패 동작을 T-A1 완료 기준으로 표기, 운영 runserver 명령(0.0.0.0:8000)·ALLOWED_HOSTS·waitress 검토 명시, .env.example 안전 조건 추가, 4.4 migrate를 리허설 세팅용으로 한정, 서버 실행 전 공통 체크 블록 추가, psql 비밀번호 비노출 주의 추가 |
| v0.1 | 2026-07-08 | 실측 환경 기준 최초 작성. .venv 세팅, .env 구성, 리허설/운영 서버 실행, 자주 겪는 문제 정리 |

---

## 1. 문서 목적

이 문서는 김포365OS를 **세팅하고 서버를 실행하는 절차**를 정의한다.

새 PC에서 환경을 다시 구성하거나, 협업자가 자기 환경에 올리거나, 실행 방법을 다시 확인할 때 이 문서를 본다.

환경값(버전·경로·DB 이름 등)은 이 문서에서 다시 정의하지 않고 `OS_ENVIRONMENT_BASELINE.md`를 기준으로 한다. 환경이 바뀌면 기준표를 먼저 고친다.

DB 백업·복구·migration 절차는 이 문서가 아니라 `OS_DB_OPERATIONS.md`를 따른다.

---

## 2. 전제 (이미 설치되어 있어야 하는 것)

현재 운영 PC 기준으로 아래는 이미 설치·구성되어 있다(기준표 참조).

```text
Windows (PowerShell)
Python 3.14.3
PostgreSQL 17  (C:\Program Files\PostgreSQL\17\bin)
Git
운영 DB gimpo365_inventory / 리허설 DB gimpo365os_rehearsal (같은 인스턴스)
```

새 PC에 처음 세팅하는 경우에는 위를 먼저 설치해야 한다(이 문서 범위 밖. 향후 보강).

---

## 3. 핵심 주의 (세팅·실행 내내 적용)

```text
1. 모든 Python/Django/pip 명령은 .venv를 활성화한 상태에서 실행한다.
   → 활성화 안 하면 시스템 Python이 실행되어 "No module named django" 등 오류가 난다.
2. psql/pg_dump 등은 PATH에 없다. 전체 경로로 호출한다.
   → C:\Program Files\PostgreSQL\17\bin\...
3. 운영 DB와 리허설 DB는 .env의 POSTGRES_DB 한 줄로만 갈린다.
   → 작업 전 항상 어느 DB를 가리키는지 확인한다.
4. .env는 절대 Git에 커밋하지 않는다(이미 .gitignore 처리됨).
```

---

## 4. 최초 세팅 절차 (새 환경에 처음 올릴 때)

> `gimpo365-os` 폴더를 확보한 상태(git clone 또는 복사)에서 시작.

### 4.1 가상환경 생성·활성화

```powershell
# gimpo365-os 폴더에서
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- 활성화되면 프롬프트 앞에 `(.venv)`가 표시된다. 이 표시가 "상자가 열렸다"는 신호다.
- 활성화 확인:

```powershell
where.exe python
```

경로가 `...\gimpo365-os\.venv\Scripts\python.exe` 를 가리키면 정상. 시스템 Python 경로가 나오면 활성화가 안 된 것이다.

**스크립트 실행이 막히는 경우** (`이 시스템에서 스크립트를 실행할 수 없으므로...`):

```powershell
Set-ExecutionPolicy -Scope Process -Bypass
```

- 이 명령은 **현재 PowerShell 창에서만** 정책을 풀며, 시스템 전체 설정을 바꾸지 않는다. 창을 닫으면 원래대로 돌아간다.

### 4.2 패키지 설치

```powershell
# .venv 활성화 상태에서
pip install -r requirements.txt
```

- 설치 확인:

```powershell
python -m django --version
pip freeze | Select-String -Pattern "Django|psycopg|django-environ|openpyxl"
```

기대: Django 6.0.6 / psycopg 3.3.4 / django-environ 0.13.0 / openpyxl 3.1.5 (기준표 §3)

### 4.3 `.env` 구성

`.env`는 저장소에 없다(비밀값이므로 커밋 금지). `.env.example`을 복사해 만든다.

> ⚠️ **복사 전 안전 조건**: `.env.example`은 운영 DB 값(`gimpo365_inventory`)을 포함하면 안 된다. `POSTGRES_DB`는 비워두거나 리허설(`gimpo365os_rehearsal`) 예시여야 한다. 만약 `.env.example`에 `POSTGRES_DB=gimpo365_inventory`가 들어 있으면, **복사하기 전에 먼저 수정**한다(그대로 복사하면 운영 DB를 가리키는 `.env`가 만들어진다). — 이 조건은 T-A1(코드조사 후속작업)에서 `.env.example` 정비가 완료된 상태를 전제로 한다.

```powershell
Copy-Item .env.example .env
```

그다음 `.env`를 열어 값을 채운다. **키 구성**(기준표 §4):

```text
DJANGO_SECRET_KEY=        (개발용 임의 키)
DJANGO_DEBUG=             (개발/리허설은 True, 운영은 False 권장)
DJANGO_ALLOWED_HOSTS=     (접속 허용 호스트/IP)

POSTGRES_DB=              (★ 이 작업장에서는 gimpo365os_rehearsal)
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=            (localhost)
POSTGRES_PORT=            (5432)
```

> ★ **가장 중요**: `gimpo365-os` 작업장의 `POSTGRES_DB`는 반드시 `gimpo365os_rehearsal`(리허설)로 둔다.
> **(T-A1 완료 기준)** settings에 기본값이 없으므로, 이 키가 비면 서버가 **명시적으로 실패**한다(운영에 조용히 붙지 않는다 — 의도된 안전장치). 단 이 동작은 T-A1(settings.py 기본 DB 안전화)이 적용된 뒤의 기준이며, T-A1 이전 코드에서는 기본값(`gimpo365_inventory`)으로 운영에 붙을 수 있다.

### 4.4 DB 연결·migration 확인 (리허설 최초 세팅/검증용)

> 이 절의 migrate는 **리허설 DB 최초 세팅·연결 검증** 목적이다. 운영 DB에 대한 migration은 여기서 하지 않으며, 반드시 `OS_DB_OPERATIONS.md`의 migration 절차(리허설 선적용 → 백업 → --plan → 적용)를 따른다.

```powershell
# .env가 리허설을 가리키는지 먼저 확인
Select-String -Path .env -Pattern "POSTGRES_DB"   # = gimpo365os_rehearsal

python manage.py check
python manage.py migrate        # 리허설 DB에 적용 (최초 세팅/검증)
python manage.py showmigrations # 적용 상태 확인
```

- `check`가 통과하고 migrate가 오류 없이 끝나면 리허설 DB 연결이 정상이다.

---

## 5. 서버 실행

### 5.0 서버 실행 전 공통 체크 (리허설·운영 공통)

어떤 서버를 띄우든 실행 전 아래를 확인한다.

```text
[ ] .venv 활성화됨 ( 프롬프트에 (.venv) 표시 )
[ ] Select-String -Path .env -Pattern "POSTGRES_DB" 로 대상 DB 확인
[ ] python manage.py check 통과
[ ] 띄우려는 포트와 .env의 DB가 맞게 매칭되는가
    - 리허설: 8001 ↔ gimpo365os_rehearsal
    - 운영  : 8000 ↔ gimpo365_inventory
```

> ⚠️ **운영/리허설 .env 전환 위험 (반드시 숙지)**
> 운영과 리허설은 같은 작업장·같은 `.env`를 공유한다. 따라서:
> - 하나의 작업장에서 `.env`를 바꿔가며 운영(8000)과 리허설(8001)을 **동시에 운용하지 않는다.** `.env`를 운영으로 바꾸는 순간, 그 작업장에서 실행되는 모든 서버(리허설 포함)가 운영 DB를 보게 된다.
> - 운영·리허설을 **동시에 상시 유지**하려면, 운영용 폴더와 리허설용 폴더를 분리하거나 실행 시 환경변수를 분리하는 방식을 **별도로 확정**한다(현재 미확정 — 향후 보강).
> - 단일 작업장에서 `.env`를 전환하는 것은 **임시 수동 절차**다. 전환 전후로 반드시 `POSTGRES_DB`를 확인한다.

### 5.1 리허설 서버 (8001) — 개발/검증 기본

```powershell
# 5.0 공통 체크 후. .env가 리허설(gimpo365os_rehearsal)인지 확인
Select-String -Path .env -Pattern "POSTGRES_DB"
python manage.py runserver 8001
```

- 브라우저에서 `http://127.0.0.1:8001/` 로 접속.
- 개발·검증·OS 틀 작업은 이 리허설 서버에서 한다.

### 5.2 운영 서버 (8000) — 직원 실사용

> 운영 서버는 `.env`가 운영 DB(`gimpo365_inventory`)를 가리키는 상태에서 실행한다. 5.0 공통 체크와 위 전환 위험을 반드시 확인한다.

원내 다른 기기(직원 모바일 등)에서 접속해야 하므로, localhost가 아니라 모든 인터페이스로 바인딩한다.

```powershell
# 5.0 공통 체크 + POSTGRES_DB가 운영(gimpo365_inventory)인지 재확인 후
Select-String -Path .env -Pattern "POSTGRES_DB"
python manage.py runserver 0.0.0.0:8000
```

- `0.0.0.0:8000` : 서버 PC의 모든 네트워크 인터페이스에서 접속을 받는다(원내 다른 기기 접속용). `127.0.0.1`은 서버 PC 자신만 접속 가능하므로 운영에는 부적합.
- 직원 접속 주소: `http://<서버 PC 내부 IP>:8000`
- **`DJANGO_ALLOWED_HOSTS`에 서버 PC 내부 IP를 포함**해야 원내 다른 기기에서 접속된다(누락 시 Django가 접속을 거부). `.env`의 `DJANGO_ALLOWED_HOSTS`를 확인한다.
- ⚠️ 초기 내부 운영/알파 단계 기준이다. `runserver`는 개발용 서버이므로, **장기 운영에서는 waitress 등 운영용 WSGI 서버 또는 서비스화를 별도 검토**한다(9장 보강).
- 운영 반영·전환 시점 판단은 `OS_WORKING_RULES.md`·`OS_DB_OPERATIONS.md`의 운영 반영 기준을 따른다.

### 5.3 네트워크 접속 (원내)

```text
서버 PC: 유선 연결. 직원 모바일은 같은 공유기 대역(기준표 §7).
접속 방식: 서버 PC 내부 IP + 포트. 예) http://192.168.x.x:8000
원외 접속: 차단(서버를 인터넷에 직접 노출하지 않음, 포트포워딩 안 함).
관리자 원격이 필요하면 VPN/Tailscale 등 사설망만 검토(일반 직원 원외 허용 아님).
```

- 바인딩은 5.2의 `runserver 0.0.0.0:8000`으로 처리된다. 추가로 **서버 PC 방화벽이 해당 포트(8000)를 허용**해야 원내 다른 기기에서 접속된다(방화벽 허용은 배포 시 실측·확정 — 향후 보강).
- 같은 서브넷 조건: 서버 PC와 동일 대역의 기기만 접속 가능. 게스트/분리 Wi-Fi에서는 안 될 수 있다.

### 5.4 운영 후보 DB(`gimpo365os_prod`) 알파 → 정식 전환 (P3-08A)

현재 배포 방향은 rehearsal 복제본(`gimpo365os_prod`)을 그대로 정식 운영으로 승격하는 것이다.
별도의 데이터 마이그레이션은 하지 않는다.

```text
- gimpo365os_prod : rehearsal 을 PostgreSQL TEMPLATE 로 복제한 운영 후보 DB.
- 8001 포트에서 gimpo365os_prod 로 팀장 알파테스트 → 기준정보·운영 설정 축적.
- 알파 종료 후 알파 운영기록(재고 거래·주문)만 초기화 → 실물 실사 → 최초재고 등록.
- 같은 DB 를 8000 포트로 구동하여 정식 운영 시작.
- 알파에서 입력한 기준정보(계정/부서/거래처/품목/관리품목/공지/체크리스트)는 정식 운영에 그대로 사용.
```

전환 절차(요약. DB 상세는 OS_DB_OPERATIONS.md §6A):

```text
1. 8001 포트에서 팀장 알파테스트
2. 실제 계정·부서·거래처·품목·관리품목 입력
3. 실제 공지사항·체크리스트 항목 설정
4. 알파테스트 종료 시각 공지 → 모든 입력 일시 중지
5. gimpo365os_prod 전체 백업 (backup_db.bat)
6. python manage.py reset_alpha_transactions --dry-run  → 삭제·보존 예상 건수 검토
7. 다빈 승인 후 python manage.py reset_alpha_transactions --yes --confirm-db gimpo365os_prod
8. 기준정보 건수 검증 + 관리품목 현재고 전부 0 확인
9. 실물 재고 조사 → 최초재고(또는 실사조정)로 실제 수량 등록
10. 테스트 공지·임시 계정 선별 정리, 로그인 세션 초기화(--clear-sessions)
11. 최종 DB 백업
12. 8001 서버 종료 → 동일 DB 를 8000 포트에서 실행
13. 원내 PC 접속 확인 → 정식 운영 시작
```

```text
⚠️ python manage.py flush 금지:
flush 는 사용자·부서·품목 등 기준정보까지 삭제한다. 정식 운영 전환에는 reset_alpha_transactions 만 사용한다.
```

> `reset_alpha_transactions` 안전장치는 **--confirm-db(연결 DB명 정확 일치) + 전체 백업 + 다빈 승인**이다.
> 실제 초기화는 이번 작업 범위가 아니라 알파테스트 종료 후 별도 승인·실행한다.
> 상세: docs/modules/inventory/RESET_ALPHA_TRANSACTIONS_SPEC.md

---

## 6. PostgreSQL 직접 접근 (필요 시)

`psql`은 PATH에 없으므로 전체 경로로 호출한다.

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -l   # DB 목록
```

- DB 목록에 `gimpo365_inventory`, `gimpo365os_rehearsal`이 보이면 정상.
- ⚠️ `psql`·`pg_dump` 등 실행 시 **비밀번호 입력 프롬프트**가 뜰 수 있다. 입력해도 화면에 표시되지 않는다(정상). 이 비밀번호는 **문서·로그·커밋 메시지·채팅에 남기지 않는다.**
- 백업/복구 관련 psql·pg_dump·pg_restore 사용은 `OS_DB_OPERATIONS.md`를 따른다.

---

## 7. 자주 겪는 문제 (Troubleshooting)

### 7.1 `No module named django`

```text
원인: .venv를 활성화하지 않고 명령을 실행함(시스템 Python이 실행됨).
해결: .\.venv\Scripts\Activate.ps1 로 활성화. 프롬프트에 (.venv) 표시 확인.
확인: where.exe python 이 .venv 안 경로를 가리키는지 확인.
```

### 7.2 `python manage.py check`가 통과해야 하는데 실패 / DB 관련 오류

```text
먼저 확인: Select-String -Path .env -Pattern "POSTGRES_DB"
- 값이 비어 있으면 → settings에 기본값이 없으므로 의도적으로 실패한다. .env에 리허설 값을 채운다.
- 운영(gimpo365_inventory)을 가리키면 → 리허설 작업 중이라면 즉시 중단하고 리허설로 바꾼다.
```

### 7.3 `psql`/`pg_dump`이 "인식되지 않습니다"

```text
원인: PostgreSQL bin이 PATH에 없음(정상 상태).
해결: 전체 경로로 호출. C:\Program Files\PostgreSQL\17\bin\psql.exe
```

### 7.4 `이 시스템에서 스크립트를 실행할 수 없으므로...` (.venv 활성화 실패)

```text
해결(현재 창에서만): Set-ExecutionPolicy -Scope Process -Bypass
그다음 다시: .\.venv\Scripts\Activate.ps1
```

### 7.5 원내 다른 기기(모바일 등)에서 접속이 안 됨

```text
확인 순서:
1. 접속 기기가 서버 PC와 같은 공유기 대역인가(게스트/분리 Wi-Fi 아님).
2. runserver가 해당 IP로 바인딩되었는가.
3. 서버 PC 방화벽이 해당 포트를 허용하는가.
→ 배포 시 실측 항목. 상세는 향후 보강.
```

---

## 8. 세팅 체크리스트 (요약)

```text
[ ] .venv 활성화됨 ( (.venv) 표시 )
[ ] where.exe python → .venv 경로
[ ] pip install -r requirements.txt 완료
[ ] python -m django --version → 6.0.6
[ ] .env 존재, POSTGRES_DB=gimpo365os_rehearsal
[ ] Select-String .env POSTGRES_DB 로 대상 DB 확인
[ ] python manage.py check 통과
[ ] python manage.py migrate 완료(리허설)
[ ] runserver 8001 → http://127.0.0.1:8001/ 접속
```

---

## 9. 향후 보강 필요 항목

```text
새 PC 최초 설치(Python/PostgreSQL/Git) 절차
운영 서버 상시 실행 방식(부팅 시 자동 실행, 서비스화 여부)
runserver 대신 운영용 WSGI 서버 사용 여부(waitress 등) 검토
원내 네트워크 바인딩·방화벽 실측 결과
DJANGO_DEBUG/ALLOWED_HOSTS 운영값 확정
운영/리허설 .env 전환을 안전하게 하는 방식
```
