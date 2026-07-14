# OS_DB_OPERATIONS.md

# 김포365OS DB 운영 문서

## 문서 버전

```text
문서명: OS_DB_OPERATIONS.md
문서 버전: v0.2
최종 수정일: 2026-07-08
문서 범위: 김포365OS의 DB 백업, 복구, migration 적용 절차
근거: OS_ENVIRONMENT_BASELINE.md v1.0, 실사용 backup_db.bat
```

## 변경 이력

| 버전 | 수정일 | 변경 요약 |
| --- | --- | --- |
| v0.2 | 2026-07-08 | 검토 반영: migration 절차에서 makemigrations 제거(--check --dry-run으로 대체), 운영 migrate 전 --plan 확인 추가, 백업의 읽기 전용·승인 성격 명시, --clean 위험 강화 및 임시 복구 DB 권장, pg_restore -l 표현 교정(1차 검증), 복구 백업 선택 기준·복구 후 QA 항목 추가 |
| v0.1 | 2026-07-08 | 실측 환경·실사용 백업 스크립트 기준 최초 작성. 백업/검증/복구/migration 절차, 리허설 우선 원칙 정의 |

---

## 1. 문서 목적

이 문서는 김포365OS의 **DB 백업·복구·migration 적용 실행 절차**를 정의한다.

원칙은 `OS_WORKING_RULES.md`와 `CLAUDE.md`에 있고, 이 문서는 그 원칙을 실제 명령으로 수행하는 절차서다.

환경값(경로·DB 이름·포트 등)은 이 문서에서 다시 정의하지 않고 `OS_ENVIRONMENT_BASELINE.md`를 기준으로 한다. 환경이 바뀌면 기준표를 먼저 고친다.

---

## 2. 대전제 (실행 전 항상)

```text
1. 운영 DB와 리허설 DB는 같은 PostgreSQL 17 인스턴스에 공존한다. .env의 POSTGRES_DB 한 줄로만 갈린다.
2. 어떤 DB 작업이든, 시작 전 현재 .env가 어느 DB를 가리키는지 확인한다.
3. 복구(restore)는 되돌릴 수 없는 유일한 작업이다. 운영에 바로 하지 않는다. 반드시 리허설에서 먼저.
4. 위험 작업 전에는 백업을 먼저 확보한다.
5. 운영 데이터는 삭제하지 않는다.
```

실행 전 필수 확인 (PowerShell, `gimpo365-os` 폴더):

```powershell
Select-String -Path .env -Pattern "POSTGRES_DB"
```

- 리허설 작업이면 `POSTGRES_DB=gimpo365os_rehearsal` 이어야 한다.
- 백업처럼 운영 DB를 대상으로 하는 작업은, 아래 3처럼 **명령 인자에서 DB 이름을 직접 지정**한다(.env에 의존하지 않는다).

---

## 3. 백업 (Backup)

백업 대상은 운영 DB `gimpo365_inventory`이다.

백업의 성격을 분명히 한다.

```text
백업은 운영 DB를 읽기만 하는 pg_dump 작업이다(수정·삭제 없음). 따라서 운영 DB를 변경하지 않는다.
백업은 Claude Code가 임의로 실행하는 작업이 아니다. 다빈 또는 지정 운영 담당자가 수행하는 승인된 운영 절차다.
백업 대상 DB 이름은 스크립트 인자에 직접 지정하며, .env에 의존하지 않는다.
```

### 3.1 현행 방식 — `backup_db.bat`

> `backup_db.bat` 실제 파일 위치: **(TODO — 확정 필요.** 현재 `gimpo365-inventory` 기준으로 사용 중. 저장소 내 위치를 확정해 여기 기재. `scripts/` 이관 여부도 함께 결정.)

현재 운영 백업은 실사용 스크립트 `backup_db.bat`로 수행한다. 이 스크립트는 다음을 한다.

```text
1. pg_dump로 운영 DB를 커스텀 포맷(-F c)으로 덤프
2. E:\gimpo365-backup\db 에 타임스탬프 파일로 저장
3. pg_restore -l 로 덤프 파일이 읽히는지 1차 검증(파일이 열리는지 수준)
4. 로그를 E:\gimpo365-backup\logs 에 저장
```

