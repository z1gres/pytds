# ═══════════════════════════════════════════════════════════════════════════════
# infernal_enemies.py  —  Режим «INFERNAL» (Пекло)
#   34 основные волны + 10 волн Challenger (режим «БРАТСКАЯ МОГИЛА»)
#
#  Чтобы подключить:
#   1. В enemies.py в конец добавьте:  from infernal_enemies import *
#   2. В game.py добавьте кейс "play_infernal" → mode="infernal"
#   3. В Game.__init__ обработайте mode=="infernal":
#        self.wave_manager = WaveManager(INFERNAL_WAVE_DATA, INFERNAL_MAX_WAVES)
#        self.money = 750  (+100 к стандартному старту)
# ═══════════════════════════════════════════════════════════════════════════════

import pygame, math, random, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from game_core import (
    SCREEN_W, SCREEN_H, PATH_Y, PATH_H, TILE,
    C_WHITE, C_HP_BG, C_HP_FG, C_HP_FG2, C_GOLD,
    get_map_path, font_sm, font_md, txt, draw_rect_alpha, dist,
)

# Импортируем базовые классы из enemies.py (уже загружен к этому моменту)
from enemies import (
    Enemy, NormalBoss, WaveManager,
    FallenKing, TrueFallenKing,
    FallenRusher, FallenEnemy,
    Yeti,
)

# ──────────────────────────────────────────────────────────────────────────────
#  КОНСТАНТЫ СКОРОСТЕЙ
#  BASE_WOLF_SPEED = 55  (как у стандартного Enemy)
# ──────────────────────────────────────────────────────────────────────────────
_WOLF_SPD = 55      # базовая скорость волка / нормала


# ══════════════════════════════════════════════════════════════════════════════
#  БАЗОВЫЕ ВРАГИ РЕЖИМА
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Волк (Wolf) ────────────────────────────────────────────────────────────
class Wolf(Enemy):
    """30 HP, скорость как у Normal (55)."""
    DISPLAY_NAME = "Волк"; BASE_HP = 30; BASE_SPEED = _WOLF_SPD; KILL_REWARD = 15
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = self.BASE_HP; self.maxhp = self.hp
        self.speed = self.BASE_SPEED + (wave - 1) * 2
        self.radius = 16
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob) * 2; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (130, 120, 100), (cx, cy), self.radius)
        pygame.draw.circle(surf, (200, 190, 160), (cx - 4, cy - 4), 6)
        pygame.draw.circle(surf, (220, 210, 180), (cx, cy), self.radius, 2)
        # уши
        for dx2, dy2 in [(-8, -13), (2, -14)]:
            pygame.draw.polygon(surf, (110, 100, 80),
                [(cx+dx2, cy+dy2), (cx+dx2+5, cy+dy2+8), (cx+dx2-3, cy+dy2+8)])
        self._draw_hp_bar(surf, 28, 5)
        if hovered: self._hover_label(surf)


# ── 2. Спиди Волк (SpeedyWolf) ───────────────────────────────────────────────
class SpeedyWolf(Enemy):
    """15 HP, на 20% быстрее волка."""
    DISPLAY_NAME = "Спиди Волк"; BASE_HP = 15; BASE_SPEED = int(_WOLF_SPD * 1.20); KILL_REWARD = 12
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = self.BASE_HP; self.maxhp = self.hp
        self.speed = self.BASE_SPEED + (wave - 1) * 3
        self.radius = 13
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 1.8) * 3; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (80, 160, 220), (cx, cy), self.radius)
        pygame.draw.circle(surf, (140, 210, 255), (cx - 3, cy - 3), 5)
        pygame.draw.circle(surf, (180, 230, 255), (cx, cy), self.radius, 2)
        # скоростные линии
        for i in range(3):
            lx = cx - self.radius - 2 - i * 4
            pygame.draw.line(surf, (140, 210, 255), (lx, cy - 3 + i * 3), (lx - 6, cy - 3 + i * 3), 2)
        self._draw_hp_bar(surf, 22, 4)
        if hovered: self._hover_label(surf)


# ── 3. Снежок (Snowball) — при смерти оставляет SnowCorpse ───────────────────
class SnowCorpse(Enemy):
    """Корпс снеговика. 60 HP, стоит на месте — не идёт."""
    DISPLAY_NAME = "Снеговик (труп)"; BASE_HP = 60; BASE_SPEED = 0; KILL_REWARD = 5
    def __init__(self, wave=1, x=None, y=None, wp_index=None):
        super().__init__(wave)
        self.hp = self.BASE_HP; self.maxhp = self.hp
        self.speed = 0
        self.radius = 17
        if x is not None: self.x = x
        if y is not None: self.y = y
        if wp_index is not None: self._wp_index = wp_index
    def update(self, dt):
        # Стоит на месте, никуда не идёт, никогда не доходит до базы
        self._bob += dt * 2
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.5) * 1; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (220, 240, 255), (cx, cy), self.radius)
        pygame.draw.circle(surf, (180, 220, 250), (cx - 5, cy - 5), 7)
        pygame.draw.circle(surf, (200, 230, 255), (cx, cy), self.radius, 2)
        # кнопки
        for i in range(3):
            pygame.draw.circle(surf, (60, 60, 80), (cx, cy - 4 + i * 5), 2)
        self._draw_hp_bar(surf, 30, 5, (200, 230, 255))
        if hovered: self._hover_label(surf)

class Snowball(Enemy):
    """140 HP, скорость +10% к волку. При смерти спавнит SnowCorpse."""
    DISPLAY_NAME = "Снежок"; BASE_HP = 140; BASE_SPEED = int(_WOLF_SPD * 1.10); KILL_REWARD = 40
    _spawned_corpse = False
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = self.BASE_HP; self.maxhp = self.hp
        self.speed = self.BASE_SPEED + (wave - 1) * 2
        self.radius = 22; self._spawned_corpse = False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.8) * 2; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (200, 230, 255), (cx, cy), self.radius)
        pygame.draw.circle(surf, (240, 250, 255), (cx - 6, cy - 6), 9)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), self.radius, 2)
        # снежинки
        for a_deg in range(0, 360, 60):
            a = math.radians(a_deg)
            x2 = cx + int(math.cos(a) * (self.radius - 4))
            y2 = cy + int(math.sin(a) * (self.radius - 4))
            pygame.draw.circle(surf, (160, 200, 240), (x2, y2), 2)
        self._draw_hp_bar(surf, 36, 5, (200, 230, 255))
        if hovered: self._hover_label(surf)


