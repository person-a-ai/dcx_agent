# v1-cleanup · 승인 계획과 다르게 진행한 것

승인된 01·02·03·QA 문서는 하네스가 해시로 고정하므로 고치지 않고, 달라진 점을 여기에 남긴다.

| # | 날짜 | 무엇 | 왜 | 결정 |
|---|---|---|---|---|
| DV-1 | 2026-10-20 | `test_legacy_session_preprocess_still_reads_old_crawl` 삭제를 T3에서 T1로 앞당김 | T1이 collection 없는 옛 crawl 경로를 지우면서 이 v1 전용 테스트가 깨짐. 같은 파일이 T1 허용 목록에 있었음 | Controller(작업 순서 조정, 범위·QA 기대값 변화 없음) |
| DV-2 | 2026-10-20 | **crawl4ai 유지** — T4에서 `requirements.txt`의 `crawl4ai`, `constraints.txt`의 crawl4ai 계열 고정, README `crawl4ai-setup` 안내, `test_crawl4ai_not_required_or_documented` 삭제를 뺀다. T4는 `workflow.py` 삭제만 한다 | 병행 중인 채널 확장 작업(`/Users/yunho/Documents/dcx_agent-channels`, `docs/development/channel-expansion/03-plan.md`)이 Threads 채널을 crawl4ai/Playwright로 렌더링한다. 두 브랜치가 합쳐지면 삭제가 그 작업을 깨뜨림 | 사용자(부모 세션에서 "A. v1 정리에서 삭제 빼기" 선택, 이 세션에서 "승인된 이탈로 기록" 선택) |

영향: 01-brainstorm.md "문제 1"과 성공 기준, 02-design.md 2-1 표, 03-plan.md Task 4의 crawl4ai 관련 문장은 DV-2로 대체된다. QA 계획에는 crawl4ai 시나리오가 없어 영향 없음.
