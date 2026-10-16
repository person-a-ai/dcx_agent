/* eslint-disable @typescript-eslint/no-explicit-any */
import { beforeEach, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
const h = vi.hoisted(() => ({values: [] as any[], cursor: 0, data: null as any, options: null as any, session: {sid:'s',sd:{prep:{derivedRef:'ref'}}} as any, push:vi.fn(), refresh:vi.fn(), history:false}));
vi.mock('react', async original => ({...await original<typeof import('react')>(), useState:(initial:any)=>{const i=h.cursor++;if(!(i in h.values))h.values[i]=typeof initial==='function'?initial():initial;return [h.values[i],(next:any)=>{h.values[i]=typeof next==='function'?next(h.values[i]):next;}];},useRef:(v:any)=>{const i=h.cursor++;return h.values[i]??(h.values[i]={current:v});},useMemo:(factory:any,deps:any[])=>{const i=h.cursor++;const previous=h.values[i];if(!previous||deps.some((value,index)=>!Object.is(value,previous.deps[index])))h.values[i]={deps,value:factory()};return h.values[i].value;},useCallback:(f:any)=>f,useEffect:()=>{}}));
vi.mock('next/navigation',()=>({useRouter:()=>({push:h.push}),usePathname:()=>'/pipeline/personas'}));
vi.mock('@/stores/useSessionStore',()=>({useSessionStore:()=>h.session}));
vi.mock('@/components/versions/VersionProvider',()=>({useVersion:()=>({version:'v2',readonly:h.history,meta:{activeVersion:'v3'},session:null})}));
vi.mock('@/components/versions/useStageCompletionRefresh',()=>({useStageCompletionRefresh:vi.fn()}));
vi.mock('@/lib/usePolling',()=>({usePolling:(options:any)=>{h.options=options;return {data:h.data,refresh:h.refresh};}}));
vi.mock('@/lib/api/persona',()=>({getPersonaStatus:vi.fn(),getPersonaCards:vi.fn(),getPersonaMap:vi.fn(),getPersonaTree:vi.fn(),startPersona:vi.fn(),retryPersonaCard:vi.fn()}));
vi.mock('@/lib/api/segment',()=>({getSegmentPersonas:vi.fn().mockResolvedValue({personas:[]})}));
import { PersonaScreen } from './PersonaScreen';
import { ContextTable } from './ContextTable';
import { VersionRouteBoundary } from '../versions/StageVersion';
import Page from '../../app/pipeline/personas/page';
import { OpportunityMap } from './OpportunityMap';
import { PersonaSummary } from './PersonaSummary';
import { HierarchyTree } from './HierarchyTree';
import { CCMTable } from './CCMTable';

import * as api from '@/lib/api/persona';
import { ApiError } from '@/lib/api/errors';
import { addKnownInsight } from '@/lib/api/known';
vi.mock('@/lib/api/known',()=>({addKnownInsight:vi.fn().mockResolvedValue({id:'known1'})}));
function nodes(n:any):any[]{return !n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(nodes):[n,...nodes(n.props?.children)];}
function text(n:any):string{return typeof n==='string'||typeof n==='number'?String(n):Array.isArray(n)?n.map(text).join(''):n?.type===PersonaSummary? n.props.name+' '+n.props.meta :n?.props?text(n.props.children):'';}
const draw=(readonly=false)=>{h.cursor=0;return PersonaScreen({sid:'s',version:'v2',readonly});};
const button=(tree:any,label:string)=>nodes(tree).find(n=>text(n)===label&&n.props?.onClick);
const point=(id:string,odi:number)=>({context_id:id,persona_id:'P1',cluster_id:'CL0',i:.5,s:.4,odi,zone:'B',star:false,counter:false,shape:'circle',tone:0});
beforeEach(()=>{vi.clearAllMocks();h.history=false;h.values=[];h.cursor=0;h.session={sid:'s',sd:{prep:{derivedRef:'ref'}}};h.data={status:{package:true,status:'done',run:'r1',progress:1,personas:[{id:'P1',status:'done'}]},cards:{run:'r1',personas:{P1:{status:'done',card:{persona_name:'확정 이름',cluster_id:'CL0',desire:'확정 Desire',goal:['목표'],metrics:{doc_count:12,author_count:8},contexts:[]}}}},map:{points:[point('C1',1),point('C2',3)],base:{s_line:.5,diag1:[[0,.4],[1,1]],diag2:[[.5,0],[1,1]]}},tree:null,identities:[]};});
it('opens map first, switches both views, and opens the point persona card',()=>{let tree=draw();expect(nodes(tree).some(n=>n.type===OpportunityMap)).toBe(true);button(tree,'Persona 카드').props.onClick();tree=draw();expect(text(tree)).toContain('확정 이름');expect(text(tree)).toContain('근거 12건 · 작성자 8명 · Context 0개');button(tree,'전체 맵').props.onClick();tree=draw();nodes(tree).find(n=>n.type===OpportunityMap).props.onOpenCard('P1','C2');tree=draw();expect(button(tree,'Persona 카드').props['aria-pressed']).toBe(true);expect(nodes(tree).find(n=>n.type===OpportunityMap).props.focusPersonaId).toBe('P1');});
it('places the sortable Context table below the map',()=>{const tree=draw();const all=nodes(tree);expect(all.findIndex(n=>n.type===ContextTable)).toBeGreaterThan(all.findIndex(n=>n.type===OpportunityMap));const props=all.find(n=>n.type===ContextTable).props;h.values=[];h.cursor=0;let table=ContextTable(props);expect(renderToStaticMarkup(table).indexOf('C2')).toBeLessThan(renderToStaticMarkup(table).indexOf('C1'));button(table,'기회').props.onClick();h.cursor=0;table=ContextTable(props);expect(renderToStaticMarkup(table).indexOf('C1')).toBeLessThan(renderToStaticMarkup(table).indexOf('C2'));});
it('retries only the failed persona with the current run and version',async()=>{h.data.cards.personas.P1.status='failed';h.data.status.personas[0].status='failed';let tree=draw();button(tree,'Persona 카드').props.onClick();tree=draw();expect(text(tree)).toContain('이 페르소나 카드를 만들지 못했습니다.');await button(tree,'다시 만들기').props.onClick();expect(api.retryPersonaCard).toHaveBeenCalledWith('s','P1',{run:'r1'},'v2');});
it('shows the exact missing-package empty state and evidence navigation',()=>{h.data={...h.data,missing:true};const tree=draw();expect(text(tree)).toContain('근거 탐색을 마친 뒤 페르소나를 만들 수 있습니다.');button(tree,'근거 탐색으로').props.onClick();expect(h.push).toHaveBeenCalledWith('/pipeline/evidence');expect(button(tree,'페르소나 만들기')).toBeUndefined();});
it('keeps legacy sessions on the original page and keys new sessions by version',()=>{expect(Page().type).toBe(PersonaScreen);expect(Page().key).toBe('s:v2');h.session.sd={};expect(Page().type).not.toBe(PersonaScreen);});
it('keeps readonly navigation available while disabling retry',()=>{h.data.cards.personas.P1.status='failed';h.data.status.personas[0].status='failed';let tree=draw(true);button(tree,'Persona 카드').props.onClick();tree=draw(true);expect(button(tree,'다시 만들기').props.disabled).toBe(true);});
it('renders intent warning, null attributes and blocked constraint reasons',()=>{h.data.cards.personas.P1.prescription={blocked:true,constraint:[{constraint:'의료적 효과 표현 금지',verdict:'violates',reason:'효과를 단정함'}]};let tree=draw();button(tree,'Persona 카드').props.onClick();tree=draw();expect(text(draw())).toContain('의도 ≠ 행동');expect(renderToStaticMarkup(draw())).toContain('근거 부족');expect(text(draw())).toContain("사내 제약 '의료적 효과 표현 금지'를 지키는 처방을 만들지 못했습니다.");});

it('loads versioned results and refreshes after partial results instead of caching failure',async()=>{const snapshot=h.data;vi.mocked(api.getPersonaStatus).mockResolvedValue(snapshot.status);vi.mocked(api.getPersonaCards).mockResolvedValue(snapshot.cards);vi.mocked(api.getPersonaMap).mockRejectedValueOnce(new Error('결과 준비 중')).mockResolvedValue(snapshot.map);vi.mocked(api.getPersonaTree).mockResolvedValue({id:'product',size:12});draw();const first=await h.options.fetcher();expect(first.map).toBeNull();const second=await h.options.fetcher();expect(second.map.points).toHaveLength(2);expect(api.getPersonaCards).toHaveBeenCalledWith('s','v2');expect(api.getPersonaMap).toHaveBeenCalledTimes(2);});
it('handles missing package returned by the run endpoint',async()=>{h.data.status={status:'idle',run:null,progress:0,personas:[]};vi.mocked(api.startPersona).mockRejectedValueOnce(new ApiError('근거 탐색을 마친 뒤 페르소나를 만들 수 있습니다.','evidence_required',409));await button(draw(),'페르소나 만들기').props.onClick();expect(text(draw())).toContain('근거 탐색을 마친 뒤 페르소나를 만들 수 있습니다.');});
it('enforces readonly in mutation handlers and keeps a single primary',async()=>{h.data.status.status='idle';const tree=draw(true);expect(nodes(tree).filter(n=>n.props?.variant==='primary')).toHaveLength(1);await button(tree,'페르소나 만들기').props.onClick();expect(api.startPersona).not.toHaveBeenCalled();});

it('allows version-aware Persona screens through the historical route boundary',()=>{h.history=true;expect(VersionRouteBoundary({children:'persona child'})).toBe('persona child');h.session.sd={};expect(VersionRouteBoundary({children:'legacy child'})).not.toBe('legacy child');});
it('shows unverified original quotes and adds their source document to Known Insight',async()=>{h.data.cards.personas.P1.card.contexts=[{context_id:'C1',context_name:'상황',state:{text:'상태',cite:['E1']}}];h.data.cards.personas.P1.trace=[{context_id:'C1',field:'state',evidence_id:'E1',evidence:{doc_id:'doc1',source:'카페',quote:{text:'원문 인용',verified:false,field:'body',start:3,end:8}}}];let tree=draw();button(tree,'Persona 카드').props.onClick();tree=draw();const table=nodes(tree).find(n=>n.type===CCMTable);const cell=table.props.contexts[0].cells.state;expect(renderToStaticMarkup(cell.evidence)).toContain('인용 문장을 원문에서 찾지 못해 추론으로 낮췄습니다.');expect(text(cell.evidence)).toContain('원문 인용');await button(cell.evidence,'Known Insight에 추가').props.onClick();expect(addKnownInsight).toHaveBeenCalledWith('s',{type:'doc',doc_id:'doc1'},'v2');});

it('C1 regenerates stale results with fresh true',async()=>{h.data.status.status='stale';vi.stubGlobal('confirm',vi.fn(()=>true));try{await button(draw(),'페르소나 다시 만들기').props.onClick();expect(api.startPersona).toHaveBeenCalledWith('s',{fresh:true},'v2');}finally{vi.unstubAllGlobals();}});
it.each(['evidence_required'])('I1 uses real cards fetch error kind %s on entry',async kind=>{const real=await vi.importActual<typeof import('@/lib/api/persona')>('@/lib/api/persona');vi.mocked(api.getPersonaStatus).mockResolvedValue({status:'none',run:null,progress:0,personas:[]} as any);vi.mocked(api.getPersonaCards).mockImplementation(real.getPersonaCards);vi.mocked(api.getPersonaMap).mockResolvedValue(h.data.map);vi.mocked(api.getPersonaTree).mockResolvedValue({});vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:409,json:async()=>({error:{kind,message:'아직 결과가 준비되지 않았습니다.'}})}));try{draw();h.data=await h.options.fetcher();const tree=draw();expect(text(tree)).toContain('근거 탐색을 마친 뒤 페르소나를 만들 수 있습니다.');button(tree,'근거 탐색으로').props.onClick();expect(h.push).toHaveBeenCalledWith('/pipeline/evidence');}finally{vi.unstubAllGlobals();}});
it('I3 renders context keywords and persona artifacts in CCM',()=>{Object.assign(h.data.cards.personas.P1.card,{artifacts:[{name:'노트북',mention_count:1234}],contexts:[{context_id:'C1',keywords:['휴대','작업']}]});button(draw(),'Persona 카드').props.onClick();const cells=nodes(draw()).find(n=>n.type===CCMTable).props.contexts[0].cells;expect(cells.keywords.text).toBe('휴대 · 작업');expect(cells.artifact.text).toContain('노트북');expect(cells.artifact.text).toContain('1,234');});
it('D315 localizes attribute keys and formats counts and metrics',()=>{Object.assign(h.data.cards.personas.P1.card,{metrics:{doc_count:12345,author_count:2345},journey:{pre_purchase:.623456,purchase:.2,post_purchase:.8},sensitivity:{price:'상',brand:'중',function:'하'}});button(draw(),'Persona 카드').props.onClick();expect(text(draw())).toContain('12,345건');const out=text(draw());expect(out).toContain('구매 전: 0.62');expect(out).toContain('가격: 상');expect(out).not.toContain('pre_purchase');});
it('I1 handles a real status endpoint evidence_required error on entry',async()=>{const real=await vi.importActual<typeof import('@/lib/api/persona')>('@/lib/api/persona');vi.mocked(api.getPersonaStatus).mockImplementation(real.getPersonaStatus);vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:409,json:async()=>({error:{kind:'evidence_required',message:'package missing'}})}));try{draw();await expect(h.options.fetcher()).rejects.toThrow();expect(text(draw())).toContain('근거 탐색을 마친 뒤 페르소나를 만들 수 있습니다.');}finally{vi.unstubAllGlobals();}});
it('I1 does not replace a running persona with an empty-evidence state for unpublished cards',async()=>{const real=await vi.importActual<typeof import('@/lib/api/persona')>('@/lib/api/persona');vi.mocked(api.getPersonaStatus).mockResolvedValue({...h.data.status,status:'running'});vi.mocked(api.getPersonaCards).mockImplementation(real.getPersonaCards);vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:409,json:async()=>({error:{kind:'not_ready',message:'결과 준비 중'}})}));try{draw();h.data=await h.options.fetcher();expect(text(draw())).toContain('페르소나를 만들고 있습니다.');expect(button(draw(),'근거 탐색으로')).toBeUndefined();}finally{vi.unstubAllGlobals();}});

