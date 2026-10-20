# v1-cleanup-r2 · 01 기획

- 작성: 2026-10-20 · 하네스 실행 `v1-cleanup-r2` (base `c15ea7f`, 브랜치 `chore/v1-cleanup` 위)
- 앞선 실행: `v1-cleanup` — 기획·설계·계획·구현 T1~T6·리뷰는 끝났고 브라우저 QA에서 멈췄다. 경위와 결과: [../v1-cleanup/deviations.md](../v1-cleanup/deviations.md) "1차 브라우저 QA 결과와 재계획", 증거 [../v1-cleanup/qa/qa.json](../v1-cleanup/qa/qa.json).

## 문제

1. **6~9단계 잠금이 너무 일찍 풀리고, 다시 잠기지 않는다(F-01, F-04).** 사이드바와 세 페이지는 `prep.derivedRef`가 있으면 연다. 그런데 백엔드는 전처리를 **시작할 때** `derivedRef`를 저장하고(`backend/app/routers/prep.py:115`), "3단계부터 다시 시작"으로 새 버전을 만들어도 `derivedRef`를 남긴 채 `prep.status`만 `stale`로 바꾼다(`backend/app/context/versions.py:143`). 그래서 전처리가 도는 중이거나 무효가 된 세션에서도 클러스터링·근거 탐색·페르소나·인사이트가 열린다.
2. **승인된 QA 계획의 시나리오 3개가 이번 정리와 무관한 조건을 단언했다(F-02, F-03, F-05).**
   - QA-E2E-004: `/sessions` 요청 금지 — 이 요청은 모든 페이지의 사이드바 세션 목록(`components/SessionList.tsx`)이 보낸다. 원래 뜻은 "옛 인사이트 화면의 세션 목록 호출이 없을 것"이었다.
   - QA-E2E-005: 세 화면 콘솔 오류 0건 — 페르소나 화면(이번 정리에서 안 바뀜)은 구획 확정 전에 `/segment/{sid}/personas`를 불러 409를 받고 브라우저가 이를 콘솔 오류로 남긴다. main과 같은 동작이다.
   - QA-REG-001: 인사이트 화면 챗봇 UI — D-306 이후 `/insights`가 `/pipeline/insights`로 바로 넘어가 닿을 수 없다(B-120에 기록된 현황). API(`POST /insight-chat`)는 200.

## 결정

| # | 결정 | 출처 |
|---|---|---|
| 1 | 6~9단계는 `prep.derivedRef`가 있고 **`prep.status === 'done'`일 때만** 연다. 백엔드 완료 표시 `prepDone`(`routers/sessions.py:121`, `prep.status == "done"`)과 같은 기준 | F-01·F-04 분석 |
| 2 | 진행 중·실패·중단·무효(stale) 세션은 지금의 "전처리 전" 배너와 같은 배너·잠금을 쓴다(새 문구 없음). 옛 세션은 계속 "구버전" 배너 | 화면 변경 최소화 |
| 3 | QA 계획은 새 실행의 QA 계획(QA_PLAN-v1-cleanup-r2.md)으로 다시 승인한다. ID는 바꾸지 않고, 틀린 3개는 `[withdrawn]`으로 남기고 바로잡은 시나리오를 새 ID로 더한다 | 사용자 "작게 재계획" |
| 4 | 페르소나 화면의 409 콘솔 기록, 인사이트 챗봇 UI 도달 불가는 이번 범위가 아니다(각각 기존 동작, B-120) | 범위 유지 |

## 범위

**포함:** 게이트 규칙 1곳(`frontend/src/lib/logic/laterStageGate.ts`)과 그 테스트, QA 계획 수정, 전체 QA 재실행.

**제외:** 1차 실행의 승인 범위 밖 전부(그대로 유지). 백엔드 변경 없음.

## 성공 기준

1. 전처리 진행 중(`prep.status` = running/paused), 실패·중단, 3단계 재시작 후(`stale`)인 새 세션: 사이드바 6~9 잠김, 세 페이지 "전처리를 먼저 완료하세요" 배너.
2. 전처리가 끝나면(`done`) 새로고침 없이 사이드바가 열린다(전처리 화면이 완료 시 세션을 다시 읽음: `components/prep/PrepScreen.tsx:80,118`).
3. 1차 실행에서 PASS한 14개 시나리오가 그대로 PASS.
4. 백엔드 pytest, 프론트 lint · vitest · build 통과.

## 기준선

`c15ea7f`: 백엔드 직렬 pytest 2807 통과, 프론트 lint 통과 · vitest 80파일 962개 통과 · build 통과(1차 실행 build.json).
