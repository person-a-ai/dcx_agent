# QA-EDGE-003

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:53:00.392Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Family: Input and boundary
Given: R1 검토 화면
When: 엑셀 형식 텍스트를 붙여넣는다: 첫 줄 `﻿키워드\t축\t하위분류\t`, 둘째 줄 `"창문, 문틈"\t물리\t공간\t\t`
Then:
  - "1행 인식"이 보인다
  - 미리보기 키워드가 "창문,문틈", 분류 "물리 › 공간"이다
  - "키워드"라는 키워드 행이 없다

## Executed and observed

BOM header and trailing tabs recognized; only 창문,문틈, physical/space. No header keyword.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-003.json](QA-EDGE-003.json)
- [QA-EDGE-003.png](QA-EDGE-003.png)
