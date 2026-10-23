# docs-refresh — 02 설계

승인된 기획: 대안 A (구조 유지·내용 갱신, `CLAUDE.md` 신설, 예전 EC2 파일은 유지·표시만). 2026-10-23 사용자 승인.

## 1. 동작

코드·스크립트·설정 동작은 바뀌지 않는다. 바뀌는 것은 아래 6개 문서의 내용뿐이다.

| 파일 | 처리 |
|---|---|
| `README.md` | 다시 씀 (구조 3절) |
| `backend/BACKEND.md` | 다시 씀 (구조 4절) |
| `frontend/PIPELINE.md` | 다시 씀 (구조 5절) |
| `frontend/README.md` | create-next-app 기본 문구를 짧은 안내로 교체 (6절) |
| `ops/macmini/README.md` | 운영 사용자 표기만 수정 (7절) |
| `CLAUDE.md` | 신규 (8절) |

UI가 해당하지 않는 이유: 화면·프런트 코드 변경이 없고 Markdown 문서만 바뀐다. 브라우저 QA 대신 문서 사실 검사(9절)를 한다.

## 2. 사실의 출처 (문서에 쓰는 모든 사실은 여기서만 가져온다)

| 사실 | 출처 |
|---|---|
| 단계·화면 | `frontend/src/components/StepBar.tsx` 10개 항목, `frontend/src/app/pipeline/*` |
| 단계 번호·역할 | `docs/development/dcx2-stage0-2/02-design.md` 1절, `dcx2-stage3-5/02-design.md` 1절, `dcx2-stage6-8/02-design.md` 1절, 각 패키지 `__init__.py` docstring |
| API | 앱의 OpenAPI 출력(`app.openapi()`, 현재 93 operation)과 `backend/app/routers/*.py` |
| 패키지 구조 | `backend/app/` 실제 디렉터리 |
| 크롤링 채널 | `backend/app/crawl/adapters/`, `crawl/channels.py` |
| 환경변수 | `backend/app/config.py`, `.env.example` |
| 배포·운영 | `ops/macmini/deploy.sh`, `ops/macmini/README.md`, 운영 맥미니 읽기 전용 확인(`dcxctl status`, `shared/ci-mode`, LaunchAgent 목록, 자동 로그인 사용자) |
| 검증 명령 | `harness.config.json`, `.github/workflows/ci.yml` |
| 작업 규칙 | `~/.claude/skills/development-harness-native/SKILL.md`·`OPERATIONS.md` |

출처에서 확인되지 않는 내용은 쓰지 않는다. 기존 문서의 설명 중 출처와 맞는 문장(예: Jev 미연결 시 GPT 단독 판정, 오프라인 fake 설정)은 그대로 살린다.

## 3. `README.md` 구조

1. 제목·한 줄 소개·운영 주소(웹 `https://dcx.person-a.ai`, API `https://dcx-api.person-a.ai`)
2. 기술 스택 표: FastAPI·PyTorch(CPU 멀티헤드)·scikit-learn / Next.js 16·React 19·Zustand·Tailwind 4·D3 / LLM: OpenAI API 기본·Claude API 선택·라벨링 Codex / Voyage 임베딩 + 로컬 벡터 샤드 / 로컬 디스크 저장(S3 선택) / 맥미니 launchd + Cloudflare 터널
3. 파이프라인 단계 표: 단계 번호(0~8), 화면 경로, 하는 일 한 줄, 백엔드 라우터·패키지. 8단계는 페르소나·인사이트 두 줄. `/pipeline/compare`(버전 비교) 한 줄. 크롤링 채널 9개 나열
4. 프로젝트 구조 트리: 최상위 디렉터리와 역할. `scripts/`(deploy.sh·systemd)와 `nginx/`는 "예전 EC2 배포용 — 현재 운영에 쓰지 않음"으로 표시
5. 로컬 개발: Python 3.12, Node(CI는 26), 클론, `.env`, 백엔드(`-c constraints.txt` 포함, `crawl4ai-setup`), 프런트, 테스트 4개 명령(`harness.config.json`과 동일), 오프라인 fake 설정
6. 배포·운영 요약: 운영 맥미니(운영 사용자 `tech`, 루트 `~/srv/dcx-agent`), PR → main 머지 → 120초 폴링 → 검사(`ci-mode=local`이면 맥미니, 없으면 GitHub CI) → 배포 → 실패 시 자동 롤백. `dcxctl status`·`rollback` 명령, 로그 위치, 상세는 ops README 링크. EC2 절차 전부 삭제
7. 환경변수 표: `config.py`의 사용자 설정 항목. "필요할 때" 열로 조건 표기(S3는 `STORAGE=s3`일 때만). 운영 값 위치(`shared/app.env`, `shared/runtime.env`)
8. 상세 문서 링크: `CLAUDE.md`, `backend/BACKEND.md`, `frontend/PIPELINE.md`, `ops/macmini/README.md`, `docs/development/`

