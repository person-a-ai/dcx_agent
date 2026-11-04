# QA-EDGE-005

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:55:44.663Z
- Result: PASS

## Approved procedure and expected result

Priority: P2
Family: Navigation and lifecycle
Given: 모바일 375×812 뷰포트, QA-E2E-001과 같은 입력
When: 미리보기까지 진행한다
Then:
  - 표 머리글이 보이지 않고 행이 세로 블록으로 쌓인다
  - `document.documentElement.scrollWidth`가 `clientWidth`보다 크지 않다
  - "5개 추가하기" 버튼이 화면에 보이고 누를 수 있다

## Executed and observed

{"width":375,"scrollWidth":375,"head":[{"display":"none","visible":0}],"rows":[{"display":"block","rect":{"x":114,"y":361,"width":204,"height":173,"top":361,"right":318,"bottom":534,"left":114}},{"display":"block","rect":{"x":114,"y":534,"width":204,"height":173,"top":534,"right":318,"bottom":707,"left":114}}]}; 5개 추가하기 scrolls into view and passes click actionability.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-005.json](QA-EDGE-005.json)
- [QA-EDGE-005-viewport.png](QA-EDGE-005-viewport.png)
- [QA-EDGE-005.png](QA-EDGE-005.png)
