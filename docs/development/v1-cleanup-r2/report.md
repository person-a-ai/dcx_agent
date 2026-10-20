# v1 정리 결과 보고 (v1-cleanup + v1-cleanup-r2)

- 브랜치: `chore/v1-cleanup-r2` (워크트리 `/Users/yunho/Documents/dcx_agent-v1-cleanup-r2`). `chore/v1-cleanup`의 커밋을 모두 포함하므로 이 브랜치 하나만 보면 된다.
- 기준: `main` `4444a50`(+ 문서 커밋 `b36cdf5`, `81e2477`는 main에 로컬로만 있음, push 안 함)
- 하네스 실행: `v1-cleanup`(T1~T6, 브라우저 QA에서 멈춤 → 보관: `/Users/yunho/Documents/dcx_agent-v1-cleanup-harness-archive-r1`) → `v1-cleanup-r2`(T7, 진행 중 실행)

## 바뀐 것

| 커밋 | 작업 | 내용 |
|---|---|---|
| `330dbc9` | T1 | 전처리 공용 함수를 `app/prep/documents.py`로 이동, v1 전용 분기 삭제 |
| `6f20ec0` | T2 | 호환 파일 `preprocessed/{sid}/*.jsonl` 쓰기와 재사용 조건 제거(D-065) |
| `9db84bf` | T3 | v1 백엔드 경로 13개·서비스·`context/compat.py`·안 쓰는 스키마 삭제(약 1,600줄) |
| `56cae23` | T4 | 루트 `workflow.py`(Flask 원형) 삭제. crawl4ai는 유지(DV-2) |
| `2a1360a`, `6bcaa30` | T5 | 전처리 전 세션은 사이드바 6~9단계 잠금 + 세 페이지 배너, 모바일 줄바꿈 |
| `c15ea7f` | T6 | 옛 인사이트 화면·고아 컴포넌트 5개·`lib/api.ts` v1 함수 삭제(`SNAGraph`는 v2가 써서 유지, DV-4) |
| `af0e0ce`, `5de8f30` | T7 | 6~9단계를 `prep.status === 'done'`일 때만 열고, 세 페이지 모두 보고 있는 버전의 세션으로 판단(DV-5) |

그대로 둔 것: 사이드바 챗봇(B-120)과 그 의존 모듈, crawl4ai, v2 라우터의 `is_legacy` 가드, 데이터 파일.

## 검증

- 작업마다 Codex 구현 → Controller 게이트·커밋 → 다른 Codex 독립 리뷰 PASS(T5·T7은 리뷰 지적 수정 후 재리뷰 PASS).
- 브랜치 전체 독립 리뷰: 1차 PASS, r2 PASS(r2 1차에서 P2 1건 → DV-5로 수정).
- 브라우저 QA: 1차 14/19(실제 결함 2건 + QA 계획 오류 3건) → r2 **19/19 PASS**. 증거: [qa/qa.json](qa/qa.json), 1차 [../v1-cleanup/qa/qa.json](../v1-cleanup/qa/qa.json).
- 테스트(`5de8f30`): 백엔드 pytest 2807 통과, 프론트 lint 통과 · vitest 80파일 978개 통과 · build 통과. 하네스 `evidence` 결과는 verification 보고서.
- 운영 확인(2026-10-19, 읽기만): 운영 세션 4개 모두 새 형식, 옛 세션 0개.

## 이탈 기록

[../v1-cleanup/deviations.md](../v1-cleanup/deviations.md)(DV-1~DV-4)와 [deviations.md](deviations.md)(DV-5).

## 후속 과제(이번 범위 밖)

1. 근거 탐색 페이지(`frontend/src/app/pipeline/evidence/page.tsx`)가 아직 `derivedRef`만 보고 열린다. 사이드바는 잠기지만 주소로 직접 들어가면 전처리 중에도 열린다. 같은 `laterStageGate`로 맞추기.
2. 배너의 단계 이름을 `STEP_NAMES`에서 가져오기(지금은 문자열, 값은 같음).
3. `BACKEND.md`·`PIPELINE.md`·README의 오래된 설명(옛 크롤링 라우터, Pinecone, 8단계) 정리.
4. 프론트 테스트 파일의 `tsc --noEmit` 오류 7개(이번 정리 전부터 있음).
5. v2 문서의 `desc`·`cafe`·`link`를 없애고 내보내기가 `body`/`src_meta`를 직접 쓰게 하기, `clustersDone` 정리.
6. 챗봇이 v2 결과를 읽게 하기(B-120).
7. 맥미니의 옛 데이터 파일(`preprocessed/`, `clusters/`, `personas/` 등) 정리 여부 결정.

## 남은 일

UAT 승인 → 하네스 마무리(브랜치 유지). push · PR · 배포는 별도 요청이 있을 때만.
