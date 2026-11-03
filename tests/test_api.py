import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PRODUCT = {"name": "Прибор X", "manufacturer": "Производитель", "specs": {"диапазон": "0–1,6 МПа", "питание": ""}, "description": "Измеряет давление."}
COPY = {"seo_title": "Прибор X", "seo_description": "Прибор X измеряет давление.", "search_queries": ["прибор X", "прибор X давление", "прибор X производитель"], "commercial_block": "Для измерения давления."}


def fake_provider(monkeypatch, copy=COPY):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    def post(url, **kwargs):
        assert url.endswith('/chat/completions')
        assert kwargs['json']['messages'][0]['role'] == 'system'
        assert kwargs['json']['messages'][1]['role'] == 'user'
        request = httpx.Request('POST', url)
        return httpx.Response(200, request=request, json={'choices': [{'message': {'content': json.dumps(copy, ensure_ascii=False)}}]})
    monkeypatch.setattr('app.main.httpx.post', post)


def test_health_and_page():
    assert client.get('/health').json() == {'status': 'ok', 'service': 'ai-helper'}
    assert 'AI-Helper' in client.get('/').text
    assert '/generate' in client.get('/openapi.json').json()['paths']


def test_input_validation_and_missing_key(monkeypatch):
    assert client.post('/generate', content='{bad', headers={'Content-Type': 'application/json'}).status_code == 422
    for changes in ({'name': '   '}, {'manufacturer': ''}, {'specs': {'x': 5}}, {'specs': {'': 'x'}}, {'extra': 'x'}):
        assert client.post('/generate', json={**PRODUCT, **changes}).status_code == 422
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    assert client.post('/generate', json=PRODUCT).status_code == 503


def test_specs_are_from_input_and_missing_values_are_visible(monkeypatch):
    fake_provider(monkeypatch)
    result = client.post('/generate', json=PRODUCT)
    assert result.status_code == 200
    data = result.json()
    assert data['model_input'] == PRODUCT
    assert data['specs'] == {'диапазон': '0–1,6 МПа', 'питание': 'данных нет'}
    assert 'питание: данных нет' in data['missing_fields']
    assert any('800–1200' in w for w in data['warnings'])
    assert data['status'] == 'warning'


def test_model_output_checks(monkeypatch):
    fake_provider(monkeypatch, {**COPY, 'seo_title': 'А' * 71, 'seo_description': 'Допустимо 99 МПа.', 'search_queries': ['Один', 'один']})
    data = client.post('/generate', json=PRODUCT).json()
    assert any('максимум 70' in w for w in data['warnings'])
    assert any('99' in w for w in data['warnings'])
    assert '99' not in data['seo_description']
    assert any('3–5' in w for w in data['warnings'])


def test_displayed_input_matches_model_message(monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key')
    sent = {}

    def post(url, **kwargs):
        sent.update(json.loads(kwargs['json']['messages'][1]['content']))
        return httpx.Response(200, request=httpx.Request('POST', url), json={
            'choices': [{'message': {'content': json.dumps(COPY, ensure_ascii=False)}}]
        })

    monkeypatch.setattr('app.main.httpx.post', post)
    response = client.post('/generate', json={**PRODUCT, 'name': '  Прибор X  '})
    assert response.status_code == 200
    assert response.json()['model_input'] == sent
    assert sent['name'] == 'Прибор X'


@pytest.mark.parametrize('mode, expected', [('timeout', 504), ('network', 502), ('unauthorized', 502), ('bad_json', 502), ('blank', 502), ('bad_schema', 502)])
def test_provider_failures(monkeypatch, mode, expected):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'secret')
    def post(url, **kwargs):
        req = httpx.Request('POST', url)
        if mode == 'timeout': raise httpx.ReadTimeout('secret', request=req)
        if mode == 'network': raise httpx.ConnectError('secret', request=req)
        if mode == 'unauthorized': return httpx.Response(401, request=req, text='secret')
        content = {'bad_json': '{', 'blank': ' ', 'bad_schema': '{"seo_title":"x"}'}[mode]
        return httpx.Response(200, request=req, json={'choices': [{'message': {'content': content}}]})
    monkeypatch.setattr('app.main.httpx.post', post)
    response = client.post('/generate', json=PRODUCT)
    assert response.status_code == expected
    assert 'secret' not in response.text


