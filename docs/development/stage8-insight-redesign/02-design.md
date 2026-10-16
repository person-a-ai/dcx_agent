# 인사이트(8-E) 화면 재구성 · 설계

기준 문서: `01-brainstorm.md` (제품 승인 "인사이트 화면 기획 승인"). 기준 커밋: main `87eb794`.

## 1. 동작 요약

1. 인사이트 도출(`insight.derive`)과 인사이트 목록 채팅 수정(`insight.edit`)이 기존 필드에 더해 `headline`·`statements`·`hashtags`·`flow`를 낸다. 코드가 형식과 Context ID를 검사한다.
2. `recompute`가 인사이트마다 Context 보기 정보(`contexts`)와 세션 요약(`summary`)을 계산해 저장한다. 숫자·축·차원·반례는 모두 코드가 채운다.
3. 조회 API는 저장된 값을 돌려주고, 새 필드가 없는 예전 판은 근거 묶음·카드로 보기 정보를 채워 돌려준다(축은 비움).
4. 화면은 인사이트 하나만 보여 준다. 위에서 아래로 상단 바 → 헤더 → (레이더 | Opportunity Score) → 흐름 카드 → insight-chat → 컨셉 순서다.

## 2. 데이터 구조

### 2.1 LLM 출력 스키마 (`backend/app/persona/insights.py`)

```python
class FlowStep(BaseModel):
    context_id: Text
    text: Text                     # 카드 문장, 40자 안팎 권장(프롬프트), 길이 검사는 1~80자

class InsightItem(BaseModel):     # 기존 필드 유지
    id: Text; title: Text; pain_point: Text
    context_ids: list[Text] = Field(min_length=1)
    known_ki_id: Text | None
    headline: Text                 # 따옴표 없이 저장. 화면이 따옴표를 붙인다.
    statements: list[Text] = Field(min_length=2, max_length=2)
    hashtags: list[Text] = Field(min_length=2, max_length=4)   # '#' 없이 저장
    flow: list[FlowStep] = Field(min_length=1)
```

`DeriveOut.items: list[InsightItem]`는 그대로다. 채팅 수정도 같은 `DeriveOut`을 쓴다.

### 2.2 공통 검사 함수 `validate_items(items, available) -> list[dict]`

지금 `derive()`와 `chat.edit()`에 따로 있는 검사를 한 함수로 모은다. 실패하면 `ValueError`.

- 개수 `INSIGHT_RANGE`, id 고유, `context_ids` ⊆ `available`, `context_ids` 중복 없음 (기존 규칙)
- `flow`의 `context_id` ⊆ 그 인사이트 `context_ids`, 중복 없음, 개수 `min(2, len(context_ids))` 이상 `len(context_ids)` 이하
- `hashtags`: 앞의 `#`·공백 제거 후 빈 값 없음, 중복 없음 (정리한 값을 돌려준다)
- `headline`: 앞뒤 따옴표(`"` `“` `”` `'`) 제거 후 빈 값 없음

`derive()`는 실패 시 기존처럼 `payload['retry']` 문구를 넣어 1회 재시도한다. 재시도 문구에 새 규칙을 덧붙인다.

### 2.3 코드 계산 필드 (`recompute`가 인사이트마다 저장)

```text
item.contexts: [
  { context_id, short: "C1",            # context_id 마지막 '-' 뒤
    persona_id, persona_name,           # 근거 묶음 PersonaBlock.persona_evidence
    context_name,
    odi: float | null,                  # metrics.odi
    axis: "Computed"|"Connected"|"Shared"|null,   # 이 Context 중심점의 radar raw 최댓값 축
    dim: "Sense"|"Feel"|"Think"|"Act"|"Relate"|"Outcome"|null,  # 지지 근거 tags 최다 차원
    counter: bool,                      # flags에 counter_context
    pain_point: str | null }            # 카드 contexts[].pain_points[0].text
  ]                                     # 순서 = item.context_ids
```

