# RESET_ALPHA_TRANSACTIONS_SPEC.md

알파 운영기록 초기화 명령(`reset_alpha_transactions`) 사양. (P3-08A-01)

## 문서 버전

```text
문서명: docs/modules/inventory/RESET_ALPHA_TRANSACTIONS_SPEC.md
최종 수정일: 2026-07-14
대상 명령: inventory/management/commands/reset_alpha_transactions.py
```

---

## 1. 목적

`gimpo365os_prod`(리허설 복제본)에서 팀장 알파테스트를 마친 뒤, **정식 운영 시작 직전**에
기준정보는 보존하고 알파테스트 중 쌓인 **Inventory 운영기록만** 물리적으로 초기화한다.

정식 운영 개시 전 모든 관리품목의 현재고를 0 으로 되돌려, 실물 실사 → 최초재고 입력의
깨끗한 출발점을 만드는 것이 목표다.

이 명령은 `python manage.py flush`(사용자·부서·품목 등 기준정보까지 삭제)를 **대체**한다.
정식 운영 전환 과정에서 `flush` 는 사용하지 않는다.

## 2. 사용 시점

```text
알파테스트 종료 → 입력 중단 → prod 전체 백업 → reset_alpha_transactions --dry-run 검토
→ 다빈 승인 → --yes --confirm-db 실제 실행 → 현재고 0 확인 → 실물 실사/최초재고 등록
```

배포 전 **1회 유지보수 예외**로 실행한다. 일상 운영 중에는 사용하지 않는다.

## 3. 유지 데이터 (절대 보존 — 명령 전후 건수 동일)

```text
Department, User(role·department 포함), Supplier, Item, ManagedItem,
ChecklistItem, DepartmentChecklistItem, Notice(공지사항),
Django migration 기록, ContentType, Permission
```

공지사항은 자동 삭제하지 않는다. 테스트 공지는 사람이 제목·내용을 확인 후 선별 삭제한다.

## 4. 삭제 데이터 (기본)

Inventory 운영기록만 삭제한다.

```text
StockTransaction   재고 거래 원장(입고/출고/최초재고/실사조정, 승인/반려/취소/철회 상태 포함)
CartItem           주문 장바구니 항목
OrderItem          주문 품목(잔여마감 포함)
Order              주문
```

승인·반려·취소·철회는 별도 모델이 아니라 `StockTransaction.status` 값이다.
따라서 상태와 무관하게 StockTransaction 을 전부 삭제하면 관련 기록이 함께 제거된다.

## 5. 선택 삭제 데이터

```text
--include-checklist-records   ChecklistRecord(완료 기록) 삭제. ChecklistItem/DepartmentChecklistItem 유지.
--clear-sessions              django_session(로그인 세션) 삭제. User 유지.
```

공지사항 삭제 옵션은 제공하지 않는다.

## 6. 모델별 삭제 순서

FK PROTECT 제약을 지키기 위해 **자식 → 부모** 순서로 삭제한다.
특히 `StockTransaction.source_order_item → OrderItem` 이 PROTECT 이므로 StockTransaction 을 먼저 삭제한다.

```text
1. StockTransaction        (OrderItem/ManagedItem/Supplier/User 를 PROTECT 로 참조 → 가장 먼저)
2. CartItem
3. OrderItem               (StockTransaction 삭제 후 PROTECT 해제됨)
4. Order
5. ChecklistRecord         (--include-checklist-records 일 때만)
6. Session                 (--clear-sessions 일 때만)
```

## 7. 모델 분류표

| 모델명 | 분류 | 기본 동작 | 근거 |
| --- | --- | --- | --- |
| Department (core) | A 기준정보(조직) | 보존 | 부서 |
| User (accounts) | A 기준정보(조직) | 보존 | 계정·role·department |
| Supplier | A 기준정보 | 보존 | 공급업체 마스터 |
| Item | A 기준정보 | 보존 | 품목 마스터 |
| ManagedItem | B 관리품목·설정 | 보존 | 부서별 관리품목/단위/최소재고/보관위치 |
| ChecklistItem | A 기준정보 | 보존 | 체크리스트 항목 정의 |
| DepartmentChecklistItem | A 기준정보 | 보존 | 항목의 부서 배정 |
| Notice | A 기준정보(운영) | 보존 | 공지사항(사람 선별 삭제) |
| StockTransaction | C 거래 | 삭제 | 재고 변동 원장 |
| Order | E 하위 운영기록 | 삭제 | 주문 |
| OrderItem | E 하위 운영기록 | 삭제 | 주문 품목 |
| CartItem | E 하위 운영기록 | 삭제 | 장바구니 항목 |
| ChecklistRecord | 선택 | 옵션 삭제 | 완료 기록 |
| Session | 선택 | 옵션 삭제 | 로그인 세션 |
| OrderCart | 컨테이너 | 보존 | 사용자별 빈 장바구니(재사용). CartItem 만 삭제 |

