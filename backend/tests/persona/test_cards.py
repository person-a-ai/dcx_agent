import json
from copy import deepcopy

import pytest
from pydantic import BaseModel, ConfigDict

from app.llm.base import failure, validate
from app.persona.cards import generate_card
from app.persona.package import Package, evidence_index
from tests.fixtures.evidence_package import make_package, fake_persona_backend


class RawOutput(BaseModel):
    model_config = ConfigDict(extra="allow")


class Runner:
    """Adapt the shared fake's Persona-wide citations to chunk-local IDs."""
    def __init__(self, package, mutate=None):
        self.package = Package.model_validate(package)
        self.backend = fake_persona_backend(package)
        self.calls = []
        self.mutate = mutate

    def __call__(self, task):
        self.calls.append(task)
        result = self.backend.run(task.model_copy(update={"output_schema": RawOutput}))
        data = json.loads(result.raw)
        if task.task == 'persona.card':
            payload = json.loads(task.attachments[0].body)
            block = next(b for b in self.package.personas if b.persona_evidence.persona_id == payload['persona_id'])
            selected = payload['context_ids']
            keys = [k for k, ref in evidence_index(block).items() if ref.context_id in selected]
            mapping = {key: f'E{i+1}' for i, key in enumerate(keys)}
            for row in data['contexts']:
                for cell in [row[field] for field in ('state', 'emotion', 'barrier')] + row.get('pain_points', []):
                    cell['cite'] = [mapping[c] for c in cell['cite']]
        if self.mutate:
            self.mutate(task, data)
        return validate(task, json.dumps(data))


def setup(**kwargs):
    raw = make_package(**kwargs)
    return Package.model_validate(raw), Runner(raw)


def test_chunks_of_four():
    package, runner = setup(big_persona_contexts=10)
    result = generate_card('s', package.personas[0], run_task=runner)
    assert result.status == 'done'
    assert [t.task for t in runner.calls] == ['persona.card'] * 3 + ['persona.summary']
    assert [len(json.loads(t.attachments[0].body)['context_ids']) for t in runner.calls[:3]] == [4, 4, 2]
    assert len(result.card['contexts']) == 10


def test_cite_renumbered():
    package, runner = setup(big_persona_contexts=10)
    block = package.personas[0]
    result = generate_card('s', block, run_task=runner)
    refs = evidence_index(block)
    for row, original in zip(result.card['contexts'], block.context_evidence):
        cite = row['state']['cite'][0]
        assert refs[cite].context_id == original.context_id
        assert refs[cite].quote == original.evidence[0].quote
    assert result.card['contexts'][4]['state']['cite'] == ['E18']
    assert result.card['trace'][0]['evidence']['quote'] == block.context_evidence[0].evidence[0].quote.model_dump()


def test_action_from_6c_not_generated():
    package, runner = setup()
    block = package.personas[0]
    block.context_evidence[0].action = '확정된 고유 행동'
    result = generate_card('s', block, run_task=runner)
    assert result.card['contexts'][0]['action'] == '확정된 고유 행동'
    schema = runner.calls[0].output_schema.model_json_schema()
    assert 'action' not in schema['$defs']['ContextOut']['properties']


@pytest.mark.parametrize('field', ['state', 'emotion', 'barrier'])
def test_dims_situation_keeps_cited_llm_text(field):
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.card':
            data['contexts'][0][field]['text'] = '다듬은 문장'
    runner.mutate = mutate
    result = generate_card('s', package.personas[0], run_task=runner)
    assert result.card['contexts'][0][field]['text'] == '다듬은 문장'


def test_target_scope_not_in_prompt():
    package, runner = setup()
    block = package.personas[0]
    block.model_extra['targetScope'] = 'SCOPE_SENTINEL'
    block.persona_evidence.model_extra['projectContext'] = {'targetScope': 'SCOPE_SENTINEL'}
    block.context_evidence[0].evidence[0].model_extra['targetScope'] = 'SCOPE_SENTINEL'
    generate_card('s', block, run_task=runner)
    for task in runner.calls:
        prompt = task.instructions + ''.join(a.body for a in task.attachments)
        assert 'targetScope' not in prompt
        assert 'SCOPE_SENTINEL' not in prompt


