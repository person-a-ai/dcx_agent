# QA Plan — label-import (외부 라벨 결과 가져오기)

## 1. Scope

- 대상: 브랜치 `feature/label-import`, 하네스 실행 `label-import`(full). 근거 문서: [01-brainstorm.md](01-brainstorm.md), [02-design.md](02-design.md), [03-plan.md](03-plan.md).
- 표면: **non-ui**. 서버 명령(`dcxctl import-labels`, `python -m app.importer`)과 백엔드 저장 형식·완료 판정. 웹 화면은 바꾸지 않는다. 브라우저 QA는 하지 않는다(nonUiReason은 plan-bundle 참고). 모든 시나리오는 pytest 또는 CLI 실행으로 확인한다.
- 포함: 입력 읽기·검증, 프로젝트·수집본·전처리·라벨·내보내기 생성, 이어서 하기, 가져온 라벨 보호, `dcxctl` 하위 명령.
- 제외: 웹 업로드, 확률 CSV, GPT·Jev 재판정, 감사 라운드, `naver_cafe` 외 채널, 6단계 이후 기능 자체의 품질.

## 2. Acceptance Criteria

01-brainstorm의 AC와 02-design의 결정을 그대로 쓴다.

| AC | 내용 | 시나리오 |
|---|---|---|
| AC1 | 명령 한 번으로 새 프로젝트, 0단계 `.`·기본값 | QA-E2E-001, QA-E2E-004 |
| AC2 | zip/CSV 입력, 필수 컬럼 없으면 저장 전 멈춤 | QA-E2E-002, QA-NEG-001, QA-NEG-002, QA-NEG-003 |
| AC3 | 수집본이 '완료'로 인정, 크롤링 요구 없음 | QA-E2E-001, QA-REG-004 |
| AC4 | 기존 전처리 코드로 실행, 진행률 출력, 웹에서도 같은 run | QA-E2E-001, QA-E2E-003, QA-REG-003 |
| AC5 | done 판정이 최종 라벨(출처 imported), 4단계 완료, 모델 호출 없음 | QA-E2E-001, QA-NEG-008, QA-REG-001 |
| AC6 | 판정 버전 다르면 멈춤 | QA-NEG-004 |
| AC7 | 판정 없는 글 개수 보고, 라벨·내보내기에서 제외 | QA-EDGE-004 |
| AC8 | 끊겨도 이어서, 같은 파일로 프로젝트 두 개 없음 | QA-E2E-003, QA-EDGE-001, QA-EDGE-002, QA-NEG-007 |
| AC9 | 웹에서 6단계(세그먼트) 진행 가능(= 내보내기 완료) | QA-E2E-001, QA-E2E-005 |
| AC10 | 승인된 검증 명령 통과, 모델·임베딩 호출 없음 | QA-REG-005 |
| D-1 (설계 7절) | 서버 점검 중에는 `dcxctl import-labels` 거절 | QA-NEG-009 |
| D-2 (설계 3.1) | 원문 닉네임·지식인 답변 저장 안 함 | QA-EDGE-005 |

## 3. Critical User Journeys

| 순위 | 여정 | 위험 등급 |
|---|---|---|
| J1 | 운영자가 서버에서 zip으로 가져오기를 실행해 끝까지 완료한다 | 데이터 쓰기(가져오기) · 핵심 경로 → P0 |
| J2 | 가져오기가 중간에 끊긴 뒤 다시 실행해 이어서 끝낸다 | 데이터 손상 위험 → P0 |
| J3 | 잘못된 파일을 넣었을 때 아무것도 만들지 않고 이유를 본다 | 데이터 오염 방지 → P0 |
| J4 | 가져온 프로젝트를 웹에서 열었을 때 4단계가 가져온 라벨을 지우거나 다시 판정하지 않는다 | 데이터 손실 → P0 |
| J5 | 기존 프로젝트(크롤링·판정 경로)가 예전처럼 동작한다 | 회귀 → P0 |

인증·결제 여정은 없다. `dcxctl`은 서버 사용자 셸 권한으로만 실행한다.

## 4. E2E Scenarios

