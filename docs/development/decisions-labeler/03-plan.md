# OpenAI Decisions 교차 판정 백엔드 — 구현 계획 (DCX-23)

기획 [01](01-brainstorm.md). light 트랙, 설계 게이트 없음(설계 불필요, 이유는 기획 문서). QA 계획 [QA_PLAN](QA_PLAN-decisions-labeler.md).
구현 담당: Claude Opus(`harness-opus`), 리뷰: Claude Sonnet(`harness-sonnet`, 읽기 전용), 브라우저 QA: Claude Opus.

## 0. 작업 환경
- `development-harness worktree /Users/baenaongunmandu/workspace/dcx/dcx_agent-decisions feature/decisions-labeler`.
- 의존성: `uv venv --python 3.12 backend/.venv` 후 `uv pip install -r backend/requirements.txt -r backend/requirements-dev.txt -c backend/constraints.txt`(**constraints 필수** — 빠지면 selectolax 최신판으로 수집 단계 26건 실패), `npm --prefix frontend ci`.
- 기준 검사: `harness.config.json`의 4개 명령(백엔드 pytest, 프런트 lint · build · test).
- 실제 Decisions·Jev 키 없음. 모든 테스트는 `httpx.MockTransport`, QA는 로컬 가짜 Decisions 서버.

## 1. Task
| ID | 내용 | 담당 파일 | 의존 | AC |
|---|---|---|---|---|
| T1 | 설정 · Decisions 클라이언트 · 요청/응답 변환 · 오류 매핑 · 백엔드 선택 | `backend/app/config.py`, `backend/app/label/jev.py`, `backend/app/label/decisions.py`(신규), `backend/tests/label/test_decisions.py`(신규), `backend/tests/fixtures/decisions/success.json`(신규) | — | AC1~AC6 |
| T2 | 판정 워커 · 모니터 연결, 캐시 키, 시간·비용 추정, 개요 API 라벨러 이름 | `backend/app/label/judge.py`, `backend/app/model/monitor.py`, `backend/app/label/overview.py`, `backend/tests/label/test_decisions_judge.py`(신규) | T1 | AC5, AC7, AC8 |
| T3 | 화면 라벨러 이름 · 비용 문구 | `frontend/src/lib/types.ts`, `frontend/src/lib/api/label.ts`(Overview 타입이 여기 있으면), `frontend/src/components/label/Overview.tsx`, `frontend/src/components/label/KappaTable.tsx`, `frontend/src/components/label/Audit.tsx`, `frontend/src/components/label/Queue.tsx`, `frontend/src/components/label/QueueCard.tsx`, `frontend/src/components/label/labelerMode.ts`, `frontend/src/components/label/labelerName.test.ts`(신규) | T2 | AC8 |
| T4 | 문서 | `.env.example`, `README.md` | T1 | — |

### T1 상세
- **설정** (`config.py`)
  - `jev_backend: Literal["http", "fake", "decisions"]`.
  - `decisions_api_keys: Annotated[list[str], NoDecode]`(별칭 `DECISIONS_API_KEY`, 쉼표 분리 — `split_jev_keys`와 같은 방식).
  - `decisions_model: str = "gpt-6-luna"`, `decisions_rate_per_min: int = 120`, `decisions_base_url: str = "https://api.openai.com/v1"`(QA용 가짜 서버 주소를 넣기 위함).
  - 새 항목 모두 빈 문자열이면 기본값(`empty_stage_setting_uses_default` 목록에 추가).