# ── 4. Нормалы (Normal) — это стандартный Enemy из enemies.py ────────────────
#  В INFERNAL_WAVE_DATA используем Enemy напрямую.


# ── 5. Печка (Furnace) — минибосс, стан от пламени, оставляет угольки ────────
class Ember(Enemy):
    """Уголёк. 25 HP, скорость +10% к волку. Дебафф: снижает урон на 25%."""
    DISPLAY_NAME = "Уголёк"; BASE_HP = 25; BASE_SPEED = int(_WOLF_SPD * 1.10); KILL_REWARD = 8
    DEBUFF_DAMAGE_MULT = 0.75   # игровой код должен применять на юнита в радиусе

    def __init__(self, wave=1, x=None, y=None, wp_index=None):
        super().__init__(wave)
        self.hp = self.BASE_HP; self.maxhp = self.hp
        self.speed = self.BASE_SPEED
        self.radius = 11
        if x is not None: self.x = x
        if y is not None: self.y = y
        if wp_index is not None: self._wp_index = wp_index
        # таймер дебаффа
        self._debuff_timer = 0.0
        self.debuff_radius = 80      # пикселей
    def update(self, dt):
        self._debuff_timer = max(0.0, self._debuff_timer - dt)
        return super().update(dt)
    def tick_debuff(self):
        """Вернуть True каждые 2 секунды → применять дебафф к юнитам рядом."""
        if self._debuff_timer <= 0:
            self._debuff_timer = 2.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 2) * 2; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (60, 60, 60), (cx, cy), self.radius)
        pygame.draw.circle(surf, (120, 80, 20), (cx - 3, cy - 3), 4)
        pygame.draw.circle(surf, (160, 100, 20), (cx, cy), self.radius, 2)
        # маленькие искры
        for i in range(4):
            a = math.radians(i * 90 + self._bob * 30)
            px2 = cx + int(math.cos(a) * 8); py2 = cy + int(math.sin(a) * 8)
            pygame.draw.circle(surf, (255, 160, 20), (px2, py2), 2)
        self._draw_hp_bar(surf, 20, 4, (255, 160, 20))
        if hovered: self._hover_label(surf)


class Furnace(Enemy):
    """Печка — мини-босс. 350 HP. Стан пламенем. Оставляет 3 угольков."""
    DISPLAY_NAME = "Печка"; BASE_HP = 350; BASE_SPEED = int(_WOLF_SPD * 0.855); KILL_REWARD = 120
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = self.BASE_HP; self.maxhp = self.hp
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 28
        self._flame_timer = 4.0      # интервал станения
        self._spawned_embers = False
    def update(self, dt):
        self._flame_timer -= dt
        return super().update(dt)
    def should_stun(self):
        """Вернуть True → юниты в radius 100 оглушаются на 1.5 сек."""
        if self._flame_timer <= 0:
            self._flame_timer = 4.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.7) * 1.5; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(s, (220, 100, 20, 40), (55, 55), 52); surf.blit(s, (cx - 55, cy - 55))
        pygame.draw.circle(surf, (180, 80, 10), (cx, cy), self.radius + 4, 4)
        pygame.draw.circle(surf, (120, 50, 10), (cx, cy), self.radius)
        pygame.draw.circle(surf, (240, 160, 20), (cx - 7, cy - 7), 11)
        pygame.draw.circle(surf, (255, 200, 60), (cx, cy), self.radius, 2)
        # огонь
        t_flame = self._bob * 0.5
        for i in range(5):
            a = math.radians(i * 72 + t_flame * 20)
            fx = cx + int(math.cos(a) * (self.radius + 6))
            fy = cy + int(math.sin(a) * (self.radius + 6))
            pygame.draw.circle(surf, (255, 80 + i * 20, 0), (fx, fy), 4)
        self._draw_hp_bar(surf, 52, 7, (255, 160, 20))
        if hovered: self._hover_label(surf)


# ── 6. Untouchable — убить могут только Ковбой, Гладиатор, Арчер ─────────────
class Untouchable(Enemy):
    """
    1 HP, скорость как у волка. Убивается только Cowboy/Gladiator/Archer.
    Если дойдёт до базы — поражение.
    Флаг IMMUNE_UNITS_ONLY = True → game.py должен проверять тип атакующего.
    """
    DISPLAY_NAME = "Неприкасаемый"; BASE_HP = 1; BASE_SPEED = _WOLF_SPD; KILL_REWARD = 80
    IMMUNE_UNITS_ONLY = True  # маркер для game.py
    ALLOWED_KILLERS = {"GoldenCowboy", "Gladiator", "Archer"}

    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 1; self.maxhp = 1
        self.speed = self.BASE_SPEED
        self.radius = 18
    def take_damage_from(self, dmg, attacker_class_name):
        if attacker_class_name in self.ALLOWED_KILLERS:
            self.take_damage(dmg)
        # иначе урон не принимается
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob) * 2; cx, cy = int(self.x), int(self.y + bob)
        # переливающаяся граница
        pulse = int(abs(math.sin(self._bob * 0.8)) * 80 + 120)
        pygame.draw.circle(surf, (pulse, 0, pulse), (cx, cy), self.radius + 3, 3)
        pygame.draw.circle(surf, (60, 0, 60), (cx, cy), self.radius)
        pygame.draw.circle(surf, (180, 60, 180), (cx - 5, cy - 5), 7)
        # череп-метка
        pygame.draw.circle(surf, (230, 230, 230), (cx, cy - 2), 8, 2)
        pygame.draw.line(surf, (230, 230, 230), (cx - 4, cy + 5), (cx + 4, cy + 5), 2)
        self._draw_hp_bar(surf, 30, 5, (200, 0, 200))
        if hovered: self._hover_label(surf)


