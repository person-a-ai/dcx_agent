# label-import-multi · 02 설계

- 작성: 2026-11-04 · light 트랙이라 계획 번들(`plan-bundle.json`의 `design`)로 계획과 함께 승인한다.
- 앞선 설계: `docs/development/label-import/02-design.md`. 아래에 적지 않은 부분(단계 A~E, 잠금, 버전 고정, 체크포인트, `imported` 라벨 보호)은 그대로 둔다.

## 1. 채널

| 채널 키 | `doc_id` 접두사 | 표시 이름 | CSV `site` | 크롤러 |
|---|---|---|---|---|
| `naver_cafe` | `nc` | 네이버 카페 | `네이버카페` | 있음 |
| `naver_kin` | `kn` | 지식iN | `네이버지식인` | 있음 |
| `daum_cafe` (새) | `dc` | 다음 카페 | `다음카페` | 없음(가져오기 전용) |
| `daum_brunch` (새) | `db` | 브런치 | `다음블로그_브런치` | 없음(가져오기 전용) |

- 백엔드에 새 채널 키를 등록하는 곳: `app/crawl/schema.py`의 `Doc.source` Literal, `app/context/models.py`의 `Channel` enum, `app/crawl/urls.py`의 `_PREFIXES`, `app/context/labels.py`의 `LABELS['channels']`.
- 크롤러 레지스트리(`app/crawl/adapters`)에는 넣지 않는다. 그래서 `available_sources()`에 나오지 않고, 크롤링 시작·설정 저장은 지금처럼 422로 거절된다.
- `channel_defaults()`는 모르는 채널에 기본값을 주므로 바꾸지 않는다. 전처리 상투어(`boilerplate.v1.json`)도 `cfg.boilerplate.get(source, [])`로 읽으므로 바꾸지 않는다.
- URL 정규화: `daum_cafe`이고 호스트가 `cafe.daum.net`·`m.cafe.daum.net`이면 `https://cafe.daum.net` + 경로(끝 `/` 제거)로 바꾸고 쿼리를 모두 뗀다. 실제 파일 278,662행의 호스트는 모두 `cafe.daum.net`이고, 앞 5,000행의 `doc_id`가 이 규칙과 맞는다. `daum_brunch`는 공통 규칙(추적 파라미터 제거, 끝 `/` 제거)이 그대로 맞는다.

## 2. 웹 표시

- `frontend/src/lib/contextLabels.ts`의 `channels`에 두 이름을 넣는다. 백엔드 `LABELS`와 같아야 한다(`tests/context/test_labels_parity.py`).
- 같은 파일에 `IMPORT_ONLY_CHANNELS = ['daum_cafe', 'daum_brunch']`를 내보낸다.
- 0단계(`app/pipeline/start/page.tsx`) 채널 선택지: 가져오기 전용 채널은 **이미 선택된 경우에만** 보인다. 새 프로젝트에는 나오지 않고, 가져온 프로젝트의 0단계에서는 선택된 칩으로 보인다(저장해도 값이 사라지지 않는다).
- 2단계 크롤링 설정(`components/crawl/Settings.tsx`) `channelNames`에 두 이름을 넣는다. `settingsSources()`(`lib/logic/crawlConfig.ts`)의 `known` 목록에서는 가져오기 전용 채널을 뺀다. 이미 선택된 채널(`selected`)은 지금처럼 보인다.
- 나머지 표시(6단계 `ChannelBar`, 근거 카드, 버전 보기, 수집 진행 표)는 `contextLabels.channels`·`channelNames`를 이미 찾아 쓰므로 이름만 들어가면 한글로 보인다.
- 3단계 전처리 설정의 채널 체크박스·상투어 탭(`components/prep/prep.ts`)은 바꾸지 않는다(제외 범위).

## 3. 입력 읽기 (`app/importer/read.py`)

- `SITE`/`SOURCE` 상수 대신 `CHANNELS = {'네이버카페': 'naver_cafe', '네이버지식인': 'naver_kin', '다음카페': 'daum_cafe', '다음블로그_브런치': 'daum_brunch'}`와 정해진 순서 `CHANNEL_ORDER`를 둔다.
- 행의 채널은 `CHANNELS.get(row['site'])`이다. 없으면 `unknown_site`로 건너뛴다(지금과 같음).
- `doc_id` 검사, URL 정규화, `author_hash`, 문서 `source`는 모두 그 행의 채널을 쓴다.
- `src_meta`: 네이버 카페·다음 카페는 `cafe`/`cafe_id` = URL 경로 첫 조각(지금과 같은 방식), 지식인·브런치는 넣지 않는다. 모든 채널에 `imported=True`를 넣는다. 전처리 문서의 카페 칸은 `src_meta.cafe`가 없으면 채널 이름을 쓴다(`app/prep/documents.py`, 기존 동작).
- `answers`는 어떤 채널에서도 저장하지 않는다(지식인 포함). `comments`는 지금과 같은 방식으로 읽는다.
- 날짜(`_date`): 아래 세 형식만 받아 `YYYY-MM-DD`로 바꾼다. 월 1~12, 일 1~31이 아니거나 형식이 다르면 빈 값이다.
  1. `YYYY.MM.DD`(뒤에 `.`·시각이 붙어도 됨) — 네이버 카페·지식인
  2. `YYYY-MM-DD` 뒤에 `T`/공백/끝 — 브런치(ISO 8601)
  3. `YY.MM.DD HH:MM` — 다음 카페, 연도 `20YY`
