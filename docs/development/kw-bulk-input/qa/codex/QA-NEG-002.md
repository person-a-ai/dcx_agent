# QA-NEG-002

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:56:43.312Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Type: Negative / Permission
Journey: J-4
Given: QA 세션에 버전 v2를 만들어 활성화하고, v1을 읽기 전용으로 연다
When: 키워드 화면(v1)을 보고, API `POST /keywords/{sid}/bulk/preview?version=v1`, `POST /keywords/{sid}/bulk?version=v1`를 직접 호출한다
Then:
  - 카드에 "읽기 전용 버전에서는 키워드를 추가할 수 없습니다."만 있고 "일괄 추가하기" 버튼이 없다
  - 두 API 응답이 409이고 본문 `status`가 "error"이다
  - v1 `session.json`의 키워드 수가 호출 전과 같다

## Executed and observed

Opened v1 through sidebar; read-only notice and no bulk button. Preview and bulk both 409 status:error. GET keywords before/after identical.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-NEG-002.json](QA-NEG-002.json)
- [QA-NEG-002.png](QA-NEG-002.png)
- [readonly-api.json](readonly-api.json)
