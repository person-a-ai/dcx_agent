# QA-EDGE-010

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:55:11.752Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Family: Concurrency and repetition
Given: 미리보기 상태(추가 예정 2)
When: "2개 추가하기"를 누른 직후(요청 중) 화면 하단 버튼들을 본다
Then:
  - "다음 라운드 생성"·"생성하기" 버튼이 요청이 끝날 때까지 비활성이다
  - 그룹의 "직접 추가하기" 버튼이 요청이 끝날 때까지 비활성이다

## Executed and observed

Bulk POST held 4 seconds by route interceptor; all manual add, 생성하기 and 다음 라운드 생성 buttons disabled until response.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-010.json](QA-EDGE-010.json)
- [QA-EDGE-010.png](QA-EDGE-010.png)
