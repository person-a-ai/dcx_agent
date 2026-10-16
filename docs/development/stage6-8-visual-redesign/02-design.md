# 클러스터링 ~ 페르소나 화면 재구성 · 설계

기획 승인: 페인포인트 LLM 보충 포함 B안. Opportunity Map 눈금은 0~10으로 바꾸지 않는다. 세라젬_261012_sk v2 재생성은 이번 범위에서 제외한다.

## 1. 전체 흐름

```text
7단계 태깅 캐시 (pain_point {text, quote})          ← 변경 없음, 재호출 없음
  └─ evidence/assemble.py  근거 항목에 pain_point 싣기     [백엔드 변경 1]
       └─ evidence/package.json (evidence-package/1, 선택 필드 추가)
            └─ persona/cards.py  Context 페인포인트 생성·검증    [백엔드 변경 2]
                 │                 페르소나 Pain Points 집계(코드)
                 │                 키워드 덮어쓰기 제거
                 └─ persona cards.json → /persona/{sid}/cards
                      ├─ 인사이트 도출 입력(cards)에 자동 포함
                      └─ 페르소나 화면 재구성                        [프론트 변경]
```

## 2. 백엔드

### 2.1 근거 묶음에 페인포인트 싣기

- `app/evidence/package.py` `EvidenceItem`에 선택 필드를 추가한다.
  - `pain_point: PainPoint | None = None`, `PainPoint = {text: str, quote: str | None}`
  - 기본값이 None이므로 기존 `package.json`도 그대로 읽힌다. 스키마 이름(`evidence-package/1`)은 유지한다.
- `app/evidence/assemble.py` `_item()`이 태깅 결과의 `pain_point`를 옮긴다.
  - `text`가 비어 있거나 공백이면 None으로 둔다. `quote`는 문자열이 아니면 None으로 둔다.
  - 태깅 LLM은 다시 부르지 않는다. 이미 캐시된 태깅 결과(`llmcache/.../tag-*.sqlite`)를 읽는 기존 경로를 그대로 쓴다.
- `app/persona/package.py` `Evidence` 계약 모델에도 같은 선택 필드를 추가해, 페르소나 단계에서 그대로 읽는다.

### 2.2 Context 페인포인트 생성 (카드 생성 LLM)

- `app/persona/cards.py`
  - `_evidence_payload()`가 근거마다 `pain_point` 텍스트를 함께 넘긴다.
  - 출력 스키마 `ContextOut`에 `pain_points: list[PainCell]`을 추가한다. 최대 3개.
    - `PainCell = {text: str, cite: list[str] (1개 이상)}`
  - 검증(`_card_schema`)에 다음을 추가한다.
    - 모든 `cite`는 그 Context에 속한 근거 번호여야 한다 (기존 규칙과 동일).
    - `pain_points`의 `cite`는 비어 있으면 안 된다.
    - 근거가 없는 Context는 `pain_points`가 빈 배열이어야 한다. 코드에서도 강제로 비운다.
- `app/persona/prompts/card.v1.md` 지시 추가.
  - 출력 항목에 `pain_points`를 넣는다.
  - 입력 근거의 `pain_point`가 있으면 그 문장들을 우선 쓰고, 비슷한 것은 하나로 합친다.
  - 근거는 있으나 `pain_point`가 하나도 없으면, 근거 인용만 보고 그 Context의 불편·어려움을 직접 쓴다.
  - 어느 경우든 근거 번호를 반드시 단다. 근거가 없으면 빈 배열을 낸다.
  - 프롬프트 파일 내용이 바뀌므로 카드 캐시 키가 바뀌고, 다음 실행에서 카드가 새로 만들어진다.
- 관측/추론 표시 (코드가 결정, LLM이 정하지 않음):
  - **관측**: 인용한 근거 중 하나 이상에 태깅된 `pain_point`가 있고, 그 근거의 원문 인용이 검증됨(`verified`).
  - **추론**: 그 외 모든 경우 (LLM이 근거 인용만 보고 쓴 경우 포함).
  - 결과는 Context 항목에 `pain_points: [{text, cite, grade, source_pain}]`로 저장한다. `source_pain`은 인용 근거의 태깅 페인포인트 원문(있을 때)이다.
