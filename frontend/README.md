# 프런트엔드 개발

이 디렉터리에서 `npm ci`로 의존성을 설치한다.
`npm run dev`로 개발 서버를 시작하고 http://localhost:3000 에 접속한다.
백엔드 주소는 `NEXT_PUBLIC_API_URL`로 설정한다(예: `http://localhost:8000`).
`src/lib/api.ts`는 이 값과 API 경로를 이어 붙이며, 미설정 시 같은 출처로 요청한다.
운영 설정 `.env.production`의 값은 `NEXT_PUBLIC_API_URL=/api`다.
검사 명령은 `npm run lint`, `npm test`, `npm run build`다.
단계별 화면·API·저장 구조는 [PIPELINE.md](PIPELINE.md)를 참고한다.
전체 설치·백엔드 실행 안내는 [루트 README](../README.md)를 참고한다.
