# GPT(Codex) 판정 묶음 실패 내성 — 설계

기획 승인: 2026-10-21, 추천안 D (`01-brainstorm.md`).

## 동작 요약
| 상황 | 지금 | 바뀐 뒤 |
|---|---|---|
| Codex가 답을 `.part`에만 남김 | 백엔드 실패 → 20건 실패 1회 + 전체 정지 | 프로세스가 정상 종료(코드 0)했고 `.part`가 스키마를 통과하면 `task-{n}.json`으로 옮겨 채택. 실패 아님 |
| "model at capacity" | 백엔드 실패 → 전체 정지 | 같은 묶음을 대기 후 최대 2회 더 실행. 그래도 실패하면 아래 "단발 실패" |
| 단발 실패 (위 외 백엔드 실패·시간 초과) | 20건 실패 1회 + 전체 정지 | 20건 실패 1회, **판정 계속**. 글은 다시 임대되어 최대 3회 시도 후 `bad`(판정 실패로 제외) |
| 성공 없이 묶음 연속 5회 실패 | (매번 정지) | 일시정지 + 사유 "GPT 판정이 연속으로 실패해 멈췄습니다…" |
| 사용량 한도 | 임대 해제 + 즉시 정지 | 변경 없음 |
| 형식 오류(parse/schema) | 해당 글 실패, 계속 | 변경 없음 |

## 구조와 변경 위치

### 1. `backend/app/llm/codex_exec.py` — `_worker`
- 지시문 첫 줄을 바꾼다(최종 파일명 명시):
  `답 JSON만 answers/task-{n}.json.part에 쓴 뒤 answers/task-{n}.json으로 이름을 바꿔라 (mv answers/task-{n}.json.part answers/task-{n}.json)`
- 프로세스가 코드 0으로 끝났는데 `answers/task-{n}.json`이 없고 `answers/task-{n}.json.part`가 있으면 `.part`를 `task-{n}.json`으로 `replace`한 뒤 기존 `_answer()`로 검증한다. 검증 실패는 기존 경로(`answers/bad/` 격리 + parse/schema 오류)를 탄다.
- 코드 0이 아니면 `.part`가 있어도 채택하지 않는다(쓰다 만 파일일 수 있음). 기존 `failure('backend')`.
- 영향: `run_many`를 쓰는 곳은 `gpt.judge_batch` 하나, `CodexExecBackend`는 registry 경유 다른 단계가 쓴다. 지시문·`.part` 채택은 공통 개선이라 함께 적용된다(동작이 엄격해지는 방향이 아님).

### 2. `backend/app/label/gpt.py` — `judge_batch`
- codex_exec 결과가 실패이고 이번 시도 로그(`--- attempt ---` 이후)에 용량 표지(`at capacity`, `capacity`)가 있으면 같은 `run_id`로 `run_many`를 다시 부른다. 최대 `settings.label_capacity_retries`(기본 2)회 추가. 대기: `min(5·2^k, 30)`초 + 0~3초 무작위.
  - 같은 `run_id` 재실행은 기존 설계상 안전하다(manifest 동일, 답 없으면 새 attempt를 로그에 덧붙임).
- 로그 읽기는 기존 `_pause_message`와 같은 방식(최신 attempt만, 호출자에 노출 안 함)으로 함수 하나로 묶는다: `_latest_attempt(run_id) -> str`.
- 사용량 한도 판정·메시지는 변경 없음. 그 밖의 실패는 지금처럼 `LabelerPaused(message, usage_limit=False)`를 던진다(판단은 judge가 함).

### 3. `backend/app/label/judge.py` — `run_worker`의 GPT `collect`
- 새 지역 상태 `consecutive_failures = 0`.
- 묶음 결과별:
  - 성공(`votes, missing` 반환): `consecutive_failures = 0`.
  - `LabelerPaused`, `usage_limit=False`: 묶음 글 `cache.fail(..., 'gpt_backend_failed')`(기존), `consecutive_failures += 1`. **`paused`로 설정하지 않는다.** 단 `consecutive_failures >= settings.label_failure_pause_after`(기본 5)면 `paused = LabelerPaused(BREAKER_MESSAGE)`.
  - `LabelerPaused`, `usage_limit=True`: 기존대로 `paused` 설정(즉시 정지, 글 실패 기록 없음).
- 정지 후 "이어서 진행"으로 풀리면 `consecutive_failures = 0`.
- `bad` 글은 이미 `progress = (done+bad)/total`, 남은 글 0이면 `judge_done` — 완료를 막지 않는다(테스트로 확인).
- `BREAKER_MESSAGE = 'GPT 판정이 연속으로 실패해 멈췄습니다. 잠시 뒤 이어서 진행하거나 설정에서 API 경로로 바꾸세요.'`

### 4. `backend/app/config.py`
- `label_capacity_retries: int = 2` (0 이상), `label_failure_pause_after: int = 5` (1 이상). 빈 값이면 기본값(기존 `empty_stage_setting_uses_default` 목록에 추가).