def test_desire_goal_equal_6b():
    package, runner = setup()
    block = package.personas[0]
    result = generate_card('s', block, run_task=runner)
    for field in ('persona_id', 'persona_name', 'desire', 'goal'):
        assert result.card[field] == getattr(block.persona_evidence, field)


@pytest.mark.parametrize('failed_task', ['persona.card', 'persona.summary'])
def test_schema_fail_twice_marks_failed(failed_task):
    package, runner = setup(big_persona_contexts=10)
    def mutate(task, data):
        if task.task == failed_task:
            data['unexpected'] = True
    runner.mutate = mutate
    result = generate_card('s', package.personas[0], run_task=runner)
    assert result.status == 'failed' and result.card is None
    assert sum(t.task == failed_task for t in runner.calls) == 2
    runner.mutate = None
    assert generate_card('s', package.personas[1], run_task=runner).status == 'done'


def test_null_when_no_evidence():
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.card':
            for row in data['contexts']:
                row['pain_points'] = []
                for field in ('state', 'emotion', 'barrier'):
                    row[field] = {'text': '지어낸 값', 'cite': []}
    runner.mutate = mutate
    result = generate_card('s', package.personas[-1], run_task=runner)
    assert result.card['pain_points'] == []
    assert result.card['contexts'][-1]['pain_points'] == []
    for field in ('state', 'emotion', 'barrier'):
        assert result.card['contexts'][-1][field] == {'text': None, 'cite': []}


@pytest.mark.parametrize('value', ['high', 0.8, '매우 높음'])
def test_sensitivity_ordinal_only(value):
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.summary':
            data['sensitivity']['price'] = value
    runner.mutate = mutate
    assert generate_card('s', package.personas[0], run_task=runner).status == 'failed'


@pytest.mark.parametrize('ratios,ok', [([.2, .3, .5], True), ([None]*3, True), ([.3]*3, False), ([None, .5, .5], False), ([-1., 1., 1.], False)])
def test_journey_ratios(ratios, ok):
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.summary':
            data['journey'] = dict(zip(('pre_purchase', 'purchase', 'post_purchase'), ratios))
    runner.mutate = mutate
    assert (generate_card('s', package.personas[0], run_task=runner).status == 'done') is ok


def test_recovery_and_no_retry_for_backend_failure():
    package, runner = setup()
    calls = []
    def recover(task):
        calls.append(task)
        return failure('schema', 'bad') if len(calls) == 1 else runner(task)
    assert generate_card('s', package.personas[0], run_task=recover).status == 'done'
    assert len(calls) == 3
    calls.clear()
    def broken(task):
        calls.append(task)
        return failure('backend', 'unavailable')
    assert generate_card('s', package.personas[0], run_task=broken).card is None
    assert len(calls) == 1


@pytest.mark.parametrize('issue', ['missing', 'duplicate', 'foreign_cite', 'foreign_context'])
def test_invalid_references_and_context_coverage(issue):
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.card':
            if issue == 'missing':
                data['contexts'].pop()
            elif issue == 'duplicate':
                data['contexts'][1] = deepcopy(data['contexts'][0])
            elif issue == 'foreign_cite':
                data['contexts'][0]['state']['cite'] = ['E999']
        elif issue == 'foreign_context':
            data['intent']['basis_context_ids'] = ['unknown']
    runner.mutate = mutate
    assert generate_card('s', package.personas[0], run_task=runner).status == 'failed'


def test_later_chunk_failure_discards_entire_card():
    package, runner = setup(big_persona_contexts=10)
    failed_id = package.personas[0].context_evidence[4].context_id
    def mutate(task, data):
        if task.task == 'persona.card' and data['contexts'][0]['context_id'] == failed_id:
            data['unexpected'] = True
    runner.mutate = mutate
    result = generate_card('s', package.personas[0], run_task=runner)
    assert result.status == 'failed' and result.card is None
    assert len(runner.calls) == 3
    assert all(task.task == 'persona.card' for task in runner.calls)


