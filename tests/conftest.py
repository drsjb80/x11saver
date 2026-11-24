"""Shared test setup: headless pygame and loaders for the extensionless scripts."""
import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path

# Must be set before pygame is imported anywhere.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame  # noqa: E402
import pytest  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# Initialise at import, so module-level checks (e.g. skipif) can use fonts.
pygame.init()
pygame.display.set_mode((1, 1))

PLUGINS = sorted(p.stem for p in (REPO / "plugins").glob("*.py") if not p.stem.startswith("_"))


def load_script(name, path):
    """Import a Python script that has no .py extension."""
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _seed():
    """Make the random-driven plugins repeatable from test to test."""
    import random
    random.seed(1234)


@pytest.fixture(scope="session", autouse=True)
def _pygame():
    yield
    pygame.quit()


@pytest.fixture(scope="session")
def runner():
    return load_script("x11saver", REPO / "x11saver")


@pytest.fixture(scope="session")
def capture_tool():
    return load_script("capture_tool", REPO / "tools" / "capture")


@pytest.fixture
def surface():
    """A drawing surface of a given size, like the screen a plugin gets."""
    def make(width=320, height=200):
        return pygame.Surface((width, height))
    return make