핵심 값(기준표 참조):

```text
pg_dump 경로 : C:\Program Files\PostgreSQL\17\bin\pg_dump.exe
백업 대상 DB : gimpo365_inventory (운영)
백업 저장 위치 : E:\gimpo365-backup\db
덤프 포맷 : custom (-F c)  → 복구는 반드시 pg_restore 사용 (5장)
```

### 3.2 백업 실행

```text
backup_db.bat 실행 → 완료 메시지와 저장 경로 확인
```

성공 시 다음을 확인한다.

```text
E:\gimpo365-backup\db 에 gimpo365_inventory_<타임스탬프>.dump 생성됨
로그 파일에 오류 없음
스크립트가 "백업 완료"로 종료됨 (검증 단계 pg_restore -l 통과)
```

### 3.3 백업 파일 읽기 가능 여부 1차 확인 (선택)

스크립트가 자동으로 수행하지만, 수동으로 다시 볼 때:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -l "E:\gimpo365-backup\db\<백업파일>.dump"
```

- 덤프 안의 객체 목록이 출력되면 파일이 **읽을 수 있는 상태**다. (파일 손상 1차 확인.)
- 오류가 나면 그 백업은 신뢰하지 않는다. 다시 백업을 뜬다.
- ⚠️ `pg_restore -l` 통과는 "파일이 읽힌다"까지만 보장한다. **실제 복구 가능 여부는 리허설 DB에 실제 복구해봐야 최종 확인된다(5.1).** 이 1차 검증만으로 복구 가능하다고 과신하지 않는다.

### 3.4 백업 시점 원칙

```text
운영 migration 적용 직전에는 반드시 백업.
운영 DB에 영향을 주는 위험 작업 직전에는 반드시 백업.
그 외 일상 백업은 최소 일 1회를 목표로 한다(현재 수동 실행).
```

---

## 4. 백업 보관과 리스크

현재 백업은 운영 PC 내부 `E:\gimpo365-backup\db`에 저장된다(수동 실행).

```text
⚠️ 리스크: 백업본이 운영 DB와 같은 물리 PC에 있다.
   이 PC 또는 저장장치가 고장나면 운영 DB와 백업이 함께 소실된다.
```

완화 방향:

```text
단기: 정기적으로 백업본을 외부 매체 또는 클라우드로 복사(수동이라도 병행).
중기: 원내 NAS 구축 후 원외 보관.
장기: 백업 자동화(Windows 작업 스케줄러) + 원외 복제 자동화.
```

자동화·원외 보관은 확정 후 이 문서에 절차로 추가한다(현재는 수동 기준).

---

## 5. 복구 (Restore) — 가장 위험, 리허설 우선

복구는 되돌릴 수 없다. 아래 순서를 반드시 지킨다.

```text
1. 복구는 먼저 리허설 DB(또는 임시 복구용 DB)에 수행해 내용을 확인한다.
2. 리허설에서 데이터가 정상임을 확인한 뒤에만 운영 복구를 검토한다.
3. 운영 복구는 반드시 별도 승인(다빈) 후, 직원 사용 중단 상태에서 수행한다.
4. 덤프가 custom 포맷(-F c)이므로 psql이 아니라 pg_restore로 복구한다.
5. 복구 중에는 대상 DB를 쓰는 서버(리허설 8001 / 운영 8000)와 직원 입력을 중단한다.
```

⚠️ `--clean --if-exists` 옵션의 위험:

```text
--clean 은 복구 전에 대상 DB의 기존 객체(테이블 등)를 DROP한다.
즉 -d 로 지정한 DB의 현재 내용을 삭제하고 덤프 내용으로 덮어쓴다.
-d 값이 운영을 가리키면 운영 데이터를 지운다. 실행 전 -d 값을 반드시 두 번 확인한다.
확인 목적의 복구라면, 기존 리허설을 건드리지 말고 아래 5.0의 임시 복구용 DB를 쓰는 것을 권장한다.
```

### 5.0 임시 복구용 DB 사용 (권장)

기존 리허설 데이터를 보존하면서 백업 내용만 확인하려면, 임시 DB를 새로 만들어 거기에 복구한다. 기존 리허설/운영을 건드리지 않는 가장 안전한 방법이다.

```powershell
# 임시 복구용 빈 DB 생성 (이름 예: gimpo365_restore_check)
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -c "CREATE DATABASE gimpo365_restore_check;"

