import pygame
import math
import random
import sys
import json
import os

pygame.init()

SCREEN_W, SCREEN_H = 1920, 1080
FPS  = 60
TILE = 40

C_BG       = (18,22,30)
C_PATH     = (55,60,72)
C_WHITE    = (255,255,255)
C_BLACK    = (0,0,0)
C_RED      = (220,60,60)
C_GREEN    = (60,200,80)
C_GOLD     = (255,200,50)
C_CYAN     = (60,220,220)
C_ORANGE   = (255,140,40)
C_DARKGRAY = (40,45,55)
C_PANEL    = (25,30,42)
C_BORDER   = (70,80,110)
C_HP_BG    = (60,20,20)
C_HP_FG    = (220,60,60)
C_HP_FG2   = (60,200,80)
C_SLOT_BG  = (30,35,48)
C_SLOT_SEL = (60,80,130)
C_ASSASSIN = (180,80,255)
C_ACCEL    = (130,60,255)

CURRENT_MAP = "straight"  # "straight", "zigzag", or "frosty"

PATH_Y      = 432   # 288 * 1080/720
PATH_H      = 42    # 28  * 1080/720, rounded
SLOT_AREA_Y = SCREEN_H - 155  # slightly taller panel
SLOT_W, SLOT_H = 160, 140
MAX_WAVES   = 20

# Map waypoints — defined after PATH_Y
_ZIGZAG_PATH = [
    (  -45,  290),   # entry: left edge
    (  400,  290),   # turn: right→down
    (  400,  846),   # turn: down→right
    (  766,  846),   # turn: right→up
    (  766,  106),   # turn: up→right
    ( 1167,  106),   # turn: right→down
    ( 1167,  846),   # turn: down→right
    (SCREEN_W+60, 846),  # exit: right edge
]

# ── Frosty map: 4 paths from the 4 screen edges converging on the center ──────
# Center = (SCREEN_W//2, SCREEN_H//2 - 60)  (slightly above true center to avoid UI)
_FROSTY_CX = SCREEN_W // 2        # 960
_FROSTY_CY = SCREEN_H // 2 - 60   # 480

# Vertical arm travel distance: top → center = _FROSTY_CY + 45 = 525px
# We use the same distance for horizontal arms so all 4 lanes feel equal.
_FROSTY_ARM = _FROSTY_CY + 45   # 525px — arm length for all 4 paths

# Each path: [start_off_screen, center]
_FROSTY_PATHS = [
    # TOP  (enters from top-center, goes straight down)
    [(_FROSTY_CX,              -45),                      (_FROSTY_CX, _FROSTY_CY)],
    # BOTTOM (enters from bottom-center, goes straight up)
    [(_FROSTY_CX,              SCREEN_H+45),              (_FROSTY_CX, _FROSTY_CY)],
    # LEFT  (enters at same arm-distance from center)
    [(_FROSTY_CX - _FROSTY_ARM, _FROSTY_CY),             (_FROSTY_CX, _FROSTY_CY)],
    # RIGHT (enters at same arm-distance from center)
    [(_FROSTY_CX + _FROSTY_ARM, _FROSTY_CY),             (_FROSTY_CX, _FROSTY_CY)],
]

# ── Event map: S-образный путь с 3 поворотами ─────────────────────────────────
_EVENT_PATH = [
    (  -45,  200),           # вход: левый край (верхняя треть)
    (  480,  200),           # → вправо
    (  480,  540),           # ↓ вниз к центру
    (  960,  540),           # → вправо к середине экрана
    (  960,  320),           # ↑ вверх
    ( 1440,  320),           # → вправо
    ( 1440,  700),           # ↓ вниз
    (SCREEN_W+60, 700),      # выход: правый край (нижняя треть)
]

def get_map_path():
    if CURRENT_MAP == "zigzag":
        return _ZIGZAG_PATH
    if CURRENT_MAP == "frosty":
        return _FROSTY_PATHS[0]   # default; individual enemies carry their own path
    if CURRENT_MAP == "event":
        return _EVENT_PATH
    return [(-30, PATH_Y), (SCREEN_W+40, PATH_Y)]

def get_frosty_path(lane_index):
    """Return the path list for a specific Frosty lane (0-3)."""
    return _FROSTY_PATHS[lane_index % 4]

def spawn_enemy_at_start(e, offset_x=0):
    """Position enemy at path start with correct x/y and reset waypoint index."""
    path = get_map_path()
    e.x = float(path[0][0]) + offset_x
    e.y = float(path[0][1])
    e._wp_index = 1




