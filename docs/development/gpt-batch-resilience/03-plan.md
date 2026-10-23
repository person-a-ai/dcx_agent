# GPT(Codex) 판정 묶음 실패 내성 — 구현 · QA 계획

> 실행: 하네스 규칙에 따라 각 Task를 Codex(`codex:codex-rescue`, `--wait --fresh`, 쓰기 모드)에 위임한다. Main Claude는 위임 · 결과 확인 · 리뷰만 한다.

**목표:** GPT 묶음 하나가 실패해도 판정 전체가 멈추지 않게 하고, 실패 원인 두 가지(답 파일 이름 미변경, 모델 용량 초과)를 없앤다.
**구조:** codex_exec가 `.part` 답을 구제하고, gpt가 용량 오류를 재시도하고, judge가 단발 실패는 건너뛰고 연속 실패만 정지한다. 진행 카드에 검수 큐로 간 건수를 보인다.
**기술:** Python 3.12 · FastAPI 워커 · SQLite(VoteCache) · Next.js/React · pytest · vitest.
**명세:** [01-brainstorm.md](01-brainstorm.md) · [02-design.md](02-design.md) (2026-10-21 승인).

## 전역 제약
- 설정 기본값: `label_capacity_retries = 2`(0 이상), `label_failure_pause_after = 5`(1 이상). 환경변수 `LABEL_CAPACITY_RETRIES`, `LABEL_FAILURE_PAUSE_AFTER`, 빈 값이면 기본값.
- 연속 실패 정지 문구(정확히): `GPT 판정이 연속으로 실패해 멈췄습니다. 잠시 뒤 이어서 진행하거나 설정에서 API 경로로 바꾸세요.`
- 화면 문구(정확히, R1·R5·R7 반영): 진행 중·정지 `판정 실패 {N}건 · 검수 큐로 보냄`, 설명(title·sr-only) `3번 시도해도 판정하지 못한 글은 검수 큐에서 사람이 판정합니다.`, 완료 `판정을 마쳤습니다. {N}건은 판정하지 못해 검수 큐로 보냈습니다.` (N은 `toLocaleString('ko-KR')`). Jev·GPT 카드에만 표시하고 분류 모델 카드에는 표시하지 않는다(R5).
- **설계 정정(R1):** 02-design.md §5 · UI 상태와 01-brainstorm.md AC5 · AC7의 "제외 / 학습에서 빠짐" 표현은 사실과 다르다. GPT `bad` 글은 `route.py:183`에서 검수 큐(`labeler_failed`, 우선순위 0)로 간다. 구현은 위 문구를 따른다. 01 · 02는 하네스 해시로 잠겨 있어 이 계획에서 정정한다.
- 사용량 한도 동작 · 메시지, 형식 오류(parse/schema) 동작, Jev 경로는 바꾸지 않는다. 새 실패 정책(건너뛰기 · 연속 실패 정지 · 성공 사이 실패만 횟수 셈)은 `label_gpt_backend == 'codex_exec'`에서만 적용하고, `openai_api` · `fake`의 비한도 실패는 지금처럼 즉시 정지한다(R4).
- DB 스키마 · API 응답 형식 변경 없음.

## 리뷰 집중점 (테스트로 고정)
1. Codex가 코드 0으로 끝났지만 `.part`가 잘린 JSON → 채택하지 않고 기존 parse 오류 + `answers/bad/` 격리. (T1)
2. Codex가 코드 1로 끝났는데 `.part`가 있음 → 채택하지 않음(백엔드 실패). (T1)
3. 용량 오류가 재시도 한도까지 계속 → 재시도 후 `LabelerPaused(usage_limit=False)`, 사용량 한도 문구가 아님. (T2)
4. 동시 4묶음이 모두 실패(장애) → 연속 기준에서 정지하고, 어떤 글도 3회 실패로 `bad`가 되지 않음(기준 5, 시도 0에서 시작). (T3)
5. 실패 묶음과 성공 묶음이 섞여 계속 → 정지 없이 끝까지 가고 실패 글만 `bad`, run은 `done`. (T3)
6. 남은 묶음 1개에서 Codex 전체 장애 → 글 시도 횟수가 늘지 않아 `bad` 0, 연속 기준에서 정지. (T3, R2)
7. 코드 1 시도가 `.part`를 남기고 다음 시도가 아무것도 안 쓰고 코드 0 → 남은 `.part`를 채택하지 않음. (T1, R3)

## 0. 작업 환경
- 계획 승인 후 기획 산출물 커밋 → `development-harness worktree /Users/tech/code/dcx_agent-gpt-batch-resilience feature/gpt-batch-resilience`.
- 새 worktree에서 `backend/.venv`: `/Users/tech/code/dcx_agent/backend/.venv` 심볼릭 링크(기존 구현 worktree와 같은 방식), `npm --prefix frontend ci`.
- 기준 검사: `harness.config.json`의 4개 명령(pytest · lint · build · vitest)이 구현 전에 통과하는지 확인.

## 1. Task
| ID | 내용 | 담당 파일 | 의존 | AC |
|---|---|---|---|---|
| T1 | 지시문 최종 파일명 + `.part` 채택 | `backend/app/llm/codex_exec.py`, `backend/tests/fakes/fake_codex.py`, `backend/tests/llm/test_codex_exec.py` | — | AC1, AC2 |
| T2 | 용량 오류 재시도 + 설정 2개 | `backend/app/label/gpt.py`, `backend/app/config.py`, `backend/tests/fakes/fake_codex.py`, `backend/tests/label/test_gpt.py`(설정 테스트 포함 — 별도 설정 테스트 파일 없음) | T1(fake 공유) | AC3 |
| T3 | 단발 실패 계속 · 연속 실패 정지 | `backend/app/label/judge.py`, `backend/app/label/votes.py`(`release_docs`), `backend/tests/label/test_lease_refresh.py`(release_docs 테스트), `backend/tests/fakes/fake_codex.py`(QA용 `flaky` 모드), `backend/tests/label/test_judge_concurrency.py`, `backend/tests/label/test_judge.py`, `README.md`, `ops/macmini/README.md` | T2(설정) | AC4, AC5, AC6 |
| T4 | 진행 카드 판정 실패 건수 | `frontend/src/components/label/LabelerProgress.tsx`, `frontend/src/components/label/Overview.tsx`(prop 전달만), `frontend/src/components/browserQa.test.ts`(Overview 렌더 1건), `frontend/src/components/label/LabelerProgress.test.ts`(신규) | — | AC7 |

