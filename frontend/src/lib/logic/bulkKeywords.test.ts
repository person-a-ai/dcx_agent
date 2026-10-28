import { describe, expect, it } from 'vitest';
import * as api from '../api/keywords';

describe('bulkKeywords', () => {
  it('provides bulk API clients', () => {
    expect('previewBulk' in api).toBe(true);
    expect('addBulk' in api).toBe(true);
  });
});

import { destinations } from '@/components/keywords/taxonomy';
import type { BulkPreview, Destination } from '../api/keywords';
import { parseBulk, resolveGroup, decodeCsv, viewRows, bulkSummary, addableItems, applyToIncluded, retryRows } from './bulkKeywords';
const parse = (text: string) => parseBulk(text, destinations);
const sense = { axis: 'physical', sub: 'sense' } satisfies Destination;
const preview: BulkPreview = { rows: [
  { row: 0, kw: '소음', ...sense, source: 'input', status: 'new' },
  { row: 1, kw: '환기', ...sense, source: null, status: 'existing' },
  { row: 2, kw: '소음', ...sense, source: null, status: 'in_list_duplicate', firstRow: 0 },
  { row: 3, kw: '불안', axis: null, sub: null, source: 'llm_failed', status: 'needs_class' },
] };
describe('bulkKeywords', () => {
  it('parses Korean and English headers', () => {
    expect(parse('키워드,축,하위분류\n층간소음,물리,감각\n불안감,,').rows).toEqual([{ kw: '층간소음', ...sense }, { kw: '불안감' }]);
    expect(parse('kw\tAXIS\tsub\n소음\tphysical\tsense').rows).toEqual([{ kw: '소음', ...sense }]);
  });
  it('strips BOM before header detection', () => expect(parse('\uFEFF키워드\n소음').rows).toEqual([{ kw: '소음' }]));
  it('treats a single headerless line as a comma list', () => expect(parse('소음, 환기 ,  ,습도').rows.map(r => r.kw)).toEqual(['소음', '환기', '습도']));
  it('uses first cell per line and tries axis/sub without header', () => expect(parse('소음,물리,감각\n환기').rows).toEqual([{ kw: '소음', ...sense }, { kw: '환기' }]));
  it('parses excel paste with quotes and trailing tabs', () => expect(parse('"a, b"\t심리\t감정\t\t\n"줄\n바꿈"\t\t').rows).toEqual([{ kw: 'a, b', axis: 'psychological', sub: 'emotion' }, { kw: '줄\n바꿈' }]));
  it('resolves sub-only, labels, codes and custom names', () => {
    expect(resolveGroup(undefined, '정보탐색', destinations)).toEqual({ axis: 'behavioral', sub: 'info_search' });
    expect(resolveGroup('심리', 'emotion', destinations)).toEqual({ axis: 'psychological', sub: 'emotion' });
    expect(resolveGroup('물리', '설치환경', [...destinations, { axis: 'physical', sub: 'custom:설치환경' }])).toEqual({ axis: 'physical', sub: 'custom:설치환경' });
    expect(resolveGroup('물리', undefined, destinations)).toBeNull();
    expect(resolveGroup('심리', '감각', destinations)).toBeNull();
  });
  it('truncates to 500 rows', () => {
    const result = parse(Array.from({ length: 520 }, (_, i) => `단어${i}`).join('\n'));
    expect(result.rows).toHaveLength(500); expect(result.truncated).toBe(20);
  });
  it('skips cells longer than 100 chars', () => {
    const result = parse(`키워드\n${'a'.repeat(101)}\n${'b'.repeat(100)}`);
    expect(result.rows).toEqual([{ kw: 'b'.repeat(100) }]); expect(result.tooLong).toHaveLength(1);
  });
  it('decodes utf-8, BOM and cp949', () => {
    for (const bytes of [new TextEncoder().encode('키워드'), new TextEncoder().encode('\uFEFF키워드'), Uint8Array.from([0xc5, 0xb0, 0xbf, 0xf6, 0xb5, 0xe5])]) expect(decodeCsv(bytes.buffer as ArrayBuffer)).toBe('키워드');
  });
  it('view rows, summary, addable and bulk apply', () => {
    const edits = { 3: { to: { axis: 'physical', sub: 'space' } as Destination }, 0: { include: false }, 1: { include: true, to: sense } };
    const rows = viewRows(preview, edits);
    expect(rows.map(r => r.state)).toEqual(['excluded', 'existing', 'in_list_duplicate', 'new']);
    expect(rows[1]).toMatchObject({ include: false, chosen: false });
    expect(bulkSummary(rows)).toEqual({ new: 1, existing: 1, inListDuplicate: 1, needsClass: 0, excluded: 1 });
    expect(addableItems(rows)).toEqual([{ row: 3, kw: '불안', axis: 'physical', sub: 'space' }]);
    const next = applyToIncluded(rows, edits, sense);
    expect(next[1]).toBe(edits[1]); expect(next[0]).toBe(edits[0]); expect(next[3].to).toEqual(sense);
    expect(edits[3].to.sub).toBe('space');
  });
  it('retry keeps chosen and input classes', () => {
    expect(retryRows(viewRows(preview, {}))[3]).toEqual({ kw: '불안' });
    const rows = viewRows(preview, { 3: { to: sense } });
    expect(retryRows(rows)[0]).toEqual({ kw: '소음', ...sense });
    expect(retryRows(rows)[3]).toEqual({ kw: '불안', ...sense });
    expect(retryRows(viewRows({ rows: [{ ...preview.rows[0], source: 'llm' }] }, {}))[0]).toEqual({ kw: '소음', ...sense });
  });
  it('edits survive retry', () => {
    const edits = { 1: { include: false } };
    const fresh: BulkPreview = { rows: preview.rows.map(r => ({ ...r, status: 'new', source: 'llm' })) };
    expect(viewRows(fresh, edits)[1].state).toBe('excluded');
  });
  it('quoted tab does not switch delimiter', () => expect(parse('키워드,축,하위분류\n"a\tb",물리,감각').rows).toEqual([{ kw: 'a\tb', ...sense }]));
  it('unterminated quote ends at line end', () => expect(parse('"abc\n소음').rows.map(r => r.kw)).toEqual(['abc', '소음']));
  it('keeps an unterminated quoted line in one cell', () => expect(parse('"abc,def\n소음').rows.map(r => r.kw)).toEqual(['abc,def', '소음']));
  it('handles escaped quotes and CRLF', () => expect(parse('kw,axis,sub\r\n"a""b",physical,sense\r\n').rows).toEqual([{ kw: 'a"b', ...sense }]));
});
