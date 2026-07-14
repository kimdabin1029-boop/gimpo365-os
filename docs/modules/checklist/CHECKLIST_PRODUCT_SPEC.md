# CHECKLIST_PRODUCT_SPEC.md

# 김포365OS Checklist Module 제품 명세서

## 문서 버전

```text
문서명: CHECKLIST_PRODUCT_SPEC.md
문서 범위: 김포365OS Module 3 — Checklist(부서 단위 반복업무 수행 기록) 제품 명세
문서 상태: Checklist v1 구현 완료 (Phase 3 마감, P3-07)
전제 문서: OS_PRODUCT_SPEC.md, OS_ROADMAP.md, OS_WORKING_RULES.md, OS_TECH_SPEC.md, NOTICE_PRODUCT_SPEC.md
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                     |
| ---- | ---------- | ----------------------------------------- |
| v0.2 | 2026-07-14 | Checklist v1 구현 완료 상태 반영. §17.1 "당일 마감담당자" 표현 정리(사전 지정 아님) 해결로 갱신 |
| v0.1 | 2026-07-13 | P3-00 Checklist v1 제품 명세 초안 작성 (부서 단위·3모델·daily 우선) |

---

## 0. 문서 성격

이 문서는 Checklist Module을 "무엇을, 왜" 만드는지 정의하는 제품 명세서다.
구현 방식은 `CHECKLIST_TECH_SPEC.md`, 작업 단위는 `CHECKLIST_TASKS.md`에서 다룬다.

이 문서는 P3-00 문서 설계 단계에서 작성되며, 코드·앱·모델·migration을 만들지 않는다.
기존 OS 문서와 충돌/차이가 있으면 임의 수정하지 않고 "16. 기존 OS 문서와의 정합성"에 "[검토 필요]"로 기록한다.

---

## 1. 목적

Checklist Module은 김포365OS의 **일일 사용 핵심 모듈**이다(OS_ROADMAP MVP 컷라인의 마지막 핵심 모듈).

Checklist v1의 한 문장 정의:

```text
김포365OS Checklist v1은
부서별 반복 정기업무를
당일 실제 수행자가 완료 처리하고,
TEAM_LEADER 이상이 누락 현황을 확인하는
부서 단위 업무 수행 기록 시스템이다.
```

목적:

```text
- 매일 수행해야 할 부서 반복업무를 OS 안에서 수행·기록한다.
- 누가 언제 완료했는지 개인 계정 기준으로 남긴다.
- TEAM_LEADER 이상이 부서/전체 누락을 확인한다.
- 전 직원이 매일 OS 에 접속할 실질적 동인을 만든다.
```

Checklist는 개인 할 일 앱이 아니다. 부서 단위 수행 기록 시스템이다.

---

## 2. 운영 배경

김포365한의원은 데스크/치료실/피부관리실/탕전 등 파트별로 매일 반복되는 오픈·마감 업무가 있다.
기존에는 종이 체크리스트, 구두 전달, 마감 양식 작성·전송 등에 흩어져 있어 다음 문제가 있다.

```text
- 수행 여부를 관리자가 한눈에 확인하기 어렵다.
- 누락이 발생해도 사후 추적이 어렵다.
- 수행 기준이 사람마다 다르게 이해된다.
- 마감 양식이 외부 도구/파일로 흩어진다.
```

Checklist v1은 이 반복업무 수행과 누락 확인을 OS 내부에서 자기완결적으로 처리한다(OS 자기완결 원칙).

---

## 3. 적용 대상

```text
적용 조직: 김포365한의원 전 상시 근무자 (부서 소속 직원)
접속 환경: 원내 네트워크 (원외 접속 차단 원칙 유지)
계정 원칙: 개인 계정 (공용/부서 계정 금지)
조직 기준: Department + role (Phase 1.5 확정, Team 모델 미도입)
```

---

## 4. 부서 단위 운영 원칙

```text
- 체크리스트는 부서(Department)별로 사용한다.
- 한 부서에 배정된 항목은 그 부서 구성원이 공동으로 수행한다.
- 개인별 체크리스트를 만들지 않는다.
- 사전에 개인 담당자를 지정하지 않는다.
- 실제 수행한 사람(개인 계정)을 완료자로 기록한다.
```

기록 단위 요약:

```text
운영 단위: Department
기록 단위: User (실제 수행자 = completed_by)
완료 판정 단위: 부서 배정 항목 × 기준 날짜
```

동일한 부서 배정 항목은 하루에 하나의 완료 상태만 갖는다.

---

## 5. 개인 업무와의 차이

```text
개인 할 일 앱                     Checklist v1
------------------------------   ------------------------------
개인에게 업무 배정                부서에 업무 배정
지정된 담당자가 수행              부서 구성원 중 실제 수행자가 완료
개인별 목록                       부서 공유 목록(같은 부서면 같은 오늘 목록)
승인/반려 흐름                    승인 없음(완료/미완료만)
```

Checklist는 "누가 해야 하는가"를 사전 지정하지 않고, "그 부서가 오늘 했는가"를 기록한다.

---

## 6. 사용자 역할

김포365OS 역할 체계(`accounts.User.role`, 계층 STAFF < TEAM_LEADER < MANAGER < ADMIN)를 사용한다.

```text
STAFF        본인 소속 Department 오늘 항목 조회·완료·완료취소
TEAM_LEADER  본인 소속 Department 오늘 항목 조회·완료·완료취소 + 본인 Department 누락 현황 확인
MANAGER      전체 Department 누락 현황 확인 (완료 처리는 §10 기준)
ADMIN        전체 Department 누락 현황 확인 + Django admin 초기 설정
```

역할과 소속은 분리한다. 역할은 권한 등급, 소속(Department)은 오늘 항목 범위 판정에 쓴다.

---

## 7. Checklist v1 범위

```text
- ChecklistItem 항목 정의 (업무 문구 + frequency)
- DepartmentChecklistItem 부서 배정 (항목을 어느 부서가 수행할지)
- ChecklistRecord 날짜별 완료 기록
- frequency choices: daily / weekly / monthly (필드 포함)
- 실제 "오늘 항목" 판정 로직은 daily 만 지원
- 날짜 기준은 KST 로컬 날짜 (timezone.localdate())
- 오늘의 내 부서 체크리스트 화면
- 수행자 완료 처리 / 완료 취소
- completed_by / completed_at 기록
- TEAM_LEADER 이상 누락 현황 화면
- OS 홈 / sidebar 실사용 진입
- Django admin 을 통한 항목/부서 배정 초기 설정
```

---

## 8. 제외 범위

```text
- 개인 담당자 지정 / 개인별 할 일
- 승인 / 반려 / 승인자 / 승인시각
- 파일첨부 / 사진첨부 / 마감 양식 업로드·전송 / 양식 버전관리
- 읽음 확인 / 알림 / 자동 독촉
- 복잡한 반복 규칙 (weekly 요일 규칙, monthly 날짜 규칙)
- 공휴일/휴무일 자동 제외
- 통계 대시보드
- 별도 항목/배정 관리 CRUD 화면 (초기 설정은 Django admin)
```

---

## 9. 항목 정의와 부서 배정 분리 이유

Checklist는 **항목 정의(ChecklistItem)**와 **부서 배정(DepartmentChecklistItem)**을 분리한다.
이는 Inventory의 품목(Item) ↔ 관리품목(ManagedItem) 구조와 같은 방향이다.

### 9.1 공통 항목 재사용

```text
ChecklistItem: "냉난방 전원을 끈다"
DepartmentChecklistItem: 데스크 배정 / 치료실 배정 / 피부실 배정

