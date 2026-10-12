import sqlite3
import pytest
from lane_coach import create_app

@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.sqlite3')})

@pytest.mark.parametrize('opponent', ['Ahri', 'Yasuo', 'Zed'])
def test_guides(app, opponent):
    response = app.test_client().get(f'/matchup?champion=Yone&opponent={opponent}&lane=mid')
    assert response.status_code == 200
    assert 'class="profile-source"' not in response.text
    assert 'Descrição oficial' not in response.text
    assert 'class="review"' not in response.text

@pytest.mark.parametrize('query', ['', 'champion=Yone&opponent=Ahri', 'champion=Yone&opponent=Yone&lane=mid', 'champion=Yone&opponent=Ahri&lane=unknown', 'champion=Yone&opponent=Ahri&lane=mid&lane=mid', 'champion=Yone&opponent=Ahri&lane=mid&extra=1', 'champion=%3Cscript%3Ealert(1)%3C/script%3E&opponent=Ahri&lane=mid', "champion=Yone%27%3B%20DROP%20TABLE%20guides%3B--&opponent=Ahri&lane=mid"])
def test_invalid(app, query):
    client = app.test_client()
    response = client.get('/matchup?' + query)
    assert response.status_code == 400
    assert '<script>alert(1)</script>' not in response.text
    assert client.get('/healthz').json == {'status': 'ok'}

def test_reverse(app):
    response = app.test_client().get('/matchup?champion=Ahri&opponent=Yone&lane=mid')
    assert response.status_code == 200
    assert 'Ahri contra Yone' in response.text
    assert 'aria-label="Categorias de Yone"' in response.text

def test_privacy(app):
    response = app.test_client().get('/')
    assert response.status_code == 200
    assert 'Set-Cookie' not in response.headers
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    assert response.headers['Cache-Control'] == 'no-store'
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    with sqlite3.connect(app.config['DATABASE']) as connection:
        assert {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} == {'champions', 'guides'}

def test_restart(app):
    with sqlite3.connect(app.config['DATABASE']) as connection:
        connection.execute("UPDATE guides SET summary='Conteúdo revisado localmente' WHERE opponent='Ahri'")
    restarted = create_app({'TESTING': True, 'DATABASE': app.config['DATABASE']})
    assert restarted.test_client().get('/matchup?champion=Yone&opponent=Ahri&lane=mid').status_code == 200
    with sqlite3.connect(app.config['DATABASE']) as connection:
        assert connection.execute('SELECT COUNT(*) FROM guides').fetchone()[0] == 3
        assert connection.execute("SELECT summary FROM guides WHERE opponent='Ahri'").fetchone()[0] == 'Conteúdo revisado localmente'

def test_backup(app, tmp_path):
    target = tmp_path / 'backup.sqlite3'
    runner = app.test_cli_runner()
    assert runner.invoke(args=['backup-db', str(target)]).exit_code == 0
    with sqlite3.connect(target) as connection:
        assert connection.execute('SELECT COUNT(*) FROM guides').fetchone()[0] == 3
        assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    assert runner.invoke(args=['backup-db', str(target)]).exit_code != 0

def test_database_failure(app):
    with sqlite3.connect(app.config['DATABASE']) as connection:
        connection.execute('DROP TABLE guides')
    response = app.test_client().get('/healthz')
    assert response.status_code == 503
    assert 'temporariamente indisponíveis' in response.text
    assert app.config['DATABASE'] not in response.text
    assert 'Traceback' not in response.text


@pytest.mark.parametrize('lane', ['top', 'jungle', 'mid', 'adc', 'support'])
def test_lane_selection_is_validated_and_preserved(app, lane):
    response = app.test_client().get(f'/matchup?champion=Yone&opponent=Ahri&lane={lane}')
    assert response.status_code == 200
    assert f'value="{lane}" selected' in response.text
    assert response.text.count('class="classification-facts"') == 2
    assert app.extensions['knowledge'].context('Yone', 'Ahri', lane)['lane'] == lane


def test_local_selection_does_not_open_external_connections(tmp_path, monkeypatch):
    import socket
    def unexpected(*args, **kwargs):
        pytest.fail('Local champion selection must not open an external connection')
    monkeypatch.setattr(socket, 'create_connection', unexpected)
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'local.sqlite3')})
    client = app.test_client()
    for route in ('/', '/matchup?champion=Yone&opponent=Ahri&lane=mid',
                  '/matchup?champion=LeeSin&opponent=Evelynn&lane=jungle'):
        response = client.get(route)
        assert response.status_code == 200
        assert response.text.count('class="ability-entry"') == 10
        assert 'Aguardando dados' not in response.text
        assert 'matchup-statistics' not in response.text
    assert client.get('/api/statistics?champion=Yone&opponent=Ahri&lane=mid').status_code == 404
    assert client.post('/matchup').status_code == 405
    assert not any(rule.rule.startswith('/api/') for rule in app.url_map.iter_rules())
    assert set(app.cli.commands) == {'backup-db'}
    assert set(app.extensions) == {'knowledge'}
    assert {path.name for path in tmp_path.iterdir()} == {'local.sqlite3'}
