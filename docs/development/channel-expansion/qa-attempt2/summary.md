# Independent browser QA — FAIL

16 PASS, 1 FAIL, 0 BLOCKED, 0 NOT_RUN.

| ID | Result | Actual |
|---|---|---|
| [QA-E2E-001](QA-E2E-001.md) | PASS | 새 채널 네 행 각각 1개, 새 채널 배지, 사용 가능 및 스위치 off→on 확인. 브이로그/Threads 수집 방식 문구와 기존 5개 채널 유지. |
| [QA-E2E-002](QA-E2E-002.md) | PASS | 새로고침 후 5·2·30. API 저장값 videos_per_keyword=5,min_duration_s=120,max_duration_s=1800. 안내 문구 존재, 스위치 off에서 설정 그룹 제거. |
| [QA-E2E-003](QA-E2E-003.md) | PASS | 목록 완료 게이트 제목, Threads 약20건 배너, 브이로그 구간 안내, qa-empty 0건 배지 확인. 에어컨청소 행을 실제 펼쳐 네 채널 내역 확인. 대상 URL=86. |
| [QA-E2E-004](QA-E2E-004.md) | PASS | 실행 중 및 완료 후 건너뜀 열 존재. 완료 후 브이로그 2 (자막 없음), 지식iN 2 (삭제된 글), Threads 완료. progress.skipped.youtube_vlog.no_ko_captions=2. |
| [QA-E2E-005](QA-E2E-005.md) | PASS | 건너뛴 항목: 브이로그 한국어 자막 없음 2개 영상, 지식iN 삭제된 글 2건. report와 일치. 네 채널 분포, 영상 8개 → 구간 16, 전처리 버튼. 수집 문서 90. |
| [QA-E2E-006](QA-E2E-006.md) | PASS | 기본 설정/fake 임베더로 완료. 오류 없음. 원본=90, 통과=90, 임베딩=90; 수집 문서 90과 일치. 분석 채널에 네 새 채널 모두 존재. |
| [QA-NEG-001](QA-NEG-001.md) | PASS | 30·10 입력 시 저장/목록 수집 시작 disabled. 직접 PUT 422 invalid_request. 이전 저장값 5/120/1800 불변. |
| [QA-NEG-002](QA-NEG-002.md) | PASS | Threads 사용 불가 배지와 Crawl4AI 브라우저 미설치 문구. 스위치 disabled, available_sources에 threads 없음, threads PUT=422 sources_unavailable. |
| [QA-NEG-003](QA-NEG-003.md) | PASS | Threads 차단 후 멈춤 배너·Threads 배지·로그인 미시도 문구 확인. 확인창 승인 후 결과에 Threads 차단으로 여기까지 마침 50건. 브라우저 요청과 제공된 워커 로그에 threads.com 로그인 요청 없음. |
| [QA-NEG-004](QA-NEG-004.md) | PASS | videos_per_keyword=0 직접 PUT이 422 invalid_request 반환. |
| [QA-EDGE-001](QA-EDGE-001.md) | PASS | qa-empty 단일 키워드 목록 완료. 수집된 목록이 없습니다 안내, 대상 URL=0, 오류 배너 없음. |
| [QA-EDGE-002](QA-EDGE-002.md) | PASS | v2 생성 후 v1 readonly=true. v1 결과 및 건너뛴 사유 표 유지. 일시 정지하기/다시 수집 없음, 자동 연쇄 체크박스 disabled. |
| [QA-EDGE-003](QA-EDGE-003.md) | FAIL | 375px 설정/결과에서 document.scrollWidth=375. 네 행과 건너뜀 표의 세 열은 보이나, 설정/건너뜀 표는 자체 가로 스크롤 없이 폭204px로 축소되고 Threads 및 한국어가 여러 줄로 쪼개짐. 계획의 표 가로 스크롤 요구 불충족. |
| [QA-EDGE-004](QA-EDGE-004.md) | PASS | 0·1분 저장 성공; API min_duration_s=0,max_duration_s=60. |
| [QA-REG-001](QA-REG-001.md) | PASS | 샘플 전용 목록→게이트→상세→결과 완료. 수집 문서 2,000>0. 건너뛴 항목이 없습니다 및 전처리로 이동하기 존재. |
| [QA-REG-002](QA-REG-002.md) | PASS | 유튜브 댓글 영상 수20/댓글500 필드 유지. 네이버 카페·블로그·뽐뿌·클리앙 동시성1/간격0.5초; 블로그 요구 기본값과 일치. |
| [QA-REG-003](QA-REG-003.md) | PASS | 0단계 기존/새 4채널 선택지 모두 존재. Threads 선택해 새 프로젝트 저장 POST201. GET session.projectContext.channels=[threads], 재열람 선택 상태 유지. |
