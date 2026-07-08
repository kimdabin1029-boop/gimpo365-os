# OS_ARCHITECTURE.md

# 김포365OS 아키텍처 문서

## 문서 버전

```text
문서명: OS_ARCHITECTURE.md
문서 버전: v0.2
최종 수정일: 2026-07-08
문서 범위: 김포365OS 시스템 구조, 모듈 구조, 문서 구조, DB 운영 구조, migration 원칙, 개발 원칙
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                                                                                                                                                      |
| ---- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| v0.2 | 2026-07-08 | `OS_PRODUCT_SPEC.md v0.2` 기준 반영. `docs/modules/` 문서 구조 확정, 운영/리허설 DB 분리, 단일 DB 공유 원칙, migration 정책, 리허설 DB 동기화 원칙, Department/Team 소속 모델 원칙, 원외 접속 차단 구현 방식, OS 자기완결 원칙 반영 |
| v0.1 | 2026-07-08 | 김포365OS 초기 아키텍처 초안 작성                                                                                                                                                      |

---

## 1. 문서 목적

이 문서는 김포365한의원 내부 운영 시스템인 `김포365OS`의 기술적 구조와 설계 원칙을 정의한다.

김포365OS는 기존 `gimpo365-inventory` MVP를 기반으로 시작하지만, 단순 재고관리 앱이 아니라 공지사항, 체크리스트, SOP, 내부 요청, 근태/근무표 등 내부 운영 모듈을 단계적으로 포함하는 모듈형 시스템이다.

이 문서의 목적은 다음과 같다.

```text
김포365OS의 전체 구조를 정의한다.
기존 Inventory Module을 OS 안에서 어떻게 다룰지 정의한다.
Django 앱 폴더와 문서 폴더의 역할을 구분한다.
향후 새 모듈을 추가할 때의 기준을 정의한다.
운영 DB와 리허설 DB의 분리 원칙을 명확히 한다.
운영 DB schema 변경 시 migration 정책을 정의한다.
리허설 DB가 실제 운영 환경 검증 역할을 하도록 동기화 원칙을 정의한다.
Claude Code 및 향후 개발자가 구조를 임의로 대개조하지 않도록 방지한다.
```

---

## 2. 전체 아키텍처 개요

김포365OS는 Django + PostgreSQL 기반의 원내 내부 운영 시스템이다.

초기 구조는 기존 `gimpo365-inventory` MVP를 기반으로 한다.

전체 방향은 다음과 같다.

```text
김포365OS
├─ 공통 계정/권한
├─ 공통 Department/Team 기준정보
├─ 공통 홈
├─ 공통 사이드바/상단바
├─ 공통 운영 문서
├─ Module 1: Inventory
├─ Module 2: Notice
├─ Module 3: Checklist
├─ Module 4: SOP / Manual
├─ Module 5: Internal Request / Approval
└─ Module 6: Attendance / Work Schedule
```

초기에는 Inventory Module만 실제 기능으로 제공한다.

다른 모듈은 문서와 placeholder부터 준비한다.

---

## 3. 현재 로컬 작업장 구조

현재 로컬 개발 구조는 다음과 같다.

```text
E:\gimpo365
├─ gimpo365-inventory
│  └─ Inventory MVP 보존용
│
└─ gimpo365-os
   └─ 김포365OS 새 작업장
