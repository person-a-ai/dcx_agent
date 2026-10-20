# QA-REG-003 — PASS

URL: http://localhost:3000/pipeline/start

Tested commit: c597b2a678231016e51b0d3644f3d6df921810c2; observed HEAD: c597b2a678231016e51b0d3644f3d6df921810c2.

## Approved scenario (unchanged)

```text
QA-REG-003
Priority: P1
Type: Regression
Given: 새 프로젝트를 0단계(입력)에서 만든다
When: 수집 채널 선택 칸을 연다
Then:
  - 기존 채널 선택지가 그대로 있다
  - 새 채널 4개가 선택지에 보이고, 하나를 골라 저장하면 GET /session/{sid}의 `projectContext.channels`에 그 값이 들어간다
```

## Executed steps

1. 새 프로젝트에서 제품명/한줄 정의/신규기획/리서치 질문 입력
2. Threads 선택 후 저장
3. GET session 및 저장된 프로젝트 재열람 확인

## Actual / verdict

0단계 기존/새 4채널 선택지 모두 존재. Threads 선택해 새 프로젝트 저장 POST201. GET session.projectContext.channels=[threads], 재열람 선택 상태 유지.

처음 프로젝트 성격 신규기획을 button으로 찾은 QA 도구 오류를 보존(QA-REG-003-data.json). 실제 DOM radio로 수정해 저장했다. 첫 저장 직후 스크린샷은 처리 중 화면이어서 저장 후 재열람 캡처를 추가했다.

## Timestamped DOM / API evidence

```json
{
  "time": "2026-10-20T07:07:02.176Z",
  "dom": "- group \"수집 채널\":\n  - button \"네이버 카페\"\n  - button \"네이버 블로그\"\n  - button \"유튜브\"\n  - button \"뽐뿌\"\n  - button \"클리앙\"\n  - button \"개발용 샘플\"\n  - button \"유튜브 브이로그\"\n  - button \"Threads\" [pressed]\n  - button \"지식iN\"\n  - button \"82쿡\"",
  "channels": [
    "threads"
  ]
}
```

## Evidence files

- [QA-REG-003-retry-data.json](QA-REG-003-retry-data.json)
- [QA-REG-003-saved-data.json](QA-REG-003-saved-data.json)

Screenshots were saved using explicit absolute paths and inspected for relevant states:

- [preflight.png](preflight.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/preflight.png`
- [QA-REG-003-saved-channels.png](QA-REG-003-saved-channels.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-REG-003-saved-channels.png`

Shared main browser console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Main console: no errors; logo aspect-ratio warning. Scenario-specific API responses and variant network records are in the JSON above or linked raw evidence. Screenshots supplement DOM/API evidence, not replace it.
