"""Rain: drops stay in bounds and splashes are limited."""
from plugins import rain

SIZE = (320, 200)


def test_drops_respawn_before_passing_their_ground(surface):
    screen = surface(*SIZE)
    rain.init(screen, SIZE)
    for _ in range(300):
        rain.render(screen, 1 / 60)
        assert all(d.y < d.ground for d in rain._drops)


def test_splashes_are_capped(monkeypatch, surface):
    monkeypatch.setattr(rain, "MAX_SPLASHES", 10)
    screen = surface(*SIZE)
    rain.init(screen, SIZE)
    for _ in range(300):
        rain.render(screen, 1 / 60)
        # A drop adds at most 4 droplets once the cap check passes.
        assert len(rain._splashes) <= 10 + 3


def test_only_near_drops_splash(surface):
    rain.init(surface(*SIZE), SIZE)
    rain._splashes.clear()
    far, near = rain._Drop(0.2), rain._Drop(0.9)
    for drop in (far, near):
        drop.respawn(*SIZE)
    rain._splash(far)
    assert rain._splashes == []
    rain._splash(near)
    assert 2 <= len(rain._splashes) <= 4


def test_splashes_fade_out(surface):
    screen = surface(*SIZE)
    rain.init(screen, SIZE)
    near = rain._Drop(1.0)
    near.respawn(*SIZE)
    rain._splashes.clear()
    rain._splash(near)
    for drop in rain._drops:                # keep new drops from splashing
        drop.depth = 0.0
    for _ in range(60):                     # 1s: longer than any splash lives
        rain.render(screen, 1 / 60)
    assert not any(s[0] == near.x for s in rain._splashes)
