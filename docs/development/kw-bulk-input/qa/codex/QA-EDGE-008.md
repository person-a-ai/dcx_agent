# QA-EDGE-008

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:56:30.665Z
- Result: PASS

## Approved procedure and expected result

Priority: P2
Family: Input and boundary
Given: 사용자 정의 하위분류 "물리 › 설치환경"에 키워드가 하나 있는 세션
When: `창틀,물리,설치환경` 과 `벽지,심리,감각`을 붙여넣고 미리보기
Then:
  - "창틀" 분류가 "물리 › 설치환경", 출처 "입력값"이다
  - "벽지"는 출처가 "자동 제안"이다(축·하위분류 불일치 → 분류 없음으로 보고 자동 분류 대상)
  - 분류 선택 목록에 "물리 › 설치환경"이 있다

## Executed and observed

Created physical 설치환경 and manually added 창문. Preview resolves 창틀 to physical/custom:설치환경 with 입력값; mismatch 벽지 auto-suggested; custom option listed.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-EDGE-008.json](QA-EDGE-008.json)
- [QA-EDGE-008.png](QA-EDGE-008.png)
