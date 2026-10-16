# 리뷰 지적 (1차)

- **RV1 (P2)** `frontend/src/components/persona/PersonaScreen.tsx:127` — 페인포인트 근거 펼침이 일반 인용(ref.quote)과 그 검증값을 보여 줌. 태그 페인포인트 근거는 ref.pain_point.quote와 pain_point.verified를 보여야 함(R4).
- **RV2 (P2)** `frontend/src/components/persona/OpportunityMap.tsx:78` — 카드 화면 지도에서 선택 페르소나 Context 라벨이 안 붙음. 설계 3.3: 강조 Context + focusPersonaId 페르소나 Context에 라벨, 겹치면 위아래로 비킴. components.test.ts:269 테스트가 잘못된 동작을 고정.
- **RV3 (P2)** `frontend/src/components/persona/OpportunityMap.tsx:75` — 전체 맵에서 점 클릭이 바로 카드를 엶. 결정 3A: 클릭은 오른쪽 상세에 선택만 유지(hover와 분리), [카드 열기]로 카드 진입.
- **RV4 (P2)** `frontend/src/components/persona/PersonaScreen.tsx:138` — 근거 수 행이 trace의 인용된 근거만 셈. Context의 실제 근거 수(card context metrics.doc_count)를 써야 함.
- **RV5 (P2)** `frontend/src/components/persona/HierarchyTree.tsx:20` — PersonaScreen이 렌더마다 hierarchy(data.tree)로 새 root를 만들어 펼침 상태가 초기화됨. useMemo로 data.tree 기준 고정.
- **RV6 (P3)** `frontend/src/components/persona/PersonaScreen.tsx:41` — PersonaContextTable이 ContextTable.tsx와 중복. ContextTable에 페인포인트 열을 추가해 재사용하고 중복 제거, 테스트를 공용 컴포넌트로.
