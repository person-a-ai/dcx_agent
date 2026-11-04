# QA-REG-001

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T13:00:43.159Z
- Result: PASS

## Approved procedure and expected result

그룹의 "직접 추가하기"로 1개 추가, 중복 시 "이미 있는 키워드입니다…" 배너와 "중복 키워드 확인하기"

## Executed and observed

Single manual add 단건회귀확인 succeeded (75→76); repeating it showed 이미 있는 키워드입니다 and 중복 키워드 확인하기.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-REG-001.json](QA-REG-001.json)
- [QA-REG-001.png](QA-REG-001.png)
- [regression-final-api.json](regression-final-api.json)
