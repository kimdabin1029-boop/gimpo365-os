# OS_TASKS.md

# 김포365OS 작업 목록

## 문서 버전

```text
문서명: OS_TASKS.md
문서 버전: v0.2
최종 수정일: 2026-07-08
문서 범위: 김포365OS의 실제 작업 목록(살아있는 문서). 진행 상태를 추적한다.
```

## 변경 이력

| 버전 | 수정일 | 변경 요약 |
| --- | --- | --- |
| v0.2 | 2026-07-08 | 검토 반영: 경로 규칙 확정(OS_*.md 루트, 리포트·모듈문서만 docs/), TECH_SPEC 등 참조를 절 제목 기준으로 변경, Phase 1 착수 전제에서 T-B4/B5 성격 분리, T-A1/T-A2 커밋 완료 반영 |
| v0.1 | 2026-07-08 | 최초 작성. 코드조사 후속작업 흡수, 문서 세트 현황 반영, Phase 1 착수 작업 단위 연결 |

---

## 1. 문서 목적과 사용법

이 문서는 김포365OS의 **실제 작업 목록**이다. 다른 문서와 달리 **계속 갱신되는 살아있는 문서**다.

```text
기준·절차·설계 결정은 여기에 다시 쓰지 않는다. 해당 문서를 가리킨다.
이 문서는 "지금 무엇을, 어떤 순서로, 어디까지 했는가"만 다룬다.
작업 단위는 작게. 한 항목은 하나의 작업 단위 = 하나의 커밋을 지향한다.
문서/코드/migration/DB/배포 작업을 한 항목에 섞지 않는다. (OS_WORKING_RULES)
```

상태 표기:

```text
[x] 완료   [~] 진행중   [ ] 예정   [!] 막힘/결정필요
```

---

## 2. 현재 상태 요약 (스냅샷)

```text
단계: Phase 1 (OS 최소 틀) 착수 준비 — 문서 기반 구축 단계
브랜치: docs/os-foundation (문서 작업 중)
문서 세트: 초안 완료, 검토 반영 중
코드: 아직 OS 셸 미착수. 안전화(T-A1/T-A2)만 선반영 완료.
```

---

## 3. 문서 세트 현황

김포365OS 기준 문서. 대부분 초안·검토 완료 상태이며, 일부는 조사 결과 반영이 남아 있다.

```text
[x] CLAUDE.md                      (최상위 강제층)
[x] OS_PRODUCT_SPEC.md             (v0.2)
[x] OS_ARCHITECTURE.md             (v0.2, 아래 T-B3 반영 대상 일부 남음)
[x] OS_ROADMAP.md                  (v0.2)
[x] OS_WORKING_RULES.md            (v0.2)
[x] OS_TECH_SPEC.md                (v0.2, 아래 T-B3 반영 대상 일부 남음)
[x] OS_ENVIRONMENT_BASELINE.md     (v1.0)
[x] OS_DB_OPERATIONS.md            (v0.2)
[x] OS_OPERATIONS_SETUP.md         (v0.2)
[x] OS_MANUAL_QA_CHECKLIST.md      (v0.2)
[~] OS_TASKS.md                    (이 문서)
[x] docs/CODE_RECONCILIATION_REPORT.md (조사 리포트)
```

모듈 문서:

```text
[x] docs/modules/inventory/INVENTORY_*.md (기존 보존)
[ ] docs/modules/notice/                  (Phase 2에서 생성)
[ ] docs/modules/checklist/               (Phase 3에서 생성)
```

> 경로 규칙(확정): 기준 문서(CLAUDE.md, OS_*.md)는 저장소 루트에 둔다. 조사 리포트(`docs/CODE_RECONCILIATION_REPORT.md`)와 모듈 문서(`docs/modules/`)만 `docs/` 아래에 둔다.

---

## 4. 코드조사 후속 작업 (Reconciliation Follow-up)

