import pygame
import math
import random
import time
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)
big_font = pygame.font.SysFont("consolas", 42, bold=True)
small_font = pygame.font.SysFont("consolas", 16)
title_font = pygame.font.SysFont("consolas", 64, bold=True)
label_font = pygame.font.SysFont("consolas", 18, bold=True)
import os
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
try:
  remastered_img = pygame.image.load(os.path.join(_BASE_DIR, "assets", "remastered.png")).convert_alpha()
except Exception:
  remastered_img = None
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 200, 255)
GREY = (180, 180, 180)
DARK_GREY = (50, 50, 50)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
ADMIN_COLOR = (255, 215, 0)
NULL_COLOR = (100, 0, 100)
# UI palette
UI_BG        = (10, 12, 18)
UI_PANEL     = (18, 22, 32)
UI_PANEL2    = (24, 30, 44)
UI_BORDER    = (40, 55, 80)
UI_ACCENT    = (0, 200, 255)
UI_ACCENT2   = (0, 255, 160)
UI_RED       = (220, 50, 60)
UI_ORANGE    = (255, 140, 30)
UI_MUTED     = (90, 105, 130)
UI_TEXT      = (210, 225, 245)
UI_SUBTEXT   = (120, 140, 170)

def draw_rounded_rect(surface, color, rect, radius=8, border=0, border_color=None):
  pygame.draw.rect(surface, color, rect, border_radius=radius)
  if border and border_color:
    pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

def draw_gradient_rect(surface, color_top, color_bot, rect, radius=8):
  r = pygame.Rect(rect)
  temp = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
  for y in range(r.height):
    t = y / max(r.height - 1, 1)
    c = tuple(int(color_top[i] + (color_bot[i] - color_top[i]) * t) for i in range(3))
    pygame.draw.line(temp, c, (0, y), (r.width, y))
  # apply radius mask
  mask = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
  pygame.draw.rect(mask, (255,255,255,255), (0,0,r.width,r.height), border_radius=radius)
  temp.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
  surface.blit(temp, r.topleft)

def draw_button(surface, rect, label, fnt, base_color, text_color=None, hover=False, radius=8, border_color=None, icon=None):
  tc = text_color or UI_TEXT
  if hover:
    top = tuple(min(255, c + 40) for c in base_color)
    bot = base_color
  else:
    top = tuple(min(255, c + 15) for c in base_color)
    bot = tuple(max(0, c - 20) for c in base_color)
  draw_gradient_rect(surface, top, bot, rect, radius)
  bc = border_color or tuple(min(255, c + 80) for c in base_color)
  pygame.draw.rect(surface, bc, rect, 1, border_radius=radius)
  # subtle inner highlight line at top
  hl_rect = pygame.Rect(rect.x + 2, rect.y + 1, rect.width - 4, 1)
  hl_col = tuple(min(255, c + 120) for c in base_color) + (80,)
  hl_s = pygame.Surface((hl_rect.width, 1), pygame.SRCALPHA)
  hl_s.fill((*tuple(min(255, c + 120) for c in base_color), 60))
  surface.blit(hl_s, hl_rect.topleft)
  txt = fnt.render(label, True, tc)
  surface.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

def draw_panel(surface, rect, radius=10, alpha=240):
  s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
  pygame.draw.rect(s, (*UI_PANEL, alpha), (0,0,rect.width,rect.height), border_radius=radius)
  pygame.draw.rect(s, (*UI_BORDER, 180), (0,0,rect.width,rect.height), 1, border_radius=radius)
  surface.blit(s, rect.topleft)

def draw_glowing_text(surface, text, fnt, color, pos, glow_radius=3):
  glow_col = tuple(min(255, c) for c in color)
  for dx in range(-glow_radius, glow_radius+1):
    for dy in range(-glow_radius, glow_radius+1):
      if dx==0 and dy==0: continue
      alpha = max(0, 80 - (abs(dx)+abs(dy))*20)
      gs = fnt.render(text, True, glow_col)
      gs.set_alpha(alpha)
      surface.blit(gs, (pos[0]+dx, pos[1]+dy))
  surface.blit(fnt.render(text, True, color), pos)
path = [
  (0, HEIGHT * 0.4),
  (WIDTH * 0.2, HEIGHT * 0.4),
  (WIDTH * 0.2, HEIGHT * 0.7),
  (WIDTH * 0.5, HEIGHT * 0.7),
  (WIDTH * 0.5, HEIGHT * 0.2),
  (WIDTH * 0.8, HEIGHT * 0.2),
  (WIDTH * 0.8, HEIGHT * 0.6),
  (WIDTH * 0.95, HEIGHT * 0.6)
]
GAME_STATE_MAIN_MENU = 0
GAME_STATE_LOADOUT = 1
GAME_STATE_PLAYING = 2
GAME_STATE_PAUSED = 3
GAME_STATE_HIDDEN_WAVE_EFFECT = 4
GAME_STATE_HIDDEN_WAVE = 5
base_hp = 150
money = 500
wave_timer = 0
wave_count = 0
spawn_delay = 30
enemies_left_in_wave = 0
wave_ended_time = None
wave_cooldown = 5
boss_spawned_this_wave = False
selected_tower = None
sell_confirm_pending = False
upgrade_btn_rect = None
sell_btn_rect = None
placing_tower_type = None
placing_pos = None
confirm_rect = None
bullets = []
towers = []
enemies = []
boss_health_bar_y = -50
boss_health_bar_target_y = HEIGHT * 0.07
game_state = GAME_STATE_MAIN_MENU
console_active = False
console_input = ""
console_history = []
MAX_CONSOLE_HISTORY_DISPLAY = 12
console_scroll_offset = 0
console_cmd_history = []      # история введённых команд
console_cmd_index = -1        # текущая позиция в истории команд
console_spawn_queue = []
console_spawn_timer = 0
PATH_TOLERANCE = 25
TOWER_PLACEMENT_DISTANCE = 40
hidden_wave_active = False
hidden_wave_effect_timer = 0
hidden_wave_fade_duration = 120
hidden_wave_shake_offset = [0, 0]
hidden_wave_shake_intensity = 5
hidden_wave_shake_boost_timer = 0
hidden_wave_speedy_count = 0
hidden_wave_boss_spawned = False
hidden_wave_flash_timer = 0
hidden_wave_error_timer = 0
tower_stun_timer = {}
stun_duration = 120
boss_stun_cooldown = 300
boss_stun_timer = 0
null_tower_unlocked = False
final_boss_spawned = False
final_boss_flash_timer = 0
class TowerType:
  def __init__(self, name, base_cost, base_damage, base_range, base_cooldown, max_level,
         upgrade_base_cost, upgrade_cost_mult, is_farm=False, income_per_level=None, is_admin=False, is_hidden_from_loadout=False):
    self.name = name
    self.base_cost = base_cost
    self.base_damage = base_damage
    self.base_range = base_range
    self.base_cooldown = base_cooldown
    self.max_level = max_level
    self.upgrade_base_cost = upgrade_base_cost
    self.upgrade_cost_mult = upgrade_cost_mult
    self.is_farm = is_farm
    self.income_per_level = income_per_level
    self.is_admin = is_admin
    self.is_hidden_from_loadout = is_hidden_from_loadout
# Scout lv1: 4 dmg / 35cd = ~6.9 DPS. 2 выстрела убивают normal(8HP). Норм.
SCOUT_TYPE = TowerType(name="Scout", base_cost=200, base_damage=4, base_range=130, base_cooldown=35, max_level=5, upgrade_base_cost=120, upgrade_cost_mult=1.5)
# Hacker — дорогой, контролирует
HACKER_TYPE = TowerType(name="Hacker", base_cost=4500, base_damage=5, base_range=160, base_cooldown=20, max_level=5, upgrade_base_cost=1500, upgrade_cost_mult=2.0)
# Farm — пассивный доход. lv1=50, lv2=100, lv3=225, lv4=500, lv5=900, lv6=1600
FARM_TYPE = TowerType(name="Farm", base_cost=250, base_damage=0, base_range=0, base_cooldown=0, max_level=6, upgrade_base_cost=200, upgrade_cost_mult=1.0, is_farm=True, income_per_level=[50, 100, 225, 500, 900, 1600])
# Antider lv1: 3 dmg / 28cd = ~6.4 DPS. 3 выстрела убивают normal(8HP).
ANTIDER_TYPE = TowerType(name="Antider", base_cost=400, base_damage=1, base_range=4 * 40, base_cooldown=28, max_level=5, upgrade_base_cost=250, upgrade_cost_mult=1.8)
# Admin — скрытый, мощный
ADMIN_TYPE = TowerType(name="Admin", base_cost=7500, base_damage=10, base_range=200, base_cooldown=15, max_level=5, upgrade_base_cost=3000, upgrade_cost_mult=2.2, is_admin=True, is_hidden_from_loadout=True)
# Null — оставляем в коде но скрыт
NULL_TYPE = TowerType(name="Null", base_cost=1000, base_damage=8, base_range=8 * 40, base_cooldown=18, max_level=5, upgrade_base_cost=300, upgrade_cost_mult=1.7)
ALL_TOWER_TYPES = [SCOUT_TYPE, HACKER_TYPE, FARM_TYPE, ANTIDER_TYPE, ADMIN_TYPE, NULL_TYPE]
default_initial_loadout_types = [SCOUT_TYPE, FARM_TYPE, ANTIDER_TYPE]
selected_loadout_types = list(default_initial_loadout_types)
MAX_LOADOUT_SLOTS = 4

# Floating reward texts
floating_texts = []  # list of [x, y, text, timer, color]

def add_floating_text(x, y, text, color=(255, 220, 50)):
  floating_texts.append([x, y, text, 45, color])  # 45 frames lifetime