it.each([true,false])('N1 uses package=%s with none and cards not_ready',async present=>{
 const {ApiError}=await import('@/lib/api/errors');
 vi.mocked(api.getPersonaStatus).mockResolvedValue({...h.data.status,status:'none',package:present} as any);
 vi.mocked(api.getPersonaCards).mockRejectedValue(new ApiError('준비 중','not_ready',409));
 draw();h.data=await h.options.fetcher();
 expect(Boolean(button(draw(),'페르소나 만들기'))).toBe(present);
 expect(Boolean(button(draw(),'근거 탐색으로'))).toBe(!present);
});
it('C1 sends old package users to evidence without offering regeneration',()=>{
 h.data.status={...h.data.status,status:'stale',package:true,evidence_required:true};
 expect(text(draw())).toContain('근거 탐색을 다시 실행한 뒤 페르소나를 만드세요.');
 button(draw(),'근거 탐색으로').props.onClick();
 expect(h.push).toHaveBeenCalledWith('/pipeline/evidence');
 expect(button(draw(),'페르소나 다시 만들기')).toBeUndefined();
});
it('C1 cancelled rebuild does not launch destructive fresh work',async()=>{
 h.data.status.status='stale';const confirm=vi.fn(()=>false);vi.stubGlobal('confirm',confirm);
 try {await button(draw(),'페르소나 다시 만들기').props.onClick();
 expect(confirm).toHaveBeenCalledWith('페르소나를 다시 만들면 인사이트와 컨셉도 지워집니다. 계속할까요?');
 expect(api.startPersona).not.toHaveBeenCalled();} finally {vi.unstubAllGlobals();}
});
it.each([[.7,'상'],[.4,'중'],[.39,'하']])('M8 confidence from traceable support %s', (support,expected)=>{
 h.data.cards.personas.P1.card.traceable_support={C1:support,C2:support};
 h.data.cards.personas.P1.prescription={blocked:false,constraint:[{verdict:'ok'}]};
 button(draw(),'Persona 카드').props.onClick();
 expect(text(draw())).toContain(`신뢰도 ${expected}`);
 expect(text(draw())).toContain('처방 · 제약 ✓ 통과');
});
it.each([[false,'review','⚠ 검토'],[true,'violates','✕ 차단']])('M8 constraint summary %s %s',(blocked,verdict,expected)=>{
 h.data.cards.personas.P1.prescription={blocked,constraint:[{verdict}]};
 button(draw(),'Persona 카드').props.onClick();expect(text(draw())).toContain(`처방 · 제약 ${expected}`);
});
it('M14 exposes simultaneous panels through headings without tab roles',()=>{
 button(draw(),'Persona 카드').props.onClick();
 const tree=draw();expect(nodes(tree).filter(n=>n.type==='h3').map(text)).toEqual(expect.arrayContaining(['8-B 수렴','8-C 속성','8-D 처방','구조 트리']));
 expect(nodes(tree).some(n=>['tab','tablist','tabpanel'].includes(n.props?.role))).toBe(false);
});
it('M6 uses naturally sorted backend legend presentation',()=>{
 const map={...h.data.map,points:[{...point('C10',1),cluster_id:'CL10',persona_id:'P10'},{...point('C2',1),cluster_id:'CL2',persona_id:'P2'}],legend:[
 {cluster_id:'CL10',shape:'diamond',cluster_label:'ten',personas:[{persona_id:'P10',persona_name:'열 이름',tone:'--ink'}]},
 {cluster_id:'CL2',shape:'triangle',cluster_label:null,personas:[{persona_id:'P2',persona_name:'둘 이름',tone:'--line-strong'}]}]};
 const tree=OpportunityMap({map});const out=renderToStaticMarkup(tree);
 expect(out.indexOf('▲ CL2')).toBeLessThan(out.indexOf('◆ CL10'));
 expect(out).toContain('둘 이름');expect(out).toContain('ten');
 const points=nodes(tree).filter(n=>n.props?.['data-context-id']);
 expect(points[0].props['data-shape']).toBe('diamond');expect(points[1].props.stroke).toBe('var(--line-strong)');
});
it('M7 legend toggles point visibility and keeps the table complete',()=>{
 const map=h.data.map;let tree=OpportunityMap({map});
 nodes(tree).find(n=>n.props?.['aria-label']==='Persona P1').props.onClick();h.cursor=0;tree=OpportunityMap({map});
 expect(nodes(tree).filter(n=>n.props?.['data-context-id'])).toHaveLength(0);
 expect(map.points).toHaveLength(2);
 nodes(tree).find(n=>n.props?.['aria-label']==='Persona P1').props.onClick();h.cursor=0;
 expect(nodes(OpportunityMap({map})).filter(n=>n.props?.['data-context-id'])).toHaveLength(2);
});
it('N6 retains decimal metrics greater than one in CCM and prescription',()=>{
 h.data.cards.personas.P1.card.contexts=[{context_id:'unmapped',metrics:{odi:1.37}}];
 h.data.cards.personas.P1.prescription={target_metric:1.37};
 button(draw(),'Persona 카드').props.onClick();
 expect(nodes(draw()).find(n=>n.type===CCMTable).props.contexts[0].cells.opportunity.text).toBe('1.37');
 expect(text(draw())).toContain('핵심 지표 · 1.37');
});

