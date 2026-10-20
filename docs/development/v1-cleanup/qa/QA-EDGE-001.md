# QA-EDGE-001

```json
{
  "id": "QA-EDGE-001",
  "url": "http://localhost:3411/pipeline/preprocess",
  "result": "PASS",
  "expected": "375×812: sidebar 72px, number only, complete banner, visible clickable action below message, no horizontal overflow.",
  "actual": "{\"viewport\":[375,812],\"scrollWidth\":375,\"sidebar\":{\"x\":0,\"y\":0,\"width\":72,\"height\":812,\"top\":0,\"right\":72,\"bottom\":812,\"left\":0},\"labels\":[{\"text\":\"시작\",\"display\":\"none\"},{\"text\":\"키워드\",\"display\":\"none\"},{\"text\":\"크롤링\",\"display\":\"none\"},{\"text\":\"전처리\",\"display\":\"none\"},{\"text\":\"라벨링\",\"display\":\"none\"},{\"text\":\"학습\",\"display\":\"none\"},{\"text\":\"클러스터링\",\"display\":\"none\"},{\"text\":\"근거 탐색\",\"display\":\"none\"},{\"text\":\"페르소나\",\"display\":\"none\"},{\"text\":\"인사이트\",\"display\":\"none\"}],\"banner\":{\"x\":88,\"y\":24,\"width\":271,\"height\":130,\"top\":24,\"right\":359,\"bottom\":154,\"left\":88},\"bannerText\":\"3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 페르소나 화면을 열 수 있습니다.전처리 화면으로\",\"button\":{\"x\":102,\"y\":106,\"width\":110.5390625,\"height\":36,\"top\":106,\"right\":212.5390625,\"bottom\":142,\"left\":102},\"bannerScrollWidth\":271,\"bannerClientWidth\":271}",
  "evidence": "docs/development/v1-cleanup/qa/QA-EDGE-001.md",
  "time": "2026-10-20T04:20:29.975Z",
  "steps": [
    "Set viewport 375×812",
    "Opened personas directly",
    "Measured visible DOM",
    "Saved mobile screenshot",
    "Clicked preprocessing action"
  ],
  "screenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-EDGE-001.png",
  "mobileScreenshot": "/Users/yunho/Documents/dcx_agent-v1-cleanup/docs/development/v1-cleanup/qa/QA-EDGE-001-mobile.png",
  "destination": "http://localhost:3411/pipeline/preprocess"
}
```

