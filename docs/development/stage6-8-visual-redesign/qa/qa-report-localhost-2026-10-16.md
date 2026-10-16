# QA 보고서 — 페르소나 화면 재구성 (report-only)

- 날짜: 2026-10-16 · 브랜치: feature/stage6-8-visual-redesign · 기준 커밋: 8658bfa
- 호출: /qa-only (하네스 browser-qa 단계), 모드: Full, 범위: 03-plan.md QA 계획 Q1~Q8
- 대상: http://localhost:3411/pipeline/personas (프론트), API http://127.0.0.1:8411
- 격리: 운영 데이터 복사본 `/private/tmp/dcx-qa-data` (세션 2개). 운영 API(8400)·운영 데이터는 사용하지 않음.
- 드라이버: gstack 헤드리스 브라우저 `$B` (Aside 미설치)
- 사전 준비(복사본에서만): s8b25 v2 근거 묶음 재조립(`assemble.assemble`, 태깅 캐시 사용) 후 페르소나 fresh 재생성(21/21 완료)

## Charters

| ID | 계약(기대 결과) | 위험 | 진입점 | 종료 조건 |
|---|---|---|---|---|
| Q1 | 이전 카드 세션(s89d9234) 전체 맵: 점이 축 대부분에 퍼짐, 구역 면 6개, 라벨 겹침 없음, 범례는 클러스터만, 기회 최대 Context가 오른쪽 상세에 미리 선택 | 몰림·겹침 재발 | /pipeline/personas (세션 s89d9234 활성) | 스크린샷 + DOM 확인 |
| Q2 | 같은 세션 카드: Pain Points 자리에 근거 탐색 재실행 안내 + 링크, 버튼 없음, 화면 깨짐 없음 | 이전 카드에서 깨짐 | 목록에서 첫 페르소나 | 스크린샷 + 텍스트 |
| Q3 | s8b25 v2 카드: 상단 Pain Points 3~5개, 관측/추론 표시, 원문 펼침 | 페인포인트 미표시 | 세션 s8b25 활성, 카드 열기 | 스크린샷 + 펼침 확인 |
| Q4 | 같은 카드 비교 표: 장벽·상태·감정이 문장, 키워드 나열 없음, 3줄 말줄임/펼침 | 키워드 덮어쓰기 잔존 | 카드 하단 표 | 텍스트 + 스크린샷 |
| Q5 | 카드 오른쪽 지도: 선택 페르소나 점만 진함, 라벨 표시 | 강조 누락 | 카드 화면 지도 | DOM opacity/label |
| Q6 | 구조 트리 펼치기, 인사이트 기회 순위: 선 겹침·잘림 없음, 문장·막대 겹침 없음 | 레이아웃 깨짐 | 카드 하단 트리, /pipeline/insights | 스크린샷 |
| Q7 | 768px 미만: 목록→select, 표 가로 스크롤 + 항목 열 고정, 44px | 좁은 화면 깨짐 | responsive | 스크린샷 + computed style |
| Q8 | 키보드 Tab: 목록 → 보기 버튼 → 페인포인트 → 표 칸, 포커스 보임 | 접근성 회귀 | 카드 화면 | 포커스 순서 기록 |

## 타이밍

- Probe budget: Full 900초 지정, 이번 실행은 `$B` 명령을 deadline guard 없이 개별 실행(가드 미사용은 한계로 기록).
- Guarded command time: 해당 없음(가드 미사용). Total session elapsed: unmeasured.

## 결과 요약