QA-E2E-001
Priority: P0
Type: Acceptance / E2E (pytest `tests/importer/test_steps.py::test_full_import_reaches_stage6`)
Given: 빈 `LOCAL_DATA_DIR`, `embed_backend=fake`, done 6행(core 5·non 1), skipped 1행, 지식인 1행이 든 결과 CSV
When: `steps.run_import(<csv>)`를 실행한다
Then:
  - 반환 `sid`가 `imp-` + 파일 sha256 앞 12자리다
  - `session.json`의 `projectContext.bk`, `oneLiner`, `researchQuestion.text`가 모두 `.`이다
  - `projectContext.taskMode`가 `explore`이다
  - `keywords`가 CSV 키워드 2개를 `approved`로 담는다
  - `crawl.control.phase_state(sid,'c1')`이 `done`이다
  - `prep.status`가 `done`이다
  - `labeling.status`가 `done`이고 `labelerMode`가 `imported`이다
  - `step`이 `cluster-start`이다
  - `known.filter.read_export`가 5건(core+supporting)을 돌려주고 모두 `source == 'imported'`다
  - `routers.sessions._completion`의 `crawlDone`, `prepDone`, `labelingDone`, `exportDone`이 모두 참이다
  - 로그 마지막 줄에 `0단계` 경고가 있다

QA-E2E-002
Priority: P0
Type: Acceptance (pytest `tests/importer/test_read.py::test_zip_picks_result_csv_and_ignores_probs`)
Given: 폴더 안에 `*_full.csv`와 `*_full_probs.csv`가 든 zip
When: `read.open_source(zip)` 후 `read.scan`
Then:
  - `source.name`이 결과 CSV 이름이다
  - `source.sha256`이 같은 CSV를 직접 연 값과 같다
  - 확률 CSV는 읽지 않는다(스캔 done 수가 결과 CSV의 done 수와 같다)

QA-E2E-003
Priority: P0
Type: Recovery / E2E (pytest `test_resume_after_interruption`[4개 매개변수])
Given: QA-E2E-001과 같은 입력
When: 수집본 등록 / 전처리 / 라벨 넣기 / 내보내기 중 한 단계에서 `KeyboardInterrupt`가 난 뒤 같은 명령을 다시 실행한다
Then:
  - 두 번째 실행이 예외 없이 끝난다
  - `step`이 `cluster-start`이다
  - `training.exportRef`가 있다
  - 같은 `sid` 하나만 존재한다

QA-E2E-004
Priority: P1
Type: CLI (pytest `tests/importer/test_main.py`, `tests/ops/test_dcxctl.py::test_import_labels_runs_release_importer`)
Given: 현재 릴리스와 가짜 `.venv/bin/python`이 있는 macmini 테스트 루트
When: `dcxctl import-labels <file> --sid imp-a`
Then:
  - 종료 코드 0
  - 릴리스 python이 `app.importer`, 파일의 절대 경로, `--sid`, `imp-a`를 인자로 받는다
  - `python -m app.importer` 성공 시 종료 코드 0, 표준 출력에 로그가 찍힌다

QA-E2E-005
Priority: P1
Type: Smoke / 실제 데이터(수동, 사용자 확인 후)
Given: 개발 PC, 빈 임시 `LOCAL_DATA_DIR`, `EMBED_BACKEND=fake`, 사용자가 준 `네이버 카페.zip`(197,913행)
When: `cd backend && LOCAL_DATA_DIR=<tmp> EMBED_BACKEND=fake AUTHOR_SALT_PATH=<tmp>/.salt .venv/bin/python -m app.importer "<zip>"`
Then:
  - 종료 코드 0
  - 검증 줄: `197,913행 · done 195,446`, 건너뜀 `skipped 2,467`
  - `[4/5]` 줄의 넣은 수 + 전처리에서 빠짐 = 195,446
  - `classified/<sid>/v1/gen-*/relevant.jsonl` 줄 수가 `[5/5]`의 core+supporting 수와 같다
  - 실행 시간과 최대 메모리(`/usr/bin/time -l`)를 기록한다(판정 기준 아님, 서버 실행 계획용)
  - 서버(Mac mini) 실제 실행은 이 결과를 보고 사용자가 결정한다

## 5. Negative Scenarios

QA-NEG-001
Priority: P0
Type: Negative (pytest `test_missing_columns_named`)
Given: `signal`, `url` 컬럼이 없는 CSV
When: `read.scan`
Then:
  - `ImportError_` 메시지에 파일 이름, `signal`, `url`이 들어 있다

