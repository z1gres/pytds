"""
moon_lord_fight.py  (rewritten)
================================
Файт с Мун Лордом — Tower Defence стиль.

Изменения:
  - Карта пустая (никакого пути, чистое поле)
  - Лоадаут: только башня "Scout" (лимит 4, место стоит 150 монет)
  - Мун Лорд НЕ стоит на месте — двигается по экрану
  - Мун Лорд иногда уничтожает башни
  - Рандомно во время боя падают монеты
  - Башни сами стреляют по боссу
  - Победа = убить все части Мун Лорда
"""

import pygame
import math
import random
import sys
import os

# ── Bootstrap imports ─────────────────────────────────────────────────────────
_HERE   = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_HERE, "assets")
if _ASSETS not in sys.path:
    sys.path.insert(0, _ASSETS)

from game_core import (
    SCREEN_W, SCREEN_H, FPS,
    C_WHITE, C_BLACK, C_RED, C_GREEN, C_GOLD,
    font_sm, font_md, font_lg,
    draw_rect_alpha, txt, dist,
    load_save, write_save,
)
import game_core

# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────
SCOUT_LIMIT      = 4
SCOUT_COST       = 150      # монет за размещение
SCOUT_DAMAGE_L0  = 1800     # урон за выстрел (lvl 0)
SCOUT_FIRERATE   = 1.4      # выстрелов в секунду
SCOUT_RANGE      = 340      # пикселей

# Стартовые монеты игрока
STARTING_MONEY   = 450

# Интервалы дропа монет (секунды)
MONEY_DROP_MIN   = 3.0
MONEY_DROP_MAX   = 7.0
MONEY_DROP_AMT   = (80, 200)   # мин-макс монет за дроп

# Скорость движения Мун Лорда
ML_SPEED_BASE    = 90          # пикселей/сек
ML_SPEED_ENRAGE  = 160         # ускоряется в фазе 3

# Шанс атаки башни каждый апдейт при проходе Мун Лорда рядом
TOWER_SMASH_RANGE = 160        # радиус уничтожения башни
TOWER_SMASH_CD    = 3.5        # секунд между попытками уничтожения

# ─────────────────────────────────────────────────────────────────────────────
#  Utility helpers
# ─────────────────────────────────────────────────────────────────────────────

def _lerp(a, b, t):
    return a + (b - a) * t


