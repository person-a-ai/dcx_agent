"use client";
import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useSessionStore } from "@/stores/useSessionStore";
import { startPreprocess, getPreprocessStatus, saveSession } from "@/lib/api";
import { usePolling } from "@/lib/usePolling";
import Spinner from "@/components/Spinner";

export default function PreprocessPage() {
  const router = useRouter();
  const store = useSessionStore();
  const { sid, sd } = store;

  const [started, setStarted] = useState(sd?.step === "preprocess-start");
  const [extraFilter, setExtraFilter] = useState("");

  const fetcher = useCallback(() => getPreprocessStatus(sid!), [sid]);
  const shouldStop = useCallback((d: Awaited<ReturnType<typeof getPreprocessStatus>>) => d.status === "done" || d.status === "error", []);
  const { data } = usePolling({ fetcher, interval: 3000, enabled: started && !!sid, shouldStop });

  const isDone = data?.status === "done";

  const handleStart = async () => {
    await startPreprocess({ sid, extraFilter, excludeCafes: [] });
    const updated = { ...sd!, step: "preprocess-start" };
    store.setSession({ sd: updated, step: "preprocess-start" });
    await saveSession(sid!, updated);
    setStarted(true);
  };

  const handleNext = async () => {
    const updated = { ...sd!, step: "labeling" };
    store.setSession({ sd: updated, step: "labeling" });
    await saveSession(sid!, updated);
    router.push("/pipeline/labeling");
  };

  if (started) {
    return (
      <div>
        <div className="bg-surface-raised rounded-2xl p-5 border border-line mb-5">
          <h3 className="text-lg font-semibold text-stone-800 tracking-tight">전처리 진행중</h3>
        </div>
        <div className="bg-surface-raised rounded-2xl p-6 border border-line">
          {isDone ? (
            <div className="bg-action-soft text-indigo-700 text-sm px-4 py-3 rounded-xl font-medium border border-indigo-100">완료! 원본:{(data?.original || 0).toLocaleString()} → 정제:{(data?.filtered || 0).toLocaleString()}건</div>
          ) : (
            <div className="flex items-center gap-2.5 text-sm text-amber-600 font-medium"><Spinner size={16} /> 처리 중...</div>
          )}
          {isDone && <button onClick={handleNext} className="w-full bg-action text-on-action py-3 rounded-lg text-sm font-semibold hover:bg-action-hover active:scale-[0.99] shadow-sm transition-all mt-5">라벨링 →</button>}
        </div>
      </div>
    );
  }

  return (
    <div>
      <button onClick={() => router.push("/pipeline/crawling")} className="inline-flex items-center gap-1.5 text-stone-500 hover:text-stone-700 text-sm font-medium mb-4 transition-colors">← 크롤링 설정으로</button>
      <div className="bg-surface-raised rounded-2xl p-5 border border-line mb-5">
        <h3 className="text-lg font-semibold text-stone-800 tracking-tight">전처리</h3>
      </div>
      <div className="bg-surface-raised rounded-2xl p-6 border border-line">
        <label className="block text-sm font-medium text-stone-700 mb-1.5">추가 필터</label>
        <textarea className="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm bg-surface-raised placeholder:text-stone-400" rows={2} placeholder="추가 제외 키워드" value={extraFilter} onChange={(e) => setExtraFilter(e.target.value)} />
        <button onClick={handleStart} className="w-full bg-indigo-500 text-white py-3 rounded-lg text-sm font-semibold hover:bg-indigo-600 active:scale-[0.99] shadow-sm transition-all mt-4">전처리 시작</button>
      </div>
    </div>
  );
}
