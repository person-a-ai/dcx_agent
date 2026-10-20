# Independent browser QA — FAIL

{'PASS': 12, 'FAIL': 1, 'BLOCKED': 4, 'NOT_RUN': 0}

Exact-commit acceptance is blocked by external source/HEAD changes and server loss.

| ID | Result | Actual |
|---|---|---|
| [QA-E2E-001](QA-E2E-001.md) | PASS | All four new rows occur once with 새 채널, available switches, required descriptions, and existing five channels. Each new switch toggled off/on. |
| [QA-E2E-002](QA-E2E-002.md) | PASS | Reloaded inputs5/2/30; GET config5/120/1800. Required notice exists; switching vlog off removes its settings group. |
| [QA-E2E-003](QA-E2E-003.md) | PASS | Gate heading and both notices present; qa-empty zero badge; expanded 에어컨청소 row shows all four channels.86 URLs. API normalizes requested 에어컨 청소 to 에어컨청소. |
| [QA-E2E-004](QA-E2E-004.md) | PASS | Running/completed tables have skipped column. Completed vlog2(자막 없음), 지식iN2(삭제된 글), Threads완료. Status skipped.youtube_vlog.no_ko_captions=2. |
| [QA-E2E-005](QA-E2E-005.md) | PASS | Skipped rows show vlog/한국어 자막 없음/2개 영상 and 지식iN/삭제된 글/2건 matching report. Four distribution names, 영상8개→구간16, preprocessing button.90 collected documents. |
| [QA-E2E-006](QA-E2E-006.md) | BLOCKED | Observed completion with original90/token90/embed90 and no error; all four source choices present before execution. Backend creation07:44:50Z, but final UI/API captured07:46:15Z after external source drift. Exact-commit final acceptance withheld. |
| [QA-NEG-001](QA-NEG-001.md) | PASS | 30/10 disables Save and list start. PUT422 invalid_request; saved config remains5/120/1800 before and after. |
| [QA-NEG-002](QA-NEG-002.md) | PASS | Threads unavailable badge and exact Crawl4AI missing-browser sentence; switch disabled; available_sources excludes threads; PUT422 sources_unavailable. |
| [QA-NEG-003](QA-NEG-003.md) | PASS | Required paused banner/Threads badge/no-login sentence. Accepted finish-partial confirm; result Threads/차단으로 여기까지 마침/50건. Browser network and copied worker logs contain no Threads login request. Logs are sparse(detail.log empty,list.log snapshot only); this is the approved network-free hook, not a real-site trace. |
| [QA-NEG-004](QA-NEG-004.md) | PASS | PUT videos_per_keyword=0 returned422 invalid_request. |
| [QA-EDGE-001](QA-EDGE-001.md) | BLOCKED | Observed empty-list notice,0 estimated URLs,no error banner. Execution07:46Z occurred after external source modifications; cannot accept against immutable99606c7. |
| [QA-EDGE-002](QA-EDGE-002.md) | FAIL | After creatingv2(201), opening read-onlyv1 shows saved-settings screen, not the result/skipped-items table. Writes absent/disabled. Required table assertion fails. Observation followed external source drift; attribution to exact commit requires clean rerun. |
| [QA-EDGE-003](QA-EDGE-003.md) | BLOCKED | Before drift, settings/results both document scrollWidth=innerWidth=375; table overflow:auto, scrollWidth600/clientWidth206, actual scrollLeft394. Result headers exposed by horizontal scrolling. Comprehensive settings-header sweep occurred only after drift, so full exact-commit assertion incomplete. |
| [QA-EDGE-004](QA-EDGE-004.md) | PASS | Saved0/1 minute boundary successfully; GET min_duration_s0,max_duration_s60. |
| [QA-REG-001](QA-REG-001.md) | PASS | Separate copied-frontend environment completed2000 documents; no-skipped message and preprocessing button; API report matches. |
| [QA-REG-002](QA-REG-002.md) | PASS | Comments video-count/max-comments fields20/500. Cafe/blog/ppomppu/clien concurrency1 and interval0.5; blog1/0.5. |
| [QA-REG-003](QA-REG-003.md) | BLOCKED | Fresh project form exposes all existing and four new choices. Navigation load wait timed out but DOM rendered. Source drift and backend connection refusal prevented channel-selection/save/GET verification. |