# ── 6b. ??? (SpecterEnemy) — убивают только Cowboy/Gladiator/Archer, 1 HP, game over если дойдёт ─
class SpecterEnemy(Enemy):
    """
    ??? — загадочный враг без имени.
    1 HP, убивается ТОЛЬКО Cowboy (GoldenCowboy), Gladiator, Archer.
    Любой другой урон полностью блокируется.
    Если дойдёт до базы — немедленное поражение (независимо от HP).
    """
    DISPLAY_NAME = "???"; BASE_HP = 1; BASE_SPEED = _WOLF_SPD; KILL_REWARD = 200
    IMMUNE_UNITS_ONLY = True   # маркер: game.py и units.py используют take_damage_from
    ALLOWED_KILLERS = {"GoldenCowboy", "Gladiator", "Archer"}
    INSTANT_DEFEAT = True      # маркер: game.py устанавливает game_over если дойдёт

    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 1; self.maxhp = 1
        self.speed = self.BASE_SPEED
        self.radius = 20

    # Блокируем весь входящий урон — разрешённые юниты используют take_damage_from
    def take_damage(self, amount, *args, **kwargs):
        pass  # иммунитет ко всем обычным атакам

    def take_damage_from(self, dmg, attacker_class_name):
        """Вызывается из units.py для Cowboy/Gladiator/Archer."""
        if attacker_class_name in self.ALLOWED_KILLERS:
            self.hp -= dmg
            if self.hp <= 0:
                self.hp = 0
                self.alive = False

    def draw(self, surf, hovered=False, detected=False):
        import math as _math
        bob = _math.sin(self._bob * 1.1) * 2
        cx, cy = int(self.x), int(self.y + bob)
        t_val = self._bob

        # Внешнее мерцающее кольцо — чёрно-фиолетовое
        pulse = int(abs(_math.sin(t_val * 1.2)) * 60 + 60)
        glow_s = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (pulse // 2, 0, pulse, 80), (45, 45), 44)
        surf.blit(glow_s, (cx - 45, cy - 45))

        # Тело — тёмно-фиолетовое, почти чёрное
        pygame.draw.circle(surf, (20, 0, 30), (cx, cy), self.radius + 2, 3)
        pygame.draw.circle(surf, (10, 0, 18), (cx, cy), self.radius)

        # Внутренний блеск
        inner_bright = int(abs(_math.sin(t_val * 0.7)) * 60 + 30)
        pygame.draw.circle(surf, (inner_bright, 0, inner_bright * 2), (cx - 4, cy - 4), 7)

        # Вращающиеся символы "?" вокруг
        for i in range(3):
            a = _math.radians(t_val * 80 + i * 120)
            qx = cx + int(_math.cos(a) * (self.radius + 8))
            qy = cy + int(_math.sin(a) * (self.radius + 8))
            qf = pygame.font.SysFont("consolas", 11, bold=True)
            ql = qf.render("?", True, (180, 0, 220))
            surf.blit(ql, ql.get_rect(center=(qx, qy)))

        # Надпись "???" в центре
        nf = pygame.font.SysFont("consolas", 12, bold=True)
        nl = nf.render("???", True, (200, 100, 255))
        surf.blit(nl, nl.get_rect(center=(cx, cy)))

        self._draw_hp_bar(surf, 32, 5, (150, 0, 200))
        if hovered: self._hover_label(surf)


# ── 7. Коллектор судьбы (FateCollector) — при убийстве −100$, если дойдёт +500$ ─
class FateCollector(Enemy):
    """
    Нормальная скорость.
    KILL_REWARD = -100 (игрок ТЕРЯЕТ деньги при убийстве).
    При достижении базы: +500$. Обрабатывается в game.py через флаги.
    """
    DISPLAY_NAME = "Коллектор Судьбы"; BASE_HP = 80; BASE_SPEED = _WOLF_SPD; KILL_REWARD = -100
    REACH_BONUS = 500  # бонус если дойдёт

    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 80; self.maxhp = 80
        self.speed = self.BASE_SPEED
        self.radius = 19
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.9) * 2; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 160, 20, 50), (40, 40), 38); surf.blit(s, (cx - 40, cy - 40))
        pygame.draw.circle(surf, (160, 120, 10), (cx, cy), self.radius + 2, 3)
        pygame.draw.circle(surf, (100, 70, 0), (cx, cy), self.radius)
        pygame.draw.circle(surf, (230, 200, 60), (cx - 5, cy - 5), 8)
        # знак $
        sf = pygame.font.SysFont("segoeui", 14, bold=True)
        sl = sf.render("$", True, (255, 220, 60))
        surf.blit(sl, sl.get_rect(center=(cx + 2, cy + 4)))
        self._draw_hp_bar(surf, 32, 5, (230, 200, 60))
        if hovered: self._hover_label(surf)


# ── 8. Топот (Stomp) — оглушает БЛИЖНИХ юнитов своим топотом ─────────────────
class Stomp(Enemy):
    """150 HP, дефолт скорость. Периодически оглушает ближайших юнитов (радиус 90)."""
    DISPLAY_NAME = "Топот"; BASE_HP = 150; BASE_SPEED = _WOLF_SPD; KILL_REWARD = 60
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 150; self.maxhp = 150
        self.speed = self.BASE_SPEED + (wave - 1) * 2
        self.radius = 24
        self._stomp_timer = 3.5
        self.stomp_radius = 90       # px, только ближние
    def update(self, dt):
        self._stomp_timer -= dt
        return super().update(dt)
    def should_stomp(self):
        if self._stomp_timer <= 0:
            self._stomp_timer = 3.5; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.7) * 2; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(s, (80, 50, 20, 50), (50, 50), 48); surf.blit(s, (cx - 50, cy - 50))
        pygame.draw.circle(surf, (100, 60, 20), (cx, cy), self.radius + 3, 4)
        pygame.draw.circle(surf, (70, 40, 10), (cx, cy), self.radius)
        pygame.draw.circle(surf, (180, 130, 60), (cx - 6, cy - 6), 9)
        pygame.draw.circle(surf, (200, 150, 80), (cx, cy), self.radius, 2)
        # трещины
        for i in range(4):
            a = math.radians(i * 90 + 45)
            x1 = cx + int(math.cos(a) * 6); y1 = cy + int(math.sin(a) * 6)
            x2 = cx + int(math.cos(a) * self.radius); y2 = cy + int(math.sin(a) * self.radius)
            pygame.draw.line(surf, (50, 30, 5), (x1, y1), (x2, y2), 2)
        self._draw_hp_bar(surf, 38, 6, (200, 150, 80))
        if hovered: self._hover_label(surf)


# ── 11. Мистери (InfernalMystery) — быстрый, случайный дроп ─────────────────
class InfernalStone(Enemy):
    """Камень. 1300 HP, медленный."""
    DISPLAY_NAME = "Камень"; BASE_HP = 1300; BASE_SPEED = 28; KILL_REWARD = 200
    def __init__(self, wave=1, x=None, y=None, wp_index=None):
        super().__init__(wave)
        self.hp = 1300; self.maxhp = 1300
        self.speed = self.BASE_SPEED
        self.radius = 30
        if x is not None: self.x = x
        if y is not None: self.y = y
        if wp_index is not None: self._wp_index = wp_index
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.4) * 1; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 100, 90, 40), (60, 60), 58); surf.blit(s, (cx - 60, cy - 60))
        pygame.draw.circle(surf, (90, 90, 80), (cx, cy), self.radius + 4, 5)
        pygame.draw.circle(surf, (60, 60, 55), (cx, cy), self.radius)
        pygame.draw.circle(surf, (140, 140, 130), (cx - 8, cy - 8), 12)
        pygame.draw.circle(surf, (160, 160, 150), (cx, cy), self.radius, 2)
        self._draw_hp_bar(surf, 55, 7, (160, 160, 150))
        if hovered: self._hover_label(surf)


