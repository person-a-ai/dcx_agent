# QA report — localhost (insight 8-E redesign)

- Date: 2026-10-16 · Branch: feature/stage8-insight-redesign · Revision: dff82a8
- Caller: development-harness browser-qa phase (report-only, /qa-only)
- Mode: Full · Surface: browser · Driver: Claude built-in browser pane (Aside not installed: NEEDS_ASIDE; gstack `$B` not used)
- Target: http://localhost:3412/pipeline/insights (Next.js dev) → API http://127.0.0.1:8412 (worktree backend)
- Data isolation: QA copy /private/tmp/dcx-qa-insight (session s8b25bf1f185143118303600ee0ec5293 "세라젬_261012_sk", v2). Production data not touched.
- Permitted writes: this report directory only. LOCAL target: rederive / chat / confirm mutations allowed on the QA copy.

## Charters

| ID | Contract (expected) | Risk | Entrypoint | Isolation | Exit condition |
|---|---|---|---|---|---|
| Q1 | Legacy insights (no new fields) render one at a time; title/pain_point fallback; one-line legacy notice + 자세히; flow cards without axis badge; no breakage | Old sessions unusable | /pipeline/insights, session v2 | QA copy | Screenshot + text show fallback and notice |
| Q2 | After 다시 도출 (confirm dialog), new revision shows quoted headline, 2 numbered statements, hashtags, contributing personas, flow cards with dim + axis badge | Rederive no-op / format missing | Legacy notice → 다시 도출 | QA copy (LLM call) | New revision rendered or failure shown |
| Q3 | 1280×800: top bar → header → radar|bars → flow bottom visible without scroll (≤4 flow cards) | First-screen promise broken | Same page at 1280×800 | — | Measured element bottoms ≤ 800 |
| Q4 | Radar mean dashed + per-context ODI bars + session mean label; labels not overlapping | Chart misread | Charts area | — | Screenshot + DOM check |
| Q5 | › click and → key on pager group move; → with focus on body does not move; first/last disabled | Keyboard trap / unintended paging | Top bar pager | — | Index changes observed |
| Q6 | Chip ① fills input; "Insight n에 대해 수정 요청" shown; send edits only current insight; stays on same insight; history count increments | Edit wrong insight | Chat band | QA copy (LLM call) | New revision, other items unchanged |
| Q7 | Confirm toggle persists after reload; concept area works | Confirmation lost | Top bar, concept section | QA copy | Toggle state after reload |
| Q8 | 768px: charts 2 columns, flow wraps; 375px: 1 column, ↓ arrows; hit areas ≥44px | Mobile breakage | Viewport emulation | — | Screenshots + computed sizes |
| Q9 | Revision preview: pager works, confirm/chat disabled, "현재 판으로" returns | Preview misleads | 판 목록 | — | Disabled states observed |

## Summary

- Health score: **86 (provisional)** — Console 100, Visual 89, Functional 100, UX 100, Content 97, Accessibility 100 (tested: weights 80/100). Links and Performance not tested.
- Severity counts: Critical 0 · High 0 · Medium 1 · Low 2. Framework: Next.js (dev). Screenshots: 6. Probe budget: 900 s. Total session elapsed: unmeasured.
- Console: one error `Failed to execute 'getComputedStyle' ... at <anonymous>` — stack is an anonymous injected script, not an app bundle; not counted as an app error (unconfirmed origin).

### Top 3 things to fix
1. ISSUE-001 (Medium): the rederive confirmation dialog renders at the top-left corner (left 0, top 0) without centering.
2. ISSUE-002 (Low): a wrapped flow-card row starts with a leading arrow.
3. ISSUE-003 (Low): chip ② uses a fixed particle "과" (e.g. "생활관리자-C4과 관리자-C4").

## Scenario results

| ID | Result | Evidence |
|---|---|---|
| Q1 | PASS — legacy revision shows one insight at a time (Insight 3 / 7), quoted title, pain_point statement, one-line legacy notice + 다시 도출 + 자세히, flow cards with dim and no axis badge | screenshots/q1-legacy-1280.jpg |
| Q2 | PASS — after 다시 도출 → 확인, worker ran with fresh=true, revision 1→2, legacy notice gone, quoted headline, 2 numbered statements, 4 hashtags, contributing personas, flow cards with dim + axis badge (Computed/Connected); confirmations cleared (확정하기) | screenshots/q2-rederived-1280.jpg; API worker status `done 2 True` |
| Q3 | PASS — 1280×800: legacy insight flow bottom 705px, rederived insight (4 flow cards) flow bottom 647px; charts height 240px | DOM measurement |
| Q4 | PASS — radar solid + dashed mean with legend "평균(전체 인사이트)"; per-context bars with labels `C3 / 중장년-C3`, mean "평균 0.2" in chart header; no overlapping text observed | screenshots/q2-rederived-1280.jpg |
| Q5 | PASS — → with focus on "다음 인사이트" moved 5→6; → with focus on body did not move; at 7/7 "다음" disabled and focus stayed in the group on "이전 인사이트" | JS probe result |
| Q6 | PASS — chip ① filled input and focused it; label "Insight 1에 대해 수정 요청"; send → revision 2→3, only Insight 1 changed (title, pain_point, statements, flow), other 5 items unchanged; stayed on Insight 1; reply "판 3에 반영했습니다."; history count 3 | API before/after diff |
| Q7 | PASS (partial) — confirm toggle off persisted to session.json and survived reload, then restored. Concept section rendered outside the panel under "컨셉" with "선택 컨셉 만들기"; concept creation (LLM) not run | JS probe; session.json |
| Q8 | PASS — 768px: charts 2 columns, flow 2 per row, no horizontal scroll; 375px: 1 column, ↓ arrows, no horizontal scroll; pager/confirm/chips/send/history/다시 도출 hit areas 44px high | screenshots/q8-768.jpg, q8-375.jpg |
| Q9 | PASS — 판 1 보기 shows the 7 legacy items with legacy notice, pager works (1→2 / 7), confirm/input/send disabled; 현재 판으로 returns to Insight 1 / 6 | screenshots/q9-revisions.jpg |

