Fixed OpportunityMap labels clipped at the SVG’s right edge.

- Estimate label width at 6.5px per character. Labels that would exceed x=596 use `text-anchor="end"` and sit 12px left of the point; horizontal positions are clamped to a 4px viewBox inset.
- Left-edge labels retain the start anchor. Placement is deterministic; RV8 vertical collision and bounds logic is unchanged.
- Added regression coverage for focused `CL1-P2-C1` at importance 1 and 0, checking horizontal bounds, anchors, and repeatable placement.

Validation:

- RED — `npm --prefix frontend test -- components`: 1 failed, 482 passed. The new importance=1 case failed with `expected 610.5 to be less than or equal to 596`; importance=0 passed.
- GREEN — `npm --prefix frontend test -- components`: 38 files, 483 tests passed, including RV8.
- Full suite — `npm --prefix frontend test`: 73 files, 846 tests passed.
- Lint — `npm --prefix frontend run lint`: passed.
- TypeScript — `npx --prefix frontend tsc --noEmit -p frontend --incremental false`: only the known TS2783 duplicate `max_per_keyword` errors in `frontend/src/lib/logic/crawlConfig.test.ts` at 13:63 and 25:98. Incremental output disabled to avoid writing a build cache outside the allowed files.

Only the three authorized files were edited. No backend changes or git writes.
