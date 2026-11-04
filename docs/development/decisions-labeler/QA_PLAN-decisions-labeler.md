# QA Plan — OpenAI Decisions 교차 판정 백엔드 (DCX-23)

| | |
|---|---|
| Source spec | Notion DCX-23 · [01-brainstorm.md](01-brainstorm.md) · [03-plan.md](03-plan.md) |
| Branch / version | `feature/decisions-labeler` 하네스 build worktree의 최신 task commit (base main `d7d6827`) |
| Author | Controller (Claude Code) |
| Last updated | 2026-11-02 |
| Status | draft (계획 승인 대상) |

## 1. Scope

**In scope**
- `JEV_BACKEND=decisions`일 때 4단계 라벨링의 교차 판정이 Decisions 응답으로 끝까지 도는지.
- 라벨링 화면(개요 · 감사 · 검수 큐)의 라벨러 이름과 비용 문구.
- 거절 · 401 · 잔액 부족 응답의 화면·상태 동작.
- `JEV_BACKEND=fake`(기존 경로) 회귀.

**Out of scope**
- 실제 OpenAI Decisions 호출, 실제 Jev 호출(키 없음). 모든 Decisions 응답은 로컬 가짜 서버가 만든다.
- Jev ↔ Decisions 속도·일치율 비교(기획 제외 범위, 키·운영 데이터 확보 후 별도).
- 판정 품질(가짜 응답이라 의미 없음).
- 오류 매핑의 세부 HTTP 경우(재시도 횟수 등)는 단위 테스트(T1)가 맡는다. 브라우저 QA는 화면에서 관찰되는 결과만 본다.

**Open questions**
- 없음(열린 질문은 기획 문서에서 티켓 기본안으로 확정, 이 계획 승인으로 함께 승인).

## 2. Acceptance Criteria

| # | Criterion (기획) | Covered by |
|---|---|---|
| AC1 | `decisions`면 Decisions 클라이언트 사용, 키 있을 때만 교차 판정 | QA-E2E-001, QA-NEG-003 |
| AC2 | 요청 형식(질문 8개 순서·변환, input) | QA-E2E-001(가짜 서버 요청 로그), T1 단위 테스트 |
| AC3 | 응답 → `JevVote` 변환 | QA-E2E-001(저장된 투표 확인), T1 |
| AC4 | 형식 오류 → `bad` | T1 단위 테스트(브라우저 범위 밖) |
| AC5 | 거절 → `refused`, 검수 큐 | QA-NEG-001 |
| AC6 | 오류 매핑 401 · 잔액 부족 | QA-NEG-002, QA-NEG-004, T1 |
| AC7 | Jev · Decisions 캐시 분리 | QA-EDGE-001, T2 |
| AC8 | 이름 · 시간 · 비용 표시 | QA-E2E-001, QA-E2E-002, QA-REG-001 |
| AC9 | pytest · lint · build · test | 하네스 verification 단계(브라우저 QA 범위 밖) |

## 3. Critical User Journeys

| # | Journey | Tier | Priority |
|---|---|---|---|
| J-1 | Decisions로 설정한 서버에서 라벨링 시작 → 교차 판정 완료 → 최종 라벨 확인 | core / data | P0 |
| J-2 | 일부 문서가 거절됨 → 검수 큐로 감 | data | P0 |
| J-3 | 키 오류 · 잔액 부족 → 멈춤 · 일시정지 안내 | money / core | P1 |
| J-4 | 기존 Jev(fake) 설정에서 지금과 같은 화면 | regression | P0 |

## 4. E2E Scenarios

