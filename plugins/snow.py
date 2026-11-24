"""Snow drifting down in a gentle wind and slowly piling up."""
import math
import random

import pygame

FPS = 60
DENSITY = 1 / 2500          # flakes per square pixel of screen
BACKGROUND = (6, 8, 20)
GROUND_COLOR = (215, 222, 235)
CELL = 4                    # horizontal resolution of the snow pile, in px
MAX_PILE = 0.12             # pile never grows past this fraction of the height
SLOPE = 0.5 * CELL          # steepest step between neighbouring pile cells

_flakes = []
_pile = []
_caps = []                  # per-column max height: rolling drift shape
_visible = 0                # number of pile columns actually on screen
_size = None
_time = 0.0
_sprites = {}


def _sprite(radius, shade):
    """A soft round flake: solid core with a faint glow around it (cached)."""
    key = (radius, shade)
    if key not in _sprites:
        color = (shade, shade, min(255, shade + 12))
        size = 4 * radius + 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        for r in range(2 * radius, radius, -1):         # glow, fading outward
            alpha = int(110 * (1 - (r - radius) / (radius + 1)))
            pygame.draw.circle(surf, (*color, alpha), (c, c), r)
        pygame.draw.circle(surf, (*color, 255), (c, c), radius)
        _sprites[key] = surf
    return _sprites[key]


class _Flake:
    __slots__ = ("x", "y", "depth", "radius", "speed", "sway", "freq", "phase",
                 "sprite", "offset")

    def __init__(self, depth):
        self.depth = depth                      # 0 = far away, 1 = close
        self.radius = 1 + int(4 * depth ** 2)
        self.speed = 35 + 95 * depth            # px/s
        self.sway = 8 + 30 * depth              # side-to-side amplitude, px
        self.freq = random.uniform(0.4, 1.2)    # sway cycles per second
        shade = 140 + 10 * int(11.5 * depth)    # quantised so sprites are shared
        self.sprite = _sprite(self.radius, shade)
        self.offset = self.sprite.get_width() // 2

    def respawn(self, width, height, anywhere=False):
        self.x = random.uniform(0, width)
        self.y = random.uniform(-height, height) if anywhere else random.uniform(-40, -5)
        self.phase = random.uniform(0, 2 * math.pi)


def init(screen, size):
    global _flakes, _pile, _caps, _visible, _size, _time
    _size = size
    _time = 0.0
    width, height = size
    count = int(width * height * DENSITY)
    # Sorted far-to-near so close flakes are drawn on top.
    _flakes = [_Flake(d) for d in sorted(random.random() for _ in range(count))]
    for flake in _flakes:
        flake.respawn(width, height, anywhere=True)
    _visible = (width - 1) // CELL + 1
    _pile = [0.0] * (_visible + 1)          # one extra column to reach the right edge
    # Two slow sine waves with random phases give rolling drifts when full.
    top = height * MAX_PILE
    a, b = random.uniform(0, 2 * math.pi), random.uniform(0, 2 * math.pi)
    _caps = [top * (0.55 + 0.45 * (0.5 + 0.3 * math.sin(i * 0.011 + a)
                                   + 0.2 * math.sin(i * 0.029 + b)))
             for i in range(len(_pile))]


def _land(col, amount):
    """Add snow at a pile column, spreading a little to the neighbours."""
    for offset, share in ((0, 0.5), (-1, 0.25), (1, 0.25)):
        i = col + offset
        if 0 <= i < _visible:
            _pile[i] = min(_caps[i], _pile[i] + amount * share)


def _settle():
    """Let steep steps in the pile slide down so it stays smooth."""
    for i in range(_visible - 1):
        diff = _pile[i] - _pile[i + 1]
        if abs(diff) > SLOPE:
            move = (abs(diff) - SLOPE) / 2
            if diff > 0:
                _pile[i] -= move
                _pile[i + 1] += move
            else:
                _pile[i] += move
                _pile[i + 1] -= move
    _pile[_visible] = _pile[_visible - 1]   # off-screen column mirrors the edge


def render(screen, dt):
    global _time
    _time += dt
    width, height = _size
    # Horizontal wind in px/s, drifting slowly.
    wind = 25 * math.sin(_time * 0.07) + 15 * math.sin(_time * 0.31)

    screen.fill(BACKGROUND)

    for flake in _flakes:
        flake.y += flake.speed * dt
        flake.phase += 2 * math.pi * flake.freq * dt
        flake.x = (flake.x + wind * (0.4 + 0.6 * flake.depth) * dt) % width
        x = (flake.x + flake.sway * math.sin(flake.phase)) % width

        col = min(_visible - 1, int(x // CELL))
        if flake.y >= height - _pile[col]:
            if flake.depth > 0.5:               # only near flakes add to the pile
                _land(col, flake.radius * 1.2)
            flake.respawn(width, height)
            continue
        screen.blit(flake.sprite, (int(x) - flake.offset, int(flake.y) - flake.offset))

    _settle()
    _settle()
    points = [(0, height)]
    points += [(i * CELL, height - h) for i, h in enumerate(_pile)]
    points += [(width, height)]
    pygame.draw.polygon(screen, GROUND_COLOR, points)


def shutdown():
    pass
