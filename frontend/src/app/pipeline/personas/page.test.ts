import { describe, expect, it, vi } from 'vitest';
const page = vi.hoisted(() => ({session: {sid: 's', sd: {schemaVersion: 2}} as {sid: string | null; sd: Record<string, unknown> | null}}));
vi.mock('@/stores/useSessionStore', () => ({useSessionStore: () => page.session}));
vi.mock('@/components/versions/VersionProvider', () => ({useVersion: () => ({version: 'v1', readonly: false, conflict: false, session: null})}));
vi.mock('@/components/persona/PersonaScreen', () => ({PersonaScreen: () => null}));
vi.mock('@/lib/api', () => { throw new Error('v1 api must not be imported by the personas page'); });
vi.mock('next/navigation', () => ({useRouter: () => ({push: vi.fn()})}));
import { LaterStageBanner } from '@/components/LaterStageBanner';
import { PersonaScreen } from '@/components/persona/PersonaScreen';

describe('personas page gate', () => {
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
