# QA Plan — label-import-multi (여러 채널 라벨 결과를 한 프로젝트로 가져오기)

## 1. Scope

- 대상: 하네스 실행 `label-import-multi`(light), PR person-a-ai/dcx_agent#43 브랜치 위. 근거: [01-brainstorm.md](01-brainstorm.md), [02-design.md](02-design.md), [03-plan.md](03-plan.md).
- 표면: **web**. 화면 구조는 그대로이고 채널 표시 이름과 0단계·크롤링 설정 선택지 필터만 바뀐다. 나머지는 서버 명령·백엔드 저장 형식이다.
- 포함: 새 채널 등록·정규화, 채널별 읽기·검증·매핑, 날짜, 여러 파일 묶음(해시·중복·이어하기), 0단계·크롤링 설정 선택지, 가져온 프로젝트의 채널 이름 표시, `dcxctl` 여러 인자, 실제 4개 파일 검증과 표본 실행.
- 제외: 다음 채널 크롤러, 3단계 설정 화면의 채널 탭, 확률 CSV, 6단계 결과 품질 자체, 5단계 메모리 최적화.

## 2. Acceptance Criteria

01-brainstorm의 AC1~AC8.

## 3. Critical User Journeys

- J1: 운영자가 4개 zip으로 `dcxctl import-labels`를 실행해 한 프로젝트를 만든다(AC1~AC5).
- J2: 끊긴 가져오기를 파일 순서를 바꿔 다시 실행해 이어서 끝낸다(AC7).
- J3: 잘못된 묶음(파일 사이 중복, 다른 묶음의 같은 sid, 채널 규칙과 다른 doc_id)은 아무것도 쓰기 전에 거절된다(AC3, AC7).
- J4: 일반 사용자가 새 프로젝트 0단계·크롤링 설정에서 다음 채널을 보지 못한다(AC6).
- J5: 가져온 프로젝트를 웹에서 열면 채널이 한글 이름으로 보인다(AC5).
- J6: 기존 단일 파일 가져오기와 기존 채널 동작이 그대로다(AC8).

## 4. E2E Scenarios

QA-E2E-001
Priority: P0
Type: Acceptance / E2E (pytest `tests/importer/test_steps.py::test_multi_file_import_creates_one_project_with_all_channels`)
Given: 빈 데이터 폴더, `embed_backend=fake`, 채널별 결과 CSV 4개(하나는 zip)
When: `steps.run_import([4개 경로])`
Then:
  - `sid`가 `imp-` + 묶음 해시 앞 12자다
  - `projectContext.channels`와 `manifest.channels`가 `['naver_cafe','naver_kin','daum_cafe','daum_brunch']`다
  - 문서 shard의 `source`가 4가지이고, 각 문서의 `doc_id` 접두사가 채널과 맞는다(`nc_`,`kn_`,`dc_`,`db_`)
  - 큐 URL의 `source`가 같은 URL 문서의 `source`와 같다
  - `final` 라벨 수가 done 합과 같고 출처가 모두 `imported`다
  - 4단계 `done`, 5단계 `exportRef`가 있다
  - `imported.files`가 입력 순서의 파일 이름·sha256이다

QA-E2E-002
Priority: P0
Type: Acceptance / 실데이터 검증 (컨트롤러 실행, 쓰기 없음)
Given: 사용자 파일 `~/Downloads/네이버 카페.zip`, `네이버 지식인.zip`, `다음 카페.zip`, `다음 브런치.zip`
When: `read.open_sources`와 공유 `seen`을 쓴 `read.scan`을 4개 파일에 차례로 돌린다(데이터 폴더를 만들지 않는다)
Then:
  - 문제(ImportError_) 없이 끝난다
  - 파일별 `total`/`done`이 01-brainstorm 표와 같다(197,913/195,446 · 155,136/151,133 · 278,662/277,056 · 171,505/171,497)
  - `channels`가 파일마다 그 채널 하나다
  - 결과를 `docs/development/label-import-multi/qa/QA-E2E-002.md`에 적는다

QA-E2E-003
Priority: P1
Type: 실데이터 표본 E2E (컨트롤러 실행)
Given: 각 실제 파일의 앞 20,000행(헤더 포함)을 저장소 밖 임시 폴더에 CSV로 잘라 낸 4개, 빈 임시 `LOCAL_DATA_DIR`, `EMBED_BACKEND=fake`, 임시 `AUTHOR_SALT_PATH`
When: `/usr/bin/time -l backend/.venv/bin/python -m app.importer <4개 CSV>`
Then:
  - 종료 코드 0이고 `[1/5]`~`[5/5]`와 완료 줄이 찍힌다
  - 걸린 시간, 최대 RSS, 데이터 폴더 크기를 기록하고 80만 건으로 늘린 어림값을 적는다(`qa/QA-E2E-003.md`)
  - 끝난 뒤 임시 폴더를 지운다

