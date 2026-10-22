# gpt-batch-resilience 진행 기록 (SDD ledger)

기준: `03-plan.md`(sha256 cfc352ad…) · 결정 R1~R7 · 설계 정정(R1)이 01·02 문구보다 우선.
기준 검사(구현 전): pytest 2,807 passed · lint 0 · vitest 978 passed · build 0.

## Rulings (plan 승인 이후 판단)
- **RL1** `test_chunk_failures_preserve_peers`의 `backend` 변형은 R2를 따른다. 시작 attempts 0이면 d000·d001은 다른 묶음이 성공한 뒤의 첫 실패로 attempts 1·pending. 새 성공 없이 다시 실패하면 횟수 유지, 연속 실패 기준에서 `BREAKER_MESSAGE`로 정지. 시작 attempts 2면 첫 실패로 bad. 계획 본문 "결국 bad"는 R2 이전 문장의 잔재.
- **RL2** T3의 새/갱신 judge 테스트는 모두 `settings.label_gpt_backend`를 테스트 안에서 monkeypatch로 지정(`codex_exec` 또는 `openai_api`).
- **RL3** 진행 기록 위치는 하네스 훅이 허용하는 `docs/development/gpt-batch-resilience/reports/`(이 파일).
- **RL4** `backend/.venv`는 계획 §0의 심볼릭 링크 대신 uv로 이 worktree에 새로 생성(원래 체크아웃에 venv 없음).
- **RL6** T3 범위에 `.env.example` 추가(두 변수 빈 값 두 줄만). 근거: 기존 `test_g6_environment_documentation`이 설정 필드 전부의 문서화를 요구 — T2 설정 추가의 직접 결과. ops README는 env 블록 인라인 주석 대신 본문 설명.
- **RL5** T1·T4는 파일이 겹치지 않아 병렬 위임. Codex는 커밋하지 않고, Claude가 Task 리뷰 후 계획의 커밋 메시지로 Task별 커밋(동시 git index 충돌 방지).

## Task 상태
| Task | 상태 | dispatch | 보고서 | 커밋 |
|---|---|---|---|---|
| T1 | 완료·리뷰 | codex:codex-rescue 작업 a949fbc170a19edb2 | reports/T1.md | 6444003 |
| T2 | 완료·리뷰 | codex:codex-rescue 작업 a5b843e9ff6bf8752 | reports/T2.md | 6720eb0 |
| T3 | 완료·리뷰 | codex:codex-rescue 작업 a0916be9a3aff9934 (runtime bg b6r5fllif, bjn8tjohr) | reports/T3.md | 83bc051 |
| T4 | 완료·리뷰 | codex:codex-rescue 작업 a7864b727846e70fa | reports/T4.md | 48efea3 |

## Task 리뷰 메모
- T1: RED 4/5 실패(`test_part_ignored_on_nonzero_exit`은 기존 동작이 이미 맞아 처음부터 통과 — 사실대로 기록). Main 재실행 10 passed.
- T2: 재시도 대기 합계 기본 15~21초 동안 정지 요청 미확인(설계 §실패 상태 "≤33초, 묶음 스레드 안" 범위 내). Main 재실행 test_gpt 38 passed.
- T4: Codex 샌드박스에서 기본 build 정체 → Main 셸에서 exit 0 확인. 판정 실패 줄은 running·paused에만 표시(failed·interrupted·cancelled 미표시) — 브랜치 리뷰에서 재검토.
- T3: Main 재실행 label 290 passed. Codex 전체 2841 passed, 0 failed. R2·R4·R6·사용량 한도 우선 반영 확인. `release_docs`는 `self.run_id` 임대만 해제.

## 리뷰 1차 → retry (2026-10-22)
- reports/review-r1.md: F1(P2 재임대 기아 — AC4) · F2(P2 정지 상태 실패 줄 숨김). `harness retry`로 build 복귀.
- 수정 위임: codex:codex-rescue aebb8e23792244695 → reports/fix-r1.md.
- **RL7** F1 수정은 스키마 변경 없이 `lease` 정렬에서 release_docs로 풀린 글을 같은 priority·attempts의 미시도 글 뒤로 미루는 방향(구현 세부는 Codex, 근거는 fix-r1.md). 승인된 목표(AC4) 달성을 위한 구현 보정으로 기록, UAT에서 알림.

## QA 환경
- 데이터: scratchpad `qa-data/`(운영 shared/data에서 세라젬 세션 sessions·derived/c1/p_85024e028d18·crawl만 복사, work·judge 캐시 없음, author salt는 새 무작위 값).
- `.claude/launch.json`(gitignore 대상) `qa-api` 8412 · `qa-web` 3412. 시나리오별 `qa-mode.env`의 `FAKE_CODEX_LABEL_MODE` 등을 바꾸고 API 재시작(워커가 API 하위 프로세스라 환경 상속).
