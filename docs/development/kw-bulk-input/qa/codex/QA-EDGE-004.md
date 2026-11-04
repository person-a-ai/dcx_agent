# QA-EDGE-004

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:53:27.863Z
- Result: PASS

## Approved procedure and expected result

Priority: P0
Family: Concurrency and repetition
Given: 같은 세션을 탭 A·B로 연다. 탭 A에서 `곰팡이 냄새`를 붙여넣고 미리보기(“추가 예정”)
When: 탭 B에서 "직접 추가하기"로 "곰팡이냄새"(물리 › 감각)를 추가한 뒤, 탭 A에서 "1개 추가하기"
Then:
  - 탭 A 결과 배너가 "키워드 0개를 추가했습니다. 1개는 건너뛰었습니다."이다
  - 건너뛴 행 표에 "곰팡이냄새"와 "이미 있음"이 있다
  - `GET /keywords/{sid}`에서 "곰팡이냄새"가 정확히 1개다

## Executed and observed

Tab B manually added 곰팡이냄새 physical/sense after A preview; A reports 0 added, 1 skipped, already exists; GET count=1.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-004.json](QA-EDGE-004.json)
- [QA-EDGE-004.png](QA-EDGE-004.png)
- [race-api.json](race-api.json)
