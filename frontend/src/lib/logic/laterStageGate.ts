export type LaterStageGate = 'no-session' | 'legacy' | 'needs-prep' | 'open';

export const LATER_STAGE_LOCK_TITLE = '전처리(3단계)를 먼저 완료하세요';

/** Stages 6–9 need a finished preparation: prep.derivedRef plus prep.status 'done' (same as backend prepDone). */
export function laterStagesOpen(session: Record<string, unknown> | null | undefined): boolean {
  const prep = session?.prep as {derivedRef?: unknown; status?: unknown} | undefined;
  return !!prep?.derivedRef && prep?.status === 'done';
}

export function laterStageGate(sid: string | null | undefined, session: Record<string, unknown> | null | undefined): LaterStageGate {
  if (!sid || !session) return 'no-session';
  if (laterStagesOpen(session)) return 'open';
  // Same rule as backend store.is_legacy: old sessions have no schemaVersion key.
  return 'schemaVersion' in session ? 'needs-prep' : 'legacy';
}