QA-NEG-002
Priority: P0
Type: Negative (pytest `test_zip_with_two_result_csvs_rejected`)
Given: 결과 CSV 후보가 두 개인 zip
When: `read.open_source`
Then:
  - `ImportError_` 메시지에 `결과 CSV`가 들어 있다

QA-NEG-003
Priority: P0
Type: Negative / 무변경 (pytest `test_invalid_file_creates_nothing`)
Given: 검증에 실패하는 CSV
When: `steps.run_import`
Then:
  - `ImportError_`가 난다
  - `LOCAL_DATA_DIR/sessions`에 프로젝트 폴더가 생기지 않는다
  - `LOCAL_DATA_DIR/crawl`에 폴더가 생기지 않는다

QA-NEG-004
Priority: P0
Type: Negative (pytest `test_scan_rejects_invalid_rows[questions_version]`)
Given: `questions_version=q2`인 done 행
When: `read.scan`
Then:
  - 메시지에 `판정 버전`과 행 번호가 들어 있다

QA-NEG-005
Priority: P0
Type: Negative (pytest `test_scan_rejects_invalid_rows[...]`, `test_duplicate_doc_id_rejected`)
Given: 각각 잘못된 `doc_id`, 등급 불일치, 태그 값 `2`, 허용 밖 `signal`, 중복 `doc_id`가 있는 CSV
When: `read.scan`
Then:
  - 각 경우 메시지에 `doc_id` / `등급` / `태그` / `signal` / `중복`이 들어 있다
  - 예시는 최대 5개까지 출력된다

QA-NEG-006
Priority: P1
Type: Negative (pytest `test_prep_failure_reported`)
Given: 전처리 run이 `failed`로 끝난다
When: `steps.run_import`
Then:
  - 두 번 시도한 뒤 `ImportError_` 메시지에 `전처리`가 들어 있다
  - `labeling`이 `done`으로 바뀌지 않는다

QA-NEG-007
Priority: P0
Type: Negative (pytest `test_same_sid_different_file_rejected`)
Given: `--sid imp-fixed`로 이미 가져온 프로젝트
When: 다른 CSV로 `--sid imp-fixed`를 다시 실행한다
Then:
  - `ImportError_` 메시지에 `다른 파일`이 들어 있다
  - 기존 프로젝트의 `training.exportRef`가 바뀌지 않는다

QA-NEG-008
Priority: P0
Type: Negative / 권한 (pytest `tests/label/test_imported_mode.py::test_label_api_refuses_judging`)
Given: `labelerMode=imported` 세션
When: `POST /label/{sid}/start`, `POST /label/{sid}/mode`, `POST /label/{sid}/judge/gpt/resume`
Then:
  - 세 응답 모두 409다
  - 응답 본문에 `가져온 라벨`이 들어 있다
  - `work` run DB에 judge run이 생기지 않는다

QA-NEG-009
Priority: P1
Type: Negative (pytest `tests/ops/test_dcxctl.py::test_import_labels_refused_in_maintenance`, `test_import_labels_requires_file`)
Given: `shared/maintenance` 파일이 있음 / 인자 없음
When: `dcxctl import-labels …` / `dcxctl import-labels`
Then:
  - 점검 중: 종료 코드 1, stderr에 `점검`, 릴리스 python이 실행되지 않는다
  - 인자 없음: 종료 코드 2

QA-NEG-010
Priority: P1
Type: Negative (pytest `test_main_import_error`, `test_main_interrupt`)
Given: `run_import`가 `ImportError_` / `KeyboardInterrupt`를 낸다
When: `python -m app.importer`
Then:
  - 각각 종료 코드 1 / 130
  - stderr에 오류 메시지 / `다시 실행`이 찍힌다

QA-NEG-011
Priority: P0
Type: Concurrency (pytest `test_concurrent_import_refused`)
Given: 같은 `sid`의 가져오기 잠금(`imports/<sid>.lock`)을 다른 프로세스가 잡고 있다
When: 같은 파일로 가져오기를 실행한다
Then:
  - `ImportError_` 메시지에 `이미 실행 중`이 들어 있다
  - `sessions/<sid>`가 생기지 않는다

## 6. Edge Cases

catalog의 Input and boundary, Concurrency and repetition, Recovery paths, Data volume 항목을 적용했다. Permission and tenancy와 Time and locale은 아래 EDGE-005와 날짜 매핑으로만 다룬다. Navigation and lifecycle은 UI가 없어 해당 없다.

