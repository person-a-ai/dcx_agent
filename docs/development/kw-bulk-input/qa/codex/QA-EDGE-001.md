# QA-EDGE-001

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:53:00.085Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Family: Data volume
Given: R1 검토 화면
When: `단어001`~`단어520` 520줄을 붙여넣고 "미리보기"
Then:
  - 입력 상태에 "500행 인식"이 보인다
  - 미리보기에 정보 배너 "앞 500행만 불러왔습니다(나머지 20행 제외)"가 보인다
  - 표의 마지막 키워드가 "단어500"이다
  - 요약이 "추가 예정 10", "분류 필요 490"이다(가짜 LLM이 100개 묶음마다 앞 두 행만 분류 → 묶음 5개)

## Executed and observed

Input capped at 500 rows, banner excludes remaining 20, final row 단어500, 10 addable and 490 unclassified.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-001.json](QA-EDGE-001.json)
- [QA-EDGE-001.png](QA-EDGE-001.png)
