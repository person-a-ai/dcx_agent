# QA-REG-001 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3013/pipeline/crawling

Session: `s7c6d9e8136f7487e805cbd6a90b750a0; retry s3dc3562081264047840cf756c7d0acb8`. Capture timestamps (UTC): 2026-10-20T09:24:28.962Z, 2026-10-20T09:24:39.198Z, 2026-10-20T09:24:59.024Z, 2026-10-20T09:26:09.394Z, 2026-10-20T09:26:19.666Z, 2026-10-20T09:26:21.025Z, 2026-10-20T09:26:41.167Z.

## Approved Given / When / Then

```text
Priority: P0
Type: Regression
Given: 개발용 샘플(fixture) 채널만 켠 세션(`ENABLE_FIXTURE_CHANNEL=true`)
When: 목록 수집 → 게이트 → 상세 수집 → 결과까지 진행한다
Then:
  - 결과 화면 "수집 문서"가 0보다 크다
  - "건너뛴 항목이 없습니다." 문구가 보인다
  - "전처리로 이동하기" 버튼이 보인다
```

## Executed steps

On controller's fixture environment 3013→8013, run the first fixture-only seed through list, gate, detail and result. Preserve zero-document result. Create a fresh fixture-only session using corpus-matching keyword 에어컨 via HTTP API, then repeat the entire UI flow.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 결과 화면 "수집 문서"가 0보다 크다 | First attempt: 0 documents, so the >0 Then FAILED. Fresh matching-keyword retry: 2,000 documents, so >0 PASSED. |
| "건너뛴 항목이 없습니다." 문구가 보인다 | Both attempts show 건너뛴 항목이 없습니다.; retry status has empty skip_reasons. |
| "전처리로 이동하기" 버튼이 보인다 | Both results expose 전처리로 이동하기. |

## Qualifications and preserved attempts

Result PASS applies to the fully executed matching-keyword retry; the first failed attempt is preserved and is not relabeled as a pass. The first attempt met the written Given (fixture-only, ENABLE_FIXTURE_CHANNEL=true) but did not meet all Then clauses. Its submitted 에어컨 청소 was stored as 에어컨청소 and did not match the synthetic corpus. The fresh retry used 에어컨, met the same written Given, and met every Then. This plan does not prescribe a specific fixture keyword, so choosing a corpus-matching keyword does not weaken the >0 assertion. The controller supplied a 2,000-row corpus and NEXT_PUBLIC_INTERNAL_TOOLS=true on 3013; section 8 did not originally specify that corpus. Failed retry locator attempts are retained. See sample-seed.js and both result JSONs/screenshots.

## Evidence

- [QA-REG-001-settings.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-settings.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-gate.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-gate.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-first-result.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-first-result.json) — DOM, API output, timestamps and/or recorded tool result.
- [sample-matching-seed-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/sample-matching-seed-final.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-valid-settings.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-valid-settings.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-valid-gate.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-valid-gate.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-valid-running.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-valid-running.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-final.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-REG-001-final.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-final.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-001-first-result.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-first-result.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-001-gate.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-gate.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-001-settings.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-settings.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-001-valid-gate.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-valid-gate.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-001-valid-running.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-valid-running.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-REG-001-valid-settings.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-valid-settings.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).

Preserved tool-error captures: [QA-REG-001-retry-gate.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-retry-gate.json), [QA-REG-001-retry-running.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-retry-running.json), [QA-REG-001-retry-settings.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-001-retry-settings.json). These are not treated as passing assertions.