| ID | 결과 | 근거 |
|---|---|---|
| Q1 | **부분 통과** — 점 114개가 가로로 퍼지고 구역 면 6개·범례 7개, 기회 최대 Context(CL1-P2-C1) 미리 선택 확인. 단 표·구역 이름·범례에 시각 결함(F2·F4·F5) | screenshots/q1-overview-s8b25.png, DOM `{"zones":6,"points":114,"labels":["CL1-P2-C1"],"legend":7}` |
| Q1′ | 세라젬 AI 웰니스 모듈러하우스는 운영에서 페르소나를 만든 적이 없어 지도 없음 → F1 | screenshots/q1-overview-s89d.png |
| Q2 | **통과** — 이전 카드: 안내 문구 + `/pipeline/evidence` 링크, "다시 만들기" 버튼 없음 (QA 복사본에 운영 구버전 카드를 잠시 넣어 확인 후 원복) | screenshots/q2-legacy-card.png |
| Q3 | **통과** — 상단 Pain Points 3개, 추론 표시·Context 칩·근거 수, 페인포인트가 주 영역 | screenshots/q3-card-top.png |
| Q4 | **실패** — 상태·감정·장벽 칸에 키워드 나열이 남음(F6). 3줄 말줄임·펼침 버튼은 동작 | screenshots/q4-card-table.png, 데이터 집계(아래) |
| Q5 | **부분 통과** — 선택 페르소나 점 1개만 진함(113개 opacity 0.25), 라벨 표시. 단 카드 지도가 폭 222px로 축소(F3) | DOM `{"svgW":222,"svgH":320,"dim":113,"full":1}` |
| Q6 | 구조 트리 **통과**(들여쓰기·막대, 선 겹침 없음). 인사이트 기회 순위는 **차단** — QA 환경에서 인사이트 도출 LLM이 2회 연속 "LLM이 연결되지 않았거나 한도를 넘었습니다"로 중단 | screenshots/q6-card-bottom.png, q6-insights.png |
| Q7 | **부분 통과** — 375px: 목록→select, 문서 가로 스크롤 없음(docW 375), 표만 가로 스크롤(402>247), 항목 열 sticky. 단 제목 중복·페인포인트 들여쓰기(F7) | screenshots/q7-mobile-card.png |
| Q8 | **통과** — Tab 순서: 인사이트 도출 → 목록 21개 → 보기 버튼 → 더 보기 → 페인포인트 3개 → 표 칸 10개 → 범례. 모든 요소 포커스 링(2px solid) | 탭 순서 기록(대화 로그) |

## Findings

### F6 (High, Functional) 상태·감정·장벽 칸 37%가 여전히 키워드 나열
- Observed: s8b25 v2 재생성 카드 114개 Context × 3칸 = 342칸 중 126칸이 근거 묶음의 키워드 원문과 동일(예: CL1-P2-C1 감정 "혈압 저하 고칼륨혈증 단백질 변화", 장벽 "2,000mg 상한 수분 섭취 제한").
- Expected: 기획 수용 기준 4 "키워드를 이어 붙인 문자열이 더 이상 나오지 않는다".
- Evidence: q4-card-table.png, API 집계 스크립트 결과 `cells 342 keyword fallback cells 126`.
- Confirmation: 데이터 전수 집계(재현 불필요).
- Hypothesis: 카드 LLM이 해당 칸에 근거 번호(cite)를 달지 않아, 승인된 R2 규칙("cite 없으면 키워드 원문으로 대체")이 적용됨. R2 결정과 수용 기준 4가 실제 데이터에서 충돌 → **계획 수정(사용자 결정) 필요**.

### F8 (Medium, Content) 페인포인트 '관측'이 거의 없음
- Observed: 페인포인트 335개 중 관측 5개, 추론 330개.
- Expected: 설계 2.2 — 태깅 페인포인트를 우선 사용, 원문 확인된 것은 관측.
- Evidence: API 집계 `grades Counter({'inferred': 330, 'observed': 5})`, 근거 956건 중 페인포인트 950·검증 919.
- Hypothesis: LLM이 태그 문장을 다듬거나 합쳐 정확 일치(R4 기준)가 거의 성립하지 않음. 기능은 계약대로 동작하나 사용자 체감상 "모두 추론"으로 보임 → 계획 수정(사용자 결정) 필요.

