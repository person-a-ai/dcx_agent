'use client';
import { Button } from '../ds/Button';
import { ProgressBar } from '../ds/ProgressBar';
import { workerActions, type WorkerAction } from './workerControls';
import type { LabelProgress } from '@/lib/types';
export function LabelerProgress({name, progress, onControl, busy = false, reviewQueue = false}: {name: string; progress: LabelProgress; onControl?: (action: WorkerAction) => void; busy?: boolean; reviewQueue?: boolean}) {
 const waiting = ['none', 'pending', 'idle'].includes(progress.state);
 const done = progress.done ?? 0;
 const pending = progress.total === undefined ? progress.pending : Math.max(0, progress.total - done);
 const bad = progress.bad ?? 0;
 const reviewFailures = reviewQueue && bad > 0;
 const reviewExplanation = '3번 시도해도 판정하지 못한 글은 검수 큐에서 사람이 판정합니다.';
 const completion = reviewFailures ? `판정을 마쳤습니다. ${bad.toLocaleString('ko-KR')}건은 판정하지 못해 검수 큐로 보냈습니다.` : '판정을 마쳤습니다.';
 const stopped = ['paused','failed','interrupted','cancelled'].includes(progress.state);
 return <section aria-label={`${name} 판정 진행`}><h3 className="ds-t-card">{name}</h3><ProgressBar label={`${name} 판정 진행`} value={waiting ? 0 : progress.progress === undefined ? undefined : progress.progress * 100}/><p>{done.toLocaleString('ko-KR')}{progress.total !== undefined && ` / ${progress.total.toLocaleString('ko-KR')}`}건 판정 · {pending.toLocaleString('ko-KR')}건 남음</p>{reviewFailures && ['running', 'paused'].includes(progress.state) && <p className="ds-t-caption" title={reviewExplanation}>판정 실패 {bad.toLocaleString('ko-KR')}건 · 검수 큐로 보냄<span className="sr-only">{reviewExplanation}</span></p>}<p>{waiting ? '대기 중' : progress.state === 'done' ? completion : stopped ? '판정이 멈췄습니다.' : '처리 중…'}</p>{progress.reason && <p role="status">{progress.reason}</p>}{progress.estimate?.seconds != null && <p className="ds-t-caption">예상 {Math.ceil(progress.estimate.seconds / 60).toLocaleString('ko-KR')}분</p>}{onControl && workerActions(progress.state).map(action => <Button key={action} disabled={busy} onClick={() => onControl(action)}>{action === 'resume' ? '이어서 진행' : action === 'pause' ? '일시 정지' : '중단'}</Button>)}</section>;
}