## 4. `backend/BACKEND.md` 구조

1. 개요: FastAPI 앱(`app/main.py`), 라우터 14개 등록, `/health`는 `{"status","release"}` 반환
2. 패키지 표: `backend/app/` 아래 실제 패키지 전부(context, crawl, evidence, external, jobs, keywords, known, label, lexicon, llm, model, models, persona, prep, routers, segment, services, utils, vectors, work)와 역할 한 줄, 해당 단계
3. LLM 공통 층: `app/llm/registry.py`의 `run_task`·`get_backend`, 백엔드 `openai_api`(기본)·`claude_api`·`codex_exec`·`fake`, `LLM_BACKEND_OVERRIDES`
4. 저장소: `services/s3.py`가 `STORAGE=local`이면 로컬 디스크, `s3`이면 AWS. 주요 데이터 경로(`sessions/{sid}/versions/vN/…`, `derived/…`, `judge/…`, `models/{modelId}/`, `work/…`, `llmcache/…`) — 3~5, 6~8 설계 문서 1절 기준
5. API 표: 라우터 파일별 섹션, 각 행 = Method · Path · 한 줄 설명. OpenAPI 93 operation 전부. 설명은 함수 이름·docstring·설계 문서에서 확인되는 것만, 불확실하면 설명 칸을 비우지 않고 함수 이름을 적는다
6. 삭제: `routers/crawling.py`, `services/crawling.py`, `services/pinecone_svc.py`, `POST /crawl`, `GET /status/{sid}`, Pinecone 설명, `classified/`·예전 S3 경로 표

## 5. `frontend/PIPELINE.md` 구조

1. 전체 구조: 프런트 `frontend/src/app/pipeline/<단계>/page.tsx`, 상태 `stores/`, API 클라이언트 `lib/`, 백엔드 REST. 외부 서비스는 실제 사용분만(OpenAI·Claude·Codex·Voyage·네이버 오픈 API·네이버 검색광고·YouTube Data·Jev)
2. 단계별 절: 0~8단계 각각 목적 2~3줄, 화면 경로, 백엔드 라우터·패키지, API 경로 접두사, 결과 저장 위치. 근거는 2절 출처
3. 데이터 흐름 요약 다이어그램(텍스트)
4. 공통: 버전(세션 버전·비교 화면), Known Insight 서랍, 챗봇(`/chat`, `/insight-chat`), 검색(`/search`), 긴 작업 워커(`app/work`)
5. 삭제: S3·Pinecone 전제, `KeywordTag.tsx`·`routers/crawling.py`·`services/crawling.py` 참조, 예전 네이버 카페 전용 크롤링 로직

## 6. `frontend/README.md`

10줄 안팎: 개발 서버(`npm ci`, `npm run dev`, `http://localhost:3000`), 검사 명령(lint·test·build), 백엔드 주소 설정(`NEXT_PUBLIC_API_URL`), 단계 설명은 `PIPELINE.md`, 전체 안내는 루트 `README.md` 링크.

