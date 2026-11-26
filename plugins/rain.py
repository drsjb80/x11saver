# SPDX-License-Identifier: MIT
# Copyright (c) 2026 drsjb80. See the license in x11saver.
"""Rain falling at a slant in shifting wind, with splashes on the ground."""
import math
import random

import pygame

FPS = 60
DENSITY = 1 / 3000          # drops per square pixel of screen
BACKGROUND = (8, 10, 18)
GRAVITY = 900               # px/s^2, for splash droplets
MAX_SPLASHES = 400

_drops = []
_splashes = []              # [x, y, vx, vy, life, max_life, color]
_size = None
_time = 0.0


class _Drop:
    __slots__ = ("x", "y", "depth", "speed", "length", "thickness", "color", "ground")

    def __init__(self, depth):
        self.depth = depth                      # 0 = far away, 1 = close
        self.speed = 450 + 600 * depth          # px/s
        self.length = 6 + 24 * depth
        self.thickness = 1 if depth < 0.75 else 2
        shade = 70 + 130 * depth
        self.color = (int(shade * 0.75), int(shade * 0.82), int(shade))

    def respawn(self, width, height, anywhere=False):
        # Far drops "land" higher up the screen, which reads as depth.
        self.ground = height * (0.78 + 0.2 * self.depth) + random.uniform(0, 0.02 * height)
        self.x = random.uniform(-0.25 * width, 1.25 * width)
        if anywhere:
            self.y = random.uniform(-height, self.ground)
        else:
            self.y = random.uniform(-0.3 * height, 0)


def init(screen, size):
    global _drops, _splashes, _size, _time
    _size = size
    _time = 0.0
    width, height = size
    count = int(width * height * DENSITY)
    # Sorted far-to-near so close drops are drawn on top.
    _drops = [_Drop(d) for d in sorted(random.random() for _ in range(count))]
    for drop in _drops:
        drop.respawn(width, height, anywhere=True)
    _splashes = []


def _splash(drop):
    if drop.depth < 0.35 or len(_splashes) >= MAX_SPLASHES:
        return
    for _ in range(random.randint(2, 4)):
        life = random.uniform(0.2, 0.45)
        _splashes.append([
            drop.x, drop.ground,
            random.uniform(-80, 80) * drop.depth,
            -random.uniform(80, 220) * drop.depth,
            life, life, drop.color,
        ])


def _fade(color, frac):
    return tuple(int(b + (c - b) * frac) for c, b in zip(color, BACKGROUND))


def render(screen, dt):
    global _time, _splashes
    _time += dt
    width, height = _size
    # Wind as a slope (horizontal px per vertical px), drifting slowly.
    wind = 0.22 * math.sin(_time * 0.11) + 0.08 * math.sin(_time * 0.43)

    screen.fill(BACKGROUND)

    for drop in _drops:
        drop.y += drop.speed * dt
        drop.x += drop.speed * wind * dt
        if drop.y >= drop.ground:
            _splash(drop)
            drop.respawn(width, height)
            continue
        tail = (drop.x - wind * drop.length, drop.y - drop.length)
        pygame.draw.line(screen, drop.color, tail, (drop.x, drop.y), drop.thickness)

    alive = []
    for s in _splashes:
        s[4] -= dt
        if s[4] <= 0:
            continue
        s[3] += GRAVITY * dt
        s[0] += s[2] * dt
        s[1] += s[3] * dt
        pygame.draw.circle(screen, _fade(s[6], s[4] / s[5]), (int(s[0]), int(s[1])), 1)
        alive.append(s)
    _splashes = alive


def shutdown():
    pass
