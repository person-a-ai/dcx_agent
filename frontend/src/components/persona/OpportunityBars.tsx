import type { BarRow } from './insightView';
import './insight.css';
export function OpportunityBars({ rows, mean }: { rows: BarRow[]; mean: number | null }) {
  const empty = rows.every(row => row.value === null);
  const max = Math.max(1, ...rows.map(row=>row.value ?? 0), mean ?? 0);
  const percent = (value: number) => `${Math.max(0,value) / max * 100}%`;
  const summary = rows.map(row=>`${row.label}: ${row.value ?? '값 없음'}`).join(', ') + (mean !== null ? `; 평균 ${mean.toFixed(1)}` : '');
  return <figure className="insight-chart insight-bars"><figcaption>Opportunity Score</figcaption>
    {empty ? <p className="insight-chart-empty">이 인사이트의 Context에 ODI 값이 없습니다</p> :
      <div className="insight-bars-scroll"><div role="img" aria-label={summary} className="insight-bars-grid" style={{gridTemplateColumns:`repeat(${rows.length}, minmax(72px, 1fr))`}}>
        <div className="insight-bars-plot">
          {mean !== null && <div className="insight-bars-mean" style={{bottom:percent(mean)}}><span>평균 {mean.toFixed(1)}</span></div>}
        </div>
        {rows.map(row=><div className="insight-bars-column" key={row.contextId}>
          <div className="insight-bar-slot">{row.value !== null && <div className="insight-bar" style={{height:percent(row.value)}}><span className="insight-bar-value">{row.value.toFixed(1)}</span></div>}</div>
          <div className="insight-bar-label"><span>{row.short}</span><span>{row.label}</span>{row.value === null && <span>값 없음</span>}</div>
        </div>)}
      </div></div>}
  </figure>;
}
