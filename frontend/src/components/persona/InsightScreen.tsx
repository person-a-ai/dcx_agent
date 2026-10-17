'use client';
import { useEffect, useRef, useState } from 'react';
import * as api from '@/lib/api/insight';
import { displayError } from '@/lib/api/errors';
import type { InsightConcept as Concept, InsightItem, InsightResponse, InsightTarget } from '@/lib/types';
import { Button } from '../ds/Button';
import { useVersion } from '../versions/VersionProvider';
import { useStageCompletionRefresh } from '../versions/useStageCompletionRefresh';
import { Radar, radarAxes, type RadarValues } from './Radar';
import { OpportunityBars } from './OpportunityBars';
import { createInsightActions } from './insightActions';
import { displayValue } from './personaView';
import { InsightTopBar } from './InsightTopBar';
import { InsightHeader } from './InsightHeader';
import { InsightChatBar } from './InsightChatBar';
import { InsightFlow } from './InsightFlow';
import { InsightConcept } from './InsightConcept';
import { toInsightView, radarMean } from './insightView';
import './insight.css';

const record = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
const text = displayValue;
const number = (value: unknown) => typeof value === 'number' && Number.isFinite(value) ? value : null;
function radarValues(value: unknown): RadarValues {
 const row = record(value); const raw = record(row.raw); const percentile = record(row.percentile);
 return Object.fromEntries(Object.keys(radarAxes).map(axis => [axis,{raw:number(raw[axis] ?? record(row[axis]).raw),percentile:number(percentile[axis] ?? record(row[axis]).percentile)}])) as RadarValues;
}
export function InsightScreen({sid,version,readonly = false,initialConfirmed = []}: {sid: string; version?: string; readonly?: boolean; initialConfirmed?: string[]}) {
 const {refreshSessionAfterStage} = useVersion();
 const [data,setData] = useState<InsightResponse | null>(null);
 const [confirmed,setConfirmed] = useState(initialConfirmed);
 const [selected,setSelected] = useState(''); const [target,setTarget] = useState<InsightTarget | ''>('');
 const [preview,setPreview] = useState<number | null>(null); const [busy,setBusy] = useState(false); const lock = useRef(false);
 const [error,setError] = useState(''); const [retry,setRetry] = useState(0);
 const [pending,setPending] = useState<{runId:string; mode:'derive'|'concept'; target?:string} | null>(null);
 const worker = data?.worker;
 const running = worker?.status === 'running';
 const stopped = worker?.status === 'failed' || worker?.status === 'interrupted';
 const failureVisible = stopped && (!pending || worker.runId === pending.runId || (!worker.runId && worker.mode === pending.mode && worker.target === (pending.target ?? null)));
 const disabled = readonly || busy || (!!pending && !failureVisible) || running;
 useStageCompletionRefresh(data?.insights.revision ? `insight:${data.insights.revision}` : null);
 useEffect(() => {
  let active = true;
  api.getInsights(sid,version).then(result => {if(active) {setData(result);setConfirmed(result.confirmed ?? []);setSelected(result.bars?.targets[0] ?? result.insights.items.find(item => record(item).default_target)?.id ?? result.insights.items[0]?.id ?? '');setTarget('');setPreview(null);setError('');}}).catch(cause => {if(active) setError(displayError(cause));});
  return () => {active = false;};
 },[sid,version,retry]);
 useEffect(() => {
  if (!pending && !running) return;
  let active = true; let count = 0;
  const timer = setInterval(async () => {
   try {
    const result = await api.getInsights(sid,version);
    if (!active) return;
    setData(result);setConfirmed(result.confirmed ?? []);
    setSelected(id => result.insights.items.some(item => item.id === id) ? id : result.insights.items[0]?.id ?? '');
    if (result.worker && result.worker.status !== 'running' && (!pending || result.worker.runId === pending.runId || (!result.worker.runId && result.worker.mode === pending.mode && result.worker.target === (pending.target ?? null)))) {setPending(null);return;}
    if (++count >= 120) {setPending(null);setError('처리 상태를 확인하지 못했습니다. 다시 불러오세요.');}
   } catch(cause) {if(active) {setPending(null);setError(displayError(cause));}}
  },3000);
  return () => {active = false;clearInterval(timer);};
 },[sid,version,pending,running]);
 const actions = createInsightActions(sid,version,api,result => {setData(result);setConfirmed(result.confirmed ?? []);setSelected(id => result.insights.items.some(item => item.id === id) ? id : result.insights.items[0]?.id ?? '');setPreview(null);},setConfirmed);
 async function mutate(action: () => Promise<unknown>) {
  if(disabled || lock.current) return;
  lock.current = true;setBusy(true);setError('');
  try {await action();} catch(cause) {setError(displayError(cause));} finally {lock.current = false;setBusy(false);}
 }
 const insightTarget = !target || target === 'insights' || target.startsWith('insight:');
 const revisions = insightTarget ? data?.insights : data?.concepts;
 const history = revisions?.history ?? [];
 const viewed = preview === null ? null : history.find(row => row.revision === preview);
 const insightItems = insightTarget && Array.isArray(viewed?.items) ? viewed.items as InsightItem[] : data?.insights.items ?? [];
 const concepts = !insightTarget && Array.isArray(viewed?.items) ? viewed.items as Concept[] : data?.concepts.items ?? [];
 const index = Math.max(0, insightItems.findIndex(item => item.id === selected));
 const item = insightItems[index];
 const selectedId = item?.id ?? '';
 const usableConcept = data?.concepts.items.some(row => (row.insight_id ?? row.id) === selectedId && !row.outdated);
 const chatTarget: InsightTarget = target === 'insights' ? target : target.startsWith('concept:') && usableConcept ? `concept:${selectedId}` : `insight:${selectedId}`;
 const focusId = chatTarget === 'insights' ? selectedId : chatTarget.slice(chatTarget.indexOf(':') + 1);
 const concept = concepts.find(row => (row.insight_id ?? row.id) === selectedId);
 const view = item ? toInsightView(item,data?.summary) : null;
 const historicalInsights = preview !== null && insightTarget;
 const mean = historicalInsights ? radarMean(insightItems) : data?.summary?.radar_mean ?? null;
 const controlsDisabled = disabled || preview !== null;
 const navigate = (next: number) => {
  const nextId = insightItems[next]?.id;
  if (!nextId) return;
  setSelected(nextId);
  if (target.startsWith('concept:')) {
   const available = data?.concepts.items.some(row => (row.insight_id ?? row.id) === nextId && !row.outdated);
   setTarget(available ? `concept:${nextId}` : `insight:${nextId}`);
   setPreview(null);
  }
 };
 const derive = (fresh = false) => {
  if (controlsDisabled || pending) return Promise.resolve();
  return mutate(async () => {
  const run = await api.startInsight(sid,{mode:'derive',...(fresh ? {fresh:true} : {})},version);
  setPending({runId:run.runId,mode:'derive'});
  });
 };
 return <div className="space-y-5">
  <InsightTopBar count={insightItems.length} index={index} onPrev={() => navigate(index-1)} onNext={() => navigate(index+1)}
   confirmed={confirmed.includes(selectedId)} confirmDisabled={controlsDisabled} deriveDisabled={controlsDisabled || !data || !!pending}
   onDerive={() => void derive()} onToggleConfirm={() => {if(controlsDisabled) return;void mutate(async () => {
    const ids = confirmed.includes(selectedId) ? confirmed.filter(id => id !== selectedId) : [...confirmed,selectedId];
    await actions.confirm(ids);await refreshSessionAfterStage();
   });}}/>
  {readonly && <p>읽기 전용</p>}{((pending && !failureVisible) || running) && <p role="status">처리 중…</p>}
  {error && <div role="alert">{error}<Button onClick={() => setRetry(value => value+1)}>다시 불러오기</Button></div>}
  {!data && !error && <p role="status">불러오는 중…</p>}
  {failureVisible && <div role="alert"><p>{worker.mode === 'concept' ? '컨셉을 만들지 못했습니다. 다시 시도하세요.' : '인사이트를 만들지 못했습니다. 다시 시도하세요.'}</p>{worker.reason && <p>{worker.reason}</p>}<Button disabled={disabled} onClick={() => void mutate(async () => {const mode = worker.mode ?? 'derive';const run = await api.startInsight(sid,{mode,...(worker.fresh !== undefined ? {fresh:worker.fresh} : {}),...(worker.target ? {target:worker.target} : {})},version);setPending({runId:run.runId,mode,target:worker.target ?? undefined});})}>{worker.status === 'interrupted' ? '이어서 진행' : '다시 시도'}</Button></div>}
  {data && !insightItems.length && !pending && !running && !stopped && <p role="status">페르소나를 바탕으로 인사이트를 도출하세요.</p>}
  {preview !== null && <p role="status">판 {preview} 보기 <Button onClick={() => setPreview(null)}>현재 판으로</Button></p>}
  {item && view && <>
   <main className="ds-card insight-panel">
    <InsightHeader key={item.id} view={view} index={index} knownBadge={<span className="ds-badge">{item.known_ki_id ? `Known Insight #${item.known_ki_id}와 같은 내용` : '새 발견'}</span>} onRederive={() => derive(true)} rederiveDisabled={controlsDisabled || !data || !!pending}/>
    <div className="insight-charts">
     <Radar values={radarValues(record(item).radar ?? (historicalInsights ? null : data?.radar?.[item.id]))} mean={mean} label={`Insight ${index+1}`}/>
     <OpportunityBars rows={view.bars} mean={data?.summary?.context_odi_mean ?? null}/>
    </div>
    <InsightFlow cards={view.flow}/>
    <InsightChatBar target={chatTarget} focusId={focusId} focusLabel={`Insight ${index+1}`} onTarget={value => {setTarget(value);setPreview(null);}}
     conceptAvailable={!!concept && !concept.outdated} chips={view.chips} disabled={controlsDisabled}
     onSend={async message => {
      if(controlsDisabled || lock.current) return '처리 중입니다.';
      let reply = '';
      await mutate(async () => {reply = await actions.chat(chatTarget,message,...(chatTarget === 'insights' ? [selectedId] : []));});
      return reply;
     }} historyCount={history.length} revisions={{
      revisions:history.flatMap(row => typeof row.revision === 'number' ? [{revision:row.revision,message:text(row.message),by:text(row.by),createdAt:text(row.at ?? row.createdAt)}] : []),
      currentRevision:revisions?.revision ?? 0,busy:disabled,onView:revision => {
       const row = history.find(entry => entry.revision === revision);
       if (insightTarget && Array.isArray(row?.items)) {
        const items = row.items as InsightItem[];
        setSelected(id => items.some(item => item.id === id) ? id : items[0]?.id ?? '');
       }
       setPreview(revision);
      },
      onRevert:revision => void mutate(() => actions.revert(chatTarget,revision)),
     }}/>
   </main>
   <InsightConcept concept={concept} disabled={controlsDisabled} onCreate={() => void mutate(async () => {
    const run = await api.createInsightConcept(sid,selectedId,version);setPending({runId:run.runId,mode:'concept',target:selectedId});
   })}/>
  </>}
 </div>;
}
