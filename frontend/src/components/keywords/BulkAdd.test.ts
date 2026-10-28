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
 it('preview with classifyError shows retry', () => { const html = render(state('preview', { preview: { ...preview, classifyError: { kind: 'backend', message: 'down' } } })); expect(html).toContain('자동 분류에 실패했습니다'); expect(html).toContain('자동 분류 다시 하기'); });
 it('truncated shows notice', () => expect(render(state('input', { parsed: { rows: [], truncated: 20, tooLong: [] } }))).toContain('앞 500행만 불러왔습니다(나머지 20행 제외)'));
 it('result shows added and skipped rows', () => { const html = render(state('result', { preview, result: { results: [{ index: 0, status: 'added' }, { index: 1, status: 'duplicate' }], keywords: [] } })); for (const text of ['키워드 1개를 추가했습니다. 1개는 건너뛰었습니다.', '추가한 키워드 보기', '새 리스트 넣기']) expect(html).toContain(text); });
 it('disabled blocks add', () => { expect(render(state('preview', { preview }), { disabled: true })).toMatch(/<button[^>]*disabled=""[^>]*>1개 추가하기/); expect(render(state('preview', { preview: { rows: [] } }))).toMatch(/<button[^>]*disabled=""[^>]*>0개 추가하기/); });
});