class InfernalMystery(Enemy):
    """
    50 HP, высокая скорость (130).
    При смерти: 0.1% → FallenKing, 50% → InfernalStone, 49.9% → 8 Furnace.
    Логика дропа реализуется в game.py через метод get_mystery_drop().
    """
    DISPLAY_NAME = "Мистери"; BASE_HP = 50; BASE_SPEED = 130; KILL_REWARD = 30

    DROP_FALLEN_KING_CHANCE = 0.001   # 0.1%
    DROP_STONE_CHANCE       = 0.500   # 50%
    # остальные 49.9% → 8 Furnace

    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 50; self.maxhp = 50
        self.speed = self.BASE_SPEED + (wave - 1) * 3
        self.radius = 15; self._rot = 0.0
    def update(self, dt):
        self._rot += dt * 120; return super().update(dt)

    def get_mystery_drop(self):
        """Вызывается из game.py когда этот враг умирает. Возвращает список врагов."""
        r = random.random()
        if r < self.DROP_FALLEN_KING_CHANCE:
            from enemies import FallenKing
            fk = FallenKing(1); fk.x = self.x; fk.y = self.y
            fk._wp_index = self._wp_index; return [fk]
        elif r < self.DROP_FALLEN_KING_CHANCE + self.DROP_STONE_CHANCE:
            st = InfernalStone(1, self.x, self.y, self._wp_index); return [st]
        else:
            spawns = []
            for _ in range(8):
                f = Furnace(1); f.x = self.x; f.y = self.y
                f._wp_index = self._wp_index; spawns.append(f)
            return spawns

    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 1.4) * 3; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 200, 60, 50), (30, 30), 28); surf.blit(s, (cx - 30, cy - 30))
        pygame.draw.circle(surf, (180, 160, 20), (cx, cy), self.radius + 2, 2)
        pygame.draw.circle(surf, (120, 100, 10), (cx, cy), self.radius)
        pygame.draw.circle(surf, (240, 220, 60), (cx - 4, cy - 4), 6)
        # знак вопроса
        qf = pygame.font.SysFont("segoeui", 14, bold=True)
        ql = qf.render("?", True, (255, 240, 80))
        surf.blit(ql, ql.get_rect(center=(cx + 1, cy + 2)))
        self._draw_hp_bar(surf, 26, 4, (240, 220, 60))
        if hovered: self._hover_label(surf)


# ── 12. Терпила (Terpila) — мини-босс 2, 2000 HP, ярость при 1500 HP ─────────
class Terpila(Enemy):
    """
    1500 HP, скорость в 2 раза ниже волка.
    Когда HP ≤ 750 → RAGE:
      каждые 3 сек оглушает 1 случайного юнита до своей смерти.
    """
    DISPLAY_NAME = "Терпила"; BASE_HP = 1500; BASE_SPEED = int(_WOLF_SPD * 0.50); KILL_REWARD = 500
    RAGE_HP_THRESHOLD = 750
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 1500; self.maxhp = 1500
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 32; self._rage = False
        self._rage_timer = 3.0
    def update(self, dt):
        if self.hp <= self.RAGE_HP_THRESHOLD: self._rage = True
        if self._rage: self._rage_timer -= dt
        return super().update(dt)
    def should_rage_stun(self):
        """Вернуть True каждые 3 сек в ярости → оглушить 1 юнита."""
        if self._rage and self._rage_timer <= 0:
            self._rage_timer = 3.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.6) * 1.5; cx, cy = int(self.x), int(self.y + bob)
        col = (200, 40, 20) if self._rage else (100, 60, 200)
        border_col = (255, 80, 30) if self._rage else (160, 100, 255)
        s = pygame.Surface((128, 128), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col[:3], 40), (64, 64), 60); surf.blit(s, (cx - 64, cy - 64))
        pygame.draw.circle(surf, col, (cx, cy), self.radius + 4, 5)
        pygame.draw.circle(surf, tuple(max(0, c - 40) for c in col), (cx, cy), self.radius)
        pygame.draw.circle(surf, border_col, (cx - 8, cy - 8), 12)
        pygame.draw.circle(surf, border_col, (cx, cy), self.radius, 3)
        if self._rage:
            # пульсирующие линии ярости
            for i in range(6):
                a = math.radians(i * 60 + self._bob * 30)
                rx = cx + int(math.cos(a) * (self.radius + 8))
                ry = cy + int(math.sin(a) * (self.radius + 8))
                pygame.draw.circle(surf, (255, 100, 20), (rx, ry), 4)
        self._draw_hp_bar(surf, 58, 8, border_col)
        if hovered: self._hover_label(surf)


# ── 13. Путана (Putana) — 5000 HP, нужен 1000$ чтобы убить кликом ─────────────
class Putana(Enemy):
    """
    5 000 HP. Скорость ~62% к волку (в 2 раза медленнее чем раньше).
    Заплати BUYOUT_COST=$1000 → instant_kill() (клик по врагу в game.py).
    Обычный урон тоже работает.
    """
    DISPLAY_NAME = "Шлюха"; BASE_HP = 5000; BASE_SPEED = int(_WOLF_SPD * 0.625); KILL_REWARD = 0
    BUYOUT_COST = 1000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 5000; self.maxhp = 5000
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 22
        self._buyout_available = True   # маркер для game.py: показывать кнопку откупа
    def instant_kill(self):
        """Вызов из game.py при оплате BUYOUT_COST."""
        self.hp = 0; self.alive = False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob) * 2; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((88, 88), pygame.SRCALPHA)
        pygame.draw.circle(s, (220, 60, 120, 50), (44, 44), 42); surf.blit(s, (cx - 44, cy - 44))
        pygame.draw.circle(surf, (200, 40, 100), (cx, cy), self.radius + 3, 3)
        pygame.draw.circle(surf, (160, 20, 80), (cx, cy), self.radius)
        pygame.draw.circle(surf, (255, 120, 180), (cx - 5, cy - 5), 8)
        pygame.draw.circle(surf, (255, 160, 200), (cx, cy), self.radius, 2)
        # знак $$
        mf = pygame.font.SysFont("segoeui", 12, bold=True)
        ml = mf.render("$$", True, (255, 220, 230))
        surf.blit(ml, ml.get_rect(center=(cx + 1, cy + 4)))
        self._draw_hp_bar(surf, 38, 5, (255, 160, 200))
        if hovered: self._hover_label(surf)