순서: T1 → T2 → T3 순차(파일 겹침). T4는 독립이라 T1과 병렬 가능.

### T1 — `codex_exec._worker`
**Interfaces:** 산출 — 지시문 첫 줄이 `` 답 JSON만 `answers/task-{n}.json.part`에 쓴 뒤 `answers/task-{n}.json`으로 이름을 바꿔라 (mv answers/task-{n}.json.part answers/task-{n}.json) ``. 첫 백틱 구간이 `.part` 경로여야 한다(fake_codex가 그것을 답 경로로 읽음).
- [ ] RED: fake_codex에 일반 과제용 표지 `NORENAME_MODE`(답을 `.part`에 쓰고 rename 안 함, 코드 0), `NORENAME_FAIL_MODE`(`.part`를 쓰고 코드 1), `TRUNCATED_MODE`(`.part`에 `{"value":` 쓰고 rename 안 함, 코드 0)를 추가. 테스트(`test_codex_exec.py`):
  - `test_unrenamed_part_is_adopted`: `NORENAME_MODE` → `result.ok`, `data.value == 1`, `answers/task-0.json` 존재, `.part` 없음.
  - `test_part_ignored_on_nonzero_exit`: `NORENAME_FAIL_MODE` → `error.kind == 'backend'`, `answers/task-0.json` 없음.
  - `test_truncated_part_quarantined`: `TRUNCATED_MODE` → `error.kind == 'parse'`, `answers/bad/task-0.json` 존재.
  - `test_instruction_names_final_file`: 실행 후 `prompts/task-0.txt` 첫 줄에 `` `answers/task-0.json.part` ``와 `answers/task-0.json으로 이름을 바꿔라`가 둘 다 있음.
  - `test_stale_part_not_adopted` (R3): fake 표지 `SILENT_MODE`(아무것도 안 쓰고 코드 0) 추가. `answers/task-0.json.part`를 미리 만들어 두고 `SILENT_MODE` 실행 → `error.kind == 'backend'`, 미리 둔 파일이 `answers/bad/` 아래로 옮겨짐(이름 `task-0.json.part.` 접두), `answers/task-0.json` 없음.
- [ ] 실행 `backend/.venv/bin/python -m pytest backend/tests/llm/test_codex_exec.py -q -p no:cacheprovider` → 새 5개 FAIL.
- [ ] GREEN: 지시문 교체. Codex 실행 직전 남은 `answers/task-{n}.json.part`가 있으면 `answers/bad/task-{n}.json.part.<time.time_ns()>`로 옮긴다(R3). `process.returncode == 0`이고 `answer`가 없고 `answer.with_name(answer.name + '.part')`가 있으면 `replace(answer)` 후 `_answer(task, answer)`.
- [ ] 같은 명령 → 전부 PASS. `backend/tests/label` 전체도 PASS(지시문 변경 회귀 확인).
- [ ] 커밋 `fix(llm): Codex 답 파일명을 명시하고 이름을 바꾸지 않은 답도 채택`.

### T2 — `gpt.judge_batch` 용량 재시도 · 설정
**Interfaces:** 소비 — T1의 fake. 산출 — `settings.label_capacity_retries: int`, `settings.label_failure_pause_after: int`; `gpt._latest_attempt(run_id: str) -> str`(최신 attempt 로그, 소문자); `gpt._capacity_wait(k: int) -> float` = `min(5 * 2**k, 30) + random.uniform(0, 3)`; 대기는 `time.sleep(gpt._capacity_wait(k))`.
- [ ] RED: fake_codex 라벨 모드 `capacity`(`ERROR: Selected model is at capacity. Please try a different model.` 출력, 코드 1), `capacity_once`(그 run 폴더 `invocations` 줄 수가 1일 때만 capacity, 이후 정상)를 추가. 테스트(`test_gpt.py`, `time.sleep`은 monkeypatch로 기록만):
  - `test_capacity_retried_then_succeeds`: `capacity_once` → 결과 정상, invocations 2줄, sleep 1회.
  - `test_capacity_gives_up_after_retries`: `capacity`, 재시도 2 → `LabelerPaused`, `usage_limit is False`, 메시지가 사용량 한도 문구 아님, invocations 3줄, sleep 2회.
  - `test_capacity_retries_zero`: `label_capacity_retries=0` → invocations 1줄, sleep 0회.
  - `test_usage_limit_not_retried`: 기존 `usage_limit` 모드 → invocations 1줄, sleep 0회.
  - 설정: `Settings(_env_file=None)` 기본값 2 · 5, 환경변수 빈 문자열이면 기본값, `LABEL_CAPACITY_RETRIES=-1` · `LABEL_FAILURE_PAUSE_AFTER=0`은 검증 오류.
- [ ] 실행 `backend/.venv/bin/python -m pytest backend/tests/label/test_gpt.py -q -p no:cacheprovider` → 새 테스트 FAIL.
- [ ] GREEN: 실패 결과이고 `_latest_attempt(run_id)`에 `at capacity`가 있으면 재시도 루프. `_pause_message`는 `_latest_attempt`를 쓰도록 정리. 설정은 `Field(ge=0)` · `Field(ge=1)`, `empty_stage_setting_uses_default` 목록에 추가.
- [ ] 같은 명령 + `backend/tests/label` 전체 PASS.
- [ ] 커밋 `fix(label): 모델 용량 초과 묶음을 자동 재시도`.