```
QA-E2E-001
Priority: P0
Type: Acceptance / E2E
Given: QA 서버가 JEV_BACKEND=decisions, DECISIONS_BASE_URL=가짜 서버, DECISIONS_API_KEY=qa-key-1,qa-key-2, LABEL_GPT_BACKEND=fake 로 떠 있고, 합성 코퍼스 세션이 3단계까지 끝나 있다
When: 4단계 라벨링 화면에서 판정을 시작하고 완료될 때까지 기다린다
Then:
  - 개요의 "전량 판정" 카드에 "Decisions" 진행 카드와 "GPT" 진행 카드가 보인다
  - 화면 어디에도 "Jev 정확도", "Jev 확률" 같은 Jev 표기가 보이지 않는다(TrainingResult 제외)
  - 두 진행 카드가 완료 상태가 된다
  - 가짜 서버 요청 로그에 문서 수만큼 POST /decisions 가 있고, 각 요청 본문 questions 의 name 순서가 anchor, sense, feel, think, act, situation, relate_outcome, reason_code 이다
  - 요청 헤더에 Idempotency-Key 가 없고 Authorization 이 qa-key-1 과 qa-key-2 를 번갈아 쓴다
  - GET 개요 API 응답의 crossLabeler 가 "Decisions" 이고 labelerMode 가 "cross" 이다
  - 판정 캐시 폴더 아래 jev 라벨러 결과 파일의 투표에 probs(relate·outcome 포함 8개)·reason_probs·model 이 있다
```

```
QA-E2E-002
Priority: P1
Type: Acceptance / E2E
Given: QA-E2E-001 과 같은 서버이고, 새 버전으로 라벨링을 시작한 직후(진행 중)
When: 개요 화면의 Decisions 진행 카드를 본다
Then:
  - "예상 Decisions 비용 · 약 $" 로 시작하는 문구가 보인다
  - 같은 문구에 "입력" 과 "토큰" 이 포함된다
  - "금액 추정은 아직 제공되지 않습니다" 문구가 보이지 않는다
  - 개요 API 의 Decisions 진행 estimate.jevCostUsd 가 0 이상 숫자이다
```

## 5. Negative Scenarios

```
QA-NEG-001
Priority: P0
Type: Negative
Given: 가짜 서버가 특정 문서 2건(요청 input 에 표식 문자열 포함)에 대해 reason_code 답을 type "refusal" 로 돌려준다
When: 새 버전에서 라벨링을 시작해 완료까지 기다린다
Then:
  - Decisions 판정 결과에서 그 2건이 실패(bad)로, 실패 코드가 refused 로 기록된다
  - 가짜 서버 로그에서 그 2건의 요청이 각 1회뿐이다(재시도 없음)
  - 나머지 문서는 완료된다
  - 검수 큐 탭의 총 건수가 그 2건을 포함해 0보다 크다
```

```
QA-NEG-002
Priority: P1
Type: Negative
Given: 가짜 서버가 모든 요청에 401 을 돌려준다
When: 새 버전에서 라벨링을 시작한다
Then:
  - Decisions 진행 카드가 멈춤 상태가 되고 "연결 키" 안내 문구가 보인다
  - 화면·API 응답 어디에도 키 문자열 qa-key 와 가짜 서버 응답 본문이 나오지 않는다
```

```
QA-NEG-003
Priority: P1
Type: Negative
Given: QA 서버가 JEV_BACKEND=decisions 이지만 DECISIONS_API_KEY 와 OPENAI_API_KEY 가 모두 비어 있다
When: 새 버전에서 라벨링을 시작한다
Then:
  - 개요 API labelerMode 가 "gpt_only" 이다
  - GPT 단독 안내 문구가 보이고, 문구 안의 라벨러 이름이 "Decisions" 이다
  - 가짜 서버로 요청이 0건이다
```

```
QA-NEG-004
Priority: P1
Type: Negative
Given: 가짜 서버가 모든 요청에 429 와 {"error":{"code":"insufficient_quota"}} 를 돌려준다
When: 새 버전에서 라벨링을 시작한다
Then:
  - Decisions 진행 카드가 일시정지 상태가 된다
  - 일시정지 사유에 잔액 부족 안내가 보인다
  - 가짜 서버 로그에 요청이 1건뿐이다(재시도 없음)
```

## 6. Edge Cases

```
QA-EDGE-001
Priority: P1
Type: Edge
Given: 같은 세션을 JEV_BACKEND=fake 로 한 번 라벨링한 기록이 있다
When: 서버를 JEV_BACKEND=decisions 로 재시작하고 새 버전에서 라벨링을 시작한다
Then:
  - data/judge/<sid>/<prep>/jev/ 아래에 서로 다른 q1-<hash> 폴더 두 개가 있다
  - Decisions 쪽 결과의 model 값이 가짜 서버가 준 모델 이름이다(fake-jev 값이 섞이지 않음)
```

