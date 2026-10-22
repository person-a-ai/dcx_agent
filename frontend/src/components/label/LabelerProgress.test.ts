import { expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { LabelerProgress } from './LabelerProgress';
import type { LabelProgress } from '@/lib/types';

const explanation = '3번 시도해도 판정하지 못한 글은 검수 큐에서 사람이 판정합니다.';
const failure = '판정 실패 12건 · 검수 큐로 보냄';
const render = (progress: Partial<LabelProgress>, reviewQueue?: boolean) => renderToStaticMarkup(createElement(LabelerProgress, {
 name:'GPT', progress:{state:'running',done:4000,total:5688,pending:1676,bad:12,...progress}, reviewQueue,
}));

it('shows running failures after counts and before processing, with accessible explanation', () => {
 const html = render({}, true);
 expect(html).toContain(failure);
 expect(html).toContain(`title="${explanation}"`);
 expect(html).toContain(`<span class="sr-only">${explanation}</span>`);
 expect(html).toContain('class="ds-t-caption"');
 expect(html.indexOf('건 판정')).toBeLessThan(html.indexOf(failure));
 expect(html.indexOf(failure)).toBeLessThan(html.indexOf('<p>처리 중…</p>'));
});
it('shows paused failures before the stopped status', () => {
 const html = render({state:'paused'}, true);
 expect(html).toContain(failure);
 expect(html.indexOf(failure)).toBeLessThan(html.indexOf('판정이 멈췄습니다.'));
});
it('includes failures in the completion text without a separate failure line', () => {
 const html = render({state:'done',done:5676}, true);
 expect(html).toContain('<p>판정을 마쳤습니다. 12건은 판정하지 못해 검수 큐로 보냈습니다.</p>');
 expect(html).not.toContain(failure);
});
it.each(['running','done'])('does not mention review failures without reviewQueue in %s', state => {
 const html = render({state});
 expect(html).not.toContain('검수 큐');
 expect(html).not.toContain('판정 실패');
 if (state === 'done') expect(html).toContain('<p>판정을 마쳤습니다.</p>');
});
it.each(['running','done'])('does not mention zero or missing failures in %s', state => {
 for (const bad of [0, undefined]) {
  const html = render({state,bad}, true);
  expect(html).not.toContain('판정 실패');
  expect(html).not.toContain('검수 큐');
  if (state === 'done') expect(html).toContain('<p>판정을 마쳤습니다.</p>');
 }
});
it('does not show failures while waiting', () => {
 const html = render({state:'none',bad:3}, true);
 expect(html).not.toContain('판정 실패');
 expect(html).not.toContain('검수 큐');
});
it('formats failure counts with Korean thousands separators', () => {
 expect(render({bad:1234}, true)).toContain('판정 실패 1,234건 · 검수 큐로 보냄');
 expect(render({state:'done',bad:1234}, true)).toContain('1,234건은 판정하지 못해 검수 큐로 보냈습니다.');
});
