# Browser QA preflight — PASS

This is the same independent QA run resumed after the reported capacity interruption, not a new implementation or review session. Executor: Codex; role: browser-qa; dispatch/runtime thread: `01a1583f-bc1a-7ba2-af7a-590ba8288a20`. `freshSession: true` describes the independent QA origin. Earlier attempts' verdicts are not inherited.

Skill followed: `/Users/yunho/.codex/skills/harness-browser-qa/SKILL.md`. Approved plan: `docs/development/channel-expansion/QA_PLAN-channel-expansion.md` (17 active IDs). Product code and Git remained read-only. All manually created evidence/helpers are under this QA directory or the authorized sibling qa.json.

HEAD: `8d99f5323e800a0860f363751c783a4551b69714`. Fingerprint: `3bae4a00deb67d67b3ed5f9ab6c8a9907a2795857b93e93c8e9ab9700c5731fc`. Both match the resumed brief. The resumed initial terminal checks matched, and [integrity-resume.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/integrity-resume.json) records a further check at 09:34:07Z with empty tracked diff. Final check is in integrity-final.json.

## Browser and access

Live tool metadata exposed Playwright MCP. Chrome 155.0.8059.85 is configured isolated with no headless flag (visible window preferred and used by the configured browser). Viewport 1280×900 for desktop; 375×900 for mobile. [browser-identity.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/browser-identity.json)

Original preflight opened http://localhost:3010/pipeline/start, inspected the rendered form, exercised sidebar collapse, and captured [preflight.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/preflight.png) with tool output [preflight-output.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/preflight-output.json), around 09:12:35Z on 2026-10-20.

On continuation the previous browser context was no longer live; a new isolated context within this same QA runtime opened the same URL, waited for the setup heading, inspected the DOM, toggled Threads on/off without saving, and captured [resume-preflight.png](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/resume-preflight.png) / [resume-preflight.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/resume-preflight.json) around 09:29Z. Browser access works; no missing-tool assertion was marked PASS. Historical-version failure and mobile result header scrolling were additionally checked live during continuation.

## Controller-started servers and substitutions

| Environment | Frontend → API | Use |
|---|---|---|
| main | http://localhost:3010 → http://localhost:8010 | Default QA hook |
| unavailable | http://localhost:3011 → http://localhost:8011 | Empty PLAYWRIGHT_BROWSERS_PATH, substitutes NEG-002 restart |
| blocked | http://localhost:3012 → http://localhost:8012 | QA_THREADS_MODE=blocked, substitutes NEG-003 restart |
| fixture | http://localhost:3013 → http://localhost:8013 | ENABLE_FIXTURE_CHANNEL, internal-tools row, controller's 2,000-row corpus |

The worker did not start, stop or restart any server. These are the controller's replacement ports from the resumed brief, not the original 3000–3003 environments. Shared declared environment: STORAGE=local, EMBED_BACKEND=fake, REAL_CHANNELS_ENABLED=true, ENABLE_FIXTURE_CHANNEL=true, CORS for each frontend, DCX_TEST_ADAPTER_MODULE=channel_expansion_qa, QA-hook PYTHONPATH, no Voyage key. These launch settings are controller-supplied; observed availability and outputs are independently captured. Worker data directories use qa-data-r4main / qa-data-r4neg003 and the other source paths recorded in [log-manifest.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/log-manifest.json).

## Seeds, logs and evidence

[seed.js](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/seed.js) and [seed-output.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/seed-output.json) record fresh sessions through each backend's HTTP API. [sample-seed.js](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/sample-seed.js) and [sample-matching-seed-final.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/sample-matching-seed-final.json) record the fresh corpus-matching fixture retry. Keyword normalization and rejected exact-keyword patch are retained in [seed-exact-keywords.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/seed-exact-keywords.json).

Read-only copies of collection list.log, detail.log, report.json, worker_state.json and queue evidence are under logs/. [log-manifest.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/log-manifest.json) gives original and copied paths. [QA-NEG-003-log-inspection.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-NEG-003-log-inspection.json) records the no-login-request checks and sparse-log limitation. No claim is made about live external-site behavior or a complete backend wire capture.

[console-network.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/console-network.json) consolidates 1644 distinct captured events, including 68 console messages and no console errors/pageerrors. Warnings concern the development logo aspect ratio and CSS preload. Negative API 422s and the seed PATCH 400 are separately preserved in API outputs.

Screenshot files were saved with explicit absolute paths and existence/size checked. Relevant images were inspected, including settings 375px left/middle/right, result left/right plus resumed middle, completed collection/preprocessing, stopped Threads, historical v1, and both fixture outcomes. Offscreen details are established by complete DOM snapshots/API values, not inferred from cropped screenshots.

## Tool-created artifacts outside the authorized evidence folder

Playwright automatically created these files outside qa/; the worker did not manually direct evidence there. Copies and original paths are in [tool-artifacts.json](/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/tool-artifacts.json):

- `/Users/yunho/Documents/dcx_agent-channels-build/.playwright-mcp/console-2026-10-20T09-11-32-089Z.log` → `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/tool-artifacts/console-2026-10-20T09-11-32-089Z.log`
- `/Users/yunho/Documents/dcx_agent-channels-build/.playwright-mcp/console-2026-10-20T09-29-22-299Z.log` → `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/tool-artifacts/console-2026-10-20T09-29-22-299Z.log`
- `/Users/yunho/Documents/dcx_agent-channels-build/.playwright-mcp/page-2026-10-20T09-11-41-442Z.yml` → `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/tool-artifacts/page-2026-10-20T09-11-41-442Z.yml`

Chrome/Playwright also use their automatic isolated temporary profile/cache; this is tool-managed state, not a product edit. No manual temporary helper was written outside qa/.

## Outcome

15 PASS, 2 FAIL, 0 BLOCKED, 0 NOT_RUN. FAIL: QA-EDGE-002 missing historical result table; QA-E2E-003 literal keyword Given/row mismatch. QA-REG-001's initial failed seed and successful matching retry are both reported. No harness complete/decide, staging or commit action was run.
