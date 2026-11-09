'use client';
import { useEffect, useState } from 'react';
import { Badge, Banner, Card, Table } from '@/components/ds';
import * as api from '@/lib/api/segment';
import { displayError } from '@/lib/api/errors';
import type { SegmentTargetReport, TargetPersonaReport, TargetQuote } from '@/lib/types';

const RESULTS = ['효과 있음', '일시적', '효과 없음'] as const;
const percent = (part: number, whole: number) => whole ? `${Math.round(part / whole * 1000) / 10}%` : '0%';

function Quote({ quote }: { quote: TargetQuote }) {
    return <blockquote className="space-y-1 border-l-2 border-[var(--line)] pl-3">
        <p className="ds-t-body">{quote.sentences.join(' ')}</p>
        <p className="ds-t-caption">— {quote.title || '제목 없음'}{quote.source ? ` · ${quote.source}` : ''}{quote.tried && quote.tried !== '언급 없음' ? ` · ${quote.tried} → ${quote.result}` : ''}{quote.cause ? ` · 원인: ${quote.cause}` : ''}</p>
    </blockquote>;
}

/** Docs, threshold, removals, first-person share, causes, tried solutions and quotes for one persona card. */
export function TargetPersona({ persona }: { persona: TargetPersonaReport }) {
    const needs = persona.needs;
    const examples = needs?.examples ?? [];
    const quotes = [...examples, ...persona.quotes.filter(q => !examples.some(e => e.docId === q.docId))].slice(0, 10);
    return <article className="min-w-0 space-y-4 py-5" aria-label={persona.name}>
        <div className="flex flex-wrap items-center gap-2"><h3 className="ds-t-card">{persona.name}</h3><Badge>{persona.id}</Badge>
            {persona.flags.includes('no_match') && <Badge tone="warning">맞는 문서 없음</Badge>}</div>
        {persona.card.pain && <p className="ds-t-caption">카드 Pain: {persona.card.pain}</p>}
        <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div><dt className="ds-t-caption">배정 문서</dt><dd className="ds-t-body">{persona.docs.toLocaleString()}건</dd></div>
            <div><dt className="ds-t-caption">본인 고민 추정</dt><dd className="ds-t-body">{persona.firstPerson == null ? '—' : `약 ${persona.firstPerson.toLocaleString()}건`}{needs?.share != null ? ` (${Math.round(needs.share * 100)}%)` : ''}</dd></div>
            <div><dt className="ds-t-caption">기준선</dt><dd className="ds-t-body">{persona.threshold == null ? '없음' : persona.threshold.toFixed(2)}</dd></div>
            <div><dt className="ds-t-caption">제외 (바이럴 / 광고)</dt><dd className="ds-t-body">{persona.viral.toLocaleString()} / {persona.ads.toLocaleString()}건</dd></div>
        </dl>
        {needs && needs.causes.length > 0 && <div className="space-y-1"><h4 className="ds-t-label">원인 (본인 고민 {needs.mine}건 기준)</h4>
            <p className="ds-t-body">{needs.causes.map(c => `${c.label} ${c.count}`).join(' · ')}</p></div>}
        {needs && needs.tried.length > 0 && <div className="min-w-0 space-y-1 overflow-x-auto"><h4 className="ds-t-label">해 본 것과 결과</h4>
            <Table><thead><tr><th>해결 시도</th><th>건수</th>{RESULTS.map(r => <th key={r}>{r}</th>)}</tr></thead>
                <tbody>{needs.tried.map(row => <tr key={row.tried}><td>{row.tried}</td><td>{row.total}</td>{RESULTS.map(r => <td key={r}>{row[r]}</td>)}</tr>)}</tbody></Table></div>}
        {quotes.length > 0 && <div className="space-y-3"><h4 className="ds-t-label">원문</h4>{quotes.map(q => <Quote key={q.docId} quote={q}/>)}</div>}
        <details><summary className="ds-t-caption cursor-pointer">기준선 근거 (점수 구간별 LLM 표본 판정)</summary>
            <Table><thead><tr><th>점수 구간</th><th>문서</th><th>판정</th><th>정확도</th><th>yes</th></tr></thead>
                <tbody>{persona.bands.map(b => <tr key={b.start}><td>{b.start.toFixed(2)}+</td><td>{b.docs.toLocaleString()}</td><td>{b.judged}</td><td>{b.precision == null ? '—' : b.precision.toFixed(2)}</td><td>{b.yes}</td></tr>)}</tbody></Table>
        </details>
    </article>;
}

export function TargetReportView({ report }: { report: SegmentTargetReport }) {
    return <Card className="min-w-0 space-y-2 [overflow-wrap:anywhere]">
        <h2 className="ds-t-card">목표 페르소나 리포트</h2>
        <p className="ds-t-caption">전체 {report.total.toLocaleString()}건 중 목표 페르소나 {report.assigned.toLocaleString()}건 ({percent(report.assigned, report.total)}) · 기타 {report.other.toLocaleString()}건 ({percent(report.other, report.total)}). 기타 문서는 다음 단계로 넘어가지 않습니다.</p>
        <div className="divide-y">{report.personas.map(p => <TargetPersona key={p.id} persona={p}/>)}</div>
        {report.discovered.length > 0 && <details className="space-y-3 pt-3"><summary className="ds-t-label cursor-pointer">{`기타에서 찾은 새 후보 ${report.discovered.length}개`}</summary>
            {report.discovered.map(group => <article key={group.id} className="space-y-2 border-t border-[var(--line)] pt-3">
                <div className="flex flex-wrap items-center gap-2"><h3 className="ds-t-label">{group.label?.name || group.id}</h3><Badge>{group.docs.toLocaleString()}건</Badge>
                    {group.label && <Badge tone={group.label.consumer_voice ? 'success' : 'neutral'}>{group.label.consumer_voice ? '본인 경험 위주' : '정보·홍보 위주'}</Badge>}</div>
                {group.label && <p className="ds-t-body">{group.label.who} {group.label.pain}</p>}
                <p className="ds-t-caption">{group.keywords.join(', ')}</p>
                {group.quotes.slice(0, 3).map(q => <Quote key={q.docId} quote={q}/>)}
            </article>)}
        </details>}
    </Card>;
}

export function TargetReport({ sid, version }: { sid: string; version?: string }) {
    const [report, setReport] = useState<SegmentTargetReport | null>(null);
    const [error, setError] = useState('');
    useEffect(() => {
        let alive = true;
        api.getSegmentTarget(sid, version).then(r => { if (alive) setReport(r); }).catch(e => { if (alive) setError(displayError(e)); });
        return () => { alive = false; };
    }, [sid, version]);
    if (error) return <Banner tone="warning">{error}</Banner>;
    if (!report) return <Card><p role="status">목표 페르소나 리포트를 불러오는 중…</p></Card>;
    return <TargetReportView report={report}/>;
}
