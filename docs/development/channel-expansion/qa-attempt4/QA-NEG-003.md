# QA-NEG-003 — PASS

Tested HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Source fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`.

URL: http://localhost:3012/pipeline/crawling

Session: `se7bf07c3a54e46a3b6d6da788a8c55b2`. Capture timestamps (UTC): 2026-10-20T09:21:13.832Z, 2026-10-20T09:22:53.940Z, 2026-10-20T09:23:10.150Z, 2026-10-20T09:27:42.197705+00:00.

## Approved Given / When / Then

```text
Priority: P0
Type: Negative / Failure injection
Given: 서버를 `QA_THREADS_MODE=blocked`로 다시 띄웠고, Threads만 켠 세션에서 목록 수집이 끝난 게이트 화면이다
When: "상세 수집 시작"을 누르고 멈출 때까지 기다린 뒤 "여기까지로 마치기"를 누르고 확인한다
Then:
  - 멈춤 배너 "수집이 멈췄습니다"가 보인다
  - 배너에 "Threads" 배지가 보인다
  - 배너에 "Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다." 문구가 보인다
  - "여기까지로 마치기" 후 결과 화면 "건너뛴 항목" 표에 "Threads · 차단으로 여기까지 마침" 행이 있다
  - 서버 로그와 네트워크 기록에 threads.com 로그인 주소 요청이 없다
```

## Executed steps

Use controller's 3012→8012 blocked environment instead of restarting. In a Threads-only session run list to gate, start detail, inspect stopped state, click 여기까지로 마치기 and accept its confirmation. Inspect result, recorded browser requests and copied worker logs/queue.

## Expected versus actual

| Expected (unchanged plan) | Actual |
|---|---|
| 멈춤 배너 "수집이 멈췄습니다"가 보인다 | The stopped banner contains 수집이 멈췄습니다. |
| 배너에 "Threads" 배지가 보인다 | Threads badge is visible in the banner. |
| 배너에 "Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다." 문구가 보인다 | Banner includes Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다. |
| "여기까지로 마치기" 후 결과 화면 "건너뛴 항목" 표에 "Threads · 차단으로 여기까지 마침" 행이 있다 | Result row says Threads · 차단으로 여기까지 마침 · 50건. |
| 서버 로그와 네트워크 기록에 threads.com 로그인 주소 요청이 없다 | Recorded browser network requests and copied list/detail logs contain no threads.com login request; queue has 50 synthetic qa.invalid Threads URLs skipped with blocked reason. |

## Qualifications and preserved attempts

Preserved paused/stopped exact-text waits timed out because the banner contains additional text. state2 proves the complete banner and terminal paused state. Worker stdout is sparse: list.log contains a snapshot identifier and detail.log is empty. This is inspection of the approved hook's logs and browser network record, not a complete backend wire capture or validation of live Threads. See logs/blocked and QA-NEG-003-log-inspection.json.

## Evidence

- [QA-NEG-003-gate.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-gate.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-003-state2.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-state2.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-003-confirm.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-confirm.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-003-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-final.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-003-log-inspection.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-log-inspection.json) — DOM, API output, timestamps and/or recorded tool result.
- [QA-NEG-003-final.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-final.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-NEG-003-gate.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-gate.png) — screenshot saved at the explicit absolute path shown in this link.
- [QA-NEG-003-state2.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-state2.png) — screenshot saved at the explicit absolute path shown in this link.

Console/network: [console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json); original per-capture `events` arrays are retained. No captured console error or pageerror; development warnings include logo aspect ratio and unused CSS preload. Direct API validations are preserved in the listed response JSONs (browser page request events do not include every APIRequestContext call).

Preserved tool-error captures: [QA-NEG-003-paused.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-paused.json), [QA-NEG-003-stopped.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-stopped.json). These are not treated as passing assertions.
