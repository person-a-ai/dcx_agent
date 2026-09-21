# 목업 — DCX STEP 07~11

## 위치

목업 소스는 제품 소스와 분리해 `docs/development/dcx-step07-11/mockup/`에 있다. Design 캔버스 아티팩트의 게시 루트가 그곳이라 이동하지 않았다.

- **아티팩트** https://claude.ai/artifact/8mb7VfY8ZyX2s7w8xpbJTK — 페이지 `Person A` (15 아트보드)
- **소스** `docs/development/dcx-step07-11/mockup/parts/*.body.html` (내용) + `docs/development/dcx-step07-11/mockup/_shell.css` (Person A 토큰 — **수정본** 기준)
- **빌드** `cd docs/development/dcx-step07-11/mockup && node build.mjs && node preview.mjs`

## 디자인 기준 — 수정본 적용 (2026-09-21)

`_shell.css`는 handoff 번들의 `tokens/*.css`(seed 산물)가 아니라 **`펄슨에이_디자인규칙_수정본`** 을 따른다.
충돌하는 값은 수정본이 이긴다 — 근거는 번들의 `CLAUDE.md` 우선순위 항. 자세한 대조표는 루트 `DESIGN.persona.md` §0.

- 토큰: Person Blue `#38B6F9` · Empathy White `#F8FCFF` · sidebar 224 · Card radius 14 / padding 24 · 역할 스케일 7단계(insight 800)
- 블루 2색 역할 분리: `persona-blue` = 신호(채움·선택·차트, 위 글자는 ink) / `action` = 조작(링크·버튼·포커스)
- 폰트: Pretendard 400/500/600/700 + **800(ExtraBold)** — 수정본의 dominant insight용. `assets/`는 gitignore 대상이라 새 클론에서는 다시 만들어야 한다 (번들 OTF → woff2 변환)
- 스킬: `/person-a-design` (`~/.claude/skills/person-a-design/`)

**수정본 구조가 들어간 화면은 STEP 07~11 일곱 개다.** 앞단(00~06)은 토큰 정합만 되어 있고,
"사람의 변화" 문장·근거 블록·다음 행동 종결은 넣지 않았다 — 개발 범위가 07~11이고 앞단은 원본을 임시로 쓰기 때문이다.

각 07~11 화면의 상단은 다음 순서를 지킨다:
eyebrow → `insight.display`(화면당 **하나**, 800) → 해석 → 다른 가능성 → 근거(표본·기간·source·`신뢰도 n/3`·원문) → **다음 행동**

## 화면 15개

| 파일 | 화면 | 이번 범위 |
|---|---|---|
| `Main` | 00 세션 | 참조 |
| `Declare` | 01·02 입력 선언 | **수정** — `known_insights` 입력 신설 |
| `Keywords` | 03 키워드 설계 | 참조 |
| `Crawling` | 04 데이터 수집 | **수정** — doc_id · author_hash |
| `Preprocess` | 05 전처리 · 임베딩 | **수정** — Pinecone 메타 확장 |
| `Training` | 06-A 모델 학습 · 캘리브레이션 | **수정** — alpha · run 사이드카 |
| `Labeling` | 06-B 근거 판정 | **수정** — decision · label |
| `Clustering` | 07 군집 → Touch Point | **신규 구현** |
| `Persona` | 08 SNA → 페르소나 | **신규 구현** |
| `Evidence` | 09 LDA → 근거 수집 | **신규 구현** |
| `ContextMap` | 10-A Customer Action Map | **신규 구현** |
| `Opportunity` | 10-B 기회 영역 | **신규 구현** |
| `Concept` | 11-A 인사이트 도출 | **신규 구현** |
| `Design` | 11-B 경험 디자인 컨셉 | **신규 구현** |
| `Admin` | 프롬프트 · 파이프라인 상수 | **신규 구현** |

`Liquid Glass (이전안)` 페이지는 동결 상태다. Person A 시스템(Light 단일 테마 · 정적 카드 그림자 금지)과 충돌해 갱신을 멈췄고, 기록으로만 남겼다.

## 읽는 법

각 화면 아래 `1.0 대비 변경점` 스트립의 번호가 화면 안의 동그란 핀과 짝을 이룬다.
`치환` AS-IS가 있고 대체된다 · `신설` AS-IS 없음 · `유지` 기존 확정 재확인 · `미결` 답이 필요한 것

## 상태

정적 아트보드다. **인터랙션은 별도 세션에서 부여한다** (클릭·입력·단계 전환).