# ── 19. Силач (Silyach/Cigarette) — 2000 HP, дебафф -75% урона ─────────────
class Silyach(Enemy):
    """
    Сигарета. 2000 HP, скорость на 30% НИЖЕ волка.
    Каждые 5 сек — дебафф случайному юниту: урон ×0.25 на 8 сек.
    """
    DISPLAY_NAME = "Сигарета"; BASE_HP = 2000; BASE_SPEED = int(_WOLF_SPD * 0.70); KILL_REWARD = 800
    DEBUFF_DAMAGE_MULT = 0.25
    DEBUFF_DURATION    = 15.0
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 2000; self.maxhp = 2000
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 26; self._debuff_timer = 5.0
    def update(self, dt):
        self._debuff_timer -= dt
        return super().update(dt)
    def should_debuff(self):
        if self._debuff_timer <= 0:
            self._debuff_timer = 5.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.7) * 1.5; cx, cy = int(self.x), int(self.y + bob)
        # туловище-сигарета (прямоугольник + круги)
        pygame.draw.rect(surf, (240, 230, 210), (cx - 8, cy - self.radius, 16, self.radius * 2), border_radius=4)
        pygame.draw.rect(surf, (200, 80, 60), (cx - 8, cy + self.radius - 12, 16, 12), border_radius=3)
        pygame.draw.circle(surf, (220, 200, 180), (cx, cy), self.radius, 2)
        # дым
        for i in range(3):
            sa = int(abs(math.sin(self._bob * 0.5 + i)) * 30 + 60)
            pygame.draw.circle(surf, (sa, sa, sa),
                (cx - 6 + i * 6, cy - self.radius - 6 - i * 5), 4 - i)
        self._draw_hp_bar(surf, 46, 7, (220, 200, 180))
        if hovered: self._hover_label(surf)


# ── 20. Конфузионале (Confusilionale) — 5000 HP, заставляет юнита бить другого ─
class Confusilionale(Enemy):
    """
    4200 HP, скорость на 40% НИЖЕ волка.
    Каждые 6 сек: оглушает 1 случайного юнита на 2.5 сек.
    """
    DISPLAY_NAME = "Конфузионале"; BASE_HP = 4200; BASE_SPEED = int(_WOLF_SPD * 0.60); KILL_REWARD = 600
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 4200; self.maxhp = 4200
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 24; self._confuse_timer = 6.0
    def update(self, dt):
        self._confuse_timer -= dt
        return super().update(dt)
    def should_confuse(self):
        if self._confuse_timer <= 0:
            self._confuse_timer = 6.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob) * 2; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(s, (80, 200, 160, 50), (50, 50), 48); surf.blit(s, (cx - 50, cy - 50))
        pygame.draw.circle(surf, (60, 180, 140), (cx, cy), self.radius + 3, 3)
        pygame.draw.circle(surf, (30, 120, 100), (cx, cy), self.radius)
        pygame.draw.circle(surf, (120, 240, 200), (cx - 6, cy - 6), 9)
        pygame.draw.circle(surf, (160, 255, 220), (cx, cy), self.radius, 2)
        # спирали
        for i in range(3):
            a = math.radians(i * 120 + self._bob * 40)
            sx2 = cx + int(math.cos(a) * (self.radius - 4))
            sy2 = cy + int(math.sin(a) * (self.radius - 4))
            pygame.draw.circle(surf, (200, 255, 230), (sx2, sy2), 3)
        self._draw_hp_bar(surf, 44, 6, (160, 255, 220))
        if hovered: self._hover_label(surf)


# ── 22. Инвалид (Wheelchair) — 12000 HP, едет на инвалидной коляске ──────────
class Wheelchair(Enemy):
    """
    12 000 HP, скорость дефолт.
    Мини-финальный босс (не главный и не мини-босс,
    это просто «особый босс» с промежуточным значением).
    """
    DISPLAY_NAME = "Инвалид"; BASE_HP = 1500; BASE_SPEED = int(_WOLF_SPD * 0.90); KILL_REWARD = 1000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 1500; self.maxhp = 1500
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 30; self._rot = 0.0
    def update(self, dt):
        self._rot += dt * 180; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.5) * 1; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(s, (60, 120, 200, 40), (60, 60), 58); surf.blit(s, (cx - 60, cy - 60))
        # колёса коляски
        for dx2 in [-14, 14]:
            pygame.draw.circle(surf, (50, 50, 60), (cx + dx2, cy + 8), 10)
            pygame.draw.circle(surf, (120, 120, 140), (cx + dx2, cy + 8), 10, 2)
            a_w = math.radians(self._rot)
            for wi in range(4):
                wa = a_w + math.radians(wi * 90)
                wx2 = cx + dx2 + int(math.cos(wa) * 6)
                wy2 = cy + 8 + int(math.sin(wa) * 6)
                pygame.draw.line(surf, (100, 100, 120),
                    (cx + dx2, cy + 8), (wx2, wy2), 1)
        # тело
        pygame.draw.circle(surf, (70, 100, 180), (cx, cy - 4), self.radius - 8)
        pygame.draw.circle(surf, (120, 160, 240), (cx - 5, cy - 10), 8)
        pygame.draw.circle(surf, (160, 200, 255), (cx, cy - 4), self.radius - 8, 2)
        self._draw_hp_bar(surf, 55, 8, (160, 200, 255))
        if hovered: self._hover_label(surf)


