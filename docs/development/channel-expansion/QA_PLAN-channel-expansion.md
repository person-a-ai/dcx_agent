# QA Plan — 2단계 크롤링 채널 확장

## 1. Scope

**In**
- 크롤링 설정 화면: 새 채널 4개(유튜브 브이로그 · Threads · 지식iN · 82쿡) 행, 사용 가능 표시, 브이로그 설정 칸
- 게이트 화면: Threads 수집량 안내, 브이로그 문서 수 안내
- 상세 수집 화면: 채널 상태 표의 "건너뜀" 열, Threads 차단 문장
- 결과 화면: 채널 × 사유 건너뜀 표, 브이로그 분포 보충 표기
- 설정 API(`PUT /crawl/{sid}/config`)의 `youtube_vlog` 검증, 상태 API(`GET /crawl/{sid}/status`)의 `progress.skipped` · `report.channels[*].skip_reasons`
- 새 채널 문서가 전처리까지 지나가는지

**Out**
- 실제 사이트 크롤링 결과의 내용 품질(→ 구현 계획 T9 수동 확인 `reports/T9-manual.md`)
- 자막 분할 알고리즘의 경계 정확도(→ `backend/tests/crawl/test_captions.py`)
- 어댑터 파싱(→ `backend/tests/crawl/adapters/test_*.py` 녹화 응답 테스트)
- Threads 공식 API, OCR, 분류 모델 재학습

**대상:** build worktree `feature/channel-expansion`의 최신 task commit.

## 2. Acceptance Criteria

| ID | 기준 (01-brainstorm AC) | 시나리오 |
|---|---|---|
| AC-01 | 새 채널 4개가 설정 화면에 나오고 사용 가능 여부가 실제 조건대로 표시된다 | QA-E2E-001, QA-NEG-002 |
| AC-02 | 새 채널로 목록 → 게이트 → 상세 → 보고서가 끝까지 돈다, 멈춤 · 여기까지로 마치기가 동작한다 | QA-E2E-003, QA-E2E-004, QA-E2E-005, QA-NEG-003 |
| AC-03 | 브이로그 길이 범위를 설정할 수 있다 | QA-E2E-002, QA-NEG-001, QA-EDGE-004 |
| AC-04/05 | 브이로그 문서가 구간으로 나뉘고 `segmenter`가 기록된다 | QA-E2E-005 (문서 수 표기) · 단위 테스트 `test_captions.py`, `test_youtube_vlog.py` |
| AC-06 | 자막 없는 영상이 건너뜀 사유 건수로 남는다 | QA-E2E-004, QA-E2E-005 |
| AC-07 | Threads 차단 시 채널만 멈추고 로그인 시도 없이 안내한다 | QA-NEG-003 |
| AC-08/09 | 지식iN 질문만 · 82쿡 본문+댓글 | 단위 테스트 `test_naver_kin.py`, `test_cook82.py` · QA-E2E-005(채널 분포) |
| AC-10 | 새 채널 문서가 전처리를 오류 없이 지난다 | QA-E2E-006 |
| AC-11 | 기존 채널 흐름 회귀 없음 | QA-REG-001, QA-REG-002, QA-REG-003 |

## 3. Critical User Journeys

| # | Journey | 등급 | 이유 |
|---|---|---|---|
| J-1 | 새 채널을 켜고 수집해 결과를 확인한다 | P0 | 핵심 가치 경로 |
| J-2 | 새 채널 문서로 전처리를 시작한다 | P0 | 데이터가 다음 단계로 이어지는지(데이터 손상 위험) |
| J-3 | Threads가 막혔을 때 멈추고 여기까지로 마친다 | P0 | 실패 시 데이터 보존 |
| J-4 | 브이로그 길이 설정을 바꾼다 | P1 | 설정 저장 |
| J-5 | 과거 버전 · 모바일에서 화면을 본다 | P2 | 열람 · 반응형 |

## 4. E2E Scenarios