## 7. `ops/macmini/README.md`

- `persona1`이 나오는 2곳(현재 51행, 59행)을 "운영 사용자(현재 맥미니는 `tech`)"로 바꾼다. 다른 장비에서도 맞도록 특정 이름에 묶지 않고 현재 값을 괄호로 적는다.
- 그 밖의 절차·명령은 바꾸지 않는다.
- `docs/development/` 과거 로그의 `persona1` 경로는 바꾸지 않는다.

## 8. `CLAUDE.md` (신규, 루트)

AI 코딩 도구가 레포를 열자마자 읽는 작업 규칙. 80줄 안팎.

1. 프로젝트 한 줄 + 상세 문서 링크(README, BACKEND.md, PIPELINE.md, ops README)
2. 작업 방식: 개발 하네스(`harness.config.json`, `claude-only` 모드). 기획(`01-brainstorm.md`) → 제품 승인 → 설계(`02-design.md`) → 설계 승인 → 계획(`03-plan.md`) → 계획 승인 → worktree → Codex 구현 → 리뷰·QA·검증 → UAT 승인. 승인은 사용자가 자기 터미널에서 `decide`로 기록. Claude는 `docs/development/` 밖을 직접 수정하지 않는다. 산출물 위치 `docs/development/<slug>/`
3. 검증 명령: `harness.config.json`의 4개 명령
4. 운영 주의: 이 맥미니가 운영 서버(`~/srv/dcx-agent`, 사용자 `tech`). main 머지 = 운영 배포. main 직접 push 금지, 티켓 하나 = PR 하나, PR 제목에 노션 티켓 ID(`DCX-번호`). 운영 루트·`shared/` 파일을 작업 중에 건드리지 않는다
5. 코드 규칙(설계 문서 원칙에서 확인된 것만): 결정론적인 일은 코드, LLM은 생성·분류만 / 외부 호출은 어댑터 뒤, 테스트는 가짜로 네트워크 없이 / LLM 호출은 `app/llm` 레지스트리 / 비싼 결과는 버전 밖 모듈·캐시
6. 비밀: 키는 `.env`(로컬)·`shared/app.env`(운영)에만. 커밋·노션·PR에 키 값을 적지 않는다

## 9. 검증 방법 (문서 사실 검사)

- **경로 검사**: 6개 문서에서 백틱·링크로 적힌 레포 경로를 뽑아 존재 여부 확인. 의도적으로 "삭제됨" 등으로 언급하는 경로는 없도록 쓴다(없는 경로는 문서에 남기지 않음). 운영 경로(`~/srv/...`, `shared/...`)와 URL은 대상에서 뺀다
- **API 검사**: `app.openapi()`의 (method, path) 집합과 BACKEND.md API 표의 집합이 같음(차집합 양쪽 0)
- **단계 검사**: README·PIPELINE.md의 화면 경로 집합 = `StepBar.tsx` 경로 집합 + `/pipeline/compare`
- **금지어 검사**: 6개 문서에 `Pinecone`, `EC2`(예전 파일 표시 문구 제외), `systemd`(같음), `persona1`이 운영 안내로 남지 않음
- **회귀**: `harness.config.json` 검증 명령 4개 통과(문서만 바뀌므로 기준선과 같아야 함)
- 검사 스크립트는 `docs/development/docs-refresh/` 아래에 두어 결과 로그와 함께 남긴다

## 10. 실패 상태

- 출처에서 확인되지 않는 설명 → 쓰지 않거나 사실(함수 이름·경로)만 적는다
- 검사 불일치 → 해당 문서만 수정 후 재검사(하네스 retry)
- 문서 머지 후 운영 배포: 맥미니 검사 통과 후 배포, 동작 변화 없음. 실패 시 자동 롤백
