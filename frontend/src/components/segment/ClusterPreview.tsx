'use client';
import { useState } from 'react';
import type { SegmentPreview, SegmentPreviewPersona, SegmentRepresentative } from '@/lib/types';
import { KSuggestChart } from './KSuggestChart';

const orders = [['center', '중심순 대표 원문'], ['edge', '가장자리순 · 숨은 니즈 후보']] as const;

function Sources({ reps, edges }: { reps: SegmentRepresentative[]; edges?: SegmentRepresentative[] }) {
    const [order, setOrder] = useState<'center' | 'edge'>('center');
    const shown = order === 'edge' ? edges ?? [] : reps;
    return <details>
        <summary className="cursor-pointer ds-t-caption">원문 보기</summary>
        <div role="group" aria-label="원문 정렬" className="my-2 flex flex-wrap gap-2">
            {orders.map(([key, label]) => <button key={key} type="button" aria-pressed={order === key} disabled={key === 'edge' && !edges?.length}
                className={`ds-btn ${order === key ? 'ds-primary' : 'ds-secondary'}`} onClick={() => setOrder(key)}>{label}</button>)}
        </div>
        {shown.map((rep, i) => <blockquote key={`${rep.docId}:${i}`} className="my-3 border-l-2 pl-3 break-words"><p>{rep.text}</p><cite className="ds-t-caption">{rep.source} · {rep.field}{rep.idx !== null ? ` ${rep.idx}` : ''}</cite></blockquote>)}
    </details>;
}

function Chips({ words }: { words: string[] }) {
    return <div className="flex min-w-0 flex-wrap gap-2">{words.map((word, i) => <span key={`${word}:${i}`} className="min-w-0 rounded-full border border-[var(--line)] px-2 py-1 ds-t-caption">#{word}</span>)}</div>;
}

function PersonaPreview({ persona }: { persona: SegmentPreviewPersona }) {
    return <li className="min-w-0 space-y-2 rounded-lg border border-[var(--line)] p-3">
        <p className="ds-t-caption">{persona.id} · 문서 {persona.docs.toLocaleString('ko-KR')}건</p>
        {persona.name && <h4 className="ds-t-label">{persona.name} · 초안</h4>}
        {persona.desire && <p><span className="ds-t-caption">Desire </span>{persona.desire}</p>}
        {persona.goals.length > 0 && <ul className="list-disc pl-5">{persona.goals.map((goal, i) => <li key={i}>{goal}</li>)}</ul>}
        {persona.draftFailed && <p className="ds-t-caption">Desire·Goal 초안 생성 실패 · 최종 단계에서 다시 시도</p>}
        <Chips words={persona.centrality.slice(0, 10)}/>
        <Sources reps={persona.reps} edges={persona.edges}/>
    </li>;
}

export function ClusterPreview({ preview }: { preview: SegmentPreview }) {
    const personas = preview.personas ?? [];
    return <section aria-label="미리보기 · Persona·관계망·토픽 분석 진행 중" className="min-w-0 space-y-4 [overflow-wrap:anywhere]">
        <h2 className="ds-t-card">미리보기 · Persona·관계망·토픽 분석 진행 중</h2>
        <p className="ds-t-caption">{preview.mode === 'target' ? `목표 페르소나 ${preview.k}개 · 기타 ${(preview.other ?? 0).toLocaleString()}건` : `k = ${preview.k}`}{personas.length ? ` · Persona ${personas.length}개` : ''}</p>
        {preview.naming === 'pending' && <p role="status">군집 이름 만드는 중</p>}
        {preview.personaDrafting === 'pending' && <p role="status">Persona Desire·Goal 만드는 중</p>}
        {preview.mode !== 'target' && <div className="min-w-0 max-w-sm"><KSuggestChart k={preview.suggested} silhouette={preview.silhouette} sample={preview.sample}/></div>}
        <div className="min-w-0 divide-y rounded-xl border border-[var(--line)] px-5">
            {preview.clusters.map(cluster => {
                const members = personas.filter(persona => persona.cluster === cluster.id);
                return <article key={cluster.id} className="space-y-4 py-5">
                    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                        <div className="min-w-0 space-y-3">
                            <p className="ds-t-caption">{cluster.id} · 문서 {cluster.docs.toLocaleString('ko-KR')}건</p>
                            {cluster.name && <h3 className="ds-t-label">{cluster.name} · 이름 초안</h3>}
                            {cluster.nameFailed && <p className="ds-t-caption">이름 생성 실패 · 최종 단계에서 다시 시도</p>}
                            <Sources reps={cluster.reps} edges={cluster.edges}/>
                        </div>
                        <div className="min-w-0 space-y-3">
                            <h3 className="ds-t-label">키워드</h3>
                            <Chips words={cluster.keywords}/>
                        </div>
                    </div>
                    {members.length > 0 && <div className="min-w-0 space-y-2">
                        <h3 className="ds-t-label">Persona {members.length}개</h3>
                        <ul className="grid grid-cols-1 gap-3 md:grid-cols-2">{members.map(persona => <PersonaPreview key={persona.id} persona={persona}/>)}</ul>
                    </div>}
                </article>;
            })}
        </div>
    </section>;
}
