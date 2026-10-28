import type { BulkPreview, BulkPreviewRow, BulkRowIn, Destination } from '../api/keywords';
import { axes, subLabel } from '@/components/keywords/taxonomy';

export const MAX_BULK_ROWS = 500;
export const MAX_KW_LENGTH = 100;
export function decodeCsv(buf: ArrayBuffer): string {
  let text: string;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(buf); }
  catch { text = new TextDecoder('euc-kr').decode(buf); }
  return text.replace(/^\uFEFF/, '');
}
export function resolveGroup(axis: string | undefined, sub: string | undefined, groups: Destination[]): Destination | null {
  const a = axis?.trim().toLowerCase();
  const s = sub?.trim().toLowerCase();
  if (!s) return null;
  const resolvedAxis = a ? axes.find(x => x.value === a || x.label === a)?.value : undefined;
  if (a && !resolvedAxis) return null;
  const matches = groups.filter(g => (!resolvedAxis || g.axis === resolvedAxis) &&
    (g.sub.toLowerCase() === s || subLabel(g).toLowerCase() === s));
  return matches.length === 1 ? { ...matches[0] } : null;
}

// A quote opens only at a cell start. It may span lines only if a closing
// quote followed by a delimiter, newline or EOF occurs before another line
// starts with a quote. Otherwise recover at the opening line's end.
// Both delimiter detection and cell parsing use this same boundary rule.
function closingQuote(text: string, opening: number): number {
  for (let i = opening + 1; i < text.length; i++) {
    if ((text[i] === '\n' || text[i] === '\r') && text[i + 1] === '"') return -1;
    if (text[i] !== '"') continue;
    if (text[i + 1] === '"') { i++; continue; }
    if (i + 1 === text.length || ',\t\r\n'.includes(text[i + 1])) return i;
  }
  return -1;
}
function cells(text: string, delimiter: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"') {
        if (text[i + 1] === '"') { cell += '"'; i++; }
        else if (i + 1 === text.length || ',\t\r\n'.includes(text[i + 1])) quoted = false;
        else cell += c;
      } else cell += c;
    } else if (c === '"' && cell === '') {
      if (closingQuote(text, i) >= 0) quoted = true;
      else {
        while (i + 1 < text.length && text[i + 1] !== '\n' && text[i + 1] !== '\r') cell += text[++i];
      }
    } else if (c === delimiter) { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') {
      row.push(cell); rows.push(row); row = []; cell = '';
      if (c === '\r' && text[i + 1] === '\n') i++;
    } else cell += c;
  }
  row.push(cell); rows.push(row);
  return rows;
}
function delimiterFor(text: string): string {
  let quoted = false, start = true;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"' && (quoted || start)) {
      if (quoted && text[i + 1] === '"') { i++; continue; }
      if (quoted && i + 1 < text.length && !',\t\r\n'.includes(text[i + 1])) continue;
      if (!quoted && closingQuote(text, i) < 0) {
        while (i + 1 < text.length && text[i + 1] !== '\n' && text[i + 1] !== '\r') i++;
      } else quoted = !quoted;
    } else if (!quoted && c === '\t') return '\t';
    start = !quoted && (c === ',' || c === '\n' || c === '\r');
  }
  return ',';
}
export function parseBulk(text: string, groups: Destination[]): { rows: BulkRowIn[]; truncated: number; tooLong: string[] } {
  text = text.replace(/^\uFEFF/, '');
  const delimiter = delimiterFor(text);
  const table = cells(text, delimiter).filter(row => row.some(c => c.trim()));
  const aliases = [['키워드', 'keyword', 'kw'], ['축', 'axis'], ['하위분류', 'sub']];
  const header = table[0]?.map(c => c.trim().toLowerCase()) ?? [];
  const kwIndex = header.findIndex(c => aliases[0].includes(c));
  const hasHeader = kwIndex >= 0;
  const axisIndex = hasHeader ? header.findIndex(c => aliases[1].includes(c)) : 1;
  const subIndex = hasHeader ? header.findIndex(c => aliases[2].includes(c)) : 2;
  let data = hasHeader ? table.slice(1) : table;
  if (!hasHeader && delimiter === ',' && data.length === 1) data = data[0].map(c => [c]);
  const rows: BulkRowIn[] = [], tooLong: string[] = [];
  let truncated = 0;
  for (const row of data) {
    const kw = (row[hasHeader ? kwIndex : 0] ?? '').trim();
    if (!kw) continue;
    if ([...kw].length > MAX_KW_LENGTH) { tooLong.push(kw); continue; }
    if (rows.length >= MAX_BULK_ROWS) { truncated++; continue; }
    const to = resolveGroup(row[axisIndex], row[subIndex], groups);
    rows.push({ kw, ...(to ?? {}) });
  }
  return { rows, truncated, tooLong };
}
export type BulkEdit = Record<number, { include?: boolean; to?: Destination }>;
export type BulkView = BulkPreviewRow & { include: boolean; chosen: boolean; state: BulkPreviewRow['status'] | 'excluded' };
export function viewRows(preview: BulkPreview, edits: BulkEdit): BulkView[] {
  return preview.rows.map(row => {
    if (row.status === 'existing' || row.status === 'in_list_duplicate') return { ...row, include: false, chosen: false, state: row.status };
    const edit = edits[row.row];
    const to = edit?.to;
    const include = edit?.include !== false;
    return { ...row, ...to, include, chosen: !!to, state: !include ? 'excluded' : to && row.status === 'needs_class' ? 'new' : row.status };
  });
}
export function bulkSummary(rows: BulkView[]) {
  const result = { new: 0, existing: 0, inListDuplicate: 0, needsClass: 0, excluded: 0 };
  for (const row of rows) {
    const key = row.state === 'in_list_duplicate' ? 'inListDuplicate' : row.state === 'needs_class' ? 'needsClass' : row.state;
    result[key]++;
  }
  return result;
}
export function addableItems(rows: BulkView[]): (Destination & { kw: string; row: number })[] {
  return rows.flatMap(r => r.state === 'new' && r.axis && r.sub ? [{ kw: r.kw, row: r.row, axis: r.axis, sub: r.sub }] : []);
}
export function applyToIncluded(rows: BulkView[], edits: BulkEdit, to: Destination): BulkEdit {
  const next = { ...edits };
  for (const r of rows) if (r.include && (r.state === 'new' || r.state === 'needs_class')) next[r.row] = { ...next[r.row], to };
  return next;
}
export function retryRows(rows: BulkView[]): BulkRowIn[] {
  return rows.map(r => ({ kw: r.kw, ...((r.chosen || r.source !== 'llm_failed') && r.axis && r.sub ? { axis: r.axis, sub: r.sub } : {}) }));
}
