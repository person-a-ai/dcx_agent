'use client';
import './insight.css';
export type InsightTopBarProps = {
  count: number; index: number; onPrev: () => void; onNext: () => void;
  confirmed: boolean; onToggleConfirm: () => void; confirmDisabled: boolean;
  onDerive: () => void; deriveDisabled: boolean;
};
export function InsightTopBar({count,index,onPrev,onNext,confirmed,onToggleConfirm,confirmDisabled,onDerive,deriveDisabled}: InsightTopBarProps) {
  return <header className="insight-topbar">
    <h1>8-E 인사이트 도출 <span>›</span> 인사이트별 Pain Point</h1>
    <span className="insight-count">인사이트 {count}개 · 대화형</span>
    {count > 0 ? <>
      <button type="button" className="ds-btn insight-hit" aria-pressed={confirmed} disabled={confirmDisabled} onClick={onToggleConfirm}>{confirmed ? '확정됨' : '확정하기'}</button>
      <div role="group" aria-label="인사이트 넘기기" className="insight-pager" onKeyDown={event => {
        if (event.key === 'ArrowLeft' && index > 0) { event.preventDefault(); onPrev(); }
        if (event.key === 'ArrowRight' && index < count - 1) { event.preventDefault(); onNext(); }
      }}>
        <button type="button" className="ds-btn insight-hit" aria-label="이전 인사이트" disabled={index <= 0} onClick={onPrev}>‹</button>
        <span aria-live="polite">Insight {index + 1} / {count}</span>
        <button type="button" className="ds-btn insight-hit" aria-label="다음 인사이트" disabled={index >= count - 1} onClick={onNext}>›</button>
      </div>
    </> : <button type="button" className="ds-btn insight-hit" disabled={deriveDisabled} onClick={onDerive}>인사이트 도출</button>}
  </header>;
}
