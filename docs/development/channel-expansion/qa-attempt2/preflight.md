# Independent browser QA preflight — PASS

- Skill read first: `/Users/yunho/.codex/skills/harness-browser-qa/SKILL.md`.
- Executor: Codex, role browser-qa, fresh session; no implementation/review work performed by this QA worker.
- Actual runtime `CODEX_THREAD_ID` / `CODEX_SESSION_ID`: `01a15813-127f-7a82-88f3-49c75511ec0a`.
- Companion dispatch session: `9251127c-9663-4223-85bb-09f9c61d81cd`.
- Worktree: `/Users/yunho/Documents/dcx_agent-channels-build`; branch `feature/channel-expansion`.
- Initial observed HEAD and tested commit: `c597b2a678231016e51b0d3644f3d6df921810c2`.
- Initial/final fingerprint: `f722a6089a25d90ce9e44d679f01fa0e996152689d2f302cdf272972fafad49c`.
- `git diff --stat c597b2a678231016e51b0d3644f3d6df921810c2..HEAD -- . ':(exclude)docs'`: empty at preflight and final verification. Working tracked product diff also empty. See [integrity-final.json](integrity-final.json).

## Browser / live access

Playwright MCP discovered in the live tool metadata after tool_search returned unsupported-call. Its actual schemas were read before use. Config: `/Users/yunho/.codex/config.toml`, command `/Users/yunho/.codex/tools/playwright-mcp/node_modules/.bin/playwright-mcp`, args `--browser chrome --isolated`. No headless option; visible Chrome used. A fresh isolated initial context opened main tab 0. Additional QA tabs and isolated contexts were created during testing.

- 2026-10-20T06:50:40Z: opened `http://localhost:3000`, redirected to `/pipeline/start`; rendered DCX Pipeline with no existing session.
- Inspected live body DOM, including all channel buttons, before targeting.
- 2026-10-20T06:50:58.449Z: harmless Threads selection click; `aria-pressed=true`, project preview changed to Threads.
- Screenshot saved with explicit absolute path `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/preflight.png`. File existence checked; image opened and inspected.
- Browser HTTP APIs reached all tested backends. Shell `curl localhost:8000` failed under sandbox network restrictions, so seed/helper scripts executed through Playwright's HTTP request context. No server was started/stopped by QA.
- Browser waits used actual visible headings, table states, responses and API status; no arbitrary sleep used.
- Main console: 0 errors, logo aspect-ratio warning; [console-main.log](console-main.log). Browser network: [network-main.log](network-main.log). Variant callbacks are saved in the corresponding scenario JSON.

## Controller-started servers and substitutions

| Case | Frontend | Backend | Controller environment |
|---|---|---|---|
| Main | http://localhost:3000 | http://localhost:8000 | local/fresh data, fake embedder, channel_expansion_qa hook, real channels enabled |
| QA-NEG-002 | http://localhost:3001 | http://localhost:8001 | empty PLAYWRIGHT_BROWSERS_PATH; used instead of a server restart |
| QA-NEG-003 | http://localhost:3002 | http://localhost:8002 | QA_THREADS_MODE=blocked; used instead of a server restart |
| QA-REG-001 retry | http://localhost:3003 | http://localhost:8003 | controller-added FIXTURE_CORPUS_PATH (2,000 synthetic rows), NEXT_PUBLIC_INTERNAL_TOOLS=true |

All four frontends/backends were reachable through the real browser. Environment details are controller-provided and corroborated by available_sources, blocked behavior and fixture results; QA did not claim to independently dump every server environment variable.

The original main environment lacked usable fixture configuration: fixture PUT returned 422 sources_unavailable, and the fixture UI row was absent. The controller supplied 3003/8003 after receiving this finding. First sample on that environment used `에어컨 청소`, normalized to `에어컨청소`, which does not occur literally in the provided synthetic corpus. Preserved that zero-result attempt; created a fresh session using `에어컨`, a literal corpus match. The approved QA-REG-001 does not prescribe a keyword. Final sample collected 2,000 documents.

Seed script: [seed.js](seed.js), run through the Playwright `filename` command; [seed-output.json](seed-output.json) preserves the initial rejected fixture setup and [seed-output-2.json](seed-output-2.json) records the three requested session types in each original environment. [sample-case.js](sample-case.js) seeds and drives the controller-added environment. All state creation/configuration uses HTTP/app actions; product source and Git remain read-only. No data directories were wiped.

## Evidence storage exception / tooling limits

The MCP automatically created `.playwright-mcp/console-2026-10-20T06-50-40-485Z.log` outside the assigned QA directory on initial navigation. This was reported immediately and is finding QA-F-002. QA did not request that path, alter MCP config, or delete the outside artifact. All explicitly requested screenshots, scripts, console/network captures and reports are under the assigned QA folder, plus the authorized top-level qa.json. Controller-owned `build.json`/`review.json` appeared during the run; QA did not create or modify them.

Several helper attempts had locator-role/heading mismatches, a beforeunload confirmation, or returned before background execution evidence could be recovered; raw errors are preserved. Actual live DOM was re-inspected and the completed relevant state was captured with API verification. Those tool errors are not counted as product failures. A final optional screenshot enrichment found that the original tabs were no longer available (browser inventory returned only about:blank); all required scenario evidence had already been saved. No PASS depends on that attempt. A contact-sheet helper was unavailable because system Python has no PIL; original saved images were inspected directly instead.

## Final evidence

[summary.md](summary.md) contains per-ID results. One report per active ID includes unchanged approved assertions, steps, timestamps, DOM/API output, screenshot paths and notes about retries. [server-logs/README.md](server-logs/README.md) identifies controller-provided QA-NEG-003 worker logs and the access-log limitation. QA independently read the copied worker logs; no threads.com URL appears. The fake adapter's no-network blocked branch and browser request records corroborate the scoped assertion; no real-site login test was attempted.
