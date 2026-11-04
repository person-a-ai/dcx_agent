import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, it, expect } from 'vitest';
import { BulkAdd, type BulkState } from './BulkAdd';
import type { BulkPreview, Destination } from '@/lib/api/keywords';
const groups: Destination[] = [{ axis: 'physical', sub: 'sense' }];
const preview: BulkPreview = { rows: [
  { row: 0, kw: '소음', axis: 'physical', sub: 'sense', source: 'input', status: 'new' },
  { row: 1, kw: '저소음', axis: null, sub: null, source: null, status: 'existing', duplicateOf: { id: 'k1', kw: '저소음', ...groups[0] } },
  { row: 2, kw: '소음', axis: null, sub: null, source: null, status: 'in_list_duplicate', firstRow: 0 },
  { row: 3, kw: '환기', axis: null, sub: null, source: 'llm_failed', status: 'needs_class' },
] };
function render(initialState?: BulkState, extra = {}) { return renderToStaticMarkup(createElement(BulkAdd, { groups, disabled: false, readonly: false, preview: async () => preview, add: async () => ({ results: [], keywords: [] }), onReveal: () => {}, initialState, ...extra })); }
const state = (stage: BulkState['stage'], extra = {}): BulkState => ({ stage, text: '', edits: {}, ...extra });
describe('BulkAdd', () => {
 it('closed shows title and open button', () => { const html = render(); expect(html).toContain('키워드 일괄 추가'); expect(html).toContain('일괄 추가하기'); });
 it('readonly shows notice only', () => { const html = render(undefined, { readonly: true }); expect(html).toContain('읽기 전용 버전에서는 키워드를 추가할 수 없습니다.'); expect(html).not.toContain('일괄 추가하기'); });
 it('input shows textarea hint, file button and row count', () => { const html = render(state('input', { text: '소음\n환기' })); for (const text of ['2행 인식', 'CSV 파일 선택하기', '한 번에 최대 500행']) expect(html).toContain(text); expect(render(state('input'))).toMatch(/<button[^>]*disabled=""[^>]*>미리보기/); });
 it('loading shows status', () => { const html = render(state('loading')); expect(html).toContain('자동 분류하는 중'); expect(html).toContain('role="status"'); });
 it('preview shows summary, statuses and add count', () => { const html = render(state('preview', { preview })); for (const text of ['추가 예정 1', '이미 있음 1', '리스트 안 중복 1', '분류 필요 1', '1개 추가하기', '“저소음”', '1행과 같음']) expect(html).toContain(text); });
 it('preview badges use mockup tones for summaries, statuses and sources', () => {
  const html = render(state('preview', { preview: { rows: [...preview.rows,
   { row: 4, kw: '자동', ...groups[0], source: 'llm', status: 'new' },
   { row: 5, kw: '제외됨', ...groups[0], source: 'input', status: 'new' },
   { row: 6, kw: '선택됨', axis: null, sub: null, source: 'llm_failed', status: 'needs_class' },
  ] }, edits: { 5: { include: false }, 6: { to: groups[0] } } }));
  const badge = (label: string, tone: string) => expect(html).toMatch(new RegExp(`<span class="ds-badge ds-${tone}[^">]*">${label}</span>`));
  for (const label of ['추가 예정 3', '추가 예정']) badge(label, 'info');
  for (const label of ['분류 필요 1', '분류 필요', '분류 실패']) badge(label, 'warning');
  badge('자동 제안', 'success');
  for (const label of ['이미 있음 1', '이미 있음', '리스트 안 중복 1', '리스트 안 중복', '제외 1', '제외', '입력값', '직접 선택']) badge(label, 'neutral');
 });
 it('preview with classifyError shows retry', () => { const html = render(state('preview', { preview: { ...preview, classifyError: { kind: 'backend', message: 'down' } } })); expect(html).toContain('자동 분류에 실패했습니다'); expect(html).toContain('자동 분류 다시 하기'); });
 it('truncated shows notice', () => expect(render(state('input', { parsed: { rows: [], truncated: 20, tooLong: [] } }))).toContain('앞 500행만 불러왔습니다(나머지 20행 제외)'));
 it('result shows added and skipped rows', () => { const html = render(state('result', { preview, result: { results: [{ index: 0, status: 'added' }, { index: 1, status: 'duplicate' }], keywords: [] } })); for (const text of ['키워드 1개를 추가했습니다. 1개는 건너뛰었습니다.', '추가한 키워드 보기', '새 리스트 넣기']) expect(html).toContain(text); });
 it('counts only actual llm suggestions in the preview notice', () => {
  const html = render(state('preview', { text: '자동1\n자동2\n저소음\n자동1', preview: { rows: [
   { ...preview.rows[0], source: 'llm' },
   { ...preview.rows[0], row: 1, kw: '자동2', source: 'llm' },
   preview.rows[1], preview.rows[2],
  ] } }));
  expect(html).toContain('분류가 없던 2개는 자동 제안입니다');
  expect(html).not.toContain('분류가 없던 4개');
 });
 it('omits the automatic suggestion notice when no rows have llm source', () => {
  expect(render(state('preview', { text: '저소음', preview }))).not.toContain('개는 자동 제안입니다');
 });
 it('omits skipped count when all results were added', () => {
  const html = render(state('result', { result: { results: [{ index: 0, status: 'added' }], keywords: [] } }));
  expect(html).toContain('키워드 1개를 추가했습니다.');
  expect(html).not.toContain('개는 건너뛰었습니다');
 });
 it('disabled blocks add', () => { expect(render(state('preview', { preview }), { disabled: true })).toMatch(/<button[^>]*disabled=""[^>]*>1개 추가하기/); expect(render(state('preview', { preview: { rows: [] } }))).toMatch(/<button[^>]*disabled=""[^>]*>0개 추가하기/); });
});
