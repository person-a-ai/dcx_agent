# 브라우저 QA 결과: Decisions 교차 판정 (DCX-23)

- 코드: `a807c12` (`feature/decisions-labeler`), 실행일 2026-11-02, 실행자 claude (browser-qa)
- 브라우저: Claude 내장 브라우저 창(`mcp__Claude_Browser__*`), 뷰포트 1280x900 에뮬레이션
- 서버: 백엔드 `127.0.0.1:8321` (`start_backend.sh`), 프런트 `next dev -p 3321` (`NEXT_PUBLIC_API_URL=http://localhost:8321`), 가짜 Decisions `127.0.0.1:8399` (`mock_decisions.py`). 8000/3000에는 손대지 않음.
- 공통 설정: `STORAGE=local`, `LOCAL_DATA_DIR`=scratchpad `qa-data/data`, `LLM_BACKEND=fake`, `EMBED_BACKEND=fake`, `LABEL_GPT_BACKEND=fake`, `ENABLE_FIXTURE_CHANNEL=True`, `FIXTURE_CORPUS_PATH`=scratchpad `qa-data/corpus.csv`, `DECISIONS_BASE_URL=http://127.0.0.1:8399/v1`, `DECISIONS_API_KEY=qa-key-1,qa-key-2`(가짜), `OPENAI_API_KEY` 비움.
- 코퍼스: `make_qa_corpus.py`가 `make_corpus.write_corpus`(200행)를 부르고 3행을 덧붙임. 덧붙인 행은 거절 표식 행 2개(`QA-REFUSE-MARK-A/B`, 후기 300/301)와 14,439자 행 1개(후기 302). 키워드 매칭 뒤 세션 문서는 131건이고 특수 행 3개가 모두 들어 있음.
- 세션 준비(화면): 0단계 입력 → 키워드 R1/R3/R4 생성·저장(가짜 LLM) → 크롤링(`개발용 샘플`만 켬, 목록 131 → 상세 131) → 전처리(131건, prepKey `p_82344a663550`) → 4단계 진입. 대체 스크립트는 쓰지 않음. 세션 `s245f6045a3454d51a9b2b1bb080c0f8e`.
- 각 시나리오는 화면의 "4단계부터 다시 → 새 버전 만들기"로 새 버전을 만든 뒤 "라벨링 시작"을 눌러 진행함(v1~v9).

## 테스트 데이터 차이 (명시)
판정 캐시는 `context_key` = `DECISIONS_MODEL/decisions` 기준이라, 같은 모델이면 새 버전도 E2E-001의 투표를 재사용하고 가짜 서버로 요청을 보내지 않는다. 그래서 새 요청이 필요한 시나리오(E2E-002, NEG-001, NEG-002, NEG-004, NEG-003)에서는 `DECISIONS_MODEL`만 시나리오별 값(`qa-model-e2e002` 등)으로 바꿔 백엔드를 다시 띄웠다. 백엔드(`decisions`), 주소, 키는 모두 같다. E2E-001과 EDGE-001은 기본값 `gpt-6-luna`를 썼다.

## 시나리오
| ID | 버전 | 결과 | 근거 |
|---|---|---|---|
| QA-E2E-001 | v1 | PASS | `shots/e2e001-running.jpg`, `shots/e2e001-done.jpg`, `evidence/e2e001-analysis.json`, `evidence/e2e001-overview.json`, `logs/mock-e2e001.jsonl` |
| QA-E2E-002 | v2 | PASS | `shots/e2e002-running.jpg`, `evidence/e2e002-overview-running.json`, `logs/mock-e2e002.jsonl` |
| QA-NEG-001 | v3 | PASS | `shots/neg001-overview.jpg`, `shots/neg001-queue.jpg`, `evidence/neg001-analysis.json`, `evidence/neg001-overview.json`, `logs/mock-neg001.jsonl` |
| QA-NEG-002 | v4 | PASS | `shots/neg002-stopped.jpg`, `evidence/neg002-overview.json`, `evidence/neg002-session.json`, `evidence/neg002-pipeline-status.json`, `logs/mock-neg002.jsonl` |
| QA-NEG-003 | v6 | PASS | `shots/neg003-gpt-only.jpg`, `evidence/neg003-overview.json`, `logs/mock-neg003.jsonl` 없음(0건) |
| QA-NEG-004 | v5 | PASS (문구 참고) | `shots/neg004-paused.jpg`, `evidence/neg004-overview.json`, `evidence/neg004-analysis.json`, `logs/mock-neg004.jsonl` |
| QA-EDGE-001 | v7→v8 | PASS | `shots/reg001-fake-jev.jpg`, `shots/edge001-decisions.jpg`, `evidence/edge001-folders.txt`, `evidence/edge001-overview.json` |
| QA-EDGE-002 | v1 | PASS | `evidence/e2e001-analysis.json` (`doc302`, `truncated_doc_tags`) |
| QA-REG-001 | v7 | PASS | `shots/reg001-fake-jev.jpg`, `evidence/reg001-overview.json` |
| QA-REG-002 | v9 | PASS | `shots/reg002-jev-gpt-only.jpg`, `evidence/reg002-overview.json` |
| QA-REG-003 | v1 | PASS | `shots/reg003-audit.jpg` |