vi.mock('@/lib/api/insight',()=>({getInsights:vi.fn(),startInsight:vi.fn().mockResolvedValue({runId:'ir1'})}));
import * as insightApi from '@/lib/api/insight';
it('QA-F3 keeps blocked text muted and struck without active metrics',()=>{
 h.data.cards.personas.P1.prescription={blocked:true,direction:'위반 처방',target_metric:'만족도',contribution:'효과',constraint:[{constraint:'금지',verdict:'violates',reason:'위반 이유'}]};
 button(draw(),'Persona 카드').props.onClick();
 const tree=draw();expect(text(tree)).toContain('차단된 처방');expect(text(tree)).toContain('위반 이유');
 expect(text(tree)).not.toContain('핵심 지표');expect(text(tree)).not.toContain('기여 ·');
 const struck=nodes(tree).find(n=>n.type==='s');expect(text(struck)).toBe('위반 처방');expect(struck.props.className).toContain('text-muted');
});
it.each([0,1])('QA-F6 derives only without an existing revision (%s)',async revision=>{
 vi.mocked(insightApi.getInsights).mockResolvedValue({insights:{revision,items:[],history:[]},concepts:{revision:0,items:[],history:[]},bars:null,radar:null,worker:{status:'idle',reason:null,runId:null,mode:null,target:null}});
 await button(draw(),'인사이트 도출').props.onClick();
 expect(insightApi.startInsight).toHaveBeenCalledTimes(revision?0:1);expect(h.push).toHaveBeenCalledWith('/pipeline/insights');
});
it.each(['evidence_required','package'])('m3 hides evidence action in readonly %s guidance',key=>{
 h.data.status[key]=key==='package'?false:true;expect(button(draw(true),'근거 탐색으로')).toBeUndefined();
});

