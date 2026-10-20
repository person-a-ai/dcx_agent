# QA-EDGE-002 — FAIL

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3010/pipeline/crawling

Session: `s33a213de835b40fb8085e04e41d7e104`. Capture timestamps (UTC): 2026-10-20T09:23:24.719Z, 2026-10-20T09:23:32.625Z, 2026-10-20T09:23:48.995Z, 2026-10-20T09:24:03.428Z, 2026-10-20T09:32:36.912Z.

## Approved Given / When / Then

```text
Priority: P1
Type: Edge / Permission (read-only)
Given: QA-E2E-005가 끝난 세션에서 새 버전을 만들어, 끝난 버전이 과거 버전(열람 전용)이 됐다
When: 과거 버전의 크롤링 화면을 연다
Then:
  - 결과 화면의 "건너뛴 항목" 표가 보인다
  - "일시 정지하기" · "다시 수집" 등 쓰기 버튼이 보이지 않거나 비활성화돼 있다
```

## Executed steps

After completing main collection, create v2 from v1 at stage2 (HTTP 201). Open version history and select v1. Inspect historical crawling. Repeat v1 selection after resuming the same QA run.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 결과 화면의 "건너뛴 항목" 표가 보인다 | FAIL: no skipped-items/result table exists. The page instead says 저장된 수집 설정을 확인합니다 and only renders saved configuration. |
| "일시 정지하기" · "다시 수집" 등 쓰기 버튼이 보이지 않거나 비활성화돼 있다 | Pause is absent; restart is disabled in the captured Playwright assertion. Read-only fields are disabled. |

## Qualifications and preserved attempts

Active version=v2, historical version=v1, collection=c1. Reproduced at 09:32:36Z. The table's actual accessible name on active results is 채널별 건너뛴 사유; the historical snapshot has no tables at all, independently of the recorded skippedTableCount selector. Creating a new version is a separate action and does not mutate v1.

## Evidence

- [QA-EDGE-002-before.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-before.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-002-created.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-created.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-002-past.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-past.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-002-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-final.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-002-resume.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-resume.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-EDGE-002-before.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-before.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-002-created.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-created.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-002-final.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-final.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-002-past.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-past.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-EDGE-002-resume.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-002-resume.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).
