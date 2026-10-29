# QA-EDGE-007

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:58:15.870Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Family: State and session
Given: R1을 저장한 뒤 "다음 라운드 생성"으로 R3 생성이 진행 중이다(R2는 잠긴 라운드라 건너뜀)
When: 키워드 화면을 본다
Then:
  - "키워드 일괄 추가" 카드가 보이지 않는다
  - 생성이 끝나면 카드가 다시 보인다

## Executed and observed

After R1 save and Next Round, bulk card disappeared during R3 generation and returned when R3 completed; mutation timeline plus in-generation screenshot captured.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-007.json](QA-EDGE-007.json)
- [QA-EDGE-007-generating.png](QA-EDGE-007-generating.png)
- [QA-EDGE-007.png](QA-EDGE-007.png)
- [generation-observed-states.json](generation-observed-states.json)
