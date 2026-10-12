from lane_coach import create_app
from lane_coach.knowledge import KnowledgeBase, MAINTENANCE_CHAMPIONS


def test_every_available_champion_has_editorial_notes_and_combat_roles():
    base = KnowledgeBase()
    available = [c for key, c in base.champions.items() if key not in MAINTENANCE_CHAMPIONS]
    assert len(available) == 171
    for champion in available:
        profile = champion['profile']
        assert profile['basis'] == 'champion_specific', champion['id']
        assert profile['status'] == 'editorial_unreviewed'
        assert not profile['reviewed_at']
        assert all(set(f['coaching']) == {'use', 'limit'} for f in champion['facts'])
        for phase in profile['phases'].values():
            assert phase['resource'] and phase['caution']
        assert profile['phases']['mid']['plan'] != profile['phases']['late']['plan']
    # Roles are authored per champion, not a renamed class template.
    assert len({c['profile']['phases']['mid']['plan'] for c in available}) > 150


def test_repeat_cooldowns_compact_and_scaling_not_mixed_with_damage(tmp_path):
    app = create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'cooldown.sqlite3')})
    html = app.test_client().get('/matchup?champion=Yone&opponent=Annie&lane=mid').text
    assert 'Recarga base: 4 s' in html
    assert '4 / 4 / 4' not in html
    assert 'Velocidade de Ataque adicional, até o mínimo de 1,33 s' in html
    assert 'Recarga base: 120 / 100 / 80 s' in html
    assert html.count('class="ability-coaching"') == 0