# ── 23. Чёрный квадрат (BlackSquare) — 4000 HP, 20% Армор, скорость -20% ─────
class BlackSquare(Enemy):
    """4000 HP, ARMOR=0.20, скорость на 20% ниже волка."""
    DISPLAY_NAME = "Чёрный Квадрат"; BASE_HP = 4000; BASE_SPEED = int(_WOLF_SPD * 0.80)
    ARMOR = 0.20; KILL_REWARD = 400
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 4000; self.maxhp = 4000
        self.speed = self.BASE_SPEED + (wave - 1)
        self.radius = 26; self._rot = 0.0
    def update(self, dt):
        self._rot += dt * 25; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.6) * 1; cx, cy = int(self.x), int(self.y + bob)
        # вращающийся квадрат (малевич approved)
        r = self.radius
        a = math.radians(self._rot)
        pts = []
        for corner in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            dx2 = corner[0] * r * math.cos(a) - corner[1] * r * math.sin(a)
            dy2 = corner[0] * r * math.sin(a) + corner[1] * r * math.cos(a)
            pts.append((int(cx + dx2), int(cy + dy2 + bob)))
        pygame.draw.polygon(surf, (10, 10, 10), pts)
        pygame.draw.polygon(surf, (80, 80, 80), pts, 3)
        # блик
        b1 = (int(cx - r * 0.4), int(cy - r * 0.4 + bob))
        pygame.draw.circle(surf, (60, 60, 60), b1, 5)
        bw = max(1, int(r * 1.8))
        bx = cx - bw // 2; by = cy - 10
        pygame.draw.rect(surf, C_HP_BG, (bx, by, bw, 7), border_radius=2)
        fill = max(0, int(bw * self.hp / self.maxhp))
        if fill:
            col = (180, 180, 180) if self.hp / self.maxhp > 0.5 else (120, 120, 120)
            pygame.draw.rect(surf, col, (bx, by, fill, 7), border_radius=2)
        pygame.draw.rect(surf, (80, 80, 80), (bx, by, bw, 7), 1, border_radius=2)
        if hovered: self._hover_label(surf)


# ══════════════════════════════════════════════════════════════════════════════
#  CHALLENGER — враги (TDS-style fallen/chester)
# ══════════════════════════════════════════════════════════════════════════════

class FallenChester(Enemy):
    """Упавший Честер. Высокий урон, 300 HP, быстрый."""
    DISPLAY_NAME = "Fallen Chester"; BASE_HP = 300; BASE_SPEED = 130; KILL_REWARD = 150
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 300; self.maxhp = 300
        self.speed = self.BASE_SPEED + (wave - 1) * 5
        self.radius = 18
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 1.6) * 3; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (20, 0, 80), (cx, cy), self.radius)
        pygame.draw.circle(surf, (80, 0, 200), (cx - 4, cy - 4), 6)
        pygame.draw.circle(surf, (120, 20, 240), (cx, cy), self.radius, 2)
        # кресты
        for a_deg in [45, 135]:
            a = math.radians(a_deg)
            pygame.draw.line(surf, (200, 100, 255),
                (cx + int(math.cos(a)*8), cy + int(math.sin(a)*8)),
                (cx + int(math.cos(a)*self.radius), cy + int(math.sin(a)*self.radius)), 2)
        self._draw_hp_bar(surf, 34, 5, (120, 20, 240))
        if hovered: self._hover_label(surf)


class FastFallenChester(FallenChester):
    """Честер на 30% быстрее (волна 9 Challenger)."""
    DISPLAY_NAME = "Fallen Chester (Fast)"; BASE_SPEED = int(130 * 1.30)
    def __init__(self, wave=1):
        super().__init__(wave)
        self.speed = self.BASE_SPEED


class TowerDestroyer(Enemy):
    """
    Волна 5 Challenger. Намеренно удаляет самую сильную башню
    (реализация в game.py: при спавне — пометить башню на удаление,
     при смерти врага — башня восстанавливается, если жив — удалена).
    Нельзя поставить башню пока он жив.
    """
    DISPLAY_NAME = "Разрушитель"; BASE_HP = 2000; BASE_SPEED = _WOLF_SPD; KILL_REWARD = 0
    IS_TOWER_DESTROYER = True
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 2000; self.maxhp = 2000
        self.speed = self.BASE_SPEED; self.radius = 28
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.8) * 2; cx, cy = int(self.x), int(self.y + bob)
        s = pygame.Surface((112, 112), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 50, 20, 50), (56, 56), 53); surf.blit(s, (cx - 56, cy - 56))
        pygame.draw.circle(surf, (200, 30, 10), (cx, cy), self.radius + 4, 5)
        pygame.draw.circle(surf, (140, 10, 0), (cx, cy), self.radius)
        pygame.draw.circle(surf, (255, 100, 60), (cx - 7, cy - 7), 11)
        pygame.draw.circle(surf, (255, 80, 40), (cx, cy), self.radius, 2)
        # крест-прицел
        pygame.draw.line(surf, (255, 220, 200), (cx - self.radius, cy), (cx + self.radius, cy), 2)
        pygame.draw.line(surf, (255, 220, 200), (cx, cy - self.radius), (cx, cy + self.radius), 2)
        self._draw_hp_bar(surf, 52, 7, (255, 80, 40))
        if hovered: self._hover_label(surf)


# ── Главный босс — Колобок (Kolobok) ─────────────────────────────────────────
class GrandpaEnemy(Enemy):
    """Дед, идёт за Колобком. 5000 HP."""
    DISPLAY_NAME = "Дед"; BASE_HP = 5000; BASE_SPEED = int(_WOLF_SPD * 0.60); KILL_REWARD = 300
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 5000; self.maxhp = 5000
        self.speed = self.BASE_SPEED; self.radius = 20
        self._throw_timer = 3.0
    def update(self, dt):
        self._throw_timer -= dt; return super().update(dt)
    def should_throw(self):
        if self._throw_timer <= 0:
            self._throw_timer = 3.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.7) * 2; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (200, 160, 100), (cx, cy), self.radius)
        pygame.draw.circle(surf, (230, 200, 150), (cx - 5, cy - 5), 7)
        # шапка
        pygame.draw.rect(surf, (80, 60, 40),
            (cx - self.radius + 2, cy - self.radius - 8, (self.radius - 2) * 2, 10),
            border_radius=3)
        self._draw_hp_bar(surf, 36, 5, (230, 200, 150))
        if hovered: self._hover_label(surf)

class GrandmaEnemy(Enemy):
    """Бабка, идёт за Колобком. 5000 HP. Оглушает скалкой юнитов."""
    DISPLAY_NAME = "Бабка"; BASE_HP = 5000; BASE_SPEED = int(_WOLF_SPD * 0.65); KILL_REWARD = 250
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp = 5000; self.maxhp = 5000
        self.speed = self.BASE_SPEED; self.radius = 18
        self._rolling_pin_timer = 4.0
        self.rolling_pin_radius = 80
    def update(self, dt):
        self._rolling_pin_timer -= dt; return super().update(dt)
    def should_stun(self):
        if self._rolling_pin_timer <= 0:
            self._rolling_pin_timer = 4.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob = math.sin(self._bob * 0.7) * 2; cx, cy = int(self.x), int(self.y + bob)
        pygame.draw.circle(surf, (220, 150, 170), (cx, cy), self.radius)
        pygame.draw.circle(surf, (255, 200, 210), (cx - 4, cy - 4), 6)
        # скалка
        a = math.radians(45 + self._bob * 10)
        sx2 = cx + int(math.cos(a) * 6); sy2 = cy + int(math.sin(a) * 6)
        ex2 = cx + int(math.cos(a) * (self.radius + 10))
        ey2 = cy + int(math.sin(a) * (self.radius + 10))
        pygame.draw.line(surf, (200, 160, 100), (sx2, sy2), (ex2, ey2), 4)
        self._draw_hp_bar(surf, 34, 5, (255, 200, 210))
        if hovered: self._hover_label(surf)

