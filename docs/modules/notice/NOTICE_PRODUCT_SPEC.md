# NOTICE_PRODUCT_SPEC.md

# 김포365OS Notice Module 제품 명세서

## 문서 버전

```text
문서명: NOTICE_PRODUCT_SPEC.md
문서 범위: 김포365OS Module 2 — Notice(공지) 제품 명세
문서 상태: Notice v1 구현 완료 (Phase 2 마감, P2-07)
전제 문서: OS_PRODUCT_SPEC.md, OS_ROADMAP.md, OS_WORKING_RULES.md, OS_TECH_SPEC.md
```

## 변경 이력

| 버전   | 수정일        | 변경 요약                                          |
| ---- | ---------- | ---------------------------------------------- |
| v0.2 | 2026-07-13 | Notice v1 구현 완료 상태 반영. 운영 기준(§16) 추가. 첨부 v1 제외·reference_url v1 포함·부서 접근제어 유지 |
| v0.1 | 2026-07-11 | P2-00 Notice v1 MVP 제품 명세 초안 작성 (첨부 v1 제외, 외부링크 포함) |

---

## 완료 상태 (P2-07)

Notice v1 은 Phase 2(P2-00~P2-07)로 구현 완료되었다. 본 명세의 v1 포함 범위(§5)와
제외 범위(§6)는 실제 구현과 일치한다. 첨부파일은 v1 제외로 유지하며 v1.1 Attachment Gate(§11)에서
Checklist 정착 이후 검토한다. 운영 기준은 §16 참조.

---

## 0. 문서 성격

이 문서는 Notice Module을 "무엇을, 왜" 만드는지 정의하는 제품 명세서다.

구현 방식(모델·URL·view·권한 코드)은 `NOTICE_TECH_SPEC.md`에서, 작업 단위 분리는 `NOTICE_TASKS.md`에서 다룬다.

이 문서는 P2-00 문서 설계 단계에서 작성되며, 코드·앱·모델·migration을 만들지 않는다.
기존 OS 문서와 충돌하는 표현은 임의로 수정하지 않고 "14. 기존 OS 문서와의 정합성" 절에 "검토 필요"로 기록한다.

---

## 1. 목적

Notice Module은 김포365OS의 **첫 신규 운영 모듈**이다.

Notice의 목적은 두 층으로 나뉜다.

```text
1. 제품 목적
   병원 공지를 김포365OS 안에서 등록·조회·관리한다.

2. 개발 목적(Notice-first)
   가장 단순한 문서형 CRUD 모듈을 먼저 만들어,
   이후 SOP / Manual / Request / Checklist 일부가 재사용할
   문서형 CRUD 표준 패턴(목록/상세/등록/수정/권한/상태값/메뉴 연결)을 확립·안정화한다.
```

Notice-first는 "가장 중요한 모듈이라서 먼저"가 아니라 "가장 단순한 문서형 CRUD라서 패턴 확립용으로 먼저"라는 OS_ROADMAP / OS_WORKING_RULES §18 기준을 따른다.

따라서 Notice v1은 **작고 명확**해야 한다.
김포365OS의 실질적인 일일 사용 핵심 모듈은 Checklist(Phase 3)이며, Notice가 비대해져 Checklist 착수를 지연시키지 않는다.

---

## 2. 운영 배경

현재 김포365한의원은 협업 도구(JANDI)를 사용하고 있으나, 무료요금제에 보관 기간/용량/첨부파일 한계가 있다.
이 때문에 장기적으로 다시 확인해야 하는 공지와 자료가 시간이 지나면 사라지거나 찾기 어려워진다.

장기 보관이 필요한 공지와 자료를 김포365OS 안에 축적할 필요가 있다는 운영 목적은 타당하다.

다만 `OS_ROADMAP.md`의 Notice Phase 가드(8.1)는 다음을 명시한다.

```text
Notice가 비대해지거나 Checklist를 지연시키지 않도록 한다.
Notice의 후순위 기능(확인 독촉, 첨부, 예약 게시 등)은 Checklist 정착 이후에 검토한다.
```

