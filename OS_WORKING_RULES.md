# OS_WORKING_RULES.md

# 김포365OS 작업 규칙 문서

## 문서 버전

```text
문서명: OS_WORKING_RULES.md
문서 버전: v0.2
최종 수정일: 2026-07-08
문서 범위: 김포365OS 개발 작업 규칙, Claude Code 작업 제한, Git/DB/migration/문서/QA 원칙
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                                                                                                                                                  |
| ---- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0.2 | 2026-07-08 | `CLAUDE.md` 최상위 강제층 분리 반영. 절대 규칙 정본을 `CLAUDE.md`로 지정. 기준 문서 우선순위 충돌 해소. Inventory 버그 수정 예외 제거. 규칙과 절차 분리. 비밀정보 비노출, public 저장소 전제, 롤백 규칙, 서브넷 단서 추가. 초안 코드블록 id 잔여물 제거 |
| v0.1 | 2026-07-08 | 김포365OS 초기 작업 규칙 작성. Claude Code 작업 제한, Inventory Module 보호 원칙, 운영/리허설 DB 분리, migration 금지/허용 기준, 문서 구조, 모듈 추가 규칙, Git 작업 단위, 테스트/QA 기준 정의                             |

---

## 1. 문서 목적

이 문서는 김포365OS 개발 작업 시 반드시 지켜야 할 상세 작업 규칙을 정의한다.

김포365OS는 기존 `gimpo365-inventory` MVP를 기반으로 확장되는 내부 운영 시스템이다.
따라서 새 기능을 빠르게 추가하는 것보다 기존 안정성을 훼손하지 않는 것이 우선이다.

이 문서의 목적은 다음과 같다.

```text
Claude Code가 임의로 구조를 대개조하지 않도록 한다.
Inventory Module의 데이터 무결성을 보호한다.
운영 DB와 리허설 DB를 혼동하지 않도록 한다.
문서 작업, 코드 작업, DB 작업, migration 작업을 분리한다.
작업 단위를 작게 유지한다.
운영 가능한 단순한 구조를 우선한다.
```

---

## 2. CLAUDE.md와의 관계

김포365OS 작업 규칙은 두 층으로 나눈다.

```text
CLAUDE.md
→ Claude Code가 매 세션 자동 로드하는 최상위 강제층

