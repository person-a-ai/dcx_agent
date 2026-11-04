import { createElement, isValidElement, type ReactElement, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it, vi } from 'vitest';
import { GradeMark } from './GradeMark';
import { ProvisionalBadge } from './ProvisionalBadge';
import { CCMTable, type CCMContext } from './CCMTable';
import { OpportunityMap } from './OpportunityMap';
import { MAP_TICKS } from './personaView';
import { ContextTable } from './ContextTable';
import { HierarchyTree } from './HierarchyTree';
import { Radar } from './Radar';
import { OpportunityBars } from './OpportunityBars';
import { JourneyTable } from './JourneyTable';
import { RevisionList } from './RevisionList';
import type { PersonaContextRow, PersonaMap } from '../../lib/types';

// Node-only interaction harness, matching segment's direct element-handler tests.
const state = vi.hoisted(() => ({ values: [] as unknown[], cursor: 0 }));
vi.mock('react', async importOriginal => ({ ...await importOriginal<typeof import('react')>(), useId: () => 'test-id', useState: (initial: unknown) => {
  const index = state.cursor++;
  if (!(index in state.values)) state.values[index] = initial;
  return [state.values[index], (next: unknown) => { state.values[index] = typeof next === 'function' ? next(state.values[index]) : next; }];
} }));
function draw<T>(component: (props: T) => ReactElement, props: T, reset = true) {
  state.cursor = 0; if (reset) state.values = []; return component(props);
}
function nodes(node: ReactNode, match: (e: ReactElement<Record<string, unknown>>) => boolean): ReactElement<Record<string, unknown>>[] {
  if (Array.isArray(node)) return node.flatMap(n => nodes(n, match));
  if (!isValidElement<Record<string, unknown>>(node)) return [];
  return [...(match(node) ? [node] : []), ...nodes(node.props.children as ReactNode, match)];
}
const html = (node: ReactNode) => renderToStaticMarkup(node);
const point = (id: string, odi = 1): PersonaContextRow => ({ context_id: id, name: `이름 ${id}`, persona_id: 'P1', cluster_id: 'CL1', i: .5, s: .5, odi, zone: 'B', star: true, counter: false, shape: 'circle', tone: 0 });
const map = (points: PersonaContextRow[]): PersonaMap => ({ points, base: { s_line: .5, diag1: [[0,.4],[1,1]], diag2: [[.6,0],[1,1]] }, legend: [...new Set(points.map(p=>p.cluster_id))].map((cluster_id,index)=>({cluster_id,shape:['circle','square','triangle','diamond','pentagon'][index] ?? 'circle',cluster_label:index>=5?cluster_id:null,personas:[...new Set(points.filter(p=>p.cluster_id===cluster_id).map(p=>p.persona_id))].map((persona_id,n)=>({persona_id,persona_name:persona_id,tone:['--ink-strong','--ink','--line-strong'][n%3]}))})) });
const contexts: CCMContext[] = Array.from({ length: 10 }, (_, n) => ({ id: `C${n}`, name: '긴Context이름'.repeat(20), counter: n === 9, cells: { action: { text: '긴문자'.repeat(50), grade: 'observed', evidence: '근거 원문' } } }));