따라서 이번 결정은 다음과 같다.

```text
Notice v1에서는 첨부파일을 제외하고, v1.1 Attachment Gate에서 별도 검토한다.
  (첨부는 JANDI 한계 보완이라는 운영 목적이 있어 중요하지만, 로드맵 가드를 존중해 후순위로 분리한다.)
대신 Notice v1에는 reference_url(외부 링크)을 포함해
  구글드라이브, NAS, 외부 문서 등으로 연결할 수 있게 한다.
```

Notice v1은 순수 문서형 CRUD 패턴 확립에 집중한다.

---

## 3. 적용 대상

```text
적용 조직: 김포365한의원 전 상시 근무자
접속 환경: 원내 네트워크 (원외 접속 차단 원칙 유지)
계정 원칙: 개인 계정 (공용/부서 계정 금지)
```

공지 수신 범위:

```text
전체 공지: 로그인한 전 직원 대상
부서 대상 공지: 특정 Department 소속 직원 대상 (접근제어 기준, 단순 라벨 아님 — §9)
```

---

## 4. 사용자 역할

김포365OS의 역할 체계(`accounts.User.role`)를 그대로 사용한다.

```text
STAFF        일반 직원
TEAM_LEADER  팀장
MANAGER      운영진
ADMIN        관리자
계층: STAFF < TEAM_LEADER < MANAGER < ADMIN
```

Notice에서 각 역할의 기본 동작:

```text
STAFF        자신에게 공개된 게시 공지 조회
TEAM_LEADER  자신에게 공개된 게시 공지 조회
MANAGER      공지 작성 / 수정 + 전체 공지(draft 포함) 조회
ADMIN        공지 작성 / 수정 + 전체 공지(draft 포함) 조회
```

역할과 소속은 분리한다(OS_ARCHITECTURE §14). 역할은 권한 등급이고, 소속(Department)은 공지 대상 범위 판정에 사용한다.

---

## 5. Notice v1 MVP 범위

포함할 것:

```text
공지 목록
공지 상세
공지 등록
공지 수정
전 직원 또는 대상 직원 조회
MANAGER 이상 작성/수정
전체 공지
부서 대상 공지
게시 상태 관리 (draft / published)
중요 공지 뱃지 (is_important)
category (choices 상수)
reference_url 외부 링크 (선택 입력)
```

---

## 6. 제외 범위

Notice v1에서 만들지 않는다.

```text
첨부파일            (→ v1.1 Attachment Gate, §11)
댓글
읽음 확인 / 확인 여부 기록
확인 독촉
푸시 알림 / 자동 알림
예약 게시
상단 고정
노션식 임베드
리치 에디터
본문 중간 이미지 삽입
이미지 미리보기
드래그앤드롭 업로드
첨부파일 버전관리
복잡한 검색
```

주의 — 중요 공지 뱃지와 상단 고정은 다르다.

```text
is_important : 중요 표시 뱃지만 제공         → v1 포함
상단 고정     : 정렬/운영 정책이 필요       → v1 제외
```

---

## 7. 주요 사용 시나리오

```text
1. 전체 공지 게시
   MANAGER가 전 직원 대상 공지를 등록하고 published 로 게시한다.
   전 직원이 OS 홈 → 공지사항에서 목록/상세를 확인한다.

2. 부서 대상 공지
   MANAGER가 특정 부서(예: 데스크) 대상 공지를 등록한다.
   해당 부서 소속 직원과 MANAGER/ADMIN 만 조회할 수 있다(접근제어).

3. 초안 작성 후 게시
   MANAGER가 draft 로 저장해 두고, 준비되면 published 로 전환한다.
   draft 는 일반 직원 목록에 노출되지 않는다.

4. 중요 공지
   중요한 공지에 is_important 뱃지를 붙여 눈에 띄게 한다(상단 고정 정렬은 없음).

5. 외부 링크 공지
   외부 문서/드라이브가 있으면 reference_url 로 연결한다.
   본문에 일반 URL 을 텍스트로 적을 수도 있다(미리보기/임베드 없음).

6. 공지 정정
   내용이 바뀌면 MANAGER가 같은 공지를 수정한다(물리 삭제하지 않음).
```

