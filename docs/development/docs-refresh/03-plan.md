# docs-refresh 구현·QA 계획

> **실행 방식:** 개발 하네스 규칙. 각 Task는 `codex:codex-rescue`(`--wait --fresh`, 쓰기 가능)로 Codex에 위임하고, Claude는 결과 diff·검사 출력만 확인한다. 체크박스(`- [ ]`)로 진행을 기록한다.

**목표:** 안내 문서 6개(README·BACKEND.md·PIPELINE.md·frontend/README.md·ops/macmini/README.md·CLAUDE.md)를 최신 main 코드와 운영 맥미니 사실에 맞춘다.

**구조:** 먼저 문서 사실 검사기(`check_docs.py`)를 만들어 현재 문서가 실패함을 확인(RED)하고, 문서를 하나씩 고쳐 해당 검사를 통과시킨다(GREEN). 코드·스크립트·설정은 바꾸지 않는다.

**기술:** Markdown, Python 3.12 표준 라이브러리(검사기), FastAPI `app.openapi()`(API 검사).

**설계:** `docs/development/docs-refresh/02-design.md` (승인 2026-10-23). 사실의 출처는 설계 2절, 문서별 구조는 3~8절, 검사 기준은 9절이다. 구현자는 설계 문서를 함께 읽는다.

## 전역 제약

- 변경 허용 파일: `README.md`, `CLAUDE.md`(신규), `backend/BACKEND.md`, `frontend/PIPELINE.md`, `frontend/README.md`, `ops/macmini/README.md`, `docs/development/docs-refresh/check_docs.py`(신규), `docs/development/docs-refresh/` 아래 보고서·로그. 그 밖의 파일 변경 0
- 설계 2절 출처에서 확인되지 않는 설명은 쓰지 않는다
- 예전 EC2 파일(`scripts/deploy.sh`, `scripts/systemd/`, `nginx/`)은 삭제·수정하지 않고 README 구조 트리에서 "예전 EC2 배포용 — 현재 운영에 쓰지 않음"으로만 표시
- 운영 사용자 표기: "운영 사용자(현재 맥미니는 `tech`)". `docs/development/` 과거 기록의 `persona1`은 수정하지 않음
- 운영 주소: 웹 `https://dcx.person-a.ai`, API `https://dcx-api.person-a.ai`
- 키 값은 어떤 문서에도 적지 않는다(변수 이름만)

## 리뷰 중점 (검사기가 직접 잡지 못하는 것)

1. 복사해 실행할 명령(`dcxctl status`·`rollback`, 로컬 설치, 검사 4개)이 실제 스크립트·`harness.config.json`과 글자 그대로 같은가 → T6에서 리뷰어가 대조
2. 단계 설명 한 줄이 해당 단계 설계 문서 1절과 모순되지 않는가 → T3·T4 리뷰
3. 배포 설명이 `ops/macmini/deploy.sh`의 `ci-mode` 분기(로컬 검사 / GitHub CI)와 자동 롤백을 정확히 말하는가 → T4 리뷰
4. 상대 링크가 GitHub에서 열리는가(문서 위치 기준 상대 경로) → 검사기 `paths`가 링크 대상도 검사
5. 환경변수 기본값이 `config.py` 기본값과 같은가 → 검사기 `env`가 이름 일치만 보므로 리뷰어가 기본값 대조

---

## 작업 준비 (계획 승인 후, Claude)

```bash
cd /Users/tech/code/dcx_agent
git add docs/development/docs-refresh && git commit -m 'docs: docs-refresh 기획·설계·계획 승인'
~/.local/bin/development-harness worktree /Users/tech/code/dcx_agent-docs-refresh docs/refresh-guides-impl
cd /Users/tech/code/dcx_agent-docs-refresh
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-dev.txt -c backend/constraints.txt
npm ci --prefix frontend
```

기준선: 아래 4개 명령이 변경 전에 통과하는지 기록(`logs/baseline.txt`).

```bash
backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
```

---

### Task T1: 문서 사실 검사기

**Files:**
- Create: `docs/development/docs-refresh/check_docs.py`

**Interfaces:**
- Produces: 명령 `backend/.venv/bin/python docs/development/docs-refresh/check_docs.py [--only CHECK ...]` (레포 루트에서 실행). CHECK ∈ `paths`, `api`, `stages`, `banned`, `env`. 실패마다 `FAIL <check> <file>: <detail>` 한 줄, 끝에 `OK` 또는 `FAILED <n>`. 실패 0이면 종료 코드 0, 아니면 1
- 대상 문서 상수 `DOCS = ["README.md", "CLAUDE.md", "backend/BACKEND.md", "frontend/PIPELINE.md", "frontend/README.md", "ops/macmini/README.md"]`. 없는 문서는 `FAIL exists <file>`

