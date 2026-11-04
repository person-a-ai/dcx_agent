# 브랜치 전체 리뷰 (fc4a75c..a807c12) — PASS

실행: backend/tests/label + backend/tests/model 428 passed(전체 스위트는 미실행), 프런트 test 1063 passed, lint 통과, build 통과.

## 교차 확인
- config → jev.py(get_jev_client, jev_available) → judge.py(jev_client_args, context_key, estimate) → monitor.py(같은 인자) → overview.py(crossLabeler) → types.ts → labelerMode.ts → Overview/KappaTable/Queue/QueueCard 연결이 일관됨. Jev 백엔드일 때 context_key identity 문자열, 비용 문구, 열 제목은 기존과 동일.
- 결정된 deviation 4건 모두 타당: refused는 mark_bad(재시도 없음, pending이 아니면 no-op인 run_id 가드 유지), `JevClient(*jev_client_args())`는 monkeypatch 호환, .env.example 제외는 사용자 결정(PR 전 별도 커밋 필요), 설정 위치는 range 제약.
- 오류 메시지는 고정 문구, 본문·키 미포함. 거절 검사가 길이·형식 검사보다 먼저.

## 발견 (모두 비차단)
1. minor — overview.py `_estimate` lru_cache 키가 backend만 포함. 같은 프로세스에서 DECISIONS_MODEL/키 수가 바뀌면 오래된 추정이 나올 수 있음(설정은 보통 재시작으로 바뀌므로 영향 낮음).
2. minor/info — `estimate` 토큰이 JSON 길이/4라 실측 대비 약 3.5배 과소(알려진 항목). 비용 문구가 "약 $"로 표시되므로 하한값임을 README나 후속 작업에 기록 권장.
3. info — `.env.example`에 DECISIONS_* 4줄이 아직 없음. PR 전 별도 커밋 필수.
