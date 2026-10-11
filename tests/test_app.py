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
    assert 'Não validado' in response.text
    assert 'Ver base mecânica' in response.text

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
    assert 'CONTRA Yone' in response.text

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
    assert 'ainda não mudam por lane' in response.text
    assert app.extensions['knowledge'].context('Yone', 'Ahri', lane)['lane'] == lane
