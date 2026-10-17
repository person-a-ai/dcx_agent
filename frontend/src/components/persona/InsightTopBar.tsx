'use client';
import './insight.css';
import {useLayoutEffect, useRef} from 'react';

export function pagerFocusTarget<T extends {disabled: boolean}, G>(focused: T | null, previous: T | null, next: T | null, group: G): T | G | null {
  if (!focused?.disabled) return null;
  return previous && !previous.disabled ? previous : next && !next.disabled ? next : group;
}
export type InsightTopBarProps = {
  count: number; index: number; onPrev: () => void; onNext: () => void;
  confirmed: boolean; onToggleConfirm: () => void; confirmDisabled: boolean;
  onDerive: () => void; deriveDisabled: boolean;
};
export function InsightTopBar({count,index,onPrev,onNext,confirmed,onToggleConfirm,confirmDisabled,onDerive,deriveDisabled}: InsightTopBarProps) {
  const groupRef = useRef<HTMLDivElement>(null);
  const previousRef = useRef<HTMLButtonElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const focusedRef = useRef<HTMLButtonElement | null>(null);
  const navigate = (action: () => void) => {
    const active = groupRef.current?.ownerDocument.activeElement;
    focusedRef.current = active === previousRef.current ? previousRef.current : active === nextRef.current ? nextRef.current : null;
    action();
  };
  useLayoutEffect(() => {
    const target = pagerFocusTarget(focusedRef.current, previousRef.current, nextRef.current, groupRef.current);
    target?.focus();
    focusedRef.current = null;
  }, [index, count]);
  return <header className="insight-topbar">
    <h1>8-E 인사이트 도출 <span>›</span> 인사이트별 Pain Point</h1>
    <span className="insight-count">인사이트 {count}개 · 대화형</span>
    {count > 0 ? <>
      <button type="button" className="ds-btn insight-hit" aria-pressed={confirmed} disabled={confirmDisabled} onClick={onToggleConfirm}>{confirmed ? '확정됨' : '확정하기'}</button>
      <div ref={groupRef} tabIndex={-1} role="group" aria-label="인사이트 넘기기" className="insight-pager" onKeyDown={event => {
        if (event.key === 'ArrowLeft' && index > 0) { event.preventDefault(); navigate(onPrev); }
        if (event.key === 'ArrowRight' && index < count - 1) { event.preventDefault(); navigate(onNext); }
      }}>
        <button type="button" className="ds-btn insight-hit" ref={previousRef} aria-label="이전 인사이트" disabled={index <= 0} onClick={() => navigate(onPrev)}>‹</button>
        <span aria-live="polite">Insight {index + 1} / {count}</span>
        <button type="button" className="ds-btn insight-hit" ref={nextRef} aria-label="다음 인사이트" disabled={index >= count - 1} onClick={() => navigate(onNext)}>›</button>
      </div>
    </> : <button type="button" className="ds-btn insight-hit" disabled={deriveDisabled} onClick={onDerive}>인사이트 도출</button>}
  </header>;
}