- 근거 추적: 기존 `grade_card()`의 trace에 `field='pain_point'` 행을 추가해, 화면에서 원문을 펼칠 수 있게 한다.

### 2.3 장벽·상태·감정 키워드 덮어쓰기 제거

- `cards.py`의 `situation_origin == 'dims'`일 때 LLM 문장을 키워드 문자열로 되돌리는 분기를 지운다.
- 대신 프롬프트가 이미 "dims 값의 의미와 범위를 유지하며 표현만 다듬는다"고 지시하므로 그 결과를 쓴다.
- 장벽 칸이 null인데 Context 페인포인트가 있으면, 첫 번째 페인포인트 문장과 근거 번호로 장벽 칸을 채운다.
- 이 변경으로 등급 검사(`grade_card`)는 그대로 적용되어, 근거 번호가 없는 문장은 추론 이하로 표시된다.

### 2.4 페르소나 Pain Points 집계 (코드, LLM 호출 없음)

- 카드 생성이 끝난 뒤 Context 페인포인트를 모은다.
- 같은 문장(공백·문장부호 정규화 후 동일)은 합치고 `context_ids`와 `cite`를 합친다.
- 정렬: 관측 우선 → 인용 근거 수 내림차순 → Context 문서 수 내림차순.
- 상위 5개를 카드 최상위 `pain_points: [{text, grade, context_ids, cite}]`로 저장한다. 근거가 적으면 있는 만큼만 저장한다.

### 2.5 인사이트 연동

- 인사이트 도출(`persona/insights.py` `derive`)은 카드 전체를 입력으로 넘기므로 `pain_points`가 자동으로 포함된다. 코드 변경은 없다.

### 2.6 API 변경

- 엔드포인트 추가·삭제는 없다.
- `GET /persona/{sid}/cards` 응답의 카드 본문에 `pain_points`(페르소나)와 `contexts[].pain_points`가 추가된다. 기존 필드는 그대로다.
- 이 기능 배포 전에 만든 카드에는 두 필드가 없다. 화면은 이 경우 "페르소나를 다시 만들면 페인포인트가 표시됩니다"로 안내한다.

## 3. 프론트엔드

### 3.1 화면 구조

```text
┌ 헤더: 8단계 · 페르소나 / 제목 / [인사이트 도출] ───────────────────────────┐
├ 왼쪽 목록 (240px) ┬ 본문 ──────────────────────────────────────────────────┤
│ CL0               │ [전체 맵] [Persona 카드]                               │
│  · 이름(2줄까지)  │                                                        │
│    상태 점        │ (전체 맵) Opportunity Map + 선택 Context 상세 + Context 표 │
│ CL1 ...           │ (카드)   Action Map 상단 → Context 비교 표 + 오른쪽 지도 │
│                   │          → 8-B · 8-C · 8-D 패널 → 구조 트리(접힘)       │
└───────────────────┴────────────────────────────────────────────────────────┘
```

### 3.2 왼쪽 목록 (`PersonaList`, 새 컴포넌트)

- 클러스터별 묶음. 각 항목은 이름을 최대 2줄로 줄바꿈하고 넘치면 말줄임, 전체 이름은 `title`로 제공한다.
- 상태는 이름 옆 배지 대신 왼쪽 작은 점(완료·진행·실패·대기)과 스크린리더용 숨김 텍스트로 표시해, 이름과 겹치지 않는다.
- FUTURE(범위 밖) 표시는 이름 아래 작은 배지 한 줄로 둔다.
- 선택 항목은 배경색과 `aria-current`로 표시한다.

### 3.3 Opportunity Map (`OpportunityMap` 개편)

