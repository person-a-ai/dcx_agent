import { formatMetric } from './personaView';
import { ProvisionalBadge } from './ProvisionalBadge';
import './persona.css';

export type OpportunityBar = { id: string; label: string; value: number | null };
export function OpportunityBars({ bars, mean }: { bars: OpportunityBar[]; mean: number | null }) {
  const ranked = [...bars].sort((a, b) => (b.value ?? -Infinity) - (a.value ?? -Infinity));
  const max = Math.max(1, ...ranked.map(bar => bar.value ?? 0), mean ?? 0);
  return <figure className="opportunity-bars"><figcaption>기회 순위 <ProvisionalBadge/> · 평균 {formatMetric(mean)}</figcaption>
    {ranked.length ? <ol className="opportunity-ranking">{ranked.map((bar, index) => <li key={bar.id} className="opportunity-row">
      <span className="opportunity-rank">{index + 1}</span>
      <span className="opportunity-sentence">{bar.label}</span>
      <div className="opportunity-bar-area">
        {bar.value !== null && <span className="opportunity-bar" aria-hidden="true" style={{width: `${Math.max(0, bar.value) / max * 100}%`}}/>}
        {mean !== null && <span className="opportunity-mean" data-mean={mean} role="img" aria-label={`평균 ${formatMetric(mean)}`} style={{left: `${Math.max(0, mean) / max * 100}%`}}/>}
      </div>
      <span className="opportunity-value">{formatMetric(bar.value)}</span>
    </li>)}</ol> : <p>기회 정보가 없습니다.</p>}
  </figure>;
}