- **`decisions.py`**
  - `DecisionsClient(keys, model, transport=None)`. 키가 비면 `settings.openai_api_key`를 한 개짜리 목록으로 씀. 중복 키 제거, 라운드로빈, 키별 레이트리밋은 `jev._limiter_for(key, decisions_rate_per_min)` 재사용. 분당 요청 수는 양수만 허용(상한 없음).
  - `judge(doc, one_liner, *, idempotency_key=None) -> JevVote`. 인자는 받되 쓰지 않음, `Idempotency-Key` 헤더 보내지 않음. `close()` · 컨텍스트 매니저.
  - 요청 `POST {decisions_base_url}/decisions`, 헤더 `Authorization: Bearer <key>`, 본문 `{model, input: build_state() 문자열, questions: [...]}`.
  - 질문 변환 `to_decisions_questions(jev_questions(one_liner))` — 순서 고정. `noul` → `{type:"predicate", name, instructions: instructions + "\n" + criteria}`. `choice` → `{type:"choice", name, instructions, choices:[{value:키, description:설명}]}`(criteria 순서 유지).
  - 응답 파서 `_parse_decision(payload, questions, truncated)`:
    - `answers`는 리스트이고 길이 8, i번째 `name`이 요청 i번째 이름과 같아야 함(누락·중복·순서 바뀜 모두 여기서 잡힘).
    - 어느 답이든 `type == "refusal"`이면 → `JevError('refused', 'Decisions가 이 문서 판정을 거절했습니다')`(transient 아님). 거절 검사를 형식 검사보다 먼저 함.
    - 나머지는 `type`이 요청 타입(`predicate`/`choice`)과 같아야 함. predicate → `probability`. choice → `probabilities` 리스트를 `{value: probability}`로, 값 중복 금지, 값 집합 = criteria 키 집합, 합 > 0, 정규화.
    - 확률은 `jev._probability`로 0~1 유한수 검사. `model`은 비지 않은 문자열.
    - `relate = relate+both`, `outcome = outcome+both`, `reason_probs = reason_code` 정규화값 → `JevVote`.
    - 그 밖의 `KeyError/TypeError/ValueError` → `bad`.
  - 오류 매핑: 401 → `unconnected` / 429 이고 본문 JSON의 `error.code == "insufficient_quota"` → `insufficient` / 그 밖 429·5xx → `2**attempt`초 대기 후 최대 5회 재시도, 소진 시 `bad`(transient) / `httpx.RequestError` → `bad`(transient) / 그 밖 비200·JSON 파싱 실패 → `bad`. 메시지는 고정 문구(본문·키 미포함).
- **`jev.py`**
  - `jev_available()`: `decisions`면 `bool(settings.decisions_api_keys or settings.openai_api_key)`.
  - `get_jev_client(keys=None, model=None, transport=None)`: `decisions`면 `DecisionsClient(settings.decisions_api_keys if keys is None else keys, model or settings.decisions_model, transport)`. 순환 import는 함수 안 import로 피함.
  - `GPT_ONLY_MESSAGE`는 그대로.

### T1 RED 테스트 (`test_decisions.py`, 네트워크 없음)
- 요청 스냅샷: URL·헤더(Authorization 있음, Idempotency-Key 없음), 질문 8개 이름·순서·타입, predicate의 instructions 끝 criteria, choice의 choices 순서.
- 정상 응답(`fixtures/decisions/success.json`) → `JevVote` 각 필드 값(relate·outcome 합산, reason 정규화, model, truncated True/False 둘 다).
- `bad`(transient False): 질문 누락 · 중복 · 순서 바뀜 · 타입 불일치 · 확률 -0.1/1.1/NaN/문자열 · choice 값 집합 불일치 · choice 값 중복 · 합 0 · `model` 빈 값 · `answers`가 dict · 비JSON 본문.
- 거절 1개 → `refused`, transient False. 거절과 형식 오류가 같이 있어도 `refused`.
- 401 → `unconnected` · 429 `insufficient_quota` → `insufficient`(재시도 없음, 요청 1회) · 429 기타/500/503 → 재시도 후 성공, 재시도 소진 → `bad` transient(요청 6회, `time.sleep` monkeypatch) · `httpx.ConnectError` → `bad` transient · 400/404 → `bad`.
- 오류 메시지에 응답 본문 문자열·키 문자열이 없음.
- 키: `DECISIONS_API_KEY` 쉼표 두 개 → 번갈아 사용 · 없으면 `OPENAI_API_KEY` · 둘 다 없으면 `unconnected`.
- `jev_available()` / `get_jev_client()` 분기(http · fake · decisions).
- 실제 소켓 연결 시도 시 `conftest`가 실패시키는지(가짜 transport 없이 `get_jev_client()`로 판정하면 외부 연결 차단으로 실패 — `bad` transient로 감싸지는 것 포함).
- 명령: `backend/.venv/bin/python -m pytest backend/tests/label -q -p no:cacheprovider`.

### T2 상세
- `judge.py`
  - `context_key`: `jev` 라벨러이고 백엔드가 `decisions`면 identity = `f'{settings.decisions_model}/decisions'`, 아니면 지금 그대로.
  - `estimate`: `decisions`면 키 수 = `len(set(decisions_api_keys))` 또는 OpenAI 키 1개, 속도 = `decisions_rate_per_min`. 토큰은 Decisions 요청 본문(`{model, input, questions}`) JSON 길이/4. `jevCostUsd = tokens * 0.10 / 1_000_000`을 결과 dict에 추가(Jev면 `None`).
  - 클라이언트 생성: `JevClient(settings.jev_api_keys, settings.jev_model)` → `JevClient()`(백엔드 기본값을 `get_jev_client`가 고름).