QA-E2E-004
Priority: P0
Type: Browser (로컬 스택)
Given: QA-E2E-001과 같은 작은 4채널 묶음을 임시 데이터 폴더에 가져온 프로젝트, 같은 데이터 폴더로 띄운 백엔드·프론트(가짜 임베딩)
When: 웹 프로젝트 목록에서 그 프로젝트를 열고 0단계, 2단계, 3단계, 6단계 화면을 차례로 본다
Then:
  - 0단계 수집 채널에 "네이버 카페", "지식iN", "다음 카페", "브런치"가 선택된 칩으로 보인다
  - 2단계 채널 표·수집 결과 표의 채널 칸에 원시 키(`daum_cafe` 등)가 아니라 한글 이름이 보인다
  - 3단계·6단계 화면이 오류 없이 열린다(6단계에서 세그먼트 결과가 있으면 채널 비율 막대에 한글 이름이 보인다. 생성에 외부 모델이 필요해 만들 수 없으면 그 사실을 적는다)
  - 콘솔 오류가 없다

QA-E2E-005
Priority: P0
Type: Browser (로컬 스택)
Given: 같은 스택에서 새 프로젝트 만들기
When: 0단계 화면을 연다
Then:
  - 수집 채널 칩에 "다음 카페"·"브런치"가 없다
  - 기존 채널(네이버 카페, 네이버 블로그, 유튜브, 뽐뿌, 클리앙, 유튜브 브이로그, Threads, 지식iN, 82쿡)은 그대로 있다

QA-E2E-006
Priority: P1
Type: CLI (pytest `tests/ops/test_dcxctl.py`, `tests/importer/test_main.py`)
Given: 가짜 릴리스
When: `dcxctl import-labels "네이버 카페.zip" rel/b.csv --sid imp-x`(상대 경로, 공백 포함)
Then:
  - python이 `<PWD>/네이버 카페.zip`, `<PWD>/rel/b.csv`, `--sid`, `imp-x`를 그대로 받는다
  - `main`이 `run_import([...], sid='imp-x')`를 부른다

## 5. Negative Scenarios

QA-NEG-001
Priority: P0
Type: Negative (pytest `test_cross_file_duplicate_writes_nothing`)
Given: 두 파일에 같은 `doc_id`
When: `run_import([a, b])`
Then:
  - `ImportError_`에 "중복"과 행·doc_id 예시가 있다
  - `sessions/`·`crawl/`에 아무것도 생기지 않는다

QA-NEG-002
Priority: P0
Type: Negative (pytest `test_other_bundle_with_same_sid_is_rejected`)
Given: 묶음 A로 만든 `--sid imp-x`
When: 묶음 B로 같은 `--sid`를 준다
Then:
  - "다른 파일로 만든 프로젝트" 오류, 기존 프로젝트가 바뀌지 않는다

QA-NEG-003
Priority: P0
Type: Negative (pytest `test_wrong_doc_id_for_channel_is_rejected`)
Given: `site=다음카페`인데 `doc_id`가 규칙과 다른 행
When: `scan`
Then:
  - "doc_id가 DCX 규칙(URL 해시)과 다릅니다" 오류

QA-NEG-004
Priority: P1
Type: Negative (pytest `test_same_file_twice_is_rejected`, test_dcxctl)
Given: 같은 파일을 두 번 / `--sid`만 있고 값 없음
When: `open_sources` / `dcxctl import-labels a.csv --sid`
Then:
  - "같은 파일이 두 번" 오류 / 종료 코드 2와 사용법

QA-NEG-005
Priority: P0
Type: Negative (pytest `test_import_only_channels_are_valid_but_not_crawlable` + API)
Given: 일반 프로젝트
When: 크롤링 설정을 `channels=['daum_cafe']`로 저장하거나 크롤링을 시작한다
Then:
  - `available_sources()`에 두 채널이 없고, 저장·시작이 "Sources are unavailable"(422)로 거절된다

## 6. Edge Cases

QA-EDGE-001
Priority: P0
Type: Edge (pytest `test_dates`)
Given: `2026.03.30. 22:02`, `2025.12.22`, `2026-06-06T03:46:43+09:00`, `2026-06-06`, `26.06.02 11:32`, 빈 값, `26.13.02 11:32`, `어제`, `2026.6.1`
When: `_date`
Then:
  - 각각 `2026-03-30`, `2025-12-22`, `2026-06-06`, `2026-06-06`, `2026-06-02`, ``, ``, ``, `2026-06-01`

QA-EDGE-002
Priority: P0
Type: Edge (pytest `test_resume_with_files_in_other_order`)
Given: 3단계 직전에 멈춘 묶음 가져오기
When: 파일 순서를 바꿔 다시 실행
Then:
  - 같은 sid로 이어서 끝나고 수집본을 다시 만들지 않는다

QA-EDGE-003
Priority: P1
Type: Edge (pytest `test_channels_only_include_present_channels`, `test_mixed_channels_in_one_file`)
Given: 지식인·브런치 두 파일 / 한 파일에 채널 4개가 섞인 행
When: 가져오기·검증
Then:
  - 채널 목록이 `['naver_kin','daum_brunch']` / `channels` Counter가 채널마다 1이다