```

각 폴더의 역할은 다음과 같다.

| 경로                               | 역할                                         |
| -------------------------------- | ------------------------------------------ |
| `E:\gimpo365\gimpo365-inventory` | 기존 Inventory MVP 저장소. Module 1의 기준 구현으로 보존 |
| `E:\gimpo365\gimpo365-os`        | 김포365OS 새 작업장. 향후 OS 본체로 발전                |

`gimpo365-inventory`는 완성된 재고관리 MVP 기준점으로 보존한다.

`gimpo365-os`는 김포365OS 본체로 발전시킨다.

---

## 4. 저장소 구조 원칙

## 4.1 기존 저장소

기존 GitHub 저장소는 다음 역할을 가진다.

```text
kimdabin1029-boop/gimpo365-inventory
```

역할:

```text
Inventory MVP 완료본
김포365OS Module 1의 기준 구현
재고관리 모듈의 원형
향후 OS 개발 시 참고할 안정판
```

## 4.2 신규 저장소

김포365OS는 향후 별도 저장소로 관리한다.

예정 저장소명:

```text
kimdabin1029-boop/gimpo365-os
```

역할:

```text
김포365OS 본체
Inventory Module 포함
향후 Notice, Checklist, SOP, Request, Attendance 등 모듈 추가
OS 공통 UI와 공통 권한 관리
```

기본 공개 정책은 private이다.

public은 AI 구조 검토 또는 임시 공유를 위한 예외적 조치로만 사용한다.

---

## 5. Django 앱 구조

초기 Django 앱 구조는 기존 Inventory MVP 구조를 유지한다.

```text
gimpo365-os
├─ accounts/
├─ core/
├─ inventory/
├─ config/
├─ templates/
├─ static/
└─ manage.py
```

각 앱의 역할은 다음과 같다.

| 앱/폴더         | 역할                                                   |
| ------------ | ---------------------------------------------------- |
| `config/`    | Django 프로젝트 설정, URL 루트, settings                     |
| `accounts/`  | 사용자 계정, 권한, 로그인 관련 공통 기능                             |
| `core/`      | 공통 기반 기능, OS 홈, placeholder, Department/Team 기준정보 후보 |
| `inventory/` | Inventory Module 실제 Django 앱                         |
| `templates/` | 공통 base, navbar, sidebar, 각 앱 template               |
| `static/`    | CSS, JS, 이미지 등 정적 파일                                 |

초기에는 새 앱을 과도하게 만들지 않는다.

실제 기능 구현이 시작되기 전의 예정 모듈은 `core`의 placeholder view로 처리할 수 있다.

---

## 6. 중요한 구조 원칙

## 6.1 Django 앱 물리 이동 금지

현재 단계에서 `inventory/` Django 앱을 `docs/modules/inventory/` 아래로 물리적으로 이동하지 않는다.

금지 예시:

```text
금지:
inventory/
→ docs/modules/inventory/inventory/
```

이유는 다음과 같다.

```text
INSTALLED_APPS 경로가 흔들림
import 경로가 흔들림
URL include 경로가 흔들림
template 경로가 흔들림
test 경로가 흔들림
기존 Inventory Module 안정성이 훼손될 수 있음
```

따라서 현재 구조는 다음 원칙을 따른다.

```text
inventory/
→ 실제 Django 앱 코드

docs/modules/inventory/
→ Inventory Module 문서 폴더
```

## 6.2 코드 구조와 문서 구조 분리

김포365OS에서는 코드 폴더와 문서 폴더를 명확히 구분한다.

```text
inventory/
→ 실행되는 Django 코드

docs/modules/inventory/
→ 재고관리 모듈 문서
```

향후 notice, checklist 등 다른 모듈에도 동일한 원칙을 적용한다.

예시:

```text
notice/
→ 실제 공지사항 Django 앱 코드

docs/modules/notice/
→ 공지사항 모듈 문서
```

`docs/modules/`는 문서 전용 폴더이다.
코드를 넣지 않는다.

---

## 7. 문서 구조

김포365OS의 루트 문서는 OS 전체 기준으로 작성한다.

```text
README.md
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

각 문서의 역할은 다음과 같다.

| 문서                          | 역할                         |
| --------------------------- | -------------------------- |
| `README.md`                 | 저장소 입구 문서                  |
| `OS_PRODUCT_SPEC.md`        | 김포365OS 제품 목적, 사용자, 기능 범위  |
| `OS_ARCHITECTURE.md`        | 김포365OS 구조, 앱 배치, 모듈 설계 원칙 |
| `OS_ROADMAP.md`             | 김포365OS 개발 순서              |
| `OS_TECH_SPEC.md`           | 기술 구현 기준                   |
| `OS_WORKING_RULES.md`       | Claude Code 및 개발 작업 규칙     |
| `OS_TASKS.md`               | 실제 작업 목록                   |
| `OS_DB_OPERATIONS.md`       | DB, 백업, 복구 운영 기준           |
| `OS_OPERATIONS_SETUP.md`    | 로컬/리허설/운영 세팅 절차            |
| `OS_MANUAL_QA_CHECKLIST.md` | OS 공통 smoke test 및 회귀 점검표  |