> D(조정·승인·상태변경 전용 모델)와 F(현재고 저장/캐시 모델)는 이 코드베이스에 **존재하지 않는다.**
> 승인/반려/취소는 StockTransaction.status, 현재고는 계산형이다(§7 현재고 초기화 원리).

## 8. 현재고 초기화 원리

현재고는 **계산형**이다. 별도 저장 필드·캐시 테이블이 없다.

```text
현재고 = 해당 ManagedItem 의 APPROVED StockTransaction.quantity_delta 합계
         (inventory/selectors.py get_current_stock / _annotate_current_stock)
```

따라서 StockTransaction 을 전부 삭제하면 모든 관리품목 현재고가 **자동으로 0** 이 된다.
별도의 현재고 초기화·캐시 무효화 단계는 필요 없다.

## 9. 안전장치

실제 삭제는 아래 **세 조건을 모두** 만족할 때만 수행된다(파괴적 작업 전에 transaction 진입 없이 검사).

```text
검사 순서:
1. --dry-run 여부 확인      (dry-run 이면 무변경 후 종료. 가드와 무관)
2. --yes 확인
3. --confirm-db 확인 + 현재 연결 DB명(connection.settings_dict["NAME"])과 정확히 일치 확인
4. settings.ALLOW_ALPHA_TRANSACTION_RESET is True 확인
5. transaction.atomic 진입 → 삭제 실행

하나라도 불만족이면 데이터 변경 없이 CommandError 로 차단한다.
- --dry-run 을 함께 주면 --yes 가 있어도 삭제하지 않는다.
- 전체 삭제는 하나의 transaction.atomic 안에서 수행, 중간 오류 시 전체 rollback.
```

### 9.1 운영 재실행 방지 가드 — `ALLOW_ALPHA_TRANSACTION_RESET`

정식 운영에서도 DB명은 계속 `gimpo365os_prod` 이므로, `--confirm-db` 만으로는 정식 운영 이후
실수 재실행을 막지 못한다. 이를 위해 **DB명과 별개의 독립 환경변수 가드**를 둔다.

```text
환경변수: ALLOW_ALPHA_TRANSACTION_RESET  (config/settings.py 에서 env.bool, 기본 False)
- False(기본): 실제 삭제 불가. dry-run 은 가능.
- True: 실제 삭제 가능(다른 두 조건도 만족해야 함).
- 특정 DB 이름을 코드에 하드코딩하지 않는다(운영 DB명이 바뀌거나 테스트 DB 여도 동작해야 하므로).
- 가드 비활성 상태에서 실제 실행 시:
    CommandError: 알파 운영기록 초기화가 비활성화되어 있습니다.
    실행 전 ALLOW_ALPHA_TRANSACTION_RESET=true 를 명시적으로 설정해야 합니다.
```

> 이 명령은 `settings.DEBUG` 가드를 두지 않는다. 대상 DB(`gimpo365os_prod`)가 정식 운영 후보로서
> DEBUG=False 로 구동될 수 있기 때문이다. 안전장치는 **연결 DB명 정확 일치(--confirm-db) +
> ALLOW_ALPHA_TRANSACTION_RESET=true + 전체 백업 + 다빈 승인**이다.
> 기존 `reset_operational_data`(DEBUG 가드 + --allow-production)와는 안전 모델이 다르다(§역할 구분).

## 10. dry-run 출력

```text
[reset_alpha_transactions] DRY RUN

현재 데이터베이스:
- gimpo365os_prod

실제 실행 허용 설정:
- ALLOW_ALPHA_TRANSACTION_RESET: 비활성

보존 예정:
- Department: 6
- User: 21
- Supplier: 34
- Item: 284
- ManagedItem: 411
- ChecklistItem: 27
- DepartmentChecklistItem: 61
- Notice: 12

삭제 예정:
- StockTransaction: 187
- CartItem: 5
- OrderItem: 29
- Order: 14

선택 대상:
- ChecklistRecord: 43 (미선택)
- Session: 8 (미선택)

예상 결과:
- 관리품목 수: 411 유지
- 예상 현재고: 전부 0
- DB 변경: 없음
```

## 11. 실행 전 백업

