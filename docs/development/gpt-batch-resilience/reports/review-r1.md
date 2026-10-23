# 브랜치 리뷰 1차 (804f84e..83bc051)

리뷰어: Main Claude(gstack `review`, 읽기 전용) + Codex 읽기 전용 리뷰(codex:codex-rescue a58317cc851f0696b). 수정은 하지 않음.

## 발견
### F1 — P2 (confidence 9/10) `backend/app/label/judge.py:197` 실패 묶음이 곧바로 재임대되어 다른 묶음이 처리되지 못한 채 정지
- 근거: `votes.py` `lease()` — `ORDER BY priority, attempts, doc_id`. 성공 전(evidence 0) 실패 글은 `release_docs`로 attempts 그대로 임대만 풀림 → 다음 `lease()`가 같은 글을 다시 고름.
- 재현: concurrency=1, 묶음 여러 개, 정렬상 첫 묶음만 항상 백엔드 실패 → 같은 묶음 5회 반복 → 정상 묶음 0건 처리한 채 `BREAKER_MESSAGE` 정지. concurrency>1이어도 첫 파동의 모든 슬롯이 성공 전에 실패하면 같음.
- 영향: AC4(단발 실패는 건너뛰고 판정 계속) 위반. R2(횟수 미소진)는 유지됨. 운영 README가 한도 시 동시 수를 낮추라고 안내하므로 concurrency 1~2는 실제 경로.
- 테스트 공백: `test_isolated_failures_do_not_pause`는 첫 묶음이 3번째 호출에 성공해 잡지 못함.
- 수정 방향: `release_docs`로 풀린 글은 같은 우선순위·시도 횟수의 아직 시도하지 않은 글 뒤로 재선택(스키마 변경 없이). 회귀 테스트: concurrency 1, 첫 묶음 영구 실패 + 나머지 정상 → 첫 정지 전에 나머지 묶음 done.

### F2 — P2 (confidence 9/10) `frontend/src/components/label/LabelerProgress.tsx:15` 일부 정지 상태에서 판정 실패 줄이 사라짐
- 근거: 표시 조건 `['running','paused'].includes(progress.state)`; 같은 파일의 `stopped`는 `paused·failed·interrupted·cancelled`.
- 재현: reviewQueue true, bad 12, state `interrupted`(또는 failed·cancelled) → "판정이 멈췄습니다."만 보이고 실패 건수 없음.
- 영향: 계획 전역 제약 "진행 중·정지" · 설계 "대기·완료 제외"와 불일치.
- 수정 방향: 조건을 `progress.state === 'running' || stopped`로, 세 상태 매개변수 테스트 추가.

## 확인한 항목(문제 없음)
- 연속 카운터·evidence·failed_at은 메인 스레드 `collect`에서만 갱신. `future.exception()`은 완료된 future에만 호출.
- 사용량 한도가 용량 재시도·차단기보다 우선.
- `.part` 격리·채택은 워커 락·로그 안, 종료 코드 0 확인 후에만 채택.
- 설정 하한 검증·빈 값 기본값 명세대로. 용량 재시도 대기(기본 15~21초)는 설계 허용 범위(≤33초).

판정: FAIL → `retry`로 구현 단계 복귀, F1·F2를 Codex TDD 수정에 위임.