- `axis`: `radar({cid: centroid}, {cid: 1}, axes)['raw']`의 최댓값 축. 동률이면 `RADAR_AXES` 순서(Computed→Connected→Shared). 중심점이 영벡터라 모두 0이면 null.
- `dim`: 그 Context의 `evidence`(지지 근거만, 반례·희귀 제외) 각 항목 `tags` 목록을 센다. 동률이면 Sense→Feel→Think→Act→Relate→Outcome 순서. 지지 근거가 없거나 태그가 없으면 null.
- 세션 요약은 각 항목에 반복 저장하지 않고 조회 응답에서 계산한다(2.4).

### 2.4 조회 응답 `GET /insight/{sid}` (`backend/app/routers/stage8.py`)

기존 키(`insights`, `concepts`, `bars`, `radar`, `worker`)는 그대로 두고 아래를 더한다.

```text
summary: {
  context_odi_mean: float | null,   # 근거 묶음 전체 Context ODI 평균 (null 제외)
  radar_mean: {Computed, Connected, Shared} | null   # 현재 판 인사이트 radar.raw 축별 평균
}
```

- `insights.items[*].contexts`가 없으면(예전 판) `insights.context_view(package, cards, item)`으로 채우고 `axis`는 null로 둔다. 임베딩을 부르지 않는다.
- 근거 묶음이 없으면(`PackageMissing`) `contexts`는 `context_ids`만 담은 최소 행(`short`만 채움)으로, `summary.context_odi_mean`은 null로 돌려준다. 오류로 만들지 않는다.
- `bars`(인사이트 간 막대)는 화면에서 더 쓰지 않지만 `targets`로 첫 선택 인사이트를 정하므로 유지한다.

### 2.5 프론트 타입 (`frontend/src/lib/types.ts`)

`InsightItem`에 선택 필드 `headline?`, `statements?`, `hashtags?`, `flow?: {context_id; text}[]`, `contexts?: InsightContextView[]`를 더하고, `InsightResponse`에 `summary?: {context_odi_mean: number | null; radar_mean: RadarRaw | null}`를 더한다. 모두 선택 필드라 예전 응답도 타입 오류가 없다.

## 3. 프롬프트

- `prompts/derive.v1.md` → `prompts/derive.v2.md` 새 파일. 기존 규칙에 추가:
  - `headline`: 사용자 말투의 한 줄(20자 안팎), 따옴표 없이.
  - `statements`: 정확히 2개. 1번은 원하는 것, 2번은 막히는 점·바라는 해결. 각 1~2줄.
  - `hashtags`: 2~4개, `#` 없이, 명사형 짧은 단어.
  - `flow`: 그 인사이트 `context_ids` 중에서 경험이 이어지는 순서로 고르고, 카드 문장은 그 Context의 pain point·근거 인용을 바탕으로 사용자 1인칭 한 문장. 새 원문을 지어내지 않는다.
  - 숫자·축·차원·반례 표시는 만들지 않는다(코드 소유).
- `prompts/edit.v1.md` → `prompts/edit.v2.md`: insights 대상은 `derive.v2`와 같은 스키마로 답하고, `context_ids`를 바꾸면 `flow`도 맞춰 고치라는 문장을 더한다.
- v1 파일은 지우지 않는다(과거 실행 재현용). 코드는 v2만 읽는다.
- 테스트 fixture `backend/tests/fixtures/llm/insight.derive*.json`, `insight.edit.json`에 새 필드를 더한다.

### 3.1 채팅 대상 인사이트 (디자인 검토 4A)

