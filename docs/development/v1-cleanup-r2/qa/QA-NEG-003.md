# QA-NEG-003 — PASS

- URL: http://localhost:3411/pipeline/clustering
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:53:27.116Z → 2026-10-20T07:53:28.318Z.

## Expected

Empty browser storage shows project-selection banner; action reaches start; zero console errors.

## Steps

1. Clear localStorage, sessionStorage and context cookies.
2. Directly navigate to clustering.
3. Check banner/error trace and click 프로젝트 선택하기.

## Actual

Storage empty, exact banner displayed, action reached start; console errors 0.

- PASS — empty storage
- PASS — exact banner
- PASS — action
- PASS — zero errors

## Evidence

- [negative.json](negative.json)
- [all-events.json](all-events.json)
- [QA-NEG-003.png](QA-NEG-003.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:53:27.579Z HTTP 200 http://localhost:8411/integrations
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:53:28.203Z",
  "storage": {
    "local": {},
    "session": {}
  },
  "url": "http://localhost:3411/pipeline/clustering",
  "body": "프로젝트를 먼저 선택하세요.\n프로젝트 선택하기",
  "actionUrl": "http://localhost:3411/pipeline/start"
}
```