it('renders grades with distinct shapes and text, including missing evidence and provisional copy', () => {
  for (const [grade, symbol, label] of [['observed','●','관측'],['inferred','▲','추론'],['speculated','✕','추측']] as const) {
    const out = html(createElement(GradeMark, { grade })); expect(out).toContain(symbol); expect(out).toContain(label);
  }
  expect(html(createElement(GradeMark, { grade: null }))).toContain('근거 부족');
  expect(html(createElement(ProvisionalBadge))).toContain('잠정');
});
it('test_ccm_ten_columns_fold_no_overflow', () => {
  const out = html(draw(CCMTable, { contexts }));
  expect(out.match(/<table/g)).toHaveLength(2);
  expect(out.match(/table-layout:fixed/g)).toHaveLength(2);
  expect(out).toContain('overflow-wrap:anywhere'); expect(out).toContain('width:100%');
  expect(out.match(/scope="col"/g)).toHaveLength(12); expect(out).toContain('반례');
});
it('opens and closes cell evidence with native keyboard button activation and aria-expanded', () => {
  const props = { contexts: contexts.slice(0,1) };
  let tree = draw(CCMTable, props);
  let button = nodes(tree, e => e.type === 'button')[0];
  expect(button.props['aria-expanded']).toBe(false); expect(button.props.type).toBe('button');
  // Native buttons dispatch click for both Enter and Space; no duplicate key handlers.
  for (const key of ['Enter', ' ']) {
    (button.props.onClick as () => void)(); tree = draw(CCMTable, props, false);
    button = nodes(tree, e => e.type === 'button')[0];
    expect(button.props['aria-expanded']).toBe(key === 'Enter');
    expect(button.props['aria-controls']).toBeTruthy();
  }
});
it('sorts opportunity descending by default and toggles sortable headers', () => {
  const props = { rows: [point('C1',1),point('C2',3)], onOpenCard: vi.fn() };
  let tree = draw(ContextTable, props); expect(html(tree).indexOf('이름 C2')).toBeLessThan(html(tree).indexOf('이름 C1'));
  const header = nodes(tree, e => e.type === 'button' && e.props.children === '기회')[0];
  (header.props.onClick as () => void)(); tree = draw(ContextTable, props, false);
  expect(html(tree)).toContain('aria-sort="ascending"'); expect(html(tree).indexOf('이름 C1')).toBeLessThan(html(tree).indexOf('이름 C2'));
  expect(nodes(tree, e => e.type === 'th' && !!e.props['aria-sort'])).toHaveLength(8);
});
it('synchronizes row focus/hover and map click through shared highlightedId', () => {
  const onHighlight = vi.fn(), onOpenCard = vi.fn();
  const rows = [point('C1')]; const props = { rows, onHighlight, onOpenCard, highlightedId: 'C1' };
  const tree = draw(ContextTable, props); const row = nodes(tree, e => e.type === 'tr' && e.props.tabIndex === 0)[0];
  (row.props.onFocus as () => void)(); (row.props.onMouseEnter as () => void)(); expect(onHighlight).toHaveBeenLastCalledWith('C1');
  expect(row.props['data-highlighted']).toBe(true);
  const chart = draw(OpportunityMap, { map: map(rows), highlightedId: 'C1', onHighlight });
  const dot = nodes(chart, e => e.props['data-context-id'] === 'C1')[0];
  (dot.props.onClick as () => void)(); expect(onHighlight).toHaveBeenLastCalledWith('C1'); expect(dot.props['data-highlighted']).toBe(true);
  const stopPropagation=vi.fn();
  (nodes(tree, e => e.props.children === '카드 열기')[0].props.onClick as (event: {stopPropagation:()=>void}) => void)({stopPropagation});expect(stopPropagation).toHaveBeenCalledOnce(); expect(onOpenCard).toHaveBeenCalledWith('P1', 'C1');
});
it('test_overlapping_points_table_lists_all', () => {
  const rows = [point('C1'), point('C2')];
  const out = html(draw(OpportunityMap, { map: map(rows) }));
  expect(out).toContain('겹친 Context 2개'); expect(new Set(nodes(draw(OpportunityMap, { map: map(rows) }), e => !!e.props['data-context-id']).map(e => e.props.transform)).size).toBe(2);
  expect(out).toContain('role="img"'); expect(out).toContain('B Experiencing 2개');
  const table = html(draw(ContextTable, { rows, onOpenCard: vi.fn() })); for (const row of rows) expect(table).toContain(row.name);
});
it('renders cluster shapes, hollow counters, stars, baselines and toggling legend chips', () => {
  const points = Array.from({length: 6}, (_,n) => ({...point(`C${n}`), cluster_id: `CL${n}`, persona_id: `P${n}`, counter: true}));
  const props = { map: map(points) }; let tree = draw(OpportunityMap, props); const out = html(tree);
  for (const shape of ['circle','square','triangle','diamond','pentagon']) expect(out).toContain(`data-shape="${shape}"`);
  expect(out).toContain('fill="none"'); expect(out).toContain('★'); expect(out).toContain('CL5'); expect(out.match(/data-baseline=/g)).toHaveLength(3);
  const chip = nodes(tree, e => e.type === 'button' && e.props['data-cluster'] === 'CL0')[0];
  (chip.props.onClick as () => void)(); tree = draw(OpportunityMap, props, false); expect(nodes(tree, e => e.props['data-context-id'] === 'C0')).toHaveLength(0);
  expect(nodes(tree, e => e.props['data-cluster'] === 'CL0')[0].props['aria-pressed']).toBe(false);
});
it('renders hierarchy sizes, radar raw and percentile, bars mean, journey distribution and revisions', () => {
  expect(html(createElement(HierarchyTree, { root: { id:'product', name:'제품', doc_count:10, children:[{id:'CL1',name:'Cluster',doc_count:4}] } }))).toContain('문서 10건');
  const radar = html(createElement(Radar, { mean:null, label:'Insight 1', values: { Computed:{raw:.4,percentile:80}, Connected:{raw:.3,percentile:50}, Shared:{raw:.2,percentile:10} } }));
  for (const word of ['Computed','Connected','Shared','0.40','80']) expect(radar).toContain(word);
  expect(html(createElement(OpportunityBars, { rows:[{contextId:'C1',short:'C1',label:'인사이트',value:2}], mean:1 }))).toContain('평균 1');
  const journey = html(createElement(JourneyTable, { rows:[{context_id:'C1',action:'행동',feeling:'감정',service:'서비스',service_action:'처방행동',cx_4d:'정신적'}] }));
  for (const word of ['AS-IS','TO-BE','⚪','처방','정신적 1','물리적 0','문화적 0','시스템 0']) expect(journey).toContain(word);
  const onView=vi.fn(), onRevert=vi.fn(); const tree=RevisionList({ revisions:[{revision:1,message:'초안'}], currentRevision:2,onView,onRevert });
  const buttons=nodes(tree,e=>e.type==='button'); (buttons[0].props.onClick as ()=>void)(); (buttons[1].props.onClick as ()=>void)();
  expect(onView).toHaveBeenCalledWith(1); expect(onRevert).toHaveBeenCalledWith(1); expect(html(tree)).toContain('이 판으로 되돌리기');
});

