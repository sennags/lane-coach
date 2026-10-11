import itertools
import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from lane_coach import create_app, generation
from lane_coach.knowledge import KnowledgeBase


@pytest.fixture
def knowledge():
    return KnowledgeBase()


@pytest.mark.parametrize('own,enemy', itertools.permutations(['Yone', 'Ahri', 'Yasuo', 'Zed'], 2))
def test_composes_every_direction(knowledge, own, enemy):
    guide = knowledge.guide(own, enemy)
    assert len(guide['sections']) == 5
    assert [s['champion'] for s in guide['sections']] == [enemy] * 3 + [own] * 2
    assert all(s['evidence'] and s['exception'] for s in guide['sections'])
    assert guide['status'] == 'demo'
    assert [profile['id'] for profile in guide['profiles']] == [own, enemy]
    assert all(set(profile['profile']['phases']) == {'lane', 'mid', 'late'}
               for profile in guide['profiles'])
    assert knowledge.context(own, enemy)['own']['id'] == own


def test_context_is_isolated_and_version_changes(knowledge, tmp_path):
    context = knowledge.context('Yone', 'Ahri')
    context['own']['tips'][0]['action'] = 'changed'
    assert knowledge.context('Yone', 'Ahri')['own']['tips'][0]['action'] != 'changed'
    for key, value in knowledge.champions.items():
        (tmp_path / f'{key}.json').write_text(json.dumps(value), encoding='utf-8')
    assert KnowledgeBase(tmp_path).version == knowledge.version
    (tmp_path / 'Yone.json').write_text(json.dumps(context['own']), encoding='utf-8')
    assert KnowledgeBase(tmp_path).version != knowledge.version


def test_unknown_evidence_blocks_loading(knowledge, tmp_path):
    champion = knowledge.context('Yone', 'Ahri')['own']
    champion['tips'][0]['evidence_ids'] = ['invented']
    (tmp_path / 'Yone.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError):
        KnowledgeBase(tmp_path)


@pytest.mark.parametrize('failure', ['missing_phase', 'empty_plan', 'empty_weaknesses', 'false_review'])
def test_incomplete_profiles_are_rejected(knowledge, tmp_path, failure):
    champion = knowledge.context('Yone', 'Ahri')['own']
    profile = champion['profile']
    if failure == 'missing_phase': del profile['phases']['late']
    if failure == 'empty_plan': profile['phases']['lane']['plan'] = ' '
    if failure == 'empty_weaknesses': profile['weaknesses'] = []
    if failure == 'false_review': profile['status'] = 'reviewed'
    (tmp_path / 'Yone.json').write_text(json.dumps(champion), encoding='utf-8')
    with pytest.raises(ValueError):
        KnowledgeBase(tmp_path)


def test_profile_output_preserves_perspective_and_escapes_content(knowledge, tmp_path):
    for key, champion in knowledge.champions.items():
        data = json.loads(json.dumps(champion))
        if key == 'Yone': data['facts'][0]['coaching']['use'] = '<script>alert(1)</script>'
        (tmp_path / f'{key}.json').write_text(json.dumps(data), encoding='utf-8')
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3'),
                      'KNOWLEDGE_PATH': str(tmp_path)})
    response = app.test_client().get('/matchup?champion=Ahri&opponent=Yone&lane=mid')
    assert response.status_code == 200
    assert '<script>alert(1)</script>' not in response.text
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in response.text
    assert 'Plano para quem joga Ahri' in response.text
    assert 'Sua resposta contra Yone' in response.text
    assert 'Sua resposta contra Ahri' not in response.text
    assert response.text.count('data-phase="late"') == 2


def valid_output():
    return {'tips': [{'title': 'Escudo', 'situation': 'Ao trocar', 'action': 'Considere W',
                      'reason': 'Concede escudo', 'exception': 'Depende do alcance',
                      'evidence_ids': ['Yone.W']}]}


@pytest.mark.parametrize('mutation', ['unknown', 'empty', 'long', 'extra', 'missing', 'type'])
def test_rejects_invalid_generation(knowledge, mutation):
    value = valid_output()
    tip = value['tips'][0]
    if mutation == 'unknown': tip['evidence_ids'] = ['Ahri.fake']
    if mutation == 'empty': value['tips'] = []
    if mutation == 'long': tip['action'] = 'x' * 601
    if mutation == 'extra': tip['source_url'] = 'https://untrusted.example'
    if mutation == 'missing': del tip['exception']
    if mutation == 'type': tip['evidence_ids'] = [{}]
    with pytest.raises(generation.GenerationError):
        generation.validate_output(value, knowledge.context('Yone', 'Ahri'))


def test_provider_contract_and_minimal_data(knowledge, monkeypatch):
    def open_request(request, timeout):
        assert request.full_url == 'https://api.groq.com/openai/v1/chat/completions'
        assert timeout == 20
        body = json.loads(request.data)
        assert body['response_format'] == {'type': 'json_object'}
        assert 'test-secret' not in request.data.decode()
        context = json.loads(body['messages'][1]['content'])
        assert set(context) == {'version', 'lane', 'own', 'enemy', 'limitations'}
        return BytesIO(json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
            'content': json.dumps(valid_output())}}]}).encode())
    class Opener:
        open = staticmethod(open_request)
    monkeypatch.setattr(generation, 'build_opener', lambda *args: Opener())
    result = generation.generate(knowledge.context('Yone', 'Ahri'), 'test-secret', 'test-model')
    assert result == valid_output()


@pytest.mark.parametrize('failure', ['timeout', 'quota', 'json', 'truncated', 'oversized', 'shape'])
def test_provider_failure_is_safe(knowledge, monkeypatch, failure):
    def open_request(*args, **kwargs):
        if failure == 'timeout': raise URLError('test-secret')
        if failure == 'quota': raise HTTPError('https://api.groq.com', 429, 'test-secret', {}, None)
        if failure == 'json': return BytesIO(b'not JSON')
        if failure == 'oversized': return BytesIO(b'x' * 100_001)
        if failure == 'shape': return BytesIO(b'{"choices": [null]}')
        return BytesIO(b'{"choices": [{"finish_reason": "length"}]}')
    class Opener:
        open = staticmethod(open_request)
    monkeypatch.setattr(generation, 'build_opener', lambda *args: Opener())
    with pytest.raises(generation.GenerationError) as error:
        generation.generate(knowledge.context('Yone', 'Ahri'), 'test-secret', 'test-model')
    assert 'test-secret' not in str(error.value)


def test_cli_dry_run_and_web_do_not_call_provider(tmp_path, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail('Unexpected external request')
    monkeypatch.setattr(generation, 'build_opener', unexpected)
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3')})
    response = app.test_client().get('/matchup?champion=Zed&opponent=Ahri&lane=mid')
    assert response.status_code == 200
    assert app.test_client().post('/matchup').status_code == 405
    runner = app.test_cli_runner()
    result = runner.invoke(args=['preview-ai', 'Yone', 'Ahri'])
    assert result.exit_code == 0
    assert json.loads(result.output)['enemy']['id'] == 'Ahri'
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    result = runner.invoke(args=['preview-ai', 'Yone', 'Ahri', '--generate'])
    assert result.exit_code != 0
    assert 'Configure GROQ_API_KEY' in result.output
