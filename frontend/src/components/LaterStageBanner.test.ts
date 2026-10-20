import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
const nav = vi.hoisted(() => ({push: vi.fn()}));
vi.mock('next/navigation', () => ({useRouter: () => nav}));
import { LaterStageBanner } from './LaterStageBanner';

describe('LaterStageBanner', () => {
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
    expect(tree.props.tone).toBe(gate === 'no-session' ? undefined : 'warning');
    if (gate === 'needs-prep') expect(tree.props.actions.props.variant).toBe('primary');
    tree.props.actions.props.onClick();
    expect(nav.push).toHaveBeenCalledWith(route);
  });
});
