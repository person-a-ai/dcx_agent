import { createElement as h } from 'react';
import { renderToStaticMarkup as render } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { expect, it } from 'vitest';
import { Radar, type RadarValues } from './Radar';
import { OpportunityBars } from './OpportunityBars';
import { InsightFlow } from './InsightFlow';
import type { BarRow, FlowCard } from './insightView';
const values: RadarValues = {Computed:{raw:.4,percentile:70},Connected:{raw:null,percentile:null},Shared:{raw:.8,percentile:90}};
const mean = {Computed:.3,Connected:.5,Shared:.7};
const radar = (average: typeof mean | null = null, data = values) => render(h(Radar,{values:data,mean:average,label:'Insight 2'}));
const rows: BarRow[] = [{contextId:'a',short:'C1',label:'러너-C1',value:null},{contextId:'b',short:'C2',label:'러너-C2',value:0}];
const bars = (data = rows, average: number | null = null) => render(h(OpportunityBars,{rows:data,mean:average}));
const card: FlowCard = {contextId:'a',label:'러너-C1',text:'재고 싶다',dim:null,axis:null,counter:false};
it('radar draws mean dashed polygon only when mean given',()=>{
 expect(radar(mean).match(/<polygon[^>]*stroke-dasharray/g)).toHaveLength(1);
 expect(radar(mean)).toContain('평균(전체 인사이트)');
 expect(radar()).not.toContain('stroke-dasharray'); expect(radar()).not.toContain('평균(전체 인사이트)');
});
it('radar empty state',()=>{expect(radar(null,Object.fromEntries(Object.keys(values).map(key=>[key,{raw:null,percentile:50}])) as RadarValues)).toContain('경험 차원 값이 없습니다');});
it('radar aria label has raw and percentile',()=>{
 expect(radar()).toMatch(/aria-label="[^"]*Computed: 원값 0.40, 백분위 70/);
 expect(radar()).toContain('<title>'); expect(radar()).toContain('Connected'); expect(radar()).toContain('—');
});
it('bars null and zero',()=>{
 const html = bars(); expect(html).toContain('값 없음'); expect(html.match(/class="insight-bar"/g)).toHaveLength(1); expect(html).toContain('height:0%');
 expect(html).toContain('러너-C1'); expect(html).toContain('role="img"');
 expect(html.indexOf('러너-C1')).toBeLessThan(html.lastIndexOf('러너-C2'));
});
it('bars mean line',()=>{expect(bars(rows,2.34)).toContain('평균 2.3');expect(bars(rows,0)).toContain('평균 0.0');expect(bars()).not.toContain('insight-bars-mean');});
it('bars all null',()=>{const html=bars([rows[0]],3);expect(html).toContain('이 인사이트의 Context에 ODI 값이 없습니다');expect(html).not.toContain('insight-bars-plot');expect(html).not.toContain('평균 3.0');});
it('flow ordered list with arrows',()=>{
 const html=render(h(InsightFlow,{cards:[card,{...card,contextId:'b'}]}));expect(html).toContain('<ol aria-label="Context 흐름"');expect(html.match(/→/g)).toHaveLength(1);
 expect(render(h(InsightFlow,{cards:[card]}))).not.toContain('→');
});
it('counter card',()=>{const html=render(h(InsightFlow,{cards:[{...card,counter:true}]}));expect(html).toContain('⚠ 반례');expect(html).toContain('insight-flow-card--counter');});
it('axis badge hidden when null and dim null shows 근거 부족',()=>{
 const html=render(h(InsightFlow,{cards:[card]}));expect(html).not.toContain('insight-axis-badge');expect(html).toContain('근거 부족');
 expect(render(h(InsightFlow,{cards:[{...card,axis:'Shared',dim:'Feel'}]}))).toContain('insight-axis-badge');
});
it('no hardcoded colors',()=>{for(const file of ['Radar.tsx','OpportunityBars.tsx','InsightFlow.tsx','insight.css']) expect(readFileSync(new URL(file,import.meta.url),'utf8')).not.toMatch(/#[0-9a-fA-F]{3,6}/);});
it('bars mean label is in the header outside bar columns',()=>{
 const html = bars([{...rows[1],value:2.34}],2.34);
 expect(html).toMatch(/<figcaption>Opportunity Score.*<span class="insight-bars-mean-label">평균 2.3<\/span><\/figcaption>/);
 const grid = html.slice(html.indexOf('class="insight-bars-grid"'));
 expect(grid).not.toContain('insight-bars-mean-label');
 expect(grid).not.toContain('>평균 2.3<');
});
it('bars aria summary matches visible formatted values and missing copy',()=>{
 const html = bars([rows[0],{...rows[1],value:2.3456}],1.234);
 expect(html).toContain('aria-label="러너-C1: 값 없음, 러너-C2: 2.3; 평균 1.2"');
 expect(html).toContain('class="insight-bar-value">2.3</span>');
});
it('partial radar mean omits polygon and announces the missing axis',()=>{
 const html = render(h(Radar,{values,mean:{Computed:.3,Connected:null,Shared:.7},label:'Insight 2'}));
 expect(html).not.toContain('stroke-dasharray');
 expect(html).toMatch(/aria-label="[^"]*Connected 평균 없음/);
 expect(html).not.toContain('--- 평균(전체 인사이트)');
});
it('radar legend uses the caption text color',()=>{
 const css = readFileSync(new URL('./insight.css',import.meta.url),'utf8');
 expect(css).toMatch(/\.insight-chart-legend\s*\{[^}]*color:\s*var\(--sub\)/);
});

it('bars scroll region is keyboard reachable and named',()=>{expect(bars()).toMatch(/tabindex="0" role="group" aria-label="[^"]+"/);});
it('bar labels clamp with full title',()=>{const html=bars();expect(html).toContain('class="insight-bar-short" title="C1"');expect(html).toContain('class="insight-clamp-2" title="러너-C1"');});
it('charts show provisional badges',()=>{expect(radar()).toContain('잠정');expect(bars()).toContain('잠정');});