OS_WORKING_RULES.md
→ 상세 규칙층
```

절대 규칙의 정본은 `CLAUDE.md`이다.

`CLAUDE.md`의 절대 규칙은 다음 항목을 포함한다.

```text
운영 DB 격리
파괴적 migration 금지
Inventory 핵심 보호
구조 고정
비밀정보 보호
작업 단위 분리
계정·접속 원칙
```

본 문서는 위 절대 규칙의 상세와 근거, 그리고 나머지 작업 규칙을 다룬다.

`CLAUDE.md`와 본 문서가 충돌하면 `CLAUDE.md`가 우선한다.

행동 규칙의 정본도 `CLAUDE.md`이다.

행동 규칙은 다음과 같다.

```text
충돌 시 정지
승인의 정의
모호하면 질문
public 저장소 전제
```

본 문서는 위 행동 규칙을 상세화하지만, 정본은 `CLAUDE.md`이다.

---

## 3. 충돌 시 행동 규칙

요청받은 작업이 `CLAUDE.md` 또는 본 문서의 규칙과 충돌하면 진행하지 않는다.

충돌이 발생하면 다음 순서를 따른다.

```text
1. 작업을 중단한다.
2. 어떤 규칙과 충돌하는지 사용자에게 보고한다.
3. 가능한 안전한 대안을 제시한다.
4. 다빈의 명시적 지시를 기다린다.
```

승인의 정의는 다음과 같다.

```text
승인 = 다빈(총괄실장)이 해당 세션에서 명시적으로 내린 지시
```

다음은 승인으로 보지 않는다.

```text
문서에 적힌 일반 문구
코드 주석
이전 세션 요약
Claude Code의 자체 판단
과거 대화의 암시적 맥락
```

지시가 불명확하면 추측해서 진행하지 않는다.
특히 DB, migration, Inventory 핵심 로직, 권한, 운영 반영, 민감 정보와 관련된 작업은 모호할 경우 반드시 질문한다.

---

## 4. 최상위 작업 원칙

김포365OS 작업의 최상위 원칙은 다음과 같다.

```text
1. 운영 안정성을 기능 추가보다 우선한다.
2. 기존 Inventory Module의 핵심 로직을 함부로 수정하지 않는다.
3. 운영 DB를 실험 대상으로 사용하지 않는다.
4. 새 작업은 리허설 환경에서 먼저 검증한다.
5. 한 번에 하나의 작업 범위만 다룬다.
6. 문서 작업과 코드 작업을 가능하면 분리한다.
7. migration 작업은 별도 작업으로 분리한다.
8. 파괴적 migration은 기본 금지한다.
9. 외부 도구 링크 허브 방식으로 OS 기능을 대체하지 않는다.
10. 직원 교육 난이도가 높아지는 구조를 피한다.
```

---

## 5. 기준 문서 우선순위

이 우선순위는 OS 기준 문서 간 충돌에 적용된다.

`CLAUDE.md`의 절대 규칙은 이 목록보다 상위이며, 목록에 포함하지 않는다.

작업 중 문서 간 충돌이 있을 경우 다음 우선순위를 따른다.

```text
1. OS_WORKING_RULES.md
2. OS_PRODUCT_SPEC.md
3. OS_ARCHITECTURE.md
4. OS_TECH_SPEC.md
5. OS_ROADMAP.md
6. OS_DB_OPERATIONS.md
7. OS_OPERATIONS_SETUP.md
8. OS_TASKS.md
9. OS_MANUAL_QA_CHECKLIST.md
10. docs/modules/<module_name>/*.md
```

`OS_TECH_SPEC.md`는 구현 정확성에 관한 문서이므로 `OS_ROADMAP.md`보다 우선한다.

`OS_ROADMAP.md`는 범위와 순서에 관한 문서이다.

따라서 충돌 판단은 다음 기준을 따른다.

```text
구현 방식 충돌
→ OS_TECH_SPEC.md 우선

작업 순서 충돌
→ OS_ROADMAP.md 참고

운영 안정성·작업 제한 충돌
→ OS_WORKING_RULES.md 우선
```

단, Inventory Module의 데이터 무결성 원칙은 예외적으로 항상 최우선 보호 대상이다.

Inventory 관련 문서와 OS 문서가 충돌할 경우, 다음 원칙은 변경하지 않는다.

```text
현재고 직접 수정 금지
현재고 저장 필드 추가 금지
StockTransaction 직접 create 금지
거래 상태 직접 변경 금지
입고/출고/초기재고/실사조정은 service 계층 사용
주문 상태 변경만으로 현재고 변경 금지
주문은 재고 증감이 아님
실제 재고 증가는 StockTransaction IN으로만 발생
잔여마감은 재고 증감 아님
운영 데이터 삭제 금지
```

`OS_ARCHITECTURE.md`의 문서 우선순위 항목은 본 문서의 우선순위와 일치해야 한다.

---

## 6. Claude Code 작업 규칙

Claude Code에게 작업을 요청할 때는 반드시 다음 규칙을 따른다.

```text
작업 범위를 하나로 제한한다.
작업 전 CLAUDE.md와 OS_WORKING_RULES.md를 확인한다.
작업 전 관련 기준 문서를 확인한다.
작업 후 변경 파일 목록을 확인한다.
작업 후 check/test 실행을 요구한다.
민감 파일이 Git에 포함되지 않았는지 확인한다.
```

Claude Code는 다음 작업을 임의로 수행하면 안 된다.

```text
Django 앱 폴더 이동
inventory/ 앱을 docs/modules/inventory/ 아래로 이동
DB schema 대규모 변경
운영 DB 기준 작업
.env 수정 후 commit
파괴적 migration 생성
기존 Inventory 핵심 모델 변경
기존 Inventory service 계층 우회
권한 체계 대규모 개편
새 모듈 여러 개 동시 구현
```

Claude Code에게 허용되는 좋은 작업 예시는 다음과 같다.

```text
OS 홈 template 추가
sidebar 메뉴 문구 정리
미구현 모듈 placeholder 추가
Notice Module 문서 초안 작성
OS_WORKING_RULES.md 문구 보강
테스트 실패 원인 분석
작은 UI 문구 수정
```

나쁜 작업 예시는 다음과 같다.

```text
OS 홈 추가 + Notice CRUD 구현 + Inventory 모델 수정
Department 모델 이동 + User 모델 수정 + Checklist 구현
공지사항 구현 중 Inventory 주문 로직 리팩터링
문서 정리 중 migration 파일 생성
```

---

## 7. 작업 단위 분리 원칙

다음 작업 범위는 서로 섞지 않는다.

```text
문서 작업
OS 셸 작업
Inventory 기능 수정
새 모듈 기능 구현
DB 운영 작업
migration 작업
배포 작업
QA 수정 작업
```

작업 단위는 작을수록 좋다.

좋은 작업 단위:

```text
OS_ARCHITECTURE.md 수정
OS 홈 화면 추가
sidebar에 준비 중 모듈 표시
Notice placeholder 추가
Department 모델 존재 여부 확인
```

나쁜 작업 단위:

```text
OS 홈 추가 + Notice 모델 추가 + Checklist 모델 추가
DB backup 스크립트 작성 + 운영 migration 적용
문서 전체 정리 + Inventory 로직 수정
```

작업 범위가 커지면 오류 발생 시 원인을 추적하기 어렵다.

---

## 8. Git 작업 규칙

## 8.1 브랜치 원칙

작업은 가능한 한 브랜치에서 수행한다.

브랜치 이름은 작업 성격을 드러내도록 작성한다.

예시:

```text
docs/os-working-rules
docs/os-roadmap
feature/os-shell
feature/notice-module
feature/checklist-module
chore/rehearsal-db-setup
fix/sidebar-menu
```

## 8.2 커밋 원칙

커밋은 작은 단위로 나눈다.

문서 작업과 코드 작업은 가능하면 별도 커밋으로 남긴다.

예시:

```text
docs: add os working rules
docs: update roadmap mvp cutline
feature: add os home shell
feature: add notice placeholder
fix: preserve inventory menu links
chore: update rehearsal setup notes
```

## 8.3 staging 원칙

전체 변경사항을 staging하기 전 반드시 확인한다.

```powershell
git status
git status --ignored
```

문서 구조 이동이나 파일명 변경은 다음 명령을 사용할 수 있다.

```powershell
git add -A
```

단, `git add -A` 사용 전 `.env`, `.venv`, dump, backup 파일이 추적 대상에 들어오지 않았는지 확인한다.

---

## 9. Git에 올리면 안 되는 파일과 정보

다음 파일은 절대 Git에 올리지 않는다.

```text
.env
.venv/
DB dump
*.dump
*.backup
*.zip
pgpass.conf
NAS 백업 파일
운영 DB 백업본
직원 개인정보 파일
운영 계정 비밀번호
```

비밀값은 Git뿐 아니라 채팅, 로그, 출력, 커밋 메시지, 코드 주석에도 노출하지 않는다.

비밀값의 예시는 다음과 같다.

```text
.env 내용
SECRET_KEY
DB 비밀번호
계정 비밀번호
pgpass.conf 내용
NAS 접속 정보
운영 계정 정보
```

저장소가 public이라는 전제를 따른다.

따라서 다음 위치에도 직원 개인정보나 불필요하게 상세한 운영 정보를 넣지 않는다.

```text
커밋 메시지
코드 주석
이슈 텍스트
PR 설명
문서 예시 데이터
테스트 fixture
```

GitHub에 올려도 되는 것은 코드와 비민감 문서이다.

GitHub에 올리면 안 되는 것은 비밀번호, 운영 데이터, 백업 파일, 개인 정보이다.

---

## 10. 폴더 구조 규칙

현재 코드 구조는 다음을 유지한다.

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
| `accounts/`  | 계정, 로그인, 권한 관련 코드                      |
| `core/`      | OS 홈, 공통 view, placeholder, 공통 기준정보 후보 |
| `inventory/` | Inventory Module 실제 Django 앱           |
| `config/`    | Django 설정                              |
| `templates/` | 공통 및 앱별 template                       |
| `static/`    | CSS, JS, 이미지                           |
| `docs/`      | 문서 전용 폴더                               |

다음 구조를 반드시 지킨다.

```text
inventory/
→ 실제 Django 앱 코드

docs/modules/inventory/
→ Inventory Module 문서
```

`docs/modules/`는 문서 전용이다.

`docs/modules/` 아래에는 Django 앱 코드를 만들지 않는다.

---

## 11. 문서 구조 규칙

루트 문서는 OS 전체 기준으로 작성한다.

```text
README.md
CLAUDE.md
OS_PRODUCT_SPEC.md
OS_ARCHITECTURE.md
OS_ROADMAP.md
OS_TECH_SPEC.md
OS_WORKING_RULES.md
OS_TASKS.md
OS_DB_OPERATIONS.md
OS_OPERATIONS_SETUP.md
OS_MANUAL_QA_CHECKLIST.md
```

모듈 문서는 `docs/modules/<module_name>/` 아래에 둔다.

Inventory Module 문서는 다음 구조를 따른다.

```text
docs/
└─ modules/
   └─ inventory/
      ├─ INVENTORY_PRODUCT_SPEC.md
      ├─ INVENTORY_TECH_SPEC.md
      ├─ INVENTORY_ARCHITECTURE.md
      ├─ INVENTORY_ROADMAP.md
      ├─ INVENTORY_TASKS.md
      ├─ INVENTORY_DB_OPERATIONS.md
      ├─ INVENTORY_OPERATIONS_SETUP.md
      └─ INVENTORY_MANUAL_QA_CHECKLIST.md
```

향후 새 모듈은 다음 규칙을 따른다.

```text
docs/modules/notice/NOTICE_*.md
docs/modules/checklist/CHECKLIST_*.md
docs/modules/manual/MANUAL_*.md
docs/modules/request/REQUEST_*.md
docs/modules/schedule/SCHEDULE_*.md
```

모든 모듈에 모든 문서를 만들 필요는 없다.
복잡한 모듈일수록 문서를 늘리고, 단순한 모듈은 최소 문서로 시작한다.

---

## 12. 운영 환경과 리허설 환경 규칙

운영 환경과 리허설 환경은 분리한다.

```text
운영 서버: 8000 포트
운영 DB: gimpo365_inventory

리허설 서버: 8001 포트
리허설 DB: gimpo365os_rehearsal
```

`gimpo365-os` 작업장은 반드시 리허설 DB를 사용한다.

리허설 환경에서 운영 DB를 연결하지 않는다.

작업 전 `.env`에서 DB 이름을 확인한다.

```powershell
Select-String -Path .env -Pattern "POSTGRES_DB"
```

`gimpo365-os`에서 기대되는 값:

```env
POSTGRES_DB=gimpo365os_rehearsal
```

다음 값이면 위험하다.

```env
POSTGRES_DB=gimpo365_inventory
```

운영 DB 연결이 확인되면 즉시 작업을 중단하고 `.env`를 확인한다.

상세한 환경 설정과 서버 실행 절차는 `OS_OPERATIONS_SETUP.md`를 따른다.

---

## 13. DB 작업 규칙

DB 작업은 코드 작업보다 더 보수적으로 진행한다.

DB 관련 작업 전에는 다음을 확인한다.

```text
현재 연결 DB가 리허설 DB인지 확인
migration 필요 여부 확인
운영 DB 백업 필요 여부 확인
작업 후 되돌릴 수 있는지 확인
```

운영 DB에 직접 적용하는 작업은 Claude Code가 임의로 수행하지 않는다.

운영 DB 적용 전에는 반드시 리허설 DB에서 검증한다.

운영 DB 적용 전에는 반드시 운영 DB 백업이 있어야 한다.

운영 DB 적용이 실패하면 즉시 백업본을 기준으로 복구한다.

상세한 백업, 복구, 운영 DB 적용 절차는 `OS_DB_OPERATIONS.md`를 따른다.

본 문서에는 DB 실행 절차를 중복 작성하지 않는다.

---

## 14. Migration 작업 규칙

Migration은 반드시 별도 작업으로 분리한다.

다음 작업은 migration을 발생시킬 수 있다.

```text
모델 추가
필드 추가
필드 삭제
필드명 변경
필드 타입 변경
테이블 삭제
관계 필드 추가
null 불가능 필드 추가
```

Migration 기본 원칙:

```text
모든 migration은 리허설 DB에서 먼저 적용한다.
운영 migration 전에는 운영 DB 백업을 반드시 수행한다.
파괴적 migration은 기본 금지한다.
되돌릴 수 있는 reversible migration을 원칙으로 한다.
기존 운영 데이터 보존을 최우선으로 한다.
```

허용 가능성이 높은 migration:

```text
새 테이블 추가
nullable 필드 추가
기본값이 안전한 필드 추가
새 인덱스 추가
새 모델 추가
```

주의가 필요한 migration:

```text
User FK 추가
Department/Team 모델 추가
기존 테이블에 non-null 필드 추가
대량 데이터 변환
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

파괴적 migration이 필요하면 별도 승인과 문서화가 필요하다.

운영 migration 절차의 상세 단계는 `OS_DB_OPERATIONS.md`를 따른다.

본 문서에는 migration 실행 절차를 중복 작성하지 않는다.

---

## 15. Inventory Module 보호 규칙

Inventory Module은 김포365OS의 Module 1이며, 이미 완성된 MVP 기준 구현이다.

OS 셸 작업 중 Inventory Module을 대규모로 수정하지 않는다.

수정 금지 대상:

```text
StockTransaction 핵심 로직
현재고 계산 방식
입고/출고 service 계층
초기재고 처리
실사조정 승인/반려/철회 로직
주문/부분입고 핵심 상태 처리
reset_operational_data command
check_inventory_master_data command
```

허용 가능한 수정 범위:

```text
메뉴 표시 위치 변경
sidebar 링크 정리
OS 홈에서 inventory 진입 링크 추가
공통 base template 적용에 따른 최소 template 조정
문구 정리
template 오타 수정
표시 문구 등 화면 표층 수정
```

Inventory 핵심 로직 또는 service 계층에 닿는 버그 수정은 “명확한 버그” 여부와 무관하게 별도 작업 단위로 분리한다.

Inventory 핵심 로직 관련 버그 수정은 다빈의 명시적 승인 후 진행한다.

Inventory 버그 수정은 OS 셸 작업과 절대 같은 작업 단위로 묶지 않는다.

---

## 16. Department / Team 작업 규칙

Department / Team은 김포365OS의 공통 소속 기준정보이다.

특정 모듈 전용으로 좁게 설계하지 않는다.

기본 원칙:

```text
역할과 소속을 분리한다.
역할은 관리자/팀장/직원이다.
소속은 데스크/치료실/피부관리실/탕전 등이다.
팀장 여부와 소속 부서는 별개로 관리한다.
```

Department / Team 작업 시 우선순위:

```text
1. 기존 Inventory MVP에 Department 또는 유사 모델이 있는지 확인한다.
2. 기존 모델을 OS 공통 소속 기준으로 활용 가능한지 판단한다.
3. 필요 시 core에 Department/Team 기준정보를 신설한다.
4. User와 Department/Team 연결 방식은 additive 변경으로 처리한다.
5. 앱 물리 이동이나 테이블 rename은 서두르지 않는다.
```

금지:

```text
체크리스트 전용 Department 모델 생성
기존 Department 테이블명 즉시 변경
기존 앱에서 모델을 물리 이동
User 모델 대규모 재설계
```

---

## 17. 모듈 추가 규칙

새 모듈은 다음 흐름으로 추가한다.

```text
1. OS_ROADMAP.md에서 우선순위 확인
2. docs/modules/<module_name>/ 문서 폴더 생성
3. <MODULE>_PRODUCT_SPEC.md 작성
4. <MODULE>_TECH_SPEC.md 작성
5. migration 필요 여부 검토
6. Django 앱 생성 여부 결정
7. URL 설계
8. 권한 설계
9. template 설계
10. 테스트 작성
11. 리허설 DB 검증
12. 수동 QA
13. 운영 반영
14. 직원 안내 및 교육
15. 1~2주 실사용 관찰
16. 관찰 결과 조정
```

위 목록은 모듈 추가의 흐름을 설명하기 위한 규칙이다.

세부 실행 절차는 각 모듈 문서, `OS_DB_OPERATIONS.md`, `OS_OPERATIONS_SETUP.md`, `OS_TASKS.md`를 따른다.

한 번에 여러 모듈을 만들지 않는다.

---

## 18. Notice-first 규칙

Notice Module은 가장 중요한 모듈이라서 먼저 만드는 것이 아니다.

Notice Module은 가장 단순한 문서형 CRUD이므로, 김포365OS의 모듈 추가 패턴을 확립하기 위해 먼저 만든다.

Notice Module에서 확립할 패턴:

```text
모듈 문서 작성
Django 앱 생성
모델 추가
migration 생성
리허설 DB 적용
목록/상세/등록/수정 화면 구현
권한 적용
테스트 작성
수동 QA
운영 반영
직원 안내
실사용 관찰
```

Notice v1은 작게 만든다.

Notice 후순위 기능은 Checklist 정착 이후 검토한다.

후순위 기능:

```text
공지 확인 독촉
첨부파일
예약 게시
공지 카테고리 고도화
확인률 리포트
자동 알림
```

Checklist는 김포365OS의 실질적인 일일 사용 핵심 모듈이다.

Notice가 비대해져 Checklist 착수를 지연시키면 안 된다.

---

## 19. Checklist 우선성 규칙

Checklist Module은 김포365OS MVP의 핵심 모듈이다.

Checklist는 전 직원의 일일 접속 습관과 가장 직접적으로 연결된다.

Checklist 작업 전에는 다음이 선행되어야 한다.

```text
OS 홈
공통 sidebar/navbar
준비 중 모듈 placeholder
Department/Team 소속 기준
개인 계정 원칙
리허설 DB 검증 흐름
```

Checklist는 다음 기준을 따른다.

```text
기록 단위: User
운영 단위: Department / Team
책임 확인 단위: 당일 마감담당자
```

Checklist 작업 시 Notice 후순위 기능을 추가하지 않는다.

---

## 20. OS MVP 컷라인 규칙

김포365OS MVP 컷라인은 다음으로 정의한다.

```text
Phase 1. OS 최소 틀
Phase 1.5. Department/Team 소속 기준
Module 1. Inventory
Phase 2. Notice v1
Phase 3. Checklist v1
```

위 단계까지 완료되면 김포365OS는 일일 업무 허브로서 최소 완성 상태에 도달한 것으로 본다.

Phase 4 이후는 확장 단계이다.

```text
Phase 4. SOP / Manual
Phase 5. Internal Request / Approval
Phase 6. Attendance / Work Schedule
Phase 7. 운영 안정화 및 확장
```

개발이 Phase 5 중간에 중단되더라도, MVP 컷라인까지 완료되어 있다면 “핵심 완성 + 추가 진행 중” 상태로 본다.

---

## 21. OS 자기완결 규칙

김포365OS는 내부 운영 기능을 OS 안에서 자체 완결하도록 만든다.

다음 기능은 외부 도구 링크 허브로 대체하지 않는다.

```text
공지사항
체크리스트
SOP
업무 매뉴얼
내부 요청
결재
근무표
휴가 일정
```

외부 도구는 보조 수단으로만 사용할 수 있다.

```text
카카오톡
→ 즉시 알림 보조 수단

외부 문서 도구
→ 임시 참고 자료

메신저
→ 알림 보조 수단
```

기준 기록, 최신본, 확인 여부, 처리상태는 OS 내부에 남긴다.

---

## 22. 접속 및 네트워크 규칙

김포365OS는 원내 네트워크 사용을 기본으로 한다.

기본 원칙:

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

모바일 접속은 원내 Wi-Fi 연결 상태에서만 허용한다.

관리자 원격 접근이 필요한 경우에는 앱을 인터넷에 직접 노출하지 않고, VPN 또는 Tailscale 같은 사설 네트워크 방식만 검토한다.

관리자 예외 접속은 일반 직원 원외 접속 허용을 의미하지 않는다.

---

## 23. 테스트 규칙

코드 작업 후에는 기본적으로 다음을 실행한다.

```powershell
python manage.py check
python manage.py test
```

migration이 포함된 작업은 리허설 DB에서 먼저 검증한다.

운영 DB에는 바로 migration을 적용하지 않는다.

상세한 테스트 절차와 QA 범위는 `OS_TECH_SPEC.md`, `OS_MANUAL_QA_CHECKLIST.md`, 각 모듈별 QA 문서를 따른다.

본 문서에는 상세 테스트 절차를 중복 작성하지 않는다.

---

## 24. 수동 QA 규칙

자동 테스트가 통과해도 수동 확인이 필요하다.

OS 공통 smoke QA:

```text
로그인 가능
OS 홈 표시
Inventory Module 진입 가능
준비 중 모듈 placeholder 표시
권한별 메뉴 노출 이상 없음
리허설 DB 연결 확인
```

Inventory Module을 수정하지 않은 경우에는 상세 inventory QA 전체를 매번 수행하지 않는다.

다만 다음은 확인한다.

```text
Inventory 메뉴 진입 가능
재고현황 주요 화면 접근 가능
입고/출고 주요 화면 접근 가능
오류 화면 없음
```

상세 Inventory QA는 다음 문서에서 관리한다.

```text
docs/modules/inventory/INVENTORY_MANUAL_QA_CHECKLIST.md
```

---

## 25. 운영 반영 규칙

운영 반영은 Claude Code가 임의로 수행하지 않는다.

운영 반영 전에는 다음 원칙을 따른다.

```text
리허설 환경에서 먼저 검증한다.
운영 DB 백업을 확보한다.
migration 필요 여부를 확인한다.
직원 사용 중단 또는 입력 중단이 필요한지 확인한다.
실패 시 백업본으로 복구할 수 있어야 한다.
```

운영 반영이 실패하면 즉시 백업본을 기준으로 복구한다.

운영 반영과 복구의 상세 절차는 `OS_DB_OPERATIONS.md`와 `OS_OPERATIONS_SETUP.md`를 따른다.

본 문서에는 운영 반영 실행 절차를 중복 작성하지 않는다.

---

## 26. 모듈 정착 규칙

모듈은 기술 완료가 아니라 실사용 정착까지를 완료로 본다.

Phase 2~6의 업무 모듈은 다음 정착 루프를 거친다.

```text
1. 운영 반영
2. 직원 안내 및 교육
3. 1~2주 실사용 관찰
4. 관찰 결과에 따른 조정
```

이전 모듈로 돌아가 조정하는 것은 예외가 아니라 정상 흐름이다.

실사용 중 발견되는 문제는 다음 기준으로 판단한다.

```text
직원이 입력을 누락하는가
메뉴 위치를 찾지 못하는가
용어를 이해하지 못하는가
관리자가 확인하기 어려운가
수동 업무보다 복잡해졌는가
기록이 개인/부서 기준으로 남는가
```

---

## 27. SOP / Manual 작업 규칙

SOP / Manual Module은 문서를 담고 관리하는 그릇을 만드는 단계와 실제 콘텐츠를 작성하는 단계를 구분한다.

Phase 완료 기준은 다음이다.

```text
매뉴얼 작성 가능
매뉴얼 조회 가능
매뉴얼 수정 가능
최신본 관리 가능
최소 샘플 매뉴얼로 동작 검증
```

전체 SOP 콘텐츠 작성 완료를 Phase 완료 조건으로 삼지 않는다.

SOP 콘텐츠 작성은 별도 운영 프로젝트로 지속 진행한다.

---

## 28. Internal Request 상태값 규칙

Internal Request Module은 간단하게 시작한다.

초기 상태값은 다음으로 제한한다.

```text
요청됨
처리중
처리완료
반려
```

후순위 상태값:

```text
확인중
보류
```

후순위 상태값은 실제 운영에서 필요성이 확인된 후 추가한다.

처음부터 복잡한 결재선, 댓글, 첨부파일, 자동 알림을 만들지 않는다.

---

## 29. 금지 작업 목록

다음 작업은 명시적 승인 없이 수행하지 않는다.

```text
운영 DB 직접 수정
운영 DB에 바로 migration 적용
파괴적 migration 생성
Inventory 핵심 모델 수정
Inventory service 계층 우회
inventory/ 앱 물리 이동
docs/modules/ 아래에 코드 생성
모듈 여러 개 동시 구현
공용 계정 생성
부서 계정 생성
원외 접속 허용을 위한 공인 IP 노출
```

명시적 승인 없이 수행하지 않는다는 말은, Claude Code가 스스로 판단하여 진행할 수 없다는 의미이다.

승인은 해당 세션에서 다빈이 명확하게 지시한 경우에만 인정한다.

---

## 30. 작업 전 체크리스트

작업 전 다음을 확인한다.

```text
현재 브랜치가 맞는가
작업 범위가 하나인가
관련 문서를 확인했는가
.env가 리허설 DB를 바라보는가
운영 DB를 건드리지 않는가
migration이 필요한 작업인가
Inventory 핵심 로직을 건드리지 않는가
```

권장 명령:

```powershell
git status
Select-String -Path .env -Pattern "POSTGRES_DB"
python manage.py check
```

---

## 31. 작업 후 체크리스트

작업 후 다음을 확인한다.

```text
변경 파일이 예상 범위 안에 있는가
민감 파일이 Git에 잡히지 않았는가
python manage.py check가 통과했는가
python manage.py test가 통과했는가
필요한 경우 smoke QA를 수행했는가
문서 변경이 필요한 경우 반영했는가
```

권장 명령:

```powershell
git status
git status --ignored
python manage.py check
python manage.py test
```

---

## 32. 향후 보강 필요 항목

이 문서는 초기 작업 규칙 문서이다.

향후 다음 항목을 보강한다.

```text
OS_TECH_SPEC.md 작성 후 기술 세부 규칙 반영
OS_DB_OPERATIONS.md 작성 후 백업/복구 명령 반영
OS_OPERATIONS_SETUP.md 작성 후 운영 반영 절차 반영
OS_TASKS.md 작성 후 TASK 관리 규칙 반영
Notice Module 구현 후 모듈 추가 규칙 보강
Checklist Module 구현 후 Department/Team 규칙 보강
```
