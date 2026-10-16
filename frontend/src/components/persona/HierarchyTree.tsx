'use client';

import { useState } from 'react';
import { formatCount } from './personaView';
import './persona.css';

export type HierarchyNode = { id: string; name: string; doc_count: number; children?: HierarchyNode[] };
export function HierarchyTree({ root, expandedId }: { root: HierarchyNode; expandedId?: string | null }) {
  const [overrides, setOverrides] = useState<{ root: HierarchyNode; selected: typeof expandedId; values: Record<string, boolean> } | null>(null);
  const defaults = new Set<string>();
  let max = 0;
  function visit(node: HierarchyNode): boolean {
    max = Math.max(max, node.doc_count);
    const children = node.children?.map(visit) ?? [];
    const selected = node.id === expandedId || children.some(Boolean);
    if (selected) defaults.add(node.id);
    return selected;
  }
  visit(root);
  const values = overrides?.root === root && overrides.selected === expandedId ? overrides.values : {};
  function renderNode(node: HierarchyNode, depth: number) {
    const open = depth === 0 || (values[node.id] ?? defaults.has(node.id));
    const toggle = depth === 1 || depth === 2;
    const ratio = max > 0 ? Math.max(0, node.doc_count) / max : 0;
    return <li key={node.id}>
      <div className="hierarchy-row">
        {toggle ? <button type="button" className="hierarchy-toggle" aria-expanded={open} onClick={() => setOverrides(previous => ({
          root, selected: expandedId,
          values: { ...(previous?.root === root && previous.selected === expandedId ? previous.values : {}), [node.id]: !open },
        }))}><span aria-hidden="true">{open ? '▾' : '▸'} </span>{node.name}</button> : <span className="hierarchy-name">{node.name}</span>}
        <span className="hierarchy-bar-area" aria-hidden="true"><span className="hierarchy-bar" data-ratio={ratio} style={{ width: `${ratio * 100}%` }}/></span>
        <span className="hierarchy-count">문서 {formatCount(node.doc_count)}건</span>
      </div>
      {open && !!node.children?.length && <ul>{node.children.map(child => renderNode(child, depth + 1))}</ul>}
    </li>;
  }
  return <figure className="hierarchy-tree"><figcaption>제품 → Cluster → Persona → Context · 막대 길이 = 문서 수</figcaption><ul>{renderNode(root, 0)}</ul></figure>;
}
