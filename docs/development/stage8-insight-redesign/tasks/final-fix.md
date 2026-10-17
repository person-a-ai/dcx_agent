# Insight 8-E final review fixes

All nine findings are addressed. Changes remain in the working tree; no commit or delegation was performed.

## Per-item changes and RED → GREEN evidence

1. **Fresh retry preserves intent.** Files: `backend/app/persona/insight_pipeline.py`, `backend/app/routers/stage8.py`, `frontend/src/lib/types.ts`, `frontend/src/components/persona/InsightScreen.tsx`; tests: `backend/tests/persona/test_review_fixes.py`, `frontend/src/components/persona/InsightScreen.qa.test.ts`. Worker session state records `fresh` at launch, the API returns it (including durable supervisor args), and retry resends it. RED: `test_fresh_recorded_returned_and_retry_derives` failed with missing `fresh`; `retry resends fresh worker flag` failed on the request payload. GREEN: both pass; retry produces revision 2 despite an existing revision. Existing exact-response assertions in `test_api.py` and `test_final_fixes.py` now include the added default `fresh=False` field.

2. **Concept target follows paging.** Files: `InsightScreen.tsx`, `InsightScreen.qa.test.ts`. A usable concept follows the new selected ID; missing/outdated concepts fall back to the selected insight, including its revision/revert source. The list target remains unchanged. RED: replaced the old target-retention test with `concept paging follows selection or falls back (outdated %s)`; the old implementation retained `concept:I2`. GREEN: usable, outdated, and missing cases pass, including focus ID, stored target, and revision source. Existing list-target test also passes.

3. **Fresh confirmation clearing survives later interruption/error and reads under lock.** Files: `insight_pipeline.py`, `test_review_fixes.py`. Clearing runs in a `finally` immediately around derive when a newer revision exists, before the next pulse. The revision check and session read/write occur under `sessions.locked`; unrelated remembered IDs are retained. RED: `test_fresh_confirmation_clear_survives_post_publish_stop_and_reads_locked[True]` retained `I1`, and `[False]` detected an unlocked session read. GREEN: stop, normal completion, and an exception after revision publication all pass. The first post-publication session read is explicitly checked to occur under the session lock, preventing the stale read used by the previous implementation.

4. **Keyboard-reachable horizontal bars.** Files: `OpportunityBars.tsx`, `insightCharts.test.ts`. The scroll wrapper has `tabIndex={0}`, `role="group"`, and an accessible name; the inner image retains the value summary. RED: `bars scroll region is keyboard reachable and named` failed on missing attributes. GREEN: passes; existing formatted summary test also passes.

5. **Bounded bar labels.** Files: `OpportunityBars.tsx`, `insight.css`, `insightCharts.test.ts`. Short labels use single-line ellipsis; persona labels use the existing two-line clamp. Both expose complete text through `title`. Removed the generic span display rule that would otherwise override the clamp. RED: `bar labels clamp with full title` failed on missing classes/title. GREEN: passes, along with existing CSS two-line-clamp checks and fixed 240px chart checks.

6. **Nullable radar means.** File: `frontend/src/lib/types.ts`. `InsightSummary.radar_mean` now permits `number | null` for each axis. This is a type-contract correction rather than a runtime behavior change, so no artificial RED runtime test was added. GREEN: production TypeScript compilation passes; existing `partial radar mean omits polygon and announces the missing axis` passes. Radar already handles nullable axes and required no consumer change.

7. **Edit prompt matches validation.** Files: `backend/app/persona/prompts/edit.v2.md`, `test_review_fixes.py`. Added flow text length 1–80 and unique hashtag rules; `edit.v1.md` is unchanged. RED: `test_edit_v2_prompt_declares_flow_length_and_unique_hashtags` was run against the original v2 prompt and failed. GREEN: passes against the updated prompt.

8. **Provisional badges restored.** Files: `Radar.tsx`, `OpportunityBars.tsx`, `insightCharts.test.ts`. Both captions render the existing `ProvisionalBadge` with “잠정”. RED: `charts show provisional badges` failed on the missing badge. GREEN: passes for both charts; updated the existing mean-caption assertion to accommodate the badge.

9. **Chat resets on target change.** Files: `InsightChatBar.tsx`, `insightParts.test.ts`. `ChatPanel` now receives `key={target}`. RED: `chat transcript is keyed by target` initially failed on the missing key. GREEN: final test inspects the actual React element key for insight, concept, and list targets rather than testing source text.

## Final commands and results

- `backend/.venv/bin/python -m pytest backend/tests/persona -q`: 401 passed, 2 warnings.
- `npm --prefix frontend test`: 76 files, 917 tests passed.
- `npm --prefix frontend run lint`: passed, no lint diagnostics.
- `npm --prefix frontend run build`: Turbopack stayed at “Creating an optimized production build” without further output; interrupted the stalled command.
- `npm --prefix frontend run build -- --webpack`: passed, including TypeScript and static generation of 16 pages.
- `git diff --check`: passed.

Initial targeted RED runs: backend 3 failing cases; frontend 7 failing cases (50 passing). The prompt RED was checked separately against its original content. Full-suite intermediate failures were six exact worker-response expectations, all updated for the explicitly requested API field.

## Concerns and verification limits

- Coordinator should rerun the default Turbopack build outside this sandbox. Webpack production build passed.
- Existing warnings: Pydantic class-based configuration deprecation, joblib physical-core detection fallback, and Node `module.register()` deprecation.
- Label layout is verified through rendered attributes/classes and CSS assertions; no browser screenshot QA was performed.
- Confirmation clearing handles cooperative stops and exceptions after publication; this does not claim transactional durability across an abrupt process/OS kill between separate JSON file writes.