- **표시 척도**: 각 축에 로그 척도 `f(v) = ln(1 + k·v) / ln(1 + k)`, `k = 50`을 적용한다. 원래 값은 0~1 사이로 정규화돼 있으므로 0→0, 1→1이 유지된다.
  - 눈금은 원래 값으로 적는다 (0, 0.02, 0.05, 0.1, 0.2, 0.5, 1). 0~10 표기는 쓰지 않는다.
  - 축 제목 옆에 "로그 척도"를 표시한다.
  - 툴팁·선택 Context 상세·표에는 원래 값을 보여 준다.
- **구역 면**: 기준선 3개(`s_line`, `diag1`, `diag2`)를 원래 값 공간에서 촘촘히(축마다 64점) 샘플링한 뒤 같은 척도로 변환해 곡선 경계를 그린다. 구역 판정은 백엔드 `zone` 값을 그대로 쓰고, 면은 그 판정 규칙과 같은 경계로 칠한다.
  - 구역마다 옅은 면색과 이름(A Exciting 등)을 면 안에 표시한다. F At-risk와 C Competitive는 강조색, 나머지는 중립색이다.
  - **색 토큰 (결정 5A, 기존 토큰만 사용)**: 구역 면 F=`--danger-soft`, C=`--warning-soft`, A·B·D·E=`--sunken`. 구역 이름 글자 F=`--danger`, C=`--warning`, 나머지=`--sub`. 점은 선택 페르소나 `--blue`, 그 외는 백엔드가 주는 기존 tone(`--ink-strong`/`--ink`/`--line-strong`). 기준선은 `--line-strong` 점선. 새 색이나 hex 값은 추가하지 않는다.
  - 화면 전체의 관측/추론 표시도 같은 규칙: 관측=`--success` 글자 + ●, 추론=`--warning` 글자 + ▲ (기존 `GradeMark` 재사용).
- **점 라벨**: 평소에는 라벨을 그리지 않는다. 마우스를 올리거나 선택한 Context, 그리고 카드 화면에서 선택 페르소나의 Context에만 `C번호` 라벨을 붙인다. 라벨끼리 겹치면 위·아래로 비켜 둔다.
- **범례**: 클러스터 7개의 모양과 이름만 한 줄로 보여 준다. 클릭하면 그 클러스터를 숨기거나 보인다. 페르소나 21개 버튼은 지운다(왼쪽 목록이 그 역할).
- **강조 모드**: `focusPersonaId`가 있으면 다른 점은 투명도 0.25, 해당 페르소나 점은 진하게 그린다.
- **겹친 점**: 같은 위치의 점은 1~3px 범위에서 고정된 각도로 살짝 흩어 그리고, 툴팁에 겹친 개수를 보여 준다.
- SVG는 `viewBox` 비율을 유지하고 컨테이너 폭에 맞춘다. 최소 높이 320px.

### 3.4 Persona 카드 (Action Map 구조)

**시각 우선순위 (결정 1A, 페인포인트 우선)**: 이 화면이 답하는 질문은 "이 사람은 어디서 막히는가"이다.

```text
1순위  Pain Points          ← 상단 주 영역, 가장 큰 본문 글자(--type-section), 첫 화면에 반드시 보임
2순위  Desire · Goal        ← Pain Points 바로 위 한 줄 요약(이름 아래), 보조 글자
3순위  Context 비교 표 + 기회 지도 ← 스크롤 첫 단락
보조   8-B · 8-C · 8-D, 구조 트리 ← 아래쪽, 작은 제목과 옅은 구분선
```

1. **상단 요약 (`PersonaSummary`)**
   - 맨 위 한 줄: Actor 이름(`--type-screen`)과 FUTURE 배지, 그 아래 메타 한 줄(근거·작성자·Context 수, 신뢰도·처방·제약).
   - 그 아래 한 줄: Desire 문장, Goal은 쉼표로 이은 한 줄(넘치면 "더 보기"로 펼침).
   - 주 영역: **Pain Points** 3~5개를 번호 목록으로 크게 보여 준다. 항목마다 관측/추론 표시, 출처 Context 번호 칩, 근거 수. 항목을 누르면 원문 인용이 펼쳐진다.
   - 페인포인트가 없는 이전 카드는 안내 문구를 보여 준다.
