# QA-REG-004 — PASS

- URL: http://localhost:3411/pipeline/keywords
- Tested HEAD: `5de8f30bbb05986afa4b5ccf579d3d0442302857`
- Executor: codex / browser-qa; thread `01a15844-a762-7910-97e2-9d33167a6188`.
- Recorded UTC interval: 2026-10-20T07:52:28.374Z → 2026-10-20T07:52:46.622Z.

## Expected

Keyword screen opens with zero console errors.

## Steps

1. Select QA 전처리 전.
2. Directly open keywords and await rendered UI/network readiness.
3. Capture screen and all console/pageerror events.

## Actual

R1 keyword screen rendered; console errors and pageerror both 0.

- PASS — keyword screen
- PASS — zero console errors

## Evidence

- [keyboard-keywords.json](keyboard-keywords.json)
- [all-events.json](all-events.json)
- [QA-REG-004.png](QA-REG-004.png) — absolute-path capture, existence verified, visually inspected.

## Console / network / API

Page errors: 0; console error messages: 0.

Complete timestamped request/response bodies and console locations are in the linked JSON. Relevant observed HTTP/error entries:

```text
2026-10-20T07:52:37.158Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:37.183Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:37.214Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:43.242Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:52:43.310Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:43.321Z HTTP 200 http://localhost:8411/integrations
2026-10-20T07:52:43.324Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:43.325Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:43.843Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f
2026-10-20T07:52:43.843Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:43.845Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:43.852Z HTTP 200 http://localhost:8411/sessions
2026-10-20T07:52:43.939Z HTTP 200 http://localhost:8411/known/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:43.940Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:43.940Z HTTP 200 http://localhost:8411/keywords/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:43.940Z HTTP 200 http://localhost:8411/sessions/sa0e61b32fcd940bebff92bc1e0189a8f/versions
2026-10-20T07:52:44.620Z HTTP 200 http://localhost:8411/keywords/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:44.640Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
2026-10-20T07:52:44.649Z HTTP 200 http://localhost:8411/session/sa0e61b32fcd940bebff92bc1e0189a8f?version=v1
```

## Captured state / API output

```json
{
  "time": "2026-10-20T07:52:46.622Z",
  "url": "http://localhost:3411/pipeline/keywords",
  "body": "이 단계부터 다시\n1단계 · 키워드\nR1 초기 발산 결과 0개를 검토합니다\n\n거절할 키워드를 누르고 사유를 남기면 다음 라운드에 반영됩니다. 드래그하거나 M 키로 하위 카테고리를 옮길 수 있습니다.\n\nR1 · 현재\n초기 발산\n5W1H · JTBD\nR2\n인접 확장\nSCAMPER 대체·결합·응용\nR3\n수렴 · 균형\n분포 · 거절 · 커버리지\nR4\n재발산\n역발상 · 제거 · 부정 공간\n최종\n최종 검토\n크롤링으로 전달\n검토할 라운드\nR1\n다음 라운드 방향 지시 (선택)\n지시 저장하기\n전체0\n물리0\n심리0\n행동0\n전체 0\n판단 필요 0\nLLM 단독 0\n검색량 적음 0\n미연결 0\n거절됨 0\n수동 0\n키워드 검색\n키보드 도움말 보기\n모두 접기\n조건에 맞는 키워드가 없습니다. 필터를 해제하세요.\n물리 › 시간 접기\n0\n직접 추가하기\n물리 › 공간 접기\n0\n직접 추가하기\n물리 › 사회적 환경 접기\n0\n직접 추가하기\n물리 › 감각 접기\n0\n직접 추가하기\n물리 › 신체 상태 접기\n0\n직접 추가하기\n물리 › 제품·물리 상호작용 접기\n0\n직접 추가하기\n새 하위 카테고리 축\n축 선택\n물리\n심리\n행동\n새 하위 카테고리 이름\n하위 카테고리 추가하기\n축 분포\n\n승인 예정 포함 0개 기준 · 부족한 축은 다음 라운드가 채웁니다.\n\n물리\n0개 · 0%\n심리\n0개 · 0%\n행동\n0개 · 0%\n커버리지\nR1 확정 후 계산\nkeyword_feedback.md 미리보기 내부용\n\n승인 예정 0 · 거절 0\n\n변경 사항 없음\n임시 저장\n저장\n생성하기\n다음 라운드 생성"
}
```