---

## 8. 권한 원칙

```text
로그인한 직원은 자신에게 공개된 공지를 볼 수 있다.
전체 공지는 로그인 직원 전체가 볼 수 있다.
부서 대상 공지는 해당 Department 직원과 MANAGER/ADMIN 이 볼 수 있다.
department 가 없는 일반 직원은 전체 공지만 볼 수 있다.
MANAGER 이상은 공지를 작성/수정할 수 있다.
STAFF / TEAM_LEADER 는 작성/수정 권한이 없다.
ADMIN 은 Django Admin 관리 권한과 별개로 role 기준(MANAGER 이상) 권한을 따른다.
```

보충:

```text
draft 공지는 작성자 본인과 MANAGER/ADMIN 만 조회할 수 있다.
권한 없는 공지 상세(pk) 접근은 404 를 권장한다(존재 사실 노출 최소화 — TECH_SPEC §8).
작성/수정 화면은 공통 권한 판정(MANAGER 이상)으로 처리하고, 모듈마다 제각각 권한 로직을 만들지 않는다.
```

---

## 9. 부서 대상 공지 접근제어

부서 대상 공지는 **단순 분류 라벨이 아니라 조회 범위 제한이 있는 대상 공지**로 설계한다.

```text
전체 공지 (target_type=all)
- 로그인한 모든 직원이 조회 가능

부서 대상 공지 (target_type=department)
- 해당 target_department 소속 직원이 조회 가능
- MANAGER / ADMIN 은 전체 조회 가능
- 작성/수정 권한은 MANAGER 이상
```

department 없는 사용자 처리 (Phase 1.5: `User.department` nullable 유지):

```text
department 가 없는 일반 직원은 전체 공지만 본다.
department 가 없는 사용자는 부서 대상 공지를 조회할 수 없다.
MANAGER / ADMIN 은 department 유무와 관계없이 전체 공지 관리 범위를 가진다.
```

주의:

```text
부서 대상 공지를 단순 분류 라벨로 해석하지 않는다.
쿼리에서 user.department 를 단독 조건으로 쓰지 않는다
  (None 이면 target_department IS NULL 로 번역되어 의도치 않은 노출 가능 — TECH_SPEC §9).
```

---

## 10. 외부 링크 운영 기준

외부 링크는 첨부파일과 성격이 다르다.

```text
첨부파일: MEDIA 저장 / 다운로드 권한 / 확장자 제한 / 백업 정책 / 파일 유실 리스크
외부 링크: URLField 1개 / 파일 저장 없음 / MEDIA 백업 없음 / 구현 난이도 낮음
```

따라서 Notice v1에는 외부 링크를 포함한다.

```text
Notice v1 에 reference_url 필드를 포함한다.
reference_url 은 선택 입력이다.
구글드라이브, NAS, 외부 문서, 관련 URL 등을 연결하는 용도다.
링크 미리보기, 임베드, 썸네일은 제공하지 않는다.
본문 안에 일반 URL 을 텍스트로 적는 것도 허용한다.
서버가 대상 URL 을 fetch 하지 않는다(저장·표시만).
```

---

## 11. JANDI 한계와 첨부파일 v1.1 게이트

첨부파일은 v1에서 제외하지만, 필요성을 잊지 않도록 별도 게이트로 문서화한다.

**Notice v1.1 Attachment Gate**

```text
- JANDI 무료요금제의 보관/첨부 한계를 보완하기 위한 후보 기능
- Notice v1 CRUD 패턴이 안정화된 뒤 재검토
- 기본 로드맵상 Checklist 정착 이후 검토
- 조기 도입하려면 OS_ROADMAP 8.1 가드 개정이 필요
```

첨부파일 필요성 / 제외 이유 / 향후 처리:

