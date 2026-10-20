/* eslint-disable @typescript-eslint/no-explicit-any */
import { afterEach, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
const hooks = vi.hoisted(() => ({slots: [] as any[], cursor: 0, effects: [] as (() => void | (() => void))[]}));
vi.mock('react', async () => ({...await vi.importActual('react'),
 useState: (initial:any) => {const i=hooks.cursor++;if(!(i in hooks.slots)) hooks.slots[i]=initial;return [hooks.slots[i],(next:any)=>{hooks.slots[i]=next;}];},
 useEffect: (effect:()=>void) => {hooks.effects.push(effect);},
 useRef: (initial:any) => {const i=hooks.cursor++;if(!(i in hooks.slots)) hooks.slots[i]={current:initial};return hooks.slots[i];},
}));
const state = vi.hoisted(() => ({push:vi.fn(),select:vi.fn(),setSession:vi.fn(), version:'v1'}));
vi.mock('next/navigation',()=>({useRouter:()=>({push:state.push}),usePathname:()=>'/pipeline/evidence'}));
vi.mock('./VersionProvider',()=>({useVersion:()=>({sid:'s',version:state.version,readonly:true,session:{collectionId:'c1',crawlConfig:{channels:['youtube_vlog']}},meta:{activeVersion:'v2'},select:state.select})}));
vi.mock('../DirtyProvider',()=>({useDirty:()=>({confirmNavigation:()=>true})}));
vi.mock('@/stores/useSessionStore',()=>({useSessionStore:Object.assign(()=>({}),{getState:()=>({setSession:state.setSession})})}));
vi.mock('@/lib/api/versions',()=>({createVersion:vi.fn(),getVersionSession:vi.fn()}));
import { createVersion, getVersionSession } from '@/lib/api/versions';
import { HistoricalCrawl, RestartVersion } from './StageVersion';
vi.mock('@/lib/api/crawl',()=>({getCrawlReport:vi.fn()}));
import { getCrawlReport } from '@/lib/api/crawl';
function nodes(n:any):any[]{return !n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(nodes):[n,...nodes(n.props?.children)];}
function render(){hooks.cursor=0;return nodes(RestartVersion({}));}
afterEach(()=>{hooks.slots=[];hooks.effects=[];state.version='v1';vi.clearAllMocks();});
it('offers stage 8 and opens personas after creating its restart version',async()=>{
 const tree=render();
 expect(tree.find(n=>n.type==='option' && n.props.value==='stage8')?.props.children).toEqual([8,'단계']);
 tree.find(n=>n.type==='select').props.onChange({target:{value:'stage8'}});
 vi.mocked(createVersion).mockResolvedValue({version:'v2'});
 vi.mocked(getVersionSession).mockResolvedValue({data:{step:'persona-start',version:'v2'}} as any);
 const button=render().find(n=>n.props.children==='새 버전 만들기');
 expect(button.props.disabled).toBe(false);
 button.props.onClick();
 await vi.waitFor(()=>expect(state.push).toHaveBeenCalledWith('/pipeline/personas'));
 expect(createVersion).toHaveBeenCalledWith('s','v2','stage8','');
 expect(state.select).toHaveBeenCalledWith('v2',true);
});

const savedReport = {version:'v1',collectionId:'c1',keywordDisplay:{},report:{
 matrix:{},totals:{doc_count:47},channels:{youtube_vlog:{docs:47,urls_done:8,share:1,status:'done',errors_top:[],skip_reasons:{no_ko_captions:3}}},
}};
function history(){hooks.cursor=0;return HistoricalCrawl();}
it('fetches the selected version report and renders readonly results above saved settings',async()=>{
 vi.mocked(getCrawlReport).mockResolvedValue(savedReport);
 history(); hooks.effects.pop()!();
 await vi.waitFor(()=>expect(hooks.slots.some(s=>s?.report || s?.data?.report)).toBe(true));
 expect(getCrawlReport).toHaveBeenCalledWith('s','v1');
 const html=renderToStaticMarkup(history());
 expect(html).toContain('P5 수집 요약');
 expect(html).toContain('수집 문서');
 expect(html).toContain('채널별 건너뛴 사유');
 expect(html).toContain('class="crawl-channel-scroll" role="region" aria-label="채널별 건너뛴 사유 스크롤" tabindex="0"');
 expect(html).toContain('한국어 자막 없음');
 expect(html).toContain('3개 영상');
 expect(html).toContain('영상 8개 → 구간 47');
 expect(html.indexOf('P5 수집 요약')).toBeLessThan(html.indexOf('크롤링 수집본'));
 expect(html).toContain('과거 버전의 실시간 수집 상태는 제공되지 않습니다');
 expect(html).not.toMatch(/일시 정지하기|다시 수집|상세 수집 시작|남은 URL/);
});
it('keeps saved settings when there is no report',async()=>{
 vi.mocked(getCrawlReport).mockRejectedValue(new Error('No crawl report'));
 history(); hooks.effects.pop()!();
 await Promise.resolve(); await Promise.resolve();
 const html=renderToStaticMarkup(history());
 expect(html).toContain('크롤링 수집본');
 expect(html).toContain('수집 설정');
 expect(html).not.toContain('P5 수집 요약');
});
it('does not leak a late report after selecting another version',async()=>{
 let resolve!:(value:typeof savedReport)=>void;
 vi.mocked(getCrawlReport).mockReturnValue(new Promise(r=>{resolve=r;}));
 history(); const cleanup=hooks.effects.pop()!();
 state.version='v2'; cleanup?.();
 resolve(savedReport); await Promise.resolve(); await Promise.resolve();
 expect(renderToStaticMarkup(history())).not.toContain('P5 수집 요약');
});
