# QA-EDGE-003 — FAIL

URL: http://localhost:3000/pipeline/crawling

Tested commit: c597b2a678231016e51b0d3644f3d6df921810c2; observed HEAD: c597b2a678231016e51b0d3644f3d6df921810c2.

## Approved scenario (unchanged)

```text
QA-EDGE-003
Priority: P2
Type: Edge / Viewport
Given: 브라우저 폭 375px
When: 설정 화면과 결과 화면을 연다
Then:
  - 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤)
  - 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다
```

## Executed steps

1. 375×812 설정 화면에서 네 새 채널 행으로 스크롤 및 촬영
2. 문서·표·부모의 clientWidth/scrollWidth/overflow 측정
3. 결과 건너뜀 표 헤더 위치 측정
4. 가로 scrollLeft를 최대로 설정해 스크롤 가능 여부 확인

## Actual / verdict

375px 설정/결과에서 document.scrollWidth=375. 네 행과 건너뜀 표의 세 열은 보이나, 설정/건너뜀 표는 자체 가로 스크롤 없이 폭204px로 축소되고 Threads 및 한국어가 여러 줄로 쪼개짐. 계획의 표 가로 스크롤 요구 불충족.

좁은 표에서 내용이 사라졌다고 주장하지 않는다. 문서 넘침 없음과 모든 열 존재는 PASS지만, 가로 스크롤로 확인하도록 명시된 두 번째 Then의 방식은 구현되지 않았다. 더 느슨한 가독성 기준으로 대체하지 않았다.

## Timestamped DOM / API evidence

```json
{
  "time": "2026-10-20T07:00:59.693Z",
  "result": {
    "viewport": 375,
    "documentWidth": 375,
    "headers": [
      {
        "text": "채널",
        "left": 114,
        "right": 182
      },
      {
        "text": "사유",
        "left": 182,
        "right": 250
      },
      {
        "text": "건수",
        "left": 250,
        "right": 318
      }
    ],
    "ancestors": [
      {
        "tag": "TABLE",
        "clientWidth": 206,
        "scrollWidth": 204,
        "overflow": "hidden"
      },
      {
        "tag": "DIV",
        "clientWidth": 254,
        "scrollWidth": 254,
        "overflow": "visible"
      },
      {
        "tag": "DIV",
        "clientWidth": 256,
        "scrollWidth": 256,
        "overflow": "visible"
      }
    ]
  },
  "settings": [
    {
      "name": "유튜브 브이로그",
      "text": "유튜브 브이로그 새 채널\t\"키워드 브이로그\" 영상 검색 · 한국어 자막을 화제 단위로 나눠 문서화\t사용 가능\t\n유튜브 브이로그 사용하기",
      "bounds": {
        "x": 114,
        "y": 225.5,
        "width": 204,
        "height": 361
      },
      "width": {
        "viewport": 375,
        "documentWidth": 375
      }
    },
    {
      "name": "Threads",
      "text": "Threads 새 채널\t검색 화면(로그인 없음) · 글 본문 · 키워드당 약 20건\t사용 가능\t\nThreads 사용하기",
      "bounds": {
        "x": 114,
        "y": 511,
        "width": 204,
        "height": 301
      },
      "width": {
        "viewport": 375,
        "documentWidth": 375
      }
    },
    {
      "name": "지식iN",
      "text": "지식iN 새 채널\t질문 검색 · 질문 제목과 본문 (답변 제외)\t사용 가능\t\n지식iN 사용하기",
      "bounds": {
        "x": 114,
        "y": 285.5,
        "width": 204,
        "height": 241
      },
      "width": {
        "viewport": 375,
        "documentWidth": 375
      }
    },
    {
      "name": "82쿡",
      "text": "82쿡 새 채널\t자유게시판 검색 · 본문 · 댓글\t사용 가능\t\n82쿡 사용하기",
      "bounds": {
        "x": 114,
        "y": 526.5,
        "width": 204,
        "height": 161
      },
      "width": {
        "viewport": 375,
        "documentWidth": 375
      }
    }
  ]
}
```

## Evidence files

- [settings-results-retry.json](settings-results-retry.json)
- [mobile-detail-data.json](mobile-detail-data.json)

Screenshots were saved using explicit absolute paths and inspected for relevant states:

- [QA-EDGE-003-settings.png](QA-EDGE-003-settings.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings.png`
- [QA-EDGE-003-settings-scrolled.png](QA-EDGE-003-settings-scrolled.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-settings-scrolled.png`
- [mobile-setting-1.png](mobile-setting-1.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/mobile-setting-1.png`
- [mobile-setting-2.png](mobile-setting-2.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/mobile-setting-2.png`
- [mobile-setting-3.png](mobile-setting-3.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/mobile-setting-3.png`
- [mobile-setting-4.png](mobile-setting-4.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/mobile-setting-4.png`
- [QA-EDGE-003-result-skip.png](QA-EDGE-003-result-skip.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-skip.png`
- [QA-EDGE-003-result-scrolled.png](QA-EDGE-003-result-scrolled.png) — `/Users/yunho/Documents/dcx_agent-channels-build/docs/development/channel-expansion/qa/QA-EDGE-003-result-scrolled.png`

Shared main browser console/network: [console-main.log](console-main.log), [network-main.log](network-main.log). Main console: no errors; logo aspect-ratio warning. Scenario-specific API responses and variant network records are in the JSON above or linked raw evidence. Screenshots supplement DOM/API evidence, not replace it.
