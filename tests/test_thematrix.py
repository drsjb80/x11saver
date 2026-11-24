"""thematrix: font selection never shows missing-glyph boxes."""
import pygame
import pytest

from plugins import thematrix


def test_has_glyph_detects_real_and_missing_glyphs():
    font = pygame.font.SysFont("monospace", 18)
    assert thematrix._has_glyph(font, "A")
    assert not thematrix._has_glyph(font, "\U0010FFFD")


def test_falls_back_to_ascii_without_a_katakana_font(monkeypatch, surface):
    monkeypatch.setattr(thematrix.pygame.font, "match_font", lambda name: None)
    thematrix.init(surface(), (320, 200))
    assert thematrix._ranges == [thematrix.ASCII]


def test_rejects_font_that_lacks_katakana(monkeypatch, surface):
    # A font that exists but can't draw katakana must not be used for it.
    monospace = pygame.font.match_font("monospace") or pygame.font.get_default_font()
    monkeypatch.setattr(thematrix.pygame.font, "match_font", lambda name: monospace)
    monkeypatch.setattr(thematrix, "_has_glyph", lambda font, ch: False)
    thematrix.init(surface(), (320, 200))
    assert thematrix._ranges == [thematrix.ASCII]


def _katakana_font_installed():
    for name in thematrix.KATAKANA_FONTS:
        path = pygame.font.match_font(name)
        if path and thematrix._has_glyph(pygame.font.Font(path, 18), "ア"):
            return True
    return False


@pytest.mark.skipif(not _katakana_font_installed(), reason="no katakana font installed")
def test_uses_katakana_when_a_font_supports_it(surface):
    thematrix.init(surface(), (320, 200))
    assert thematrix.KATAKANA in thematrix._ranges