```
QA-E2E-001
Priority: P0
Type: Acceptance / E2E
Given: "QA 채널 확장" 세션이 2단계 크롤링 설정 화면에 있고, 서버는 기본 QA 환경(8절)으로 떠 있다
When: /pipeline/crawling 화면을 연다
Then:
  - 채널 표에 "유튜브 브이로그", "Threads", "지식iN", "82쿡" 행이 각각 1개씩 보인다
  - 네 행 모두 "새 채널" 배지가 보인다
  - 네 행 모두 "사용 불가" 배지가 없고 "사용하기" 스위치를 켤 수 있다
  - "유튜브 브이로그" 행의 수집 방식 칸에 "한국어 자막을 화제 단위로 나눠 문서화" 문구가 보인다
  - "Threads" 행의 수집 방식 칸에 "키워드당 약 20건" 문구가 보인다
  - 기존 채널 행(네이버 카페 · 네이버 블로그 · 유튜브 댓글 · 뽐뿌 · 클리앙)이 그대로 보인다
```

```
QA-E2E-002
Priority: P1
Type: Acceptance / E2E
Given: QA-E2E-001 화면에서 "유튜브 브이로그"가 켜져 있다
When: "고급 설정 펼치기"를 열고 "유튜브 브이로그" 칸에서 키워드당 영상 수 5, 최소 길이 2, 최대 길이 30을 입력해 저장한 뒤 새로고침한다
Then:
  - 새로고침 후 세 칸 값이 5 · 2 · 30으로 보인다
  - GET /session/{sid} 응답의 `crawlConfig.youtube_vlog`가 `{"videos_per_keyword": 5, "min_duration_s": 120, "max_duration_s": 1800}`이다
  - "1분 미만 쇼츠와 60분이 넘는 영상은 목록에서 뺍니다" 안내 문구가 보인다
  - "유튜브 브이로그"를 끄면 이 칸 묶음이 사라진다
```

```
QA-E2E-003
Priority: P0
Type: Acceptance / E2E
Given: 네 새 채널만 켠 설정이 저장돼 있고 확정 키워드가 `에어컨 청소`, `제습기`, `qa-empty` 3개다
When: "목록 수집 시작"을 누르고 목록 수집이 끝날 때까지 기다린다
Then:
  - 화면 제목이 "본문 수집 전에 키워드를 정리합니다"로 바뀐다
  - "Threads는 로그인 없이 볼 수 있는 결과만 모아 키워드당 약 20건입니다" 배너가 보인다
  - 상세 수집 예상 카드 아래 "유튜브 브이로그는 영상마다 자막 구간을 나누므로" 문구가 보인다
  - 키워드 표에 `qa-empty` 행이 "0건" 배지와 함께 보인다
  - `에어컨 청소` 행을 펼치면 유튜브 브이로그 · Threads · 지식iN · 82쿡 네 채널 이름이 보인다
```

```
QA-E2E-004
Priority: P0
Type: Acceptance / E2E
Given: QA-E2E-003이 끝난 게이트 화면
When: "상세 수집 시작"을 누르고 진행 화면을 본다
Then:
  - 채널 상태 표 머리에 "건너뜀" 열이 있다
  - 수집이 끝난 뒤 "유튜브 브이로그" 행 "건너뜀" 칸에 0보다 큰 숫자와 "(자막 없음)"이 보인다
  - "지식iN" 행 "건너뜀" 칸에 0보다 큰 숫자가 보인다
  - "Threads" 행 상태가 "완료"다
  - GET /crawl/{sid}/status 응답의 `progress.skipped.youtube_vlog.no_ko_captions`가 0보다 크다
```