```text
필요성:
- JANDI 한계 보완이라는 운영 목적이 있어 중요함.

제외 이유:
- OS_ROADMAP 8.1 가드에서 첨부를 후순위로 명시함.
- 파일 업로드는 MEDIA 저장, 다운로드 권한, 확장자 제한, 백업 정책 등으로 Notice를 복잡하게 만듦.
- 첫 신규 모듈의 목적은 단순 CRUD 표준 패턴 확립임.

향후 처리:
- Notice v1.1 Attachment Gate에서 재검토.
- Checklist 정착 후 또는 로드맵 개정 후 진행.
```

향후 첨부파일을 구현할 경우 필요한 설계(기록용):

```text
- NoticeAttachment 모델
- 파일 크기 제한 / 확장자 제한
- 다운로드 권한 검사 view (MEDIA_URL 직접 링크 공개 금지, 로그인/권한 확인 view 경유)
- MEDIA_ROOT / MEDIA_URL 설정
- media 파일 백업 정책 (OS_DB_OPERATIONS 보강 필요)
- 환자정보/개인정보 업로드 금지
- 부서 대상 공지의 첨부는 그 공지를 볼 수 있는 사용자만 다운로드 가능해야 함
- 확장자 검사는 파일 위장에 취약 → content-type/파일 시그니처 검증은 후순위 보강 항목
```

---

## 12. 환자정보 / 개인정보 업로드 금지 원칙

```text
Notice는 내부 공지 기능이지 환자 기록 저장소가 아니다.
다음은 본문/외부링크(및 향후 첨부)에 올리지 않는다.
  - 환자 진료기록, 차트, 처방 등 진료자료
  - 환자 개인정보
  - 직원 개인정보(주민번호, 계좌 등 민감정보)
  - 운영 계정 비밀번호, 접속정보 등 비밀값
저장소가 public 전제임을 고려해, 운영 상세·개인정보를 공지 본문에 남기지 않는다.
민감 자료 공유가 필요하면 Notice 가 아닌 별도 안전 경로를 사용한다.
```

---

## 13. 성공 기준

```text
MANAGER 이상이 공지를 등록/수정하고 draft ↔ published 를 전환할 수 있다.
전 직원이 자신에게 공개된 게시 공지 목록과 상세를 볼 수 있다.
전체 공지와 부서 대상 공지가 접근제어 기준으로 구분되어 노출된다.
department 없는 직원은 전체 공지만 보고, 부서 대상 공지는 보이지 않는다.
is_important 뱃지와 category 분류가 표시된다.
reference_url 외부 링크를 등록하고 상세에서 이동할 수 있다.
문서형 CRUD 표준 패턴(제네릭 CBV + OperationalBaseModel + 공통 권한)이 검증되어,
  SOP/Manual·Request 가 이 패턴을 재사용할 수 있다.
Inventory 기능이 깨지지 않는다.
```

정량 지표는 후속 운영 관찰 단계(모듈 정착 루프)에서 정의한다.

---

## 14. 후순위 기능

Checklist(Phase 3) 정착 이후 검토한다.

```text
첨부파일 (Notice v1.1 Attachment Gate)
공지 확인 여부 기록 / 확인 독촉 / 확인률 리포트
상단 고정 정렬
예약 게시 / 만료일 자동 숨김
category 고도화 (별도 테이블화 등)
자동 알림 (카카오톡 등 외부 채널 병행 포함)
이미지 미리보기 / 리치 에디터 / 본문 이미지
복잡한 검색
```

---

## 15. 기존 OS 문서와의 정합성 (검토 필요 항목)

P2-00 원칙: 기존 문서 표현을 임의 수정하지 않고, 충돌/차이를 여기에 "검토 필요"로 기록해 다빈에게 보고한다.

### 15.1 OS_ROADMAP 8.1 가드와의 정합 — 충돌 없음

```text
이번 Notice v1 은 첨부파일을 v1 에서 제외하고 v1.1 Attachment Gate 로 분리했다.
→ OS_ROADMAP 8.1 "첨부는 Checklist 정착 이후 검토" 가드와 충돌하지 않는다.
```