def _draw_hp_bar(surf, cx, y, w, h, hp, maxhp, col_fg,
                 col_bg=(20, 20, 20), label=""):
    ratio = max(0.0, hp / maxhp)
    bg_r = pygame.Rect(cx - w // 2, y, w, h)
    pygame.draw.rect(surf, col_bg, bg_r, border_radius=4)
    if ratio > 0:
        fg_r = pygame.Rect(cx - w // 2, y, int(w * ratio), h)
        pygame.draw.rect(surf, col_fg, fg_r, border_radius=4)
    pygame.draw.rect(surf, (200, 200, 200), bg_r, 1, border_radius=4)
    if label:
        lf = pygame.font.SysFont("segoeui", 13, bold=True)
        ls = lf.render(label, True, (255, 255, 255))
        surf.blit(ls, (cx - ls.get_width() // 2,
                       y + h // 2 - ls.get_height() // 2))


# ─────────────────────────────────────────────────────────────────────────────
#  Projectile classes
# ─────────────────────────────────────────────────────────────────────────────

class Bullet:
    """Пуля башни Scout."""
    def __init__(self, x, y, tx, ty, damage):
        self.x  = float(x)
        self.y  = float(y)
        spd     = 780
        d       = math.hypot(tx - x, ty - y) or 1
        self.vx = (tx - x) / d * spd
        self.vy = (ty - y) / d * spd
        self.damage  = damage
        self.alive   = True
        self.r       = 5
        self._t      = 0.0

    def update(self, dt):
        self._t += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if (self.x < -40 or self.x > SCREEN_W + 40 or
                self.y < -40 or self.y > SCREEN_H + 40 or
                self._t > 2.0):
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        glow = pygame.Surface((self.r * 4, self.r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 220, 255, 80),
                           (self.r * 2, self.r * 2), self.r * 2)
        surf.blit(glow, (int(self.x) - self.r * 2, int(self.y) - self.r * 2))
        pygame.draw.circle(surf, (160, 240, 255),
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (255, 255, 255),
                           (int(self.x), int(self.y)), self.r // 2 + 1)


class LaserBeam:
    """Лазер Мун Лорда."""
    def __init__(self, x1, y1, x2, y2,
                 color=(255, 50, 80), duration=0.22, width=4, damage=0):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color    = color
        self.duration = duration
        self._t       = 0.0
        self.alive    = True
        self.width    = width
        self.damage   = damage

    def update(self, dt):
        self._t += dt
        if self._t >= self.duration:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        alpha = int(255 * (1 - self._t / self.duration))
        w     = max(1, int(self.width * (1 - self._t / self.duration * 0.5)))
        try:
            glow_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.line(glow_s, (*self.color, alpha // 3),
                             (int(self.x1), int(self.y1)),
                             (int(self.x2), int(self.y2)), w + 8)
            surf.blit(glow_s, (0, 0))
        except Exception:
            pass
        pygame.draw.line(surf, self.color,
                         (int(self.x1), int(self.y1)),
                         (int(self.x2), int(self.y2)), w)


class PhantasmalSphere:
    """Орбитальный снаряд Мун Лорда."""
    def __init__(self, x, y, angle, speed=210):
        self.x    = float(x)
        self.y    = float(y)
        self.vx   = math.cos(angle) * speed
        self.vy   = math.sin(angle) * speed
        self.alive = True
        self.r     = 9
        self.damage = 0   # урон по башням не нужен
        self._t    = 0.0

    def update(self, dt):
        self._t += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if (self.x < -60 or self.x > SCREEN_W + 60 or
                self.y < -60 or self.y > SCREEN_H + 60):
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        glow_r = self.r + 5
        glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        alpha  = int(120 + 60 * math.sin(self._t * 8))
        pygame.draw.circle(glow, (120, 40, 220, alpha),
                           (glow_r, glow_r), glow_r)
        surf.blit(glow, (int(self.x) - glow_r, int(self.y) - glow_r))
        pygame.draw.circle(surf, (200, 100, 255),
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (255, 200, 255),
                           (int(self.x), int(self.y)), self.r // 2)


class CoinDrop:
    """Монета, падающая с экрана."""
    def __init__(self, x, y, amount):
        self.x       = float(x)
        self.y       = float(y)
        self.vy      = random.uniform(-60, -20)
        self.amount  = amount
        self._t      = 0.0
        self.alive   = True
        self.r       = 12
        self.collected = False

    def update(self, dt):
        self._t += dt
        self.vy += 120 * dt
        self.y  += self.vy * dt
        if self._t > 6.0 or self.y > SCREEN_H + 20:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        alpha = min(255, int(self._t * 500)) if self._t < 0.5 else 255
        s = pygame.Surface((self.r * 2 + 4, self.r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 210, 30, alpha),
                           (self.r + 2, self.r + 2), self.r)
        pygame.draw.circle(s, (255, 255, 100, alpha),
                           (self.r + 2, self.r + 2), self.r // 2)
        surf.blit(s, (int(self.x) - self.r - 2, int(self.y) - self.r - 2))
        lf = pygame.font.SysFont("segoeui", 11, bold=True)
        ls = lf.render(f"+{self.amount}", True, (255, 230, 60))
        surf.blit(ls, (int(self.x) - ls.get_width() // 2,
                       int(self.y) - self.r - 14))


# ─────────────────────────────────────────────────────────────────────────────
#  Scout Tower
# ─────────────────────────────────────────────────────────────────────────────

class ScoutTower:
    def __init__(self, x, y):
        self.x        = float(x)
        self.y        = float(y)
        self.damage   = SCOUT_DAMAGE_L0
        self.firerate = SCOUT_FIRERATE
        self.range    = SCOUT_RANGE
        self._fire_cd = 0.0
        self._t       = 0.0
        self.alive    = True
        self.r        = 18
        self._angle   = 0.0   # куда смотрит башня
        self._flash   = 0.0
        self._destroy_flash = 0.0

    def update(self, dt, boss_parts):
        """Возвращает список Bullet, которые надо добавить."""
        self._t      += dt
        self._fire_cd = max(0.0, self._fire_cd - dt)
        self._flash   = max(0.0, self._flash - dt)
        self._destroy_flash = max(0.0, self._destroy_flash - dt)
        bullets = []
        if not self.alive:
            return bullets

        # Ищем ближайшую живую часть босса в радиусе
        best_part = None
        best_d    = self.range + 1
        for part in boss_parts:
            if not part.alive:
                continue
            d = dist((self.x, self.y), (part.x, part.y))
            if d < best_d:
                best_d    = d
                best_part = part

        if best_part and self._fire_cd <= 0:
            self._angle   = math.atan2(best_part.y - self.y,
                                       best_part.x - self.x)
            self._fire_cd = 1.0 / self.firerate
            self._flash   = 0.12
            bullets.append(Bullet(self.x, self.y,
                                  best_part.x, best_part.y,
                                  self.damage))
        return bullets

    def draw(self, surf):
        if not self.alive:
            return
        # Shadow
        shad = pygame.Surface((self.r * 2 + 8, self.r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(shad, (0, 0, 0, 60),
                           (self.r + 4, self.r + 4), self.r + 4)
        surf.blit(shad, (int(self.x) - self.r - 4, int(self.y) - self.r - 4))

        # Base
        col = (220, 240, 255) if self._flash > 0 else (90, 140, 200)
        pygame.draw.circle(surf, (40, 55, 80),
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, col,
                           (int(self.x), int(self.y)), self.r, 3)

        # Gun barrel
        blen = self.r + 8
        ex = self.x + math.cos(self._angle) * blen
        ey = self.y + math.sin(self._angle) * blen
        pygame.draw.line(surf, (160, 200, 255),
                         (int(self.x), int(self.y)),
                         (int(ex), int(ey)), 4)

        # Range circle (faint)
        rang_s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(rang_s, (80, 140, 220, 18),
                           (self.range, self.range), self.range)
        pygame.draw.circle(rang_s, (80, 140, 220, 40),
                           (self.range, self.range), self.range, 1)
        surf.blit(rang_s, (int(self.x) - self.range, int(self.y) - self.range))

        # "S" label
        lf = pygame.font.SysFont("consolas", 13, bold=True)
        ls = lf.render("S", True, (200, 230, 255))
        surf.blit(ls, (int(self.x) - ls.get_width() // 2,
                       int(self.y) - ls.get_height() // 2))


# ─────────────────────────────────────────────────────────────────────────────
#  Boss parts
# ─────────────────────────────────────────────────────────────────────────────

class _BossPart:
    """Общий базовый класс для частей Мун Лорда."""
    MAXHP = 1

    def __init__(self):
        self.hp     = self.MAXHP
        self.alive  = True
        self._flash = 0.0
        self._t     = 0.0
        self.x      = 0.0
        self.y      = 0.0
        self.r      = 30

    def hurt(self, dmg):
        if not self.alive:
            return
        self.hp     = max(0, self.hp - dmg)
        self._flash = 0.12
        if self.hp <= 0:
            self.alive = False

    def update(self, dt):
        self._t     += dt
        self._flash  = max(0.0, self._flash - dt)


class MoonLordEye(_BossPart):
    MAXHP = 42_000

    def __init__(self, side):
        super().__init__()
        self.side   = side
        self.r      = 36
        self._laser_cd = random.uniform(1.0, 2.5)

    def try_fire_laser(self):
        if not self.alive or self._laser_cd > 0:
            return None
        self._laser_cd = random.uniform(2.5, 4.2)
        # Стреляет в случайном направлении вниз
        angle = random.uniform(math.pi * 0.3, math.pi * 0.7)
        length = 900
        ex = self.x + math.cos(angle) * length
        ey = self.y + math.sin(angle) * length
        col = (255, 70, 80) if self.side == "left" else (70, 140, 255)
        return LaserBeam(self.x, self.y, ex, ey,
                         color=col, damage=0, width=5)

    def update(self, dt):
        super().update(dt)
        self._laser_cd = max(0.0, self._laser_cd - dt)

    def draw(self, surf):
        glow_r = self.r + 10 + int(4 * math.sin(self._t * 3))
        gc     = (180, 50, 50) if self.side == "left" else (50, 100, 200)
        glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*gc, 60), (glow_r, glow_r), glow_r)
        surf.blit(glow, (int(self.x) - glow_r, int(self.y) - glow_r))

        col = (255, 255, 255) if self._flash > 0 else (220, 200, 200)
        pygame.draw.circle(surf, col,
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (20, 10, 10),
                           (int(self.x), int(self.y)), self.r, 3)
        if self.alive:
            pc = (200, 30, 30) if self.side == "left" else (30, 80, 200)
            pygame.draw.circle(surf, pc,
                               (int(self.x), int(self.y)), self.r // 2)
            pygame.draw.circle(surf, (10, 0, 0),
                               (int(self.x), int(self.y)), self.r // 5)
        else:
            d = self.r // 2
            cx, cy = int(self.x), int(self.y)
            pygame.draw.line(surf, (120, 0, 0),
                             (cx - d, cy - d), (cx + d, cy + d), 4)
            pygame.draw.line(surf, (120, 0, 0),
                             (cx + d, cy - d), (cx - d, cy + d), 4)

        _draw_hp_bar(surf, int(self.x), int(self.y) - self.r - 20,
                     90, 8, self.hp, self.MAXHP,
                     (200, 50, 50) if self.side == "left" else (50, 100, 200),
                     label=f"{'L' if self.side=='left' else 'R'} Eye")


class MoonLordForehead(_BossPart):
    MAXHP = 55_000

    def __init__(self):
        super().__init__()
        self.r       = 28
        self._active = False
        self._sphere_cd  = 0.0
        self._deathray_cd = 0.0
        self._deathray_active = False
        self._deathray_angle  = 0.0
        self._deathray_timer  = 0.0

    def activate(self):
        self._active = True

    def hurt(self, dmg):
        if not self._active:
            return
        super().hurt(dmg)

    def update(self, dt):
        super().update(dt)
        if not self._active:
            return
        self._sphere_cd   = max(0.0, self._sphere_cd - dt)
        self._deathray_cd = max(0.0, self._deathray_cd - dt)
        if self._deathray_active:
            self._deathray_timer -= dt
            self._deathray_angle += dt * 1.3
            if self._deathray_timer <= 0:
                self._deathray_active = False

    def try_fire_spheres(self):
        if not self.alive or not self._active or self._sphere_cd > 0:
            return []
        self._sphere_cd = random.uniform(1.6, 3.0)
        count   = random.randint(4, 7)
        spheres = []
        for i in range(count):
            angle = (2 * math.pi / count) * i + self._t
            spheres.append(PhantasmalSphere(self.x, self.y, angle,
                                            speed=random.uniform(170, 250)))
        return spheres

    def try_deathray(self):
        if not self.alive or not self._active or self._deathray_cd > 0:
            return None
        self._deathray_cd     = random.uniform(4.0, 6.5)
        self._deathray_active = True
        self._deathray_timer  = 1.5
        self._deathray_angle  = random.uniform(0, math.pi * 2)
        length = 700
        ex = self.x + math.cos(self._deathray_angle) * length
        ey = self.y + math.sin(self._deathray_angle) * length
        return LaserBeam(self.x, self.y, ex, ey,
                         color=(160, 255, 100),
                         duration=0.09, width=6, damage=0)

    def draw(self, surf):
        if not self._active:
            return
        glow_r = self.r + 8 + int(5 * math.sin(self._t * 4))
        glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 220, 50, 70),
                           (glow_r, glow_r), glow_r)
        surf.blit(glow, (int(self.x) - glow_r, int(self.y) - glow_r))

        col = (255, 255, 255) if self._flash > 0 else (180, 240, 150)
        pygame.draw.circle(surf, col,
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (20, 60, 10),
                           (int(self.x), int(self.y)), self.r, 3)

        if self.alive:
            pygame.draw.circle(surf, (50, 200, 50),
                               (int(self.x), int(self.y)), self.r // 2)
            pygame.draw.circle(surf, (10, 30, 5),
                               (int(self.x), int(self.y)), self.r // 5)
            if self._deathray_active:
                length = 600
                ex = self.x + math.cos(self._deathray_angle) * length
                ey = self.y + math.sin(self._deathray_angle) * length
                pygame.draw.line(surf, (180, 255, 120),
                                 (int(self.x), int(self.y)),
                                 (int(ex), int(ey)), 3)
        else:
            d = self.r // 2
            cx, cy = int(self.x), int(self.y)
            pygame.draw.line(surf, (0, 80, 0),
                             (cx - d, cy - d), (cx + d, cy + d), 3)
            pygame.draw.line(surf, (0, 80, 0),
                             (cx + d, cy - d), (cx - d, cy + d), 3)

        if self._active:
            _draw_hp_bar(surf, int(self.x), int(self.y) - self.r - 20,
                         100, 8, self.hp, self.MAXHP,
                         (60, 200, 60), label="True Eye")


class MoonLordCore(_BossPart):
    MAXHP = 85_000

    def __init__(self):
        super().__init__()
        self.r       = 30
        self._active = False
        self._flame_cd = 0.0

    def activate(self):
        self._active = True

    def hurt(self, dmg):
        if not self._active:
            return
        super().hurt(dmg)

    def update(self, dt):
        super().update(dt)
        if self._active:
            self._flame_cd = max(0.0, self._flame_cd - dt)

    def draw(self, surf):
        glow_r = self.r + 10 + int(6 * math.sin(self._t * 5))
        gc     = (220, 30, 30) if self._active else (60, 30, 30)
        glow   = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*gc, 80), (glow_r, glow_r), glow_r)
        surf.blit(glow, (int(self.x) - glow_r, int(self.y) - glow_r))

        col = (255, 255, 255) if self._flash > 0 else (
            (255, 80, 50) if self._active else (80, 40, 40)
        )
        pygame.draw.circle(surf, col,
                           (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (60, 10, 10),
                           (int(self.x), int(self.y)), self.r, 3)

        if self._active and self.alive:
            ir = int(self.r * 0.55 + 4 * math.sin(self._t * 7))
            pygame.draw.circle(surf, (200, 50, 20),
                               (int(self.x), int(self.y)), ir)
            pygame.draw.circle(surf, (255, 200, 50),
                               (int(self.x), int(self.y)), ir // 3)

        if self._active:
            _draw_hp_bar(surf, int(self.x), int(self.y) - self.r - 20,
                         110, 8, self.hp, self.MAXHP,
                         (220, 60, 20), label="Core")


# ─────────────────────────────────────────────────────────────────────────────
#  Moon Lord Boss container  (теперь двигается!)
# ─────────────────────────────────────────────────────────────────────────────

class MoonLordBoss:
    """
    Мун Лорд движется по экрану (зона верхних 55% экрана).
    Атакует башни на поле.
    Фазы:
      1: Eyes живы → лазеры из глаз
      2: Eyes мертвы → True Eye (сферы + deathray)
      3: True Eye мёртв → Core + emergency lasers
    """

    def __init__(self):
        self.left_eye  = MoonLordEye("left")
        self.right_eye = MoonLordEye("right")
        self.forehead  = MoonLordForehead()
        self.core      = MoonLordCore()
        self.alive     = True
        self._t        = 0.0
        self._phase    = 1
        self._shake    = 0.0

        # Движение
        self._bx  = float(SCREEN_W // 2)
        self._by  = float(180)
        # Случайная целевая точка
        self._tx, self._ty = self._new_target()
        self._speed = ML_SPEED_BASE

        # Уничтожение башен
        self._smash_cd   = TOWER_SMASH_CD
        self._smash_flash = 0.0   # визуальная вспышка при разрушении

        self._death_timer     = None
        self._explode_particles = []
        self._explosion_done  = False

        self._position_parts()

    def _new_target(self):
        margin = 250
        tx = random.uniform(margin, SCREEN_W - margin)
        ty = random.uniform(80, SCREEN_H * 0.52)
        return tx, ty

    def _position_parts(self):
        bx, by = self._bx, self._by
        self.left_eye.x  = bx - 200
        self.left_eye.y  = by - 20
        self.right_eye.x = bx + 200
        self.right_eye.y = by - 20
        self.forehead.x  = bx
        self.forehead.y  = by - 65
        self.core.x      = bx
        self.core.y      = by + 45

    def update(self, dt, towers):
        """Возвращает (lasers, spheres) для добавления в projectiles."""
        self._t += dt
        if self._shake > 0:
            self._shake = max(0.0, self._shake - dt * 8)
        self._smash_cd    = max(0.0, self._smash_cd - dt)
        self._smash_flash = max(0.0, self._smash_flash - dt)

        # ── Движение ──────────────────────────────────────────────────────────
        spd = ML_SPEED_ENRAGE if self._phase == 3 else self._speed
        dx  = self._tx - self._bx
        dy  = self._ty - self._by
        d   = math.hypot(dx, dy)
        if d < 15:
            self._tx, self._ty = self._new_target()
        else:
            self._bx += dx / d * spd * dt
            self._by += dy / d * spd * dt

        self._position_parts()

        # ── Апдейт частей ─────────────────────────────────────────────────────
        self.left_eye.update(dt)
        self.right_eye.update(dt)
        self.forehead.update(dt)
        self.core.update(dt)

        # ── Фазовые переходы ──────────────────────────────────────────────────
        if self._phase == 1:
            if not self.left_eye.alive and not self.right_eye.alive:
                self._phase = 2
                self.forehead.activate()
                self._shake = 1.5
        elif self._phase == 2:
            if not self.forehead.alive:
                self._phase = 3
                self.core.activate()
                self._shake = 2.0
        elif self._phase == 3:
            if not self.core.alive and self._death_timer is None:
                self._death_timer = 3.0
                self._shake = 3.0
                for _ in range(80):
                    self._explode_particles.append({
                        "x": self._bx + random.randint(-150, 150),
                        "y": self._by + random.randint(-80, 80),
                        "vx": random.uniform(-200, 200),
                        "vy": random.uniform(-200, 200),
                        "life": random.uniform(0.5, 2.0),
                        "maxlife": 2.0,
                        "col": random.choice([
                            (255, 200, 50), (255, 80, 30),
                            (200, 255, 100), (255, 255, 255)
                        ]),
                        "r": random.randint(4, 14),
                    })

        if self._death_timer is not None:
            self._death_timer -= dt
            self._shake = max(0.0, self._death_timer)
            for p in self._explode_particles:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 60 * dt
                p["life"] -= dt
            self._explode_particles = [p for p in self._explode_particles
                                       if p["life"] > 0]
            if self._death_timer <= 0:
                self.alive = False

        # ── Атаки ──────────────────────────────────────────────────────────────
        lasers  = []
        spheres = []
        if self._phase == 1:
            l = self.left_eye.try_fire_laser()
            if l: lasers.append(l)
            r = self.right_eye.try_fire_laser()
            if r: lasers.append(r)
        elif self._phase == 2:
            spheres += self.forehead.try_fire_spheres()
            dr = self.forehead.try_deathray()
            if dr: lasers.append(dr)
        elif self._phase == 3:
            # Emergency random laser
            if random.random() < 0.012:
                angle  = random.uniform(0, math.pi * 2)
                ex     = self.core.x + math.cos(angle) * 800
                ey     = self.core.y + math.sin(angle) * 800
                lasers.append(LaserBeam(self.core.x, self.core.y, ex, ey,
                                        color=(255, 80, 30), damage=0, width=5))

        # ── Уничтожение башни ─────────────────────────────────────────────────
        smashed = None
        if self._smash_cd <= 0:
            alive_towers = [tw for tw in towers if tw.alive]
            if alive_towers:
                # Берём башню в радиусе
                cands = [tw for tw in alive_towers
                         if dist((self._bx, self._by), (tw.x, tw.y))
                         < TOWER_SMASH_RANGE]
                if cands:
                    smashed = random.choice(cands)
                    smashed.alive = False
                    self._smash_cd    = TOWER_SMASH_CD * random.uniform(0.8, 1.4)
                    self._smash_flash = 0.4
                    self._shake       = 0.8
                else:
                    # Если нет рядом — иногда телепортируемся к ближайшей
                    if random.random() < 0.3:
                        target_tower = min(
                            alive_towers,
                            key=lambda tw: dist((self._bx, self._by), (tw.x, tw.y))
                        )
                        self._tx = target_tower.x + random.randint(-60, 60)
                        self._ty = max(80, target_tower.y - 120)
                    self._smash_cd = TOWER_SMASH_CD * 0.6

        return lasers, spheres, smashed

    def get_all_alive_parts(self):
        parts = []
        if self.left_eye.alive:  parts.append(self.left_eye)
        if self.right_eye.alive: parts.append(self.right_eye)
        if self.forehead._active and self.forehead.alive: parts.append(self.forehead)
        if self.core._active and self.core.alive: parts.append(self.core)
        return parts

    def get_shake_offset(self):
        if self._shake > 0.1:
            mag = int(self._shake * 6)
            return (random.randint(-mag, mag), random.randint(-mag, mag))
        return (0, 0)

    def draw(self, surf):
        self._draw_body(surf)
        self.left_eye.draw(surf)
        self.right_eye.draw(surf)
        self.forehead.draw(surf)
        self.core.draw(surf)

        for p in self._explode_particles:
            ratio = max(0.0, min(1.0, p["life"] / p["maxlife"]))
            alpha = int(255 * ratio)
            r     = max(1, int(p["r"] * ratio))
            s     = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["col"], alpha), (r, r), r)
            surf.blit(s, (int(p["x"]) - r, int(p["y"]) - r))

    def _draw_body(self, surf):
        bx, by = int(self._bx), int(self._by)
        head_w, head_h = 400, 180
        head_col = (25, 12, 35)
        if self._phase >= 3 and self.core.alive:
            pulse = abs(math.sin(self._t * 5))
            border_col = (int(100 + 120 * pulse), 20, int(40 + 60 * pulse))
        else:
            border_col = (100, 60, 160)

        pygame.draw.ellipse(
            surf, head_col,
            (bx - head_w // 2, by - head_h // 2, head_w, head_h)
        )
        pygame.draw.ellipse(
            surf, border_col,
            (bx - head_w // 2, by - head_h // 2, head_w, head_h), 3
        )

        # Tendrils
        for (x2, y2, col) in [
            (int(self.left_eye.x),  int(self.left_eye.y),  (80, 40, 120)),
            (int(self.right_eye.x), int(self.right_eye.y), (80, 40, 120)),
            (int(self.forehead.x),  int(self.forehead.y),  (60, 100, 60)),
        ]:
            ox = random.randint(-2, 2) if self._shake > 0 else 0
            pygame.draw.line(surf, col, (bx, by - 30), (x2 + ox, y2), 2)

        # Smash flash
        if self._smash_flash > 0:
            alpha = int(self._smash_flash / 0.4 * 180)
            fs = pygame.Surface((head_w + 40, head_h + 40), pygame.SRCALPHA)
            pygame.draw.ellipse(fs, (255, 80, 0, alpha),
                                (0, 0, head_w + 40, head_h + 40))
            surf.blit(fs, (bx - (head_w + 40) // 2, by - (head_h + 40) // 2))

        # Phase label
        ph_labels = {1: "PHASE I", 2: "PHASE II", 3: "PHASE III"}
        ph_col    = [(200, 120, 255), (100, 220, 80), (255, 80, 30)][self._phase - 1]
        pf  = pygame.font.SysFont("consolas", 13, bold=True)
        ps  = pf.render(ph_labels[self._phase], True, ph_col)
        surf.blit(ps, (bx - ps.get_width() // 2, by - 10))


# ─────────────────────────────────────────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────────────────────────────────────────

def _draw_hud(surf, boss, towers, money, selected, t,
              hovering_place, smash_notif):
    """Draw game HUD: boss bar, money, loadout slot, instructions."""
    # ── Top bar ───────────────────────────────────────────────────────────────
    draw_rect_alpha(surf, (5, 0, 15), (0, 0, SCREEN_W, 36), 210)

    # Boss name + aggregate HP bar
    total_max = (MoonLordEye.MAXHP * 2 +
                 MoonLordForehead.MAXHP + MoonLordCore.MAXHP)
    total_cur = (boss.left_eye.hp + boss.right_eye.hp +
                 boss.forehead.hp + boss.core.hp)
    rc = int(180 + 60 * math.sin(t * 2.0))
    nf = pygame.font.SysFont("consolas", 17, bold=True)
    ns = nf.render("MOON LORD", True, (rc, 60, 200))
    surf.blit(ns, (SCREEN_W // 2 - ns.get_width() // 2, 6))
    _draw_hp_bar(surf, SCREEN_W // 2, 24, 500, 6,
                 total_cur, total_max, (160, 40, 200), col_bg=(20, 5, 35))

    # ── Bottom panel ──────────────────────────────────────────────────────────
    panel_y = SCREEN_H - 90
    draw_rect_alpha(surf, (10, 12, 20), (0, panel_y, SCREEN_W, 90), 220)
    pygame.draw.line(surf, (60, 40, 100), (0, panel_y), (SCREEN_W, panel_y), 2)

    # Tower count
    alive_count = sum(1 for tw in towers if tw.alive)
    cf = pygame.font.SysFont("segoeui", 14, bold=True)
    cs = cf.render(f"Towers: {alive_count}/{SCOUT_LIMIT}", True, (160, 200, 255))
    surf.blit(cs, (10, panel_y + 8))

    # Money
    mf = pygame.font.SysFont("segoeui", 20, bold=True)
    ms = mf.render(f"$ {money}", True, (255, 215, 30))
    surf.blit(ms, (10, panel_y + 30))

    # ── Scout slot ────────────────────────────────────────────────────────────
    slot_x, slot_y, slot_w, slot_h = SCREEN_W // 2 - 45, panel_y + 8, 90, 74
    can_afford = money >= SCOUT_COST
    can_place  = alive_count < SCOUT_LIMIT and can_afford

    # Border colour based on state
    if selected:
        brd = (80, 200, 255)
    elif can_place:
        brd = (60, 120, 220)
    else:
        brd = (60, 50, 80)

    pygame.draw.rect(surf, (20, 25, 40), (slot_x, slot_y, slot_w, slot_h),
                     border_radius=8)
    pygame.draw.rect(surf, brd, (slot_x, slot_y, slot_w, slot_h),
                     2, border_radius=8)

    # Tower icon (mini circle + barrel)
    ic_x = slot_x + slot_w // 2
    ic_y = slot_y + 26
    ic_r = 14
    pygame.draw.circle(surf, (40, 55, 80), (ic_x, ic_y), ic_r)
    pygame.draw.circle(surf, (90, 140, 200), (ic_x, ic_y), ic_r, 2)
    pygame.draw.line(surf, (160, 200, 255),
                     (ic_x, ic_y), (ic_x + ic_r + 4, ic_y), 3)
    lf = pygame.font.SysFont("consolas", 10, bold=True)
    ll = lf.render("S", True, (200, 230, 255))
    surf.blit(ll, (ic_x - ll.get_width() // 2, ic_y - ll.get_height() // 2))

    # Name + cost
    nf2 = pygame.font.SysFont("segoeui", 12, bold=True)
    ns2 = nf2.render("Scout", True, (200, 220, 255))
    surf.blit(ns2, (slot_x + slot_w // 2 - ns2.get_width() // 2, slot_y + 44))
    cost_col = (255, 215, 30) if can_afford else (180, 80, 80)
    cs2 = nf2.render(f"${SCOUT_COST}", True, cost_col)
    surf.blit(cs2, (slot_x + slot_w // 2 - cs2.get_width() // 2, slot_y + 57))

    if not can_place and not selected:
        # Dim overlay
        dim = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 100))
        surf.blit(dim, (slot_x, slot_y))

    # ── Instructions ──────────────────────────────────────────────────────────
    hf = pygame.font.SysFont("segoeui", 12)
    if selected:
        hs = hf.render("Click on the field to place Scout  [RMB / ESC to cancel]",
                       True, (120, 200, 255))
    else:
        hs = hf.render("Click the Scout slot then click field to place  |  collect coins",
                       True, (90, 90, 130))
    surf.blit(hs, (SCREEN_W // 2 - hs.get_width() // 2, panel_y + 75))

    # ── Smash notification ────────────────────────────────────────────────────
    if smash_notif > 0:
        alpha = min(255, int(smash_notif * 600))
        sf2 = pygame.font.SysFont("consolas", 22, bold=True)
        ss2 = sf2.render("⚠ TOWER DESTROYED!", True, (255, 80, 40))
        ss2.set_alpha(alpha)
        surf.blit(ss2, (SCREEN_W // 2 - ss2.get_width() // 2, SCREEN_H // 2 - 60))

    # ── Hover placement preview cost ──────────────────────────────────────────
    if hovering_place:
        mx, my = pygame.mouse.get_pos()
        pf2 = pygame.font.SysFont("segoeui", 13, bold=True)
        ps2 = pf2.render(f"-${SCOUT_COST}", True, (255, 215, 30))
        surf.blit(ps2, (mx + 18, my - 18))


# ─────────────────────────────────────────────────────────────────────────────
#  Ghost preview for placement
# ─────────────────────────────────────────────────────────────────────────────

def _draw_ghost(surf, mx, my):
    r = ScoutTower.__new__(ScoutTower)
    r.x = mx; r.y = my; r.r = 18
    r._angle = 0.0; r._flash = 0.0; r.range = SCOUT_RANGE
    r.alive = True
    # Semi-transparent ghost
    ghost = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    pygame.draw.circle(ghost, (40, 55, 80, 120), (mx, my), r.r)
    pygame.draw.circle(ghost, (90, 140, 200, 160), (mx, my), r.r, 3)
    pygame.draw.circle(ghost, (80, 140, 220, 28), (mx, my), SCOUT_RANGE)
    pygame.draw.circle(ghost, (80, 140, 220, 70), (mx, my), SCOUT_RANGE, 1)
    surf.blit(ghost, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
#  Intro / End screens
# ─────────────────────────────────────────────────────────────────────────────

def _run_intro(screen):
    clock    = pygame.time.Clock()
    t        = 0.0
    duration = 5.0
    lines    = [
        (0.3, "You have proven yourself worthy..."),
        (1.8, "But the true test awaits."),
        (3.2, "THE MOON LORD DESCENDS."),
    ]
    while t < duration:
        dt = clock.tick(60) / 1000.0
        t += dt
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return

        screen.fill((2, 0, 8))
        random.seed(42)
        for _ in range(200):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H)
            sr = random.randint(1, 2)
            a  = int(100 + 120 * abs(math.sin(t * random.uniform(0.5, 2.0) + sx)))
            s2 = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(s2, (255, 255, 255, a), (sr, sr), sr)
            screen.blit(s2, (sx - sr, sy - sr))
        random.seed()

        moon_y = int(_lerp(-120, SCREEN_H // 2 - 40, min(1.0, t / 2.0)))
        pygame.draw.circle(screen, (200, 190, 160), (SCREEN_W // 2, moon_y), 80)
        pygame.draw.circle(screen, (160, 150, 120), (SCREEN_W // 2, moon_y), 80, 3)
        red_a = int(min(160, t * 30))
        rs    = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        rs.fill((180, 0, 0, red_a))
        screen.blit(rs, (0, 0))

        for show_t, line in lines:
            if t >= show_t:
                alpha = min(255, int((t - show_t) * 300))
                big   = (line == "THE MOON LORD DESCENDS.")
                fnt   = pygame.font.SysFont("consolas", 26 if big else 18, bold=big)
                col   = (255, 80, 80) if big else (220, 200, 255)
                ls    = fnt.render(line, True, col)
                ls.set_alpha(alpha)
                screen.blit(ls, (SCREEN_W // 2 - ls.get_width() // 2,
                                 SCREEN_H // 2 + 80 + (60 if big else 0)))

        sk = pygame.font.SysFont("segoeui", 12)
        ss = sk.render("ESC to skip", True, (60, 60, 80))
        screen.blit(ss, (SCREEN_W - ss.get_width() - 10, SCREEN_H - 22))
        pygame.display.flip()


def _run_end_screen(screen, victory):
    clock    = pygame.time.Clock()
    t        = 0.0
    btn_rect = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H // 2 + 80, 280, 55)
    while True:
        dt = clock.tick(60) / 1000.0
        t += dt
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_rect.collidepoint(ev.pos):
                    return

        screen.fill((2, 0, 8) if victory else (8, 0, 0))
        random.seed(99)
        for _ in range(150):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            sr = random.randint(1, 2)
            a  = int(100 + 100 * abs(math.sin(t * random.uniform(0.5, 2.5) + sx)))
            col = (200, 200, 255) if victory else (200, 80, 80)
            s2  = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(s2, (*col, a), (sr, sr), sr)
            screen.blit(s2, (sx - sr, sy - sr))
        random.seed()

        if victory:
            title, sub, t_col = ("MOON LORD DEFEATED!",
                                  "The celestial terror crumbles into stardust.",
                                  (220, 180, 255))
        else:
            title, sub, t_col = ("YOUR TOWERS FELL.",
                                  "The Moon Lord endures.",
                                  (255, 80, 60))

        tf = pygame.font.SysFont("consolas", 32, bold=True)
        ts = tf.render(title, True, t_col)
        screen.blit(ts, (SCREEN_W // 2 - ts.get_width() // 2,
                         SCREEN_H // 2 - 80 + int(4 * math.sin(t * 3))))
        sf2 = pygame.font.SysFont("segoeui", 18)
        ss  = sf2.render(sub, True, (180, 170, 200))
        screen.blit(ss, (SCREEN_W // 2 - ss.get_width() // 2,
                         SCREEN_H // 2 - 35))

        hov = btn_rect.collidepoint(mx, my)
        bcol = (60, 120, 200) if victory else (120, 40, 40)
        pygame.draw.rect(screen,
                         tuple(min(255, c + 30) for c in bcol) if hov else bcol,
                         btn_rect, border_radius=10)
        pygame.draw.rect(screen,
                         (200, 200, 255) if hov else (80, 80, 120),
                         btn_rect, 2, border_radius=10)
        bf = pygame.font.SysFont("segoeui", 20, bold=True)
        bs = bf.render("Return to Menu", True, (255, 255, 255))
        screen.blit(bs, (btn_rect.centerx - bs.get_width() // 2,
                         btn_rect.centery - bs.get_height() // 2))
        pygame.display.flip()


# ─────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_moon_lord_fight(screen, save_data):
    """
    Запускается из game.py после завершения Castbound-квестов.
    Возвращает 'menu' когда бой завершён.
    """
    _run_intro(screen)

    boss   = MoonLordBoss()
    towers : list[ScoutTower] = []
    bullets: list[Bullet]     = []
    projectiles               = []   # LaserBeam + PhantasmalSphere
    coins  : list[CoinDrop]   = []

    money   = STARTING_MONEY
    selected = False   # True = игрок выбрал слот и хочет разместить башню

    # Монеты дроп таймер
    money_drop_cd = random.uniform(MONEY_DROP_MIN, MONEY_DROP_MAX)

    # Уведомление об уничтожении башни
    smash_notif = 0.0

    # Background stars
    bg_stars = [
        (random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
         random.randint(1, 3), random.uniform(0.3, 2.0))
        for _ in range(180)
    ]

    t     = 0.0
    clock = pygame.time.Clock()

    PANEL_Y = SCREEN_H - 90   # Y начала нижней панели

    running = True
    while running:
        raw_dt = clock.tick(FPS) / 1000.0
        dt     = min(raw_dt, 0.05)
        t     += dt

        mx, my = pygame.mouse.get_pos()
        # Позиция выше панели — зона поля
        on_field     = my < PANEL_Y - 4
        hovering_place = selected and on_field

        # ── SLOT_RECT (кнопка выбора башни в нижней панели) ───────────────────
        slot_rect = pygame.Rect(SCREEN_W // 2 - 45, PANEL_Y + 8, 90, 74)

        # ── Events ────────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if selected:
                        selected = False
                    else:
                        running = False

            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:   # ПКМ — отмена
                    selected = False

                if ev.button == 1:
                    # Клик по слоту Scout
                    if slot_rect.collidepoint(ev.pos):
                        alive_count = sum(1 for tw in towers if tw.alive)
                        if alive_count < SCOUT_LIMIT and money >= SCOUT_COST:
                            selected = not selected
                    # Размещение башни на поле
                    elif selected and on_field:
                        alive_count = sum(1 for tw in towers if tw.alive)
                        if alive_count < SCOUT_LIMIT and money >= SCOUT_COST:
                            towers.append(ScoutTower(mx, my))
                            money   -= SCOUT_COST
                            selected = False
                    # Подбор монет
                    else:
                        for coin in coins:
                            if coin.alive and not coin.collected:
                                if dist((mx, my), (coin.x, coin.y)) < coin.r + 10:
                                    money += coin.amount
                                    coin.alive    = False
                                    coin.collected = True

        # ── Update boss ───────────────────────────────────────────────────────
        if boss.alive:
            new_lasers, new_spheres, smashed_tower = boss.update(dt, towers)
            projectiles += new_lasers + new_spheres
            if smashed_tower is not None:
                smash_notif = 0.4

        smash_notif = max(0.0, smash_notif - dt)

        # ── Update towers ─────────────────────────────────────────────────────
        all_parts = boss.get_all_alive_parts()
        for tw in towers:
            new_bullets = tw.update(dt, all_parts)
            bullets += new_bullets

        # ── Update bullets — проверяем попадание по боссу ────────────────────
        for b in bullets:
            b.update(dt)
            if not b.alive:
                continue
            for part in all_parts:
                if dist((b.x, b.y), (part.x, part.y)) < part.r + b.r:
                    part.hurt(b.damage)
                    b.alive = False
                    break

        bullets = [b for b in bullets if b.alive]

        # ── Update projectiles ────────────────────────────────────────────────
        for proj in projectiles:
            proj.update(dt)
        projectiles = [p for p in projectiles if p.alive]

        # ── Money drops ───────────────────────────────────────────────────────
        money_drop_cd -= dt
        if money_drop_cd <= 0:
            money_drop_cd = random.uniform(MONEY_DROP_MIN, MONEY_DROP_MAX)
            amt = random.randint(*MONEY_DROP_AMT)
            cx  = random.randint(80, SCREEN_W - 80)
            cy  = random.randint(int(SCREEN_H * 0.55), PANEL_Y - 40)
            coins.append(CoinDrop(cx, cy, amt))

        for coin in coins:
            coin.update(dt)
        coins = [c for c in coins if c.alive]

        # ── Win / Lose check ──────────────────────────────────────────────────
        if not boss.alive:
            save_data["castbound_quest"] = "done"
            write_save(save_data)
            _run_end_screen(screen, victory=True)
            return "menu"

        # Проигрыш — если башен больше нет И деньги не позволяют купить новую
        alive_count = sum(1 for tw in towers if tw.alive)
        if alive_count == 0 and money < SCOUT_COST and boss.alive:
            # Дожидаемся пока деньги не появятся или принимаем поражение
            # (только если уже прошло >10 сек и монет нет в воздухе)
            if not coins and t > 12.0:
                _run_end_screen(screen, victory=False)
                return "menu"

        # ── Draw ──────────────────────────────────────────────────────────────
        ox, oy = boss.get_shake_offset() if boss.alive else (0, 0)
        screen.fill((4, 0, 12))

        # Stars / nebula
        for sx, sy, sr, spd in bg_stars:
            a   = int(80 + 60 * abs(math.sin(t * spd + sx * 0.01)))
            col = ((80, 40, 120) if sr == 1 else
                   (160, 100, 200) if sr == 2 else (200, 200, 255))
            s2  = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(s2, (*col, a), (sr, sr), sr)
            screen.blit(s2, (sx - sr + ox, sy - sr + oy))

        # Draw towers
        for tw in towers:
            if tw.alive:
                tw.draw(screen)

        # Draw bullets
        for b in bullets:
            b.draw(screen)

        # Draw projectiles
        for proj in projectiles:
            proj.draw(screen)

        # Draw coins
        for coin in coins:
            coin.draw(screen)

        # Draw boss
        if boss.alive:
            boss.draw(screen)

        # Phase transition flash
        if boss.alive and boss._shake > 1.8:
            flash_a = int(min(120, boss._shake * 40))
            fs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fs.fill((200, 100, 255, flash_a))
            screen.blit(fs, (0, 0))

        # Ghost preview
        if hovering_place:
            _draw_ghost(screen, mx, my)

        # HUD
        _draw_hud(screen, boss, towers, money, selected, t,
                  hovering_place, smash_notif)

        pygame.display.flip()

    return "menu"