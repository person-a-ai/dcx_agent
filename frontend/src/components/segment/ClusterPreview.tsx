import type { SegmentPreview } from '@/lib/types';
import { Representatives } from './ClusterLayer';
import { KSuggestChart } from './KSuggestChart';

export function ClusterPreview({ preview }: { preview: SegmentPreview }) {
    return <section aria-label="미리보기 · Persona·관계망·토픽 분석 진행 중" className="min-w-0 space-y-4 [overflow-wrap:anywhere]">
        <h2 className="ds-t-card">미리보기 · Persona·관계망·토픽 분석 진행 중</h2>
        <p className="ds-t-caption">k = {preview.k}</p>
        {preview.naming === 'pending' && <p role="status">군집 이름 만드는 중</p>}
        <div className="min-w-0 max-w-sm"><KSuggestChart k={preview.suggested} silhouette={preview.silhouette} sample={preview.sample}/></div>
        <div className="min-w-0 divide-y rounded-xl border border-[var(--line)] px-5">
            {preview.clusters.map(cluster => <article key={cluster.id} className="grid grid-cols-1 gap-5 py-5 md:grid-cols-2">
                <div className="min-w-0 space-y-3">
                    <p className="ds-t-caption">{cluster.id} · 문서 {cluster.docs.toLocaleString('ko-KR')}건</p>
                    {cluster.name && <h3 className="ds-t-label">{cluster.name} · 이름 초안</h3>}
                    {cluster.nameFailed && <p className="ds-t-caption">이름 생성 실패 · 최종 단계에서 다시 시도</p>}
                    <Representatives reps={cluster.reps}/>
                </div>
                <div className="min-w-0 space-y-3">
                    <h3 className="ds-t-label">키워드</h3>
                    <div className="flex min-w-0 flex-wrap gap-2">{cluster.keywords.map((keyword, i) => <span key={`${keyword}:${i}`} className="min-w-0 rounded-full border border-[var(--line)] px-2 py-1 ds-t-caption">#{keyword}</span>)}</div>
                </div>
            </article>)}
        </div>
    </section>;
}
