"use client";
import { useRouter } from "next/navigation";
import { Banner, Button } from "@/components/ds";
import type { LaterStageGate } from "@/lib/logic/laterStageGate";

export function LaterStageBanner({ gate, stage }: { gate: Exclude<LaterStageGate, "open">; stage: string }) {
  const router = useRouter();
  if (gate === "needs-prep") {
    return <Banner tone="warning" actions={<Button variant="primary" onClick={() => router.push("/pipeline/preprocess")}>전처리 화면으로</Button>}>
      3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 {stage} 화면을 열 수 있습니다.
    </Banner>;
  }
  if (gate === "legacy") {
    return <Banner tone="warning" actions={<Button onClick={() => router.push("/pipeline/start")}>프로젝트 선택하기</Button>}>
      구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요.
    </Banner>;
  }
  return <Banner actions={<Button onClick={() => router.push("/pipeline/start")}>프로젝트 선택하기</Button>}>프로젝트를 먼저 선택하세요.</Banner>;
}