### T3 — `judge.run_worker` 연속 실패 차단
**Interfaces:** 소비 — `settings.label_failure_pause_after`, `settings.label_gpt_backend`. 산출 — `judge.BREAKER_MESSAGE`(전역 제약의 문구). 새 정책 전체는 `settings.label_gpt_backend == 'codex_exec'`일 때만(R4); 테스트는 이 값을 monkeypatch로 지정.
- [ ] RED (`test_judge_concurrency.py`, 기존 `concurrent_judge` 픽스처 · `stop_on_pause` 방식 재사용):
  - 기존 `test_chunk_failures_preserve_peers`의 `backend` · `mixed` 기대를 갱신: `backend`(단발)는 `_pause` 호출 없이 `run_worker`가 정상 반환, d000/d001은 실패 횟수 +1 후 다시 시도되어 결국 `bad`(fake가 계속 실패하므로 3회), 나머지 done. `mixed`는 사용량 한도가 있으므로 기존대로 paused · 사유 `usage limit`.
  - `test_isolated_failures_do_not_pause`: 8건 중 d000 묶음만 **처음 2번** 실패 후 성공, `label_failure_pause_after=5` → `_pause` 호출 0, counts `done=8, bad=0`.
  - `test_consecutive_failures_pause`: 모든 묶음 항상 실패, concurrency 4, 기준 5 → 정지 1회, 사유 == `BREAKER_MESSAGE`, `bad == 0`(모든 글 attempts ≤ 2), run `paused`.
  - `test_success_resets_counter`: 기준 2, 실패·성공·실패·성공 순서 → 정지 0.
  - `test_resume_resets_counter`: 기준 2로 정지 → resume → 다음 실패 1회로 다시 정지하지 않음.
  - `test_outage_does_not_spend_attempts` (R2): 문서 2건(묶음 1개), 항상 실패, 기준 5 → 정지 1회, 두 글 `attempts == 0`(첫 실패 후 성공이 없었으므로 임대만 해제), `bad == 0`.
  - `test_failures_between_successes_count` (R2): d000 묶음만 항상 실패, 다른 묶음은 성공(문서 8건, concurrency 1, 기준 5) → 다른 묶음 done, d000 · d001은 성공 사이 실패만 세어짐; 꼬리에서 연속 실패로 정지하면 `stop_on_pause` 대신 재개를 흉내 내 최대 3회 재개 → d000 · d001 `bad`(attempts 3), run 종료.
  - `test_release_docs_keeps_attempts` (`test_lease_refresh.py`에 추가): 임대 후 `release_docs` → run_id NULL, attempts · status · last_error 그대로, 다른 run의 임대는 그대로.
  - `test_existing_attempts_not_spent_by_outage` (R2): 시작 attempts=2인 글 묶음 1개, 항상 실패 → `bad` 0, 정지.
  - `test_successes_counted_first` (R6): 한 번의 수거에 성공 1 · 실패 3이 함께 끝나도록(Barrier) 하고 기준 4 → 정지 0.
  - `test_api_backend_still_pauses_immediately` (R4): `label_gpt_backend='openai_api'`, 첫 묶음 비한도 `LabelerPaused('API 실패')` → 즉시 정지, 사유 'API 실패', 실패 글 attempts +1(기존 동작).
  - `test_judge.py::test_real_context_pause_resume`의 `LabelerPaused('사용량 한도')`를 `usage_limit=True`로 바꿔 기존 의미 유지. `test_gpt_failures_bounded_per_document`: `missing` 변형은 수정 없이 통과(호출 3회, bad 3). `paused` 변형은 `label_gpt_backend='openai_api'`로 고정해 기존 의미(즉시 정지 · 3회 후 bad 3)를 보존하고, codex_exec용 새 변형 `paused_codex`를 추가: 성공이 없으므로 run마다 연속 기준에서 정지, 4번 실행 후 `bad == 0`, attempts 0.
- [ ] 실행 `backend/.venv/bin/python -m pytest backend/tests/label -q -p no:cacheprovider` → 새/갱신 테스트 FAIL.
- [ ] GREEN (codex_exec 경로에서만, 다른 백엔드는 기존 코드 그대로 — R4):
  - 메인 스레드 지역 상태: `consecutive_failures = 0`, `evidence = 0`(실행 중 성공 묶음 수 + 사용자 재개 횟수), `failed_at: dict[str, int]`(글이 마지막으로 실패했을 때의 `evidence`).
  - 수거한 결과는 성공 먼저 처리한다(R6). 성공 묶음마다 `evidence += 1`, `consecutive_failures = 0`.
  - 비한도 `LabelerPaused` 묶음의 각 글(R2): `evidence > failed_at.get(doc, -1)`이고 `evidence > 0`이면 `cache.fail(doc, 'gpt_backend_failed')`, 아니면 `cache.release_docs([doc])`(횟수 유지, 임대만 해제). 그다음 `failed_at[doc] = evidence`. 묶음당 `consecutive_failures += 1`.
  - `consecutive_failures >= settings.label_failure_pause_after`면 `paused = LabelerPaused(BREAKER_MESSAGE)`. `_pause`에서 복귀(사용자 재개)하면 `consecutive_failures = 0`, `evidence += 1`(재개는 장애가 끝났다는 신호 — 꼬리의 문제 글이 재개마다 1회씩 세어져 결국 검수 큐로 감).
  - `votes.py`에 `VoteCache.release_docs(doc_ids: list[str]) -> None` 추가: 이 run이 잡은 pending 임대만 `run_id=NULL`로, attempts · last_error 변경 없음.
- [ ] 같은 명령 PASS, 이어서 `backend/.venv/bin/python -m pytest backend/tests -q -p no:cacheprovider` 전체 PASS.
- [ ] 문서: `README.md` 환경변수 표와 `ops/macmini/README.md` 운영 설정에 두 변수 한 줄씩.
- [ ] 커밋 `fix(label): GPT 묶음 하나 실패로 판정 전체가 멈추지 않게`.

