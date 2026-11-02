# OpenAI Decisions를 교차 판정 라벨러 백엔드로 추가 — 기획 (DCX-23)

## 문제
- 4단계 교차 판정에서 GPT와 함께 판정하는 자리는 Jev(`jevmodel.org/v1/systemone`) 하나만 연결할 수 있다(`backend/app/label/jev.py`의 `JevClient`).
- 같은 일을 하는 OpenAI Decisions API(`POST /v1/decisions`, `gpt-6-luna`)를 같은 자리에 꽂아 쓰고 싶다. 질문 개념은 1:1로 대응하지만 요청·응답 JSON 모양이 달라 지금 파서(`_parse_vote`)를 그대로 쓸 수 없다.
- 출처: Notion 티켓 DCX-23(작성 Yunho Bae, 2026-11-02). 결정: Decisions는 셋째 라벨러가 아니라 **Jev 자리의 백엔드**다. 한 세션에서는 Jev와 Decisions 중 하나만 GPT와 교차 판정한다.

## 동작 (예시)
- `.env`에 `JEV_BACKEND=decisions`, `DECISIONS_API_KEY`(없으면 `OPENAI_API_KEY`)를 두고 새 버전에서 라벨링을 시작하면, 문서마다 Decisions에 요청 1건을 보내 8개 질문 답을 받고 `JevVote`로 바꿔 저장한다. 병합·감사·κ는 지금처럼 동작한다.
- 화면의 라벨러 이름은 "Jev" 대신 "Decisions"로 보이고, 비용 칸에 예상 금액(입력 $0.10/1M 토큰)이 나온다.
- Decisions가 한 질문이라도 거절(`refusal`)하면 그 문서는 `refused`로 실패 처리되어 검수 큐로 가고 재시도하지 않는다.
- 키가 틀리면(401) 판정이 멈추고, 잔액 부족(429 `insufficient_quota`)이면 일시정지, 그 밖의 429·5xx는 재시도 후 재큐된다.

## 열린 질문 처리 (티켓 기본안 채택, 계획 승인으로 확정)
| 질문 | v1 결정 |
|---|---|
| UI 이름 | 백엔드가 `decisions`면 "Decisions"로 표시 |
| relate·outcome 분리 | 분리하지 않음. Jev와 같게 `relate_outcome` choice 하나 |
| 8000자 입력 예산 | 유지 |
| 거절 코드 | 새 코드 `refused` |
| 429 잔액 부족 구분 | `error.code == "insufficient_quota"` 기준. 실제 응답 확인은 키 확보 후(아래 위험) |

## 수용 기준
- AC1: `JEV_BACKEND=decisions`면 `get_jev_client()`가 `DecisionsClient`를 돌려주고, `jev_available()`은 Decisions 키(없으면 OpenAI 키)가 있을 때만 `True`다.
- AC2: 요청 본문이 `{model, input, questions}`이고 8개 질문이 `anchor, sense, feel, think, act, situation, relate_outcome, reason_code` 순서이며, `noul`→`predicate`(criteria를 instructions 끝에 줄바꿈으로 붙임), `choice`→`choices:[{value, description}]`로 바뀐다. `input`은 `build_state()` 결과 그대로다.
- AC3: 정상 응답이 `JevVote`로 바뀐다. predicate 6개 확률, `relate = relate+both`, `outcome = outcome+both`, `reason_probs` 합 1 정규화, 응답 `model`, `build_state()`의 `truncated`.
- AC4: 질문 누락·중복·순서 바뀜·타입 불일치·확률 범위 밖·choice 값 집합 불일치·합 0·빈 `model`은 `bad`(재시도 안 함)다.
- AC5: 거절이 하나라도 있으면 `JevError('refused', transient=False)`이고, 판정 워커가 `cache.fail(doc_id, 'refused')`로 남긴다.
- AC6: 오류 매핑 — 401→`unconnected`, 429+`insufficient_quota`→`insufficient`, 그 밖 429·5xx→지수 백오프 최대 5회 후 `bad`(transient), 네트워크 오류→`bad`(transient), 400·기타 4xx·파싱 실패→`bad`. 메시지에 응답 본문·키를 넣지 않는다.
- AC7: Jev 판정 캐시와 Decisions 판정 캐시가 섞이지 않는다(`context_key`가 Decisions 모델·백엔드로 달라짐).
- AC8: 시간 추정이 `DECISIONS_RATE_PER_MIN × 키 수`를 쓰고, 비용 칸이 Decisions일 때 예상 금액을 보여 준다. Jev일 때 화면·추정은 지금과 같다.
- AC9: 테스트는 네트워크 없이 돈다(`conftest`의 외부 연결 차단 유지). 백엔드 pytest · 프런트 lint · build · test 통과.

## 제외 범위
- relate·outcome 질문 분리, 프롬프트 캐싱, 이미지·JSON 입력, `score` 질문, 8000자 예산 확대.
- `usage.input_tokens` 누적 표시(티켓 "선택" 항목) — v1 제외.
- Jev ↔ Decisions 속도·일치율 수동 비교 — 실제 키와 운영 문서가 필요해 이 실행 밖에서 따로 한다.
- PR·배포·dcx.person-a.ai 확인 — 사용자가 따로 요청할 때.

## 위험
- **실제 API 미확인:** 개발자에게 Decisions 키가 없다. 요청·응답 형식은 티켓과 OpenAI 문서 기준의 가짜 응답으로만 검증된다. 특히 429 잔액 부족 응답 모양은 실제 확인 전까지 가정이다. 틀려도 그 429는 재시도 후 재큐되므로 문서 유실은 없다.
- **판정 워커 호출부:** `judge.py`·`monitor.py`가 지금 `JevClient(settings.jev_api_keys, settings.jev_model)`처럼 Jev 키·모델을 직접 넘긴다. Decisions일 때 엉뚱한 키가 쓰이지 않도록 호출부를 인자 없는 호출로 바꾼다(티켓의 "judge.py 유지"에서 벗어나는 최소 변경).
- **분당 요청 수:** Jev는 1~120으로 막혀 있다. Decisions는 조직 tier에 따라 더 높을 수 있어 상한을 두지 않는다(양수만).

## 설계 필요 여부
- **불필요.** 새 화면·흐름이 없고, 기존 카드·표의 라벨러 이름과 비용 문구만 바뀐다. 백엔드 구조는 티켓 명세(클라이언트 인터페이스 동일, `JevVote`로 변환)가 그대로 설계 역할을 한다.