font_sm = pygame.font.SysFont("consolas", 13)
font_md = pygame.font.SysFont("consolas", 15, bold=True)
font_lg = pygame.font.SysFont("consolas", 20, bold=True)
font_xl = pygame.font.SysFont("consolas", 26, bold=True)
font_ru = pygame.font.SysFont("segoeui", 18)
font_ru_lg = pygame.font.SysFont("segoeui", 22, bold=True)

SAVE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "savegame.json")
ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "achievements.json")

# Achievement definitions
ACHIEVEMENT_DEFS = [
    {"id": "first_path",        "name": "First Path",         "desc": "Beat Easy mode",                            "color": (80,200,80),   "border": (120,255,120)},
    {"id": "fallen_angel",      "name": "Fallen Angel",        "desc": "Beat Fallen mode",                          "color": (140,40,200),  "border": (200,80,255)},
    {"id": "frosty_clear",      "name": "Frosty Path",        "desc": "Beat Frosty mode",                          "color": (80,200,255),  "border": (140,240,255)},
    {"id": "glitch",            "name": "tH3 GL1tcH",          "desc": "Beat Hidden Wave. Unavailable",               "color": (0,200,255),   "border": (80,240,255)},
    {"id": "king_victim",       "name": "King's Victim",       "desc": "Lose to Fallen King on wave 40",     "color": (180,20,20),   "border": (255,60,60)},
    {"id": "true_end",          "name": "True Ending",      "desc": "Beat True Fallen",                           "color": (200,150,0),   "border": (255,210,50)},
    {"id": "free_pass",         "name": "Free Pass",     "desc": "Beat Easy without killing final boss",         "color": (60,160,220),  "border": (100,210,255)},
    {"id": "rich",              "name": "Rich",               "desc": "Have 5,000+ coins at once",         "color": (200,160,20),  "border": (255,220,60)},
    # New achievements
    {"id": "frosty_perfect",    "name": "Ice Fortress",    "desc": "Beat Frosty with no HP loss",       "color": (140,240,255), "border": (200,255,255)},
    {"id": "endless_10",        "name": "Steadfast",             "desc": "Survive 10 Endless waves",            "color": (100,100,220), "border": (160,160,255)},
    {"id": "endless_100",       "name": "Unstoppable",         "desc": "Survive 100 Endless waves",           "color": (80,60,220),   "border": (140,120,255)},
    {"id": "endless_1000",      "name": "Legend",             "desc": "Survive 1000 Endless waves",          "color": (60,20,200),   "border": (120,80,255)},
    {"id": "last_stand",        "name": "Last Stand",     "desc": "Beat any mode with 1 HP left",        "color": (220,60,60),   "border": (255,120,80)},
    {"id": "collector_10",      "name": "Collector",        "desc": "Unlock 10+ units",             "color": (80,200,120),  "border": (120,255,160)},
    {"id": "collector_20",      "name": "Collection Master",    "desc": "Unlock 20+ units",             "color": (60,180,100),  "border": (100,240,140)},
    {"id": "millionaire",       "name": "Millionaire",           "desc": "Have 100,000+ coins",                  "color": (255,200,40),  "border": (255,240,100)},
    {"id": "shard_500",         "name": "Sparkling",           "desc": "Gather 500 shards",                        "color": (100,200,255), "border": (180,240,255)},
    {"id": "shard_1000",        "name": "Crystal",         "desc": "Gather 1000 shards",                       "color": (60,160,255),  "border": (140,220,255)},
    {"id": "april_fools_2026", "name": "April Fools 2026",    "desc": "Beat April Fools 2026",                "color": (255, 80, 120), "border": (255, 160, 200)},
    # ── New achievements ──────────────────────────────────────────────────────
    {"id": "has_skin",         "name": "Stylist",              "desc": "Own at least 1 skin",                        "color": (200, 100, 220),"border": (230, 160, 255)},
    {"id": "naked_run",        "name": "Lightweight",              "desc": "Start game with no units equipped",            "color": (120, 120, 120),"border": (180, 180, 180)},
    {"id": "fallen_duo",       "name": "Duo",                 "desc": "Beat Fallen with max 2 units",          "color": (180, 60, 255), "border": (210, 120, 255)},
    {"id": "grand_slam",       "name": "Grand Slam",           "desc": "Beat Easy->Fallen->Frosty->Hardcore in a row", "color": (255, 200, 0), "border": (255, 240, 80)},
    # ── Batch 2 achievements ──────────────────────────────────────────────────
    {"id": "capitalist",       "name": "Capitalist",           "desc": "Build 8 Farms all upgraded to max level",     "color": (80, 180, 60),  "border": (140, 255, 100)},
    {"id": "overkill",         "name": "Overkill",             "desc": "Apply Freeze, Burn and Armor Shred to one boss at once", "color": (180, 60, 220), "border": (220, 120, 255)},
    {"id": "moonwalk",         "name": "Moonwalk",             "desc": "Have 15 enemies walking in reverse simultaneously", "color": (80, 160, 255), "border": (140, 210, 255)},
    {"id": "why",              "name": "Why",                  "desc": "Do nothing for 1 hour",                       "color": (60, 60, 80),   "border": (100, 100, 140)},
    {"id": "gold_rush",        "name": "Gold Rush",            "desc": "Earn $10,000 in one game using only Cowboys",  "color": (220, 170, 20), "border": (255, 230, 80)},
    {"id": "hacker",           "name": "Hacker",               "desc": "Open the admin panel in Sandbox mode",        "color": (40, 200, 120), "border": (80, 255, 180)},
    {"id": "no_refunds",       "name": "No Refunds",           "desc": "Beat Fallen without selling any tower",       "color": (200, 80, 60),  "border": (255, 130, 100)},
    {"id": "absolute_zero",    "name": "Absolute Zero",        "desc": "Keep a boss frozen for 15 seconds straight",  "color": (140, 220, 255),"border": (200, 250, 255)},
    {"id": "speedrunner",      "name": "Speedrunner",          "desc": "Beat Fallen with Auto-skip on all game",      "color": (255, 140, 40), "border": (255, 200, 100)},
]