---

## 8. 모듈 문서 구조

모듈별 문서는 `docs/modules/<module_name>/` 아래에 둔다.

Inventory Module의 문서 구조는 다음과 같다.

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

`INVENTORY_` 접두사를 사용하는 이유는 다음과 같다.

```text
문서만 열어도 어떤 모듈 문서인지 알 수 있음
향후 NOTICE_, CHECKLIST_ 등 다른 모듈 문서와 구분 가능
Claude Code가 루트 OS 문서와 모듈 문서를 혼동할 가능성을 줄임
```

향후 공지사항 모듈이 추가되면 다음 구조를 사용할 수 있다.

```text
docs/
└─ modules/
   └─ notice/
      ├─ NOTICE_PRODUCT_SPEC.md
      ├─ NOTICE_TECH_SPEC.md
      ├─ NOTICE_ROADMAP.md
      └─ NOTICE_TASKS.md
```

체크리스트 모듈이 추가되면 다음 구조를 사용할 수 있다.

```text
docs/
└─ modules/
   └─ checklist/
      ├─ CHECKLIST_PRODUCT_SPEC.md
      ├─ CHECKLIST_TECH_SPEC.md
      ├─ CHECKLIST_ROADMAP.md
      └─ CHECKLIST_TASKS.md
```

모든 모듈에 반드시 모든 문서를 만들 필요는 없다.
모듈의 복잡도에 따라 필요한 문서만 만든다.

---

## 9. OS 문서와 모듈 문서의 우선순위

문서 간 우선순위는 다음과 같다.

```text
1. OS_WORKING_RULES.md
2. OS_PRODUCT_SPEC.md
3. OS_ARCHITECTURE.md
4. OS_TECH_SPEC.md
5. OS_ROADMAP.md
6. 모듈별 *_PRODUCT_SPEC.md
7. 모듈별 *_TECH_SPEC.md
8. 모듈별 *_TASKS.md
```

단, Inventory Module의 데이터 무결성 원칙은 예외적으로 최우선으로 보호한다.

Inventory Module에서 다음 원칙은 OS 작업 중에도 변경하지 않는다.

```text
현재고 저장 필드 추가 금지
현재고 직접 수정 금지
StockTransaction 직접 create 금지
거래 상태 직접 변경 금지
입고/출고/초기재고/실사조정은 service 계층 사용
주문 상태 변경만으로 현재고 변경 금지
주문은 재고 증감이 아님
실제 재고 증가는 StockTransaction IN으로만 발생
잔여마감은 재고 증감 아님
운영 데이터 삭제 금지
```

---

## 10. 환경 분리 구조

김포365OS는 운영 환경과 리허설 환경을 분리한다.

현재 기준은 다음과 같다.

```text
운영 서버: 8000 포트
운영 DB: gimpo365_inventory

리허설 서버: 8001 포트
리허설 DB: gimpo365os_rehearsal
```

환경 구분:

| 환경  |   포트 | DB                     | 용도            |
| --- | ---: | ---------------------- | ------------- |
| 운영  | 8000 | `gimpo365_inventory`   | 직원 실사용        |
| 리허설 | 8001 | `gimpo365os_rehearsal` | 개발/검증/OS 틀 작업 |

리허설 환경에서 운영 DB를 직접 연결하지 않는다.

`.env` 파일에서 DB 이름을 반드시 확인한다.

```text
운영 DB 연결 금지:
POSTGRES_DB=gimpo365_inventory

리허설 DB 연결:
POSTGRES_DB=gimpo365os_rehearsal
```

