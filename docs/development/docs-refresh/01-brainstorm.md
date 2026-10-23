# docs-refresh — 01 기획

## 요청과 이해

- 사용자 요청(2026-10-23): "README, CLAUDE.md 파일들 맞아? 최신화가 안 되어 있는 것 같다" → "이 맥미니는 tech여서 그것도 바뀌어야 해. 문서 PR 만들어줘."
- 목적: 개발자가 아닌 팀원과 AI 코딩 도구가 레포 안내 문서만 보고 **현재 코드와 현재 운영(맥미니)** 을 정확히 이해하게 한다. 노션 DCX 2.0의 운영 카드가 이 문서들을 링크한다.
- 성공 기준: 안내 문서에 적힌 경로·API·명령·계정·배포 방식이 최신 main(`fa71e31`)과 운영 맥미니에서 사실로 확인된다.
- 가정(사용자 확인 필요): 코드·스크립트 동작은 바꾸지 않는다. 예전 EC2용 파일(`scripts/deploy.sh`, `scripts/systemd/`, `nginx/`)은 지우지 않고 "현재 운영에 쓰지 않음"으로 표시만 한다.

## 현재 문제 (근거: 최신 main 대조, 2026-10-23)

| 문서 | 마지막 수정 | 확인된 불일치 |
|---|---|---|
| `README.md` | 10-04 | EC2·systemd·Nginx 배포 가이드 전체가 현재 운영(맥미니 launchd, Cloudflare 터널, 8400/3400)과 다름. "8단계"라고 하지만 화면은 10개(0~8단계, 8단계가 페르소나·인사이트 두 화면). 단계 설명이 예전 방식(2% 수동 라벨링, 3모델 앙상블, Claude 키워드). 크롤링 채널이 네이버 카페뿐(실제 어댑터 9개). 폴더 구조가 `backend/app` 20개 패키지 중 6개만 표기. `S3_BUCKET` "필수" 표기(기본 `STORAGE=local`), `SEARCHAD_*`·`YOUTUBE_API_KEY`·`LLM_BACKEND`·`AUTHOR_SALT_PATH` 등 누락 |
| `backend/BACKEND.md` | 10-20 | 없는 파일 설명: `routers/crawling.py`, `services/crawling.py`, `services/pinecone_svc.py`. 없는 API: `POST /crawl`, `GET /status/{sid}`(실제 `/crawl/{sid}/…` 10개). Pinecone RAG 설명(실제 로컬 벡터 `known/filter.py`). 등록 router 14개 중 `integrations`·`context`·`known` 누락. 실제 API 93개 중 대부분 미기재 |
| `frontend/PIPELINE.md` | 10-20 | 외부 서비스에 S3·Pinecone. 없는 파일 `KeywordTag.tsx`, `routers/crawling.py`, `services/crawling.py`. 크롤링이 예전 네이버 카페 전용 로직 |
| `frontend/README.md` | 03-19 | create-next-app 기본 문구 그대로 |
| `ops/macmini/README.md` | 최신 | 운영 계정을 `persona1`로 안내하나 이 맥미니에 해당 사용자가 없음. 실제 자동 로그인·운영 사용자는 `tech`, LaunchAgent(`~/Library/LaunchAgents/ai.person-a.dcx-agent.*`) 모드 |
| `CLAUDE.md` | 없음 | AI 도구용 작업 안내 파일이 레포에 없음 |

운영 사실(맥미니에서 읽기 전용 확인): `dcxctl status` 정상, current = `fa71e31`, `shared/ci-mode` = `local`, 배포 로그에 `ops_outdated: true`.

## 대안

| 안 | 내용 | 장점 | 단점 |
|---|---|---|---|
| A (추천) | 기존 문서 구조는 유지하고 내용만 사실에 맞게 갱신. `CLAUDE.md` 신설, `frontend/README.md`는 짧은 안내로 교체. API 목록은 실제 등록 라우트에서 뽑아 정리 | 링크·습관 유지, 범위 명확, 리뷰 쉬움 | 문서가 다시 낡을 수 있음 |
| B | A + 라우트 목록 자동 생성 스크립트·CI 검사 추가 | 재발 방지 | 코드·CI 변경이 생겨 범위가 커짐 |
| C | 상세 문서(BACKEND.md·PIPELINE.md)를 없애고 README + CLAUDE.md로 통합 | 관리 대상 감소 | 노션·기존 링크가 깨지고 정보 손실 |

추천: **A**. 재발 방지(B)는 별도 작업으로 남긴다.

## 수용 기준

1. README·BACKEND.md·PIPELINE.md·frontend/README.md·CLAUDE.md에 적힌 모든 레포 경로가 실제로 존재한다(스크립트로 확인).
2. BACKEND.md의 API 표가 실제 등록 라우트(OpenAPI 93개 operation)와 일치한다(누락·없는 경로 0).
3. 단계 목록이 `frontend/src/components/StepBar.tsx`의 10개 화면, 0~8단계 번호와 일치한다.
4. 배포 설명이 `ops/macmini/deploy.sh`의 동작(120초 폴링, `ci-mode=local`이면 맥미니 검사, 실패 시 자동 롤백)과 일치하고, EC2·systemd·Nginx를 현재 운영 방법으로 안내하지 않는다.
5. 운영 계정 안내가 `tech`(현재 맥미니)로 바뀐다. 과거 실행 기록(`docs/development/*/logs`, `build.json`)의 `persona1` 경로는 기록이므로 바꾸지 않는다.
6. 환경변수 표가 `backend/app/config.py`·`.env.example`과 모순되지 않는다(S3는 `STORAGE=s3`일 때만 필요).
7. `CLAUDE.md`가 하네스 작업 규칙(기획→승인→Codex 구현→리뷰·QA·검증→UAT), 검증 명령(`harness.config.json`), 운영 주의(main 직접 push 금지, 운영 서버가 이 맥미니), 키를 커밋·노션에 적지 않는 규칙을 담는다.
8. 코드·테스트·스크립트·설정 파일 변경 0. 기존 검증 명령이 그대로 통과한다.

## 제외 범위

- 코드·스크립트 동작 변경, 예전 EC2 파일 삭제, `dcxctl restart` 추가, 라우트 문서 자동 생성(B안)
- 운영 맥미니의 재설치(`ops_outdated`)·설정 변경 — 문서에 안내만 남김
- GitHub 브랜치 보호 설정, 노션 페이지 추가 수정
- `docs/development/` 과거 기록 수정

## 위험

- 단계 설명을 코드만 보고 요약하면 의도와 어긋날 수 있음 → 단계별 설계 문서(`docs/development/dcx2-stage*`)를 근거로 쓰고, 확인 못 한 내용은 쓰지 않는다.
- `ops/macmini/README.md`는 다른 맥미니(`persona1`) 시절 절차도 담고 있음 → 계정 이름을 "운영 사용자(현재 `tech`)"로 일반화해 다른 장비에서도 맞게 쓴다.
- 문서 PR이 머지되면 운영 배포가 한 번 돈다(문서만 바뀌어도 새 커밋) → 로컬 검사 통과 후 배포되며 동작 변화는 없음.

## 결정이 필요한 점

1. 대안 A로 진행할지
2. 예전 EC2 파일은 유지하고 표시만 할지(추천), 이번에 삭제할지
