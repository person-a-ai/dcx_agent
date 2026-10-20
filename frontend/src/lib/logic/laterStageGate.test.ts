import { describe, expect, it } from 'vitest';
import { laterStageGate, laterStagesOpen } from './laterStageGate';

describe('laterStageGate', () => {
  it.each([
    [null, {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}}, 'no-session'],
    ['s', null, 'no-session'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}}, 'open'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'running'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'paused'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'failed'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'interrupted'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'stale'}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}}}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {status: 'done'}}, 'needs-prep'],
    ['s', {schemaVersion: 2}, 'needs-prep'],
    ['s', {schemaVersion: 2, prep: {status: 'running'}}, 'needs-prep'],
    ['s', {step: 'clustering'}, 'legacy'],
    ['s', {prep: {derivedRef: ''}}, 'legacy'],
  ] as const)('sid=%j session=%j → %s', (sid, session, expected) => {
    expect(laterStageGate(sid, session as Record<string, unknown> | null)).toBe(expected);
  });
  it('opens later stages only with a finished derived preparation', () => {
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}, status: 'done'}})).toBe(true);
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}, status: 'running'}})).toBe(false);
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}, status: 'stale'}})).toBe(false);
    expect(laterStagesOpen({prep: {derivedRef: {prepKey: 'p'}}})).toBe(false);
    expect(laterStagesOpen({prep: {}})).toBe(false);
    expect(laterStagesOpen(undefined)).toBe(false);
  });
});