`gimpo365-os` 작업장은 반드시 리허설 DB를 사용한다.

---

## 11. 계정 및 접속 구조

김포365OS는 개인 계정을 원칙으로 한다.

```text
개인 계정: 사용
부서 계정: 금지
공용 계정: 금지
공용 PC: 사용 가능
공용 PC 로그인 방식: 개인 계정 로그인
모바일 개인 접속: 허용
원외 접속: 차단
```

공용 PC를 사용하더라도 개인 계정으로 로그인한다.

이유는 다음과 같다.

```text
공지 확인 기록을 개인에게 귀속해야 함
체크리스트 완료 기록을 개인에게 귀속해야 함
재고관리 입력 기록을 개인에게 귀속해야 함
향후 교육 이수 기록을 개인에게 귀속해야 함
내부 요청/결재 기록을 개인에게 귀속해야 함
```

접속 가능 범위는 원내 네트워크로 제한한다.

원외 접속은 허용하지 않는다.

---

## 12. 원외 접속 차단 구현 방식

김포365OS의 원외 접속 차단은 초기에는 애플리케이션 코드가 아니라 네트워크 구조로 처리한다.

기본 원칙은 다음과 같다.

```text
서버를 인터넷에 직접 노출하지 않는다.
공유기 포트포워딩을 사용하지 않는다.
공인 IP로 직접 접속 가능하게 만들지 않는다.
원내 LAN 또는 원내 Wi-Fi에 연결된 기기에서만 접속한다.
초기에는 Django 앱 레벨 IP 화이트리스트 로직을 구현하지 않는다.
```

즉, 일반 직원은 원내 네트워크에 연결된 상태에서만 김포365OS에 접속할 수 있다.

모바일 접속은 허용하지만, 원내 Wi-Fi에 연결된 상태에서만 허용한다.

관리자 원격 접근이 필요한 경우에는 앱을 인터넷에 직접 노출하지 않고, VPN 또는 Tailscale 같은 사설 네트워크 방식만 검토한다.

관리자 예외 접속은 운영 편의를 위한 별도 인프라 정책이며, 일반 직원 원외 접속 허용을 의미하지 않는다.

---

## 13. 권한 구조

초기 권한 구조는 단순하게 유지한다.

```text
관리자
팀장
직원
```

추후 필요 시 다음 권한을 검토할 수 있다.

```text
조회 전용
수습 직원
```

권한 구조를 과도하게 세분화하지 않는다.

권한 설계 원칙은 다음과 같다.

```text
일반 직원은 본인 업무 수행과 조회에 집중한다.
팀장은 팀 단위 확인과 일부 관리 기능을 가진다.
관리자는 전체 운영 상태를 확인하고 설정을 관리한다.
수습 직원은 필요 시 조회 전용 또는 제한 권한으로 운영할 수 있다.
```

초기에는 Django의 기존 사용자/권한 구조를 최대한 활용한다.
새 권한 체계를 대규모로 만들지 않는다.

---

## 14. Department / Team 소속 모델 원칙

역할과 소속은 분리해서 관리한다.

```text
역할:
관리자, 팀장, 직원

소속:
데스크, 치료실, 피부관리실, 탕전, 기타 부서/파트
```

Django Group 또는 권한은 사용자의 역할을 표현한다.

Department 또는 Team은 사용자의 소속을 표현한다.

즉, 다음 두 개념을 혼동하지 않는다.

```text
팀장
→ 역할

치료실
→ 소속

치료실 팀장
→ 역할이 팀장이고, 소속이 치료실인 사용자
```

Department / Team 모델은 `core` 앱의 공통 기준정보로 관리하는 것을 원칙으로 한다.

초기에는 기존 Department 개념을 최대한 활용한다.

소속 모델 원칙은 다음과 같다.

```text
User는 최소 하나의 주 소속 Department/Team을 가진다.
초기에는 1인 1주 소속을 기본으로 한다.
필요 시 향후 복수 소속을 검토할 수 있다.
마감담당자 기록은 개인 계정과 Department/Team 기준으로 남긴다.
팀별 체크리스트, 파트별 재고관리, 팀장 확인은 Department/Team 정보를 기준으로 한다.
```