it.each([[0,0],[4,1],[5,2],[8,2],[9,2],[10,2]])('folds %i contexts into %i tables without dropping columns', (count,tables) => {
  const out = html(draw(CCMTable,{contexts:contexts.slice(0,count)}));
  expect(out.match(/<table/g) || []).toHaveLength(tables);
  expect(out.match(/scope="col"/g) || []).toHaveLength(count + tables);
  if (!count) expect(out).toContain('Context가 없습니다.');
});
it('shows evidence only while expanded and associates the button with its panel', () => {
  const props = {contexts:contexts.slice(0,1)};
  let tree=draw(CCMTable,props); const button=nodes(tree,e=>e.type==='button')[0];
  expect(html(tree)).not.toContain('근거 원문');
  (button.props.onClick as ()=>void)(); tree=draw(CCMTable,props,false);
  const panel=nodes(tree,e=>e.props.id===`${button.props['aria-controls']}`)[0];
  expect(panel.props.hidden).toBe(false); expect(panel.props.children).toBe('근거 원문');
});
it('uses backend persona tones and toggles visibility', () => {
  const points=Array.from({length:4},(_,n)=>({...point(`C${n}`),persona_id:`P${n}`}));
  const props={map:map(points)}; let tree=draw(OpportunityMap,props);
  for (const tone of ['--ink-strong','--ink','--line-strong']) expect(html(tree)).toContain(`var(${tone})`);
  expect(html(tree)).not.toContain('var(--blue)');
  const chip=()=>nodes(tree,e=>e.props['data-cluster']==='CL1')[0];
  (chip().props.onClick as ()=>void)(); tree=draw(OpportunityMap,props,false);
  expect(chip().props['aria-pressed']).toBe(false);
  expect(nodes(tree,e=>e.props['data-context-id']==='C0')).toHaveLength(0);
  (chip().props.onClick as ()=>void)(); tree=draw(OpportunityMap,props,false);
  expect(chip().props['aria-pressed']).toBe(true); expect(nodes(tree,e=>e.props['data-context-id']==='C0')).toHaveLength(1);
});
it('toggles a whole cluster and marks an externally selected persona blue', () => {
  const props={map:map([point('C1')])}; let tree=draw(OpportunityMap,props);
  const cluster=nodes(tree,e=>e.type==='button')[0]; (cluster.props.onClick as ()=>void)();
  tree=draw(OpportunityMap,props,false); expect(nodes(tree,e=>e.type==='button').every(e=>!e.props['aria-pressed'])).toBe(true);
  expect(html(draw(OpportunityMap,{...props,selectedPersonaId:'P1'}))).toContain('var(--blue)');
});
it('sorts every Context column using the shared sorter without mutating input', () => {
  const rows=[{...point('B',1),name:'가',persona_name:'가',i:.1,s:.9,zone:'A' as const,star:false},{...point('A',2),name:'나',persona_name:'나',i:.9,s:.1,zone:'F' as const,star:true}];
  const original=JSON.stringify(rows);
  for (const label of ['ID','이름','Persona','중요도','만족도','기회','구역','★']) {
    const props={rows,onOpenCard:vi.fn()}; let tree=draw(ContextTable,props);
    (nodes(tree,e=>e.type==='button'&&e.props.children===label)[0].props.onClick as ()=>void)();
    tree=draw(ContextTable,props,false);
    expect(nodes(tree,e=>e.type==='th'&&e.props['aria-sort']!=='none'&&!!e.props['aria-sort'])).toHaveLength(1);
  }
  expect(JSON.stringify(rows)).toBe(original);
});
it('renders empty charts and missing metrics without invalid coordinates', () => {
  const outputs=[html(draw(OpportunityMap,{map:map([])})),html(createElement(OpportunityBars,{rows:[],mean:null})),html(createElement(Radar,{mean:null,label:'Insight 1',values:{Computed:{raw:null,percentile:null},Connected:{raw:0,percentile:0},Shared:{raw:1,percentile:100}}})),html(createElement(JourneyTable,{rows:[]}))];
  outputs.forEach(out=>expect(out).not.toMatch(/NaN|Infinity/));
});
it('keeps ten journey Contexts in fixed-width rows and shows all four distribution buckets', () => {
  const rows=Array.from({length:10},(_,n)=>({context_id:`C${n}`,action:'a'.repeat(200),feeling:'감정',service:'서비스',service_action:'행동',cx_4d:'문화적' as const}));
  const out=html(createElement(JourneyTable,{rows}));
  expect(out.match(/scope="row"/g)).toHaveLength(10); expect(out).toContain('문화적 10'); expect(out).toContain('table-layout:fixed');
});
it('disables reverting the current revision and all revision actions while busy', () => {
  const props={revisions:[{revision:1}],currentRevision:1,onView:vi.fn(),onRevert:vi.fn()};
  expect(nodes(RevisionList(props),e=>e.type==='button')[1].props.disabled).toBe(true);
  expect(nodes(RevisionList({...props,busy:true}),e=>e.type==='button').every(e=>e.props.disabled)).toBe(true);
});

it('keeps hover emphasis neutral, reserves blue for selected personas, and labels all map zones', () => {
  const props = { map: map([point('C1')]), highlightedId: 'C1' };
  const tree = draw(OpportunityMap, props);
  const dot = nodes(tree, e => e.props['data-context-id'] === 'C1')[0];
  expect(dot.props.stroke).toBe('var(--ink-strong)');
  const labels = html(tree);
  for (const label of ['A Exciting', 'B Experiencing', 'C Competitive', 'D Forgiven', 'E Dangling', 'F At-risk']) expect(labels).toContain(label);
  const selected = draw(OpportunityMap, { ...props, selectedPersonaId: 'P1' });
  expect(nodes(selected, e => e.props['data-context-id'] === 'C1')[0].props.stroke).toBe('var(--blue)');
});

it('folds long journeys into two tables while preserving mockup rows and all four dimensions', () => {
  const rows = Array.from({length:10}, (_,i) => ({context_id:`C${i}`,action:'긴행동'.repeat(40),feeling:'느낌',service:'서비스',service_action:'바뀐 행동',cx_4d:'정신적' as const}));
  const tree = JourneyTable({rows});
  expect(nodes(tree,e=>e.type==='table')).toHaveLength(2);
  expect(nodes(tree,e=>e.type==='th' && e.props.scope==='row')).toHaveLength(10);
  expect(html(tree)).toContain('overflow-wrap:anywhere');
  expect(html(tree)).toContain('정신적 10');
});