### T4 — `LabelerProgress` 판정 실패 건수
**Interfaces:** 소비 — 기존 `LabelProgress.bad?: number`. 산출 — `LabelerProgress`의 새 prop `reviewQueue?: boolean`(기본 false). `Overview.tsx`가 jev · gpt 카드에만 `reviewQueue` 전달(R5).
- [ ] RED (`LabelerProgress.test.ts`, `renderToStaticMarkup` 방식은 `workerControls.test.ts`와 같음):
  - `reviewQueue` true, running, `done:4000,total:5688,pending:1676,bad:12` → `판정 실패 12건 · 검수 큐로 보냄` 포함, `title="3번 시도해도 판정하지 못한 글은 검수 큐에서 사람이 판정합니다."` 포함, `sr-only` 텍스트 포함, 이 문구가 `건 판정` 문구 뒤 · `처리 중` 앞에 위치.
  - paused + bad 12 → 같은 줄 표시.
  - done, `done:5676,total:5688,bad:12` → `판정을 마쳤습니다. 12건은 판정하지 못해 검수 큐로 보냈습니다.` 포함, `판정 실패 12건 · 검수 큐로 보냄` 미포함.
  - `reviewQueue` 없음(분류 모델 카드), running · done + bad 12 → `검수 큐` · `판정 실패` 미포함, done이면 정확히 `판정을 마쳤습니다.`.
  - `Overview` 렌더(기존 `browserQa.test.ts`의 `gptOnlyOverview` 재사용, gpt bad 3, state running) → `판정 실패 3건 · 검수 큐로 보냄` 포함.
  - bad 0 · 없음(running · done) → `판정 실패` · `검수 큐` 미포함, done이면 정확히 `판정을 마쳤습니다.`.
  - none(대기) + bad 3 → `판정 실패` 미포함.
  - bad 1234 → `1,234건`.
- [ ] 실행 `npm --prefix frontend test -- src/components/label/LabelerProgress.test.ts` → FAIL.
- [ ] GREEN: 설계 02 §5 · UI 상태 표의 위치 · 상태 규칙대로, 문구는 이 계획 전역 제약대로 구현.
- [ ] `npm --prefix frontend test`, `npm --prefix frontend run lint`, `npm --prefix frontend run build` PASS.
- [ ] 커밋 `feat(label): 판정 진행 카드에 판정 실패로 검수 큐에 간 글 수 표시`.

## 2. TDD 규칙 (Codex에 전달)
RED → GREEN → 리팩터링. 담당 파일 외 수정 금지, 다른 작업자 변경 보존. 실제 Codex · 네트워크 호출 금지(fake만). 보고서 `docs/development/gpt-batch-resilience/reports/T<n>.md`에 RED 출력 · GREEN 출력 · 변경 파일 기록.

## 3. 리뷰
- Task별: Claude가 diff · 테스트 출력 확인, 명세 대조.
- 브랜치 전체: gstack `review`(읽기 전용) + 별도 Codex 읽기 전용 리뷰. 중점: 재시도 루프가 정지 · 중단 요청을 막지 않는지, 연속 카운터가 스레드 안전한지(메인 스레드 `collect`에서만 갱신), `.part` 채택이 쓰는 중 파일을 읽을 수 없는지, 설정 검증.
- 수정은 모두 Codex에 재위임.

## 4. QA
- **서버:** 구현 worktree에서 API 8412 · 웹 3412. 데이터 디렉터리는 scratchpad에 운영 `shared/data`의 세라젬 세션(`sessions/s1ef426ca23624027b2acddff133fa4b1`, `derived/<sid>/c1/p_85024e028d18`, 필요한 `crawl/<sid>`)만 복사. `LABEL_GPT_BACKEND=codex_exec`, `CODEX_BIN=<worktree>/backend/tests/fakes/fake_codex.py`, `LABEL_CONCURRENCY=8`, `LABEL_BATCH_SIZE=20`. 시작 명령은 `.claude/launch.json`에 `qa-api` · `qa-web`로 등록(`preview_start`).
- **테스트 URL:** `http://localhost:3412/pipeline/labeling?sid=s1ef426ca23624027b2acddff133fa4b1`
- **시나리오**(각각 새 버전 · "라벨링 시작"):
  1. `FAKE_CODEX_LABEL_MODE=no_rename`(T1 fake 라벨 모드로 추가: `.part`만 쓰고 코드 0) → 정지 0회로 5,688건 완료, 카드 `판정을 마쳤습니다.`, `llm_runs`의 답이 모두 `task-0.json`.
  2. `FAKE_CODEX_LABEL_MODE=capacity_once` → 정지 0회로 완료, run 폴더마다 invocations 2줄.
  3. `FAKE_CODEX_LABEL_MODE=flaky`(T3에서 fake에 추가: 묶음 첫 글 ID의 마지막 16진 자리가 0~3이면 항상 코드 1) → 정지 없이 완료, 카드 완료 문구에 검수 큐로 보낸 건수, 그 건수 = 해당 글 수 = 검수 큐 '판정 실패' 건수, 진행 중 스크린샷에 `판정 실패 N건 · 검수 큐로 보냄`.
  4. `FAKE_CODEX_LABEL_MODE=capacity` + `LABEL_CAPACITY_RETRIES=0` → 시작 직후 정지, 카드 사유 = 연속 실패 문구, `bad` 0. "이어서 진행" 버튼 표시.
  5. 375px 폭에서 시나리오 3 화면: 판정 실패 문구 줄바꿈 · 가로 스크롤 없음.
  6. 시나리오 4 뒤 `FAKE_CODEX_LABEL_MODE=normal`로 바꾸고 "이어서 진행" → 완료, `bad` 0(R2: 장애가 횟수를 소진하지 않음).
- **보고서:** `docs/development/gpt-batch-resilience/reports/qa.md` + 스크린샷.
- **운영 반영(UAT 이후, 사용자 요청 시에만):** main 병합 → 자동 배포. 운영 설정 변경 불필요(기본값 사용).

## 5. 수용 기준 연결
AC1→T1 · AC2→T1, QA1 · AC3→T2, QA2 · AC4→T3, QA3 · AC5→T3, QA3 · AC6→T3, QA4 · AC7→T4, QA3·QA5 · AC8→검증 명령 4개.

## 6. 되돌리기
- 커밋 단위 revert(T1~T4 독립 커밋). 데이터 형식 변경 없음.
- 즉시 완화: `LABEL_FAILURE_PAUSE_AFTER=1`이면 지금처럼 묶음 하나 실패에 정지, `LABEL_CAPACITY_RETRIES=0`이면 재시도 없음.

## Eng review (plan-eng-review, 2026-10-21) — 대상: 이 계획 + 02-design.md