마감담당자는 김포365OS의 중요한 운영 단위이다.

운영 단위는 팀 또는 파트이고, 기록 단위는 개인 계정이다.

```text
운영 단위: Department / Team
기록 단위: User
책임 확인 단위: 당일 마감담당자
```

---

## 15. 모듈 표시 구조

로그인 후 첫 화면은 `김포365OS 홈`이다.

OS 홈은 모듈 선택 화면 역할을 한다.

초기 OS 홈에는 다음 항목을 표시한다.

```text
김포365OS 이름
현재 사용 가능한 모듈
재고관리 바로가기
준비 중 모듈
간단한 안내 문구
```

Inventory Module은 다음 위치에 둔다.

```text
운영관리 > 재고관리
```

미구현 모듈은 전 직원에게 준비 중 상태로 표시한다.

```text
직원: 준비 중 모듈 확인 가능
팀장: 준비 중 모듈 확인 가능
관리자: 준비 중 모듈 확인 가능
```

미구현 모듈은 실제 기능처럼 보이면 안 된다.

클릭 시 placeholder 화면에서 다음 문구를 표시한다.

```text
현재 미구현 상태입니다.
향후 기능이 추가될 예정입니다.
```

또는:

```text
준비 중인 모듈입니다.
현재는 사용할 수 없습니다.
```

---

## 16. URL 및 라우팅 원칙

초기 URL 구조는 단순하게 유지한다.

권장 방향은 다음과 같다.

```text
/
→ OS 홈

/inventory/
→ Inventory Module

/notices/
→ Notice Module, 향후 구현

/checklists/
→ Checklist Module, 향후 구현

/manuals/
→ SOP / Manual Module, 향후 구현

/requests/
→ Internal Request / Approval Module, 향후 구현

/schedules/
→ Attendance / Work Schedule Module, 향후 구현
```

초기 단계에서 구현되지 않은 모듈은 실제 앱을 만들지 않고, `core` 앱의 placeholder view로 처리할 수 있다.

예시:

```text
/notices/
→ core.views.placeholder_notice

/checklists/
→ core.views.placeholder_checklist

/manuals/
→ core.views.placeholder_manual

/requests/
→ core.views.placeholder_request

/schedules/
→ core.views.placeholder_schedule
```

다만 실제 모듈 개발이 시작되면 별도 Django 앱으로 분리한다.

---

## 17. 공통 UI 구조

김포365OS는 공통 레이아웃을 사용한다.

기본 구조는 다음과 같다.

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

현재 기존 구조에 맞춰 세부 경로는 조정할 수 있다.

공통 UI 원칙은 다음과 같다.

```text
모든 화면은 동일한 base.html을 사용한다.
상단에는 김포365OS 이름을 표시한다.
사이드바에는 모듈 메뉴를 표시한다.
Inventory Module은 운영관리 > 재고관리로 표시한다.
준비 중 모듈은 준비 중 상태로 표시한다.
일반 직원도 향후 모듈 구조를 볼 수 있다.
```

---

## 18. OS 홈 구조

OS 홈은 김포365OS의 첫 화면이다.

OS 홈의 역할은 다음과 같다.

```text
단일 재고관리 앱이 아니라 OS라는 점을 명확히 한다.
전 직원이 모듈 구조를 이해하게 한다.
현재 사용 가능한 기능과 준비 중인 기능을 구분한다.
재고관리로 빠르게 이동할 수 있게 한다.
향후 공지사항, 체크리스트, SOP를 추가할 공간을 마련한다.
```

초기 OS 홈 구성 후보는 다음과 같다.

```text
상단: 김포365OS 소개 문구
카드 1: 운영관리 > 재고관리
카드 2: 공지사항, 준비 중
카드 3: 오픈/마감 체크리스트, 준비 중
카드 4: SOP/업무 매뉴얼, 준비 중
카드 5: 내부 요청/결재, 준비 중
카드 6: 근태/근무표, 준비 중
```