QA-EDGE-001
Priority: P0
Type: Repetition (pytest `test_rerun_is_noop`)
Given: 끝까지 가져온 프로젝트
When: 같은 명령을 다시 실행한다
Then:
  - 같은 `sid`를 돌려준다
  - `training.exportRef`가 바뀌지 않는다(새 내보내기 없음)

QA-EDGE-002
Priority: P0
Type: Recovery / partial write (pytest `test_partial_collection_is_rebuilt`)
Given: 수집본 문서를 쓰는 중에 끊겨 `collections/c1.partial`만 남았다
When: 다시 실행한다
Then:
  - `c1.partial`이 없어진다
  - `c1`이 생기고 `phase_state == 'done'`이다

QA-EDGE-003
Priority: P1
Type: Input boundary (pytest `test_records_map_to_doc_and_label`)
Given: 댓글 칸이 목록 문자열 / 깨진 문자열 / `[]`, 날짜가 `2026.03.30. 22:02`, Non 행의 `signal`이 빈 칸
When: `read.iter_records`
Then:
  - 목록 문자열은 항목마다 댓글 하나(`depth=0`, `date=""`, `author_hash=""`)가 된다
  - 깨진 문자열은 댓글 하나가 된다
  - `date`가 `2026-03-30`이다
  - Non 행의 `signal`이 null, `reason_code`가 CSV 값이다
  - 결과 문서가 `crawl.schema.Doc` 검증을 통과한다

QA-EDGE-004
Priority: P1
Type: Data boundary (pytest `test_short_body_dropped_by_prep_is_reported`, `test_unlabeled_prepared_docs_use_partial_export`)
Given: done이지만 본문이 전처리 기준(10자) 미만인 행
When: 가져오기를 끝까지 실행한다
Then:
  - `[4/5]` 로그의 `전처리에서 빠짐`이 1이다
  - 그 `doc_id`가 `final`에 없다
  - 내보내기가 성공한다
  - `unlabeled > 0`이면 `export.write(partial=True)`로 호출되고 `training.exportPartial`이 참이다

QA-EDGE-005
Priority: P1
Type: Privacy (pytest `test_records_do_not_keep_nicknames_or_answers`)
Given: `author_nickname`, `comment_nicknames`, `answers`에 값이 있는 행
When: 수집본 문서를 만든다
Then:
  - 문서 JSON 어디에도 원문 닉네임 문자열이 없다
  - `author_hash`가 16자리 16진수다
  - 문서에 `answers` 키가 없다

QA-EDGE-006
Priority: P2
Type: Input boundary (pytest `test_blank_keyword_becomes_dot`)
Given: `keyword`가 빈 done 행
When: 가져오기
Then:
  - 그 문서의 `kw`가 `.`이다
  - 수집 큐 `add_urls`가 실패하지 않는다

QA-EDGE-007
Priority: P2
Type: Data volume (QA-E2E-005에서 관찰)
Given: 1GB zip
When: 가져오기
Then:
  - 압축을 디스크에 풀지 않는다(작업 폴더에 CSV 사본이 없다)
  - 최대 메모리를 기록한다(URL 목록 외 전체 행을 메모리에 올리지 않음)

## 7. Regression Scope

변경 함수의 호출처를 찾았다: `label.route.rebuild_queue/rebuild_final/sync`(judge.py, labeling_v2.py, overview.py), `context.stale._judges_complete`(judge_done, reconcile_judge_done), `routers.prep.run`, `label.overview.overview`(report.label_part, export.write_stage5), `ops/macmini/dcxctl`.

QA-REG-001
Priority: P0
Type: Regression (기존 `tests/test_integration_stage3_5.py`)
Given: cross 모드(Jev+GPT) 통합 흐름
When: 기존 테스트를 실행한다
Then:
  - 통과한다(판정·사람 검수·감사 라운드 1회·학습·내보내기 동작이 그대로다)

QA-REG-002
Priority: P0
Type: Regression (기존 `tests/label/*`)
Given: gpt_only·model 모드의 final 재생성, 규칙 버전 변경 시 삭제
When: 기존 라벨 테스트를 실행한다
Then:
  - 통과한다
  - 새 테스트 `test_version_change_does_not_delete_imported_rows`에서 imported 행 3개가 남는다