### Scope Challenge
- 구조 답변: Original arrangement (2026-10-21). feature answers: 축소 제안 없음; structure: Original arrangement; accepted scope: T1~T4 그대로; pending remedies: none(R1 승인).
- 결과: scope accepted as-is.
- 기존 해결책: 글 단위 3회 → `bad`는 이미 있음(`backend/app/label/votes.py` `fail`: `status=CASE WHEN attempts+1>=3 THEN 'bad'`). `bad` 글은 검수 큐로 이미 라우팅됨(`backend/app/label/route.py:183` `SELECT doc_id, 'labeler_failed', 0, 'open' FROM {name}.votes v WHERE status='bad'`).
- 복잡도: 변경 파일 약 14개(코드 5 · fake 1 · 테스트 6 · 문서 2), 새 클래스·서비스 0 → 8개 이상이라 구조 확인 질문 대상.
- 기능 축소 제안: 없음. 더 작은 배치: 같은 계약을 지키는 더 작은 파일 배치는 없음(용량 재시도를 codex_exec로 옮기면 모든 Codex 과제에 적용되어 승인된 설계 범위를 넘음).

## Decision ledger

### R1: 판정 실패 글의 화면 문구와 문서 표현
Finding: 1, P1, confidence 9/10, backend/app/label/route.py:183, reviewer: Claude (plan-eng-review)
Plan baseline: 02-design.md §5 · UI 상태(D2·D3·D4 승인) — 진행 중 `제외 {N}건 (3번 실패)`, 설명 `3번 시도해도 판정하지 못한 글은 학습에서 빠집니다.`, 완료 `판정을 마쳤습니다. {N}건은 판정하지 못해 제외했습니다.`; 01-brainstorm.md AC5 "판정 실패로 제외(`bad`)"
Runtime evidence: route.py:183-187이 GPT `bad` 글을 `queue(reason='labeler_failed', priority=0, status='open')`로 넣음. 사람이 검수하면 final source='human'으로 학습에 들어감. 즉 "제외"가 아니라 "검수 대기".
Comparison grid:
| 항목 | 현재(승인) | A | B | C |
|---|---|---|---|---|
| bad 글 동작 | 검수 큐 맨 앞(실제) | 그대로 | 검수 큐에 넣지 않게 route.py 변경 | 그대로 |
| 진행 중 문구 | `제외 N건 (3번 실패)` | `검수 대기 N건 (3번 실패)` | `제외 N건 (3번 실패)` | 그대로 |
| 설명(title·sr-only) | 학습에서 빠집니다 | `3번 시도해도 GPT가 판정하지 못한 글은 검수 큐에서 사람이 판정합니다.` | 그대로 | 그대로 |
| 완료 문구 | `…판정하지 못해 제외했습니다.` | `판정을 마쳤습니다. N건은 GPT가 판정하지 못해 검수 큐로 보냈습니다.` | 그대로 | 그대로 |
| 01·02 문서 '제외' 표현 | 제외 | '검수 큐로 보냄'으로 정정 | 그대로 | 그대로 |
| 줄 위치(D4) | 건수 줄 아래 | 그대로 | 그대로 | 그대로 |
Question D1:
D1 — GPT가 3번 실패한 글의 화면 문구가 실제 동작과 다릅니다
Project/branch/task: main, gpt-batch-resilience 계획 검토.
ELI10: 지금 코드는 GPT가 3번 판정에 실패한 글을 버리지 않고 사람이 보는 검수 큐 맨 앞에 넣습니다(route.py:183). 그런데 승인된 화면 문구는 "학습에서 빠집니다 / 제외했습니다"라고 말합니다. 그대로 만들면 사용자는 데이터가 사라졌다고 오해하고, 검수 큐에 할 일이 생긴 걸 놓칩니다.
Stakes if we pick wrong: 사용자가 잘못된 안내를 믿고 검수를 건너뛰거나, 반대로 필요한 사람 검수 경로를 지워 데이터가 실제로 빠집니다.
Recommendation: A because 동작은 이미 안전(사람 검수)하고, 문구만 사실에 맞추면 되는 가장 작은 변경입니다.
Note: options differ in kind, not coverage — no completeness score.
Pros / cons:
A) 문구를 '검수 큐로 보냄'으로 정정 (recommended)
  ✅ 실제 동작과 일치해 사용자가 검수 큐에서 그 글을 찾아 처리할 수 있음
  ✅ 코드 동작 변경 없음, T4 문구와 01·02 문서 표현만 바뀜 (human: ~20min / CC: ~3min)
  ❌ 승인했던 화면 문구(D2·D3 결정의 단어)를 다시 바꿔야 함
B) 실제로 제외하도록 동작 변경
  ✅ 문구를 그대로 쓸 수 있고 검수 큐가 실패 글로 붐비지 않음
  ✅ GPT가 계속 실패하는 이상한 글을 사람이 볼 필요가 없음
  ❌ route.py 변경과 회귀 테스트가 필요하고, 사람이 살릴 수 있던 글이 학습에서 빠짐 (human: ~2h / CC: ~15min)
C) 그대로 둠
  ✅ 추가 작업이 전혀 없음
  ❌ 화면 안내가 사실과 달라 사용자를 오도함
Net: 사람 검수라는 안전한 기존 동작을 지키며 문구를 고칠지, 문구에 맞춰 동작을 바꿀지의 선택입니다.
Header: 실패 글 문구
Options:
A) 문구를 '검수 큐로 보냄'으로 정정 (recommended)
진행 중 `검수 대기 N건 (3번 실패)`, 설명 `3번 시도해도 GPT가 판정하지 못한 글은 검수 큐에서 사람이 판정합니다.`, 완료 `판정을 마쳤습니다. N건은 GPT가 판정하지 못해 검수 큐로 보냈습니다.` 01·02 문서의 '제외' 표현도 정정. 동작 변경 없음. 줄 위치는 그대로.
B) 실제로 제외하도록 동작 변경
GPT bad 글을 검수 큐에 넣지 않도록 route.py를 바꾸고 회귀 테스트 추가. 문구는 승인된 '제외' 그대로. 사람이 살릴 수 있던 글이 학습에서 빠짐.
C) 그대로 둠
승인된 문구 그대로. 실제로는 검수 큐로 가므로 안내가 사실과 다름.

