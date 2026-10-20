import { readFileSync } from 'node:fs';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
const nav = vi.hoisted(() => ({push: vi.fn()}));
vi.mock('next/navigation', () => ({useRouter: () => nav}));
import { LaterStageBanner } from './LaterStageBanner';

describe('LaterStageBanner', () => {
  it.each(['needs-prep', 'legacy', 'no-session'] as const)('%s has a scoped banner wrapper', (gate) => {
    const html = renderToStaticMarkup(LaterStageBanner({gate, stage: '페르소나'}));
    expect(html.match(/^<[^>]+>/)?.[0]).toBe('<div class="later-stage-banner">');
  });

  it('wraps banner actions onto a full-width row at 600px and below', () => {
    const css = readFileSync('src/app/globals.css', 'utf8');
    const mobileBlocks = [...css.matchAll(/@media\s*\(\s*max-width\s*:\s*600px\s*\)\s*\{((?:[^{}]|\{[^{}]*\})*)\}/g)];
    const bannerRules = mobileBlocks.find((block) => block[1].includes('.later-stage-banner .ds-note'))?.[1] ?? '';
    expect.soft(bannerRules).toMatch(/\.later-stage-banner \.ds-note\s*\{[^}]*flex-wrap\s*:\s*wrap\s*;/);
    expect.soft(bannerRules).toMatch(/\.later-stage-banner \.ds-actions\s*\{[^}]*width\s*:\s*100%\s*;/);
  });

  it.each([
    ['needs-prep', '3단계(전처리)를 먼저 완료하세요. 전처리가 끝나야 페르소나 화면을 열 수 있습니다.', '/pipeline/preprocess', '전처리 화면으로'],
    ['legacy', '구버전 세션은 이 단계를 열 수 없습니다. 새 프로젝트를 만들어 진행하세요.', '/pipeline/start', '프로젝트 선택하기'],
    ['no-session', '프로젝트를 먼저 선택하세요.', '/pipeline/start', '프로젝트 선택하기'],
  ] as const)('%s', (gate, text, route, label) => {
    nav.push.mockClear();
    const tree = LaterStageBanner({gate, stage: '페르소나'});
    const html = renderToStaticMarkup(tree);
    expect(html.replace(/<!-- -->/g, '')).toContain(text);
    expect(html).toContain(label);
    const banner = tree.props.children;
    expect(banner.props.tone).toBe(gate === 'no-session' ? undefined : 'warning');
    if (gate === 'needs-prep') expect(banner.props.actions.props.variant).toBe('primary');
    banner.props.actions.props.onClick();
    expect(nav.push).toHaveBeenCalledWith(route);
  });
});