### QA-E2E-001
- 화면(완료 후): 전량 판정 카드에 `Decisions` "131건 판정 · 0건 남음 / 판정을 마쳤습니다.", `GPT` "131건 판정 · 0건 남음 / 판정을 마쳤습니다." 표시. 비용 줄은 "예상 Decisions 비용 · 약 $0.01(입력 67,014토큰)". κ 표 열 제목은 "Decisions 정확도", "GPT 정확도".
- Jev 표기 검사: 개요, 검수 큐(제출 전), 검수 큐(제출 후 비교표 "Decisions 확률"), 감사 탭에서 `document.body.innerText`로 `Jev`를 찾았고 0건이었다. 비교표를 보려고 v1 검수 큐에서 1건을 제출했다(테스트 세션).
- 가짜 서버 로그: POST `/v1/decisions` 131건(문서 131건), 131건 모두 질문 순서가 `anchor, sense, feel, think, act, situation, relate_outcome, reason_code`. `Idempotency-Key` 헤더 0건. 키 슬롯은 1/2를 번갈아 씀(1:66, 2:65, 연속된 두 요청이 같은 키인 경우 없음).
- 개요 API: `crossLabeler="Decisions"`, `labelerMode="cross"`.
- 캐시 `judge/<sid>/p_82344a663550/jev/q1-61259f54/votes.sqlite`: done 131, 131건 모두 probs 키 8개(relate·outcome 포함), reason_probs 있음, model `mock-decisions-1`.

### QA-E2E-002
- 라벨링 시작 6초 뒤(진행 중, Decisions "11건 판정 · 120건 남음 / 처리 중…") 화면 문구: "예상 Decisions 비용 · 약 $0.01(입력 67,187토큰)". "입력"과 "토큰"이 들어 있고, "금액 추정은 아직 제공되지 않습니다"는 없음.
- 개요 API(진행 중, state `running`): `progress.jev.estimate.jevCostUsd = 0.0067187`.
- 참고: 같은 비용 줄은 라벨링 시작 전에도 보인다.

### QA-NEG-001
- 가짜 서버는 `refuse` 모드. 표식이 든 요청에는 `reason_code` 답을 `type:"refusal"`로 돌려준다.
- 캐시: done 129, bad 2(`last_error="refused"`, attempts 0). bad 두 건의 문서가 후기 300/301(표식 문서)임을 확인.
- 로그: 131건, 입력별 최대 요청 수 1. 표식 요청은 300, 301 각 1회.
- 화면: Decisions "129건 판정 · 0건 남음 / 판정을 마쳤습니다. 2건은 판정하지 못해 검수 큐로 보냈습니다.", 탭 "검수 큐56", 큐 화면 "남은 56건", 사유 "등급 불일치 54건 · 판정 실패 2건". 첫 카드는 "판정 실패" 표식 문서(후기 300).