2. **Context 비교 표 (`CCMTable` 개편) + 오른쪽 지도**: 1280px 이상에서 `표 2 : 지도 1` 2열, 그보다 좁으면 표 아래에 지도.
   - 열 = Context(최대 4개씩 접어 여러 표로 나누는 기존 방식 유지), 행 = 행동 · 상태 · 감정 · 장벽 · **페인포인트** · 키워드 · 쓰는 제품·수단 · 만족도 · 기회(구역) · 근거 수.
   - 열 머리: Context 번호 배지, 이름, 반례면 경고 표시.
   - 칸은 지금처럼 누르면 근거 원문이 펼쳐진다. 관측/추론 표시를 유지한다.
   - **긴 문장 (결정 7A)**: 칸 문장은 최대 3줄(`line-clamp: 3`)까지 보이고 넘치면 …로 자른다. 칸을 누르면 전체 문장과 근거 원문이 함께 펼쳐진다. 페인포인트 행은 대표 1개만 보이고 나머지는 "+N"으로 표시하며, 누르면 모두 펼친다.
   - 오른쪽 지도는 3.3의 강조 모드로 선택 페르소나를 진하게 보여 준다. 점을 누르면 해당 열이 강조된다.
3. **8-B 수렴 · 8-C 속성 · 8-D 처방**: 탭 대신 3열 한 줄로 한 화면에 놓는다. 열 사이는 세로 구분선(`--line`)만 쓰고 상자는 두지 않는다. 1024px 미만은 세로로 쌓고 가로 구분선으로 나눈다. 제목은 기존 이름을 유지한다.

**표면 규칙 (결정 4A, 한 장의 작업면)**: 카드 본문은 하나의 흰 작업면(`--paper`)이다. 구역은 제목(`--type-card`), 위 32px · 아래 12px 여백, 얇은 가로선(`--line`)으로 나눈다. 테두리 상자(`ds-card`)는 **Pain Points 각 항목**과 **Opportunity Map** 두 곳에만 쓴다. 비교 표는 `ds-tbl` 표 스타일만 쓰고 바깥 상자를 두지 않는다. 그림자는 쓰지 않는다.
4. **구조 트리 (`HierarchyTree` 개편)**: 들여쓰기 목록으로 바꾼다. 클러스터·페르소나는 접고 펼칠 수 있고, 각 줄에 문서 수 막대(가로)와 숫자를 둔다. 기본은 선택 페르소나만 펼친다. 선과 원은 그리지 않는다.

### 3.5 전체 맵

- 왼쪽 2/3 Opportunity Map, 오른쪽 1/3 선택 Context 상세(이름, 페르소나, 구역, 중요도·만족도·기회 원래 값, 대표 페인포인트, "카드 열기").
- 아래 Context 표는 지금처럼 유지하되, 페인포인트 열(대표 1개)을 추가하고 이름 칸 폭을 고정해 줄바꿈한다.

### 3.5.1 사용 흐름 (결정 3A, 전체 맵 먼저)

| 단계 | 사용자가 하는 일 | 느낌 | 설계가 받쳐 주는 것 |
|---|---|---|---|
| 1 | 페르소나 단계에 들어옴 | "전체가 어떻게 생겼지?" | 전체 맵으로 열림. 기회 값이 가장 큰 Context를 미리 선택해 오른쪽 상세에 보여 줌 |
| 2 | 구역을 훑음 | "F At-risk에 뭐가 있지?" | 구역 면과 이름, 강조색(F·C) |
| 3 | 점이나 표 행을 누름 | "이게 어느 사람 이야기지?" | 오른쪽 상세에 페르소나·대표 페인포인트·원래 값, [카드 열기] |
| 4 | 카드를 엶 | "이 사람은 어디서 막히지?" | Pain Points가 첫 화면 주 영역 (결정 1A) |
| 5 | 원문을 펼침 | "진짜 이런 말을 했나?" | 관측/추론 표시와 원문 인용 |
| 6 | 다른 사람으로 이동 | 비교 | 왼쪽 목록, 지도에서 해당 페르소나 강조 |