OS 홈은 복잡한 대시보드가 아니다.

초기에는 단순한 모듈 선택 화면으로 만든다.

---

## 19. 모듈 추가 원칙

새 모듈은 다음 순서로 추가한다.

```text
1. OS_ROADMAP.md에서 우선순위 확인
2. docs/modules/<module_name>/ 문서 폴더 생성
3. <MODULE>_PRODUCT_SPEC.md 작성
4. <MODULE>_TECH_SPEC.md 작성
5. OS_ARCHITECTURE.md와 충돌 여부 확인
6. Django 앱 생성 여부 결정
7. URL 설계
8. 권한 설계
9. template 설계
10. migration 필요 여부 검토
11. 테스트 작성
12. 수동 QA
13. README 문서 지도 반영
```

모듈 추가 시 지켜야 할 원칙은 다음과 같다.

```text
한 번에 하나의 모듈만 추가한다.
기존 Inventory Module 기능을 건드리지 않는다.
공통 구조 변경과 모듈 기능 구현을 같은 작업으로 섞지 않는다.
새 모듈은 OS 내부에서 자기완결적으로 작동해야 한다.
외부 도구 링크 허브 방식으로 만들지 않는다.
차트 프로그램으로 해결 가능한 환자 관련 업무는 만들지 않는다.
```

---

## 20. OS 자기완결 원칙

김포365OS는 내부 운영 기능을 OS 안에서 자체 완결하도록 설계한다.

다음 기능은 OS 내부에 자체 구현하는 것을 원칙으로 한다.

```text
공지사항
체크리스트
SOP
업무 매뉴얼
직원 교육자료
내부 요청
결재
근무표
휴가 일정
```

외부 도구는 보조 수단으로만 사용할 수 있다.

예시:

```text
카카오톡
→ 즉시 알림 채널로 병행 가능
→ 공지 원문과 확인 여부는 OS에 기록

외부 문서 도구
→ 임시 참고 가능
→ 기준 문서와 최신본은 OS 내부에 보관

메신저
→ 안내 보조 가능
→ 요청 처리상태와 완료 기록은 OS에 보관
```

외부 도구에 의존하는 구조는 만들지 않는다.

---

## 21. DB 구조 및 단일 DB 공유 원칙

김포365OS의 모든 Django 앱은 하나의 PostgreSQL 운영 DB를 공유한다.

초기에는 모듈별 DB 분리를 사용하지 않는다.

```text
accounts
core
inventory
notice
checklist
manual
request
attendance
```

위 앱들은 각각 별도 DB를 갖지 않고, 하나의 운영 DB 안에 테이블을 추가한다.

현재 DB 구조는 다음과 같다.

```text
운영 DB: gimpo365_inventory
리허설 DB: gimpo365os_rehearsal
```

현재 운영 DB 이름은 `gimpo365_inventory`이지만, 향후 OS 모듈 테이블도 이 DB에 추가될 수 있다.

이 이름은 Inventory Module에서 시작된 역사적 이름이다.

운영 중인 DB 이름을 무리하게 변경하지 않는다.

운영 DB rename은 별도 백업, 리허설, 전환 계획 없이는 수행하지 않는다.

향후 김포365OS 정식 운영 시 운영 DB 이름은 별도로 검토할 수 있다.

후보:

```text
gimpo365os
gimpo365_os
```

다만 현재 단계에서는 이름보다 운영 안정성을 우선한다.

---

## 22. DB 및 백업 구조

DB 운영 원칙은 다음과 같다.

```text
운영 DB와 리허설 DB를 분리한다.
리허설 환경에서 운영 DB를 연결하지 않는다.
운영 DB는 일 1회 이상 자동 백업한다.
백업본은 운영 PC 외 별도 위치 또는 매체에 보관한다.
위험 command는 기본 dry-run을 원칙으로 한다.
DB dump, pgpass.conf, 백업 zip은 Git에 올리지 않는다.
```