- `POST /insight/{sid}/chat` 본문에 선택 필드 `focus_id: str | None`을 더한다. `target='insights'`일 때만 쓰고, 현재 판에 없는 id면 무시한다(오류로 만들지 않음).
- `chat.edit`은 `payload['focus_id']`를 넣고, `edit.v2.md`에 "사용자가 '이 인사이트'·'여기'라고 하면 focus_id 인사이트를 뜻한다. 다른 인사이트는 요청이 명시할 때만 바꾼다"를 더한다.
- 프론트 `InsightChatRequest`에 `focus_id?`를 더하고, 채팅 띠 입력창 위에 "Insight n에 대해 수정 요청"을 표시한다. 대상이 `concept:*`이면 이 표시 대신 "선택 컨셉 수정".

## 4. 화면 구조 (`frontend/src/components/persona/`)

`InsightScreen.tsx`는 데이터 불러오기·폴링·mutate(지금 로직 유지)만 맡고, 그리기는 새 컴포넌트로 나눈다. 순수 계산은 `insightView.ts`로 분리해 단위 테스트한다.

| 파일 | 역할 |
|---|---|
| `insightView.ts` (새) | `toInsightView(item, summary)` → `{headline, statements, hashtags, personas, flow, bars, legacy}`. 대체 규칙(4.1)을 여기서 적용 |
| `InsightTopBar.tsx` (새) | 제목 `8-E 인사이트 도출 › 인사이트별 Pain Point`, `인사이트 N개 · 대화형`, `‹ Insight n / N ›`, 확정 토글, `인사이트 도출` 버튼(목록이 비었을 때) |
| `InsightHeader.tsx` (새) | (이미지·아이콘 자리 없음, 디자인 검토 6A) `Insight n` 배지 + “headline”, 번호 문장 2개, 해시태그, 기여 페르소나, Known Insight 배지, 예전 판 안내 |
| `Radar.tsx` (고침) | 이 인사이트 raw 실선 + `radar_mean` 점선. 축 이름(Computed/Connected/Shared) 아래 raw 값. 백분위는 `aria-label`과 `title`에 둔다. 범례 `— Insight n · --- 평균(전체 인사이트)` |
| `OpportunityBars.tsx` (다시 씀) | 세로 막대. x축 라벨 2줄(`C1` / `페르소나축약-C1`), 막대 위 값, `context_odi_mean` 점선과 `평균 x.x` 라벨. ODI null은 막대 없이 `값 없음` |
| `InsightFlow.tsx` (새) | 흐름 카드 행. 카드: 문장 / `페르소나축약 - C1 - dim` + axis 배지. 반례 카드는 `--danger` 테두리와 `⚠ 반례`. 카드 사이 `→` (좁은 화면 `↓`) |
| `InsightChatBar.tsx` (새) | 채팅 대상 선택(인사이트 목록 / 선택 컨셉), 추천 질문 칩 2개, 입력·전송(ChatPanel), `대화 기록 n` 버튼 → 판 목록 펼치기, 안내 문구 |
| (칩 문구, 디자인 검토 10A) | `insightView.ts`가 현재 인사이트로 채운다. ① "이 인사이트 문장을 더 짧게 다시 써줘" ② "흐름에서 {첫 카드 라벨}과 {마지막 카드 라벨} 순서를 바꿔줘" (라벨 = 흐름 카드 메타의 `페르소나축약-C1`). 흐름 카드가 1개면 ②는 숨긴다. LLM을 부르지 않는다 |
| `ChatPanel.tsx` (작게 고침) | 선택 prop `suggestions?: string[]` 추가. 칩을 누르면 입력창을 채우고 포커스. 다른 화면은 prop을 안 주므로 동작 같음 |
| `ConceptDetail` | `InsightScreen.tsx`에서 `InsightConcept.tsx`로 옮김. 채팅 아래 `컨셉` 영역에서 지금처럼 만들기·상세 |

### 4.1 대체 규칙 (예전 판, `insightView.ts`)

