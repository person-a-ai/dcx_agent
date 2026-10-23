# DCX Agent (DCX 2.0)

키워드 생성부터 다채널 수집, 전처리·라벨링·학습, 근거 탐색과 페르소나·인사이트 도출까지 이어지는 소비자 분석 파이프라인입니다.

운영 주소: 웹 https://dcx.person-a.ai · API https://dcx-api.person-a.ai

## 기술 스택

| 구분 | 기술 |
|---|---|
| Backend | FastAPI · PyTorch(CPU 멀티헤드 앙상블) · scikit-learn |
| Frontend | Next.js 16 · React 19 · Zustand · Tailwind CSS 4 · D3.js |
| LLM | OpenAI API(기본) · Claude API(선택) · 라벨링 Codex(`codex exec`) |
| 임베딩 | Voyage AI + 로컬 벡터 샤드(별도 벡터 DB 없음) |
| 저장소 | 로컬 디스크(`STORAGE=local` 기본, S3 선택) |
| 운영 | 맥미니 launchd(LaunchAgent) · Cloudflare 터널 |

프런트 버전은 `frontend/package.json`, 백엔드 의존성은 `backend/requirements.txt`를 기준으로 합니다.

## 파이프라인 단계

| 단계 | 화면 경로 | 역할 | 백엔드 라우터 · 패키지 |
|---|---|---|---|
| 0 시작 | `/pipeline/start` | 프로젝트 맥락과 제품군 제안을 생성합니다. | `backend/app/routers/context.py` · `backend/app/context/` |
| 1 키워드 | `/pipeline/keywords` | 3축 분류와 라운드별 생성·피드백, 검색량·커버리지를 다룹니다. | `backend/app/routers/keywords_v2.py` · `backend/app/keywords/` |
| 2 크롤링 | `/pipeline/crawling` | 채널별 큐·워커로 수집하고 필터·정규화·리포트를 만듭니다. | `backend/app/routers/crawl_v2.py` · `backend/app/crawl/` |
| 3 전처리 | `/pipeline/preprocess` | 규칙 필터·정제·Kiwi 토큰 처리와 임베딩 샤드를 생성합니다. | `backend/app/routers/prep.py` · `backend/app/prep/` · `backend/app/vectors/` |
| 4 라벨링 | `/pipeline/labeling` | Jev·GPT 판정, 캘리브레이션·라우팅·감사를 수행합니다. | `backend/app/routers/labeling_v2.py` · `backend/app/label/` |
| 5 학습 | `/pipeline/training` | 다중 헤드 학습·확률 보정·추론·감시 재판정을 수행합니다. | `backend/app/routers/training_v2.py` · `backend/app/model/` |
| 6 클러스터링 | `/pipeline/clustering` | Ward/K-means·네트워크 모듈성·LDA로 구획하고 초안을 확정합니다. | `backend/app/routers/segment.py` · `backend/app/segment/` |
| 7 근거 탐색 | `/pipeline/evidence` | 쿼리 생성·검증, 필터 검색·지연 태깅·리랭킹으로 Evidence Package를 만듭니다. | `backend/app/routers/evidence.py` · `backend/app/evidence/` |
| 8 페르소나 | `/pipeline/personas` | 지표·카드·등급 판정과 맵·트리를 만듭니다. | `backend/app/routers/stage8.py` · `backend/app/persona/` |
| 8 인사이트 | `/pipeline/insights` | 8-E·8-F 결과를 생성하고 채팅으로 수정합니다. | `backend/app/routers/stage8.py` · `backend/app/persona/` |
| 버전 비교 | `/pipeline/compare` | 세션 버전을 비교합니다. | `backend/app/routers/sessions.py` · `backend/app/context/` |

수집 채널은 9개입니다: 네이버 블로그(`naver_blog`), 네이버 카페(`naver_cafe`), 네이버 지식iN(`naver_kin`), YouTube 댓글(`youtube`), YouTube 브이로그(`youtube_vlog`), Threads(`threads`), 클리앙(`clien`), 뽐뿌(`ppomppu`), 82쿡(`cook82`). 구현은 `backend/app/crawl/adapters/`에 있습니다.

## 프로젝트 구조

```text
dcx_agent/
├── backend/             # FastAPI · 분석 패키지 · 테스트
├── frontend/            # Next.js 화면 · 상태 · API 클라이언트
├── ops/macmini/         # 맥미니 설치 · 배포 · 운영
├── docs/development/    # 개발 기획 · 설계 · 계획 · 검증 기록
├── .github/workflows/  # GitHub CI
├── scripts/             # 예전 EC2 배포용 — 현재 운영에 쓰지 않음
└── nginx/               # 예전 EC2 배포용 — 현재 운영에 쓰지 않음
```