### 3.6 인사이트 기회 순위 (`OpportunityBars` 개편)

- SVG 텍스트 대신 HTML 그리드로 바꾼다: `[순위] [문장(줄바꿈 허용)] [막대 영역] [값]`.
- 평균선은 막대 영역 안에서만 그린다. 문장이 길어도 막대와 겹치지 않는다.

### 3.7 데이터 타입

- `lib/types.ts`
  - `PersonaPainPoint = { text: string; grade: PersonaGrade; context_ids: string[]; cite: string[] }`
  - `PersonaCardContextPain = { text: string; cite: string[]; grade: PersonaGrade; source_pain?: string | null }`
  - `PersonaCardBody`에 `pain_points?: PersonaPainPoint[]`, `PersonaCardContext`에 `pain_points?: PersonaCardContextPain[]`를 추가한다.

## 4. 상태와 실패 처리

| 상황 | 화면 |
|---|---|
| 카드에 `pain_points` 필드 자체가 없음 (이전 카드) | Pain Points 자리에 "페르소나를 다시 만들면 페인포인트가 표시됩니다." |
| 필드는 있으나 빈 배열 (근거 없음) | "근거 부족" |
| 카드 생성 실패 | 기존 "다시 만들기" 흐름 유지 |
| 지도 데이터 없음 / 점의 i·s가 null | 지도 자리에 안내 문구, null 점은 표에만 표시 |
| 페르소나 생성 중 | 기존 진행률 문구 유지, 목록 상태 점은 진행 중 |
| LLM이 근거 없는 페인포인트를 냄 | 스키마 검증 실패 → 기존 재시도(최대 2회) → 실패하면 카드 실패 |

### 4.1 영역별 상태 표 (결정 2A)

| 영역 | 로딩 | 빈 값 | 오류 | 성공 | 부분 |
|---|---|---|---|---|---|
| 왼쪽 목록 | 클러스터 3묶음 × 3줄 회색 자리 | "아직 확정된 페르소나가 없습니다." + [클러스터링으로] | 목록 자리에 오류 문구 + [다시 불러오기] | 클러스터별 이름·상태 점 | 카드 실패 항목은 빨간 점 + "실패" 숨김 텍스트, 목록은 정상 표시 |
| Pain Points | 3줄 회색 자리 | 필드 없음: "페르소나를 다시 만들면 페인포인트가 표시됩니다." + [페르소나 다시 만들기] / 빈 배열: "근거가 부족해 페인포인트를 만들지 못했습니다." | 카드 오류와 같음 | 번호 목록 3~5개 | 1~2개만 있으면 있는 만큼 표시하고 "근거가 적어 N개만 찾았습니다." |
| Context 비교 표 | 열 머리와 행 이름은 보이고 칸만 회색 자리 | "이 페르소나에 확정된 Context가 없습니다." | 표 자리에 오류 문구 + [다시 불러오기] | 칸 표시, 칸 누르면 근거 펼침 | 근거 없는 칸은 "근거 부족"(옅은 글자), 다른 칸은 정상 |
| Opportunity Map | 축과 구역 면만 먼저 그리고 점은 생략 | "기회 지도를 만들 Context가 없습니다." | 지도 자리에 오류 문구 + [다시 불러오기] | 점·구역·강조 | i·s가 null인 점은 빼고 "지도에 없는 Context N개는 표에서 확인하세요." |
| 8-B · 8-C · 8-D | 각 패널 2줄 회색 자리 | 항목별 "근거 부족" | 패널마다 오류 문구 | 내용 표시 | 처방만 실패하면 처방 패널에만 오류, 나머지 정상 |
| 구조 트리 | 5줄 회색 자리 | "구조 트리가 준비되지 않았습니다." | 오류 문구 + [다시 불러오기] | 들여쓰기 목록 | 문서 수 0인 노드는 막대 없이 숫자 0 |