def load_achievements():
    if os.path.exists(ACHIEVEMENTS_FILE):
        try:
            with open(ACHIEVEMENTS_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"unlocked": []}

def grant_achievement(ach_id):
    data = load_achievements()
    if ach_id in data.get("unlocked", []):
        return False
    data.setdefault("unlocked", []).append(ach_id)
    try:
        with open(ACHIEVEMENTS_FILE, "w") as f:
            json.dump(data, f)
    except: pass
    return True

# ── Icon loading ───────────────────────────────────────────────────────────────
_ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "image")
_icon_cache = {}

def load_icon(name, size):
    """Load icon from assets/image/<name>.png, scale to size. Returns Surface or None."""
    key = (name, size)
    if key in _icon_cache:
        return _icon_cache[key]
    path = os.path.join(_ICON_DIR, f"{name}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (size, size))
        _icon_cache[key] = img
        return img
    except Exception:
        _icon_cache[key] = None
        return None


# Rarity definitions: name, base color, shimmer color, border color
RARITY_DATA = {
    "starter":   {"label":"STARTER",   "color":(70,70,80),    "border":(120,120,130), "shimmer":None,             "text_col":(180,180,190)},
    "common":    {"label":"COMMON",    "color":(50,80,50),    "border":(80,140,80),   "shimmer":None,             "text_col":(140,220,140)},
    "rare":      {"label":"RARE",      "color":(30,50,120),   "border":(80,120,255),  "shimmer":(100,150,255),    "text_col":(120,180,255)},
    "epic":      {"label":"EPIC",      "color":(80,20,120),   "border":(180,60,255),  "shimmer":None,             "text_col":(200,120,255)},
    "exclusive": {"label":"EXCLUSIVE", "color":(50,10,90),    "border":(200,50,255),  "shimmer":(255,160,255),    "text_col":(255,180,255)},
    "mythic":    {"label":"MYTHIC",    "color":(80,60,0),     "border":(255,200,0),   "shimmer":(255,240,100),    "text_col":(255,220,60)},
}

# Unit rarity assignments
# Unit placement limits (max on field at once), None = unlimited
UNIT_LIMITS = {
    "Assassin":       5,
    "Accelerator":    5,
    "Frostcelerator": 1,
    "xw5yt":          1,
    "Lifestealer":    4,
    "Archer":         4,
    "ArcherOld":      4,
    "Red Ball":       4,
    "Farm":           8,
    "Freezer":        6,
    "Frost Blaster":  6,
    "Sledger":        6,
    "Gladiator":      4,
    "Toxic Gunner":   3,
    "Slasher":        3,
    "Golden Cowboy":  6,   # legacy save compat
    "Cowboy":         6,
    "Hallow Punk":    10,
    "Spotlight Tech": 1,
    "Commander":      3,
    "Snowballer":     4,
    "Commando":       4,
    "hacker_laser_effects_test": 1,
    "Caster":         3,
    "Warlock":        4,
    "Jester":         8,
    "Rubber Duck":    5,
}

def load_save():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE,"r") as f:
                return json.load(f)
        except: pass
    return {"frostcelerator_unlocked": False, "loadout": ["Assassin", None, None, None, None], "coins": 0, "owned_units": ["Assassin"], "xw5yt_unlocked": False, "shards": 0}

