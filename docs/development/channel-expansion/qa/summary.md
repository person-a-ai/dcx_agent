# Independent browser QA — PASS

17/17 active scenarios passed at `ff4d4d163021e0c476897be0abecdb440f3996f1`.

Fingerprint: `3e73f4f996f1e1ad1b2152feacc356506d51ba32d37cd722e73f060fd931c86f`.

Dispatch: `01a15985-5ca6-76a2-84dc-0a2a9040839c`.

| ID | Result | Actual |
|---|---|---|
| [QA-E2E-001](QA-E2E-001.md) | PASS | [{"name":"유튜브 브이로그","count":1,"text":"유튜브 브이로그 새 채널\t\"키워드 브이로그\" 영상 검색 · 한국어 자막을 화제 단위로 나눠 문서화\t사용 가능\t\n유튜브 브이로그 사용하기","enabled":true},{"name":"Threads","count":1,"text":"Threads 새 채널\t검색 화면(로그인 없음) · 글 본문 · 키워드당 약 20건\t사용 가능\t\nThreads 사용하기","enabled":true},{"name":"지식iN","count":1,"text":"지식iN 새 채널\t질문 검색 · 질문 제목과 본문 (답변 제외)\t사용 가능\t\n지식iN 사용하기","enabled":true},{"name":"82쿡","count":1,"text":"82쿡 새 채널\t자유게시판 검색 · 본문 · 댓글\t사용 가능\t\n82쿡 사용하기","enabled":true}] |
| [QA-E2E-002](QA-E2E-002.md) | PASS | {"values":["5","2","30"],"stored":{"videos_per_keyword":5,"min_duration_s":120,"max_duration_s":1800},"hidden":true,"hint":"유튜브 브이로그\n키워드당 영상 수\n최소 길이(분)\n최대 길이(분)\n\n1분 미만 쇼츠와 60분이 넘는 영상은 목록에서 뺍니다. 한국어 자막이 없는 영상은 건너뛰고 결과에 건수를 남깁니다."} |
| [QA-E2E-003](QA-E2E-003.md) | PASS | All specified gate text visible; qa-empty has 0건; 에어컨 청소 expanded with four channels. 86 target URLs. |
| [QA-E2E-004](QA-E2E-004.md) | PASS | {"rows":["채널상태시도차단파싱 오류건너뜀","82쿡완료1600—","지식iN완료8002 (삭제된 글)","Threads완료5000—","유튜브 브이로그완료8002 (자막 없음)"],"skipped":{"naver_kin":{"deleted":2},"youtube_vlog":{"no_ko_captions":2}}} |
| [QA-E2E-005](QA-E2E-005.md) | PASS | 90 documents; vlog 2 videos skipped, Kin 2 deleted; all four channels; vlog 영상 8개 → 구간 16; preprocess button visible. |
| [QA-E2E-006](QA-E2E-006.md) | PASS | 90 originals, 90 retained, 90 embeddings completed; four new channel checkboxes; no error banner. |
| [QA-NEG-001](QA-NEG-001.md) | PASS | {"disabled":{"save":true,"start":true},"invalid":{"http":422,"body":{"status":"error","error":{"kind":"validation","code":"invalid_request","message":"Invalid crawl request"}}},"same":true} |
| [QA-NEG-002](QA-NEG-002.md) | PASS | {"row":"Threads 새 채널 사용 불가\t검색 화면(로그인 없음) · 글 본문 · 키워드당 약 20건\n\nCrawl4AI 브라우저가 설치돼 있지 않아 사용할 수 없습니다.\n\n\t사용 불가\t\nThreads 사용하기","disabled":true,"available":["naver_blog","naver_cafe","naver_kin","cook82","youtube","youtube_vlog","clien","ppomppu"],"put":{"http":422,"body":{"status":"error","error":{"kind":"validation","code":"sources_unavailable","message":"Sources are unavailable"}}}} |
| [QA-NEG-003](QA-NEG-003.md) | PASS | Paused after 20 blocked attempts; confirmed finish; Threads 차단으로 여기까지 마침 50건. Browser login requests zero; copied list.log/detail.log contain no login URLs, queue consists of qa.invalid URLs, network-free QA hook raises AdapterBlocked without login. See logs-blocked/ and qa-hook-inspected.py. |
| [QA-NEG-004](QA-NEG-004.md) | PASS | {"http":422,"body":{"status":"error","error":{"kind":"validation","code":"invalid_request","message":"Invalid crawl request"}}} |
| [QA-EDGE-001](QA-EDGE-001.md) | PASS | 수집된 목록이 없습니다; target URL 0; no error banner. Given and status in evidence. |
| [QA-EDGE-002](QA-EDGE-002.md) | PASS | Skipped table visible; restart isDisabled=true (aria-disabled=true); pause/recollect absent. Earlier evidence edge002-pass.json incorrectly tested only native .disabled and produced a false QA-script failure; preserved, corrected by live semantics and screenshot. Same actual completed session and version picker used. |
| [QA-EDGE-003](QA-EDGE-003.md) | PASS | Document widths 375/1100/1200/1300 exactly match viewport. At 375px table clientWidth206, scrollWidth600; scrollLeft 0/200/394 exposes 채널/사유/건수. Four new settings rows present and viewed. See edge003-settings.json, edge003-result.json, edge003-mobile-new-rows.json and screenshots. |
| [QA-EDGE-004](QA-EDGE-004.md) | PASS | {"videos_per_keyword":5,"min_duration_s":0,"max_duration_s":60} |
| [QA-REG-001](QA-REG-001.md) | PASS | 2,000 documents; 건너뛴 항목이 없습니다.; preprocess button visible. See sample-session.json, reg001-gate.json, reg001-start.json and logs-sample/. |
| [QA-REG-002](QA-REG-002.md) | PASS | {"defaults":[{"name":"네이버 카페","values":["1","0.5","1000"]},{"name":"네이버 블로그","values":["1","0.5","1000"]},{"name":"뽐뿌","values":["1","0.5","1000"]},{"name":"클리앙","values":["1","0.5","1000"]}],"videos":"20","comments":"500"} |
| [QA-REG-003](QA-REG-003.md) | PASS | {"options":["네이버 카페","네이버 블로그","유튜브","뽐뿌","클리앙","개발용 샘플","유튜브 브이로그","Threads","지식iN","82쿡"],"sid":"s613cb442a2d44c028b33677e27c36556","channels":["youtube_vlog"]} |

No findings. Product tracked files and Git index unchanged. Controller servers untouched. Browser closed. See tool-artifacts.md for MCP-generated files outside qa/.
