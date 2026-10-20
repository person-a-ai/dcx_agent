# QA-EDGE-004 — PASS

- URL: http://localhost:3411/pipeline/personas
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:52:24.269Z → 2026-10-20T07:52:28.323Z.

## Expected

Tab skips all four locked sidebar items; unlocked links show 2px focus outline.

## Steps

1. Restore desktop viewport with QA 전처리 전 selected.
2. Focus sidebar collapse control as a starting point.
3. Press Tab seven times and record active element and computed outline; capture third link focus.

## Actual

Six earlier links received 2px solid focus-visible outlines; next Tab skipped to version button.

- PASS — six links
- PASS — 2px visible outlines
- PASS — locked items skipped

## Evidence

- [keyboard-keywords.json](keyboard-keywords.json)
- [all-events.json](all-events.json)
- [QA-EDGE-004.png](QA-EDGE-004.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:52:26.314Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:52:26.621Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:26.748Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:26.749Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:26.786Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:52:26.983Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:26.984Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:26.985Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:27.120Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:27.121Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:27.124Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:27.144Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
```

## Captured state / API output

```json
[
  {
    "time": "2026-10-20T07:52:27.681Z",
    "tag": "A",
    "text": "1시작",
    "aria": "1. 시작",
    "href": "/pipeline/start",
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  },
  {
    "time": "2026-10-20T07:52:27.740Z",
    "tag": "A",
    "text": "2키워드",
    "aria": "2. 키워드",
    "href": "/pipeline/keywords",
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  },
  {
    "time": "2026-10-20T07:52:27.853Z",
    "tag": "A",
    "text": "3크롤링",
    "aria": "3. 크롤링",
    "href": "/pipeline/crawling",
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  },
  {
    "time": "2026-10-20T07:52:28.191Z",
    "tag": "A",
    "text": "4전처리",
    "aria": "4. 전처리",
    "href": "/pipeline/preprocess",
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  },
  {
    "time": "2026-10-20T07:52:28.241Z",
    "tag": "A",
    "text": "5라벨링",
    "aria": "5. 라벨링",
    "href": "/pipeline/labeling",
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  },
  {
    "time": "2026-10-20T07:52:28.285Z",
    "tag": "A",
    "text": "6학습",
    "aria": "6. 학습",
    "href": "/pipeline/training",
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  },
  {
    "time": "2026-10-20T07:52:28.323Z",
    "tag": "BUTTON",
    "text": "v1 · 활성 버전 목록 열기",
    "aria": "v1 · 활성 버전 목록 열기",
    "href": null,
    "disabled": null,
    "outlineWidth": "2px",
    "outlineStyle": "solid",
    "outlineColor": "rgb(10, 115, 181)",
    "focusVisible": true
  }
]
```
