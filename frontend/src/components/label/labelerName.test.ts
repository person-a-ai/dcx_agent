import { expect, it } from 'vitest';
import { crossCostLine, crossLabelerName, GPT_ONLY_BODY, GPT_ONLY_TITLE, gptOnlyNotice } from './labelerMode';

it('names the cross labeler from the overview and falls back to Jev', () => {
 expect(crossLabelerName({crossLabeler:'Decisions'})).toBe('Decisions');
 expect(crossLabelerName({crossLabeler:'Jev'})).toBe('Jev');
 expect(crossLabelerName({})).toBe('Jev');
});

it('shows the Decisions cost estimate in dollars with input tokens', () => {
 expect(crossCostLine('Decisions', {seconds:null, jevTokens:12345, jevCostUsd:1.234})).toBe('예상 Decisions 비용 · 약 $1.23(입력 12,345토큰)');
 expect(crossCostLine('Decisions', {seconds:null, jevCostUsd:0})).toBe('예상 Decisions 비용 · 약 $0.00');
});

it('keeps the current wording when no dollar estimate is available', () => {
 expect(crossCostLine('Jev', {seconds:null, jevTokens:500, jevCostUsd:null})).toBe('예상 Jev 비용 · 금액 추정은 아직 제공되지 않습니다. 예상 입력 500토큰');
 expect(crossCostLine('Jev', {seconds:null})).toBe('예상 Jev 비용 · 금액 추정은 아직 제공되지 않습니다.');
 expect(crossCostLine('Jev', undefined)).toBe('예상 Jev 비용 · 금액 추정은 아직 제공되지 않습니다.');
});

it('names the cross labeler in the GPT-only notice', () => {
 expect(gptOnlyNotice('Decisions')).toEqual({
  title:'Decisions 미연결 · GPT 단독 판정',
  body:'등급 불일치 검수 없이 GPT 판정을 그대로 채택합니다. 오류는 무작위 감사로 확인합니다. Decisions를 연결한 뒤 새 버전에서 시작하면 교차 판정합니다.',
 });
 expect(gptOnlyNotice('Jev')).toEqual({title:GPT_ONLY_TITLE, body:GPT_ONLY_BODY});
});
