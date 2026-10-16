# Fix 2 — RV7, RV8, RV9

Implemented the three findings against `02-design.md` sections 3.3 and 6, decision 6A.

## RV7 — Independent selection and hover

- Added optional `selectedId` while preserving existing OpportunityMap props and callbacks.
- PersonaScreen passes persisted selection and hover separately. Both points receive labels; selection has a solid ring distinct from the dashed hover ring.
- Regression: select C1, hover C2 → both labels remain, C1 has the selection marker, and the detail panel stays on C1. Updated the existing initial-selection assertion to check `selectedId`.
- RED: `npm --prefix frontend test -- components PersonaScreen` — 1 failed, 465 passed; selectedId was undefined.
- GREEN: same command — 38 files, 466 tests passed.

## RV8 — Labels stay within vertical viewBox bounds

- Label placement prefers downward movement near the top and upward movement elsewhere, searches bounded collision-free alternatives, and clamps baselines to [12, 420] to account for text height.
- Regression: three coincident focused points at s=1 and s=0; absolute label coordinates remain within the viewBox and baselines are separated by at least 12px.
- RED: `npm --prefix frontend test -- components PersonaScreen` — 1 failed, 467 passed; top-edge label baseline was y=8.
- GREEN: same command — 38 files, 468 tests passed.

## RV9 — 44px touch targets

- Raised ContextTable card-button inline minHeight from 36 to 44.
- Added `.persona-map-legend .ds-chip{min-height:44px}` in persona.css and the matching legend class. Global ds.css is untouched.
- Regression asserts inline minHeight >=44, the scoped CSS rule, and the matching legend container.
- RED: `npm --prefix frontend test -- components PersonaScreen` — 1 failed, 468 passed; inline minHeight was 36.
- GREEN: same command — 38 files, 469 tests passed.

## Final verification

- `npm --prefix frontend test` — PASS: 73 files, 832 tests.
- `npm --prefix frontend run lint` — PASS.
- `npx --prefix frontend tsc --noEmit -p frontend` — only the allowed existing TS2783 duplicate `max_per_keyword` errors at `frontend/src/lib/logic/crawlConfig.test.ts:13:63` and `:25:98`.
- Changes are limited to the six permitted persona files and this report. Existing unrelated working-tree changes were left untouched. No backend, global design-system CSS, or git writes; existing design tokens retained.
