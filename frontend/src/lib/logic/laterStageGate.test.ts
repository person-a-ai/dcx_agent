import { describe, expect, it } from 'vitest';
import { laterStageGate, laterStagesOpen } from './laterStageGate';

describe('laterStageGate', () => {
  it.each([
    [null, {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'no-session'],
    ['s', null, 'no-session'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'open'],
    ['s', {schemaVersion: 2}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {status: 'running'}}, 'needs-prep'],
    ['s', {step: 'clustering'}, 'legacy'],
    ['s', {prep: {derivedRef: ''}}, 'legacy'],
  ] as const)('sid=%j session=%j → %s', (sid, session, expected) => {
    expect(laterStageGate(sid, session as Record<string, unknown> | null)).toBe(expected);
  });
  it('opens later stages only with a derived reference', () => {
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}}})).toBe(true);
    expect(laterStagesOpen({prep: {}})).toBe(false);
    expect(laterStagesOpen(undefined)).toBe(false);
  });
});
