# QA-REG-002

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T13:01:08.148Z
- Result: PASS

## Approved procedure and expected result

"추천 단어 불러오기" → "추천 단어 모두 추가하기"

## Executed and observed

Ten autocomplete suggestions loaded and all added; chips have 추천 badge; total 76→86.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-REG-002.json](QA-REG-002.json)
- [QA-REG-002-suggestions.png](QA-REG-002-suggestions.png)
- [QA-REG-002.png](QA-REG-002.png)
- [regression-final-api.json](regression-final-api.json)
