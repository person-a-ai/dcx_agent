# QA-EDGE-003 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/crawling

Session: `s33a213de835b40fb8085e04e41d7e104`. Capture timestamps (UTC): 2026-10-20T09:18:53.680Z, 2026-10-20T09:19:18.422Z, 2026-10-20T09:22:05.583Z, 2026-10-20T09:33:31.447Z.

## Approved Given / When / Then

```text
Priority: P2
Type: Edge / Viewport
Given: 브라우저 폭 375px
When: 설정 화면과 결과 화면을 연다
Then:
  - 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤)
  - 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다
```

## Executed steps

At 375px inspect settings and completed results, measure document width and scroll regions, scroll the tables left/middle/right. On resume supplement the middle-header screenshot using the completed blocked result on 3012.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤) | Settings and results: viewport=375 and document.scrollWidth=375. Table scroll containers are 206px wide with scrollWidth=600, overflow-x:auto, scrollLeft reaches 394. |
| 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다 | Settings left capture shows all four new rows. Skipped-table headers 채널, 사유, 건수 are visible at left, middle and right positions. |

## Qualifications and preserved attempts

Primary settings/results measurements are on 3010; supplemental 3012 result uses the same component and confirms the previously uncaptured middle header visually. Settings were also measured at 1100/1200/1300px. Screenshot paths are explicit absolute paths. Sidebar is collapsed in the tested mobile state.

## Evidence

- [QA-EDGE-003-settings.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-003-settings-visible.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-visible.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-003-result.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-003-resume-result.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-resume-result.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-003-result-left.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-left.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-result-right.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-right.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-result.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-resume-result-left.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-resume-result-left.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-resume-result-middle.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-resume-result-middle.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-resume-result-right.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-resume-result-right.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-settings-375.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-375.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-settings-right.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-right.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-table-375-left.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-table-375-left.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-table-375-middle.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-table-375-middle.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-003-table-375-right.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-table-375-right.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).
