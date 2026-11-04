# QA-REG-003

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:57:55.393Z
- Result: PASS

## Approved procedure and expected result

일괄 추가 후 R1 "저장" → 커버리지 계산 완료 → "다음 라운드 생성"이 성공하고 R3 키워드가 나온다

## Executed and observed

Bulk additions persisted; R1 Save completed and coverage displayed 100%; Next Round generated R3 with 59 keywords. API confirms R1 committed and R3 populated.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-REG-003.json](QA-REG-003.json)
- [QA-REG-003-coverage.png](QA-REG-003-coverage.png)
- [QA-REG-003.png](QA-REG-003.png)
- [generation-api.json](generation-api.json)
