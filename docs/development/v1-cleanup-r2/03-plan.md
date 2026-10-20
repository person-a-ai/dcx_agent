# v1-cleanup-r2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Under the development harness the task is implemented by a fresh Codex worker (`codex:codex-rescue --wait --fresh`, write mode), committed by the Controller, reviewed by a different fresh Codex reviewer, then the whole QA plan is re-run by a fresh Codex browser-QA worker.

- 입력: [01-brainstorm.md](01-brainstorm.md) · [02-design.md](02-design.md) · QA: [QA_PLAN-v1-cleanup-r2.md](QA_PLAN-v1-cleanup-r2.md)

**Goal:** 6~9단계를 전처리가 실제로 끝난(`prep.status === 'done'`) 세션에서만 연다.

**Architecture:** `laterStagesOpen` 한 함수만 바꾼다. 사이드바(`StepBar`)·세 페이지·배너가 모두 이 함수를 거치므로 화면 코드는 그대로다.

**Tech Stack:** Next.js 16 · React 19 · vitest(node 환경).

## Global Constraints

- 1차 실행([../v1-cleanup/03-plan.md](../v1-cleanup/03-plan.md))의 Global Constraints 전부 유지(챗봇 범위 밖, 배너 문구, 잠금 툴팁 `전처리(3단계)를 먼저 완료하세요`).
- 작업 디렉터리: 하네스 `worktree` 명령으로 만든 새 체크아웃 `/Users/yunho/Documents/dcx_agent-v1-cleanup-r2` (브랜치 `chore/v1-cleanup-r2`, `chore/v1-cleanup`의 커밋을 모두 포함). 백엔드 파이썬은 `backend/.venv/bin/python`(새 체크아웃에서 다시 설치).
- 모든 구현 dispatch에 그대로 넣는 문장: "Do not create Git commits. Complete the implementation and verification, then return READY_FOR_COMMIT with the exact changed-file list and a proposed commit message. Repository state transitions are owned by the controller."
- RED는 단언 실패여야 한다. 프론트 빌드는 Codex 샌드박스에서 멈추므로 Controller가 샌드박스 밖에서 돌린다. `tsc --noEmit`의 기존 오류 7개(손대지 않은 테스트 파일)는 늘지 않아야 한다.

공통 검사:

```bash
backend/.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
```

---

### Task 7: 전처리 완료(`status === 'done'`)일 때만 6~9단계 열기

**allowed_files:**
- Modify: `frontend/src/lib/logic/laterStageGate.ts`, `frontend/src/lib/logic/laterStageGate.test.ts`, `frontend/src/lib/logic/completedThrough.test.ts`, `frontend/src/app/pipeline/clustering/page.test.ts`, `frontend/src/app/pipeline/personas/page.test.ts`, `frontend/src/components/persona/insight-route.test.ts`, `frontend/src/components/persona/insight.test.ts`, `frontend/src/components/evidence/evidenceScreen.test.ts`
- 조건부 Modify(새 규칙 때문에 실패할 때만, 세션 데이터에 `status: 'done'`을 더하는 것만): `frontend/src/components/segment/T15.test.ts`, `frontend/src/components/persona/PersonaScreen.test.ts`

**Interfaces:**
- Produces: `laterStagesOpen(session)`은 `prep.derivedRef`가 truthy이고 `prep.status === 'done'`일 때만 true. `laterStageGate`의 반환 타입·순서(no-session → open → needs-prep/legacy)는 그대로.

- [ ] **Step 1: RED 테스트** — `frontend/src/lib/logic/laterStageGate.test.ts`의 `it.each` 표에 아래 행을 더하고, "opens later stages only with a derived reference" 테스트를 바꾼다.

```ts
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'running'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'paused'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'failed'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'interrupted'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'stale'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {status: 'done'}}, 'needs-prep'],
```

기존 행 `['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'open']`(첫 행 포함 'open' 기대 행 모두)은 `prep`에 `status: 'done'`을 더한다.

```ts
  it('opens later stages only with a finished derived preparation', () => {
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}, status: 'done'}})).toBe(true);
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}, status: 'running'}})).toBe(false);
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}, status: 'stale'}})).toBe(false);
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}}})).toBe(false);
    expect(laterStagesOpen({prep: {}})).toBe(false);
    expect(laterStagesOpen(undefined)).toBe(false);
  });
```

