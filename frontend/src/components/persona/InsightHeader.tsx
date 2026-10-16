'use client';
import './insight.css';
import {useId, useState, type ReactNode} from 'react';
import type {InsightView} from './insightView';
export function InsightHeader({view,index,knownBadge,onRederive,rederiveDisabled}: {
  view: InsightView; index: number; knownBadge?: ReactNode; onRederive: () => void; rederiveDisabled: boolean;
}) {
  const [confirming,setConfirming] = useState(false);
  const dialogLabel = useId();
  return <section className="insight-header" aria-label={`Insight ${index + 1}`}>
    <div className="insight-headline"><span className="insight-number">Insight {index + 1}</span><h2>“{view.headline}”</h2>{knownBadge}</div>
    <ol className="insight-statements">{view.statements.map((statement,index) => <li key={index}><span className="insight-clamp-2" title={statement}>{statement}</span></li>)}</ol>
    {!!view.hashtags.length && <div className="insight-hashtags">{view.hashtags.map(tag => <span key={tag}>#{tag}</span>)}</div>}
    {!!view.personas.length && <p className="insight-personas"><span>기여 페르소나: </span>{view.personas.map((name,index) => <span key={name} title={name}>{index > 0 && ' · '}{name}</span>)}</p>}
    {view.legacy && <div className="insight-legacy"><p>예전 방식으로 만든 인사이트입니다. 다시 도출하면 제목·문장·흐름이 채워집니다.</p>
      <button type="button" className="ds-btn insight-hit" disabled={rederiveDisabled} onClick={() => setConfirming(true)}>다시 도출</button>
      <details><summary>자세히</summary><p>다시 도출하면 확정과 컨셉이 초기화됩니다.</p></details>
      {confirming && <dialog open aria-modal="true" aria-labelledby={dialogLabel} className="insight-confirm" ref={element => {if (element && !element.matches(':modal')) {element.close(); element.showModal();}}} onCancel={() => setConfirming(false)}>
        <p id={dialogLabel}>다시 도출하면 확정과 컨셉이 초기화됩니다. 이전 판은 판 목록에서 되돌릴 수 있습니다.</p>
        <button type="button" autoFocus className="ds-btn insight-hit" onClick={() => setConfirming(false)}>취소</button>
        <button type="button" className="ds-btn insight-hit" disabled={rederiveDisabled} onClick={() => {if (!rederiveDisabled) {setConfirming(false);onRederive();}}}>확인</button>
      </dialog>}
    </div>}
  </section>;
}