검사 규칙:
- `paths`: 각 문서의 백틱 토큰과 Markdown 링크 대상 중 `backend/`, `frontend/`, `ops/`, `docs/`, `scripts/`, `nginx/`, `.github/`, `app/`로 시작하거나 `README.md`·`CLAUDE.md`·`.env.example`·`harness.config.json`인 것. `<`·`{`·`*`가 든 경로는 그 앞 디렉터리까지만 본다. URL·`~/`·`$HOME`·`shared/`로 시작하는 것은 제외. 해석 순서: 레포 루트 → 문서 디렉터리 → `backend/`. 어디에도 없으면 실패
- `api`: `backend/BACKEND.md`에서 `| GET | \`/path\` |` 형태 행(METHOD ∈ GET·POST·PUT·PATCH·DELETE)을 모은 집합과, 서브프로세스로 `STORAGE=local LOCAL_DATA_DIR=<임시 폴더>`를 주고 `backend/`에서 `from app.main import app; app.openapi()["paths"]`로 얻은 (METHOD, path) 집합이 같아야 함. 양쪽 차집합을 각각 실패로 출력
- `stages`: `frontend/src/components/StepBar.tsx`의 `path: "/pipeline/..."` 집합 ∪ {`/pipeline/compare`} 와, `README.md`·`frontend/PIPELINE.md` 각각에 나오는 `/pipeline/<이름>` 집합이 같아야 함
- `banned`: 대상 문서에 `Pinecone`, `persona1`, `pinecone_svc`가 있으면 실패. `EC2`·`systemd`·`Nginx`/`nginx/`가 있는 줄은 같은 줄에 `예전`이 없으면 실패
- `env`: `README.md`의 환경변수 표 첫 열 백틱 이름(`/`로 여러 개)이 모두 `backend/app/config.py` `Settings` 필드의 대문자 이름이거나 `JEVMODEL_API_KEY`여야 하고, `.env.example`의 모든 변수 이름이 표에 있어야 함(단, `FIXTURE_CORPUS_PATH`, `ENABLE_FIXTURE_CHANNEL`, `LOW_VOLUME_THRESHOLD`, `GATE_LOW_COUNT`, `GATE_LOW_UNIQUE`, `NAVER_SEARCH_BASE_URL`은 표 대신 "그 밖의 값은 `.env.example`·`config.py` 참고" 문장으로 대체 가능 → 표에 없어도 통과)

- [ ] **Step 1: 검사기 작성** — 위 규칙대로 `check_docs.py` 작성(표준 라이브러리만, API 검사만 앱 import)
- [ ] **Step 2: RED 확인** — `backend/.venv/bin/python docs/development/docs-refresh/check_docs.py > docs/development/docs-refresh/logs/T1-red.txt; echo $?`
  기대: 종료 1. 최소한 `FAIL exists CLAUDE.md`, `api`(예: `/crawl` POST가 코드에 없음, `/label/{sid}/next` 등 문서에 없음), `stages`(README에 `/pipeline/evidence` 없음), `banned`(Pinecone, persona1, EC2)가 출력됨
- [ ] **Step 3: 커밋** — `git add docs/development/docs-refresh/check_docs.py docs/development/docs-refresh/logs/T1-red.txt && git commit -m 'test(docs): 문서 사실 검사기'`

### Task T2: `backend/BACKEND.md`

**Files:** Modify(전체 재작성): `backend/BACKEND.md`
**Interfaces:** Consumes T1 검사기. API 행 형식은 반드시 `| METHOD | \`/path\` | 설명 |`(path 파라미터 이름은 OpenAPI 그대로, 예: `{sid}`, `{item_id}`)

- [ ] **Step 1: RED** — `check_docs.py --only api paths banned` 실패 확인(T1 로그로 갈음 가능)
- [ ] **Step 2: 작성** — 설계 4절 구조(개요, 패키지 표 20개, LLM 공통 층, 저장소·데이터 경로, 라우터별 API 표 93개)
- [ ] **Step 3: GREEN** — `backend/.venv/bin/python docs/development/docs-refresh/check_docs.py --only api paths banned > docs/development/docs-refresh/logs/T2-green.txt` 중 `backend/BACKEND.md` 관련 FAIL 0
- [ ] **Step 4: 커밋** — `docs(backend): BACKEND.md를 현재 패키지·API 93개 기준으로 갱신`

