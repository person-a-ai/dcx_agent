# Visual inspection

The QA executor opened saved PNGs with the local view_image tool. Inspected states include preflight; new channels; invalid range; boundary values; 5/2/30 values (e2e002-values-visible.png); expanded gate; running/completed progress; skip reasons; preprocessing choices and completion; unavailable Threads; paused and partially completed Threads; empty gate; new project channels; past version; fixture result and preprocess action.

Mobile screenshots were inspected at 375px: all four new channel names fit vertically after scrolling (edge003-mobile-four-rows.png); local horizontal scrolling exposes 채널, 사유, 건수 in three separate captures. Settings and result desktop screenshots at 1100, 1200, 1300px were inspected. The document width matched each viewport; table overflow remained local. Narrow labels wrap; no required column becomes unreachable.

Some early fullPage screenshots retain the viewport of the app's inner scrolling container. Relevant controls were subsequently scrolled into view and supplemental screenshots saved. Functional conclusions also use live DOM and API evidence, not screenshots alone.

All PNG paths and checksums are verified in screenshot-manifest.json. Failed locator attempts and the temporary native-disabled-only QA check are preserved; edge002-verified.json verifies aria-disabled with Playwright isDisabled. No product code was changed to resolve these QA script errors.
