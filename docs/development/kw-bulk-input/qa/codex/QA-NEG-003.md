# QA-NEG-003

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:56:19.073Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Type: Negative / Failure injection
Journey: J-1
Given: R1 검토 화면에서 입력 상태에 3행을 붙여넣은 뒤 백엔드 프로세스를 멈춘다
When: "미리보기"를 누른다
Then:
  - 입력 상태로 돌아와 위험 배너가 보인다
  - 텍스트 영역에 붙여넣은 3행이 그대로 있다
  - 백엔드를 다시 띄우고 "미리보기"를 누르면 미리보기 표가 나온다

## Executed and observed

Stopped API; preview returned to input with 요청에 실패했습니다 and all three lines retained. Restarted normal API; retry produced 3-row preview.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-NEG-003.json](QA-NEG-003.json)
- [QA-NEG-003-outage.png](QA-NEG-003-outage.png)
- [QA-NEG-003.png](QA-NEG-003.png)
