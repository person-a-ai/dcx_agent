# QA-EDGE-001 — PASS

- URL: http://localhost:3411/pipeline/personas
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:52:06.797Z → 2026-10-20T07:52:07.180Z.

## Expected

375×812: 72px number-only sidebar; full unclipped banner; visible clickable action; scrollWidth <=375.

## Steps

1. Select QA 전처리 전 and resize browser viewport to 375×812.
2. Directly open personas.
3. Inspect screenshot and DOM rectangles; click 전처리 화면으로.

## Actual

Sidebar 72px, labels hidden, scrollWidth 375; banner and button fully visible; click reached preprocess.

- PASS — viewport
- PASS — 72px sidebar
- PASS — text labels hidden
- PASS — banner in viewport and visually unclipped
- PASS — button in viewport
- PASS — button click
- PASS — no horizontal overflow

## Evidence

- [insights-mobile.json](insights-mobile.json)
- [all-events.json](all-events.json)
- [QA-EDGE-001.png](QA-EDGE-001.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:52:06.939Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:52:06.953Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:06.975Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:06.978Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:52:06.978Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:06.979Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:06.980Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:06.980Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:06.984Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:07.002Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:07.009Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:07.011Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:52:07.077Z",
  "layout": {
    "width": 375,
    "height": 812,
    "scrollWidth": 375,
    "side": {
      "x": 0,
      "y": 0,
      "width": 72,
      "height": 812,
      "top": 0,
      "right": 72,
      "bottom": 812,
      "left": 0
    },
    "banner": {
      "x": 88,
      "y": 24,
      "width": 271,
      "height": 130,
      "top": 24,
      "right": 359,
      "bottom": 154,
      "left": 88
    },
    "button": {
      "x": 102,
      "y": 106,
      "width": 110.5390625,
      "height": 36,
      "top": 106,
      "right": 212.5390625,
      "bottom": 142,
      "left": 102
    },
    "labels": [
      {
        "text": "시작",
        "display": "none"
      },
      {
        "text": "키워드",
        "display": "none"
      },
      {
        "text": "크롤링",
        "display": "none"
      },
      {
        "text": "전처리",
        "display": "none"
      },
      {
        "text": "라벨링",
        "display": "none"
      },
      {
        "text": "학습",
        "display": "none"
      },
      {
        "text": "클러스터링",
        "display": "none"
      },
      {
        "text": "근거 탐색",
        "display": "none"
      },
      {
        "text": "페르소나",
        "display": "none"
      },
      {
        "text": "인사이트",
        "display": "none"
      }
    ]
  },
  "body": "3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 페르소나 화면을 열 수 있습니다.\n전처리 화면으로",
  "actionUrl": "http://localhost:3411/pipeline/preprocess"
}
```