```
QA-E2E-005
Priority: P0
Type: Acceptance / E2E
Given: QA-E2E-004의 상세 수집이 완료됐다
When: 결과 화면("수집 결과를 확인합니다")을 본다
Then:
  - "건너뛴 항목" 표에 "유튜브 브이로그 · 한국어 자막 없음 · N개 영상" 행이 있다(N = status 응답 `report.channels.youtube_vlog.skip_reasons.no_ko_captions`)
  - 같은 표에 "지식iN · 삭제된 글 · M건" 행이 있다(M = `report.channels.naver_kin.skip_reasons.deleted`)
  - "채널 분포"에 네 새 채널 이름이 모두 보인다
  - "유튜브 브이로그" 분포 줄에 "영상 … → 구간 …" 표기가 보인다
  - "전처리로 이동하기" 버튼이 보인다
```

```
QA-E2E-006
Priority: P0
Type: Acceptance / E2E
Given: QA-E2E-005의 결과 화면
When: "전처리로 이동하기"를 누르고 기본 설정으로 전처리를 시작해 끝날 때까지 기다린다
Then:
  - 전처리 화면이 오류 배너 없이 완료 상태가 된다
  - 전처리 결과의 원본 문서 수가 결과 화면 "수집 문서" 수와 같다
  - 전처리 채널 목록(제외 소스 선택)에 "유튜브 브이로그", "Threads", "지식iN", "82쿡"이 보인다
```

## 5. Negative Scenarios

```
QA-NEG-001
Priority: P1
Type: Negative
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 30, 최대 길이 10을 입력한다
Then:
  - "저장" 버튼과 "목록 수집 시작" 버튼이 비활성화된다
  - PUT /crawl/{sid}/config에 `youtube_vlog: {"min_duration_s": 1800, "max_duration_s": 600}`을 직접 보내면 422 응답과 `error.code: "invalid_request"`가 온다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`는 이전 저장값 그대로다
```

```
QA-NEG-002
Priority: P1
Type: Negative
Given: 서버를 `PLAYWRIGHT_BROWSERS_PATH=<빈 임시 폴더>`로 다시 띄웠다(Chromium 없음)
When: 설정 화면을 연다
Then:
  - "Threads" 행에 "사용 불가" 배지가 보인다
  - "Threads" 행에 "Crawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다." 문구가 보인다
  - "Threads" 스위치가 비활성화돼 있다
  - GET /crawl/{sid}/status의 `available_sources`에 `threads`가 없다
  - `threads`를 포함한 설정을 PUT /crawl/{sid}/config로 보내면 422와 `error.code: "sources_unavailable"`이 온다
```

```
QA-NEG-003
Priority: P0
Type: Negative / Failure injection
Given: 서버를 `QA_THREADS_MODE=blocked`로 다시 띄웠고, Threads만 켠 세션에서 목록 수집이 끝난 게이트 화면이다
When: "상세 수집 시작"을 누르고 멈출 때까지 기다린 뒤 "여기까지로 마치기"를 누르고 확인한다
Then:
  - 멈춤 배너 "수집이 멈췄습니다"가 보인다
  - 배너에 "Threads" 배지가 보인다
  - 배너에 "Threads가 로그인 화면을 보여 주어 멈췄습니다. 로그인은 시도하지 않습니다." 문구가 보인다
  - "여기까지로 마치기" 후 결과 화면 "건너뛴 항목" 표에 "Threads · 차단으로 여기까지 마침" 행이 있다
  - 서버 로그와 네트워크 기록에 threads.com 로그인 주소 요청이 없다
```

```
QA-NEG-004
Priority: P2
Type: Negative / API
Given: QA 세션
When: PUT /crawl/{sid}/config에 `youtube_vlog: {"videos_per_keyword": 0}`을 보낸다
Then:
  - 422 응답과 `error.code: "invalid_request"`가 온다
```

## 6. Edge Cases

```
QA-EDGE-001
Priority: P1
Type: Edge / Empty
Given: 확정 키워드가 `qa-empty` 하나뿐인 세션
When: 네 새 채널로 목록 수집을 끝낸다
Then:
  - 게이트 화면 인사이트에 "수집된 목록이 없습니다"가 보인다
  - 상세 수집 예상 대상 URL이 0이다
  - 화면에 오류 배너가 없다
