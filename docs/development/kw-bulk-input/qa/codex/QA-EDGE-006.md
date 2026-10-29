# QA-EDGE-006

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:54:10.470Z
- Result: PASS

## Approved procedure and expected result

Priority: P1
Family: Concurrency and repetition
Given: 미리보기 상태(추가 예정 2)
When: "2개 추가하기"를 빠르게 두 번 누른다
Then:
  - 결과 배너 "키워드 2개를 추가했습니다."가 한 번 보인다
  - `POST /keywords/{sid}/bulk` 요청이 1번이다(네트워크 기록)
  - 두 키워드가 각각 1개씩만 있다

## Executed and observed

Rapid double click sent exactly one bulk POST; one success banner and one stored record per keyword.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-006.json](QA-EDGE-006.json)
- [QA-EDGE-006.png](QA-EDGE-006.png)
- [doubleclick-network.json](doubleclick-network.json)