it('Q2 failed card keeps package counts with a null card',()=>{
 h.data.cards.personas.P1={status:'failed',card:null,error:'qa',package_counts:{doc_count:16,author_count:8,context_count:2}};
 h.data.status.personas[0].status='failed';
 button(draw(),'Persona 카드').props.onClick();
 expect(text(draw())).toContain('근거 16건 · 작성자 8명 · Context 2개');
});

it('marks traces with no quote as unverified inference',()=>{
 h.data.cards.personas.P1.card.contexts=[{context_id:'C1',state:{text:'상태',cite:['E1']}}];
 h.data.cards.personas.P1.trace=[{context_id:'C1',field:'state',evidence_id:'E1',evidence:{doc_id:'doc1',quote:null}}];
 button(draw(),'Persona 카드').props.onClick();
 const cell=nodes(draw()).find(n=>n.type===CCMTable).props.contexts[0].cells.state;
 expect(text(cell.evidence)).toContain('인용 없음 · 추론');
 expect(text(cell.evidence)).toContain('인용 미확인');
});

it('T8 preselects the highest opportunity and assembles a continuous card surface',()=>{
 let tree=draw();expect(nodes(tree).find(n=>n.type===OpportunityMap).props.highlightedId).toBe('C2');expect(text(nodes(tree).find(n=>n.props?.['aria-label']==='선택 Context 상세'))).toContain('C2');
 button(tree,'Persona 카드').props.onClick();tree=draw();
 const all=nodes(tree);expect(all.find(n=>n.type===PersonaSummary)).toBeTruthy();
 expect(all.find(n=>n.type===OpportunityMap).props.focusPersonaId).toBe('P1');
 expect(all.some(n=>['tab','tablist','tabpanel'].includes(n.props?.role))).toBe(false);
 expect(text(tree)).toContain('8-B 수렴');expect(text(tree)).toContain('8-C 속성');expect(text(tree)).toContain('8-D 처방');
});
it('T8 maps pain points and context document counts into CCM',()=>{
 h.data.cards.personas.P1.card.contexts=[{context_id:'C1',pain_points:[{text:'불편',grade:'observed',cite:['E1']},{text:'불안',grade:'inferred',cite:['E2']}],metrics:{doc_count:2},evidence:[{id:'E1'},{id:'E2'}]}];
 button(draw(),'Persona 카드').props.onClick();
 const cells=nodes(draw()).find(n=>n.type===CCMTable).props.contexts[0].cells;
 expect(cells.pain_point).toMatchObject({text:'불편',grade:'observed',more:1});expect(cells.evidence_count.text).toBe('2');
});
it('T8 failed cards replace all three supporting panels with one notice',()=>{
 h.data.cards.personas.P1.status='failed';button(draw(),'Persona 카드').props.onClick();
 const out=text(draw());expect(out.split('이 페르소나 카드를 만들지 못했습니다.')).toHaveLength(2);expect(out).not.toContain('8-B 수렴');
});

