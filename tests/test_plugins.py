"""Smoke tests run against every plugin in plugins/, including future ones."""
import importlib

import pytest

from conftest import PLUGINS

SIZES = [(1920, 1080), (800, 450), (320, 200), (64, 48)]


def test_plugins_found():
    assert {"thematrix", "starfield", "rain", "snow"} <= set(PLUGINS)


@pytest.mark.parametrize("name", PLUGINS)
def test_plugin_interface(name):
    plugin = importlib.import_module(f"plugins.{name}")
    for fn in ("init", "render", "shutdown"):
        assert callable(getattr(plugin, fn, None)), f"{name} is missing {fn}()"
    fps = getattr(plugin, "FPS", 30)
    assert isinstance(fps, int) and 1 <= fps <= 240


@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("name", PLUGINS)
def test_plugin_runs_at_any_size(name, size, surface):
    plugin = importlib.import_module(f"plugins.{name}")
    screen = surface(*size)
    plugin.init(screen, size)
    for _ in range(90):                     # 1.5 seconds at 60 fps
        plugin.render(screen, 1 / 60)
    plugin.shutdown()


@pytest.mark.parametrize("name", PLUGINS)
def test_plugin_survives_frame_hitches(name, surface):
    """A long pause (e.g. the machine was busy) must not break the effect."""
    plugin = importlib.import_module(f"plugins.{name}")
    screen = surface(320, 200)
    plugin.init(screen, (320, 200))
    for dt in (1 / 60, 0.5, 2.0, 0.0, 1 / 60):
        plugin.render(screen, dt)


@pytest.mark.parametrize("name", PLUGINS)
def test_plugin_draws_something(name, surface):
    plugin = importlib.import_module(f"plugins.{name}")
    screen = surface(320, 200)
    plugin.init(screen, (320, 200))
    for _ in range(60):
        plugin.render(screen, 1 / 60)
    colors = {screen.get_at((x, y))[:3] for x in range(0, 320, 4) for y in range(0, 200, 4)}
    assert len(colors) > 1, f"{name} drew a blank screen"
