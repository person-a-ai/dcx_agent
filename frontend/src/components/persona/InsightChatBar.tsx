'use client';
import './insight.css';
import {useId, useState, type ComponentProps} from 'react';
import type {InsightTarget} from '@/lib/types';
import ChatPanel from '../ChatPanel';
import {RevisionList} from './RevisionList';
export type InsightChatBarProps = {
  target: InsightTarget; onTarget: (target: InsightTarget) => void; conceptAvailable: boolean;
  /** Current selection label, e.g. Insight 2. */
  focusLabel: string; focusId?: string; chips: string[]; disabled: boolean;
  onSend: ComponentProps<typeof ChatPanel>['onSend']; historyCount: number;
  revisions: ComponentProps<typeof RevisionList>;
};
export function InsightChatBar({target,onTarget,conceptAvailable,focusLabel,focusId,chips,disabled,onSend,historyCount,revisions}: InsightChatBarProps) {
  const [historyOpen,setHistoryOpen] = useState(false);
  const historyId = useId();
  const id = focusId ?? (target === 'insights' ? '' : target.slice(target.indexOf(':') + 1));
  const label = target === 'insights' ? '인사이트 목록 전체 수정' : target.startsWith('concept:') ? '선택 컨셉 수정' : `${focusLabel}에 대해 수정 요청`;
  return <section className="insight-chat" aria-label="인사이트 수정">
    <h2>insight-chat</h2>
    <label>채팅 대상 <select className="ds-inp" value={target} disabled={disabled} onChange={event => onTarget(event.target.value as InsightTarget)}>
      <option value={`insight:${id}`} disabled={!id}>현재 인사이트</option><option value="insights">인사이트 목록</option><option value={`concept:${id}`} disabled={!conceptAvailable || !id}>선택 컨셉</option>
    </select></label>
    <p className="insight-focus">{label}</p>
    <ChatPanel initialMessage="수정할 내용을 알려 주세요." suggestions={chips} readonly={disabled} onSend={onSend}/>
    <button type="button" className="ds-btn insight-hit" disabled={historyCount === 0} aria-expanded={historyOpen && historyCount > 0} aria-controls={historyId} onClick={() => setHistoryOpen(!historyOpen)}>대화 기록 {historyCount}</button>
    {historyOpen && historyCount > 0 && <div id={historyId}><RevisionList {...revisions}/></div>}
  </section>;
}
