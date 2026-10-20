# 02 · 설계 — 2단계 크롤링 채널 확장

- 기획: [01-brainstorm.md](01-brainstorm.md) (제품 승인 2026-10-20) · 목업: [mockup/index.html](mockup/index.html)
- 기준 커밋: main `4444a50` · 작업 공간 `/Users/yunho/Documents/dcx_agent-channels`

## 0. 목업 제작 방식

`/claude-design`(설치 확인됨)은 쓰지 않았다. 이유는 세 가지다. ① 사용자가 원격(Remote Control)으로 접속 중이라 claude.ai/design 첫 실행에 필요한 Chrome 로그인을 이 컴퓨터 창에서 할 수 없다. ② 코드베이스 컨텍스트를 외부 서비스로 보내야 한다. ③ 이번 화면 변경은 기존 크롤링 화면에 행 · 열 · 문구를 더하는 것이라 새 시각 언어가 없다. 대신 실제 앱 CSS(`frontend/src/styles/tokens.css`, `components/ds/ds.css`, `components/crawl/crawl.css` @`4444a50`)를 `mockup/app.css`로 복사하고, 그 CSS를 쓰는 로컬 HTML 목업을 작성했다. 목업 위쪽 도구 막대로 화면 4개(설정 · 게이트 · 수집 중 · 결과) × 상태 5개(정상 · 로딩 · 빈 결과 · 오류·차단 · 읽기 전용) × 폭 2개(데스크톱 · 모바일 375)를 바꿔 볼 수 있다. 승인 후 바꾸기 원하면 `/claude-design`으로 다시 만든다.

## 1. 실측 확인 (2026-10-20)

| 대상 | 결과 | 설계에 미친 영향 |
|---|---|---|
| 유튜브 자막 직접 요청 | 영상 페이지의 `captionTracks.baseUrl`(`exp=xpe`)을 그대로 요청하면 HTTP 200 · **0바이트** | 자막은 반드시 yt-dlp의 자막 경로로 받는다. 자체 요청 · 토큰 생성은 하지 않는다 |
| yt-dlp 2026.08.19 자막 | `ytsearch20:"에어컨 브이로그"` → 20개 모두 195초 이상. 길이 조건 통과 4개 중 3개에서 한국어 자막 json3 수신(자동 2, 수동+자동 1, 2,900~7,200자, `tStartMs`/`dDurationMs` 포함), 1개는 자막 없음 | 브이로그 경로 성립. "자막 없음" 건너뜀이 실제로 생긴다 |
| 지식iN 검색 | `kin.naver.com/search/list.naver?query=` 로그인 없이 페이지당 결과 10건, 제목 링크 `a._searchListTitleAnchor` (`detail.naver?dirId=&docId=&answerNo=&qb=`) | 목록은 페이지 단위, URL은 `dirId`+`docId`만 남겨 정규화 |
| 지식iN 질문 | `.endTitleSection`(제목), `.questionDetail`(본문, `data-tag`=해시태그), `작성일` 날짜, 답변 블록 `.answerArea` | 질문만 문서화, 답변 수는 `.answerArea` 개수 |
| 82쿡 검색 | `entiz/enti.php?bn=15&searchType=search&search1=1&keys=`, 표 `tbody tr`(공지 `tr.noticeList` 제외) 페이지당 25건, `page=N` | 공지 행을 거른다 |
| 82쿡 글 | 제목 `h4.title.bbstitle`, 본문 `#articleBody`, 댓글 `ul.reples > li.rp`(작성자 `h5 strong`, 시각 `.repleFunc em`, 본문 `p`), IP 일부 표기(`#writerIP`, `.ip`) | IP는 저장하지 않는다 |
| Threads 검색 | 로그인 없이 `threads.com/search?q=` 렌더링, 18~21건 뒤 로그인 창 | 키워드당 수십 건, 로그인 창 = 차단 |

## 2. 구조

### 2.1 새 모듈