def test_extra_provider_fields_are_rejected(monkeypatch):
    fake_provider(monkeypatch, {**COPY, 'specs': {'диапазон': '999 МПа'}})
    assert client.post('/generate', json=PRODUCT).status_code == 502


@pytest.mark.parametrize('stem', ['rgk_ct12', 'oven_pm01'])
def test_recorded_feed_examples_through_api(monkeypatch, stem):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'examples'
    product = json.loads((root / f'{stem}.input.json').read_text(encoding='utf-8'))
    expected = json.loads((root / f'{stem}.live.json').read_text(encoding='utf-8'))
    copy = {k: expected[k] for k in ('seo_title', 'seo_description', 'search_queries', 'commercial_block')}
    fake_provider(monkeypatch, copy)
    actual = client.post('/generate', json=product)
    assert actual.status_code == 200
    assert actual.json()['model_input'] == product
    assert {k: v for k, v in actual.json().items() if k != 'model_input'} == expected
    assert actual.json()['specs'] == product['specs']
    if not product['specs']:
        assert any('характеристики: данных нет' in item for item in actual.json()['missing_fields'])
    assert len(expected['seo_title']) <= 70
    assert 3 <= len(expected['search_queries']) <= 5
    assert any('800–1200' in item for item in expected['warnings'])


def test_dotenv_loads_file_without_overriding_environment(monkeypatch, tmp_path):
    from app.main import load_environment
    config = tmp_path / '.env'
    config.write_text('DEEPSEEK_API_KEY=file-key\nDEEPSEEK_MODEL=file-model\n', encoding='utf-8')
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.setenv('DEEPSEEK_MODEL', 'environment-model')
    load_environment(config)
    import os
    assert os.environ['DEEPSEEK_API_KEY'] == 'file-key'
    assert os.environ['DEEPSEEK_MODEL'] == 'environment-model'


def test_optional_search_includes_sources_but_not_in_specs(monkeypatch):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key')
    sent = {}
    source = {'title': 'Применение X', 'url': 'https://example.org/product', 'summary': 'Прибор X измеряет давление.'}

    def post(url, **kwargs):
        request = httpx.Request('POST', url)
        if url.endswith('/v1/tools/search'):
            assert kwargs['json']['count'] == 5
            assert 'Прибор X' in kwargs['json']['query']
            return httpx.Response(200, request=request, json={'results': [source, {'title': 'bad', 'url': 'javascript:alert(1)', 'summary': 'text'}]})
        sent.update(json.loads(kwargs['json']['messages'][1]['content']))
        return httpx.Response(200, request=request, json={'choices': [{'message': {'content': json.dumps(COPY, ensure_ascii=False)}}]})

    monkeypatch.setattr('app.main.httpx.post', post)
    response = client.post('/generate?web_search=true', json=PRODUCT)
    data = response.json()
    assert response.status_code == 200
    assert data['search_status'] == 'found'
    assert data['sources'] == [{'title': source['title'], 'url': source['url'], 'excerpt': source['summary']}]
    assert data['model_input'] == sent
    assert sent['search_sources'] == data['sources']
    assert data['specs']['диапазон'] == PRODUCT['specs']['диапазон']
    assert any('внешние источники' in item for item in data['warnings'])


@pytest.mark.parametrize('mode', ['empty', 'unavailable'])
def test_search_failure_is_visible_and_generation_continues(monkeypatch, mode):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key')

    def post(url, **kwargs):
        request = httpx.Request('POST', url)
        if url.endswith('/v1/tools/search'):
            if mode == 'unavailable':
                raise httpx.ConnectError('offline', request=request)
            return httpx.Response(200, request=request, json={'results': []})
        assert 'search_sources' not in json.loads(kwargs['json']['messages'][1]['content'])
        return httpx.Response(200, request=request, json={'choices': [{'message': {'content': json.dumps(COPY, ensure_ascii=False)}}]})

    monkeypatch.setattr('app.main.httpx.post', post)
    response = client.post('/generate?web_search=true', json=PRODUCT)
    assert response.status_code == 200
    assert response.json()['search_status'] == mode
    assert response.json()['sources'] == []
    assert any('Поиск' in warning or 'поиск' in warning for warning in response.json()['warnings'])
