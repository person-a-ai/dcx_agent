# 라벨 결과 가져오기 — 설계 (non-ui)

기준: [01-brainstorm.md](01-brainstorm.md) 제품 승인(2026-11-03). 추가 결정(대화, 2026-11-03): 웹 화면은 바꾸지 않는다. "가져온 프로젝트" 안내는 명령 로그에만 남긴다.

## 1. 목적과 결과

- 서버에서 `dcxctl import-labels <파일>` 한 번으로 새 프로젝트를 만든다. 명령은 0단계~5단계 내보내기까지 끝내고, 웹에서는 **6단계(세그먼트)**부터 이어 간다.
  - 화면 단계 번호는 0 입력, 1 키워드, 2 크롤링, 3 전처리, 4 라벨링, 5 학습·내보내기, 6 세그먼트다(`StepBar.STEP_MAP`). 01의 AC9 "5단계(세그먼트)"는 화면 번호로 6단계를 뜻한다.
- 6단계가 읽는 것은 5단계 내보내기 파일(`training.exportRef` → `classified/<sid>/<v>/gen-*/relevant.jsonl`)이다(`known/filter.read_export`). 그래서 명령이 모델 없는 내보내기(`model/export.write(without_model=True)`)까지 실행한다.

## 2. 명령

- 서버: `dcxctl import-labels <zip 또는 csv> [--sid <id>]`
  - `ops/macmini/dcxctl`에 하위 명령을 추가한다. `run-api.sh`와 같은 방식으로 `shared/app.env`·`shared/runtime.env`를 읽고, 현재 릴리스 `backend/`에서 `.venv/bin/python -m app.importer …`를 실행한다. API와 같은 `LOCAL_DATA_DIR`, `AUTHOR_SALT_PATH`, 임베딩 설정을 쓴다.
  - 서버가 점검 중(`$MAINTENANCE`)이면 실행하지 않는다.
- 개발 PC: `cd backend && .venv/bin/python -m app.importer <파일> [--sid <id>]`
- `--sid`를 주지 않으면 `imp-` + sha256(결과 CSV 바이트)[:12]를 쓴다. 같은 파일은 항상 같은 프로젝트가 되고, 다시 실행하면 이어서 한다(AC8).
- 종료 코드: 0 완료, 1 입력 오류 또는 진행 불가(사유 출력), 130 Ctrl+C(그때까지 저장된 상태 유지).

## 3. 입력 읽기

- zip이면 압축을 풀지 않고 `zipfile`로 스트리밍한다. 이름이 `.csv`로 끝나고 `_probs.csv`로 끝나지 않는 멤버가 정확히 하나여야 한다. 확률 CSV는 무시한다. CSV 경로를 직접 줘도 된다.
- 인코딩 `utf-8-sig`, `csv.field_size_limit`는 충분히 크게 둔다.
- 필수 컬럼: `date, keyword, title, contents, comments, answers, site, url, author_nickname, comment_nicknames, doc_id, status, anchor, sense, feel, think, act, relate, outcome, situation, evidence_level, reason_code, signal, questions_version, rule_version`. 빠지면 파일 이름과 빠진 컬럼을 출력하고 종료 코드 1로 끝나며, 아무것도 만들지 않는다(AC2).
- **사전 검증 패스.** 프로젝트를 만들기 전에 전체를 한 번 읽는다. 다음 중 하나라도 있으면 처음 5개 예시를 출력하고 종료 코드 1로 끝난다.
  - `questions_version != QVER` 또는 `rule_version != RULE_VERSION`(AC6)
  - `doc_id`가 DCX 규칙(`crawl/urls.doc_id('naver_cafe', normalize_url(url,'naver_cafe'))`)과 다름
  - 같은 `doc_id`가 두 번 이상 나옴
  - `status='done'`인데 태그가 0/1이 아니거나, `evidence_level`이 DCX `rule.grade(태그)`와 다름
  - `reason_code`·`signal` 값이 DCX 허용값 밖
- 건너뛰는 행은 개수를 집계해 보고한다. 문서와 라벨에 넣지 않는다.
  - `site != '네이버카페'`: `unknown_site`
  - `status != 'done'`: `skipped`. 이번 데이터에서는 `short_body` 2,467건

