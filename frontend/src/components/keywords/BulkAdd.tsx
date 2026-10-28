'use client';
import { useEffect, useRef, useState } from 'react';
import { Banner, Badge, Button, Card, Select, TextArea, Table, Skeleton } from '@/components/ds';
import type { BulkPreview, BulkResult, BulkRowIn, Destination } from '@/lib/api/keywords';
import { addableItems, applyToIncluded, bulkSummary, decodeCsv, parseBulk, retryRows, viewRows, type BulkEdit } from '@/lib/logic/bulkKeywords';
import { displayError } from '@/lib/api/errors';
import { groupKey, groupLabel } from './taxonomy';
export type BulkState = { stage: 'closed' | 'input' | 'loading' | 'preview' | 'result'; text: string; parsed?: ReturnType<typeof parseBulk>; preview?: BulkPreview; edits: BulkEdit; result?: BulkResult; error?: string };
const empty = (): BulkState => ({ stage: 'closed', text: '', edits: {} });
const labels = { new: '추가 예정', existing: '이미 있음', in_list_duplicate: '리스트 안 중복', needs_class: '분류 필요', excluded: '제외' };
export function BulkAdd(props: { groups: Destination[]; disabled: boolean; readonly: boolean; preview: (rows: BulkRowIn[]) => Promise<BulkPreview>; add: (items: (Destination & { kw: string })[]) => Promise<BulkResult>; onReveal: (groups: Destination[]) => void; initialState?: BulkState }) {
 const [state, setState] = useState<BulkState>(props.initialState ?? empty);
 const [elapsed, setElapsed] = useState(0), [target, setTarget] = useState(''), [adding, setAdding] = useState(false);
 const request = useRef(0), addLock = useRef(false), file = useRef<HTMLInputElement>(null);
 useEffect(() => { if (state.stage !== 'loading') return; const timer = setInterval(() => setElapsed(n => n + 1), 1000); return () => clearInterval(timer); }, [state.stage]);
 useEffect(() => () => { request.current++; }, []);
 const parsed = state.parsed ?? parseBulk(state.text, props.groups);
 const rows = viewRows(state.preview ?? { rows: [] }, state.edits), summary = bulkSummary(rows), items = addableItems(rows);
 const options = <><option value="">분류 선택</option>{props.groups.map(g => <option key={groupKey(g)} value={groupKey(g)}>{groupLabel(g)}</option>)}</>;
 const reset = (stage: 'closed' | 'input') => { request.current++; setState({ ...empty(), stage }); };
 async function classify(retry = false) {
  if (props.disabled || addLock.current) return;
  const input = retry ? retryRows(rows) : parsed.rows;
  if (!input.length) return;
  const id = ++request.current; setElapsed(0);
  setState(s => ({ ...s, stage: 'loading', parsed, error: undefined, edits: retry ? s.edits : {} }));
  try { const preview = await props.preview(input); if (id === request.current) setState(s => ({ ...s, stage: 'preview', preview })); }
  catch (e) { if (id === request.current) setState(s => ({ ...s, stage: retry ? 'preview' : 'input', error: displayError(e) })); }
 }
 async function readFile(selected: File) {
  const id = ++request.current;
  try { const text = decodeCsv(await selected.arrayBuffer()); if (id === request.current) setState({ stage: 'input', text, edits: {} }); }
  catch { if (id === request.current) setState(s => ({ ...s, error: '파일을 읽지 못했습니다. CSV(UTF-8 또는 엑셀 CSV)인지 확인하세요.' })); }
 }
 async function submit() {
  if (props.disabled || addLock.current || !items.length) return;
  addLock.current = true; setAdding(true); const id = request.current;
  setState(s => ({ ...s, error: undefined }));
  try { const result = await props.add(items.map(({ kw, axis, sub }) => ({ kw, axis, sub }))); if (id === request.current) setState(s => ({ ...s, stage: 'result', result })); }
  catch (e) { if (id === request.current) setState(s => ({ ...s, error: displayError(e) })); }
  finally { addLock.current = false; setAdding(false); }
 }
 function edit(row: number, change: BulkEdit[number]) { setState(s => ({ ...s, edits: { ...s.edits, [row]: { ...s.edits[row], ...change } } })); }
 const added = state.result?.results.filter(r => r.status === 'added').length ?? 0;
 return <Card aria-labelledby="kwb-title"><div className="kwb-head"><div><h2 className="ds-t-card" id="kwb-title">키워드 일괄 추가</h2><p className="ds-t-caption">CSV나 리스트로 정리한 키워드를 한 번에 넣습니다. 분류가 없으면 자동으로 제안합니다.</p></div>{!props.readonly && (state.stage === 'closed' ? <Button disabled={props.disabled} onClick={() => reset('input')}>일괄 추가하기</Button> : <Button variant="quiet" size="sm" onClick={() => reset('closed')}>닫기</Button>)}</div>
 {props.readonly ? <div className="kwb-body"><Banner>읽기 전용 버전에서는 키워드를 추가할 수 없습니다.</Banner></div> : state.stage !== 'closed' && <div className="kwb-body">
 {state.error && <Banner tone="danger">{state.error}</Banner>}
 {state.stage === 'input' && <><div className="kwb-input"><TextArea label="키워드 리스트" value={state.text} onChange={e => { request.current++; setState({ stage: 'input', text: e.target.value, edits: {} }); }} placeholder={'한 줄에 하나씩, 또는 쉼표로 구분해 붙여넣으세요.\n엑셀 표를 복사해 붙여넣어도 됩니다.\n\n키워드,축,하위분류\n층간소음,물리,감각\n퇴근 후 휴식,물리,시간\n불안감'} /><span className="ds-hint">머리글이 있으면 키워드·축·하위분류 열을 인식합니다. 한 번에 최대 500행.</span></div><div className="kwb-row-actions"><input ref={file} hidden type="file" accept=".csv,text/csv,text/plain" onChange={e => { const selected = e.target.files?.[0]; e.target.value = ''; if (selected) void readFile(selected); }} /><Button onClick={() => file.current?.click()}>CSV 파일 선택하기</Button><span className="ds-t-caption">또는 위에 붙여넣기 · {`${parsed.rows.length}행 인식`}</span><Button variant="primary" style={{ marginLeft: 'auto' }} disabled={!parsed.rows.length || props.disabled || adding} onClick={() => void classify()}>미리보기</Button></div>{!parsed.rows.length && <Banner>키워드를 찾지 못했습니다</Banner>}</>}
 {parsed.truncated > 0 && <Banner tone="warning">{`앞 500행만 불러왔습니다(나머지 ${parsed.truncated}행 제외)`}</Banner>}
 {parsed.tooLong.length > 0 && <Banner tone="warning">{`100자를 넘는 ${parsed.tooLong.length}개는 제외했습니다`}</Banner>}
 {state.stage === 'loading' && <><p role="status" aria-live="polite">{`처리 중… 분류 없는 키워드 ${parsed.rows.filter(r => !r.axis || !r.sub).length}개를 자동 분류하는 중 · 보통 10~40초 · 경과 ${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`}</p><Skeleton height={40} /><Skeleton height={200} /><Button disabled>미리보기</Button></>}
 {state.stage === 'preview' && <>{state.preview?.classifyError ? <Banner tone="warning" actions={<Button size="sm" disabled={props.disabled || adding} onClick={() => void classify(true)}>자동 분류 다시 하기</Button>}>{`자동 분류에 실패했습니다(원인: ${state.preview.classifyError.message}). 분류가 필요한 ${summary.needsClass}개는 직접 고르거나 다시 시도하세요.`}</Banner> : parsed.rows.some(r => !r.axis || !r.sub) && <Banner>{`${rows.length}행을 읽었습니다. 분류가 없던 ${parsed.rows.filter(r => !r.axis || !r.sub).length}개는 자동 제안입니다. 확인하고 필요하면 바꾸세요.`}</Banner>}
 <div className="kwb-summary" aria-label="미리보기 요약">{[['추가 예정', summary.new], ['이미 있음', summary.existing], ['리스트 안 중복', summary.inListDuplicate], ['분류 필요', summary.needsClass], ['제외', summary.excluded]].map(([label, count]) => <Badge key={label} tone={label === '추가 예정' ? 'info' : label === '분류 필요' ? 'warning' : 'neutral'}>{`${label} ${count}`}</Badge>)}</div>
 <div className="kwb-bulk"><Select label="선택한 행 분류 일괄 변경" value={target} disabled={adding} onChange={e => setTarget(e.target.value)}>{options}</Select><Button disabled={!target || adding} onClick={() => { const to = props.groups.find(g => groupKey(g) === target); if (to) setState(s => ({ ...s, edits: applyToIncluded(rows, s.edits, to) })); }}>모두 이 그룹으로</Button></div>
 <div className="kwb-scroll"><Table className="kwb-table"><thead><tr><th><input type="checkbox" aria-label="전체 선택" disabled={adding || !rows.some(r => r.state !== 'existing' && r.state !== 'in_list_duplicate')} checked={rows.filter(r => r.status !== 'existing' && r.status !== 'in_list_duplicate').every(r => r.include)} onChange={e => { const include = e.target.checked; setState(s => ({ ...s, edits: { ...s.edits, ...Object.fromEntries(rows.filter(r => r.status !== 'existing' && r.status !== 'in_list_duplicate').map(r => [r.row, { ...s.edits[r.row], include }])) } })); }} /></th><th>키워드</th><th>분류</th><th>분류 출처</th><th>상태</th></tr></thead><tbody>{rows.map(r => { const off = r.status === 'existing' || r.status === 'in_list_duplicate'; return <tr key={r.row} className={!r.include ? 'kwb-off' : undefined}><td><input type="checkbox" aria-label={`${r.kw} 포함`} disabled={off || adding} checked={r.include} onChange={e => edit(r.row, { include: e.target.checked })} /></td><td>{r.kw}</td><td>{off ? r.axis && r.sub ? groupLabel({ axis: r.axis, sub: r.sub }) : '—' : <select aria-label={`${r.kw} 분류`} disabled={adding} value={r.axis && r.sub ? groupKey({ axis: r.axis, sub: r.sub }) : ''} onChange={e => { const to = props.groups.find(g => groupKey(g) === e.target.value); if (to) edit(r.row, { to }); }}>{options}</select>}</td><td>{r.chosen ? <Badge>직접 선택</Badge> : r.source ? <Badge tone={r.source === 'llm' ? 'success' : r.source === 'llm_failed' ? 'warning' : 'neutral'}>{r.source === 'input' ? '입력값' : r.source === 'llm' ? '자동 제안' : '분류 실패'}</Badge> : '—'}</td><td><Badge tone={r.state === 'new' ? 'info' : r.state === 'needs_class' ? 'warning' : 'neutral'}>{labels[r.state]}</Badge>{r.duplicateOf && <span className="ds-t-caption">{`“${r.duplicateOf.kw}” · ${groupLabel(r.duplicateOf)}`}</span>}{r.firstRow !== undefined && <span className="ds-t-caption">{`${r.firstRow + 1}행과 같음`}</span>}</td></tr>; })}</tbody></Table></div>
 <p className="ds-t-caption">“이미 있음”과 “리스트 안 중복”은 추가하지 않습니다. “분류 필요”는 분류를 고르기 전까지 추가하지 않습니다.</p><div className="kwb-row-actions"><Button disabled={adding} onClick={() => { request.current++; setState(s => ({ ...s, stage: 'input', error: undefined })); }}>입력으로 돌아가기</Button><Button variant="primary" style={{ marginLeft: 'auto' }} disabled={!items.length || props.disabled || adding} loading={adding} onClick={() => void submit()}>{`${items.length}개 추가하기`}</Button></div></>}
 {state.stage === 'result' && state.result && <><Banner tone="success" actions={<Button size="sm" onClick={() => props.onReveal([...new Map(state.result!.keywords.map(k => [groupKey(k), { axis: k.axis, sub: k.sub }])).values()])}>추가한 키워드 보기</Button>}>{`키워드 ${added}개를 추가했습니다. ${state.result.results.length - added}개는 건너뛰었습니다.`}</Banner>{state.result.results.some(r => r.status !== 'added') && <Table className="kwb-table"><caption>건너뛴 행만 표시합니다.</caption><thead><tr><th>키워드</th><th>결과</th></tr></thead><tbody>{state.result.results.filter(r => r.status !== 'added').map(r => <tr key={r.index}><td>{items[r.index]?.kw}</td><td><Badge>{r.status === 'duplicate' ? '이미 있음' : '분류 오류'}</Badge></td></tr>)}</tbody></Table>}<div className="kwb-row-actions"><Button style={{ marginLeft: 'auto' }} onClick={() => reset('input')}>새 리스트 넣기</Button></div></>}
 </div>}</Card>;
}
