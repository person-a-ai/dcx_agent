# QA-REG-004

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:57:23.357Z
- Result: PASS

## Approved procedure and expected result

일괄 추가한 칩을 M 키 또는 드래그로 다른 그룹에 옮기기, 거절·복원

## Executed and observed

M opened move dialog; moved bulk keyword 층간소음 sense→time. Rejected with irrelevant tag; clicking rejected chip restored it. API snapshots confirm each transition.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-REG-004.json](QA-REG-004.json)
- [QA-REG-004.png](QA-REG-004.png)
- [move-reject-restore-api.json](move-reject-restore-api.json)
