# QA-NEG-005

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:52:11.371Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Type: Negative
Journey: J-1
Given: QA-E2E-002로 추가가 끝난 세션
When: 같은 7행을 다시 붙여넣고 "미리보기", 이어서 "퇴근후휴식" 행 체크를 끈다
Then:
  - QA-E2E-002에서 추가한 4행이 모두 "이미 있음"이다
  - "퇴근후휴식"만 "추가 예정"이고 버튼이 "1개 추가하기"이다
  - 체크를 끈 뒤 버튼이 "0개 추가하기"이고 비활성이다

## Executed and observed

All four prior additions and original 저소음 show already existing; repeated 층간소음 is also already existing (6 existing rows total). Only 퇴근후휴식 was addable; unchecking it made 0개 추가하기 disabled.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-NEG-005.json](QA-NEG-005.json)
- [QA-NEG-005.png](QA-NEG-005.png)
