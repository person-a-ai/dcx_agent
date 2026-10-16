# Label collision fix

Fixed the mixed-anchor label collision in `OpportunityMap.tsx` identified in review of commit `978cbbc`.

Label anchors and horizontal text intervals are now computed before vertical placement, using the existing 6.5px-per-character estimate, flip rule, and 4px viewBox inset. Candidates collide only when their horizontal intervals overlap and their baselines are less than 12px apart. Rendering uses the stored anchor and coordinates. Context ID ordering, vertical candidate order, fallback, and [12,420] bounds remain unchanged.

Added a regression test with two focused nine-character labels at point x=450 and x=540 with equal y. It checks mixed anchors, rendered intervals, and deterministic placement across repeated renders and reversed input order.

Verification:

- RED — `npm --prefix frontend test -- components`: 1 failed, 483 passed. After correcting the fixture's inverse log calculation, the regression failed on overlapping rendered intervals as expected; existing RV8 and edge tests passed.
- GREEN — `npm --prefix frontend test -- components`: 484 tests passed across 38 files, including the regression, existing RV8 bounds, and horizontal edge tests.
- `npm --prefix frontend test`: 847 tests passed across 73 files.
- `npm --prefix frontend run lint`: passed.
- `npx --prefix frontend tsc --noEmit -p frontend --incremental false`: exited 2 with only the known TS2783 duplicate `max_per_keyword` errors in `frontend/src/lib/logic/crawlConfig.test.ts` at (13,63) and (25,98).
- `git diff --check`: passed.

Only the three authorized files were changed. No backend changes or git writes were performed.
