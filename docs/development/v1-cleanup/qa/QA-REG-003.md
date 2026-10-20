# QA-REG-003

```json
{
  "id": "QA-REG-003",
  "url": "http://localhost:3411/pipeline/preprocess",
  "result": "PASS",
  "expected": "Every derived docs JSONL row has desc/cafe/link and desc <=4000 chars.",
  "actual": "Read all six rows in part-00001.jsonl: required keys present, each desc length 44.",
  "evidence": "docs/development/v1-cleanup/qa/QA-REG-003.md",
  "time": "2026-10-20T04:21:42.908Z",
  "steps": [
    "Read all derived docs JSONL rows after first successful UI preprocessing",
    "Validated keys and desc lengths"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-REG-003.png",
  "fileEvidence": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/prep-files.json"
}
```

