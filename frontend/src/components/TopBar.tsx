"use client";
import { useSessionStore } from "@/stores/useSessionStore";

export default function TopBar() {
  const { bk, sid } = useSessionStore();
  return (
    <div className="flex items-center justify-between bg-surface-raised px-6 h-14 shrink-0 border-b border-line">
      <h2 className="text-lg font-bold text-indigo-600 tracking-tight">DCX</h2>
      <span className="text-xs font-medium text-stone-500 bg-surface-raised px-3 py-1 rounded-full border border-line">
        {bk && sid ? `${bk} | ${sid}` : "세션 없음"}
      </span>
    </div>
  );
}