State: approved
Actual answer: A) 문구를 '검수 큐로 보냄'으로 정정 (recommended) — 2026-10-21 plan-eng-review D1 답변
Accepted scope: T4 화면 문구 · 테스트 기대 · QA 시나리오 3·5 문구를 A의 문구로 바꿈. 동작 변경 없음, 줄 위치(D4) 유지.
History: A의 '01·02 문서 정정'은 하네스가 승인 문서 해시 변경을 거부하므로(cli.js "Approved evidence changed") 이 계획의 전역 제약 '설계 정정(R1)'으로 기록함. 01·02 원문을 고치려면 해당 게이트를 revise해야 함 — 사용자에게 알림.

### R2: 장애가 글의 실패 횟수를 소진하는 문제
Finding: 2, P1, confidence 9/10, backend/app/label/votes.py:114 (`status=CASE WHEN attempts+1>=3 THEN 'bad'`), reviewer: Codex outside voice
Plan baseline: 02-design §3 — 비한도 실패마다 `cache.fail` +1, 연속 5회에서 정지.
Runtime evidence: 남은 묶음이 1~2개거나 기존 attempts=2인 글이 있으면, Codex 전체 장애에서도 연속 5회 전에 글이 3회 실패로 `bad`(검수 큐행)가 됨.
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| 백엔드 실패 시 글 시도 횟수 | 항상 +1 | 그 글의 직전 실패 이후 다른 묶음 성공이 1번이라도 있었을 때만 +1, 아니면 임대만 해제(횟수 유지) | 항상 +1 |
| 연속 실패 정지(5회) | 있음 | 그대로 | 그대로 |
Question D2: GPT 장애가 글의 '3번 실패'를 소진합니다 — 성공 사이의 실패만 셀까요?
Header: 장애 시 횟수
Options:
A) 성공 사이 실패만 셈 (recommended)
글의 직전 실패 이후 다른 묶음이 성공한 적이 있을 때만 시도 횟수 +1. 장애 중에는 임대만 풀고 횟수 유지. judge.py 메모리 상태(글별 마지막 실패 시점의 성공 수) 약 15줄 + 테스트 2개(남은 묶음 1개 장애 → bad 0, 성공 사이 3회 실패 → bad).
B) 그대로 항상 셈
장애 끝부분에서 글이 3회 실패로 검수 큐에 갈 수 있음을 받아들임. 추가 작업 없음.
State: approved
Actual answer: A) 성공 사이 실패만 셈 (recommended) — 2026-10-21 plan-eng-review 답변
Accepted scope: judge.py: 백엔드 실패 글은 직전 실패 이후 성공이 있었을 때만 attempts+1, 아니면 임대만 해제. 테스트 2개.
History: 구현 계획 작성 중 보완 — 꼬리의 문제 글은 성공 사이 실패가 생기지 않아 끝나지 않으므로, 사용자 재개도 증거로 센다(evidence += 1). 승인된 A의 '성공 사이 실패만 셈'을 끝나게 하는 데 필요한 구현으로 기록, 사용자에게 알림.

### R3: 이전 실패 시도의 .part 채택
Finding: 3, P1, confidence 9/10, backend/app/llm/codex_exec.py:69-92, reviewer: Codex outside voice
Plan baseline: T1 — 코드 0이고 최종 답이 없으면 `.part` 채택.
Runtime evidence: 코드 1 시도의 `.part`는 지워지지 않음. 같은 run_id 다음 시도가 아무것도 안 쓰고 코드 0이면 지난 시도의 파일을 채택.
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| 시도 시작 전 남은 `.part` | 그대로 둠 | `answers/bad/task-{n}.json.part.<시각>`로 격리 | 그대로 둠 |
Question D3: 지난 실패 시도의 .part를 정상 답으로 쓸 수 있습니다 — 시도 전에 치울까요?
Header: 남은 .part
Options:
A) 시도 전 격리 (recommended)
Codex 실행 직전에 남은 `.part`를 `answers/bad/`로 옮김. codex_exec 2~3줄 + 테스트 1개(코드 1 시도 후 아무것도 안 쓰는 코드 0 시도 → backend 실패).
B) 그대로
남은 `.part`도 스키마만 맞으면 채택될 수 있음을 받아들임.
State: approved
Actual answer: A) 시도 전 격리 (recommended) — 2026-10-21 plan-eng-review 답변
Accepted scope: codex_exec: 실행 직전 남은 .part를 answers/bad/로 격리. 테스트 1개.
History: none

### R4: 연속 실패 차단의 적용 범위(백엔드)
Finding: 4, P1, confidence 8/10, backend/app/label/gpt.py:148 (API 경로 실패도 `LabelerPaused` usage_limit=False), reviewer: Codex outside voice
Plan baseline: 전역 제약 "OpenAI API 경로는 바꾸지 않는다" + T3 `collect`는 모든 GPT 백엔드 공통.
Runtime evidence: `openai_api` 인증 실패 등도 지금은 즉시 정지, 계획대로면 5회까지 계속 돌며 횟수 소진.
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| codex_exec 비한도 실패 | 즉시 정지 | 건너뛰고 연속 5회에 정지 | 건너뛰고 연속 5회에 정지 |
| openai_api · fake 비한도 실패 | 즉시 정지 | 즉시 정지(그대로) | 건너뛰고 연속 5회에 정지 |
Question D4: 연속 실패 차단을 Codex 경로에만 적용할까요?
Header: 적용 범위
Options:
A) Codex 경로에만 (recommended)
`settings.label_gpt_backend == 'codex_exec'`일 때만 새 정책, API · fake는 지금처럼 즉시 정지. 회귀 테스트 1개(openai_api 실패 → 즉시 정지).
B) 모든 GPT 경로 공통
API 인증 실패도 5회까지 돌다 멈춤. 전역 제약 문구를 바꿔야 함.
State: approved
Actual answer: A) Codex 경로에만 (recommended) — 2026-10-21 plan-eng-review 답변
Accepted scope: 연속 실패 차단·건너뛰기는 label_gpt_backend == 'codex_exec'에서만. openai_api·fake는 즉시 정지 유지. 회귀 테스트 1개.
History: none