it('T8 orders summary, comparison, panels and expanded hierarchy with only allowed card surfaces',()=>{
 h.data.tree={id:'root',children:[{id:'CL0',children:[{id:'P1'}]}]};
 h.data.cards.personas.P1.card.pain_points=[{text:'불편',grade:'observed',context_ids:['C1'],cite:['E1']}];
 h.data.cards.personas.P1.card.contexts=[{context_id:'C1'}];
 button(draw(),'Persona 카드').props.onClick();
 const tree=draw(), all=nodes(tree);
 const summary=all.findIndex(n=>n.type===PersonaSummary),ccm=all.findIndex(n=>n.type===CCMTable),map=all.findIndex(n=>n.type===OpportunityMap),panel=all.findIndex(n=>n.type==='h3'&&text(n)==='8-B 수렴'),hierarchy=all.findIndex(n=>n.type===HierarchyTree);
 expect(summary).toBeLessThan(ccm);expect(ccm).toBeLessThan(map);expect(map).toBeLessThan(panel);expect(panel).toBeLessThan(hierarchy);
 expect(all[hierarchy].props.expandedId).toBe('P1');
 const html=renderToStaticMarkup(tree);
 expect((html.match(/class="ds-card(?: |")/g)||[])).toHaveLength(2);
 expect(html).toContain('persona-mobile-select');expect(html).toContain('페인포인트');
});
it.each(['map','cards','tree','identities'] as const)('T8 retries only the failed %s request and retains other areas',async area=>{
 const snapshot=h.data;
 vi.mocked(api.getPersonaStatus).mockResolvedValue(snapshot.status);
 vi.mocked(api.getPersonaCards).mockResolvedValue(snapshot.cards);
 vi.mocked(api.getPersonaMap).mockResolvedValue(snapshot.map);
 vi.mocked(api.getPersonaTree).mockResolvedValue({id:'root'});
 const segment=await import('@/lib/api/segment');
 vi.mocked(segment.getSegmentPersonas).mockResolvedValue({personas:[]} as any);
 const calls={map:api.getPersonaMap,cards:api.getPersonaCards,tree:api.getPersonaTree,identities:segment.getSegmentPersonas};
 vi.mocked(calls[area]).mockRejectedValueOnce(new Error('영역 오류'));
 draw();h.data=await h.options.fetcher();
 button(draw(),'Persona 카드').props.onClick();
 const tree=draw();expect(nodes(tree).some(n=>n.props?.role==='alert')).toBe(true);
 if(area==='map')expect(nodes(tree).some(n=>n.type===PersonaSummary)).toBe(true);
 Object.values(calls).forEach(call=>vi.mocked(call).mockClear());
 await button(tree,'다시 불러오기').props.onClick();
 expect(calls[area]).toHaveBeenCalledTimes(1);
 Object.entries(calls).filter(([key])=>key!==area).forEach(([,call])=>expect(call).not.toHaveBeenCalled());
 expect(nodes(draw()).some(n=>n.props?.role==='alert')).toBe(false);
});
it('T8 presents independent loading areas with CCM headings and an empty map',()=>{
 h.data=null;
 let tree=draw();expect(nodes(tree).some(n=>n.props?.['aria-label']==='페르소나 목록'&&n.props?.['aria-busy'])).toBe(true);
 expect(nodes(tree).find(n=>n.type===OpportunityMap).props.map.points).toEqual([]);
 button(tree,'Persona 카드').props.onClick();tree=draw();
 for(const title of ['Pain Points','Context 비교 표','Opportunity Map','8-B 수렴','8-C 속성','8-D 처방','구조 트리']){
  expect(nodes(tree).some(n=>n.props?.['aria-label']===title&&n.props?.['aria-busy'])).toBe(true);
 }
 expect(text(tree)).toContain('페인포인트');expect(text(tree)).toContain('근거 수');
});
it.each([undefined,[]])('T8 distinguishes legacy pain fields from empty evidence (%s)',painPoints=>{
 h.data.cards.personas.P1.card.pain_points=painPoints;
 button(draw(),'Persona 카드').props.onClick();
 expect(nodes(draw()).find(n=>n.type===PersonaSummary).props.legacy).toBe(painPoints===undefined);
});