```text
- reset 실행 전 gimpo365os_prod 전체 백업(pg_dump 등)을 반드시 확보한다.
- 백업 없이 실제 실행하지 않는다. 절차는 OS_DB_OPERATIONS.md 를 따른다.
```

## 12. 실행 후 검증

명령이 COMPLETE 출력에서 자동 검증한다.

```text
- 거래기록(StockTransaction): 0
- 최대 현재고: 0
- 기준정보 건수 일치: 예
```

추가로 관리자가 재고현황 화면에서 전 품목 현재고 0 을 육안 확인한다.

## 13. 실패 시 롤백

```text
- 삭제 중 오류 발생 시 transaction.atomic 이 전체를 rollback → 부분 삭제 상태가 남지 않는다.
- 명령은 실패 단계·모델을 출력한다.
- DB 손상이 의심되면 §11 백업본으로 복구한다(OS_DB_OPERATIONS.md).
```

## 14. 정식 운영 전환 절차

`OS_OPERATIONS_SETUP.md` / `OS_DB_OPERATIONS.md` 의 배포 전환 절차를 따른다. 요약:

```text
1. 8001 포트 알파테스트 → 실제 기준정보(계정/부서/거래처/품목/관리품목/공지/체크리스트) 입력
2. 알파 종료 공지 → 모든 입력 중단
3. gimpo365os_prod 전체 백업
4. reset_alpha_transactions --dry-run 으로 삭제·보존 예상 건수 + 가드 상태 검토
5. 다빈 최종 승인 후:
   (a) .env 에 ALLOW_ALPHA_TRANSACTION_RESET=true 설정
   (b) 새 프로세스로 python manage.py reset_alpha_transactions --yes --confirm-db gimpo365os_prod 실행
6. 기준정보 건수·현재고 0 검증
7. ALLOW_ALPHA_TRANSACTION_RESET=false 로 즉시 복구 + Django 프로세스 재시작
8. 실물 재고 실사 → 최초재고 입력/승인
9. 테스트 공지·임시 계정 선별 정리, 필요 시 --clear-sessions(이때도 5~7 절차 동일)
10. 최종 백업 → 8001 종료 → 동일 DB 를 8000 포트로 구동 → 정식 운영
```

### 14.1 실제 실행 필수 조건

```text
1. 알파테스트 입력 중지
2. gimpo365os_prod 전체 백업 완료
3. dry-run 결과 검토(삭제·보존 건수 + 가드 상태)
4. ALLOW_ALPHA_TRANSACTION_RESET=true
5. --yes
6. --confirm-db <현재 연결 DB명>
7. 다빈 최종 승인
```

### 14.2 실행 후 즉시 조치

```text
1. 기준정보 보존 확인
2. 거래기록 0 확인
3. 현재고 0 확인
4. ALLOW_ALPHA_TRANSACTION_RESET=false 로 복구
5. Django 프로세스 재시작
```

> 환경변수는 실행 중인 Django 프로세스에 자동 반영되지 않는다. 설정을 바꾼 뒤에는 **새 프로세스로**
> 명령을 실행해야 하며(활성화), 실행 후 false 로 되돌린 뒤에도 **프로세스를 재시작**해야 반영된다.

### 14.3 정식 운영 중 규칙

```text
- ALLOW_ALPHA_TRANSACTION_RESET=false 유지.
- 환경변수 활성화 금지. reset_alpha_transactions 실제 실행 금지.
- dry-run 은 진단 목적으로만 허용.
```

## 15. `reset_operational_data` 와의 역할 구분

같은 삭제 범위(StockTransaction/CartItem/OrderItem/Order)를 갖는 기존 명령 `reset_operational_data`
가 있으나, 두 명령은 역할이 다르며 통합하지 않는다.

```text
reset_operational_data
- 기존 개발·운영 보조 명령. CLAUDE.md 보호 대상.
- 안전 모델: DEBUG 가드 + --allow-production.
- 이번 OS 운영 후보 DB 알파 종료 절차에서는 사용하지 않는다.

reset_alpha_transactions
- OS 운영 후보 DB(gimpo365os_prod) 알파테스트 종료 전용. 이번 전환 과정의 공식 명령.
- 안전 모델: --confirm-db(연결 DB명 일치) + ALLOW_ALPHA_TRANSACTION_RESET 가드.
- 추가: --include-checklist-records / --clear-sessions / 현재고 0 자동 검증.
```

두 명령의 통합·`reset_operational_data` 수정/삭제·DEBUG 가드 변경은 하지 않는다.
관리 명령 중복 정리는 향후 별도 작업으로 미룬다.