- `monitor.py`: 같은 호출을 `JevClient()`로.
- `overview.py`: 결과에 `crossLabeler`(`'Decisions'` 또는 `'Jev'`) 추가. 진행 카드 `estimate`에 `jevCostUsd` 전달.
- 판정 워커는 `refused`를 기존 `cache.fail(doc_id, exc.code)` 경로로 처리(코드 변경 없이 동작해야 함 — 테스트로 고정).

### T2 RED 테스트 (`test_decisions_judge.py`)
- `JEV_BACKEND=decisions` + MockTransport(정상): 라벨링 시작 → Jev 자리 워커가 모든 문서 `done`, 저장된 투표가 `JevVote` 형식, GPT(fake)와 병합된 최종 라벨 수 = 문서 수, `labelerMode == 'cross'`.
- 한 문서만 거절 응답: 그 문서 `bad`·코드 `refused`, 나머지 `done`, 재시도 없음.
- 401: 워커 중단, 상태에 `unconnected`. 429 `insufficient_quota`: 일시정지.
- 캐시 분리: 같은 세션·맥락에서 `http`와 `decisions`의 `cache_root`가 다름.
- 추정: 키 2개·분당 60 → 문서 120건이면 60초. `jevCostUsd`가 토큰×0.1/1M. Jev 백엔드면 `jevCostUsd` 없음/None, 기존 추정 테스트 무변경 통과.
- 개요 API `crossLabeler` 값(Decisions/Jev).
- 기존 `test_judge*.py` · `test_jev.py` · 모니터 테스트 무변경 통과.

### T3 상세
- 개요 타입에 `crossLabeler?: 'Jev' | 'Decisions'`, 진행 추정에 `jevCostUsd?: number | null`.
- 라벨러 표시 이름 = `o.crossLabeler ?? 'Jev'`. 적용 위치: 진행 카드 이름(`name === 'jev'`), 비용 문구, `KappaTable`의 "Jev 정확도" 열 제목(prop `crossName`), `QueueCard`의 "Jev 확률" 열 제목(`Queue`가 overview에서 전달), `labelerMode.ts`의 GPT 단독 안내 문구(이름을 인자로 받는 함수로).
- 비용 문구: `jevCostUsd`가 숫자면 `예상 {이름} 비용 · 약 $X.XX(입력 N토큰)`, 아니면 지금 문구 그대로.
- `TrainingResult.tsx`의 "Jev 대비"는 변경하지 않음(학습 단계, 범위 밖).
- 테스트(`labelerName.test.ts`): 이름 함수 · 비용 문구 함수 단위 테스트(Decisions/Jev/값 없음). 기존 프런트 테스트 무변경 통과.

### T4 상세
- `.env.example`에 `DECISIONS_API_KEY=`, `DECISIONS_MODEL=`, `DECISIONS_RATE_PER_MIN=`, `DECISIONS_BASE_URL=` 추가, `JEV_BACKEND` 설명은 README로.
- README 환경변수 표에 `JEV_BACKEND`의 `decisions` 값과 새 4개 항목 추가, "Jev 키가 없거나…" 단락에 Decisions 사용법 한 줄.

## 2. TDD 규칙 (워커에 전달)
RED → GREEN → 리팩터링. 담당 외 파일 수정 금지. 보고서 `docs/development/decisions-labeler/reports/T<n>.md`. 실제 네트워크 호출 금지.

## 3. 리뷰 체크리스트 (Sonnet)
- 오류 메시지·로그에 응답 본문·키가 새지 않는가.
- 응답 파서가 순서·중복·누락·타입·확률 범위를 모두 막는가, 거절이 다른 오류보다 먼저 판정되는가.
- 키별 레이트리밋이 Jev와 같은 풀을 쓰되 서로 다른 키끼리 간섭하지 않는가.
- `context_key` 변경이 기존 Jev 세션의 캐시 경로를 바꾸지 않는가(Jev일 때 identity 문자열 그대로).
- 판정 워커의 거절 처리 경로가 재시도·일시정지로 새지 않는가.

## 4. QA
[QA_PLAN](QA_PLAN-decisions-labeler.md) 참고. 로컬 가짜 Decisions 서버 + 합성 코퍼스 세션으로 4단계를 끝까지 돌리고 화면 표시를 확인한다.

## 5. 수용 기준 연결
AC1→T1 · AC2→T1 · AC3→T1 · AC4→T1 · AC5→T1,T2 · AC6→T1 · AC7→T2 · AC8→T2,T3,QA · AC9→전체 검증 명령.

## 6. 되돌리기
`JEV_BACKEND`를 `http`(또는 `fake`)로 돌리면 즉시 기존 동작. 데이터 형식 변경 없음(`JevVote` 그대로). 코드는 revert.