it.each([true,false])('RV1 pain quote verification %s is independent',verified=>{
 h.data.cards.personas.P1.card.contexts=[{context_id:'C1',pain_points:[{text:'불편'}]}];
 h.data.cards.personas.P1.trace=[{context_id:'C1',field:'pain_point',evidence_id:'E1',evidence:{quote:{text:'일반 인용',verified:!verified},pain_point:{quote:'페인 인용',verified}}}];
 button(draw(),'Persona 카드').props.onClick();
 const evidence=nodes(draw()).find(n=>n.type===CCMTable).props.contexts[0].cells.pain_point.evidence;
 expect(text(evidence)).toContain('페인 인용');expect(text(evidence)).not.toContain('일반 인용');
 expect(text(evidence).includes('인용 미확인')).toBe(!verified);
});
it('RV3 map and row clicks persist detail without opening the card',()=>{
 let tree=draw();let map=nodes(tree).find(n=>n.type===OpportunityMap);
 const rendered=OpportunityMap(map.props);
 nodes(rendered).find(n=>n.props?.['data-context-id']==='C1').props.onClick();
 tree=draw();expect(button(tree,'전체 맵').props['aria-pressed']).toBe(true);
 const detail=()=>text(nodes(draw()).find(n=>n.props?.['aria-label']==='선택 Context 상세'));
 expect(detail()).toContain('C1');
 map=nodes(tree).find(n=>n.type===OpportunityMap);map.props.onHighlight('C2');expect(detail()).toContain('C1');
 map.props.onHighlight(null);expect(detail()).toContain('C1');
 const table=nodes(draw()).find(n=>n.type===ContextTable);
 table.props.onSelect('C2');expect(detail()).toContain('C2');
 expect(button(draw(),'전체 맵').props['aria-pressed']).toBe(true);
 button(nodes(draw()).find(n=>n.props?.['aria-label']==='선택 Context 상세'),'카드 열기').props.onClick();
 expect(button(draw(),'Persona 카드').props['aria-pressed']).toBe(true);
});
it.each([11,undefined])('RV4 uses context doc_count %s rather than cited trace count',count=>{
 h.data.cards.personas.P1.card.contexts=[{context_id:'C1',metrics:{doc_count:count}}];
 h.data.cards.personas.P1.trace=[{context_id:'C1',field:'state',evidence_id:'E1'}];
 button(draw(),'Persona 카드').props.onClick();
 expect(nodes(draw()).find(n=>n.type===CCMTable).props.contexts[0].cells.evidence_count.text).toBe(count===11?'11':'근거 부족');
});

