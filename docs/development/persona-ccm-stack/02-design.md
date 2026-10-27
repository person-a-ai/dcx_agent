# 페르소나 Context 비교 표 · 지도 세로 배치 — 설계

기획: [01-brainstorm.md](01-brainstorm.md) (2026-10-27 승인). 기준 브랜치: `main`.

## 1. 원인
- `frontend/src/components/persona/persona.css`의 `@media(min-width:1280px)` 블록에 있는 `.persona-comparison-layout{grid-template-columns:minmax(0,1fr) minmax(420px,0.8fr)}` 때문에 카드 화면의 비교 표와 지도가 좌우로 나뉜다.
- 비교 표 `CCMTable`은 `table-layout:fixed; width:100%`라서 칸 폭은 (표 폭 − 항목 열) ÷ Context 수로 정해진다. 표 폭이 절반 남짓이라 칸이 좁다.

## 2. 동작
- 1280px 이상에서도 `.persona-comparison-layout`을 기본 규칙(`grid-template-columns:minmax(0,1fr)`, 1열)대로 둔다. 즉, 위 2열 규칙 한 줄을 지운다. 같은 블록의 `.persona-map-layout` 규칙(지도 단독 화면)은 그대로 둔다.
- DOM 순서는 이미 `section(비교 표) → mapArea`라서 TSX는 바꾸지 않는다. 지도는 자동으로 표 아래에 놓인다.
- 지도 크기: `OpportunityMap` SVG는 `width:100%`, viewBox 600×420이다. 전체 폭(약 900px)이면 높이가 약 630px까지 커지므로, 카드 화면에서만 지도 카드 폭을 제한한다.
  - 추가: `.persona-comparison-layout>.persona-map-surface{max-width:720px}` (높이 최대 약 504px). 지도 단독 화면(`.persona-map-layout`)에는 적용하지 않는다.
- 원문 펼침, 칸 강조(`<style>` nth-child 규칙), 지도 선택 ↔ 표 열 강조 연동은 코드 변경 없이 그대로 동작한다.

## 3. 데이터·API · 권한
변경 없음(스타일만 바뀜). 읽기 전용 버전 보기도 같은 배치를 쓴다.

## 4. 실패 상태
해당 없음. 지도 로딩, 오류, 빈 상태 표시는 같은 `mapArea` 안에 있어서 위치만 아래로 바뀐다.

## 5. UI 상태 · 반응형 · 접근성
| 폭 | 지금 | 바뀐 뒤 |
|---|---|---|
| ≥1280px | 표 \| 지도 2열 | 표(전체 폭) → 지도(최대 720px) |
| 768–1279px | 1열 | 그대로(지도 최대 720px만 적용) |
| ≤767px | 1열, 칸 최소 200px 가로 스크롤 | 그대로 |
- 읽기 순서와 탭 순서는 DOM 순서와 같아서 그대로다.
- 지도가 표 아래로 가면서 표가 길 때 지도까지 스크롤이 필요하다. 기획에서 받아들인 결과다.

## 6. 테스트 영향
- `components.test.ts` F3은 2열 규칙의 존재를 고정하고 있다. 이를 "카드 비교 영역에 2열 규칙이 없고, 카드 지도에 `max-width:720px`가 있다"로 바꾼다(먼저 RED, 다음에 GREEN).
- `PersonaScreen.test.ts` T8(요약 → 표 → 지도 → 패널 순서)은 그대로 통과해야 한다.

## 7. 디자인 검토 (plan-design-review 요지)
- 정보 위계: 이 화면의 주 작업은 근거 원문 읽기이고, 지도는 보조다. 표에 전체 폭을 주는 것이 위계와 맞다.
- 일관성: 768–1279px에서 이미 쓰던 1열 배치를 넓은 화면까지 늘린 것이라 새 시각 상태가 생기지 않는다.
- 위험: 지도가 너무 크면 화면을 지배한다 → 720px 상한. 왼쪽 정렬로 표의 왼쪽 선과 맞춘다.
- 후속: 그래도 원문이 불편하면 A안(원문 패널)을 별도 작업으로 검토한다.

## 8. 되돌리기
`persona.css` 두 줄 변경과 테스트 F3을 되돌리면 원래대로 돌아간다.
