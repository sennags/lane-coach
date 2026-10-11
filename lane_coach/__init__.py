import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from . import db
from .knowledge import KnowledgeBase, LANES, MAINTENANCE_CHAMPIONS
from .generation import preview_ai


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get('DATABASE_PATH', str(Path(app.instance_path) / 'lane-coach.sqlite3')),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    knowledge = KnowledgeBase(app.config.get('KNOWLEDGE_PATH'))
    app.extensions['knowledge'] = knowledge
    app.cli.add_command(preview_ai)
    db.init_app(app)
    with app.app_context():
        db.initialize()

    def page(guide=None, message=None, status=200, message_title='Seleção inválida'):
        champions = sorted(knowledge.champions.values(), key=lambda champion: champion['name'])
        choices = {champion['id']: champion for champion in champions}
        own = request.args.get('champion', 'Yone')
        enemy = request.args.get('opponent', 'Ahri')
        return render_template(
            'index.html', champions=champions, own=choices.get(own, choices['Yone']),
            enemy=choices.get(enemy, choices['Ahri']), guide=guide, message=message,
            lanes=LANES, selected_lane=request.args.get('lane', 'general'),
            maintenance_champions=MAINTENANCE_CHAMPIONS, message_title=message_title,
        ), status

    @app.get('/')
    def index():
        return page(guide=knowledge.guide('Yone', 'Ahri', 'general'))

    @app.get('/matchup')
    def matchup():
        fields = ('champion', 'opponent', 'lane')
        if set(request.args) != set(fields) or any(len(request.args.getlist(key)) != 1 for key in fields):
            return page(message='Selecione seu campeão, o adversário e a lane para continuar.', status=400)
        own, enemy, lane = (request.args[key] for key in fields)
        known = knowledge.champions
        if own not in known or enemy not in known:
            return page(message='Escolha campeões disponíveis na lista.', status=400)
        if own == enemy:
            return page(message='Escolha dois campeões diferentes para este confronto.', status=400)
        if lane not in LANES:
            return page(message='Escolha uma lane disponível na lista.', status=400)
        if own in MAINTENANCE_CHAMPIONS or enemy in MAINTENANCE_CHAMPIONS:
            return page(message='Aphelios e Hwei estão em manutenção para revisão dos seus kits diferenciados. Escolha outro campeão.',
                        status=503, message_title='Campeão em manutenção')
        return page(guide=knowledge.guide(own, enemy, lane))

    @app.get('/healthz')
    def health():
        db.get_db().execute('SELECT COUNT(*) FROM guides').fetchone()
        return jsonify(status='ok')

    @app.errorhandler(sqlite3.Error)
    def database_error(error):
        # No query values, request details, paths or credentials in public errors/logs.
        app.logger.error('Database unavailable (%s)', type(error).__name__)
        return render_template('error.html', message='Os guias estão temporariamente indisponíveis. Tente novamente em instantes.'), 503

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', message='Essa página não foi encontrada.'), 404

    @app.after_request
    def security_headers(response):
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
            "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request.endpoint != 'static':
            response.headers['Cache-Control'] = 'no-store'
        return response

    return app