it('keeps Context order without changing inputs and labels the mean independently of color', () => {
  const rows = [{contextId:'low',short:'C1',label:'낮음',value:.5},{contextId:'high',short:'C2',label:'높음',value:2}];
  const original = JSON.stringify(rows);
  const tree = OpportunityBars({rows,mean:1});
  const out = html(tree);
  expect(out.indexOf('낮음')).toBeLessThan(out.indexOf('높음'));
  expect(JSON.stringify(rows)).toBe(original);
  expect(nodes(tree,e=>e.type==='svg')).toHaveLength(0);
  const columns = nodes(tree,e=>e.props.className==='insight-bars-column');
  expect(columns).toHaveLength(2);
  columns.forEach(column => {
    expect(nodes(column,e=>e.props.className==='insight-bar-slot')).toHaveLength(1);
    expect(nodes(column,e=>e.props.className==='insight-bar-label')).toHaveLength(1);
  });
  const average = nodes(tree,e=>e.props.className==='insight-bars-mean');
  expect(average).toHaveLength(1);
  expect(nodes(tree,e=>e.type==='figcaption').map(html).join('')).toContain('평균 1.0');
  expect(out).toContain('평균 1.0');
  expect(html(OpportunityBars({rows:[],mean:null}))).toContain('이 인사이트의 Context에 ODI 값이 없습니다');
});

it('keeps exact radar axes, missing values, and distinct raw/mean encodings', () => {
  const tree = Radar({mean:{Computed:.3,Connected:.2,Shared:.1},label:'Insight 1',values:{Computed:{raw:.4,percentile:80},Connected:{raw:null,percentile:null},Shared:{raw:0,percentile:0}}});
  const out = html(tree);
  for (const label of ['Computed','Connected','Shared','원값 —','백분위 80','— Insight 1','평균(전체 인사이트)']) expect(out).toContain(label);
  expect(nodes(tree,e=>e.type==='svg')[0].props.role).toBe('img');
  expect(out).not.toMatch(/NaN|Infinity/);
  const polygons = nodes(tree,e=>e.type==='polygon');
  expect(polygons.filter(e=>e.props.strokeDasharray)).toHaveLength(1);
  expect(polygons.find(e=>e.props.stroke==='var(--action)')?.props.strokeDasharray).toBeUndefined();
});

it('disables revision actions while busy and prevents reverting the current revision', () => {
  const props = {revisions:[{revision:1},{revision:2}],currentRevision:2,onView:vi.fn(),onRevert:vi.fn()};
  const tree = RevisionList(props);
  expect(nodes(tree,e=>e.type==='li' && e.props['aria-current']==='true')).toHaveLength(1);
  expect(nodes(tree,e=>e.type==='button').map(e=>e.props.disabled)).toEqual([false,false,false,true]);
  expect(nodes(RevisionList({...props,busy:true}),e=>e.type==='button').every(e=>e.props.disabled)).toBe(true);
  expect(html(RevisionList({...props,revisions:[]}))).toContain('저장된 판이 없습니다.');
});

it('opens actual CCM evidence and closes the previous cell with matching disclosure targets', () => {
  const props = {contexts:contexts.slice(0,2)};
  let tree = draw(CCMTable,props);
  (nodes(tree,e=>e.type==='button')[0].props.onClick as ()=>void)();
  tree = draw(CCMTable,props,false);
  const first = nodes(tree,e=>e.type==='button')[0];
  expect(nodes(tree,e=>e.props.id===first.props['aria-controls'])[0].props.hidden).toBe(false);
  expect(html(tree)).toContain('근거 원문');
  (nodes(tree,e=>e.type==='button')[1].props.onClick as ()=>void)();
  tree = draw(CCMTable,props,false);
  expect(nodes(tree,e=>e.type==='button' && e.props['aria-expanded']===true)).toHaveLength(1);
  expect(nodes(tree,e=>e.type==='button')[0].props['aria-expanded']).toBe(false);
});


