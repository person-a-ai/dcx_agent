# 브라우저 QA — gpt-batch-resilience (report-only, gstack qa-only)

- 날짜: 2026-10-22 · 브랜치 feature/gpt-batch-resilience · 대상 커밋 11ec883
- 대상 URL: http://localhost:3412/pipeline/labeling?sid=s1ef426ca23624027b2acddff133fa4b1
- 서버: `.claude/launch.json` qa-api(8412, uvicorn) · qa-web(3412, next dev). 데이터는 scratchpad `qa-data/`(운영 세라젬 세션 복사본). `LABEL_GPT_BACKEND=codex_exec`, `CODEX_BIN=backend/tests/fakes/fake_codex.py`, `LABEL_CONCURRENCY=8`, `LABEL_BATCH_SIZE=20`, `JEV_BACKEND=fake`(GPT 단독).
- 브라우저: Claude 내장 브라우저. 모드: Full(계획 §4 시나리오 1~6). 수정 없음.
- 시나리오 사이 fake 모드는 `qa-mode.env` 변경 + API 재시작(워커가 API 하위 프로세스).

## Charters (탐색 전 작성)
| ID | 진입 | 기대 결과 | 위험 | 종료 조건 |
|---|---|---|---|---|
| QA1 | `FAKE_CODEX_LABEL_MODE=no_rename`, 새 버전 → 라벨링 시작 | 정지 0회로 5,688건 완료, 카드 `판정을 마쳤습니다.`, llm_runs 답이 모두 `answers/task-0.json`(.part 잔여 0) | `.part` 미채택 시 전 묶음 실패·정지 | 완료 또는 정지 |
| QA2 | `capacity_once` | 정지 0회 완료, run 폴더마다 invocations 2줄 | 재시도 미동작 → 연속 실패 정지 | 완료 또는 정지 |
| QA3 | `flaky`(첫 글 ID 끝 16진 0~3 묶음 항상 실패) | 정지 없이 완료(또는 꼬리 연속 실패 정지 시 재개로 완료), 진행 중 `판정 실패 N건 · 검수 큐로 보냄`, 완료 문구 건수 = bad 수 = 검수 큐 '판정 실패' 건수 | 단발 실패가 전체 정지 유발, 건수 불일치 | 완료 |
| QA4 | `capacity` + `LABEL_CAPACITY_RETRIES=0` | 시작 직후 정지, 사유 = 연속 실패 문구, bad 0, "이어서 진행" 버튼 | 장애가 시도 횟수 소진 | 정지 확인 |
| QA5 | 375px 폭, QA3 화면 | 실패 문구 줄바꿈, 가로 스크롤 없음 | 좁은 화면 넘침 | 스크린샷 |
| QA6 | QA4 뒤 `normal`로 바꾸고 "이어서 진행" | 완료, bad 0 | 장애 중 횟수 소진(R2) | 완료 |

## 결과 요약
| ID | 결과 | 근거 |
|---|---|---|
| QA1 `no_rename` | **PASS** | v4 run `done`, 정지 0회(action 없음). votes 5,688 done·attempts 0. llm_runs 285개 모두 `answers/task-0.json`, `.part` 잔여 0, `answers/bad` 0, invocations 각 1. 카드 `판정을 마쳤습니다.` — `qa-screens/qa1-done.jpg` |
| QA2 `capacity_once` | **PASS** | v5 run `done`, 정지 0회. 285개 run 모두 invocations 2줄(용량 1회 → 재시도 성공). 5,688 done·attempts 0 — `qa-screens/qa2-done.jpg` |
| QA3 `flaky` (계획 그대로: 동시 8·묶음 20) | **PASS** | v6 run `done`, 정지 0회. bad 144(attempts 3, `gpt_backend_failed`) = 검수 큐 `labeler_failed` open 144 = 카드 `판정을 마쳤습니다. 144건은 판정하지 못해 검수 큐로 보냈습니다.` — `qa-screens/qa3-done.jpg` |
| QA3b `flaky`, 동시 1 (F1 실경로 확인) | **PASS** | v7 run `done`, 정지 0회. bad 128 = 검수 큐 128. 동시 1에서도 실패 묶음이 다른 묶음을 막지 않음 |
| QA3c `flaky`, 동시 1·묶음 5 (진행 중 화면 확보용) | **PASS** | 진행 중 `판정 실패 86건 · 검수 큐로 보냄`이 건수 줄 아래·`처리 중…` 위 — `qa-screens/qa3c-running-failures.jpg`. 연속 실패 정지 3회 발생(아래 관찰) 후 재개로 v8 `done`, bad 114 = 검수 큐 114 = 완료 문구 114건 — `qa-screens/qa3c-done.jpg`, 정지 화면 `qa-screens/qa3c-breaker-paused.jpg` |
| QA4 `capacity` + `LABEL_CAPACITY_RETRIES=0` | **PASS** | 시작 직후 v9 run `paused`, 사유 `GPT 판정이 연속으로 실패해 멈췄습니다. 잠시 뒤 이어서 진행하거나 설정에서 API 경로로 바꾸세요.`, "이어서 진행"·"중단" 버튼. votes 5,688 pending·attempts 0, bad 0. 12묶음 각 invocations 1(재시도 없음) — `qa-screens/qa4-breaker-paused.jpg` |
| QA5 375px | **PASS** | 375×812에서 `scrollWidth 375 = clientWidth 375`(가로 스크롤 없음), 판정 실패 줄 `white-space: normal`, 폭 221px로 카드 안에 표시. 정지 상태에서도 줄 표시(F2) — `qa-screens/qa5-375-paused-failures.jpg` |
| QA6 장애 후 `normal`로 이어서 진행 | **PASS** | QA4 정지 워커(capacity 환경 상속)를 종료하고 API를 `normal`로 재시작 → 카드 상태 "중단됨 · 이어서 진행" → 이어서 진행 → v9 새 run `done`. 5,688 done·attempts 0, bad 0, 검수 큐 0 — `qa-screens/qa6-resumed-done.jpg` |

## 관찰 (결함 아님)
- O1 QA3c(묶음 5, fake 실패율 약 25%)에서 연속 실패 정지가 3회 났다. 실패 묶음 5개가 무작위로 연달아 나온 경우로, 직전 실패 묶음 첫 글 ID 끝자리 2·2·0·0·1을 확인했다. 기준 5 차단기가 설계대로 동작한 것이고, 계획 구성(묶음 20)의 QA3·QA3b에서는 정지가 없었다. 실패율이 매우 높은 장애에서는 정지·재개가 반복될 수 있다는 운영 참고 사항.
- O2 QA6은 정지 워커가 장애 환경 변수를 물려받아 살아 있으므로, 워커를 종료하고 API를 재시작해 "중단됨 → 이어서 진행"(새 워커) 경로로 확인했다. 같은 워커에서 재개하는 경로는 QA3c의 재개 3회로 확인했다.
- O3 첫 재개 클릭이 적용되지 않은 적이 한 번 있었다. 원인은 브라우저 도구가 스크롤 뒤 오래된 좌표로 카드 위쪽 다른 버튼을 누른 것이다. 카드의 "이어서 진행"을 다시 눌러 정상 재개했고, 앱 결함은 아니다.
- 콘솔 오류: API 재시작 중 `ERR_CONNECTION_REFUSED`(예상됨), 브라우저 도구가 주입한 익명 스크립트의 `getComputedStyle` 오류. 앱 코드 오류는 없음.

## 판정
**PASS**: 계획 §4 시나리오 1~6 모두 통과했고 수정할 발견은 없다. 테스트 프레임워크는 pytest·vitest가 있다.