### 3.1 행 → 수집 문서 (`crawl/schema.Doc`, extra=forbid)

| Doc 필드 | 값 |
|---|---|
| `doc_id` | CSV `doc_id`(검증됨) |
| `source` | `naver_cafe` |
| `src_meta` | `{"cafe": <URL 첫 경로>, "cafe_id": <같음>, "imported": true}` |
| `kw` / `kw_axis` / `kw_sub` / `kw_hits` | `keyword` / `""` / `""` / `[keyword]` |
| `title` / `body` | `title` / `contents` |
| `comments` | `ast.literal_eval(comments)`가 문자열 목록이면 각 항목, 실패하면 문자열 하나를 댓글 하나로, 비었으면 `[]`. 댓글은 `{"text": 항목, "depth": 0, "date": "", "author_hash": ""}` |
| `date` | `YYYY.MM.DD`를 ISO 날짜(`YYYY-MM-DD`)로 바꾼다. 파싱하지 못하면 `""` |
| `url` | `normalize_url(url, 'naver_cafe')` |
| `fetch_level` / `access` / `snippet` | `full` / `public` / `contents[:200]` |
| `author_hash` | `crawl/hashing.author_hash('naver_cafe', author_nickname)`, 닉네임이 비었으면 `""` |
| `crawled_at` | 가져온 시각(ISO) |

- 지식인 `answers`와 `comment_nicknames`는 넣지 않는다. 댓글 작성자는 개수가 안 맞는 경우가 있어 매칭하지 않는다.

### 3.2 행 → 최종 라벨 (`labels.sqlite.final`)

| 열 | 값 |
|---|---|
| `level` | `rule.grade(태그)`(= CSV `evidence_level`, 검증됨) |
| `confidence` | `NULL` |
| `source` | `imported`(새 값) |
| `route` | `accepted` |
| `tags_json` | `Tags(anchor, sem{sense,feel,think,act,relate,outcome}, situation, reason_code, signal)`. Non이면 `signal=null`, 그 밖이면 `reason_code=null` |
| `reason_code`, `signal` | 위와 같음 |
| `rule_version` / `questions_version` | DCX 현재 값 |
| `votes_json` | `{"imported": {"file": <CSV 이름>, "sha256": <앞 12자리>}}` |
| `disagree_json` / `grade_mismatch` | `[]` / `0` |

## 4. 단계별 동작

진행 상태는 `session.json`의 `imported` 블록에 남긴다: `{file, sha256, steps: {session, crawl, prep, labels, export}, counts}`. 각 단계는 끝난 것을 다시 하지 않는다.

### A. 프로젝트 만들기
- `store.update_session(sid, {...})`로 `schemaVersion: 2` 세션 v1을 만든다. 저장소 잠금과 버전 초기화는 기존 함수를 그대로 쓴다.
- `projectContext`(검증: `ProjectContext`):
  - `bk: "."`, `oneLiner: "."`, `researchQuestion: {"text": "."}`, `projectType: {"choice": "new", "note": "."}`
  - `taskMode: "explore"`(지표·분석 목적·포지셔닝이 필수가 아니게 된다), `constraints: []`, `channels: ["naver_cafe"]`
  - `productCategory: {"l1": ".", "source": "user"}`
- `keywords`: CSV `keyword` 고유값마다 `{kw, status: "approved", axis: "", sub: ""}`. 1단계 화면에 키워드 목록이 보인다.
- 같은 `sid`가 이미 있는데 `imported.sha256`이 다르면, 다른 파일로 만든 프로젝트이므로 종료 코드 1로 끝난다.

### B. 수집본 등록 (2단계)
- `crawl/<sid>/collections/c1/`에 기존 크롤러와 **같은 형식의, 이미 끝난 수집본**을 만든다. 수집·전처리 코드는 바꾸지 않는다.
  - `meta.json`: `{id: "c1", parent: null, createdAt, keywords, status: "done"}`
  - `manifest.json`: 위 값 + `{channels: ["naver_cafe"], config: {...기본값}, snapshotId: null, imported: {file, sha256}}`
  - `docs/shard-*.jsonl`: `crawl/writer.DocWriter`로 3.1 문서를 쓴다.
  - `queue.sqlite`: `crawl/queue.CrawlQueue`로 만든다. `urls`에 문서마다 한 행(`status='done'`), `runs`에 `kind='detail', status='done'` 한 행을 넣는다. `report.can_finalize`가 참이 되어 `phase_state == 'done'`이 된다.