| 파일 | 책임 | 공개 인터페이스 | 의존 |
|---|---|---|---|
| `crawl/adapters/youtube_vlog.py` | 브이로그 검색 · 자막 수신 · 구간 문서화 | `YoutubeVlogAdapter.list_page(kw, cursor, *, videos_per_keyword, min_duration_s, max_duration_s)`, `.fetch(item)` | yt-dlp, `captions`, `vectors.embedder.get_embedder` |
| `crawl/captions.py` | 자막 cue → 화제 구간 | `parse_json3(data) -> list[Cue]`, `segment(cues, embedder, *, window_s, min_s, max_s, fixed_s) -> (list[Segment], segmenter)` | numpy만 (임베더는 인자) |
| `crawl/render.py` | Crawl4AI 브라우저 1개 유지, 동기 호출 다리 | `RenderBridge.available() -> bool`, `.fetch_html(url, *, wait_selector, timeout_s) -> str`, `.close()` | crawl4ai (Playwright Chromium) |
| `crawl/adapters/threads.py` | Threads 검색 → 글 문서 | `ThreadsAdapter.list_page(kw, cursor)`, `.fetch(item)`; 공급자 경계 `ThreadsSearchProvider.search(kw) -> list[ListItem]`, 구현 `WebSearchProvider(RenderBridge)` | `render` |
| `crawl/adapters/naver_kin.py` | 지식iN 질문 | `NaverKinAdapter(CommunityAdapter)` | httpx, selectolax |
| `crawl/adapters/cook82.py` | 82쿡 자유게시판 | `Cook82Adapter(CommunityAdapter)` | httpx, selectolax |

### 2.2 기존 모듈 변경

| 파일 | 변경 |
|---|---|
| `crawl/adapters/base.py` | `AdapterSkipped(reason: str)` 예외 추가 — "문서를 만들지 않고 건너뛴다"(실패 아님) |
| `crawl/queue.py` | `mark_skipped(url_norm, source, reason)` — `status='skipped'`, `last_error=reason`, 소유권 검사는 `mark_excluded`와 같게 |
| `crawl/worker.py` | 상세 단계에서 `AdapterSkipped`를 잡아 `mark_skipped` 호출. `outcome()`에서 시도 · 차단 · 파싱 오류 어느 쪽에도 세지 않는다. 채널 기본값(`_Run` 기본 동시 수 · 간격)에 새 채널 추가. `youtube_vlog` 옵션을 `list_page`에 넘기고(`youtube`와 같은 `inspect.signature` 방식), `list_remaining` 상한에 `youtube_vlog.videos_per_keyword` 반영 |
| `crawl/control.py` | `_status_settings`의 기본 간격 목록에 새 채널 |
| `crawl/report.py` | `progress()`에 `skipped={source: {reason: count}}`, `build_report()` 채널마다 `skip_reasons={reason: count}` 추가(기존 `skipped` · `skip_reason`은 유지) |
| `crawl/schema.py` · `context/models.py` | `source` · `Channel`에 `youtube_vlog`, `threads`, `naver_kin`, `cook82` |
| `crawl/urls.py` | 접두사 `yv` · `th` · `kn` · `c8`. 정규화: 지식iN은 `dirId` · `docId`만, 82쿡은 `bn` · `num`만, Threads는 `https://www.threads.com/@{user}/post/{code}` |
| `crawl/adapters/__init__.py` | 레지스트리 등록. `threads`의 `is_available`은 `REAL_CHANNELS_ENABLED` + `RenderBridge.available()` |
| `routers/crawl_v2.py` | `Config.youtube_vlog: YoutubeVlog(videos_per_keyword=20 ≥1, min_duration_s=60 ≥0, max_duration_s=3600)`, `min < max` 검증 |
| `config.py` | `caption_window_s=20`, `caption_min_segment_s=45`, `caption_max_segment_s=300`, `caption_fixed_segment_s=90`, `threads_render_timeout_s=30` |
| `context/labels.py` · `prep/boilerplate.v1.json` | 채널 이름, 채널별 상투어 목록(빈 목록으로 시작) |
| `keywords/prompts.py` | 구어 · 줄임말 허용 채널 집합에 `threads`, `cook82`, `naver_kin` |
| 프론트 `components/crawl/Settings.tsx` | 채널 행 4개(배지 "새 채널"), 수집 방식 설명을 `channelDescriptions` 표로 분리, 고급 설정에 "유튜브 브이로그" 칸(키워드당 영상 수 · 최소/최대 길이(분)), 키워드 카드 안내 1줄 |
| `lib/logic/crawlConfig.ts` | 채널 기본값(`limits`) · `youtube_vlog` 기본 설정 · 파싱 |
| `app/pipeline/crawling/page.tsx` | 게이트에 Threads 안내 배너(설정에 `threads`가 있을 때만), 멈춤 배너에 Threads 로그인 화면 문장(멈춘 채널에 `threads`가 있을 때만), 검증식에 `youtube_vlog` |
| `components/crawl/Progress.tsx` | 채널 상태 표에 "건너뜀" 열, 결과의 건너뜀 문장을 채널 × 사유 표로 교체, 브이로그 분포 줄에 "영상 수 → 구간 수" |
| `lib/logic/finishPartial.ts` · `lib/contextLabels.ts` · `components/prep/prep.ts` | 사유 이름표(`no_ko_captions` → "한국어 자막 없음", `restricted` → "회원 전용 · 폐쇄 카페(제외)", `blocked` · `parse_error`), 채널 이름 |

