# 리뷰 지적 (3차)

RV7~RV9 수정 확인됨. 새 지적:

- **RV10 (P2)** `frontend/src/components/persona/PersonaScreen.tsx:171` `onSelect={id => {if (view === 'map') setSelectedContext(id);else setHighlighted(id);}}` — 카드 화면에서 지도 점을 누르면 hover 상태에만 저장되어, `OpportunityMap.tsx:93` `onMouseLeave={() => onHighlight?.(null)}`가 그 값을 지움. 비교 표 열 강조가 전체 맵 선택값으로 돌아감(설계 3.4: 지도 점을 누르면 해당 열 강조). 카드 화면 클릭 선택을 hover와 별도 상태로 저장하고 열 강조의 기본값으로 사용. 테스트: A 클릭 → A에서 마우스 떼기 → B hover → B에서 떼기 후에도 A 열 강조 유지.