→ 항목 문구를 한 번 수정하면 모든 배정 부서에 동일하게 반영된다.
```

### 9.2 배정 공백·중복 파악

부서 배정을 별도 단계로 두면 운영자가 다음을 확인할 수 있다.

```text
- 어느 부서에도 배정되지 않은 항목
- 같은 업무가 여러 부서에 중복 배정된 상태
- 수행 주체가 불명확한 업무
```

단, 시스템이 중복 배정을 자동 오류 처리하지는 않는다.

```text
- 동일 항목을 여러 Department 에 배정하는 것은 허용한다(의도된 공통 업무일 수 있음).
- 같은 항목을 같은 Department 에 중복 배정하는 것만 차단한다(UniqueConstraint).
- 여러 부서 배정이 의도된 것인지는 운영자가 판단한다.
```

---

## 10. 수행 및 완료 기준

```text
- 오늘 항목은 로그인 사용자의 Department 기준으로 표시한다.
- department 가 없는 직원은 수행할 체크리스트가 없다.
- 완료는 실제 수행자가 직접 처리하고, completed_by 에 로그인 사용자를 기록한다.
- 완료 시각(completed_at)을 기록한다.
- 승인자/승인시각/반려 상태는 만들지 않는다.
```

완료 대행(타 부서 완료 처리) 기본안:

```text
- STAFF / TEAM_LEADER: 본인 Department 항목만 완료 가능.
- MANAGER / ADMIN: 누락 현황은 전체 조회 가능하나, 타 Department 항목 완료는 기본적으로 허용하지 않는다.
  이유: "완료는 실제 수행자가 직접 체크한다"는 원칙, 누락 조회 권한과 타 부서 수행 권한을 분리.