### R5: 진행 카드 문구를 어느 판정기에 보일지
Finding: 5, P2, confidence 9/10, frontend/src/components/label/Overview.tsx:57 (Jev · GPT · 분류 모델이 같은 LabelerProgress 사용) + backend/app/label/route.py `if model_mode: return`(모델 모드 bad는 검수 큐에 안 감), reviewer: Codex outside voice + Claude
Plan baseline: R1 문구 "GPT가 판정하지 못한 글은 검수 큐…"를 모든 카드에 표시.
Runtime evidence: Jev `bad`도 검수 큐로 감(gpt_only 아닐 때). 분류 모델 `bad`(incomplete)는 검수 큐로 안 감.
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| 표시 대상 | 모든 카드 | Jev · GPT 카드만(분류 모델 제외) | GPT 카드만 |
| 문구의 'GPT가' | 있음 | 빼고 판정기 공통 문구 | 그대로 |
Question D5: 실패 문구를 Jev·GPT 카드에만 보이고 'GPT가'를 뺄까요?
Header: 표시 대상
Options:
A) Jev·GPT만, 공통 문구 (recommended)
`LabelerProgress`에 `reviewQueue?: boolean` prop, Overview가 jev·gpt 카드에만 true. 문구에서 'GPT가' 제거. 테스트: 분류 모델 카드에는 미표시.
B) GPT 카드만
prop은 같고 GPT 카드에만 true, 'GPT가' 유지. Jev 실패는 화면에 안 보임.
State: approved
Actual answer: A) Jev·GPT만, 공통 문구 (recommended) — 2026-10-21 plan-eng-review 답변
Accepted scope: LabelerProgress에 reviewQueue?: boolean, Overview가 jev·gpt 카드에만 true, 문구에서 'GPT가' 제거. 분류 모델 카드 미표시 테스트.
History: none

### R6: 연속 실패 집계 순서
Finding: 6, P2, confidence 8/10, backend/app/label/judge.py:173 (`collect(finished)`가 set 순회), reviewer: Codex outside voice
Plan baseline: 결과 순서대로 성공이면 0, 실패면 +1.
Runtime evidence: 같은 수거 묶음에 성공·실패가 섞이면 set 순서에 따라 정지 여부가 달라짐.
Comparison grid:
| 항목 | 현재 | A | B |
|---|---|---|---|
| 한 번에 수거한 결과의 처리 순서 | set 순서 | 성공 먼저, 실패 나중 | set 순서 |
Question D6: 한 번에 끝난 묶음들은 성공을 먼저 셀까요?
Header: 집계 순서
Options:
A) 성공 먼저 (recommended)
수거한 결과를 성공·실패로 나눠 성공 먼저 처리. 결정적이라 테스트 가능. 테스트 1개(같은 수거에 성공1·실패3, 기준 4 → 정지 안 함).
B) 그대로
운영에서 정지 시점이 가끔 하나 일찍/늦게 됨을 받아들임.
State: approved
Actual answer: A) 성공 먼저 (recommended) — 사용자 '이어서 진행해주세요'(D6 미응답)를 추천안 진행으로 해석, 2026-10-21. 이의 시 재개방.
Accepted scope: T3: 수거 결과 성공 먼저 처리 + test_successes_counted_first.
History: none

### R7: 진행 중 문구의 숫자 의미
Finding: 7, P2, confidence 9/10, backend/app/label/votes.py:127 (`counts`의 bad는 누적), backend/app/label/route.py:263 (검수 후 큐만 닫힘), reviewer: Codex outside voice
Plan baseline: R1 승인 — 진행 중 `검수 대기 {N}건 (3번 실패)`.
Runtime evidence: 사람이 검수를 마쳐도 `bad`는 그대로라 '검수 대기'가 계속 같은 숫자로 남음.
Comparison grid:
| 항목 | 현재(R1) | A | B | C |
|---|---|---|---|---|
| 진행 중 문구 | `검수 대기 N건 (3번 실패)` | `판정 실패 N건 · 검수 큐로 보냄` | 열린 검수 큐의 labeler_failed 수로 `검수 대기 N건` (overview API에 값 추가) | 그대로 |
| 완료 문구 | `…검수 큐로 보냈습니다.` | 그대로 | 그대로 | 그대로 |
Question D7: '검수 대기 N건'은 검수 후에도 줄지 않습니다 — 문구를 바꿀까요?
Header: 진행 중 문구
Options:
A) '판정 실패 N건 · 검수 큐로 보냄' (recommended)
숫자는 누적 실패 수 그대로, 문구가 사실과 맞음. API 변경 없음. T4 테스트 문자열만 교체.
B) 실제 대기 수 표시
overview에 열린 labeler_failed 큐 수를 추가해 진짜 대기 건수 표시. 백엔드 · 타입 · 테스트 추가(human ~2h / CC ~15min).
C) 그대로
검수 후에도 '검수 대기' 숫자가 남음.
State: approved
Actual answer: A) '판정 실패 N건 · 검수 큐로 보냄' (recommended) — 사용자 '이어서 진행해주세요'(D7 미응답)를 추천안 진행으로 해석, 2026-10-21. 이의 시 재개방.
Accepted scope: T4 진행 중 문구 교체, API 변경 없음.
History: none

Approval readiness: PASS — R1(D1 답) · R2(D2 답) · R3(D3 답) · R4(D4 답) · R5(D5 답) · R6 · R7('이어서 진행해주세요'를 추천안 진행으로 기록).

### Section 1 — Architecture
- 이슈 4건: R2(장애가 횟수 소진, Codex), R3(남은 .part, Codex), R4(API 경로 범위, Codex), R5(카드 공유, Codex+Claude). 모두 결정 반영.
- 흐름:
```
judge.run_worker (codex_exec)
  lease batch -> pool: gpt.judge_batch
        -> codex_exec._worker: [남은 .part 격리] -> codex exec
             rc0 & task.json      -> _answer
             rc0 & only .part     -> rename -> _answer
             rc!=0 / none         -> backend failure
        <- capacity? (log)  -> sleep(min(5*2^k,30)+U(0,3)) retry <= label_capacity_retries
  collect (successes first)
     success -> put, evidence++, consecutive=0
     usage limit -> release, pause
     other fail -> per doc: evidence>failed_at? fail(+1, 3->bad->검수 큐) : release_docs
                   consecutive++ >= pause_after -> pause(BREAKER_MESSAGE)
     resume -> consecutive=0, evidence++
```