| 값 없음 | 대체 |
|---|---|
| `headline` | `title` |
| `statements` | `pain_point`를 한 문장 블록으로(번호 1개) |
| `hashtags` | 숨김 |
| `flow` | `context_ids` 순서, 문장은 `contexts[].pain_point` → 없으면 `context_name` |
| `contexts[].axis` | 배지 숨김 |
| `contexts` 자체 | `short`만으로 카드·막대 라벨 |

`legacy = !headline || !statements || !flow`이면 헤더 맨 아래에 한 줄 "예전 방식으로 만든 인사이트입니다. 다시 도출하면 제목·문장·흐름이 채워집니다."와 `<details>` "자세히"를 둔다. 펼치면 "다시 도출하면 확정과 컨셉이 초기화됩니다."가 보인다 (디자인 검토 3A). 다시 도출 버튼은 이번 범위에 넣지 않는다.

- 페르소나 축약: `persona_name`의 마지막 어절(공백 기준). 예: "귀로 건강 재는 러너" → "러너". 같은 인사이트 안에서 두 페르소나의 축약이 같으면 둘 다 전체 이름을 쓴다. 전체 이름은 `title`로 보인다.
- 기여 페르소나: `contexts` 순서대로 `persona_name` 중복 제거, ` · `로 잇는다.

## 5. 레이아웃·반응형·접근성

### 5.0 정보 위계와 첫 화면 (디자인 검토 1A)

1280×800에서 스크롤 없이 상단 바 → 헤더 → 레이더|Opportunity Score → 흐름 카드까지 보인다. 채팅 띠와 컨셉은 그 아래(한 번 스크롤)에 둔다. 이를 위해 레이더·막대 영역 높이는 240px, 헤더는 최대 180px(문장 2줄씩 기준)로 맞춘다.

```text
┌ 상단 바 (48px) ─ 8-E 인사이트 도출 › 인사이트별 Pain Point · 인사이트 N개 · 대화형 ── [확정] ‹ Insight n/N › ┐
├ 헤더 (≤180px) ─ [Insight n] “headline”  ① 문장  ② 문장  #태그 #태그  기여 페르소나: … ─────────────────────┤
├ 레이더 (5) ───────────────┬ Opportunity Score (7) ─────────────────────────── 240px ──────────────────────┤
├ 흐름 카드: [C1 카드] → [C2 카드] → [C9 카드] → [C3 반례 카드] ─────────────── ~110px ── 첫 화면 끝 ─────┤
├ insight-chat 띠: 대상 선택 · 칩 · 입력/전송 · 대화 기록 n · 안내 ──────────────────────────────────────────┤
└ 컨셉: 컨셉 만들기 / 컨셉 상세 ──────────────────────────────────────────────────────────────────────────┘
```

### 5.0.1 표면 구조 (디자인 검토 5A)

- 상단 바는 패널 밖. 헤더~채팅 띠는 바깥 `ds-card` **하나**(`--r-card`, `--line` 1px, 그림자 없음) 안에 둔다.
- 레이더와 Opportunity Score는 `--line` 테두리 하나(`--r-input`) 안에서 세로 구분선으로 나눈다. 각 영역을 따로 카드로 감싸지 않는다.
- 카드 모양은 흐름 카드(항목 하나 = Context 하나)와 채팅 띠(테두리 `--line`)에만 쓴다. 헤더·레이더·막대는 카드가 아니다.
- 컨셉은 패널 밖 아래 구간으로 두고 `--type-section` 제목 "컨셉"으로 구분한다.

