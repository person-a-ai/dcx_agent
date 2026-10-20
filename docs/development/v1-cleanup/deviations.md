# v1-cleanup · 승인 계획과 다르게 진행한 것

승인된 01·02·03·QA 문서는 하네스가 해시로 고정하므로 고치지 않고, 달라진 점을 여기에 남긴다.

| # | 날짜 | 무엇 | 왜 | 결정 |
|---|---|---|---|---|
| DV-1 | 2026-10-20 | `test_legacy_session_preprocess_still_reads_old_crawl` 삭제를 T3에서 T1로 앞당김 | T1이 collection 없는 옛 crawl 경로를 지우면서 이 v1 전용 테스트가 깨짐. 같은 파일이 T1 허용 목록에 있었음 | Controller(작업 순서 조정, 범위·QA 기대값 변화 없음) |
| DV-2 | 2026-10-20 | **crawl4ai 유지** — T4에서 `requirements.txt`의 `crawl4ai`, `constraints.txt`의 crawl4ai 계열 고정, README `crawl4ai-setup` 안내, `test_crawl4ai_not_required_or_documented` 삭제를 뺀다. T4는 `workflow.py` 삭제만 한다 | 병행 중인 채널 확장 작업(`/Users/yunho/Documents/dcx_agent-channels`, `docs/development/channel-expansion/03-plan.md`)이 Threads 채널을 crawl4ai/Playwright로 렌더링한다. 두 브랜치가 합쳐지면 삭제가 그 작업을 깨뜨림 | 사용자(부모 세션에서 "A. v1 정리에서 삭제 빼기" 선택, 이 세션에서 "승인된 이탈로 기록" 선택) |
| DV-3 | 2026-10-20 | 02-design.md §1-2의 "375px에서 배너 버튼이 다음 줄로 내려간다(ds-note의 기존 줄바꿈)"는 사실이 아니었다(목업 전용 CSS). T5 리뷰 FAIL(P2) 후 review-fix `6bcaa30`에서 `.later-stage-banner` 범위 CSS로 구현 | 설계 문서 오류 | Controller(리뷰 지적 반영) |
| DV-4 | 2026-10-20 | T6에서 `components/SNAGraph.tsx`를 지우지 않고 남김 | v2 `components/segment/WordNetwork.tsx`가 `'../SNAGraph'`로 import한다(계획 당시 grep이 상대 경로를 놓침) | Controller(삭제 범위 축소, v2 보호) |

영향: 01-brainstorm.md "문제 1"과 성공 기준, 02-design.md 2-1 표, 03-plan.md Task 4의 crawl4ai 관련 문장은 DV-2로 대체된다. QA 계획에는 crawl4ai 시나리오가 없어 영향 없음.

## 1차 브라우저 QA 결과와 재계획 (2026-10-20)

하네스 실행 `v1-cleanup`(보관: `/Users/yunho/Documents/dcx_agent-v1-cleanup-harness-archive-r1`)의 browser-qa에서 19개 중 14 PASS, 5 FAIL(증거: [qa/qa.json](qa/qa.json)).

- F-01(QA-EDGE-002)·F-04(QA-EDGE-003) — **실제 결함.** 게이트가 `prep.derivedRef`만 보는데 백엔드는 전처리 시작 시점에 `derivedRef`를 쓰고(`routers/prep.py:115`) 3단계 재시작 후에도 남긴다(`status: stale`, `context/versions.py:143`).
- F-02(QA-E2E-004) — QA 계획 오류. `/sessions`는 모든 페이지의 사이드바 세션 목록(`SessionList`)이 부른다.
- F-03(QA-E2E-005) — QA 계획 오류. 페르소나 화면(이번 정리에서 안 바뀜)이 구획 확정 전에 `/segment/{sid}/personas`를 불러 409를 받고 브라우저가 콘솔에 남긴다. main과 같다.
- F-05(QA-REG-001) — QA 계획 오류. D-306 이후 `/insights`가 바로 넘어가 인사이트 챗봇 UI에 닿을 수 없다(B-120에 기록된 현황).

사용자 결정(2026-10-20): "작게 재계획". 새 실행 `v1-cleanup-r2`(같은 브랜치 위)에서 게이트 규칙을 고치고 QA 계획 3개를 바로잡는다 → [../v1-cleanup-r2/01-brainstorm.md](../v1-cleanup-r2/01-brainstorm.md).
