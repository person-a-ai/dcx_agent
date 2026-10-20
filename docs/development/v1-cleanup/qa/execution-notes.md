# Independent QA execution notes

- Runtime: `01a15786-12bc-7fa3-a3ca-65e3d7d2f1d0`; actual CODEX_SESSION_ID / CODEX_THREAD_ID. No implementation or review verdict was read or adopted.
- Operating contract: `/Users/yunho/.codex/skills/harness-browser-qa/SKILL.md`.
- Executed all 19 active IDs. QA-E2E-006 ran before completed-session checks. QA-EDGE-003 was the final scenario and created active v2 through the actual UI.
- Result: 14 PASS, 5 FAIL. Detailed assertions, actual DOM, timestamps, requests, responses and screenshots are in the per-ID evidence files.
- The completed fixture retains its displayed name `QA 전처리 실행`; it serves as the plan's logical `QA 전처리 완료` after preprocessing. No unsolicited rename was performed.
- QA-REG-001 is conservatively FAIL: both HTTP endpoints returned 200, and the pipeline panel displayed the no-model answer. The separate `/insight-chat` UI request could not be exercised because `/insights` redirects to the pipeline screen whose visible panel sends `/chat`. Direct API survival is recorded separately from UI integration.
- QA-EDGE-002: both post-completion assertions passed. Its given locked-running state failed: the four links unlocked before completion. The report preserves this distinction rather than claiming the completed/reload checks failed.
- Initial `/crawl/{sid}/status` calls on the seeded preprocessing fixture returned 404 `parent_collection_not_found`. The seeded collection manifest contains only `{"parent": null}`. Preprocessing still completed and reused successfully. This fixture observation is not counted as an additional product regression.
- Setup failures preserved here: tool_search was unavailable; actual Playwright schemas were discovered using ALL_TOOLS. The Playwright code VM does not expose `require`, dynamic imports, or `URL`, and global bindings do not persist. A wrong expand-button name (`펼치기` instead of observed `펴기`) and an initial wrong storage-key readiness predicate timed out; both were corrected using inspected DOM/storage. No product failures were inferred from those harness errors.
- Shell localhost requests were blocked. Backend HTTP assertions used Playwright's APIRequestContext; file assertions used read-only local data inspection.
- Browser used configured isolated Chrome/Chromium, version 155.0.8059.85. Headed/headless flags were not exposed, and sandbox process inspection was denied. The worker's page was closed; controller servers were never started or stopped.
- Playwright's automatic initial `.playwright-mcp/` output was moved intact to `qa/playwright-tool-artifacts/` after closing the page. All final generated artifacts reside under `qa/`. This transient initial output location is disclosed as a write-boundary deviation.
- No source/test changes, staging, commits, harness `complete`, or harness `decide`.
- Initial and final product fingerprint: `a89512faf2eacae1e240d660ab0707ad5043d4e09f028b5a79b7fc68da8044e8`.
- Final HEAD: `c15ea7fa22e3641078939a524f5a5581b2689127`. Final git status contains only the expected untracked build/review JSON plus this QA directory.

## Screenshot verification

All 34 explicit PNG files were verified as present with valid dimensions; see `screenshot-manifest.json`. Relevant rendered states were opened and visually inspected:

- preflight and selected-session start page
- all three new-session gate banners
- all three completed-session screens, including persona error text
- preprocessing completion and reuse
- all three legacy-session gate banners
- 375×812 mobile banner, full message, wrapped action and collapsed sidebar
- keyboard focus outline
- no-session selection banner
- pipeline chat fallback answer
- keyword screen
- legacy crawling banner
- v2 stale-result clustering screen with enabled sidebar

DOM and HTTP evidence, rather than screenshots alone, establish each functional assertion. Screenshot-only API scenario images are contextual; their response logs are the primary evidence.
