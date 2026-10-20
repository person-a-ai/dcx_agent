# Saved screenshot inspection

All 25 original PNG screenshots were opened using view_image and inspected by this independent QA worker. PNG signatures, nonempty files and paths were also verified; hashes are in [screenshots.json](screenshots.json).

- Preflight: rendered project list and form, expanded sidebar.
- Prep: running indicator with locked later stages; done result with six documents; reuse result after reload.
- Gates: required desktop messages and buttons visible for clustering, personas and insights; legacy banners match all three routes; no-session prompt and old crawling restriction visible.
- Mobile: 375×812 screenshot shows 72px number-only sidebar, whole wrapped message and full action button; no horizontal clipping. DOM scrollWidth is 375.
- Keyboard: visible blue focus ring around the crawling link, corroborated by six 2px computed outlines.
- Completed pages: clustering run button, persona map/error state and insight empty state rendered. Persona's unconfirmed-layer error is the planned allowed 409 condition.
- Chat: panel shows the sent message and actual no-model fallback answer.
- Version restart: v2 shows stale-results notice plus required prep gate; v1 clustering shows read-only stored-results view, and v1 personas shows the read-only persona screen with no prep gate. The sidebar is open in both v1 screenshots.
- Keyword screen: R1 empty keyword state is rendered. A Next development compilation indicator is visible; this does not replace the captured console/network assertions.

No image was fabricated or altered. Functional verdicts also use DOM attributes, navigation outcomes, complete console/network capture and read-only API/filesystem records.