### Section 2 — Code quality
- 이슈 1건: R6(set 순회 순서) 반영. `_pause_message`와 `_latest_attempt` 로그 읽기 통합(T2). 새 추상화 없음.

### Section 3 — Tests
```
CODE PATHS
[+] codex_exec._worker
  ├── [★★★ PLANNED] 지시문 최종 파일명 — test_instruction_names_final_file
  ├── [★★★ PLANNED] rc0 + .part만 → 채택 — test_unrenamed_part_is_adopted
  ├── [★★★ PLANNED] rc!=0 + .part → 거부 — test_part_ignored_on_nonzero_exit
  ├── [★★★ PLANNED] 잘린 .part → parse 격리 — test_truncated_part_quarantined
  └── [★★★ PLANNED] 남은 .part 격리 — test_stale_part_not_adopted
[+] gpt.judge_batch
  ├── [★★★ PLANNED] 용량 1회 후 성공 / 한도까지 실패 / 재시도 0 — test_capacity_*
  └── [★★★ PLANNED] 사용량 한도 비재시도 — test_usage_limit_not_retried
[+] judge.collect (codex_exec)
  ├── [★★★ PLANNED] 단발 실패 계속 — test_isolated_failures_do_not_pause, test_chunk_failures_preserve_peers(갱신)
  ├── [★★★ PLANNED] 연속 실패 정지 · bad 0 — test_consecutive_failures_pause, test_outage_does_not_spend_attempts
  ├── [★★★ PLANNED] 기존 attempts 2 보호 — test_existing_attempts_not_spent_by_outage
  ├── [★★★ PLANNED] 성공·재개 리셋 — test_success_resets_counter, test_resume_resets_counter
  ├── [★★★ PLANNED] 성공 사이 3회 → bad — test_failures_between_successes_count
  ├── [★★★ PLANNED] 성공 먼저 집계 — test_successes_counted_first
  └── [★★★ PLANNED] API 경로 즉시 정지 유지 — test_api_backend_still_pauses_immediately (CRITICAL 회귀)
[+] VoteCache.release_docs — test_release_docs_keeps_attempts
[+] LabelerProgress / Overview — 표시 규칙 6건 + Overview 렌더 1건
USER FLOWS: QA 1~6 (브라우저)
COVERAGE: 계획된 경로 전부 테스트 있음 | GAPS: 0
```
- 폐기 테스트: 없음(갱신 3건: test_chunk_failures_preserve_peers backend/mixed, test_real_context_pause_resume, test_gpt_failures_bounded_per_document paused).

### Section 4 — Performance
- No issues found. `_latest_attempt`는 실패 때만 로그(~300KB) 1회 읽기. `failed_at`는 실행 중 실패 글 수만큼(최대 문서 수) 메모리.

### NOT in scope
- 배포 재시작 시 판정 자동 이어가기 — 별도 작업.
- 검수 큐의 실제 대기 수 표시(R7 B) — 문구로 해결.
- 01 · 02 원문 정정 — 하네스 잠금, 이 계획에서 정정(R1).

### What already exists
- 글 단위 3회 → bad(`votes.py` `fail`), bad → 검수 큐(`route.py:183`), 정지 · 재개(`_pause`, runner), 진행 카드(`LabelerProgress`) — 모두 재사용.

### Failure modes
| 경로 | 운영 실패 | 처리 | 사용자에게 보임 |
|---|---|---|---|
| .part 채택 | 잘린 JSON | parse 격리 → 글 실패 | 판정 실패 건수 |
| 용량 재시도 | 계속 용량 초과 | 2회 후 실패 → 연속 기준 정지 | 정지 사유 문구 |
| 연속 실패 | Codex 로그아웃·장애 | 정지, 횟수 소진 없음 | 정지 사유 + 이어서 진행 |
| 꼬리 문제 글 | 같은 글만 계속 실패 | 정지 → 재개마다 1회 → 3회 후 검수 큐 | 정지 사유, 판정 실패 건수 |
- critical gap 0.

### Worktree parallelization
| Step | Modules touched | Depends on |
|---|---|---|
| T1 | backend/app/llm, backend/tests | — |
| T2 | backend/app/label, backend/app (config), backend/tests | T1 |
| T3 | backend/app/label, backend/tests, docs | T2 |
| T4 | frontend/src/components | — |
- Lane A: T1 → T2 → T3 (backend 공유). Lane B: T4 (독립). 실행: A와 B 동시 시작, A 순차 진행.

### Completion summary
- Step 0: Scope Challenge — scope accepted as-is
- Architecture Review: 4 issues found
- Code Quality Review: 1 issues found
- Test Review: diagram produced, 0 gaps identified
- Performance Review: 0 issues found
- NOT in scope: written
- What already exists: written
- TODOS.md updates: 0 items proposed to user (TODOS.md 없음, 후속은 별도 세션 제안)
- Failure modes: 0 critical gaps flagged
- Unresolved decisions: 0 in this review
- Outside voice: codex, completed (5 findings, 모두 반영)
- Parallelization: 2 lanes, 1 parallel / 3 sequential
- Lake Score: N/A (선택지가 종류 차이)


## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Outside Review | codex (plan-eng-review outside voice) | Independent 2nd opinion | 1 | completed | 5 findings, 5 반영 |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open (모두 결정·반영) | 5 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | issues_found (결정 완료) | score: 7/10 → 9/10, 3 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **OUTSIDE COVERAGE:** codex, plan-review phase, completed, 5 findings(P1 3 · P2 2) → R2~R7로 결정·반영. design phase는 skipped(사용자 범위 축소).
- **CROSS-MODEL:** Claude가 찾은 R1(bad → 검수 큐)과 Codex의 R7(검수 대기 수치)이 같은 사실(route.py)에서 출발해 서로 보강. Codex의 R2 · R3 · R4는 Claude 검토에서 놓친 항목.
- **VERDICT:** ENG + DESIGN 결정 완료 — 모든 발견 사항이 계획에 반영되어 구현 가능(Eng 상태는 해결된 이슈가 있어 issues_open으로 기록).

NO UNRESOLVED DECISIONS
