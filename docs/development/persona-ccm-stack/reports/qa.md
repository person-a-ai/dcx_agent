# 브라우저 QA — persona-ccm-stack (2026-10-28)

- 대상: worktree `feature/persona-ccm-stack` (HEAD d99866d + 미커밋 T1 변경: `persona.css`, `components.test.ts`).
- 서버: `.claude/launch.json` `qa-api`(uvicorn 8413) · `qa-web`(next dev 3413). 데이터는 `/private/tmp/dcx-qa-persona-ccm` 복사본(세션 `s8b25bf1f185143118303600ee0ec5293`, `llmcache`, `.author_salt`)만 사용.
- 도구: Claude 내장 브라우저(preview), 측정은 `getBoundingClientRect` / `getComputedStyle`.
- URL: 계획의 `/pipeline/persona`는 404. 실제 경로 `http://localhost:3413/pipeline/personas`에서 세라젬_261012_sk를 열고 v2(활성 버전), 페르소나 "현실을 따지는 은퇴 후 귀촌 준비자"(CL2-P2, Context 2개) 카드를 사용.
- 하네스 기록(`qa.json`, `complete browser-qa`)은 사용자 결정에 따라 생략.

## 결과 요약

| # | 결과 | 측정값 |
|---|---|---|
| S1 | PASS | 1440×900. 비교 영역 그리드 `814px` 1열. 표 폭 814 = 영역 폭 814. 표 section bottom 878 < 지도 top 902(페이지 좌표). 지도 폭 720px, `max-width:720px`, 왼쪽 x=544로 표와 정렬. |
| S2 | **FAIL** | Context 칸 폭 271px (기준 ≥300px). 항목 열도 271px. 비교: 이전 2열 규칙을 브라우저에서만 임시 주입했을 때 표 370px, 칸 123px. 즉 123 → 271px(약 2.2배)로 넓어졌으나 AC2 수치 미달. 사용자 수용(2026-10-28): 123→271px 개선으로 충분, 300px 기준 미달은 받아들임. 항목 열 폭 고정은 하지 않음. |
| S3 | PASS | "행동" 칸(CL2-P2-C1) 클릭 → `aria-expanded=true`, `.ccm-full-text` 펼침. 줄당 25 · 26 · 22자(3줄). 이 칸은 펼침 영역에 "근거가 없습니다."가 표시됨(데이터 특성). |
| S4 | PASS | 카드 지도에서 CL2-P2-C2 점 클릭 → `<style>` 규칙 `table:nth-child(1) :is(th,td):nth-child(3)` 생성, 3번째 열 배경 `rgb(234,248,255)`(blue-soft), 다른 열은 그대로. |
| S5 | PASS | 1024×800: 그리드 `550px` 1열, 표 → 지도 순서, 지도 550px(상한 미적용 폭), 표/페이지 가로 넘침 없음. 375×812: 그리드 `247px` 1열, 칸 200px, 표 내부 가로 스크롤(scrollWidth 602 / client 247), `documentElement.scrollWidth` 375 = 뷰포트 → 페이지 가로 스크롤 없음. |
| S6 | PASS | "기회 지도" 단독 화면 1440px: `.persona-map-layout` 그리드 `558.656px 279.344px`(2:1), 지도 카드 `max-width:none`. 기존과 동일. |

## S2 실패 분석
- 카드 본문(`.persona-card-body`) 폭이 862px(왼쪽 내비 240px + 페르소나 목록 열 차지)라서 표 폭은 814px이다. 설계는 "전체 폭 약 900px"를 가정했다.
- `CCMTable`은 `table-layout:fixed`이고 열 폭 지정이 없어 항목 열을 포함한 3열이 똑같이 나뉜다(271 × 3). 설계 1절의 "(표 폭 − 항목 열) ÷ Context 수" 가정과 다르다.
- 300px을 넘기려면 코드 변경이 필요하다(예: 항목 열 폭 고정 · 축소). 이번 작업에서는 고치지 않고 보고만 한다.

## 기타 관찰
- QA 중 창(window) 자체를 스크롤하면 `.pipeline-shell`(높이 100vh) 아래가 빈 화면으로 보인다. 앱은 `.pipeline-main` 내부 스크롤을 쓰므로 일반 사용에서는 생기지 않는 측정 도구 쪽 현상이다.
- 375px 측정은 뷰포트만 바꾸고 새로 고침하지 않았다. 배치는 CSS 미디어 쿼리로만 정해져 영향이 없다.

## 증거
- S1: [qa/S1-1440-stack.jpg](qa/S1-1440-stack.jpg) — 표 하단과 그 아래 720px 지도.
- S3: [qa/S3-1440-expanded.jpg](qa/S3-1440-expanded.jpg) — "행동" 칸 원문 펼침, 271px 칸.
- 그 밖의 측정값은 위 표에 적은 브라우저 스크립트 출력이다.
