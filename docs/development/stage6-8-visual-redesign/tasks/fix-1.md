# RV1–RV6 수정 결과

완료: RV1–RV6. 지정된 프론트엔드 파일과 이 보고서만 수정했다. backend 변경, git 쓰기, 신규 디자인 토큰 추가 없음.

## RV별 TDD 기록

각 RV에서 테스트를 먼저 추가/수정하고 아래 명령으로 RED를 확인한 뒤 구현을 수정하고 같은 명령으로 GREEN을 확인했다.

```sh
npm --prefix frontend test -- components PersonaScreen finalReview
```

이 명령은 Vitest 필터의 `components` 때문에 persona 외의 기존 component 테스트도 포함한다. 매번 38개 테스트 파일을 실행했다.

| RV | 수정 및 검증 내용 | 실제 RED 출력 | 실제 GREEN 출력 |
|---|---|---|---|
| RV1 | pain_point trace는 pain_point.quote와 pain_point.verified 사용. 그 외는 일반 quote 유지. 일반/페인 인용의 검증값이 서로 반대인 두 경우 검사. | `Tests 2 failed / 457 passed (459)`; 일반 인용을 표시해 `to contain '페인 인용'` 실패 | `Test Files 38 passed (38)`, `Tests 459 passed (459)` |
| RV2 | 강조 점과 focusPersonaId의 모든 점에 라벨 표시. 화면 좌표와 jitter를 반영해 가까운 라벨을 수직으로 이동. Context ID 정렬로 결정적 배치. 기존 0개 기대 수정, 가까운 두 점의 서로 다른 y 및 반복 결과 검사. | `Tests 2 failed / 458 passed (460)`; 라벨 기대 1/2개, 실제 0개 | `Test Files 38 passed (38)`, `Tests 460 passed (460)` |
| RV3 | selectedContext와 hover highlighted 분리. 지도/행 클릭은 전체 맵을 유지하며 오른쪽 상세 선택 저장. 상세의 카드 열기로 카드 진입. 카드 지도 클릭은 열 강조. 실제 지도 점 클릭, hover/leave 후 상세 유지, 행 선택, 카드 열기 검사. | `Tests 1 failed / 460 passed (461)`; 클릭 후 전체 맵 aria-pressed가 false | `Test Files 38 passed (38)`, `Tests 461 passed (461)` |
| RV4 | 근거 수는 Context metrics.doc_count 사용, 누락 시 근거 부족. trace가 E1 하나여도 doc_count=11이면 11 표시. 누락값도 검사. 기존 trace 기반 기대 fixture를 metrics 기반으로 갱신. | `Tests 2 failed / 461 passed (463)`; 실제 '1', 기대 '11' 및 '근거 부족' | `Test Files 38 passed (38)`, `Tests 463 passed (463)` |
| RV5 | PersonaScreen에서 data.tree 기준 useMemo로 HierarchyTree root 고정. 기존 hook-mocking harness에 의존성 기반 useMemo 모의 구현 추가. 다른 클러스터 수동 펼침 후 지도 highlight로 재렌더하고 펼침과 자식 표시 유지 검사. | `Tests 1 failed / 463 passed (464)`; 수동 확장 aria-expanded가 false로 초기화 | `Test Files 38 passed (38)`, `Tests 464 passed (464)` |
| RV6 | PersonaContextTable 제거, 공용 ContextTable 재사용. 대표 페인포인트 열과 고정 폭/줄바꿈 이름 셀 추가. 행 클릭/키보드 선택 및 카드 버튼 클릭 전파 차단. 관련 테스트를 ContextTable 대상으로 변경. | `Tests 3 failed / 462 passed (465)`; 공용 ContextTable 부재로 table 위치/선택/재사용 테스트 실패 | `Test Files 38 passed (38)`, `Tests 465 passed (465)` |

## 최종 검증

- `npm --prefix frontend test`
  - `Test Files 73 passed (73)`
  - `Tests 828 passed (828)`
- `npm --prefix frontend run lint`
  - `> frontend@0.1.0 lint`, `> eslint`
  - 진단 없이 통과.
- `npx --prefix frontend tsc --noEmit -p frontend`
  - 알려진 오류 2건만 발생:
  - `frontend/src/lib/logic/crawlConfig.test.ts(13,63): error TS2783: 'max_per_keyword' is specified more than once, so this usage will be overwritten.`
  - `frontend/src/lib/logic/crawlConfig.test.ts(25,98): error TS2783: 'max_per_keyword' is specified more than once, so this usage will be overwritten.`

## 보정 및 편차

- RV2 첫 구현 후 가까운 점 테스트가 1건 실패했다. fixture의 첫 점 s=.5와 두 번째 점 s=.40001은 가까운 점이 아니었다. 두 번째를 s=.50001로 바로잡고 동일 명령으로 GREEN을 확인했다.
- RV6 첫 구현 후 기존 카드 버튼 테스트가 이벤트 없이 핸들러를 호출해 stopPropagation에서 실패했다. 실제 이벤트 형태의 mock과 전파 차단 검증을 추가한 뒤 GREEN을 확인했다.
- next build는 실행하지 않았다. 요청된 최종 test/lint/tsc 검증을 수행했다. 브라우저 시각 검증은 수행하지 않았다.
- 기존 build.json 변경 및 review-findings.md/review.json 파일은 수정하지 않았다.