class Kolobok(Enemy):
    """
    Финальный босс Challenger.
    HP: 80 000. Скорость 20 (очень медленный).
    Абилки:
      1. Прыжок (каждые 8 сек) → стан всех юнитов в jump_radius (120 px) через game.py
      2. Самолечение (каждые 15 сек) → +3000 HP (до maxhp)
      3. Дебафф аура (каждые 5 сек) → ближайший юнит в aura_radius получает
         _silyach_debuff на aura_debuff_dur секунд (game.py проверяет should_aura_debuff)
    """
    DISPLAY_NAME = "Колобок (Финальный Босс)"; BASE_HP = 80000; BASE_SPEED = 20; KILL_REWARD = 0
    def __init__(self, wave=1):
        super().__init__(1)
        self.hp = 80000; self.maxhp = 80000
        self.speed = self.BASE_SPEED; self.radius = 46
        self._stun_immune = True
        self._rot = 0.0
        # Абилка 1: прыжок
        self._jump_timer = 8.0; self._jump_anim = 0.0
        self.jump_radius = 120
        # Абилка 2: самолечение
        self._heal_timer = 15.0
        self._heal_amount = 3000
        # Абилка 3: дебафф аура
        self._aura_timer = 5.0
        self._aura_radius = 200
        self._aura_debuff_dur = 4.0
    def update(self, dt):
        self._rot += dt * 30
        if self._jump_anim > 0: self._jump_anim = max(0, self._jump_anim - dt * 4)
        self._jump_timer -= dt
        # Самолечение
        self._heal_timer -= dt
        if self._heal_timer <= 0:
            self._heal_timer = 15.0
            self.hp = min(self.maxhp, self.hp + self._heal_amount)
        # Аура (таймер тикает, game.py читает should_aura_debuff)
        self._aura_timer -= dt
        return super().update(dt)
    def should_jump(self):
        """True каждые 8 сек → game.py станит юнитов в jump_radius на 2 сек."""
        if self._jump_timer <= 0:
            self._jump_timer = 8.0; self._jump_anim = 1.0; return True
        return False
    def should_aura_debuff(self):
        """True каждые 5 сек → game.py применяет _silyach_debuff ближайшему юниту."""
        if self._aura_timer <= 0:
            self._aura_timer = 5.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        jump_off = int(self._jump_anim * 30)
        bob = math.sin(self._bob * 0.4) * 2 - jump_off
        cx, cy = int(self.x), int(self.y + bob)
        # тень
        shadow_s = pygame.Surface((110, 30), pygame.SRCALPHA)
        shadow_alpha = max(30, 120 - jump_off * 3)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, shadow_alpha), (0, 0, 110, 30))
        surf.blit(shadow_s, (cx - 55, int(self.y) + self.radius - 8))
        # основное тело
        s = pygame.Surface((220, 220), pygame.SRCALPHA)
        pulse = int(abs(math.sin(self._rot / 30 * math.pi)) * 40) + 20
        pygame.draw.circle(s, (255, 200, 50, pulse), (110, 110), 106); surf.blit(s, (cx - 110, cy - 110))
        pygame.draw.circle(surf, (220, 160, 20), (cx, cy), self.radius + 8, 8)
        pygame.draw.circle(surf, (255, 200, 50), (cx, cy), self.radius)
        pygame.draw.circle(surf, (255, 230, 120), (cx - 14, cy - 14), 20)
        pygame.draw.circle(surf, (255, 220, 80), (cx, cy), self.radius, 3)
        # глаза
        pygame.draw.circle(surf, (20, 20, 20), (cx - 12, cy - 8), 6)
        pygame.draw.circle(surf, (20, 20, 20), (cx + 12, cy - 8), 6)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 10, cy - 10), 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx + 14, cy - 10), 2)
        # рот
        pygame.draw.arc(surf, (20, 20, 20),
            (cx - 16, cy + 2, 32, 18), math.radians(200), math.radians(340), 3)
        # крутящиеся орнаменты
        for i in range(8):
            a = math.radians(self._rot + i * 45)
            rx = cx + int(math.cos(a) * (self.radius + 14))
            ry = cy + int(math.sin(a) * (self.radius + 14))
            pygame.draw.circle(surf, (255, 220, 60), (rx, ry), 5)
        self._draw_hp_bar(surf, 90, 10, (255, 220, 60))
        if hovered: self._hover_label(surf)


# ══════════════════════════════════════════════════════════════════════════════
#  INFERNAL WAVE DATA — 34 волны
#  Формат: ([(EnemyClass, count), ...], loot_money, bonus_money)
#  Стартовый бонус: +100 к обычному (реализуется в game.py)
# ══════════════════════════════════════════════════════════════════════════════

INFERNAL_MAX_WAVES = 34

