import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it } from 'vitest';
import { TargetReportView } from './TargetReport';
import type { SegmentTargetReport } from '@/lib/types';

const card = { desire: '', context: '', pain: '코골이 때문에 각방', unmet: '', keywords: [], quotes: [] };
const report: SegmentTargetReport = {
  total: 1000, assigned: 80, other: 920, at: '2026-11-05',
  personas: [{
    id: 'T1', name: '잠자리 협상가', card, threshold: .7, pool: 100, viral: 15, ads: 5, docs: 80, firstPerson: 40, flags: [],
    bands: [{ start: .7, docs: 100, judged: 20, precision: .8, yes: 14 }],
    needs: { sampled: 80, judged: 80, mine: 40, share: .5, causes: [{ label: '남편 코골이', count: 30 }],
      tried: [{ tried: '제품·기기', total: 6, '효과 있음': 1, '일시적': 3, '효과 없음': 2 }],
      examples: [{ docId: 'd1', title: '각방 고민', source: 'naver_cafe', sentences: ['남편 코골이 때문에 잠을 못 자요.'], cause: '남편 코골이', tried: '제품·기기', result: '일시적' }] },
    quotes: [{ docId: 'd1', title: '각방 고민', source: 'naver_cafe', sentences: ['중복'] }, { docId: 'd2', title: '침대', source: 'naver_cafe', sentences: ['같이 자고 싶어요.'] }],
  }, {
    id: 'T2', name: '빈 카드', card: { ...card, pain: '' }, threshold: null, pool: 0, viral: 0, ads: 0, docs: 0, firstPerson: null,
    flags: ['no_match'], bands: [], needs: null, quotes: [],
  }],
  discovered: [{ id: 'N1-1', docs: 300, keywords: ['어깨', '뭉침'], quotes: [], label: { name: '뭉침·통증', who: '직장인', pain: '어깨가 늘 뭉침', consumer_voice: true } }],
};

it('shows counts, removals, tried table, deduplicated quotes, no-match and candidates', () => {
  const html = renderToStaticMarkup(createElement(TargetReportView, { report }));
  expect(html).toContain('목표 페르소나 80건 (8%)');
  expect(html).toContain('기타 920건 (92%)');
  expect(html).toContain('약 40건');
  expect(html).toContain('15 / 5건');
  expect(html).toContain('남편 코골이 30');
  expect(html).toContain('<td>제품·기기</td><td>6</td><td>1</td><td>3</td><td>2</td>');
  expect(html).toContain('제품·기기 → 일시적');
  expect(html).not.toContain('중복');
  expect(html).toContain('같이 자고 싶어요.');
  expect(html).toContain('맞는 문서 없음');
  expect(html).toContain('기타에서 찾은 새 후보 1개');
  expect(html).toContain('본인 경험 위주');
});
