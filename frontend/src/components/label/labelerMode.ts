import type { Overview } from '@/lib/api/label';
import type { LabelProgress } from '@/lib/types';

export function gptOnlyNotice(name: string) {
 return {title:`${name} 미연결 · GPT 단독 판정`, body:`등급 불일치 검수 없이 GPT 판정을 그대로 채택합니다. 오류는 무작위 감사로 확인합니다. ${name}를 연결한 뒤 새 버전에서 시작하면 교차 판정합니다.`};
}
export const GPT_ONLY_TITLE = gptOnlyNotice('Jev').title;
export const GPT_ONLY_BODY = gptOnlyNotice('Jev').body;

export function crossLabelerName(o: Pick<Overview, 'crossLabeler'>): string {
 return o.crossLabeler ?? 'Jev';
}
export function crossCostLine(name: string, estimate: LabelProgress['estimate']): string {
 const tokens = typeof estimate?.jevTokens === 'number' ? estimate.jevTokens.toLocaleString('ko-KR') : null;
 if (typeof estimate?.jevCostUsd === 'number') return `예상 ${name} 비용 · 약 $${estimate.jevCostUsd.toFixed(2)}${tokens ? `(입력 ${tokens}토큰)` : ''}`;
 return `예상 ${name} 비용 · 금액 추정은 아직 제공되지 않습니다.${tokens ? ` 예상 입력 ${tokens}토큰` : ''}`;
}
export function isGptOnly(o: Pick<Overview, 'labelerMode'>): boolean {
 return o.labelerMode === 'gpt_only';
}
export function formatRate(value: number | null | undefined): string {
 return value == null ? '—' : `${(value * 100).toFixed(1)}%`;
}
export function labelerView(o: Pick<Overview, 'labelerMode' | 'progress' | 'mode'>, mode = o.mode) {
 const showNotice = mode === 'llm' && isGptOnly(o);
 return {showNotice, workers:Object.entries(o.progress).filter(([name]) => !showNotice || name === 'gpt')};
}
