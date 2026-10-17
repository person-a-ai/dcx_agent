import { expect, it } from 'vitest';
import type { InsightContextView, InsightItem } from '@/lib/types';
import { dimLabel, personaShortLabels, radarMean, toInsightView } from './insightView';

const contexts: InsightContextView[] = [
 {context_id:'a',short:'C1',persona_id:'runner',persona_name:'귀로 건강 재는 러너',pain_point:'측정이 어렵다',odi:null,dim:null},
 {context_id:'b',short:'C9',persona_id:'pillow',persona_name:'편안한 베개',context_name:'잠들기',odi:0,axis:'Shared',dim:'Feel',counter:true},
 {context_id:'c',short:'C3',persona_id:'runner',persona_name:'귀로 건강 재는 러너',odi:2.5},
];
const item = (extra: Partial<InsightItem> = {}): InsightItem => ({id:'I1',title:'제목',pain_point:'문제',context_ids:['a','b','c'],known_ki_id:null,contexts,...extra});
it('new fields pass through', () => {
 const view = toInsightView(item({headline:'새 제목',statements:['원함','막힘'],hashtags:['건강','수면'],flow:[{context_id:'b',text:'쉬고 싶다'},{context_id:'a',text:'재고 싶다'}]}), {context_odi_mean:1,radar_mean:null});
 expect(view).toMatchObject({headline:'새 제목',statements:['원함','막힘'],hashtags:['건강','수면'],legacy:false});
 expect(view.flow.map(card=>[card.contextId,card.text])).toEqual([['b','쉬고 싶다'],['a','재고 싶다']]);
 expect(view.flow[0]).toMatchObject({label:'베개-C9',dim:'Feel',axis:'Shared',counter:true});
});
it('legacy fallback', () => {
 const view = toInsightView(item());
 expect(view).toMatchObject({headline:'제목',statements:['문제'],hashtags:[],legacy:true});
 expect(view.flow.map(card=>[card.contextId,card.text])).toEqual([['a','측정이 어렵다'],['b','잠들기'],['c','C3']]);
});
it('persona short label', () => {
 expect(personaShortLabels(contexts)).toEqual({runner:'러너',pillow:'베개'});
 expect(toInsightView(item()).flow[0].label).toBe('러너-C1');
});
it('persona short label collision', () => {
 const rows = [contexts[0],{context_id:'d',short:'C4',persona_id:'other',persona_name:'새벽 러너'}];
 expect(personaShortLabels(rows)).toEqual({runner:'귀로 건강 재는 러너',other:'새벽 러너'});
});
it('personas deduped in context order', () => {
 expect(toInsightView(item()).personas).toEqual(['귀로 건강 재는 러너','편안한 베개']);
});
it('bars keep null distinct from zero', () => {
 expect(toInsightView(item()).bars).toEqual(contexts.map(row=>({contextId:row.context_id,short:row.short,label:row.persona_id==='pillow'?'베개-C9':`러너-${row.short}`,value:row.odi})));
});
it('radarMean averages raw values and excludes missing values', () => {
 expect(radarMean([item({radar:{raw:{Computed:0,Connected:2,Shared:4}}}),item({radar:{raw:{Computed:2,Connected:4,Shared:6}}}),item()])).toEqual({Computed:1,Connected:3,Shared:5});
 expect(radarMean([item()])).toBeNull();
 expect(radarMean([])).toBeNull();
});
it('chips', () => {
 expect(toInsightView(item({context_ids:['a','b']})).chips).toEqual(['이 인사이트 문장을 더 짧게 다시 써줘','흐름에서 러너-C1과 베개-C9 순서를 바꿔줘']);
});
it('single context hides second chip', () => {
 expect(toInsightView(item({context_ids:['a']})).chips).toEqual(['이 인사이트 문장을 더 짧게 다시 써줘']);
});
it('dim null shows 근거 부족', () => {
 expect(toInsightView(item()).flow[0].dim).toBeNull();
 expect(dimLabel(null)).toBe('근거 부족');
 expect(dimLabel('Feel')).toBe('Feel');
});
it('missing contexts use short IDs without inventing evidence', () => {
 const view = toInsightView(item({contexts:undefined,context_ids:['C1']}));
 expect(view.flow).toEqual([{contextId:'C1',label:'C1',text:'C1',dim:null,axis:undefined,counter:false}]);
 expect(view.bars).toEqual([{contextId:'C1',short:'C1',label:'C1',value:null}]);
 expect(view.personas).toEqual([]);
});
it('radarMean leaves axes with no observations null and preserves observed zero',()=>{
 expect(radarMean([item({radar:{raw:{Computed:0,Connected:null,Shared:.6}}}),item({radar:{raw:{Computed:null,Connected:null,Shared:.2}}})])).toEqual({Computed:0,Connected:null,Shared:.4});
 expect(radarMean([item({radar:{raw:{Computed:null,Connected:null,Shared:null}}})])).toBeNull();
});

it.each([
 ['시니어-C1','과'],['생활관리자-C4','와'],['중장년-C3','과'],
 ['베개','와'],['건강','과'],
 ...Array.from('0123456789',(digit,index)=>[`C${digit}`,[0,1,3,6,7,8].includes(index)?'과':'와']),
 ['Label','와'],['기타!','와'],
])('QA ISSUE-003 chooses the particle for %s', (label,particle)=>{
 const view=toInsightView(item({context_ids:['first','last'],contexts:[{context_id:'first',short:label},{context_id:'last',short:'끝'}]}));
 expect(view.chips[1]).toBe(`흐름에서 ${label}${particle} 끝 순서를 바꿔줘`);
});
