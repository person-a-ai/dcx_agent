# 리뷰 R1 수정 보고서

## 범위

F1·F2만 최소 수정. 커밋하지 않음. 실제 Codex CLI·외부 네트워크 호출 없이 fake/monkeypatch 테스트로 검증. 작업 시작 전부터 있던 미추적 build.json, reports/progress.md, reports/review-r1.md는 보존했다.

## F1 — 실패 묶음의 정상 묶음 기아 방지

### RED → GREEN

먼저 `test_failed_chunk_does_not_starve_peers`, `test_release_docs_defers_relase`를 추가하고 구현 변경 전 실행:

`backend/.venv/bin/python -m pytest backend/tests/label -q -p no:cacheprovider`

- RED: **2 failed, 290 passed**, 14.33s.
- 첫 테스트: d002~d007의 done 단언 실패. 첫 묶음 반복 실패로 정상 묶음을 실행하지 못함.
- 두 번째 테스트: release_docs 후 at 갱신 단언 실패(1000.0 != 1010.0). 이어서 같은 priority·attempts의 b가 다음 lease에서 선택됨을 단언하도록 작성했다.
- 수정 후 같은 명령 GREEN: **292 passed**, 11.73s.

### 설계와 영향

- 스키마 변경 없이 기존 at을 활용한다. release_docs는 소유한 pending 글의 run_id만 해제하면서 at을 현재 시각으로 기록한다. attempts·status·last_error는 변경하지 않는다. 다른 run 및 terminal 글은 기존 WHERE 조건으로 보호한다.
- lease 순서는 `priority, attempts, (at IS NOT NULL), doc_id`. SQLite에서 NULL인 미임대 글은 0, 기록이 있는 글은 1이므로 같은 priority·attempts의 미임대 글이 먼저 처리된다. 실제 시각 값으로 정렬하지 않아 refresh 주기나 완료 시각 차이가 기존 doc_id 동률 순서를 흔들지 않는다.
- priority와 attempts가 항상 먼저다. 모든 후보가 미임대이거나 모두 이전 임대 이력이 있으면 기존 doc_id 순서다. 기존 DB에도 바로 적용되며 timestamp 비교나 새 칼럼이 필요 없다.
- 정확한 회귀 기대: 최초 d000 묶음 실패는 evidence=0이라 attempts=0 유지. 미임대 d002·d004·d006 묶음 성공 후 evidence=3. d000 재실패 때만 attempts=1이 되고, 이후 성공·재개가 없어 추가 소진 없이 꼬리 연속 실패 5회에 한 번 정지한다. d002~d007 done, d000·d001 pending/attempts=1/last_error=gpt_backend_failed, bad=0. 호출 수는 d000=6, 나머지 각 1회. resumes=0이므로 완료 대신 정상 묶음을 모두 처리한 paused가 올바르다.
- release()는 at을 보존하므로 일시정지 후 재개에서 이전에 임대한 글이 같은 priority·attempts의 미임대 글 뒤로 이동한다. reclaim도 at을 보존하므로 회수한 글에 같은 순서 변화가 적용된다. 이는 공용 VoteCache를 사용하는 Jev/API/fake에도 임대 순서 수준으로 적용된다. R4의 즉시 정지/실패 횟수 정책은 judge에서 그대로 유지한다.
- reclaim의 소유권·생존·만료 조건과 refresh의 소유 pending 임대 갱신 조건은 수정하지 않았다. 임대한 행은 run_id 필터로 선택에서 제외된다. at NULL 여부만 비교하므로 heartbeat 갱신이 정렬에 추가 영향을 주지 않는다.
- judge.py 변경 없음: R2 evidence/failed_at, R4 백엔드 분기, R6 성공 우선 수거를 보존했다. 기존 priority·attempts, live lease, SIGKILL 재개, 650초 refresh, 다른 run 보호 테스트를 포함한 label 전체가 통과했다.

## F2 — 모든 정지 상태의 실패 줄 표시

먼저 failed·interrupted·cancelled 매개변수 테스트를 추가하고 구현 변경 전 실행:

`npm --prefix frontend test -- src/components/label/LabelerProgress.test.ts`

- RED: **3 failed, 9 passed**. 세 상태 모두 `판정 실패 12건 · 검수 큐로 보냄` 누락으로 실패.
- 조건을 `progress.state === 'running' || stopped`로 수정.
- GREEN: **12 passed**. 세 상태에서 실패 줄 포함 및 `판정이 멈췄습니다.` 앞 위치를 검증. 기존 대기·완료·reviewQueue 미지정·0건 테스트도 통과.

## 검증

- 대상 파일 3회 반복: backend test_judge_concurrency.py + test_lease_refresh.py 매회 **32 passed** (5.36s / 1.28s / 1.20s), frontend LabelerProgress.test.ts 매회 **12 passed**. flaky 현상 없음.
- frontend 전체: **81 files, 991 tests passed** (3.33s).
- frontend lint: **exit 0**.
- backend 전체: 실행 중, 최종 결과를 아래에 기록한다.
- frontend build: 요청에 따라 생략.
- 기존 경고: Pydantic class-based config deprecated, Node module.register deprecated.

## 변경 파일

- backend/app/label/votes.py
- backend/tests/label/test_judge_concurrency.py
- backend/tests/label/test_lease_refresh.py
- frontend/src/components/label/LabelerProgress.tsx
- frontend/src/components/label/LabelerProgress.test.ts
- docs/development/gpt-batch-resilience/reports/fix-r1.md

## Main Claude 확인 (2026-10-22)
- Codex 실행(codex:codex-rescue aebb8e23792244695, runtime bg bkfbmgubq)은 최종 단계에서 "Selected model is at capacity"로 exit 1 — 실행 자체는 실패로 기록. 코드·테스트·이 보고서는 그 전에 완성되어 있었고 Main이 diff를 검토함.
- Main이 마무리 검증 실행: `backend/.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider` → **2843 passed, 3 deselected**(9:42); `npm --prefix frontend run build` exit 0; `npm --prefix frontend test` **991 passed**.