```

```
QA-EDGE-002
Priority: P1
Type: Edge / Permission (read-only)
Given: QA-E2E-005가 끝난 세션에서 새 버전을 만들어, 끝난 버전이 과거 버전(열람 전용)이 됐다
When: 과거 버전의 크롤링 화면을 연다
Then:
  - 결과 화면의 "건너뛴 항목" 표가 보인다
  - "일시 정지하기" · "다시 수집" 등 쓰기 버튼이 보이지 않거나 비활성화돼 있다
```

```
QA-EDGE-003
Priority: P2
Type: Edge / Viewport
Given: 브라우저 폭 375px
When: 설정 화면과 결과 화면을 연다
Then:
  - 문서 가로 스크롤 폭(`document.documentElement.scrollWidth`)이 화면 폭과 같다(표만 자체 가로 스크롤)
  - 새 채널 네 행과 "건너뛴 항목" 표의 모든 열 이름을 가로 스크롤로 볼 수 있다
```

```
QA-EDGE-004
Priority: P2
Type: Edge / Boundary
Given: 설정 화면에서 "유튜브 브이로그"가 켜져 있다
When: 최소 길이 0, 최대 길이 1을 입력해 저장한다
Then:
  - 저장에 성공한다
  - GET /session/{sid}의 `crawlConfig.youtube_vlog`가 `min_duration_s: 0`, `max_duration_s: 60`이다
```

## 7. Regression Scope

검색한 곳: `crawl/worker.py` · `report.py` · `control.py` 호출처, `Progress.tsx` · `Settings.tsx` · `crawling/page.tsx`, 0단계 채널 선택(`context/models.Channel`), 전처리 채널 목록(`prep.ts`).

```
QA-REG-001
Priority: P0
Type: Regression
Given: 개발용 샘플(fixture) 채널만 켠 세션(`ENABLE_FIXTURE_CHANNEL=true`)
When: 목록 수집 → 게이트 → 상세 수집 → 결과까지 진행한다
Then:
  - 결과 화면 "수집 문서"가 0보다 크다
  - "건너뛴 항목이 없습니다." 문구가 보인다
  - "전처리로 이동하기" 버튼이 보인다
```

```
QA-REG-002
Priority: P1
Type: Regression
Given: 설정 화면
When: "유튜브 댓글"을 켜고 고급 설정을 연다
Then:
  - "키워드당 영상 수", "영상당 최대 댓글" 칸이 기존대로 보인다
  - 기존 채널(네이버 카페 · 블로그 · 뽐뿌 · 클리앙)의 동시성 · 요청 간격 기본값이 바뀌지 않았다(블로그 1 · 0.5)
```

```
QA-REG-003
Priority: P1
Type: Regression
Given: 새 프로젝트를 0단계(입력)에서 만든다
When: 수집 채널 선택 칸을 연다
Then:
  - 기존 채널 선택지가 그대로 있다
  - 새 채널 4개가 선택지에 보이고, 하나를 골라 저장하면 GET /session/{sid}의 `projectContext.channels`에 그 값이 들어간다
