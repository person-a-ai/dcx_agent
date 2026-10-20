import { expect, it, vi } from 'vitest';
const state = vi.hoisted(() => ({sid:'s',sd:{schemaVersion:2,prep:{derivedRef:''},insight:{confirmed:['I1']}} as {schemaVersion?:number;prep:{derivedRef:string};insight:{confirmed:string[]}}}));
const view = vi.hoisted(() => ({version:'v2',readonly:false,conflict:false,session:null}));
vi.mock('@/stores/useSessionStore', () => ({useSessionStore:() => state}));
vi.mock('@/components/versions/VersionProvider', () => ({useVersion:() => view}));
vi.mock('@/components/persona/InsightScreen', () => ({InsightScreen:() => null}));
vi.mock('next/navigation', () => ({redirect:vi.fn()}));
import Page from '@/app/pipeline/insights/page';
import OldPage from '@/app/insights/page';
import { InsightScreen } from './InsightScreen';
import { LaterStageBanner } from '@/components/LaterStageBanner';
import { redirect } from 'next/navigation';
it('redirects /insights to the pipeline route', () => {OldPage();expect(redirect).toHaveBeenCalledWith('/pipeline/insights');});
it('shows the prep banner for v2 sessions and the legacy banner for old sessions', () => {
 state.sd = {schemaVersion:2, prep:{derivedRef:''}, insight:{confirmed:[]}};
 let page = Page(); expect(page.type).toBe(LaterStageBanner); expect(page.props).toEqual({gate:'needs-prep', stage:'인사이트'});
 state.sd = {prep:{derivedRef:''}, insight:{confirmed:[]}};
 page = Page(); expect(page.type).toBe(LaterStageBanner); expect(page.props).toEqual({gate:'legacy', stage:'인사이트'});
});
it('passes session, selected version, confirmations and conflict readonly to new screen', () => {
 state.sd={prep:{derivedRef:''},insight:{confirmed:['I1']}};
 state.sd.prep.derivedRef='derived';view.conflict=true;
 const page = Page();expect(page.type).toBe(InsightScreen);expect(page.props).toMatchObject({sid:'s',version:'v2',readonly:true,initialConfirmed:['I1']});
});