### F2 (High, Visual) 전체 맵 Context 표 열이 짓눌림
- Observed: 1440px에서 표 폭 888px, Persona·중요도 등 열이 61px, 이름·대표 페인포인트 200px 고정 → Persona 이름이 2글자씩 줄바꿈, "카드 열기"가 세로로 한 글자씩 표시.
- Expected: 설계 3.5 "이름 칸 폭을 고정해 줄바꿈", 표가 깨지지 않음(기획 12).
- Evidence: q1-overview-s8b25.png, DOM 열 폭 측정.

### F3 (High, Visual) 카드 화면 지도가 너무 작음
- Observed: 카드 화면 오른쪽 지도 SVG 폭 222px, 눈금·라벨 판독 불가, 범례 칩이 지도보다 큼.
- Expected: 설계 3.3 최소 높이 320px·판독 가능, 시안의 카드 오른쪽 기회 지도.
- Evidence: q4-card-table.png, DOM `svgW:222`.

### F4 (Medium, Visual) 구역 이름 겹침
- Observed: 오른쪽 위 B Experiencing·C Competitive 이름이 겹쳐 "ExperienCompetitive"로 보이고, D Forgiven 이름이 점과 겹침.
- Expected: 설계 3.3 구역 이름이 면 안에 읽히게.
- Evidence: q1-overview-s8b25.png.

### F5 (Low, Content) 범례 이름 중복
- Observed: 범례 "● CL5 · CL5", "● CL6 · CL6".
- Expected: 클러스터 이름 1회.
- Evidence: DOM 범례 텍스트 `["● CL0",…,"● CL5 · CL5","● CL6 · CL6"]`.

### F1 (Medium, Functional) 페르소나 미생성 세션이 오류처럼 보임
- Observed: 페르소나를 만든 적 없는 세션에서 지도 자리에 "아직 결과가 준비되지 않았습니다. [다시 불러오기]", 표 "Context 0개", 화면이 3초마다 409 응답을 반복(10회 관측).
- Expected: 설계 4.1 빈 상태 — 페르소나를 만들라는 안내(기존 화면 문구 "페르소나를 만들면 전체 맵과 Context를 확인할 수 있습니다.").
- Evidence: q1-overview-s89d.png, network 409 ×30(cards/map/tree 각 10).

### F7 (Medium, Visual) 좁은 화면 카드 상단
- Observed: 375px에서 페르소나 이름이 페이지 제목과 카드 제목으로 두 번 크게 표시, Pain Points 목록 왼쪽 들여쓰기가 넓고 글자가 커서 한 줄 4~6자.
- Expected: 설계 6 — 좁은 화면에서 Pain Points가 먼저, 읽기 쉬운 배치.
- Evidence: q7-mobile-card.png.

## 점수 (잠정, 시험한 범주만)

| 범주 | 점수 | 근거 |
|---|---|---|
| Console | 70 | 409 오류 1종(F1 관련) |
| Visual | 48 | F2·F3(High), F4·F7(Medium), F5(Low) |
| Functional | 77 | F6(High), F1(Medium) |
| Content | 92 | F8(Medium) |
| Accessibility | 100 | 탭 순서·포커스 링 정상 |
| Links | 미시험 | — |

## Top 3

1. F6 — 상태·감정·장벽 칸 37% 키워드 나열 (계획 수정 필요)
2. F2 — 전체 맵 Context 표 열 짓눌림
3. F3 — 카드 화면 지도 222px로 판독 불가

## 제안 테스트 (보고만)

- F2: `ContextTable`이 1440px 컨테이너에서 Persona 열 최소 폭(예: 140px)을 갖는지 렌더 테스트. Value: protects=전체 맵 표 가독성; fails_when=고정 폭 열이 다른 열을 짓누름; why_new=현재 테스트는 열 존재만 확인; seam=none
- F3: 카드 화면에서 지도 컨테이너 최소 폭/높이 규칙 테스트. Value: protects=카드 지도 판독성; fails_when=1/3 열에 지도가 축소; why_new=스타일 규칙 테스트 없음; seam=none
- F5: 범례가 cluster_label이 id와 같을 때 한 번만 표시. Value: protects=범례 텍스트; fails_when=label==id 중복 출력; why_new=범례 테스트는 버튼 수만 확인; seam=none