it('RV5 manual hierarchy expansion survives an unrelated screen render',()=>{
 h.data.tree={id:'root',children:[{id:'CL0',name:'선택 클러스터',children:[{id:'P1'}]},{id:'CL1',name:'다른 클러스터',children:[{id:'P2',name:'다른 페르소나'}]}]};
 button(draw(),'Persona 카드').props.onClick();
 const first=nodes(draw()).find(n=>n.type===HierarchyTree);
 const screenSlots=h.cursor;
 h.cursor=screenSlots;let tree=HierarchyTree(first.props);
 const toggle=nodes(tree).find(n=>n.type==='button'&&text(n).includes('다른 클러스터'));
 expect(toggle.props['aria-expanded']).toBe(false);toggle.props.onClick();
 nodes(draw()).find(n=>n.type===OpportunityMap).props.onHighlight('C1');
 const next=nodes(draw()).find(n=>n.type===HierarchyTree);
 h.cursor=screenSlots;tree=HierarchyTree(next.props);
 expect(nodes(tree).find(n=>n.type==='button'&&text(n).includes('다른 클러스터')).props['aria-expanded']).toBe(true);
 expect(text(tree)).toContain('다른 페르소나');
});

it('RV6 shared ContextTable shows representative pain and wrapping fixed name column',()=>{
 h.data.cards.personas.P1.card.contexts=[{context_id:'C1',context_name:'아주 긴 상황 이름',pain_points:[{text:'대표 불편'}]}];
 const table=nodes(draw()).find(n=>n.type===ContextTable);expect(table).toBeTruthy();
 h.cursor=0;const rendered=ContextTable(table.props);
 expect(text(rendered)).toContain('대표 페인포인트');expect(text(rendered)).toContain('대표 불편');
 const cell=nodes(rendered).find(n=>n.type==='td'&&text(n)==='아주 긴 상황 이름');
 expect(cell.props.style).toMatchObject({width:180,minWidth:180,maxWidth:180,whiteSpace:'normal',overflowWrap:'anywhere'});
 const row=nodes(rendered).find(n=>n.type==='tr'&&text(n).includes('아주 긴 상황 이름')&&n.props.tabIndex===0);
 row.props.onClick();expect(button(draw(),'전체 맵').props['aria-pressed']).toBe(true);
});