def update_draw_floating_texts(shake_x=0, shake_y=0):
  global floating_texts
  alive = []
  for ft in floating_texts:
    ft[3] -= 1
    ft[1] -= 0.8  # плывёт вверх
    if ft[3] > 0:
      alpha = int(255 * ft[3] / 45)
      s = small_font.render(ft[2], True, ft[4])
      s.set_alpha(alpha)
      screen.blit(s, (ft[0] + shake_x - s.get_width()//2, ft[1] + shake_y))
      alive.append(ft)
  floating_texts = alive
class Enemy:
  def __init__(self, path, hp, speed, color=RED, is_clone=False, is_hidden=False, is_admin_clone=False, radius=12, name=None, reward=0):
    self.path = path
    self.pos = list(path[0])
    self.speed = speed
    self.max_hp = hp
    self.hp = hp
    self.path_index = 0
    self.color = color
    self.is_clone = is_clone
    self.alive = True
    self.reverse = False
    self.damage_dealt_by_clone = 0
    self.is_hidden = is_hidden
    self.is_admin_clone = is_admin_clone
    self.radius = radius
    self.name = name
    self.reward = reward
  def update(self):
    target_index = self.path_index - 1 if self.reverse else self.path_index + 1
    if (self.reverse and target_index < 0) or (not self.reverse and target_index >= len(self.path)):
      self.alive = False
      return
    target = self.path[target_index]
    dx, dy = target[0] - self.pos[0], target[1] - self.pos[1]
    dist = math.hypot(dx, dy)
    if dist <= self.speed:
      self.pos = list(target)
      self.path_index = target_index
    else:
      self.pos[0] += self.speed * dx / dist
      self.pos[1] += self.speed * dy / dist
  def draw(self, shake_x=0, shake_y=0):
    cx = int(self.pos[0] + shake_x)
    cy = int(self.pos[1] + shake_y)
    r = self.radius
    # Тип врага → цвета и имя
    enemy_visuals = {
      # color: (inner, outer, display_name)
    }
    # Определяем по self.color
    if self.is_admin_clone:
      inner, outer, ename = (180, 140, 0), (255, 215, 50), "IMMORTAL"
    elif self.color == RED:
      inner, outer, ename = (180, 30, 30), (255, 80, 80), "Normal"
    elif self.color == ORANGE:
      inner, outer, ename = (200, 100, 0), (255, 165, 30), "Fast"
    elif self.color == GREEN:
      inner, outer, ename = (20, 130, 40), (60, 220, 80), "Slow"
    elif self.color == BLACK:
      inner, outer, ename = (20, 20, 40), (100, 100, 180), "Hidden"
    elif self.color == PURPLE:
      inner, outer, ename = (100, 0, 160), (200, 50, 255), "Boss"
    elif self.color == CYAN:
      inner, outer, ename = (0, 140, 160), (0, 220, 255), "Clone"
    else:
      inner, outer, ename = self.color, WHITE, self.name or "?"
    if self.name:
      ename = self.name
    # Glow
    glow_surf = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*outer, 35), (r*2, r*2), r + 4)
    screen.blit(glow_surf, (cx - r*2, cy - r*2))
    # Body
    pygame.draw.circle(screen, inner, (cx, cy), r)
    pygame.draw.circle(screen, outer, (cx, cy), r, 2)
    # HP bar thin under enemy
    if not self.is_admin_clone and self.hp > 0 and self.hp < self.max_hp:
      bw = r * 2 + 4
      bx = cx - bw // 2
      by_bar = cy + r + 3
      pygame.draw.rect(screen, (40, 10, 10), (bx, by_bar, bw, 3), border_radius=1)
      fill = int(bw * max(0, self.hp) / self.max_hp)
      col = (50, 200, 70) if self.hp / self.max_hp > 0.5 else (220, 160, 20) if self.hp / self.max_hp > 0.25 else (220, 50, 50)
      pygame.draw.rect(screen, col, (bx, by_bar, fill, 3), border_radius=1)
    # Hover tooltip
    mx, my = pygame.mouse.get_pos()
    hovered = math.hypot(self.pos[0] - mx, self.pos[1] - my) <= r + 8
    if hovered:
      tip_y = cy - r - 10
      # Имя
      name_s = small_font.render(ename, True, (*outer,))
      screen.blit(name_s, (cx - name_s.get_width()//2, tip_y - 14))
      # HP
      hp_s = small_font.render(f"{int(self.hp)}/{int(self.max_hp)} HP", True, WHITE)
      screen.blit(hp_s, (cx - hp_s.get_width()//2, tip_y))
      # HP bar large
      bar_w = 50
      pygame.draw.rect(screen, (40,10,10), (cx - bar_w//2, tip_y + 14, bar_w, 5), border_radius=2)
      fill2 = int(bar_w * max(0, self.hp) / self.max_hp)
      col2 = (50,200,70) if self.hp/self.max_hp > 0.5 else (220,160,20) if self.hp/self.max_hp > 0.25 else (220,50,50)
      pygame.draw.rect(screen, col2, (cx - bar_w//2, tip_y + 14, fill2, 5), border_radius=2)
class Bullet:
  def __init__(self, x, y, target, damage, shooter=None, is_fire_bullet=False):
    self.x = x
    self.y = y
    self.target = target
    self.speed = 10
    self.damage = damage
    self.alive = True
    self.shooter = shooter
    self.is_fire_bullet = is_fire_bullet
  def update(self):
    if (not self.target or not self.target.alive or (self.target.hp <= 0 and not self.target.is_admin_clone) or
      (self.target.is_clone and self.shooter and self.shooter.type != HACKER_TYPE and not self.target.is_admin_clone) or
      (self.target.is_hidden and self.shooter and self.shooter.hidden_detection == "No") or
      (self.target.is_admin_clone and self.shooter and self.shooter.type != ADMIN_TYPE)):
      self.alive = False
      return
    dx, dy = self.target.pos[0] - self.x, self.target.pos[1] - self.y
    dist = math.hypot(dx, dy)
    if dist < self.speed:
      if not self.target.is_admin_clone:
        self.target.hp -= self.damage
      self.alive = False
      if self.shooter and self.shooter.type == HACKER_TYPE: self.shooter.clone_cooldown = False
    else:
      self.x += self.speed * dx / dist
      self.y += self.speed * dy / dist
  def draw(self, shake_x=0, shake_y=0):
    color = YELLOW
    if self.is_fire_bullet:
      color = ORANGE
    pygame.draw.circle(screen, color, (int(self.x + shake_x), int(self.y + shake_y)), 5)
class Laser:
  def __init__(self, start_pos, target_enemy, shooter_type):
    self.start_pos = start_pos
    self.target_enemy = target_enemy
    self.alive = True
    self.shooter_type = shooter_type
    
  def update(self):
    if not self.target_enemy or not self.target_enemy.alive or (self.target_enemy.hp <= 0 and not self.target_enemy.is_admin_clone): self.alive = False
  def draw(self, shake_x=0, shake_y=0):
    if self.alive and self.target_enemy and self.target_enemy.alive:
      color = GREEN if self.shooter_type == HACKER_TYPE else ADMIN_COLOR
      pygame.draw.line(screen, color, (self.start_pos[0] + shake_x, self.start_pos[1] + shake_y), (self.target_enemy.pos[0] + shake_x, self.target_enemy.pos[1] + shake_y), 3)
class Tower:
  def __init__(self, x, y, tower_type: TowerType):
    self.x, self.y, self.type, self.level = x, y, tower_type, 1
    self.timer, self.selected = 0, False
    self.clone_cooldown, self.clones_spawned_this_wave = False, 0
    self.lasers = []
    self.fire_bullet_chance = 0
    self.fire_bullet_damage = 0
    self.hidden_detection = "No"
    self.clone_chance = 0
    self.is_stunned = False
    self.radius = 16
    self.update_stats()
  def update_stats(self):
    if self.type.is_farm:
      self.damage, self.range, self.cooldown = 0, 0, 0
      self.income = self.type.income_per_level[self.level - 1] if self.level - 1 < len(self.type.income_per_level) else self.type.income_per_level[-1]
      self.hidden_detection = "No"
      self.fire_bullet_chance = 0
      self.clone_chance = 0
    elif self.type == SCOUT_TYPE:
      # dmg, range_px, cd_frames, hidden, radius_bonus
      scout_levels = {
        1: (3,  240, 98,  False, 0),
        2: (6,  240, 118, False, 0),
        3: (7,  240, 118, False, 0),
        4: (9,  240, 168, False, 0),
        5: (14, 240, 168, False, 1),
      }
      stats = scout_levels.get(self.level, scout_levels[1])
      self.damage = stats[0]
      self.range = stats[1]
      self.cooldown = stats[2]
      self.hidden_detection = "Yes" if stats[3] else "No"
      self.radius = 16 + stats[4]
      self.fire_bullet_chance = 0
      self.clone_chance = 0
    elif self.type == HACKER_TYPE:
      hacker_levels = {
        1: (5,  160, 22, False, 0.10),  # dmg, range, cd, hidden, clone%
        2: (7,  175, 19, True,  0.20),
        3: (9,  190, 16, True,  0.35),
        4: (11, 210, 13, True,  0.55),
        5: (14, 235, 10, True,  0.80),
      }
      stats = hacker_levels.get(self.level, hacker_levels[1])
      self.damage = stats[0]
      self.range = stats[1]
      self.cooldown = stats[2]
      self.hidden_detection = "Yes" if stats[3] else "No"
      self.clone_chance = stats[4]
      self.fire_bullet_chance = 0
    elif self.type == ANTIDER_TYPE:
      # firerate 0.608 = cd 99f, 0.508 = cd 118f, 0.358 = cd 168f
      # range "6" = 6*40 = 240px
      antider_levels = {
        # dmg, range_tiles, cd_frames, hidden, fire%, fire_dmg, radius_bonus
        1: (3,  6, 99,  False, 0,    0,  0),
        2: (6,  6, 118, False, 0,    0,  0),
        3: (7,  6, 118, False, 0,    0,  0),
        4: (9,  6, 168, False, 0,    0,  0),
        5: (14, 6, 168, True,  0,    0,  1),
      }
      stats = antider_levels.get(self.level, antider_levels[1])
      self.damage = stats[0]
      self.range = stats[1] * 40
      self.cooldown = stats[2]
      self.hidden_detection = "Yes" if stats[3] else "No"
      self.fire_bullet_chance = stats[4]
      self.fire_bullet_damage = stats[5]
      self.radius = 16 + stats[6]
      self.clone_chance = 0
    elif self.type == ADMIN_TYPE:
      admin_levels = {
        1: (8,  200, 18, True, 0.15),   # dmg, range, cd, hidden, clone%
        2: (13, 225, 15, True, 0.22),
        3: (19, 250, 13, True, 0.30),
        4: (27, 280, 11, True, 0.38),
        5: (38, 315, 9,  True, 0.50),
      }
      stats = admin_levels.get(self.level, (0, 0, 0, False, 0))
      self.damage = stats[0]
      self.range = stats[1]
      self.cooldown = stats[2]
      self.hidden_detection = "Yes" if stats[3] else "No"
      self.clone_chance = stats[4]
      self.fire_bullet_chance = 0
      self.fire_bullet_damage = 0
    elif self.type == NULL_TYPE:
      null_levels = {
        1: (30, 8, 0.3, True),
        2: (40, 10, 0.25, True),
        3: (45, 15, 0.20, True),
        4: (60, 15, 0.20, True),
        5: (100, 20, 0.15, True)
      }
      stats = null_levels.get(self.level, (0, 0, 0, False))
      self.damage = stats[0]
      self.range = stats[1] * 40
      self.cooldown = int(stats[2] * 60)
      self.hidden_detection = "Yes" if stats[3] else "No"
      self.fire_bullet_chance = 0
      self.fire_bullet_damage = 0
      self.clone_chance = 0
  def draw(self, shake_x=0, shake_y=0):
    tower_visuals = {
      SCOUT_TYPE:   ((40, 100, 200),  (100, 180, 255)),
      HACKER_TYPE:  ((0,  150, 160),  (0,   220, 230)),
      FARM_TYPE:    ((20, 120, 40),   (60,  200, 80)),
      ANTIDER_TYPE: ((90, 90,  110),  (160, 160, 190)),
      ADMIN_TYPE:   ((160,130, 0),    (255, 215, 50)),
      NULL_TYPE:    ((90, 0,   110),  (180, 0,   220)),
    }
    inner_c, outer_c = tower_visuals.get(self.type, ((60,80,140),(120,160,255)))
    cx, cy = self.x + shake_x, self.y + shake_y
    r = self.radius
    # Outer glow ring
    glow = pygame.Surface((r*3+12, r*3+12), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*outer_c, 40), (r*3//2+6, r*3//2+6), r + 6)
    screen.blit(glow, (cx - r*3//2 - 6, cy - r*3//2 - 6))
    # Main body
    pygame.draw.circle(screen, inner_c, (cx, cy), r)
    pygame.draw.circle(screen, outer_c, (cx, cy), r, 2)
    # Level dots
    for i in range(self.level):
      dx = (i - (self.level - 1) / 2) * 7
      pygame.draw.circle(screen, outer_c, (int(cx + dx), cy + r + 6), 3)
    if self.selected:
      if not self.type.is_farm:
        rs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(rs, (*outer_c, 25), (cx, cy), int(self.range))
        pygame.draw.circle(rs, (*outer_c, 80), (cx, cy), int(self.range), 1)
        screen.blit(rs, (0, 0))
    if self.is_stunned:
      pygame.draw.circle(screen, YELLOW, (cx, cy), r + 6, 2)
      angle = (pygame.time.get_ticks() / 10) % 360
      ex = cx + (r + 6) * math.cos(math.radians(angle))
      ey = cy + (r + 6) * math.sin(math.radians(angle))
      pygame.draw.line(screen, YELLOW, (cx, cy), (int(ex), int(ey)), 2)
  def upgrade(self):
    if self.level < self.type.max_level:
      self.level += 1
      self.update_stats()
  def upgrade_cost(self):
    if self.level >= self.type.max_level: return 0
    costs = {
      SCOUT_TYPE:   [450, 550, 1500, 2500],
      HACKER_TYPE:  [1500, 2200, 3200, 4800],
      FARM_TYPE:    [200, 600, 1200, 2500, 4500],   # lv1->2, 2->3, 3->4, 4->5, 5->6
      ANTIDER_TYPE: [450, 550, 1500, 2500],
      ADMIN_TYPE:   [3000, 4500, 6500, 9500],
      NULL_TYPE:    [300, 500, 750, 1100],
    }
    table = costs.get(self.type, [500, 750, 1000, 1500])
    return table[self.level - 1] if self.level - 1 < len(table) else 9999
  def sell_value(self):
    return int((self.type.base_cost + sum(int(self.type.upgrade_base_cost * (self.type.upgrade_cost_mult ** (lvl - 1))) for lvl in range(1, self.level))) * 0.7)
  def get_dps(self):
    return round(self.damage / (self.cooldown / 60), 1) if not self.type.is_farm else 0
  
  def get_income(self):
    return self.income if self.type.is_farm else 0
  def update(self, enemies_list, bullets_list):
    if self.is_stunned:
      self.timer = self.cooldown
      self.lasers = []
      return
    self.lasers = [l for l in self.lasers if l.alive and math.hypot(self.x - l.target_enemy.pos[0], self.y - l.target_enemy.pos[1]) < self.range]
    for l in self.lasers: l.update()
    self.timer -= 1
    if self.type.is_farm or self.timer > 0: return
    effective_enemies = []
    for e in enemies_list:
      if e.hp <= 0 and not e.is_admin_clone or not e.alive:
        continue
      if e.is_hidden and self.hidden_detection == "No":
        continue
      if e.is_clone and not e.is_admin_clone and self.type != HACKER_TYPE:
        continue
      if e.is_admin_clone and self.type != ADMIN_TYPE:
        continue
      effective_enemies.append(e)
    targets_in_range = [e for e in effective_enemies if math.hypot(self.x - e.pos[0], self.y - e.pos[1]) < self.range]
    
    self.lasers = []
    if self.type == HACKER_TYPE:
      targets_in_range_sorted = sorted(targets_in_range, key=lambda e: e.path_index, reverse=True)
      if targets_in_range_sorted:
        target_to_clone = None
        if len(targets_in_range_sorted) >= 2:
          t1, t2 = targets_in_range_sorted[0], targets_in_range_sorted[1]
          t1.hp -= self.damage; t2.hp -= self.damage
          self.lasers.extend([Laser((self.x, self.y), t1, self.type), Laser((self.x, self.y), t2, self.type)])
          target_to_clone = random.choice([t1, t2])
        else:
          t1 = targets_in_range_sorted[0]
          t1.hp -= self.damage * 2
          self.lasers.extend([Laser((self.x, self.y), t1, self.type), Laser((self.x, self.y), t1, self.type)])
          target_to_clone = t1
        self.timer = self.cooldown
        
        if not self.clone_cooldown and self.clones_spawned_this_wave < 4 and target_to_clone and random.random() < self.clone_chance:
          clone = Enemy(target_to_clone.path, target_to_clone.max_hp * 2, target_to_clone.speed, color=CYAN, is_clone=True)
          clone.pos = list(target_to_clone.pos)
          clone.path_index = target_to_clone.path_index - (1 if target_to_clone.reverse else -1)
          clone.reverse = not target_to_clone.reverse
          clone.path_index = max(0, min(clone.path_index, len(clone.path) - 1))
          enemies_list.append(clone)
          self.clone_cooldown, self.clones_spawned_this_wave = True, self.clones_spawned_this_wave + 1
    elif self.type == ADMIN_TYPE:
      if targets_in_range:
        for enemy in targets_in_range:
          if not enemy.is_admin_clone:
            enemy.hp -= self.damage
          self.lasers.append(Laser((self.x, self.y), enemy, self.type))
        self.timer = self.cooldown
        
        if not self.clone_cooldown and random.random() < self.clone_chance:
          if targets_in_range:
            target_to_clone = random.choice(targets_in_range)
            clone = Enemy(target_to_clone.path, 1000000, target_to_clone.speed, color=ADMIN_COLOR, is_clone=True, is_admin_clone=True)
            clone.pos = list(target_to_clone.pos)
            clone.path_index = target_to_clone.path_index - (1 if target_to_clone.reverse else -1)
            clone.reverse = not target_to_clone.reverse
            clone.path_index = max(0, min(clone.path_index, len(clone.path) - 1))
            enemies_list.append(clone)
            self.clone_cooldown = True
    else:
      target = next((e for e in targets_in_range if math.hypot(self.x - e.pos[0], self.y - e.pos[1]) < self.range), None)
      if target:
        bullet_damage = self.damage
        is_fire = False
        if self.type == ANTIDER_TYPE and self.level == 5 and random.random() < self.fire_bullet_chance:
          bullet_damage = self.fire_bullet_damage
          is_fire = True
        bullets_list.append(Bullet(self.x, self.y, target, bullet_damage, self, is_fire))
        self.timer = self.cooldown
def draw_game_elements(shake_x=0, shake_y=0):
  global upgrade_btn_rect, sell_btn_rect
  path_line_thickness = 30
  path_color = (35, 45, 65)
  path_edge  = (50, 65, 95)
  for i in range(len(path) - 1):
    start = (path[i][0] + shake_x, path[i][1] + shake_y)
    end = (path[i + 1][0] + shake_x, path[i + 1][1] + shake_y)
    pygame.draw.line(screen, path_color, start, end, path_line_thickness)
    pygame.draw.line(screen, path_edge, start, end, 2)
  for point in path:
    pygame.draw.circle(screen, path_color, (point[0] + shake_x, point[1] + shake_y), path_line_thickness // 2)
    pygame.draw.circle(screen, path_edge,  (point[0] + shake_x, point[1] + shake_y), path_line_thickness // 2, 2)
  for enemy in enemies:
    enemy.draw()  # Модифицируем метод draw для Enemy
  for tower in towers:
    tower.draw()  # Модифицируем метод draw для Tower
    if tower.type == HACKER_TYPE or tower.type == ADMIN_TYPE:
      for laser in tower.lasers: laser.draw(shake_x, shake_y)
      for bullet in bullets:
          bullet.draw()  # Модифицируем метод draw для Bullet
  if selected_tower:
    upgrade_btn_rect, sell_btn_rect = draw_upgrade_menu(selected_tower, shake_x, shake_y)
  else:
    upgrade_btn_rect, sell_btn_rect = None, None
  draw_tower_selector(selected_loadout_types, shake_x, shake_y)
  if not hidden_wave_active:
    # HUD panel top-left
    hud_rect = pygame.Rect(8, 8, 200, 100)
    draw_panel(screen, pygame.Rect(8+shake_x, 8+shake_y, 200, 100), radius=8)
    pygame.draw.rect(screen, UI_ACCENT, (8+shake_x, 8+shake_y, 200, 2), border_radius=8)
    money_s = font.render(f"${money}", True, UI_ACCENT2)
    hp_s    = font.render(f"{int(base_hp)} HP", True, UI_RED if base_hp < 50 else UI_TEXT)
    wave_s  = font.render(f"Wave {wave_count}", True, UI_TEXT)
    ml = small_font.render("MONEY", True, UI_MUTED)
    hl = small_font.render("BASE", True, UI_MUTED)
    wl = small_font.render("WAVE", True, UI_MUTED)
    screen.blit(ml,      (18+shake_x, 14+shake_y))
    screen.blit(money_s, (18+shake_x, 30+shake_y))
    pygame.draw.line(screen, UI_BORDER, (16+shake_x, 56+shake_y), (200+shake_x, 56+shake_y))
    screen.blit(hl,   (18+shake_x, 60+shake_y))
    screen.blit(hp_s, (18+shake_x, 76+shake_y))
    screen.blit(wl,    (120+shake_x, 60+shake_y))
    screen.blit(wave_s,(120+shake_x, 76+shake_y))
  else:
    hud_rect = pygame.Rect(8+shake_x, 8+shake_y, 200, 100)
    draw_panel(screen, hud_rect, radius=8)
    pygame.draw.rect(screen, UI_RED, (8+shake_x, 8+shake_y, 200, 2), border_radius=8)
    screen.blit(font.render("$∞", True, UI_ACCENT2),  (18+shake_x, 30+shake_y))
    screen.blit(font.render("1 HP", True, UI_RED),    (18+shake_x, 76+shake_y))
    screen.blit(font.render("Wave ???", True, UI_TEXT),(120+shake_x,76+shake_y))
  if placing_tower_type:
    mx_cur, my_cur = pygame.mouse.get_pos()
    px, py = mx_cur + shake_x, my_cur + shake_y
    can_place = is_valid_placement(mx_cur, my_cur)
    tower_color_map = {
      HACKER_TYPE: (0, 200, 255), SCOUT_TYPE: (0, 160, 255),
      FARM_TYPE: (0, 220, 80), ANTIDER_TYPE: (180, 180, 200),
      ADMIN_TYPE: (255, 215, 0), NULL_TYPE: (180, 0, 220),
    }
    base_color = tower_color_map.get(placing_tower_type, (100, 100, 255))
    color = (220, 50, 50) if not can_place else base_color
    alpha = 180
    # Range circle
    if not placing_tower_type.is_farm:
      range_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
      r = int(placing_tower_type.base_range)
      ring_col = (80, 80, 255, 60) if can_place else (255, 60, 60, 40)
      pygame.draw.circle(range_surf, ring_col, (px, py), r)
      pygame.draw.circle(range_surf, (*color, 120), (px, py), r, 1)
      screen.blit(range_surf, (0, 0))
    # Tower circle preview
    prev_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(prev_surf, (*color, alpha), (20, 20), 18)
    pygame.draw.circle(prev_surf, (255, 255, 255, 80), (20, 20), 18, 2)
    screen.blit(prev_surf, (px - 20, py - 20))
    # Can't place indicator
    if not can_place:
      cross_s = small_font.render("✕", True, (255, 80, 80))
      screen.blit(cross_s, (px + 20, py - 20))
    # Cost label
    cost_col = UI_ACCENT2 if money >= placing_tower_type.base_cost else (220, 60, 60)
    cost_s = small_font.render(f"${placing_tower_type.base_cost}", True, cost_col)
    screen.blit(cost_s, (px + 22, py + 4))
  # Floating reward texts
  update_draw_floating_texts(shake_x, shake_y)
def draw_upgrade_menu(tower, shake_x=0, shake_y=0):
  global sell_confirm_pending
  panel_w = 250
  panel_rect = pygame.Rect(WIDTH - panel_w + shake_x, 0 + shake_y, panel_w, HEIGHT - 100)
  s = pygame.Surface((panel_w, HEIGHT - 100), pygame.SRCALPHA)
  pygame.draw.rect(s, (*UI_PANEL, 235), (0, 0, panel_w, HEIGHT-100))
  pygame.draw.rect(s, (*UI_BORDER, 200), (0, 0, panel_w, HEIGHT-100), 1)
  screen.blit(s, (WIDTH - panel_w + shake_x, shake_y))
  pygame.draw.rect(screen, UI_ACCENT, (WIDTH - panel_w + shake_x, shake_y, panel_w, 2))

  tower_color_map = {
    HACKER_TYPE: (0, 130, 150),
    SCOUT_TYPE:  (0, 100, 200),
    FARM_TYPE:   (20, 130, 50),
    ANTIDER_TYPE:(90, 90, 100),
    ADMIN_TYPE:  (150, 120, 0),
    NULL_TYPE:   (90, 0, 110),
  }
  accent_c = tower_color_map.get(tower.type, (60, 80, 120))

  # Tower name header
  name_s = big_font.render(tower.type.name.upper(), True, tuple(min(255,c+80) for c in accent_c))
  screen.blit(name_s, (WIDTH - panel_w + 14 + shake_x, 10 + shake_y))
  # Level pips
  pip_y = 58 + shake_y
  for i in range(tower.type.max_level):
    pip_rect = pygame.Rect(WIDTH - panel_w + 14 + i * 34 + shake_x, pip_y, 28, 8)
    col = tuple(min(255,c+60) for c in accent_c) if i < tower.level else UI_BORDER
    pygame.draw.rect(screen, col, pip_rect, border_radius=4)
  lv_s = small_font.render(f"LVL {tower.level}/{tower.type.max_level}", True, UI_SUBTEXT)
  screen.blit(lv_s, (WIDTH - panel_w + 14 + shake_x, 72 + shake_y))

  pygame.draw.line(screen, UI_BORDER, (WIDTH-panel_w+10+shake_x, 94+shake_y), (WIDTH-10+shake_x, 94+shake_y))

  # Upgrade button
  mx, my = pygame.mouse.get_pos()
  upgrade_button_rect = pygame.Rect(WIDTH - panel_w + 12 + shake_x, 102 + shake_y, panel_w - 24, 46)
  sell_button_rect    = pygame.Rect(WIDTH - panel_w + 12 + shake_x, 156 + shake_y, panel_w - 24, 46)
  if tower.level < tower.type.max_level:
    can_afford = money >= tower.upgrade_cost()
    uc = (0, 90, 140) if can_afford else (50, 50, 60)
    draw_button(screen, upgrade_button_rect, f"UPGRADE  ${tower.upgrade_cost()}", small_font, uc, hover=upgrade_button_rect.collidepoint(mx,my) and can_afford)
  else:
    draw_button(screen, upgrade_button_rect, "✦ MAX LEVEL", small_font, (40, 80, 40))
  if sell_confirm_pending:
    draw_button(screen, sell_button_rect, "CONFIRM SELL?", small_font, (160, 20, 20), hover=sell_button_rect.collidepoint(mx,my))
    # Cancel hint
    cancel_s = small_font.render("click elsewhere to cancel", True, UI_MUTED)
    screen.blit(cancel_s, (sell_button_rect.x, sell_button_rect.bottom + 4))
  else:
    draw_button(screen, sell_button_rect, f"SELL  +${tower.sell_value()}", small_font, (80, 20, 20), hover=sell_button_rect.collidepoint(mx,my))

  pygame.draw.line(screen, UI_BORDER, (WIDTH-panel_w+10+shake_x, 210+shake_y), (WIDTH-10+shake_x, 210+shake_y))

  # Stats
  stats = [
    ("TYPE",    tower.type.name),
    ("INCOME",  f"{tower.get_income()}$/wave") if tower.type.is_farm else None,
    ("DAMAGE",  str(tower.damage))             if not tower.type.is_farm else None,
    ("RANGE",   str(int(tower.range)))         if not tower.type.is_farm else None,
    ("COOLDOWN",f"{tower.cooldown}f")          if not tower.type.is_farm else None,
    ("DPS",     str(tower.get_dps()))          if not tower.type.is_farm else None,
    ("CLONE%",  f"{int(tower.clone_chance*100)}%") if tower.type in (HACKER_TYPE, ADMIN_TYPE) else None,
    ("HIDDEN",  tower.hidden_detection),
    ("FIRE%",   f"{int(tower.fire_bullet_chance*100)}%") if tower.type == ANTIDER_TYPE and tower.fire_bullet_chance > 0 else None,
    ("FIRE DMG",str(tower.fire_bullet_damage)) if tower.type == ANTIDER_TYPE and tower.fire_bullet_damage > 0 else None,
  ]
  y_off = 218 + shake_y
  for entry in stats:
    if entry is None: continue
    k, v = entry
    ks = small_font.render(k, True, UI_MUTED)
    vs = small_font.render(v, True, UI_TEXT)
    screen.blit(ks, (WIDTH - panel_w + 14 + shake_x, y_off))
    screen.blit(vs, (WIDTH - 14 - vs.get_width() + shake_x, y_off))
    y_off += 24
  return upgrade_button_rect, sell_button_rect
def draw_tower_selector(current_loadout_types, shake_x=0, shake_y=0):
  bar_h = 100
  # Background panel
  bar_rect = pygame.Rect(0+shake_x, HEIGHT - bar_h+shake_y, WIDTH, bar_h)
  s = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
  pygame.draw.rect(s, (*UI_PANEL, 230), (0,0,WIDTH,bar_h))
  pygame.draw.rect(s, (*UI_BORDER, 200), (0,0,WIDTH,bar_h), 1)
  screen.blit(s, (0+shake_x, HEIGHT-bar_h+shake_y))
  pygame.draw.rect(screen, UI_ACCENT, (0+shake_x, HEIGHT-bar_h+shake_y, WIDTH, 2))

  tower_color_map = {
    HACKER_TYPE: (0, 110, 130),
    SCOUT_TYPE:  (0, 80, 160),
    FARM_TYPE:   (20, 100, 40),
    ANTIDER_TYPE:(70, 70, 80),
    ADMIN_TYPE:  (130, 100, 0),
    NULL_TYPE:   (70, 0, 90),
  }
  tower_buttons = {}
  x_offset = 14
  mx, my = pygame.mouse.get_pos()
  for i, t_type in enumerate(current_loadout_types):
    btn_w = 148
    btn_rect = pygame.Rect(x_offset + shake_x, HEIGHT - bar_h + 10 + shake_y, btn_w, bar_h - 20)
    base_c = tower_color_map.get(t_type, (50,50,80))
    is_selected = placing_tower_type == t_type
    if is_selected:
      draw_button(screen, btn_rect, "", font, tuple(min(255,c+60) for c in base_c), hover=True)
      pygame.draw.rect(screen, UI_ACCENT, btn_rect, 2, border_radius=8)
    else:
      draw_button(screen, btn_rect, "", font, base_c, hover=btn_rect.collidepoint(mx,my))

    # Номер слота
    slot_num = label_font.render(f"[{i+1}]", True, UI_ACCENT if is_selected else UI_MUTED)
    screen.blit(slot_num, (btn_rect.x + 6, btn_rect.y + 4))

    name_s = label_font.render(t_type.name.upper(), True, UI_TEXT)
    cost_s = small_font.render(f"${t_type.base_cost}", True, UI_ACCENT2)
    screen.blit(name_s, (btn_rect.x + btn_rect.width//2 - name_s.get_width()//2, btn_rect.y + 14))
    screen.blit(cost_s, (btn_rect.x + btn_rect.width//2 - cost_s.get_width()//2, btn_rect.y + 44))
    tower_buttons[t_type] = btn_rect
    x_offset += btn_w + 8

  return tower_buttons
def draw_confirm_button(rect, shake_x=0, shake_y=0):
  pygame.draw.rect(screen, YELLOW, rect.move(shake_x, shake_y))
  pygame.draw.line(screen, BLACK, (rect.left + 5 + shake_x, rect.centery + shake_y), (rect.centerx + shake_x, rect.bottom - 5 + shake_y), 3)
  pygame.draw.line(screen, BLACK, (rect.centerx + shake_x, rect.bottom - 5 + shake_y), (rect.right - 5 + shake_x, rect.top + 5 + shake_y), 3)
def spawn_enemy_for_wave(wave_num):
  global boss_spawned_this_wave
  # HP растёт ~20% каждые 2 волны: normal wave0=8, wave5=~20, wave10=~50, wave20=~310
  hp_scale = 1.20 ** (wave_num // 2)
  speed_chance  = min(0.05 + 0.015 * wave_num, 0.30)
  slow_chance   = min(0.05 + 0.012 * wave_num, 0.25)
  hidden_chance = 0.0 if wave_num < 5 else min(0.08 + 0.015 * (wave_num - 5), 0.35)
  # Босс каждые 5 волн начиная с 10
  if wave_num >= 10 and wave_num % 5 == 0 and not boss_spawned_this_wave and random.random() < (0.05 + 0.02 * ((wave_num - 10) / 5)):
    boss_spawned_this_wave = True
    boss_hp = int(400 * (1.25 ** ((wave_num - 10) // 5)))
    return Enemy(path, boss_hp, 0.6, color=PURPLE, reward=1488)
  r = random.random()
  if wave_num >= 5 and r < hidden_chance:
    return Enemy(path, int(14 * hp_scale), 1.4, color=BLACK, is_hidden=True, reward=16)
  if r < speed_chance:
    return Enemy(path, int(5 * hp_scale), 2.8, color=ORANGE, reward=8)
  if r < speed_chance + slow_chance:
    return Enemy(path, int(28 * hp_scale), 0.55, color=GREEN, reward=10)
  return Enemy(path, int(8 * hp_scale), 1.1, color=RED, reward=8)
def spawn_enemy_from_queue(enemy_type):
  global enemies, wave_count
  hp_scale = 1.20 ** (wave_count // 2)
  if enemy_type == "normal":
    enemies.append(Enemy(path, int(8 * hp_scale),  1.1, color=RED,   reward=8))
  elif enemy_type == "hidden":
    enemies.append(Enemy(path, int(14 * hp_scale), 1.4, color=BLACK, is_hidden=True, reward=16))
  elif enemy_type == "slow":
    enemies.append(Enemy(path, int(28 * hp_scale), 0.55, color=GREEN, reward=10))
  elif enemy_type == "fast":
    enemies.append(Enemy(path, int(5 * hp_scale),  2.8, color=ORANGE, reward=8))
  elif enemy_type == "boss":
    enemies.append(Enemy(path, int(400 * (1.25 ** (wave_count // 5))), 0.6, color=PURPLE, reward=1488))
def reset_game_state():
  global base_hp, money, wave_timer, wave_count, enemies_left_in_wave, wave_ended_time, boss_spawned_this_wave
  global selected_tower, placing_tower_type, placing_pos, confirm_rect, bullets, towers, enemies, boss_health_bar_y
  global sell_confirm_pending, upgrade_btn_rect, sell_btn_rect
  global floating_texts
  global console_spawn_queue, console_spawn_timer, console_history, console_input, console_active, console_scroll_offset
  global console_cmd_history, console_cmd_index
  global hidden_wave_active, hidden_wave_effect_timer, hidden_wave_shake_offset, hidden_wave_shake_intensity
  global hidden_wave_speedy_count, hidden_wave_boss_spawned, hidden_wave_flash_timer, hidden_wave_error_timer
  global tower_stun_timer, boss_stun_timer, null_tower_unlocked, final_boss_spawned, final_boss_flash_timer
  base_hp, money, wave_timer, wave_count, enemies_left_in_wave = 150, 500, 0, 0, 0
  wave_ended_time, boss_spawned_this_wave = None, False
  selected_tower, placing_tower_type, placing_pos, confirm_rect = None, None, None, None
  sell_confirm_pending = False
  upgrade_btn_rect = None
  sell_btn_rect = None
  bullets, towers, enemies = [], [], []
  floating_texts = []
  boss_health_bar_y = -50
  console_spawn_queue = []
  console_spawn_timer = 0
  console_history = []
  console_input = ""
  console_active = False
  console_scroll_offset = 0
  console_cmd_history.clear()
  console_cmd_index = -1
  null_tower_unlocked = False
  hidden_wave_active = False
  hidden_wave_effect_timer = 0
  hidden_wave_shake_offset = [0, 0]
  hidden_wave_shake_intensity = 5
  hidden_wave_speedy_count = 0
  hidden_wave_boss_spawned = False
  hidden_wave_flash_timer = 0
  hidden_wave_error_timer = 0
  tower_stun_timer = {}
  boss_stun_timer = 0
  final_boss_spawned = False
  final_boss_flash_timer = 0
def draw_main_menu():
  screen.fill(UI_BG)
  # Background grid
  for x in range(0, WIDTH, 60):
    pygame.draw.line(screen, (20, 28, 42), (x, 0), (x, HEIGHT))
  for y in range(0, HEIGHT, 60):
    pygame.draw.line(screen, (20, 28, 42), (0, y), (WIDTH, y))
  # Accent glow lines
  pygame.draw.line(screen, (*UI_ACCENT, 60) if False else (0, 50, 70), (0, HEIGHT//2), (WIDTH, HEIGHT//2), 1)
  # Top decorative bar
  pygame.draw.rect(screen, UI_ACCENT, (0, 0, WIDTH, 3))
  pygame.draw.rect(screen, UI_ACCENT2, (0, 3, WIDTH, 1))

  # Title
  title_y = HEIGHT // 5
  title_text = title_font.render("TDS YOPTA", True, UI_ACCENT)
  draw_glowing_text(screen, "TDS YOPTA", title_font, UI_ACCENT, (WIDTH//2 - title_text.get_width()//2, title_y))

  # Remastered image
  if remastered_img:
    img_x = WIDTH // 2 - remastered_img.get_width() // 2
    img_y = title_y + title_text.get_height() + 6
    screen.blit(remastered_img, (img_x, img_y))
    img_bottom = img_y + remastered_img.get_height() + 20
  else:
    sub = label_font.render("TOWER DEFENSE", True, UI_SUBTEXT)
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, title_y + title_text.get_height() + 4))
    img_bottom = title_y + title_text.get_height() + 40

  # Center panel
  panel_w, panel_h = 320, 240
  panel_x = WIDTH//2 - panel_w//2
  panel_y = max(img_bottom, HEIGHT//2 - 80)
  draw_panel(screen, pygame.Rect(panel_x, panel_y, panel_w, panel_h), radius=12)

  mx, my = pygame.mouse.get_pos()
  btn_w, btn_h = 260, 52
  bx = WIDTH//2 - btn_w//2
  start_btn   = pygame.Rect(bx, panel_y + 28,  btn_w, btn_h)
  loadout_btn = pygame.Rect(bx, panel_y + 96,  btn_w, btn_h)
  exit_btn    = pygame.Rect(bx, panel_y + 164, btn_w, btn_h)

  draw_button(screen, start_btn,   "▶  START GAME",    font, (0, 90, 160),  hover=start_btn.collidepoint(mx,my))
  draw_button(screen, loadout_btn, "⚙  TOWER LOADOUT", font, (120, 70, 0),  hover=loadout_btn.collidepoint(mx,my))
  draw_button(screen, exit_btn,    "✕  EXIT",           font, (100, 20, 20), hover=exit_btn.collidepoint(mx,my))

  # Bottom version label
  ver = small_font.render("v0.1  |  REMASTERED", True, UI_MUTED)
  screen.blit(ver, (WIDTH//2 - ver.get_width()//2, HEIGHT - 28))
  return start_btn, loadout_btn, exit_btn
def draw_loadout_screen():
  screen.fill(UI_BG)
  for x in range(0, WIDTH, 60):
    pygame.draw.line(screen, (20, 28, 42), (x, 0), (x, HEIGHT))
  for y in range(0, HEIGHT, 60):
    pygame.draw.line(screen, (20, 28, 42), (0, y), (WIDTH, y))
  pygame.draw.rect(screen, UI_ACCENT, (0, 0, WIDTH, 3))

  # Header
  header_rect = pygame.Rect(0, 0, WIDTH, 70)
  draw_panel(screen, header_rect, radius=0)
  title = big_font.render("TOWER LOADOUT", True, UI_ACCENT)
  draw_glowing_text(screen, "TOWER LOADOUT", big_font, UI_ACCENT, (WIDTH//2 - title.get_width()//2, 16))

  mx, my = pygame.mouse.get_pos()
  COL_W = WIDTH // 2 - 30
  # Left panel
  avail_rect = pygame.Rect(20, 85, COL_W, HEIGHT - 160)
  draw_panel(screen, avail_rect, radius=10)
  lbl = label_font.render("AVAILABLE TOWERS", True, UI_ACCENT)
  screen.blit(lbl, (avail_rect.x + 16, avail_rect.y + 12))
  pygame.draw.line(screen, UI_BORDER, (avail_rect.x+10, avail_rect.y+36), (avail_rect.right-10, avail_rect.y+36))

  tower_color_map = {
    SCOUT_TYPE:  (0, 100, 200),
    HACKER_TYPE: (0, 130, 150),
    FARM_TYPE:   (20, 110, 40),
    ANTIDER_TYPE:(80, 80, 90),
    ADMIN_TYPE:  (140, 110, 0),
    NULL_TYPE:   (80, 0, 100),
  }
  avail_btns = {}
  y_offset = 0
  for t_type in ALL_TOWER_TYPES:
    if t_type.is_hidden_from_loadout and not (t_type == ADMIN_TYPE and t_type.is_admin) and not (t_type == NULL_TYPE and null_tower_unlocked):
      continue
    btn_rect = pygame.Rect(avail_rect.x + 12, avail_rect.y + 48 + y_offset, COL_W - 24, 52)
    already = t_type in selected_loadout_types
    base_c = tower_color_map.get(t_type, (50,50,80))
    if already:
      base_c = tuple(c // 3 for c in base_c)
    draw_button(screen, btn_rect, t_type.name.upper(), font, base_c, hover=btn_rect.collidepoint(mx,my) and not already)
    # cost tag
    cost_s = small_font.render(f"${t_type.base_cost}", True, UI_ACCENT2)
    screen.blit(cost_s, (btn_rect.right - cost_s.get_width() - 10, btn_rect.centery - cost_s.get_height()//2))
    if already:
      tag = small_font.render("IN LOADOUT", True, UI_MUTED)
      screen.blit(tag, (btn_rect.x + 8, btn_rect.centery + 4))
    avail_btns[t_type] = btn_rect
    y_offset += 62

  # Right panel
  sel_rect = pygame.Rect(WIDTH//2 + 10, 85, COL_W, HEIGHT - 160)
  draw_panel(screen, sel_rect, radius=10)
  lbl2 = label_font.render("YOUR LOADOUT", True, UI_ACCENT2)
  screen.blit(lbl2, (sel_rect.x + 16, sel_rect.y + 12))
  pygame.draw.line(screen, UI_BORDER, (sel_rect.x+10, sel_rect.y+36), (sel_rect.right-10, sel_rect.y+36))

  selected_btns = {}
  y_offset = 0
  for i in range(MAX_LOADOUT_SLOTS):
    slot_rect = pygame.Rect(sel_rect.x + 12, sel_rect.y + 48 + y_offset, COL_W - 24, 52)
    if i < len(selected_loadout_types):
      t_type = selected_loadout_types[i]
      base_c = tower_color_map.get(t_type, (50,50,80))
      draw_button(screen, slot_rect, f"[{i+1}]  {t_type.name.upper()}", font, base_c, hover=slot_rect.collidepoint(mx,my))
      cost_s = small_font.render(f"${t_type.base_cost}", True, UI_ACCENT2)
      screen.blit(cost_s, (slot_rect.right - cost_s.get_width() - 10, slot_rect.centery - cost_s.get_height()//2))
      selected_btns[t_type] = slot_rect
    else:
      # empty slot
      s = pygame.Surface((slot_rect.width, slot_rect.height), pygame.SRCALPHA)
      pygame.draw.rect(s, (255,255,255,12), (0,0,slot_rect.width,slot_rect.height), border_radius=8)
      pygame.draw.rect(s, (*UI_BORDER, 100), (0,0,slot_rect.width,slot_rect.height), 1, border_radius=8)
      screen.blit(s, slot_rect.topleft)
      empty_txt = small_font.render(f"[ SLOT {i+1} — EMPTY ]", True, UI_MUTED)
      screen.blit(empty_txt, (slot_rect.centerx - empty_txt.get_width()//2, slot_rect.centery - empty_txt.get_height()//2))
    y_offset += 62

  # Back button
  back_btn = pygame.Rect(WIDTH//2 - 120, HEIGHT - 62, 240, 46)
  draw_button(screen, back_btn, "←  BACK TO MENU", font, (80, 20, 20), hover=back_btn.collidepoint(mx,my))
  return avail_btns, selected_btns, back_btn
def draw_pause_menu():
  overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
  overlay.fill((0, 0, 0, 160))
  screen.blit(overlay, (0, 0))
  menu_w, menu_h = 340, 240
  menu_x, menu_y = WIDTH//2 - menu_w//2, HEIGHT//2 - menu_h//2
  draw_panel(screen, pygame.Rect(menu_x, menu_y, menu_w, menu_h), radius=14)
  # Accent top border
  pygame.draw.rect(screen, UI_ACCENT, (menu_x, menu_y, menu_w, 3), border_radius=14)
  title = big_font.render("PAUSED", True, UI_ACCENT)
  draw_glowing_text(screen, "PAUSED", big_font, UI_ACCENT, (menu_x + menu_w//2 - title.get_width()//2, menu_y + 18))
  pygame.draw.line(screen, UI_BORDER, (menu_x+16, menu_y+68), (menu_x+menu_w-16, menu_y+68))
  mx, my = pygame.mouse.get_pos()
  continue_btn  = pygame.Rect(menu_x + 40, menu_y + 84, menu_w - 80, 52)
  main_menu_btn = pygame.Rect(menu_x + 40, menu_y + 152, menu_w - 80, 52)
  draw_button(screen, continue_btn,  "▶  CONTINUE",   font, (0, 90, 140),  hover=continue_btn.collidepoint(mx,my))
  draw_button(screen, main_menu_btn, "⌂  MAIN MENU",  font, (80, 20, 20),  hover=main_menu_btn.collidepoint(mx,my))
  return continue_btn, main_menu_btn
def draw_console():
  console_height = 300
  line_h = 20
  s = pygame.Surface((WIDTH, console_height), pygame.SRCALPHA)
  pygame.draw.rect(s, (4, 8, 14, 235), (0, 0, WIDTH, console_height))
  pygame.draw.rect(s, (*UI_ACCENT, 130), (0, 0, WIDTH, console_height), 1)
  screen.blit(s, (0, HEIGHT - console_height))
  pygame.draw.rect(screen, UI_ACCENT, (0, HEIGHT - console_height, WIDTH, 2))

  # Header
  con_lbl = label_font.render("  CONSOLE  [ ↑↓ history | PgUp/PgDn or scroll — scroll log ]", True, UI_ACCENT)
  screen.blit(con_lbl, (8, HEIGHT - console_height + 4))
  pygame.draw.line(screen, UI_BORDER, (0, HEIGHT - console_height + 22), (WIDTH, HEIGHT - console_height + 22))

  # Log area
  log_y_start = HEIGHT - console_height + 26
  input_h = 32
  log_area_h = console_height - 26 - input_h - 4
  max_visible = log_area_h // line_h

  total = len(console_history)
  # clamp scroll
  max_offset = max(0, total - max_visible)
  visible = console_history[console_scroll_offset : console_scroll_offset + max_visible]

  for i, entry in enumerate(visible):
    if entry.startswith(">"):
      color = UI_ACCENT2
    elif entry.startswith("==="):
      color = UI_ACCENT
    elif "error" in entry.lower() or "invalid" in entry.lower() or "unknown" in entry.lower():
      color = (220, 80, 80)
    else:
      color = UI_TEXT
    text_surface = small_font.render(entry, True, color)
    screen.blit(text_surface, (10, log_y_start + i * line_h))

  # Scrollbar
  if total > max_visible:
    sb_x = WIDTH - 10
    sb_y_start = log_y_start
    sb_h = log_area_h
    pygame.draw.rect(screen, UI_BORDER, (sb_x, sb_y_start, 4, sb_h), border_radius=2)
    thumb_h = max(20, int(sb_h * max_visible / total))
    thumb_y = sb_y_start + int((sb_h - thumb_h) * console_scroll_offset / max(1, max_offset))
    pygame.draw.rect(screen, UI_ACCENT, (sb_x, thumb_y, 4, thumb_h), border_radius=2)

  # Input line
  sep_y = HEIGHT - input_h - 2
  pygame.draw.line(screen, UI_BORDER, (0, sep_y), (WIDTH, sep_y))
  prompt = font.render("> ", True, UI_ACCENT)
  inp    = font.render(console_input, True, UI_TEXT)
  screen.blit(prompt, (6, sep_y + 4))
  screen.blit(inp,    (6 + prompt.get_width(), sep_y + 4))
  if (pygame.time.get_ticks() // 500) % 2 == 0:
    cx = 6 + prompt.get_width() + inp.get_width() + 2
    pygame.draw.rect(screen, UI_ACCENT, (cx, sep_y + 6, 10, 18))
def add_console_message(message):
  global console_scroll_offset
  console_history.append(message)
  # Автоскролл вниз если пользователь не скроллил вверх
  max_visible = (300 - 26 - 32 - 4) // 20
  max_offset = max(0, len(console_history) - max_visible)
  # Если были внизу — остаёмся внизу
  if console_scroll_offset >= max_offset - 1:
    console_scroll_offset = max_offset
def toggle_console():
  global console_active, console_input, console_scroll_offset, console_cmd_index
  console_active = not console_active
  console_input = ""
  console_cmd_index = -1
  max_visible = (300 - 26 - 32 - 4) // 20
  console_scroll_offset = max(0, len(console_history) - max_visible)
def process_console_command(command):
  global money, base_hp, game_state, hidden_wave_active, hidden_wave_effect_timer, enemies
  global console_spawn_queue, console_spawn_timer, selected_loadout_types, null_tower_unlocked
  global hidden_wave_shake_boost_timer, final_boss_spawned
  add_console_message(f"> {command}")
  parts = command.lower().split()
  if not parts:
    add_console_message("Type 'help' for a list of commands.")
    return
  command = parts[0]
  if command == "help":
    add_console_message("=== COMMANDS ===")
    add_console_message("help                    — show this list")
    add_console_message("spawn_enemy <type> <n>  — spawn n enemies")
    add_console_message("spawn_enemy help        — list enemy types")
    add_console_message("set_cash <amount>       — set money")
    add_console_message("set_hp <amount>         — set base HP")
    add_console_message("unit <type>             — add tower to loadout")
    add_console_message("hd                      — activate hidden wave")
  elif command == "spawn_enemy" and len(parts) == 2 and parts[1] == "help":
    add_console_message("=== ENEMY TYPES ===")
    add_console_message("normal  — standard enemy (medium HP, medium speed)")
    add_console_message("fast    — low HP, high speed")
    add_console_message("slow    — high HP, low speed")
    add_console_message("hidden  — invisible to most towers")
    add_console_message("boss    — very high HP, slow")
    add_console_message("Usage: spawn_enemy <type> <count>")
  elif command == "hd":
    if not hidden_wave_active:
      reset_game_state()
      game_state = GAME_STATE_HIDDEN_WAVE_EFFECT
      hidden_wave_active = True
      hidden_wave_effect_timer = hidden_wave_fade_duration
      # Queue enemies for hidden wave
      console_spawn_queue.extend(["fast"] * 10 + ["slow"] * 10 + ["normal"] * 10 + ["boss"] * 10)
      hidden_wave_shake_boost_timer = 120  # 2 seconds at 60 FPS
      final_boss_spawned = False
      add_console_message("Hidden wave activated! 40 enemies queued.")
    else:
      add_console_message("Hidden wave is already active!")
  elif command == "spawn_enemy":
    if len(parts) == 3:
      enemy_type = parts[1]
      valid_types = ["fast", "slow", "normal", "boss", "hidden"]
      if enemy_type not in valid_types:
        add_console_message(f"Invalid enemy type. Valid types: {', '.join(valid_types)}")
        return
      try:
        count = int(parts[2])
        if count <= 0:
          add_console_message("Count must be positive.")
          return
        for _ in range(count):
          console_spawn_queue.append(enemy_type)
        add_console_message(f"Queued {count} {enemy_type} enemies for spawn every 0.5 seconds.")
      except ValueError:
        add_console_message("Invalid count. Usage: spawn_enemy <type> <count>")
    else:
      add_console_message("Usage: spawn_enemy <type> <count>")
  elif command == "set_cash":
    if len(parts) == 2:
      try:
        amount = int(parts[1])
        if amount < 0:
          add_console_message("Amount must be non-negative.")
          return
        money = amount
        add_console_message(f"Money set to {money}.")
      except ValueError:
        add_console_message("Invalid amount. Usage: set_cash <amount>")
    else:
      add_console_message("Usage: set_cash <amount>")
  elif command == "set_hp":
    if len(parts) == 2:
      try:
        amount = int(parts[1])
        if amount < 0:
          add_console_message("HP must be non-negative.")
          return
        base_hp = amount
        add_console_message(f"Base HP set to {base_hp}.")
      except ValueError:
        add_console_message("Invalid amount. Usage: set_hp <amount>")
    else:
      add_console_message("Usage: set_hp <amount>")
  elif command == "unit":
    if len(parts) == 2:
      unit_name = parts[1].lower()
      unit_map = {
        "scout": SCOUT_TYPE,
        "hacker": HACKER_TYPE,
        "farm": FARM_TYPE,
        "antider": ANTIDER_TYPE,
        "admin": ADMIN_TYPE,
        "null": NULL_TYPE
      }
      if unit_name in unit_map:
        t_type = unit_map[unit_name]
        if t_type.is_hidden_from_loadout and not (t_type == NULL_TYPE and null_tower_unlocked) and not (t_type == ADMIN_TYPE):
          add_console_message(f"{t_type.name} tower is not available or not unlocked.")
          return
        if t_type in selected_loadout_types:
          add_console_message(f"{t_type.name} is already in loadout.")
        elif len(selected_loadout_types) < MAX_LOADOUT_SLOTS:
          selected_loadout_types.append(t_type)
          add_console_message(f"{t_type.name} tower added to loadout.")
        else:
          add_console_message("Loadout is full. Remove a tower first.")
      else:
        add_console_message(f"Unknown unit type. Valid types: {', '.join(unit_map.keys())}")
    else:
      add_console_message("Usage: unit <type>")
  else:
    add_console_message(f"Unknown command '{command}'. Type 'help' for commands.")
def dist_point_to_segment(px, py, ax, ay, bx, by):
  """Расстояние от точки (px,py) до отрезка (ax,ay)-(bx,by)"""
  dx, dy = bx - ax, by - ay
  if dx == 0 and dy == 0:
    return math.hypot(px - ax, py - ay)
  t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
  return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def is_valid_placement(x, y):
  if x < 0 or x > WIDTH or y < 0 or y > HEIGHT - 100: return False
  # Проверяем расстояние до каждого сегмента дороги
  min_dist = PATH_TOLERANCE + TOWER_PLACEMENT_DISTANCE
  for i in range(len(path) - 1):
    ax, ay = path[i][0], path[i][1]
    bx, by = path[i+1][0], path[i+1][1]
    if dist_point_to_segment(x, y, ax, ay, bx, by) < min_dist:
      return False
  for tower in towers:
    if math.hypot(x - tower.x, y - tower.y) < TOWER_PLACEMENT_DISTANCE * 2: return False
  return True
def get_tower_at_pos(x, y):
  for tower in towers:
    if math.hypot(x - tower.x, y - tower.y) < 18: return tower
  return None
def calculate_damage_dealt_by_clones():
  total_damage = 0
  for enemy in enemies:
    if enemy.is_clone and not enemy.is_admin_clone:
      total_damage += enemy.damage_dealt_by_clone
  return total_damage
reset_game_state()
running = True
while running:
  if console_spawn_queue:
    if console_spawn_timer <= 0:
      enemy_type_to_spawn = console_spawn_queue.pop(0)
      spawn_enemy_from_queue(enemy_type_to_spawn)
      console_spawn_timer = 30
    else:
      console_spawn_timer -= 1
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.KEYDOWN:
      if event.key in (pygame.K_BACKQUOTE, pygame.K_F1, pygame.K_F2) or event.unicode in ('`', '~', 'ё', 'Ё'):
        toggle_console()
      elif event.key == pygame.K_ESCAPE:
        if placing_tower_type:
          placing_tower_type = None
        elif game_state == GAME_STATE_PLAYING:
          game_state = GAME_STATE_PAUSED
        elif game_state == GAME_STATE_PAUSED:
          game_state = GAME_STATE_PLAYING
      elif console_active:
        max_visible = (300 - 26 - 32 - 4) // 20
        max_offset = max(0, len(console_history) - max_visible)
        if event.key == pygame.K_RETURN:
          if console_input.strip():
            process_console_command(console_input.strip())
            console_cmd_history.insert(0, console_input.strip())
            console_cmd_index = -1
          console_input = ""
        elif event.key == pygame.K_BACKSPACE:
          console_input = console_input[:-1]
        elif event.key == pygame.K_UP:
          # Стрелка вверх — листаем историю команд
          if console_cmd_history:
            console_cmd_index = min(console_cmd_index + 1, len(console_cmd_history) - 1)
            console_input = console_cmd_history[console_cmd_index]
        elif event.key == pygame.K_DOWN:
          # Стрелка вниз — листаем историю команд обратно
          if console_cmd_index > 0:
            console_cmd_index -= 1
            console_input = console_cmd_history[console_cmd_index]
          else:
            console_cmd_index = -1
            console_input = ""
        elif event.key == pygame.K_PAGEUP:
          console_scroll_offset = max(0, console_scroll_offset - max_visible)
        elif event.key == pygame.K_PAGEDOWN:
          console_scroll_offset = min(max_offset, console_scroll_offset + max_visible)
        else:
          console_input += event.unicode
      elif event.key == pygame.K_e and selected_tower:
        if selected_tower.level < selected_tower.type.max_level and money >= selected_tower.upgrade_cost():
          money -= selected_tower.upgrade_cost()
          selected_tower.upgrade()
      elif event.key == pygame.K_x and selected_tower and not console_active:
        money += selected_tower.sell_value()
        towers.remove(selected_tower)
        selected_tower = None
        sell_confirm_pending = False
      elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4) and not console_active:
        if game_state in (GAME_STATE_PLAYING, GAME_STATE_HIDDEN_WAVE):
          slot = event.key - pygame.K_1  # 0-3
          if slot < len(selected_loadout_types):
            t = selected_loadout_types[slot]
            if placing_tower_type == t:
              placing_tower_type = None  # повторное нажатие снимает выбор
            else:
              placing_tower_type = t
              if selected_tower:
                selected_tower.selected = False
                selected_tower = None
      elif event.key == pygame.K_r:
        reset_game_state()
        game_state = GAME_STATE_MAIN_MENU
    elif event.type == pygame.MOUSEWHEEL:
      if console_active:
        max_visible = (300 - 26 - 32 - 4) // 20
        max_offset = max(0, len(console_history) - max_visible)
        console_scroll_offset = max(0, min(max_offset, console_scroll_offset - event.y))
    elif event.type == pygame.MOUSEBUTTONDOWN:
      mx, my = event.pos
      if game_state == GAME_STATE_MAIN_MENU:
        start_game_button, loadout_button, exit_button = draw_main_menu()
        if start_game_button.collidepoint(mx, my):
          reset_game_state()
          game_state = GAME_STATE_PLAYING
        elif loadout_button.collidepoint(mx, my):
          game_state = GAME_STATE_LOADOUT
        elif exit_button.collidepoint(mx, my):
          running = False
      elif game_state == GAME_STATE_LOADOUT:
        avail_btns, selected_btns, back_btn = draw_loadout_screen()
        for t_type, rect in avail_btns.items():
          if rect.collidepoint(mx, my):
            if t_type not in selected_loadout_types and len(selected_loadout_types) < MAX_LOADOUT_SLOTS:
              selected_loadout_types.append(t_type)
            break
        for t_type, rect in selected_btns.items():
          if rect.collidepoint(mx, my):
            if t_type in selected_loadout_types:
              selected_loadout_types.remove(t_type)
            break
        if back_btn.collidepoint(mx, my):
          game_state = GAME_STATE_MAIN_MENU
      elif game_state == GAME_STATE_PAUSED:
        continue_btn, main_menu_btn = draw_pause_menu()
        if continue_btn.collidepoint(mx, my):
          game_state = GAME_STATE_PLAYING
        elif main_menu_btn.collidepoint(mx, my):
          game_state = GAME_STATE_MAIN_MENU
          reset_game_state()
      elif game_state == GAME_STATE_PLAYING or game_state == GAME_STATE_HIDDEN_WAVE:
        # Клики по кнопкам апгрейда/продажи
        if selected_tower and upgrade_btn_rect and upgrade_btn_rect.collidepoint(mx, my):
          if selected_tower.level < selected_tower.type.max_level and money >= selected_tower.upgrade_cost():
            money -= selected_tower.upgrade_cost()
            selected_tower.upgrade()
          sell_confirm_pending = False
        elif selected_tower and sell_btn_rect and sell_btn_rect.collidepoint(mx, my):
          if sell_confirm_pending:
            money += selected_tower.sell_value()
            towers.remove(selected_tower)
            selected_tower = None
            sell_confirm_pending = False
          else:
            sell_confirm_pending = True
        elif placing_tower_type:
          if event.button == 3:  # правый клик — отмена
            placing_tower_type = None
          elif event.button == 1:
            if is_valid_placement(mx, my) and money >= placing_tower_type.base_cost:
              towers.append(Tower(mx, my, placing_tower_type))
              money -= placing_tower_type.base_cost
              # Shift не зажат — снимаем выбор; зажат — продолжаем ставить
              if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                placing_tower_type = None
        else:
          clicked_tower = get_tower_at_pos(mx, my)
          if clicked_tower:
            if selected_tower: selected_tower.selected = False
            selected_tower = clicked_tower
            selected_tower.selected = True
            sell_confirm_pending = False
          else:
            if selected_tower: selected_tower.selected = False
            selected_tower = None
            sell_confirm_pending = False
            tower_buttons = draw_tower_selector(selected_loadout_types)
            for t_type, rect in tower_buttons.items():
              if rect.collidepoint(mx, my):
                placing_tower_type = t_type
                break
  current_shake_x, current_shake_y = 0, 0
  if game_state == GAME_STATE_PLAYING or game_state == GAME_STATE_HIDDEN_WAVE:
    if hidden_wave_active and hidden_wave_effect_timer > 0:
      if hidden_wave_effect_timer % 6 < 3:
        screen.fill(RED)
      current_shake_x = random.randint(-hidden_wave_shake_intensity, hidden_wave_shake_intensity)
      current_shake_y = random.randint(-hidden_wave_shake_intensity, hidden_wave_shake_intensity)
    else:
      screen.fill(UI_BG)
      for gx in range(0, WIDTH, 50):
        pygame.draw.line(screen, (18, 24, 36), (gx, 0), (gx, HEIGHT))
      for gy in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (18, 24, 36), (0, gy), (WIDTH, gy))
    
    # Apply shake effect if boost timer is active
    if hidden_wave_shake_boost_timer > 0:
      hidden_wave_shake_intensity = 20
      hidden_wave_shake_boost_timer -= 1
      if hidden_wave_shake_boost_timer <= 0:
        hidden_wave_shake_intensity = 5
      current_shake_x = random.randint(-hidden_wave_shake_intensity, hidden_wave_shake_intensity)
      current_shake_y = random.randint(-hidden_wave_shake_intensity, hidden_wave_shake_intensity)
    
    # Apply screen shake
    draw_game_elements(current_shake_x, current_shake_y)
    if hidden_wave_active and hidden_wave_effect_timer > 0:
      hidden_wave_effect_timer -= 1
    elif hidden_wave_active:
      game_state = GAME_STATE_HIDDEN_WAVE
    if hidden_wave_active and hidden_wave_flash_timer > 0:
      s = pygame.Surface((WIDTH, HEIGHT))
      s.fill((255, 0, 0))
      s.set_alpha(int(255 * (hidden_wave_flash_timer / 30)))
      screen.blit(s, (0, 0))
      hidden_wave_flash_timer -= 1
    
    if hidden_wave_active and final_boss_flash_timer > 0:
      s = pygame.Surface((WIDTH, HEIGHT))
      s.fill(WHITE)
      s.set_alpha(int(255 * (final_boss_flash_timer / 30)))
      screen.blit(s, (0, 0))
      final_boss_flash_timer -= 1
    if hidden_wave_active and hidden_wave_error_timer > 0:
      for _ in range(5):
        text_surface = big_font.render("ERROR", True, RED)
        x = random.randint(0, WIDTH - text_surface.get_width())
        y = random.randint(0, HEIGHT - text_surface.get_height())
        screen.blit(text_surface, (x, y))
      hidden_wave_error_timer -= 1
    for enemy in enemies: enemy.update()
    for tower in towers:
      if tower in tower_stun_timer and pygame.time.get_ticks() < tower_stun_timer[tower]:
        tower.is_stunned = True
      else:
        tower.is_stunned = False
        tower_stun_timer.pop(tower, None)
      tower.update([e for e in enemies if e.alive], bullets)
    for bullet in bullets: bullet.update()
    for enemy in enemies:
      if not enemy.alive or enemy.hp <= 0:
        if not enemy.is_clone and not enemy.is_admin_clone and enemy.reward > 0:
          money += enemy.reward
          add_floating_text(enemy.pos[0], enemy.pos[1] - enemy.radius, f"+${enemy.reward}")
    enemies = [e for e in enemies if e.alive and (e.hp > 0 or e.is_admin_clone)]
    bullets = [b for b in bullets if b.alive]
    if hidden_wave_active and boss_stun_timer > 0: boss_stun_timer -= 1
    if not hidden_wave_active:
      wave_timer += 1
      if wave_timer >= spawn_delay and enemies_left_in_wave > 0:
        new_enemy = spawn_enemy_for_wave(wave_count)
        if new_enemy:
          enemies.append(new_enemy)
          enemies_left_in_wave -= 1
        wave_timer = 0
      
      if not enemies and wave_ended_time is None: wave_ended_time = pygame.time.get_ticks()
      if enemies_left_in_wave == 0 and not enemies and wave_ended_time is not None and pygame.time.get_ticks() - wave_ended_time >= wave_cooldown * 1000:
        money += 100 + wave_count * 20
        for tower in towers:
          if tower.type.is_farm: money += tower.get_income()
        wave_count += 1
        enemies_left_in_wave = 5 + wave_count * 2
        wave_timer = 0
        wave_ended_time = None
        boss_spawned_this_wave = False
        for tower in towers: tower.clone_cooldown = False
    else:
      if not enemies and not final_boss_spawned and not console_spawn_queue and not hidden_wave_boss_spawned:
        final_boss_spawned = True
        final_boss_flash_timer = 30  # 0.5 seconds at 60 FPS
        enemies.append(Enemy(path, 200000, 0.3, color=PURPLE, name=".n.u.ul.l.404"))
      
      if boss_stun_timer <= 0:
        boss = next((e for e in enemies if e.color == PURPLE and not e.is_admin_clone), None)
        if boss:
          for tower in towers:
            if math.hypot(tower.x - boss.pos[0], tower.y - boss.pos[1]) < tower.range:
              tower_stun_timer[tower] = pygame.time.get_ticks() + stun_duration * 1000 // 60
          boss_stun_timer = boss_stun_cooldown
    for enemy in enemies:
      if not enemy.reverse and enemy.path_index == len(path) - 1:
        base_hp -= (enemy.max_hp if enemy.is_clone else enemy.max_hp) / 10
        enemy.alive = False
      elif enemy.reverse and enemy.path_index == 0:
        enemy.alive = False
    if base_hp <= 0:
      game_state = GAME_STATE_MAIN_MENU
      reset_game_state()
      print("Game Over!")
    boss_alive = any(e.color == PURPLE for e in enemies)
    if boss_alive:
      boss = next(e for e in enemies if e.color == PURPLE)
      boss_max_hp, boss_current_hp = boss.max_hp, max(0, boss.hp)
      if boss_health_bar_y < boss_health_bar_target_y: boss_health_bar_y += 2
      bar_w = WIDTH - 400
      bar_x = WIDTH // 2 - bar_w // 2
      # Background
      pygame.draw.rect(screen, (15, 15, 25), (bar_x + current_shake_x, int(boss_health_bar_y) + current_shake_y, bar_w, 30), border_radius=6)
      # Fill
      fill_w = int((boss_current_hp / boss_max_hp) * bar_w)
      pct = boss_current_hp / boss_max_hp
      bar_col = (int(220*(1-pct)), int(60+160*pct), 60)
      pygame.draw.rect(screen, bar_col, (bar_x + current_shake_x, int(boss_health_bar_y) + current_shake_y, fill_w, 30), border_radius=6)
      # Border
      pygame.draw.rect(screen, UI_BORDER, (bar_x + current_shake_x, int(boss_health_bar_y) + current_shake_y, bar_w, 30), 1, border_radius=6)
      name_text = ".n.u.ul.l.404" if boss.name else "Boss"
      boss_lbl = font.render(f"{name_text}  {int(boss_current_hp):,} / {int(boss_max_hp):,}", True, UI_TEXT)
      screen.blit(boss_lbl, (WIDTH//2 - boss_lbl.get_width()//2 + current_shake_x, int(boss_health_bar_y) + 4 + current_shake_y))
  elif game_state == GAME_STATE_MAIN_MENU:
    draw_main_menu()
  elif game_state == GAME_STATE_LOADOUT:
    draw_loadout_screen()
  elif game_state == GAME_STATE_PAUSED:
    draw_pause_menu()
  elif game_state == GAME_STATE_HIDDEN_WAVE_EFFECT:
    if hidden_wave_effect_timer > 0:
      hidden_wave_effect_timer -= 1
      alpha = int(255 * (hidden_wave_effect_timer / hidden_wave_fade_duration))
      s = pygame.Surface((WIDTH, HEIGHT))
      s.fill((0, 0, 0))
      s.set_alpha(alpha)
      screen.blit(s, (0, 0))
      
      current_shake_x = random.randint(-hidden_wave_shake_intensity, hidden_wave_shake_intensity)
      current_shake_y = random.randint(-hidden_wave_shake_intensity, hidden_wave_shake_intensity)
      
      if hidden_wave_effect_timer > hidden_wave_fade_duration / 2:
        if hidden_wave_effect_timer % 10 < 5: screen.fill(RED)
      else:
        if hidden_wave_effect_timer % 10 < 5:
          for _ in range(5):
            text_surface = big_font.render("ERROR", True, RED)
            x = random.randint(0, WIDTH - text_surface.get_width())
            y = random.randint(0, HEIGHT - text_surface.get_height())
            screen.blit(text_surface, (x, y))
    else:
      game_state = GAME_STATE_HIDDEN_WAVE
      hidden_wave_shake_boost_timer = 120  # 2 seconds at 60 FPS
  if console_active:
    draw_console()
  pygame.display.flip()
  clock.tick(60)
pygame.quit()