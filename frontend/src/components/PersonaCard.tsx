import type { Persona } from "@/lib/types";

interface PersonaCardProps {
  persona: Persona;
}

export default function PersonaCard({ persona }: PersonaCardProps) {
  return (
    <div className="bg-surface-raised rounded-2xl p-5 border border-line transition-shadow">
      <div className="text-sm font-bold text-indigo-600 mb-4">{persona.name}</div>
      <div className="border-l-[3px] border-blue-300 pl-3 mb-3">
        <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">상황</span>
        <p className="text-sm text-stone-600 mt-1 leading-relaxed">{persona.situation}</p>
      </div>
      <div className="border-l-[3px] border-rose-300 pl-3 mb-3">
        <span className="text-xs font-semibold text-rose-600 uppercase tracking-wide">Pain Point</span>
        <p className="text-sm text-stone-600 mt-1 leading-relaxed">{persona.pain_point}</p>
      </div>
      <div className="border-l-[3px] border-emerald-300 pl-3 bg-success-soft rounded-lg p-3">
        <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">인사이트</span>
        <p className="text-sm text-stone-600 mt-1 leading-relaxed">{persona.insight}</p>
      </div>
    </div>
  );
}