운영 DB는 원내 운영 이력의 기준이다.

운영 DB가 원내 PC 한 대에만 존재하면 PC 장애, 저장장치 장애, 실수 삭제 시 운영 이력이 소실될 수 있다.

따라서 운영 DB는 최소 일 1회 이상 자동 백업하고, 백업본은 운영 PC 외 별도 위치 또는 별도 매체에 보관한다.

상세 DB 운영 절차는 `OS_DB_OPERATIONS.md`에서 관리한다.

---

## 23. Migration 정책

김포365OS는 운영 중인 PostgreSQL DB 위에서 성장한다.

따라서 새 모듈 추가, 기존 모델 변경, 필드 추가 등으로 migration이 발생할 수 있다.

Migration은 김포365OS 성장 과정에서 가장 큰 데이터 리스크 중 하나이므로, 다음 원칙을 따른다.

```text
모든 migration은 리허설 DB에서 먼저 적용한다.
운영 migration 전에는 운영 DB 백업을 반드시 수행한다.
운영 migration 전에는 python manage.py check를 실행한다.
운영 migration 전에는 python manage.py test를 실행한다.
운영 migration 후에는 최소 smoke QA를 수행한다.
파괴적 migration은 기본 금지한다.
되돌릴 수 있는 reversible migration을 원칙으로 한다.
기존 운영 데이터 보존을 최우선으로 한다.
```

파괴적 migration의 예시는 다음과 같다.

```text
기존 컬럼 삭제
기존 컬럼 rename
기존 컬럼 type 변경
기존 테이블 삭제
운영 데이터 일괄 삭제
기존 null 불가능 필드 추가
```

파괴적 migration은 별도 승인 없이는 수행하지 않는다.

불가피하게 파괴적 migration이 필요한 경우 다음 절차를 따른다.

```text
1. 변경 사유 문서화
2. 운영 DB 백업
3. 리허설 DB에서 migration 적용
4. 기존 데이터 보존 여부 확인
5. 되돌리기 가능 여부 확인
6. 수동 QA
7. 운영 적용 시점 지정
8. 직원 사용 중단 또는 입력 중단 안내
9. 운영 migration 적용
10. 적용 후 smoke QA
```

초기 OS 확장에서는 가능하면 새 테이블 추가와 새 nullable 필드 추가 중심으로 설계한다.

기존 Inventory Module의 핵심 모델을 변경하지 않는다.

---

## 24. 리허설 DB 동기화 원칙

리허설 DB는 운영 DB를 보호하기 위한 검증 환경이다.

리허설 DB가 운영 DB와 다른 스키마 또는 빈 데이터 상태라면 실제 운영 환경 검증 역할을 할 수 없다.

따라서 다음 원칙을 따른다.

```text
리허설 DB는 운영 DB의 스키마를 기준으로 유지한다.
새 migration은 리허설 DB에 먼저 적용한다.
운영 적용 전 리허설 DB에서 화면, 권한, 주요 기능을 확인한다.
필요 시 운영 DB 백업본을 리허설 DB로 복원해 운영과 유사한 상태를 만든다.
리허설 DB는 별도 운영 환경이 아니라 검증 환경이다.
```

현재 단계에서는 운영 DB 백업본을 리허설 DB로 복원하여 실제 운영과 유사한 데이터를 사용할 수 있다.

다만 향후 직원 개인정보, 근태, 교육 이수, 내부 요청 등 민감 정보가 증가하면 다음 정책을 검토한다.

```text
운영 데이터 익명화
운영 데이터 축약 복제
민감 테이블 제외 복제
리허설 전용 seed data 생성
```

운영 DB 백업본과 리허설 DB dump는 외부에 공유하지 않는다.

리허설 DB 동기화 절차는 `OS_DB_OPERATIONS.md`에서 별도로 관리한다.

---

## 25. 보안 및 민감파일 원칙

다음 파일은 Git에 올리지 않는다.

```text
.env
.venv/
DB dump
*.dump
*.backup
*.zip
pgpass.conf
NAS 백업파일
```

