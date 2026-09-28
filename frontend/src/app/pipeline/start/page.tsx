"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import SessionList from "@/components/SessionList";
import { useSessionStore } from "@/stores/useSessionStore";
import { saveSession } from "@/lib/api";
import { restoreSessionToStore } from "@/lib/sessionPersist";

const AGES = ["주부", "직장인", "1인가구", "신혼부부", "육아맘", "시니어", "대학생", "자영업"];
const RANGES = ["20대", "30대", "40대", "50대+"];
const GENDERS = ["남성", "여성"];

// known_insights — STEP 01 에서 받아 STEP 05 가 좌표를 붙이고
// STEP 09 리랭킹이 감점 항으로 쓴다. 서버(schemas.py)와 같은 값.
const KI_MIN = 5;
const KI_MAX = 10;

export default function StartPage() {
  const router = useRouter();
  const store = useSessionStore();
  const [bk, setBk] = useState("");
  const [pd, setPd] = useState("");
  const [ages, setAges] = useState<string[]>([]);
  const [ar, setAr] = useState<string[]>([]);
  const [gens, setGens] = useState<string[]>([]);
  const [ki, setKi] = useState<string[]>(["", "", ""]);
  const [warnings, setWarnings] = useState<string[]>([]);

  const kiFilled = ki.map((t) => t.trim()).filter(Boolean);
  const kiOff = kiFilled.length < KI_MIN || kiFilled.length > KI_MAX;
  const setKiAt = (i: number, v: string) =>
    setKi(ki.map((t, j) => (j === i ? v : t)));

  const toggle = (arr: string[], val: string, setter: (v: string[]) => void) => {
    setter(arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val]);
  };

  const handleNew = async () => {
    if (!bk.trim()) return alert("키워드 입력");
    if (!pd.trim()) return alert("문제정의 입력");
    const sid = "s" + Date.now();
    const sd = {
      bk, problemDef: pd, ages, ageRange: ar, gens, allKw: [], sid, step: "r1",
      known_insights: kiFilled.map((text) => ({ text })),
    };
    store.setSession({ sid, bk, pd, ages, ar, gens, kw: [], step: "r1", sd });
    const res = await saveSession(sid, sd);
    // 개수 경고는 막지 않는다 — 알려주고 그대로 넘어간다.
    if (res?.warnings?.length) setWarnings(res.warnings);
    router.push("/pipeline/keywords");
  };

  const handleLoad = async (sid: string) => {
    try {
      const step = await restoreSessionToStore(sid, store);
      const routeMap: Record<string, string> = {
        start: "/pipeline/start", r1: "/pipeline/keywords", r2: "/pipeline/keywords",
        r3: "/pipeline/keywords", "r3-expand": "/pipeline/keywords", final: "/pipeline/keywords",
        "crawl-setup": "/pipeline/crawling", "crawl-start": "/pipeline/crawling",
        "preprocess-setup": "/pipeline/preprocess", "preprocess-start": "/pipeline/preprocess",
        labeling: "/pipeline/labeling", "labeling-done": "/pipeline/labeling",
        "train-start": "/pipeline/training", "train-check": "/pipeline/training",
        clustering: "/pipeline/clustering", "cluster-start": "/pipeline/clustering",
        "cluster-check": "/pipeline/clustering", "cluster-refine": "/pipeline/clustering",
        persona: "/pipeline/personas", "persona-start": "/pipeline/personas",
        "persona-check": "/pipeline/personas", "embed-start": "/pipeline/personas",
        "embed-check": "/pipeline/personas", done: "/pipeline/personas",
      };
      router.push(routeMap[step] || "/pipeline/start");
    } catch {
      alert("세션 로드 실패");
    }
  };

  return (
    <div>
      <SessionList onSelect={handleLoad} />
      <div className="bg-surface-raised rounded-2xl p-6 border border-line">
        <h3 className="text-lg font-semibold text-stone-800 tracking-tight">새로 시작</h3>
        <div className="mt-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">메인 키워드</label>
            <input className="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm bg-surface-raised placeholder:text-stone-400" placeholder="예: 에어컨" value={bk} onChange={(e) => setBk(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">문제정의</label>
            <textarea className="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm bg-surface-raised placeholder:text-stone-400" rows={3} placeholder="예: 에어컨 구매 시 소비자 고민 파악" value={pd} onChange={(e) => setPd(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">타겟</label>
            <div className="flex flex-wrap gap-2">
              {AGES.map((v) => (
                <span key={v} onClick={() => toggle(ages, v, setAges)} className={`px-3.5 py-1.5 rounded-full text-xs font-medium cursor-pointer border transition-all ${ages.includes(v) ? "bg-indigo-500 text-white border-indigo-500 shadow-sm" : "bg-white text-stone-600 border-stone-200 hover:border-stone-300 hover:bg-stone-50"}`}>{v}</span>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">나이대</label>
            <div className="flex flex-wrap gap-2">
              {RANGES.map((v) => (
                <span key={v} onClick={() => toggle(ar, v, setAr)} className={`px-3.5 py-1.5 rounded-full text-xs font-medium cursor-pointer border transition-all ${ar.includes(v) ? "bg-indigo-500 text-white border-indigo-500 shadow-sm" : "bg-white text-stone-600 border-stone-200 hover:border-stone-300 hover:bg-stone-50"}`}>{v}</span>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-1.5">성별</label>
            <div className="flex flex-wrap gap-2">
              {GENDERS.map((v) => (
                <span key={v} onClick={() => toggle(gens, v, setGens)} className={`px-3.5 py-1.5 rounded-full text-xs font-medium cursor-pointer border transition-all ${gens.includes(v) ? "bg-indigo-500 text-white border-indigo-500 shadow-sm" : "bg-white text-stone-600 border-stone-200 hover:border-stone-300 hover:bg-stone-50"}`}>{v}</span>
              ))}
            </div>
          </div>
          <div>
            <div className="flex items-baseline gap-2 mb-1.5">
              <label className="block text-sm font-medium text-stone-700">이미 알고 있는 사실</label>
              <span className="text-meta text-ink-subtle">{KI_MIN}~{KI_MAX}문장</span>
              <span className="grow" />
              <span className={`text-meta ${kiOff ? "text-amber-700" : "text-ink-subtle"}`}>
                {kiFilled.length} / {KI_MIN}~{KI_MAX}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              {ki.map((t, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    className="flex-1 border border-stone-200 rounded-lg px-4 py-2.5 text-sm bg-surface-raised placeholder:text-stone-400"
                    placeholder="예: 러너는 심박을 보려고 워치를 추가로 착용한다"
                    value={t}
                    onChange={(e) => setKiAt(i, e.target.value)}
                  />
                  {ki.length > 1 && (
                    <button
                      onClick={() => setKi(ki.filter((_, j) => j !== i))}
                      className="px-3 rounded-lg text-sm text-ink-subtle border border-stone-200 hover:bg-stone-100 transition-colors"
                      title="이 문장 지우기"
                    >−</button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={() => setKi([...ki, ""])}
              className="w-full mt-2 py-2 rounded-lg text-xs font-medium border border-dashed border-stone-300 text-ink-subtle hover:bg-stone-100 transition-colors"
            >＋ 문장 추가</button>
            <p className="mt-2 text-meta text-ink-subtle leading-relaxed">
              여기 적힌 것과 겹치는 문서는 STEP 09 근거 순위에서 내려간다.
              적지 않으면 이미 아는 이야기가 근거로 되돌아온다.
            </p>
          </div>

          {warnings.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
              {warnings.map((w, i) => (
                <p key={i} className="text-meta text-amber-800 leading-relaxed">{w}</p>
              ))}
            </div>
          )}

          <button onClick={handleNew} className="w-full bg-indigo-500 text-white py-3 rounded-lg text-sm font-semibold hover:bg-indigo-600 active:scale-[0.99] shadow-sm transition-all mt-2">시작</button>
        </div>
      </div>
    </div>
  );
}
