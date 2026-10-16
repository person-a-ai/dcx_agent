import { dimLabel, type FlowCard } from './insightView';
import './insight.css';
export function InsightFlow({ cards }: { cards: FlowCard[] }) {
  return <ol aria-label="Context 흐름" className="insight-flow">{cards.map((card,index)=><li key={card.contextId} className="insight-flow-step">
    {index > 0 && <span className="insight-flow-arrow" aria-hidden="true"><span className="insight-flow-arrow-wide">→</span><span className="insight-flow-arrow-narrow">↓</span></span>}
    <div className={`insight-flow-card${card.counter ? ' insight-flow-card--counter' : ''}`}>
      <p>{card.text}</p><div className="insight-flow-meta">{card.label} - {dimLabel(card.dim)}</div>
      {card.axis && <span className="insight-axis-badge">{card.axis}</span>}
      {card.counter && <span className="insight-counter-badge">⚠ 반례</span>}
    </div>
  </li>)}</ol>;
}