- **1280px 이상**: 상단 바 한 줄. 헤더(글 전체 폭). 레이더와 Opportunity Score를 2열(5:7). 흐름 카드 한 줄(카드 4개까지 가로, 넘치면 줄바꿈). 채팅 띠는 칩(왼쪽) · 입력(오른쪽) 2열.
- **768~1279px**: 레이더·막대 2열 유지, 흐름 카드는 2개씩 줄바꿈, 채팅 띠는 칩 위·입력 아래.
- **767px 이하**: 모두 1열. 흐름 화살표는 `↓`.
- **키보드**: `‹` `›` 버튼은 `aria-label="이전 인사이트"/"다음 인사이트"`. 처음·끝에서 비활성. 두 버튼을 `role="group" aria-label="인사이트 넘기기"`로 묶고, **그 묶음에 포커스가 있을 때만** 좌우 화살표 키로 넘긴다(화면 전역 키 처리 없음, 디자인 검토 8A). 현재 위치는 `aria-live="polite"`.
- **스크린리더**: 레이더·막대 `role="img"`에 축·값 요약 `aria-label`. 흐름은 `<ol aria-label="Context 흐름">`. 반례는 색만이 아니라 텍스트 "반례"로 구분.
- **터치 영역**: `‹` `›`, 확정 토글, 추천 질문 칩, `대화 기록 n`, 전송 버튼은 최소 44×44px(보이는 크기가 작으면 padding으로 확보). 해시태그는 버튼이 아니므로 제외 (디자인 검토 8A).
- **확정 토글**: `<button aria-pressed>` "확정됨/확정하기". 읽기 전용·판 미리보기 중에는 비활성.
- 색·글자는 `frontend/src/styles/tokens.css`의 기존 토큰만 쓴다. 새 토큰을 만들지 않는다 (디자인 검토 7A).

### 5.1 토큰 매핑 (디자인 검토 7A)

| 요소 | 글자 | 색 |
|---|---|---|
| 상단 바 제목 `8-E 인사이트 도출 › 인사이트별 Pain Point` | `--type-card` (18px) | `--action` / 구분자 `--sub` |
| `인사이트 N개 · 대화형`, `Insight n / N` | `--type-label` (13px) | `--ink-strong`, 바탕 `--sunken` |
| `Insight n` 배지 | `--type-badge` (12px) | 글자 `--paper`, 바탕 `--action`, `--r-input` |
| headline (따옴표 포함) | `--type-section` (24px/34px) | `--ink-strong` |
| 번호 문장 | `--type-body` (15px/24px) | `--ink-strong`, 번호 원 `--action` 바탕 + `--paper` 글자 |
| 해시태그 | `--type-badge` | 글자 `--action`, 바탕 `--action-soft` |
| 기여 페르소나 | `--type-label` 라벨 + `--type-body` 값 | 라벨 `--ink-strong`, 값 `--ink` |
| 영역 제목(경험 차원 레이더, Opportunity Score, insight-chat) | `--type-label` | `--action` |
| 레이더 실선·면 / 평균 점선 | 축 이름 `--type-label`, 값 `--type-caption` | 선 `--action`, 면 `--action-soft`, 점선 `--line-strong` |
| 막대 / 평균선 / 값 | 값 `--type-label`, 축 라벨 `--type-caption` | 막대 `--action`, 평균선 `--line-strong` 점선 |
| 흐름 카드 문장 / 메타 | 문장 `--type-body`, 메타 `--type-caption` | 테두리 `--line`, 문장 `--ink-strong`, 메타 `--sub` |
| 축 배지 (Computed/Connected/Shared) | `--type-badge` | `--blue-soft` 바탕 + `--blue-deep` 글자 |
| 반례 카드 | 같음 | 테두리 `--danger`, `⚠ 반례` 배지 `--danger-soft` 바탕 + `--danger` 글자 |
| 빈 상태 caption | `--type-caption` | `--sub` |
| 카드 사이 화살표 `→`/`↓` | — | `--line-strong` |

흐름 카드 안에는 방향·색 아이콘을 두지 않는다. 색으로 의미를 나타내는 것은 반례(`--danger`) 하나뿐이다 (디자인 검토 9A).

## 6. 상태와 실패 처리

