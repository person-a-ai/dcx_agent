"use client";
import { useSessionStore } from "@/stores/useSessionStore";
import { useVersion } from "@/components/versions/VersionProvider";
import { SegmentScreen } from "@/components/segment/SegmentScreen";
import { LaterStageBanner } from "@/components/LaterStageBanner";
import { laterStageGate } from "@/lib/logic/laterStageGate";
import type { SegmentDraft } from "@/lib/types";

export default function ClusteringPage() {
  const {sid, sd} = useSessionStore();
  const view = useVersion();
  const session = view.session ?? sd;
  const gate = laterStageGate(sid, session as Record<string, unknown> | null | undefined);
  if (gate !== 'open') return <LaterStageBanner gate={gate} stage="클러스터링" />;
  return <SegmentScreen key={`${sid}:${view.version ?? ''}`} sid={sid!} version={view.version} readonly={view.readonly || !!view.conflict} draft={sd?.drafts?.segment as SegmentDraft | undefined} />;
}
