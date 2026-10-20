'use client';
import { useSessionStore } from '@/stores/useSessionStore';
import { useVersion } from '@/components/versions/VersionProvider';
import { InsightScreen } from '@/components/persona/InsightScreen';
import { LaterStageBanner } from '@/components/LaterStageBanner';
import { laterStageGate } from '@/lib/logic/laterStageGate';
export default function InsightsPage() {
 const {sid,sd} = useSessionStore();
 const view = useVersion();
 const session = view.session ?? sd;
 const gate = laterStageGate(sid, session as Record<string, unknown> | null | undefined);
 if (gate !== 'open') return <LaterStageBanner gate={gate} stage="인사이트" />;
 const insight = session?.insight as {confirmed?: string[]} | undefined;
 return <InsightScreen key={`${sid}:${view.version ?? ''}`} sid={sid!} version={view.version} readonly={view.readonly || !!view.conflict} initialConfirmed={insight?.confirmed ?? []}/>;
}
