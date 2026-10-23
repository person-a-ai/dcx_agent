# 브랜치 리뷰 2차 (804f84e..11ec883)

리뷰어: Codex 읽기 전용 리뷰(codex:codex-rescue a8b0ea133496e56bd) + Main Claude(seed·스키마 `at` 초기값 직접 확인: `votes.py:28-31` `at REAL` 기본 NULL, `seed` INSERT OR IGNORE는 `at` 미설정).

결과: **발견 없음.** 1차 F1·F2 해소 확인.
- F1: `votes.py:96` `ORDER BY priority, attempts, (at IS NOT NULL), doc_id` — 미시도 글이 release_docs된 글보다 먼저. concurrency 1·첫 파동 전부 실패 모두 미시도 묶음이 다음 후보. 성공 전에 연속 기준 도달 시 정지는 차단기 의도대로.
- F2: `LabelerProgress.tsx:15` running + 네 정지 상태 포함, 테스트 고정.

남은 위험(결함 아님, UAT에 제시):
- R1-a 증거(evidence)는 워커 메모리 상태라 프로세스 재시작(배포 등) 뒤에는 0부터. 꼬리에 남은 영구 실패 글은 같은 워커에서 재개할 때만 1회씩 세어져 검수 큐로 감. 재시작이 반복되면 그 글은 pending으로 남고 연속 실패 정지만 반복될 수 있음(R2 승인 설계의 범위; 사용자는 정지 사유와 "이어서 진행"으로 대응 가능).
- R1-b lease 정렬 변경은 공용 VoteCache를 쓰는 Jev·API 경로의 재임대 순서에도 적용(정지·횟수 정책은 불변). 일시정지 후 재개 시 이전에 임대된 글이 같은 priority·attempts의 미시도 글 뒤로 감.
- R1-c 용량 재시도 대기(기본 합계 15~21초) 동안 정지 요청 미확인(설계 허용 ≤33초).
