# QA-EDGE-009

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:55:21.588Z
- Result: PASS

## Approved procedure and expected result

Priority: P2
Family: Navigation and lifecycle
Given: 백엔드 응답을 늦추기 위해 브라우저 개발 도구로 `/bulk/preview` 요청을 5초 지연(네트워크 조건 또는 요청 가로채기)
When: 리스트 A(`소음`)로 "미리보기" → 분류 중에 "닫기" → "일괄 추가하기" → 리스트 B(`환기`) 입력 상태로 둔다
Then:
  - 5초 뒤에도 입력 상태이고 텍스트 영역이 "환기"이다
  - 미리보기 표가 나타나지 않는다

## Executed and observed

Preview A delayed 5s; closed and reopened with 환기; after old response input remains 환기 and no table appears.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-009.json](QA-EDGE-009.json)
- [QA-EDGE-009.png](QA-EDGE-009.png)
