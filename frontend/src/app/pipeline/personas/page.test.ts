import { afterEach, describe, expect, it, vi } from 'vitest';
const page = vi.hoisted(() => ({session: {sid: 's', sd: {schemaVersion: 2}} as {sid: string | null; sd: Record<string, unknown> | null}}));
const view = vi.hoisted(() => ({version: 'v1', readonly: false, conflict: false, session: null as Record<string, unknown> | null | undefined}));
vi.mock('@/stores/useSessionStore', () => ({useSessionStore: () => page.session}));
vi.mock('@/components/versions/VersionProvider', () => ({useVersion: () => view}));
vi.mock('@/components/persona/PersonaScreen', () => ({PersonaScreen: () => null}));
vi.mock('@/lib/api', () => { throw new Error('v1 api must not be imported by the personas page'); });
vi.mock('next/navigation', () => ({useRouter: () => ({push: vi.fn()})}));
import { LaterStageBanner } from '@/components/LaterStageBanner';
import { PersonaScreen } from '@/components/persona/PersonaScreen';

describe('personas page gate', () => {
  afterEach(() => {
    view.session = null;
    page.session = {sid: 's', sd: {schemaVersion: 2}};
  });
  it('opens the selected done session when the store session is stale', async () => {
    const {default: PersonasPage} = await import('@/app/pipeline/personas/page');
    page.session.sd = {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'stale'}};
    view.session = {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}};
    expect(PersonasPage().type).toBe(PersonaScreen);
  });
  it('gates the selected running session when the store session is done', async () => {
    const {default: PersonasPage} = await import('@/app/pipeline/personas/page');
    page.session.sd = {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}};
    view.session = {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'running'}};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'needs-prep', stage: '페르소나'}});
  });
  it.each([null, undefined])('falls back to the store session when view.session is %s', async (session) => {
    const {default: PersonasPage} = await import('@/app/pipeline/personas/page');
    view.session = session;
    page.session.sd = {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}};
    expect(PersonasPage().type).toBe(PersonaScreen);
    page.session.sd = {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'stale'}};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'needs-prep', stage: '페르소나'}});
  });
  it('routes by gate without importing the v1 api', async () => {
    const pageModule = import('@/app/pipeline/personas/page');
    await expect(pageModule).resolves.toHaveProperty('default');
    const {default: PersonasPage} = await pageModule;
    page.session = {sid: 's', sd: {schemaVersion: 2}};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'needs-prep', stage: '페르소나'}});
    page.session = {sid: 's', sd: {}};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'legacy', stage: '페르소나'}});
    page.session = {sid: null, sd: null};
    expect(PersonasPage()).toMatchObject({type: LaterStageBanner, props: {gate: 'no-session', stage: '페르소나'}});
    page.session = {sid: 's', sd: {schemaVersion: 2, prep: {derivedRef: {prepKey: 'p'}, status: 'done'}}};
    expect(PersonasPage().type).toBe(PersonaScreen);
  });
});
