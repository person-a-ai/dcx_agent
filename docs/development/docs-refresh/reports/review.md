# docs-refresh 리뷰 (Claude, 읽기 전용)

기준: `02-design.md`, `03-plan.md`의 리뷰 중점 1~5. 대상 HEAD `3ab5685`.

## Task별

- **T1** 검사기: 규칙이 계획과 일치. `ops/env.sh`·`ops/lib.sh`(설치 후 `$APP_ROOT/ops/`, 원본 `ops/macmini/`) 오탐 1건 → Codex 수정(`ops/` 경로는 `ops/macmini/`도 확인). RED 140건이 계획한 범주(exists·api·stages·banned·env·paths)에 모두 분포.
- **T2** `backend/BACKEND.md`: API 행 93개 = OpenAPI 93 operation(검사기 `api` 0건). 패키지 표 20개가 실제 `backend/app/` 디렉터리와 일치. LLM 백엔드 이름·`fnmatchcase` 재정의는 `app/llm/registry.py`와 대조.
- **T3** `frontend/PIPELINE.md`·`frontend/README.md`: 저장 파일명 표본(`keyword_events.jsonl`, `keyword_feedback.md`, `runs.sqlite`, `known_vectors.f16`, `classified/`, `calib.json`, `project_context.md`, `tree`)을 코드에서 확인.
  - **F1(수정됨)**: 프런트 README가 `.env.production`(`/api`)을 "운영 설정"이라 함. 실제 운영 빌드는 `ops/macmini/install.sh` 75행이 `shared/runtime.env`에 쓰는 `https://dcx-api.person-a.ai`. → 출처를 runtime.env로 바로잡음.
- **T4** `README.md`: 단계 10개·채널 9개·환경변수 기본값을 `StepBar.tsx`·`crawl/adapters/`·`config.py`와 대조(리뷰 중점 5). 배포 설명이 `deploy.sh` 74~75행 `ci-mode` 분기와 자동 롤백에 맞음(리뷰 중점 3). `dcxctl` 명령이 ops README와 글자 그대로 같음(리뷰 중점 1).
- **T5** `CLAUDE.md`·ops README: ops README 2줄만 변경(2+/2-). 검증 명령이 `harness.config.json`과 같음.
  - **F2(수정됨)**: 승인 명령 예시의 근거 문구가 OPERATIONS.md 예시 그대로 → `'<승인 근거>'` 자리표시자로 교체, revise/cancel 안내 추가.

## 전체 브랜치

- 허용 파일 외 변경 0 (`git diff --name-only origin/main...HEAD`)
- 상대 링크: 검사기 `paths`가 링크 대상까지 확인(리뷰 중점 4)
- 남은 발견 사항: 없음