## 3. 채널별 데이터 흐름

### 3.1 유튜브 브이로그 (`youtube_vlog`)
1. **목록:** `ytsearch{2N}:"{kw} 브이로그"`(flat)를 받아 `min_duration_s ≤ duration ≤ max_duration_s`만 남기고 앞에서 N개(`videos_per_keyword`). 커서 없음. `ListItem.src_meta = {video_id, video_title, channel, duration, view_count}`.
2. **상세:** yt-dlp `extract_info(skip_download, writesubtitles, writeautomaticsub, subtitleslangs=['ko'], subtitlesformat='json3')`. 한국어 수동 자막이 있으면 수동, 없으면 자동. 자막 본문은 yt-dlp `urlopen`으로 메모리에서 읽고 파일로 남기지 않는다. 한국어 자막이 없으면 `AdapterSkipped('no_ko_captions')`. 봇 확인 · 403 · 429는 기존 `_blocked()` 판별 → `AdapterBlocked`.
3. **분할:** `captions.parse_json3` → `[음악]` · `[박수]` 같은 대괄호 표기 제거, 빈 cue 제거 → `captions.segment(...)`.
4. **문서:** 구간마다 `FetchedDoc(title=영상 제목, body=구간 텍스트, comments=[], date=업로드일, src_meta={...목록 meta, segment_start_s, segment_end_s, caption_kind: 'manual'|'auto', segmenter: 'embedding'|'fixed'}, access='public', author_raw=channel_id, thread_key=f"{start_s}-{end_s}")`.

**분할 알고리즘 (`captions.segment`)** — 결정적이어야 한다(같은 입력 · 같은 임베더 → 같은 결과).
1. cue를 시작 시각 순으로 `window_s`(20초) 창에 묶는다. 창이 2개 미만이거나 영상이 `min_s` 미만이면 구간 1개.
2. 임베더로 창 텍스트를 한 번에 임베딩한다. 임베더가 `None`이거나 예외(`EmbedderUnconnected` 포함)를 내거나 0행을 돌려주면 **고정 구간**(`fixed_s`=90초)으로 대체하고 `segmenter='fixed'`.
3. 이웃 창 코사인 유사도 `s_i`를 구하고 TextTiling 깊이 `d_i = (왼쪽 최고 s − s_i) + (오른쪽 최고 s − s_i)`를 계산한다. 경계 후보는 `d_i > mean(d) − std(d)/2`.
4. 후보를 깊이 내림차순(동점이면 앞쪽 시각)으로 채택하되, 양쪽 구간이 `min_s`(45초) 이상일 때만 채택한다.
5. `max_s`(300초)를 넘는 구간은 그 안의 깊이가 가장 큰 창 경계에서 다시 자르고, 후보가 없으면 `fixed_s` 간격으로 자른다.
6. 경계 시각은 초 단위 정수로 내림한다(`thread_key`에 쓰이므로 부동소수 표기 차이를 없앤다).

### 3.2 Threads (`threads`)
1. **목록:** `WebSearchProvider`가 `RenderBridge`로 `https://www.threads.com/search?q={kw}&serp_type=default`와 최신 보기를 각각 렌더링한다. 글 링크 `/@{user}/post/{code}`와 글 텍스트 · 표시 날짜를 파싱하고 두 보기를 `code`로 합친다. 커서 없음.
   - 로그인 창만 있고 글이 0건이면 `AdapterBlocked(host='threads.com')`. 검색 결과 없음 표시가 있으면 빈 페이지.
   - 로그인 · 쿠키 · 프록시 · 브라우저 위장 설정은 쓰지 않는다(G2). 요청 간격 2초, 동시 1.
