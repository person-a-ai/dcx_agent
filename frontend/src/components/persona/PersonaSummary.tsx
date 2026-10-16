'use client';

import { useId, useState } from 'react';
import type { PersonaPainPoint } from '../../lib/types';
import { Badge } from '../ds/Badge';
import { GradeMark } from './GradeMark';
import './persona.css';

export type PersonaSummaryProps = {
  name: string;
  future?: boolean;
  meta: string;
  desire: string;
  goals: string[];
  painPoints: PersonaPainPoint[] | undefined;
  legacy: boolean;
  onOpenEvidence: (index: number) => void;
};
export function PersonaSummary({ name, future, meta, desire, goals, painPoints, legacy, onOpenEvidence }: PersonaSummaryProps) {
  const [expanded, setExpanded] = useState(false);
  const id = useId();
  const points = painPoints ?? [];
  return <section className="persona-summary" aria-labelledby={`${id}-name`}>
    <header className="persona-summary-header"><h2 id={`${id}-name`}>{name}</h2>{future && <Badge>FUTURE</Badge>}<p>{meta}</p></header>
    <div className="persona-desire-goals">
      <p id={`${id}-goals`} className={expanded ? 'persona-goals-expanded' : 'persona-goals-collapsed'}>Desire · {desire} · Goal · {goals.join(', ')}</p>
      {!legacy && goals.length > 0 && <button type="button" aria-expanded={expanded} aria-controls={`${id}-goals`} onClick={() => setExpanded(!expanded)}>{expanded ? '접기' : '더 보기'}</button>}
    </div>
    <section className="persona-pain-points" aria-labelledby={`${id}-pains`}>
      <h3 id={`${id}-pains`}>Pain Points</h3>
      {legacy ? <p>근거 탐색을 다시 실행한 뒤 페르소나를 다시 만들면 페인포인트가 표시됩니다. 인사이트도 다시 만들어야 합니다. <a href="/pipeline/evidence">근거 탐색으로</a></p> : points.length === 0 ? <p>근거가 부족해 페인포인트를 만들지 못했습니다.</p> : <>
        <ol>{points.map((point, index) => <li key={index} className="ds-card persona-pain-item"><button type="button" className="persona-pain-button" onClick={() => onOpenEvidence(index)}>
          <span className="persona-pain-text">{point.text}</span>
          <span className="persona-pain-meta"><GradeMark grade={point.grade} />{point.context_ids.map(context => <Badge key={context}>{context}</Badge>)}<span>근거 {point.cite.length}건</span></span>
        </button></li>)}</ol>
        {points.length < 3 && <p>근거가 적어 {points.length}개만 찾았습니다.</p>}
      </>}
    </section>
  </section>;
}
