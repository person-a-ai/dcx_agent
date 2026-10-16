'use client';
import { useMemo, useState } from 'react';
import type { PersonaMap, PersonaZone } from '../../lib/types';
import { zoneName, formatMetric, formatCount, MAP_TICKS, zoneRegions, jitter } from './personaView';
import { ProvisionalBadge } from './ProvisionalBadge';
const shapes = ['circle','square','triangle','diamond','pentagon'];
const symbols = ['●','■','▲','◆','⬟'];
const tones = ['--ink-strong','--ink','--line-strong'];
const x = (value: number) => 60 + Math.max(0, Math.min(1, value)) * 480;
const y = (value: number) => 340 - Math.max(0, Math.min(1, value)) * 320;
function Shape({ index }: { index: number }) {
  if (index === 1) return <rect x={-7} y={-7} width={14} height={14}/>;
  if (index === 2) return <polygon points="0,-9 8,7 -8,7"/>;
  if (index === 3) return <polygon points="0,-9 9,0 0,9 -9,0"/>;
  if (index === 4) return <polygon points="0,-9 8.6,-2.8 5.3,7.3 -5.3,7.3 -8.6,-2.8"/>;
  return <circle r={7}/>;
}
function ZoneLayer({ base }: { base: PersonaMap['base'] }) {
  const regions = useMemo(() => zoneRegions(base), [base]);
  return <g>
      {(Object.keys(regions) as PersonaZone[]).map(zone => <polygon key={zone} data-zone={zone} points={regions[zone].map(([i,s]) => `${60+i*480},${340-s*320}`).join(' ')} fill={`var(--${zone === 'F' ? 'danger-soft' : zone === 'C' ? 'warning-soft' : 'sunken'})`}/>)}

  </g>;
}
export type OpportunityMapProps = { map: PersonaMap; highlightedId?: string | null; selectedId?: string | null; selectedPersonaId?: string | null; focusPersonaId?: string | null; compact?: boolean; onHighlight?: (id: string | null) => void; onSelect?: (id: string) => void; onOpenCard?: (personaId: string, contextId: string) => void };
export function OpportunityMap({ map, highlightedId, selectedId, selectedPersonaId, focusPersonaId, compact, onHighlight, onSelect, onOpenCard }: OpportunityMapProps) {
  const [hiddenClusters, setHiddenClusters] = useState<string[]>([]);
  const validPoints = map.points.filter(point => point.i !== null && point.s !== null);
  const missingCount = map.points.length - validPoints.length;
  const overlapGroups = new Map<string, string[]>();
  for (const point of validPoints) {
    const position = `${point.i}:${point.s}`;
    overlapGroups.set(position, [...(overlapGroups.get(position) ?? []), point.context_id]);
  }
  for (const group of overlapGroups.values()) group.sort();
  const clusters = [...new Set([...(map.legend ?? []).map(row => row.cluster_id), ...map.points.map(point => point.cluster_id)])].sort((a,b) => a.localeCompare(b, undefined, {numeric:true}));
  const legend = new Map((map.legend ?? []).map(row => [row.cluster_id, row]));
  const toggle = (cluster: string) => setHiddenClusters(current => current.includes(cluster) ? current.filter(id => id !== cluster) : [...current, cluster]);
  const summary = (['A','B','C','D','E','F'] as PersonaZone[]).map(zone => `${zoneName(zone)} ${formatCount(map.points.filter(p => p.zone === zone).length)}개`).join(', ');
  const labelPlacements = new Map<string, {anchor: 'start' | 'end'; x: number; y: number}>();
  const placed: {left:number;right:number;y:number}[] = [];
  for (const point of [...validPoints].sort((a,b)=>a.context_id.localeCompare(b.context_id))) {
    if (hiddenClusters.includes(point.cluster_id) || (point.context_id !== highlightedId && point.context_id !== selectedId && point.persona_id !== focusPersonaId)) continue;
    const group = overlapGroups.get(`${point.i}:${point.s}`)!;
    const [dx,dy] = jitter(group.indexOf(point.context_id),group.length);
    const px=x(point.i!)+dx, py=y(point.s!)+dy;
    const width = point.context_id.length * 6.5;
    const anchor = px + 12 + width > 596 ? 'end' : 'start';
    const labelX = anchor === 'end'
      ? Math.max(4 + width, Math.min(596, px - 12))
      : Math.max(4, Math.min(596 - width, px + 12));
    const left = labelX - (anchor === 'end' ? width : 0);
    const right = left + width;
    const clampY = (value: number) => Math.max(12, Math.min(420, value));
    // Prefer the interior at either edge; all candidates include text height.
    const direction = py < 36 ? 1 : -1;
    const preferred = clampY(py + direction * 12);
    const candidates = [preferred];
    for (let step = 1; step <= 34; step++) {
      candidates.push(clampY(preferred + direction * step * 12), clampY(preferred - direction * step * 12));
    }
    const labelY = candidates.find(candidate => !placed.some(label => label.left < right && left < label.right && Math.abs(label.y-candidate)<12)) ?? preferred;
    placed.push({left,right,y:labelY});
    labelPlacements.set(point.context_id, {anchor, x:labelX-px, y:labelY-py});
  }
  const lines = [ [[0,map.base.s_line],[1,map.base.s_line]], map.base.diag1, map.base.diag2 ];
  return <figure data-compact={compact || undefined} style={{ margin: 0, minWidth: 0 }}><figcaption className="ds-t-label">Opportunity Map · Context {formatCount(map.points.length)}개 · 기회 <ProvisionalBadge/></figcaption>
    <svg viewBox="0 0 600 420" role="img" aria-label={`Opportunity Map: ${summary}`} style={{ width:'100%',display:'block',minHeight:320 }}>
      <ZoneLayer base={map.base}/>
      <path d="M60 20V340H540" fill="none" stroke="var(--ink)"/>
      {lines.map((line,index) => <polyline key={index} data-baseline={index} points={line.map(([i,s]) => `${x(i)},${y(s)}`).join(' ')} fill="none" stroke="var(--line-strong)" strokeDasharray="4 4"/>)}
      {(['x','y'] as const).map(axis => MAP_TICKS.map(tick => <text key={`${axis}-${tick}`} data-axis-tick={axis} x={axis === 'x' ? x(tick) : 52} y={axis === 'x' ? 359 : y(tick)+4} textAnchor={axis === 'x' ? 'middle' : 'end'} fontSize={11} fill="var(--sub)">{tick}</text>))}
      <text x={300} y={392} textAnchor="middle" fill="var(--ink)">중요도</text><text x={14} y={180} transform="rotate(-90 14 180)" textAnchor="middle" fill="var(--ink)">만족도</text>
      {validPoints.filter(point => !hiddenClusters.includes(point.cluster_id)).map(point => {
        if (point.i === null || point.s === null) return null;
        const entry = legend.get(point.cluster_id);
        const shape = entry?.shape ?? point.shape ?? shapes[clusters.indexOf(point.cluster_id)] ?? 'circle';
        const cluster = shapes.indexOf(shape);
        const tone = entry?.personas.find(p => p.persona_id === point.persona_id)?.tone ?? (typeof point.tone === 'string' ? point.tone : tones[Number(point.tone) % tones.length]);
        const highlighted = highlightedId === point.context_id;
        const selected = selectedPersonaId === point.persona_id;
        const color = `var(${selected ? '--blue' : tone})`;
        const group = overlapGroups.get(`${point.i}:${point.s}`)!;
        const count = group.length;
        const [dx,dy] = jitter(group.indexOf(point.context_id), count);
        const label = labelPlacements.get(point.context_id);
        return <g key={point.context_id} data-context-id={point.context_id} data-highlighted={highlighted} data-shape={shape} opacity={focusPersonaId && focusPersonaId !== point.persona_id ? 0.25 : 1} transform={`translate(${x(point.i)+dx} ${y(point.s)+dy})`} fill={point.counter ? 'none' : color} stroke={color} strokeWidth={highlighted ? 3 : 2} style={{cursor:'pointer'}} onMouseEnter={() => onHighlight?.(point.context_id)} onMouseLeave={() => onHighlight?.(null)} onClick={() => {if (onSelect) onSelect(point.context_id); else {onHighlight?.(point.context_id); onOpenCard?.(point.persona_id,point.context_id);}}}>
          <title>{`${point.context_id} · ${point.persona_id} · ${zoneName(point.zone)} · 중요도 ${formatMetric(point.i)} · 만족도 ${formatMetric(point.s)} · 기회 ${formatMetric(point.odi)} (잠정)${point.counter ? " · 반례" : ""}${count > 1 ? ` · 겹친 Context ${formatCount(count)}개` : ""}`}</title>
          {point.context_id === selectedId && <circle data-selected-marker="true" r={16} fill="none" strokeWidth={2}/>}
          {highlighted && <circle r={13} fill="none" strokeDasharray="3 2"/>}<Shape index={cluster}/>
          {point.star && <text x={-5} y={-14} fill={color} stroke="none">★</text>}{label && <text data-label={point.context_id} textAnchor={label.anchor} x={label.x} y={label.y} fill={color} stroke="none" fontSize={11}>{point.context_id}</text>}
        </g>;
      })}
    </svg>
    <ul className="persona-zone-legend" aria-label="구역 범례">{(['A','B','C','D','E','F'] as PersonaZone[]).map(zone => <li key={zone} data-zone-name={zone} style={{color:`var(--${zone === 'F' ? 'danger' : zone === 'C' ? 'warning' : 'sub'})`}}>{zoneName(zone)}</li>)}</ul>
    <div className="persona-map-legend" aria-label="클러스터 범례" style={{display:'flex',flexWrap:'wrap',gap:8,marginTop:8}}>{clusters.map(cluster => <button key={cluster} data-cluster={cluster} aria-label={`Persona ${[...new Set(map.points.filter(p => p.cluster_id === cluster).map(p => p.persona_id))].join(', ')}`} title={legend.get(cluster)?.personas.map(p => p.persona_name).join(', ')} type="button" className="ds-chip" aria-pressed={!hiddenClusters.includes(cluster)} onClick={() => toggle(cluster)}>{symbols[shapes.indexOf(legend.get(cluster)?.shape ?? shapes[clusters.indexOf(cluster)])] || '●'} {cluster}{legend.get(cluster)?.cluster_label && legend.get(cluster)?.cluster_label !== cluster ? ` · ${legend.get(cluster)?.cluster_label}` : ''}</button>)}</div>
    {missingCount > 0 && <p className="ds-t-caption">지도에 없는 Context {missingCount}개는 표에서 확인하세요.</p>}
    {map.points.length === 0 && <p className="ds-t-caption">기회 지도를 만들 Context가 없습니다.</p>}
    <p className="ds-t-caption">속 빈 모양 · 반례 Context / ★ 몰랐고 기회도 큰 지점 · 겹친 점은 아래 Context 표에서 각각 확인할 수 있습니다.</p>
  </figure>;
}