def test_default_registry_does_not_double_retry(monkeypatch):
    from app.llm import registry
    package, _ = setup()
    calls = []
    class BrokenBackend:
        def run(self, task):
            calls.append(task)
            return validate(task, '{}')
    monkeypatch.setattr(registry, 'get_backend', lambda name: BrokenBackend())
    result = generate_card('s', package.personas[0])
    assert result.status == 'failed' and result.card is None
    assert len(calls) == 2


def test_no_persona_evidence_nulls_summary():
    raw = make_package()
    block = raw['personas'][0]
    block['persona_evidence']['desire_support'] = []
    for context in block['context_evidence']:
        for field in ('evidence', 'counter_evidence', 'rare_evidence'):
            context[field] = []
    package, runner = Package.model_validate(raw), Runner(raw)
    card = generate_card('s', package.personas[0], run_task=runner).card
    assert card['intent']['text'] is None
    assert card['usage_context']['text'] is None
    assert card['jtbd']['text'] is None
    assert set(card['sensitivity'].values()) == {None}
    assert set(card['journey'].values()) == {None}
    assert card['trace'] == []
    assert card['pain_points'] == []


@pytest.mark.parametrize('field', ['state', 'emotion', 'barrier'])
def test_dims_situation_uncited_falls_back(field):
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.card':
            data['contexts'][0][field] = dict(text='근거에 없는 완전히 다른 상황', cite=[])
    runner.mutate = mutate
    card = generate_card('s', package.personas[0], run_task=runner).card
    assert card['contexts'][0][field] == dict(
        text=getattr(package.personas[0].context_evidence[0].situation, field), cite=[])


def pain_card(*, text='냉방 조절이 번거로움', tagged=True, verified=True, barrier=False):
    raw = make_package()
    # Global E2 (chunk-local E1) is the first Context's first support.
    evidence = raw['personas'][0]['context_evidence'][0]['evidence'][0]
    evidence['pain_point'] = dict(text='냉방 조절이 번거로움', quote='인용', verified=verified) if tagged else None
    package, runner = Package.model_validate(raw), Runner(raw)
    def mutate(task, data):
        if task.task == 'persona.card':
            data['contexts'][0]['pain_points'] = [dict(text=text, cite=['E1'])]
            if barrier:
                data['contexts'][0]['barrier'] = dict(text=None, cite=[])
    runner.mutate = mutate
    return generate_card('s', package.personas[0], run_task=runner), runner


def test_pain_points_observed_from_tagged_evidence():
    result, runner = pain_card(text='냉방_조절이 번거로움!')
    pain = result.card['contexts'][0]['pain_points'][0]
    assert pain == dict(text='냉방_조절이 번거로움!', cite=['E2'], grade='observed', source_pain='냉방 조절이 번거로움')
    payload = json.loads(runner.calls[0].attachments[0].body)
    assert payload['evidence']['E1']['pain_point'] == '냉방 조절이 번거로움'
    assert result.card['pain_points'][0]['grade'] == 'observed'


def test_pain_points_inferred_when_rewritten():
    result, _ = pain_card(text='냉방을 조절하기 어려움')
    pain = result.card['contexts'][0]['pain_points'][0]
    assert pain['grade'] == 'inferred'
    assert pain['source_pain'] == '냉방 조절이 번거로움'


def test_pain_points_observed_requires_pain_quote_verified():
    result, _ = pain_card(verified=False)
    assert result.card['contexts'][0]['pain_points'][0]['grade'] == 'inferred'


def test_pain_points_inferred_when_untagged():
    result, runner = pain_card(tagged=False)
    pain = result.card['contexts'][0]['pain_points'][0]
    assert pain['grade'] == 'inferred' and pain['source_pain'] is None
    assert json.loads(runner.calls[0].attachments[0].body)['evidence']['E1']['pain_point'] is None


