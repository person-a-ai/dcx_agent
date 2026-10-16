'use client';

import type { PersonaState } from '../../lib/types';
import { Badge } from '../ds/Badge';
import './persona.css';

export type PersonaListProps = {
  groups: { clusterId: string; items: { id: string; name: string; status: PersonaState; future?: boolean }[] }[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};
function statusLabel(status: PersonaState) {
  if (status === 'done') return '완료';
  if (status === 'running') return '진행 중';
  if (status === 'failed' || status === 'interrupted') return '실패';
  return '대기';
}
export function PersonaList({ groups, selectedId, onSelect }: PersonaListProps) {
  if (!groups.some(group => group.items.length)) return <div className="persona-list-empty"><p>아직 확정된 페르소나가 없습니다.</p><a href="/pipeline/clustering">클러스터링으로</a></div>;
  return <nav className="persona-navigation" aria-label="페르소나 선택">
    <div className="persona-desktop-list">{groups.map(group => <section key={group.clusterId} aria-label={group.clusterId}>
      <h3 className="persona-cluster-title">{group.clusterId}</h3>
      <ul>{group.items.map(item => <li key={item.id}><button type="button" className="persona-list-item" aria-current={selectedId === item.id ? 'true' : undefined} onClick={() => onSelect(item.id)}>
        <span className={`persona-status persona-status-${item.status}`} aria-hidden="true" />
        <span className="persona-visually-hidden">{statusLabel(item.status)} </span>
        <span className="persona-list-name"><span className="persona-name" title={item.name}>{item.name}</span>{item.future && <Badge className="persona-future">FUTURE</Badge>}</span>
      </button></li>)}</ul>
    </section>)}</div>
    <label className="persona-mobile-select">페르소나 선택
      <select value={selectedId ?? ''} onChange={event => onSelect(event.target.value)}>
        <option value="" disabled>페르소나를 선택하세요</option>
        {groups.map(group => <optgroup key={group.clusterId} label={group.clusterId}>{group.items.map(item => <option key={item.id} value={item.id}>{item.name} · {statusLabel(item.status)}{item.future ? ' · FUTURE' : ''}</option>)}</optgroup>)}
      </select>
    </label>
  </nav>;
}