## 로컬 개발

Python 3.12, Node.js와 npm, Git이 필요합니다. CI는 Node 26을 사용합니다(`.github/workflows/ci.yml`).

```bash
git clone https://github.com/uyunho99/dcx_agent.git
cd dcx_agent
cp .env.example .env
```

저장소 기본값은 `STORAGE=local`입니다. AWS 키 없이 로컬 디스크를 사용하며, `LOCAL_DATA_DIR=data`가 데이터 경로입니다(백엔드에서 실행하면 backend/data/). 필요한 연동의 키를 .env에 설정하고 커밋하지 않습니다.

백엔드는 레포지토리 루트에서 설치합니다.

```bash
python3.12 -m venv backend/.venv
cd backend
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt -c constraints.txt
crawl4ai-setup
uvicorn app.main:app --reload --port 8000
```

`crawl4ai-setup`은 크롤링용 브라우저를 준비합니다. API는 http://localhost:8000, 헬스체크는 http://localhost:8000/health, API 문서는 http://localhost:8000/docs 입니다.

별도 터미널에서 레포지토리 루트를 기준으로 프런트를 실행합니다.

```bash
cd frontend
npm ci
npm run dev
```

브라우저에서 http://localhost:3000 에 접속합니다.

검증은 레포지토리 루트에서 `harness.config.json`의 네 명령을 실행합니다.

```bash
backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
```

오프라인 판정·임베딩 점검에는 `EMBED_BACKEND=fake`, `JEV_BACKEND=fake`, `LABEL_GPT_BACKEND=fake`를 함께 설정하세요.

## 배포·운영

운영 서버는 맥미니이며, 운영 사용자(현재 맥미니는 `tech`)의 루트는 ~/srv/dcx-agent 입니다. launchd LaunchAgent와 Cloudflare 터널로 운영하므로 사용자 로그인 세션을 유지해야 합니다.

PR → main 머지(직접 push 금지) → 배포 잡이 main을 120초마다 폴링 → 검사 → 배포 순서입니다. shared/ci-mode 값이 `local`이면 맥미니가 백엔드 pytest와 프런트 lint·test·build를 직접 실행합니다. 그 외에는 GitHub CI 통과를 기다립니다. 배포 후 헬스체크 실패 시 자동 롤백합니다.

상태 확인과 수동 롤백 명령:

```bash
APP_ROOT="$HOME/srv/dcx-agent" "$HOME/srv/dcx-agent/ops/dcxctl" status
APP_ROOT="$HOME/srv/dcx-agent" "$HOME/srv/dcx-agent/ops/dcxctl" rollback
```

로그는 ~/srv/dcx-agent/logs/ 아래 deploy.log, api.log, web.log, local-ci-<sha>.log에 남습니다. 설치·복구·롤백 범위는 [맥미니 운영 안내](ops/macmini/README.md)를 참고하세요.

## 환경변수

로컬 설정은 .env, 운영 키는 shared/app.env, 설치기가 관리하는 운영 설정은 shared/runtime.env에 둡니다. 아래 기본값은 `backend/app/config.py` 기준입니다. 인증값은 필요한 연동에 맞게 설정합니다.

