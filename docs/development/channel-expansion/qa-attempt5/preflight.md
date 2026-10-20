# Independent browser preflight — PASS

Executor: Codex, fresh runtime thread `01a158f9-b73b-7e50-a138-7e141d487784`.
Tool: Playwright MCP, configured Chrome --isolated, headed; Chrome 155.0.8059.85. Fresh browser context created by first navigation.
HEAD: `6955ba0256d60043b1410871a3f56445e578c6b2`.
Before fingerprint: `81efe86f6f470305c619e5329ed332c63d05f044ee4f5ba70a9ddd86df1b7b84`.
Initial git tracked changes: none. Existing untracked: build.json, qa-attempt2/, qa-attempt3-orphan/, qa-attempt3-stopped/, qa-attempt4/, reviews/final-review-3.json, reviews/final-review-4.json.

Opened http://localhost:3010 → /pipeline/start, rendered project form. Clicked inspected “사이드바 접기”; sidebar collapsed. Initial readiness locator incorrectly expected “사이드바 펼치기” and timed out; subsequent live DOM showed actual button “사이드바 펴기” and collapsed navigation. This is an automation locator error preserved here, not a product failure. Screenshot saved at absolute path `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/preflight.png` on 2026-10-20T13:11:59Z. Initial navigation tool timestamp 11:02:58Z; clocks/timing preserved as returned.

Harness-browser-qa skill read first. Approved plan read in full. Product and Git read-only; only evidence written. Reused seed.js after reading it; all seeds newly created on supplied servers. No earlier verdicts inherited.

Controller-started environments substitute plan section 8 restarts (no servers started/stopped here):
- main 3010 → 8010, qa-data-r5main
- NEG-002 3011 → 8011, qa-data-r5neg002, empty PLAYWRIGHT_BROWSERS_PATH
- NEG-003 3012 → 8012, qa-data-r5neg003, QA_THREADS_MODE=blocked
- REG-001 3013 → 8013, qa-data-r5reg001 (verified before log collection), internal tools enabled, supplied aircon_qa.csv corpus
Base scratchpad: `/private/tmp/claude-501/-Users-yunho--claude-spares-spare-d69SsJ/9251127c-9663-4223-85bb-09f9c61d81cd/scratchpad`.
STORAGE=local, EMBED_BACKEND=fake, ENABLE_FIXTURE_CHANNEL=true, REAL_CHANNELS_ENABLED=true, CORS per frontend, DCX_TEST_ADAPTER_MODULE=channel_expansion_qa, PYTHONPATH QA hooks + backend, VOYAGE_API_KEY unset (controller declaration).

Tool-created artifacts outside assigned folder: `.playwright-mcp/page-2026-10-20T11-02-58-898Z.yml`, `.playwright-mcp/console-2026-10-20T11-02-43-413Z.log`. These are automatic MCP artifacts; direct screenshots and evidence use absolute paths in qa/. Prior 09:* files preexisted this session.

## Final integrity — BLOCKED / overall FAIL

Initial preflight remains PASS: browser/tool/server access worked. Final worktree HEAD changed to `ff4d4d163021e0c476897be0abecdb440f3996f1`, fingerprint `3e73f4f996f1e1ad1b2152feacc356506d51ba32d37cd722e73f060fd931c86f`. Git commit timestamp 2026-10-20T13:25:43Z. Product changes were external to this QA worker. Tracked unstaged/staged diffs are empty, but HEAD is different. [Integrity evidence](integrity-check.json), [commit log](integrity-git-log.txt), [source delta](integrity-source-drift.diff). All17 browser/API scenarios passed on the supplied environments. Controller frontend copies of the changed Progress.tsx match the requested6955ba0; this does not satisfy the worktree unchanged requirement. No harness completion/decide command was run.

Console inspection: no application error messages; repeated Next.js logo aspect-ratio warning and normal HMR/React development messages. Network has navigation-aborted integrations/logo requests; completed scenario requests and explicit negative API responses are preserved. No observed threads.com login URL requests.

Screenshots were opened with view_image for relevant settings, gate, progress/result, preprocessing, unavailable, blocked, empty, historical, boundary, regression and mobile states. Full-page screenshots cover the app viewport because content scrolls inside the layout; DOM/API logs support assertions outside individual image crops. Additional table/field captures are identified as supplemental. All explicit screenshot paths are inventoried with absolute paths and hashes in screenshot-manifest.json.
