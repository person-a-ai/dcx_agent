# QA-NEG-004

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:52:59.291Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Type: Negative
Journey: J-2
Given: R1 검토 화면, 이미지 파일을 `.csv`로 이름만 바꾼 `qa/broken.csv`, 빈 파일 `qa/empty.csv`
When: 각각 파일로 선택하고, 또 텍스트 영역을 공백·빈 줄만 남긴다
Then:
  - broken.csv: "파일을 읽지 못했습니다" 배너 또는 "키워드를 찾지 못했습니다" 중 하나가 보이고 미리보기 표가 생기지 않는다
  - empty.csv: "키워드를 찾지 못했습니다"가 보인다
  - 공백만 있을 때 "미리보기" 버튼이 비활성이다

## Executed and observed

PNG renamed .csv shows 파일을 읽지 못했습니다 without table; empty file shows 키워드를 찾지 못했습니다; whitespace preview disabled.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-NEG-004.json](QA-NEG-004.json)
- [QA-NEG-004-broken.png](QA-NEG-004-broken.png)
- [QA-NEG-004.png](QA-NEG-004.png)