# 임시 DB에 복구 (--clean 불필요: 빈 DB이므로)
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" `
  -h localhost -p 5432 -U postgres `
  -d gimpo365_restore_check `
  "E:\gimpo365-backup\db\<백업파일>.dump"

# 확인이 끝나면 임시 DB 삭제 (운영/리허설과 무관한 임시 DB만 삭제)
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -c "DROP DATABASE gimpo365_restore_check;"
```

- 임시 DB는 운영·리허설과 이름이 완전히 다르므로, 마지막 DROP이 운영/리허설을 건드릴 위험이 없다(그래도 실행 전 DB 이름을 눈으로 확인).

### 5.1 기존 리허설 DB에 직접 복구 (리허설을 운영과 동일 상태로 맞출 때만)

> 이 방식은 **기존 리허설 데이터를 삭제**하고 덮어쓴다. 단순 확인 목적이면 5.0(임시 DB)을 쓴다.
> 이 방식을 쓰기 전 확인: 현재 리허설 데이터를 보존할 필요가 없는가? 필요하면 먼저 리허설을 백업하거나 5.0으로 전환한다.

```powershell
# 복구 중에는 리허설 서버(8001)를 중단한 상태에서 수행
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" `
  -h localhost -p 5432 -U postgres `
  -d gimpo365os_rehearsal `
  --clean --if-exists `
  "E:\gimpo365-backup\db\<백업파일>.dump"
```

- `-d gimpo365os_rehearsal` : 복구 대상이 **리허설**임을 명시(운영 아님). 실행 전 이 값을 두 번 확인.
- `--clean --if-exists` : 기존 리허설 객체를 DROP 후 복구. **기존 리허설 데이터가 사라진다.**
- 복구 후 리허설 서버(8001)를 다시 올려 화면·데이터를 확인한다.

### 5.2 운영 DB로 복구 (예외적, 승인·중단 필수)

```text
전제:
- 다빈의 명시적 승인
- 직원 사용/입력 중단 상태
- 복구 직전 현재 운영 DB를 한 번 더 백업(현 상태 보존)
- 리허설에서 동일 덤프로 복구가 정상임을 이미 확인
```

명령 형태는 5.1과 같되 `-d gimpo365_inventory`(운영)로 바뀐다. **이 명령은 승인 전에 실행하지 않는다.** 절차·명령을 문서에 적어두되, 실제 실행은 사람이 판단한다.

```text
복구 후 smoke 확인:
- 운영 서버(8000) 접속·로그인
- OS 홈 표시
- 재고현황 화면 접근 가능
- 입고/출고 주요 화면 접근 가능
- 최근 데이터(복구 시점 근처의 거래·입출고 기록)가 존재하는지 확인
- 오류 화면 없음
- 이상 시 직전 백업본으로 재복구 검토
```

### 5.3 복구할 백업 파일 선택 기준

여러 백업 파일 중 어떤 것을 복구할지는 아래를 모두 만족하는 것으로 고른다.

```text
- 문제 발생 시점 이전의 가장 최근 정상 백업일 것
- pg_restore -l 통과(파일이 읽힘, 3.3)
- 해당 백업의 로그 파일(E:\gimpo365-backup\logs)에 오류가 없을 것
- 복구 시점·대상 파일을 다빈이 확인·승인했을 것
```

- 파일명이 타임스탬프(`gimpo365_inventory_<날짜_시간>.dump`)이므로, 복구하려는 시점을 파일명으로 특정한다.
- 가장 최근 파일이 항상 정답은 아니다. "문제가 생기기 전"의 정상 백업을 골라야 한다.

---

## 6. Migration 적용 절차

Migration은 김포365OS 성장에서 가장 큰 데이터 리스크다. 원칙(허용/주의/금지 종류)은 `OS_TECH_SPEC.md`·`OS_WORKING_RULES.md`에 있다. 이 장은 **실행 순서**만 다룬다.