| 상태 | 화면 |
|---|---|
| 불러오는 중 | 상단 바만, 본문 "불러오는 중…" (지금과 같음) |
| 인사이트 없음 | "페르소나를 바탕으로 인사이트를 도출하세요." + 상단 바 `인사이트 도출` 버튼 |
| 도출·수정 처리 중 | 상단 바 아래 `role=status` "처리 중…", 입력·토글·넘김 외 조작 비활성 |
| 도출·컨셉 실패/중단 | 지금 알림과 `다시 시도`/`이어서 진행` 그대로 |
| 조회 실패 | 지금 알림과 `다시 불러오기` 그대로 |
| 판 미리보기 | 상단 바 아래 "판 n 보기 · 현재 판으로". 미리보기 판의 인사이트로 넘김이 동작하고, 확정·채팅 비활성 |
| 선택한 인사이트가 사라짐(수정·되돌리기 뒤) | 첫 인사이트로 이동 |
| 채팅 수정 실패 | 지금 `FAILURE_COPY` 응답 그대로 |
| LLM 새 필드 검사 실패 | 도출: 1회 재시도 후 지금 실패 문구. 수정: `FAILURE_COPY` |

### 6.1 영역별 부분 상태 (디자인 검토 2A)

| 영역 | 값 있음 | 일부 없음 | 전부 없음 | 처리 중 |
|---|---|---|---|---|
| 헤더 | 4절 그대로 | `hashtags` 없음 → 태그 줄 숨김. 기여 페르소나 못 찾음 → 그 줄 숨김 | 예전 판 → 4.1 대체 + 예전 판 안내 | 그대로 보이고 확정 토글만 비활성 |
| 레이더 | 실선 + 평균 점선 | `radar_mean` 없음 → 점선과 범례 "평균" 숨김. 축 값 null → 그 축 0으로 그리고 축 아래 "—" | 레이더 자리에 "경험 차원 값이 없습니다" (회색 caption, 영역 높이 유지) | 그대로 |
| Opportunity Score | 막대 + 평균선 | ODI null인 Context → 막대 없이 라벨 아래 "값 없음". 평균 null → 평균선 숨김 | 모든 ODI null → 축 없이 "이 인사이트의 Context에 ODI 값이 없습니다" | 그대로 |
| 흐름 카드 | 4절 그대로 | `axis` null → 축 배지 숨김. `dim` null → "근거 부족". `pain_point`·`text` 없음 → `context_name` | `contexts`·`flow` 모두 없음 → `context_ids` 짧은 번호만 담은 카드 | 그대로 |
| 채팅 띠 | 입력·칩·대화 기록 | 대화 기록 0 → "대화 기록 0" 버튼 비활성 | — | 입력·칩·전송 비활성, 전송 버튼 "처리 중…" |
| 컨셉 | 컨셉 상세 | 컨셉 `outdated` → "인사이트가 바뀌어 컨셉을 다시 만들어야 합니다" + 다시 만들기 | 컨셉 없음 → "선택 컨셉 만들기" 버튼 | 버튼 비활성 |

빈 상태 문구는 모두 영역 안 caption(`--type-caption`, `--sub`)으로 두고 영역 높이를 유지해 넘길 때 화면이 흔들리지 않게 한다.

선택 인사이트 초기값: `bars.targets[0]` → `default_target` → 첫 인사이트 (지금 규칙 유지). 넘김은 `insights.items` 순서.

## 7. 권한

바뀌지 않는다. 쓰기 API(도출·채팅·되돌리기·확정·컨셉)는 지금처럼 `writable=True` 세션만 허용한다. 읽기 전용(`readonly`)·과거 버전에서는 넘김·레이더·막대·흐름·판 목록 보기만 동작한다.

## 8. 바뀌는 파일 (소유권 초안)