- `Scan`에 `channels: Counter`(채널별 done 수)를 더한다.
- 여러 파일:
  - `open_sources(paths) -> list[Source]`: 각 파일을 `open_source`로 연다. 같은 sha256이 두 번 나오면 `ImportError_('같은 파일이 두 번 들어왔습니다: …')`.
  - `bundle_sha(sources) -> str`: 파일 하나면 그 sha256, 여럿이면 `sha256('\n'.join(sorted(sha들)))`. 파일 순서와 무관하다.
  - `scan(source, seen=None)`: `seen`(doc_id 집합)을 넘기면 파일 사이 중복도 같은 방식(최대 5개 예시)으로 찾는다. 첫 파일에서 본 `doc_id`가 다음 파일에 또 나오면 그 행을 문제로 적는다.
  - `merge_scans(scans) -> Scan`: 합계, 건너뜀, 키워드(처음 나온 순서), 채널을 합친다.

## 4. 가져오기 단계 (`app/importer/steps.py`)

- 진입점: `run_import(paths, *, sid=None, log=print, poll_s=10, sleep=time.sleep)`. `paths`는 경로 하나(`str`/`Path`) 또는 경로 목록이다.
- 모든 파일을 단계 전에 검증한다. 파일마다 `검증` 줄을 찍고, 하나라도 문제가 있으면 아무것도 쓰지 않는다.
- 프로젝트 id 기본값은 `'imp-' + bundle_sha[:12]`이다(파일 하나면 지금과 같다).
- 세션 `imported`: `sha256`에 묶음 해시를, `files`에 `[{name, sha256}]`(입력 순서)를 넣는다. 파일 하나일 때는 지금처럼 `file`도 둔다. 이어서 하기·`--sid` 충돌 판정은 `imported.sha256`과 묶음 해시를 비교한다.
- 0단계 `channels`와 수집본 `manifest.channels`는 `Scan.channels`에 done이 1건 이상인 채널을 `CHANNEL_ORDER` 순서로 담는다. `manifest.imported`도 `sha256`·`files`를 담는다.
- 수집본 등록, 라벨 넣기는 모든 파일을 입력 순서대로 읽는다. 큐 URL의 `source`는 문서의 `source`다. 라벨 `votes`의 `imported`에는 그 행이 나온 파일 이름과 sha256 앞 12자를 적는다.
- 전처리·내보내기·체크포인트·버전 고정은 바꾸지 않는다.

## 5. 명령

- `python -m app.importer <파일> [<파일> …] [--sid ID]` (`nargs='+'`).
- `dcxctl import-labels <파일>... [--sid ID]`: 옵션이 아닌 인자를 모두 절대 경로로 바꿔 넘긴다. `--sid` 뒤에 값이 없으면 사용법을 찍고 2로 끝낸다. macOS `/bin/bash` 3.2에서 돈다(`set -Eeuo pipefail`, 빈 배열 전개 금지).
- `ops/macmini/README.md`의 사용법 예시를 여러 파일로 바꾼다.

## 6. 규모와 자원

- 약 80만 건. 수집본 등록은 이미 5,000건씩 끊어 쓰고, 라벨 넣기는 전처리 문서의 `doc_id`만 메모리에 둔다(약 80만 개 문자열, 수십 MB).
- 3단계 전처리·5단계 내보내기는 기존 코드다. 시간·최대 메모리는 QA에서 표본으로 재서 80만 건으로 늘려 어림하고, 서버 실행 전에 사용자에게 알린다.
- 개발 PC 남은 디스크는 약 12GB(2026-11-04)라 실제 4개 파일 전체 가져오기는 하지 않는다. 전체 검증(읽기만, 디스크를 쓰지 않음)은 4개 파일 모두 한다.

## 7. 되돌리기

- 코드: PR #43 브랜치에서 이번 실행의 커밋을 되돌린다. 새 채널 키는 가져온 데이터에만 쓰이므로, 되돌린 뒤 남은 가져온 프로젝트는 `Doc.source`/`Channel` 검증에서 걸릴 수 있다. 서버에서 가져오기 전이면 영향이 없다.
- 데이터: 가져온 프로젝트는 `sessions/<sid>`, `crawl/<sid>`, `imports/<sid>.lock`을 지우면 사라진다(기존과 같음).