```

## 8. Test Data / Preconditions

| Item | Value / source | Notes |
|---|---|---|
| 실행 환경 | build worktree 최신 task commit. 백엔드 `backend/.venv/bin/python -m uvicorn app.main:app --port 8000`(cwd `backend`), 프론트 `npm --prefix frontend run dev` (`NEXT_PUBLIC_API_URL=http://localhost:8000`) | QA 워커가 직접 띄운다 |
| 기본 환경 변수 | `STORAGE=local`, `LOCAL_DATA_DIR=<QA 전용 임시 폴더>`, `EMBED_BACKEND=fake`, `ENABLE_FIXTURE_CHANNEL=true`, `REAL_CHANNELS_ENABLED=true`, `CORS_ORIGINS=http://localhost:3000`, `DCX_TEST_ADAPTER_MODULE=channel_expansion_qa`, `PYTHONPATH=<worktree>/backend/tests/qa_hooks` | 상세 · 목록 워커는 API 프로세스 환경을 물려받아 QA 훅 어댑터를 쓴다. 실제 사이트 요청 없음 |
| 변형 환경 | QA-NEG-002: `PLAYWRIGHT_BROWSERS_PATH=<빈 임시 폴더>` · QA-NEG-003: `QA_THREADS_MODE=blocked` | 시나리오마다 서버를 다시 띄운다 |
| 사전 설치 | `backend/.venv/bin/crawl4ai-setup` 완료(T0) — Threads "사용 가능" 판정에 필요 | |
| 세션 "QA 채널 확장" | `POST /context`로 생성 후, 시드 스크립트가 확정 키워드 `에어컨 청소`, `제습기`, `qa-empty`(축 · 하위는 임의, `status: approved`)를 세션에 기록 | 시드 스크립트는 `docs/development/channel-expansion/qa/`에 둔다 |
| 세션 "QA 빈 결과" | 위와 같되 확정 키워드 `qa-empty` 하나 | QA-EDGE-001 |
| 세션 "QA 샘플" | 개발용 샘플 채널만 | QA-REG-001 |
| QA 훅 데이터 | 키워드당 브이로그 6(3번째마다 `no_ko_captions`) · Threads 25 · 지식iN 5(5번째 `deleted`) · 82쿡 8, `qa-empty`는 0건 | `backend/tests/qa_hooks/channel_expansion_qa.py` (계획 T9) |
| External services | 모두 끔(fake 임베더, QA 훅 어댑터) | |
| 쓰기 가능 경로 | `docs/development/channel-expansion/qa/` | 제품 소스 · Git 변경 금지 |

## 9. Priority

- **P0** — 새 채널 핵심 흐름(J-1), 전처리 연결(J-2), 차단 시 보존(J-3), 기존 흐름 회귀(QA-REG-001)
- **P1** — 브이로그 설정 저장 · 검증, 사용 불가 표시, 빈 결과, 과거 버전, 기존 설정 칸 · 0단계 회귀
- **P2** — 모바일, 경계값, API 직접 검증 일부

## 10. Expected Result

**Pass condition** — 활성 ID 전부(QA-E2E-001~006, QA-NEG-001~004, QA-EDGE-001~004, QA-REG-001~003)가 PASS이고, 각 시나리오의 실행 단계 · 기대/실제 · 시간 · 스크린샷 또는 응답 로그 경로가 `docs/development/channel-expansion/qa/`에 있다. FAIL/BLOCKED/NOT_RUN이 있으면 browser-qa 단계를 완료하지 않는다.

**Known gaps**
- 실제 Threads · 유튜브 · 지식iN · 82쿡 응답은 브라우저 QA에서 쓰지 않는다(QA 훅). 실제 사이트 동작은 T9 수동 확인과 어댑터 녹화 테스트가 맡는다.
- QA-NEG-003의 Threads 차단은 상세 단계에서 재현한다(실제 Threads는 목록 단계에서 차단된다). 화면 상태 · 문구 · "여기까지로 마치기" 동작을 확인하는 목적이다.
- 브이로그 구간 경계가 "화제 단위"인지는 화면으로 판정할 수 없다 → `test_captions.py`, `test_youtube_vlog.py`.
- QA-REG-003: 0단계 채널 선택지는 `frontend/src/app/pipeline/start/page.tsx`가 `labels.channels`(= `contextLabels.channels`)에서 만든다(확인함). T2가 그 목록에 새 채널을 더하므로 선택지에 나타난다.

**Already covered by existing tests**
- 건너뜀 상태 · 사유 집계: `backend/tests/crawl/test_skipped.py`(T1)
- 채널 기본값 · URL 정규화 · 설정 검증: `backend/tests/crawl/test_channel_identity.py`(T2)
- 프론트 기본값 · 사유 이름표 · 행 정렬: `frontend/src/lib/logic/channelExpansion.test.ts`(T8)
- 새 채널 문서 → 전처리 필터 · 분류 특징: `backend/tests/crawl/test_channel_expansion_flow.py`(T9)
