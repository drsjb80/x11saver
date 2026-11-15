"""Matrix-style falling characters."""
import random

import pygame

FONT_SIZE = 18

_font = None
_drops = None
_fade = None
_size = None


def init(screen, size):
    global _font, _drops, _fade, _size
    _size = size
    _font = pygame.font.SysFont("monospace", FONT_SIZE, bold=True)
    _drops = [0] * (size[0] // FONT_SIZE)
    _fade = pygame.Surface(size)
    _fade.set_alpha(15)
    _fade.fill((0, 0, 0))


def render(screen, dt):
    width, height = _size
    screen.blit(_fade, (0, 0))

    for i in range(len(_drops)):
        char = chr(random.randint(33, 126) if random.random() < 0.5
                   else random.randint(12450, 12540))
        text_surface = _font.render(char, True, (0, 255, 70))
        x, y = i * FONT_SIZE, _drops[i] * FONT_SIZE
        screen.blit(text_surface, (x, y))
        if y > height and random.random() > 0.975:
            _drops[i] = 0
        _drops[i] += 1


def shutdown():
    pass
