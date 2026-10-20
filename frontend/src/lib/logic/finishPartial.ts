import type { CrawlStatus } from '../api/crawl';
type PartialStatus = Pick<CrawlStatus,'kind'|'status'|'resumable'|'channels'|'remaining_by_channel'>;
const pausedChannels = (status:PartialStatus) => Object.entries(status.channels).filter(([,c])=>['paused_blocked','paused_parse_error'].includes(c.status));
export function canFinishPartial(status:PartialStatus) {
 const paused=pausedChannels(status).map(([s])=>s);
 return status.kind==='detail' && !['running','stopping'].includes(status.status) && status.resumable!==false && paused.length>0 && !!status.remaining_by_channel && Object.entries(status.remaining_by_channel).every(([s,n])=>!n||paused.includes(s));
}
export function skippedSummary(name:string,count:number,reason?:string|null) {
 return `${name} ${count.toLocaleString('ko-KR')}건 미수집(${reason==='parse_error'?'파싱 오류':'차단'})`;
}
export function finishPartialConfirmation(status:PartialStatus,names:Record<string,string>) {
 return pausedChannels(status).map(([s,c])=>skippedSummary(names[s]??s,status.remaining_by_channel?.[s]??0,c.status.replace('paused_',''))).join('\n')+'\n남은 URL을 건너뛰고 지금까지 모은 결과로 마치시겠습니까?';
}

const SKIP_REASONS: Record<string, string> = {
  no_ko_captions: '한국어 자막 없음', deleted: '삭제된 글', restricted: '회원 전용 · 폐쇄 카페(제외)',
  blocked: '차단으로 여기까지 마침', parse_error: '파싱 오류로 여기까지 마침',
};
export const skipReasonLabel = (reason: string): string => SKIP_REASONS[reason] ?? reason;
type ReportChannels = { channels: Record<string, { skip_reasons?: Record<string, number>; skipped?: number; skip_reason?: string | null }> };
export function skipRows(report: ReportChannels): { source: string; reason: string; count: number }[] {
  return Object.entries(report.channels).flatMap(([source, c]) => {
    const reasons = c.skip_reasons ?? (c.skipped ? { [c.skip_reason ?? 'blocked']: c.skipped } : {});
    return Object.entries(reasons).filter(([, count]) => count > 0).map(([reason, count]) => ({ source, reason, count }));
  }).sort((a, b) => b.count - a.count);
}

export const vlogDocsLabel = (docs: number, videos?: number): string =>
  `${videos === undefined ? '' : `영상 ${videos.toLocaleString('ko-KR')}개 → `}구간 ${docs.toLocaleString('ko-KR')}`;