QA-REG-003
Priority: P0
Type: Regression (기존 `tests/prep/*`, `test_router_uses_start_prep`)
Given: `POST /prep/{sid}/run`
When: 전처리 시작·재사용·실행 중 재요청
Then:
  - 응답 형식(`status, runId, progress, reused`)이 이전과 같다
  - 기존 prep 테스트가 통과한다

QA-REG-004
Priority: P1
Type: Regression (기존 `tests/crawl/*`)
Given: 크롤러가 만든 수집본
When: 기존 수집 테스트
Then:
  - 통과한다(수집 코드는 바꾸지 않음)

QA-REG-005
Priority: P0
Type: Regression (하네스 검증 명령 4개)
Given: 브랜치 최종 커밋
When: `backend/.venv/bin/python -m pytest backend/tests -q`, `npm --prefix frontend run lint`, `npm --prefix frontend run build`, `npm --prefix frontend test`
Then:
  - 네 명령 모두 종료 코드 0
  - `tests/test_no_network.py`가 통과한다(외부 호출 없음)

QA-REG-006
Priority: P1
Type: Regression (기존 `tests/ops/test_dcxctl.py`)
Given: `status`, `deploy`, `rollback`
When: 기존 ops 테스트
Then:
  - 통과한다

QA-REG-007
Priority: P1
Type: Regression (`tests/label/test_imported_mode.py::test_overview_reports_imported_totals` + 기존 overview 테스트)
Given: cross·gpt_only 세션의 `GET /label/{sid}/overview`
When: 기존 테스트
Then:
  - 응답 키·값이 이전과 같다
  - imported 세션에서는 `labelerAccuracy.jev`, `labelerAccuracy.gpt`가 null이고 분포 합계가 final 수와 같다

## 8. Test Data / Preconditions

- pytest: `tests/importer/conftest.py`의 `row()`, `write_csv()`, `write_zip()`, `salt` 픽스처. 공용 `data_dir`, `client` 픽스처(`tests/conftest.py`). `embed_backend='fake'`. `runner.start`·`runner.status`는 가짜로 바꾸고, 전처리는 `pipeline.run_prep`을 세션 잠금 밖에서 직접 실행한다(03-plan T4 픽스처).
- ops: `tests/ops/conftest.py`의 `macmini` 픽스처, `DCX_BASH=/bin/bash`.
- 실제 데이터(QA-E2E-005): `~/Downloads/네이버 카페.zip`, 개발 PC, 빈 임시 데이터 폴더, `EMBED_BACKEND=fake`. 사용자 데이터이므로 저장소에 넣지 않는다. 결과 폴더는 확인 후 지운다.
- 가상환경: worktree의 `backend/.venv`에 CI와 같은 의존성(`requirements.txt`, `requirements-dev.txt`, `constraints.txt`)을 설치한다(03-plan "실행 환경 준비"). 하네스 `prepare`는 Python 의존성을 설치하지 않는다. 구현 전 기준선 pytest를 한 번 돌려 기존 실패가 없는지 확인한다.

## 9. Priority

- P0: 데이터를 쓰거나 지우는 경로(가져오기 생성·이어하기·무변경 실패·가져온 라벨 보호)와 기존 경로 회귀.
- P1: CLI 표면, 실패 보고, 개수 보고, 실제 데이터 스모크.
- P2: 드문 입력(빈 키워드), 관찰 위주 항목(메모리).

## 10. Expected Result

- 자동 시나리오: 해당 pytest가 통과하면 PASS. 실행하지 못하면 NOT_RUN, 환경 문제면 BLOCKED로 적는다. PASS로 바꿔 적지 않는다.
- QA-E2E-005: 사용자가 실행을 허락한 뒤 개발 PC에서 한 번 실행하고, 출력 로그·실행 시간·메모리를 `docs/development/label-import/qa/QA-E2E-005.md`에 남긴다. 허락이 없으면 NOT_RUN이다.
- 확인할 수 없는 약속: 웹 6단계 화면이 가져온 프로젝트를 실제로 그리는지는 화면 QA 범위 밖이다. 대신 6단계 입력(`read_export`)과 완료 판정(`_completion`)으로 확인한다. 사용자 UAT에서 웹으로 한 번 열어 본다.
- 커버리지 점검: 2절의 모든 AC가 시나리오에 연결된다. P0 여정 J1~J5마다 정상과 실패 시나리오가 있다(J1: E2E-001/NEG-006, J2: E2E-003/EDGE-002, J3: NEG-001~005, J4: NEG-008/REG-002, J5: REG-001~003).
