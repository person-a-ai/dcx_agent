# SDD ledger — plan: docs/development/stage8-insight-redesign/03-plan.md

Spec: docs/development/stage8-insight-redesign/01-brainstorm.md, 02-design.md (계획의 R1~R7이 설계와 다르면 계획 우선 — 계획 머리말에 명시).
Implementer: codex:codex-rescue (--wait --fresh, write). Reviewer: Claude 서브에이전트(읽기 전용).
Shared context file: .superpowers/sdd/03-plan/constraints.md

## Pre-flight scan

| 행 | 생산 | 소비 | 확인 결과 |
|---|---|---|---|
| T1↔T2 (insights.py) | T1 InsightItem·validate_items | T2 recompute 같은 파일 | 순차, 충돌 없음 |
| T1↔T3 | T1 validate_items(require_new, previous), EditItem, EditOut | T3 chat.edit | T1 Interfaces에 R4 시그니처. 일치 |
| T2↔T3 (stage8.py) | T2 get_insights summary·history | T3 Chat.focus_id, InsightRun.fresh | 같은 파일 다른 함수, 순차 |
| T2↔T3 (context_view) | T2 context_view(F1 경로) | T3 R5 Context 요약 | 재사용, 일치 |
| T1 store.py | T1 Files store.py(R2) | T1 Step 3 | 일치 |
| T4↔T5/T6 | InsightView, FlowCard, BarRow, dimLabel, radarMean | T5, T6 | 일치 |
| T4↔T6/T7 | InsightTarget insight:${string}(R3), InsightRunRequest.fresh(R1) | T6 채팅 띠, T7 | 일치 |
| T5↔T6 | 파일 겹침 없음 | — | 순차 실행 |
| T6↔T7 | InsightHeader onRederive | T7 startInsight(fresh) | 일치 |
| T3 테스트 위치 | R1 테스트 test_insights.py | 기존 파이프라인 테스트가 다른 파일이면 그 파일 허용 | 일치 |
| T1~T6 자체 | 테스트 ↔ 코드 | — | 일치 |
| T7 자체 | QA 테스트 useState 순서 mock | 재구성 시 깨짐 | 계획이 의미 유지·구조 맞춤 허용 |

Ruling: 실행 순서를 T1 → T4 → T2 → T5 → T6 → T3 → T7 순차로 한다 — 계획은 두 lane 병렬을 허용하지만 Codex가 같은 워크트리에서 커밋하므로 git index 충돌을 피한다 — 틀리면 시간만 더 든다.

