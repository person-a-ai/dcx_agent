/* eslint-disable @typescript-eslint/no-explicit-any */
import {beforeEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
const h=vi.hoisted(()=>({cursor:0,values:[] as any[],effects:[] as any[]}));
vi.mock('react',async original=>({...await original<typeof import('react')>(),useState:(initial:any)=>{const i=h.cursor++;if(!(i in h.values))h.values[i]=initial;return [h.values[i],(v:any)=>{h.values[i]=typeof v==='function'?v(h.values[i]):v;}];},useRef:()=>({current:false}),useEffect:(f:any)=>{h.effects.push(f);}}));
vi.mock('../versions/VersionProvider',()=>({useVersion:()=>({refreshSessionAfterStage:vi.fn()})}));
vi.mock('../versions/useStageCompletionRefresh',()=>({useStageCompletionRefresh:vi.fn()}));
vi.mock('@/lib/api/insight',()=>({getInsights:vi.fn(),startInsight:vi.fn().mockResolvedValue({runId:'fresh'}),chatInsight:vi.fn().mockResolvedValue({ok:false})}));
import * as api from '@/lib/api/insight';
import {OpportunityBars} from './OpportunityBars';
import {InsightScreen} from './InsightScreen';
import {InsightHeader} from './InsightHeader';
import {InsightTopBar} from './InsightTopBar';
import {InsightChatBar} from './InsightChatBar';
import {Radar} from './Radar';
function nodes(n:any):any[]{return !n||typeof n!=='object'?[]:Array.isArray(n)?n.flatMap(nodes):[n,...nodes(n.props?.children)];}
function text(n:any):string{return typeof n==='string'?n:Array.isArray(n)?n.map(text).join(''):n?.props?text(n.props.children):'';}
const item=(id:string,value=0)=>({id,title:id,pain_point:'문제',context_ids:['C1'],known_ki_id:null,radar:{raw:{Computed:value,Connected:value,Shared:value}}});
let data:any;
const draw=()=>{h.cursor=0;h.effects=[];return InsightScreen({sid:'s',version:'v2'});};
const props=(type:any)=>nodes(draw()).find(n=>n.type===type)?.props;
beforeEach(()=>{vi.clearAllMocks();data={insights:{revision:2,items:[item('I1'),item('I2'),item('I3')],history:[]},concepts:{revision:0,items:[],history:[]},bars:{targets:['I2']},summary:{context_odi_mean:0,radar_mean:{Computed:9,Connected:9,Shared:9}},worker:{status:'idle'}};h.values=[data,[],'I2','insight:I2',null,false,'',0,null];});
it('renders one insight at a time',()=>{expect(nodes(draw()).filter(n=>n.type===InsightHeader)).toHaveLength(1);expect(props(InsightTopBar).index).toBe(1);});
it('selected insight removed falls back to first',()=>{data.insights.items=[item('I1'),item('I3')];expect(props(InsightHeader).view.headline).toBe('I1');});
it('preview disables confirm and chat but keeps pager',()=>{data.insights.history=[{revision:1,items:[item('old'),item('older')]}];h.values[4]=1;expect(props(InsightTopBar).count).toBe(2);expect(props(InsightTopBar).confirmDisabled).toBe(true);expect(props(InsightChatBar).disabled).toBe(true);props(InsightTopBar).onNext();expect(props(InsightHeader).view.headline).toBe('older');});
it('preview uses viewed revision radar mean',()=>{data.insights.history=[{revision:1,items:[item('old',2),item('older',4)]}];h.values[4]=1;expect(props(Radar).mean).toEqual({Computed:3,Connected:3,Shared:3});h.values[4]=null;expect(props(Radar).mean).toEqual(data.summary.radar_mean);});
it('rederive starts fresh run',async()=>{await props(InsightHeader).onRederive();expect(api.startInsight).toHaveBeenCalledWith('s',{mode:'derive',fresh:true},'v2');expect(h.values[8]).toEqual({runId:'fresh',mode:'derive'});expect(props(InsightHeader).rederiveDisabled).toBe(true);});
it('chat default target is current insight',async()=>{h.values[3]='';expect(props(InsightChatBar).target).toBe('insight:I2');props(InsightTopBar).onNext();expect(props(InsightChatBar).target).toBe('insight:I3');expect(props(InsightChatBar).focusId).toBe('I3');await props(InsightChatBar).onSend('m');expect(api.chatInsight).toHaveBeenCalledWith('s',{target:'insight:I3',message:'m'},'v2');});
it('list target sends focus id',async()=>{props(InsightChatBar).onTarget('insights');props(InsightTopBar).onNext();expect(props(InsightChatBar).target).toBe('insights');await props(InsightChatBar).onSend('m');expect(api.chatInsight).toHaveBeenCalledWith('s',{target:'insights',message:'m',focus_id:'I3'},'v2');});
it.each([null,'r1'])('QA-F2 shows concept failure with a pending launch and runId %s',runId=>{data.worker={status:'failed',mode:'concept',target:'I2',reason:'실패',runId};h.values[8]={runId:'r1',mode:'concept',target:'I2'};expect(nodes(draw()).filter(n=>n.props?.role==='alert').map(text).join('')).toContain('컨셉을 만들지 못했습니다. 다시 시도하세요.');});
it('keeps missing ODI distinct from a measured zero',()=>{data.insights.items[1].contexts=[{context_id:'C1',short:'C1',odi:null},{context_id:'C2',short:'C2',odi:0}];data.insights.items[1].context_ids=['C1','C2'];const bars=props(OpportunityBars);expect(bars.rows.map((b:any)=>b.value)).toEqual([null,0]);const rendered=OpportunityBars(bars);const elements=nodes(rendered).filter(n=>n.props?.className==='insight-bar');expect(elements).toHaveLength(1);expect(elements[0].props.style.height).toBe('0%');expect(text(rendered)).toContain('값 없음');});
it('css uses tokens only',()=>{const css=readFileSync('src/components/persona/insight.css','utf8');expect(css).not.toMatch(/#[\da-f]{3,8}\b/i);expect(css).toMatch(/\.insight-hit\s*\{[^}]*min-width:\s*44px;[^}]*min-height:\s*44px/);expect(css).toMatch(/\.insight-charts\s*\{[^}]*height:\s*240px/);expect(css).toMatch(/\.insight-clamp-2\s*\{[^}]*-webkit-line-clamp:\s*2/);});
it.each([
 {targets:['I3'],defaultId:'I2',expected:2},
 {targets:[],defaultId:'I2',expected:1},
 {targets:[],defaultId:null,expected:0},
])('initial selection follows targets then default then first: $expected',async({targets,defaultId,expected})=>{
 data.bars.targets=targets;
 data.insights.items.forEach((row:any)=>{row.default_target=row.id===defaultId;});
 vi.mocked(api.getInsights).mockResolvedValueOnce(data);
 h.values=[];draw();const cleanup=h.effects[0]();await Promise.resolve();
 expect(props(InsightTopBar).index).toBe(expected);
 expect(props(InsightChatBar).target).toBe(`insight:${data.insights.items[expected].id}`);
 cleanup();
});
it.each(['readonly','busy','pending','running','preview'])('rederive is disabled during %s',async state=>{
 if(state==='busy')h.values[5]=true;
 if(state==='pending')h.values[8]={runId:'r1',mode:'derive'};
 if(state==='running')data.worker.status='running';
 if(state==='preview'){data.insights.history=[{revision:1,items:[item('old')]}];h.values[4]=1;}
 h.cursor=0;
 const header=nodes(InsightScreen({sid:'s',version:'v2',readonly:state==='readonly'})).find(n=>n.type===InsightHeader);
 expect(header.props.rederiveDisabled).toBe(true);
 await header.props.onRederive();
 expect(api.startInsight).not.toHaveBeenCalled();
});
it.each([false,true,null])('concept paging follows selection or falls back (outdated %s)',outdated=>{
 h.values[3]='concept:I2';data.concepts.items=outdated===null?[]:[{insight_id:'I3',outdated}];props(InsightTopBar).onNext();
 expect(props(InsightChatBar).target).toBe(outdated===false?'concept:I3':'insight:I3');
 expect(props(InsightChatBar).focusId).toBe('I3');
 expect(h.values[3]).toBe(outdated===false?'concept:I3':'insight:I3');
 expect(props(InsightChatBar).revisions.currentRevision).toBe(outdated===false?0:2);
});
it('retry resends fresh worker flag',async()=>{
 data.worker={status:'interrupted',mode:'derive',fresh:true};
 const button=nodes(draw()).find(n=>text(n)==='이어서 진행' && n.props?.onClick);
 await button.props.onClick();
 expect(api.startInsight).toHaveBeenCalledWith('s',{mode:'derive',fresh:true},'v2');
});