INFERNAL_WAVE_DATA = [
    None,                                                                                               # 0

    # 1: 3 волка
    ([(Wolf, 3)],                                                                          220, 50),   # 1
    # 2: 4 спиди волка
    ([(SpeedyWolf, 4)],                                                                    260, 60),   # 2
    # 3: 1 снежок (при смерти — SnowCorpse стоит на месте, обработка в game.py)
    ([(Snowball, 1)],                                                                      300, 70),   # 3
    # 4: 15 нормалов
    ([(Enemy, 15)],                                                                        360, 80),   # 4
    # 5: 1 печка (мини-босс 1, скорость -10%), после смерти — 3 угольков (обработка в game.py)
    ([(Furnace, 1)],                                                                       440, 100),  # 5
    # 6: ??? (убить могут только Cowboy, Gladiator, Archer; 1 тычки хватает; если дойдёт — поражение)
    ([(SpecterEnemy, 1)],                                                                  480, 100),  # 6
    # 7: 3 Коллектора судьбы (убить = -100$, дойдут = +500$ каждый)
    ([(FateCollector, 3)],                                                                 520, 100),  # 7
    # 8: Топот (станит ближних)
    ([(Stomp, 1)],                                                                           560, 110),  # 8
    # 9: 3 нормал-босса
    ([(NormalBoss, 3)],                                                                    620, 120),  # 9
    # 10: 3 печки + 15 волков
    ([(Furnace, 3), (Wolf, 15)],                                                           700, 130),  # 10
    # 11: 2 мистери
    ([(InfernalMystery, 2)],                                                               760, 140),  # 11
    # 12: Терпила (мини-босс 2)
    ([(Terpila, 1)],                                                                       860, 150),  # 12
    # 13: Путана
    ([(Putana, 1)],                                                                        980, 180),  # 13
    # 14: 15 волков + 5 печек
    ([(Wolf, 15), (Furnace, 5)],                                                            1080, 200),  # 14
    # 15: 15 нормал-боссов + 2 печки сзади
    ([(NormalBoss, 15), (Furnace, 2)],                                                    1180, 220),  # 15
    # 16: 2 камня (вместо волков)
    ([(InfernalStone, 2)],                                                                1280, 240),  # 16
    # 17: 5 мистери
    ([(InfernalMystery, 5)],                                                              1380, 260),  # 17
    # 18: 10 печек
    ([(Furnace, 10)],                                                                     1480, 280),  # 18
    # 19: Сигарета (дебафф урона)
    ([(Silyach, 1)],                                                                      1580, 300),  # 19
    # 20: Конфузионале
    ([(Confusilionale, 1)],                                                               1680, 320),  # 20
    # 21: 3 волка + 3 печки + 3 мистери + 4 нормал-босса
    ([(Wolf, 3), (Furnace, 3), (InfernalMystery, 3), (NormalBoss, 4)],                   1780, 340),  # 21
    # 22: Инвалид (12к HP)
    ([(Wheelchair, 1)],                                                                   1900, 360),  # 22
    # 23: 10 печек + 2 нормал-босса
    ([(Furnace, 10), (NormalBoss, 2)],                                                      2000, 400),  # 23
    # 24: 1 путана + Конфузионале + Сигарета
    ([(Putana, 1), (Confusilionale, 1), (Silyach, 1)],                                    2100, 420),  # 24
    # 25: Инвалид (босс из intermediate — Wheelchair снова)
    ([(Wheelchair, 1)],                                                                   2200, 440),  # 25
    # 26: 10 мистери
    ([(InfernalMystery, 10)],                                                             2300, 460),  # 26
    # 27: 3 чёрных квадрата
    ([(BlackSquare, 3)],                                                                  2400, 480),  # 27
    # 28: 20 печек
    ([(Furnace, 20)],                                                                     2500, 500),  # 28
    # 29: 5 волков + Инвалид
    ([(Wolf, 5), (Wheelchair, 1)],                                                        2700, 550),  # 29
    # 30: 1 Инвалид + Конфузионале (+15000$ бонус)
    ([(Wheelchair, 1), (Confusilionale, 1)],                                              15000, 600),  # 30
    # 31: 3 камня + 30 печек + 1 путана + 2 сигареты
    ([(InfernalStone, 3), (Furnace, 30), (Putana, 1), (Silyach, 2)],                     3000, 650),  # 31
    # 32: 7 волков + 1 путана
    ([(Wolf, 7), (Putana, 1)],                                                            3200, 700),  # 32
    # 33: 3 нормал-босса + 1 камень
    ([(NormalBoss, 3), (InfernalStone, 1)],                                               3500, 750),  # 33
    # 34: 20 мистери + 3 камня + 20 волков
    ([(InfernalMystery, 20), (InfernalStone, 3), (Wolf, 20)],                            5000, 0),    # 34
]


# ══════════════════════════════════════════════════════════════════════════════
#  CHALLENGER — режим «БРАТСКАЯ МОГИЛА»
#  Активируется после победы на 34 волне.
#  Радиус всех юнитов снижается на 10% в game.py.
#  10 волн.
# ══════════════════════════════════════════════════════════════════════════════

CHALLENGER_MAX_WAVES = 10

CHALLENGER_WAVE_DATA = [
    None,                                                                                               # 0

    # 1: 10 Fallen Chester
    ([(FallenChester, 10)],                                                                500, 100),  # 1
    # 2: 9 Fallen Rusher
    ([(FallenRusher, 9)],                                                                  500, 100),  # 2
    # 3: 3 Путаны (вместо нормалов)
    ([(Putana, 3)],                                                                        500, 100),  # 3
    # 4: Fallen King
    ([(FallenKing, 1)],                                                                   1000, 200),  # 4
    # 5: Печка — стан, скорость -10% (should_stun работает через game.py)
    ([(Furnace, 1)],                                                                       600, 100),  # 5
    # 6: Инвалид (скорость -10%)
    ([(Wheelchair, 1)],                                                                    480, 100),  # 6
    # 7: 15 Fallen Chester + 15 Fallen Rusher
    ([(FallenChester, 15), (FallenRusher, 15)],                                            800, 150),  # 7
    # 8: 3 Йети (вместо Fallen King)
    ([(Yeti, 3)],                                                                         2000, 300),  # 8
    # 9: 1 Fast Fallen Chester (+30% скорость)
    ([(FastFallenChester, 1)],                                                             500, 100),  # 9
    # 10: Колобок (3 абилки) + Дед (5000 HP) + Бабка (5000 HP)
    ([(Kolobok, 1), (GrandpaEnemy, 1), (GrandmaEnemy, 1)],                                   0, 0),   # 10
]


# ══════════════════════════════════════════════════════════════════════════════
#  Константа для проверки волны 6 Challenger (снять HP)
# ══════════════════════════════════════════════════════════════════════════════
CHALLENGER_WAVE6_HP_DAMAGE = 10

# ══════════════════════════════════════════════════════════════════════════════
#  ЭКСПОРТ
# ══════════════════════════════════════════════════════════════════════════════
__all__ = [
    # Infernal enemies
    "Wolf", "SpeedyWolf",
    "SnowCorpse", "Snowball",
    "Ember", "Furnace",
    "Untouchable",
    "SpecterEnemy",
    "FateCollector",
    "Stomp",
    "InfernalMystery", "InfernalStone",
    "Terpila",
    "Putana",
    "Silyach",
    "Confusilionale",
    "Wheelchair",
    "BlackSquare",
    # Challenger enemies
    "FallenChester", "FastFallenChester",
    "TowerDestroyer",
    "GrandpaEnemy", "GrandmaEnemy",
    "Kolobok",
    "Yeti",
    # Wave data
    "INFERNAL_MAX_WAVES", "INFERNAL_WAVE_DATA",
    "CHALLENGER_MAX_WAVES", "CHALLENGER_WAVE_DATA",
    "CHALLENGER_WAVE6_HP_DAMAGE",
]