`docs/CODE_RECONCILIATION_REPORT.md`의 발견 10건에 대한 처리. (원본: 코드조사_후속작업목록)

### 4.1 안전 (우선)

```text
[x] T-A1  settings.py POSTGRES_DB default 제거 + .env.example 안전화 (D-05)
          → 완료(코드 반영·검증·커밋). .env 미설정 시 명시적 실패 확인함.
[x] T-A2  .gitignore에 *.dump/*.backup/*.sql/*.zip 추가 (D-10)
          → 완료(반영·커밋).
```

### 4.2 문서 정합

```text
[x] T-B1  OS_ENVIRONMENT_BASELINE.md 저장소 반입 (D-03) → 루트 반입 완료
[ ] T-B2  기준표 소폭 갱신 (D-04/06/08)
          - §8 백업 위치: 현행 backup_db.bat, E:\gimpo365-backup\db 명확화 (OneDrive는 구 잔재)
          - §1 OS 빌드 10.0.26100 → 10.0.26200.0
          - §3 패키지표에 openpyxl==3.1.5 추가
[ ] T-B3  폴더 목록·스택 버전 반영 (D-09)
          - OS_TECH_SPEC / OS_WORKING_RULES 폴더 목록에 scripts/ 추가
          - OS_TECH_SPEC 스택 버전(Django 6.0.6 / psycopg 3.3.4 / Python 3.14.3), 기준표 참조 형태
          - (OS_TECH_SPEC 수정 지시서와 함께 처리)
[ ] T-B4  D-01 rename 사후 확인 (OS_OPERATIONS_SETUP.md 참조 13곳 grep 재확인)
[!] T-B5  backup_db.bat 실제 위치 확정 → OS_DB_OPERATIONS.md 3.1 TODO 채우기
          - 결정 필요: 저장소 내 위치, scripts/ 이관 여부
```

### 4.3 남은 결정

```text
[!] settings 관련 T-A1은 완료됐으나, .env.example 최종 내용(리허설 예시 vs 빈 값)이
    OS_OPERATIONS_SETUP의 .env 구성 절 전제와 일치하는지 확인 필요.
```

---

## 5. Phase 1 — OS 최소 틀 (다음 착수)

기준: OS_ROADMAP Phase 1, OS_ARCHITECTURE의 초기 구현 우선순위 절. 각 항목은 별도 작업 단위.

> 착수 전제(정리):
> - T-B2 / T-B3(기준표 갱신·폴더/버전 반영): 문서 혼선을 줄이므로 **착수 전 정리 권장.**
> - T-B4(rename 사후 확인): 단순 확인이므로 Phase 1과 **병행 가능.**
> - T-B5(backup_db.bat 위치): DB 운영 문서(OS_DB_OPERATIONS) 보강 항목이라 **OS 셸 구현을 막지 않는다.** 별도로 처리.
> 모든 코드 작업은 리허설에서. 작업 전 `.env` POSTGRES_DB 확인(OS_OPERATIONS_SETUP의 서버 실행 전 공통 체크).

```text
[ ] P1-01  README.md를 gimpo365-os 기준으로 정비 (문서 지도)
[ ] P1-02  루트 URL을 OS 홈으로 연결 (config urls)
[ ] P1-03  OS 홈 view/template 생성 (core) — 모듈 카드 배치
[ ] P1-04  공통 base template / navbar / sidebar 정비
[ ] P1-05  Inventory를 "운영관리 > 재고관리" 위치로 메뉴 배치
[ ] P1-06  준비 중 모듈 placeholder view/template (core) — notices/checklists/manuals/requests/schedules
[ ] P1-07  미구현 모듈을 전 직원에게 "준비 중"으로 노출
[ ] P1-08  권한별 메뉴 노출 확인 (관리자/팀장/직원)
[ ] P1-09  check/test 통과 + OS 공통 smoke QA (OS_MANUAL_QA_CHECKLIST의 OS 공통 smoke QA)
```

