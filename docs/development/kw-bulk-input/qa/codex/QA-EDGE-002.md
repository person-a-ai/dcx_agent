# QA-EDGE-002

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:53:00.243Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Family: Input and boundary
Given: R1 검토 화면
When: 101자짜리 한 줄과 `소음` 한 줄을 붙여넣는다
Then:
  - "100자를 넘는 1개는 제외했습니다"가 보인다
  - "1행 인식"이고 미리보기에 "소음" 한 행만 있다

## Executed and observed

101-character row excluded with 100자 warning; one recognized row 소음 remains (existing fixture keyword).

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-002.json](QA-EDGE-002.json)
- [QA-EDGE-002.png](QA-EDGE-002.png)