`frontend/src/lib/logic/completedThrough.test.ts`에 사이드바 테스트를 더한다.

```ts
it('keeps clustering, evidence, personas and insights locked while preprocessing is running or stale', () => {
  for (const status of ['running', 'stale']) {
    const html = sidebar('start', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status}});
    for (const name of ['클러스터링', '근거 탐색', '페르소나', '인사이트']) {
      const tag = lockedTag(html, name);
      expect(tag![2]).toContain('aria-disabled="true"');
      expect(tag![2]).not.toMatch(/\bhref=/);
    }
  }
});
```

그리고 기존 `'opens every stage once preprocessing is derived'`의 세션을 `{schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}}`로 바꾼다.

- [ ] **Step 2: RED 확인** — Run: `npm --prefix frontend test -- src/lib/logic/laterStageGate.test.ts src/lib/logic/completedThrough.test.ts` · Expected: 새 행·새 테스트가 단언 실패(`expected 'open' to be 'needs-prep'`, `expected true to be false`, aria-disabled 없음).

- [ ] **Step 3: 구현** — `frontend/src/lib/logic/laterStageGate.ts`:

```ts
/** Stages 6–9 need a finished preparation: prep.derivedRef plus prep.status 'done' (same as backend prepDone). */
export function laterStagesOpen(session: Record<string, unknown> | null | undefined): boolean {
  const prep = session?.prep as {derivedRef?: unknown; status?: unknown} | undefined;
  return !!prep?.derivedRef && prep?.status === 'done';
}
```

나머지 파일(`StepBar.tsx`, 세 페이지, `LaterStageBanner.tsx`)은 건드리지 않는다.

- [ ] **Step 4: 기존 테스트의 "열림" 세션 데이터 갱신** — 아래 테스트의 열림 상태 세션에 `status: 'done'`을 더한다(단언은 그대로).
  - `frontend/src/app/pipeline/clustering/page.test.ts`: `state.session.sd={prep:{derivedRef:{prepKey:'p'}}}`(초기값과 `afterEach` 재설정 두 곳) → `{prep:{derivedRef:{prepKey:'p'},status:'done'}}`
  - `frontend/src/app/pipeline/personas/page.test.ts`: 열림 케이스 세션
  - `frontend/src/components/persona/insight-route.test.ts`: `state.sd.prep.derivedRef='derived'` 케이스에 `state.sd.prep.status='done'`
  - `frontend/src/components/persona/insight.test.ts`: StepBar 세션 `{prep:{derivedRef:{prepKey:'p'}},…}` → `status:'done'` 추가
  - `frontend/src/components/evidence/evidenceScreen.test.ts` 85~86행 StepBar 세션: 열림을 기대하는 쪽에 `status:'done'` 추가
  - 조건부: `T15.test.ts`, `PersonaScreen.test.ts`가 새 규칙 때문에 실패하면 같은 방식으로만 고친다.

- [ ] **Step 5: GREEN** — Run: `npm --prefix frontend test` (모두 통과), `npm --prefix frontend run lint`, `npx --prefix frontend tsc --noEmit -p frontend/tsconfig.json`(기존 7개 외 새 오류 0).

- [ ] **Step 6:** 백엔드 확인(변경 없음): `backend/.venv/bin/python -m pytest backend/tests/test_v1_boundary.py -q -p no:cacheprovider` → READY_FOR_COMMIT. 제안 커밋 메시지: `fix(pipeline): 전처리가 끝난 세션에서만 6~9단계를 연다`

## 되돌리기

`git revert <T7 commit>` 한 번. 데이터 변경 없음.

## 엔지니어링 리뷰 메모 (plan-eng-review 축약)

- 범위: 함수 1개 + 테스트. 새 경로·클래스 없음.
- 실패 모드: 전처리가 끝났는데 `status`가 아직 `running`으로 남은 세션 → 잠김. 백엔드 `GET /prep/{sid}/status`가 상태가 바뀌면 세션에 저장하고(`routers/prep.py:125`), 전처리 화면이 완료 시 세션을 다시 읽는다. 사용자가 전처리 화면을 거치지 않은 채 완료된 경우는 다음 상태 조회나 새로고침에서 풀린다(조용하지만 데이터 손상 없음). QA-EDGE-002가 실제 흐름을 확인한다.
- 회귀: 1차에서 PASS한 14개 + 바로잡은 3개 + 기존 F-01·F-04 시나리오를 다시 돈다.