민감 정보는 `.env` 또는 운영 환경 설정에서 관리한다.

GitHub에는 다음 정보를 올리지 않는다.

```text
DB 비밀번호
SECRET_KEY
운영 DB dump
NAS 경로 상세 비밀번호
직원 개인정보
운영 계정 비밀번호
```

Git commit 전에는 반드시 다음을 확인한다.

```powershell
git status --ignored
```

`.env`, `.venv`, dump 파일이 추적 대상에 나타나면 commit하지 않는다.

---

## 26. 테스트 및 수동 QA 구조

자동 테스트는 Django test를 기본으로 한다.

```powershell
python manage.py check
python manage.py test
```

OS 공통 작업 후에는 최소한 다음을 확인한다.

```text
로그인 가능
OS 홈 표시
재고관리 모듈 진입 가능
준비 중 모듈 placeholder 표시
권한별 메뉴 노출 이상 없음
리허설 DB 연결 확인
```

`OS_MANUAL_QA_CHECKLIST.md`는 상세 QA 문서가 아니라 OS 공통 smoke test 및 regression checklist로 사용한다.

Inventory Module의 상세 QA는 다음 문서에서 관리한다.

```text
docs/modules/inventory/INVENTORY_MANUAL_QA_CHECKLIST.md
```

Inventory Module을 수정하지 않은 OS 틀 작업에서는 상세 inventory QA 전체를 매번 수행하지 않는다.

다만 inventory 메뉴 진입과 주요 화면 접근 가능 여부는 확인한다.

---

## 27. 개발 작업 분리 원칙

개발 작업은 다음 범위를 섞지 않는다.

```text
OS 틀 작업
Inventory 기능 수정
새 모듈 기능 구현
문서 정리
DB 운영 작업
migration 작업
배포 작업
```

예시:

```text
좋은 작업 단위:
- OS 홈 추가
- sidebar 모듈 구조 정리
- Notice placeholder 추가
- OS_PRODUCT_SPEC.md 수정

나쁜 작업 단위:
- OS 홈 추가 + 재고 출고 로직 수정 + DB command 수정
```

작업 단위가 섞이면 테스트 범위가 불명확해지고, 오류 발생 시 원인을 찾기 어렵다.

---

## 28. 초기 구현 우선순위

아키텍처 관점에서 초기 구현 우선순위는 다음과 같다.

```text
1. 루트 URL을 OS 홈으로 정리
2. OS 홈 template 생성
3. 공통 sidebar/navbar를 김포365OS 기준으로 정리
4. Inventory Module을 운영관리 > 재고관리 위치로 표시
5. 준비 중 모듈 placeholder 추가
6. 권한별 메뉴 노출 확인
7. check/test 통과 확인
8. README 문서 지도 정리
```

아직 구현하지 않을 것:

```text
공지사항 실제 CRUD
체크리스트 실제 CRUD
SOP 문서관리 기능
내부 요청/결재 기능
근태/근무표 기능
Inventory 모델 대규모 수정
DB schema 대규모 변경
파괴적 migration
```

---

## 29. 향후 보강 필요 항목

이 문서는 초기 아키텍처 초안이다.

향후 다음 항목을 보강한다.

```text
OS_TECH_SPEC.md 작성 후 기술 세부 기준 반영
OS_WORKING_RULES.md 작성 후 Claude Code 작업 규칙 반영
OS_TASKS.md 작성 후 실제 작업 단위 연결
OS_DB_OPERATIONS.md 작성 후 백업/복구 절차 연결
OS_OPERATIONS_SETUP.md 작성 후 리허설/운영 세팅 절차 연결
OS_MANUAL_QA_CHECKLIST.md 작성 후 수동 점검 항목 연결
Notice Module 설계 시 notice 앱 구조 반영
Checklist Module 설계 시 checklist 앱 구조 반영
Department/Team 모델 실제 구현 방식 확정
migration 운영 절차 상세화
리허설 DB 동기화 절차 상세화
```