it('renders six token-colored zone polygons with names in the outside legend', () => {
  const tree = draw(OpportunityMap, {map: map([point('C1')])});
  const out = html(tree);
  const regions = out.match(/<polygon data-zone="[A-F]"[^>]*>/g) ?? [];
  expect(regions).toHaveLength(6);
  for (const zone of ['A','B','C','D','E','F']) {
    expect(regions.find(region => region.includes(`data-zone="${zone}"`))).toContain(`fill="var(--${zone === 'F' ? 'danger-soft' : zone === 'C' ? 'warning-soft' : 'sunken'})"`);
    const label = out.match(new RegExp(`<li data-zone-name="${zone}"[^>]*>`))?.[0];
    expect(label).toContain(`color:var(--${zone === 'F' ? 'danger' : zone === 'C' ? 'warning' : 'sub'})`);
  }
});
it('uses linear ticks, responsive dimensions and straight dashed baselines', () => {
  const tree = draw(OpportunityMap, {map: map([point('C1')]), compact: true});
  const svg = nodes(tree, e => e.type === 'svg')[0];
  expect(svg.props.viewBox).toBe('0 0 600 420');
  expect(svg.props.style).toMatchObject({minHeight: 320});
  const ticks = nodes(tree, e => e.type === 'text' && !!e.props['data-axis-tick']);
  expect(ticks.map(e => e.props.children)).toEqual([...MAP_TICKS, ...MAP_TICKS]);
  expect(html(tree)).not.toContain('로그 척도');
  expect(ticks.some(e => String(e.props.children) === '10')).toBe(false);
  for (const line of nodes(tree, e => e.props['data-baseline'] !== undefined)) {
    expect(line.type).toBe('polyline');
    expect(line.props.points.split(' ')).toHaveLength(2);
    expect(line.props.stroke).toBe('var(--line-strong)');
    expect(line.props.strokeDasharray).toBeTruthy();
  }
  const dot = nodes(tree, e => e.props['data-context-id'] === 'C1')[0];
  expect(dot.props.transform).toBe(`translate(${60 + .5*480} ${340-.5*320})`);
});
it.each([[-1, 2, 'translate(60 20)'], [2, -1, 'translate(540 340)']])('clamps linear map coordinates (%s, %s)', (i, s, transform) => {
  const tree = draw(OpportunityMap, {map: map([{...point('C1'), i: Number(i), s: Number(s)}])});
  expect(nodes(tree, e => e.props['data-context-id'] === 'C1')[0].props.transform).toBe(transform);
});
it('RV2 labels focused and highlighted points and dims other personas in focus mode', () => {
  const props = {map: map([point('C1'), {...point('C2'), persona_id:'P2'}]), focusPersonaId:'P1', selectedPersonaId:'P1'};
  expect(nodes(draw(OpportunityMap, props), e => e.type === 'text' && !!e.props['data-label'])).toHaveLength(1);
  const tree = draw(OpportunityMap, {...props, highlightedId:'C2'});
  expect(nodes(tree, e => e.type === 'text' && !!e.props['data-label']).map(e => e.props.children)).toEqual(['C1','C2']);
  expect(nodes(tree, e => !!e.props['data-context-id']).map(e => e.props.opacity)).toEqual([1,.25]);
});
it('uses cluster-only legend buttons and toggles all cluster members', () => {
  const props = {map: map([point('C1'), {...point('C2'),persona_id:'P2'}, {...point('C3'),cluster_id:'CL2'}])};
  let tree = draw(OpportunityMap,props);
  expect(nodes(tree,e=>e.type==='button')).toHaveLength(2);
  const click = nodes(tree,e=>e.type==='button')[0].props.onClick as ()=>void;
  click(); tree=draw(OpportunityMap,props,false);
  expect(nodes(tree,e=>!!e.props['data-context-id']).map(e=>e.props['data-context-id'])).toEqual(['C3']);
  (nodes(tree,e=>e.type==='button')[0].props.onClick as ()=>void)();
  expect(nodes(draw(OpportunityMap,props,false),e=>!!e.props['data-context-id'])).toHaveLength(3);
});
it('omits null coordinates, explains missing contexts and preserves raw tooltip metrics', () => {
  const tree=draw(OpportunityMap,{map:map([{...point('C1'),i:null},{...point('C2'),s:null},{...point('C3'),i:.02,s:.1,odi:.32}])});
  expect(nodes(tree,e=>!!e.props['data-context-id']).map(e=>e.props['data-context-id'])).toEqual(['C3']);
  expect(html(tree)).toContain('지도에 없는 Context 2개는 표에서 확인하세요.');
  const title=html(nodes(tree,e=>e.type==='title')[0]);
  for(const value of ['중요도 0.02','만족도 0.10','기회 0.32']) expect(title).toContain(value);
  expect(html(draw(OpportunityMap,{map:map([])}))).toContain('기회 지도를 만들 Context가 없습니다.');
});