> 전제: migration 파일 **생성**(`makemigrations`)은 개발 단계에서 이미 끝나 커밋된 상태다. DB 운영 절차는 **이미 커밋된 migration을 적용(`migrate`)**하는 것만 다룬다. 운영 절차 중 새 migration 파일을 만들지 않는다.

### 6.1 리허설 적용 (항상 먼저)

```powershell
# .env가 리허설을 가리키는지 먼저 확인
Select-String -Path .env -Pattern "POSTGRES_DB"   # = gimpo365os_rehearsal 이어야 함

.\.venv\Scripts\Activate.ps1

# (검증) 커밋 안 된 모델 변경이 남아 있지 않은지 확인 — 파일을 생성하지는 않음
python manage.py makemigrations --check --dry-run

# 이미 커밋된 migration을 적용
python manage.py migrate
python manage.py check
python manage.py test
```

- `makemigrations --check --dry-run`은 "생성할 migration이 남아 있는가"만 검사하고 **파일을 만들지 않는다.** 여기서 변경이 감지되면, 커밋되지 않은 모델 변경이 있다는 뜻이므로 운영 절차를 멈추고 개발 단계로 되돌아간다.
- 리허설에서 migration이 문제없이 적용되고 check/test가 통과해야 다음 단계로 간다.
- 리허설 화면(8001)에서 관련 기능·권한을 눈으로 확인한다.

### 6.2 운영 적용 (리허설 통과 후에만)

```text
순서:
1. 운영 DB 백업 (3장) — 필수
2. 직원 사용/입력 중단이 필요한지 판단
3. .env를 운영으로 전환하거나, 운영 환경에서 migrate 실행
   (같은 인스턴스이므로, 어느 DB에 적용되는지 POSTGRES_DB로 반드시 재확인)
4. python manage.py migrate --plan  ← 적용 전, 무엇이 적용될지 미리 확인
   (여기서 예상 밖 변경·파괴적 변경이 보이면 멈추고 재검토)
5. python manage.py migrate
6. python manage.py check
7. smoke QA (로그인 / OS홈 / inventory 진입 / 재고현황 / 관련 화면)
8. 이상 시 백업본 기준 복구 검토(5장)
```

- **파괴적 migration(컬럼 삭제/rename/type 변경, 테이블 삭제, non-null 필드 추가, 앱 이동 등)은 기본 금지.** 불가피하면 별도 승인·문서화 후, 위 절차에 "적용 전 추가 백업"과 "리허설에서 데이터 보존 확인"을 더해 수행한다.
- 운영 적용은 가능하면 새 테이블 추가·nullable 필드 추가 중심으로 설계한다.

---

## 6A. 운영 후보 DB 전환과 알파 운영기록 초기화 (P3-08A)

현재 배포 방향:

```text
- gimpo365os_prod : rehearsal 을 PostgreSQL TEMPLATE 방식으로 통째로 복제한 운영 후보 DB.
- 포트 8001 에서 gimpo365os_prod 로 팀장 교육·알파테스트를 진행한다.
- 별도의 데이터 마이그레이션은 하지 않는다.
- 알파테스트에서 입력한 기준정보(계정/부서/거래처/품목/관리품목/체크리스트/공지)는 정식 운영에 그대로 쓴다.
- 알파 운영기록(재고 거래·주문)만 초기화한 뒤, 실물 실사 → 최초재고 등록 → 같은 DB 를 8000 포트로 전환한다.
```

정식 운영 시작 직전, 기준정보는 보존하고 Inventory 운영기록만 비우는 전용 명령:

```powershell
# 1) 반드시 먼저 전체 백업 (backup_db.bat / §3)
# 2) 삭제·보존 예상 건수 + 가드 상태 검토 (DB 변경 없음)
python manage.py reset_alpha_transactions --dry-run

# 3) 다빈 승인 후 실제 실행:
#    (a) .env 에 ALLOW_ALPHA_TRANSACTION_RESET=true 설정 후 새 프로세스로 실행
#    (b) --confirm-db 값이 현재 연결 DB명과 정확히 일치해야 한다
python manage.py reset_alpha_transactions --yes --confirm-db gimpo365os_prod

# (선택) 완료 기록·로그인 세션도 함께 초기화
python manage.py reset_alpha_transactions --yes --confirm-db gimpo365os_prod --include-checklist-records --clear-sessions

# 4) 실행 후 즉시 ALLOW_ALPHA_TRANSACTION_RESET=false 로 복구 + Django 프로세스 재시작
```