## Progress
Baseline (5a4e9ba): pytest 2780 passed (9m25s), lint 0, vitest 849 passed, build 0.
T1 BASE: 5a4e9ba
Task 1: dispatch 1 (codex acefcb00759a1cffa) → BLOCKED: 구현 완료, 대상 테스트 57 passed, persona 4 failed/73 errors (가짜·echo LLM 생성기가 예전 스키마), 커밋 불가(샌드박스가 워크트리 git 메타데이터 쓰기 거부).
Ruling: T1 소유 파일에 backend/tests/fixtures/evidence_package.py(fake_persona_backend)와 backend/app/llm/fake.py(echo insight.derive)를 추가한다 — 새 필드가 필수라 기존 가짜 응답이 모두 깨지며 계획 파일 목록이 이를 빠뜨렸다 — 틀리면 가짜 생성기 변경이 다른 테스트 기대값을 바꿀 수 있어 리뷰에서 확인.
Ruling: Codex 변경의 git 커밋은 컨트롤러(Claude)가 테스트 결과 확인 후 수행한다 — Codex 샌드박스가 /Users/tech/code/dcx_agent/.git/worktrees 아래를 쓸 수 없다 — 커밋은 기록 행위이며 코드 내용은 Codex 산출물 그대로; 틀리면 작성자 표기만 다름.
Task 1: review 1 (a36ec1f18204ae663) Approved, Minor 6.
Ruling: Minor #2(스키마 단계 실패는 재시도 없음)와 #1(derive.v2.md가 v1의 "이 필드만 반환" 문장을 유지해 새 필드 지시와 모순)을 수정 대상으로 올린다 — 설계 6절 "LLM 새 필드 검사 실패: 도출 1회 재시도"와 어긋나고 실제 모델 출력 실패를 키운다 — 틀리면 수정 1회 비용.
Task 1: minor (deferred): headline 따옴표 strip이 앞뒤 작은따옴표도 제거(브리프 문자 목록대로); test_validate_flow_single_context가 실패 케이스 없음; 재시도 문구 상수화; 보고서 머리 상태 stale.
Task 1: fix round 2/5 (2 addressed, 0 open; commits 2f298ea..e2ba725; re-review aaa7518d4113df554)
Task 1: complete (commits 5a4e9ba..e2ba725, review clean)
T4 BASE: e2ba725
Task 4: complete (commits e2ba725..46d4353, review clean; reviewer ab987c2f2148e33ff)
Task 4: minor (deferred): toInsightView의 summary 인자 미사용(서명 유지, 주석 권장); radarMean이 일부 축만 값 없을 때 0 반환(누락과 0 구분 안 됨); personas가 context_ids 밖 contexts까지 포함 가능.
T2 BASE: 46d4353
Task 2: complete (commits 46d4353..9c33d7c, review clean; reviewer a50e2cde870d628de)
Task 2: minor (deferred): GET마다 load_package(약 24ms); recompute가 cards를 별도 store로 읽음; get_insights 보강이 store.read 새 객체에 의존(주석 권장); 저장된 contexts 스냅샷은 페르소나 재생성 시 인사이트가 초기화되므로 수용.
T5 BASE: 9c33d7c
Task 5: dispatch 1 (codex a6577e8ccfeaeb655) → 새 테스트 10 통과, 전체 vitest 8 실패(예전 Radar/OpportunityBars 계약 테스트), InsightScreen.tsx 빌드 타입 오류.
Ruling: components.test.ts·finalReview.test.ts 중 Radar/OpportunityBars를 직접 검사하는 테스트는 T5에서 새 계약으로 옮긴다(남는 동작의 회귀 의미 유지, 의도적으로 없앤 동작의 단언만 제거하고 보고서에 나열) — 계획 파일 목록이 빠뜨렸다 — 틀리면 회귀 보호가 약해질 수 있어 리뷰에서 제거 목록 확인.
Ruling: InsightScreen을 렌더하는 테스트(InsightScreen.qa.test.ts, finalReview D313 등)와 InsightScreen.tsx 빌드 오류는 T7에서 처리한다. T5~T7 사이 빌드는 일시적으로 깨진 상태 — T7이 화면을 다시 짜므로 중간 수정은 버려질 작업 — 틀리면 중간 커밋에서 빌드 실패(브랜치 최종 상태에는 영향 없음).
Task 5: fix round 1/5 (테스트 이관; commits 9c33d7c..d2e19ed; 남은 실패 2개는 T7 소유 InsightScreen 렌더 테스트)
Task 5: review 1 (a72f3b12ca188df76) Approved, Important 3: 평균 라벨-막대 값 겹침, 막대 aria-label 원값, radarMean 일부 축 0을 실제 0으로 그림.
Ruling: radarMean 수정을 위해 T5 소유에 insightView.ts의 radarMean과 insightView.test.ts를 추가하고, 반환 타입을 축별 number|null로 바꾼다 — T4 deferred minor가 T5 화면에서 실제 오표시로 드러남 — 틀리면 T7 소비 타입 조정 필요(T7 브리프에 전달).
Ruling: 레이아웃 px(240px, 열 최소폭 등)는 허용한다 — tokens.css에는 글자·색·모서리만 있고 설계 5.0이 240px 등 px를 직접 정함; 설계 D4의 "임의 px"는 글자 크기·색 하드코딩을 뜻한다 — 틀리면 추후 토큰화 작업.
Ruling: 범례 글자색 --line-strong(테두리용) → --sub로 바꾼다 — 설계 5.1 매핑 밖이고 대비가 낮다 — 틀리면 색만 다름.
Task 5: fix round 2/5 (4 addressed, 0 open; commits d2e19ed..88b2aea; re-review a76a7562176987855)
Task 5: complete (commits 9c33d7c..88b2aea, review clean; 남은 실패 finalReview D313·InsightScreen.qa 1건은 T7 소유)
Task 5: minor (deferred): 막대 가로 스크롤 영역 키보드 접근(tabindex) 없음; 240px 고정 높이에서 긴 라벨이 세로 스크롤 유발 가능; 흐름 줄바꿈 시 줄 앞 화살표; radar <title>과 aria-label 중복; persona.css 예전 .opportunity-* 규칙 정리 여부.
Note for T7: radarMean 반환 타입이 축별 number|null로 바뀜(T5 fix round 2).
T6 BASE: 88b2aea
Task 6: review 1 (adc2fa5d82044ab08) Approved, Important 1: 넘김 경계에서 포커스된 버튼이 비활성되어 포커스 소실.
Task 6: minor (deferred → T7에 전달): focusId와 target id 불일치 시 select 빈 값 — T7이 항상 일치시킴; focusId 없을 때 '현재 인사이트' 비활성; 대화상자 rederiveDisabled 변경 시 열린 채 유지; 다시 도출 트리거 disabled 단언 없음; insightParts.test의 위치 기반 useState mock 취약; <h2>insight-chat</h2>은 설계 5.1 표 문구대로.
Task 6: fix round 1/5 (2 addressed, 0 open; commits b391c2f..c3fb225; re-review aaae6307f491e832d)
Task 6: complete (commits 88b2aea..c3fb225, review clean)
Task 6: minor (deferred): focusedRef가 index 불변 시 남을 수 있음; navigate·layout effect 연결은 순수 함수 테스트만(브라우저 QA Q5로 확인).
T3 BASE: c3fb225
Task 3: dispatch 1 (codex a3b58fa4714792bd4) → 집중 106 통과, 전체 2838 통과 2 실패(test_final_fix2::test_n4_only_changed_insight_concept_is_outdated, test_final_fixes::test_concept_revert_cannot_restore_obsolete_source — context_ids만 바꾸고 flow는 옛 ID).
Ruling: 두 테스트의 입력에 바뀐 Context를 가리키는 flow를 넣도록 T3 소유를 넓힌다(단언은 그대로) — R4 승인 규칙(옛 flow 거부)과 충돌하는 것은 테스트 입력이지 동작이 아니다 — 틀리면 회귀 보호가 약해질 수 있어 리뷰에서 단언 보존 확인.
Task 3: fix round 1/5 (테스트 입력 2건; commits c3fb225..d47c756)
Task 3: complete (commits c3fb225..d47c756, review clean; reviewer ad35c36c532bea55f)
Task 3: minor (deferred): 근거 묶음 없을 때 LLM 호출 후 실패(이전과 결과 같음, 호출 낭비); contexts 요약 길이 상한 없음; fresh 도출의 확정 비우기가 load_session을 잠금 밖에서 읽어 동시 확정 PUT과 경합 가능(작은 창); 단일 항목 수정 시 다른 항목 백분위가 갱신되지 않음(R3 바이트 동일 요구의 결과).
T7 BASE: d47c756
Task 7: dispatch 1 (codex aac81e33d2dd3388b) → NEEDS_CONTEXT: finalReview.test.ts에서 D313 외 4건이 예전 체크박스·직접 렌더된 버튼을 찾아 실패.
Ruling: 그 4건은 요소 찾는 코드만 새 InsightTopBar/InsightHeader 구조로 바꾸고 단언은 그대로 둔다 — 화면 구조 변경은 승인된 범위, 단언 의미 보존이 회귀 보호 — 틀리면 리뷰에서 단언 변경 여부 확인.
Task 7: 컨트롤러 확인 — 기본 build 0(Codex 샌드박스에서 Turbopack 정지는 환경 문제), vitest 910 passed, lint 0.
Task 7: review 1 (ac9102c5401359d9e) Approved, Important 1(되돌리기가 insight:* 대상이면 한 항목만 되돌린다는 주장).
Task 7: Ruling: Important 지적은 사실과 다름 — backend/app/persona/chat.py revert에서 _target('insight:I2')의 name이 'insights'라 store.revert로 판 전체를 되돌린다(항목별 분기는 concept 전용) — 틀리면 판 일부만 되돌아감, 브라우저 QA Q9에서 확인.
Task 7: Ruling: 미리보기 막대 평균선이 현재 summary.context_odi_mean을 쓰는 것은 정상 — 이 값은 근거 묶음 기준 세션 값이라 판마다 같다(R6 표) — 틀리면 표시만 다름.
Task 7: minor (deferred): QA 테스트가 useState 위치 인덱스(h.values[8] 등)에 의존; insight.css의 1280px 미디어 블록 3개 병합; 768~1279 전용 규칙 없음(공통 기본값); D313 기대 문자열 마침표 제거·단언 1개 추가(작은 편차).
Task 7: complete (commits d47c756..e20ea28, review clean after ruling)
Final review (opus afeaa2876d887e03d): With fixes — Important 3(fresh 재시도 경로, concept 대상 페이지 추종, 확정 비우기 원자성) + 병합 전 수정 deferred(막대 스크롤 tabIndex, 240px 라벨 넘침).
Ruling: 최종 수정 1회에 Important 3 + 막대 tabIndex + 라벨 2줄 말줄임 + radar_mean 축 타입 number|null + edit.v2에 flow 1~80자·해시태그 중복 금지 규칙 + ProvisionalBadge 복원(설계 재사용 목록에 있고 ODI·RADAR_AXES가 여전히 PROVISIONAL) + ChatPanel을 대상별 key로 리셋을 묶는다 — 모두 작고 사용자에게 보이는 결함 — 틀리면 범위가 조금 넓어짐.
Ruling: R4 id 바꾸기 회피(#4), 처리 중 문구 범위(#5), 다중 탭 대기 채팅(#7), summary 인자(#8)는 보류 — UI가 이미 실행 중 채팅을 막고, 나머지는 영향이 작다 — 틀리면 드문 경우 오수정.
FINAL FIX BASE: e20ea28
Final fix: 1 dispatch (codex ad3dc15cadbe6961a), re-review acc447044a6044cea — 9/9 addressed, commits e20ea28..dff82a8. 컨트롤러 확인: persona 401, vitest 917, lint 0, build 0.
QA run-20261016T132612Z: Q1–Q9 PASS, ISSUE-001 Medium(대화상자 좌상단), ISSUE-002 Low(줄바꿈 화살표), ISSUE-003 Low(조사 과/와) → harness retry, QA FIX BASE: dff82a8
QA fix: dispatch 1 (codex a8dec1898629d7f16) commit 906e5de — 3건 수정, vitest 939, lint 0, build 0. 단 tokens.css에 새 토큰 3개 추가.
Ruling: tokens.css 변경을 되돌리고 insight.css에 padding 24px, max-width min(32rem, calc(100% - 32px)), backdrop rgba(28,30,34,.4)를 직접 쓴다 — 계획 Global Constraints '새 토큰 금지'; 레이아웃 px는 앞선 판정으로 허용, rgba는 기존 --shadow-overlay와 같은 색 — 틀리면 값 중복만 생김.
QA fix: fix round 1 (tokens 되돌림) commit 530b55c; re-review a30840d3a5a00671c — 4/4 addressed.
QA fix: parked — 줄바꿈 행 끝 화살표가 빈 공간을 가리킴(Low) — Ruling: 수용, 화살표가 앞 카드를 따르므로 오해가 작고 CSS 해결은 중단점별 nth-child 규칙 필요 — 틀리면 시각적 사소함.
QA re-check: ISSUE-001..003 FIXED; ISSUE-004 Low(막대 라벨 잘림·세로 스크롤) 신규, ARROW-TRAIL Low → 하네스가 열린 지적이 있으면 browser-qa 완료 불가 → retry. QA FIX2 BASE: 530b55c
QA fix: fix round 2 commit 2012741 (ISSUE-004, ARROW-TRAIL); re-review adac1ad5b14f988c8 2/2 addressed; 브라우저: scroller 202==202 overflow hidden, 5카드 화살표 [block,block,block,none,-].
Note: 1279.5px·767.5px 같은 소수 폭은 미디어 쿼리 사이 틈(기존 경계, 이번 변경 아님) — 기록만.
