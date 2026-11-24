"""Matrix-style falling characters."""
import random

import pygame

FONT_SIZE = 18
# Fonts that usually include katakana, tried in order. If none is installed,
# the plugin falls back to monospace with ASCII only, so no empty boxes appear.
KATAKANA_FONTS = ["notosansmonocjkjp", "notosanscjkjp", "droidsansfallback",
                  "takaogothic", "ipagothic", "vlgothic"]
KATAKANA = (0x30A2, 0x30FC)
ASCII = (33, 126)

_font = None
_ranges = None
_drops = None
_fade = None
_size = None


def _has_glyph(font, ch):
    """True if font really draws ch, not its 'missing glyph' box."""
    missing = font.render("\U0010FFFD", False, (255, 255, 255))   # no font has this
    test = font.render(ch, False, (255, 255, 255))
    return (test.get_size() != missing.get_size()
            or pygame.image.tobytes(test, "RGBA") != pygame.image.tobytes(missing, "RGBA"))


def _pick_font():
    for name in KATAKANA_FONTS:
        path = pygame.font.match_font(name)
        if path:
            font = pygame.font.Font(path, FONT_SIZE)
            font.set_bold(True)
            if _has_glyph(font, chr(KATAKANA[0])):
                return font, [ASCII, KATAKANA]
    return pygame.font.SysFont("monospace", FONT_SIZE, bold=True), [ASCII]


def init(screen, size):
    global _font, _ranges, _drops, _fade, _size
    _size = size
    _font, _ranges = _pick_font()
    _drops = [0] * (size[0] // FONT_SIZE)
    _fade = pygame.Surface(size)
    _fade.set_alpha(15)
    _fade.fill((0, 0, 0))


def render(screen, dt):
    width, height = _size
    screen.blit(_fade, (0, 0))

    for i in range(len(_drops)):
        char = chr(random.randint(*random.choice(_ranges)))
        text_surface = _font.render(char, True, (0, 255, 70))
        x, y = i * FONT_SIZE, _drops[i] * FONT_SIZE
        screen.blit(text_surface, (x, y))
        if y > height and random.random() > 0.975:
            _drops[i] = 0
        _drops[i] += 1


def shutdown():
    pass
