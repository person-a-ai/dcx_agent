# 6단계 "목표 페르소나 모드" — 구현 계획

근거: 2026-11-04~05 실험(`~/srv/dcx-agent/shared/experiments/anchor/`)과 노션 방법론 문서.
결정: 카드 입력은 **0단계 페르소나 시드 확장**, 범위는 **실험 전체**, 진행은 **계획 승인 후 직접 구현**.

## 사용자 흐름
1. 0단계 "생각하는 페르소나"에서 시드마다 **카드 펼치기**: Desire, Context, Pain, Unmet Needs, 키워드(최대 10), 대표 원문(최대 5). 기존 시드(이름 40자)는 그대로 둠.
2. 6단계 실행 화면에서 **"목표 페르소나로 나누기"** 선택(카드가 1개 이상 있어야 활성). 기존 "데이터로 나누기(k-means)"는 그대로.
3. 실행 중 미리보기: 페르소나별 배정 문서 수와 대표 원문이 먼저 보임.
4. 완료 후: 기존 6-A/6-B/6-C 화면이 그대로 동작(군집 = 목표 페르소나, Persona = 하위 상황, Context = LDA). 새 **"목표 페르소나 리포트"** 탭에서 기준선·바이럴·원인·해결 시도·원문·기타 비율·새 후보를 봄.

## 백엔드

### 0단계 스키마 (`context/models.py`, `context/render.py`)
- `PersonaSeed`에 선택 필드 `card: PersonaCard | None` 추가. `PersonaCard = {desire, context, pain, unmet: str(≤200), keywords: list[str](≤10), quotes: list[str](≤5, 각 ≤300)}`. 모두 선택값, 기존 데이터와 호환.
- 라벨링 이후에도 수정 가능(현재처럼 경고만). project_context.md에 카드 내용 렌더.

### 실행 옵션 (`routers/segment.py`)
- `Run.mode: 'clusters' | 'target' = 'clusters'`. target인데 카드가 없으면 409 `cards_required`. `k`는 target 모드에서 무시.
- checkpoint에 mode 기록. resume 시 같은 mode로 이어감. 모드를 바꾸면 fresh(확정값 초기화 확인 필요 — 기존 confirmReset 규칙 그대로).

### 새 모듈 `segment/target.py` (순수 함수 + LLM 주입)
| 함수 | 내용 |
|---|---|
| `anchor_texts(cards)` | 카드 전체 문장, Desire+Context+Pain, Pain+Unmet, 키워드, 대표 원문 각각 |
| `score(vectors, anchors, owner)` | 문서×페르소나 최대 코사인 (5만 건씩 청크) |
| `calibrate(S, judge)` | 점수 0.45~0.70 구간(0.05)마다 20건 LLM 판정(yes/partial/no) → 위 구간이 모두 평균 ≥0.5인 최저 구간을 기준선. 없으면 `no_match` |
| `viral(vectors, pool)` | 묶음 안 유사도 ≥0.92 이웃 3개 초과 → 복붙. + 광고 표시 정규식 |
| `assign(S, thresholds, excluded)` | 최고 점수 페르소나 & 기준선 이상 & 바이럴·광고 아님 → 배정, 나머지 기타 |
| `needs(pool_docs, judge)` | 페르소나별 표본 ≤100건: 본인 고민 여부, 원인(짧은 구), 해결 시도(고정 6종: 전문 관리·병원/약, 셀프 관리, 제품·기기, 식단·영양, 휴식·환경 바꾸기, 없음), 결과(효과 있음/일시적/효과 없음/언급 없음). 원인 구는 LLM 1회로 ≤6개 범주로 묶음 |
| `need_sentences(text)` | 고민·불편·바람 표지어 문장 추출(실험 규칙 그대로) |
| `discover(other_ids, vectors, nouns)` | 기타 문서에 L1(k=12) + L2 → 묶음별 키워드·원문 → LLM이 후보 요약(이름, 누가, Pain, 본인 목소리 여부) |

LLM 작업 3종 추가: `target_judge`, `target_needs`(+원인 묶기), `target_discover` — 프롬프트 파일은 `segment/prompts/`, fake 백엔드 응답도 추가.

### 파이프라인 (`segment/pipeline.py`)
- target 모드 STEPS: `load → anchor → calibrate → assign → L2 → L3 → needs → discover → quality → dims → drafts`.
- `assign` 결과를 **clusters 레이어**로: `cluster_id = T1..Tn`, 이름 초안 = 카드 이름(LLM 이름 생성 생략). 기타 문서는 레이어에 넣지 않음(리포트에만 집계). → 7단계 이후는 목표 페르소나에 배정된 문서만 사용.
- `L2`: 기존 `l2.personas`를 각 T 묶음에 그대로.
- `L3`: 기존 `l3.contexts`에 `fit_sample` 인자 추가(target 모드에서 4,000) — 표본으로 토픽 수 선택 후 전체 배정. 기존 모드는 동작 그대로.
- `quality`: target용 함수(응집도·채널 분포·Persona 응집도·Context npmi). k-means ARI·경계는 해당 없음.
- `drafts`: target 모드는 0단계 맥락 **전체**(리서치 질문, Known Insight, 해당 카드)와 하위 묶음 원문을 프롬프트에 넣음.
- 결과 `segment/target.json`: 기준선 구간표, 페르소나별 모인 글·바이럴·광고·배정·본인 고민 추정, 원인·해결 시도 표와 원문, 기타 수·비율, 새 후보 목록. 미리보기(preview.json)도 assign 직후 기록.

### API
- `GET /segment/{sid}/status`에 `mode` 추가.
- `GET /segment/{sid}/target` → target.json(원문 300자 제한).

## 프론트엔드
- `pipeline/start/page.tsx` + `startForm.ts`: 시드 행에 "카드" 토글과 입력 필드.
- `SegmentScreen.tsx`: 실행 옵션에 모드 선택, 실행 중 target 미리보기, 완료 후 **"목표 페르소나 리포트"** 탭(`TargetReport.tsx` 신규): 페르소나 카드별 요약 · 기준선 · 해결 시도 표 · 원인 · 원문 / 기타 비율 / 새 후보 목록.
- 기존 6-A/6-B/6-C 화면은 그대로 쓰되 target 모드 표시만 추가.

## 테스트
- `tests/segment/test_target.py`: 앵커 텍스트, 점수, 기준선(가짜 판정), 바이럴 감지, 배정·기타, need_sentences, 원인 묶기.
- `tests/segment/test_pipeline.py`: 합성 세션 + fake 임베더/LLM으로 target 모드 전 과정, resume, 카드 없음 409.
- `tests/context`: 카드 필드 저장·검증·렌더.
- 프론트: 카드 입력 로직, 모드 선택, 리포트 렌더 테스트. lint/build/test.

## QA (서버)
- 실제 프로젝트를 덮어쓰지 않도록 `imp-96bc83bbb84b`의 **새 버전**(또는 복제 세션)에서 실험 카드 5개로 target 모드 실행 → 실험 결과(배정 수·하위 묶음)와 비교.

## 위험·결정 사항
- target 모드에서 기타 문서는 7단계 이후로 넘어가지 않음.
- LLM 호출: 판정 페르소나당 ~120 + needs ~100 + 원인 묶기 1 + 새 후보 ~36 + drafts. 5개 기준 약 1,200회.
- 실행 시간 목표: 51만 건 기준 L3 포함 30분 이내.

## 되돌리기
- 기능 플래그 없이 모드 선택으로 분리. 기존 모드 코드 경로는 바뀌지 않음(l3 `fit_sample` 기본값 None).