2. **상세:** 네트워크 요청 없이 목록 항목을 문서로 돌려준다 — `FetchedDoc(title='', body=item.snippet, comments=[], date=item.date, src_meta={post_code, like_count?, reply_count?}, access='public', author_raw=username)`. 사용자 이름은 원문으로 저장하지 않고 `author_hash`로만 남긴다(URL에는 공개 주소로 포함).
3. **공급자 경계:** `ThreadsSearchProvider` 프로토콜 하나. 공식 API 공급자(`threads_keyword_search`)는 이번에 만들지 않고, 설정값 `threads_provider='web'`만 둔다.

### 3.3 지식iN (`naver_kin`)
1. **목록:** `https://kin.naver.com/search/list.naver?query={kw}&page={n}`, 커서 = 페이지 번호(1부터). 결과 0건 표시면 빈 페이지, 결과 행이 있는데 제목 링크를 못 찾으면 파싱 오류. 같은 페이지가 반복되면 끝(네이버 어댑터의 반복 감지와 같은 방식).
2. **상세:** 정규화 URL(`dirId` · `docId`) 요청 → 제목(`.endTitleSection`, 앞의 아이콘 · 숨김 텍스트 제외), 본문(`.questionDetail` 텍스트, 이미지 자리표시 제거), 작성일, `src_meta={dir_id, doc_id, answer_count, tags}`. 답변 본문은 읽지 않는다. 작성자는 대부분 비공개라 `author_raw=None`.
3. 호스트가 `search.naver.com`이 아니므로 네이버 검색 공용 제한기를 쓰지 않고 채널 자체 제한기(0.5초, ±20% 흔들림)를 쓴다.

### 3.4 82쿡 (`cook82`)
1. **목록:** `https://www.82cook.com/entiz/enti.php?bn=15&searchType=search&search1=1&keys={kw}&page={n}`, `tbody tr` 중 `tr.noticeList` 제외, 링크 `read.php?bn=15&num=`, 날짜 `td.regdate`. `search1` 값의 검색 범위(제목 / 제목+본문)는 계획 단계에서 녹화 응답으로 확정한다.
2. **상세:** 제목 `h4.title.bbstitle`, 본문 `#articleBody`, 댓글 `ul.reples > li.rp` → `Comment(text=p, depth=0, date=정규화('26.10.4 11:04 AM'→2026-10-04), author_hash)`. `#writerIP` · `.ip`는 읽지 않는다. 작성자 = 목록의 `td.user_function` 닉네임.

## 4. 데이터 · API 계약

- 새 문서 필드는 없다. `Doc` 스키마 그대로, `source` 값만 4개 늘어난다.
- doc_id: `{yv|th|kn|c8}_` + `sha1(url_norm + thread_key)[:16]`. 브이로그만 `thread_key`(구간)를 쓴다.
- `PUT /crawl/{sid}/config`: `youtube_vlog` 객체를 받는다(없으면 기본값). `channels`에 새 채널 이름을 받는다(사용 불가 채널이면 기존처럼 422 `sources_unavailable`).
- `GET /crawl/{sid}/status`: `progress.skipped`(채널 × 사유 건수) 추가. `report.channels[s].skip_reasons` 추가. 기존 필드는 그대로.
- 새 엔드포인트 없음. 권한 모델 변화 없음 — 쓰기는 기존처럼 활성 버전에서만, 과거 버전은 열람만(D-080/D-089), 읽기 전용 화면에서는 모든 입력 · 스위치가 잠긴다(목업 "읽기 전용").
- 분류 모델 입력 차원 1032 유지 — 새 채널은 채널 특징이 0이다(`model/features.py` 변경 없음).

## 5. 오류 처리

