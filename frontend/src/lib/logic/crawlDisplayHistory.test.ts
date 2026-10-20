/* eslint-disable @typescript-eslint/no-explicit-any */
import { afterEach, expect, it, vi } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import type { CrawlStatus } from '../api/crawl';
const hooks = vi.hoisted(() => ({ slots: [] as any[], cursor: 0 }));
vi.mock('react', async () => ({ ...await vi.importActual('react'),
  useState: (initial: any) => { const i = hooks.cursor++; if (!(i in hooks.slots)) hooks.slots[i] = initial; return [hooks.slots[i], (next: any) => { hooks.slots[i] = typeof next === 'function' ? next(hooks.slots[i]) : next; }]; },
  useRef: () => ({ current: null }), useLayoutEffect: () => {},
}));
import { GateTable } from '../../components/crawl/GateTable';
import { Progress } from '../../components/crawl/Progress';
const kw = '에어컨청소';
const keywordDisplay = { [kw]: '에어컨 청소' };
function nodes(n: any): any[] { return !n || typeof n !== 'object' ? [] : Array.isArray(n) ? n.flatMap(nodes) : [n, ...nodes(n.props?.children)]; }
afterEach(() => { hooks.slots = []; hooks.cursor = 0; });

it('labels gate rows accessibly while expansion and exclusion keep stored keys', () => {
  const onChange = vi.fn();
  const props = { rows: [{ kw, axis: 'a', sub: 's', per_source: {}, listed: 1, after_filter: 1, unique_ratio: 1, badges: [] }], excluded: [], onChange, disabled: false, keywordDisplay };
  const render = () => { hooks.cursor = 0; return GateTable(props); };
  const tree = nodes(render());
  const checkbox = tree.find(n => n.type === 'input');
  expect(checkbox.props['aria-label']).toBe('에어컨 청소 제외');
  checkbox.props.onChange({ target: { checked: true } });
  expect(onChange).toHaveBeenCalledWith([kw]);
  expect(tree.find(n => n.type === 'tr' && n.props['data-measure']).props['data-measure']).toBe(`${kw}:false`);
  tree.find(n => n.type === 'button' && n.props.className === 'crawl-row-button').props.onClick({ stopPropagation() {} });
  const expanded = renderToStaticMarkup(render());
  expect(expanded).toContain('에어컨 청소 · 접기');
  expect(expanded).toContain(`data-measure="${kw}:true"`);
  expect(renderToStaticMarkup(createElement(GateTable, { ...props, keywordDisplay: undefined }))).toContain(`${kw} 제외`);
});

it('uses display labels in the result matrix and both keyword bars without changing raw report keys', () => {
  const report = { matrix: { [kw]: { youtube_vlog: { docs: 7, listed: 2, filtered: 0, unique: 2, urls_done: 2 } } }, channels: {}, totals: { doc_count: 7 } };
  const status: CrawlStatus = {
    status: 'done', kind: 'detail', progress: null, channels: {}, report, keywordDisplay,
    gate: null, estimate: null, defaults: { adWords: [], excludeSources: [] },
    added_keywords_count: 0, collection_keywords: [kw],
  };
  const html = renderToStaticMarkup(createElement(Progress, { status }));
  expect(html.match(/에어컨 청소/g)).toHaveLength(3);
  expect(html).not.toContain(kw);
  expect(Object.keys(report.matrix)).toEqual([kw]);
  expect(renderToStaticMarkup(createElement(Progress, { status: { ...status, keywordDisplay: undefined } }))).toContain(kw);
});

it('keeps raw keyword React keys in both bars when display labels collide or change', () => {
  const otherKw = '에어컨세척';
  const status: CrawlStatus = {
    status: 'done', kind: 'detail', progress: null, channels: {},
    report: {
      matrix: {
        [kw]: { youtube_vlog: { docs: 7, listed: 7, filtered: 0, unique: 7 } },
        [otherKw]: { youtube_vlog: { docs: 3, listed: 3, filtered: 0, unique: 3 } },
      },
      channels: {}, totals: { doc_count: 10 },
    },
    gate: null, estimate: null, defaults: { adWords: [], excludeSources: [] },
    added_keywords_count: 0, collection_keywords: [kw, otherKw],
  };
  const labelVariants: (Record<string, string> | undefined)[] = [
    { [kw]: '같은 표시명', [otherKw]: '같은 표시명' }, keywordDisplay, undefined,
  ];
  for (const labels of labelVariants) {
    const bars = nodes(Progress({ status: { ...status, keywordDisplay: labels } }))
      .filter(n => typeof n.type === 'function' && Array.isArray(n.props?.items)
        && n.props.items.some((item: any) => item.value === 7));
    expect(bars).toHaveLength(2);
    bars.forEach((bar, index) => {
      const rows = nodes(bar.type(bar.props)).filter(n => n.props?.className === 'ds-bar');
      const rawKeys = index === 0 ? [kw, otherKw] : [otherKw, kw];
      expect(rows.map(row => row.key)).toEqual(rawKeys);
      expect(rows.map(row => row.props.children[0].props.children))
        .toEqual(rawKeys.map(raw => labels?.[raw] ?? raw));
    });
  }
});
