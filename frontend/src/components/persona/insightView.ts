import type { InsightContextView, InsightItem, InsightSummary } from '@/lib/types';

export type FlowCard = {
  contextId: string; label: string; text: string; dim: string | null;
  axis: InsightContextView['axis']; counter: boolean;
};
export type BarRow = { contextId: string; short: string; label: string; value: number | null };
export type InsightView = {
  headline: string; statements: string[]; hashtags: string[]; personas: string[];
  flow: FlowCard[]; bars: BarRow[]; legacy: boolean; chips: string[];
};

export function personaShortLabels(contexts: InsightContextView[]): Record<string, string> {
  const names = new Map<string, string>();
  for (const context of contexts) {
    if (context.persona_id && context.persona_name) names.set(context.persona_id, context.persona_name);
  }
  const lastWord = (name: string) => name.trim().split(/\s+/).at(-1) ?? name;
  const counts = new Map<string, number>();
  for (const name of names.values()) {
    const short = lastWord(name);
    counts.set(short, (counts.get(short) ?? 0) + 1);
  }
  return Object.fromEntries([...names].map(([id, name]) => {
    const short = lastWord(name);
    return [id, (counts.get(short) ?? 0) > 1 ? name : short];
  }));
}

export function dimLabel(dim: string | null): string {
  return dim ?? '근거 부족';
}

export function toInsightView(item: InsightItem, summary?: InsightSummary | null): InsightView {
  // Summary is session-wide; card and bar values always come from their Contexts.
  void summary;
  const contexts = item.contexts ?? [];
  const labels = personaShortLabels(contexts);
  const byId = new Map(contexts.map(context => [context.context_id, context]));
  const contextFor = (id: string): InsightContextView => byId.get(id) ?? {context_id:id,short:id};
  const labelFor = (context: InsightContextView) => {
    const persona = context.persona_id ? labels[context.persona_id] : undefined;
    return persona ? `${persona}-${context.short}` : context.short;
  };
  const steps = item.flow ?? item.context_ids.map(id => {
    const context = contextFor(id);
    return {context_id:id,text:context.pain_point || context.context_name || context.short};
  });
  const flow = steps.map(step => {
    const context = contextFor(step.context_id);
    return {contextId:step.context_id,label:labelFor(context),text:step.text,
      dim:context.dim ?? null,axis:context.axis,counter:context.counter ?? false};
  });
  const chips = ['이 인사이트 문장을 더 짧게 다시 써줘'];
  if (flow.length > 1) chips.push(`흐름에서 ${flow[0].label}과 ${flow[flow.length - 1].label} 순서를 바꿔줘`);
  return {
    headline:item.headline || item.title, statements:item.statements ?? [item.pain_point], hashtags:item.hashtags ?? [],
    personas:[...new Set(contexts.flatMap(context => context.persona_name ? [context.persona_name] : []))],
    flow, bars:item.context_ids.map(id => {
      const context = contextFor(id);
      return {contextId:id,short:context.short,label:labelFor(context),value:context.odi ?? null};
    }),
    legacy:!item.headline || !item.statements || !item.flow, chips,
  };
}

export function radarMean(items: InsightItem[]): Record<'Computed' | 'Connected' | 'Shared', number> | null {
  const axes = ['Computed', 'Connected', 'Shared'] as const;
  let hasValues = false;
  const means = axes.map(axis => {
    const values = items.flatMap(item => {
      const value = item.radar?.raw?.[axis];
      return typeof value === 'number' && Number.isFinite(value) ? [value] : [];
    });
    if (values.length) hasValues = true;
    return [axis, values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0];
  });
  return hasValues ? Object.fromEntries(means) as Record<typeof axes[number], number> : null;
}