### 5. `frontend/src/components/label/LabelerProgress.tsx`
- `progress.bad > 0`이고 처리 중·정지 상태면(대기·완료 제외) **건수 줄(`N건 판정 · M건 남음`) 바로 아래**에 한 줄: `제외 {bad}건 (3번 실패)` (`ds-t-caption`). 이 `<p>`에 `title="3번 시도해도 판정하지 못한 글은 학습에서 빠집니다."`를 두고, 같은 설명을 화면낭독기용 숨김 텍스트(Tailwind `sr-only`, `GateTable.tsx`와 같은 방식)로 붙인다. (D3·D4)
- `state === 'done'`이고 `bad > 0`이면 별도 줄 대신 완료 문구를 `판정을 마쳤습니다. {bad}건은 판정하지 못해 제외했습니다.`로 바꾼다. (D2)
- `bad`가 0·없음이면 둘 다 표시하지 않는다(지금과 동일).
- 데이터는 이미 overview `progress.gpt.bad`로 내려온다. API·타입 변경 없음.

## 데이터와 API
- DB 스키마 변경 없음. `votes.attempts`·`status='bad'`·`last_error` 기존 칼럼 사용.
- API 변경 없음. 설정 2개 추가(환경변수 `LABEL_CAPACITY_RETRIES`, `LABEL_FAILURE_PAUSE_AFTER`).

## 권한
- 변경 없음. 운영 워커 내부 동작만 바뀐다.

## 실패 상태
| 경우 | 처리 |
|---|---|
| `.part`가 잘렸거나 스키마 위반 | `answers/bad/` 격리, parse/schema 오류 → 해당 글 실패(기존) |
| 용량 재시도 중 정지/중단 요청 | 재시도 대기는 짧고(≤33초) 묶음 스레드 안에서 끝남. 정지는 기존처럼 진행 중 묶음을 수거한 뒤 반영 |
| 모든 묶음 실패(Codex 장애·로그아웃) | 연속 5회에서 정지. 동시 20개면 이미 떠 있던 묶음까지 최대 약 20묶음(400건)이 실패 1회를 얻을 수 있음 — 3회 전에 정지하므로 제외는 발생하지 않음 |
| 묶음이 계속 같은 글 때문에 실패 | 그 묶음 글들이 각각 3회 실패 후 제외. 다른 묶음은 정상 진행이라 연속 카운터는 리셋됨 |

## UI 상태
- 이 작업의 UI는 진행 카드 문구 변경뿐이다. 레이아웃·반응형 변화 없음(문단 한 줄, 기존 caption 스타일). 좁은 화면에서도 기존 `<p>`처럼 줄바꿈된다.
- 카드 줄 순서: 진행 막대 → 건수 → **제외 건수(진행 중·정지일 때만)** → 상태 문구 → 정지 사유 → 예상 시간 → 버튼.

| 상태 | bad = 0 | bad > 0 |
|---|---|---|
| 처리 중 / 정지 | 지금과 동일 | 건수 줄 아래 `제외 N건 (3번 실패)` |
| 완료 | `판정을 마쳤습니다.` | `판정을 마쳤습니다. N건은 판정하지 못해 제외했습니다.` (별도 줄 없음) |
| 대기 | 지금과 동일 | 표시 안 함 |

- 정지 사유는 기존 `progress.reason` 표시를 그대로 쓴다(연속 실패 정지 문구 포함).
- 접근성: 일반 텍스트(`<p>`), 숫자는 `ko-KR` 형식, 설명은 title + 화면낭독기 텍스트로 제공. 색만으로 의미를 전달하지 않음.

## 테스트 전략
- 백엔드 단위: codex_exec(`.part` 채택·코드≠0 거부·지시문 파일명), gpt(용량 재시도 횟수·대기 호출·사용량 한도 비재시도), judge(단발 실패 후 계속·연속 N회 정지·성공 시 리셋·3회 실패 → bad·bad 있어도 done).
- 기존 테스트 중 "백엔드 실패 → paused"를 기대하는 `test_judge_concurrency.py`, `test_judge.py` 케이스는 새 동작으로 갱신(연속 기준 1로 설정해 기존 의미 보존 가능).
- 프런트: `LabelerProgress` 렌더 테스트(bad 0 숨김 / N 표시).

## GSTACK REVIEW REPORT

| Run | Status | Findings |
|---|---|---|
| plan-design-review (2026-10-21, 텍스트 전용, 사용자 요청으로 UI 3항목만) | issues_found → 모두 결정 | 3건 |

- 설계 완성도(UI 부분): 7/10 → 9/10. 남은 1점: 시각 시안 없음(디자이너 도구 미설정, 한 줄 변경이라 생략 합의).
- D2 완료 문구에 제외 건수 포함 — 승인(추천안).
- D3 본문은 `제외 N건 (3번 실패)`로 짧게, 설명은 title·화면낭독기 텍스트 — 승인(추천안).
- D4 제외 줄은 건수 줄 바로 아래 — 승인(추천안).
- 외부 의견(Codex/서브에이전트): 범위 축소 합의로 실행 안 함(outside_status: skipped).

VERDICT: UI 범위 설계 결정 완료, 구현 가능.

NO UNRESOLVED DECISIONS
