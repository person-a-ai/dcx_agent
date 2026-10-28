# 페르소나 Context 비교 표 · 지도 세로 배치 — 구현 · QA 계획

기획 [01](01-brainstorm.md) · 설계 [02](02-design.md) 승인(2026-10-27). 구현 담당: Codex(`codex:codex-rescue`, 쓰기 모드). Claude는 위임·리뷰·QA만 맡는다.

## 0. 작업 환경
- 기획 자료는 `origin/main`(fa71e31)에서 만든 브랜치 `docs/persona-ccm-stack`에 커밋한다. 그 HEAD에서 worktree `/Users/tech/code/dcx_agent-persona-ccm-stack`, 브랜치 `feature/persona-ccm-stack`을 만든다(`development-harness worktree`).
- 준비: `npm --prefix frontend ci`, `cd backend && /opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt -c constraints.txt`.
- 기준 검사: `harness.config.json`의 4개 명령(pytest · lint · build · vitest)을 먼저 돌려 기존 실패를 기록한다.

## 1. Task

| ID | 내용 | 담당 파일 | 의존 | AC |
|---|---|---|---|---|
| T1 | 카드 비교 영역 1열 + 카드 지도 최대 720px | `frontend/src/components/persona/persona.css`, `frontend/src/components/persona/components.test.ts`(F3만) | — | AC1, AC2, AC4 |

### T1 세부
- RED: `components.test.ts`의 F3을 다음으로 바꾸고 실패를 확인한다.
  - 이름: `F3 stacks the card comparison table above a width-capped map`
  - `css`가 `/\.persona-comparison-layout\{grid-template-columns:minmax\(0,1fr\) minmax\(420px,0\.8fr\)\}/`와 맞지 않아야 한다(`not.toMatch`).
  - `css`에 `.persona-comparison-layout>.persona-map-surface{max-width:720px}`가 들어 있어야 한다(`toContain`).
  - `.persona-map-layout{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}`는 그대로 남아 있어야 한다(`toContain`).
  - 명령: `npm --prefix frontend test -- components` → F3 실패가 예상 결과.
- GREEN: `persona.css`
  - `@media(min-width:1280px)` 블록에서 `.persona-comparison-layout{grid-template-columns:minmax(0,1fr) minmax(420px,0.8fr)}` 줄을 지운다(블록과 `.persona-map-layout` 줄은 남긴다).
  - `.persona-map-surface{min-width:0;box-shadow:none}` 다음 줄에 `.persona-comparison-layout>.persona-map-surface{max-width:720px}`를 추가한다.
  - 명령: `npm --prefix frontend test -- components PersonaScreen` → 전체 통과(T8 순서 테스트 포함).
- TSX 변경 없음. 담당 외 파일 수정 금지.

## 2. TDD 규칙 (Codex에 전달)
RED(바꾼 테스트의 실패 확인 · 출력 기록) → GREEN(최소 구현) → 리팩터링(없으면 생략). 담당 외 파일은 수정하지 않는다. 보고서 `docs/development/persona-ccm-stack/reports/T1.md`에 RED/GREEN 명령과 결과 요약, 변경 파일을 적는다.

## 3. 리뷰
- Task: Claude가 diff · 테스트 출력을 확인하고 설계 2절과 대조한다(지도 단독 화면 규칙 보존, 선택자 범위).
- 브랜치 전체: gstack `review`(읽기 전용). 수정은 Codex에 다시 맡긴다.

## 4. 브라우저 QA (gstack `qa-only`)
- 데이터 복사본: `QA_DATA=/private/tmp/dcx-qa-persona-ccm`에 `~/srv/dcx-agent/shared/data`의 `sessions/s8b25bf1f185143118303600ee0ec5293`(세라젬_261012_sk), `llmcache`, `.author_salt`를 복사한다. 운영 데이터는 바꾸지 않는다.
- 서버(worktree 기준, `.claude/launch.json`에 `qa-api` · `qa-web`로 등록해 `preview_start`):
  - 백엔드: `cd backend && LOCAL_DATA_DIR=$QA_DATA AUTHOR_SALT_PATH=$QA_DATA/.author_salt .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8413`
  - 프런트: `cd frontend && NEXT_PUBLIC_API_URL=http://127.0.0.1:8413 npx next dev -p 3413`
- 테스트 URL: `http://localhost:3413/pipeline/persona` (세라젬_261012_sk, v2 선택 → 페르소나 "현실을 따지는 은퇴 후 귀촌 준비자" 카드).
- 시나리오

| # | 시나리오 | 기대 결과 | AC |
|---|---|---|---|
| S1 | 1440×900, 카드 열기 | 비교 표 폭 = 비교 영역 폭, 지도 카드 top > 표 bottom, 지도 폭 ≤ 720px | AC1 |
| S2 | S1에서 Context 열 폭 측정(`getBoundingClientRect`) | 칸 폭 ≥ 300px (Context 2개) | AC2 |
| S3 | "행동" 칸 클릭 | 원문이 펼쳐지고 한 줄에 20자 이상 들어감. 스크린샷 | AC3 |
| S4 | 지도에서 다른 Context 점 선택 | 해당 표 열 배경 강조 | AC3 |
| S5 | 1024px · 375px 폭 | 기존과 같은 1열, 375px에서 표 가로 스크롤만 있고 페이지 가로 스크롤 없음 | AC4 |
| S6 | "기회 지도" 화면(지도 단독) 1440px | 기존 2:1 배치 그대로 | 제외 범위 보존 |

- 증거: S1 · S3 스크린샷, 측정값, 보고서 `docs/development/persona-ccm-stack/reports/qa.md`.

## 5. 수용 기준 연결
AC1→T1, S1 · AC2→S2 · AC3→S3, S4 · AC4→S5 · AC5→검증 명령 4개.

## 6. 되돌리기
병합 전이면 worktree와 브랜치를 지우면 끝. 병합 후에는 커밋을 revert한다. 데이터 · API 변경은 없다.
