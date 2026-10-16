'use client';
import { useId, useState, type ReactNode } from 'react';
import type { PersonaGrade } from '../../lib/types';
import { GradeMark } from './GradeMark';
import { ProvisionalBadge } from './ProvisionalBadge';
import { foldColumns } from './personaView';
import './persona.css';
export type CCMCell = { text: string; grade?: PersonaGrade | null; evidence?: ReactNode; more?: number };
export type CCMContext = { id: string; name: string; counter?: boolean; cells: Record<string, CCMCell> };
export const ccmRows = [ ['action', '행동'], ['state', '상태'], ['emotion', '감정'], ['barrier', '장벽'], ['pain_point', '페인포인트'], ['keywords', '키워드'], ['artifact', '쓰는 제품·수단'], ['satisfaction', '만족도'], ['opportunity', '기회'], ['evidence_count', '근거 수'] ] as const;
export function CCMTable({ contexts }: { contexts: CCMContext[] }) {
  const [opened, setOpened] = useState<string | null>(null);
  const id = useId();
  const { rows, columns } = foldColumns(contexts.length);
  if (!contexts.length) return <p>Context가 없습니다.</p>;
  return <div className="ccm-scroll" style={{ minWidth: 0, maxWidth: '100%', overflowWrap: 'anywhere' }}>{Array.from({ length: rows }, (_, group) => <table key={group} className="ds-tbl" style={{ tableLayout: 'fixed', width: '100%', marginBottom: 16 }}>
    <caption>CCM · {group + 1}/{rows}</caption>
    <thead><tr><th scope="col">항목</th>{contexts.slice(group * columns, (group + 1) * columns).map(context => <th scope="col" key={context.id} style={{ color: context.counter ? 'var(--danger)' : undefined }}>{context.id} {context.name}{context.counter && ' · 반례'}</th>)}</tr></thead>
    <tbody>{ccmRows.map(([key, label]) => <tr key={key}><th scope="row" className="ccm-sticky">{label} {key === 'opportunity' && <ProvisionalBadge/>}</th>{contexts.slice(group * columns, (group + 1) * columns).map((context, column) => {
      const cell = context.cells[key]; const cellId = `${id}-${group}-${column}-${key}`; const expanded = opened === cellId; const text = cell?.text?.trim() ? cell.text : null;
      return <td key={context.id} data-counter={context.counter || undefined} style={{ background: context.counter ? 'var(--danger-soft)' : undefined }}><button type="button" className="ds-btn ds-quiet ccm-cell-button" style={{ width: '100%', height: 'auto', padding: 4, whiteSpace: 'normal', overflowWrap: 'anywhere', display: 'block', textAlign: 'left' }} aria-label={`${context.id} · ${label} · ${text || "근거 부족"}`} aria-expanded={expanded} aria-controls={`${cellId}-evidence`} onClick={() => setOpened(expanded ? null : cellId)}>{text && cell?.grade !== undefined && <GradeMark grade={cell.grade}/>} {text ? <span className="ccm-clamp">{text}</span> : <span className="ccm-empty">근거 부족</span>}{text && (cell?.more ?? 0) > 0 && <span className="ccm-more">+{cell?.more}</span>}</button>{expanded && text && <p className="ccm-full-text">{text}</p>}<div id={`${cellId}-evidence`} hidden={!expanded}>{expanded && (cell?.evidence || '근거가 없습니다.')}</div></td>;
    })}</tr>)}</tbody>
  </table>)}</div>;
}