```text
보존: Department / User(role·부서) / Supplier / Item / ManagedItem / ChecklistItem /
      DepartmentChecklistItem / Notice (+ migration/ContentType/Permission).
삭제(기본): StockTransaction / CartItem / OrderItem / Order (자식→부모, transaction.atomic).
현재고: 계산형(APPROVED quantity_delta 합계)이라 거래 삭제만으로 전 품목 0. 별도 초기화 불필요.
안전장치(세 조건 모두): 기본 dry-run / 실제 삭제는 --yes + --confirm-db<연결 DB명 일치>
      + ALLOW_ALPHA_TRANSACTION_RESET=true. 하나라도 불만족 시 무변경 거부.
      ALLOW_ALPHA_TRANSACTION_RESET 은 정식 운영에서도 DB명이 동일한 점을 보완하는 재실행 방지 가드다.
공지사항: 자동 삭제하지 않음(사람이 선별 삭제).
상세: docs/modules/inventory/RESET_ALPHA_TRANSACTIONS_SPEC.md
```

`flush` 금지:

```text
정식 운영 전환 과정에서 python manage.py flush 를 사용하지 않는다.
flush 는 사용자·부서·품목 등 기준정보까지 삭제하므로 이번 운영 절차와 맞지 않는다.
```

> 참고: 기존 `reset_operational_data`(DEBUG 가드 + --allow-production)도 같은 삭제 범위를 갖는다.
> `reset_alpha_transactions` 는 운영 후보(DEBUG=False 가능) DB 를 위해 **--confirm-db 연결명 일치**를
> 안전장치로 쓰고, --include-checklist-records / --clear-sessions / 현재고 0 자동 검증을 추가로 제공한다.

---

## 7. 위험 명령 주의

```text
DROP DATABASE / DROP TABLE / TRUNCATE : 운영에서 사용 금지.
psql로 custom 포맷 덤프 복구 시도 금지 : -F c 덤프는 pg_restore 전용.
--clean 옵션은 대상 DB 객체를 지운다 : 대상이 리허설인지 운영인지 -d 값을 두 번 확인.
운영 DB를 대상으로 한 실험/테스트 금지.
DB 비밀번호·pgpass 정보를 로그·커밋·출력에 남기지 않는다.
```

---

## 8. 빠른 참조 (Cheat Sheet)

```text
[백업]         backup_db.bat  →  E:\gimpo365-backup\db\*.dump  (읽기 가능 1차 검증 포함)
[백업 1차검증]  pg_restore -l "<파일>.dump"   (파일이 읽히는지까지만)
[확인용 복구]   임시 DB 생성 → pg_restore -d gimpo365_restore_check "<파일>.dump" → 확인 후 DROP  (5.0, 가장 안전)
[리허설 복구]   (기존 리허설 삭제됨, 8001 중단) pg_restore -d gimpo365os_rehearsal --clean --if-exists "<파일>.dump"
[운영 복구]     (승인·중단 필수, -d 두 번 확인) pg_restore -d gimpo365_inventory ...
[migration]    리허설: makemigrations --check --dry-run → migrate → check/test
              운영: 백업 → migrate --plan → migrate → check → smoke
[알파리셋]      백업 → --dry-run → 승인 → ALLOW_ALPHA_TRANSACTION_RESET=true(새 프로세스) → --yes --confirm-db gimpo365os_prod → 즉시 false 복구·재시작 (flush 금지)
[항상]          작업 전 Select-String .env POSTGRES_DB 로 대상 DB 확인. --clean 쓸 땐 -d 값 두 번 확인.
```

> pg_dump / pg_restore / psql 전체 경로: `C:\Program Files\PostgreSQL\17\bin\` (기준표 §5)

---

## 9. 향후 보강 필요 항목

```text
백업 자동화(작업 스케줄러) 등록 절차
백업 원외 보관(NAS/클라우드) 절차
백업 보관 주기·세대 관리(며칠치 보관, 오래된 것 정리)
운영 복구 실제 리허설 결과 기록
migration 실패 시 롤백 상세 사례
```
