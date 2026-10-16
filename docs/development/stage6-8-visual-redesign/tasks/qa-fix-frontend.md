# Frontend QA fixes — 2026-10-16

Implemented F1, F2, F3, F4, F5, F7 from `qa-findings-1.md`, using the existing QA report and screenshot references.

| Item | Change | RED → GREEN evidence |
|---|---|---|
| F1 | Request cards/map/tree only when status is `done`. Unavailable results show “페르소나를 만들면 전체 맵과 Context를 확인할 수 있습니다.”; `not_ready` produces no error or retry control. Status polling continues. | Five non-done status cases and one publication-race case failed before the fix; all six pass. |
| F2 | Explicit column widths: ID 96, name 220, Persona 160, metrics 72 each, zone 100, pain 260, card 96px. Table minimum width 1180px with local horizontal scrolling; card action stays on one line. | Column-width/scroll regression failed before the fix; passes afterward. |
| F3 | At 1280px and above, card comparison grid reserves at least 420px for the map. Below that breakpoint it stacks. | Desktop grid regression failed before the fix; passes afterward. |
| F4 | Move all six zone names outside the SVG into a deterministic wrapping legend with 16px gaps. Names cannot overlap plotted points. Existing zone color tokens remain. | Six-name/outside-plot/determinism regression failed before the fix; passes afterward. |
| F5 | Show cluster label once when it equals the cluster ID. Distinct labels remain visible. | Duplicate-label regression failed before the fix; passes afterward. |
| F7 | Below 768px, visually hide the duplicate summary heading while retaining its accessible name. Pain Points indentation is 20px; text and markers use `--type-card`. | Mobile heading/indent/type regression failed before the fix; passes afterward. |

TDD command: `npm --prefix frontend test -- components PersonaScreen`.

- RED: 11 failed, 470 passed (38 files); all six items had failing coverage before implementation.
- GREEN: 481 passed (38 files).
- Full suite: `npm --prefix frontend test` — 844 passed (73 files).
- Lint: `npm --prefix frontend run lint` — passed.
- TypeScript: `npx --prefix frontend tsc --noEmit -p frontend` — only known TS2783 errors in `frontend/src/lib/logic/crawlConfig.test.ts`, lines 13 and 25 (`max_per_keyword` duplicated).

Updated prior assertions for the revised column layout, outside zone legend, and done-only result fetching. Added no hex colors; visual changes use existing tokens. Edited only permitted frontend files and this report; no backend edits or git writes.

Verification limits: browser screenshots were not regenerated; layout coverage checks source/CSS and rendered markup rather than browser geometry. `next build` was not run.