### 15.2 [정합] OS_TECH_SPEC §24 Notice 후보 필드

```text
OS_TECH_SPEC §24 후보 필드: title, body, category, is_important, is_active, created_by, updated_by, created_at, updated_at
이번 v1: title, content(=body), category, is_important, target_type, target_department, status(draft/published), reference_url + (OperationalBaseModel: created_by/updated_by/created_at/updated_at/is_active), published_at

- category / is_important : §24 와 일치(v1 포함). 정합.
- 첨부파일 : §24 후순위 목록에 있음 → v1 제외로 정합.
- 추가(additive) 필드: target_type, target_department, status, reference_url, published_at.
```

### 15.3 [검토 필요] status(draft/published) vs is_active

```text
OS_TECH_SPEC §24 는 게시 여부를 is_active 로만 표현할 여지가 있다.
이번 설계는 status(draft/published)와 is_active(논리적 삭제/비활성)를 의미상 분리한다.
  status    = 게시 상태(초안/게시)
  is_active = 논리적 삭제 또는 운영상 비활성 (OperationalBaseModel 제공)
권고: 두 축을 섞지 않는다. 목록 쿼리는 published + is_active=True 를 기본 노출 조건으로 한다.
      본문 필드명 body vs content 는 구현 단계에서 코드 스타일 맞춰 확정.
```

### 15.4 [검토 필요] reference_url / target_type 은 §24 목록 밖 추가 필드

```text
OS_TECH_SPEC §24 후보 필드에는 reference_url, target_type, target_department 가 없다.
이번 v1 은 이를 additive 로 추가한다(파괴적 변경 아님).
권고: 문서 수정 불필요. Notice 문서에 근거를 남긴다(본 문서 §9·§10).
```

### 15.5 [검토 필요] 확인 여부 기록

```text
OS_PRODUCT_SPEC §7.2 는 Notice 예정 기능에 "직원 공지 확인 여부 기록"을 포함한다.
이번 v1 은 읽음 확인을 제외한다.
충돌 성격: 약함(예정 표현). v1 에서는 후순위로 둔다(본 문서 §6·§14).
```

### 15.6 [해결] OperationalBaseModel 신설 완료

```text
OS_TECH_SPEC §17 의 공통 abstract base model 은 P2-01.5 에서
core.OperationalBaseModel(abstract, migration 없음)로 신설 완료되었다.
→ Notice 는 이를 상속한다.
→ created_by / updated_by 는 SET_NULL + null=True/blank=True 로 확정(P2-01.6, CASCADE 금지).
```

정합성 판단 요약:

```text
- 하드 충돌: 없음. (이번 v1 은 OS_ROADMAP 8.1 가드와 정합)
- 소프트 차이: 15.3 / 15.4 / 15.5 → 구현 단계 확정 또는 후순위 처리로 흡수 가능.
- 선행 작업: 15.6 OperationalBaseModel 신설(P2-01.5) 완료.
```

---

## 16. Notice 운영 기준 (v1)

```text
- 공지는 MANAGER 이상이 등록/수정한다. (STAFF/TEAM_LEADER 는 조회 중심)
- 일반 직원은 자신에게 공개된 공지를 조회한다.
- 부서 대상 공지는 해당 부서 직원과 MANAGER/ADMIN 이 볼 수 있다.
- department 가 없는 직원은 전체 공지만 본다.
- 첨부파일은 아직 지원하지 않는다(v1 제외).
- 외부 문서가 필요한 경우 reference_url(외부 링크)을 사용한다.
- 환자 개인정보/진료자료는 공지 본문이나 링크에 올리지 않는다.
```

주의:

```text
reference_url 은 외부 링크 필드일 뿐이다.
외부 링크에 어떤 자료가 있는지까지 OS 가 검증하지 않는다.
운영자가 개인정보/진료자료 링크를 올리지 않도록 주의해야 한다.
```