| 상황 | 처리 | 화면 |
|---|---|---|
| 한국어 자막 없음 | `AdapterSkipped('no_ko_captions')` → `skipped` | 수집 중 "건너뜀" 열, 결과 사유 표 |
| 임베더 미연결 · 실패 | 고정 90초 구간, `segmenter='fixed'` | 표시 없음(문서 메타로 추적) |
| Threads 로그인 창 · 빈 결과 | `AdapterBlocked(host='threads.com')`, 연속 20회면 채널만 `paused_blocked` | 멈춤 배너 + Threads 문장, "여기까지로 마치기" 가능 |
| Crawl4AI · Chromium 미설치 | `threads` 사용 불가 | 설정 표 "사용 불가" 배지 + 이유 한 줄 |
| 유튜브 봇 확인 · 403 · 429 | 기존 `AdapterBlocked` | 기존과 같음 |
| 지식iN · 82쿡 구조 변경 | `ValueError` → 파싱 오류(30% 넘으면 `paused_parse_error`) | 기존과 같음 |
| 지식iN 삭제된 질문 | 본문 블록 없음 + 삭제 안내 문구 → `AdapterSkipped('deleted')` | 사유 표 "삭제된 글" |

## 6. 화면 변경 (목업 기준)

| 화면 | 변경 | 상태별 동작 |
|---|---|---|
| ① 설정 | 채널 표 4행 추가, 고급 설정 "유튜브 브이로그" 칸 3개, 키워드 카드 안내 1줄 | 로딩: 기존 "처리 중…" · 오류: 상단 오류 배너, Threads 사용 불가 · 읽기 전용: 모든 입력 잠금 |
| ② 게이트 | Threads 안내 배너(Threads 선택 시), 예상 카드 안내 1줄 | 빈 결과: 기존 "수집된 목록이 없습니다" |
| ③ 수집 중 | 채널 표 "건너뜀" 열, Threads 차단 문장 | 오류·차단: 기존 멈춤 배너 + Threads 문장 |
| ④ 결과 | 건너뛴 항목 표(채널 × 사유 × 건수), 브이로그 분포 줄 보충 | 빈 결과: "건너뛴 항목이 없습니다" |
| 모바일 | 기존 반응형 규칙 그대로(`crawl-columns` 세로 쌓기, 표 가로 스크롤) | — |

## 7. 테스트 전략

- **어댑터:** 녹화 응답 픽스처로 네트워크 없이 — 지식iN 목록 · 질문 · 삭제 질문, 82쿡 목록(공지 포함) · 글(댓글 포함), Threads 렌더링 HTML(정상 · 로그인 창 · 결과 없음), yt-dlp 정보 dict(수동 · 자동 · 자막 없음). 픽스처의 실제 글 · 자막 본문은 구조 검증에 필요한 만큼만 남기고 줄인다.
- **분할:** 합성 cue + 결정적 가짜 임베더로 경계 위치, `min_s` · `max_s` 준수, 임베더 없음 · 예외 · 0행 대체, 같은 입력 반복 시 같은 구간.
- **워커 · 큐 · 보고서:** `AdapterSkipped` → `skipped` 상태 · 시도 수 미증가, 보고서 `skip_reasons`, `progress.skipped`, 기존 워커 테스트 회귀.
- **설정 API:** `youtube_vlog` 검증(경계값, `min ≥ max` 거부), 사용 불가 채널 거부.
- **프론트:** `crawlConfig` 기본값 · 파싱, 사유 이름표, Vitest. 화면은 브라우저 QA(설정 행 · 브이로그 칸 · 게이트 배너 · 결과 표 · 읽기 전용 잠금 · 모바일).
- **수동 확인(AC-12):** 실제 사이트에서 채널별 키워드 2개로 목록 → 상세 → 보고서, 결과를 구현 보고서에 첨부.

## 8. 계획 단계로 넘기는 확인 항목

1. Crawl4AI 헤드리스 렌더링에서 Threads 검색 결과가 로그인 없이 보이는지(위장 설정 없이). 안 보이면 `threads` 채널은 "사용 불가"로 두고 공식 API 공급자를 다음 작업으로 올린다.
2. 82쿡 `search1` 값별 검색 범위.
3. 맥미니 운영 환경의 Voyage 키 유무 — 없으면 브이로그는 항상 고정 90초 구간이 된다.
4. `crawl4ai-setup`(Playwright Chromium 설치)이 운영 설치 스크립트(`ops/macmini/install.sh`)에 포함되는지.
