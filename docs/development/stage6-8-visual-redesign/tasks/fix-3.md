# RV10 fix report

Implemented separate `cardSelectedContext` state for card-view map clicks. Comparison columns use `highlighted ?? cardSelectedContext`, and the card map receives the persisted selection as `selectedId`. Changing the selected persona clears the card selection. Overview-map behavior remains unchanged.

Regression coverage exercises C1 click → C1 mouseleave → C2 hover → C2 mouseleave, verifying C1 remains selected, its column highlight returns, and its map label/marker remain visible. Switching personas clears the selection, including when returning to the original persona.

- RED — `npm --prefix frontend test -- PersonaScreen`: 57 passed, 1 failed. After C1 mouseleave, the column incorrectly highlighted C2 (`nth-child(3)` instead of `nth-child(2)`).
- GREEN — same command after the fix: 58 passed, including RV3/RV7/RV10.
- Full suite — `npm --prefix frontend test`: 73 files, 833 tests passed.
- Lint — `npm --prefix frontend run lint`: passed.
- TypeScript — `npx --prefix frontend tsc --noEmit -p frontend`: only the allowed TS2783 duplicate `max_per_keyword` errors in `frontend/src/lib/logic/crawlConfig.test.ts` at 13:63 and 25:98; exit 2.

Edits are limited to PersonaScreen.tsx, PersonaScreen.test.ts, and this report. No backend changes or git writes.
