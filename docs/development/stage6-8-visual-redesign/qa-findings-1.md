# 브라우저 QA 지적 (1차) + 사용자 결정

근거: qa/qa-report-localhost-2026-10-16.md

## 사용자 결정 (2026-10-16, 대화에서 선택)
- **F6 → "문장 유지 + 낮은 등급"**: 상태·감정·장벽 칸은 LLM 문장을 그대로 쓴다. 근거 번호(cite)가 없으면 키워드 원문으로 되돌리지 않고 문장을 유지하며 등급은 '추측'(speculated)으로 낮춘다. (03-plan.md R2 결정을 이 결정으로 대체)
- **F8 → "태그 문장 그대로 사용"**: 카드 프롬프트에서, 근거에 태깅된 pain_point가 있으면 그 문장을 고치지 말고 그대로 고른다(비슷한 것은 대표 1개만). 관측 판정 기준(R4: pain_point.verified + 정규화 문장 일치)은 그대로 유지.

## 백엔드 (Codex 수정 대상)
- **F6** `backend/app/persona/cards.py` dims 폴백 제거: cite가 비어도 LLM text 유지, 등급은 grade_card 결과(cite 없음 → speculated) 그대로. 테스트 `test_dims_situation_uncited_falls_back`을 새 계약으로 교체(`test_dims_situation_uncited_keeps_text_as_speculated`).
- **F8** `backend/app/persona/prompts/card.v1.md`: "입력 evidence의 pain_point가 있으면 그 문장을 한 글자도 바꾸지 말고 그대로 text로 쓴다. 비슷한 pain_point가 여럿이면 가장 대표적인 하나만 고른다. 태깅된 pain_point가 없을 때만 직접 쓴다." 테스트: 프롬프트 파일에 해당 지시 포함, fake backend가 태그 문장을 그대로 쓰면 observed가 됨(기존 R4 테스트 재확인).

## 프론트엔드 (Codex 수정 대상)
- **F2** 전체 맵 `ContextTable` 열이 짓눌림(1440px에서 Persona·수치 열 61px, 이름·페인포인트 200px 고정 → 2글자 줄바꿈, '카드 열기' 세로). 열 최소 폭(ID 96, 이름 220, Persona 160, 수치 72, 구역 100, 페인포인트 260, 카드 96)과 표 영역 가로 스크롤로 해결.
- **F3** 카드 화면 지도 SVG 폭 222px. 1280px 이상에서 비교 표:지도 비율을 지도 최소 폭 420px 보장(예: grid `minmax(0,1fr) minmax(420px,0.8fr)`), 그보다 좁으면 지도를 표 아래 전체 폭으로.
- **F4** 구역 이름 겹침(B·C 이름이 오른쪽 위에서 겹침, D 이름이 점과 겹침). 구역 이름을 각 구역 다각형의 넓은 내부 지점(화면 좌표 기준 면적 중심이 아니라, 다른 구역 이름과 최소 거리 16px 이상, 점 밀집 영역 회피)에 두거나 축 바깥 가장자리 범례로 이동. 결정론적.
- **F5** 범례 "CL5 · CL5" 중복: cluster_label이 cluster_id와 같으면 한 번만.
- **F1** 페르소나 미생성(status none/stale, 결과 409 not_ready) 세션: 지도·표 자리에 "페르소나를 만들면 전체 맵과 Context를 확인할 수 있습니다." 안내, not_ready 응답은 오류 문구·재시도로 표시하지 않고 폴링으로 cards/map/tree를 반복 요청하지 않음(status가 done일 때만 요청).
- **F7** 768px 미만: 카드 화면에서 페이지 제목과 카드 제목 중 하나만(카드 제목 숨김 또는 축소), Pain Points 목록 들여쓰기 축소(padding-left ≤ 20px)와 글자 크기 한 단계 축소.