// T5: list selection, responsive contracts and primary Pain Points summary (R6).
import { readFileSync } from 'node:fs';
import { PersonaList } from './PersonaList';
import { PersonaSummary } from './PersonaSummary';
const summaryProps = { name:'긴 이름', future:true, meta:'근거 4 · Context 2', desire:'쉬고 싶다', goals:['목표 하나','목표 둘'], legacy:false, onOpenEvidence:vi.fn() };
const pains = [0,1,2].map(n=>({text:`불편 ${n}`, grade:n ? 'inferred' as const : 'observed' as const, context_ids:['C1','C2'], cite:['E1','E2']}));
it('renders grouped desktop/mobile personas, full names, statuses and selection callbacks', () => {
  const onSelect=vi.fn();
  const groups=[{clusterId:'CL1',items:[{id:'P1',name:'긴 이름'.repeat(40),status:'done' as const,future:true},{id:'P2',name:'생성 중',status:'running' as const}]},{clusterId:'CL2',items:[{id:'P3',name:'오류',status:'failed' as const},{id:'P4',name:'대기',status:'pending' as const}]}];
  const tree=PersonaList({groups,selectedId:'P1',onSelect});
  expect(nodes(tree,e=>e.type==='optgroup').map(e=>e.props.label)).toEqual(['CL1','CL2']);
  expect(nodes(tree,e=>e.props['aria-current']==='true')).toHaveLength(1);
  expect(nodes(tree,e=>e.props.className==='persona-name')[0].props.title).toBe(groups[0].items[0].name);
  for(const label of ['완료','진행 중','실패','대기','FUTURE']) expect(html(tree)).toContain(label);
  (nodes(tree,e=>e.type==='button')[1].props.onClick as ()=>void)();
  (nodes(tree,e=>e.type==='select')[0].props.onChange as (e:unknown)=>void)({target:{value:'P3'}});
  expect(onSelect.mock.calls).toEqual([['P2'],['P3']]);
  expect(html(PersonaList({groups:[],selectedId:null,onSelect}))).toContain('아직 확정된 페르소나가 없습니다.');
});
it('renders numbered primary pains with grades, contexts, evidence counts and index callbacks', () => {
  const onOpenEvidence=vi.fn(); const tree=draw(PersonaSummary,{...summaryProps,painPoints:pains,onOpenEvidence});
  expect(nodes(tree,e=>e.type==='ol')).toHaveLength(1);
  expect(nodes(tree,e=>e.type==='li')).toHaveLength(3);
  for(const word of ['Pain Points','관측','추론','C1','C2','근거 2건']) expect(html(tree)).toContain(word);
  const buttons=nodes(tree,e=>e.props.className==='persona-pain-button');
  buttons.forEach(e=>(e.props.onClick as ()=>void)());
  expect(onOpenEvidence.mock.calls).toEqual([[0],[1],[2]]);
  const more=nodes(tree,e=>e.props['aria-expanded']===false)[0];
  (more.props.onClick as ()=>void)();
  expect(nodes(draw(PersonaSummary,{...summaryProps,painPoints:pains,onOpenEvidence},false),e=>e.props['aria-expanded']===true)).toHaveLength(1);
});
it('distinguishes legacy R6, empty and partial pains and never offers a legacy button', () => {
  const legacy=draw(PersonaSummary,{...summaryProps,legacy:true,painPoints:undefined});
  expect(html(legacy)).toContain('근거 탐색을 다시 실행한 뒤 페르소나를 다시 만들면 페인포인트가 표시됩니다. 인사이트도 다시 만들어야 합니다.');
  expect(nodes(legacy,e=>e.type==='button')).toHaveLength(0);
  expect(nodes(legacy,e=>e.type==='a').map(e=>e.props.href)).toEqual(['/pipeline/evidence']);
  expect(html(draw(PersonaSummary,{...summaryProps,painPoints:[]}))).toContain('근거가 부족해 페인포인트를 만들지 못했습니다.');
  for(const n of [1,2]) expect(html(draw(PersonaSummary,{...summaryProps,painPoints:pains.slice(0,n)}))).toContain(`근거가 적어 ${n}개만 찾았습니다.`);
});
it('uses token-only responsive CSS with clamped names, mobile pain priority and touch targets', () => {
  const css=readFileSync(new URL('./persona.css',import.meta.url),'utf8');
  expect(css).toMatch(/-webkit-line-clamp:\s*2/);
  expect(css).toMatch(/@media\s*\(max-width:\s*767px\)/);
  expect(css).toMatch(/min-height:\s*44px/);
  expect(css).toContain('--type-section'); expect(css).toContain('--type-screen');
  expect(css).toMatch(/\.persona-mobile-select\{display:none/);
  expect(css).toMatch(/\.persona-desktop-list\{display:none/);
  expect(css).toMatch(/\.persona-pain-points\{order:1/);
  expect(css).toMatch(/\.persona-desire-goals\{order:2/);
  expect(css).not.toMatch(/#[\da-f]{3,8}\b|rgba?\(/i);
  const tokens=readFileSync(new URL('../../styles/tokens.css',import.meta.url),'utf8');
  for(const variable of css.matchAll(/var\((--[\w-]+)\)/g)) expect(tokens).toContain(`${variable[1]}:`);
});

it('renders the ten CCM rows in contract order with plain table surfaces and sticky headers', () => {
  const tree = draw(CCMTable, {contexts: contexts.slice(0, 1)});
  expect(nodes(tree, e => e.type === 'th' && e.props.scope === 'row').map(e => html(e))).toEqual(
    ['행동','상태','감정','장벽','페인포인트','키워드','쓰는 제품·수단','만족도','기회','근거 수'].map(label => expect.stringContaining(label))
  );
  expect(nodes(tree, e => e.props.className === 'ccm-scroll')).toHaveLength(1);
  expect(nodes(tree, e => e.type === 'th' && e.props.scope === 'row').every(e => e.props.className === 'ccm-sticky')).toBe(true);
  expect(html(tree)).not.toContain('ds-card');
});
it('clamps CCM text, shows extra pain count, and expands full text together with evidence', () => {
  const text = '긴 페인포인트 '.repeat(100);
  const props = {contexts: [{id:'C1',name:'이름',cells:{pain_point:{text,more:2,evidence:'모든 페인포인트와 인용'}}}]};
  let tree = draw(CCMTable, props);
  const button = nodes(tree, e => e.type === 'button' && String(e.props['aria-label']).includes('페인포인트'))[0];
  expect(html(button)).toContain('+2');
  expect(nodes(button, e => e.props.className === 'ccm-clamp')).toHaveLength(1);
  (button.props.onClick as () => void)(); tree = draw(CCMTable, props, false);
  expect(nodes(tree, e => e.props.className === 'ccm-full-text').map(e => e.props.children)).toContain(text);
  expect(html(tree)).toContain('모든 페인포인트와 인용');
});
it('marks missing and blank CCM cells as insufficient evidence', () => {
  const tree = draw(CCMTable, {contexts:[{id:'C1',name:'이름',cells:{action:{text:'  '},state:{text:''}}}]});
  expect(nodes(tree, e => e.props.className === 'ccm-empty')).toHaveLength(10);
  expect(nodes(tree, e => e.props.className === 'ccm-empty').every(e => e.props.children === '근거 부족')).toBe(true);
});
it('defines CCM three-line clamp, scrolling, sticky paper headers, mobile widths and touch targets', () => {
  const css = readFileSync(new URL('./persona.css', import.meta.url), 'utf8');
  expect(css).toMatch(/\.ccm-clamp\s*\{[^}]*-webkit-line-clamp:\s*3/);
  expect(css).toMatch(/\.ccm-scroll\s*\{[^}]*overflow-x:\s*auto/);
  expect(css).toMatch(/\.ccm-sticky\s*\{[^}]*position:\s*sticky;[^}]*left:\s*0;[^}]*background:\s*var\(--paper\)/);
  expect(css).toMatch(/\.ccm-cell-button\s*\{[^}]*min-height:\s*44px/);
  expect(css).toMatch(/@media\s*\(max-width:\s*767px\)[\s\S]*\.ccm-scroll[^}]*min-width:\s*200px/);
});

const hierarchy = {id:'root',name:'제품',doc_count:16,children:[
  {id:'CL1',name:'Cluster 1',doc_count:4,children:[
    {id:'P1',name:'Persona 1',doc_count:1,children:[{id:'C1',name:'Context 1',doc_count:0}]},
    {id:'P2',name:'Persona 2',doc_count:2,children:[{id:'C2',name:'Context 2',doc_count:2}]}
  ]},
  {id:'CL2',name:'Cluster 2',doc_count:8,children:[{id:'P3',name:'Persona 3',doc_count:8}]}
]};
it('renders nested hierarchy lists with selected branch disclosures and proportional bars', () => {
  const props = {root:hierarchy,expandedId:'P1'};
  let tree = draw(HierarchyTree,props);
  expect(nodes(tree,e=>e.type==='svg')).toHaveLength(0);
  expect(nodes(tree,e=>e.type==='ul')).toHaveLength(4);
  expect(nodes(tree,e=>e.props['data-ratio']!==undefined).map(e=>e.props['data-ratio'])).toEqual([1,.25,.0625,0,.125,.5]);
  expect(html(tree)).toContain('문서 0건');
  expect(html(tree)).not.toContain('Context 2'); expect(html(tree)).not.toContain('Persona 3');
  const buttons = nodes(tree,e=>e.type==='button');
  expect(buttons.map(e=>e.props['aria-expanded'])).toEqual([true,true,false,false]);
  expect(buttons.every(e=>e.props.type==='button')).toBe(true);
  (buttons[1].props.onClick as ()=>void)(); tree=draw(HierarchyTree,props,false);
  expect(html(tree)).not.toContain('Context 1');
  (nodes(tree,e=>e.type==='button')[1].props.onClick as ()=>void)();
  expect(html(draw(HierarchyTree,props,false))).toContain('Context 1');
});
it('keeps only the root open without a selection and handles zero document totals', () => {
  const tree=draw(HierarchyTree,{root:hierarchy});
  expect(nodes(tree,e=>e.type==='ul')).toHaveLength(2);
  expect(nodes(tree,e=>e.type==='button').every(e=>e.props['aria-expanded']===false)).toBe(true);
  expect(html(draw(HierarchyTree,{root:{id:'zero',name:'빈 제품',doc_count:0}}))).toContain('data-ratio="0"');
});
it('keeps wrapping sentences in their own grid cell and omits absent mean lines', () => {
  const label='긴 문장'.repeat(100);
  const tree=OpportunityBars({rows:[{contextId:'null',short:'C1',label,value:null},{contextId:'zero',short:'C2',label:'영',value:0}],mean:null});
  const labels=nodes(tree,e=>e.props.className==='insight-bar-label');
  expect(html(labels[0])).toContain(label);
  expect(nodes(labels[0],e=>e.type==='span')[1].props.children).toBe(label);
  expect(nodes(tree,e=>e.props.className==='insight-bars-mean')).toHaveLength(0);
  const fills=nodes(tree,e=>e.props.className==='insight-bar');
  expect(fills).toHaveLength(1);
  expect(fills[0].props.style).toEqual({height:'0%'});
  expect(html(labels[0])).toContain('값 없음');
  expect(html(labels[1])).not.toContain('값 없음');
  expect(html(tree)).not.toMatch(/NaN|Infinity/);
  const css=readFileSync(new URL('./insight.css',import.meta.url),'utf8');
  expect(css).toMatch(/\.insight-bars-grid\s*\{[^}]*display:\s*grid/);
  expect(nodes(tree,e=>e.props.className==='insight-bars-grid')[0].props.style).toMatchObject({gridTemplateColumns:'repeat(2, minmax(72px, 1fr))'});
  expect(css).toMatch(/\.insight-bar-label\s*\{[^}]*overflow-wrap:\s*anywhere/);
  const personaCss=readFileSync(new URL('./persona.css',import.meta.url),'utf8');
  expect(personaCss).toMatch(/\.hierarchy-toggle\s*\{[^}]*min-height:\s*44px/);
});

it('RV2 separates nearby focused labels deterministically',()=>{
 const props={map:map([point('C1'),{...point('C2'),i:.50001,s:.50001}]),focusPersonaId:'P1'};
 const labels=nodes(draw(OpportunityMap,props),e=>!!e.props['data-label']);
 expect(labels).toHaveLength(2);
 expect(labels[0].props.y).not.toBe(labels[1].props.y);
 expect(nodes(draw(OpportunityMap,props),e=>!!e.props['data-label']).map(e=>e.props.y)).toEqual(labels.map(e=>e.props.y));
});

it.each([1,0])('RV8 keeps three coincident focused labels inside the viewBox at s=%s',s=>{
 const tree=draw(OpportunityMap,{map:map(['C1','C2','C3'].map(id=>({...point(id),s}))),focusPersonaId:'P1'});
 const positions=nodes(tree,e=>!!e.props['data-context-id']).map(dot=>{
   const label=nodes(dot,e=>!!e.props['data-label'])[0];
   const [,px,py]=String(dot.props.transform).match(/translate\(([^ ]+) ([^)]+)\)/)!;
   const x=Number(px)+Number(label.props.x), y=Number(py)+Number(label.props.y);
   expect(x).toBeGreaterThanOrEqual(0);expect(x).toBeLessThanOrEqual(600);
   expect(y).toBeGreaterThanOrEqual(12);expect(y).toBeLessThanOrEqual(420);
   return y;
 });
 for(let i=0;i<positions.length;i++) for(let j=i+1;j<positions.length;j++) expect(Math.abs(positions[i]-positions[j])).toBeGreaterThanOrEqual(12);
});

it('RV9 gives ContextTable actions and scoped map legend chips 44px touch targets',()=>{
 const tree=draw(ContextTable,{rows:[point('C1')],onOpenCard:vi.fn()});
 const action=nodes(tree,e=>e.type==='button' && e.props.children==='카드 열기')[0];
 expect((action.props.style as {minHeight:number}).minHeight).toBeGreaterThanOrEqual(44);
 const css=readFileSync(new URL('./persona.css',import.meta.url),'utf8');
 expect(css).toMatch(/\.persona-map-legend\s+\.ds-chip\s*\{[^}]*min-height:\s*44px/);
 expect(nodes(draw(OpportunityMap,{map:map([point('C1')])}),e=>e.props.className==='persona-map-legend')).toHaveLength(1);
});

it('F2 preserves readable column widths and local horizontal scrolling',()=>{
 const source=readFileSync(new URL('./ContextTable.tsx',import.meta.url),'utf8');
 expect(source).toContain('<colgroup>');
 const css=readFileSync(new URL('./persona.css',import.meta.url),'utf8');
 expect(css).toContain('.persona-context-table table{table-layout:fixed;min-width:1180px}');
 for(const width of [96,220,160,72,100,260]) expect(source).toContain(`width:${width}`);
 expect(css).toContain('.persona-context-table{overflow-x:auto}');
});
it('F3 stacks the card comparison table above a width-capped map',()=>{
 const css=readFileSync(new URL('./persona.css',import.meta.url),'utf8');
 expect(css).not.toMatch(/\.persona-comparison-layout\{grid-template-columns:minmax\(0,1fr\) minmax\(420px,0\.8fr\)\}/);
 expect(css).toContain('.persona-comparison-layout>.persona-map-surface{max-width:720px}');
 expect(css).toContain('.persona-map-layout{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}');
});
it('F7 reduces mobile pain typography and indentation while hiding the duplicate card heading accessibly',()=>{
 const css=readFileSync(new URL('./persona.css',import.meta.url),'utf8');
 expect(css).toMatch(/@media\(max-width:767px\)\{[^}]*\}[^]*?\.persona-pain-points ol\{padding-left:20px\}/);
 expect(css).toContain('.persona-pain-text,.persona-pain-item::marker{font:var(--type-card)}');
 expect(css).toContain('.persona-summary-header h2{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}');
});