- 백엔드: `backend/app/persona/insights.py`, `backend/app/persona/chat.py`(검사 함수 사용으로 교체), `backend/app/routers/stage8.py`(summary·예전 판 보기·`focus_id`), `backend/app/persona/prompts/derive.v2.md`·`edit.v2.md`(새), `backend/tests/persona/test_insights.py`, `backend/tests/persona/test_chat.py`, `backend/tests/fixtures/llm/insight.*.json`, 라우터 테스트 파일
- 프론트: `frontend/src/lib/types.ts`, `frontend/src/components/persona/{InsightScreen,Radar,OpportunityBars}.tsx`, 새 `{insightView.ts,InsightTopBar,InsightHeader,InsightFlow,InsightChatBar,InsightConcept}.tsx`, `frontend/src/components/ChatPanel.tsx`, 관련 테스트(`insight.test.ts`, `InsightScreen.qa.test.ts`, 새 `insightView.test.ts`)

## 9. 테스트 방향

- 백엔드 단위: `validate_items` 경계(statements 1·3개, flow 밖 ID, flow 개수, Context 1개 인사이트, 해시태그 `#` 정리, 따옴표 정리), `dim`·`axis` 동률·빈 값, `context_view` 예전 판, `summary` 평균(null 제외), 도출 재시도 1회, 채팅 수정 검사 실패 → `FAILURE_COPY`.
- 프론트 단위: `toInsightView` 대체 규칙 전부, 페르소나 축약 충돌, 막대 null/0 구분, 넘김 경계(처음·끝 비활성), 반례 카드 텍스트, 칩 클릭 시 입력 채움.
- 브라우저 QA: 실제 세션에서 새로 도출한 판과 예전 판 둘 다. 1440·768·375px. 키보드 넘김.

## 10. 되돌리기

프롬프트 v1 파일과 저장 형식 하위 호환(새 필드는 추가만)을 유지하므로, 브랜치를 되돌리면 예전 화면이 새 필드가 있는 판도 그대로 읽는다(모르는 필드는 무시).

## 11. 디자인 검토 결과 (plan-design-review)

기준: 사용자 시안(8-E 인사이트별 Pain Point), 새 시안 생성 생략(검토 범위 D1-A). DESIGN.md 없음 → `frontend/src/styles/tokens.css`와 PR #34 페르소나 화면 컴포넌트를 디자인 시스템으로 삼음.

### 결정 목록

| # | 결정 | 반영 위치 |
|---|---|---|
| 1A | 1280×800 첫 화면에 상단 바~흐름 카드, 채팅·컨셉은 그 아래 | 5.0 |
| 2A | 영역별 부분 상태 표 | 6.1 |
| 3A | 예전 판 안내 한 줄 + "자세히" 펼치기 | 4.1 |
| 4A | 채팅 요청에 `focus_id`, 입력창 위 대상 표시 | 3.1 |
| 5A | 바깥 패널 하나 + 구획선, 카드는 흐름 카드·채팅 띠만 | 5.0.1 |
| 6A | 헤더 이미지·아이콘 자리 없음 (기획 4절 "자리표시"를 대체) | 4 표 |
| 7A | 글자·색 토큰 매핑, 없는 `--accent` 제거 | 5.1 |
| 8A | 화살표 키는 넘김 버튼 묶음 포커스 시만, 버튼류 44px | 5 |
| 9A | 흐름 카드 안 아이콘 없음, 색 의미는 반례 하나 | 5.1 |
| 10A | 칩 문구 틀 2개를 현재 인사이트 라벨로 채움 | 4 표 |

### 범위 밖 (NOT in scope)

- 대표 이미지: 데이터 없음(기획 9절).
- `⋯` 메뉴 새 기능: 기획 9절. 기존 기능 이동만.
- 새 시안 변형 생성: 사용자 시안이 기준(D1-A).
- 컨셉(8-F) 화면 재구성: 기획 9절. 위치만 패널 아래로 옮김.

### 이미 있는 것 (재사용)