def write_save(data):
    try:
        with open(SAVE_FILE,"w") as f:
            json.dump(data, f)
    except: pass


# Compact number display toggle (1000 → 1k). Toggled from SETTINGS in game.py
_COMPACT_NUMBERS = True

def fmt_num(n):
    """Format a number as compact string up to sextillions (only when compact_numbers enabled).
    Examples: 1k, 1.5k, 10k, 1M, 2.5B, 1T, 1Qa, 1Qi, 1Sx"""
    n = int(n)
    # Check global setting — default True (compact on)
    try:
        from game_core import _COMPACT_NUMBERS
        compact = _COMPACT_NUMBERS
    except Exception:
        compact = True
    if not compact:
        return str(n)
    _STEPS = [
        (10**21, "Sx"),   # sextillion
        (10**18, "Qi"),   # quintillion
        (10**15, "Qa"),   # quadrillion
        (10**12, "T"),    # trillion
        (10**9,  "B"),    # billion
        (10**6,  "M"),    # million
        (10**3,  "k"),    # thousand
    ]
    for threshold, suffix in _STEPS:
        if n >= threshold:
            v = n / threshold
            # 1 decimal only for values < 10, integers otherwise
            if v >= 10:
                s = str(int(round(v)))
            else:
                rounded = round(v, 1)
                s = str(int(rounded)) if rounded == int(rounded) else f"{rounded:.1f}"
            return s + suffix
    return str(n)

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def path_progress(e):
    """
    Возвращает расстояние, пройденное врагом по пути от старта.
    Чем больше значение — тем ближе враг к финишу.
    Корректно работает на зигзаг/петлях/frosty-картах.
    """
    path = getattr(e, '_frosty_path', None) or get_map_path()
    wp = e._wp_index  # индекс СЛЕДУЮЩЕГО вейпоинта

    # Суммируем длины всех уже пройденных отрезков пути
    total = 0.0
    for i in range(1, min(wp, len(path))):
        px0, py0 = path[i - 1]
        px1, py1 = path[i]
        total += math.hypot(px1 - px0, py1 - py0)

    # Добавляем дистанцию от предыдущего вейпоинта до текущей позиции врага
    if 1 <= wp <= len(path):
        px0, py0 = path[wp - 1]
        total += math.hypot(e.x - px0, e.y - py0)

    return total

def txt(surf, text, pos, color=C_WHITE, f=font_md, center=False, right=False):
    s = f.render(str(text), True, color)
    r = s.get_rect()
    if center: r.center = pos
    elif right: r.right, r.centery = pos[0], pos[1]
    else: r.topleft = pos
    surf.blit(s, r)
    return r

def draw_rect_alpha(surf, color, rect, alpha=120, brad=0):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color[:3], alpha), (0,0,rect[2],rect[3]), border_radius=brad)
    surf.blit(s, (rect[0], rect[1]))

# ── Visual Effects ─────────────────────────────────────────────────────────────
class SwordEffect:
    def __init__(self, ox, oy, angle):
        self.ox=ox; self.oy=oy; self.angle=angle
        self.life=0.22; self.t=0.0; self.length=38
    def update(self, dt): self.t+=dt; return self.t<self.life
    def draw(self, surf):
        progress=self.t/self.life; alpha=int(255*(1-progress)); sweep=60*progress
        s=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        for i in range(8):
            a=math.radians(self.angle-sweep*(i/7))
            ex=self.ox+math.cos(a)*self.length; ey=self.oy+math.sin(a)*self.length
            pygame.draw.line(s,(200,200,255,max(0,alpha-i*36)),
                             (int(self.ox),int(self.oy)),(int(ex),int(ey)),3)
        surf.blit(s,(0,0))

