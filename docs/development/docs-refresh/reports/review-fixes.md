# 리뷰 수정 보고서

## F1 — 프런트엔드 운영 API 주소

- 변경 전: 운영 설정 `.env.production`의 값은 `NEXT_PUBLIC_API_URL=/api`다.
- 변경 후:
  ```markdown
  운영(맥미니) 빌드는 설치기가 작성한 `shared/runtime.env`의 `NEXT_PUBLIC_API_URL`을 사용한다(현재 `https://dcx-api.person-a.ai`; [운영 안내](../ops/macmini/README.md)).
  별도 `NEXT_PUBLIC_API_URL` 설정 없이 `npm run build`를 실행하면 `.env.production`의 `/api`를 사용한다.
  ```
- 근거: `ops/macmini/install.sh`와 `ops/macmini/README.md`의 runtime.env 및 공개 API 주소 설정 설명을 확인했다. 프런트엔드 README는 11줄로 유지했다.

## F2 — 승인 명령 예시

- 변경 전: `~/.local/bin/development-harness decide approve '대화 12번 메시지에서 제품 기획 승인'`
- 변경 후: `~/.local/bin/development-harness decide approve '<승인 근거>'`
- 추가: 설계·계획·UAT 승인 게이트에도 같은 명령 형식을 사용하며, 다른 선택지는 수정 요청 `revise`와 취소 `cancel`입니다.
- 근거: `/Users/tech/.claude/skills/development-harness-native/OPERATIONS.md`를 읽기 전용으로 확인했다. 제품·UAT의 `decide approve` 예시, 설계·계획 승인 절차, `decide revise`와 `decide cancel` 예시에 부합한다.

## 검증

- 명령: `backend/.venv/bin/python docs/development/docs-refresh/check_docs.py > docs/development/docs-refresh/logs/T6-all.txt; echo $?`
- 종료 코드: 0
- 로그 마지막 줄: `OK`