- 세션에 `collectionId: "c1"`, `step: "preprocess-setup"`을 넣는다.
- 이어서 하기: 작업 중 폴더(`c1.partial`)에 다 쓴 뒤 이름을 바꿔 공개한다. 중간에 끊기면 `c1.partial`을 지우고 다시 쓴다.

### C. 전처리 (3단계)
- `routers/prep.run`과 같은 순서를 함수로 호출한다(HTTP 없이): `PrepConfig` 기본값 → `guards.assert_ready` → `work/runner.start(sid, v, 'prep', …)` → 세션 `prep.{config, derivedRef, status, runId}` 저장.
  - 공통 부분은 `app/prep/launch.py`(새 파일)로 옮기고, 라우터와 가져오기가 같이 쓴다. 라우터 동작은 바꾸지 않는다.
- 끝날 때까지 10초마다 `runner.status(sid)`를 읽어 진행률을 한 줄씩 출력한다. 웹 3단계 화면에서도 같은 run이 보인다.
- 다시 실행할 때: `prep.status == 'done'`이면 건너뛴다. 실행 중이면 기다리고, `failed`/`interrupted`이면 새로 시작한다(기존 재사용 규칙대로 완료분은 재사용). 실패가 두 번 나면 사유를 출력하고 종료 코드 1로 끝난다.

### D. 라벨 넣기 (4단계)
- 전처리 문서(`infer.documents`)의 `doc_id` 가운데 CSV에 `done` 판정이 있는 글만 `final`에 `INSERT OR REPLACE`로 넣는다. 5,000건씩 한 트랜잭션으로 넣는다.
- `label/overview.index_documents`를 호출해 4단계 화면용 문서 색인을 만든다.
- 세션 `labeling`: `{started: true, status: "done", mode: "imported", labelerMode: "imported"}`. 세션 `step: "train-start"`.
- 집계: `labeled`(넣은 수), `unlabeled`(전처리를 통과했지만 판정이 없는 글), `droppedByPrep`(판정은 있지만 전처리에서 빠진 글)(AC7).

### E. 내보내기 (5단계)
- `model/export.write(sid, v, without_model=True, partial=(unlabeled > 0))`. 판정 없는 글은 내보내기에서 빠진다.
- 세션 `step: "cluster-start"`. 6단계가 바로 읽을 수 있다.

## 5. 기존 코드에서 바꾸는 곳 (가져온 라벨 보호)

`labelerMode: "imported"`이거나 `final.source='imported'`인 경우에만 동작이 달라진다. 기존 프로젝트의 흐름은 그대로다.

| 위치 | 변경 |
|---|---|
| `label/schema.Label.source` | 허용값에 `imported` 추가 |
| `label/route.rebuild_queue` / `rebuild_final` | 모드가 `imported`이면 표에서 final을 다시 만들지 않는다. 규칙·질문 버전이 바뀔 때 지우는 대상에서 `imported`도 뺀다(`human`·`model`과 같음) |
| `label/route.sync` | 모드가 `imported`이면 자동 감사 라운드(`audit.maybe_new_round`)를 만들지 않는다 |
| `routers/labeling_v2.start` / `mode` / `control` | 모드가 `imported`이면 판정 시작·방식 변경·워커 제어를 409로 거절한다("가져온 라벨입니다. 새 버전에서 다시 하세요.") |
| `context/stale._judges_complete` · `routers/sessions._completion.labeling_done` | `imported`이면 판정 실행 기록 없이 `labeling.status == 'done'`으로 완료 처리한다 |
| `label/overview.overview` | `imported`이면 Jev·GPT 정확도·진행 카드를 비우고 분포·총계만 보낸다(화면 코드 변경 없음, 값만 비어 있음) |
| `app/importer/`(새 패키지) | `__main__.py`(인자·출력), `read.py`(CSV 읽기·검증·매핑), `steps.py`(A~E) |
| `app/prep/launch.py`(새 파일) | 3단계 시작 공통 함수(C) |
| `ops/macmini/dcxctl` | `import-labels` 하위 명령 |