| 변수 | 필요할 때 | 설명 |
|---|---|---|
| `STORAGE` / `LOCAL_DATA_DIR` | 저장소 설정 | 기본 `local` / `data`; S3 사용 시 `STORAGE=s3` |
| `LLM_BACKEND` / `LLM_BACKEND_OVERRIDES` | LLM 선택 | 기본 `openai_api` / `{}`; 작업별 백엔드 재정의 |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI API 사용 시 | 인증과 모델 선택; 기본은 각각 빈 문자열 |
| `CLAUDE_API_KEY` / `CLAUDE_MODEL` | Claude API 사용 시 | 인증과 모델 선택; 모델 기본 `claude-sonnet-4-20250514` |
| `CODEX_BIN` / `CODEX_PROFILE` / `CODEX_TIMEOUT_S` | Codex 사용 시 | 실행 파일 `codex` / 프로필 `dcx-worker` / 제한 시간 `600`초 |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | 네이버 검색 연동 시 | 네이버 오픈 API 인증 |
| `SEARCHAD_API_KEY` / `SEARCHAD_SECRET` / `SEARCHAD_CUSTOMER_ID` | 네이버 검색광고 연동 시 | 검색량 조회 인증; 기본은 각각 빈 문자열 |
| `YOUTUBE_API_KEY` | YouTube Data API 사용 시 | API 인증; 기본 빈 문자열 |
| `AUTHOR_SALT_PATH` | 작성자 해시 생성 시 | salt 파일 위치; 기본 `data/.author_salt` |
| `S3_BUCKET` / `S3_REGION` | `STORAGE=s3`일 때만 필수 | S3 버킷과 리전; 로컬 저장에서는 불필요 |
| `VOYAGE_API_KEY` | Voyage 임베딩 사용 시 | Voyage API 인증 |
| `CORS_ORIGINS` | 브라우저 접근 설정 | 허용 origin; 기본 `*`, 운영에서는 웹 주소 지정 |
| `EMBED_BACKEND` | 임베딩 선택 | 기본 `voyage`, 오프라인 `fake` |
| `EMBED_MODEL` / `EMBED_DIM` | 임베딩 설정 | 기본 `voyage-4` / `1024` |
| `JEVMODEL_API_KEY` | Jev HTTP 사용 시 | Jev API 키; 여러 키는 쉼표로 구분, 기본 빈 목록 |
| `JEV_BACKEND` / `JEV_MODEL` | Jev 설정 | 기본 `http` / `jev-latest`, 오프라인 `fake` |
| `JEV_RATE_PER_MIN` | Jev 사용 시 | 키당 분당 요청 수; 기본 `120` |
| `LABEL_FAKE_JEV_CROSS` | 테스트·오프라인 QA | fake Jev를 교차 판정 라벨러로 취급; 기본 `false` |
| `LABEL_GPT_BACKEND` | GPT 라벨링 | 기본 `codex_exec`; `openai_api`, `fake` 선택 가능 |
| `LABEL_BATCH_SIZE` / `LABEL_CONCURRENCY` | 라벨링 처리량 조정 | 묶음 문서 수 `20` / 동시 묶음 수 `4` |
| `LABEL_CAPACITY_RETRIES` | 모델 용량 초과 시 | 같은 묶음 재시도 횟수; 기본 `2` |
| `LABEL_FAILURE_PAUSE_AFTER` | Codex 라벨링 실패 시 | 성공 없이 연속 실패한 묶음 수가 이 값이면 정지; 기본 `5` |
| `LABEL_PRIORITY_SOURCES` | 라벨링 채널 우선순위 | 기본 `["naver_blog","naver_cafe"]` |
| `SEGMENT_CONCURRENCY` | 6단계 처리량 조정 | 경험 차원 묶음·이름 초안 동시 처리 수; 기본 `4` |
| `EVIDENCE_LLM_CONCURRENCY` | 7단계 처리량 조정 | LLM 동시 호출 수; 기본 `4` |
| `KNOWN_THETA` | Known Insight 제외 | 유사도 기준; 기본 `0.85` |
| `MODEL_CUT_LOW` / `MODEL_CUT_HIGH` | 모델 사람 검수 | 검수 구간; 기본 `0.2` / `0.8` |
| `MONITOR_RATE` / `MONITOR_WARN` | 모델 감시 | 감시 비율 `0.01` / 괴리 경고 기준 `0.15` |
| `HEAD_MIN_SAMPLES` | 모델 학습 | 헤드별 최소 학습 표본 수; 기본 `30` |
| `AUDIT_FIRST` / `AUDIT_EVERY` | 라벨링 감사 | 첫 감사 채택 수 `1000` / 이후 간격 `10000` |
| `AUDIT_SIZE` / `AUDIT_REISSUE` | 라벨링 감사 | 감사 표본 수 `50` / 재판정 수 `2` |
| `KAPPA_FLOOR` | 태그 정의 점검 | κ 기준; 기본 `0.75` |

그 밖의 값은 `.env.example`·`backend/app/config.py` 참고.

Jev 키가 없거나 `JEV_BACKEND=fake`이면 라벨링은 GPT 단독 판정으로 시작합니다(D-340). Jev 실행 없이 GPT 판정을 그대로 채택하고 confidence는 비웁니다. Jev를 연결한 뒤 새 버전에서 라벨링을 시작하면 교차 판정합니다.

3단계에서 만든 로컬 벡터로 Core · Supporting 문서를 검색하며, Known Insight 필터를 적용합니다.
별도의 벡터 DB 업로드나 API 키가 필요하지 않습니다.

## 상세 문서

- [AI 코딩 작업 규칙](CLAUDE.md)
- [백엔드 구조와 API](backend/BACKEND.md)
- [파이프라인 단계별 구성](frontend/PIPELINE.md)
- [맥미니 운영 안내](ops/macmini/README.md)
- [개발 기획·설계·검증 기록](docs/development/)
