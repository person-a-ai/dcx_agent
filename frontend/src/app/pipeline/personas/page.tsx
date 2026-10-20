"use client";
import { useSessionStore } from "@/stores/useSessionStore";
import { useVersion } from "@/components/versions/VersionProvider";
import { PersonaScreen } from "@/components/persona/PersonaScreen";
import { LaterStageBanner } from "@/components/LaterStageBanner";
import { laterStageGate } from "@/lib/logic/laterStageGate";

export default function PersonasPage() {
  const {sid, sd} = useSessionStore();
  const view = useVersion();
  const gate = laterStageGate(sid, sd as Record<string, unknown> | null | undefined);
  if (gate !== 'open') return <LaterStageBanner gate={gate} stage="페르소나" />;
  return <PersonaScreen key={`${sid}:${view.version ?? ''}`} sid={sid!} version={view.version} readonly={view.readonly || !!view.conflict} />;
}