- 토큰: `--type-*` 타입 스케일, `--action`/`--action-soft`, `--danger`/`--danger-soft`, `--blue-soft`/`--blue-deep`, `--line`/`--line-strong`, `--r-card`/`--r-input`.
- 컴포넌트: `ds-card`, `ds-badge`, `Button`(ds), `ChatPanel`(선택 prop만 추가), `RevisionList`, `JourneyTable`, `ProvisionalBadge`, `personaView.formatMetric`.
- 패턴: PR #34 페르소나 화면의 Opportunity 막대·라벨 겹침 처리, 44px 터치 영역 처리(RV7~RV9).

### TODOS.md

새 미뤄 둔 디자인 부채 없음. 대표 이미지는 기획 단계에서 이미 범위 밖으로 결정됨.

### 구현 작업 (검토에서 나온 것)

- [ ] **D1 (P1)** — 레이아웃 — 첫 화면 높이 예산(헤더 ≤180px, 레이더·막대 240px)과 패널 구조(5.0, 5.0.1) 구현. 검증: 1280×800 스크린샷에서 흐름 카드 하단이 보임.
- [ ] **D2 (P1)** — 상태 — 6.1 표 전부와 예전 판 안내(4.1). 검증: `insightView.test.ts` + 예전 판 세션 브라우저 QA.
- [ ] **D3 (P1)** — 채팅 — `focus_id` API·프롬프트·입력창 대상 표시(3.1). 검증: `test_chat.py`에 focus_id 전달·무시 케이스.
- [ ] **D4 (P2)** — 토큰 — 5.1 매핑 적용, 임의 px·색 없음. 검증: 린트 + 코드 리뷰에서 하드코딩 색 검색.
- [ ] **D5 (P1)** — 접근성 — 넘김 그룹 키 처리, 44px 터치 영역(5). 검증: 키보드 QA, 계산된 크기 확인.
- [ ] **D6 (P2)** — 칩 — 10A 틀 문구, 흐름 카드 1개면 ② 숨김. 검증: `insightView.test.ts`.

### 완료 요약

```
  +====================================================================+
  |         DESIGN PLAN REVIEW — COMPLETION SUMMARY                    |
  +====================================================================+
  | System Audit         | DESIGN.md 없음, tokens.css 사용 / UI 범위 큼 |
  | Step 0               | 7/10, 위계·밀도·문구 빈칸                    |
  | Pass 1  (Info Arch)  | 6/10 → 9/10 after fixes                      |
  | Pass 2  (States)     | 7/10 → 9/10 after fixes                      |
  | Pass 3  (Journey)    | 7/10 → 9/10 after fixes                      |
  | Pass 4  (AI Slop)    | 7/10 → 9/10 after fixes                      |
  | Pass 5  (Design Sys) | 6/10 → 9/10 after fixes                      |
  | Pass 6  (Responsive) | 7/10 → 9/10 after fixes                      |
  | Pass 7  (Decisions)  | 2 resolved, 0 deferred                       |
  +--------------------------------------------------------------------+
  | NOT in scope         | written (4 items)                            |
  | What already exists  | written                                      |
  | TODOS.md updates     | 0 items proposed                             |
  | Approved Mockups     | 0 generated (사용자 시안 기준)               |
  | Decisions made       | 10 added to plan                             |
  | Decisions deferred   | 0                                            |
  | Overall design score | 6/10 → 9/10                                  |
  +====================================================================+
```

각 관점이 10이 아닌 이유: 실제 화면에서 높이 예산과 라벨 겹침은 브라우저 QA로만 확인할 수 있다.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Outside Review | — | Independent 2nd opinion | 0 | skipped (user declined) | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 0 | — | — |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | clean | score: 6/10 → 9/10, 10 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **OUTSIDE COVERAGE:** design phase, outside voices skipped by user choice; no external review completed.
- **VERDICT:** DESIGN CLEARED — eng review required (계획 단계에서 `plan-eng-review` 수행 예정).

NO UNRESOLVED DECISIONS