- 운영상 예외가 필요하면 P3-04 구현 전 별도 결정한다.
```

완료/미완료 해석:

```text
완료   = 해당 (부서 배정 항목 + 기준 날짜)의 활성(is_active=True) ChecklistRecord 가 존재
미완료 = 위 활성 ChecklistRecord 가 없음
```

완료 취소(데이터 보존):

```text
- ChecklistRecord 를 hard delete 하지 않는다(운영 데이터 삭제 금지 원칙).
- 완료 취소는 ChecklistRecord.is_active=False 로 처리한다.
- 다시 완료하면 동일 unique 레코드를 재활성화하고 completed_by/completed_at 을 현재 수행자로 갱신한다.
- 실제 코드 동작은 P3-04 구현 전 재검증하되, 승인/반려·별도 상태 필드는 추가하지 않는다.
```

---

## 11. 누락 확인 기준

```text
TEAM_LEADER: 본인 소속 Department 의 오늘 누락(미완료) 현황.
MANAGER / ADMIN: 전체 Department 의 오늘 누락 현황.
TEAM_LEADER 미만(STAFF): 누락 현황 관리 화면에 접근하지 못한다.
```

TEAM_LEADER 이상은 승인자가 아니라 **누락 확인자**다. 완료를 대신 승인/반려하지 않는다.
권한 판정은 기존 `accounts.permissions` / `ROLE_RANK` / `accounts.mixins` 공통 패턴을 재사용한다.

---

## 12. daily 우선 및 weekly/monthly 후순위

```text
- ChecklistItem.frequency 필드는 daily / weekly / monthly 를 모두 포함한다(기본값 daily 권장).
- v1 의 "오늘 항목" 판정 로직은 daily 만 구현한다.
- weekly / monthly 항목은 v1 화면에 나타나지 않는다.
- weekly 요일 규칙, monthly 날짜(말일 처리 포함) 규칙은 후순위 필드로 두며 이번에 추가하지 않는다.
```

설계 결과(중요):

```text
frequency 는 ChecklistItem 정의에 속한다.
따라서 하나의 ChecklistItem 을 여러 Department 에 배정하면 모든 Department 가 같은 frequency 를 쓴다.
같은 문구라도 부서별 주기가 달라야 하면 별도의 ChecklistItem 으로 정의한다.
weekly/monthly 활성화는 스키마 대개조가 아니라 후속 규칙 필드 + selector 를 additive 하게 추가하는 방향으로 한다.
```

시기(timing) 필드 (P3-07.5):

```text
ChecklistItem.timing choices: opening(오픈) / specific(특정 시점) / closing(마감), 기본값 specific.
timing 도 frequency 처럼 ChecklistItem 정의에 속한다 → 여러 부서 배정은 같은 timing 을 공유하고,
부서별 시기가 다르면 별도 ChecklistItem 으로 정의한다.
별도 시각(시·분) 입력 필드는 두지 않는다. 특정 시각·상황(예: "점심시간 전", "오후 3시")은 title 문구로 적는다.
오늘 화면·누락 현황은 미완료 우선 + 시기(오픈→특정 시점→마감) 순으로 정렬하고 시기 라벨을 표시한다.
Admin 감사 필드(작성자/수정자/시각)는 자동 기록·읽기 전용이며 사용자가 선택하지 않는다.
```

---

## 13. 기존 마감 양식 처리 결정

현재 사용 중인 마감 양식의 파일 작성·전송 기능은 Checklist v1에서 구현하지 않는다.

```text
- 파일첨부 / 양식 업로드·전송 / 양식 버전관리 제외.
- 마감 양식의 세부 항목을 여러 ChecklistItem 으로 옮겨 하나씩 체크하는 방식으로 흡수한다.