## 한계

- deadline guard·exploration 체크포인트 JSON 미사용(간이 진행). 브라우저 증거는 스크린샷·DOM 측정 출력.
- 인사이트 기회 순위 브라우저 확인은 QA 환경 LLM 중단으로 차단.
- 세라젬 AI 웰니스 모듈러하우스는 운영에서 페르소나 미생성이라 이전 카드 시나리오는 s8b25에 운영 구버전 카드를 잠시 넣어 확인(이후 원복 확인).

## 2차 확인 (수정 후, 커밋 115230b·bb1abdd, 하네스 밖에서 사용자 요청으로 진행)

QA 복사본에서 페르소나 fresh 재생성(21/21, CL5-P0 1건은 일시 실패 후 재시도 성공) 후 확인.

| 지적 | 결과 | 근거 |
|---|---|---|
| F6 키워드 나열 | **해결** — 126/342칸 → 4/321칸. 상태·감정·장벽 칸 등급: 관측 102, 추론 61, 추측 158 | API 집계 |
| F8 관측 비율 | **해결** — Context 페인포인트 관측 307/315, 페르소나 Pain Points 92개 모두 관측 | API 집계 |
| F2 표 열 짓눌림 | **해결** — 열 폭 ID 96·이름 220·Persona 160·수치 72·구역 100·페인포인트 260·카드 96, 표 영역 가로 스크롤 | screenshots/r2-overview.png |
| F3 카드 지도 폭 | **해결** — 222px → 370px | screenshots/r2-card-table.png |
| F4 구역 이름 겹침 | **해결** — 구역 이름을 지도 아래 별도 줄로 이동 | screenshots/r2-overview.png |
| F5 범례 중복 | **해결** — `["● CL0",…,"● CL5","● CL6"]` | DOM |
| F7 좁은 화면 | **해결** — 제목 중복 제거, Pain Points 들여쓰기·글자 크기 축소, 문서 가로 스크롤 없음(375) | screenshots/r2-mobile-card.png |
| F1 미생성 세션 | 코드·단위 테스트로 수정(status가 done일 때만 결과 요청, 안내 문구). 브라우저 재확인은 미실시 | tasks/qa-fix-frontend.md |

남은 사소한 점: 지도에서 선택 점이 오른쪽 끝(중요도 1.0)에 있으면 라벨 "CL1-P2-C1"이 SVG 오른쪽 경계에서 잘림. 인사이트 기회 순위는 QA 환경 LLM 중단으로 브라우저 미확인(단위 테스트만).

## 3차 확인 (남은 항목)

| 항목 | 결과 | 근거 |
|---|---|---|
| 지도 라벨 오른쪽 잘림 | **해결** — 오른쪽 끝 점 라벨은 점 왼쪽에 `text-anchor=end`로 표시. 화면에서 라벨 오른쪽 1008px < 지도 오른쪽 1071px | screenshots/r3-label-edge.png, tasks/fix-label-edge.md |
| 인사이트 기회 순위 | **통과** — 7개 행 모두 문장과 막대가 겹치지 않음, 평균선은 막대 영역 안. (이전 2회 중단은 워커 경로의 일시적 LLM 오류였고, 같은 설정으로 직접 호출하니 성공) | screenshots/r3-insight-bars.png |
| 페르소나 미생성 세션(F1) | **통과** — 안내 문구 표시, "다시 불러오기"·준비 안 됨 오류 없음, 12초 동안 cards/map/tree 요청 0건·409 0건 | screenshots/r3-not-generated.png |

## 4차 (리뷰 후속)
- QA 수정 커밋 리뷰(Codex 읽기 전용): F1~F8 확인, 라벨 왼쪽 배치 시 겹침 회피 누락 1건 → eee264d로 수정, 재리뷰 No findings. 브라우저에서 라벨이 지도 안에 있음 확인. 프론트 847 / 백엔드 2779 테스트, 린트, 빌드 통과.