## Findings

### ISSUE-001 — Rederive confirmation dialog not centered (Medium, Visual)
- Observed: after clicking 다시 도출, the `<dialog>` opened at left 0 / top 0 of the viewport (width 498px), overlapping the sidebar logo; computed `position: fixed`, `margin: 0px`.
- Expected: a modal confirmation centered over the page (native dialog default) with visible separation from content.
- Evidence: screenshots/issue-001-dialog-top-left.jpg; computed style probe.
- Confirmation: observed once; computed style measured in the same open dialog.
- Hypothesis (untested): a global CSS reset sets `margin: 0` on `dialog`, removing the UA `margin: auto` centering.
- Proposed test: Value: protects=confirm dialog is centered; fails_when=dialog margin reset to 0 again; why_new=insightParts tests only check markup, not CSS; seam=none — assert the dialog class in insight.css sets centering (e.g. margin:auto or inset+translate).

### ISSUE-002 — Wrapped flow row begins with an arrow (Low, Visual)
- Observed: at 768px the third flow card starts a new row preceded by "→".
- Expected: no leading arrow at the start of a wrapped row.
- Evidence: screenshots/q8-768.jpg. Confirmation: observed once. (Already a deferred minor in orchestrator-checks.md T5.)

### ISSUE-003 — Chip ② particle is fixed to "과" (Low, Content)
- Observed: chip text "흐름에서 생활관리자-C4과 관리자-C4 순서를 바꿔줘" and earlier "시니어-C1과 보호자-C1".
- Expected: Korean particle chosen by the last character of the first label ("C4와", "C1과").
- Evidence: screenshots/q9-revisions.jpg. Confirmation: observed in two insights.

## Out of scope observed
- At 375px the app-wide sidebar stays expanded (~110px), narrowing content to ~219px. Pre-existing shell behavior, not changed by this branch.

## Not run / limits
- Concept creation (LLM) not exercised; concept outdated state not exercised.
- Counter (반례) cards not exercised: this session has 0 counter contexts (covered by unit tests).
- Checkpoint files per probe were not written; evidence is the scenario table, screenshots and API diffs retained here.
- Driver was the Claude built-in browser pane, not Aside/`$B`.

## Re-check after QA fix wave (revision 530b55c)

| ID | Result | Evidence |
|---|---|---|
| ISSUE-001 | FIXED — dialog at left 384 / top 325 with width 512 / height 150 in a 1280×800 viewport (centered), backdrop dims the page, focus starts on 취소, cancel closes and returns focus to 다시 도출 | screenshots/recheck-issue-001-dialog-centered.jpg |
| ISSUE-002 | FIXED — at 768px no flow item starts with an arrow (items at left 129/413/129); an arrow now follows the last card of a full row (parked Low in orchestrator-checks) | screenshots/recheck-issue-002-768.jpg |
| ISSUE-003 | FIXED — chips "…자녀-C2와 …", "…중장년-C4와 …" | JS probe |
| Revert | PASS — 판 1 "이 판으로 되돌리기" created revision 4 with the 7 legacy items | screenshots/recheck-issue-001-dialog-centered.jpg (판 목록) |

### ISSUE-004 — Long persona bar labels clipped inside the 240px chart (Low, Visual) — new
- Observed: on an insight whose personas share a last word (full names shown by the approved collision rule), the 2-line persona labels under the Opportunity Score bars are cut off at the bottom and the bars area shows a vertical scrollbar.
- Expected: labels readable within the chart area, or truncated without a scrollbar.
- Evidence: screenshots/issue-004-bar-labels-clipped.jpg. Confirmation: observed once (Insight 2 of revision 3). Full text remains available via title tooltip.

## Verdict
All 9 scenarios pass; the Medium issue is fixed. Remaining Low: ISSUE-004 (bar label clipping) and the parked trailing arrow. QA data copy now sits at revision 4 (reverted to legacy).

## Re-check after QA fix round 2 (revision 2012741)

| ID | Result | Evidence |
|---|---|---|
| ISSUE-004 | FIXED — Insight 2 (revision 5 = revision 3 content): bars scroller scrollHeight 202 = clientHeight 202, overflow-y hidden, both label lines visible (bottom 482 < figure bottom 500), ellipsis with title | screenshots/recheck-issue-004-arrow-trail.jpg |
| ARROW-TRAIL | FIXED — 5-card flow at 1280px: arrow display [block, block, block, none] after cards 1–4, none after the last | same screenshot |

## Final verdict
All 9 scenarios pass and all findings (ISSUE-001..004, ARROW-TRAIL) are fixed and re-checked in the browser. QA data copy ends at revision 5.
