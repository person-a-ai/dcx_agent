# Insight browser-QA fixes

Date: 2026-10-16. Scope: ISSUE-001–003 from `docs/development/stage8-insight-redesign/qa/run-20261016T132612Z/qa-report-localhost-2026-10-16.md` Findings; design reference: `docs/development/stage8-insight-redesign/02-design.md`.

All fixes were made in this worktree without commits, sub-agents, or a build.

## ISSUE-001 — Center rederive confirmation

- Files: `frontend/src/components/persona/insight.css`, `frontend/src/styles/tokens.css`, `frontend/src/components/persona/insightParts.test.ts`.
- `InsightHeader.tsx` already assigns `insight-confirm` to its dialog; the new test verifies that connection, so no markup change was needed.
- RED: added `QA ISSUE-001 centers the rederive dialog despite the global margin reset`; missing `margin: auto` failed. Command: `npm --prefix frontend test -- src/components/persona/insightParts.test.ts` → 1 failed, 18 passed (19 total).
- Fix: explicit auto margins and zero inset, responsive maximum width and padding using spacing tokens, existing paper/line/overlay radius/shadow tokens, and translucent backdrop. Since tokens.css had no spacing tokens, added `--space-4` and `--space-6`; the backdrop color is defined there as `--overlay-backdrop`. No hex colors were added.
- GREEN: same command → 19 passed, 0 failed (1 file).

## ISSUE-002 — Keep arrows with preceding flow cards

- Files: `frontend/src/components/persona/InsightFlow.tsx`, `frontend/src/components/persona/insight.css`, `frontend/src/components/persona/insightCharts.test.ts`.
- RED: added four structure cases (0, 1, 2, 4 cards) checking the named ordered list, max(0,n−1) arrow containers, card first and trailing arrow in each non-final list item, plus mobile arrow CSS. Same command before implementation: `npm --prefix frontend test -- src/components/persona/insightCharts.test.ts` → 3 failed, 18 passed (21 total). The old first child was the leading arrow/false instead of the card.
- Fix: moved each arrow after its card except the last, within the same non-wrapping flex list item, and prevented arrow shrinking. Existing responsive row wrapping and ↓ display at ≤767px remain.
- GREEN: same command → 21 passed, 0 failed (1 file).

## ISSUE-003 — Select 과/와 from the first label

- Files: `frontend/src/components/persona/insightView.ts`, `frontend/src/components/persona/insightView.test.ts`.
- RED: added 17 chip-output cases covering 시니어-C1과, 생활관리자-C4와, 중장년-C3과, 베개와, 건강과, all ten trailing digits, Latin and punctuation endings. Command: `npm --prefix frontend test -- src/components/persona/insightView.test.ts` → 8 failed, 21 passed (29 total); the fixed 과 failed the 와 cases.
- Fix: select the particle using the final Hangul syllable's jongseong, the specified digit readings, or 와 for other endings.
- GREEN: same command → 29 passed, 0 failed (1 file).

## Final verification

- `npm --prefix frontend test` → 76 files passed, 939 tests passed, 0 failures. Includes 22 added regression cases.
- `npm --prefix frontend run lint` → exit 0, no warnings or errors.
- `git diff --check` → exit 0.
- Build intentionally not run. Browser QA was not rerun; visual fixes are verified through the requested CSS and React structure regression tests. Vitest printed the existing Node DEP0205 deprecation warning; it did not affect results.

## Fix round 1

- Coordinator ruling: no new global tokens. This section supersedes the ISSUE-001 spacing/backdrop token approach above.
- Files: `frontend/src/styles/tokens.css`, `frontend/src/components/persona/insight.css`, `frontend/src/components/persona/insightParts.test.ts`.
- Restored `tokens.css` exactly from `906e5de^`; `git diff 906e5de^ -- frontend/src/styles/tokens.css` produced no differences.
- Dialog now uses `padding: 24px` and `max-width: min(32rem, calc(100% - 32px))`; backdrop uses `rgba(28,30,34,.4)` directly. Auto margins, zero inset, paper background, line border, overlay radius and overlay shadow remain.
- Added a regression test forbidding definitions of `--space-4`, `--space-6`, and `--overlay-backdrop`, forbidding their use in insight.css, and checking the approved direct dialog values. No existing test referenced these tokens.
- RED: `npm --prefix frontend test -- src/components/persona/insightParts.test.ts` → 1 failed, 19 passed (20 total), because the forbidden tokens were still defined.
- GREEN: `npm --prefix frontend test` → 76 files passed, 940 tests passed, 0 failures, including all 20 insightParts tests.
- `npm --prefix frontend run lint` → exit 0, no warnings or errors. `git diff --check` → exit 0.
- No commit, build, or browser QA run. Existing Node DEP0205 warning appeared during Vitest and did not affect results.

## Fix round 2

- Scope: ISSUE-004 and ARROW-TRAIL from the browser re-check. Files: `frontend/src/components/persona/insight.css`, `frontend/src/components/persona/insightCharts.test.ts`. Component markup and existing structure tests remain unchanged.
- RED: added `QA ISSUE-004 reserves label space inside the fixed chart height` and `QA ARROW-TRAIL hides arrows at full row ends for each desktop breakpoint`. `npm --prefix frontend test -- src/components/persona/insightCharts.test.ts` → 2 failed, 21 passed (23 total). Failures confirmed missing vertical-overflow suppression and row-end arrow rules before implementation.
- ISSUE-004 fix: the scroller retains horizontal overflow and its existing tabIndex/role/aria-label; vertical overflow is hidden and min-height is zero so it can shrink below its contents. Its grid fills the available height. Each column reserves a fixed 78px label band (6px padding + 18px short ID + 36px two-line persona label + 18px missing-value text). Bar slots and the mean-line plot share the remaining height; the header cannot shrink. The existing two-line clamp, title tooltip, and 240px figure height remain.
- ARROW-TRAIL fix: hide every fourth item's trailing arrow at ≥1280px and every second item's trailing arrow at 768–1279px. Rules are scoped to those breakpoints, preserving mobile down arrows. The n−1 arrow markup is unchanged.
- GREEN: `npm --prefix frontend test -- src/components/persona/insightCharts.test.ts` → 23 passed, 0 failed (1 file).
- Final: `npm --prefix frontend test` → 76 files passed, 942 tests passed, 0 failures. `npm --prefix frontend run lint` → exit 0, no warnings or errors. `git diff --check` → exit 0.
- `git diff HEAD -- frontend/src/styles/tokens.css` produced no differences; no new tokens were added.
- No commit, build, sub-agents, or browser QA run. Visual results still need browser re-check; CSS regression and existing structure tests passed. Existing Node DEP0205 warning during Vitest did not affect results.