it('RV8 separates overlapping rendered intervals with mixed label anchors deterministically', () => {
 const points = [450, 540].map((px, index) => ({
   ...point(`CONTEXT0${index + 1}`), i: (px - 60) / 480,
 }));
 const props = {map: map(points), focusPersonaId: 'P1'};
 const positions = (tree: ReactNode) => nodes(tree, e => !!e.props['data-context-id']).map(dot => {
   const label = nodes(dot, e => !!e.props['data-label'])[0];
   const [,px,py] = String(dot.props.transform).match(/translate\(([^ ]+) ([^)]+)\)/)!;
   const anchorX = Number(px) + Number(label.props.x);
   const width = String(label.props.children).length * 6.5;
   const left = anchorX - (label.props.textAnchor === 'end' ? width : 0);
   return {left, right: left + width, y: Number(py) + Number(label.props.y), anchor: label.props.textAnchor};
 });
 const labels = positions(draw(OpportunityMap, props));
 expect(labels.map(label => label.anchor)).toEqual(['start', 'end']);
 expect(labels[0].left).toBeCloseTo(462);
 expect(labels[1].left).toBeCloseTo(469.5);
 for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) {
   const a = labels[i], b = labels[j];
   if (Math.abs(a.y - b.y) < 12) expect(a.left < b.right && b.left < a.right).toBe(false);
 }
 expect(positions(draw(OpportunityMap, props))).toEqual(labels);
 expect(positions(draw(OpportunityMap, {...props, map: map([...points].reverse())})).reverse()).toEqual(labels);
});

it.each([1, 0])('keeps focused point labels horizontally inside the viewBox at i=%s', i => {
 const id = 'CL1-P2-C1';
 const props = {map: map([{...point(id), i}]), focusPersonaId: 'P1'};
 const tree = draw(OpportunityMap, props);
 const dot = nodes(tree, e => e.props['data-context-id'] === id)[0];
 const label = nodes(dot, e => e.props['data-label'] === id)[0];
 const px = Number(String(dot.props.transform).match(/translate\(([^ ]+)/)![1]);
 const anchorX = px + Number(label.props.x);
 const width = id.length * 6.5;
 const left = anchorX - (label.props.textAnchor === 'end' ? width : 0);
 expect(left).toBeGreaterThanOrEqual(4);
 expect(left + width).toBeLessThanOrEqual(596);
 expect(label.props.textAnchor ?? 'start').toBe(i === 1 ? 'end' : 'start');
 expect(nodes(draw(OpportunityMap, props), e => e.props['data-label'] === id)[0].props).toEqual(label.props);
});