### Task T3: `frontend/PIPELINE.md`, `frontend/README.md`

**Files:** Modify(전체 재작성): `frontend/PIPELINE.md`, `frontend/README.md`
**Interfaces:** Consumes T1. 단계 절 제목에 단계 번호와 화면 경로(`/pipeline/<이름>`) 포함

- [ ] **Step 1: 작성** — 설계 5절(PIPELINE), 6절(frontend README: `npm ci`, `npm run dev`, `http://localhost:3000`, lint·test·build, `NEXT_PUBLIC_API_URL`, 링크)
- [ ] **Step 2: GREEN** — `check_docs.py --only paths stages banned > logs/T3-green.txt` 중 두 파일 관련 FAIL 0
- [ ] **Step 3: 커밋** — `docs(frontend): PIPELINE.md·README를 현재 0~8단계 기준으로 갱신`

### Task T4: `README.md`

**Files:** Modify(전체 재작성): `README.md`
**Interfaces:** Consumes T1. 환경변수 표 첫 열 형식 `| \`NAME\` / \`NAME2\` | 필요할 때 | 설명(기본값) |`

- [ ] **Step 1: 작성** — 설계 3절 8개 섹션. 배포 요약은 `ops/macmini/deploy.sh` 74~75행 `ci-mode` 분기와 README 157행 설명 기준
- [ ] **Step 2: GREEN** — `check_docs.py --only paths stages banned env > logs/T4-green.txt` 중 `README.md` 관련 FAIL 0
- [ ] **Step 3: 커밋** — `docs: README를 맥미니 운영·현재 파이프라인 기준으로 갱신`

### Task T5: `ops/macmini/README.md` 운영 사용자, `CLAUDE.md`

**Files:**
- Modify: `ops/macmini/README.md:51`, `ops/macmini/README.md:59` (`persona1` → "운영 사용자(현재 맥미니는 `tech`)", 문장 자연스럽게)
- Create: `CLAUDE.md`

**Interfaces:** Consumes T1.

- [ ] **Step 1: ops README 두 줄 수정** — 다른 줄 변경 0 (`git diff --stat ops/macmini/README.md` → 2줄 변경)
- [ ] **Step 2: CLAUDE.md 작성** — 설계 8절 6개 항목, 80줄 안팎. 검증 명령은 `harness.config.json`과 글자 그대로
- [ ] **Step 3: GREEN** — `check_docs.py --only exists paths banned > logs/T5-green.txt` 중 두 파일 관련 FAIL 0
- [ ] **Step 4: 커밋** — `docs: CLAUDE.md 추가, 운영 사용자 표기를 현재 맥미니(tech)로`

### Task T6: 전체 검증

- [ ] **Step 1:** `backend/.venv/bin/python docs/development/docs-refresh/check_docs.py > logs/T6-all.txt; echo $?` → `OK`, 종료 0
- [ ] **Step 2:** 기준선 4개 명령 재실행 → 모두 통과, 결과를 `logs/T6-regression.txt`
- [ ] **Step 3:** 허용 파일 외 변경 0 확인: `git diff --name-only origin/main...HEAD` 결과가 전역 제약 목록의 부분집합
- [ ] **Step 4: 커밋** — 로그 커밋

---

## QA 계획

UI 변경이 없으므로 브라우저 QA 대상이 없다(테스트 URL 없음). 대신:

| 시나리오 | 방법 | 수용 기준 연결 |
|---|---|---|
| 문서 경로가 모두 실재 | `check_docs.py --only paths` | 기획 AC-1 |
| API 표 = 실제 라우트 | `check_docs.py --only api` | AC-2 |
| 단계 = StepBar + compare | `check_docs.py --only stages` | AC-3 |
| EC2·Pinecone·persona1 운영 안내 없음 | `check_docs.py --only banned` | AC-4, AC-5 |
| 환경변수 이름 일치 | `check_docs.py --only env` + 리뷰어 기본값 대조 | AC-6 |
| CLAUDE.md 내용 | 리뷰어가 설계 8절 6항목 대조 | AC-7 |
| 동작 회귀 없음 | 기준선 4개 명령 + 허용 파일 외 변경 0 | AC-8 |
| GitHub 렌더링 | PR 화면에서 표·링크 확인(리뷰 단계) | 리뷰 중점 4 |

## 되돌리기

문서만 바뀌므로 PR을 revert하면 된다(`git revert <merge commit>` 후 PR). 머지 후 운영 배포는 동작 변화가 없고, 배포 검사 실패 시 맥미니가 자동 롤백한다.
