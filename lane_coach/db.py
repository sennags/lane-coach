import json
import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=5)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(error=None):
    connection = g.pop('db', None)
    if connection is not None:
        connection.close()


def initialize():
    Path(current_app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    connection = get_db()
    connection.execute('PRAGMA journal_mode = WAL')
    connection.executescript('''
        CREATE TABLE IF NOT EXISTS champions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS guides (
            champion TEXT NOT NULL REFERENCES champions(id),
            opponent TEXT NOT NULL REFERENCES champions(id),
            lane TEXT NOT NULL CHECK(lane = 'mid'),
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            sections TEXT NOT NULL,
            revision TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('demo', 'reviewed')),
            patch TEXT NOT NULL,
            reviewed_at TEXT,
            PRIMARY KEY(champion, opponent, lane)
        );
        PRAGMA user_version = 1;
    ''')
    seed = json.loads((Path(__file__).parent / 'data' / 'guides.json').read_text(encoding='utf-8'))
    with connection:
        for champion in seed['champions']:
            connection.execute('INSERT OR IGNORE INTO champions VALUES (?, ?, ?)',
                               (champion['id'], champion['name'], champion['title']))
        for guide in seed['guides']:
            connection.execute('INSERT OR IGNORE INTO guides VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
                guide['champion'], guide['opponent'], 'mid', guide['title'], guide['summary'],
                json.dumps(guide['sections'], ensure_ascii=False), 'demo-1', 'demo', 'Não validado', None,
            ))


@click.command('backup-db')
@click.argument('destination', type=click.Path(dir_okay=False))
@click.option('--statistics', is_flag=True, help='Back up anonymous statistics instead of legacy guides.')
@with_appcontext
def backup_db(destination, statistics=False):
    """Back up the live SQLite database without overwriting existing files."""
    path = Path(destination).resolve()
    if path.exists():
        raise click.ClickException('O destino já existe. Escolha um novo arquivo.')
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as output:
        if statistics:
            with current_app.extensions['statistics'].store.connection() as connection:
                connection.backup(output)
        else:
            get_db().backup(output)
    click.echo(f'Backup criado: {path}')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(backup_db)