기존:  마감 양식 하나를 작성해 전송
v1:   마감 업무를 여러 ChecklistItem 으로 나누어 직원이 하나씩 수행·완료 처리
```

외부 양식 링크/파일 첨부 필드는 확정 모델에 추가하지 않는다. 필요성이 반복 확인되면 배포 이후 후속 검토한다.

---

## 14. 주요 사용 시나리오

```text
1. 치료실 직원이 로그인 후 '오늘의 체크리스트'에서 치료실 항목을 확인한다.
2. 실제 업무를 수행한 직원이 항목을 완료 처리한다(completed_by = 본인).
3. 같은 치료실의 다른 직원에게도 그 항목이 완료 상태로 보인다(부서 공유).
4. 잘못 체크했으면 완료를 취소한다(레코드 비활성, 재완료 시 재활성).
5. 치료실 TEAM_LEADER 가 치료실 오늘 미완료 항목을 확인한다.
6. MANAGER 가 전체 부서 오늘 미완료 현황을 확인한다.
7. 관리자가 Django admin 에서 공통 항목을 정의하고 여러 부서에 배정한다.
```

---

## 15. 성공 기준

```text
- 부서 소속 직원이 로그인 후 본인 부서 오늘 항목을 조회할 수 있다.
- 실제 수행자가 완료/완료취소를 할 수 있고, 완료자·완료시각이 개인 계정 기준으로 남는다.
- 같은 부서 구성원이 동일한 오늘 항목·완료 상태를 공유한다.
- TEAM_LEADER 는 본인 부서, MANAGER/ADMIN 은 전체 부서 누락을 확인할 수 있다.
- daily 항목이 KST 로컬 날짜 기준으로 매일 갱신된다(전날 완료가 오늘로 넘어오지 않음).
- 운영자가 Django admin 으로 항목 정의·부서 배정을 초기 설정할 수 있다.
- Notice / Inventory 기능이 깨지지 않는다.
```

정량 지표(체크리스트 완료율 등)는 운영 관찰 단계(모듈 정착 루프)에서 정의한다.

---

## 16. 운영 리스크 및 예외

```text
- department 미지정 활성 직원: 오늘 항목이 비어 보인다 → 운영 점검 대상(User.department 지정 원칙).
- 완료 대행 예외: 기본 불허. 필요 시 P3-04 전 별도 결정.
- 중복 부서 배정: 허용되지만 운영자 판단 필요(자동 오류 아님).
- weekly/monthly 항목: v1 화면 미노출 → 운영자가 daily 외 항목을 기대하지 않도록 안내 필요.
- 마감 양식 전면 이관: 세부 항목화가 충분한지 초기 운영에서 관찰.
```

---

## 17. 기존 OS 문서와의 정합성

P3-00 에서 "[검토 필요]"로 남겼던 항목을 P3-07(마감)에서 정리했다.

### 16.1 [해결] "당일 마감담당자" 표현

```text
대상 문서: OS_PRODUCT_SPEC §5.3, OS_TECH_SPEC §7·§25, OS_ARCHITECTURE §14
기존 표현: "책임 확인 단위 = 당일 마감담당자" (사전 개인 지정처럼 읽힐 여지)
Checklist 구현: 사전 담당자 지정 없이 실제 수행자(completed_by)만 기록한다.
처리(P3-07): 위 OS 문서에 "당일 마감담당자 = 사전 지정이 아니라 그날 실제 수행한 직원"임을
             명확화하는 문구를 반영했다. 개념 자체는 정합(완료자 = 그날 수행자).
```

### 16.2 [정합] Department + role, Team 미도입

```text
OS_ARCHITECTURE §14 / OS_TECH_SPEC §16 = Department + role, Team 보류.
Checklist v1 은 Department 만 사용 → 정합. Team 필요성 근거 없음.
```

### 16.3 [정합] 완료 기록 삭제 금지 ↔ 완료 취소

```text
OS_TECH_SPEC §25 "완료 기록 삭제 금지" ↔ 완료 취소 = is_active=False(hard delete 아님) → 정합.
```

### 16.4 [정합] 반복 주기 단순화 / 첨부·알림 후순위

```text
OS_TECH_SPEC §25 "반복 주기 과도하게 복잡하게 만들지 않음, 사진첨부·자동알림 후순위"
↔ v1 daily 우선, weekly/monthly 로직 후순위, 첨부/알림 제외 → 정합.
```

### 16.5 [정합/참고] completed_by 와 base created_by 관계

```text
ChecklistRecord 는 OperationalBaseModel 의 created_by/updated_by(감사용) 를 상속하고,
별도로 completed_by(수행자, 재완료 시 갱신) 를 둔다. 의미가 다르므로 중복 아님(TECH_SPEC §5 참조).
```

정합성 요약:

```text
- 하드 충돌: 없음.
- 16.1 "당일 마감담당자" 표현 정리: P3-07 에서 OS 문서에 "사전 지정 아님" 명확화 반영(해결).
```

---

## 18. 후순위 기능

```text
- weekly 요일 규칙 / monthly 날짜 규칙 및 판정 로직
- 완료율·누락 통계 대시보드
- 항목/부서 배정 전용 OS 관리 CRUD 화면(초기엔 Django admin)
- 공휴일/휴무일 자동 제외
- 알림 / 자동 독촉
- 사진/파일 첨부(마감 근거)
- 개인 담당자 지정(운영 근거 확인 시에만 재검토)
```