QA-EDGE-004
Priority: P0
Type: Edge (pytest `test_each_channel_maps_source_date_and_meta`)
Given: 지식인 행에 `answers`가 있음, 모든 채널 행에 닉네임
When: `iter_records`
Then:
  - 문서 어디에도 답변·닉네임 원문이 없고 작성자 해시는 그 채널로 만든다
  - `src_meta`는 카페 채널만 `cafe`/`cafe_id`를 가진다

QA-EDGE-005
Priority: P1
Type: Edge (vitest `importOnlyChannels.test.ts`)
Given: 0단계 선택값 `['naver_cafe','daum_cafe']` / 크롤링 설정 선택값 `['daum_cafe']`
When: 선택지를 만든다
Then:
  - `daum_cafe`만 보이고 `daum_brunch`는 숨는다 / `daum_cafe`가 표에 남는다

## 7. Regression Scope

변경 함수의 호출처: `normalize_url`·`doc_id`(크롤 워커 전체), `Doc`(워커·writer), `Channel`/`ProjectContext`(0단계 API, 세션 저장), `settingsSources`(크롤링 설정), 0단계 채널 칩, `importer.read`·`steps`(가져오기 전체), `dcxctl`.

QA-REG-001
Priority: P0
Type: Regression (pytest `tests/importer/*` 기존 테스트, `test_single_file_import_unchanged`)
Given: 앞선 실행의 네이버 카페 단일 파일 테스트
When: 실행
Then:
  - 모두 통과하고 sid·세션·수집본·라벨이 같다

QA-REG-002
Priority: P0
Type: Regression (pytest `tests/crawl/*`, `tests/context/*`, `test_labels_parity`)
Given: 기존 채널 URL 정규화·doc_id·세션 검증 테스트
When: 실행
Then:
  - 모두 통과한다

QA-REG-003
Priority: P0
Type: Regression (전체 `pytest backend/tests`, `npm test`, lint, build)
Given: 하네스 고정 검증 명령
When: 실행
Then:
  - 모두 통과한다(이 PC 고유 우회: `env -u VOYAGE_API_KEY`, `TAR_READER_OPTIONS=read_concatenated_archives`)

QA-REG-004
Priority: P1
Type: Browser Regression (로컬 스택)
Given: 일반(크롤링) 프로젝트
When: 2단계 크롤링 설정 화면을 연다
Then:
  - 채널 표에 "다음 카페"·"브런치" 행이 없고 기존 채널 행은 그대로다

## 8. Test Data / Preconditions

- pytest: `tests/importer/conftest.py`의 `row()`, 새 `channel_row(channel, n)`, `write_csv()`, `write_zip()`, `salt`. 공용 `data_dir`·`client` 픽스처. 앞선 실행의 가짜 `runner.start`·직접 `pipeline.run_prep` 방식.
- 브라우저(QA-E2E-004/005, QA-REG-004): 저장소 밖 임시 데이터 폴더, `EMBED_BACKEND=fake`, `LOCAL_DATA_DIR=<임시>`, 임시 salt. 작은 4채널 묶음은 `channel_row` 방식으로 만든 CSV를 쓴다. 백엔드·프론트는 그 데이터 폴더로 로컬에서 띄운다.
- 실데이터(QA-E2E-002/003): 사용자 파일 4개(`~/Downloads`). 저장소에 넣지 않는다. 개발 PC 남은 디스크 약 12GB라 전체 가져오기는 하지 않는다.

## 9. Priority

- P0: 데이터를 쓰는 경로(묶음 가져오기·이어하기·무변경 실패), 채널 규칙, 선택지 누출 방지, 회귀.
- P1: CLI 표면, 표본 성능 측정, 드문 입력.

## 10. Expected Result

- 자동 시나리오는 해당 테스트가 통과하면 PASS, 못 돌리면 NOT_RUN, 환경 문제면 BLOCKED. PASS로 바꿔 적지 않는다.
- QA-E2E-002/003은 컨트롤러가 실행해 `qa/` 아래에 결과를 남긴다.
- 브라우저 QA 보고서는 위 모든 ID를 담는다. 브라우저로 볼 수 없는 ID는 해당 테스트·명령 결과를 근거로 적는다.
- 확인할 수 없는 약속: 서버에서 80만 건 전체의 전처리 시간·임베딩 비용·내보내기 메모리는 표본 어림값으로만 알린다. 실제 값은 서버 실행에서 처음 나온다.
- 커버리지: AC1(E2E-001, E2E-006, REG-001), AC2(E2E-002, EDGE-003, EDGE-004), AC3(NEG-001, NEG-003), AC4(E2E-001, EDGE-003), AC5(E2E-001, E2E-004), AC6(E2E-005, NEG-005, EDGE-005, REG-004), AC7(EDGE-002, NEG-002), AC8(REG-001~004).
