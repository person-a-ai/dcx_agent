# v1-cleanup-r2 · 02 설계

- 작성: 2026-10-20 · 입력: [01-brainstorm.md](01-brainstorm.md), 1차 설계 [../v1-cleanup/02-design.md](../v1-cleanup/02-design.md)(§1 화면은 그대로 유효, 아래 규칙만 바뀜)
- 목업: [mockup/index.html](mockup/index.html) — 1차 목업에 "새 세션 · 전처리 진행 중/실패/3단계 재시작" 상태를 더했다. 실제 앱 CSS(@`4444a50`)를 인라인한 로컬 HTML이고, `/claude-design`을 쓰지 않은 이유는 1차 설계와 같다(원격 접속, 외부 전송, 새 시각 요소 없음).

## 1. 바뀌는 규칙 하나

```ts
// frontend/src/lib/logic/laterStageGate.ts
export function laterStagesOpen(session) {
  const prep = session?.prep as {derivedRef?: unknown; status?: unknown} | undefined;
  return !!prep?.derivedRef && prep?.status === 'done';
}
```

`laterStageGate`, `StepBar`, 세 페이지, `LaterStageBanner`는 이 함수를 그대로 쓰므로 다른 파일은 바뀌지 않는다.

| 세션 상태 | `prep` | 1차 결과 | r2 결과 |
|---|---|---|---|
| 새 세션, 전처리 안 함 | 없음 | 잠김 · 전처리 배너 | 같음 |
| 새 세션, 전처리 진행 중 | `derivedRef` 있음, `status` running/paused | **열림(결함)** | 잠김 · 전처리 배너 |
| 새 세션, 전처리 실패·중단 | `derivedRef` 있음, `status` failed/interrupted | **열림(결함)** | 잠김 · 전처리 배너 |
| 3단계부터 다시 시작한 새 버전 | `derivedRef` 남음, `status` stale | **열림(결함)** | 잠김 · 전처리 배너 |
| 새 세션, 전처리 완료(재사용 포함) | `derivedRef` 있음, `status` done | 열림 | 같음 |
| 옛 세션 | 없음 | 잠김 · 구버전 배너 | 같음 |
| 세션 없음 | — | 잠김 · 프로젝트 선택 배너 | 같음 |

- 기준은 백엔드 완료 표시 `prepDone`(`backend/app/routers/sessions.py:121`, `prep.status == "done"`)과 같다.
- 완료 직후 갱신: 전처리 화면이 `done`을 받으면 `refreshSessionAfterStage()`로 세션을 다시 읽어 store에 넣는다(`components/prep/PrepScreen.tsx:80,118` → `lib/refreshSessionAfterStage.ts`). 사이드바 세션은 `view.session ?? store.sd`이므로 새로고침 없이 열린다.
- 읽기 전용으로 예전 버전을 볼 때는 그 버전의 `prep.status`를 따른다(완료된 버전은 `done`).
- 문구·CSS·모바일 동작은 1차 설계 + DV-3 그대로다.

## 2. 백엔드 · 데이터 · API · 권한

변경 없음.

## 3. 테스트 방침

- `laterStageGate.test.ts`: `status` running/paused/failed/interrupted/stale + `derivedRef` 있음 → `needs-prep`; `done` + `derivedRef` → `open`; `done`인데 `derivedRef` 없음 → `needs-prep`; 옛 세션은 `legacy` 유지.
- `completedThrough.test.ts`(사이드바): `derivedRef`만 있고 `status` running인 세션 → 6~9 잠김, `done` → 모두 열림. 기존 "열림" 테스트의 세션 데이터에 `status: 'done'`을 더한다.
- 세 페이지 테스트의 "열림" 데이터에도 `status: 'done'`을 더한다.
- 브라우저 QA: [QA_PLAN-v1-cleanup-r2.md](QA_PLAN-v1-cleanup-r2.md) 전체.
