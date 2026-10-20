export type LaterStageGate = 'no-session' | 'legacy' | 'needs-prep' | 'open';

export const LATER_STAGE_LOCK_TITLE = '전처리(3단계)를 먼저 완료하세요';

/** Stages 6–9 need a derived preprocessing result (prep.derivedRef). */
export function laterStagesOpen(session: Record<string, unknown> | null | undefined): boolean {
  return !!(session?.prep as {derivedRef?: unknown} | undefined)?.derivedRef;
}

export function laterStageGate(sid: string | null | undefined, session: Record<string, unknown> | null | undefined): LaterStageGate {
  if (!sid || !session) return 'no-session';
  if (laterStagesOpen(session)) return 'open';
  // Same rule as backend store.is_legacy: old sessions have no schemaVersion key.
  return 'schemaVersion' in session ? 'needs-prep' : 'legacy';
}
