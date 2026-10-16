# 리뷰 지적 (2차, 재리뷰)

RV1~RV6은 모두 수정 확인됨. 수정으로 새로 생긴 문제:

- **RV7 (P2)** `frontend/src/components/persona/PersonaScreen.tsx:141` `const activeHighlight = highlighted ?? activeSelection;`, `OpportunityMap.tsx:55` — 전체 맵에서 A를 선택한 뒤 B에 마우스를 올리면 A 라벨이 사라짐. 설계 3.3: 강조(hover)와 선택 Context 모두 라벨. 선택과 hover를 따로 넘기고 둘 다 라벨, 선택 표시는 별도 마커.
- **RV8 (P2)** `frontend/src/components/persona/OpportunityMap.tsx:61` — 라벨 비키기가 viewBox(600×420) 경계를 확인하지 않아 위쪽 경계 근처에서 라벨이 그림 밖으로 나감. 글자 높이와 viewBox 경계 안으로 제한하고 위쪽 근처면 아래로 비키기. 경계 근처 겹친 점 테스트 추가.
- **RV9 (P2)** `frontend/src/components/persona/ContextTable.tsx:13` `minHeight: 36` — 누르는 요소 44px 규칙(결정 6A) 위반. 44로. 지도 범례 칩(`OpportunityMap.tsx:95`, ds-chip height 32px)도 이 화면에서는 최소 44px 터치 영역 확보(persona.css에서 범위 지정, ds.css 전역은 수정 금지).