### QA-NEG-002
- 화면: Decisions "0건 판정 · 131건 남음 / 판정이 멈췄습니다. / Decisions 연결 키를 확인해 주세요", 지금 할 일 카드에 "판정이 멈췄습니다". API state `failed`, reason "Decisions 연결 키를 확인해 주세요".
- 유출 검사: 화면 텍스트, overview/session/pipeline-status API 응답, 백엔드 로그, LOCAL_DATA_DIR 전체에서 `qa-key`와 가짜 응답 본문(`MOCK-SECRET-BODY…`) 0건. 가짜 서버 요청 1건(401).

### QA-NEG-003
- 백엔드 env: `JEV_BACKEND=decisions`, `DECISIONS_API_KEY=`, `OPENAI_API_KEY=` (`ps eww`로 확인).
- 화면: 배너 "Decisions 미연결 · GPT 단독 판정", 본문 "... Decisions를 연결한 뒤 새 버전에서 시작하면 교차 판정합니다." 전량 판정에는 GPT 카드만 있음.
- API: `labelerMode="gpt_only"`, `crossLabeler="Decisions"`, progress 키 `['gpt']`.
- 가짜 서버(정상 모드, 로그 `logs/mock-neg003.jsonl`) 요청 0건. 파일이 끝까지 생기지 않았고, 이어진 REG-001 실행 동안에도 0건.

### QA-NEG-004
- 가짜 서버는 `quota` 모드(429 `{"error":{"code":"insufficient_quota",...}}`).
- 화면: Decisions "판정이 멈췄습니다. / Decisions 사용 한도가 부족합니다", 버튼 "이어서 진행 · 중단", 사이드바 "일시 정지됨 · 이어서 진행". API state `paused`, reason "Decisions 사용 한도가 부족합니다".
- 로그: 30초 넘게 지나도 요청 1건(재시도 없음).
- 참고: 사유 문구에 "잔액"이라는 단어는 없다. 쿼터·한도가 부족하다는 안내("사용 한도가 부족합니다")다. 계획의 기대값은 따옴표 없는 "잔액 부족 안내"라서 PASS로 판정했다. 문자 그대로 "잔액"이 필요하면 FAIL로 바꿔야 한다.

### QA-EDGE-001
- 순서: REG-001(`JEV_BACKEND=fake` + `LABEL_FAKE_JEV_CROSS=true`, v7)로 라벨링을 끝낸 뒤 `JEV_BACKEND=decisions`(기본 모델)로 재시작하고 v8을 만들어 라벨링 시작.
- judgeRefs: v7 jev → `q1-5a40afd6`, v8 jev → `q1-61259f54`(서로 다름).
- 저장된 모델: `q1-5a40afd6` = `fake-jev-latest` 131건, `q1-61259f54` = `mock-decisions-1` 131건. 섞이지 않음. v8 Decisions 실행은 같은 Decisions 캐시를 재사용해 가짜 서버 요청이 0건이었다.

### QA-EDGE-002
- 후기 302(본문 14,439자): 요청 `input_len_json = 8000`(≤ 8000), 저장된 투표 `truncated=true`. truncated가 true인 투표는 이 문서 1건뿐.

### QA-REG-001
- 화면: 진행 카드 이름 "Jev", 비용 문구 "예상 Jev 비용 · 금액 추정은 아직 제공되지 않습니다. 예상 입력 59,547토큰", κ 표 "Jev 정확도". 화면에 "Decisions"는 없음.
- API: `crossLabeler="Jev"`, `labelerMode="cross"`, `jevCostUsd=null`, fake Jev 131건 done.

### QA-REG-002
- `JEV_BACKEND=http`, Jev·Decisions 키 없음. 시작 전과 시작 후 모두 배너 "Jev 미연결 · GPT 단독 판정"과 본문 "... Jev를 연결한 뒤 새 버전에서 시작하면 교차 판정합니다." API `labelerMode="gpt_only"`, `crossLabeler="Jev"`.

### QA-REG-003
- E2E-001 세션(v1)의 감사 탭에서 κ 표 "라벨러 성능 · 감사 기준"이 열림. 열은 `칸 | 표본 | 감사 κ | Decisions 정확도 | GPT 정확도 | 비고`, 9행. GPT 열은 그대로 있음.

## 정리
- 내가 시작한 프로세스는 모두 종료함(pid는 보고서 JSON에 있음). 8000/3000 서버는 건드리지 않음.
- `git status`: `docs/development/` 밖에는 변경 없음.
