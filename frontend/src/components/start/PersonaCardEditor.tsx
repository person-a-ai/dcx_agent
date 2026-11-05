"use client";
import { useState } from "react";
import { Input, TextArea } from "@/components/ds";
import { cardFilled, emptyPersonaCard, parseCardList } from "@/lib/logic/startForm";
import type { SeedPersonaCard as PersonaCard } from "@/lib/types";

type Props = { name: string; card?: PersonaCard | null; disabled?: boolean; onChange: (patch: Partial<PersonaCard>) => void };

/** Optional target-persona card; filled cards let stage 6 group documents around this persona. */
export function PersonaCardEditor({ name, card, disabled, onChange }: Props) {
  const value = { ...emptyPersonaCard, ...card };
  // Keep the raw text so commas and blank lines can be typed before they are parsed.
  const [keywords, setKeywords] = useState(value.keywords.join(", "));
  const [quotes, setQuotes] = useState(value.quotes.join("\n"));
  return <details className="col-span-full space-y-3 rounded border border-[var(--ds-line)] p-3">
    <summary className="ds-t-label cursor-pointer">{`${name} 카드 ${cardFilled(card) ? "· 작성됨" : "채우기 (선택)"}`}</summary>
    <p className="ds-t-caption">6단계 &apos;목표 페르소나로 나누기&apos;에서 이 카드에 맞는 원문을 모읍니다. &quot;누가 + 어떤 상황에서 + 무엇이 안 되는지&quot;가 드러나게 쓰면 정확해집니다.</p>
    <div className="grid gap-3 md:grid-cols-2">
      <Input label="Desire" maxLength={200} disabled={disabled} placeholder="예: 함께 건강하게 나이 들고 싶음" value={value.desire} onChange={event => onChange({ desire: event.target.value })} />
      <Input label="Context" maxLength={200} disabled={disabled} placeholder="예: 같은 방에서 자지만 잠드는 시간과 습관이 다름" value={value.context} onChange={event => onChange({ context: event.target.value })} />
      <Input label="Pain Point" maxLength={200} disabled={disabled} placeholder="예: 코골이에 아이까지 깨서 결국 각방을 씀" value={value.pain} onChange={event => onChange({ pain: event.target.value })} />
      <Input label="Unmet Needs" maxLength={200} disabled={disabled} placeholder="예: 각방 쓰지 않고도 가족 모두 푹 자는 것" value={value.unmet} onChange={event => onChange({ unmet: event.target.value })} />
    </div>
    <Input label="키워드 (쉼표로 구분, 10개까지)" disabled={disabled} placeholder="코골이, 각방, 수면 패턴" value={keywords}
      onChange={event => { setKeywords(event.target.value); onChange({ keywords: parseCardList(event.target.value, "keywords") }); }} />
    <TextArea label="대표 원문 (한 줄에 하나, 5개까지)" disabled={disabled} placeholder="코고는 소리 때문에 아이가 자주 깨서 오히려 숙면을 방해하더라구요" value={quotes}
      onChange={event => { setQuotes(event.target.value); onChange({ quotes: parseCardList(event.target.value, "quotes") }); }} />
  </details>;
}
