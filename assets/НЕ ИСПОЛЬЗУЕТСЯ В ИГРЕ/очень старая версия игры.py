import pygame
import math
import random
import time
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24)
big_font = pygame.font.SysFont("arial", 36)
small_font = pygame.font.SysFont("arial", 18)
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
MAX_CONSOLE_HISTORY_DISPLAY = 6
console_scroll_offset = 0
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
SCOUT_TYPE = TowerType(name="Scout", base_cost=250, base_damage=35, base_range=140, base_cooldown=30, max_level=5, upgrade_base_cost=150, upgrade_cost_mult=1.5)
HACKER_TYPE = TowerType(name="Hacker", base_cost=4500, base_damage=20, base_range=160, base_cooldown=20, max_level=5, upgrade_base_cost=1500, upgrade_cost_mult=2.0)
FARM_TYPE = TowerType(name="Farm", base_cost=250, base_damage=0, base_range=0, base_cooldown=0, max_level=5, upgrade_base_cost=100, upgrade_cost_mult=1.5, is_farm=True, income_per_level=[50, 100, 250, 500, 750, 1500])
ANTIDER_TYPE = TowerType(name="Antider", base_cost=450, base_damage=1, base_range=4 * 40, base_cooldown=28, max_level=5, upgrade_base_cost=300, upgrade_cost_mult=1.9)
ADMIN_TYPE = TowerType(name="Admin", base_cost=7500, base_damage=30, base_range=200, base_cooldown=15, max_level=5, upgrade_base_cost=3000, upgrade_cost_mult=2.2, is_admin=True, is_hidden_from_loadout=True)
NULL_TYPE = TowerType(name="Null", base_cost=1000, base_damage=30, base_range=8 * 40, base_cooldown=18, max_level=5, upgrade_base_cost=300, upgrade_cost_mult=1.7)
ALL_TOWER_TYPES = [SCOUT_TYPE, HACKER_TYPE, FARM_TYPE, ANTIDER_TYPE, ADMIN_TYPE, NULL_TYPE]
default_initial_loadout_types = [SCOUT_TYPE, FARM_TYPE, ANTIDER_TYPE]
selected_loadout_types = list(default_initial_loadout_types)
MAX_LOADOUT_SLOTS = 4
class Enemy:
  def __init__(self, path, hp, speed, color=RED, is_clone=False, is_hidden=False, is_admin_clone=False, radius=12, name=None):
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
    pygame.draw.circle(screen, self.color, (int(self.pos[0] + shake_x), int(self.pos[1] + shake_y)), self.radius)
    if not self.is_admin_clone and self.color != (0,0,0) and self.hp > 0:
      hp_text = font.render(str(int(self.hp)), True, BLACK)
      screen.blit(hp_text, (self.pos[0] + shake_x - hp_text.get_width() // 2, self.pos[1] + shake_y - 30))
    if self.is_hidden:
      mx, my = pygame.mouse.get_pos()
      if math.hypot(self.pos[0] - mx, self.pos[1] - my) <= 15:
        screen.blit(small_font.render("HIDDEN", True, BLACK), (self.pos[0] + shake_x - small_font.render("HIDDEN", True, BLACK).get_width() // 2, self.pos[1] + shake_y - 55))
    if self.is_admin_clone:
      screen.blit(small_font.render("IMMORTAL", True, PURPLE), (self.pos[0] + shake_x - small_font.render("IMMORTAL", True, PURPLE).get_width() // 2, self.pos[1] + shake_y - 55))
    if self.name:
      name_text = small_font.render(self.name, True, BLACK)
      screen.blit(name_text, (self.pos[0] + shake_x - name_text.get_width() // 2, self.pos[1] + shake_y - 55))
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
    self.update_stats()
  def update_stats(self):
    if self.type.is_farm:
      self.damage, self.range, self.cooldown = 0, 0, 0
      self.income = self.type.income_per_level[self.level] if self.level < len(self.type.income_per_level) else self.type.income_per_level[-1]
      self.hidden_detection = "No"
      self.fire_bullet_chance = 0
      self.clone_chance = 0
    elif self.type == SCOUT_TYPE:
      self.damage = self.type.base_damage + (self.level - 1) * 10
      self.range = self.type.base_range + (self.level - 1) * 15
      self.cooldown = max(10, self.type.base_cooldown - (self.level - 1) * 3)
      self.hidden_detection = "Yes" if self.level >= 4 else "No"
      self.fire_bullet_chance = 0
      self.clone_chance = 0
    elif self.type == HACKER_TYPE:
      self.damage = self.type.base_damage
      self.range = self.type.base_range + (self.level - 1) * 15
      self.cooldown = max(10, self.type.base_cooldown - (self.level - 1) * 3)
      self.clone_chance = 0.10 + (self.level - 1) * (0.70 / 4)
      self.hidden_detection = "Yes" if self.level >= 2 else "No"
      self.fire_bullet_chance = 0
    elif self.type == ANTIDER_TYPE:
      antider_levels = {
        1:  (15, 4, 28, False, 0, 0),
        2:  (30, 5, 22, True, 0, 0),
        3:  (45, 6, 19, True, 0, 0),
        4:  (50, 7, 16, True, 0, 0),
        5:  (75, 8, 10, True, 0.10, 100)
      }
      stats = antider_levels.get(self.level, (0, 0, 0, False, 0, 0))
      self.damage = stats[0]
      self.range = stats[1] * 40
      self.cooldown = stats[2]
      self.hidden_detection = "Yes" if stats[3] else "No"
      self.fire_bullet_chance = stats[4]
      self.fire_bullet_damage = stats[5]
      self.clone_chance = 0
    elif self.type == ADMIN_TYPE:
      admin_levels = {
        1: (30, 200, 20, True, 0.15),
        2: (45, 220, 18, True, 0.20),
        3: (60, 240, 16, True, 0.25),
        4: (80, 260, 14, True, 0.30),
        5: (100, 300, 10, True, 0.40)
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
    color_map = {HACKER_TYPE: CYAN, SCOUT_TYPE: BLUE, FARM_TYPE: GREEN, ANTIDER_TYPE: GREY, ADMIN_TYPE: ADMIN_COLOR, NULL_TYPE: NULL_COLOR}
    color = color_map.get(self.type, BLUE)
    pygame.draw.circle(screen, color, (self.x + shake_x, self.y + shake_y), 18)
    if self.selected:
      if not self.type.is_farm:
        pygame.draw.circle(screen, (100, 100, 255), (self.x + shake_x, self.y + shake_y), int(self.range), 1)
      level_text = font.render(str(self.level), True, WHITE)
      screen.blit(level_text, (self.x + shake_x - level_text.get_width() // 2, self.y + shake_y - level_text.get_height() // 2))
    
    if self.is_stunned:
      pygame.draw.circle(screen, YELLOW, (self.x + shake_x, self.y + shake_y), 25, 2)
      angle = (pygame.time.get_ticks() / 10) % 360
      end_x = self.x + shake_x + 25 * math.cos(math.radians(angle))
      end_y = self.y + shake_y + 25 * math.sin(math.radians(angle))
      pygame.draw.line(screen, YELLOW, (self.x + shake_x, self.y + shake_y), (end_x, end_y), 2)
  def upgrade(self):
    if self.level < self.type.max_level:
      self.level += 1
      self.update_stats()
  def upgrade_cost(self):
    return int(self.type.upgrade_base_cost * (self.type.upgrade_cost_mult ** (self.level - 1))) if self.level < self.type.max_level else 0
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
  path_line_thickness = 30
  for i in range(len(path) - 1):
    start = (path[i][0] + shake_x, path[i][1] + shake_y)
    end = (path[i + 1][0] + shake_x, path[i + 1][1] + shake_y)
    pygame.draw.line(screen, DARK_GREY, start, end, path_line_thickness)
  for point in path:
    pygame.draw.circle(screen, DARK_GREY, (point[0] + shake_x, point[1] + shake_y), path_line_thickness // 2)
  for enemy in enemies:
    enemy.draw()  # Модифицируем метод draw для Enemy
  for tower in towers:
    tower.draw()  # Модифицируем метод draw для Tower
    if tower.type == HACKER_TYPE or tower.type == ADMIN_TYPE:
      for laser in tower.lasers: laser.draw(shake_x, shake_y)
      for bullet in bullets:
          bullet.draw()  # Модифицируем метод draw для Bullet
  if selected_tower:
    draw_upgrade_menu(selected_tower, shake_x, shake_y)
  draw_tower_selector(selected_loadout_types, shake_x, shake_y)
  if not hidden_wave_active:
    screen.blit(font.render(f"Money: ${money}", True, BLACK), (10 + shake_x, 10 + shake_y))
    screen.blit(font.render(f"Base HP: {base_hp}", True, RED), (10 + shake_x, 40 + shake_y))
    screen.blit(font.render(f"Wave: {wave_count}", True, BLACK), (10 + shake_x, 70 + shake_y))
  else:
    screen.blit(font.render(f"Money: inf", True, BLACK), (10 + shake_x, 10 + shake_y))
    screen.blit(font.render(f"Base HP: 1", True, RED), (10 + shake_x, 40 + shake_y))
    screen.blit(font.render(f"Wave: ???", True, BLACK), (10 + shake_x, 70 + shake_y))
  if placing_tower_type and placing_pos:
    can_place = is_valid_placement(placing_pos[0], placing_pos[1])
    color_map = {HACKER_TYPE: CYAN, SCOUT_TYPE: BLUE, FARM_TYPE: GREEN, ANTIDER_TYPE: GREY, ADMIN_TYPE: ADMIN_COLOR, NULL_TYPE: NULL_COLOR}
    base_color = color_map.get(placing_tower_type, BLUE)
    
    if isinstance(base_color, tuple) and len(base_color) == 3:
      color = base_color
      if not can_place:
        color = RED
      else:
        color = tuple(min(255, c + 50) for c in base_color)
    else:
      color = RED
    s = pygame.Surface((36, 36), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, 150), (18, 18), 18)
    screen.blit(s, (placing_pos[0] - 18 + shake_x, placing_pos[1] - 18 + shake_y))
    if not placing_tower_type.is_farm:
      pygame.draw.circle(screen, (100, 100, 255, 100), (placing_pos[0] + shake_x, placing_pos[1] + shake_y), int(placing_tower_type.base_range), 1)
  if confirm_rect:
    draw_confirm_button(confirm_rect.move(shake_x, shake_y))
def draw_upgrade_menu(tower, shake_x=0, shake_y=0):
  pygame.draw.rect(screen, DARK_GREY, (WIDTH - 250 + shake_x, 0 + shake_y, 250, HEIGHT))
  
  upgrade_button_rect = pygame.Rect(WIDTH - 230 + shake_x, 60 + shake_y, 200, 40)
  sell_button_rect = pygame.Rect(WIDTH - 230 + shake_x, 120 + shake_y, 200, 40)
  
  pygame.draw.rect(screen, GREY, upgrade_button_rect)
  pygame.draw.rect(screen, GREY, sell_button_rect)
  
  screen.blit(font.render(f"Upgrade (E) ({tower.upgrade_cost()}$)" if tower.level < tower.type.max_level else "MAX LEVEL", True, BLACK), (upgrade_button_rect.x + 10, upgrade_button_rect.y + 10))
  screen.blit(font.render(f"Sell (X) ({tower.sell_value()}$)", True, BLACK), (sell_button_rect.x + 10, sell_button_rect.y + 10))
  stats = [
    f"Type: {tower.type.name}", f"Level: {tower.level}/{tower.type.max_level}",
    f"Income: {tower.get_income()}$/wave" if tower.type.is_farm else None,
    f"Damage: {tower.damage}" if not tower.type.is_farm else None,
    f"Range: {int(tower.range)}" if not tower.type.is_farm else None,
    f"Cooldown: {tower.cooldown}f" if not tower.type.is_farm else None,
    f"DPS: {tower.get_dps()}" if not tower.type.is_farm else None,
    f"Clone Chance: {int(tower.clone_chance * 100)}%" if tower.type == HACKER_TYPE or tower.type == ADMIN_TYPE else None,
    f"Hidden Detection: {tower.hidden_detection}",
    f"Fire Bullet Chance: {int(tower.fire_bullet_chance * 100)}%" if tower.type == ANTIDER_TYPE and tower.fire_bullet_chance > 0 else None,
    f"Fire Bullet Damage: {tower.fire_bullet_damage}" if tower.type == ANTIDER_TYPE and tower.fire_bullet_damage > 0 else None
  ]
  
  y_offset = 180
  for s in [s for s in stats if s is not None]:
    screen.blit(font.render(s, True, WHITE), (WIDTH - 240 + shake_x, y_offset + shake_y))
    y_offset += 30
def draw_tower_selector(current_loadout_types, shake_x=0, shake_y=0):
  pygame.draw.rect(screen, DARK_GREY, (0 + shake_x, HEIGHT - 100 + shake_y, WIDTH, 100))
  tower_buttons = {}
  x_offset = 20
  
  display_types = current_loadout_types
  for t_type in display_types:
    btn_rect = pygame.Rect(x_offset + shake_x, HEIGHT - 85 + shake_y, 150, 70)
    
    color_to_draw = GREY
    
    highlight_colors = {
      HACKER_TYPE: CYAN,
      SCOUT_TYPE: BLUE,
      FARM_TYPE: GREEN,
      ANTIDER_TYPE: GREY,
      ADMIN_TYPE: ADMIN_COLOR,
      NULL_TYPE: NULL_COLOR
    }
    if placing_tower_type == t_type:
      color_to_draw = highlight_colors.get(t_type, GREY)
      color_to_draw = tuple(max(0, c - 50) for c in color_to_draw)
      
    if not isinstance(color_to_draw, tuple) or len(color_to_draw) != 3:
      color_to_draw = RED
    pygame.draw.rect(screen, color_to_draw, btn_rect)
    screen.blit(font.render(t_type.name, True, WHITE), (x_offset + 10 + shake_x, HEIGHT - 75 + shake_y))
    screen.blit(font.render(f"${t_type.base_cost}", True, YELLOW), (x_offset + 10 + shake_x, HEIGHT - 50 + shake_y))
    tower_buttons[t_type] = btn_rect
    x_offset += 160
  return tower_buttons
def draw_confirm_button(rect, shake_x=0, shake_y=0):
  pygame.draw.rect(screen, YELLOW, rect.move(shake_x, shake_y))
  pygame.draw.line(screen, BLACK, (rect.left + 5 + shake_x, rect.centery + shake_y), (rect.centerx + shake_x, rect.bottom - 5 + shake_y), 3)
  pygame.draw.line(screen, BLACK, (rect.centerx + shake_x, rect.bottom - 5 + shake_y), (rect.right - 5 + shake_x, rect.top + 5 + shake_y), 3)
def spawn_enemy_for_wave(wave_num):
  global boss_spawned_this_wave
  speed_chance = min(0.03 + 0.01 * wave_num, 0.3)
  slow_chance = min(0.03 + 0.01 * wave_num, 0.3)
  hidden_chance = 0.0 if wave_num < 6 else min(0.1 + 0.02 * (wave_num - 6), 0.4)
  if wave_num >= 10 and wave_num % 5 == 0 and not boss_spawned_this_wave and random.random() < (0.05 + 0.02 * ((wave_num - 10) / 5)):
    boss_spawned_this_wave = True
    return Enemy(path, 15000 + (wave_num - 10) * 1000, 0.5, color=PURPLE)
  
  r = random.random()
  if wave_num >= 6 and r < hidden_chance: return Enemy(path, 200, 1.3, color=BLACK, is_hidden=True)
  if r < speed_chance: return Enemy(path, 50 + wave_num * 5, 3.0, color=ORANGE)
  if r < speed_chance + slow_chance: return Enemy(path, 300 + wave_num * 20, 0.5, color=GREEN)
  return Enemy(path, 100 + wave_num * 10, 1.0, color=RED)
def spawn_enemy_from_queue(enemy_type):
  global enemies, wave_count
  if enemy_type == "normal":
    enemies.append(Enemy(path, 100 + wave_count * 10, 1.0, color=RED))
  elif enemy_type == "hidden":
    enemies.append(Enemy(path, 200, 1.3, color=BLACK, is_hidden=True))
  elif enemy_type == "slow":
    enemies.append(Enemy(path, 300 + wave_count * 20, 0.5, color=GREEN))
  elif enemy_type == "fast":
    enemies.append(Enemy(path, 50 + wave_count * 5, 3.0, color=ORANGE))
  elif enemy_type == "boss":
    enemies.append(Enemy(path, 5000, 0.5, color=PURPLE))
  elif enemy_type == "null":
    enemies.append(Enemy(path, 500000, 0.2, color=NULL_COLOR, radius=18, name="N.U.L.L"))
def reset_game_state():
  global base_hp, money, wave_timer, wave_count, enemies_left_in_wave, wave_ended_time, boss_spawned_this_wave
  global selected_tower, placing_tower_type, placing_pos, confirm_rect, bullets, towers, enemies, boss_health_bar_y
  global console_spawn_queue, console_spawn_timer, console_history, console_input, console_active, console_scroll_offset
  global hidden_wave_active, hidden_wave_effect_timer, hidden_wave_shake_offset, hidden_wave_shake_intensity
  global hidden_wave_speedy_count, hidden_wave_boss_spawned, hidden_wave_flash_timer, hidden_wave_error_timer
  global tower_stun_timer, boss_stun_timer, null_tower_unlocked, final_boss_spawned, final_boss_flash_timer
  base_hp, money, wave_timer, wave_count, enemies_left_in_wave = 150, 500, 0, 0, 0
  wave_ended_time, boss_spawned_this_wave = None, False
  selected_tower, placing_tower_type, placing_pos, confirm_rect = None, None, None, None
  bullets, towers, enemies = [], [], []
  boss_health_bar_y = -50
  console_spawn_queue = []
  console_spawn_timer = 0
  console_history = []
  console_input = ""
  console_active = False
  console_scroll_offset = 0
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
  screen.fill(DARK_GREY)
  title_text = big_font.render("Tower Defense yopta", True, WHITE)
  screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
  start_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
  loadout_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)
  exit_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 140, 200, 50)
  pygame.draw.rect(screen, BLUE, start_btn); screen.blit(font.render("Start Game", True, WHITE), (start_btn.centerx - font.render("Start Game", True, WHITE).get_width() // 2, start_btn.centery - font.render("Start Game", True, WHITE).get_height() // 2))
  pygame.draw.rect(screen, ORANGE, loadout_btn); screen.blit(font.render("Tower Loadout", True, WHITE), (loadout_btn.centerx - font.render("Tower Loadout", True, WHITE).get_width() // 2, loadout_btn.centery - font.render("Tower Loadout", True, WHITE).get_height() // 2))
  pygame.draw.rect(screen, RED, exit_btn); screen.blit(font.render("Exit", True, WHITE), (exit_btn.centerx - font.render("Exit", True, WHITE).get_width() // 2, exit_btn.centery - font.render("Exit", True, WHITE).get_height() // 2))
  return start_btn, loadout_btn, exit_btn
def draw_loadout_screen():
  screen.fill(DARK_GREY)
  screen.blit(big_font.render("Select Your Towers", True, WHITE), (WIDTH // 2 - big_font.render("Select Your Towers", True, WHITE).get_width() // 2, 50))
  avail_x, avail_y = 50, 150
  pygame.draw.rect(screen, GREY, (avail_x - 10, avail_y - 40, WIDTH / 2 - 50, HEIGHT - 200), 0, 5)
  screen.blit(font.render("Available Towers:", True, BLACK), (avail_x, avail_y - 30))
  avail_btns = {}
  y_offset = 0
  for t_type in ALL_TOWER_TYPES:
    if t_type.is_hidden_from_loadout and not (t_type == ADMIN_TYPE and t_type.is_admin) and not (t_type == NULL_TYPE and null_tower_unlocked):
      continue
    btn_rect = pygame.Rect(avail_x, avail_y + y_offset, 200, 40)
    btn_color = BLUE if t_type not in selected_loadout_types else (BLUE[0] // 2, BLUE[1] // 2, BLUE[2] // 2)
    if t_type == NULL_TYPE:
      btn_color = NULL_COLOR if t_type not in selected_loadout_types else (NULL_COLOR[0] // 2, NULL_COLOR[1] // 2, NULL_COLOR[2] // 2)
    pygame.draw.rect(screen, btn_color, btn_rect)
    screen.blit(font.render(t_type.name, True, WHITE), (btn_rect.x + 10, btn_rect.y + 10))
    avail_btns[t_type] = btn_rect
    y_offset += 50
  selected_x, selected_y = WIDTH / 2 + 50, 150
  pygame.draw.rect(screen, GREY, (selected_x - 10, selected_y - 40, WIDTH / 2 - 50, HEIGHT - 200), 0, 5)
  screen.blit(font.render("Your Loadout:", True, BLACK), (selected_x, selected_y - 30))
  selected_btns = {}
  y_offset = 0
  for i in range(MAX_LOADOUT_SLOTS):
    slot_rect = pygame.Rect(selected_x, selected_y + y_offset, 200, 40)
    pygame.draw.rect(screen, (100, 100, 100), slot_rect, 2)
    if i < len(selected_loadout_types):
      t_type = selected_loadout_types[i]
      btn_color = GREEN
      if t_type == NULL_TYPE:
        btn_color = NULL_COLOR
      pygame.draw.rect(screen, btn_color, slot_rect)
      screen.blit(font.render(t_type.name, True, WHITE), (slot_rect.x + 10, slot_rect.y + 10))
      selected_btns[t_type] = slot_rect
    else:
      screen.blit(font.render("Empty Slot", True, (150, 150, 150)), (slot_rect.x + 10, slot_rect.y + 10))
    y_offset += 50
  back_btn = pygame.Rect(WIDTH // 2 - 75, HEIGHT - 80, 150, 50)
  pygame.draw.rect(screen, RED, back_btn)
  screen.blit(font.render("Back", True, WHITE), (back_btn.centerx - font.render("Back", True, WHITE).get_width() // 2, back_btn.centery - font.render("Back", True, WHITE).get_height() // 2))
  return avail_btns, selected_btns, back_btn
def draw_pause_menu():
  s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
  s.fill((0, 0, 0, 128))
  screen.blit(s, (0, 0))
  menu_w, menu_h = 300, 200
  menu_x, menu_y = WIDTH // 2 - menu_w // 2, HEIGHT // 2 - menu_h // 2
  pygame.draw.rect(screen, DARK_GREY, (menu_x, menu_y, menu_w, menu_h), 0, 10)
  pygame.draw.rect(screen, GREY, (menu_x, menu_y, menu_w, menu_h), 5, 10)
  screen.blit(big_font.render("Paused", True, WHITE), (menu_x + menu_w // 2 - big_font.render("Paused", True, WHITE).get_width() // 2, menu_y + 20))
  continue_btn = pygame.Rect(menu_x + 50, menu_y + 80, menu_w - 100, 40)
  main_menu_btn = pygame.Rect(menu_x + 50, menu_y + 140, menu_w - 100, 40)
  pygame.draw.rect(screen, BLUE, continue_btn)
  screen.blit(font.render("Continue", True, WHITE), (continue_btn.centerx - font.render("Continue", True, WHITE).get_width() // 2, continue_btn.centery - font.render("Continue", True, WHITE).get_height() // 2))
  pygame.draw.rect(screen, RED, main_menu_btn)
  screen.blit(font.render("Main Menu", True, WHITE), (main_menu_btn.centerx - font.render("Main Menu", True, WHITE).get_width() // 2, main_menu_btn.centery - font.render("Main Menu", True, WHITE).get_height() // 2))
  return continue_btn, main_menu_btn
def draw_console():
  console_height = 150
  pygame.draw.rect(screen, (0, 0, 0, 180), (0, HEIGHT - console_height, WIDTH, console_height))
  y_offset = HEIGHT - console_height + 5
  visible_history = console_history[console_scroll_offset:]
  for entry in visible_history[-MAX_CONSOLE_HISTORY_DISPLAY:]:
    text_surface = font.render(entry, True, WHITE)
    screen.blit(text_surface, (5, y_offset))
    y_offset += 20
  
  input_prompt = font.render(">", True, WHITE)
  input_text = font.render(console_input, True, WHITE)
  screen.blit(input_prompt, (5, HEIGHT - 25))
  screen.blit(input_text, (20, HEIGHT - 25))
def add_console_message(message):
  console_history.append(message)
  if len(console_history) > MAX_CONSOLE_HISTORY_DISPLAY:
    global console_scroll_offset
    console_scroll_offset = max(0, len(console_history) - MAX_CONSOLE_HISTORY_DISPLAY)
def toggle_console():
  global console_active, console_input, console_scroll_offset
  console_active = not console_active
  console_input = ""
  console_scroll_offset = max(0, len(console_history) - MAX_CONSOLE_HISTORY_DISPLAY)
def process_console_command(command):
  global money, base_hp, game_state, hidden_wave_active, hidden_wave_effect_timer, enemies
  global console_spawn_queue, console_spawn_timer, selected_loadout_types, null_tower_unlocked
  global hidden_wave_shake_boost_timer, final_boss_spawned
  add_console_message(f"> {command}")
  parts = command.lower().split()
  if not parts:
    add_console_message("Empty command. Valid commands: hd, spawn_enemy, set_cash, set_hp, unit")
    return
  command = parts[0]
  if command == "hd":
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
      valid_types = ["fast", "slow", "normal", "boss", "null"]
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
    add_console_message("Unknown command. Valid commands: hd, spawn_enemy, set_cash, set_hp, unit")
def is_valid_placement(x, y):
  if x < 0 or x > WIDTH or y < 0 or y > HEIGHT - 100: return False
  for tx, ty in [(p[0], p[1]) for p in path]:
    if math.hypot(x - tx, y - ty) < PATH_TOLERANCE + TOWER_PLACEMENT_DISTANCE: return False
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
  if console_active and console_spawn_queue:
    if console_spawn_timer <= 0:
      if console_spawn_queue:
        enemy_type_to_spawn = console_spawn_queue.pop(0)
        spawn_enemy_from_queue(enemy_type_to_spawn)
        console_spawn_timer = 30
    else:
      console_spawn_timer -= 1
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      running = False
    elif event.type == pygame.KEYDOWN:
      if event.key == pygame.K_F2:
        toggle_console()
      elif event.key == pygame.K_ESCAPE:
        if game_state == GAME_STATE_PLAYING:
          game_state = GAME_STATE_PAUSED
        elif game_state == GAME_STATE_PAUSED:
          game_state = GAME_STATE_PLAYING
      elif console_active:
        if event.key == pygame.K_RETURN:
          if console_input:
            process_console_command(console_input)
          console_input = ""
        elif event.key == pygame.K_BACKSPACE:
          console_input = console_input[:-1]
        elif event.key == pygame.K_UP:
          console_scroll_offset = max(0, console_scroll_offset - 1)
        elif event.key == pygame.K_DOWN:
          console_scroll_offset = min(len(console_history) - MAX_CONSOLE_HISTORY_DISPLAY, console_scroll_offset + 1)
        else:
          console_input += event.unicode
      elif event.key == pygame.K_e and selected_tower:
        if selected_tower.level < selected_tower.type.max_level and money >= selected_tower.upgrade_cost():
          money -= selected_tower.upgrade_cost()
          selected_tower.upgrade()
      elif event.key == pygame.K_x and selected_tower:
        money += selected_tower.sell_value()
        towers.remove(selected_tower)
        selected_tower = None
      elif event.key == pygame.K_r:
        reset_game_state()
        game_state = GAME_STATE_MAIN_MENU
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
        if placing_tower_type:
          if confirm_rect and confirm_rect.collidepoint(mx, my):
            if money >= placing_tower_type.base_cost and is_valid_placement(placing_pos[0], placing_pos[1]):
              towers.append(Tower(placing_pos[0], placing_pos[1], placing_tower_type))
              money -= placing_tower_type.base_cost
              placing_tower_type, placing_pos, confirm_rect = None, None, None
            else:
              print("Cannot place tower here or not enough money.")
          else:
            if is_valid_placement(mx, my):
              placing_pos = (mx, my)
              confirm_rect = pygame.Rect(mx + 20, my - 40, 30, 30)
            else:
              placing_tower_type, placing_pos, confirm_rect = None, None, None
        else:
          clicked_tower = get_tower_at_pos(mx, my)
          if clicked_tower:
            if selected_tower: selected_tower.selected = False
            selected_tower = clicked_tower
            selected_tower.selected = True
          else:
            if selected_tower: selected_tower.selected = False
            selected_tower = None
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
      screen.fill(WHITE)
    
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
        if enemy.name == "N.U.L.L" and not enemy.is_admin_clone:
          null_tower_unlocked = True
          add_console_message("N.U.L.L defeated! Null tower unlocked.")
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
        enemies_left_in_wave = 10 + wave_count * 2
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
      pygame.draw.rect(screen, DARK_GREY, (WIDTH // 2 - (WIDTH - 400) // 2 + current_shake_x, boss_health_bar_y + current_shake_y, WIDTH - 400, 30))
      pygame.draw.rect(screen, GREEN, (WIDTH // 2 - (WIDTH - 400) // 2 + current_shake_x, boss_health_bar_y + current_shake_y, int((boss_current_hp / boss_max_hp) * (WIDTH - 400)), 30))
      name_text = ".n.u.ul.l.404" if boss.name else "Boss"
      screen.blit(font.render(f"{name_text}: {int(boss_current_hp)} / {int(boss_max_hp)}", True, BLACK), (WIDTH // 2 - font.render(f"{name_text}: {int(boss_current_hp)} / {int(boss_max_hp)}", True, BLACK).get_width() // 2 + current_shake_x, boss_health_bar_y + 2 + current_shake_y))
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