```
QA-EDGE-002
Priority: P2
Type: Edge
Given: 본문이 8000자 예산을 넘는 문서가 코퍼스에 1건 있다
When: QA-E2E-001 과 같이 판정한다
Then:
  - 그 문서의 요청 input 길이(JSON 직렬화 기준)가 8000 이하이다
  - 그 문서의 저장된 투표 truncated 가 true 이다
```

## 7. Regression Scope

| ID | 기존 동작 | 확인 방법 |
|---|---|---|
| QA-REG-001 | JEV_BACKEND=fake + LABEL_FAKE_JEV_CROSS=true 에서 진행 카드 이름 "Jev", 비용 문구 "금액 추정은 아직 제공되지 않습니다", κ 표 "Jev 정확도" 가 그대로 | 서버를 fake 로 재시작, 새 버전 라벨링 시작 후 화면 확인 · 개요 API crossLabeler == "Jev" |
| QA-REG-002 | GPT 단독 모드(교차 키 없음, JEV_BACKEND=http) 안내 문구가 "Jev 미연결 · GPT 단독 판정" 그대로 | 서버를 http·키 없음으로 재시작 후 라벨링 화면 확인 |
| QA-REG-003 | 감사 탭의 κ 표가 열리고 GPT 열이 그대로 | QA-E2E-001 세션의 감사 탭 확인 |

## 8. Test Data / Preconditions

- **서버:** 구현 worktree에서 백엔드 `:8321`, 프런트 `:3321`(`NEXT_PUBLIC_API_URL=http://localhost:8321`). 개발자 맥의 기본 8000/3000 서버와 겹치지 않게.
- **공통 설정:** `STORAGE=local`, `LOCAL_DATA_DIR`=QA 전용 폴더, `LLM_BACKEND=fake`, `EMBED_BACKEND=fake`, `LABEL_GPT_BACKEND=fake`, `ENABLE_FIXTURE_CHANNEL=True`, `FIXTURE_CORPUS_PATH`=`backend/tests/fixtures/make_corpus.py`로 만든 합성 코퍼스(200행 이상, 8000자 넘는 행 1건 추가).
- **세션 준비:** 화면에서 0단계 입력 → 키워드(가짜 LLM) → 크롤링(fixture 채널) → 전처리까지 진행해 4단계 진입. 막히면 기존 QA 스크립트(`backend/tests/scripts/make_segment_qa.py` 등)의 세션 생성 방식을 참고.
- **가짜 Decisions 서버:** QA 워커가 `docs/development/decisions-labeler/qa/mock_decisions.py`로 작성. `POST /v1/decisions`를 받아 질문 순서대로 결정적인 답을 만들고, 요청(헤더 이름·본문 questions 이름·input 길이)을 JSONL로 기록. 모드(정상 · 거절 표식 · 401 · 429 quota)를 환경변수로 바꿈. 키 값 자체는 로그에 남기지 않고 어느 키였는지(1/2)만 기록.
- **읽기 도구:** 개요 API(`GET`), 판정 캐시 파일 읽기, 가짜 서버 로그. 데이터를 직접 고치지 않는다.

## 9. Priority

P0 = 교차 판정 완주(J-1), 거절 → 검수 큐(J-2, 데이터), 기존 Jev 경로 회귀(J-4). P1 = 비용 표시, 키·잔액 오류, 캐시 분리. P2 = 입력 잘림.

## 10. Expected Result

- 모든 활성 ID가 PASS여야 browser-qa 단계를 완료한다. FAIL/BLOCKED/NOT_RUN은 보존하고 단계를 막는다.
- 각 시나리오 근거: 실행 단계, 기대·실제 결과, 시간, 스크린샷·API 응답·가짜 서버 로그 경로를 `docs/development/decisions-labeler/qa/`에 남긴다.
- **알려진 공백:** 실제 OpenAI Decisions 응답 형식(특히 429 잔액 부족 본문)은 이 QA로 증명되지 않는다. 가짜 서버는 티켓·문서 기준 형식을 따른다. 실제 확인은 키 확보 후 별도로 기록한다.
