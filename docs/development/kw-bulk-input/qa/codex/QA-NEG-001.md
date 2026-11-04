# QA-NEG-001

- URL: http://localhost:3488/pipeline/keywords
- QA fixture SID: s1732f9db5edd4b919c40e5c4986375bc
- Time: 2026-10-28T12:56:05.975Z
- Result: PASS

## Approved procedure and expected result

Priority: P0
Type: Negative
Journey: J-3
Given: 백엔드를 `LLM_BACKEND_OVERRIDES={"kw_bulk_classify":"broken"}`로 띄운 R1 검토 화면
When: `불안감\n수면 방해`를 붙여넣고 "미리보기"
Then:
  - 경고 배너 "자동 분류에 실패했습니다"와 "자동 분류 다시 하기" 버튼이 보인다
  - 두 행 상태가 "분류 필요", 출처가 "분류 실패"이다
  - 추가 버튼이 "0개 추가하기"이고 비활성이다
  - "불안감" 분류를 "심리 › 감정"으로 고르면 버튼이 "1개 추가하기"로 활성화된다
  - "수면방해" 행 체크를 끄고 "자동 분류 다시 하기"를 누른 뒤에도 "불안감"의 분류가 "심리 › 감정"으로, "수면방해" 행이 "제외"로 남는다
  - 추가하면 "불안감"만 추가되고 "수면방해"는 어떤 그룹에도 없다

## Executed and observed

Broken classifier showed warning/retry; both rows 分류 필요 with 분류 실패, zero disabled; manually selected emotion and excluded second; retry retained edits; only 불안감 persisted.

The raw DOM/control capture records the actual rendered state. API and network artifacts supplement UI actions where the plan requires persisted data or request counts. Screenshots were visually inspected; the product scrolls within its main pane, so screenshots capture the pane's current position.

## Evidence

- [QA-NEG-001.json](QA-NEG-001.json)
- [QA-NEG-001-failure.png](QA-NEG-001-failure.png)
- [QA-NEG-001.png](QA-NEG-001.png)