Phase 1에서 하지 않을 것 (OS_ROADMAP Phase 1의 "구현하지 않을 것"):

```text
공지/체크리스트 등 실제 CRUD, Inventory 모델 대규모 수정, DB schema 대규모 변경, 파괴적 migration
```

---

## 6. Phase 1.5 — Department/Team 소속 기준 (Phase 1 이후)

기준: OS_ROADMAP Phase 1.5, OS_ARCHITECTURE의 Department/Team 소속 모델 원칙 절, OS_TECH_SPEC의 Department/Team 구현 기준 절.

> 조사 리포트의 Department 관련 결론을 먼저 확인해 분기를 닫는다.

```text
[ ] P15-01 (조사 결론 확인) 기존 코드에 Department/유사 소속 모델이 있는가 → 있으면/없으면 분기 확정
[ ] P15-02 core에 Department/Team 기준정보 설계 (신설 또는 기존 승격)
[ ] P15-03 User–Department/Team 연결 (additive migration, 리허설 우선)
[ ] P15-04 check/test + smoke QA + migration 후 점검 (OS_MANUAL_QA_CHECKLIST의 Migration 후 점검)
```

---

## 7. 이후 Phase (개요만 — 상세는 착수 시 전개)

각 모듈은 착수 시 `docs/modules/<name>/` 문서부터 생성하고, 정착 루프(운영 반영 → 안내 → 관찰 → 조정)까지 완료로 본다.

```text
[ ] Phase 2  Notice v1        (문서형 CRUD 표준 패턴 확립 — CBV, 주석 학습용 첫 구현)
[ ] Phase 3  Checklist v1     (일일 사용 핵심 모듈, Department/Team 기반)
--- 여기까지가 OS MVP 컷라인 ---
[ ] Phase 4  SOP / Manual     (그릇만, 콘텐츠 저작은 별도 상시)
[ ] Phase 5  Internal Request (상태값 3+1로 시작)
[ ] Phase 6  Attendance       (근무표/휴가 확인 수준)
[ ] Phase 7  운영 안정화·확장 검토
```

---

## 8. 배포 전 마무리 후보 (기능 우선, 이후 처리)

지금은 기능 구축 우선. 아래는 배포 전에 정리한다(현재 착수 안 함).

```text
[ ] 백업 자동화 (Windows 작업 스케줄러) + 백업 세대 관리(예: 30일 보관)
[ ] 백업 원외 보관 (NAS 구축 후)
[ ] 운영 서버 상시 실행 방식(부팅 자동 실행/서비스화), waitress 등 운영 WSGI 검토
[ ] 원내 네트워크 바인딩·방화벽 실측 확정
[ ] DJANGO_DEBUG=False / ALLOWED_HOSTS 운영값 확정
[ ] 운영/리허설 작업장 분리 방식 확정 (.env 전환 위험 해소)
[ ] GitHub 원격 저장소 생성·push (현재 로컬 전용)
```

---

## 9. 결정 대기 항목 (모아보기)

```text
[!] backup_db.bat 저장소 내 위치 / scripts 이관 (T-B5)
[!] 복구 표준: 임시 DB 방식 vs 기존 리허설 덮어쓰기 중 기본 (OS_DB_OPERATIONS의 복구 절)
[!] 운영/리허설 동시 상시 유지 방식 (폴더 분리 등) — 리허설 검증 잦아지면 결정
[!] .env.example 최종 형태 (리허설 예시 vs 빈 값)
```

---

## 10. 작업 원칙 리마인더 (요약)

```text
한 번에 하나의 작업 단위. 문서/코드/migration/DB/배포 섞지 않는다.
모든 코드 작업은 리허설에서. 작업 전 .env POSTGRES_DB 확인.
Inventory 핵심 로직·service 계층은 건드리지 않는다.
파괴적 migration 금지. 새 테이블/nullable 필드 추가 중심.
상세 규칙은 CLAUDE.md / OS_WORKING_RULES.md.
```
