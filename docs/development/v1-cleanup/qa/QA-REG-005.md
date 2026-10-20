# QA-REG-005

```json
{
  "id": "QA-REG-005",
  "url": "http://localhost:3411/pipeline/crawling",
  "result": "PASS",
  "expected": "Legacy crawling page preserves 구버전 세션은 0~2단계를 편집할 수 없습니다 banner.",
  "actual": "구버전 세션은 0~2단계를 편집할 수 없습니다. 3단계 이후 화면에서 결과를 확인하세요.\n전처리 화면으로",
  "evidence": "docs/development/v1-cleanup/qa/QA-REG-005.md",
  "time": "2026-10-20T04:24:03.765Z",
  "steps": [
    "Kept QA 옛 세션 selected",
    "Opened /pipeline/crawling directly",
    "Checked existing legacy editing banner"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-REG-005.png"
}
```