- 회색 자리(스켈레톤)는 실제 영역과 같은 높이로 그려 내용이 들어올 때 화면이 튀지 않게 한다.
- 오류 문구는 기존 `displayError`를 쓰고, 다시 불러오기는 해당 영역만 다시 요청한다.

## 5. 권한·데이터 안전

- 새 API가 없고 기존 세션 권한 검사를 그대로 쓴다.
- 페인포인트 원문 인용은 이미 화면에 보여 주는 근거 원문과 같은 범위다. 작성자 식별자는 노출하지 않는다.
- 세션 데이터는 이번 작업에서 다시 만들지 않는다 (승인 조건).

## 6. 반응형과 접근성

- 기준 폭: 1280px(2열 레이아웃), 1024px(8-B/C/D 세로), 768px(모든 영역 1열, 왼쪽 목록은 본문 위 접이식).
- **768px 미만 (결정 6A, 표는 가로 스크롤)**:
  - 왼쪽 목록은 본문 위의 선택 상자(`<select>`, 클러스터별 `<optgroup>`)로 바뀐다.
  - 순서: Pain Points → Desire·Goal → 비교 표 → 지도 → 8-B·8-C·8-D(세로) → 구조 트리.
  - 비교 표는 Context 열을 최소 200px로 두고 표 영역만 가로 스크롤한다. 항목 이름 열(행동·상태…)은 왼쪽에 고정(`position: sticky`)한다. 스크롤 가능하다는 것을 오른쪽 끝 옅은 그림자로 알린다.
  - 누를 수 있는 요소(목록 항목, 칸 버튼, 페인포인트 항목, 접기 버튼)는 최소 44px 높이다.
- 지도: `role="img"`와 구역별 개수 요약 `aria-label`을 유지한다. 점은 키보드로 접근할 수 없으므로 같은 내용을 Context 표로 제공한다(현행 유지).
- 관측/추론은 색만이 아니라 글자와 기호로 구분한다.
- 탭을 패널로 바꾸면서 제목(`h3`)으로 구조를 유지하고, 구조 트리의 접기 버튼은 `aria-expanded`를 쓴다.
- 대비: 구역 면색 위의 글자와 점이 WCAG AA(4.5:1, 그래픽 3:1)를 만족하도록 기존 디자인 토큰을 쓴다.

## 7. 테스트 방향 (계획에서 구체화)

- 백엔드: 근거 묶음에 `pain_point` 실림, 기존 package.json 읽기 호환, 카드 스키마의 페인포인트 인용 검증, 근거 없는 Context는 빈 배열, 관측/추론 판정, dims 덮어쓰기 제거, 페르소나 집계 정렬·중복 제거.
- 프론트: 로그 척도 함수와 구역 경계 샘플링, 라벨 표시 조건, 범례 토글, 긴 이름 목록 렌더링, 이전 카드 안내 문구, 기회 순위 그리드.
- 브라우저: 실제 세션(세라젬 AI 웰니스 모듈러하우스 등 이미 카드가 있는 세션)에서 1280·768px 화면 확인. v2 재생성은 하지 않으므로, 페인포인트 표시는 테스트용 세션 또는 픽스처로 확인한다.

## 8. 되돌리기

- 백엔드 변경은 선택 필드 추가라 이전 데이터와 호환된다. 코드만 되돌리면 이전 동작으로 돌아간다.
- 새 카드에 추가된 필드는 이전 화면이 무시한다.

## 9. 설계 검토 결과 (plan-design-review)

### 결정 기록

