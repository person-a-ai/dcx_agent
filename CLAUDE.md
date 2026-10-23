# DCX Agent 작업 안내

DCX 2.0은 담론을 수집·분석해 페르소나와 인사이트를 만드는 프로젝트입니다.

상세 설명은 다음 문서에서 확인합니다.

- [프로젝트 안내](README.md)
- [백엔드 구조와 API](backend/BACKEND.md)
- [프런트 파이프라인](frontend/PIPELINE.md)
- [맥미니 운영 안내](ops/macmini/README.md)
- [개발 산출물](docs/development/)

## 작업 방식

개발 하네스 설정은 `harness.config.json`이며 모드는 `claude-only`입니다.
산출물은 `docs/development/` 아래 기능별 디렉터리에 둡니다.
산출물 위치 형식은 docs/development/<slug>/입니다.

작업 순서는 다음과 같습니다.

1. 기획: 01-brainstorm.md 작성
2. 사용자 제품 승인
3. 설계: 02-design.md 작성
4. 사용자 설계 승인
5. 계획: 03-plan.md에 구현 계획과 QA 계획 작성
6. 사용자 계획 승인
7. 승인 자료 커밋 후 하네스 worktree 생성
8. Codex 구현: TDD로 실패 → 통과 → 리팩터링
9. 독립 리뷰 · 브라우저 QA · 검증
10. 사용자 UAT 승인

승인은 사용자가 문서를 검토하고 자신의 터미널에서 직접 기록합니다.
제품 승인 명령 형식은 다음과 같으며, 마지막 인수는 실제 승인 근거로 바꿉니다.

```bash
~/.local/bin/development-harness decide approve '<승인 근거>'
```

설계·계획·UAT 승인 게이트에도 같은 명령 형식을 사용하며, 다른 선택지는 수정 요청 `revise`와 취소 `cancel`입니다.

Claude는 기획·관리·리뷰를 맡습니다.
Claude는 `docs/development/` 밖 파일을 직접 수정하지 않고 Codex에 위임합니다.
구현·테스트·수정은 `codex:codex-rescue`에 `--wait --fresh`로 위임합니다.
승인된 worktree, 담당 파일, 수용 기준, 검증 명령을 함께 전달합니다.
리뷰·QA에서 수정이 필요하면 Codex 구현으로 돌아가 다시 검증합니다.
Merge·push·PR 생성은 사용자가 명시적으로 요청할 때만 합니다.

## 검증 명령

`harness.config.json`의 명령을 레포 루트에서 실행합니다.

```bash
backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend run build
npm --prefix frontend test
```

## 운영 주의

이 맥미니는 운영 서버입니다. 운영 루트는 `~/srv/dcx-agent`, 운영 사용자는 `tech`입니다.
main에 머지하면 자동 배포됩니다. 배포 잡은 120초마다 변경을 확인합니다.
`shared/ci-mode`가 `local`이면 맥미니가 검사를 직접 실행하고, 그 외에는 GitHub CI를 확인합니다.
검사 통과 후 배포하며, 배포 후 health check가 실패하면 자동 롤백합니다.
동작 근거는 `ops/macmini/deploy.sh`와 [운영 안내](ops/macmini/README.md)입니다.
main 직접 push는 금지합니다. 티켓 하나는 PR 하나로 처리합니다.
PR 제목에는 `DCX-16`처럼 Notion 티켓 ID를 포함합니다.
개발 작업 중 `~/srv/dcx-agent`와 그 안의 `shared/` 파일을 건드리지 않습니다.
운영 상태 확인 명령은 다음과 같습니다.

```bash
APP_ROOT="$HOME/srv/dcx-agent" "$HOME/srv/dcx-agent/ops/dcxctl" status
```

## 코드 원칙

- 판단이 필요 없는 필터·정규화·큐·지표·확률 계산은 결정론적 코드로 처리하고 LLM은 생성·분류를 맡습니다.
- 외부 호출은 어댑터 뒤에 두고, 테스트는 가짜 어댑터로 네트워크 없이 실행합니다.
- LLM 호출은 `backend/app/llm/registry.py`의 `run_task`와 Pydantic 출력 스키마를 사용합니다.
- 비싸거나 오래 걸리는 수집본·벡터·LLM 결과는 버전 밖 모듈·캐시로 두고 버전은 이를 참조합니다.
- 튜닝값은 `backend/app/segment/params.py`, `backend/app/evidence/params.py`, `backend/app/persona/params.py`에 모으고 결과 JSON에도 사용값을 남깁니다.

근거: [0~2단계 원칙](docs/development/dcx2-stage0-2/02-design.md), [3~5단계 원칙](docs/development/dcx2-stage3-5/02-design.md), [6~8단계 원칙](docs/development/dcx2-stage6-8/02-design.md).

## 비밀

키는 로컬 `.env`와 운영 `~/srv/dcx-agent/shared/app.env`에만 둡니다.
키 값을 커밋·Notion·PR에 적지 않습니다.
