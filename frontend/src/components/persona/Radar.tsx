import { formatMetric, formatCount } from './personaView';
import './insight.css';
import { ProvisionalBadge } from './ProvisionalBadge';
export const radarAxes = { Computed: '맞춤형 서비스가 필요해', Connected: '실시간으로 직접 보고 싶어', Shared: '함께 즐기고 싶어' } as const;
export type RadarValues = Record<keyof typeof radarAxes, { raw: number | null; percentile: number | null }>;
type RadarMean = Record<keyof RadarValues, number | null>;
export function Radar({ values, mean, label }: { values: RadarValues; mean: RadarMean | null; label: string }) {
  const axes = Object.keys(radarAxes) as (keyof RadarValues)[];
  const coord = (index: number, value: number) => {
    const angle = -Math.PI / 2 + index * Math.PI * 2 / 3;
    return `${180 + Math.cos(angle) * 70 * value},${100 + Math.sin(angle) * 70 * value}`;
  };
  const safe = (value: number | null) => value !== null && Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
  const completeMean = mean !== null && axes.every(axis => typeof mean[axis] === 'number' && Number.isFinite(mean[axis]));
  const summary = `${label}: ${axes.map(axis => `${axis}: 원값 ${formatMetric(values[axis].raw)}, 백분위 ${formatCount(values[axis].percentile)}`).join('; ')}${mean ? `; 평균(전체 인사이트): ${axes.map(axis => `${axis} ${mean[axis] === null ? '평균 없음' : formatMetric(mean[axis])}`).join(', ')}` : ''}`;
  const empty = axes.every(axis => values[axis].raw === null);
  return <figure className="insight-chart insight-radar"><figcaption>경험 차원 레이더<ProvisionalBadge/></figcaption>
    {empty ? <p className="insight-chart-empty">경험 차원 값이 없습니다</p> : <>
      <svg viewBox="0 0 360 190" role="img" aria-label={summary}><title>{summary}</title>
        {[.25,.5,.75,1].map(level => <polygon key={level} points={axes.map((_,i)=>coord(i,level)).join(' ')} fill="none" stroke="var(--line)"/>)}
        <polygon points={axes.map((axis,i)=>coord(i,safe(values[axis].raw))).join(' ')} fill="var(--action-soft)" stroke="var(--action)"/>
        {completeMean && mean && <polygon points={axes.map((axis,i)=>coord(i,safe(mean[axis]))).join(' ')} fill="none" stroke="var(--line-strong)" strokeDasharray="4 4"/>}
        {axes.map((axis,i)=>{const [x,y]=coord(i,1.22).split(',');return <text key={axis} x={x} y={y} textAnchor="middle" className="insight-radar-axis">{axis}<tspan x={x} dy="16" className="insight-radar-value">{formatMetric(values[axis].raw)}</tspan></text>;})}
      </svg>
      <p className="insight-chart-legend"><span className="insight-radar-key">— {label}</span>{completeMean && <span> · --- 평균(전체 인사이트)</span>}</p>
    </>}
  </figure>;
}