class WhirlwindEffect:
    def __init__(self, ox, oy, radius):
        self.ox=ox; self.oy=oy; self.radius=radius
        self.life=1.0; self.t=0.0; self.spin=0.0
    def update(self, dt): self.t+=dt; self.spin+=dt*720; return self.t<self.life
    def draw(self, surf):
        progress=self.t/self.life; alpha=int(200*(1-progress))
        s=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        for i in range(6):
            base_a=math.radians(self.spin+i*60)
            for j in range(5):
                a=base_a+math.radians(j*8); r1=10+j*4; r2=r1+36*(1-progress*0.5)
                sx2=self.ox+math.cos(a)*r1; sy2=self.oy+math.sin(a)*r1
                ex=self.ox+math.cos(a)*r2; ey=self.oy+math.sin(a)*r2
                pygame.draw.line(s,(200,200,255,max(0,alpha-j*43)),
                                 (int(sx2),int(sy2)),(int(ex),int(ey)),3-min(2,j//2))
        pygame.draw.circle(s,(160,160,255,max(0,alpha//2)),
                           (int(self.ox),int(self.oy)),int(self.radius*TILE),2)
        surf.blit(s,(0,0))

class FloatingText:
    """Floating +money text that rises and fades on enemy kill."""
    def __init__(self, x, y, text, color=(255,255,255)):
        self.x=float(x); self.y=float(y)
        self.text=text; self.color=color
        self.life=1.1; self.t=0.0
    def update(self, dt):
        self.t+=dt; self.y-=28*dt
        return self.t<self.life
    def draw(self, surf):
        alpha=int(255*(1-self.t/self.life))
        s=font_md.render(self.text,True,self.color)
        s.set_alpha(max(0,alpha))
        surf.blit(s,s.get_rect(center=(int(self.x),int(self.y))))

class BloodSlashEffect:
    """Red slashing arc with blood splatter particles for Slasher."""
    def __init__(self, ox, oy, angle, is_crit=False):
        self.ox=ox; self.oy=oy; self.angle=angle
        self.is_crit=is_crit
        self.life=0.32 if not is_crit else 0.52
        self.t=0.0
        self.length=48 if not is_crit else 70
        # spawn blood particles
        self.particles=[]
        n = 8 if not is_crit else 18
        for _ in range(n):
            a=math.radians(angle)+random.uniform(-0.9,0.9)
            spd=random.uniform(60,180)
            self.particles.append([float(ox),float(oy),
                                    math.cos(a)*spd, math.sin(a)*spd,
                                    random.uniform(0.25,self.life)])
    def update(self, dt):
        self.t+=dt
        for p in self.particles:
            p[0]+=p[2]*dt; p[1]+=p[3]*dt
            p[3]+=120*dt   # gravity
        return self.t<self.life
    def draw(self, surf):
        progress=self.t/self.life
        alpha=int(255*(1-progress))
        s=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        # slash arcs
        sweep=70*progress; n_lines=10 if self.is_crit else 6
        base_col=(255,30,30) if self.is_crit else (200,30,30)
        for i in range(n_lines):
            a=math.radians(self.angle - sweep/2 + sweep*(i/(n_lines-1)))
            ex=self.ox+math.cos(a)*self.length*(0.6+0.4*(i/(n_lines-1)))
            ey=self.oy+math.sin(a)*self.length*(0.6+0.4*(i/(n_lines-1)))
            fade=max(0,alpha-i*22)
            w=4 if self.is_crit else 3
            pygame.draw.line(s,(*base_col,fade),(int(self.ox),int(self.oy)),(int(ex),int(ey)),w)
        # crit flash ring
        if self.is_crit and progress<0.4:
            ring_alpha=int(200*(1-progress/0.4))
            ring_r=int(self.length*(0.3+progress*0.7))
            pygame.draw.circle(s,(255,60,60,ring_alpha),(int(self.ox),int(self.oy)),ring_r,3)
        surf.blit(s,(0,0))
        # blood particles
        for p in self.particles:
            life_left=p[4]-self.t
            if life_left<=0: continue
            pa=max(0,int(200*(life_left/p[4])))
            ps=pygame.Surface((8,8),pygame.SRCALPHA)
            r=max(1,int(3*(life_left/p[4])))
            pygame.draw.circle(ps,(200,20,20,pa),(4,4),r)
            surf.blit(ps,(int(p[0])-4,int(p[1])-4))

# ── Enemy base ─────────────────────────────────────────────────────────────────
SETTINGS = {
    "colored_range": False,
    "sfx_volume":    0.7,
    "sfx_muted":     False,
    "show_fps":      False,
    "screen_shake":  True,
    "particles":     True,
    "show_damage":   True,
}

# ── Skill Tree global multipliers (set by Game.__init__ from save_data) ──────
# Fight Dirty: debuff durations multiplier (1.0 = no bonus)
DEBUFF_MULT = 1.0
# Enhanced Optics: range multiplier (applied at placement, not here)
# AoE radius multiplier for Improved Gunpowder
AOE_MULT = 1.0