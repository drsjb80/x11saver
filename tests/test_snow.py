"""Snow: the build -> hold -> melt cycle and the snow pile."""
import pytest

from plugins import snow

SIZE = (320, 200)


@pytest.fixture
def fast_cycle(monkeypatch, surface):
    monkeypatch.setattr(snow, "HOLD_SECONDS", 1)
    monkeypatch.setattr(snow, "MELT_SECONDS", 2)
    screen = surface(*SIZE)
    snow.init(screen, SIZE)
    return screen


def run_until(screen, condition, limit_s=900, dt=1 / 30):
    t = 0.0
    while not condition():
        snow.render(screen, dt)
        t += dt
        assert t < limit_s, "snow cycle did not progress"
    return t


def test_full_cycle_rebuilds_with_new_drift_shape(fast_cycle):
    screen = fast_cycle
    first_shape = snow._caps[:]
    phases = [snow._phase]
    for target in ("hold", "melt", "build"):
        run_until(screen, lambda: snow._phase == target)
        phases.append(snow._phase)
    assert phases == ["build", "hold", "melt", "build"]
    assert max(snow._pile) == 0.0
    assert snow._caps != first_shape


def test_pile_never_exceeds_drift_height(fast_cycle):
    screen = fast_cycle
    tallest = max(snow._caps)
    while snow._phase == "build":
        snow.render(screen, 1 / 30)
        assert max(snow._pile) <= tallest + 1e-9


def test_melt_only_shrinks_and_keeps_shape(fast_cycle):
    screen = fast_cycle
    run_until(screen, lambda: snow._phase == "melt")
    start = snow._melt_from[:]
    previous = sum(snow._pile)
    while snow._phase == "melt":
        snow.render(screen, 1 / 30)
        total = sum(snow._pile)
        assert total <= previous + 1e-9        # new flakes don't stick while melting
        previous = total
        if snow._phase == "melt" and max(snow._pile) > 0:
            # Every column is the same fraction of where it started.
            ratio = max(snow._pile) / max(start)
            for now, then in zip(snow._pile, start):
                assert now == pytest.approx(then * ratio, abs=1e-6)


def test_offscreen_column_mirrors_right_edge(fast_cycle):
    screen = fast_cycle
    for _ in range(600):
        snow.render(screen, 1 / 30)
    assert snow._pile[snow._visible] == snow._pile[snow._visible - 1]


def test_far_flakes_do_not_add_to_pile(monkeypatch, surface):
    screen = surface(*SIZE)
    snow.init(screen, SIZE)
    for flake in snow._flakes:
        flake.depth = 0.2                   # all "far away"
    for _ in range(600):
        snow.render(screen, 1 / 30)
    assert max(snow._pile) == 0.0