| 번호 | 항목 | 결정 |
|---|---|---|
| 1 | 카드 화면 시각 우선순위 | 1A 페인포인트 우선 (3.4) |
| 2 | 영역별 상태 | 2A 상태 표 추가 (4.1) |
| 3 | 첫 화면 | 3A 전체 맵 먼저, 기회 최대 Context 미리 선택 (3.5.1) |
| 4 | 카드 상자 남발 | 4A 한 장의 작업면, 상자는 Pain Points 항목·지도만 (3.4) |
| 5 | 색 | 5A 기존 토큰만 사용 (3.3) |
| 6 | 768px 미만 | 6A 표 가로 스크롤 + 항목 열 고정, 누르는 요소 44px (6) |
| 7 | 긴 문장 | 7A 3줄 말줄임 + 눌러 펼치기 (3.4) |

### 제외 범위 (검토 중 미룬 것)

- 시안 이미지 생성: gstack designer에 OpenAI API 키가 없어 만들지 못했다. 사용자가 보낸 시안 9장을 시각 기준으로 쓴다.
- 6·7단계 화면, Context 거리 지도, 용어 빈도, 인물 이미지, 여정 %: 기획 승인 범위 밖.

### 이미 있는 것 (재사용)

- 디자인 토큰 `frontend/src/styles/tokens.css` (`--paper`, `--line`, `--sunken`, `--danger(-soft)`, `--warning(-soft)`, `--success`, `--blue`, `--type-*`)
- 컴포넌트 `components/ds` (Button, Badge, Card, Tabs, Checkbox, Skeleton, Select), `ds-tbl` 표 스타일
- `persona/GradeMark`(관측/추론), `ProvisionalBadge`, `personaView`의 `zoneName`·`formatMetric`·`foldColumns`
- `usePolling`, `displayError` 오류 처리

### 후속 할 일

- **DESIGN.md 작성**: 6·7단계 시안 작업 전에 `/design-consultation`으로 색·표·차트·카드 사용 규칙을 문서화한다. 이번 검토가 토큰만으로 결정해서, 같은 결정을 다음 작업에서 반복하지 않기 위함이다.

### 완료 요약

```
+====================================================================+
|         DESIGN PLAN REVIEW — COMPLETION SUMMARY                    |
+====================================================================+
| System Audit         | DESIGN.md 없음, tokens.css 기준, UI 범위 있음 |
| Step 0               | 6/10, 7개 관점 전부 + 카드 시안 1개(생성 불가) |
| Pass 1  (Info Arch)  | 6/10 → 9/10 after fixes                     |
| Pass 2  (States)     | 5/10 → 9/10 after fixes                     |
| Pass 3  (Journey)    | 6/10 → 9/10 after fixes                     |
| Pass 4  (AI Slop)    | 7/10 → 9/10 after fixes                     |
| Pass 5  (Design Sys) | 6/10 → 8/10 after fixes (DESIGN.md 부재)     |
| Pass 6  (Responsive) | 5/10 → 8/10 after fixes                     |
| Pass 7  (Decisions)  | 7 resolved, 0 deferred                      |
+--------------------------------------------------------------------+
| NOT in scope         | written (2 items)                           |
| What already exists  | written                                     |
| TODOS.md updates     | 1 item (설계 문서 후속 할 일에 기록)          |
| Approved Mockups     | 0 generated (API 키 없음), 0 approved        |
| Decisions made       | 7 added to plan                             |
| Decisions deferred   | 0                                           |
| Overall design score | 5/10 → 8/10                                 |
+====================================================================+
```

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Outside Review | — | Independent 2nd opinion | 0 | skipped | 사용자가 외부 검토 건너뛰기 선택 |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 0 | — | — |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | clean | score: 5/10 → 8/10, 7 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **OUTSIDE COVERAGE:** design 단계 외부 검토 skipped (사용자 선택). 시안 생성 unavailable (OpenAI API 키 없음).
- **VERDICT:** Design Review 완료(8/10, 미해결 결정 없음, DESIGN.md 부재로 Pass 5 8점). eng review required.

NO UNRESOLVED DECISIONS
