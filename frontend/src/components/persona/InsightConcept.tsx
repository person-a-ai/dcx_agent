'use client';
import './insight.css';
import type {InsightConcept as Concept} from '@/lib/types';
import {Button} from '../ds/Button';
import {JourneyTable} from './JourneyTable';
import {contextLabels} from '@/lib/contextLabels';
import {displayValue} from './personaView';
const record = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
const text = displayValue;
function sourceLocation(value: unknown): string {
 const location = record(value);
 if (location.field === 'title') return '제목';
 if (location.field === 'body') return '본문';
 if (location.field === 'comment' || location.field === 'comments') return typeof location.idx === 'number' ? `댓글 ${location.idx + 1}` : '댓글';
 return '위치 미상';
}
function channelLabel(value: unknown): string {
 return contextLabels.channels[value as keyof typeof contextLabels.channels] ?? text(value);
}
export function ConceptDetail({concept}: {concept: Concept}) {
 return <section aria-label="경험 디자인 컨셉" className="ds-card space-y-5">
  <h2 className="ds-t-card">01 PERSONA <span style={{color:'var(--danger)'}}>🔴 합성값</span></h2><p>{text(record(concept.persona_profile).text ?? concept.persona_profile)}</p><p>{concept.basis}</p>
  <h2 className="ds-t-card">02 Pain Points</h2>{concept.pain_points.map((point,index) => <blockquote key={index}><p>{text(point.quote)}</p><footer>{channelLabel(point.channel)} · {sourceLocation(point.location)} · Context {text(point.context_id)}</footer></blockquote>)}
  <h2 className="ds-t-card">03 JOURNEY</h2><JourneyTable rows={concept.journey}/>
  <h3>제약 검사</h3><ul>{(concept.constraint_check ?? []).map((check,index) => <li key={index}>{check.verdict === 'ok' ? '✓ 충족' : check.verdict === 'violates' ? '✕ 위반' : '⚠ 검토'} · {check.constraint} · {check.reason}</li>)}</ul>
 </section>;
}
export function InsightConcept({concept,onCreate,disabled}: {concept?: Concept | null; onCreate: () => void; disabled: boolean}) {
 return <section className="insight-concept" aria-label="컨셉"><h2>컨셉</h2>{concept && !concept.outdated ? <ConceptDetail concept={concept}/> : <>{concept?.outdated && <p className="insight-caption">인사이트가 바뀌어 컨셉을 다시 만들어야 합니다</p>}<Button disabled={disabled} onClick={onCreate}>{concept?.outdated ? '컨셉 다시 만들기' : '선택 컨셉 만들기'}</Button></>}</section>;
}