@pytest.mark.parametrize('cites', [['E6'], [], ['E999']])
def test_pain_cite_must_belong_to_context(cites):
    package, runner = setup()
    def mutate(task, data):
        if task.task == 'persona.card':
            data['contexts'][0]['pain_points'] = [dict(text='불편', cite=cites)]
    runner.mutate = mutate
    result = generate_card('s', package.personas[0], run_task=runner)
    assert result.status == 'failed' and result.error == 'schema'
    assert len(runner.calls) == 2


def test_pain_cite_required():
    from app.persona.cards import PainCell
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        PainCell(text='불편', cite=[])


def test_pain_points_empty_without_evidence(monkeypatch):
    from app.persona import cards
    original_call = cards._call
    def call(*args):
        data, error = original_call(*args)
        if args[1] == 'card' and not error:
            data['contexts'][-1]['pain_points'] = [dict(text='지어낸 불편', cite=['E999'])]
        return data, error
    monkeypatch.setattr(cards, '_call', call)
    package, runner = setup()
    result = generate_card('s', package.personas[-1], run_task=runner)
    assert result.card['contexts'][-1]['pain_points'] == []


def test_barrier_filled_from_pain_point():
    result, _ = pain_card(barrier=True)
    assert result.card['contexts'][0]['barrier'] == dict(text='냉방 조절이 번거로움', cite=['E2'])


def test_aggregate_pain_points():
    from app.persona.cards import aggregate_pain_points
    def pain(text, cites, grade='inferred'):
        return dict(text=text, cite=cites, grade=grade, source_pain=None)
    contexts = [dict(context_id='c1', pain_points=[pain('같은 문장', ['E1']),
        pain('인용 많음', ['E3', 'E4', 'E9']), pain('문서 많음', ['E5'])]),
        dict(context_id='c2', pain_points=[pain('같은_문장!', ['E1', 'E2'], 'observed'),
            pain('문서 적음', ['E6']), pain('끝1', ['E7']), pain('끝2', ['E8'])])]
    original = deepcopy(contexts)
    result = aggregate_pain_points(contexts, {'c1': 10, 'c2': 1})
    assert len(result) == 5
    assert [p['text'] for p in result[:4]] == ['같은 문장', '인용 많음', '문서 많음', '문서 적음']
    assert result[0] == dict(text='같은 문장', grade='observed', context_ids=['c1', 'c2'], cite=['E1', 'E2'])
    assert contexts == original
    assert aggregate_pain_points([], {}) == []


def test_pain_cites_remapped_in_later_chunk():
    package, runner = setup(big_persona_contexts=10)
    card = generate_card('s', package.personas[0], run_task=runner).card
    assert card['contexts'][4]['pain_points'][0]['cite'] == ['E18']


def test_pain_source_uses_matching_tag_among_cited_refs():
    raw = make_package()
    evidence = raw['personas'][0]['context_evidence'][0]['evidence']
    evidence[0]['pain_point']['text'] = '첫 태그'
    evidence[1]['pain_point']['text'] = '일치하는 태그'
    package, runner = Package.model_validate(raw), Runner(raw)
    def mutate(task, data):
        if task.task == 'persona.card':
            data['contexts'][0]['pain_points'] = [dict(text='일치하는 태그!', cite=['E1', 'E2'])]
    runner.mutate = mutate
    pain = generate_card('s', package.personas[0], run_task=runner).card['contexts'][0]['pain_points'][0]
    assert pain['grade'] == 'observed' and pain['source_pain'] == '일치하는 태그'


def test_context_pain_points_max_three():
    from app.persona.cards import ContextOut
    from pydantic import ValidationError
    row = dict(context_id='c', **{field: dict(text=None, cite=[]) for field in ('state', 'emotion', 'barrier')})
    row['pain_points'] = [dict(text='불편', cite=['E1'])] * 4
    with pytest.raises(ValidationError):
        ContextOut.model_validate(row)