## 6. 출력

```
가져오기: 네이버 카페.zip → jev_longevity_full.csv (sha256 1a2b3c…)
검증  197,913행 · done 195,446 · skipped 2,467(short_body) · 다른 채널 0
[1/5] 프로젝트 imp-1a2b3c4d5e6f 만듦
[2/5] 수집본 c1 등록 195,446건
[3/5] 전처리 run r-… 시작
      12:03:10  41% (80,123/195,446)
      …
[4/5] 라벨 195,301건 넣음 · 판정 없음 0 · 전처리에서 빠짐 145
[5/5] 내보내기 완료 · core+supporting 151,420건
완료. 웹 프로젝트 목록에서 imp-1a2b3c4d5e6f를 열고 6단계(세그먼트)부터 진행하세요.
주의: 0단계 값이 모두 '.'입니다. 6~8단계 결과는 주제 정보 없이 만들어집니다.
```

## 7. 오류 처리

| 상황 | 동작 |
|---|---|
| 입력 형식·검증 실패 | 아무것도 만들지 않고 종료 코드 1 |
| 같은 sid, 다른 파일 | 종료 코드 1, `--sid`로 다른 이름을 주라고 안내 |
| 프로젝트가 이미 4단계 이후로 진행됨(가져오기가 아닌 방법으로 바뀐 경우) | 종료 코드 1. 기존 데이터를 건드리지 않는다 |
| 전처리 실패 | 사유 출력. 다시 실행하면 재시도한다 |
| Ctrl+C | 진행 중인 단계만 멈춘다. 전처리 워커는 서버 작업이라 계속 돈다. 다시 실행하면 이어서 기다린다 |
| 서버 점검 중 | `dcxctl`이 실행을 거절한다 |

## 8. 테스트

- 위치는 `backend/tests/importer/`. 승인된 `pytest backend/tests`로 같이 돈다. `LOCAL_DATA_DIR`·salt는 `tmp_path`, 임베딩·라벨러는 기존 fake 설정을 쓴다.
- 고정 데이터: 작은 CSV와 zip(정상 행, skipped, 다른 site, 댓글 목록 문자열과 깨진 문자열, 중복 URL, 잘못된 doc_id, 버전 다름, 등급 불일치).
- 단위 테스트: 컬럼 검증, 사전 검증 오류별 종료, 3.1·3.2 매핑, sid 규칙, zip 멤버 선택.
- 흐름 테스트: A~E를 끝까지 실행한 뒤 다음을 확인한다.
  - `phase_state == 'done'`, `prep.status == 'done'`, `_completion`의 crawl/prep/labeling/export가 모두 참
  - `read_export`가 core·supporting만 돌려준다
  - 다시 실행하면 아무것도 바꾸지 않는다
  - 각 단계 사이에서 끊은 뒤 다시 실행하면 이어서 끝난다
- 보호 테스트: imported 세션에서 판정 시작·모드 변경이 409로 거절된다. `overview`·`rebuild_queue`·`sync`가 imported final을 지우지 않고 감사 라운드를 만들지 않는다. 기존 cross·gpt_only 테스트는 그대로 통과한다.
- `dcxctl import-labels`는 기존 `backend/tests/ops` 방식으로 인자 전달과 점검 중 거절을 확인한다.
- 실제 1GB 파일 실행은 개발 PC에서 사용자가 확인한 뒤 한다(임베딩 시간 소모).

## 9. 제외

- 웹 화면 변경(업로드, 안내 띠).
- 확률 CSV, `confidence` 채우기, GPT·Jev 재판정, 감사 라운드.
- `naver_cafe` 외 채널.
- 가져온 프로젝트에서 2단계 수집 추가(새 키워드 수집). 화면에서 시도하면 기존 규칙대로 새 수집본이 만들어지고 4단계 이후는 새 버전이 필요하다. 이 동작은 바꾸지 않는다.
