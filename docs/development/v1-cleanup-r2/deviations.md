# v1-cleanup-r2 · 승인 계획과 다르게 진행한 것

승인된 r2 문서(01·02·03·QA)는 하네스가 해시로 고정하므로 고치지 않고 여기에 남긴다. 1차 실행의 이탈은 [../v1-cleanup/deviations.md](../v1-cleanup/deviations.md)(DV-1~DV-4).

| # | 날짜 | 무엇 | 왜 | 결정 |
|---|---|---|---|---|
| DV-5 | 2026-10-20 | T7 범위에 `frontend/src/app/pipeline/clustering/page.tsx`, `frontend/src/app/pipeline/personas/page.tsx`를 더해, 두 페이지도 인사이트 페이지·사이드바처럼 **보고 있는 버전의 세션(`view.session ?? sd`)** 으로 게이트를 판단하게 한다 | r2 브랜치 전체 독립 리뷰 FAIL(P2): 두 페이지만 `store.sd`(최신 버전)를 봐서, 3단계 재시작(v2 `stale`) 후 완료된 v1을 고르면 사이드바는 열리는데 페이지는 배너를 보인다. 02-design(r2) "읽기 전용으로 예전 버전을 볼 때는 그 버전의 `prep.status`를 따른다"를 구현하는 수정이며, 03-plan의 "세 페이지는 바뀌지 않는다"가 틀렸다 | Controller(승인된 설계에 맞추는 수정, 리뷰 지적 반영) |
