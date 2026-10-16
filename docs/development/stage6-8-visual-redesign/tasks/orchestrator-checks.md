# Task별 확인 기록 (Main Claude, 읽기·실행 검증만)

| Task | 커밋 | 확인한 것 |
|---|---|---|
| T1 | 3314814 | 운영 데이터 근거 묶음 2개(s89d9234 v2, s8b25bf1 v2)의 `_digest`를 이전 코드(운영 release)와 새 코드로 계산해 동일함 확인(bd31c377…, 97949443…). evidence+persona 테스트 596 통과 재실행. |
| T2 | eb0b0b6 | cards.py diff 검토: dims 폴백은 cite가 빈 경우만(R2), 관측은 pain_point.verified + 정규화 문장 일치(R4), 근거 없는 Context는 pain_points []. 백엔드 전체 2776 통과 재실행. |
| T3 | 9fa239e | personaView.ts 코드 검토(zoneOf가 opportunity.zone과 같은 규칙, Sutherland–Hodgman 절단). personaView 테스트 43 통과 재실행. 픽스처는 Main Claude가 로컬 API 응답을 저장(Codex 샌드박스에서 로컬 API 접근 불가). |
| T4 | 89b0e44 | hex 색상 없음, useMemo 1곳 확인. components 테스트 437 통과 재실행. |
| T5 | 85a10a9 | hex 색상 없음. 기본 `next build`를 직접 실행해 통과(Codex 샌드박스에서만 정체). |
| T6 | c5cb9e8 | components 445 통과, `next build` 통과 재실행. |
| T7 | b3c8c72 | InsightScreen.qa.test.ts 변경이 원래 의도(null 막대 없음, 0은 막대 있음) 유지함을 diff로 확인. 프론트 전체 809 통과, build exit 0 재실행. |
| T8 | a0b7cef | 프론트 전체 820 통과, build exit 0 재실행. 발견: Context 표가 PersonaScreen.tsx 내부 `PersonaContextTable`로 새로 구현되어 기존 `ContextTable.tsx`와 중복 — 리뷰 단계 지적 사항으로 넘김. |
