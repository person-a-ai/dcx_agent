# QA-EDGE-004

```json
{
  "id": "QA-EDGE-004",
  "url": "http://localhost:3411/pipeline/personas",
  "result": "PASS",
  "expected": "Tab visits six unlocked sidebar items with visible 2px outline, skips four locked items.",
  "actual": "[{\"text\":\"1시작\",\"label\":\"1. 시작\",\"href\":\"/pipeline/start\",\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true},{\"text\":\"2키워드\",\"label\":\"2. 키워드\",\"href\":\"/pipeline/keywords\",\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true},{\"text\":\"3크롤링\",\"label\":\"3. 크롤링\",\"href\":\"/pipeline/crawling\",\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true},{\"text\":\"4전처리\",\"label\":\"4. 전처리\",\"href\":\"/pipeline/preprocess\",\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true},{\"text\":\"5라벨링\",\"label\":\"5. 라벨링\",\"href\":\"/pipeline/labeling\",\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true},{\"text\":\"6학습\",\"label\":\"6. 학습\",\"href\":\"/pipeline/training\",\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true},{\"text\":\"v1 · 활성 버전 목록 열기\",\"label\":\"v1 · 활성 버전 목록 열기\",\"href\":null,\"disabled\":null,\"outlineWidth\":\"2px\",\"outlineStyle\":\"solid\",\"outlineColor\":\"rgb(10, 115, 181)\",\"focusVisible\":true}]",
  "evidence": "docs/development/v1-cleanup/qa/QA-EDGE-004.md",
  "time": "2026-10-20T04:20:41.339Z",
  "steps": [
    "Focused sidebar toggle as starting point",
    "Pressed Tab seven times",
    "Recorded active element and computed focus outline each time"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-EDGE-004.png",
  "focusScreenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-EDGE-004-focus.png"
}
```

