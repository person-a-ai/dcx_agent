# 프런트엔드 개발

이 디렉터리에서 `npm ci`로 의존성을 설치한다.
`npm run dev`로 개발 서버를 시작하고 http://localhost:3000 에 접속한다.
백엔드 주소는 `NEXT_PUBLIC_API_URL`로 설정한다(예: `http://localhost:8000`).
`src/lib/api.ts`는 이 값과 API 경로를 이어 붙이며, 미설정 시 같은 출처로 요청한다.
운영(맥미니) 빌드는 설치기가 작성한 `shared/runtime.env`의 `NEXT_PUBLIC_API_URL`을 사용한다(현재 `https://dcx-api.person-a.ai`; [운영 안내](../ops/macmini/README.md)).
별도 `NEXT_PUBLIC_API_URL` 설정 없이 `npm run build`를 실행하면 `.env.production`의 `/api`를 사용한다.
검사 명령은 `npm run lint`, `npm test`, `npm run build`다.
단계별 화면·API·저장 구조는 [PIPELINE.md](PIPELINE.md)를 참고한다.
전체 설치·백엔드 실행 안내는 [루트 README](../README.md)를 참고한다.
