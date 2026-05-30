import pygame
import math
import random
import sys
import json
import os

pygame.init()

# ── Global font cache — avoids recreating SysFont every frame ─────────────────
_FONT_CACHE: dict = {}
def _f(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    key = (name, size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(name, size, bold=bold)
    return _FONT_CACHE[key]
# Monkey-patch so existing SysFont calls go through cache automatically
_orig_SysFont = pygame.font.SysFont
def _cached_SysFont(name, size, bold=False, italic=False):
    key = (name, size, bool(bold), bool(italic))
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = _orig_SysFont(name, size, bold=bold, italic=italic)
    return _FONT_CACHE[key]
pygame.font.SysFont = _cached_SysFont

# ── Reusable fullscreen overlay surface (avoid per-frame alloc) ────────────────
_DIM_SURF: pygame.Surface | None = None
def _get_dim_surf() -> pygame.Surface:
    global _DIM_SURF
    if _DIM_SURF is None or _DIM_SURF.get_size() != (SCREEN_W if 'SCREEN_W' in dir() else 1920, SCREEN_H if 'SCREEN_H' in dir() else 1080):
        from game_core import SCREEN_W as _SW, SCREEN_H as _SH
        _DIM_SURF = pygame.Surface((_SW, _SH), pygame.SRCALPHA)
    return _DIM_SURF# Map/path constants live in assets/game_core.py — add assets/ to path first
_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
if _ASSETS_DIR not in sys.path:
    sys.path.insert(0, _ASSETS_DIR)
import game_core  # needed to update game_core.CURRENT_MAP in the shared module
_game_core = game_core  # alias expected by multiplayer.py
from game_core import (
    SCREEN_W, SCREEN_H, FPS, TILE,
    PATH_Y, PATH_H, SLOT_AREA_Y, SLOT_W, SLOT_H, MAX_WAVES,
    C_BG, C_PATH, C_WHITE, C_BLACK, C_RED, C_GREEN, C_GOLD, C_CYAN,
    C_ORANGE, C_DARKGRAY, C_PANEL, C_BORDER, C_HP_BG, C_HP_FG, C_HP_FG2,
    C_SLOT_BG, C_SLOT_SEL, C_ASSASSIN, C_ACCEL,
    get_map_path, get_frosty_path, spawn_enemy_at_start, CURRENT_MAP,
    font_sm, font_md, font_lg, font_xl, font_ru, font_ru_lg,
    SAVE_FILE, load_icon, RARITY_DATA, UNIT_LIMITS,
    load_save, write_save, dist, txt, draw_rect_alpha,
    SwordEffect, WhirlwindEffect, FloatingText, BloodSlashEffect,
    ACHIEVEMENTS_FILE, ACHIEVEMENT_DEFS, load_achievements, grant_achievement,
    fmt_num,
)

# ── Unit limit overrides (applied on top of game_core defaults) ────────────────
UNIT_LIMITS["Archer"]      = 8   # increased from default (was 6)
UNIT_LIMITS["Militant"]    = 6   # new starter unit
UNIT_LIMITS["Swarmer"]     = 14
UNIT_LIMITS["Harvester"]   = 5   # placement limit per player
UNIT_LIMITS["ToxicGunner"] = 5
UNIT_LIMITS["Gladiator"]   = 6
UNIT_LIMITS["Twitgunner"]  = 6
UNIT_LIMITS["Korzhik"]     = 6
UNIT_LIMITS["Conduit"]    = 3

UNIT_LIMITS["ControlPanel"] = 1
UNIT_LIMITS["Castbound"]   = 5

GLOBAL_UNIT_LIMIT = 40   # max total towers per match

# ── Patch early_access rarity into RARITY_DATA (from game_core) ───────────────
RARITY_DATA.setdefault("early_access", {
    "color":    (20,  80,  65),
    "border":   (60, 220, 180),
    "label":    "Early Access",
    "text_col": (60, 220, 180),
    "shimmer":  (120, 255, 220),
})

# ── Patch apex rarity into RARITY_DATA (replaces mythic) ──────────────────────
RARITY_DATA["apex"] = {
    "color":    (80,  20,  10),
    "border":   (255, 120,  20),
    "label":    "Apex",
    "text_col": (255, 180,  40),
    "shimmer":  (255, 220, 100),
}

RARITY_DATA["singularity"] = {
    "label":    "SINGULARITY",
    "color":    (0, 0, 0),
    "border":   (180, 0, 255),
    "shimmer":  (220, 80, 255),
    "text_col": (0, 0, 0),
}

# ── Daily Quest System ────────────────────────────────────────────────────────
import datetime as _dt
import hashlib  as _hashlib

# All possible daily quest definitions
# Each has: id, title, desc, type, target, reward_coins, reward_shards
_DAILY_QUEST_POOL = [
    # Win-based quests
    {"id":"dq_win_easy",    "title":"Easy Victory",      "desc":"Win 1 game on Easy difficulty.",        "type":"win_mode",   "mode":"easy",    "target":1, "coins":200,  "shards":0},
    {"id":"dq_win2_easy",   "title":"Double Easy",       "desc":"Win 2 games on Easy difficulty.",       "type":"win_mode",   "mode":"easy",    "target":2, "coins":350,  "shards":0},
    {"id":"dq_win_fallen",  "title":"Fallen Victor",     "desc":"Win 1 game on Fallen difficulty.",      "type":"win_mode",   "mode":"fallen",  "target":1, "coins":300,  "shards":5},
    {"id":"dq_win_frosty",  "title":"Frost Conqueror",   "desc":"Win 1 game on Frosty difficulty.",      "type":"win_mode",   "mode":"frosty",  "target":1, "coins":400,  "shards":8},
    {"id":"dq_win_infernal","title":"Infernal Run",      "desc":"Win 1 game on Infernal difficulty.",    "type":"win_mode",   "mode":"infernal","target":1, "coins":500,  "shards":12},
    # Kill-based quests
    {"id":"dq_kills_100",   "title":"Pest Control",      "desc":"Kill 100 enemies in any game.",         "type":"kills",      "target":100, "coins":150,  "shards":0},
    {"id":"dq_kills_300",   "title":"Slaughter",         "desc":"Kill 300 enemies in any game.",         "type":"kills",      "target":300, "coins":300,  "shards":3},
    {"id":"dq_kills_500",   "title":"Massacre",          "desc":"Kill 500 enemies in any game.",         "type":"kills",      "target":500, "coins":500,  "shards":6},
    # Wave-based quests
    {"id":"dq_waves_5",     "title":"Survivor",          "desc":"Survive 5 waves in a single game.",     "type":"waves",      "target":5,  "coins":120,  "shards":0},
    {"id":"dq_waves_10",    "title":"Veteran",           "desc":"Survive 10 waves in a single game.",    "type":"waves",      "target":10, "coins":250,  "shards":4},
    {"id":"dq_waves_15",    "title":"War Machine",       "desc":"Survive 15 waves in a single game.",    "type":"waves",      "target":15, "coins":450,  "shards":8},
    # Coin-earn quests
    {"id":"dq_earn_2000",   "title":"Early Investor",    "desc":"Earn 2 000 coins in one game.",         "type":"earn_coins", "target":2000,  "coins":150,  "shards":0},
    {"id":"dq_earn_5000",   "title":"Capitalist",        "desc":"Earn 5 000 coins in one game.",         "type":"earn_coins", "target":5000,  "coins":250,  "shards":3},
    {"id":"dq_earn_10000",  "title":"Tycoon",            "desc":"Earn 10 000 coins in one game.",        "type":"earn_coins", "target":10000, "coins":500,  "shards":6},
    # Place-towers quests
    {"id":"dq_place_5",     "title":"Builder",           "desc":"Place 5 towers in one game.",           "type":"towers_placed","target":5,  "coins":100,  "shards":0},
    {"id":"dq_place_15",    "title":"Army Builder",      "desc":"Place 15 towers in one game.",          "type":"towers_placed","target":15, "coins":220,  "shards":3},
    # No-leak quests
    {"id":"dq_no_leak",     "title":"Flawless",          "desc":"Win a game without letting any enemy through.",  "type":"no_leak_win","target":1, "coins":600, "shards":10},
    # Hardcore/fallen special
    {"id":"dq_hardcore_any","title":"Hardcore Attempt",  "desc":"Reach wave 10 in Hardcore mode.",       "type":"waves_mode", "mode":"hardcore","target":10,"coins":500,"shards":12},
]

_DRAFT_CARDS = [
    {"id": "remove_tower", "title": "Sacrifice", "desc": "Удалить рандомную башню"},
    {"id": "range_down", "title": "Myopia", "desc": "Дальность всех башен -20% на 5 волн"},
    {"id": "upgrade_cost", "title": "Inflation", "desc": "Цена на апгрейды +15%"},
    {"id": "half_money", "title": "Taxes", "desc": "Деньги делятся на 2"},
    {"id": "level_down", "title": "Amnesia", "desc": "Рандомная башня теряет 1 уровень"},
    {"id": "damage_down", "title": "Weakness", "desc": "Урон всех башен -50% на 5 волн"},
    {"id": "firerate_down", "title": "Lethargy", "desc": "Фаеррейт -20%"},
    {"id": "rollback", "title": "Time Loop", "desc": "Откат на 3 волны назад"},
    {"id": "zero_money", "title": "Bankruptcy", "desc": "Списывает деньги до нуля"},
    {"id": "damage_5", "title": "Nerf Gun", "desc": "Урон 5 всем башням на 15 секунд"},
    {"id": "all_jesters", "title": "Circus", "desc": "Все башни заменяются на Jester 1 лвла навсегда"},
]

_DAILY_COUNT = 3  # how many quests to pick per day

def _get_today_str():
    return _dt.date.today().isoformat()

def _pick_daily_quests(date_str=None):
    """Pick 3 quests for a given date deterministically."""
    if date_str is None:
        date_str = _get_today_str()
    seed_bytes = _hashlib.md5(date_str.encode()).digest()
    seed_int   = int.from_bytes(seed_bytes, "big")
    import random as _rand
    rng = _rand.Random(seed_int)
    pool = list(_DAILY_QUEST_POOL)
    rng.shuffle(pool)
    return pool[:_DAILY_COUNT]

def _load_daily_quests(save_data):
    """Return (today_str, quests, progress, claimed) — reset if date changed."""
    today = _get_today_str()
    dq    = save_data.get("daily_quests", {})
    if dq.get("date") != today:
        # New day — reset
        quests = _pick_daily_quests(today)
        dq = {
            "date":     today,
            "quests":   [q["id"] for q in quests],
            "progress": {q["id"]: 0 for q in quests},
            "claimed":  [],
        }
        save_data["daily_quests"] = dq
        write_save(save_data)
    # Rebuild full quest defs from ids
    _id_map = {q["id"]: q for q in _DAILY_QUEST_POOL}
    quests  = [_id_map[qid] for qid in dq.get("quests", []) if qid in _id_map]
    return today, quests, dq.get("progress", {}), dq.get("claimed", [])

def _claim_daily_reward(save_data, quest_id):
    """Mark quest as claimed and add rewards. Returns True if successful."""
    today, quests, progress, claimed = _load_daily_quests(save_data)
    if quest_id in claimed:
        return False
    _id_map = {q["id"]: q for q in _DAILY_QUEST_POOL}
    q = _id_map.get(quest_id)
    if q is None:
        return False
    # Check quest is complete
    if progress.get(quest_id, 0) < q["target"]:
        return False
    # Give rewards
    save_data["coins"]  = save_data.get("coins",  0) + q["coins"]
    save_data["shards"] = save_data.get("shards", 0) + q["shards"]
    dq = save_data.setdefault("daily_quests", {})
    cl = list(dq.get("claimed", []))
    cl.append(quest_id)
    dq["claimed"] = cl
    write_save(save_data)
    return True




# fonts imported from game_core

# ── New map path definitions ──────────────────────────────────────────────────
# U-Turn: left→right (top lane), turn down, right→left (mid lane), turn down, left→right (bottom lane)
_UTURN_PATH = [
    (-45, 180),
    (1760, 180),
    (1760, 460),
    (160,  460),
    (160,  740),
    (1920, 740),
]

# Labyrinth: tight 4-row zigzag with short horizontal segments
_LABYRINTH_PATH = [
    (-45,  150),
    (640,  150),
    (640,  340),
    (160,  340),
    (160,  530),
    (1760, 530),
    (1760, 720),
    (1920, 720),
]


# Monkey-patch game_core.get_map_path to support new maps
_orig_get_map_path = game_core.get_map_path
def _patched_get_map_path():
    cm = game_core.CURRENT_MAP
    if cm == "uturn":
        return _UTURN_PATH
    if cm == "labyrinth":
        return _LABYRINTH_PATH
    return _orig_get_map_path()
game_core.get_map_path = _patched_get_map_path
get_map_path = _patched_get_map_path  # update local name too
# Also patch inside game_core's own namespace so spawn_enemy_at_start picks it up
import sys as _sys_patch
if "game_core" in _sys_patch.modules:
    _sys_patch.modules["game_core"].get_map_path = _patched_get_map_path


# ── Icon loading ───────────────────────────────────────────────────────────────
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "image")
_icon_cache = {}


# Rarity definitions: name, base color, shimmer color, border color

# Unit rarity assignments





# ── Enemy base ─────────────────────────────────────────────────────────────────
# ── Enemies and units loaded from separate files ──────────────────────────────
import importlib.util as _ilu
import sys as _sys

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
if _ASSETS not in _sys.path:
    _sys.path.insert(0, _ASSETS)

def _load_local(name):
    _path = os.path.join(_ASSETS, name + ".py")
    spec = _ilu.spec_from_file_location(name, _path)
    mod  = _ilu.module_from_spec(spec)
    _sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_enemies_mod = _load_local("enemies")
_units_mod   = _load_local("units")

# Re-export everything so the rest of game.py can use names directly
from enemies import (
    Enemy, TankEnemy, ScoutEnemy, NormalBoss, HiddenEnemy, BreakerEnemy,
    ArmoredEnemy, SlowBoss, HiddenBoss, Necromancer, GraveDigger, FastBoss,
    OtchimusPrime, BounceCircle,
    AbnormalEnemy, QuickEnemy, SkeletonEnemy,
    HeftyEnemy, InvisibleEnemy, MysteryEnemy, MegaSlowEnemy,
    MYSTERY_SPAWN_POOL,
    FallenDreg, FallenSquire, FallenSoul, FallenEnemy, FallenGiant, FallenHazmat,
    PossessedArmorInner, PossessedArmor, FallenNecromancer, CorruptedFallen,
    FallenJester, NecroticSkeleton, FallenBreaker, FallenRusher, FallenReaper, FallenHonorGuard,
    FallenShield, FallenHero, FallenKing,

    FallenGuardianEnemy,
    WAVE_DATA, FALLEN_WAVE_DATA, FALLEN_MAX_WAVES,
    HARDCORE_WAVE_DATA, HARDCORE_MAX_WAVES,
    BREAKER_POOL, FALLEN_BREAKER_POOL,
    WaveManager,
    # Frosty enemies
    FrozenEnemy, SnowyEnemy, PackedIceEnemy, SnowMinion, FrostMystery,
    Frostmite, ColdMist, Permafrost, FrostHunter, UnstableIce,
    FrostWraith, FrostAcolyte,
    FrostUndead, FrostInvader, MegaFrostMystery, FrostRavager,
    TricksterElf, Yeti, FrostMage, FrostHero, DeepFreeze, FrostNecromancer, FrostSpirit,
    FROST_MYSTERY_POOL_SNOWY, FROST_MYSTERY_POOL_FROZEN,
    FROSTY_WAVE_DATA, FROSTY_MAX_WAVES,
)

# ── Infernal mode enemies ──────────────────────────────────────────────────────
try:
    from infernal_enemies import (
        Wolf, SpeedyWolf, Snowball, SnowCorpse,
        Ember, Furnace,
        Untouchable, SpecterEnemy, FateCollector, Stomp,
        InfernalMystery, InfernalStone,
        Terpila, Putana, Silyach, Confusilionale, Wheelchair, BlackSquare,
        FallenChester, FastFallenChester, TowerDestroyer,
        GrandpaEnemy, GrandmaEnemy, Kolobok,
        INFERNAL_WAVE_DATA, INFERNAL_MAX_WAVES,
        CHALLENGER_WAVE_DATA, CHALLENGER_MAX_WAVES,
        CHALLENGER_WAVE6_HP_DAMAGE,
    )
    _INFERNAL_AVAILABLE = True
except ImportError:
    _INFERNAL_AVAILABLE = False
from units import (
    WhirlwindAbility, Unit, TARGET_MODES,
    Assassin, ASSASSIN_LEVELS,
    Accelerator, ACCEL_LEVELS,
    Frostcelerator, FROST_LEVELS,
    LifestealerBullet, Lifestealer, LIFESTEALER_LEVELS,
    ArcherArrow, Archer, ARCHER_LEVELS,
    Farm, FARM_LEVELS,
    RedBall, REDBALL_LEVELS,
    Freezer, FREEZER_LEVELS,
    FreezerBullet,
    FrostBlaster, FrostBlasterBullet, FROSTBLASTER_LEVELS,
    C_FROSTBLASTER, C_FROSTBLASTER_DARK,
    Sledger, SLEDGER_LEVELS,
    C_SLEDGER, C_SLEDGER_DARK,
    Gladiator, GLADIATOR_LEVELS,
    C_GLADIATOR, C_GLADIATOR_DARK,
    ToxicGunner, ToxicGunnerBullet, TOXICGUN_LEVELS,
    C_TOXICGUN, C_TOXICGUN_DARK, C_TOXICGUN_ACID, C_TOXICGUN_GLOW,
    Slasher, SLASHER_LEVELS,
    C_SLASHER, C_SLASHER_DARK,
    GoldenCowboy, GCOWBOY_LEVELS,
    C_GCOWBOY, C_GCOWBOY_DARK, C_GCOWBOY_STAR, C_GCOWBOY_BRIM,
    HallowPunk, HallowPunkRocket, HALLOWPUNK_LEVELS,
    C_HALLOWPUNK, C_HALLOWPUNK_DARK,
    SpotlightTech, SPOTLIGHTTECH_LEVELS,
    C_SPOTLIGHT, C_SPOTLIGHT_DARK,
    C_FREEZER, C_FREEZER_DARK,

    Snowballer, SNOWBALLER_LEVELS,
    SNOWBALLER_LEVEL_NAMES,
    C_SNOWBALLER, C_SNOWBALLER_DARK,
    Commando, COMMANDO_LEVELS,
    C_COMMANDO, C_COMMANDO_DARK,
    Caster, C_HACKER, C_HACKER_DARK, CASTER_LEVELS, LIGHTNING_THRESHOLD,
    HackerLaserTest, LIGHTNING_DAMAGE,
    Warlock, WarlockUnit, C_WARLOCK, C_WARLOCK_DARK, WARLOCK_LEVELS,
    Jester, JESTER_LEVELS, C_JESTER, C_JESTER_DARK,
    SoulWeaver, C_SOULWEAVER, C_SOULWEAVER_DARK, _SW_LEVELS, _SW_SURGE_PARAMS, _sw_tick_buffs,
    SPAWN_MAP, CONSOLE_HELP,
    C_LIFESTEALER, C_LIFESTEALER_DARK,
    C_FROST, C_FROST_DARK, C_FROST_ICE,
    C_ARCHER, C_ARCHER_DARK,
    C_FARM, C_FARM_DARK, C_REDBALL, C_REDBALL_DARK,
    RubberDuck, RubberDuckProjectile, DUCK_LEVELS, DUCK_LEVEL_NAMES, C_DUCK, C_DUCK_DARK,
    Militant, MILITANT_LEVELS, C_MILITANT, C_MILITANT_DARK,
    Swarmer, SWARMER_LEVELS, C_SWARMER, C_SWARMER_DARK,
    Harvester, HARVESTER_LEVELS, C_HARVESTER, C_HARVESTER_DARK,
    ThornsAbility,
    Twitgunner, TWITGUN_LEVELS, C_TWITGUN, C_TWITGUN_DARK,
    Felyne, FELYNE_LEVELS, C_FELYNE, C_FELYNE_DARK,
    Conduit, CONDUIT_LEVELS, C_CONDUIT, C_CONDUIT_DARK,
    ControlPanel, C_CTRLPANEL, C_CTRLPANEL_DARK, RemoteControlAbility, _CP_BUFF_DEFS, _CP_ABILITY_CD,
    Castbound, CASTBOUND_LEVELS, C_CASTBOUND, C_CASTBOUND_DARK,
    CB_BLADE_DEFS, _cb_load_icon,
    C_CB_ZENITH, C_CB_ICE,
)

# ── Archer level 3 upgrade cost → 750 ────────────────────────────────────────
if len(ARCHER_LEVELS) > 3:
    _ar3 = list(ARCHER_LEVELS[3])
    _ar3[3] = 750
    ARCHER_LEVELS[3] = type(ARCHER_LEVELS[3])(_ar3)

class DevConsole:
    def __init__(self): self.visible=False; self.input_text=""; self.output_lines=[]; self.cursor_blink=0.0
    def toggle(self): pass  # console disabled
    def update(self, dt): pass
    def handle_key(self, ev, game): pass
    def _execute(self, cmd, game): pass
    def draw(self, surf): pass

# ── Admin Panel ────────────────────────────────────────────────────────────────
ADMIN_ENEMY_LIST = [
    ("Normal",      Enemy,            (160,50,50),   8,     55),
    ("Slow",        TankEnemy,        (100,60,20),   30,    28),
    ("Fast",        ScoutEnemy,       (40,140,180),  10,    140),
    ("Normal Boss", NormalBoss,       (130,20,20),   200,   55),
    ("Hidden",      HiddenEnemy,      (100,200,100), 8,     55),
    ("Breaker",     BreakerEnemy,     (140,100,20),  30,    55),
    ("Armored",     ArmoredEnemy,     (80,90,110),   25,    55),
    ("Slow Boss",   SlowBoss,         (60,80,20),    25,    28),
    ("Hidden Boss", HiddenBoss,       (80,40,120),   200,   55),
    ("Necromancer", Necromancer,      (40,80,160),   360,   55),
    ("GraveDigger", GraveDigger,      (20,60,20),    5000,  30),
    ("Fast Boss",   FastBoss,         (200,80,0),    500,   200),
    ("Optimus Prime",OtchimusPrime,   (80,10,10),    40000, 15),
    ("Abnormal",    AbnormalEnemy,    (180,60,60),   11,    55),
    ("Quick",       QuickEnemy,       (60,180,140),  12,    140),
    ("Skeleton",    SkeletonEnemy,    (200,200,190), 55,    55),
    # Fallen
    ("Fallen Dreg", FallenDreg,       (120,50,160),  80,    83),
    ("Fallen Squire",FallenSquire,    (100,40,140),  400,   42),
    ("Fallen Soul", FallenSoul,       (140,80,200),  150,   55),
    ("Fallen",      FallenEnemy,      (140,30,180),  200,   140),
    ("F.Giant",     FallenGiant,      (60,20,100),   3000,  28),
    ("F.Hazmat",    FallenHazmat,     (50,120,80),   200,   55),
    ("Corrupted",   CorruptedFallen,  (160,20,120),  1000,  120),
    ("F.Necro",     FallenNecromancer,(100,0,70),    3000,  28),
    ("F.Jester",    FallenJester,     (90,0,90),     10000, 28),
    ("Necrotic Sk.",NecroticSkeleton, (170,190,160), 1400,  120),
    ("F.Breaker",   FallenBreaker,    (120,40,160),  30,    55),
    ("F.Rusher",    FallenRusher,     (160,30,100),  350,   61),
    ("Poss.Armor",  PossessedArmor,   (80,80,110),   300,   55),
    ("F.HGuard",    FallenHonorGuard, (160,120,20),  75000, 22),
    ("F.Shield",    FallenShield,     (60,100,160),  8000,  55),
    ("F.Hero",      FallenHero,       (120,60,160),  2500,  55),
    ("F.King",      FallenKing,       (120,40,160),  175000,9),

    # Frosty
    ("Frozen",      FrozenEnemy,      (80,200,255),  10,    68),
    ("Snowy",       SnowyEnemy,       (160,220,255), 16,    28),
    ("PackedIce",   PackedIceEnemy,   (60,160,220),  75,    38),
    ("SnowMinion",  SnowMinion,       (140,210,255), 200,   38),
    ("FrostMystery",FrostMystery,     (30,130,200),  50,    55),
    ("Frostmite",   Frostmite,        (50,180,230),  32,    140),
    ("ColdMist",    ColdMist,         (100,190,240), 80,    68),
    ("Permafrost",  Permafrost,       (40,120,200),  650,   42),
    ("FrostHunter", FrostHunter,      (30,160,220),  1800,  28),
    ("UnstableIce", UnstableIce,      (80,200,240),  400,   140),
    ("FrostWraith", FrostWraith,      (60,180,220),  600,   68),
    ("FrostAcolyte",FrostAcolyte,     (40,150,210),  3050,  16),
    ("Frost Undead",FrostUndead,      (60,170,230),  800,   140),
    ("Frost Invader",FrostInvader,    (40,120,200),  4000,  27),
    ("Mega F.Myst.",MegaFrostMystery, (30,130,200),  600,   55),
    ("Frost Ravager",FrostRavager,    (20,80,170),   25000, 28),
    ("Trickster Elf",TricksterElf,    (20,70,60),    2500,  28),
    ("Yeti",        Yeti,             (80,150,220),  10000, 14),
    ("Frost Mage",  FrostMage,        (20,80,170),   12500, 55),
    ("Frost Hero",  FrostHero,        (20,90,180),   40000, 28),
    ("Deep Freeze", DeepFreeze,       (10,70,160),   12000, 55),
    ("F.Necromancer",FrostNecromancer,(20,70,160),   5000,  55),
    ("Frost Spirit",FrostSpirit,      (20,90,180),   3000,  140),
]

class AdminPanel:
    def __init__(self):
        self.visible=False
        self.tab="enemy"
        self.scroll=0
        self._close_btn=pygame.Rect(0,0,28,28)
        self._tab_rects={}
        self._card_rects=[]
        self._misc_btns=[]
        self._game_speed=1.0
        self._hp_input=""
        self._hp_input_active=False
        self._hp_input_rect=pygame.Rect(0,0,0,0)
        self._money_input=""
        self._money_input_active=False
        self._money_input_rect=pygame.Rect(0,0,0,0)

    def toggle(self): self.visible=not self.visible; self.scroll=0; self._hp_input_active=False; self._money_input_active=False

    def handle_scroll(self, dy): self.scroll=max(0,self.scroll-dy*25)

    def handle_key(self, ev, game_ref):
        """Handle keyboard input for HP and money text fields."""
        if not game_ref: return
        # HP field
        if self._hp_input_active:
            if ev.key==pygame.K_RETURN:
                try:
                    val=int(self._hp_input)
                    if val>0:
                        game_ref.player_hp=val
                        game_ref.player_maxhp=max(game_ref.player_maxhp,val)
                except: pass
                self._hp_input_active=False; self._hp_input=""
            elif ev.key==pygame.K_BACKSPACE: self._hp_input=self._hp_input[:-1]
            elif ev.key==pygame.K_ESCAPE: self._hp_input_active=False; self._hp_input=""
            else:
                if ev.unicode.isdigit() and len(self._hp_input)<7:
                    self._hp_input+=ev.unicode
            return
        # Money field
        if self._money_input_active:
            if ev.key==pygame.K_RETURN:
                try:
                    val=int(self._money_input)
                    if val>0: game_ref.money+=val
                except: pass
                self._money_input_active=False; self._money_input=""
            elif ev.key==pygame.K_BACKSPACE: self._money_input=self._money_input[:-1]
            elif ev.key==pygame.K_ESCAPE: self._money_input_active=False; self._money_input=""
            else:
                if ev.unicode.isdigit() and len(self._money_input)<10:
                    self._money_input+=ev.unicode
            return

    def handle_click(self,pos,game_units,game_enemies,wave,save_data,ui_ref=None,game_ref=None):
        if not self.visible: return
        if self._close_btn.collidepoint(pos): self.visible=False; self._hp_input_active=False; return
        for key,tr in self._tab_rects.items():
            if tr.collidepoint(pos): self.tab=key; self.scroll=0; self._hp_input_active=False; return

        if self.tab=="map" and game_ref:
            for rect,action in getattr(self,'_map_btns',[]):
                if rect.collidepoint(pos):
                    if action=="map_straight": game_core.CURRENT_MAP="straight"
                    elif action=="map_zigzag":  game_core.CURRENT_MAP="zigzag"
                    elif action=="map_frosty":  game_core.CURRENT_MAP="frosty"
                    elif action=="map_event":   game_core.CURRENT_MAP="event"
                    elif action=="map_uturn":       game_core.CURRENT_MAP="uturn"
                    elif action=="map_labyrinth":   game_core.CURRENT_MAP="labyrinth"
                    # Clear all enemies and units when map changes
                    if hasattr(game_ref, 'enemies'):
                        game_ref.enemies.clear()
                    if hasattr(game_ref, 'units'):
                        game_ref.units.clear()
                    return

        if self.tab=="mode" and game_ref:
            for rect,action in getattr(self,'_mode_btns',[]):
                if rect.collidepoint(pos):
                    mode_map={
                        "restart_easy":"easy","restart_fallen":"fallen",
                        "restart_frosty":"frosty",
                        "restart_sandbox":"sandbox","restart_hardcore":"hardcore",
                        "restart_event":"infernal",
                    }
                    new_mode=mode_map.get(action)
                    if new_mode:
                        if action=="restart_event":
                            game_core.CURRENT_MAP="event"
                        game_ref._restart_mode=new_mode
                        game_ref.running=False
                    return

        if self.tab=="misc" and game_ref:
            # HP input field click
            if self._hp_input_rect.collidepoint(pos):
                self._hp_input_active=True
                self._money_input_active=False
                self._hp_input=""
                return
            # Money input field click
            if self._money_input_rect.collidepoint(pos):
                self._money_input_active=True
                self._hp_input_active=False
                self._money_input=""
                return
            # Clicking a button deactivates both inputs
            self._hp_input_active=False
            self._money_input_active=False

            for rect,action in self._misc_btns:
                if rect.collidepoint(pos):
                    if action=="hp_full":
                        game_ref.player_hp=game_ref.player_maxhp
                    elif action=="hp_1":
                        game_ref.player_hp=1
                    elif action=="kill_all":
                        for e in game_ref.enemies: e.alive=False
                    elif action=="speed_05":
                        self._game_speed=0.5; game_ref._admin_speed=0.5
                    elif action=="speed_1":
                        self._game_speed=1.0; game_ref._admin_speed=1.0
                    elif action=="speed_2":
                        self._game_speed=2.0; game_ref._admin_speed=2.0
                    elif action=="speed_5":
                        self._game_speed=5.0; game_ref._admin_speed=5.0
                    elif action=="money_1k":
                        game_ref.money+=1000
                    elif action=="money_10k":
                        game_ref.money+=10000
                    elif action=="money_100k":
                        game_ref.money+=100000
                    elif action=="toggle_limits":
                        self._no_limits = not getattr(self, '_no_limits', False)
                        if self._no_limits:
                            self._saved_limits = dict(UNIT_LIMITS)
                            for k in list(UNIT_LIMITS.keys()):
                                UNIT_LIMITS[k] = 9999
                        else:
                            saved = getattr(self, '_saved_limits', {})
                            UNIT_LIMITS.clear()
                            UNIT_LIMITS.update(saved)
                    elif action=="remove_all_towers":
                        game_ref.units.clear()
                    elif action=="toggle_ability_cd":
                        self._no_ability_cd = not getattr(self, '_no_ability_cd', False)
                    return

        for rect,data in self._card_rects:
            if rect.collidepoint(pos):
                if self.tab=="enemy":
                    cls=data
                    try:
                        e=cls(max(1,wave))
                    except TypeError:
                        e=cls()
                    spawn_enemy_at_start(e); game_enemies.append(e)
                else:
                    cls,name=data
                    if ui_ref is None: return
                    slots=ui_ref.SLOT_TYPES
                    idx_found=None
                    for i,s in enumerate(slots):
                        if s==cls: idx_found=i; break
                    if idx_found is not None:
                        slots[idx_found]=None
                    else:
                        for i,s in enumerate(slots):
                            if s is None: slots[i]=cls; break
                return

    def draw(self,surf,game_units,t,game_ref=None,ui_ref=None):
        if not self.visible: return
        # ── Full-screen panel ─────────────────────────────────────────────────
        margin=28; top=52
        pw=SCREEN_W-margin*2; ph=SCREEN_H-top-margin
        px=margin; py=top
        # Backdrop
        draw_rect_alpha(surf,(8,10,18),(px,py,pw,ph),250,16)
        # Gradient top strip
        for _gi in range(40):
            _ga=int(60*(1-_gi/40))
            _gs=pygame.Surface((pw,1),pygame.SRCALPHA)
            _gs.fill((40,80,180,_ga))
            surf.blit(_gs,(px,py+_gi))
        pygame.draw.rect(surf,(50,70,130),(px,py,pw,ph),2,border_radius=16)

        # ── Title bar ─────────────────────────────────────────────────────────
        title_f=pygame.font.SysFont("segoeui",22,bold=True)
        title_s=title_f.render("SANDBOX ADMIN PANEL",True,(140,200,255))
        surf.blit(title_s,(px+20,py+10))

        mode_lbl=getattr(game_ref,'mode','sandbox') if game_ref else 'sandbox'
        map_lbl=game_core.CURRENT_MAP if game_ref else 'straight'
        _MAP_NAMES={"straight":"The Bridge","zigzag":"S-Turn","frosty":"4-lane","event":"AprilFools2026","uturn":"U-Turn","labyrinth":"Labyrinth"}
        info_f=pygame.font.SysFont("segoeui",14)
        info_s=info_f.render(f"mode: {mode_lbl}   map: {_MAP_NAMES.get(map_lbl,map_lbl)}",True,(80,120,160))
        surf.blit(info_s,(px+20,py+36))

        # Close button
        self._close_btn=pygame.Rect(px+pw-44,py+8,36,36)
        mx_c,my_c=pygame.mouse.get_pos()
        cb_hov=self._close_btn.collidepoint(mx_c,my_c)
        pygame.draw.rect(surf,(90,25,25) if cb_hov else (50,20,20),self._close_btn,border_radius=8)
        pygame.draw.rect(surf,(220,60,60) if cb_hov else (140,40,40),self._close_btn,2,border_radius=8)
        txt(surf,"X",self._close_btn.center,(255,120,120),pygame.font.SysFont("segoeui",20,bold=True),center=True)

        # ── Tab bar ───────────────────────────────────────────────────────────
        tab_y=py+58; tab_h=36
        tabs=[
            ("enemy", "ENEMIES",  (160,50,50)),
            ("units", "UNITS",    (50,160,80)),
            ("map",   "MAP",      (50,120,160)),
            ("mode",  "MODE",     (120,60,180)),
            ("misc",  "MISC",     (180,120,20)),
        ]
        tab_w=(pw-16)//len(tabs)
        self._tab_rects={}
        for i,(key,label,tcol) in enumerate(tabs):
            tr=pygame.Rect(px+8+i*tab_w,tab_y,tab_w-4,tab_h)
            self._tab_rects[key]=tr
            active=(self.tab==key)
            if active:
                pygame.draw.rect(surf,tuple(min(255,c+30) for c in tcol),tr,border_radius=8)
                pygame.draw.rect(surf,tuple(min(255,c+80) for c in tcol),tr,2,border_radius=8)
            else:
                hov=tr.collidepoint(mx_c,my_c)
                pygame.draw.rect(surf,(28,32,50) if not hov else (35,40,62),tr,border_radius=8)
                pygame.draw.rect(surf,(50,60,90) if not hov else tcol,tr,1,border_radius=8)
            lf=pygame.font.SysFont("segoeui",15,bold=True)
            surf.blit(lf.render(label,True,C_WHITE if active else (160,170,200)),
                      lf.render(label,True,C_WHITE).get_rect(center=tr.center))

        # ── Content area ──────────────────────────────────────────────────────
        content_top=tab_y+tab_h+8
        content_h=py+ph-content_top-8
        surf.set_clip(pygame.Rect(px+4,content_top,pw-8,content_h))
        self._card_rects=[]

        if self.tab=="enemy":
            # 8 columns, big cards
            cols=8; cw=(pw-28)//(cols); ch=110; gap=6
            start_x=px+10; start_y=content_top+6
            lf=pygame.font.SysFont("segoeui",12,bold=True)
            sf=pygame.font.SysFont("segoeui",11)
            for i,(label,cls,col,hp,spd) in enumerate(ADMIN_ENEMY_LIST):
                c=i%cols; r=i//cols
                cx2=start_x+c*(cw+gap); cy2=start_y+r*(ch+gap)-self.scroll
                cr=pygame.Rect(cx2,cy2,cw,ch)
                self._card_rects.append((cr,cls))
                if cy2+ch<content_top or cy2>content_top+content_h: continue
                hov=cr.collidepoint(mx_c,my_c)
                bg=tuple(min(255,c2+15) for c2 in (22,26,44)) if hov else (16,20,34)
                pygame.draw.rect(surf,bg,cr,border_radius=10)
                brd=tuple(min(255,c2+40) for c2 in col) if hov else col
                pygame.draw.rect(surf,brd,cr,2,border_radius=10)
                # enemy preview
                preview=pygame.Surface((44,44),pygame.SRCALPHA)
                try:
                    tmp=cls(1); tmp.x=22; tmp.y=22; tmp._bob=0; tmp.draw(preview)
                except: pygame.draw.circle(preview,col,(22,22),14)
                surf.blit(preview,(cx2+cw//2-22,cy2+4))
                # name centered
                ns=lf.render(label,True,C_WHITE if hov else (200,210,230))
                surf.blit(ns,ns.get_rect(centerx=cx2+cw//2,top=cy2+50))
                from game_core import fmt_num as _fn
                hp_s=sf.render(_fn(hp),True,(160,200,255))
                spd_s=sf.render(f"►{spd}",True,(120,220,120))
                surf.blit(hp_s,hp_s.get_rect(centerx=cx2+cw//2,top=cy2+66))
                surf.blit(spd_s,spd_s.get_rect(centerx=cx2+cw//2,top=cy2+80))

        elif self.tab=="units":
            unit_list=[
                ("Assassin",Assassin,C_ASSASSIN),("Accelerator",Accelerator,C_ACCEL),
                ("Frostcel.",Frostcelerator,(60,200,255)),
                ("Lifestealer",Lifestealer,(80,220,140)),("Archer",Archer,(200,160,60)),
                ("Militant",Militant,C_MILITANT),
                ("Swarmer",Swarmer,C_SWARMER),
                ("Farm",Farm,(80,180,60)),("Red Ball",RedBall,(220,40,40)),
                ("FrostBlast",FrostBlaster,C_FROSTBLASTER),
                ("Sledger",Sledger,C_SLEDGER),
                ("Gladiator",Gladiator,C_GLADIATOR),
                ("ToxicGun",ToxicGunner,C_TOXICGUN),
                ("Slasher",Slasher,C_SLASHER),
                ("Cowboy",GoldenCowboy,C_GCOWBOY),
                ("HallowPunk",HallowPunk,C_HALLOWPUNK),
                ("Freezer",Freezer,C_FREEZER),
                ("Snowballer",Snowballer,C_SNOWBALLER),
                ("Commando",Commando,C_COMMANDO),
                ("Caster",Caster,C_HACKER),
                ("Warlock",Warlock,C_WARLOCK),
                ("Jester",Jester,C_JESTER),
                ("Spotlight",SpotlightTech,C_SPOTLIGHT),

                ("RubberDuck",RubberDuck,C_DUCK),
                ("Harvester",Harvester,C_HARVESTER),
                ("Twitgunner",Twitgunner,C_TWITGUN),
                ("Korzhik",Felyne,C_FELYNE),
                ("Conduit",Conduit,C_CONDUIT),
                ("CtrlPanel",ControlPanel,C_CTRLPANEL),
                ("Castbound",Castbound,C_CASTBOUND),
            ]
            cols=8; cw=(pw-28)//cols; ch=100; gap=6
            start_x=px+10; start_y=content_top+6
            lf=pygame.font.SysFont("segoeui",12,bold=True)
            active_cls=set(s for s in (ui_ref.SLOT_TYPES if ui_ref else []) if s)
            for i,(name,cls,col) in enumerate(unit_list):
                c=i%cols; r=i//cols
                cx2=start_x+c*(cw+gap); cy2=start_y+r*(ch+gap)-self.scroll
                cr=pygame.Rect(cx2,cy2,cw,ch)
                self._card_rects.append((cr,(cls,name)))
                if cy2+ch<content_top or cy2>content_top+content_h: continue
                is_active=cls in active_cls
                hov=cr.collidepoint(mx_c,my_c)
                bg=(20,44,20) if is_active else ((24,30,48) if hov else (16,20,34))
                pygame.draw.rect(surf,bg,cr,border_radius=10)
                brd=(80,220,80) if is_active else (tuple(min(255,c2+30) for c2 in col) if hov else col)
                pygame.draw.rect(surf,brd,cr,2,border_radius=10)
                if name=="Accelerator": draw_accel_icon(surf,cx2+cw//2,cy2+28,t,size=20)
                elif name=="Frostcel.": draw_frost_icon(surf,cx2+cw//2,cy2+28,t,size=20)
                elif name=="Castbound": _draw_tower_icon(surf,"Castbound",cx2+cw//2,cy2+26,t,size=32)

                else:
                    pygame.draw.circle(surf,(16,12,28),(cx2+cw//2,cy2+28),20)
                    pygame.draw.circle(surf,col,(cx2+cw//2,cy2+28),16)
                ns=lf.render(name,True,(120,255,120) if is_active else C_WHITE)
                surf.blit(ns,ns.get_rect(centerx=cx2+cw//2,top=cy2+52))
                if is_active:
                    ck=pygame.font.SysFont("segoeui",10).render("IN SLOT",True,(80,200,80))
                    surf.blit(ck,ck.get_rect(centerx=cx2+cw//2,top=cy2+68))

        elif self.tab=="map":
            self._map_btns=[]
            # Two-column layout for map buttons
            bw=(pw-60)//2; bh=70; gap2=14
            col_x=[px+20, px+pw//2+10]
            row_y=content_top+20
            _MAP_DEFS=[
                ("The Bridge",   "map_straight",(20,55,28),(50,160,70),  "straight","Straight Path"),
                ("S-Turn",       "map_zigzag",  (38,28,65),(100,70,200), "zigzag",  "Zigzag"),
                ("4-lane",       "map_frosty",  (12,45,80),(50,150,220), "frosty",  "Four paths"),
                ("AprilFools2026","map_event",  (70,22,12),(200,70,30),  "event",   "Event Map"),
                ("U-Turn",       "map_uturn",   (50,35,10),(200,140,30), "uturn",   "U-shaped road"),
                ("Labyrinth",    "map_labyrinth",(20,45,45),(40,180,160),"labyrinth","Tight zigzag"),
            ]
            cur=game_core.CURRENT_MAP if game_ref else "straight"
            lf=pygame.font.SysFont("segoeui",16,bold=True)
            sf2=pygame.font.SysFont("segoeui",12)
            for i,(name,action,col,brd,key,desc) in enumerate(_MAP_DEFS):
                ci=i%2; ri=i//2
                bx=col_x[ci]; by=row_y+ri*(bh+gap2)
                r=pygame.Rect(bx,by,bw,bh)
                self._map_btns.append((r,action))
                active=(cur==key)
                hov=r.collidepoint(mx_c,my_c)
                bg=tuple(min(255,c2+20) for c2 in col) if (active or hov) else col
                pygame.draw.rect(surf,bg,r,border_radius=12)
                brd2=tuple(min(255,c2+80) for c2 in brd) if active else (tuple(min(255,c2+40) for c2 in brd) if hov else brd)
                pygame.draw.rect(surf,brd2,r,3 if active else 2,border_radius=12)
                check="[x]  " if active else ""
                ns=lf.render(check+name,True,C_WHITE)
                ds=sf2.render(desc,True,(160,180,200))
                surf.blit(ns,ns.get_rect(centerx=r.centerx,top=r.y+12))
                surf.blit(ds,ds.get_rect(centerx=r.centerx,top=r.y+36))

        elif self.tab=="mode":
            self._mode_btns=[]
            # 3-column grid of mode buttons
            _MODE_DEFS=[
                ("Easy",            "restart_easy",    (18,52,18),(55,175,55),   "Standard Mode"),
                ("Fallen",          "restart_fallen",  (45,12,70),(130,55,195),  "Fallen Mode"),
                ("Frosty",          "restart_frosty",  (12,45,85),(55,150,235),  "Frosty Mode"),

                ("Sandbox",         "restart_sandbox", (60,50,25),(170,140,55),  "Sandbox Mode"),
                ("Hardcore",        "restart_hardcore",(75,12,8),(210,55,25),    "Hardcore Mode"),
                ("🎭  April Fools",    "restart_event",   (75,8,28),(245,75,115),   "Event 2026"),

            ]
            cols3=3; bw3=(pw-40)//cols3; bh3=86; gap3=12
            start_x3=px+12; start_y3=content_top+16
            lf=pygame.font.SysFont("segoeui",16,bold=True)
            sf2=pygame.font.SysFont("segoeui",12)
            cur_mode=getattr(game_ref,'mode','sandbox') if game_ref else 'sandbox'
            for i,(label,action,col,brd,desc) in enumerate(_MODE_DEFS):
                ci=i%cols3; ri=i//cols3
                bx=start_x3+ci*(bw3+gap3); by=start_y3+ri*(bh3+gap3)
                r=pygame.Rect(bx,by,bw3,bh3)
                self._mode_btns.append((r,action))
                key=action.replace("restart_","")
                active=(cur_mode==key)
                hov=r.collidepoint(mx_c,my_c)
                bg=tuple(min(255,c2+18) for c2 in col) if (active or hov) else col
                pygame.draw.rect(surf,bg,r,border_radius=12)
                brd2=tuple(min(255,c2+80) for c2 in brd) if active else (tuple(min(255,c2+40) for c2 in brd) if hov else brd)
                pygame.draw.rect(surf,brd2,r,3 if active else 2,border_radius=12)
                if active:
                    gl2=pygame.Surface((bw3,bh3),pygame.SRCALPHA)
                    pygame.draw.rect(gl2,(*brd,30),(0,0,bw3,bh3),border_radius=12)
                    surf.blit(gl2,(bx,by))
                ns=lf.render(("● " if active else "")+label,True,C_WHITE)
                ds=sf2.render(desc,True,(160,180,210))
                surf.blit(ns,ns.get_rect(centerx=r.centerx,top=r.y+18))
                surf.blit(ds,ds.get_rect(centerx=r.centerx,top=r.y+50))

        elif self.tab=="misc":
            self._misc_btns=[]
            # Left column: HP + Money. Right column: speed + enemies
            left_x=px+30; right_x=px+pw//2+20
            col_w=(pw-80)//2
            bh=52; gap2=12
            y_l=content_top+16; y_r=content_top+16
            lf=pygame.font.SysFont("segoeui",15,bold=True)
            sf2=pygame.font.SysFont("segoeui",13)

            def mbtn_misc(label,action,col,brd,x,y,w=None):
                w2=w or col_w
                r=pygame.Rect(x,y,w2,bh)
                self._misc_btns.append((r,action))
                hov=r.collidepoint(mx_c,my_c)
                bg=tuple(min(255,c2+20) for c2 in col) if hov else col
                pygame.draw.rect(surf,bg,r,border_radius=10)
                pygame.draw.rect(surf,brd,r,2,border_radius=10)
                ns=lf.render(label,True,C_WHITE)
                surf.blit(ns,ns.get_rect(center=r.center))
                return r

            def sec_label(text,x,y):
                s=pygame.font.SysFont("segoeui",13,bold=True).render(text,True,(80,120,180))
                surf.blit(s,(x,y))

            def draw_input(inp_text, active, rect, placeholder, hint):
                self._hp_input_rect if placeholder=="Custom HP..." else None
                pygame.draw.rect(surf,(20,26,42) if not active else (28,38,62),rect,border_radius=10)
                pygame.draw.rect(surf,(80,160,255) if active else (45,55,85),rect,2,border_radius=10)
                disp=inp_text if inp_text else placeholder
                col_d=(220,230,255) if inp_text else (70,80,110)
                cursor_s="|" if (active and pygame.time.get_ticks()//500%2==0) else ""
                hs=lf.render(disp+cursor_s,True,col_d)
                surf.blit(hs,hs.get_rect(center=rect.center))
                if active:
                    ht=sf2.render(hint,True,(70,120,160))
                    surf.blit(ht,ht.get_rect(centerx=rect.centerx,top=rect.bottom+4))

            # LEFT: HP section
            sec_label("── PLAYER HP ──", left_x, y_l); y_l+=22
            mbtn_misc("Full HP",   "hp_full",(20,62,20),(55,175,55),left_x,y_l); y_l+=bh+gap2
            mbtn_misc("Set HP to 1","hp_1",   (68,18,18),(195,45,45),left_x,y_l); y_l+=bh+gap2
            # HP custom input
            inp_r=pygame.Rect(left_x,y_l,col_w,bh)
            self._hp_input_rect=inp_r
            draw_input(self._hp_input, self._hp_input_active, inp_r, "Custom HP...", "ENTER to apply")
            y_l+=bh+gap2+18

            # LEFT: Money section
            sec_label("── MONEY ──", left_x, y_l); y_l+=22
            # Quick give buttons in a row
            qbw=(col_w-gap2*2)//3
            mbtn_misc("+1K","money_1k",(20,50,20),(55,160,55),left_x,y_l,qbw)
            mbtn_misc("+10K","money_10k",(20,60,30),(55,180,55),left_x+qbw+gap2,y_l,qbw)
            mbtn_misc("+100K","money_100k",(10,70,40),(40,200,80),left_x+qbw*2+gap2*2,y_l,qbw)
            y_l+=bh+gap2
            # Money custom input
            money_r=pygame.Rect(left_x,y_l,col_w,bh)
            self._money_input_rect=money_r
            draw_input(self._money_input, self._money_input_active, money_r, "Custom amount...", "ENTER to add")
            y_l+=bh+gap2+18

            # LEFT: Enemies
            sec_label("── ENEMIES ──", left_x, y_l); y_l+=22
            mbtn_misc("Kill All","kill_all",(68,16,16),(195,45,45),left_x,y_l); y_l+=bh+gap2

            # LEFT: Towers
            sec_label("── TOWERS ──", left_x, y_l); y_l+=22
            mbtn_misc("Remove All Towers","remove_all_towers",(50,18,55),(160,50,180),left_x,y_l); y_l+=bh+gap2
            _no_cd = getattr(self, '_no_ability_cd', False)
            _acd_col = (10,55,10) if not _no_cd else (55,10,10)
            _acd_brd = (55,175,55) if not _no_cd else (220,60,60)
            _acd_lbl = ("     Ability CD: ON" if not _no_cd else "[x]  Ability CD: OFF")
            mbtn_misc(_acd_lbl,"toggle_ability_cd",_acd_col,_acd_brd,left_x,y_l); y_l+=bh+gap2

            # RIGHT: Game speed
            sec_label("── GAME SPEED ──", right_x, y_r); y_r+=22
            spd=self._game_speed
            _spd_defs=[("0.5x","speed_05",0.5,(20,40,80),(50,100,200)),
                       ("1x  normal","speed_1",1.0,(20,50,20),(55,160,55)),
                       ("2x","speed_2",2.0,(70,45,10),(190,130,30)),
                       ("5x","speed_5",5.0,(80,15,10),(220,45,25))]
            for lbl,act,spd_val,c_off,c_on in _spd_defs:
                active_spd=(spd==spd_val)
                col2=c_on if active_spd else c_off
                brd2=tuple(min(255,c2+60) for c2 in c_on) if active_spd else tuple(min(255,c2+40) for c2 in c_on)
                full_lbl=("[x]  " if active_spd else "     ")+lbl
                mbtn_misc(full_lbl,act,col2,brd2,right_x,y_r); y_r+=bh+gap2

            # RIGHT: Tower limits toggle
            sec_label("── TOWER LIMITS ──", right_x, y_r); y_r+=22
            _no_lim = getattr(self, '_no_limits', False)
            _lim_col  = (10,55,10) if not _no_lim else (55,10,10)
            _lim_brd  = (55,175,55) if not _no_lim else (220,60,60)
            _lim_lbl  = ("     No Limits: OFF" if not _no_lim else "[x]  No Limits: ON")
            mbtn_misc(_lim_lbl, "toggle_limits", _lim_col, _lim_brd, right_x, y_r); y_r+=bh+gap2

        surf.set_clip(None)

        # ── Scrollbar for enemy/units tabs ────────────────────────────────────
        if self.tab in ("enemy","units"):
            _cols=8
            n_items=len(ADMIN_ENEMY_LIST) if self.tab=="enemy" else 25
            _ch=110 if self.tab=="enemy" else 100; _gap=6
            rows=((n_items+_cols-1)//_cols)
            total_h=rows*(_ch+_gap)
            if total_h>content_h:
                max_scroll=total_h-content_h
                self.scroll=min(self.scroll,max_scroll)
                sb_h=max(30,int(content_h*content_h/total_h))
                sb_y=content_top+int((content_h-sb_h)*self.scroll/max_scroll)
                pygame.draw.rect(surf,(30,36,58),(px+pw-14,content_top,8,content_h),border_radius=4)
                pygame.draw.rect(surf,(80,120,220),(px+pw-14,sb_y,8,sb_h),border_radius=4)

# ── UI ─────────────────────────────────────────────────────────────────────────
class UI:
    SLOT_TYPES=[Assassin,Accelerator,SoulWeaver,None,None]
    # Speed steps: 0.25, 0.50, 1.0, 1.25, 1.50, 2.0
    _SPEED_STEPS = [0.25, 0.50, 1.0, 1.25, 1.50, 2.0]
    def __init__(self, save_data=None):
        self.save_data = save_data or {}
        self.ui_layout = self.save_data.get("ui_layout", {})
        self.slots=self._build_slots(); self.selected_slot=None
        self.drag_unit=None; self.open_unit=None; self.msg=""; self.msg_timer=0.0
        self._sell_pending=False  # waiting for sell confirmation
        # Harvester thorn-placement mode
        self._thorn_place_mode = False   # True while waiting for player to click on map
        self._thorn_place_owner = None   # which Harvester triggered the mode
        # ControlPanel Remote Control UI
        self._rc_open     = False
        self._rc_panel    = None   # ControlPanel owner
        self._rc_units    = []     # candidate towers in range
        self._rc_sel_unit = None   # currently selected target
        self._rc_sel_buff = "Damage"
        self._rc_duration = 30     # seconds
        self.t = 0.0  # elapsed time for animations
        self.admin_panel=AdminPanel()
        self.admin_mode = False  # set to True by Game when launched from sandbox
        self._speed_idx = 2   # default 1x
        self.cost_mult = 1.0  # 1.5 in Hardcore mode
        # Speed button rect — left of loadout area
        slots_start_x = self.slots[0].x if self.slots else (SCREEN_W - (5*SLOT_W + 4*8)) // 2
        spd_x, spd_y = self.ui_layout.get("speed", (slots_start_x - 100, SLOT_AREA_Y + 8))
        self._speed_btn = pygame.Rect(spd_x, spd_y, 88, SLOT_H)
        # Admin button rect — left of speed button (only shown in sandbox)
        adm_x, adm_y = self.ui_layout.get("admin", (spd_x - 112, SLOT_AREA_Y + 8))
        self._admin_btn_rect = pygame.Rect(adm_x, adm_y, 100, SLOT_H)
        # Skip button rect — top-left area, right of wave counter
        skp_x, skp_y = self.ui_layout.get("skip", (8, 54))
        self._skip_btn = pygame.Rect(skp_x, skp_y, 120, 28)
    def _build_slots(self):
        slots=[]; gap=8
        total_w=5*SLOT_W+4*gap
        def_x = (SCREEN_W-total_w)//2
        val = getattr(self, "ui_layout", {}).get("slots", (def_x, SLOT_AREA_Y+8))
        start_x, start_y = val[0], val[1]
        for i in range(5): slots.append(pygame.Rect(start_x+i*(SLOT_W+gap),start_y,SLOT_W,SLOT_H))
        return slots
    def show_msg(self,text,dur=2.0): self.msg=text; self.msg_timer=dur
    def update(self,dt):
        if self.msg_timer>0: self.msg_timer-=dt
        self.t += dt
    def handle_click(self,pos,units,money,effects,enemies,wave=1,save_data=None,mode="easy",wave_mgr=None):
        # ── Remote Control UI takes priority ─────────────────────────────────
        if getattr(self, '_rc_open', False):
            return self.handle_rc_click(pos, money)
        # ── Harvester thorn-placement mode ───────────────────────────────────
        if self._thorn_place_mode and self._thorn_place_owner:
            owner = self._thorn_place_owner
            if owner in units and owner.ability.ready():
                from game_core import _FROSTY_PATHS, CURRENT_MAP
                if CURRENT_MAP == "frosty":
                    paths = list(_FROSTY_PATHS)
                else:
                    paths = [get_map_path()]
                # pick the path that is closest to the click
                mx2, my2 = pos
                best_path = paths[0]
                best_d = float('inf')
                for p in paths:
                    for si in range(len(p)-1):
                        ax,ay = p[si]; bx,by = p[si+1]
                        dx,dy = bx-ax, by-ay
                        ll = dx*dx+dy*dy
                        if ll > 0:
                            t = max(0.0, min(1.0, ((mx2-ax)*dx+(my2-ay)*dy)/ll))
                            nx,ny = ax+t*dx, ay+t*dy
                        else:
                            nx,ny = ax, ay
                        d = math.hypot(nx-mx2, ny-my2)
                        if d < best_d:
                            best_d = d; best_path = p
                _farms = [u for u in units if isinstance(u, Farm)]
                owner.activate_thorns(mx2, my2, best_path, _farms)
            self._thorn_place_mode  = False
            self._thorn_place_owner = None
            return 0
        sy_r=getattr(self,'_skip_yes_rect',None)
        if sy_r and sy_r.collidepoint(pos) and wave_mgr is not None:
            can_skip=getattr(wave_mgr,'can_skip',lambda:False)()
            if can_skip:
                do_skip=getattr(wave_mgr,'do_skip',None)
                if do_skip: do_skip()

            return 0
        sn_r=getattr(self,'_skip_no_rect',None)
        if sn_r and sn_r.collidepoint(pos):

            return 0
        # Speed button
        if self._speed_btn.collidepoint(pos):
            self._speed_idx = (self._speed_idx + 1) % len(self._SPEED_STEPS)
            return 0
        # Admin panel — available in sandbox and admin-mode restarts
        if self.admin_mode:
            if self.admin_panel.visible:
                self.admin_panel.handle_click(pos,units,enemies,wave,save_data,ui_ref=self,game_ref=getattr(self,'_game_ref',None))
                return 0
            ab_r=getattr(self,'_admin_btn_rect',None)
            if ab_r and ab_r.collidepoint(pos):
                self.admin_panel.toggle()
                # Hacker achievement: admin panel opened in sandbox
                if self.admin_panel.visible:
                    self._hacker_panel_opened = True
                return 0
        if getattr(self, 'drag_unit', None) is not None:
            mx, my = pos
            if my <= SLOT_AREA_Y - 10:
                UType = self.SLOT_TYPES[self.selected_slot]
                def _on_any_path(px2, py2):
                    paths = list(getattr(game_core, "_FROSTY_PATHS", [])) if game_core.CURRENT_MAP == "frosty" else [get_map_path()]
                    for path in paths:
                        for pi in range(len(path)-1):
                            ax,ay=path[pi]; bx,by=path[pi+1]
                            if ax==bx:
                                if abs(px2-ax)<=PATH_H+5 and min(ay,by)-5<=py2<=max(ay,by)+5: return True
                            else:
                                if abs(py2-ay)<=PATH_H+5 and min(ax,bx)-5<=px2<=max(ax,bx)+5: return True
                    return False
                on_path = _on_any_path(mx, my)
                can_path = getattr(UType, 'CAN_PLACE_ON_PATH', False)
                own_units = [u for u in units if not getattr(u, '_mp_peer', False)]
                if (on_path and not can_path) or any(dist((u.px,u.py),(mx,my))<36 for u in units):
                    self.show_msg("Can't place here!")
                    return 0
                _place_cost = int(UType.PLACE_COST * getattr(self, 'cost_mult', 1.0))
                if money < _place_cost:
                    self.show_msg("Not enough money!")
                    return 0
                limit=UNIT_LIMITS.get(UType.NAME)
                if limit is not None:
                    count=sum(1 for u in own_units if type(u)==UType)
                    if count>=limit:
                        self.show_msg(f"Limit: {limit} {UType.NAME}!")
                        return 0
                if len(own_units) >= GLOBAL_UNIT_LIMIT:
                    self.show_msg(f"Tower limit reached! ({GLOBAL_UNIT_LIMIT} max)")
                    return 0
                u=UType(mx,my); units.append(u)
                if isinstance(u, Castbound) and (self.save_data or {}).get("castbound_zenith_unlocked"):
                    u.grant_zenith()
                if UType is ControlPanel and u.ability is not None:
                    u.ability.cd_left = 60.0  # starting cooldown on placement
                _sk_rng = getattr(self, '_sk_range_bonus', 0)
                if _sk_rng > 0:
                    u._base_range_tiles = u.range_tiles
                    u.range_tiles = round(u.range_tiles * (1.0 + _sk_rng), 4)
                self.drag_unit=None; self.selected_slot=None; return -_place_cost
        for u in units:
            if getattr(u, '_mp_peer', False): continue  # can't click partner's ability buttons
            btn1=getattr(u,'_ability_btn_rect',None)
            if btn1 and btn1.collidepoint(pos):
                if u.ability and u.ability.ready():
                    if isinstance(u, Harvester):
                        self._thorn_place_mode  = True
                        self._thorn_place_owner = u
                        self.show_msg("Click on the path to place Thorns  [RMB / Esc to cancel]", 4.0)
                    elif isinstance(u, ControlPanel):
                        # Open Remote Control UI
                        other = [x for x in units if x is not u and
                                 dist((x.px, x.py), (u.px, u.py)) <= u.range_tiles * TILE]
                        if not other:
                            self.show_msg("No towers in range to buff!", 3.0)
                        else:
                            self._rc_panel       = u        # owner
                            self._rc_units       = other    # targets
                            self._rc_sel_unit    = other[0]
                            self._rc_sel_buff    = "Damage"
                            self._rc_duration    = 30
                            self._rc_open        = True
                    else:
                        u.ability.activate(enemies,effects)
                return 0
            btn2=getattr(u,'_ability2_btn_rect',None)
            if btn2 and btn2.collidepoint(pos):
                ab2=getattr(u,'ability2',None)
                if ab2 and ab2.ready(): ab2.activate(enemies,effects)
                return 0
            btn3=getattr(u,'_ability3_btn_rect',None)
            if btn3 and btn3.collidepoint(pos):
                ab3=getattr(u,'ability3',None)
                if ab3 and ab3.ready(): ab3.activate(enemies,effects)
                return 0
        if self.open_unit:
            menu,btns=self._menu_rects(self.open_unit)
            # Use cached btns from last draw call if available (contains correctly repositioned buttons)
            if hasattr(self,'_cached_btns') and self._cached_btns:
                btns=self._cached_btns
            if btns.get("close") and btns["close"].collidepoint(pos):
                self.open_unit=None; self._sell_pending=False; return 0
            if btns.get("sell") and btns["sell"].collidepoint(pos):
                sell_val=self._sell_value(self.open_unit)
                if SETTINGS.get("sell_confirm", True) and not self._sell_pending:
                    self._sell_pending=True
                    self.show_msg(f"Click SELL again to confirm (${sell_val})", 3.0)
                    return 0
                self._sell_pending=False
                units.remove(self.open_unit)
                # Cancel any active placement mode if the sold unit was the owner
                if self._thorn_place_owner is self.open_unit:
                    self._thorn_place_mode = False; self._thorn_place_owner = None
                self.open_unit=None; return sell_val
            if btns.get("upgrade") and btns["upgrade"].collidepoint(pos):
                cost=self.open_unit.upgrade_cost()
                if cost is not None:
                    cost = int(cost * getattr(self, 'cost_mult', 1.0))
                if cost and money>=cost:
                    _sk_rng = getattr(self, '_sk_range_bonus', 0)
                    if _sk_rng > 0:
                        self.open_unit.range_tiles = getattr(self.open_unit, '_base_range_tiles', self.open_unit.range_tiles)
                    self.open_unit.upgrade()
                    if _sk_rng > 0:
                        self.open_unit._base_range_tiles = self.open_unit.range_tiles
                        self.open_unit.range_tiles = round(self.open_unit.range_tiles * (1.0 + _sk_rng), 4)
                    return -cost
                self.show_msg("Not enough money!" if cost else "Max level!"); return 0
            # Archer arrow mode buttons
            if isinstance(self.open_unit, Archer):
                u=self.open_unit
                if btns.get("arrow_normal") and btns["arrow_normal"].collidepoint(pos):
                    u.arrow_mode="arrow"; return 0
                if btns.get("arrow_flame") and btns["arrow_flame"].collidepoint(pos):
                    if u.level>=3: u.arrow_mode="flame"
                    else: self.show_msg("Unlock at level 3!")
                    return 0
                if btns.get("arrow_shock") and btns["arrow_shock"].collidepoint(pos):
                    if u.level>=4: u.arrow_mode="shock"
                    else: self.show_msg("Unlock at level 4!")
                    return 0
                if btns.get("arrow_explosive") and btns["arrow_explosive"].collidepoint(pos):
                    if u.level>=5: u.arrow_mode="explosive"
                    else: self.show_msg("Unlock at level 5!")
                    return 0
            # Jester bomb mode buttons
            if isinstance(self.open_unit, Jester):
                u=self.open_unit
                if btns.get("bomb_fire") and btns["bomb_fire"].collidepoint(pos):
                    u.bomb_mode="fire"; return 0
                if btns.get("bomb_ice") and btns["bomb_ice"].collidepoint(pos):
                    if u.level>=2: u.bomb_mode="ice"
                    else: self.show_msg("Unlock at level 2!")
                    return 0
                if btns.get("bomb_poison") and btns["bomb_poison"].collidepoint(pos):
                    if u.level>=3: u.bomb_mode="poison"
                    else: self.show_msg("Unlock at level 3!")
                    return 0
                if btns.get("bomb_confusion") and btns["bomb_confusion"].collidepoint(pos):
                    if u.level>=4: u.bomb_mode="confusion"
                    else: self.show_msg("Unlock at level 4!")
                    return 0
                # Second bomb row (lv4 only)
                if btns.get("bomb2_fire") and btns["bomb2_fire"].collidepoint(pos):
                    u.bomb_mode2="fire"; return 0
                if btns.get("bomb2_ice") and btns["bomb2_ice"].collidepoint(pos):
                    if u.level>=2: u.bomb_mode2="ice"
                    else: self.show_msg("Unlock at level 2!")
                    return 0
                if btns.get("bomb2_poison") and btns["bomb2_poison"].collidepoint(pos):
                    if u.level>=3: u.bomb_mode2="poison"
                    else: self.show_msg("Unlock at level 3!")
                    return 0
                if btns.get("bomb2_confusion") and btns["bomb2_confusion"].collidepoint(pos):
                    if u.level>=4: u.bomb_mode2="confusion"
                    else: self.show_msg("Unlock at level 4!")
                    return 0
            # Castbound blade selection buttons
            if isinstance(self.open_unit, Castbound):
                u = self.open_unit
                for key, val in btns.items():
                    if key.startswith("cb_blade_") and val.collidepoint(pos):
                        bid = key[len("cb_blade_"):]
                        u.toggle_blade(bid)
                        return 0
            if btns.get("ability_sq") and btns["ability_sq"].collidepoint(pos):
                if self.open_unit and self.open_unit.ability and self.open_unit.ability.ready():
                    if isinstance(self.open_unit, Harvester):
                        # Enter placement mode — player clicks on the path
                        self._thorn_place_mode  = True
                        self._thorn_place_owner = self.open_unit
                        self.show_msg("Click on the path to place Thorns  [RMB / Esc to cancel]", 4.0)
                    elif isinstance(self.open_unit, ControlPanel):
                        other = [x for x in units if x is not self.open_unit and
                                 dist((x.px, x.py), (self.open_unit.px, self.open_unit.py))
                                 <= self.open_unit.range_tiles * TILE]
                        if not other:
                            self.show_msg("No towers in range to buff!", 3.0)
                        else:
                            self._rc_panel    = self.open_unit
                            self._rc_units    = other
                            self._rc_sel_unit = other[0]
                            self._rc_sel_buff = "Damage"
                            self._rc_duration = 30
                            self._rc_open     = True
                    else:
                        self.open_unit.ability.activate(enemies, effects)
                return 0
            # Target mode arrows
            if btns.get("target_prev") and btns["target_prev"].collidepoint(pos):
                idx=TARGET_MODES.index(getattr(self.open_unit,'target_mode','First'))
                self.open_unit.target_mode=TARGET_MODES[(idx-1)%len(TARGET_MODES)]; return 0
            if btns.get("target_next") and btns["target_next"].collidepoint(pos):
                idx=TARGET_MODES.index(getattr(self.open_unit,'target_mode','First'))
                self.open_unit.target_mode=TARGET_MODES[(idx+1)%len(TARGET_MODES)]; return 0
            if not menu.collidepoint(pos) and not btns.get("ability_sq",pygame.Rect(0,0,0,0)).collidepoint(pos):
                # also keep open if clicking target panel
                tpanel=btns.get("target_panel")
                if tpanel and tpanel.collidepoint(pos): return 0
                self.open_unit=None; self._sell_pending=False
            return 0
        for u in units:
            if dist((u.px,u.py),pos)<20:
                if getattr(u, '_mp_peer', False):
                    self.show_msg("Partner's tower — view only", 1.5)
                    return 0
                self.open_unit=u; self._sell_pending=False; return 0
        for i,slot in enumerate(self.slots):
            if slot.collidepoint(pos):
                UType=self.SLOT_TYPES[i]
                if UType is None: return 0  # empty slot — silently ignore
                is_sandbox = (mode == "sandbox")
                if not is_sandbox:
                    _place_cost = int(UType.PLACE_COST * getattr(self, 'cost_mult', 1.0))
                    if money < _place_cost:
                        self.show_msg("Not enough money!")
                        return 0
                    lim = UNIT_LIMITS.get(UType.NAME)
                    if lim is not None:
                        own_u = [u for u in units if not getattr(u, '_mp_peer', False)]
                        if sum(1 for u in own_u if type(u) == UType) >= lim:
                            self.show_msg(f"Limit: {lim} {UType.NAME}!")
                            return 0
                self.selected_slot=i
                self.drag_unit=UType(*pos)
                _sk_rng = getattr(self, '_sk_range_bonus', 0)
                if _sk_rng > 0:
                    self.drag_unit._base_range_tiles = self.drag_unit.range_tiles
                    self.drag_unit.range_tiles = round(self.drag_unit.range_tiles * (1.0 + _sk_rng), 4)
                return 0
        return 0
    def handle_release(self,pos,units,money):
        return 0
    def _menu_rects(self,unit):
        # Larger card, positioned vertically centered on the right side
        mw,mh=340,520
        mx=SCREEN_W - mw - 24                        # right side with margin
        my=(SLOT_AREA_Y - mh)//2                     # vertically centered in play area
        my=max(60, min(my, SLOT_AREA_Y-mh-8))        # clamp so it doesn't go off-screen
        menu=pygame.Rect(mx,my,mw,mh); btns={}
        btns["upgrade"]=pygame.Rect(mx+6,my+258,mw-12,44)
        btns["close"]=pygame.Rect(mx+6,my+mh-44,38,38)
        btns["sell"]=pygame.Rect(mx+48,my+mh-44,mw-54,38)
        ab_sz=56
        btns["ability_sq"]=pygame.Rect(mx-ab_sz-8,my,ab_sz,ab_sz)
        if isinstance(unit, Archer):
            btn_h=24; btn_w=(mw-24)//4
            arrow_btn_y=my+260
            btns["arrow_normal"]   =pygame.Rect(mx+8,               arrow_btn_y, btn_w, btn_h)
            btns["arrow_flame"]    =pygame.Rect(mx+8+(btn_w+2),     arrow_btn_y, btn_w, btn_h)
            btns["arrow_shock"]    =pygame.Rect(mx+8+(btn_w+2)*2,   arrow_btn_y, btn_w, btn_h)
            btns["arrow_explosive"]=pygame.Rect(mx+8+(btn_w+2)*3,   arrow_btn_y, btn_w, btn_h)
        if isinstance(unit, Jester):
            btn_h=24; btn_w=(mw-20)//4
            bomb_btn_y=my+260
            btns["bomb_fire"]     =pygame.Rect(mx+8,                    bomb_btn_y, btn_w, btn_h)
            btns["bomb_ice"]      =pygame.Rect(mx+8+(btn_w+2),          bomb_btn_y, btn_w, btn_h)
            btns["bomb_poison"]   =pygame.Rect(mx+8+(btn_w+2)*2,        bomb_btn_y, btn_w, btn_h)
            btns["bomb_confusion"]=pygame.Rect(mx+8+(btn_w+2)*3,        bomb_btn_y, btn_w, btn_h)
            # Second row for lv4 dual
            if unit.level >= 4 and unit._dual:
                bomb_btn2_y = bomb_btn_y + btn_h + 6
                btns["bomb2_fire"]     =pygame.Rect(mx+8,                    bomb_btn2_y, btn_w, btn_h)
                btns["bomb2_ice"]      =pygame.Rect(mx+8+(btn_w+2),          bomb_btn2_y, btn_w, btn_h)
                btns["bomb2_poison"]   =pygame.Rect(mx+8+(btn_w+2)*2,        bomb_btn2_y, btn_w, btn_h)
                btns["bomb2_confusion"]=pygame.Rect(mx+8+(btn_w+2)*3,        bomb_btn2_y, btn_w, btn_h)
        return menu,btns

    def _draw_unit_portrait(self, surf, u, rect):
        """Draw unit portrait in a rect."""
        cx,cy=rect.centerx,rect.centery
        pygame.draw.rect(surf,(20,15,35),rect,border_radius=6)
        pygame.draw.rect(surf,(60,50,90),rect,2,border_radius=6)
        t=pygame.time.get_ticks()*0.001
        if isinstance(u,Accelerator): draw_accel_icon(surf,cx,cy,t,size=30)
        elif isinstance(u,Frostcelerator): draw_frost_icon(surf,cx,cy,t,size=30)
        elif isinstance(u,Lifestealer):
            # Hexagon outline
            hex_pts2 = []
            for i in range(6):
                a2 = math.radians(i*60 - 30)
                hex_pts2.append((cx+int(math.cos(a2)*22), cy+int(math.sin(a2)*22)))
            pygame.draw.polygon(surf, C_LIFESTEALER_DARK, hex_pts2)
            pygame.draw.polygon(surf, C_LIFESTEALER, hex_pts2, 2)
            # Venom core
            pygame.draw.circle(surf, (30,120,60), (cx,cy), 14)
            pygame.draw.circle(surf, C_LIFESTEALER, (cx,cy), 14, 2)
            # Rotating spikes
            for i in range(6):
                a2 = math.radians(t*200 + i*60)
                ox2=int(cx+math.cos(a2)*18); oy2=int(cy+math.sin(a2)*18)
                pygame.draw.circle(surf,(60,200,110),(ox2,oy2),4)
        elif isinstance(u,Assassin):
            # Dark slate body with blue rim
            pygame.draw.circle(surf, (15, 18, 28), (cx, cy), 28)
            pygame.draw.circle(surf, C_ASSASSIN, (cx, cy), 22)
            pygame.draw.circle(surf, (60, 100, 200), (cx, cy), 28, 2)
            # Twin spinning daggers
            for i in range(2):
                da = math.radians(t * 90 + i * 180)
                dx2 = int(cx + math.cos(da) * 16)
                dy2 = int(cy + math.sin(da) * 16)
                dx3 = int(cx + math.cos(da) * 5)
                dy3 = int(cy + math.sin(da) * 5)
                pygame.draw.line(surf, (120, 160, 210), (dx3, dy3), (dx2, dy2), 3)
        elif isinstance(u,Archer):
            t2=pygame.time.get_ticks()*0.001
            # Warm amber aura
            aura_s=pygame.Surface((60,60),pygame.SRCALPHA)
            pygame.draw.circle(aura_s,(180,110,40,40),(30,30),30)
            surf.blit(aura_s,(cx-30,cy-30))
            # Body
            pygame.draw.circle(surf,C_ARCHER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_ARCHER,(cx,cy),22)
            pygame.draw.circle(surf,(220,165,80),(cx,cy),22,2)  # amber rim
            # Wood-grain details
            for li in range(3):
                la=math.radians(li*60-30)
                pygame.draw.line(surf,(200,140,70),
                    (cx+int(math.cos(la)*5),cy+int(math.sin(la)*5)),
                    (cx+int(math.cos(la)*18),cy+int(math.sin(la)*18)),1)
            # Specular highlight
            pygame.draw.circle(surf,(240,200,120),(cx-6,cy-6),4)
            # Mini quiver
            pygame.draw.rect(surf,(55,30,8),(cx+10,cy+2,6,12),border_radius=2)
            pygame.draw.rect(surf,(110,70,20),(cx+10,cy+2,6,12),1,border_radius=2)
            # Orbiting arrow dot
            ba=math.radians(t2*130)
            pygame.draw.circle(surf,(230,185,100),(cx+int(math.cos(ba)*16),cy+int(math.sin(ba)*10)),4)
        elif isinstance(u,RedBall):
            pygame.draw.circle(surf,C_REDBALL_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_REDBALL,(cx,cy),22)
        elif isinstance(u,Freezer):
            pygame.draw.circle(surf,C_FREEZER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_FREEZER,(cx,cy),22)
        elif isinstance(u,FrostBlaster):
            t2 = pygame.time.get_ticks() * 0.001
            # Hex base — void purple
            hex_pts2 = []
            for i in range(6):
                a2 = math.radians(i * 60 + t2 * 8)
                hex_pts2.append((cx + int(math.cos(a2) * 22), cy + int(math.sin(a2) * 22)))
            pygame.draw.polygon(surf, C_FROSTBLASTER_DARK, hex_pts2)
            pygame.draw.polygon(surf, C_FROSTBLASTER, hex_pts2, 2)
            # Spinning energy arcs
            for ri, (r2, spd2, col2) in enumerate([(18, 60, (160,40,255)), (12, -90, (200,120,255))]):
                for seg in range(3):
                    sa2 = math.radians(t2 * spd2 + seg * 120)
                    ea2 = sa2 + math.radians(65)
                    try:
                        pygame.draw.arc(surf, col2, pygame.Rect(cx-r2, cy-r2, r2*2, r2*2), sa2, ea2, 2)
                    except Exception:
                        pass
            # Core
            pygame.draw.circle(surf, (70, 10, 130), (cx, cy), 7)
            pygame.draw.circle(surf, (200, 120, 255), (cx, cy), 7, 2)
        elif isinstance(u,Sledger):
            t2=pygame.time.get_ticks()*0.001
            # Octagonal iron body
            oct_pts2 = []
            for i in range(8):
                a_o = math.radians(i * 45 + 22.5)
                oct_pts2.append((cx + int(math.cos(a_o)*22), cy + int(math.sin(a_o)*22)))
            pygame.draw.polygon(surf, C_SLEDGER_DARK, oct_pts2)
            pygame.draw.polygon(surf, C_SLEDGER, oct_pts2, 2)
            # Glowing forge core
            heat2 = abs(math.sin(t2 * 2.2))
            pygame.draw.circle(surf, (80, 30, 5), (cx, cy), 14)
            pygame.draw.circle(surf, (int(180+heat2*60), int(60+heat2*30), 10), (cx, cy), 10)
            pygame.draw.circle(surf, (255, 220, 80), (cx, cy), 4)
            # Swinging hammer
            a2 = math.sin(t2*2)*0.4
            ca2,sa2 = math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(90,55,20),(cx+int(ca2*4),cy+int(sa2*4)),(cx+int(ca2*16),cy+int(sa2*16)),4)
            hpts=[(cx+int(ca2*17)-int(-sa2*8),cy+int(sa2*17)-int(ca2*8)),
                  (cx+int(ca2*17)+int(-sa2*8),cy+int(sa2*17)+int(ca2*8)),
                  (cx+int(ca2*22)+int(-sa2*8),cy+int(sa2*22)+int(ca2*8)),
                  (cx+int(ca2*22)-int(-sa2*8),cy+int(sa2*22)-int(ca2*8))]
            pygame.draw.polygon(surf,(60,35,10),hpts)
            pygame.draw.polygon(surf,C_SLEDGER,hpts,2)
        elif isinstance(u,Gladiator):
            t2=pygame.time.get_ticks()*0.001
            a2=math.atan2(1,-1)+math.sin(t2*3)*0.25
            ca2,sa2=math.cos(a2),math.sin(a2)
            pa2,pb2=-sa2,ca2
            # Shadow
            shad_s2=pygame.Surface((58,16),pygame.SRCALPHA)
            pygame.draw.ellipse(shad_s2,(0,0,0,35),(0,0,58,16))
            surf.blit(shad_s2,(cx-29,cy+20))
            # Body base ring
            pygame.draw.circle(surf,(50,35,5),(cx,cy),26)
            # Armor body
            pygame.draw.circle(surf,(160,120,30),(cx,cy),21)
            chest2=pygame.Surface((42,42),pygame.SRCALPHA)
            pygame.draw.circle(chest2,(220,175,55,160),(21,21),17)
            surf.blit(chest2,(cx-21,cy-21))
            # Chest emblem
            emb2=[(cx,cy-9),(cx+5,cy),(cx,cy+6),(cx-5,cy)]
            pygame.draw.polygon(surf,(80,55,10),emb2)
            pygame.draw.polygon(surf,(255,210,80),emb2,1)
            # Shoulder pads
            for side2 in (-1,1):
                sx2=cx+side2*16
                pygame.draw.circle(surf,(100,75,15),(sx2,cy-4),6)
                pygame.draw.circle(surf,(200,160,45),(sx2,cy-4),4)
                pygame.draw.circle(surf,(255,230,100),(sx2,cy-4),4,1)
            # Helmet
            helm2=[(cx-10,cy-17),(cx-12,cy-26),(cx,cy-31),(cx+12,cy-26),(cx+10,cy-17)]
            pygame.draw.polygon(surf,(130,95,20),helm2)
            pygame.draw.polygon(surf,(210,170,50),helm2,2)
            pygame.draw.line(surf,(30,20,5),(cx-6,cy-22),(cx+6,cy-22),2)
            pygame.draw.line(surf,(255,190,40),(cx-4,cy-22),(cx+4,cy-22),1)
            # Plume animated
            bob2=int(math.sin(t2*3.5)*1.5)
            for i2 in range(4):
                pygame.draw.circle(surf,(200,50,40),(cx-2+i2*2,cy-31-i2+bob2),2)
            # Shield
            sangle2=a2+math.radians(130)
            sc2=math.cos(sangle2);ss2=math.sin(sangle2)
            shx2=cx+int(sc2*15);shy2=cy+int(ss2*15)
            spts2=[(shx2+int(-sc2*3-ss2*8),shy2+int(-ss2*3+sc2*8)),
                   (shx2+int(sc2*8-ss2*4), shy2+int(ss2*8+sc2*4)),
                   (shx2+int(sc2*8+ss2*4), shy2+int(ss2*8-sc2*4)),
                   (shx2+int(-sc2*3+ss2*8),shy2+int(-ss2*3-sc2*8))]
            pygame.draw.polygon(surf,(60,45,10),spts2)
            pygame.draw.polygon(surf,(180,140,35),spts2,2)
            pygame.draw.circle(surf,(220,180,60),(shx2,shy2),3)
            # Sword pommel
            pygame.draw.circle(surf,(160,120,30),(cx+int(ca2*5),cy+int(sa2*5)),3)
            # Grip
            pygame.draw.line(surf,(110,75,20),(cx+int(ca2*6),cy+int(sa2*6)),(cx+int(ca2*18),cy+int(sa2*18)),4)
            pygame.draw.line(surf,(180,140,50),(cx+int(ca2*6),cy+int(sa2*6)),(cx+int(ca2*18),cy+int(sa2*18)),1)
            # Crossguard
            gx2a=cx+int(ca2*18+pa2*10);gy2a=cy+int(sa2*18+pb2*10)
            gx2b=cx+int(ca2*18-pa2*10);gy2b=cy+int(sa2*18-pb2*10)
            pygame.draw.line(surf,(100,70,15),(gx2a,gy2a),(gx2b,gy2b),4)
            pygame.draw.line(surf,(220,180,60),(gx2a,gy2a),(gx2b,gy2b),1)
            pygame.draw.circle(surf,(255,220,80),(gx2a,gy2a),2)
            pygame.draw.circle(surf,(255,220,80),(gx2b,gy2b),2)
            # Blade
            bx2a=cx+int(ca2*20);by2a=cy+int(sa2*20)
            bx2b=cx+int(ca2*40);by2b=cy+int(sa2*40)
            pygame.draw.line(surf,(170,155,100),(bx2a,by2a),(bx2b,by2b),3)
            pygame.draw.line(surf,(240,235,200),(bx2a,by2a),(bx2b,by2b),1)
            pygame.draw.line(surf,(255,255,240),(bx2a+int(pa2),by2a+int(pb2)),(bx2b+int(pa2),by2b+int(pb2)),1)
            pygame.draw.circle(surf,(255,255,230),(int(bx2b),int(by2b)),2)
            # Outer trim
            pygame.draw.circle(surf,(255,220,80),(cx,cy),26,2)
        elif isinstance(u,ToxicGunner):
            t2=pygame.time.get_ticks()*0.001
            # Purple-void body
            pygame.draw.circle(surf,C_TOXICGUN_DARK,(cx,cy),29)
            pygame.draw.circle(surf,C_TOXICGUN,(cx,cy),23)
            # Acid pulsing ring
            acid_a=int(abs(math.sin(t2*5))*80+120)
            ring_s2=pygame.Surface((52,52),pygame.SRCALPHA)
            pygame.draw.circle(ring_s2,(180,230,0,acid_a),(26,26),23,3)
            surf.blit(ring_s2,(cx-26,cy-26))
            # Biohazard rotating dots
            for i in range(3):
                arc_a2=math.radians(t2*60+i*120)
                ax2=cx+int(math.cos(arc_a2)*14); ay2=cy+int(math.sin(arc_a2)*14)
                pygame.draw.circle(surf,(180,230,0),(ax2,ay2),4)
                pygame.draw.circle(surf,C_TOXICGUN_DARK,(ax2,ay2),2)
            # Barrel with acid stripe
            a2=0.1+math.sin(t2*4)*0.15
            ca2,sa2=math.cos(a2),math.sin(a2)
            bx1_t=cx+int(ca2*10); by1_t=cy+int(sa2*10)
            bx2_t=cx+int(ca2*34); by2_t=cy+int(sa2*34)
            pygame.draw.line(surf,C_TOXICGUN_DARK,(bx1_t,by1_t),(bx2_t,by2_t),8)
            pygame.draw.line(surf,C_TOXICGUN,(bx1_t,by1_t),(bx2_t,by2_t),5)
            pygame.draw.line(surf,(180,230,0),(bx1_t,by1_t),(bx2_t,by2_t),2)
            pygame.draw.circle(surf,(180,230,0),(bx2_t,by2_t),5)
            for i in range(3):
                rx=cx+int(ca2*(13+i*7)); ry=cy+int(sa2*(13+i*7))
                pygame.draw.circle(surf,(180,230,0),(rx,ry),4,2)
        elif isinstance(u,Slasher):
            t2=pygame.time.get_ticks()*0.001
            # Blood-mist aura
            mist_r=36; mist_a=int(28+abs(math.sin(t2*1.4))*18)
            mist_s=pygame.Surface((mist_r*2+4,mist_r*2+4),pygame.SRCALPHA)
            pygame.draw.circle(mist_s,(180,10,10,mist_a),(mist_r+2,mist_r+2),mist_r)
            surf.blit(mist_s,(cx-mist_r-2,cy-mist_r-2))
            # Body layers
            pygame.draw.circle(surf,(18,4,4),(cx,cy),26)
            pygame.draw.circle(surf,(80,12,12),(cx,cy),22)
            pygame.draw.circle(surf,(130,20,20),(cx,cy),16)
            pygame.draw.circle(surf,(200,30,30),(cx,cy),9)
            pygame.draw.circle(surf,(255,80,60),(cx,cy),4)
            rim_s=pygame.Surface((56,56),pygame.SRCALPHA)
            pygame.draw.circle(rim_s,(255,40,0,55),(28,28),22,3)
            surf.blit(rim_s,(cx-28,cy-28))
            # Shoulder spikes
            for spike_a in [45,135,225,315]:
                sa_r=math.radians(spike_a+t2*8)
                sx=cx+int(math.cos(sa_r)*20); sy=cy+int(math.sin(sa_r)*20)
                tx2=cx+int(math.cos(sa_r)*30); ty2=cy+int(math.sin(sa_r)*30)
                pygame.draw.line(surf,(60,8,8),(sx,sy),(tx2,ty2),3)
                pygame.draw.circle(surf,(200,40,20),(tx2,ty2),2)
            # Cleaver blade pointing right at idle angle
            a2=math.radians(-40)
            ca2,sa2=math.cos(a2),math.sin(a2)
            perp2x,perp2y=-sa2,ca2
            # Handle
            pygame.draw.line(surf,(40,10,10),(cx+int(ca2*6),cy+int(sa2*6)),(cx+int(ca2*28),cy+int(sa2*28)),4)
            # Blade body
            for step in range(7):
                frac=step/6.0; blen=10+frac*24; w_off=int(7*(1.0-frac*0.55))
                bx2=cx+int(ca2*blen); by2=cy+int(sa2*blen)
                lx2=int(bx2+perp2x*w_off); ly2=int(by2+perp2y*w_off)
                rx2=int(bx2-perp2x*w_off); ry2=int(by2-perp2y*w_off)
                col_m=int(150+frac*70)
                pygame.draw.line(surf,(col_m,col_m-10,col_m-10),(lx2,ly2),(rx2,ry2),2)
            # Blade edge highlight
            tip2x=cx+int(ca2*34+perp2x*2); tip2y=cy+int(sa2*34+perp2y*2)
            base2x=cx+int(ca2*10+perp2x*6); base2y=cy+int(sa2*10+perp2y*6)
            pygame.draw.line(surf,(230,200,200),(base2x,base2y),(tip2x,tip2y),2)
            pygame.draw.circle(surf,(255,240,230),(tip2x,tip2y),3)
            # Blood groove
            pygame.draw.line(surf,(100,5,5),(cx+int(ca2*14),cy+int(sa2*14)),(cx+int(ca2*32),cy+int(sa2*32)),1)
            # Crossguard
            ga2=a2+math.pi/2
            gx1=cx+int(ca2*12+math.cos(ga2)*9); gy1=cy+int(sa2*12+math.sin(ga2)*9)
            gx2=cx+int(ca2*12-math.cos(ga2)*9); gy2=cy+int(sa2*12-math.sin(ga2)*9)
            pygame.draw.line(surf,(80,15,15),(gx1,gy1),(gx2,gy2),4)
            pygame.draw.line(surf,(150,30,30),(gx1,gy1),(gx2,gy2),2)
        elif isinstance(u,GoldenCowboy):
            t2=pygame.time.get_ticks()*0.001
            # Copper aura
            ga_c=int(abs(math.sin(t2*2.5))*55+30)
            glow_c=pygame.Surface((72,72),pygame.SRCALPHA)
            pygame.draw.circle(glow_c,(200,120,20,ga_c),(36,36),33)
            surf.blit(glow_c,(cx-36,cy-36))
            # Body
            pygame.draw.circle(surf,C_GCOWBOY_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_GCOWBOY,(cx,cy),22)
            pygame.draw.circle(surf,C_GCOWBOY_STAR,(cx,cy),22,2)
            # Sheriff star
            star_pts2=[]
            for i in range(10):
                r_s2=10 if i%2==0 else 4
                a_s2=math.radians(-90+i*36)
                star_pts2.append((cx+int(math.cos(a_s2)*r_s2),cy+int(math.sin(a_s2)*r_s2)))
            pygame.draw.polygon(surf,C_GCOWBOY_STAR,star_pts2)
            pygame.draw.polygon(surf,C_GCOWBOY_DARK,star_pts2,1)
            # Hat brim + crown
            pygame.draw.ellipse(surf,C_GCOWBOY_BRIM,(cx-19,cy-31,38,10))
            crown_pts2=[(cx-11,cy-31),(cx-9,cy-46),(cx+9,cy-46),(cx+11,cy-31)]
            pygame.draw.polygon(surf,C_GCOWBOY_BRIM,crown_pts2)
            pygame.draw.line(surf,C_GCOWBOY_STAR,(cx-11,cy-33),(cx+11,cy-33),2)
            # Barrel
            a2=0.2+math.sin(t2*2)*0.2
            ca2,sa2=math.cos(a2),math.sin(a2)
            pa2=a2+math.pi/2
            for sign2 in (1,-1):
                ox2=int(math.cos(pa2)*sign2*3); oy2=int(math.sin(pa2)*sign2*3)
                pygame.draw.line(surf,C_GCOWBOY_BRIM,(cx+int(ca2*9)+ox2,cy+int(sa2*9)+oy2),(cx+int(ca2*32)+ox2,cy+int(sa2*32)+oy2),4)
                pygame.draw.line(surf,C_GCOWBOY,(cx+int(ca2*9)+ox2,cy+int(sa2*9)+oy2),(cx+int(ca2*32)+ox2,cy+int(sa2*32)+oy2),2)
            pygame.draw.circle(surf,C_GCOWBOY_STAR,(cx+int(ca2*32),cy+int(sa2*32)),4)
        elif isinstance(u,HallowPunk):
            t2=pygame.time.get_ticks()*0.001
            lv2=u.level
            pulse2=abs(math.sin(t2*2.5))
            # Glow
            gs2=pygame.Surface((62,62),pygame.SRCALPHA)
            pygame.draw.circle(gs2,(140,50,180,int(pulse2*50+20)),(31,31),29)
            surf.blit(gs2,(cx-31,cy-31))
            # Burn ring (lv1+)
            if lv2>=1:
                brs=pygame.Surface((58,58),pygame.SRCALPHA)
                pygame.draw.circle(brs,(210,100,10,int(pulse2*70+50)),(29,29),26,3)
                surf.blit(brs,(cx-29,cy-29))
            # Spikes
            n_sp=8 if lv2>=2 else 4
            sp_len=6+lv2*3
            for i in range(n_sp):
                ang2=math.pi*2*i/n_sp-math.pi/2
                sx1=cx+math.cos(ang2)*20; sy1=cy+math.sin(ang2)*20
                sx2=cx+math.cos(ang2)*(20+sp_len); sy2=cy+math.sin(ang2)*(20+sp_len)
                col2=(255,240,60) if lv2>=3 else (200,80,200)
                pygame.draw.line(surf,col2,(int(sx1),int(sy1)),(int(sx2),int(sy2)),2)
            # Body hex
            hpts=[(cx+int(math.cos(math.pi*2*i/6-math.pi/6)*18),cy+int(math.sin(math.pi*2*i/6-math.pi/6)*18)) for i in range(6)]
            pygame.draw.polygon(surf,(42,14,68),hpts)
            pygame.draw.polygon(surf,(88,30,120),hpts,2)
            pygame.draw.circle(surf,(140,50,180),(cx,cy),9)
            pygame.draw.circle(surf,(int(pulse2*40+180),80,int(pulse2*40+180)),(cx,cy),6)
            # Launcher(s)
            a2=0.0
            ca2,sa2=math.cos(a2),math.sin(a2)
            if lv2<=1:
                pygame.draw.line(surf,(88,30,120),(cx+int(ca2*6),cy+int(sa2*6)),(cx+int(ca2*22),cy+int(sa2*22)),5)
                pygame.draw.line(surf,(200,80,200),(cx+int(ca2*6),cy+int(sa2*6)),(cx+int(ca2*22),cy+int(sa2*22)),3)
                pygame.draw.circle(surf,(230,120,240),(cx+int(ca2*22),cy+int(sa2*22)),4)
            elif lv2==2:
                for off2 in (0.16,-0.16):
                    ao=a2+off2; cao=math.cos(ao); sao=math.sin(ao)
                    pygame.draw.line(surf,(88,30,120),(cx+int(cao*6),cy+int(sao*6)),(cx+int(cao*22),cy+int(sao*22)),4)
                    pygame.draw.line(surf,(200,80,200),(cx+int(cao*6),cy+int(sao*6)),(cx+int(cao*22),cy+int(sao*22)),2)
                    pygame.draw.circle(surf,(230,120,240),(cx+int(cao*22),cy+int(sao*22)),3)
            else:
                for off2 in (0.22,0.0,-0.22):
                    ao=a2+off2; cao=math.cos(ao); sao=math.sin(ao)
                    pygame.draw.line(surf,(88,30,120),(cx+int(cao*6),cy+int(sao*6)),(cx+int(cao*24),cy+int(sao*24)),4)
                    pygame.draw.line(surf,(200,80,200),(cx+int(cao*6),cy+int(sao*6)),(cx+int(cao*24),cy+int(sao*24)),2)
                    pygame.draw.circle(surf,(230,120,240),(cx+int(cao*24),cy+int(sao*24)),3)
            # Level pips
            for i in range(lv2):
                pygame.draw.circle(surf,(210,100,10),(cx-9+i*6,cy+30),3)
        elif isinstance(u,SpotlightTech):
            t2=pygame.time.get_ticks()*0.001
            # Arctic blue body
            pygame.draw.circle(surf,C_SPOTLIGHT_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_SPOTLIGHT,(cx,cy),22)
            pygame.draw.circle(surf,(200,240,255),(cx,cy),22,2)
            pygame.draw.circle(surf,(80,160,220),(cx,cy),28,2)
            # Ice beam fan — white-blue rays
            a2=u._beam_angle
            ca2,sa2=math.cos(a2),math.sin(a2)
            for i in range(5):
                frac=(i/4-0.5)*0.6
                ex2=cx+int((ca2*24+(-sa2)*frac*20)); ey2=cy+int((sa2*24+ca2*frac*20))
                alpha2=max(0,140-abs(i-2)*40)
                beam_s=pygame.Surface((6,6),pygame.SRCALPHA)
                pygame.draw.circle(beam_s,(180,230,255,alpha2),(3,3),3)
                surf.blit(beam_s,(ex2-3,ey2-3))
            # Lens glow — ice blue
            lx2=cx+int(ca2*15); ly2=cy+int(sa2*15)
            gs2=pygame.Surface((16,16),pygame.SRCALPHA)
            gp=int(abs(math.sin(t2*4))*80+140)
            pygame.draw.circle(gs2,(160,220,255,gp),(8,8),7)
            pygame.draw.circle(gs2,(230,245,255,255),(8,8),3)
            surf.blit(gs2,(lx2-8,ly2-8))
        elif isinstance(u,Farm):
            pygame.draw.circle(surf,C_FARM_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_FARM,(cx,cy),22)
            ico_farm=load_icon("money_ico",22)
            if ico_farm:
                surf.blit(ico_farm,(cx-11,cy-11))
            else:
                txt(surf,"$",(cx,cy),C_GOLD,font_md,center=True)
        elif isinstance(u,Jester):
            t2=pygame.time.get_ticks()*0.001
            # Dark aura
            aura_s=pygame.Surface((60,60),pygame.SRCALPHA)
            pygame.draw.circle(aura_s,(80,20,160,50),(30,30),30)
            surf.blit(aura_s,(cx-30,cy-30))
            # Body
            pygame.draw.circle(surf,C_JESTER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_JESTER,(cx,cy),22)
            pygame.draw.circle(surf,(200,170,40),(cx,cy),22,2)  # gold rim
            # Mini three-point hat
            tip_c2=(cx,cy-38); tip_l2=(cx-14,cy-28); tip_r2=(cx+14,cy-28)
            hat_pts2=[( cx-9,cy-20),tip_l2,tip_c2,tip_r2,(cx+9,cy-20)]
            pygame.draw.polygon(surf,(18,8,40),hat_pts2)
            pygame.draw.polygon(surf,(90,30,160),[(cx-9,cy-20),tip_l2,(cx-2,cy-27)]) # left panel
            pygame.draw.polygon(surf,(90,30,160),[(cx+9,cy-20),tip_r2,(cx+2,cy-27)]) # right panel
            pygame.draw.polygon(surf,(170,130,20),[(cx-2,cy-27),tip_c2,(cx+2,cy-27)]) # center
            pygame.draw.polygon(surf,(200,170,40),hat_pts2,1)
            for tip2 in (tip_c2,tip_l2,tip_r2):
                pygame.draw.circle(surf,(200,160,20),tip2,3)
                pygame.draw.circle(surf,(255,220,80),tip2,2)
            # Orbiting bomb dot
            ba=math.radians(t2*140)
            bomb_col=(255,100,30)
            bg_s2=pygame.Surface((14,14),pygame.SRCALPHA)
            pygame.draw.circle(bg_s2,(255,100,30,80),(7,7),6)
            surf.blit(bg_s2,(cx+int(math.cos(ba)*14)-7,cy+int(math.sin(ba)*9)-7))
            pygame.draw.circle(surf,bomb_col,(cx+int(math.cos(ba)*14),cy+int(math.sin(ba)*9)),4)
        elif isinstance(u, SoulWeaver):
            t2 = pygame.time.get_ticks() * 0.001
            pulse = abs(math.sin(t2 * 1.8))
            aura_s = pygame.Surface((56, 56), pygame.SRCALPHA)
            pygame.draw.circle(aura_s, (160, 80, 255, int(30 + pulse * 50)), (28, 28), 27)
            surf.blit(aura_s, (cx - 28, cy - 28))
            pygame.draw.circle(surf, C_SOULWEAVER_DARK, (cx, cy), 28)
            pygame.draw.circle(surf, C_SOULWEAVER,      (cx, cy), 22)
            ring_s = pygame.Surface((48, 48), pygame.SRCALPHA)
            pygame.draw.circle(ring_s, (*C_SOULWEAVER, int(120 + pulse * 80)), (24, 24), 22, 2)
            surf.blit(ring_s, (cx - 24, cy - 24))
            pygame.draw.ellipse(surf, (220, 180, 255), (cx - 9, cy - 5, 18, 10), 2)
            pygame.draw.circle(surf, (255, 220, 255), (cx + int(math.sin(t2 * 0.7) * 3), cy), 4)
            for i, angle in enumerate([t2 * 1.2, t2 * 1.2 + 2.09, t2 * 1.2 + 4.19]):
                ox = cx + int(math.cos(angle) * 32)
                oy = cy + int(math.sin(angle) * 32)
                pygame.draw.circle(surf, (200, 140, 255), (ox, oy), 5)
                pygame.draw.circle(surf, (255, 220, 255), (ox, oy), 5, 1)
        elif isinstance(u, Swarmer):
            pygame.draw.circle(surf, C_SWARMER_DARK, (cx, cy), 28)
            pygame.draw.circle(surf, C_SWARMER,      (cx, cy), 22)
            # Mini соты
            for hx, hy in [(0,0),(-7,-6),(7,-6),(-7,6),(7,6)]:
                pts = []
                for k in range(6):
                    a2 = math.radians(60*k+30)
                    pts.append((cx+hx+int(math.cos(a2)*4), cy+hy+int(math.sin(a2)*4)))
                pygame.draw.polygon(surf, (200,140,0), pts)
                pygame.draw.polygon(surf, (80,40,0), pts, 1)
        elif isinstance(u, Harvester):
            t_ico = getattr(u, '_anim_t', 0.0)
            pygame.draw.circle(surf, (18, 55, 18), (cx, cy), 24)
            pygame.draw.circle(surf, (38, 110, 38),(cx, cy), 18)
            for i in range(3):
                base_a = t_ico * 2.0 + i * (math.pi * 2 / 3)
                pts_ico = []
                for step in range(7):
                    frac = step / 6.0
                    a_o = base_a + frac * 0.9
                    r_o = int(10 + frac * 9)
                    pts_ico.append((cx + int(math.cos(a_o)*r_o), cy + int(math.sin(a_o)*r_o)))
                for step in range(7):
                    frac = (6-step)/6.0
                    a_i = base_a + frac * 0.9
                    r_i = int(4 + frac * 4)
                    pts_ico.append((cx + int(math.cos(a_i)*r_i), cy + int(math.sin(a_i)*r_i)))
                if len(pts_ico) >= 3:
                    pygame.draw.polygon(surf, (55, 175, 55), pts_ico)
            pygame.draw.circle(surf, (80, 200, 80), (cx, cy), 5)
            pygame.draw.circle(surf, (200, 255, 150),(cx, cy), 2)
        elif isinstance(u, ControlPanel):
            t2 = pygame.time.get_ticks() * 0.001
            pulse2 = abs(math.sin(t2 * 1.8))
            C_CP2  = (40, 180, 220)
            C_CPD2 = (10, 60,  90)
            # glow
            glow_s2 = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow_s2, (*C_CP2, int(pulse2 * 40 + 15)), (30, 30), 29)
            surf.blit(glow_s2, (cx - 30, cy - 30))
            # body
            b2 = pygame.Rect(cx - 20, cy - 18, 40, 36)
            pygame.draw.rect(surf, C_CPD2, b2, border_radius=7)
            pygame.draw.rect(surf, C_CP2,  b2, 2, border_radius=7)
            # screen
            scr_col2 = (int(20 + pulse2 * 40), int(160 + pulse2 * 60), int(200 + pulse2 * 30))
            s2 = pygame.Rect(cx - 15, cy - 13, 30, 14)
            pygame.draw.rect(surf, (10, 20, 35), s2, border_radius=3)
            pygame.draw.rect(surf, scr_col2, s2, 1, border_radius=3)
            for row in range(3):
                sl2 = pygame.Surface((28, 1), pygame.SRCALPHA)
                sl2.fill((*scr_col2, int(80 + pulse2 * 60)))
                surf.blit(sl2, (s2.x + 1, s2.y + 3 + row * 4))
            # animated dot
            dot_x2 = cx + int(math.sin(t2 * 3.0) * 10)
            ds2 = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ds2, (*C_CP2, 220), (3, 3), 3)
            surf.blit(ds2, (dot_x2 - 3, cy - 9))
            # buttons
            for bx_o in (-7, 7):
                pygame.draw.circle(surf, (60, 180, 140), (cx + bx_o, cy + 12), 4)
                pygame.draw.circle(surf, (100, 220, 180), (cx + bx_o, cy + 12), 4, 1)
            # antenna
            pygame.draw.line(surf, C_CP2, (cx, cy - 18), (cx, cy - 32), 2)
            blink_a2 = int(abs(math.sin(t2 * 4.0)) * 200 + 55)
            ts2 = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(ts2, (*C_CP2, blink_a2), (4, 4), 3)
            surf.blit(ts2, (cx - 4, cy - 36))
        elif isinstance(u, Felyne):
            _draw_tower_icon(surf, "Korzhik", cx, cy, pygame.time.get_ticks()*0.001, size=30)
        elif isinstance(u, Castbound):
            _draw_tower_icon(surf, "Castbound", cx, cy, pygame.time.get_ticks()*0.001, size=30)
        else:
            pygame.draw.circle(surf,(70,40,100),(cx,cy),28)
            pygame.draw.circle(surf,u.COLOR,(cx,cy),22)

    def _sell_value(self, unit):
        """30% of place cost + all upgrade costs paid."""
        total=unit.PLACE_COST
        cls=type(unit)
        if cls==Assassin: levels=ASSASSIN_LEVELS; cost_idx=3
        elif cls==Accelerator: levels=ACCEL_LEVELS; cost_idx=3
        elif cls==Frostcelerator: levels=FROST_LEVELS; cost_idx=3
        elif cls==Lifestealer: levels=LIFESTEALER_LEVELS; cost_idx=3
        elif cls==Archer: levels=ARCHER_LEVELS; cost_idx=3
        elif cls==RedBall: levels=REDBALL_LEVELS; cost_idx=2
        elif cls==Farm: levels=FARM_LEVELS; cost_idx=1
        elif cls==Freezer: levels=FREEZER_LEVELS; cost_idx=3
        elif cls==FrostBlaster: levels=FROSTBLASTER_LEVELS; cost_idx=3
        elif cls==Sledger: levels=SLEDGER_LEVELS; cost_idx=3
        elif cls==Gladiator: levels=GLADIATOR_LEVELS; cost_idx=3
        elif cls==ToxicGunner: levels=TOXICGUN_LEVELS; cost_idx=5
        elif cls==Slasher: levels=SLASHER_LEVELS; cost_idx=3
        elif cls==GoldenCowboy: levels=GCOWBOY_LEVELS; cost_idx=3
        elif cls==HallowPunk: levels=HALLOWPUNK_LEVELS; cost_idx=3
        elif cls==SpotlightTech: levels=SPOTLIGHTTECH_LEVELS; cost_idx=3
        elif cls==Snowballer: levels=SNOWBALLER_LEVELS; cost_idx=3
        elif cls==Commando: levels=COMMANDO_LEVELS; cost_idx=3
        elif cls==Jester: levels=JESTER_LEVELS; cost_idx=3
        elif cls==SoulWeaver: levels=_SW_LEVELS; cost_idx=1
        elif cls==RubberDuck: levels=DUCK_LEVELS; cost_idx=3
        elif cls==Swarmer: levels=SWARMER_LEVELS; cost_idx=3
        elif cls==Harvester: levels=HARVESTER_LEVELS; cost_idx=3
        elif cls==Conduit: levels=CONDUIT_LEVELS; cost_idx=3
        elif cls==ControlPanel: levels=[]; cost_idx=3   # no upgrades, only placement cost
        elif cls==Militant: levels=MILITANT_LEVELS; cost_idx=3
        elif cls==Twitgunner: levels=TWITGUN_LEVELS; cost_idx=3
        elif cls==Felyne: levels=FELYNE_LEVELS; cost_idx=3
        elif cls==Caster: levels=CASTER_LEVELS; cost_idx=3
        elif cls==Warlock: levels=WARLOCK_LEVELS; cost_idx=6
        else: levels=[]; cost_idx=3
        for i in range(1,unit.level+1):
            if i<len(levels) and levels[i][cost_idx]: total+=levels[i][cost_idx]
        return int(total*0.30)

    def _get_next_stats(self, unit):
        """Return dict of next-level stats for comparison, or None if max."""
        cls=type(unit)
        nxt=unit.level+1
        if cls==Assassin:
            if nxt>=len(ASSASSIN_LEVELS): return None
            d,fr,r,_=ASSASSIN_LEVELS[nxt]
            hd=nxt>=1
            return {"Damage":d,"Firerate":fr,"Range":r,"HidDet":hd}
        elif cls==Accelerator:
            if nxt>=len(ACCEL_LEVELS): return None
            d,fr,r,_,dual=ACCEL_LEVELS[nxt]
            return {"Damage":d,"Firerate":fr,"Range":r,"Dual":dual}
        elif cls==Freezer:
            if nxt>=len(FREEZER_LEVELS): return None
            d,fr,r,_,sp,sd=FREEZER_LEVELS[nxt]
            return {"Damage":d,"Firerate":fr,"Range":r,"Slow":f"{int(sp*100)}%/{sd:.0f}s"}
        elif cls==Frostcelerator:
            if nxt>=len(FROST_LEVELS): return None
            d,fr,r,_=FROST_LEVELS[nxt]
            return {"Damage":d,"Firerate":fr,"Range":r}
        elif cls==Lifestealer:
            if nxt>=len(LIFESTEALER_LEVELS): return None
            d,fr,r,_,mp=LIFESTEALER_LEVELS[nxt]
            return {"Damage":d,"Firerate":fr,"Range":r,"Money":f"{int(mp*100)}% HP"}
        elif cls==Archer:
            if nxt>=len(ARCHER_LEVELS): return None
            d,fr,r,_,mh=ARCHER_LEVELS[nxt]
            hd=nxt>=2
            return {"Damage":d,"Firerate":fr,"Range":r,"Penetration":mh,"HidDet":hd}
        elif cls==RedBall:
            if nxt>=len(REDBALL_LEVELS): return None
            d,fr,_=REDBALL_LEVELS[nxt]
            return {"Damage":d,"Firerate":fr}
        elif cls==Farm:
            if nxt>=len(FARM_LEVELS): return None
            income,_=FARM_LEVELS[nxt]
            return {"Income":income}
        elif cls==FrostBlaster:
            if nxt>=len(FROSTBLASTER_LEVELS): return None
            d,fr,r,_,hd,sp,sd,fh,fd,ash,dd,ps=FROSTBLASTER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Slow":f"{int(sp*100)}%/{sd:.2f}s",
                    "Freeze":f"x{fh}/{fd:.2f}s","HidDet":hd}
            if ash>0: result["ArmorShred"]=f"-{int(ash*100)}%"
            if dd>0:  result["DefDrop"]=f"-{int(dd*100)}%"
            return result
        elif cls==Sledger:
            if nxt>=len(SLEDGER_LEVELS): return None
            d,fr,r,_,mh,sph,ms,sd,fd,dbl,dd,asp=SLEDGER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"Hits":mh,
                    "Slow":f"+{int(sph*100)}%/hit max {int(ms*100)}%"}
            if fd>0:  result["Freeze"]=f"{fd:.2f}s"
            if dbl:   result["IceBreaker"]="2x vs frozen"
            if dd>0:  result["DefDrop"]=f"-{int(dd*100)}%/hit"
            if asp>0: result["Aftershock"]=f"{int(asp*100)}% dmg"
            return result
        elif cls==Gladiator:
            if nxt>=len(GLADIATOR_LEVELS): return None
            d,fr,r,_,mh,hd=GLADIATOR_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"Arc Hits":f"{mh} (180°)"}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==ToxicGunner:
            if nxt>=len(TOXICGUN_LEVELS): return None
            d,fr,burst,cd,r,_,sl,sldur,pdmg,ptick,ptime,dd,hd=TOXICGUN_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Burst":f"{burst}/cd{cd:.1f}s","Range":r,
                    "Slow":f"+{int(sl*100)}%"}
            if pdmg>0: result["Poison"]=f"{pdmg}/tick {ptime:.0f}s"
            if dd>0:   result["DefDrop"]=f"-{int(dd*100)}%/tick"
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Slasher:
            if nxt>=len(SLASHER_LEVELS): return None
            d,fr,r,_,ce,cm,hd,bph,bmax,bdmg=SLASHER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"Crit":f"x{cm} every {ce}"}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            if bph>0: result["Bleed"]=f"+{bph}/hit burst@{bmax}"
            return result
        elif cls==GoldenCowboy:
            if nxt>=len(GCOWBOY_LEVELS): return None
            d,fr,r,_,cs,inc,st,hd=GCOWBOY_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"Income":inc}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==HallowPunk:
            if nxt>=len(HALLOWPUNK_LEVELS): return None
            d,fr,r,_,sr,kb,bdmg,bt,btk,hd=HALLOWPUNK_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Splash":f"{sr} tiles","Knockback":f"{kb}px"}
            if bdmg>0: result["Burn"]=f"{bdmg}/tick {bt:.0f}s"
            return result
        elif cls==SpotlightTech:
            if nxt>=len(SPOTLIGHTTECH_LEVELS): return None
            d,fr,r,_,br,bdmg,bt,btk,exp,conf,hd=SPOTLIGHTTECH_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"BeamCircle":f"{br} tiles"}
            if bdmg>0: result["Burn"]=f"{bdmg}/tick {bt:.0f}s"
            if exp and not unit._expose_hidden: result["Expose"]="Hidden Expose"
            if conf>0: result["Confuse"]=f"@{conf} dmg"
            return result
        elif cls==Snowballer:
            if nxt>=len(SNOWBALLER_LEVELS): return None
            d,fr,r,_,sp,sm,sd,ft,fs,expl,sr,db,hd=SNOWBALLER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Slow":f"{int(sp*100)}% max {int(sm*100)}% / {sd:.0f}s"}
            if expl: result["Splash"]=f"{sr} tiles"; result["DefBypass"]="YES"
            if ft>0: result["Freeze"]=f"@{int(ft*100)}% → {fs:.0f}s"
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Commando:
            if nxt>=len(COMMANDO_LEVELS): return None
            d,fr,r,_,burst,bcd,pierce,hd=COMMANDO_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Burst":f"{burst} shots / {bcd:.1f}s cd","Pierce":pierce}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Warlock:
            if nxt>=len(WARLOCK_LEVELS): return None
            row=WARLOCK_LEVELS[nxt]
            md,mfr,mr,rd,rfr,rr,_,hd,mp,kb=row
            result={"Damage":md,"Range":mr,"RangedDamage":rd,"RangedFR":f"{rfr:.3f}","RangedRange":rr}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            if kb>unit._knockback_dist: result["Knockback"]=f"{kb}px / 2 hits"
            if mp>unit._melee_pierce: result["Pierce"]=f"Up to {mp} enemies"
            return result
        elif cls==Jester:
            if nxt>=len(JESTER_LEVELS): return None
            row=JESTER_LEVELS[nxt]
            (d,fr,r,_,bdmg,bdur,_bt,exr,ipct,imax,itm,idd,iexr,pdmg,ptm,ptk,cftm,cfcd,dual,hd)=row
            result={"Damage":d,"Firerate":f"{fr:.3f}","Range":r}
            if bdmg>0: result["Burn"]=f"{bdmg}/tick {bdur:.0f}s"
            if ipct>0: result["IceSlow"]=f"{int(ipct*100)}%/hit max {int(imax*100)}%"
            if idd>0 and unit.level<3: result["IceDef"]=f"-{int(idd*100)}%/hit"
            if pdmg>0 and unit._poison_dmg==0: result["PoisonBomb"]="Unlocks Poison Bomb"
            elif pdmg>0: result["Poison"]=f"{pdmg}/tick {ptm:.0f}s"
            if cftm>0 and unit._conf_time==0: result["ConfBomb"]="Unlocks Confusion Bomb"
            elif cftm>0: result["Confuse"]=f"{cftm:.0f}s/{cfcd:.0f}s cd"
            if dual and not unit._dual: result["Dual"]="Throws 2 bombs"
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==SoulWeaver:
            if nxt>=len(_SW_LEVELS): return None
            r2,_,cd2,max_s=_SW_LEVELS[nxt]
            p2=_SW_SURGE_PARAMS[nxt]
            return {"Range":r2,"MaxStacks":max_s,"AbilCD":f"{cd2:.0f}s",
                    "Surge DMG":f"x{p2[0]:.1f}","Surge FR":f"x{p2[1]:.2f}",
                    "Chain":f"{int(p2[4]*100)}%"}
        elif cls==RubberDuck:
            if nxt>=len(DUCK_LEVELS): return None
            d,fr,r,_,_b,_sr,_sd,hd=DUCK_LEVELS[nxt]
            result={"Damage":d,"Firerate":f"{fr:.2f}","Range":r}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Militant:
            if nxt>=len(MILITANT_LEVELS): return None
            d,fr,r,_=MILITANT_LEVELS[nxt]
            hd=nxt>=2
            result={"Damage":d,"Firerate":fr,"Range":r}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Swarmer:
            if nxt>=len(SWARMER_LEVELS): return None
            bdmg,fr,r,_,st,sl,ti=SWARMER_LEVELS[nxt]
            return {"Bee Dmg":bdmg,"Firerate":f"{fr:.3f}","Range":r,
                    "Sting Time":f"{st:.2f}s","Stack Limit":sl,"Tick":f"{ti:.2f}s"}
        elif cls==Harvester:
            if nxt>=len(HARVESTER_LEVELS): return None
            d,fr,r,_,hd,tdmg,trng,tdur,tslow,ttick=HARVESTER_LEVELS[nxt]
            result={"Damage":d,"Firerate":f"{fr:.3f}","Range":r}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Twitgunner:
            if nxt>=len(TWITGUN_LEVELS): return None
            d,fr,r,_,hd=TWITGUN_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Felyne:
            if nxt>=len(FELYNE_LEVELS): return None
            d,fr,r,_,hd=FELYNE_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Conduit:
            if nxt>=len(CONDUIT_LEVELS): return None
            d,fr,r,_,ccd,jmp=CONDUIT_LEVELS[nxt]
            return {"Damage":d,"Firerate":f"{fr:.3f}","Range":r,
                    "Jumps":jmp,"ChargeCD":f"{ccd:.1f}s"}
        elif cls==ControlPanel:
            return None   # no upgrades
        elif cls==HackerLaserTest:
            if nxt>=len(CASTER_LEVELS): return None
            d,fr,r,_,hd=CASTER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        return None

    def _outline_text(self, surf, text, font, pos, text_col, outline_col=(0,0,0), outline_px=2, center_x=False, center_y=False):
        s_in = font.render(str(text), True, text_col)
        x, y = pos
        if center_x: x -= s_in.get_width() // 2
        if center_y: y -= s_in.get_height() // 2
        for dx in range(-outline_px, outline_px+1):
            for dy in range(-outline_px, outline_px+1):
                if dx==0 and dy==0: continue
                s_out = font.render(str(text), True, outline_col)
                surf.blit(s_out, (x+dx, y+dy))
        surf.blit(s_in, (x, y))
        return pygame.Rect(x, y, s_in.get_width(), s_in.get_height())

    def draw(self,surf,units,money,wave_mgr,player_hp,player_maxhp,enemies,
             boss_enemy=None,extra_boss_bars=None,fallen_boss_bars=None,mode="easy"):
        wave=wave_mgr.wave
        is_sandbox=(mode=="sandbox")
        
        f_lbl = pygame.font.SysFont("segoeui", 20, bold=True)
        f_val = pygame.font.SysFont("segoeui", 28, bold=True)
        
        # Wave Display — y=10 matches the timer on the right for symmetry
        wx, wy_raw = getattr(self, "ui_layout", {}).get("wave", (24, 10))
        wy = max(6, wy_raw)
        
        if is_sandbox:
            wave_str="SANDBOX"
        else:
            wave_str = "--" if wave == 0 else str(wave)
            if wave_mgr.max_waves < 999999: wave_str += f"/{wave_mgr.max_waves}"

        self._outline_text(surf, "Wave:", f_lbl, (wx, wy), C_WHITE, outline_px=2)
        lbl_rect_w = f_lbl.render("Wave:", True, C_WHITE).get_width()
        self._outline_text(surf, wave_str, f_val, (wx + lbl_rect_w//2, wy + 22), C_WHITE, outline_px=3, center_x=True)

        if mode == "hardcore":
            _hc_t = pygame.time.get_ticks() * 0.001
            _pr = min(255, int(180 + abs(math.sin(_hc_t * 2)) * 60))
            _hf = pygame.font.SysFont("consolas", 14, bold=True)
            _hs = _hf.render("☠ HARDCORE BETA", True, (_pr, 50, 50))
            _hbg = pygame.Rect(wx, wy + 52, _hs.get_width() + 10, 16)
            pygame.draw.rect(surf, (30, 5, 5), _hbg, border_radius=3)
            pygame.draw.rect(surf, (120, 20, 20), _hbg, 1, border_radius=3)
            surf.blit(_hs, (_hbg.x + 5, _hbg.y + 1))

        # Base Health (HP bar)
        bx_hp, by_hp_raw = getattr(self, "ui_layout", {}).get("hp", (SCREEN_W//2 - 200, 20))
        by_hp = max(16, by_hp_raw)
        bw_hp = 400; bh_hp = 30
        ratio = max(0, player_hp/player_maxhp)
        
        self._outline_text(surf, "Base Health", f_lbl, (bx_hp + bw_hp//2, by_hp - 28), C_WHITE, outline_px=2, center_x=True)
        
        pygame.draw.rect(surf, (0, 0, 0), (bx_hp-2, by_hp-2, bw_hp+4, bh_hp+4), border_radius=6)
        pygame.draw.rect(surf, (35, 120, 50), (bx_hp, by_hp, bw_hp, bh_hp), border_radius=5)
        if ratio > 0:
            col = (60, 220, 70)
            pygame.draw.rect(surf, col, (bx_hp, by_hp, int(bw_hp*ratio), bh_hp), border_radius=5)
            
        plus_f = pygame.font.SysFont("segoeui", 28, bold=True)
        plus_s = plus_f.render("+", True, (20, 80, 25))
        surf.blit(plus_s, (bx_hp + 8, by_hp + bh_hp//2 - plus_s.get_height()//2 - 1))
        
        hp_str = "∞" if is_sandbox else f"{int(player_hp)}"
        self._outline_text(surf, hp_str, f_lbl, (bx_hp + bw_hp//2, by_hp + bh_hp//2), C_WHITE, outline_px=2, center_x=True, center_y=True)

        tl = wave_mgr.time_left()
        mx_sk, my_sk = pygame.mouse.get_pos()
        if tl is not None:
            tl_ceil = math.ceil(tl); mins = tl_ceil//60; secs = tl_ceil%60
            timer_str = f"{mins:02d}:{secs:02d}"
            
            RIGHT_EDGE = SCREEN_W - 12

            f_time = pygame.font.SysFont("segoeui", 38, bold=True)
            ico_hr = load_icon("firerate_ico", 22)

            # Measure widths to right-align the block
            lbl_surf = f_lbl.render("Time Left:", True, C_WHITE)
            tim_surf = f_time.render(timer_str, True, C_WHITE)
            ico_w = (ico_hr.get_width() + 4) if ico_hr else 0
            block_w = max(ico_w + lbl_surf.get_width(), tim_surf.get_width())

            _timer_pos = getattr(self, "ui_layout", {}).get("timer", None)
            if _timer_pos:
                tx = _timer_pos[0]
                ty = max(6, _timer_pos[1])
            else:
                tx = RIGHT_EDGE - block_w
                ty = 10

            lbl_x = tx
            if ico_hr:
                surf.blit(ico_hr, (tx, ty + 1))
                lbl_x = tx + ico_w
            self._outline_text(surf, "Time Left:", f_lbl, (lbl_x, ty), C_WHITE, outline_px=2)
            tim_cx = tx + block_w // 2
            self._outline_text(surf, timer_str, f_time, (tim_cx, ty + 22), C_WHITE, outline_px=3, center_x=True)
        else:
            self._skip_yes_rect = pygame.Rect(-200, -200, 1, 1)
            self._skip_no_rect = pygame.Rect(-200, -200, 1, 1)
        bar_y=by_hp+51
        if boss_enemy and boss_enemy.alive:
            bbx=200; bby=bar_y; bbw=SCREEN_W-400; bbh=24
            pygame.draw.rect(surf,(20,20,20),(bbx-2,bby-2,bbw+4,bbh+4),border_radius=5)
            pygame.draw.rect(surf,C_HP_BG,(bbx,bby,bbw,bbh),border_radius=4)
            r2=max(0,boss_enemy.hp/boss_enemy.maxhp)
            pygame.draw.rect(surf,(60,200,60),(bbx,bby,int(bbw*r2),bbh),border_radius=4)
            pygame.draw.rect(surf,(140,255,140),(bbx,bby,bbw,bbh),2,border_radius=4)
            txt(surf,f"☠ GRAVE DIGGER   {int(boss_enemy.hp)}/{boss_enemy.maxhp}",
                (bbx+bbw//2,bby+12),(140,255,140),font_sm,center=True)
            bar_y+=28
        if extra_boss_bars:
            for label,hp,maxhp,col in extra_boss_bars:
                bbx=200; bby=bar_y; bbw=SCREEN_W-400; bbh=24
                pygame.draw.rect(surf,(20,20,20),(bbx-2,bby-2,bbw+4,bbh+4),border_radius=4)
                pygame.draw.rect(surf,C_HP_BG,(bbx,bby,bbw,bbh),border_radius=3)
                r2=max(0,hp/maxhp) if maxhp>0 else 0
                pygame.draw.rect(surf,col,(bbx,bby,int(bbw*r2),bbh),border_radius=3)
                pygame.draw.rect(surf,(min(255,col[0]+80),min(255,col[1]+80),min(255,col[2]+80)),(bbx,bby,bbw,bbh),2,border_radius=3)
                txt(surf,f"{label}  {int(hp)}/{int(maxhp)}",(bbx+bbw//2,bby+12),(240,240,240),font_sm,center=True)
                bar_y+=28
        if fallen_boss_bars:
            for label,hp,maxhp,col in fallen_boss_bars:
                bbx=200; bby=bar_y; bbw=SCREEN_W-400; bbh=26
                pygame.draw.rect(surf,(20,20,20),(bbx-2,bby-2,bbw+4,bbh+4),border_radius=5)
                pygame.draw.rect(surf,(40,10,60),(bbx,bby,bbw,bbh),border_radius=4)
                r2=max(0,hp/maxhp) if maxhp>0 else 0
                pygame.draw.rect(surf,col,(bbx,bby,int(bbw*r2),bbh),border_radius=4)
                pygame.draw.rect(surf,(min(255,col[0]+60),min(255,col[1]+60),min(255,col[2]+60)),(bbx,bby,bbw,bbh),2,border_radius=4)
                # Pick readable text color against the bar fill.
                lum = 0.2126*col[0] + 0.7152*col[1] + 0.0722*col[2]
                tcol = (15, 15, 20) if lum > 150 else (245, 245, 250)
                # tiny outline for extra contrast
                msg = f"☠ {label}   {int(hp)}/{int(maxhp)}"
                txt(surf, msg, (bbx+bbw//2+1, bby+13+1), (0,0,0), font_sm, center=True)
                txt(surf, msg, (bbx+bbw//2,   bby+13),   tcol,     font_sm, center=True)
                bar_y+=30
                
        # ── Skip UI ────────────────────────────────────────────────────────
        can_skip = getattr(wave_mgr, 'can_skip', lambda: False)()
        if can_skip and not is_sandbox:
            mx_sk, my_sk = pygame.mouse.get_pos()
            sk_x_raw, sk_y_raw = getattr(self, "ui_layout", {}).get("skip", (SCREEN_W // 2 - 140, bar_y + 20))
            cx = sk_x_raw + 140
            sy = sk_y_raw
            
            f_skip = pygame.font.SysFont("segoeui", 36, bold=True)
            self._outline_text(surf, "Skip Wave?", f_skip, (cx - 120, sy + 40), C_WHITE, outline_px=2, center_x=True, center_y=True)
            
            gx, gy = cx + 20, sy
            gw, gh = 70, 80
            self._skip_yes_rect = pygame.Rect(gx, gy, gw, gh)
            hov_y = self._skip_yes_rect.collidepoint(mx_sk, my_sk)
            
            g_col = (40, 220, 100) if hov_y else (30, 200, 80)
            pygame.draw.rect(surf, (0,0,0), (gx-3, gy-3, gw+6, gh+6), border_radius=10)
            pygame.draw.rect(surf, g_col, (gx, gy, gw, gh), border_radius=7)
            g_bot = (10, 160, 40) if hov_y else (10, 140, 30)
            pygame.draw.rect(surf, g_bot, (gx, gy + 50, gw, 30), border_radius=7)
            pygame.draw.rect(surf, g_bot, (gx, gy + 50, gw, 15))
            pygame.draw.lines(surf, (0,0,0), False, [(gx+16, gy+24), (gx+28, gy+36), (gx+54, gy+10)], 8)
            pygame.draw.lines(surf, C_WHITE, False, [(gx+16, gy+24), (gx+28, gy+36), (gx+54, gy+10)], 5)
            f_zero = pygame.font.SysFont("segoeui", 16, bold=True)
            self._outline_text(surf, "0", f_zero, (gx + gw//2, gy + 65), C_WHITE, outline_px=2, center_x=True, center_y=True)
            
            rx, ry = cx + 110, sy
            rw, rh = 70, 80
            self._skip_no_rect = pygame.Rect(rx, ry, rw, rh)
            hov_n = self._skip_no_rect.collidepoint(mx_sk, my_sk)
            
            r_col = (250, 40, 40) if hov_n else (230, 20, 20)
            pygame.draw.rect(surf, (0,0,0), (rx-3, ry-3, rw+6, rh+6), border_radius=10)
            pygame.draw.rect(surf, r_col, (rx, ry, rw, rh), border_radius=7)
            r_bot = (190, 10, 10) if hov_n else (160, 10, 10)
            pygame.draw.rect(surf, r_bot, (rx, ry + 50, rw, 30), border_radius=7)
            pygame.draw.rect(surf, r_bot, (rx, ry + 50, rw, 15))
            pygame.draw.line(surf, (0,0,0), (rx+20, ry+14), (rx+50, ry+44), 8)
            pygame.draw.line(surf, (0,0,0), (rx+50, ry+14), (rx+20, ry+44), 8)
            pygame.draw.line(surf, C_WHITE, (rx+20, ry+14), (rx+50, ry+44), 5)
            pygame.draw.line(surf, C_WHITE, (rx+50, ry+14), (rx+20, ry+44), 5)
            self._outline_text(surf, "0", f_zero, (rx + rw//2, ry + 65), C_WHITE, outline_px=2, center_x=True, center_y=True)
        else:
            self._skip_yes_rect = pygame.Rect(-200, -200, 1, 1)
            self._skip_no_rect = pygame.Rect(-200, -200, 1, 1)
        # ── Bottom panel background ──────────────────────────────────────────
        panel_h = SCREEN_H - SLOT_AREA_Y
        if not getattr(self, "ui_layout", {}):
            pygame.draw.rect(surf, (14, 17, 26), (0, SLOT_AREA_Y, SCREEN_W, panel_h))
            pygame.draw.line(surf, (50, 58, 80), (0, SLOT_AREA_Y), (SCREEN_W, SLOT_AREA_Y), 2)

        # ── Money display ──────────────────────────────────────
        money_cy = SLOT_AREA_Y + panel_h // 2
        _slots_end_def = (SCREEN_W - (5*SLOT_W + 4*8)) // 2 + 5*SLOT_W + 4*8
        _def_money_x = _slots_end_def + 8   # flush right of slots with small gap
        _def_money_y = SLOT_AREA_Y + 28     # 20px lower than slot top (8+20)
        mx, my = getattr(self, "ui_layout", {}).get("money", (_def_money_x, _def_money_y))
        
        ico_money = load_icon("money_ico", 36)
        if is_sandbox:
            ms = pygame.font.SysFont("segoeui", 28, bold=True).render("∞", True, C_WHITE)
        else:
            ms = pygame.font.SysFont("segoeui", 28, bold=True).render(fmt_num(money), True, C_WHITE)
            
        iw = ico_money.get_width() if ico_money else 0
        total_mw = iw + 6 + ms.get_width()
        
        if getattr(self, "ui_layout", {}):
            draw_rect_alpha(surf, (20,16,8), (mx-10, my-5, total_mw+20, 46), 180, 6)
            pygame.draw.rect(surf, (120,90,20), (mx-10, my-5, total_mw+20, 46), 1, border_radius=6)
        
        if ico_money:
            surf.blit(ico_money, (mx, my))
            mx_off = mx + iw + 6
        else:
            mx_off = mx
            
        surf.blit(ms, (mx_off, my + 18 - ms.get_height() // 2))

        # ── Tower limit counter ──────────────────────────────────────────────
        if not is_sandbox:
            _own_u   = [u for u in units if not getattr(u, '_mp_peer', False)]
            _cur     = len(_own_u)
            _lim     = GLOBAL_UNIT_LIMIT
            # colour: white normally, orange near cap, red at cap
            if _cur >= _lim:
                _lim_col = (255, 80, 60)
            elif _cur >= int(_lim * 0.8):
                _lim_col = (255, 180, 40)
            else:
                _lim_col = C_WHITE
            _lim_str = f"{_cur}/{_lim}"
            # same font/size as money
            _lim_f   = pygame.font.SysFont("segoeui", 28, bold=True)
            _lim_s   = _lim_f.render(_lim_str, True, _lim_col)
            # load tower icon at same size as money icon (36px)
            _ico_lim = load_icon("limit_ico", 36) or load_icon("unit_ico", 36) or load_icon("slot_ico", 36)
            _liw     = _ico_lim.get_width() if _ico_lim else 0
            _total_lw = _liw + 6 + _lim_s.get_width()
            # position: same x as money, one row below
            _lx = mx - 10
            _ly = my + 46          # ~46px below money top = flush below money box
            # same background box style as money

            _lx2 = _lx + 10
            if _ico_lim:
                surf.blit(_ico_lim, (_lx2, _ly + 5))
                _lx2 += _liw + 6
            surf.blit(_lim_s, (_lx2, _ly + 23 - _lim_s.get_height() // 2))

        # ── Slot cards ───────────────────────────────────────────────────────
        _slot_font_name  = pygame.font.SysFont("segoeui", 17, bold=True)
        _slot_font_price = pygame.font.SysFont("segoeui", 15)
        ico_coin = load_icon("money_ico", 15)

        for i, slot in enumerate(self.slots):
            UType = self.SLOT_TYPES[i]
            sel   = (i == self.selected_slot)
            cx2   = slot.centerx
            # Determine availability
            cant_afford = UType is not None and not is_sandbox and money < int(UType.PLACE_COST * getattr(self, 'cost_mult', 1.0))
            over_limit  = False
            if UType is not None:
                lim = UNIT_LIMITS.get(UType.NAME)
                if lim is not None:
                    own_u = [u for u in units if not getattr(u,'_mp_peer',False)]
                    if sum(1 for u in own_u if type(u)==UType) >= lim:
                        over_limit = True
            unavailable = cant_afford or over_limit

            # Card background
            card_col = (38, 52, 82) if sel else (22, 27, 40)
            brd_col  = (100, 140, 220) if sel else (45, 54, 78)
            pygame.draw.rect(surf, card_col, slot, border_radius=12)
            pygame.draw.rect(surf, brd_col,  slot, 2, border_radius=12)

            if UType:
                # Detailed tower icon — centred in card, leaving room for text below
                icon_cy = slot.y + 52
                r_outer = 34
                r_inner = 28
                t = pygame.time.get_ticks() * 0.001
                _is_castbound = UType.NAME == "Castbound"
                # Shadow ring (skip for Castbound)
                if not _is_castbound:
                    pygame.draw.circle(surf, (10, 10, 18), (cx2, icon_cy), r_outer + 3)
                # Draw detailed icon on a sub-surface
                icon_sz = r_inner
                _cb_sz = int(icon_sz * 1.8) if _is_castbound else icon_sz
                _surf_r = r_outer*2+6
                _ic_surf = pygame.Surface((_surf_r*2, _surf_r*2), pygame.SRCALPHA)
                _ic_cx = _surf_r; _ic_cy = _surf_r
                # Dark base circle behind icon (skip for Castbound — no bg)
                if not _is_castbound:
                    pygame.draw.circle(_ic_surf, tuple(max(0, c-60) for c in UType.COLOR),
                                       (_ic_cx, _ic_cy), r_outer)
                if not _is_castbound:
                    if unavailable:
                        _draw_tower_icon(_ic_surf, UType.NAME, _ic_cx, _ic_cy, t, size=_cb_sz)
                        dim_s = pygame.Surface((_surf_r*2, _surf_r*2), pygame.SRCALPHA)
                        pygame.draw.circle(dim_s, (0,0,0,140), (_ic_cx,_ic_cy), r_outer)
                        _ic_surf.blit(dim_s, (0,0))
                    else:
                        _draw_tower_icon(_ic_surf, UType.NAME, _ic_cx, _ic_cy, t, size=_cb_sz)
                if _is_castbound:
                    # Draw Castbound icon directly onto surf — no sub-surface bg
                    _draw_tower_icon(surf, UType.NAME, cx2, icon_cy, t, size=_cb_sz)
                    if unavailable:
                        dim_s2 = pygame.Surface((slot.w, slot.h), pygame.SRCALPHA)
                        pygame.draw.circle(dim_s2, (0,0,0,140), (cx2 - slot.x, icon_cy - slot.y), _cb_sz)
                        surf.blit(dim_s2, (slot.x, slot.y))
                else:
                    surf.blit(_ic_surf, (cx2 - _surf_r, icon_cy - _surf_r))

                # Name
                name_col = (110, 115, 130) if unavailable else (210, 215, 230)
                ns = _slot_font_name.render(UType.NAME, True, name_col)
                surf.blit(ns, ns.get_rect(centerx=cx2, top=slot.y + 94))

                if over_limit:
                    ps = _slot_font_price.render("LIMIT", True, (200, 80, 80))
                    surf.blit(ps, ps.get_rect(centerx=cx2, top=slot.y + 114))
                else:
                    price_col = (200, 80, 80) if cant_afford else C_GOLD
                    price_str = str(int(UType.PLACE_COST * getattr(self, 'cost_mult', 1.0)))
                    ps = _slot_font_price.render(price_str, True, price_col)
                    row_w = (ico_coin.get_width() + 3 + ps.get_width()) if ico_coin else ps.get_width()
                    rx = cx2 - row_w // 2
                    ry = slot.y + 115
                    if ico_coin:
                        surf.blit(ico_coin, (rx, ry + (ps.get_height() - ico_coin.get_height()) // 2))
                        surf.blit(ps, (rx + ico_coin.get_width() + 3, ry))
                    else:
                        surf.blit(ps, ps.get_rect(centerx=cx2, top=ry))
            else:
                pass

        # ── Speed button (left of loadout) ───────────────────────────────────
        spd_val = self._SPEED_STEPS[self._speed_idx]
        spd_btn = self._speed_btn
        mx_s, my_s = pygame.mouse.get_pos()
        hov_spd = spd_btn.collidepoint(mx_s, my_s)
        # Color by speed: slow=blue, normal=gray, fast=orange/red
        if spd_val < 1.0:   spd_accent = (60, 140, 255)
        elif spd_val == 1.0: spd_accent = (80, 90, 120)
        else:               spd_accent = (255, 140, 40)
        spd_bg = tuple(min(255, c + (20 if hov_spd else 0)) for c in (18, 22, 38))
        pygame.draw.rect(surf, spd_bg, spd_btn, border_radius=10)
        pygame.draw.rect(surf, spd_accent, spd_btn, 2, border_radius=10)
        spdf = pygame.font.SysFont("consolas", 13, bold=True)
        spd_lbl = f"x{spd_val:.2f}".rstrip('0').rstrip('.')
        if spd_val == 0.25: spd_lbl = "x0.25"
        elif spd_val == 0.50: spd_lbl = "x0.50"
        spd_s1 = pygame.font.SysFont("segoeui", 11).render("SPEED", True, (120, 130, 160))
        spd_s2 = pygame.font.SysFont("consolas", 20, bold=True).render(spd_lbl, True, spd_accent)
        spd_s3 = pygame.font.SysFont("segoeui", 10).render("click to cycle", True, (80, 90, 110))
        surf.blit(spd_s1, spd_s1.get_rect(centerx=spd_btn.centerx, top=spd_btn.y + 8))
        surf.blit(spd_s2, spd_s2.get_rect(centerx=spd_btn.centerx, centery=spd_btn.centery + 6))
        surf.blit(spd_s3, spd_s3.get_rect(centerx=spd_btn.centerx, bottom=spd_btn.bottom - 6))

        # ── Admin button (sandbox / admin-mode, bottom right of loadout) ──────
        if self.admin_mode:
            # Recalculate position every frame — левее кнопки speed
            self._admin_btn_rect = pygame.Rect(spd_btn.x - 112, SLOT_AREA_Y + 8, 100, SLOT_H)
            adm_btn = self._admin_btn_rect
            mx_a, my_a = pygame.mouse.get_pos()
            adm_hov = adm_btn.collidepoint(mx_a, my_a)
            adm_open = self.admin_panel.visible
            adm_accent = (100, 220, 80) if adm_open else ((120, 180, 255) if adm_hov else (70, 100, 180))
            adm_bg = (16, 36, 16) if adm_open else ((22, 34, 55) if adm_hov else (14, 18, 32))
            pygame.draw.rect(surf, adm_bg, adm_btn, border_radius=10)
            pygame.draw.rect(surf, adm_accent, adm_btn, 2, border_radius=10)
            adm_lbl1 = pygame.font.SysFont("segoeui", 11).render("ADMIN", True, (90, 170, 90) if adm_open else (100, 130, 160))
            adm_lbl2 = pygame.font.SysFont("segoeui", 26, bold=True).render("⚙", True, adm_accent)
            adm_lbl3 = pygame.font.SysFont("segoeui", 10).render("panel", True, (60, 110, 60) if adm_open else (70, 85, 105))
            surf.blit(adm_lbl1, adm_lbl1.get_rect(centerx=adm_btn.centerx, top=adm_btn.y + 6))
            surf.blit(adm_lbl2, adm_lbl2.get_rect(centerx=adm_btn.centerx, centery=adm_btn.centery + 4))
            surf.blit(adm_lbl3, adm_lbl3.get_rect(centerx=adm_btn.centerx, bottom=adm_btn.bottom - 6))
        mx2,my2=pygame.mouse.get_pos()
        for u in units:
            if SETTINGS.get("show_range_always", False):
                u.draw_range(surf)
            elif dist((u.px,u.py),(mx2,my2))<22 and self.open_unit!=u: u.draw_range(surf)
        if self.open_unit:
            u=self.open_unit; u.draw_range(surf)

            menu,btns=self._menu_rects(u)
            self._cached_btns=btns  # will be overwritten after draw updates them
            mw=menu.w; mx_m=menu.x; my_m=menu.y

            # === BACKGROUND ===
            draw_rect_alpha(surf,(20,16,36),menu,248,6)
            pygame.draw.rect(surf,(55,44,82),menu,2,border_radius=6)

            cls=type(u)
            nxt=self._get_next_stats(u)
            levels_map={Assassin:ASSASSIN_LEVELS,Accelerator:ACCEL_LEVELS,Frostcelerator:FROST_LEVELS,Lifestealer:LIFESTEALER_LEVELS,Archer:ARCHER_LEVELS,RedBall:REDBALL_LEVELS,FrostBlaster:FROSTBLASTER_LEVELS,Freezer:FREEZER_LEVELS,Sledger:SLEDGER_LEVELS,Gladiator:GLADIATOR_LEVELS,ToxicGunner:TOXICGUN_LEVELS,Slasher:SLASHER_LEVELS,GoldenCowboy:GCOWBOY_LEVELS,HallowPunk:HALLOWPUNK_LEVELS,SpotlightTech:SPOTLIGHTTECH_LEVELS,Snowballer:SNOWBALLER_LEVELS,Commando:COMMANDO_LEVELS,Caster:CASTER_LEVELS,HackerLaserTest:CASTER_LEVELS,Warlock:WARLOCK_LEVELS,RubberDuck:DUCK_LEVELS,Militant:MILITANT_LEVELS,Swarmer:SWARMER_LEVELS,Farm:FARM_LEVELS,Harvester:HARVESTER_LEVELS,Twitgunner:TWITGUN_LEVELS,Felyne:FELYNE_LEVELS,Conduit:CONDUIT_LEVELS,Castbound:CASTBOUND_LEVELS}
            lvl_list=levels_map.get(cls,[])
            if cls==Jester: lvl_list=JESTER_LEVELS
            total_lvls=len(lvl_list)

            # ── Apply skill-tree range multiplier to next-level Range display ──
            # Ensures the upgrade menu shows "next range" including Enhanced Optics bonus
            _sk_rng = getattr(self, '_sk_range_bonus', 0)
            if nxt and "Range" in nxt and _sk_rng > 0:
                _raw_nxt_r = nxt["Range"]
                if _raw_nxt_r and _raw_nxt_r > 0:
                    _scaled_r = round(_raw_nxt_r * (1.0 + _sk_rng), 4)
                    nxt["Range"] = int(_scaled_r) if _scaled_r == int(_scaled_r) else _scaled_r

            # Build stats list: (key, display_val, next_val_or_None)
            # HidDet: shown in stats only if already active; shown in "changes" if it unlocks next
            STAT_ICO={"RangedDamage":"ranged_damage_ico","Damage":"damage_ico","Firerate":"firerate_ico",
                      "Range":"range_ico","Slow":"slow_ico","HidDet":"hidden_detection_ico",
                      "FlameArrow":"flame_ico","IceArrow":"slow_ico","Income":"money_ico",
                      "Pierce":"pierce_ico","Penetration":"pierce_ico","Freeze":"slow_ico",
                      "flame_unlock":"flame_ico","shock_unlock":"damage_ico","explosive_unlock":"damage_ico"}
            ICO_SZ=16

            if cls==Assassin:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",  u.damage,       nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,  nxt.get("Range")    if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
                # Show current ability status or upcoming unlock
                if u.ability:
                    ab=u.ability
                    if ab.ready():
                        stats.append(("Ability",f"Whirlwind: READY",None))
                    else:
                        stats.append(("Ability",f"Whirlwind: {ab.cd_left:.0f}s",None))
                elif u.level==1 and nxt is not None:
                    # lv1 -> lv2 unlocks ability
                    stats.append(("Ability_unlock",None,"+Whirlwind Slash"))
            elif cls==Accelerator:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.4f}", f"{nxt['Firerate']:.4f}" if nxt else None),
                    ("Range",   u.range_tiles,   nxt.get("Range")    if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
                if nxt and nxt.get("Dual") and not u.dual:
                    stats.append(("Dual_unlock",None,"+Dual target"))

            elif cls==Freezer:
                stats=[
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.1f}", f"{nxt['Firerate']:.1f}" if nxt else None),
                    ("Range",   u.range_tiles,   nxt.get("Range")    if nxt else None),
                    ("Slow",    f"{int(u._slow_pct*100)}%/{u._slow_dur:.0f}s", nxt.get("Slow") if nxt else None),
                ]
            elif cls==Frostcelerator:
                stats=[
                    ("HidDet","Hidden Detection", None),
                    ("Slow",    "25%",            None),
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,   nxt.get("Range")    if nxt else None),
                ]
            elif cls==Lifestealer:
                stats=[
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,   nxt.get("Range")    if nxt else None),
                    ("Money",   f"{int(u.money_pct*100)}% HP", nxt.get("Money") if nxt else None),
                ]
            elif cls==Archer:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and not hd_now and (u.level+1)>=2)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",  u.damage,          nxt.get("Damage")    if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,      nxt.get("Range")     if nxt else None),
                    ("Penetration", u.max_hits,     nxt.get("Penetration") if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
                # Unlock banners
                lv_next = u.level + 1
                if lv_next == 3: stats.append(("flame_unlock", None, "Unlocks Flame Arrow"))
                if lv_next == 4: stats.append(("shock_unlock", None, "Unlocks Shock Arrow"))
                if lv_next == 5: stats.append(("explosive_unlock", None, "Unlocks Explosive Arrow"))
            elif cls==RedBall:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and not hd_now and (u.level+1)>=2)
                stats=[]
                if hd_now:
                    stats.append(("HidDet","Hidden Detection", None))
                stats+=[
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.1f}", f"{nxt['Firerate']:.1f}" if nxt else None),
                    ("Range",   u.RANGE_TILES,   None),
                ]
                if hd_next:
                    stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==Farm:
                nxt_income=FARM_LEVELS[u.level+1][0] if u.level+1<len(FARM_LEVELS) else None
                stats=[
                    ("Income", f"+{u.income}", f"+{nxt_income}" if nxt_income else None),
                ]
            elif cls==FrostBlaster:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",  u.damage,           nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,       nxt.get("Range")    if nxt else None),
                    ("Slow",    f"{int(u._slow_pct*100)}%/{u._slow_dur:.2f}s",
                                nxt.get("Slow") if nxt else None),
                    ("Freeze",  f"x{u._freeze_hits}/{u._freeze_dur:.2f}s",
                                nxt.get("Freeze") if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
                if nxt and nxt.get("ArmorShred"): stats.append(("ArmorShred",None,nxt["ArmorShred"]))
                if u._armor_shred>0: stats.append(("ArmorShred",f"-{int(u._armor_shred*100)}% Armor",None))
                if nxt and nxt.get("DefDrop"): stats.append(("DefDrop",None,nxt["DefDrop"]))
                if u._defense_drop>0: stats.append(("DefDrop",f"-{int(u._defense_drop*100)}% Defense",None))
            elif cls==Sledger:
                stats=[
                    ("Damage",  u.damage,           nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,       nxt.get("Range")    if nxt else None),
                    ("Hits",    u._max_hits,          nxt.get("Hits")     if nxt else None),
                    ("Slow",    f"+{int(u._slow_per_hit*100)}%/hit max {int(u._max_slow*100)}%",
                                nxt.get("Slow") if nxt else None),
                ]
                if u._freeze_dur>0:
                    stats.append(("Freeze", f"{u._freeze_dur:.2f}s @max",
                                  nxt.get("Freeze") if nxt else None))
                if u._double_frozen:
                    stats.append(("IceBreaker","2x vs frozen",None))
                elif nxt and nxt.get("IceBreaker"):
                    stats.append(("IceBreaker",None,nxt["IceBreaker"]))
                if u._def_drop>0:
                    stats.append(("DefDrop",f"-{int(u._def_drop*100)}%/hit",None))
                elif nxt and nxt.get("DefDrop"):
                    stats.append(("DefDrop",None,nxt["DefDrop"]))
                if u._aftershock_pct>0:
                    stats.append(("Aftershock",f"{int(u._aftershock_pct*100)}% dmg",None))
                elif nxt and nxt.get("Aftershock"):
                    stats.append(("Aftershock",None,nxt["Aftershock"]))
            elif cls==Gladiator:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,            nxt.get("Damage")    if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",  f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,         nxt.get("Range")    if nxt else None),
                    ("Hits",     f"{u._max_hits} (180°)", nxt.get("Arc Hits") if nxt else None),
                ]
                block_str="READY" if u._stun_block_cd<=0 else f"{u._stun_block_cd:.1f}s"
                stats.append(("StunBlock", f"Block: {block_str}", None))
                if hd_next: stats.append(("HidDet_unlock", None, "Hidden Detection"))
            elif cls==ToxicGunner:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[
                    ("Damage",   u.damage,             nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",   f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Burst",    f"{u._burst_count}/cd{u._cooldown:.1f}s",
                                  nxt.get("Burst") if nxt else None),
                    ("Range",    u.range_tiles,          nxt.get("Range")   if nxt else None),
                    ("Slow",     f"+{int(u._slow_pct*100)}% max 30%",
                                  nxt.get("Slow") if nxt else None),
                ]
                if u._poison_dmg>0:
                    stats.append(("Poison",f"{u._poison_dmg}/tick {u._poison_time:.0f}s",
                                   nxt.get("Poison") if nxt else None))
                elif nxt and nxt.get("Poison"):
                    stats.append(("Poison",None,nxt["Poison"]))
                if u._def_drop>0:
                    stats.append(("DefDrop",f"-{int(u._def_drop*100)}%/tick",None))
                elif nxt and nxt.get("DefDrop"):
                    stats.append(("DefDrop",None,nxt["DefDrop"]))
                if hd_now: stats.insert(0,("HidDet","Hidden Detection",None))
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==Slasher:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                next_crit=u._crit_every-(u._hit_count%u._crit_every)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,             nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",   f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,          nxt.get("Range")   if nxt else None),
                    ("Crit",     f"x{u._crit_mult} every {u._crit_every} (in {next_crit})",
                                  nxt.get("Crit") if nxt else None),
                ]
                if u._bleed_per_hit>0:
                    stats.append(("Bleed",f"+{u._bleed_per_hit}/hit burst@{u._bleed_max}",
                                   nxt.get("Bleed") if nxt else None))
                elif nxt and nxt.get("Bleed"):
                    stats.append(("Bleed",None,nxt["Bleed"]))
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==GoldenCowboy:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,            nxt.get("Damage")    if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",  f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,         nxt.get("Range")    if nxt else None),
                    ("Income",   f"${u._income}",       f"${nxt.get('Income','?')}" if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==HallowPunk:
                stats=[
                    ("Damage",   u.damage,            nxt.get("Damage")    if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",  f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,         nxt.get("Range")    if nxt else None),
                    ("Splash",   f"{u._splash_r} tiles", nxt.get("Splash") if nxt else None),
                    ("Knockback",f"{u._knockback}px",   nxt.get("Knockback") if nxt else None),
                ]
                if u._burn_dmg>0:
                    stats.append(("Burn",f"{u._burn_dmg}/tick {u._burn_time:.0f}s",
                                   nxt.get("Burn") if nxt else None))
                elif nxt and nxt.get("Burn"):
                    stats.append(("Burn",None,nxt["Burn"]))
            elif cls==SpotlightTech:
                stats=[
                    ("Damage",   u.damage,             nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",   f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,          nxt.get("Range")   if nxt else None),
                    ("BeamCircle", f"{u._beam_r} tiles", nxt.get("BeamCircle") if nxt else None),
                    ("Burn",     f"{u._burn_dmg}/tick" if u._burn_dmg else "—",
                                  nxt.get("Burn") if nxt else None),
                    ("Expose",   "YES" if u._expose_hidden else "lv2+", None),
                ]
                if u._conf_thresh>0:
                    conf_str=f"{int(u._conf_accum)}/{u._conf_thresh}"
                    stats.append(("Confuse", conf_str, None))
                elif nxt and nxt.get("Confuse"):
                    stats.append(("Confuse", None, nxt["Confuse"]))
            elif cls==Snowballer:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                    ("Slow",     f"{int(u._slow_pct*100)}% max {int(u._slow_max*100)}% / {u._slow_dur:.0f}s",
                                  nxt.get("Slow") if nxt else None),
                ]
                if u._explosive:
                    stats.append(("Splash", f"{u._splash_r:.1f} tiles", None))
                    stats.append(("DefBypass","YES",None))
                elif nxt and nxt.get("Splash"):
                    stats.append(("Splash",None,nxt["Splash"]))
                    stats.append(("DefBypass",None,"YES"))
                if u._freeze_thresh>0:
                    stats.append(("Freeze",f"@{int(u._freeze_thresh*100)}% → {u._freeze_time:.0f}s",None))
                elif nxt and nxt.get("Freeze"):
                    stats.append(("Freeze",None,nxt["Freeze"]))
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==Commando:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                    ("Burst",    f"{u._burst} shots / {u._burst_cd:.1f}s cd",
                                  nxt.get("Burst") if nxt else None),
                    ("Pierce",   u._pierce,              nxt.get("Pierce")   if nxt else None),
                ]
                if u.level>=2: stats.append(("Grenade","AoE 3-tile splash",None))
                elif nxt and u.level==1: stats.append(("Grenade",None,"AoE 3-tile splash"))
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==Warlock:
                nxt_row=WARLOCK_LEVELS[u.level+1] if u.level+1<len(WARLOCK_LEVELS) else None
                stats=[]
                if u.hidden_detection: stats.append(("HidDet","Hidden Detection",None))
                # Melee
                stats.append(("Damage", u._melee_dmg,
                    nxt_row[0] if nxt_row else None))
                # Ranged
                stats.append(("RangedDamage", u._ranged_dmg,
                    nxt_row[3] if nxt_row else None))
                stats.append(("RangedFR", f"{u._ranged_fr:.3f}",
                    f"{nxt_row[4]:.3f}" if nxt_row else None))
                stats.append(("RangedRange", u._ranged_range,
                    nxt_row[5] if nxt_row else None))
                if u._knockback_dist>0:
                    stats.append(("Knockback",f"{u._knockback_dist}px/2hits",
                        f"{nxt_row[9]}px/2hits" if nxt_row and nxt_row[9]!=u._knockback_dist else None))
                elif nxt_row and nxt_row[9]>0:
                    stats.append(("Knockback",None,f"{nxt_row[9]}px/2hits"))
                if nxt_row and not u.hidden_detection and nxt_row[7]:
                    stats.append(("HidDet_unlock",None,"Hidden Detection"))
                if u._melee_pierce>=2:
                    stats.append(("Pierce",f"Up to {u._melee_pierce} enemies",None))
                elif nxt_row and nxt_row[8]>u._melee_pierce:
                    stats.append(("Pierce",None,f"Up to {nxt_row[8]} enemies"))
            elif cls==Jester:
                hd_next=bool(nxt and nxt.get("HidDet") and not u.hidden_detection)
                stats=[]
                if u.hidden_detection: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",  u.damage,           nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']}" if nxt else None),
                    ("Range",   u.range_tiles,       nxt.get("Range")    if nxt else None),
                ]
                # Bomb unlock notices — sval=None so they only appear in "changing" section
                if nxt and nxt.get("IceSlow") and u._ice_pct==0:
                    stats.append(("IceBomb_unlock", None, "Unlocks Ice Bomb"))
                if nxt and nxt.get("PoisonBomb"):
                    stats.append(("PoisonBomb_unlock", None, "Unlocks Poison Bomb"))
                if nxt and nxt.get("ConfBomb"):
                    stats.append(("ConfBomb_unlock", None, "Unlocks Confusion Bomb"))
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==HackerLaserTest:
                hd_now  = u.hidden_detection
                hd_next = bool(nxt and nxt.get("HidDet") and not hd_now)
                stats   = []
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats += [
                    ("Damage",  u.damage,            nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.2f}",  f"{nxt['Firerate']:.2f}" if nxt else None),
                    ("Range",   u.range_tiles,         nxt.get("Range")    if nxt else None),
                    ("Targets", "∞",                  None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
                if u.level >= 2:
                    stats.append(("Lightning",
                        f"{int(u._charge)}/{LIGHTNING_THRESHOLD} ({LIGHTNING_DAMAGE} dmg)",
                        None))
            elif cls==RubberDuck:
                nxt_row = DUCK_LEVELS[u.level+1] if u.level+1 < len(DUCK_LEVELS) else None
                hd_next = nxt_row and nxt_row[7] and not u.hidden_detection
                _rng_bonus = getattr(self, '_sk_range_bonus', 0)
                _duck_nxt_r = round(nxt_row[2] * (1.0 + _rng_bonus), 4) if nxt_row else None
                stats   = []
                if u.hidden_detection: stats.append(("HidDet","Hidden Detection",None))
                stats += [
                    ("Damage",   u.damage,
                                 nxt_row[0] if nxt_row else None),
                    ("Firerate", f"{u.firerate:.2f}",
                                 f"{nxt_row[1]:.2f}" if nxt_row else None),
                    ("Range",    u.range_tiles,
                                 _duck_nxt_r),
                ]
                if hd_next: stats.append(("HidDet_unlock", None, "Hidden Detection"))
            elif cls==Militant:
                hd_now=u.hidden_detection
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            elif cls==Swarmer:
                stats=[
                    ("Bee Dmg",    u.bee_damage,           nxt.get("Bee Dmg")    if nxt else None),
                    ("Firerate",   f"{u.firerate:.3f}",     nxt.get("Firerate")   if nxt else None),
                    ("Range",      u.range_tiles,           nxt.get("Range")      if nxt else None),
                    ("Sting Time", f"{u.sting_time:.2f}s",  nxt.get("Sting Time") if nxt else None),
                    ("Stack Limit",u.stack_limit,           nxt.get("Stack Limit")if nxt else None),
                    ("Tick",       f"{u.tick_interval:.2f}s",nxt.get("Tick")      if nxt else None),
                ]
            elif cls==Harvester:
                hd_now  = u.hidden_detection
                hd_next = bool(nxt and nxt.get("HidDet") and not hd_now)
                stats = []
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats += [
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock", None, "Hidden Detection"))
            elif cls==Twitgunner:
                hd_now  = u.hidden_detection
                hd_next = bool(nxt and nxt.get("HidDet") and not hd_now)
                stats = []
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats += [
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock", None, "Hidden Detection"))
            elif cls==Felyne:
                hd_now  = u.hidden_detection
                hd_next = bool(nxt and nxt.get("HidDet") and not hd_now)
                stats = []
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats += [
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                ]
                if hd_next: stats.append(("HidDet_unlock", None, "Hidden Detection"))
            elif cls==Conduit:
                stats = [
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    nxt.get("Firerate") if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                    ("Jumps",    u._base_jumps,           nxt.get("Jumps")   if nxt else None),
                    ("ChargeCD", f"{u._charge_max_cd:.1f}s", nxt.get("ChargeCD") if nxt else None),
                ]
            elif cls==ControlPanel:
                ab = u.ability
                stats = [("Type", "Support (no attack)", None),
                         ("Range", u.range_tiles, None)]
                if ab.is_buffing():
                    tgt_name = getattr(ab._active_buff_unit, "NAME",
                                       type(ab._active_buff_unit).__name__)
                    stats.append(("Buffing", f"{ab._active_buff_type}", None))
                    stats.append(("Target",  tgt_name, None))
                    stats.append(("Buff left", f"{ab._active_buff_dur:.1f}s", None))
                stats.append(("AbilCD", "READY" if ab.cd_left <= 0 else f"{ab.cd_left:.1f}s", None))
                stats.append(("AbilCD_max", f"{_CP_ABILITY_CD:.0f}s CD", None))
            elif cls==SoulWeaver:
                nxt_sw = _SW_LEVELS[u.level+1] if u.level+1 < len(_SW_LEVELS) else None
                p_sw = _SW_SURGE_PARAMS[u.level+1] if u.level+1 < len(_SW_SURGE_PARAMS) else None
                _rng_bonus = getattr(self, '_sk_range_bonus', 0)
                _sw_nxt_r = round(nxt_sw[0] * (1.0 + _rng_bonus), 4) if nxt_sw else None
                stats=[
                    ("Range",      u.range_tiles,           _sw_nxt_r),
                    ("MaxStacks",  u.max_stacks,            nxt_sw[3]   if nxt_sw else None),
                    ("AbilCD",     f"{u._cd:.0f}s",          f"{nxt_sw[2]:.0f}s" if nxt_sw else None),
                ]
                if p_sw:
                    stats.append(("Surge DMG", f"x{_SW_SURGE_PARAMS[u.level][0]:.1f}", f"x{p_sw[0]:.1f}"))
                    stats.append(("Surge FR",  f"x{_SW_SURGE_PARAMS[u.level][1]:.2f}", f"x{p_sw[1]:.2f}"))
            elif cls==Castbound:
                nxt_cb = CASTBOUND_LEVELS[u.level+1] if u.level+1 < len(CASTBOUND_LEVELS) else None
                hd_now  = u.hidden_detection
                hd_next = bool(nxt_cb and nxt_cb[8] and not hd_now)
                stats = []
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats += [
                    ("Damage",   u.damage,             nxt_cb[0] if nxt_cb else None),
                    ("Firerate", f"{u.firerate:.2f}",  f"{nxt_cb[1]:.2f}" if nxt_cb else None),
                    ("Range",    u.range_tiles,         nxt_cb[2] if nxt_cb else None),
                ]
                if nxt_cb:
                    if u.level == 0:
                        stats.append(("fire_unlock", None, "Unlocks Fiery Greatsword"))
                    if nxt_cb[5] and not u._terra_unlocked:
                        stats.append(("terra_unlock", None, "Unlocks Terra Blade"))
                    if nxt_cb[6] and not u._star_unlocked:
                        stats.append(("star_unlock",  None, "Unlocks Starfury"))
                    if nxt_cb[4] > u._max_blades:
                        stats.append(("dual_unlock",  None, f"+{nxt_cb[4]-u._max_blades} blade slot"))
                    if nxt_cb[7] and not u._zenith_mode:
                        stats.append(("zenith_unlock",   None, "Unlocks Zenith"))
                        stats.append(("starwrath_unlock", None, "Unlocks Star Wrath"))
                if hd_next: stats.append(("HidDet_unlock",None,"Hidden Detection"))
            else:
                stats=[(k,v,None) for k,v in u.get_info().items()]

            STAT_COLORS={"HidDet":(80,255,120),"HidDet_unlock":(80,255,120),
                         "Damage":(255,120,80),"RangedDamage":(255,160,80),"Firerate":(255,220,60),
                         "Range":(80,200,255),"Dual_unlock":(200,100,255),"Slow":(100,200,255),
                         "Money":(220,60,80),"Pierce":(200,160,80),"Penetration":(200,160,80),
                         "Bee Dmg":(255,200,40),"Sting Time":(255,180,0),"Stack Limit":(255,220,80),"Tick":(200,200,100),
                         "FlameArrow":(255,130,30),"FlameArrow_unlock":(255,130,30),
                         "ShockArrow":(100,180,255),"ShockArrow_unlock":(100,180,255),
                         "ExplosiveArrow":(255,80,30),"ExplosiveArrow_unlock":(255,80,30),
                         "flame_unlock":(255,130,30),"shock_unlock":(100,180,255),"explosive_unlock":(255,80,30),
                         "IceArrow":(100,200,255),"IceArrow_unlock":(100,200,255),
                         "Income":(100,220,80),"Ability":(200,150,255),"Ability_unlock":(200,150,255),
                         "Freeze":(160,230,255),"ArmorShred":(255,160,60),"DefDrop":(255,100,80),
                         "Hits":(200,200,100),"IceBreaker":(100,220,255),"Aftershock":(140,200,255),
                         "StunBlock":(255,220,80),
                         "Poison":(100,220,80),"Crit":(255,160,40),"Bleed":(200,40,40),
                         "CashShot":(255,220,60),"SpinTime":(200,180,100),
                         "Burn":(255,130,30),"Knockback":(200,160,255),"Splash":(220,100,220),
                         "BeamCircle":(255,240,80),"Expose":(100,255,200),"Confuse":(200,100,255),
                         "IceSlow":(100,200,255),"IceDef":(140,200,255),"Dual":(200,120,255),
                         "IceBomb_unlock":(80,200,255),"PoisonBomb_unlock":(80,220,60),"ConfBomb_unlock":(200,80,255),
                         "terra_unlock":(100,220,80),"star_unlock":(255,200,60),"dual_unlock":(200,160,255),
                         "zenith_unlock":(120,200,255),"starwrath_unlock":(180,80,255),
                         "Blades":(180,140,255),}

            # === TOP HALF: portrait left + STATS right ===
            # For Frostcelerator: stun bar at very top of card
            top_offset=4
            if isinstance(u,Caster) and u.level>=2:
                bar_x=mx_m+6; bar_w=mw-12; bar_y=my_m+top_offset+14
                frac=min(1.0,u._charge/LIGHTNING_THRESHOLD)
                lbl_s=font_sm.render(f"Lightning: {int(u._charge)}/{LIGHTNING_THRESHOLD}",True,C_HACKER)
                surf.blit(lbl_s,(bar_x,my_m+top_offset))
                pygame.draw.rect(surf,(10,25,55),(bar_x,bar_y,bar_w,9),border_radius=4)
                fill_col=(40,200,255) if frac<1.0 else (200,240,255)
                pygame.draw.rect(surf,fill_col,(bar_x,bar_y,int(bar_w*frac),9),border_radius=4)
                pygame.draw.rect(surf,C_HACKER,(bar_x,bar_y,bar_w,9),1,border_radius=4)
                top_offset+=26
            if isinstance(u,Frostcelerator):
                bar_x=mx_m+6; bar_w=mw-12; bar_y=my_m+top_offset+14
                frac=min(1.0,u._shared_dmg/1000)
                stun_s=font_sm.render(f"Stun: {int(u._shared_dmg)}/1000",True,(120,200,255))
                surf.blit(stun_s,(bar_x,my_m+top_offset))
                pygame.draw.rect(surf,(15,38,65),(bar_x,bar_y,bar_w,9),border_radius=4)
                pygame.draw.rect(surf,C_FROST,(bar_x,bar_y,int(bar_w*frac),9),border_radius=4)
                pygame.draw.rect(surf,(55,150,210),(bar_x,bar_y,bar_w,9),1,border_radius=4)
                top_offset+=26
            if isinstance(u,Castbound):
                _CB_CHARGE_MAX = 1500
                _cb_charge = getattr(u, '_terraprisma_charge', 0.0)
                _cb_count  = len(getattr(u, '_terraprismas', []))
                bar_x=mx_m+6; bar_w=mw-12; bar_y=my_m+top_offset+14
                frac=min(1.0, _cb_charge / _CB_CHARGE_MAX)
                _tp_col = (180, 50, 255)
                lbl_s=font_sm.render(
                    f"Terraprisma: {int(_cb_charge)}/{_CB_CHARGE_MAX}  [{_cb_count}/3 active]",
                    True, _tp_col)
                surf.blit(lbl_s,(bar_x,my_m+top_offset))
                pygame.draw.rect(surf,(20,5,35),(bar_x,bar_y,bar_w,9),border_radius=4)
                pygame.draw.rect(surf,_tp_col,(bar_x,bar_y,int(bar_w*frac),9),border_radius=4)
                pygame.draw.rect(surf,(120,0,200),(bar_x,bar_y,bar_w,9),1,border_radius=4)
                top_offset+=26

            # Portrait square (left column)
            portrait_size=150
            portrait_rect=pygame.Rect(mx_m+6,my_m+top_offset,portrait_size,portrait_size)
            self._draw_unit_portrait(surf,u,portrait_rect)

            # === TARGET — inside portrait cube, bottom strip ===
            cur_mode=getattr(u,'target_mode','First')
            tp_zone_h=32
            tp_x=portrait_rect.x; tp_y=portrait_rect.bottom-tp_zone_h
            tp_w=portrait_size
            # ◄ mode ► — just text and arrows, no box
            arr_w=18; arr_h=18
            btn_prev=pygame.Rect(tp_x+4, tp_y+(tp_zone_h-arr_h)//2, arr_w, arr_h)
            btn_next=pygame.Rect(tp_x+tp_w-arr_w-4, tp_y+(tp_zone_h-arr_h)//2, arr_w, arr_h)
            btns["target_prev"]=btn_prev
            btns["target_next"]=btn_next
            mx3,my3=pygame.mouse.get_pos()
            for br,lbl in ((btn_prev,"◄"),(btn_next,"►")):
                hov2=br.collidepoint(mx3,my3)
                col2=(220,215,255) if hov2 else (130,125,170)
                arr_s=font_md.render(lbl,True,col2)
                surf.blit(arr_s,arr_s.get_rect(center=br.center))
            mode_f=pygame.font.SysFont("segoeui",13,bold=True)
            mode_s=mode_f.render(cur_mode,True,(210,205,255))
            surf.blit(mode_s,mode_s.get_rect(centerx=tp_x+tp_w//2, centery=tp_y+tp_zone_h//2))

            # STATS header (right column)
            rx=mx_m+portrait_size+16
            txt(surf,"STATS",(rx,my_m+top_offset),(200,200,240),font_lg)

            # Stat rows with icons (skip unlock-only rows)
            siy=my_m+top_offset+22
            for sname,sval,_ in stats:
                if sval is None: continue
                base_key=sname.replace("_unlock","")
                ico_name=STAT_ICO.get(base_key)
                sc=STAT_COLORS.get(sname,(180,180,180))
                ico_drawn=False
                if ico_name:
                    img=load_icon(ico_name,ICO_SZ)
                    if img:
                        surf.blit(img,(rx,siy+(16-ICO_SZ)//2))
                        ico_drawn=True
                if not ico_drawn:
                    dot_s=font_md.render("●",True,sc)
                    surf.blit(dot_s,(rx,siy))
                _sval_disp = int(sval) if isinstance(sval, float) and sval == int(sval) else sval
                val_s=font_md.render(str(_sval_disp),True,(230,230,230))
                surf.blit(val_s,(rx+ICO_SZ+5,siy))
                siy+=22

            # === NAME + LEVEL + TOTAL DAMAGE strip ===
            strip_y=my_m+top_offset+portrait_size+6
            pygame.draw.rect(surf,(28,22,48),(mx_m+6,strip_y,mw-12,48),border_radius=5)
            txt(surf,u.NAME,(mx_m+10,strip_y+4),(210,190,255),font_lg)
            txt(surf,f"Level: {u.level}",(mx_m+10,strip_y+26),(140,130,175),font_md)
            td_s=font_md.render(f"Total Damage:",True,(160,155,185))
            td_n=font_lg.render(fmt_num(int(u.total_damage)),True,(240,220,100))
            surf.blit(td_s,(mx_m+mw-10-max(td_s.get_width(),td_n.get_width()),strip_y+4))
            surf.blit(td_n,(mx_m+mw-10-td_n.get_width(),strip_y+22))

            # === UPGRADE BUTTON ===
            _is_peer_unit = getattr(u, '_mp_peer', False)
            cost=u.upgrade_cost()
            if cost is not None:
                cost = int(cost * getattr(self, 'cost_mult', 1.0))
            strip_y_actual=my_m+top_offset+portrait_size+6
            btns["upgrade"]=pygame.Rect(mx_m+6,strip_y_actual+54,mw-12,44)
            btn_bottom_y=my_m+menu.h-44
            btns["close"]=pygame.Rect(mx_m+6,btn_bottom_y,38,38)
            btns["sell"]=pygame.Rect(mx_m+48,btn_bottom_y,mw-54,38)
            if cls==Archer:
                btn_h=24; btn_w=(mw-24)//4
                arrow_btn_y=strip_y_actual+56
                btns["arrow_normal"]   =pygame.Rect(mx_m+8,               arrow_btn_y, btn_w, btn_h)
                btns["arrow_flame"]    =pygame.Rect(mx_m+8+(btn_w+2),     arrow_btn_y, btn_w, btn_h)
                btns["arrow_shock"]    =pygame.Rect(mx_m+8+(btn_w+2)*2,   arrow_btn_y, btn_w, btn_h)
                btns["arrow_explosive"]=pygame.Rect(mx_m+8+(btn_w+2)*3,   arrow_btn_y, btn_w, btn_h)
                btns["upgrade"]=pygame.Rect(mx_m+6,strip_y_actual+54+btn_h+6,mw-12,44)
            if cls==Jester:
                btn_h=24; btn_w=(mw-20)//4
                bomb_btn_y=strip_y_actual+56
                btns["bomb_fire"]     =pygame.Rect(mx_m+8,                 bomb_btn_y, btn_w, btn_h)
                btns["bomb_ice"]      =pygame.Rect(mx_m+8+(btn_w+2),       bomb_btn_y, btn_w, btn_h)
                btns["bomb_poison"]   =pygame.Rect(mx_m+8+(btn_w+2)*2,     bomb_btn_y, btn_w, btn_h)
                btns["bomb_confusion"]=pygame.Rect(mx_m+8+(btn_w+2)*3,     bomb_btn_y, btn_w, btn_h)
                # At lv4 dual: two rows of bomb buttons
                if u.level >= 4 and u._dual:
                    btns["upgrade"]=pygame.Rect(mx_m+6,strip_y_actual+54+(btn_h+6)*2+16,mw-12,44)
                else:
                    btns["upgrade"]=pygame.Rect(mx_m+6,strip_y_actual+54+btn_h+6,mw-12,44)
            if cls==Castbound:
                _cb_avail = u.available_blades()
                _cb_btn_h = 28; _cb_btn_w = (mw-20) // max(1, len(_cb_avail))
                _cb_blade_y = strip_y_actual + 56
                for _cb_i, _cb_bid in enumerate(_cb_avail):
                    _cb_r = pygame.Rect(mx_m+10+_cb_i*(_cb_btn_w+2), _cb_blade_y, _cb_btn_w-2, _cb_btn_h)
                    btns[f"cb_blade_{_cb_bid}"] = _cb_r
                btns["upgrade"] = pygame.Rect(mx_m+6, strip_y_actual+54+_cb_btn_h+8, mw-12, 44)
            up_rect=btns["upgrade"]
            # ── Upgrade Preview: draw next-level range ring on Upgrade-button hover ──
            if SETTINGS.get("upgrade_preview", True) and up_rect and up_rect.collidepoint(mx2, my2):
                _nxt_prev = self._get_next_stats(u)
                _sk_rng2 = getattr(self, '_sk_range_bonus', 0)
                _nxt_r = None
                if _nxt_prev and "Range" in _nxt_prev:
                    _nxt_r = _nxt_prev["Range"]
                    if _nxt_r and _nxt_r > 0 and _sk_rng2 > 0:
                        _nxt_r = round(_nxt_r * (1.0 + _sk_rng2), 4)
                if _nxt_r and _nxt_r > 0:
                    _pr = int(_nxt_r * TILE)
                    _col_prev = u.COLOR if SETTINGS.get("colored_range", False) else (255, 255, 255)
                    _prev_s = pygame.Surface((_pr*2, _pr*2), pygame.SRCALPHA)
                    pygame.draw.circle(_prev_s, (*_col_prev, 40), (_pr, _pr), _pr)
                    pygame.draw.circle(_prev_s, (*_col_prev, 160), (_pr, _pr), _pr, 3)
                    _old_clip = surf.get_clip()
                    surf.set_clip(pygame.Rect(0, 0, SCREEN_W, SLOT_AREA_Y))
                    surf.blit(_prev_s, (int(u.px) - _pr, int(u.py) - _pr))
                    surf.set_clip(_old_clip)
            if _is_peer_unit:
                # Grey out upgrade button
                pygame.draw.rect(surf,(35,35,40),up_rect,border_radius=6)
                pygame.draw.rect(surf,(60,60,70),up_rect,1,border_radius=6)
                txt(surf,"Can't upgrade partner's tower",up_rect.center,(80,80,100),font_sm,center=True)
                up_rect=None  # prevent further upgrade drawing
            can_up=bool(cost and money>=cost)
            if can_up:
                up_bg=(35,100,40); up_border=(70,200,80)
            elif cost:
                up_bg=(30,26,44); up_border=(55,52,72)
            else:
                up_bg=(28,28,38); up_border=(48,48,60)
            pygame.draw.rect(surf,up_bg,up_rect,border_radius=6)
            pygame.draw.rect(surf,up_border,up_rect,1,border_radius=6)

            # "E" key badge left side
            e_sz=30
            e_r=pygame.Rect(up_rect.x+6,up_rect.y+(up_rect.h-e_sz)//2,e_sz,e_sz)
            e_bg=(40,90,45) if can_up else (45,40,65)
            e_brd=(90,180,90) if can_up else (90,85,115)
            pygame.draw.rect(surf,e_bg,e_r,border_radius=5)
            pygame.draw.rect(surf,e_brd,e_r,1,border_radius=5)
            txt(surf,"E",e_r.center,(200,255,200) if can_up else (200,195,230),font_lg,center=True)

            if cost:
                price_col=C_GOLD if can_up else (90,85,70)
                ico_m=load_icon("money_ico",16)
                price_s=font_xl.render(f" {cost}",True,price_col)
                px_start=up_rect.x+42
                py_mid=up_rect.y+(up_rect.h-price_s.get_height())//2
                if ico_m:
                    surf.blit(ico_m,(px_start, py_mid+(price_s.get_height()-ico_m.get_height())//2))
                    surf.blit(price_s,(px_start+ico_m.get_width(), py_mid))
                else:
                    surf.blit(price_s,(px_start, py_mid))
            elif cls==Castbound and u.level==5 and not u._zenith_mode:
                # Zenith is an award — show special button (always pressable)
                txt(surf,"⚔ Zenith (Award)",up_rect.center,C_CB_ZENITH,font_lg,center=True)
            else:
                txt(surf,"✓ MAX LEVEL",up_rect.center,(100,160,100),font_lg,center=True)

            # === LEVEL PROGRESS BARS ===
            dot_y=up_rect.bottom+8
            bar_total_w=mw-20
            bar_h=10
            if cls == Castbound:
                # Кастомный level bar: 7 сегментов, без подписей
                _cb_lvl_cols  = [
                    (80, 160, 255),   # 0 — ice blue
                    (255, 120, 30),   # 1 — fire orange
                    (180, 100, 255),  # 2 — dual purple
                    (60,  200, 80),   # 3 — terra green
                    (255, 220, 60),   # 4 — star gold
                    (120, 200, 255),  # 5 — zenith seal cyan
                    (255, 120, 255),  # 6 — zenith
                ]
                _cb_total = len(_cb_lvl_cols)
                _cb_seg_w = (bar_total_w - (_cb_total - 1) * 2) // _cb_total
                for _cbi in range(_cb_total):
                    _cbx = mx_m + 10 + _cbi * (_cb_seg_w + 2)
                    _filled = _cbi <= u.level
                    _col = _cb_lvl_cols[_cbi] if _filled else (38, 35, 58)
                    _brd = tuple(min(255, c + 60) for c in _cb_lvl_cols[_cbi]) if _filled else (60, 58, 80)
                    pygame.draw.rect(surf, _col, (_cbx, dot_y, _cb_seg_w, bar_h), border_radius=3)
                    pygame.draw.rect(surf, _brd, (_cbx, dot_y, _cb_seg_w, bar_h), 1, border_radius=3)
                dot_y += bar_h + 6
            elif total_lvls>1:
                seg_w=(bar_total_w-(total_lvls-1)*3)//total_lvls
                for i in range(total_lvls):
                    bx_seg=mx_m+10+i*(seg_w+3)
                    filled=i<=u.level
                    bg_col=C_GOLD if filled else (38,35,58)
                    pygame.draw.rect(surf,bg_col,(bx_seg,dot_y,seg_w,bar_h),border_radius=4)
                    if filled:
                        pygame.draw.rect(surf,(255,235,150),(bx_seg,dot_y,seg_w,bar_h),1,border_radius=4)
                    else:
                        pygame.draw.rect(surf,(60,58,80),(bx_seg,dot_y,seg_w,bar_h),1,border_radius=4)

            # === UPGRADE NAME (if unit has named levels) ===
            _upg_names_map = {Snowballer: SNOWBALLER_LEVEL_NAMES}
            _upg_names = _upg_names_map.get(cls)
            if _upg_names and cost:
                _next_name = _upg_names[u.level+1] if u.level+1 < len(_upg_names) else None
                if _next_name:
                    _nn_s = pygame.font.SysFont("segoeui", 14, bold=True).render(f"▲ {_next_name} ▲", True, (120, 200, 255))
                    _nn_r = pygame.Rect(mx_m+6, dot_y+12, mw-12, 20)
                    pygame.draw.rect(surf, (20, 40, 80), _nn_r, border_radius=4)
                    surf.blit(_nn_s, _nn_s.get_rect(center=_nn_r.center))
                    ch_y = dot_y + 38
            # === CHANGING STATS ===
            def _norm(x):
                return int(x) if isinstance(x, float) and x == int(x) else x
            changing=[(s,v,n) for s,v,n in stats if n is not None and (v is None or str(_norm(n))!=str(_norm(v)))]
            ch_y=dot_y+(8 if cls==Castbound else 20)

            # === ARCHER ARROW MODE SELECTOR ===
            if cls==Archer:
                arrow_modes=[
                    ("arrow",     "Normal",    (200,140,60),  (255,180,80),  0),
                    ("flame",     "Flame",     (220,80,20),   (255,150,50),  3),
                    ("shock",     "Shock",     (80,160,255),  (160,220,255), 4),
                    ("explosive", "Explosive", (200,50,20),   (255,120,50),  5),
                ]
                for mode_key, mode_label, col_active, col_border, req_lv in arrow_modes:
                    br=btns.get(f"arrow_{mode_key if mode_key != 'arrow' else 'normal'}")
                    if not br: continue
                    is_sel=(u.arrow_mode==mode_key)
                    locked=(u.level < req_lv)
                    if locked:
                        bg=(22,22,35); brd=(55,50,75); tcol=(80,75,100)
                    elif is_sel:
                        bg=tuple(max(0,c-80) for c in col_active); brd=col_border; tcol=col_border
                    else:
                        bg=(30,28,48); brd=(70,65,100); tcol=(140,135,180)
                    pygame.draw.rect(surf,bg,br,border_radius=4)
                    pygame.draw.rect(surf,brd,br,1 if not is_sel else 2,border_radius=4)
                    lbl_s=font_sm.render(mode_label,True,tcol)
                    surf.blit(lbl_s,lbl_s.get_rect(center=br.center))
                    if locked:
                        lock_s=pygame.font.SysFont("consolas",9).render(f"Lv{req_lv}",True,(90,80,120))
                        surf.blit(lock_s,(br.right-lock_s.get_width()-2, br.y+2))

            # === JESTER BOMB MODE SELECTOR ===
            if cls==Jester:
                _jbomb_modes=[
                    ("fire",      "Fire",    (255,100,30),  (255,160,60),  0),
                    ("ice",       "Ice",     (80,200,255),  (160,230,255), 2),
                    ("poison",    "Poison",  (80,220,60),   (140,255,80),  3),
                    ("confusion", "Confuse", (200,80,255),  (230,140,255), 4),
                ]
                # Row 1 — primary bomb (bomb_mode), always shown
                for mode_key, mode_label, col_active, col_border, req_lv in _jbomb_modes:
                    br=btns.get(f"bomb_{mode_key}")
                    if not br: continue
                    is_sel=(u.bomb_mode==mode_key)
                    locked=(u.level < req_lv)
                    if locked:
                        bg=(22,22,35); brd=(55,50,75); tcol=(80,75,100)
                    elif is_sel:
                        bg=tuple(max(0,c-90) for c in col_active); brd=col_border; tcol=col_border
                    else:
                        bg=(30,28,48); brd=(70,65,100); tcol=(140,135,180)
                    pygame.draw.rect(surf,bg,br,border_radius=4)
                    pygame.draw.rect(surf,brd,br,1 if not is_sel else 2,border_radius=4)
                    lbl_s=font_sm.render(mode_label,True,tcol)
                    surf.blit(lbl_s,lbl_s.get_rect(center=br.center))
                    if locked:
                        lock_s=pygame.font.SysFont("consolas",9).render(f"Lv{req_lv}",True,(90,80,120))
                        surf.blit(lock_s,(br.right-lock_s.get_width()-2, br.y+2))
                # Row 2 — second bomb (bomb_mode2), only at lv4
                if u.level >= 4 and u._dual:
                    bomb_btn2_y = bomb_btn_y + btn_h + 6
                    for i,(mode_key, mode_label, col_active, col_border, req_lv) in enumerate(_jbomb_modes):
                        br2 = pygame.Rect(mx_m+8+(btn_w+2)*i, bomb_btn2_y, btn_w, btn_h)
                        btns[f"bomb2_{mode_key}"] = br2
                        is_sel2 = (u.bomb_mode2 == mode_key) if u.bomb_mode2 else (u.bomb_mode == mode_key and u.bomb_mode2 is None and mode_key == u.bomb_mode)
                        # "None" = same as bomb1 — highlight bomb1 type
                        if u.bomb_mode2 is None:
                            is_sel2 = (mode_key == u.bomb_mode)
                        locked2 = (u.level < req_lv)
                        if locked2:
                            bg2=(22,22,35); brd2=(55,50,75); tcol2=(80,75,100)
                        elif is_sel2:
                            bg2=tuple(max(0,c-90) for c in col_active); brd2=col_border; tcol2=col_border
                        else:
                            bg2=(30,28,48); brd2=(70,65,100); tcol2=(140,135,180)
                        pygame.draw.rect(surf,bg2,br2,border_radius=4)
                        pygame.draw.rect(surf,brd2,br2,1 if not is_sel2 else 2,border_radius=4)
                        lbl_s2=font_sm.render(mode_label,True,tcol2)
                        surf.blit(lbl_s2,lbl_s2.get_rect(center=br2.center))
                        if locked2:
                            lock_s2=pygame.font.SysFont("consolas",9).render(f"Lv{req_lv}",True,(90,80,120))
                            surf.blit(lock_s2,(br2.right-lock_s2.get_width()-2, br2.y+2))

            # === CASTBOUND BLADE SELECTOR ===
            if cls == Castbound:
                _cb_avail = u.available_blades()
                _cb_btn_h = 28
                _cb_btn_w = (mw-20) // max(1, len(_cb_avail))
                _cb_blade_y = strip_y_actual + 56
                _ico_sz = 18
                _cb_short = {"ice":"Ice","fire":"Fire","terra":"Terra","star":"Star","starwrath":"SWrath","zenith":"Zenith"}
                for _cb_i, _cb_bid in enumerate(_cb_avail):
                    _cb_r = btns.get(f"cb_blade_{_cb_bid}")
                    if _cb_r is None:
                        _cb_r = pygame.Rect(mx_m+10+_cb_i*(_cb_btn_w+2), _cb_blade_y, _cb_btn_w-2, _cb_btn_h)
                    _cb_is_sel = _cb_bid in u.selected_blades
                    _cb_col    = CB_BLADE_DEFS[_cb_bid][1]
                    if _cb_is_sel:
                        _cb_bg  = tuple(max(0,c//2) for c in _cb_col)
                        _cb_brd = _cb_col
                        _cb_tcol = _cb_col
                    else:
                        _cb_bg  = (22, 14, 38)
                        _cb_brd = (62, 48, 85)
                        _cb_tcol = (110, 100, 140)
                    pygame.draw.rect(surf, _cb_bg,  _cb_r, border_radius=4)
                    pygame.draw.rect(surf, _cb_brd, _cb_r, 2 if _cb_is_sel else 1, border_radius=4)
                    _cb_ico = _cb_load_icon(CB_BLADE_DEFS[_cb_bid][2], _ico_sz)
                    _lbl_s = font_sm.render(_cb_short.get(_cb_bid, _cb_bid[:4].title()), True, _cb_tcol)
                    _total_w = (_ico_sz + 3 + _lbl_s.get_width()) if _cb_ico else _lbl_s.get_width()
                    _cx = _cb_r.x + (_cb_r.w - _total_w) // 2
                    _cy = _cb_r.y + (_cb_r.h - _ico_sz) // 2
                    if _cb_ico:
                        surf.blit(_cb_ico, (_cx, _cy))
                        surf.blit(_lbl_s, (_cx + _ico_sz + 3, _cb_r.y + (_cb_r.h - _lbl_s.get_height()) // 2))
                    else:
                        surf.blit(_lbl_s, _lbl_s.get_rect(center=_cb_r.center))

            if changing:
                pygame.draw.line(surf,(48,44,70),(mx_m+8,ch_y-5),(mx_m+mw-8,ch_y-5),1)
            ARR_SZ=14
            for sname,sval,snext in changing:
                base_key=sname.replace("_unlock","")
                ico_name=STAT_ICO.get(base_key)
                sc=STAT_COLORS.get(sname,(180,180,180))
                xp=mx_m+8
                ico_drawn=False
                if ico_name:
                    img=load_icon(ico_name,ICO_SZ)
                    if img:
                        surf.blit(img,(xp,ch_y+(16-ICO_SZ)//2))
                        ico_drawn=True; xp+=ICO_SZ+5
                if not ico_drawn:
                    dot_s=font_md.render("●",True,sc)
                    surf.blit(dot_s,(xp,ch_y)); xp+=ICO_SZ+5
                if sval is not None:
                    _sval_old = int(sval) if isinstance(sval, float) and sval == int(sval) else sval
                    old_s=font_md.render(str(_sval_old),True,(190,185,210))
                    surf.blit(old_s,(xp,ch_y)); xp+=old_s.get_width()+4
                if sval is not None:
                    arr_img=load_icon("arrow_ico",ARR_SZ)
                    if arr_img:
                        surf.blit(arr_img,(xp,ch_y+(16-ARR_SZ)//2)); xp+=ARR_SZ+4
                    else:
                        arr_s=font_md.render("→",True,(160,155,180))
                        surf.blit(arr_s,(xp,ch_y)); xp+=arr_s.get_width()+3
                _snext_disp = int(snext) if isinstance(snext, float) and snext == int(snext) else snext
                new_s=font_md.render(str(_snext_disp),True,(100,220,100))
                surf.blit(new_s,(xp,ch_y))
                ch_y+=20

            # === JESTER EXTRA INFO — plain text after changing stats, clipped inside card ===
            if cls==Jester:
                _jinfo_f = pygame.font.SysFont("segoeui", 13)
                _jinfo_lines = [f"Splash: {u._expl_r} tiles  (max 5 hits)"]
                if u._burn_dmg>0:    _jinfo_lines.append(f"Burn: {u._burn_dmg}/tick  {u._burn_dur:.0f}s")
                if u._ice_pct>0:     _jinfo_lines.append(f"Ice: {int(u._ice_pct*100)}%/hit  max {int(u._ice_max*100)}%  {u._ice_time:.0f}s")
                if u._ice_def_drop>0:_jinfo_lines.append(f"Ice def drop: -{int(u._ice_def_drop*100)}%/hit")
                if u._poison_dmg>0:  _jinfo_lines.append(f"Poison: {u._poison_dmg}/tick  {u._poison_time:.0f}s  t={u._poison_tick:.1f}s")
                if u._conf_time>0:   _jinfo_lines.append(f"Confuse: {u._conf_time:.0f}s  cd {u._conf_cd:.0f}s")
                if u._dual:          _jinfo_lines.append("Dual: throws 2 bombs")
                _jinfo_y = ch_y + 4
                _card_clip = pygame.Rect(mx_m+2, my_m+2, mw-4, menu.h-4)
                old_clip = surf.get_clip()
                surf.set_clip(_card_clip)
                for _jl in _jinfo_lines:
                    if _jinfo_y + 15 > my_m + menu.h - 48: break
                    _js = _jinfo_f.render(_jl, True, (155, 150, 180))
                    surf.blit(_js, (mx_m+10, _jinfo_y))
                    _jinfo_y += 16
                surf.set_clip(old_clip)


            # === CASTBOUND EXTRA INFO — серый текст под changing stats ===
            if cls==Castbound and not u._zenith_mode:
                _cb_info_f = pygame.font.SysFont("segoeui", 13)
                _cb_info_lines = []
                lv = u.level
                from units import _CB_ICE_PARAMS, _CB_FIRE_PARAMS, _CB_TERRA_PARAMS
                slow_pct, slow_dur = _CB_ICE_PARAMS[lv]
                _cb_info_lines.append(f"Ice Blade: slow {int(slow_pct*100)}%  {slow_dur}s")
                if lv >= 1:
                    bdmg, bdur, btick = _CB_FIRE_PARAMS[lv]
                    _cb_info_lines.append(f"Fiery GS: {bdmg}/tick  {bdur}s")
                if u._terra_unlocked:
                    kb_px, kb_hits = _CB_TERRA_PARAMS[lv]
                    _cb_info_lines.append(f"Terra: knockback {kb_px}px  (every {kb_hits} hits)")
                if u._star_unlocked:
                    _cb_info_lines.append(f"Starfury: splash proj")
                _cbinfo_y = ch_y + 4
                _card_clip = pygame.Rect(mx_m+2, my_m+2, mw-4, menu.h-4)
                old_clip = surf.get_clip()
                surf.set_clip(_card_clip)
                for _cbl in _cb_info_lines:
                    if _cbinfo_y + 15 > my_m + menu.h - 48: break
                    _cbs = _cb_info_f.render(_cbl, True, (155, 150, 180))
                    surf.blit(_cbs, (mx_m+10, _cbinfo_y))
                    _cbinfo_y += 16
                surf.set_clip(old_clip)

            # === HARVESTER EXTRA INFO — серый текст под changing stats ===
            if cls==Harvester:
                _HARV_LV_DESCS = [
                    # lv0 — базовый уровень (не отображается)
                    None,
                    # lv1: Sharper Thorns
                    ["Sharper Thorns",
                     "Thorn dmg: 2 → 4",
                     "Cooldown: 40s"],
                    # lv2: Early Harvest
                    ["Early Harvest",
                     "Main dmg: 20 → 35",
                     "Thorn duration: 8 → 11s",
                     "Thorn slow: 20 → 25%"],
                    # lv3: Nature's Vengence
                    ["Nature's Vengence",
                     "Main dmg: 35 → 65",
                     "Thorn dmg: 4 → 8",
                     "Gains hidden detection",
                     "Thorn slow: 25%"],
                    # lv4
                    ["Overgrowth",
                     "Main dmg: 65 → 90",
                     "Firerate improved",
                     "Range: 20 → 25 tiles",
                     "Thorn dmg: 8 → 9",
                     "Thorn duration: 11 → 12s"],
                    # lv5
                    ["Reaping Season",
                     "Main dmg: 90 → 420",
                     "Thorn dmg: 9 → 14",
                     "Thorn slow: 25 → 40%",
                     "Thorn duration: 12 → 15s",
                     "Range: 25 → 30 tiles"],
                ]
                _nxt_lv = u.level + 1
                _hdesc = _HARV_LV_DESCS[_nxt_lv] if _nxt_lv < len(_HARV_LV_DESCS) else None
                if _hdesc and cost:
                    _hf = pygame.font.SysFont("segoeui", 13)
                    _hf_title = pygame.font.SysFont("segoeui", 13, bold=True)
                    _h_y = ch_y + 6
                    _card_clip2 = pygame.Rect(mx_m+2, my_m+2, mw-4, menu.h-4)
                    old_clip2 = surf.get_clip()
                    surf.set_clip(_card_clip2)
                    for _hi, _hl in enumerate(_hdesc):
                        if _h_y + 15 > my_m + menu.h - 48: break
                        _hf_use = _hf_title if _hi == 0 else _hf
                        _hcol = (160, 155, 185) if _hi == 0 else (120, 115, 145)
                        _hs = _hf_use.render(_hl, True, _hcol)
                        surf.blit(_hs, (mx_m+10, _h_y))
                        _h_y += 15
                    surf.set_clip(old_clip2)

# === FELYNE EXTRA INFO ===
            if cls==Felyne:
                _MAX_KLV = len(FELYNE_LEVELS) - 1
                _FELYNE_LV_DESCS = [
                    None,   # lv0 (базовый)
                    None,   # lv0 -> lv1: шарики не меняются
                    ["Sentry Upgrade:", "  - Attack speed: 1.0s to 0.2s"],   # lv1 -> lv2
                    ["Sentry Upgrade:", "  - +1 sentry (Total: 2)"],        # lv2 -> lv3
                    ["Sentry Upgrade:", "  - Damage: 2 to 4", "  - Attack speed: 0.2s to 0.15s"], # lv3 -> lv4
                    ["Sentry Upgrade:", "  - +1 sentry (Total: 3)"],        # lv4 -> lv5
                    ["Sentry Upgrade:", "  - +1 sentry (Total: 4)", "  - Damage: 4 to 5", "  - Attack speed: 0.15s to 0.10s"], # lv5 -> lv6
                ]
                _nxt_klv = u.level + 1
                _kdesc = _FELYNE_LV_DESCS[_nxt_klv] if _nxt_klv < len(_FELYNE_LV_DESCS) else None
                
                if _kdesc and cost:
                    _kf       = pygame.font.SysFont("segoeui", 13)
                    _kf_title = pygame.font.SysFont("segoeui", 13, bold=True)
                    _k_y      = ch_y + 6
                    _kclip    = pygame.Rect(mx_m+2, my_m+2, mw-4, menu.h-4)
                    old_clip_k = surf.get_clip()
                    surf.set_clip(_kclip)
                    
                    for _ki, _kl in enumerate(_kdesc):
                        if _k_y + 15 > my_m + menu.h - 48: break
                        if _ki == 0:
                            _ks = _kf_title.render(_kl, True, (200, 160, 220))
                            surf.blit(_ks, (mx_m+10, _k_y))
                        else:
                            _ks = _kf.render(_kl, True, (160, 155, 185))
                            surf.blit(_ks, (mx_m+10, _k_y))
                        _k_y += 15
                        
                    surf.set_clip(old_clip_k)

            _abil_min_level = 0 if isinstance(u, (Harvester, Felyne, ControlPanel)) else 2
            if u.ability and u.level >= _abil_min_level:
                ab=u.ability
                ab_r=btns["ability_sq"]
                ready=ab.ready()
                ab_bg=(25,80,80) if ready else (30,30,45)
                ab_brd=(60,220,220) if ready else (60,60,80)
                pygame.draw.rect(surf,ab_bg,ab_r,border_radius=10)
                pygame.draw.rect(surf,ab_brd,ab_r,2,border_radius=10)
                ic_cx=ab_r.centerx; ic_cy=ab_r.y+20
                pygame.draw.circle(surf,u.COLOR,(ic_cx,ic_cy),12)
                pygame.draw.circle(surf,(255,255,255),(ic_cx,ic_cy),12,1)
                if ready:
                    lbl=font_md.render("[F]",True,(80,240,240))
                else:
                    lbl=font_md.render(f"{ab.cd_left:.0f}s",True,(120,120,150))
                surf.blit(lbl,lbl.get_rect(centerx=ab_r.centerx,top=ab_r.y+34))
                u._ability_btn_rect=ab_r

            # === BOTTOM: X + SELL ===
            _is_peer_unit = getattr(u, '_mp_peer', False)
            pygame.draw.rect(surf,(40,22,22),btns["close"],border_radius=5)
            pygame.draw.rect(surf,(100,40,40),btns["close"],1,border_radius=5)
            txt(surf,"X",btns["close"].center,(220,100,100),font_lg,center=True)

            if _is_peer_unit:
                # Grey out sell button — can't sell partner's tower
                pygame.draw.rect(surf,(40,40,44),btns["sell"],border_radius=5)
                pygame.draw.rect(surf,(70,70,80),btns["sell"],1,border_radius=5)
                txt(surf,"Partner's tower",btns["sell"].center,(100,100,120),font_sm,center=True)
            else:
                sell_val=self._sell_value(u)
                _sell_pend = getattr(self, '_sell_pending', False)
                _sell_t = pygame.time.get_ticks() * 0.001
                _sell_flash = _sell_pend and (int(_sell_t * 6) % 2 == 0)
                _sell_bg  = (255, 80, 20) if _sell_flash else (170, 28, 28)
                _sell_brd = (255, 200, 50) if _sell_pend else (230, 65, 65)
                pygame.draw.rect(surf, _sell_bg, btns["sell"], border_radius=5)
                pygame.draw.rect(surf, _sell_brd, btns["sell"], 2 if _sell_pend else 1, border_radius=5)
                if _sell_pend:
                    txt(surf, "CONFIRM?", btns["sell"].center, (255, 255, 100), font_lg, center=True)
                else:
                    ico_m=load_icon("money_ico",14)
                    if ico_m:
                        sell_s=font_lg.render(f"Sell: ",True,(255,210,210))
                        val_s=font_lg.render(str(sell_val),True,(255,230,100))
                        total_sw=sell_s.get_width()+ico_m.get_width()+val_s.get_width()
                        sx=btns["sell"].centerx-total_sw//2
                        sy=btns["sell"].centery-sell_s.get_height()//2
                        surf.blit(sell_s,(sx,sy)); sx+=sell_s.get_width()
                        surf.blit(ico_m,(sx,sy+(sell_s.get_height()-ico_m.get_height())//2)); sx+=ico_m.get_width()
                        surf.blit(val_s,(sx,sy))
                    else:
                        txt(surf,f"Sell: ${sell_val}",btns["sell"].center,(255,210,210),font_lg,center=True)
            # Cache final button positions for handle_click
            self._cached_btns=btns

        if self.drag_unit:
            mx2,my2=pygame.mouse.get_pos()
            self.drag_unit.px=mx2; self.drag_unit.py=my2
            # Keep RedBall home in sync with cursor during drag
            if isinstance(self.drag_unit,RedBall):
                self.drag_unit._home_x=float(mx2); self.drag_unit._home_y=float(my2)
                self.drag_unit._draw_x=float(mx2); self.drag_unit._draw_y=float(my2)
            self.drag_unit.draw_range(surf)
            if SETTINGS.get("no_tower_details", False):
                self.drag_unit.draw_simple(surf)
            else:
                self.drag_unit.draw(surf)

        # ── Harvester thorn-placement preview ────────────────────────────────
        if self._thorn_place_mode and self._thorn_place_owner:
            mx2, my2 = pygame.mouse.get_pos()
            try:
                from game_core import _FROSTY_PATHS, CURRENT_MAP
                _paths = list(_FROSTY_PATHS) if CURRENT_MAP == "frosty" else [get_map_path()]
            except Exception:
                _paths = [get_map_path()]
            # find closest path to cursor
            _best_path = _paths[0]; _best_d = float('inf')
            for _p in _paths:
                for _si in range(len(_p)-1):
                    _ax,_ay=_p[_si]; _bx,_by=_p[_si+1]
                    _dx,_dy=_bx-_ax,_by-_ay; _ll=_dx*_dx+_dy*_dy
                    if _ll > 0:
                        _t2 = max(0.0, min(1.0, ((mx2-_ax)*_dx+(my2-_ay)*_dy)/_ll))
                    else:
                        _t2 = 0.0
                    _nx,_ny=_ax+_t2*_dx,_ay+_t2*_dy
                    _d=math.hypot(_nx-mx2,_ny-my2)
                    if _d < _best_d: _best_d=_d; _best_path=_p
            _preview_pts = self._thorn_place_owner.get_thorn_preview_pts(mx2, my2, _best_path)
            _r_px = int(self._thorn_place_owner.thorn_range)  # already in pixels
            _pulse = 0.5 + 0.5 * math.sin(self.t * 5)
            for (_px2, _py2) in _preview_pts:
                _s = pygame.Surface((_r_px*2+4, _r_px*2+4), pygame.SRCALPHA)
                _alpha = int(60 + 40 * _pulse)
                pygame.draw.circle(_s, (60, 220, 60, _alpha), (_r_px+2, _r_px+2), _r_px)
                pygame.draw.circle(_s, (120, 255, 80, 180),   (_r_px+2, _r_px+2), _r_px, 2)
                surf.blit(_s, (int(_px2)-_r_px-2, int(_py2)-_r_px-2))
                pygame.draw.circle(surf, (80, 200, 50), (int(_px2), int(_py2)), 5)
                pygame.draw.circle(surf, (180, 255, 100), (int(_px2), int(_py2)), 3)
            # crosshair at cursor
            pygame.draw.line(surf, (100,255,80), (mx2-12,my2), (mx2+12,my2), 2)
            pygame.draw.line(surf, (100,255,80), (mx2,my2-12), (mx2,my2+12), 2)
            pygame.draw.circle(surf, (100,255,80), (mx2,my2), 10, 2)

        ab_entries=[]
        for u in units:
            if getattr(u, '_mp_peer', False): continue  # skip partner's units — their abilities are theirs
            if getattr(u,'ability2',None) and u.level>=1: ab_entries.append((u, u.ability2, 'ab2'))
            _ab1_min = 0 if isinstance(u, (Harvester, ControlPanel)) else 2
            if u.ability and u.level >= _ab1_min: ab_entries.append((u, u.ability, 'ab1'))
            if getattr(u,'ability3',None) and u.level>=4: ab_entries.append((u, u.ability3, 'ab3'))
        _ab_clip_bottom = SLOT_AREA_Y - 4
        _old_ab_clip = surf.get_clip()
        surf.set_clip(pygame.Rect(0, 0, SCREEN_W, _ab_clip_bottom))
        for idx,(u,ab,slot) in enumerate(ab_entries):
            bw3,bh3=160,48; bx3=8; by3=80+idx*(bh3+8)
            if by3 + bh3 > _ab_clip_bottom:
                ab._btn_rect=pygame.Rect(0,0,0,0)
                if slot=='ab1': u._ability_btn_rect=pygame.Rect(0,0,0,0)
                elif slot=='ab2': u._ability2_btn_rect=pygame.Rect(0,0,0,0)
                elif slot=='ab3': u._ability3_btn_rect=pygame.Rect(0,0,0,0)
                continue
            ready=ab.ready()
            pygame.draw.rect(surf,(30,70,80) if ready else (30,30,40),(bx3,by3,bw3,bh3),border_radius=8)
            pygame.draw.rect(surf,C_CYAN if ready else C_BORDER,(bx3,by3,bw3,bh3),2,border_radius=8)
            pygame.draw.circle(surf,u.COLOR,(bx3+26,by3+bh3//2),16)
            pygame.draw.circle(surf,C_WHITE,(bx3+26,by3+bh3//2),16,2)
            txt(surf,ab.name if ready else f"CD {ab.cd_left:.1f}s",(bx3+46,by3+8),C_WHITE if ready else (100,100,120),font_sm)
            if not ready:
                r3=max(0.0, min(1.0, 1-(ab.cd_left/ab.cooldown)))
                pygame.draw.rect(surf,(40,40,60),(bx3+46,by3+26,bw3-54,8),border_radius=3)
                pygame.draw.rect(surf,C_CYAN,(bx3+46,by3+26,max(0,int((bw3-54)*r3)),8),border_radius=3)
            else:
                txt(surf,"CLICK / [F]",(bx3+46,by3+28),C_CYAN,font_sm)
            ab._btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
            if slot=='ab1': u._ability_btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
            elif slot=='ab2': u._ability2_btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
            elif slot=='ab3': u._ability3_btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
        surf.set_clip(_old_ab_clip)
        if self.msg_timer>0:
            alpha=min(255,int(self.msg_timer*255))
            s2=font_lg.render(self.msg,True,C_ORANGE); s2.set_alpha(alpha)
            surf.blit(s2,s2.get_rect(center=(SCREEN_W//2,SCREEN_H//2-60)))
        for e in enemies:
            if e.alive and dist((e.x,e.y),(mx2,my2))<e.radius+5:
                e.draw(surf,hovered=True,detected=True)

        # ── Remote Control ability UI ─────────────────────────────────────────
        if getattr(self, '_rc_open', False):
            self._draw_rc_panel(surf, money)

    # ─────────────────────────────────────────────────────────────────────────
    # Remote Control (ControlPanel ability) overlay UI
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_rc_panel(self, surf, money):
        """Draw the Remote Control selection popup and store button rects."""
        W, H = 520, 380
        px2 = SCREEN_W // 2 - W // 2
        py2 = SCREEN_H // 2 - H // 2

        # Darken background
        dim = _get_dim_surf(); dim.fill((0, 0, 0, 140))
        surf.blit(dim, (0, 0))

        # Panel background
        draw_rect_alpha(surf, (10, 30, 50), (px2, py2, W, H), 230, 12)
        pygame.draw.rect(surf, C_CTRLPANEL, (px2, py2, W, H), 2, border_radius=12)

        lf16 = pygame.font.SysFont("segoeui", 16, bold=True)
        lf14 = pygame.font.SysFont("segoeui", 14)
        lf13 = pygame.font.SysFont("segoeui", 13)
        lf12 = pygame.font.SysFont("consolas", 12, bold=True)

        # Title
        title_s = lf16.render("Remote Control", True, C_CTRLPANEL)
        surf.blit(title_s, title_s.get_rect(centerx=px2 + W // 2, top=py2 + 10))

        # ── Section 1: Choose target tower ───────────────────────────────────
        sec_s = lf14.render("Target Tower:", True, (160, 200, 255))
        surf.blit(sec_s, (px2 + 14, py2 + 38))

        btn_w = (W - 28) // max(len(self._rc_units), 1)
        btn_w = min(btn_w, 110)
        self._rc_tower_btns = []
        for i, u in enumerate(self._rc_units[:8]):
            bx = px2 + 14 + i * (btn_w + 4)
            by = py2 + 58
            bh = 38
            sel = (u is self._rc_sel_unit)
            bg  = (20, 80, 120) if sel else (15, 40, 60)
            brd = C_CTRLPANEL if sel else (40, 100, 130)
            pygame.draw.rect(surf, bg,  (bx, by, btn_w, bh), border_radius=6)
            pygame.draw.rect(surf, brd, (bx, by, btn_w, bh), 2, border_radius=6)
            uname = getattr(u, "NAME", type(u).__name__)
            ns = lf12.render(uname[:10], True, C_WHITE if sel else (160, 190, 210))
            surf.blit(ns, ns.get_rect(centerx=bx + btn_w // 2, centery=by + bh // 2))
            self._rc_tower_btns.append((pygame.Rect(bx, by, btn_w, bh), u))

        # ── Section 2: Choose buff type ───────────────────────────────────────
        sec_s2 = lf14.render("Buff Type:", True, (160, 200, 255))
        surf.blit(sec_s2, (px2 + 14, py2 + 110))

        buff_names = ["Range", "Damage", "Firerate"]
        buff_descs = ["+35% Range", "+40% Damage", "+35% Firerate"]
        buff_costs_base = [_CP_BUFF_DEFS[b]["base"] for b in buff_names]
        self._rc_buff_btns = []
        bw_b = (W - 28) // 3 - 4
        for i, (bname, bdesc) in enumerate(zip(buff_names, buff_descs)):
            bx = px2 + 14 + i * (bw_b + 6)
            by = py2 + 130
            bh = 48
            sel = (bname == self._rc_sel_buff)
            bcol = _CP_BUFF_DEFS[bname]["color"]
            bg   = (*[min(255, c // 3 + 20) for c in bcol],)
            brd  = bcol if sel else tuple(max(0, c - 80) for c in bcol)
            pygame.draw.rect(surf, bg,  (bx, by, bw_b, bh), border_radius=6)
            pygame.draw.rect(surf, brd, (bx, by, bw_b, bh), 2 if not sel else 3, border_radius=6)
            ns  = lf13.render(bname, True, C_WHITE)
            ds  = lf12.render(bdesc, True, (200, 220, 200))
            c_s = lf12.render(f"${buff_costs_base[i]}+", True, C_GOLD)
            surf.blit(ns,  ns.get_rect(centerx=bx + bw_b // 2, top=by + 4))
            surf.blit(ds,  ds.get_rect(centerx=bx + bw_b // 2, top=by + 20))
            surf.blit(c_s, c_s.get_rect(centerx=bx + bw_b // 2, top=by + 34))
            self._rc_buff_btns.append((pygame.Rect(bx, by, bw_b, bh), bname))

        # ── Section 3: Duration slider ────────────────────────────────────────
        sec_s3 = lf14.render(f"Duration: {self._rc_duration}s", True, (160, 200, 255))
        surf.blit(sec_s3, (px2 + 14, py2 + 196))

        slider_x  = px2 + 14
        slider_y  = py2 + 220
        slider_w  = W - 28
        slider_h  = 14
        dur_frac  = (self._rc_duration - 5) / 115.0  # 5–120 range
        pygame.draw.rect(surf, (20, 50, 70), (slider_x, slider_y, slider_w, slider_h), border_radius=6)
        pygame.draw.rect(surf, C_CTRLPANEL,
                         (slider_x, slider_y, int(slider_w * dur_frac), slider_h), border_radius=6)
        handle_x = slider_x + int(slider_w * dur_frac)
        pygame.draw.circle(surf, C_WHITE, (handle_x, slider_y + slider_h // 2), 10)
        pygame.draw.circle(surf, C_CTRLPANEL, (handle_x, slider_y + slider_h // 2), 10, 2)
        # Label min/max
        mn = lf12.render("5s", True, (100, 140, 160))
        mx3 = lf12.render("120s", True, (100, 140, 160))
        surf.blit(mn,  (slider_x, slider_y + 16))
        surf.blit(mx3, (slider_x + slider_w - mx3.get_width(), slider_y + 16))
        self._rc_slider_rect = pygame.Rect(slider_x - 10, slider_y - 8, slider_w + 20, slider_h + 16)

        # ── Cost summary ──────────────────────────────────────────────────────
        total_cost = RemoteControlAbility.buff_cost(self._rc_sel_buff, self._rc_duration)
        can_afford = money >= total_cost
        cost_col   = (100, 220, 80) if can_afford else (220, 80, 60)
        per_s      = _CP_BUFF_DEFS[self._rc_sel_buff]["per_sec"]
        cost_s = lf14.render(
            f"Cost: ${total_cost}  (${_CP_BUFF_DEFS[self._rc_sel_buff]['base']} + ${per_s}/s × {self._rc_duration}s)",
            True, cost_col)
        surf.blit(cost_s, cost_s.get_rect(centerx=px2 + W // 2, top=py2 + 246))

        # ── Confirm / Cancel buttons ──────────────────────────────────────────
        btn_h = 40
        confirm_r = pygame.Rect(px2 + W // 2 - 180, py2 + H - 56, 160, btn_h)
        cancel_r  = pygame.Rect(px2 + W // 2 + 20,  py2 + H - 56, 160, btn_h)
        # Confirm
        c_bg  = (20, 90, 30) if can_afford else (40, 40, 40)
        c_brd = (60, 200, 80) if can_afford else (80, 80, 80)
        pygame.draw.rect(surf, c_bg,  confirm_r, border_radius=8)
        pygame.draw.rect(surf, c_brd, confirm_r, 2, border_radius=8)
        conf_lbl = lf16.render("Confirm" if can_afford else "Not enough $", True,
                               (100, 255, 120) if can_afford else (140, 140, 140))
        surf.blit(conf_lbl, conf_lbl.get_rect(center=confirm_r.center))
        # Cancel
        pygame.draw.rect(surf, (70, 20, 20),   cancel_r, border_radius=8)
        pygame.draw.rect(surf, (200, 50, 50),  cancel_r, 2, border_radius=8)
        cancel_lbl = lf16.render("Cancel", True, (255, 100, 100))
        surf.blit(cancel_lbl, cancel_lbl.get_rect(center=cancel_r.center))

        self._rc_confirm_rect = confirm_r
        self._rc_cancel_rect  = cancel_r
        self._rc_can_afford   = can_afford

    def handle_rc_click(self, pos, money):
        """Returns money_delta (negative = spent) or 0.  Closes panel on confirm/cancel."""
        if not getattr(self, '_rc_open', False):
            return 0
        mx2, my2 = pos
        # Cancel
        if getattr(self, '_rc_cancel_rect', None) and self._rc_cancel_rect.collidepoint(pos):
            self._rc_open = False
            return 0
        # Confirm
        if (getattr(self, '_rc_confirm_rect', None) and
                self._rc_confirm_rect.collidepoint(pos) and
                getattr(self, '_rc_can_afford', False)):
            cost = RemoteControlAbility.buff_cost(self._rc_sel_buff, self._rc_duration)
            self._rc_panel.ability.apply_buff(self._rc_sel_unit, self._rc_sel_buff, self._rc_duration)
            self._rc_open = False
            return -cost
        # Tower selection buttons
        for rect, u in getattr(self, '_rc_tower_btns', []):
            if rect.collidepoint(pos):
                self._rc_sel_unit = u
                return 0
        # Buff type buttons
        for rect, bname in getattr(self, '_rc_buff_btns', []):
            if rect.collidepoint(pos):
                self._rc_sel_buff = bname
                return 0
        # Slider drag
        sl = getattr(self, '_rc_slider_rect', None)
        if sl and sl.collidepoint(pos):
            slider_x = sl.x + 10
            slider_w = sl.w - 20
            frac = max(0.0, min(1.0, (mx2 - slider_x) / slider_w))
            self._rc_duration = max(5, min(120, int(5 + frac * 115)))
            return 0
        return 0

# ── Rarity card drawing helper ──────────────────────────────────────────────────
def draw_accel_icon(surf, cx, cy, t, size=28):
    """Draw the Accelerator icon — scales to any size."""
    s = size / 28.0  # scale factor

    def sc(v): return max(1, int(v * s))

    pulse = abs(math.sin(t * 3.5))

    # ── Outer aura ────────────────────────────────────────────────────────────
    aura_r = sc(38) + int(pulse * sc(5))
    aura_alpha = int(28 + pulse * 36)
    aura_surf = pygame.Surface((aura_r * 2 + 4, aura_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(aura_surf, (100, 40, 255, aura_alpha),
                       (aura_r + 2, aura_r + 2), aura_r)
    surf.blit(aura_surf, (cx - aura_r - 2, cy - aura_r - 2))

    # ── Outer rotating dashed ring ────────────────────────────────────────────
    ring1_r = sc(30)
    ring1_spin = t * 140
    seg_count = 8
    seg_arc = math.pi * 2 / seg_count
    ring1_s = pygame.Surface((ring1_r * 2 + 8, ring1_r * 2 + 8), pygame.SRCALPHA)
    sc1 = ring1_r + 4
    for i in range(seg_count):
        a_start = math.radians(ring1_spin) + i * seg_arc
        a_end = a_start + seg_arc * 0.55
        steps = max(4, int(10 * s))
        pts = []
        for st in range(steps + 1):
            a = a_start + (a_end - a_start) * st / steps
            pts.append((sc1 + math.cos(a) * ring1_r, sc1 + math.sin(a) * ring1_r))
        if len(pts) >= 2:
            intensity = int(180 + abs(math.sin(t * 4 + i)) * 60)
            pygame.draw.lines(ring1_s, (intensity, 80, 255, 220), False, pts, max(1, sc(3)))
    surf.blit(ring1_s, (cx - sc1, cy - sc1))

    # ── Inner counter-rotating dashed ring ────────────────────────────────────
    ring2_r = sc(22)
    ring2_spin = -t * 200
    ring2_s = pygame.Surface((ring2_r * 2 + 8, ring2_r * 2 + 8), pygame.SRCALPHA)
    sc2 = ring2_r + 4
    for i in range(6):
        a_start = math.radians(ring2_spin) + i * (math.pi / 3)
        a_end = a_start + math.pi / 3 * 0.45
        steps = max(3, int(8 * s))
        pts = []
        for st in range(steps + 1):
            a = a_start + (a_end - a_start) * st / steps
            pts.append((sc2 + math.cos(a) * ring2_r, sc2 + math.sin(a) * ring2_r))
        if len(pts) >= 2:
            pygame.draw.lines(ring2_s, (200, 150, 255, 195), False, pts, max(1, sc(2)))
    surf.blit(ring2_s, (cx - sc2, cy - sc2))

    # ── 4 spinning energy nodes ───────────────────────────────────────────────
    node_spin = t * 90
    node_r = sc(30)
    for i in range(4):
        na = math.radians(node_spin + i * 90)
        nx = int(cx + math.cos(na) * node_r)
        ny = int(cy + math.sin(na) * node_r)
        gn_r = max(4, sc(7))
        gn = pygame.Surface((gn_r * 2 + 4, gn_r * 2 + 4), pygame.SRCALPHA)
        node_glow = int(100 + abs(math.sin(t * 5 + i)) * 100)
        pygame.draw.circle(gn, (180, 80, 255, node_glow), (gn_r + 2, gn_r + 2), gn_r)
        surf.blit(gn, (nx - gn_r - 2, ny - gn_r - 2))
        pygame.draw.circle(surf, (80, 20, 160), (nx, ny), max(2, sc(5)))
        pygame.draw.circle(surf, (220, 160, 255), (nx, ny), max(1, sc(3)))
        pygame.draw.circle(surf, (255, 240, 255), (nx, ny), max(1, sc(1)))

    # ── Body: layered gradient core ───────────────────────────────────────────
    pygame.draw.circle(surf, (20, 8, 50),   (cx, cy), sc(20))
    pygame.draw.circle(surf, (60, 20, 140), (cx, cy), sc(17))
    pygame.draw.circle(surf, (100, 40, 200),(cx, cy), sc(13))
    pygame.draw.circle(surf, C_ACCEL,       (cx, cy), sc(10))
    pygame.draw.circle(surf, (200, 140, 255),(cx, cy), sc(6))

    # ── Rotating cross lines inside core ─────────────────────────────────────
    cross_spin = t * 260
    for i in range(4):
        ca = math.radians(cross_spin + i * 90)
        ex = int(cx + math.cos(ca) * sc(13))
        ey = int(cy + math.sin(ca) * sc(13))
        pygame.draw.line(surf, (220, 180, 255), (cx, cy), (ex, ey), max(1, sc(2)))

    # ── Pulsing nucleus ───────────────────────────────────────────────────────
    nuc_r = max(2, sc(3) + int(pulse * sc(2)))
    nuc_s = pygame.Surface((nuc_r * 2 + 4, nuc_r * 2 + 4), pygame.SRCALPHA)
    pygame.draw.circle(nuc_s, (255, 240, 255, int(200 + pulse * 55)),
                       (nuc_r + 2, nuc_r + 2), nuc_r)
    surf.blit(nuc_s, (cx - nuc_r - 2, cy - nuc_r - 2))


def draw_frost_icon(surf, cx, cy, t, size=28):
    spin = t * 180
    orb_r = int(size * 0.65)
    for i in range(4):
        a = math.radians(spin + i * 90)
        ox = cx + int(math.cos(a) * orb_r)
        oy = cy + int(math.sin(a) * orb_r)
        pygame.draw.circle(surf, C_FROST_ICE, (ox, oy), max(2, size // 7))
        pygame.draw.circle(surf, (255, 255, 255), (ox, oy), max(1, size // 14))
    pygame.draw.circle(surf, C_FROST_DARK, (cx, cy), int(size * 0.65))
    pygame.draw.circle(surf, C_FROST, (cx, cy), int(size * 0.48))
    for i in range(6):
        a = math.radians(i * 60 + t * 20)
        ex = cx + int(math.cos(a) * int(size * 0.4))
        ey = cy + int(math.sin(a) * int(size * 0.4))
        pygame.draw.line(surf, (180, 230, 255), (cx, cy), (ex, ey), 1)
    hi = max(1, size // 6)
    pygame.draw.circle(surf, (220, 250, 255), (cx - hi, cy - hi), hi + 1)


def _draw_tower_icon(surf, unit_name, cx, cy, t, size=32):
    """Draw a tower icon that matches how the tower looks in-game, scaled to fit."""
    # Scale factor: game uses radius ~27 for outer, size param is half-width
    s = size / 27.0  # scale relative to standard tower size

    def sc(v):
        """Scale a coordinate offset."""
        return int(v * s)

    def sp(v):
        """Scale a pixel size value."""
        return max(1, int(v * s))

    if unit_name == "Accelerator":
        draw_accel_icon(surf, cx, cy, t, size=size)

    elif unit_name == "Frostcelerator":
        draw_frost_icon(surf, cx, cy, t, size=size)



    elif unit_name == "Caster":
        # Deep blue body
        pygame.draw.circle(surf, (5, 15, 40),  (cx, cy), sc(27))
        pygame.draw.circle(surf, (10, 30, 70),  (cx, cy), sc(21))
        # 6 outer node dots (like in-game)
        for i in range(6):
            a = math.radians(i * 60)
            nx2 = cx + int(math.cos(a) * sc(18))
            ny2 = cy + int(math.sin(a) * sc(18))
            pygame.draw.circle(surf, (20, 80, 140), (nx2, ny2), max(1, sc(3)))
        # Two rings of spinning lines
        spin1 = t * 70; spin2 = -t * 110
        for i in range(6):
            a = math.radians(spin1 + i * 60)
            x1b = cx + int(math.cos(a) * sc(8));  y1b = cy + int(math.sin(a) * sc(8))
            x2b = cx + int(math.cos(a) * sc(15)); y2b = cy + int(math.sin(a) * sc(15))
            pygame.draw.line(surf, (40, 200, 255), (x1b, y1b), (x2b, y2b), max(1, sp(2)))
        for i in range(4):
            a = math.radians(spin2 + i * 90)
            x1b = cx + int(math.cos(a) * sc(9));  y1b = cy + int(math.sin(a) * sc(9))
            x2b = cx + int(math.cos(a) * sc(16)); y2b = cy + int(math.sin(a) * sc(16))
            pygame.draw.line(surf, (100, 220, 255), (x1b, y1b), (x2b, y2b), max(1, sp(1)))
        # Pulsing core
        core_r = max(2, int(abs(math.sin(t * 9)) * sc(3)) + sc(3))
        core_s = pygame.Surface((core_r * 4, core_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(core_s, (80, 200, 255, 90),  (core_r * 2, core_r * 2), core_r + sc(4))
        pygame.draw.circle(core_s, (180, 230, 255, 200), (core_r * 2, core_r * 2), core_r + sp(1))
        pygame.draw.circle(core_s, (220, 245, 255, 255), (core_r * 2, core_r * 2), core_r)
        surf.blit(core_s, (cx - core_r * 2, cy - core_r * 2))
        # Outer ring border
        pygame.draw.circle(surf, (40, 200, 255), (cx, cy), sc(21), sp(2))

    elif unit_name == "Assassin":
        # Dark slate body with cold blue rim
        pygame.draw.circle(surf, (15, 18, 28), (cx, cy), sc(27))
        pygame.draw.circle(surf, C_ASSASSIN, (cx, cy), sc(21))
        pygame.draw.circle(surf, (20, 25, 40), (cx, cy), sc(21), sp(3))
        pygame.draw.circle(surf, (60, 100, 200), (cx, cy), sc(27), sp(2))
        # Twin crossed daggers in preview
        for idle_deg in (-50, -130):
            ia = math.radians(idle_deg)
            tx2 = cx + int(math.cos(ia) * sc(26))
            ty2 = cy + int(math.sin(ia) * sc(26))
            bx2 = cx + int(math.cos(ia) * sc(8))
            by2 = cy + int(math.sin(ia) * sc(8))
            pygame.draw.line(surf, (120, 160, 210), (bx2, by2), (tx2, ty2), sp(4))
            ga = ia + math.pi / 2
            pygame.draw.line(surf, (40, 60, 90),
                             (int(bx2 + math.cos(ga)*sc(7)), int(by2 + math.sin(ga)*sc(7))),
                             (int(bx2 - math.cos(ga)*sc(7)), int(by2 - math.sin(ga)*sc(7))), sp(3))

    elif unit_name == "Militant":
        pygame.draw.circle(surf, C_MILITANT_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_MILITANT, (cx, cy), sc(21))
        # Helmet
        helmet_rect = pygame.Rect(cx - sc(18), cy - sc(27), sc(36), sc(20))
        pygame.draw.ellipse(surf, (50, 35, 10), helmet_rect)
        pygame.draw.arc(surf, (90, 65, 20), helmet_rect, 0, math.pi, sp(4))
        # Rifle (pointing right)
        angle = 0.0
        bx2 = cx + sc(14); by2 = cy
        ex2 = cx + sc(30); ey2 = cy
        pygame.draw.line(surf, (70, 55, 25), (bx2, by2), (ex2, ey2), sp(5))
        pygame.draw.line(surf, (180, 150, 80), (bx2, by2), (ex2, ey2), sp(3))

    elif unit_name == "Archer":
        _star_skin = (get_equipped_skin("Archer") == "archer_star")
        if _star_skin:
            pygame.draw.circle(surf, (60, 40, 0), (cx, cy), sc(27))
            pygame.draw.circle(surf, (200, 160, 30), (cx, cy), sc(21))
            pygame.draw.circle(surf, (255, 220, 80), (cx, cy), sc(21), sp(2))
            for si2 in range(3):
                sa2 = math.radians(t * 140 + si2 * 120)
                ssx = cx + int(math.cos(sa2) * sc(24)); ssy = cy + int(math.sin(sa2) * sc(24))
                star_pts = []
                for pi2 in range(10):
                    r2 = sc(5) if pi2 % 2 == 0 else sc(2)
                    a2 = math.radians(-90 + pi2 * 36)
                    star_pts.append((ssx + int(math.cos(a2) * r2), ssy + int(math.sin(a2) * r2)))
                pygame.draw.polygon(surf, (255, 220, 60), star_pts)
        else:
            # Warm amber aura glow
            aura_a4 = pygame.Surface((sc(72), sc(72)), pygame.SRCALPHA)
            pygame.draw.circle(aura_a4, (180, 110, 40, 45), (sc(36), sc(36)), sc(36))
            surf.blit(aura_a4, (cx - sc(36), cy - sc(36)))
            # Body
            pygame.draw.circle(surf, C_ARCHER_DARK, (cx, cy), sc(27))
            pygame.draw.circle(surf, C_ARCHER, (cx, cy), sc(21))
            # Wood-grain ring + radial lines
            pygame.draw.circle(surf, (100, 60, 20), (cx, cy), sc(21), sp(3))
            for li in range(3):
                la = math.radians(li * 60 - 30)
                pygame.draw.line(surf, (200, 140, 70),
                    (cx + int(math.cos(la) * sc(6)),  cy + int(math.sin(la) * sc(6))),
                    (cx + int(math.cos(la) * sc(18)), cy + int(math.sin(la) * sc(18))), sp(1))
            pygame.draw.circle(surf, (220, 165, 80), (cx, cy), sc(21), sp(2))
            # Highlight
            pygame.draw.circle(surf, (240, 200, 120), (cx - sc(6), cy - sc(6)), sp(4))
            pygame.draw.circle(surf, (255, 230, 170), (cx - sc(7), cy - sc(7)), sp(2))
            # Quiver
            pygame.draw.rect(surf, (55, 30, 8),
                pygame.Rect(cx + sc(12), cy + sc(4), sc(8), sc(16)), border_radius=sp(2))
            pygame.draw.rect(surf, (110, 70, 20),
                pygame.Rect(cx + sc(12), cy + sc(4), sc(8), sc(16)), sp(1), border_radius=sp(2))
            for qi in range(3):
                fla = math.radians(-110 + qi * 20)
                fex = cx + sc(16) + int(math.cos(fla) * sc(10))
                fey = cy + sc(4)  + int(math.sin(fla) * sc(4))
                pygame.draw.line(surf, (180, 100, 40), (cx + sc(16), cy + sc(4)), (fex, fey), sp(1))
        # Bow pointing right — carved dark wood
        a = 0.0; ca = math.cos(a); sa = math.sin(a); pa = -sa; pb = ca
        bow_cx = cx + sc(-8); bow_cy = cy; bow_arm = sc(16)
        bow_col = (255, 200, 40) if _star_skin else (100, 60, 15)
        pygame.draw.line(surf, bow_col,
                         (int(bow_cx + pa * bow_arm), int(bow_cy + pb * bow_arm)),
                         (int(bow_cx - pa * bow_arm), int(bow_cy - pb * bow_arm)), sp(4))
        highlight_col4 = (255, 200, 40) if _star_skin else (175, 120, 55)
        pygame.draw.line(surf, highlight_col4,
                         (int(bow_cx + pa * bow_arm), int(bow_cy + pb * bow_arm)),
                         (int(bow_cx - pa * bow_arm), int(bow_cy - pb * bow_arm)), sp(1))
        # Notch tips
        for side4 in (1, -1):
            pygame.draw.circle(surf, (220, 170, 80),
                (int(bow_cx + pa * bow_arm * side4), int(bow_cy + pb * bow_arm * side4)), sp(2))
        string_col = (255, 255, 180) if _star_skin else (220, 200, 160)
        pygame.draw.line(surf, string_col,
                         (int(bow_cx + pa * bow_arm), int(bow_cy + pb * bow_arm)),
                         (cx + sc(2), cy), sp(1))
        pygame.draw.line(surf, string_col,
                         (int(bow_cx - pa * bow_arm), int(bow_cy - pb * bow_arm)),
                         (cx + sc(2), cy), sp(1))
        # Arrow shaft — dark wood + metal tip
        shaft_col = (255, 220, 60) if _star_skin else (130, 85, 30)
        pygame.draw.line(surf, shaft_col, (cx - sc(14), cy), (cx + sc(18), cy), sp(2))
        pygame.draw.polygon(surf, (210, 190, 140), [
            (cx + sc(18), cy), (cx + sc(12), cy - sc(5)), (cx + sc(12), cy + sc(5))])
        # Fletching — warm feathers
        for fc4, fm4 in [((200, 140, 60), 1), ((160, 100, 40), -1)]:
            flt_col4 = (255, 200, 40) if _star_skin else fc4
            pygame.draw.line(surf, flt_col4,
                (cx - sc(14), cy),
                (cx - sc(18), cy + sc(6) * fm4), sp(2))

    elif unit_name == "Farm":
        # Leaf spikes
        for i in range(6):
            a = math.radians(i * 60 - 90)
            tip_x = cx + int(math.cos(a) * sc(33)); tip_y = cy + int(math.sin(a) * sc(33))
            l_x = cx + int(math.cos(a - 0.4) * sc(22)); l_y = cy + int(math.sin(a - 0.4) * sc(22))
            r_x = cx + int(math.cos(a + 0.4) * sc(22)); r_y = cy + int(math.sin(a + 0.4) * sc(22))
            pygame.draw.polygon(surf, (50, 140, 35), [(tip_x, tip_y), (l_x, l_y), (r_x, r_y)])
        pygame.draw.circle(surf, C_FARM_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_FARM, (cx, cy), sc(20))
        pygame.draw.circle(surf, (100, 210, 70), (cx, cy), sc(20), sp(2))
        # Coin symbol
        ico = load_icon("money_ico", sc(27))
        if ico:
            surf.blit(ico, (cx - ico.get_width() // 2, cy - ico.get_height() // 2))
        else:
            fs = pygame.font.SysFont("segoeui", sp(18), bold=True)
            ts = fs.render("$", True, C_GOLD)
            surf.blit(ts, ts.get_rect(center=(cx, cy)))

    elif unit_name == "Red Ball":
        _true_skin = (get_equipped_skin("Red Ball") == "redball_true")
        if _true_skin:
            pygame.draw.circle(surf, (160, 10, 10), (cx, cy), sc(24))
            pygame.draw.circle(surf, (220, 30, 30), (cx, cy), sc(22))
            hl_s = pygame.Surface((sc(44), sc(44)), pygame.SRCALPHA)
            pygame.draw.circle(hl_s, (255, 80, 80, 110), (sc(15), sc(14)), sc(14))
            surf.blit(hl_s, (cx - sc(22), cy - sc(22)))
            pygame.draw.circle(surf, (255, 160, 160), (cx - sc(7), cy - sc(9)), sp(5))
            pygame.draw.circle(surf, (255, 230, 230), (cx - sc(8), cy - sc(10)), sp(2))
            # Eyes
            pygame.draw.circle(surf, (255, 255, 255), (cx - sc(7), cy - sc(2)), sp(6))
            pygame.draw.circle(surf, (255, 255, 255), (cx + sc(6), cy - sc(2)), sp(6))
            pygame.draw.circle(surf, (30, 20, 10), (cx - sc(5), cy - sc(2)), sp(3))
            pygame.draw.circle(surf, (30, 20, 10), (cx + sc(8), cy - sc(2)), sp(3))
            pygame.draw.circle(surf, (255, 255, 255), (cx - sc(4), cy - sc(4)), sp(1))
            pygame.draw.circle(surf, (255, 255, 255), (cx + sc(9), cy - sc(4)), sp(1))
            # Smile
            pygame.draw.arc(surf, (160, 10, 10),
                            pygame.Rect(cx - sc(9), cy + sc(5), sc(18), sc(10)),
                            math.radians(200), math.radians(340), sp(2))
        else:
            pygame.draw.circle(surf, C_REDBALL_DARK, (cx, cy), sc(24))
            pygame.draw.circle(surf, C_REDBALL, (cx, cy), sc(20))
            pygame.draw.arc(surf, (160, 20, 20),
                            pygame.Rect(cx - sc(14), cy - sc(18), sc(28), sc(20)),
                            math.radians(10), math.radians(170), sp(2))
            pygame.draw.arc(surf, (160, 20, 20),
                            pygame.Rect(cx - sc(14), cy - sc(2), sc(28), sc(20)),
                            math.radians(190), math.radians(350), sp(2))
            pygame.draw.line(surf, (160, 20, 20), (cx - sc(20), cy), (cx + sc(20), cy), sp(2))
            pygame.draw.circle(surf, (255, 100, 100), (cx - sc(7), cy - sc(7)), sp(5))
            pygame.draw.circle(surf, (180, 20, 20), (cx, cy), sc(24), sp(2))

    elif unit_name == "Lifestealer":
        # Hexagonal base
        hex_pts3 = []
        for i in range(6):
            a3 = math.radians(i*60 - 30)
            hex_pts3.append((cx+int(math.cos(a3)*sc(24)), cy+int(math.sin(a3)*sc(24))))
        pygame.draw.polygon(surf, C_LIFESTEALER_DARK, hex_pts3)
        pygame.draw.polygon(surf, C_LIFESTEALER, hex_pts3, sp(2))
        # Inner venom core
        pygame.draw.circle(surf, (30, 120, 60), (cx, cy), sc(15))
        pygame.draw.circle(surf, (80, 220, 140), (cx, cy), sc(15), sp(2))
        # Teardrop/venom symbol
        pygame.draw.circle(surf, (140, 255, 180), (cx, cy - sc(4)), sc(5))
        pts_drop = [(cx - sc(5), cy - sc(2)), (cx + sc(5), cy - sc(2)), (cx, cy + sc(8))]
        pygame.draw.polygon(surf, (140, 255, 180), pts_drop)
        # Outer rim
        pygame.draw.circle(surf, C_LIFESTEALER, (cx, cy), sc(27), sp(2))

    elif unit_name == "Freezer":
        pygame.draw.circle(surf, C_FREEZER_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_FREEZER, (cx, cy), sc(21))
        # Snowflake
        for i in range(6):
            a = math.radians(i * 60 + t * 15)
            ex2 = cx + int(math.cos(a) * sc(16)); ey2 = cy + int(math.sin(a) * sc(16))
            pygame.draw.line(surf, (200, 240, 255), (cx, cy), (ex2, ey2), sp(2))
            for side in (-1, 1):
                ba = a + math.radians(side * 45)
                bxb = cx + int(math.cos(a) * sc(9)) + int(math.cos(ba) * sc(5))
                byb = cy + int(math.sin(a) * sc(9)) + int(math.sin(ba) * sc(5))
                pygame.draw.line(surf, (160, 220, 255),
                                 (cx + int(math.cos(a) * sc(9)), cy + int(math.sin(a) * sc(9))),
                                 (bxb, byb), sp(1))
        pygame.draw.circle(surf, (240, 255, 255), (cx, cy), sp(5))
        pygame.draw.circle(surf, C_FREEZER, (cx, cy), sc(27), sp(2))

    elif unit_name == "Frost Blaster":
        # Hex base — void purple
        hex_pts3 = []
        for i in range(6):
            a3 = math.radians(i * 60 + t * 8)
            hex_pts3.append((cx + int(math.cos(a3) * sc(24)), cy + int(math.sin(a3) * sc(24))))
        pygame.draw.polygon(surf, C_FROSTBLASTER_DARK, hex_pts3)
        pygame.draw.polygon(surf, C_FROSTBLASTER, hex_pts3, sp(2))
        # Spinning energy arcs — 3-segment rings
        for r3, spd3, col3 in [(sc(19), 60, (160,40,255)), (sc(13), -90, (200,120,255))]:
            for seg in range(3):
                sa3 = math.radians(t * spd3 + seg * 120)
                ea3 = sa3 + math.radians(65)
                try:
                    pygame.draw.arc(surf, col3, pygame.Rect(cx-r3, cy-r3, r3*2, r3*2), sa3, ea3, sp(2))
                except Exception:
                    pass
        # Barrel pointing right
        ca3, sa3b = 1.0, 0.0; pa3, pb3 = 0.0, 1.0
        bl = sc(20); bw = sc(5)
        b_pts3 = [
            (cx + int(pa3*bw - ca3*4),   cy + int(pb3*bw - sa3b*4)),
            (cx - int(pa3*bw + ca3*4),   cy - int(pb3*bw - sa3b*4)),
            (cx - int(pa3*bw - ca3*bl),  cy - int(pb3*bw - sa3b*bl)),
            (cx + int(pa3*bw + ca3*bl),  cy + int(pb3*bw + sa3b*bl)),
        ]
        pygame.draw.polygon(surf, (55, 15, 100), b_pts3)
        pygame.draw.polygon(surf, (180, 80, 255), b_pts3, sp(1))
        # Core
        pygame.draw.circle(surf, (70, 10, 130), (cx, cy), sc(8))
        pygame.draw.circle(surf, (200, 120, 255), (cx, cy), sc(8), sp(2))

    elif unit_name == "Sledger":
        # Octagonal iron body
        oct_pts3 = []
        for i in range(8):
            a_o3 = math.radians(i * 45 + 22.5)
            oct_pts3.append((cx + int(math.cos(a_o3)*sc(24)),
                             cy + int(math.sin(a_o3)*sc(24))))
        pygame.draw.polygon(surf, C_SLEDGER_DARK, oct_pts3)
        pygame.draw.polygon(surf, C_SLEDGER, oct_pts3, sp(2))
        # Forge core
        pygame.draw.circle(surf, (80, 30, 5), (cx, cy), sc(16))
        pygame.draw.circle(surf, (200, 80, 15), (cx, cy), sc(12))
        pygame.draw.circle(surf, (255, 200, 60), (cx, cy), sc(6))
        pygame.draw.circle(surf, (255, 240, 180), (cx, cy), sc(2))
        # Massive hammer pointing right
        ca2, sa2 = 1.0, 0.0; pa2 = 0.0; pb2 = 1.0
        hx1 = cx + sc(6); hx2 = cx + sc(26)
        pygame.draw.line(surf, (90, 55, 20), (hx1, cy), (hx2, cy), sp(5))
        pygame.draw.line(surf, (140, 90, 35), (hx1, cy), (hx2, cy), sp(2))
        head_cx = cx + sc(30); head_cy = cy
        pts = [
            (int(head_cx + pa2*sc(11) - ca2*sc(6)),  int(head_cy + pb2*sc(11) - sa2*sc(6))),
            (int(head_cx - pa2*sc(11) - ca2*sc(6)),  int(head_cy - pb2*sc(11) - sa2*sc(6))),
            (int(head_cx - pa2*sc(11) + ca2*sc(10)), int(head_cy - pb2*sc(11) + sa2*sc(10))),
            (int(head_cx + pa2*sc(11) + ca2*sc(10)), int(head_cy + pb2*sc(11) + sa2*sc(10))),
        ]
        pygame.draw.polygon(surf, (60, 35, 10), pts)
        pygame.draw.polygon(surf, C_SLEDGER, pts, sp(2))
        # Hot strike face
        fs2 = pygame.Surface((sc(16), sc(16)), pygame.SRCALPHA)
        pygame.draw.circle(fs2, (255, 160, 20, 180), (sc(8), sc(8)), sc(7))
        pygame.draw.circle(fs2, (255, 230, 100, 220), (sc(8), sc(8)), sc(3))
        surf.blit(fs2, (head_cx + sc(2) - sc(8), head_cy - sc(8)))

    elif unit_name == "Gladiator":
        t_g = pygame.time.get_ticks() * 0.001
        a_g = math.radians(25) + math.sin(t_g * 2.5) * 0.15
        ca_g, sa_g = math.cos(a_g), math.sin(a_g)
        pa_g, pb_g = -sa_g, ca_g
        # Shadow
        shd = pygame.Surface((sc(64), sc(18)), pygame.SRCALPHA)
        pygame.draw.ellipse(shd, (0,0,0,35), (0, 0, sc(64), sc(18)))
        surf.blit(shd, (cx - sc(32), cy + sc(22)))
        # Base dark ring
        pygame.draw.circle(surf, (50, 35, 5), (cx, cy), sc(27))
        # Armor body
        pygame.draw.circle(surf, (160, 120, 30), (cx, cy), sc(22))
        chest_g = pygame.Surface((sc(44), sc(44)), pygame.SRCALPHA)
        pygame.draw.circle(chest_g, (220, 175, 55, 170), (sc(22), sc(22)), sc(18))
        surf.blit(chest_g, (cx - sc(22), cy - sc(22)))
        # Chest emblem diamond
        emb_g = [(cx, cy - sc(10)), (cx + sc(6), cy), (cx, cy + sc(7)), (cx - sc(6), cy)]
        pygame.draw.polygon(surf, (80, 55, 10), emb_g)
        pygame.draw.polygon(surf, (255, 210, 80), emb_g, sp(1))
        # Shoulder pads
        for sd_g in (-1, 1):
            sx_g = cx + sd_g * sc(18)
            pygame.draw.circle(surf, (100, 75, 15), (sx_g, cy - sc(4)), sc(7))
            pygame.draw.circle(surf, (200, 160, 45), (sx_g, cy - sc(4)), sc(5))
            pygame.draw.circle(surf, (255, 230, 100), (sx_g, cy - sc(4)), sc(5), sp(1))
        # Helmet
        helm_g = [
            (cx - sc(12), cy - sc(18)),
            (cx - sc(14), cy - sc(29)),
            (cx,          cy - sc(35)),
            (cx + sc(14), cy - sc(29)),
            (cx + sc(12), cy - sc(18)),
        ]
        pygame.draw.polygon(surf, (130, 95, 20), helm_g)
        pygame.draw.polygon(surf, (210, 170, 50), helm_g, sp(2))
        pygame.draw.line(surf, (30, 20, 5),   (cx - sc(7), cy - sc(24)), (cx + sc(7), cy - sc(24)), sp(2))
        pygame.draw.line(surf, (255, 190, 40), (cx - sc(5), cy - sc(24)), (cx + sc(5), cy - sc(24)), sp(1))
        # Plume animated
        bob_g = int(math.sin(t_g * 3.5) * sc(2))
        for i_g in range(6):
            pygame.draw.circle(surf, (200, 50, 40),
                               (cx - sc(3) + i_g * sc(2), cy - sc(35) - i_g + bob_g), sc(2))
        pygame.draw.line(surf, (220, 70, 50),
                         (cx - sc(3), cy - sc(35) + bob_g), (cx + sc(6), cy - sc(40) + bob_g), sp(2))
        # Shield
        sh_angle_g = a_g + math.radians(135)
        sc2_g = math.cos(sh_angle_g); ss2_g = math.sin(sh_angle_g)
        shx_g = cx + int(sc2_g * sc(17)); shy_g = cy + int(ss2_g * sc(17))
        shpts_g = [
            (shx_g + int(-sc2_g * sc(3) - ss2_g * sc(10)), shy_g + int(-ss2_g * sc(3) + sc2_g * sc(10))),
            (shx_g + int( sc2_g * sc(10) - ss2_g * sc(5)), shy_g + int( ss2_g * sc(10) + sc2_g * sc(5))),
            (shx_g + int( sc2_g * sc(10) + ss2_g * sc(5)), shy_g + int( ss2_g * sc(10) - sc2_g * sc(5))),
            (shx_g + int(-sc2_g * sc(3) + ss2_g * sc(10)), shy_g + int(-ss2_g * sc(3) - sc2_g * sc(10))),
        ]
        pygame.draw.polygon(surf, (60, 45, 10), shpts_g)
        pygame.draw.polygon(surf, (180, 140, 35), shpts_g, sp(2))
        pygame.draw.circle(surf, (220, 180, 60), (shx_g, shy_g), sc(3))
        # Sword pommel
        pygame.draw.circle(surf, (160, 120, 30), (cx + int(ca_g * sc(6)), cy + int(sa_g * sc(6))), sc(4))
        pygame.draw.circle(surf, (220, 180, 60), (cx + int(ca_g * sc(6)), cy + int(sa_g * sc(6))), sc(4), sp(1))
        # Grip
        pygame.draw.line(surf, (110, 75, 20),
                         (cx + int(ca_g * sc(7)),  cy + int(sa_g * sc(7))),
                         (cx + int(ca_g * sc(21)), cy + int(sa_g * sc(21))), sp(5))
        pygame.draw.line(surf, (180, 140, 50),
                         (cx + int(ca_g * sc(7)),  cy + int(sa_g * sc(7))),
                         (cx + int(ca_g * sc(21)), cy + int(sa_g * sc(21))), sp(2))
        # Crossguard
        ggx1 = cx + int(ca_g * sc(21) + pa_g * sc(12)); ggy1 = cy + int(sa_g * sc(21) + pb_g * sc(12))
        ggx2 = cx + int(ca_g * sc(21) - pa_g * sc(12)); ggy2 = cy + int(sa_g * sc(21) - pb_g * sc(12))
        pygame.draw.line(surf, (100, 70, 15), (ggx1, ggy1), (ggx2, ggy2), sp(5))
        pygame.draw.line(surf, (220, 180, 60), (ggx1, ggy1), (ggx2, ggy2), sp(2))
        pygame.draw.circle(surf, (255, 220, 80), (ggx1, ggy1), sc(2))
        pygame.draw.circle(surf, (255, 220, 80), (ggx2, ggy2), sc(2))
        # Blade
        gbx1 = cx + int(ca_g * sc(23)); gby1 = cy + int(sa_g * sc(23))
        gbx2 = cx + int(ca_g * sc(50)); gby2 = cy + int(sa_g * sc(50))
        pygame.draw.line(surf, (170, 155, 100), (gbx1, gby1), (gbx2, gby2), sp(4))
        pygame.draw.line(surf, (240, 235, 200), (gbx1, gby1), (gbx2, gby2), sp(2))
        pygame.draw.line(surf, (255, 255, 240),
                         (gbx1 + int(pa_g), gby1 + int(pb_g)),
                         (gbx2 + int(pa_g), gby2 + int(pb_g)), sp(1))
        pygame.draw.circle(surf, (255, 255, 230), (int(gbx2), int(gby2)), sc(3))
        # Outer trim ring
        pygame.draw.circle(surf, (255, 220, 80), (cx, cy), sc(27), sp(2))

    elif unit_name == "Toxic Gunner":
        # Purple-void body
        pygame.draw.circle(surf, C_TOXICGUN_DARK, (cx, cy), sc(28))
        pygame.draw.circle(surf, C_TOXICGUN, (cx, cy), sc(22))
        pygame.draw.circle(surf, C_TOXICGUN_ACID, (cx, cy), sc(22), sp(3))
        # Barrel with acid stripe pointing right
        bx1 = cx + sc(10); bx2 = cx + sc(34)
        pygame.draw.line(surf, C_TOXICGUN_DARK, (bx1, cy), (bx2, cy), sp(8))
        pygame.draw.line(surf, C_TOXICGUN, (bx1, cy), (bx2, cy), sp(5))
        pygame.draw.line(surf, C_TOXICGUN_ACID, (bx1, cy), (bx2, cy), sp(2))
        pygame.draw.circle(surf, C_TOXICGUN_ACID, (bx2, cy), sp(5))
        pygame.draw.circle(surf, C_TOXICGUN_DARK, (bx2, cy), sp(2))
        # Pressure valve rings
        for i in range(3):
            rx2 = cx + sc(13 + i * 7)
            pygame.draw.circle(surf, C_TOXICGUN_ACID, (rx2, cy), sp(4), sp(2))

    elif unit_name == "Slasher":
        # Blood-mist aura
        mist_r=sc(34); mist_a=int(28+abs(math.sin(t*1.4))*18)
        mist_s=pygame.Surface((mist_r*2+4,mist_r*2+4),pygame.SRCALPHA)
        pygame.draw.circle(mist_s,(180,10,10,mist_a),(mist_r+2,mist_r+2),mist_r)
        surf.blit(mist_s,(cx-mist_r-2,cy-mist_r-2))
        # Body layers
        pygame.draw.circle(surf,(18,4,4),(cx,cy),sc(26))
        pygame.draw.circle(surf,(80,12,12),(cx,cy),sc(22))
        pygame.draw.circle(surf,(130,20,20),(cx,cy),sc(16))
        pygame.draw.circle(surf,(200,30,30),(cx,cy),sc(9))
        pygame.draw.circle(surf,(255,80,60),(cx,cy),sc(4))
        rim_sz=sc(56); rim_s=pygame.Surface((rim_sz,rim_sz),pygame.SRCALPHA)
        pygame.draw.circle(rim_s,(255,40,0,55),(rim_sz//2,rim_sz//2),sc(22),sp(3))
        surf.blit(rim_s,(cx-rim_sz//2,cy-rim_sz//2))
        # Shoulder spikes
        for spike_a in [45,135,225,315]:
            sa_r=math.radians(spike_a+t*8)
            sx=cx+int(math.cos(sa_r)*sc(20)); sy=cy+int(math.sin(sa_r)*sc(20))
            tx2=cx+int(math.cos(sa_r)*sc(30)); ty2=cy+int(math.sin(sa_r)*sc(30))
            pygame.draw.line(surf,(60,8,8),(sx,sy),(tx2,ty2),sp(3))
            pygame.draw.circle(surf,(200,40,20),(tx2,ty2),sp(2))
        # Cleaver blade pointing right
        a2=math.radians(-40)
        ca2,sa2=math.cos(a2),math.sin(a2); perp2x,perp2y=-sa2,ca2
        pygame.draw.line(surf,(40,10,10),(cx+int(ca2*sc(6)),cy+int(sa2*sc(6))),(cx+int(ca2*sc(28)),cy+int(sa2*sc(28))),sp(4))
        for step in range(7):
            frac=step/6.0; blen=sc(int(10+frac*24)); w_off=int(sc(7)*(1.0-frac*0.55))
            bx2=cx+int(ca2*blen); by2=cy+int(sa2*blen)
            lx2=int(bx2+perp2x*w_off); ly2=int(by2+perp2y*w_off)
            rx2=int(bx2-perp2x*w_off); ry2=int(by2-perp2y*w_off)
            col_m=int(150+frac*70)
            pygame.draw.line(surf,(col_m,col_m-10,col_m-10),(lx2,ly2),(rx2,ry2),sp(2))
        tip2x=cx+int(ca2*sc(34)+perp2x*sp(2)); tip2y=cy+int(sa2*sc(34)+perp2y*sp(2))
        base2x=cx+int(ca2*sc(10)+perp2x*sc(6)); base2y=cy+int(sa2*sc(10)+perp2y*sc(6))
        pygame.draw.line(surf,(230,200,200),(base2x,base2y),(tip2x,tip2y),sp(2))
        pygame.draw.circle(surf,(255,240,230),(tip2x,tip2y),sp(3))
        pygame.draw.line(surf,(100,5,5),(cx+int(ca2*sc(14)),cy+int(sa2*sc(14))),(cx+int(ca2*sc(32)),cy+int(sa2*sc(32))),sp(1))
        ga2=a2+math.pi/2
        gx1=cx+int(ca2*sc(12)+math.cos(ga2)*sc(9)); gy1=cy+int(sa2*sc(12)+math.sin(ga2)*sc(9))
        gx2=cx+int(ca2*sc(12)-math.cos(ga2)*sc(9)); gy2=cy+int(sa2*sc(12)-math.sin(ga2)*sc(9))
        pygame.draw.line(surf,(80,15,15),(gx1,gy1),(gx2,gy2),sp(4))
        pygame.draw.line(surf,(150,30,30),(gx1,gy1),(gx2,gy2),sp(2))

    elif unit_name in ("Cowboy", "Golden Cowboy"):
        # Body — dark leather + copper plate
        pygame.draw.circle(surf, C_GCOWBOY_DARK, (cx, cy), sc(28))
        pygame.draw.circle(surf, C_GCOWBOY,      (cx, cy), sc(22))
        pygame.draw.circle(surf, C_GCOWBOY_STAR,  (cx, cy), sc(22), sp(2))
        # Sheriff star
        star_pts_s = []
        for i in range(10):
            r_ss = sc(10) if i % 2 == 0 else sc(4)
            a_ss = math.radians(-90 + i * 36)
            star_pts_s.append((cx + int(math.cos(a_ss) * r_ss),
                               cy + int(math.sin(a_ss) * r_ss)))
        pygame.draw.polygon(surf, C_GCOWBOY_STAR, star_pts_s)
        pygame.draw.polygon(surf, C_GCOWBOY_DARK, star_pts_s, sp(1))
        # Hat brim + crown
        pygame.draw.ellipse(surf, C_GCOWBOY_BRIM,
                            (cx - sc(19), cy - sc(31), sc(38), sc(10)))
        crown_pts_s = [(cx - sc(11), cy - sc(31)),
                       (cx - sc(9),  cy - sc(46)),
                       (cx + sc(9),  cy - sc(46)),
                       (cx + sc(11), cy - sc(31))]
        pygame.draw.polygon(surf, C_GCOWBOY_BRIM, crown_pts_s)
        pygame.draw.line(surf, C_GCOWBOY_STAR,
                         (cx - sc(11), cy - sc(33)), (cx + sc(11), cy - sc(33)), sp(2))
        # Double barrel pointing right
        for sign_s in (1, -1):
            oy_s = sp(3) * sign_s
            pygame.draw.line(surf, C_GCOWBOY_BRIM,
                             (cx + sc(9),  cy + oy_s),
                             (cx + sc(32), cy + oy_s), sp(4))
            pygame.draw.line(surf, C_GCOWBOY,
                             (cx + sc(9),  cy + oy_s),
                             (cx + sc(32), cy + oy_s), sp(2))
        pygame.draw.circle(surf, C_GCOWBOY_STAR, (cx + sc(32), cy), sp(4))

    elif unit_name == "Hallow Punk":
        pulse3 = abs(math.sin(t * 2.5))
        # Glow
        gs3 = pygame.Surface((sc(68), sc(68)), pygame.SRCALPHA)
        pygame.draw.circle(gs3, (140, 50, 180, int(pulse3*50+20)), (sc(34), sc(34)), sc(31))
        surf.blit(gs3, (cx - sc(34), cy - sc(34)))
        # Burn ring
        brs3 = pygame.Surface((sc(60), sc(60)), pygame.SRCALPHA)
        pygame.draw.circle(brs3, (210, 100, 10, int(pulse3*70+50)), (sc(30), sc(30)), sc(27), sp(3))
        surf.blit(brs3, (cx - sc(30), cy - sc(30)))
        # Spikes (4 default for icon — static lv0 appearance)
        for i in range(4):
            ang3 = math.pi * 2 * i / 4 - math.pi / 4
            sx1 = cx + math.cos(ang3) * sc(20); sy1 = cy + math.sin(ang3) * sc(20)
            sx2 = cx + math.cos(ang3) * sc(28); sy2 = cy + math.sin(ang3) * sc(28)
            pygame.draw.line(surf, (200, 80, 200), (int(sx1), int(sy1)), (int(sx2), int(sy2)), sp(2))
        # Hex body
        hpts3 = [(cx + int(math.cos(math.pi*2*i/6 - math.pi/6)*sc(19)),
                  cy + int(math.sin(math.pi*2*i/6 - math.pi/6)*sc(19))) for i in range(6)]
        pygame.draw.polygon(surf, (42, 14, 68), hpts3)
        pygame.draw.polygon(surf, (88, 30, 120), hpts3, sp(2))
        # Core
        pygame.draw.circle(surf, (140, 50, 180), (cx, cy), sc(10))
        pygame.draw.circle(surf, (int(pulse3*40+180), 80, int(pulse3*40+180)), (cx, cy), sc(7))
        # Rocket launcher tube pointing right
        bx1 = cx + sc(6); bx2 = cx + sc(27)
        pygame.draw.line(surf, (60, 15, 80), (bx1, cy), (bx2, cy), sp(6))
        pygame.draw.line(surf, (200, 80, 200), (bx1, cy), (bx2, cy), sp(3))
        pygame.draw.circle(surf, (230, 120, 240), (bx2, cy), sp(4))
        # Muzzle burn ring
        ms3 = pygame.Surface((sp(12), sp(12)), pygame.SRCALPHA)
        pygame.draw.circle(ms3, (210, 100, 10, 160), (sp(6), sp(6)), sp(5), sp(2))
        surf.blit(ms3, (bx2 - sp(6), cy - sp(6)))
        # Antenna
        pygame.draw.line(surf, (88, 30, 120), (cx, cy - sc(19)), (cx, cy - sc(28)), sp(2))
        tip3 = pygame.Surface((sp(8), sp(8)), pygame.SRCALPHA)
        pygame.draw.circle(tip3, (200, 80, 200, int(pulse3*180+75)), (sp(4), sp(4)), sp(3))
        surf.blit(tip3, (cx - sp(4), cy - sc(28) - sp(4)))

    elif unit_name == "Spotlight Tech":
        # Arctic steel body
        pygame.draw.circle(surf, C_SPOTLIGHT_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_SPOTLIGHT, (cx, cy), sc(21))
        pygame.draw.circle(surf, (200, 240, 255), (cx, cy), sc(21), sp(2))
        pygame.draw.circle(surf, (80, 160, 220), (cx, cy), sc(27), sp(2))
        # Lamp head — dark steel blue housing
        head_cx = cx + sc(14); head_cy = cy
        pa3 = 0.0; pb3 = 1.0; ca3 = 1.0; sa3 = 0.0
        pts = [
            (int(head_cx + pa3 * sc(8) - ca3 * sc(6)), int(head_cy + pb3 * sc(8) - sa3 * sc(6))),
            (int(head_cx - pa3 * sc(8) - ca3 * sc(6)), int(head_cy - pb3 * sc(8) - sa3 * sc(6))),
            (int(head_cx - pa3 * sc(4) + ca3 * sc(9)), int(head_cy - pb3 * sc(4) + sa3 * sc(9))),
            (int(head_cx + pa3 * sc(4) + ca3 * sc(9)), int(head_cy + pb3 * sc(4) + sa3 * sc(9))),
        ]
        pygame.draw.polygon(surf, (30, 60, 100), pts)
        pygame.draw.polygon(surf, C_SPOTLIGHT, pts, sp(2))
        # Lens glow — icy blue
        lx = cx + sc(20)
        ls2 = pygame.Surface((sc(20), sc(20)), pygame.SRCALPHA)
        pygame.draw.circle(ls2, (160, 220, 255, 200), (sc(10), sc(10)), sp(8))
        pygame.draw.circle(ls2, (230, 245, 255, 255), (sc(10), sc(10)), sp(4))
        surf.blit(ls2, (lx - sc(10), cy - sc(10)))

    elif unit_name == "Snowballer":
        pygame.draw.circle(surf, C_SNOWBALLER_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_SNOWBALLER, (cx, cy), sc(21))
        pygame.draw.circle(surf, (200, 240, 255), (cx, cy), sc(21), sp(2))
        # Snowball in hand (right side)
        bx2 = cx + sc(24); by2 = cy - sc(6)
        pygame.draw.circle(surf, (220, 240, 255), (bx2, by2), sp(8))
        pygame.draw.circle(surf, (255, 255, 255), (bx2, by2), sp(8), sp(2))
        # Arm
        pygame.draw.line(surf, C_SNOWBALLER, (cx + sc(8), cy), (bx2, by2), sp(4))

    elif unit_name == "Commando":
        pygame.draw.circle(surf, C_COMMANDO_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_COMMANDO, (cx, cy), sc(21))
        pygame.draw.circle(surf, (100, 200, 100), (cx, cy), sc(21), sp(2))
        # Machine gun barrel pointing right (wide)
        bx1 = cx + sc(6); bx2 = cx + sc(32)
        pygame.draw.line(surf, (60, 120, 60), (bx1, cy), (bx2, cy), sp(7))
        pygame.draw.line(surf, (120, 200, 120), (bx1, cy), (bx2, cy), sp(4))
        # Grenade on left
        gr_x = cx - sc(18); gr_y = cy - sc(10)
        pygame.draw.circle(surf, (80, 140, 60), (gr_x, gr_y), sp(6))
        pygame.draw.line(surf, (60, 100, 40), (gr_x, gr_y - sp(6)), (gr_x, gr_y - sp(10)), sp(2))

    elif unit_name == "Warlock":
        pygame.draw.circle(surf, C_WARLOCK_DARK, (cx, cy), sc(26))
        pygame.draw.circle(surf, C_WARLOCK, (cx, cy), sc(20))
        pygame.draw.circle(surf, (200, 140, 255), (cx, cy), sc(20), sp(2))
        # Staff symbol (vertical)
        pygame.draw.line(surf, (200, 140, 255), (cx, cy - sc(14)), (cx, cy + sc(14)), sp(3))
        pygame.draw.circle(surf, (230, 180, 255), (cx, cy - sc(14)), sp(5))
        pygame.draw.circle(surf, (255, 220, 255), (cx, cy - sc(14)), sp(3))
        # Orbiting orb
        oa2 = math.radians(t * 120)
        ox2 = cx + int(math.cos(oa2) * sc(22)); oy2 = cy + int(math.sin(oa2) * sc(22))
        orb_s2 = pygame.Surface((sc(20), sc(20)), pygame.SRCALPHA)
        pygame.draw.circle(orb_s2, (180, 80, 255, 160), (sc(10), sc(10)), sp(8))
        pygame.draw.circle(orb_s2, (230, 180, 255, 220), (sc(10), sc(10)), sp(5))
        surf.blit(orb_s2, (ox2 - sc(10), oy2 - sc(10)))

    elif unit_name == "Jester":
        # Dark aura
        aura_s3 = pygame.Surface((sc(68), sc(68)), pygame.SRCALPHA)
        pygame.draw.circle(aura_s3, (80, 20, 160, 55), (sc(34), sc(34)), sc(34))
        surf.blit(aura_s3, (cx - sc(34), cy - sc(34)))
        # Body
        pygame.draw.circle(surf, C_JESTER_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_JESTER, (cx, cy), sc(21))
        pygame.draw.circle(surf, (200, 170, 40), (cx, cy), sc(21), sp(2))   # gold rim
        # Harlequin cross lines
        for ang3 in (30, 150):
            r3 = math.radians(ang3)
            pygame.draw.line(surf, (200, 120, 255),
                (cx + int(math.cos(r3)*sc(17)), cy + int(math.sin(r3)*sc(17))),
                (cx - int(math.cos(r3)*sc(17)), cy - int(math.sin(r3)*sc(17))), 1)
        # Specular highlight
        pygame.draw.circle(surf, (220, 180, 255), (cx - sc(6), cy - sc(6)), sp(4))
        pygame.draw.circle(surf, (255, 245, 255), (cx - sc(7), cy - sc(7)), sp(2))
        # Three-point hat
        tip_c3 = (cx,          cy - sc(50))
        tip_l3 = (cx - sc(22), cy - sc(38))
        tip_r3 = (cx + sc(22), cy - sc(38))
        brim_l3= (cx - sc(14), cy - sc(20))
        brim_r3= (cx + sc(14), cy - sc(20))
        hat_pts3 = [brim_l3, tip_l3, tip_c3, tip_r3, brim_r3]
        pygame.draw.polygon(surf, (18, 8, 40), hat_pts3)
        pygame.draw.polygon(surf, (90, 30, 160), [brim_l3, tip_l3, (cx-sc(4), cy-sc(32))])
        pygame.draw.polygon(surf, (90, 30, 160), [brim_r3, tip_r3, (cx+sc(4), cy-sc(32))])
        pygame.draw.polygon(surf, (170, 130, 20), [(cx-sc(4), cy-sc(32)), tip_c3, (cx+sc(4), cy-sc(32))])
        pygame.draw.polygon(surf, (200, 170, 40), hat_pts3, sp(2))
        pygame.draw.line(surf, (200, 170, 40), brim_l3, brim_r3, sp(2))
        # Bells on tips
        bell_g3 = abs(math.sin(t * 3.5))
        for tip3 in (tip_c3, tip_l3, tip_r3):
            bg3 = pygame.Surface((sc(14), sc(14)), pygame.SRCALPHA)
            pygame.draw.circle(bg3, (255, 220, 60, int(60 + 50*bell_g3)), (sc(7), sc(7)), sc(7))
            surf.blit(bg3, (tip3[0] - sc(7), tip3[1] - sc(7)))
            pygame.draw.circle(surf, (200, 160, 20), tip3, sp(5))
            pygame.draw.circle(surf, (255, 220, 80), tip3, sp(3))
        # Animated juggling bombs (three types, elliptical orbits)
        bcols3 = {"fire": (255, 100, 30), "ice": (80, 200, 255), "poison": (80, 220, 60)}
        for i in range(3):
            spd3 = 110 * (1 + i * 0.35)
            a3 = math.radians(t * spd3 + i * 120)
            bx3 = cx + int(math.cos(a3) * sc(25 + i*3))
            by3 = cy + int(math.sin(a3) * sc(16 + i*2) * 0.62)
            btype3 = ["fire", "ice", "poison"][i]
            bcol3 = bcols3[btype3]
            # glow
            gh3 = pygame.Surface((sc(16), sc(16)), pygame.SRCALPHA)
            pygame.draw.circle(gh3, (*bcol3, 80), (sc(8), sc(8)), sc(8))
            surf.blit(gh3, (bx3 - sc(8), by3 - sc(8)))
            bs2 = pygame.Surface((sc(12), sc(12)), pygame.SRCALPHA)
            pygame.draw.circle(bs2, (*bcol3, 220), (sc(6), sc(6)), sp(5))
            pygame.draw.circle(bs2, (200, 170, 40, 160), (sc(6), sc(6)), sp(5), sp(1))
            surf.blit(bs2, (bx3 - sc(6), by3 - sc(6)))

    elif unit_name == "SoulWeaver":
        pygame.draw.circle(surf, C_SOULWEAVER_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_SOULWEAVER, (cx, cy), sc(20))
        # Eye symbol
        pygame.draw.ellipse(surf, (220, 180, 255), (cx - sc(9), cy - sc(5), sc(18), sc(10)), sp(2))
        pygame.draw.circle(surf, (255, 220, 255), (cx, cy), sp(4))
        pygame.draw.circle(surf, (80, 0, 160), (cx, cy), sp(2))
        # Orbiting soul orbs
        for i in range(3):
            angle = t * 1.5 + i * (math.pi * 2 / 3)
            ox2 = cx + int(math.cos(angle) * sc(32))
            oy2 = cy + int(math.sin(angle) * sc(32))
            pygame.draw.circle(surf, (200, 140, 255), (ox2, oy2), sp(5))
            pygame.draw.circle(surf, (255, 220, 255), (ox2, oy2), sp(5), sp(1))

    elif unit_name == "Swarmer":
        pygame.draw.circle(surf, C_SWARMER_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_SWARMER, (cx, cy), sc(21))
        # Honeycomb hex pattern
        for i, (hx2, hy2) in enumerate([(0, 0), (-sc(9), -sc(8)), (sc(9), -sc(8)),
                                          (-sc(9), sc(8)), (sc(9), sc(8)), (0, -sc(14)), (0, sc(14))]):
            if math.hypot(hx2, hy2) > sc(18): continue
            pts2 = []
            for k in range(6):
                a2 = math.radians(60 * k + 30)
                pts2.append((cx + hx2 + int(math.cos(a2) * sc(5)),
                              cy + hy2 + int(math.sin(a2) * sc(5))))
            col2 = (200, 140, 0) if i % 2 == 0 else (240, 180, 20)
            pygame.draw.polygon(surf, col2, pts2)
            pygame.draw.polygon(surf, (100, 60, 0), pts2, sp(1))
        # Rotating bees
        for i in range(3):
            angle = t * 2.5 + i * (math.pi * 2 / 3)
            bx3 = cx + int(math.cos(angle) * sc(28))
            by3 = cy + int(math.sin(angle) * sc(28))
            pygame.draw.ellipse(surf, C_SWARMER, (bx3 - sp(4), by3 - sp(2), sp(8), sp(5)))

    elif unit_name == "Rubber Duck":
        # Duck: yellow circle with orange beak
        pygame.draw.circle(surf, C_DUCK_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_DUCK, (cx, cy), sc(21))
        pygame.draw.circle(surf, (255, 240, 80), (cx, cy), sc(21), sp(2))
        # Beak (triangle pointing right)
        beak = [(cx + sc(18), cy), (cx + sc(28), cy - sc(5)), (cx + sc(28), cy + sc(5))]
        pygame.draw.polygon(surf, (255, 140, 0), beak)
        # Eye
        pygame.draw.circle(surf, (20, 20, 20), (cx + sc(8), cy - sc(10)), sp(4))
        pygame.draw.circle(surf, (255, 255, 255), (cx + sc(7), cy - sc(11)), sp(2))

    elif unit_name == "Harvester":
        # Base rings
        pygame.draw.circle(surf, (18, 55, 18),  (cx, cy), sc(24))
        pygame.draw.circle(surf, (28, 85, 28),  (cx, cy), sc(21))
        pygame.draw.circle(surf, (38, 110, 38), (cx, cy), sc(17))
        # 3 rotating sickle blades
        n_blades = 3
        for i in range(n_blades):
            base_a = t * 2.0 + i * (math.pi * 2 / n_blades)
            pts = []
            for step in range(7):
                frac = step / 6.0
                a_outer = base_a + frac * 0.9
                r_outer = sc(10 + int(frac * 10))
                pts.append((cx + int(math.cos(a_outer) * r_outer),
                             cy + int(math.sin(a_outer) * r_outer)))
            for step in range(7):
                frac = (6 - step) / 6.0
                a_inner = base_a + frac * 0.9
                r_inner = sc(5 + int(frac * 4))
                pts.append((cx + int(math.cos(a_inner) * r_inner),
                             cy + int(math.sin(a_inner) * r_inner)))
            if len(pts) >= 3:
                pygame.draw.polygon(surf, (55, 175, 55), pts)
                pygame.draw.polygon(surf, (120, 230, 80), pts, 1)
        # Centre hub
        pygame.draw.circle(surf, (15, 60, 15),   (cx, cy), sc(8))
        pygame.draw.circle(surf, (80, 200, 80),  (cx, cy), sc(5))
        pygame.draw.circle(surf, (200, 255, 150),(cx, cy), sp(2))
        # 6 outer thorn spikes
        for i in range(6):
            a2 = t * 0.4 + i * (math.pi / 3)
            tip_x = cx + int(math.cos(a2) * sc(21))
            tip_y = cy + int(math.sin(a2) * sc(21))
            perp = a2 + math.pi / 2
            bx1 = cx + int(math.cos(a2) * sc(16) + math.cos(perp) * sc(3))
            by1 = cy + int(math.sin(a2) * sc(16) + math.sin(perp) * sc(3))
            bx2 = cx + int(math.cos(a2) * sc(16) - math.cos(perp) * sc(3))
            by2 = cy + int(math.sin(a2) * sc(16) - math.sin(perp) * sc(3))
            pygame.draw.polygon(surf, (170, 240, 100), [(tip_x, tip_y), (bx1, by1), (bx2, by2)])

    elif unit_name == "Korzhik":
        # ── Pulsing aura ─────────────────────────────────────────────────────
        aura_r = sc(30)
        aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        aura_a = int(abs(math.sin(t * 2.2)) * 50 + 18)
        pygame.draw.circle(aura_s, (255, 130, 190, aura_a), (aura_r, aura_r), aura_r)
        surf.blit(aura_s, (cx - aura_r, cy - aura_r))
        # ── Ears ─────────────────────────────────────────────────────────────
        l_out = [(cx - sc(20), cy - sc(2)), (cx - sc(20), cy - sc(36)), (cx - sc(7), cy - sc(16))]
        l_inn = [(cx - sc(17), cy - sc(6)), (cx - sc(17), cy - sc(30)), (cx - sc(10), cy - sc(18))]
        r_out = [(cx + sc(20), cy - sc(2)), (cx + sc(20), cy - sc(36)), (cx + sc(7), cy - sc(16))]
        r_inn = [(cx + sc(17), cy - sc(6)), (cx + sc(17), cy - sc(30)), (cx + sc(10), cy - sc(18))]
        for out, inn in [(l_out, l_inn), (r_out, r_inn)]:
            pygame.draw.polygon(surf, (232, 200, 216), out)
            pygame.draw.polygon(surf, (255, 140, 175), inn)
            pygame.draw.polygon(surf, (200, 120, 160), out, sp(1))
        # ── Body ─────────────────────────────────────────────────────────────
        pygame.draw.circle(surf, C_FELYNE_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, C_FELYNE,      (cx, cy), sc(23))
        # Highlight shimmer
        hi_a = int(70 + abs(math.sin(t * 1.5)) * 40)
        hi_s = pygame.Surface((sc(20), sc(20)), pygame.SRCALPHA)
        pygame.draw.circle(hi_s, (255, 230, 245, hi_a), (sc(10), sc(10)), sc(8))
        surf.blit(hi_s, (cx - sc(18), cy - sc(18)))
        # ── Eyes ─────────────────────────────────────────────────────────────
        pygame.draw.ellipse(surf, (255, 255, 255), (cx - sc(11), cy - sc(9), sc(9), sc(7)))
        pygame.draw.ellipse(surf, (255, 255, 255), (cx + sc(2),  cy - sc(9), sc(9), sc(7)))
        blink = abs(math.sin(t * 0.4))
        ph = max(sp(1), int(sc(5) * blink))
        pygame.draw.ellipse(surf, (30, 10, 50), (cx - sc(9), cy - sc(8), sc(5), ph))
        pygame.draw.ellipse(surf, (30, 10, 50), (cx + sc(4), cy - sc(8), sc(5), ph))
        pygame.draw.circle(surf, (255,255,255), (cx - sc(7), cy - sc(8)), sp(1))
        pygame.draw.circle(surf, (255,255,255), (cx + sc(6), cy - sc(8)), sp(1))
        # ── Nose + mouth ─────────────────────────────────────────────────────
        nose = [(cx, cy - sc(2)), (cx - sc(2), cy + sc(1)), (cx + sc(2), cy + sc(1))]
        pygame.draw.polygon(surf, (255, 120, 150), nose)
        pygame.draw.line(surf, (200, 100, 130), (cx - sp(2), cy + sp(1)), (cx - sp(6), cy + sp(4)), sp(1))
        pygame.draw.line(surf, (200, 100, 130), (cx + sp(2), cy + sp(1)), (cx + sp(6), cy + sp(4)), sp(1))
        # ── Whiskers ─────────────────────────────────────────────────────────
        wc = (220, 180, 210)
        pygame.draw.line(surf, wc, (cx - sc(4), cy),     (cx - sc(18), cy - sc(2)), sp(1))
        pygame.draw.line(surf, wc, (cx - sc(4), cy + sc(2)), (cx - sc(18), cy + sc(2)), sp(1))
        pygame.draw.line(surf, wc, (cx + sc(4), cy),     (cx + sc(18), cy - sc(2)), sp(1))
        pygame.draw.line(surf, wc, (cx + sc(4), cy + sc(2)), (cx + sc(18), cy + sc(2)), sp(1))
        # ── Collar ───────────────────────────────────────────────────────────
        collar_rect = pygame.Rect(cx - sc(22), cy + sc(12), sc(44), sc(20))
        pygame.draw.arc(surf, (220, 60, 100),  collar_rect, math.pi, 0, sc(5))
        pygame.draw.arc(surf, (255, 140, 170), collar_rect, math.pi, 0, sp(2))
        bell_col = (255, int(220 + abs(math.sin(t * 3.0)) * 20), 40)
        pygame.draw.circle(surf, (120, 80, 0), (cx, cy + sc(21)), sc(5))
        pygame.draw.circle(surf, bell_col,     (cx, cy + sc(21)), sc(4))


    elif unit_name == "Twitgunner":
        # Drop shadow
        pygame.draw.circle(surf, (20, 5, 30), (cx + sp(2), cy + sp(3)), sc(26))
        # Base rings
        pygame.draw.circle(surf, C_TWITGUN_DARK, (cx, cy), sc(26))
        pygame.draw.circle(surf, (100, 40, 140),  (cx, cy), sc(22))
        pygame.draw.circle(surf, C_TWITGUN,       (cx, cy), sc(18))
        # Pulsing aura ring
        pulse = int(abs(math.sin(t * 4)) * 40) + 20
        aura = pygame.Surface((sc(60), sc(60)), pygame.SRCALPHA)
        pygame.draw.circle(aura, (180, 80, 255, pulse), (sc(30), sc(30)), sc(28), sp(2))
        surf.blit(aura, (cx - sc(30), cy - sc(30)))
        # Rotating 3-spoke ornament
        for i in range(3):
            a = t * 1.8 + i * (math.pi * 2 / 3)
            ix = cx + int(math.cos(a) * sc(14))
            iy = cy + int(math.sin(a) * sc(14))
            pygame.draw.circle(surf, (230, 160, 255), (ix, iy), sp(3))
            pygame.draw.line(surf, (160, 60, 220), (cx, cy), (ix, iy), sp(1))
        # Gun barrel pointing right (static in icon)
        blen = sc(22)
        bx2 = cx + blen; by2 = cy
        pygame.draw.line(surf, (80, 20, 120),  (cx, cy), (bx2, by2), sp(7))
        pygame.draw.line(surf, C_TWITGUN,      (cx, cy), (bx2, by2), sp(4))
        pygame.draw.line(surf, (230, 180, 255),(cx, cy), (bx2, by2), sp(2))
        pygame.draw.circle(surf, (255, 210, 255), (bx2, by2), sp(4))
        pygame.draw.circle(surf, (180, 80, 255),  (bx2, by2), sp(2))
        # Centre hub
        pygame.draw.circle(surf, (40, 10, 60),    (cx, cy), sp(7))
        pygame.draw.circle(surf, (200, 120, 255), (cx, cy), sp(4))
        pygame.draw.circle(surf, (255, 240, 255), (cx, cy), sp(2))

    elif unit_name == "Conduit":
        # Drop shadow
        pygame.draw.circle(surf, (5, 20, 40), (cx + sp(3), cy + sp(3)), sc(27))
        # Base rings
        pygame.draw.circle(surf, C_CONDUIT_DARK, (cx, cy), sc(27))
        pygame.draw.circle(surf, (20, 80, 140),  (cx, cy), sc(22))
        pygame.draw.circle(surf, C_CONDUIT,      (cx, cy), sc(17))
        # Pulsing aura ring
        pulse = int(abs(math.sin(t * 3.5)) * 35) + 15
        aura = pygame.Surface((sc(70), sc(70)), pygame.SRCALPHA)
        pygame.draw.circle(aura, (80, 200, 255, pulse), (sc(35), sc(35)), sc(33), sp(2))
        surf.blit(aura, (cx - sc(35), cy - sc(35)))
        # 3 rotating arc trails
        arc_r = sc(20)
        for i in range(3):
            a_base = t * 1.8 + i * (math.pi * 2 / 3)
            for da in range(0, 50, 10):
                a = a_base + math.radians(da)
                ix = cx + int(math.cos(a) * arc_r)
                iy = cy + int(math.sin(a) * arc_r)
                alpha_arc = 180 - da * 3
                if alpha_arc <= 0: continue
                dot = pygame.Surface((sp(6), sp(6)), pygame.SRCALPHA)
                pygame.draw.circle(dot, (160, 230, 255, alpha_arc), (sp(3), sp(3)), sp(2))
                surf.blit(dot, (ix - sp(3), iy - sp(3)))
        # Centre hub
        pygame.draw.circle(surf, (10, 40, 80),    (cx, cy), sp(8))
        pygame.draw.circle(surf, (80, 200, 255),  (cx, cy), sp(5))
        pygame.draw.circle(surf, (220, 240, 255), (cx, cy), sp(2))

    elif unit_name == "Control Panel":
        C_CP  = (40, 180, 220)
        C_CPD = (10,  60,  90)
        pulse = abs(math.sin(t * 1.8))
        # outer glow
        glow_r = sc(34)
        glow_a = int(pulse * 40 + 15)
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*C_CP, glow_a), (glow_r, glow_r), glow_r)
        surf.blit(glow_s, (cx - glow_r, cy - glow_r))
        # body rectangle
        bw, bh = sc(48), sc(44)
        body_rect = pygame.Rect(cx - bw // 2, cy - bh // 2, bw, bh)
        pygame.draw.rect(surf, C_CPD, body_rect, border_radius=max(2, sc(8)))
        pygame.draw.rect(surf, C_CP,  body_rect, max(1, sp(2)), border_radius=max(2, sc(8)))
        # screen
        sw, sh = sc(36), sc(18)
        screen_rect = pygame.Rect(cx - sw // 2, cy - bh // 2 + sc(6), sw, sh)
        scr_col = (int(20 + pulse * 40), int(160 + pulse * 60), int(200 + pulse * 30))
        pygame.draw.rect(surf, (10, 20, 35), screen_rect, border_radius=max(1, sc(3)))
        pygame.draw.rect(surf, scr_col, screen_rect, sp(1), border_radius=max(1, sc(3)))
        for row in range(3):
            line_s = pygame.Surface((max(1, sw - sp(2)), max(1, sp(1))), pygame.SRCALPHA)
            line_s.fill((*scr_col, int(80 + pulse * 60)))
            surf.blit(line_s, (screen_rect.x + sp(1), screen_rect.y + sc(4) + row * sc(5)))
        # animated dot on screen
        dot_x = cx + int(math.sin(t * 3.0) * sc(12))
        dot_s = pygame.Surface((sc(8), sc(8)), pygame.SRCALPHA)
        pygame.draw.circle(dot_s, (*C_CP, 220), (sc(4), sc(4)), max(1, sc(3)))
        surf.blit(dot_s, (dot_x - sc(4), cy - bh // 2 + sc(6) + sc(7) - sc(4)))
        # two buttons below screen
        btn_y = cy + bh // 2 - sc(14)
        for bx_off in (-sc(8), sc(8)):
            pygame.draw.circle(surf, (60, 180, 140), (cx + bx_off, btn_y), max(2, sc(5)))
            pygame.draw.circle(surf, (100, 220, 180), (cx + bx_off, btn_y), max(2, sc(5)), sp(1))
        # antenna
        ant_base_y = cy - bh // 2
        ant_tip_y  = ant_base_y - sc(16)
        pygame.draw.line(surf, C_CP, (cx, ant_base_y), (cx, ant_tip_y), max(1, sp(2)))
        blink_a = int(abs(math.sin(t * 4.0)) * 200 + 55)
        tip_s = pygame.Surface((sc(10), sc(10)), pygame.SRCALPHA)
        pygame.draw.circle(tip_s, (*C_CP, blink_a), (sc(5), sc(5)), max(1, sc(3)))
        surf.blit(tip_s, (cx - sc(5), ant_tip_y - sc(5)))

    elif unit_name == "Castbound":
        # ── Используем webm-анимацию (первый/текущий кадр) ───────────────────
        from units import _CB_WEBM_FRAMES, _CB_WEBM_LOADED, _CB_WEBM_FPS, _cb_load_webm_frames
        if not _CB_WEBM_LOADED:
            _cb_load_webm_frames()
        if _CB_WEBM_FRAMES:
            fps = max(1.0, _CB_WEBM_FPS)
            frame_idx = int(t * fps) % len(_CB_WEBM_FRAMES)
            frame = _CB_WEBM_FRAMES[frame_idx]
            target_size = max(1, size * 2)
            fw, fh = frame.get_size()
            if fw == 0 or fh == 0:
                scaled = frame
                scale_w, scale_h = fw, fh
            elif fw >= fh:
                scale_w = target_size
                scale_h = max(1, int(fh * target_size / fw))
            else:
                scale_h = target_size
                scale_w = max(1, int(fw * target_size / fh))
            scaled = pygame.transform.smoothscale(frame, (scale_w, scale_h))
            surf.blit(scaled, (cx - scale_w // 2, cy - scale_h // 2))
        else:
            P2 = max(2, int(3 * s))
            pulse_cb = abs(math.sin(t * 2.5))

            # Аура
            aura_r = sc(30)
            aura_s = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
            aura_a = int(pulse_cb * 50 + 20)
            pygame.draw.circle(aura_s, (40, 120, 255, aura_a), (aura_r, aura_r), aura_r)
            surf.blit(aura_s, (cx - aura_r, cy - aura_r))

            # Цвета Stardust Guardian
            _SB  = (30,  80, 200)
            _SL  = (60, 140, 255)
            _SW  = (140, 200, 255)
            _ST  = (0, 230, 255)
            _SBK = (10,  20,  60)
            _SG  = (80, 180, 255)
            _SA  = (180, 220, 255)
            _SGD = (255, 220,  50)
            _FL  = (
                int(_SL[0] + pulse_cb * 30),
                int(_SL[1] + pulse_cb * 20),
                min(255, int(_SL[2] + pulse_cb * 30)),
            )

            def _cbpx2(dx, dy, col):
                pygame.draw.rect(surf, col,
                                 (cx + dx * P2 - P2 // 2,
                                  cy + dy * P2 - P2 // 2, P2, P2))

            # Голова
            for dx, dy, col in [
                (-2,-8,_SBK),(-1,-8,_SB),(0,-8,_SB),(1,-8,_SB),(2,-8,_SBK),
                (-2,-7,_SB),(-1,-7,_SL),(0,-7,_SL),(1,-7,_SL),(2,-7,_SB),
                (-2,-6,_SB),(-1,-6,_ST),(0,-6,_SL),(1,-6,_ST),(2,-6,_SB),
                (-2,-5,_SB),(-1,-5,_SL),(0,-5,_SW),(1,-5,_SL),(2,-5,_SB),
                (-2,-4,_SBK),(-1,-4,_SG),(0,-4,_SG),(1,-4,_SG),(2,-4,_SBK),
            ]: _cbpx2(dx, dy, col)

            # Плечи
            for dx, dy, col in [
                (-4,-3,_SBK),(-3,-3,_SB),(-2,-3,_SL),(-1,-3,_SL),(0,-3,_SL),(1,-3,_SL),(2,-3,_SL),(3,-3,_SB),(4,-3,_SBK),
                (-4,-2,_SB),(-3,-2,_SG),(-2,-2,_FL),(-1,-2,_FL),(0,-2,_FL),(1,-2,_FL),(2,-2,_FL),(3,-2,_SG),(4,-2,_SB),
            ]: _cbpx2(dx, dy, col)

            # Туловище
            for dx, dy, col in [
                (-3,-1,_SBK),(-2,-1,_SB),(-1,-1,_SL),(0,-1,_SA),(1,-1,_SL),(2,-1,_SB),(3,-1,_SBK),
                (-3, 0,_SB),(-2, 0,_SL),(-1, 0,_SGD),(0, 0,_SA),(1, 0,_SGD),(2, 0,_SL),(3, 0,_SB),
                (-3, 1,_SBK),(-2, 1,_SB),(-1, 1,_SL),(0, 1,_SL),(1, 1,_SL),(2, 1,_SB),(3, 1,_SBK),
            ]: _cbpx2(dx, dy, col)

            # Пояс
            for dx, dy, col in [
                (-2, 2,_SBK),(-1, 2,_SGD),(0, 2,_SGD),(1, 2,_SGD),(2, 2,_SBK),
            ]: _cbpx2(dx, dy, col)

            # Ноги
            for dx, dy, col in [
                (-2, 3,_SB),(-1, 3,_SL),(0, 3,_SBK),(1, 3,_SL),(2, 3,_SB),
                (-2, 4,_SB),(-1, 4,_SG),(0, 4,_SBK),(1, 4,_SG),(2, 4,_SB),
                (-2, 5,_SBK),(-1, 5,_SL),(0, 5,_SBK),(1, 5,_SL),(2, 5,_SBK),
            ]: _cbpx2(dx, dy, col)

            # Мигающие глаза
            eye_pulse = int(abs(math.sin(t * 3.0)) * 200 + 55)
            eye_pulse = max(0, min(255, int(eye_pulse)))
            pygame.draw.rect(surf, (eye_pulse, 240, 255),
                            (cx - 2 * P2 - P2 // 2, cy - 6 * P2 - P2 // 2, P2, P2))
            pygame.draw.rect(surf, (eye_pulse, 240, 255),
                             (cx + 1 * P2 - P2 // 2, cy - 6 * P2 - P2 // 2, P2, P2))

            # Звёздный пылевой хвост
            random.seed(int(t * 12))
            for _ in range(3):
                tx2 = cx + random.randint(-10, 10)
                ty2 = cy + random.randint(22, 40)
                tr2 = random.randint(1, 3)
                ta  = random.randint(60, 140)
                ts2 = pygame.Surface((tr2 * 2, tr2 * 2), pygame.SRCALPHA)
                pygame.draw.circle(ts2, (80, 160, 255, ta), (tr2, tr2), tr2)
                surf.blit(ts2, (tx2 - tr2, ty2 - tr2))
            random.seed()

    else:
        # Fallback: colored circle with unit's color
        _col_map = {
            "Assassin": C_ASSASSIN, "Militant": C_MILITANT, "Swarmer": C_SWARMER,
            "Lifestealer": C_LIFESTEALER, "Archer": C_ARCHER, "Red Ball": C_REDBALL,
            "Farm": C_FARM, "Freezer": C_FREEZER, "Frost Blaster": C_FROSTBLASTER,
            "Sledger": C_SLEDGER, "Gladiator": C_GLADIATOR, "Toxic Gunner": C_TOXICGUN,
            "Slasher": C_SLASHER, "Cowboy": C_GCOWBOY, "Hallow Punk": C_HALLOWPUNK,
            "Spotlight Tech": C_SPOTLIGHT, "Snowballer": C_SNOWBALLER,
            "Commando": C_COMMANDO,
            "hacker_laser_effects_test": C_HACKER, "Caster": C_HACKER,
            "Warlock": C_WARLOCK, "Jester": C_JESTER, "Harvester": C_HARVESTER,
        }
        unit_col = _col_map.get(unit_name, (120, 120, 180))
        pygame.draw.circle(surf, (30, 20, 50), (cx, cy), sc(27))
        pygame.draw.circle(surf, unit_col, (cx, cy), sc(21))
        pygame.draw.circle(surf, tuple(min(255, c + 60) for c in unit_col), (cx, cy), sc(21), sp(2))


def _render_gradient_text(text, font, colors):
    """Render text with a horizontal gradient. colors = list of (r,g,b) left→right."""
    s = font.render(text, True, (255, 255, 255))
    w, h = s.get_size()
    if w == 0:
        return s
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = len(colors) - 1
    seg_w = max(1, w // steps)
    for seg in range(steps):
        c0, c1 = colors[seg], colors[seg + 1]
        x0 = seg * seg_w
        x1 = x0 + seg_w if seg < steps - 1 else w
        for x in range(x0, x1):
            frac = (x - x0) / max(1, x1 - x0)
            r2 = int(c0[0] + (c1[0] - c0[0]) * frac)
            g2 = int(c0[1] + (c1[1] - c0[1]) * frac)
            b2 = int(c0[2] + (c1[2] - c0[2]) * frac)
            pygame.draw.line(grad, (r2, g2, b2, 255), (x, 0), (x, h))
    grad.blit(s, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return grad

_APEX_GRAD_COLORS = [(220, 30, 10), (255, 130, 20), (255, 220, 40)]

def _blit_apex_label(surf, text, font, pos, center=False):
    """Blit apex rarity label with red→orange→yellow gradient."""
    s = _render_gradient_text(text, font, _APEX_GRAD_COLORS)
    r = s.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    surf.blit(s, r)


# ── Castbound card background — CPU fbm shader (cached) ─────────────────────
_CB_BG_CACHE: dict = {}   # key: (w, h, t_bucket) -> pygame.Surface

def _cb_bg_shader(w: int, h: int, t: float) -> "pygame.Surface":
    """CPU reimplementation of the Vanta-style fbm fog shader for Castbound card bg."""
    import numpy as _np
    t_bucket = int(t * 15) / 15.0          # quantise to 1/15s — smooth but cheap

    key = (w, h, t_bucket)
    if key in _CB_BG_CACHE:
        return _CB_BG_CACHE[key]

    # Clean old entries (keep at most 8)
    if len(_CB_BG_CACHE) > 8:
        oldest = next(iter(_CB_BG_CACHE))
        del _CB_BG_CACHE[oldest]

    # Build UV grids  (shape: H x W)
    xs = _np.linspace(0.0, 1.0, w, dtype=_np.float32) * (w / h)
    ys = _np.linspace(0.0, 1.0, h, dtype=_np.float32)
    uvx, uvy = _np.meshgrid(xs, ys)

    def _hash2(px, py):
        px = px * 123.34; py = py * 456.21
        px -= _np.floor(px); py -= _np.floor(py)
        tmp = px + py * 45.32
        px = px + tmp; py = py + tmp
        r = px * py
        return r - _np.floor(r)

    def _noise(px, py):
        i = _np.floor(px); j = _np.floor(py)
        fx = px - i;       fy = py - j
        a = _hash2(i,   j  ); b = _hash2(i+1, j  )
        c = _hash2(i,   j+1); d = _hash2(i+1, j+1)
        ux = fx*fx*(3-2*fx); uy = fy*fy*(3-2*fy)
        return a*(1-ux)*(1-uy) + b*ux*(1-uy) + c*(1-ux)*uy + d*ux*uy

    def _fbm(px, py, tt):
        v = _np.zeros_like(px)
        a = 0.5
        for _ in range(5):
            v += a * _noise(px, py)
            npx = 1.6*px + 1.2*py
            npy = -1.2*px + 1.6*py
            px = npx * 2.0 + tt * 0.1
            py = npy * 2.0 + tt * 0.1
            a *= 0.5
        return v

    n  = _fbm(uvx * 1.5 - t_bucket * 0.1, uvy * 1.5 - t_bucket * 0.1, t_bucket)
    n2 = _fbm(uvx * 2.0 + t_bucket * 0.05, uvy * 2.0 + t_bucket * 0.05, t_bucket)
    # Third fbm for dark void patches — slower, larger scale, offset direction
    n3v = _fbm(uvx * 0.8 + t_bucket * 0.07 + 5.3, uvy * 0.8 - t_bucket * 0.04 + 3.1, t_bucket)

    # smoothstep mask (bright highlights)
    mask = _np.clip((n * n2 - 0.2) / 0.6, 0.0, 1.0)
    mask = mask * mask * (3 - 2 * mask)

    # Dark void mask — deep, infrequent blobs where n3v is low
    void_raw = _np.clip((0.38 - n3v) / 0.22, 0.0, 1.0)
    void_mask = void_raw * void_raw * (3 - 2 * void_raw)   # smoothstep

    # Colors from Vanta config
    C_BASE      = _np.array([0.04, 0.04, 0.35], dtype=_np.float32)
    C_LOWLIGHT  = _np.array([0.03, 0.00, 0.56], dtype=_np.float32)
    C_MIDTONE   = _np.array([0.93, 0.00, 1.00], dtype=_np.float32)
    C_HIGHLIGHT = _np.array([0.035, 0.12, 0.72], dtype=_np.float32)
    C_VOID      = _np.array([0.01, 0.00, 0.04], dtype=_np.float32)  # near-black void

    n3  = n[..., _np.newaxis]
    n23 = n2[..., _np.newaxis]
    m3  = mask[..., _np.newaxis]
    vm3 = void_mask[..., _np.newaxis]

    color = C_BASE + (C_LOWLIGHT - C_BASE) * n3
    color = color + (C_MIDTONE - color) * (n23 * 0.6)
    color = color + (C_HIGHLIGHT - color) * m3
    # Overlay dark void patches on top
    color = color + (C_VOID - color) * vm3

    # Permanent subtle darkening — clouds always have some dark areas, never fully bright
    # Use n itself to create persistent dark zones that don't flash
    persistent_dark = _np.clip((0.55 - n) / 0.35, 0.0, 1.0) * 0.35
    color = color * (1.0 - persistent_dark[..., _np.newaxis])

    color = _np.clip(color, 0.0, 1.0)

    rgb = (color * 255).astype(_np.uint8)
    # pygame wants (W, H, 3) transposed
    surf = pygame.Surface((w, h))
    pygame.surfarray.blit_array(surf, rgb.transpose(1, 0, 2))

    _CB_BG_CACHE[key] = surf
    return surf



def draw_unit_card(surf, unit_name, rarity_key, cx, cy, w=160, h=220, t=0.0, selected=False):
    rd = RARITY_DATA.get(rarity_key, RARITY_DATA["starter"])
    bx, by = cx - w//2, cy - h//2

    s_card = pygame.Surface((w, h), pygame.SRCALPHA)

    if unit_name == "Castbound" and rarity_key == "singularity":
        # — Castbound shader background —
        _cb_bg = _cb_bg_shader(w, h, t)
        # Clip to rounded rect
        _bg_mask = pygame.Surface((w, h), pygame.SRCALPHA)
        _bg_mask.blit(_cb_bg, (0, 0))
        pygame.draw.rect(_bg_mask, (0, 0, 0, 0), (0, 0, w, h), border_radius=18)  # clear corners
        mask_rr = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask_rr, (255, 255, 255, 255), (0, 0, w, h), border_radius=18)
        _cb_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        _cb_surf.blit(_cb_bg, (0, 0))
        _cb_surf.blit(mask_rr, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        s_card.blit(_cb_surf, (0, 0))
        # — Neon border —
        border_pulse = 0.7 + 0.3 * math.sin(t * 4.0)
        for thickness, alpha in [(7, 40), (4, 90), (2, 220)]:
            ba = int(alpha * border_pulse)
            pygame.draw.rect(s_card, (180, 0, 255, ba), (0, 0, w, h), thickness, border_radius=18)
        if selected:
            pygame.draw.rect(s_card, (220, 80, 255, 70), (0, 0, w, h), border_radius=18)
            pygame.draw.rect(s_card, (255, 220, 50, 255), (0, 0, w, h), 2, border_radius=18)
    elif rarity_key == "apex":
        # Vertical gradient: red → orange → yellow
        grad_colors = [(180, 20, 10), (220, 90, 10), (255, 200, 30)]
        steps = len(grad_colors) - 1
        seg_h = h // steps
        for seg in range(steps):
            c0 = grad_colors[seg]
            c1 = grad_colors[seg + 1]
            for row in range(seg_h + 1):
                frac = row / seg_h
                r2 = int(c0[0] + (c1[0] - c0[0]) * frac)
                g2 = int(c0[1] + (c1[1] - c0[1]) * frac)
                b2 = int(c0[2] + (c1[2] - c0[2]) * frac)
                y_row = seg * seg_h + row
                if y_row < h:
                    pygame.draw.line(s_card, (r2, g2, b2, 210), (0, y_row), (w, y_row))
        # Clip to rounded rect
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=18)
        s_card.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Animated shimmer sweep
        shimmer_x = int((math.sin(t * 1.8) * 0.5 + 0.5) * (w + 60)) - 30
        sh = pygame.Surface((30, h), pygame.SRCALPHA)
        for sx in range(30):
            alpha = int(max(0, 80 - abs(sx - 15) * 6))
            pygame.draw.line(sh, (255, 240, 180, alpha), (sx, 0), (sx, h))
        s_card.blit(sh, (shimmer_x, 0))
        border_col = (255, 120, 20) if not selected else (255, 220, 50)
        if selected:
            pygame.draw.rect(s_card, (255, 220, 50, 50), (0, 0, w, h), border_radius=18)
        pygame.draw.rect(s_card, (*border_col, 255), (0, 0, w, h), 3, border_radius=18)
    elif rarity_key == "singularity":
        import random as _rnd
        _seed = int(t * 8)
        _rng  = _rnd.Random(_seed)
        # — No background fill — transparent base —
        # — RGB chromatic aberration fringe on edges —
        fring = pygame.Surface((w, h), pygame.SRCALPHA)
        ab_shift = int(2 + 2 * math.sin(t * 6.0))
        pygame.draw.rect(fring, (255, 0, 255, 40), (ab_shift, 0, w, h), border_radius=18)
        pygame.draw.rect(fring, (0, 220, 255, 30), (-ab_shift, 0, w, h), border_radius=18)
        s_card.blit(fring, (0, 0))
        # — Clip to rounded rect —
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=18)
        s_card.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # — Animated neon border (triple-layer glow) —
        border_pulse = 0.7 + 0.3 * math.sin(t * 4.0)
        for thickness, alpha in [(7, 40), (4, 90), (2, 220)]:
            ba = int(alpha * border_pulse)
            pygame.draw.rect(s_card, (180, 0, 255, ba), (0, 0, w, h), thickness, border_radius=18)
        if selected:
            pygame.draw.rect(s_card, (220, 80, 255, 70), (0, 0, w, h), border_radius=18)
            pygame.draw.rect(s_card, (255, 220, 50, 255), (0, 0, w, h), 2, border_radius=18)
    else:
        base_col = rd["color"]
        pygame.draw.rect(s_card, (*base_col, 220), (0, 0, w, h), border_radius=18)
        border_col = rd["border"]
        if selected:
            border_col = (255, 220, 50)
            pygame.draw.rect(s_card, (255, 220, 50, 60), (0, 0, w, h), border_radius=18)
        pygame.draw.rect(s_card, (*border_col, 255), (0, 0, w, h), 3, border_radius=18)

    surf.blit(s_card, (bx, by))

    # Unit icon — detailed in-game appearance
    icon_cx, icon_cy = cx, cy - 30
    icon_size = 55 if unit_name == "Castbound" else 32

    # Draw on a clipped sub-surface so icons don't bleed outside the card
    icon_area_w = w - 8
    icon_area_h = (h // 2 + 30) if unit_name == "Castbound" else (h // 2 + 10)
    icon_surf = pygame.Surface((icon_area_w, icon_area_h), pygame.SRCALPHA)
    iso_cx = icon_area_w // 2
    iso_cy = (icon_area_h // 2 - 6) if unit_name == "Castbound" else (icon_area_h // 2 + 4)

    _draw_tower_icon(icon_surf, unit_name, iso_cx, iso_cy, t, size=icon_size)
    surf.blit(icon_surf, (bx + 4, by + 8))

    # Unit name only — rarity label shown in slots, not on card
    name_f = pygame.font.SysFont("consolas", 17, bold=True)
    if rarity_key == "singularity":
        neon_col = (200, 0, 255)
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)]:
            ns_o = name_f.render(unit_name, True, neon_col)
            surf.blit(ns_o, ns_o.get_rect(center=(cx + ox, cy + 56 + oy)))
        ns = name_f.render(unit_name, True, (0, 0, 0))
    else:
        ns = name_f.render(unit_name, True, C_WHITE)
    surf.blit(ns, ns.get_rect(center=(cx, cy + 56)))




# ── Difficulty Menu ─────────────────────────────────────────────────────────────
class MapSelectMenu:
    """Shown after difficulty selection — lets player pick a map."""

    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        cw, ch = 210, 240
        cx = SCREEN_W // 2
        gap_x, gap_y = 40, 28
        # 2 rows × 2 cols (all 4 maps)
        total_w = 2 * cw + gap_x
        left_x  = cx - total_w // 2
        row1_y  = 150
        row2_y  = row1_y + ch + gap_y
        self.card_straight  = pygame.Rect(left_x,            row1_y, cw, ch)
        self.card_zigzag    = pygame.Rect(left_x + cw + gap_x, row1_y, cw, ch)
        self.card_uturn     = pygame.Rect(left_x,            row2_y, cw, ch)
        self.card_labyrinth = pygame.Rect(left_x + cw + gap_x, row2_y, cw, ch)
        btn_w, btn_h = 220, 48
        self.btn_back = pygame.Rect(cx - btn_w//2, row2_y + ch + 20, btn_w, btn_h)
        self.action = None
        # ── Same particles as main menu ───────────────────────────────────────
        MainMenu._ensure_heavy_surfaces()
        self._wisps = [_VoidWisp() for _ in range(30)]
        self._dots  = [_VoidDot()  for _ in range(90)]
        self._motes = [_VoidMote() for _ in range(60)]

    def run(self):
        print("Game.run() started")
        clock = pygame.time.Clock()
        self.action = None
        while self.action is None:
            
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos = ev.pos
                    if self.card_straight.collidepoint(pos):  self.action = "straight"
                    if self.card_zigzag.collidepoint(pos):    self.action = "zigzag"
                    if self.card_uturn.collidepoint(pos):     self.action = "uturn"
                    if self.card_labyrinth.collidepoint(pos): self.action = "labyrinth"
                    if self.btn_back.collidepoint(pos):       self.action = "back"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw_map_preview(self, surf, rect, map_type, hover, selected):
        bg = (40, 60, 90) if hover else (25, 32, 50)
        brd = (120, 200, 255) if selected else ((80, 160, 220) if hover else (55, 75, 110))
        pygame.draw.rect(surf, bg, rect, border_radius=12)
        pygame.draw.rect(surf, brd, rect, 2 if not selected else 3, border_radius=12)

        # Mini path preview
        pr = pygame.Rect(rect.x + 14, rect.y + 14, rect.w - 28, rect.h - 64)
        pygame.draw.rect(surf, (18, 22, 30), pr, border_radius=6)
        pygame.draw.rect(surf, (50, 60, 80), pr, 1, border_radius=6)

        ph = 5  # path half-width in preview
        ph_h = pr.h

        def _draw_pts(pts, mnx, mxx, mny, mxy, start_col=(60,20,20), end_col=(20,60,20)):
            def sc(px2, py2):
                nx = pr.x + int((px2 - mnx) / (mxx - mnx) * pr.w)
                ny = pr.y + int((py2 - mny) / (mxy - mny) * ph_h)
                return nx, ny
            for i in range(len(pts)-1):
                ax,ay = pts[i]; bx2,by2 = pts[i+1]
                pax,pay = sc(ax,ay); pbx,pby = sc(bx2,by2)
                if ax==bx2:
                    rx = min(pax,pbx)-ph; ry = min(pay,pby)
                    pygame.draw.rect(surf, C_PATH, (rx, ry, ph*2, abs(pby-pay)+1))
                else:
                    rx = min(pax,pbx); ry = min(pay,pby)-ph
                    pygame.draw.rect(surf, C_PATH, (rx, ry, abs(pbx-pax)+1, ph*2))
            # corner joints
            for i in range(1, len(pts)-1):
                cx2,cy2 = sc(*pts[i])
                pygame.draw.rect(surf, C_PATH, (cx2-ph, cy2-ph, ph*2, ph*2))
            s = sc(*pts[0]);  pygame.draw.rect(surf, start_col, (s[0],  s[1]-ph,  7, ph*2))
            e = sc(*pts[-1]); pygame.draw.rect(surf, end_col,   (e[0]-7,e[1]-ph,  7, ph*2))

        if map_type == "straight":
            py = pr.centery
            pygame.draw.rect(surf, C_PATH, (pr.x, py-ph, pr.w, ph*2))
            pygame.draw.rect(surf, (60,20,20), (pr.x, py-ph, 7, ph*2))
            pygame.draw.rect(surf, (20,60,20), (pr.right-7, py-ph, 7, ph*2))

        elif map_type == "zigzag":
            pts = [(-45,290),(400,290),(400,846),(766,846),(766,106),(1167,106),(1167,846),(1920,846)]
            _draw_pts(pts, -45, 1920, 80, 880)

        elif map_type == "uturn":
            pts = [(-45,180),(1760,180),(1760,460),(160,460),(160,740),(1920,740)]
            _draw_pts(pts, -45, 1920, 100, 820)

        elif map_type == "labyrinth":
            pts = [(-45,150),(640,150),(640,340),(160,340),(160,530),(1760,530),(1760,720),(1920,720)]
            _draw_pts(pts, -45, 1920, 80, 800)

        # Label
        labels = {
            "straight":  ("THE BRIDGE",  "Straight road"),
            "zigzag":    ("S-TURN",       "Two-lane zigzag"),
            "uturn":     ("U-TURN",       "Triple-lane sweep"),
            "labyrinth": ("LABYRINTH",    "Tight corridors"),
        }
        title, desc = labels.get(map_type, (map_type.upper(), ""))
        lf = pygame.font.SysFont("consolas", 16, bold=True)
        ls = lf.render(title, True, C_WHITE if hover or selected else (160, 170, 200))
        surf.blit(ls, ls.get_rect(center=(rect.centerx, rect.bottom - 34)))
        df = pygame.font.SysFont("segoeui", 13)
        ds = df.render(desc, True, (120, 140, 170))
        surf.blit(ds, ds.get_rect(center=(rect.centerx, rect.bottom - 16)))

    def _draw(self):
        surf = self.screen
        t = self.t
        mx, my = pygame.mouse.get_pos()

        # ── Same background as main menu ──────────────────────────────────────
        _draw_menu_bg(surf, overlay_alpha=80)

        # ── Void particles ────────────────────────────────────────────────────
        dt = 1 / 60.0
        for w in self._wisps:
            w.update(dt); w.draw(surf)
        for p in self._dots:
            p.update(); p.draw(surf)
        for e in self._motes:
            e.update(dt); e.draw(surf)

        # ── Vignette ─────────────────────────────────────────────────────────
        if MainMenu._vig_surf_cached is not None:
            surf.blit(MainMenu._vig_surf_cached, (0, 0))

        # ── Title ─────────────────────────────────────────────────────────────
        tf = pygame.font.SysFont("consolas", 36, bold=True)
        pulse = int(abs(math.sin(t * 1.8)) * 30)
        title_col = (120 + pulse, 180 + pulse // 2, 255)
        ts = tf.render("SELECT MAP", True, title_col)
        glow_s = pygame.Surface((ts.get_width() + 40, ts.get_height() + 20), pygame.SRCALPHA)
        glow_col = (60, 120, 255, int(abs(math.sin(t * 1.8)) * 40 + 20))
        pygame.draw.rect(glow_s, glow_col, glow_s.get_rect(), border_radius=10)
        surf.blit(glow_s, glow_s.get_rect(center=(SCREEN_W // 2, 100)))
        surf.blit(ts, ts.get_rect(center=(SCREEN_W // 2, 100)))

        # ── Map cards (2×2 grid) ───────────────────────────────────────────────
        cur = game_core.CURRENT_MAP
        for card, mtype in [
            (self.card_straight,  "straight"),
            (self.card_zigzag,    "zigzag"),
            (self.card_uturn,     "uturn"),
            (self.card_labyrinth, "labyrinth"),
        ]:
            self._draw_map_preview(surf, card, mtype, card.collidepoint(mx, my), cur == mtype)

        # ── Back button ───────────────────────────────────────────────────────
        hov_back = self.btn_back.collidepoint(mx, my)
        bg = (60, 80, 140) if hov_back else (35, 42, 65)
        brd = (120, 160, 255) if hov_back else (70, 90, 140)
        pygame.draw.rect(surf, bg, self.btn_back, border_radius=10)
        pygame.draw.rect(surf, brd, self.btn_back, 2, border_radius=10)
        txt(surf, "← BACK", self.btn_back.center, C_WHITE, font_xl, center=True)


class FrostyWarningScreen:
    """Full-screen warning shown before entering Frosty mode."""
    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        self.action = None  # "continue" or "back"
        cx = SCREEN_W // 2
        self.btn_continue = pygame.Rect(cx - 200, 620, 180, 52)
        self.btn_back     = pygame.Rect(cx + 20,  620, 180, 52)

    def run(self):
        clock = pygame.time.Clock()
        while self.action is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.action = "back"
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_continue.collidepoint(ev.pos): self.action = "continue"
                    if self.btn_back.collidepoint(ev.pos):     self.action = "back"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw(self):
        surf = self.screen
        # Dark icy background
        surf.fill((8, 12, 22))

        # Animated snowflakes
        import random as _rnd
        _rnd.seed(42)
        for i in range(60):
            sx = _rnd.randint(0, SCREEN_W)
            sy = _rnd.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 0.8 + i * 0.3)) * 140 + 60)
            pygame.draw.circle(surf, (br, br, min(255, br + 60)), (sx, sy), 1)
        _rnd.seed()

        # Pulsing red warning glow
        glow_a = int(abs(math.sin(self.t * 2.5)) * 60 + 40)
        glow_s = pygame.Surface((700, 200), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_s, (180, 20, 20, glow_a), (0, 0, 700, 200))
        surf.blit(glow_s, (SCREEN_W // 2 - 350, 180))

        # ⚠ icon
        warn_f = pygame.font.SysFont("segoeui", 80, bold=True)
        ws = warn_f.render("⚠", True, (255, 180, 0))
        surf.blit(ws, ws.get_rect(center=(SCREEN_W // 2, 230)))

        # Title
        title_f = pygame.font.SysFont("consolas", 46, bold=True)
        pulse_r = min(255, int(200 + abs(math.sin(self.t * 3)) * 55))
        ts = title_f.render("WARNING", True, (pulse_r, 40, 40))
        surf.blit(ts, ts.get_rect(center=(SCREEN_W // 2, 320)))

        # Warning lines
        lines = [
            ("Continue?", (160, 200, 255)),
        ]
        lf = pygame.font.SysFont("segoeui", 28)
        ly = 390
        for text, col in lines:
            if not text:
                ly += 18; continue
            ls = lf.render(text, True, col)
            surf.blit(ls, ls.get_rect(center=(SCREEN_W // 2, ly)))
            ly += 38

        # Buttons
        mx, my = pygame.mouse.get_pos()
        for btn, label, accent in [
            (self.btn_continue, "Continue", (40, 160, 255)),
            (self.btn_back,     "Back",      (180, 50,  50)),
        ]:
            hov = btn.collidepoint(mx, my)
            bg  = tuple(min(255, c + 30) for c in accent) if hov else tuple(c // 2 for c in accent)
            pygame.draw.rect(surf, bg,    btn, border_radius=10)
            pygame.draw.rect(surf, accent, btn, 2, border_radius=10)
            bf = pygame.font.SysFont("segoeui", 24, bold=True)
            bs = bf.render(label, True, C_WHITE)
            surf.blit(bs, bs.get_rect(center=btn.center))


class DifficultyMenu:
    # Mode definitions: (action, label, ico_name, accent_col, desc, stats_lines, reward)
    _MODES = [
        ("play_easy",    "EASY",    "easy_ico",
         (70, 200, 90),
         "Classic tower defense experience.",
         ["HP: 100", "Starting cash: $600"],
         ("250", (100, 220, 100))),
        ("play_fallen",  "FALLEN",  "fallen_ico",
         (180, 80, 255),
         "Fallen enemies invade. High threat.",
         ["HP: 150", "Starting cash: $650"],
         ("750", (200, 130, 255))),
        ("play_frosty",  "FROSTY",  "frosty_ico",
         (80, 200, 255),
         "Icy battlefield. Multi-lane chaos.",
         ["HP: 200", "Starting cash: $700"],
         ("1500", (100, 210, 255))),
        ("play_draft",   "DRAFT",   "draft_ico",
         (255, 60, 60),
         "Draft curses every few waves.",
         ["HP: 150", "Starting cash: $650"],
         ("1000", (255, 100, 100))),

        ("play_sandbox", "SANDBOX", "sandbox_ico",
         (220, 180, 80),
         "No rules. Test anything.",    
         ["HP: ∞", "Starting cash: ∞"],
         ("—", (180, 160, 100))),
    ]

    def __init__(self, screen, save_data=None):
        self.screen   = screen
        self.t        = 0.0
        self.action   = None
        self.save_data = save_data or {}
        self._hover_anim = [0.0] * len(self._MODES)

        # Layout: cards side by side, centred
        card_w, card_h = 220, 340
        gap    = 18
        n      = len(self._MODES)
        total_w = n * card_w + (n - 1) * gap
        x0     = SCREEN_W // 2 - total_w // 2
        cy_card = SCREEN_H // 2 - card_h // 2 + 20
        self._cards = [
            pygame.Rect(x0 + i * (card_w + gap), cy_card, card_w, card_h)
            for i in range(n)
        ]
        btn_w, btn_h = 240, 50
        self.btn_back = pygame.Rect(
            SCREEN_W // 2 - btn_w // 2,
            cy_card + card_h + 28,
            btn_w, btn_h
        )
        hc_w, hc_h = 180, 52
        self.btn_hardcore = pygame.Rect(SCREEN_W - hc_w - 18, SCREEN_H - hc_h - 18, hc_w, hc_h)

    def run(self):
        clock = pygame.time.Clock()
        self.action = None
        while self.action is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            mx, my = pygame.mouse.get_pos()
            for i, rect in enumerate(self._cards):
                target = 1.0 if rect.collidepoint(mx, my) else 0.0
                spd    = 0.15 if target else 0.25
                self._hover_anim[i] += (target - self._hover_anim[i]) * spd
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.action = "back"
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos = ev.pos
                    for i, (act, *_) in enumerate(self._MODES):
                        if self._cards[i].collidepoint(pos):
                            self.action = act
                    if self.btn_back.collidepoint(pos):
                        self.action = "back"
                    if self.btn_hardcore.collidepoint(pos):
                        self.action = "play_hardcore"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw_card(self, surf, rect, mode_def, hover_f):
        act, label, ico_name, accent, desc, stats, (reward, reward_col) = mode_def
        t = self.t

        # Lift card on hover
        lift = int(hover_f * 10)
        r = pygame.Rect(rect.x, rect.y - lift, rect.w, rect.h)

        # Shadow
        sh = pygame.Surface((r.w + 16, r.h + 16), pygame.SRCALPHA)
        sh_a = int(hover_f * 80 + 40)
        pygame.draw.rect(sh, (*accent, sh_a), (0, 0, r.w + 16, r.h + 16), border_radius=20)
        surf.blit(sh, (r.x - 8, r.y - 8 + lift // 2))

        # Card body — dark glass background
        card_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        base_alpha = int(hover_f * 30 + 180)
        pygame.draw.rect(card_surf, (12, 14, 22, base_alpha), (0, 0, r.w, r.h), border_radius=16)

        # Top image area (fill with icon image)
        img_h = int(r.h * 0.52)
        raw = load_icon(ico_name, max(r.w, img_h))
        if raw is None:
            # try loading directly at full size
            path = os.path.join(_ICON_DIR, f"{ico_name}.png")
            try:
                raw = pygame.image.load(path).convert_alpha()
            except Exception:
                raw = None
        if raw is not None:
            try:
                iw, ih = raw.get_size()
                scale = max(r.w / iw, img_h / ih)
                if ico_name == "draft_ico": scale *= 1.2
                nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
                scaled = pygame.transform.smoothscale(raw, (nw, nh))
                ox2 = (nw - r.w) // 2; oy2 = (nh - img_h) // 2
                ox2 = max(0, min(ox2, nw - r.w))
                oy2 = max(0, min(oy2, nh - img_h))
                clip = scaled.subsurface((ox2, oy2, r.w, img_h))
                img_mask = pygame.Surface((r.w, img_h), pygame.SRCALPHA)
                pygame.draw.rect(img_mask, (255,255,255,255), (0,0,r.w,img_h),
                                 border_top_left_radius=16, border_top_right_radius=16)
                img_result = clip.copy().convert_alpha()
                img_result.blit(img_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
                dim = pygame.Surface((r.w, img_h), pygame.SRCALPHA)
                dim.fill((0,0,0,int(60 - hover_f * 30)))
                img_result.blit(dim, (0,0))
                card_surf.blit(img_result, (0, 0))
            except Exception:
                raw = None
        if raw is None:
            # Fallback: gradient fill with accent colour
            for fi in range(img_h):
                frac = fi / img_h
                fc = tuple(int(c * (0.15 + frac * 0.35)) for c in accent)
                pygame.draw.line(card_surf, fc, (0, fi), (r.w, fi))
            big_f = pygame.font.SysFont("consolas", 72, bold=True)
            big_s = big_f.render(label[0], True, accent)
            tmp = pygame.Surface((big_s.get_width(), big_s.get_height()), pygame.SRCALPHA)
            tmp.blit(big_s, (0,0)); tmp.set_alpha(80)
            card_surf.blit(tmp, tmp.get_rect(center=(r.w // 2, img_h // 2)))
            corner_mask = pygame.Surface((r.w, img_h), pygame.SRCALPHA)
            pygame.draw.rect(corner_mask, (255,255,255,255), (0,0,r.w,img_h),
                             border_top_left_radius=16, border_top_right_radius=16)
            card_surf.blit(corner_mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)

        # Gradient fade at bottom of image into card body
        for gi in range(32):
            ga = int((gi / 32) * 220)
            gs2 = pygame.Surface((r.w, 1), pygame.SRCALPHA)
            gs2.fill((12, 14, 22, ga))
            card_surf.blit(gs2, (0, img_h - 32 + gi))

        # Accent line under image
        line_y = img_h
        pulse = abs(math.sin(t * 2 + hash(label) % 10)) * 0.3 + 0.7
        line_col = tuple(int(c * pulse) for c in accent)
        pygame.draw.line(card_surf, (*line_col, 200), (16, line_y), (r.w - 16, line_y), 2)

        surf.blit(card_surf, (r.x, r.y))

        # Border
        brd_alpha = int(hover_f * 80 + 120)
        brd_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(brd_surf, (*accent, brd_alpha), (0,0,r.w,r.h), 2, border_radius=16)
        surf.blit(brd_surf, (r.x, r.y))

        # ── Text area ──
        text_y = r.y + img_h + 10

        # Mode label
        lbl_f = pygame.font.SysFont("consolas", 22, bold=True)
        lbl_s = lbl_f.render(label, True, C_WHITE)
        surf.blit(lbl_s, (r.x + 14, text_y))
        text_y += lbl_s.get_height() + 6

        # Description
        desc_f = pygame.font.SysFont("segoeui", 13)
        desc_s = desc_f.render(desc, True, (160, 165, 185))
        surf.blit(desc_s, (r.x + 14, text_y))
        text_y += desc_s.get_height() + 8

        # Stats
        stat_f = pygame.font.SysFont("segoeui", 12, bold=True)
        for line in stats:
            if line.startswith("+5 shards"):
                # Render shard reward line with icon + highlight
                ico_sh = load_icon("shard_ico", 13)
                sh_col = (140, 190, 255)
                sh_s = stat_f.render(line, True, sh_col)
                if ico_sh:
                    surf.blit(ico_sh, (r.x + 14, text_y + (sh_s.get_height() - ico_sh.get_height()) // 2))
                    surf.blit(sh_s, (r.x + 14 + ico_sh.get_width() + 3, text_y))
                else:
                    sh_s2 = stat_f.render("◆ " + line, True, sh_col)
                    surf.blit(sh_s2, (r.x + 14, text_y))
                text_y += sh_s.get_height() + 3
            else:
                st_s = stat_f.render(line, True, (120, 130, 160))
                surf.blit(st_s, (r.x + 14, text_y))
                text_y += st_s.get_height() + 3

        # Reward badge — bottom right of card
        ico_m = load_icon("coin_ico", 14)
        rew_f = pygame.font.SysFont("segoeui", 13, bold=True)
        rew_s = rew_f.render(reward, True, reward_col)
        ico_w2 = (ico_m.get_width() + 3) if (ico_m and reward != "—") else 0
        total_rw = ico_w2 + rew_s.get_width() + 10
        rx = r.right - total_rw - 8
        ry = r.bottom - rew_s.get_height() - 10
        rew_bg = pygame.Surface((total_rw, rew_s.get_height() + 6), pygame.SRCALPHA)
        pygame.draw.rect(rew_bg, (0,0,0,120), (0,0,total_rw, rew_s.get_height()+6), border_radius=6)
        surf.blit(rew_bg, (rx, ry - 3))
        if ico_m and reward != "—":
            surf.blit(ico_m, (rx + 5, ry + (rew_s.get_height() - ico_m.get_height()) // 2))
            surf.blit(rew_s, (rx + 5 + ico_m.get_width() + 3, ry))
        else:
            surf.blit(rew_s, (rx + 5, ry))

    def _draw(self):
        surf = self.screen
        _draw_menu_bg(surf, overlay_alpha=130)

        t = self.t
        mx, my = pygame.mouse.get_pos()

        # Title
        title_f = pygame.font.SysFont("consolas", 38, bold=True)
        title_s = title_f.render("SELECT MODE", True, C_WHITE)
        # Subtle letter-spacing effect with alpha
        title_x = SCREEN_W // 2 - title_s.get_width() // 2
        title_y = self._cards[0].y - 80
        # Glow behind title
        glow_s = pygame.Surface((title_s.get_width() + 60, title_s.get_height() + 20), pygame.SRCALPHA)
        glow_a = int(abs(math.sin(t * 1.2)) * 20 + 20)
        glow_s.fill((80, 140, 255, glow_a))
        surf.blit(glow_s, (title_x - 30, title_y - 10))
        surf.blit(title_s, (title_x, title_y))
        # Underline
        ul_y = title_y + title_s.get_height() + 6
        ul_w = int(abs(math.sin(t * 0.8)) * 60 + title_s.get_width() - 60)
        ul_x = SCREEN_W // 2 - ul_w // 2
        pygame.draw.line(surf, (80, 140, 255), (ul_x, ul_y), (ul_x + ul_w, ul_y), 2)

        # Cards
        for i, mode_def in enumerate(self._MODES):
            self._draw_card(surf, self._cards[i], mode_def, self._hover_anim[i])

        # Back button
        hov_back = self.btn_back.collidepoint(mx, my)
        bb = self.btn_back
        back_bg = pygame.Surface((bb.w, bb.h), pygame.SRCALPHA)
        pygame.draw.rect(back_bg, (20, 24, 38, 210), (0,0,bb.w,bb.h), border_radius=10)
        surf.blit(back_bg, (bb.x, bb.y))
        brd_col = (120, 160, 255) if hov_back else (55, 65, 100)
        pygame.draw.rect(surf, brd_col, bb, 2, border_radius=10)
        back_f = pygame.font.SysFont("segoeui", 20, bold=True)
        back_s = back_f.render("← BACK", True, C_WHITE if hov_back else (160, 170, 200))
        surf.blit(back_s, back_s.get_rect(center=bb.center))

        # ── HARDCORE BETA button — bottom right ───────────────────────────────
        hc_btn = self.btn_hardcore
        hc_hov = hc_btn.collidepoint(mx, my)
        glow_alpha = int(abs(math.sin(t * 2.4)) * 60 + 30)
        glow_surf = pygame.Surface((hc_btn.w + 24, hc_btn.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (210, 40, 20, glow_alpha),
                         (0, 0, hc_btn.w + 24, hc_btn.h + 24), border_radius=14)
        surf.blit(glow_surf, (hc_btn.x - 12, hc_btn.y - 12))
        hc_bg  = (100, 18, 8) if hc_hov else (72, 10, 4)
        hc_brd = (255, 80, 30) if hc_hov else (int(160 + abs(math.sin(t * 2.4)) * 60), 40, 18)
        pygame.draw.rect(surf, hc_bg,  hc_btn, border_radius=10)
        pygame.draw.rect(surf, hc_brd, hc_btn, 2, border_radius=10)
        sk_x = hc_btn.x + 12; sk_y = hc_btn.centery; sk_r = 10
        pygame.draw.circle(surf, (230, 60, 30), (sk_x + sk_r, sk_y - 1), sk_r)
        pygame.draw.rect(surf, (230, 60, 30), (sk_x + 2, sk_y + 6, sk_r * 2 - 4, 7), border_radius=2)
        for ex2, ey2 in [(sk_x + sk_r - 4, sk_y - 3), (sk_x + sk_r + 4, sk_y - 3)]:
            pygame.draw.circle(surf, hc_bg, (ex2, ey2), 3)
        hc_f1 = pygame.font.SysFont("consolas", 18, bold=True)
        hc_f2 = pygame.font.SysFont("segoeui",  12)
        hc_lbl = hc_f1.render("HARDCORE", True, (255, 100, 60) if hc_hov else (210, 65, 30))
        hc_sub = hc_f2.render("BETA", True, (255, 200, 50))
        text_x = hc_btn.x + 36
        surf.blit(hc_lbl, (text_x, hc_btn.y + 6))
        surf.blit(hc_sub, (text_x, hc_btn.y + hc_lbl.get_height() + 4))



# ── Credits Screen ────────────────────────────────────────────────────────────
class CreditsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        self.running = True
        self.btn_back = pygame.Rect(SCREEN_W//2 - 130, SCREEN_H - 80, 260, 50)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); import sys; sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.collidepoint(ev.pos):
                        self.running = False
            self._draw()
            pygame.display.flip()

    def _draw(self):
        surf = self.screen
        surf.fill(C_BG)
        import random, math
        random.seed(33)
        for _ in range(160):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.0 + sx * 0.012)) * 150 + 50)
            pygame.draw.circle(surf, (br, br, br), (sx, sy), 1)
        random.seed()

        # Header
        pygame.draw.rect(surf, C_PANEL, (0, 0, SCREEN_W, 70))
        pygame.draw.line(surf, C_BORDER, (0, 70), (SCREEN_W, 70), 2)
        hf = pygame.font.SysFont("segoeui", 36, bold=True)
        hs = hf.render("CREDITS", True, (180, 200, 255))
        surf.blit(hs, hs.get_rect(center=(SCREEN_W // 2, 35)))

        # Credits content
        lines = [
            ("", None, False),
            ("Game Creator", (120, 140, 180), False),
            ("zigres", (255, 255, 255), True),
            ("", None, False),

            ("", None, False),
            ("Inspired by", (120, 140, 180), False),
            ("Tower Defense Simulator", (200, 220, 255), True),
        ]

        cy2 = 130
        for text, color, bold in lines:
            if not text:
                cy2 += 28
                continue
            f = pygame.font.SysFont("segoeui", 28 if bold else 20, bold=bold)
            s2 = f.render(text, True, color)
            surf.blit(s2, s2.get_rect(center=(SCREEN_W // 2, cy2)))
            cy2 += (42 if bold else 28)

        # Back button
        mx, my = pygame.mouse.get_pos()
        hov = self.btn_back.collidepoint(mx, my)
        pygame.draw.rect(surf, (60, 80, 140) if hov else (35, 42, 65), self.btn_back, border_radius=10)
        pygame.draw.rect(surf, C_BORDER, self.btn_back, 2, border_radius=10)
        bf = pygame.font.SysFont("segoeui", 24, bold=True)
        bs = bf.render("← BACK", True, C_WHITE)
        surf.blit(bs, bs.get_rect(center=self.btn_back.center))


# ── Achievement Toast ─────────────────────────────────────────────────────────
class AchievementToast:
    """Bottom-right toast notification for newly unlocked achievements."""
    def __init__(self, ach_def):
        self.ach = ach_def
        self.life = 4.5
        self.t = 0.0
        self.w, self.h = 380, 70

    def update(self, dt):
        self.t += dt
        return self.t < self.life

    def draw(self, surf, slot_index):
        """slot_index = 0 is bottom-most, each slot is (h+8) px higher."""
        alpha_frac = 1.0
        if self.t < 0.4:
            alpha_frac = self.t / 0.4
        elif self.t > self.life - 0.6:
            alpha_frac = (self.life - self.t) / 0.6
        alpha = max(0, min(255, int(alpha_frac * 255)))

        bx = SCREEN_W - self.w - 14
        by = SCREEN_H - 14 - (self.h + 8) * (slot_index + 1)

        border_col = self.ach["border"]
        bg_col = tuple(max(0, c - 100) for c in border_col)

        # Background
        bg_s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(bg_s, (*bg_col, min(210, alpha)), (0, 0, self.w, self.h), border_radius=10)
        pygame.draw.rect(bg_s, (*border_col, alpha), (0, 0, self.w, self.h), 2, border_radius=10)
        surf.blit(bg_s, (bx, by))

        # Gold left stripe
        stripe_s = pygame.Surface((5, self.h - 4), pygame.SRCALPHA)
        stripe_s.fill((*border_col, alpha))
        surf.blit(stripe_s, (bx + 2, by + 2))

        # Label row
        lf = pygame.font.SysFont("segoeui", 13)
        lbl = lf.render("ACHIEVEMENT UNLOCKED", True, (*border_col,))
        lbl.set_alpha(alpha)
        surf.blit(lbl, (bx + 14, by + 8))

        # Achievement name
        nf = pygame.font.SysFont("segoeui", 19, bold=True)
        ns = nf.render(self.ach["name"], True, (255, 255, 255))
        ns.set_alpha(alpha)
        surf.blit(ns, (bx + 14, by + 24))

        # Description
        df = pygame.font.SysFont("segoeui", 13)
        ds = df.render(self.ach["desc"], True, (180, 180, 200))
        ds.set_alpha(alpha)
        surf.blit(ds, (bx + 14, by + 46))


# ── Terraprisma summon (spawned by Castbound charge bar) ─────────────────────
_TERRAPRISMA_IMG_CACHE = {}

def _load_terraprisma_img(size=38):
    if size in _TERRAPRISMA_IMG_CACHE:
        return _TERRAPRISMA_IMG_CACHE[size]
    path = os.path.join(_ICON_DIR, "terraprisma.png")
    try:
        raw = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(raw, (size, size))
    except Exception:
        img = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(img, (180, 50, 255), [
            (size//2, 0), (size, size//2), (size//2, size), (0, size//2)
        ])
    _TERRAPRISMA_IMG_CACHE[size] = img
    return img


class Terraprisma:
    """Floating summon spawned by Castbound. Seeks enemies, attacks them."""
    DAMAGE    = 100
    FIRERATE  = 3.0      # attacks per second
    LIFETIME  = 20.0     # seconds
    SPEED     = 220.0    # px/s towards target
    ATTACK_RANGE = 180   # px — distance at which it starts attacking
    IDLE_RADIUS  = 55    # px — orbit radius behind owner when idle
    IMG_SIZE  = 38

    def __init__(self, owner, index):
        self.owner   = owner          # Castbound instance
        self.index   = index          # 0-2, orbit slot
        self.x       = float(owner.px)
        self.y       = float(owner.py)
        self.life    = self.LIFETIME
        self.t       = 0.0
        self._cd     = 0.0            # attack cooldown
        self._target = None           # current enemy
        self._state  = "idle"         # "idle" | "approach" | "attack"
        self._angle  = 0.0            # spin angle for idle orbit
        self._hit_flash = 0.0         # visual flash timer

    def update(self, dt, enemies, effects):
        self.life -= dt
        if self.life <= 0:
            return False
        self.t += dt
        self._cd = max(0.0, self._cd - dt)
        self._hit_flash = max(0.0, self._hit_flash - dt)

        # Find closest living enemy
        best_e = None
        best_d = 9999999
        for e in enemies:
            if not e.alive:
                continue
            d = dist((self.x, self.y), (e.x, e.y))
            if d < best_d:
                best_d = d
                best_e = e

        if best_e is None or best_d > self.ATTACK_RANGE * 3:
            self._state  = "idle"
            self._target = None
        elif best_d <= self.ATTACK_RANGE:
            self._state  = "attack"
            self._target = best_e
        else:
            self._state  = "approach"
            self._target = best_e

        ox, oy = float(self.owner.px), float(self.owner.py)

        if self._state == "idle":
            # Orbit behind owner
            self._angle += dt * 1.4
            slot_off = self.index * (2 * math.pi / 3)
            tx = ox - math.cos(self._angle + slot_off) * self.IDLE_RADIUS
            ty = oy + math.sin(self._angle + slot_off) * self.IDLE_RADIUS * 0.5
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy) or 1
            speed = min(d / dt if dt > 0 else self.SPEED, self.SPEED * 2)
            self.x += (dx / d) * speed * dt
            self.y += (dy / d) * speed * dt

        elif self._state == "approach":
            e = self._target
            dx, dy = e.x - self.x, e.y - self.y
            d = math.hypot(dx, dy) or 1
            self.x += (dx / d) * self.SPEED * dt
            self.y += (dy / d) * self.SPEED * dt

        elif self._state == "attack":
            e = self._target
            # Hover just outside enemy radius
            dx, dy = e.x - self.x, e.y - self.y
            d = math.hypot(dx, dy) or 1
            hover_d = max(0, d - e.radius - 20)
            if hover_d > 8:
                self.x += (dx / d) * self.SPEED * 0.6 * dt
                self.y += (dy / d) * self.SPEED * 0.6 * dt
            # Attack on cooldown
            if self._cd <= 0 and e.alive:
                e.hp -= self.DAMAGE
                if e.hp <= 0:
                    e.alive = False
                self._cd = 1.0 / self.FIRERATE
                self._hit_flash = 0.12
                # Hit visual effect
                effects.append(FloatingText(e.x, e.y - e.radius - 8, f"-{self.DAMAGE}", (200, 80, 255)))

        return True  # still alive

    def draw(self, surf):
        img = _load_terraprisma_img(self.IMG_SIZE)

        # Spin animation
        angle = (self.t * 180) % 360
        rotated = pygame.transform.rotate(img, angle)

        # Flash white on hit
        if self._hit_flash > 0:
            flash = rotated.copy()
            flash.fill((255, 255, 255, 160), special_flags=pygame.BLEND_RGBA_MULT)
            rotated = flash

        # Lifetime fade-out in last 2s
        if self.life < 2.0:
            alpha = max(0, int((self.life / 2.0) * 255))
            rotated.set_alpha(alpha)

        r = rotated.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rotated, r)

        # Purple glow aura
        glow_r = self.IMG_SIZE // 2 + 6
        glow_s = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        pulse = int(30 + 20 * math.sin(self.t * 5.0))
        pygame.draw.circle(glow_s, (180, 0, 255, pulse), (glow_r, glow_r), glow_r)
        surf.blit(glow_s, (int(self.x) - glow_r, int(self.y) - glow_r))

        # Lifetime bar above
        bar_w = 32
        bar_h = 3
        bx = int(self.x) - bar_w // 2
        by = int(self.y) - self.IMG_SIZE // 2 - 7
        frac = max(0.0, self.life / self.LIFETIME)
        pygame.draw.rect(surf, (40, 10, 60), (bx, by, bar_w, bar_h), border_radius=2)
        pygame.draw.rect(surf, (200, 80, 255), (bx, by, int(bar_w * frac), bar_h), border_radius=2)



# ── Achievement Manager ────────────────────────────────────────────────────────
class AchievementManager:
    """Manages granting and displaying achievement toasts in-game."""
    def __init__(self):
        self.toasts = []  # list of AchievementToast

    def try_grant(self, ach_id):
        """Try to grant achievement; if newly unlocked, show toast."""
        if grant_achievement(ach_id):
            adef = next((a for a in ACHIEVEMENT_DEFS if a["id"] == ach_id), None)
            if adef:
                self.toasts.append(AchievementToast(adef))

    def update(self, dt):
        self.toasts = [t for t in self.toasts if t.update(dt)]

    def draw(self, surf):
        for i, toast in enumerate(self.toasts):
            toast.draw(surf, i)


# ── Achievements Screen ────────────────────────────────────────────────────────
class AchievementsScreen:
    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        self.running = True
        self.btn_back = pygame.Rect(20, 20, 130, 44)
        self.scroll_y = 0

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); import sys; sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.type == pygame.MOUSEWHEEL:
                    self.scroll_y = max(0, self.scroll_y - ev.y * 30)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.collidepoint(ev.pos):
                        self.running = False
            self._draw()
            pygame.display.flip()

    def _draw(self):
        surf = self.screen
        surf.fill(C_BG)

        # Stars bg
        import random, math
        random.seed(99)
        for _ in range(160):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.1 + sx * 0.013)) * 160 + 50)
            pygame.draw.circle(surf, (br, br, br), (sx, sy), 1)
        random.seed()

        # Header
        pygame.draw.rect(surf, C_PANEL, (0, 0, SCREEN_W, 70))
        pygame.draw.line(surf, C_BORDER, (0, 70), (SCREEN_W, 70), 2)
        hf = pygame.font.SysFont("segoeui", 36, bold=True)
        hs = hf.render("ACHIEVEMENTS", True, C_GOLD)
        surf.blit(hs, hs.get_rect(center=(SCREEN_W // 2, 35)))

        # Back button
        mx, my = pygame.mouse.get_pos()
        hov = self.btn_back.collidepoint(mx, my)
        pygame.draw.rect(surf, (110, 50, 50) if hov else (80, 40, 40), self.btn_back, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_back, 2, border_radius=8)
        txt(surf, "← BACK", self.btn_back.center, C_WHITE, font_md, center=True)

        # Load unlocked
        ach_data = load_achievements()
        unlocked = set(ach_data.get("unlocked", []))

        # Grid layout
        CARD_W, CARD_H = 340, 100
        COLS = 4
        GAP = 24
        START_X = (SCREEN_W - (CARD_W * COLS + GAP * (COLS - 1))) // 2
        START_Y = 90

        # Scrollable zone
        CONTENT_TOP = 82
        CONTENT_H = SCREEN_H - CONTENT_TOP
        n_rows = max(1, (len(ACHIEVEMENT_DEFS) + COLS - 1) // COLS)
        total_h = n_rows * (CARD_H + GAP)
        max_scroll = max(0, total_h - CONTENT_H + 40)
        self.scroll_y = min(self.scroll_y, max_scroll)

        surf.set_clip(pygame.Rect(0, CONTENT_TOP, SCREEN_W, CONTENT_H))

        for i, ach in enumerate(ACHIEVEMENT_DEFS):
            col = i % COLS
            row = i // COLS
            cx2 = START_X + col * (CARD_W + GAP) + CARD_W // 2
            cy2 = START_Y + row * (CARD_H + GAP) + CARD_H // 2 - self.scroll_y

            if cy2 < CONTENT_TOP - CARD_H or cy2 > SCREEN_H + CARD_H:
                continue

            is_done = ach["id"] in unlocked
            border = ach["border"] if is_done else (60, 65, 80)
            bg = tuple(max(0, c - 110) for c in ach["color"]) if is_done else (22, 27, 38)

            card_rect = pygame.Rect(cx2 - CARD_W // 2, cy2 - CARD_H // 2, CARD_W, CARD_H)
            draw_rect_alpha(surf, bg, (card_rect.x, card_rect.y, CARD_W, CARD_H), 220, 12)
            pygame.draw.rect(surf, border, card_rect, 2, border_radius=12)

            # Colored left stripe
            stripe_col = ach["border"] if is_done else (50, 55, 70)
            pygame.draw.rect(surf, stripe_col,
                             pygame.Rect(card_rect.x + 2, card_rect.y + 6, 4, CARD_H - 12),
                             border_radius=2)

            # Lock / checkmark icon
            icon_x = card_rect.x + 22
            icon_y = cy2
            if is_done:
                # Pulsing checkmark circle
                pulse = abs(math.sin(self.t * 1.8 + i * 0.7))
                r_col = tuple(min(255, int(c * (0.7 + 0.3 * pulse))) for c in ach["border"])
                pygame.draw.circle(surf, r_col, (icon_x, icon_y), 18)
                # Hand-drawn checkmark (pygame can't render ✓ glyph reliably)
                _ck_pts = [
                    (icon_x - 7, icon_y),
                    (icon_x - 2, icon_y + 6),
                    (icon_x + 7, icon_y - 7),
                ]
                pygame.draw.lines(surf, C_WHITE, False, _ck_pts, 3)
            else:
                pygame.draw.circle(surf, (50, 55, 70), (icon_x, icon_y), 18)
                # Hand-drawn padlock (pygame cannot render emoji glyphs)
                _lc = (90, 95, 115)
                _bx, _by = icon_x - 6, icon_y - 1
                _bw, _bh = 12, 9
                pygame.draw.rect(surf, _lc, (_bx, _by, _bw, _bh), border_radius=2)
                pygame.draw.arc(surf, _lc,
                                pygame.Rect(icon_x - 5, icon_y - 11, 10, 10),
                                0, math.pi, 3)
                pygame.draw.circle(surf, (50, 55, 70), (icon_x, icon_y + 2), 2)

            # Name + desc
            tx = icon_x + 28
            name_col = C_WHITE if is_done else (100, 105, 120)
            nf2 = pygame.font.SysFont("segoeui", 20, bold=True)
            ns2 = nf2.render(ach["name"], True, name_col)
            surf.blit(ns2, (tx, cy2 - 24))
            df2 = pygame.font.SysFont("segoeui", 14)
            desc_col = (160, 165, 185) if is_done else (70, 75, 90)
            ds2 = df2.render(ach["desc"], True, desc_col)
            surf.blit(ds2, (tx, cy2 + 4))

        surf.set_clip(None)

        # Scrollbar
        if max_scroll > 0:
            sb_x = SCREEN_W - 10
            sb_top = CONTENT_TOP + 4
            sb_h = CONTENT_H - 8
            pygame.draw.rect(surf, (40, 45, 60), (sb_x - 4, sb_top, 6, sb_h), border_radius=3)
            thumb_h = max(30, int(sb_h * CONTENT_H / (total_h + 20)))
            thumb_y = sb_top + int((sb_h - thumb_h) * self.scroll_y / max_scroll)
            pygame.draw.rect(surf, (100, 120, 180), (sb_x - 4, thumb_y, 6, thumb_h), border_radius=3)

        # Counter bottom-right
        total_ach = len(ACHIEVEMENT_DEFS)
        done_ach = len(unlocked)
        cf3 = pygame.font.SysFont("segoeui", 18, bold=True)
        cs3 = cf3.render(f"{done_ach}/{total_ach} unlocked", True,
                         C_GOLD if done_ach == total_ach else (140, 145, 170))
        surf.blit(cs3, cs3.get_rect(bottomright=(SCREEN_W - 16, SCREEN_H - 10)))


# ── Global settings ──────────────────────────────────────────────────────────
SETTINGS = {
    "music_volume":   0.7,
    "music_muted":    False,
    "colored_range":  False,
    "sfx_volume":     0.7,
    "sfx_muted":      False,
    "show_fps":       False,
    "screen_shake":   True,
    "particles":      True,
    "show_damage":    True,
    "compact_numbers": True,
    "auto_skip":      False,
    "show_range_always": False,
    "sell_confirm":   True,
    "fast_forward_default": False,
    "low_quality":    False,
    "show_grid":      False,
    "windowed":       False,
    "resolution":     "1920x1080",
    "unlock_fps":     False,
    "linux_mode":     False,  # Включает Wayland Fix + KDE Tearing Fix + Arch Font Fix
    "menu_style":     0,   # 0 = Void/Gothic, 1 = Modern/Blue
    "no_tower_details": False,  # simple colored circles instead of detailed tower art
    "upgrade_preview":  True,   # show translucent next-level range ring on Upgrade hover
}


def _get_emoji_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return best available emoji font, respecting Linux Mode setting."""
    if SETTINGS.get("linux_mode", False):
        order = ("notocoloremoji", "noto color emoji", "symbola",
                 "segoeuiemoji", "seguiemj", "applesymbol", "segoeui")
    else:
        order = ("segoeuiemoji", "seguiemj", "notocoloremoji",
                 "applesymbol", "symbola", "segoeui")
    for _fname in order:
        try:
            _ef = pygame.font.SysFont(_fname, size, bold=bold)
            _ef.render("🌳", True, (255, 255, 255))
            return _ef
        except Exception:
            pass
    return pygame.font.SysFont("segoeui", size, bold=bold)

def _apply_audio_settings():
    try:
        vol = 0.0 if SETTINGS["music_muted"] else SETTINGS["music_volume"]
        pygame.mixer.music.set_volume(vol)
    except Exception: pass

def _apply_arch_linux_fix(key=None):
    """Apply all Linux Mode fixes (Wayland, KDE Tearing, Arch Font) at once."""
    import os as _os
    try:
        # ── Wayland Fix ──────────────────────────────────────────────────────────
        # Force SDL to use the Wayland backend instead of XWayland.
        # Fixes blurry scaling, incorrect DPI, and input lag on Wayland compositors.
        _os.environ.setdefault("SDL_VIDEODRIVER", "wayland")
        _os.environ.setdefault("SDL_DYNAMIC_API", "")
        # Disable compositor bypass (prevents black-screen flicker under KWin).
        _os.environ["SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR"] = "1"
        _os.environ.pop("SDL_VIDEO_X11_DGAMOUSE", None)

        # ── KDE Tearing Fix ──────────────────────────────────────────────────────
        # Tell SDL to request adaptive vsync (EGL_MIN_SWAP_INTERVAL=0 allows
        # triple-buffering), which eliminates tearing artifacts in KWin.
        _os.environ["SDL_RENDER_VSYNC"] = "1"
        _os.environ["__GL_SYNC_TO_VBLANK"] = "1"
        _os.environ["__GL_MaxFramesAllowed"] = "1"
        # Prevent KDE compositor from dropping frames on fullscreen apps.
        _os.environ.setdefault("KWIN_X11_NO_EXPLICIT_SYNC", "0")

        # ── Arch Font Fix ────────────────────────────────────────────────────────
        # On minimal Arch installs several Windows fonts are absent.
        # Pre-seed the pygame font cache with Noto/Liberation fallbacks.
        _os.environ.setdefault("PYGAME_FREETYPE", "1")
        _extra = "/usr/share/fonts/noto:/usr/share/fonts/liberation:/usr/share/fonts/TTF"
        _cur = _os.environ.get("FONTCONFIG_PATH", "")
        if _extra not in _cur:
            _os.environ["FONTCONFIG_PATH"] = (_cur + ":" + _extra).lstrip(":")
        try:
            pygame.font.init()
        except Exception:
            pass
    except Exception:
        pass

_RESOLUTIONS = ["1280x720", "1600x900", "1920x1080", "2560x1440"]

def _apply_display_mode(screen_ref=None):
    """Apply windowed/fullscreen and resolution. Returns new screen surface."""
    res_str = SETTINGS.get("resolution", "1920x1080")
    try:
        rw, rh = map(int, res_str.split("x"))
    except Exception:
        rw, rh = 1920, 1080
    windowed = SETTINGS.get("windowed", False)
    flags = 0 if windowed else pygame.FULLSCREEN
    new_screen = pygame.display.set_mode((rw, rh), flags)
    return new_screen

from game_core import SAVE_FILE as _SAVE_FILE
_SETTINGS_FILE = os.path.join(os.path.dirname(_SAVE_FILE), "settings.json")

def load_settings():
    global SETTINGS
    if os.path.exists(_SETTINGS_FILE):
        try:
            import json as _j
            data = _j.load(open(_SETTINGS_FILE))
            for k in SETTINGS:
                if k in data: SETTINGS[k] = data[k]
        except Exception: pass

def save_settings():
    try:
        import json as _j
        _j.dump(SETTINGS, open(_SETTINGS_FILE,"w"))
    except Exception: pass

load_settings()
game_core._COMPACT_NUMBERS = SETTINGS.get("compact_numbers", True)

def _apply_display_mode_startup():
    """Apply saved windowed/resolution on startup — only if non-default."""
    if SETTINGS.get("windowed", False) or SETTINGS.get("resolution", "1920x1080") != "1920x1080":
        try:
            _apply_display_mode()
        except Exception:
            pass
_apply_display_mode_startup()

def _sync_compact():
    game_core._COMPACT_NUMBERS = SETTINGS.get("compact_numbers", True)

# ── Patch Unit.draw_range for colored range rings ─────────────────────────────
_range_surf_cache: dict = {}
def _patched_draw_range(self, surf):
    r = int(self.range_tiles * TILE)
    if r <= 0: return
    col = self.COLOR if SETTINGS.get("colored_range", False) else (255, 255, 255)
    cache_key = (r, col)
    if cache_key not in _range_surf_cache:
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, 22), (r, r), r)
        pygame.draw.circle(s, (*col, 60), (r, r), r, 2)
        _range_surf_cache[cache_key] = s
    s = _range_surf_cache[cache_key]
    blit_x = int(self.px) - r
    blit_y = int(self.py) - r
    old_clip = surf.get_clip()
    surf.set_clip(pygame.Rect(0, 0, SCREEN_W, SLOT_AREA_Y))
    surf.blit(s, (blit_x, blit_y))
    surf.set_clip(old_clip)
Unit.draw_range = _patched_draw_range

# ── Wrap every subclass draw_range to clip to the game area (above the UI panel) ─
def _wrap_draw_range_clip(fn):
    """Wrap a draw_range method so it never blits below SLOT_AREA_Y."""
    def _wrapped(self, surf):
        old_clip = surf.get_clip()
        surf.set_clip(pygame.Rect(0, 0, SCREEN_W, SLOT_AREA_Y))
        fn(self, surf)
        surf.set_clip(old_clip)
    return _wrapped

_ALL_UNIT_CLASSES = [
    Assassin, Accelerator, Frostcelerator, Lifestealer,
    Archer, Farm, RedBall, FrostBlaster, Freezer,
    Sledger, Gladiator, ToxicGunner, Slasher, GoldenCowboy, HallowPunk,
    SpotlightTech, Snowballer, Commando,
    Caster, Warlock, Jester, SoulWeaver, RubberDuck,
    Militant, Swarmer, Harvester,
]
for _ucls in _ALL_UNIT_CLASSES:
    if "draw_range" in _ucls.__dict__:  # only patch classes that explicitly define it
        _ucls.draw_range = _wrap_draw_range_clip(_ucls.__dict__["draw_range"])

# ── Castbound: кастомный draw_range с клипом к игровой зоне ──────────────────
def _castbound_draw_range(self, surf):
    r = int(self.range_tiles * TILE)
    if r <= 0: return
    col = C_CASTBOUND if SETTINGS.get("colored_range", False) else (255, 255, 255)
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*col, 22), (r, r), r)
    pygame.draw.circle(s, (*col, 60), (r, r), r, 2)
    old_clip = surf.get_clip()
    surf.set_clip(pygame.Rect(0, 0, SCREEN_W, SLOT_AREA_Y))
    surf.blit(s, (int(self.px) - r, int(self.py) - r))
    surf.set_clip(old_clip)
Castbound.draw_range = _castbound_draw_range


class InterfaceSettingsScreen:
    def __init__(self, screen, save_data):
        self.screen = screen
        self.save_data = save_data
        self.layout = dict(save_data.get("ui_layout", {})) # working copy
        self.running = True
        self.t = 0.0
        
        total_slots_w = 5 * SLOT_W + 4 * 8
        self.elements = {
            "wave": {"w": 120, "h": 60, "def": (24, 10), "label": "Wave Info"},
            "hp":   {"w": 400, "h": 40, "def": (SCREEN_W//2-200, 20), "label": "HP Bar"},
            "timer":{"w": 200, "h": 70, "def": (SCREEN_W-214, 10), "label": "Time Left"},
            "skip": {"w": 280, "h": 90, "def": (SCREEN_W//2-140, 150), "label": "Skip Prompt"},
            "money":{"w": 160, "h": 46, "def": (SCREEN_W - 220, SLOT_AREA_Y + (SCREEN_H - SLOT_AREA_Y)//2 - 23), "label": "Money Counter"},
            "slots":{"w": total_slots_w, "h": SLOT_H, "def": ((SCREEN_W - total_slots_w)//2, SLOT_AREA_Y + 8), "label": "Loadout Slots"},
            "upgrade":{"w": 340, "h": 520, "def": (SCREEN_W-364, 80), "label": "Upgrade Menu"},
            "speed":{"w": 88,  "h": SLOT_H, "def": (((SCREEN_W - total_slots_w)//2)-100, SLOT_AREA_Y + 8), "label": "Speed Ctrl"},
            "admin":{"w": 100, "h": SLOT_H, "def": (((SCREEN_W - 332)//2)+344, SLOT_AREA_Y + 8), "label": "Admin Panel"}
        }
        
        self.drag_key = None
        self.drag_offset = (0, 0)
        
        cx = SCREEN_W // 2
        self.btn_accept = pygame.Rect(cx + 20, SCREEN_H - 120, 200, 44)
        self.btn_reset  = pygame.Rect(cx - 220, SCREEN_H - 120, 200, 44)
        self.btn_back   = pygame.Rect(18, 14, 100, 36)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0; self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: self.running = False
                
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos = ev.pos
                    if self.btn_back.collidepoint(pos):
                        self.running = False
                    elif self.btn_accept.collidepoint(pos):
                        self.save_data["ui_layout"] = dict(self.layout)
                        write_save(self.save_data)
                        self.running = False
                    elif self.btn_reset.collidepoint(pos):
                        self.layout = {}
                    else:
                        for k in list(self.elements.keys())[::-1]:
                            info = self.elements[k]
                            ex, ey = self.layout.get(k, info["def"])
                            rect = pygame.Rect(ex, ey, info["w"], info["h"])
                            if rect.collidepoint(pos):
                                self.drag_key = k
                                self.drag_offset = (pos[0] - ex, pos[1] - ey)
                                break
                                
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    self.drag_key = None
                    
                if ev.type == pygame.MOUSEMOTION:
                    if self.drag_key:
                        self.layout[self.drag_key] = (ev.pos[0] - self.drag_offset[0], ev.pos[1] - self.drag_offset[1])
                        
            self._draw()
            pygame.display.flip()

    def _draw(self):
        surf = self.screen
        surf.fill((10, 15, 25))
        
        # Grid
        for x in range(0, SCREEN_W, 50): pygame.draw.line(surf, (30,35,50), (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 50): pygame.draw.line(surf, (30,35,50), (0, y), (SCREEN_W, y))
        
        f_lbl = pygame.font.SysFont("segoeui", 20, bold=True)
        f_val = pygame.font.SysFont("segoeui", 28, bold=True)
        def _out_txt(text, font, pos, color=(255,255,255), outline=2, cx=False, cy=False):
            s_in = font.render(str(text), True, color)
            x, y = pos
            if cx: x -= s_in.get_width() // 2
            if cy: y -= s_in.get_height() // 2
            for dx in range(-outline, outline+1):
                for dy in range(-outline, outline+1):
                    if dx==0 and dy==0: continue
                    s_out = font.render(str(text), True, (0,0,0))
                    surf.blit(s_out, (x+dx, y+dy))
            surf.blit(s_in, (x, y))

        for k, info in self.elements.items():
            ex, ey = self.layout.get(k, info["def"])
            r = pygame.Rect(ex, ey, info["w"], info["h"])
            # Draw subtle background box for selection feeling
            draw_rect_alpha(surf, (100,100,100), r, 60 if self.drag_key == k else 30, 8)
            pygame.draw.rect(surf, (255,255,255) if self.drag_key == k else (80,80,100), r, 2 if self.drag_key == k else 1, border_radius=8)
            
            if k == "wave":
                _out_txt("Wave:", f_lbl, (ex, ey), cx=False)
                _out_txt("10/50", f_val, (ex + f_lbl.render("Wave:", True, C_WHITE).get_width()//2, ey + 26), cx=True)
            elif k == "hp":
                bx_hp, by_hp = ex, ey
                bw_hp, bh_hp = 400, 30
                _out_txt("Base Health", f_lbl, (bx_hp + bw_hp//2, by_hp - 22), cx=True)
                pygame.draw.rect(surf, (0, 0, 0), (bx_hp-2, by_hp-2, bw_hp+4, bh_hp+4), border_radius=6)
                pygame.draw.rect(surf, (60, 220, 70), (bx_hp, by_hp, bw_hp, bh_hp), border_radius=5)
                plus_f = pygame.font.SysFont("segoeui", 28, bold=True)
                plus_s = plus_f.render("+", True, (20, 80, 25))
                surf.blit(plus_s, (bx_hp + 8, by_hp + bh_hp//2 - plus_s.get_height()//2 - 1))
                _out_txt("100", f_lbl, (bx_hp + bw_hp//2, by_hp + bh_hp//2), cx=True, cy=True)
            elif k == "timer":
                tx, ty = ex, ey
                ico_hr = load_icon("firerate_ico", 22)
                ico_w_t = (ico_hr.get_width() + 4) if ico_hr else 0
                f_time = pygame.font.SysFont("segoeui", 38, bold=True)
                lbl_surf_t = f_lbl.render("Time Left:", True, C_WHITE)
                tim_surf_t = f_time.render("00:45", True, C_WHITE)
                block_w_t = max(ico_w_t + lbl_surf_t.get_width(), tim_surf_t.get_width())
                lbl_x = tx
                if ico_hr:
                    surf.blit(ico_hr, (tx, ty + 1))
                    lbl_x = tx + ico_w_t
                _out_txt("Time Left:", f_lbl, (lbl_x, ty))
                _out_txt("00:45", f_time, (tx + block_w_t // 2, ty + 22), cx=True)
            elif k == "skip":
                cx_skip = ex + 140
                sy = ey
                f_skip = pygame.font.SysFont("segoeui", 36, bold=True)
                _out_txt("Skip Wave?", f_skip, (cx_skip - 120, sy + 40), cx=True, cy=True)
                
                gx, gy = cx_skip + 20, sy; gw, gh = 70, 80
                pygame.draw.rect(surf, (0,0,0), (gx-3, gy-3, gw+6, gh+6), border_radius=10)
                pygame.draw.rect(surf, (40, 220, 100), (gx, gy, gw, gh), border_radius=7)
                pygame.draw.rect(surf, (10, 160, 40), (gx, gy + 50, gw, 30), border_radius=7)
                pygame.draw.rect(surf, (10, 160, 40), (gx, gy + 50, gw, 15))
                pygame.draw.lines(surf, (0,0,0), False, [(gx+16, gy+24), (gx+28, gy+36), (gx+54, gy+10)], 8)
                pygame.draw.lines(surf, C_WHITE, False, [(gx+16, gy+24), (gx+28, gy+36), (gx+54, gy+10)], 5)
                f_zero = pygame.font.SysFont("segoeui", 16, bold=True)
                _out_txt("0", f_zero, (gx + gw//2, gy + 65), cx=True, cy=True)
                
                rx, ry = cx_skip + 110, sy; rw, rh = 70, 80
                pygame.draw.rect(surf, (0,0,0), (rx-3, ry-3, rw+6, rh+6), border_radius=10)
                pygame.draw.rect(surf, (250, 40, 40), (rx, ry, rw, rh), border_radius=7)
                pygame.draw.rect(surf, (190, 10, 10), (rx, ry + 50, rw, 30), border_radius=7)
                pygame.draw.rect(surf, (190, 10, 10), (rx, ry + 50, rw, 15))
                pygame.draw.line(surf, (0,0,0), (rx+20, ry+14), (rx+50, ry+44), 8)
                pygame.draw.line(surf, (0,0,0), (rx+50, ry+14), (rx+20, ry+44), 8)
                pygame.draw.line(surf, C_WHITE, (rx+20, ry+14), (rx+50, ry+44), 5)
                pygame.draw.line(surf, C_WHITE, (rx+50, ry+14), (rx+20, ry+44), 5)
                _out_txt("0", f_zero, (rx + rw//2, ry + 65), cx=True, cy=True)
            elif k == "money":
                ico_money = load_icon("money_ico", 36)
                if ico_money: surf.blit(ico_money, (ex, ey))
                ms = pygame.font.SysFont("segoeui", 28, bold=True).render("1,500", True, C_GOLD)
                surf.blit(ms, (ex + (36 if ico_money else 0) + 6, ey + 18 - ms.get_height()//2))
            elif k == "slots":
                sw, sh = SLOT_W, SLOT_H
                for i in range(5):
                    sx, sy = ex + i * (sw + 8), ey
                    # Card
                    pygame.draw.rect(surf, (22, 27, 40), (sx, sy, sw, sh), border_radius=12)
                    pygame.draw.rect(surf, (45, 54, 78), (sx, sy, sw, sh), 2, border_radius=12)
                    # Circle
                    r_outer, r_inner = 34, 28
                    icon_cy = sy + 52
                    pygame.draw.circle(surf, (10, 10, 18), (sx + sw//2, icon_cy), r_outer + 3)
                    pygame.draw.circle(surf, tuple(max(0, c-60) for c in ((100, 100, 200) if i%2==0 else (200, 100, 100))), (sx + sw//2, icon_cy), r_outer)
                    pygame.draw.circle(surf, (100, 100, 200) if i%2==0 else (200, 100, 100), (sx + sw//2, icon_cy), r_inner)
                    pygame.draw.circle(surf, (160, 160, 255) if i%2==0 else (255, 160, 160), (sx + sw//2, icon_cy), r_inner, 2)
                    # Label
                    name_f = pygame.font.SysFont("segoeui", 17, bold=True)
                    price_f = pygame.font.SysFont("segoeui", 15)
                    _out_txt("Scout" if i==0 else "Unit", name_f, (sx + sw//2, sy + 94), outline=0, color=(210, 215, 230), cx=True)
                    _out_txt(f"$ {i*200+200}", price_f, (sx + sw//2, sy + 115), color=C_GOLD, outline=0, cx=True)
            elif k == "upgrade":
                uw, uh = info["w"], info["h"]
                pygame.draw.rect(surf, (22, 27, 38), (ex, ey, uw, uh), border_radius=16)
                pygame.draw.rect(surf, (45, 55, 75), (ex, ey, uw, uh), 2, border_radius=16)
                pygame.draw.rect(surf, (30, 40, 60), (ex, ey, uw, 120), border_radius=16)
                pygame.draw.rect(surf, (22, 27, 38), (ex, ey+100, uw, 20))
                pygame.draw.circle(surf, (100, 100, 200), (ex + 60, ey + 60), 32)
                _out_txt("Scout", f_val, (ex + 110, ey + 30))
                _out_txt("Level 0", f_lbl, (ex + 110, ey + 60), color=(180, 180, 200))
                
                # Upgrade Button in center
                ubx, uby, ubw, ubh = ex + 6, ey + 258, uw - 12, 44
                pygame.draw.rect(surf, (40, 140, 60), (ubx, uby, ubw, ubh), border_radius=6)
                _out_txt("UPGRADE   $ 200", f_lbl, (ubx + ubw//2, uby + ubh//2), cx=True, cy=True)
                
                # Target panel to the left
                tp_w, tp_h = 100, 70
                tp_x = ex - tp_w - 8
                tp_y = ey + (uh - tp_h) // 2
                pygame.draw.rect(surf, (20, 16, 36), (tp_x, tp_y, tp_w, tp_h), border_radius=8)
                pygame.draw.rect(surf, (55, 44, 82), (tp_x, tp_y, tp_w, tp_h), 2, border_radius=8)
                f_sm = pygame.font.SysFont("segoeui", 12)
                mode_f = pygame.font.SysFont("segoeui", 15, bold=True)
                _out_txt("TARGET", f_sm, (tp_x + tp_w//2, tp_y + 10), color=(160,155,200), cx=True, cy=True)
                _out_txt("First", mode_f, (tp_x + tp_w//2, tp_y + 36), color=(220,215,255), cx=True, cy=True)
                
                # Bottom Buttons
                br_y = ey + uh - 44
                pygame.draw.rect(surf, (160, 40, 40), (ex + 6, br_y, 38, 38), border_radius=6)
                pygame.draw.rect(surf, (220, 180, 30), (ex + 48, br_y, uw - 54, 38), border_radius=6)
                _out_txt("X", f_lbl, (ex + 25, br_y + 19), cx=True, cy=True)
                _out_txt("SELL $100", f_lbl, (ex + 48 + (uw-54)//2, br_y + 19), color=(20, 20, 20), outline=0, cx=True, cy=True)
            else:
                txt(surf, info.get("label", k), r.center, C_WHITE, font_lg, center=True)
            
        mx, my = pygame.mouse.get_pos()
        txt(surf, "DRAG ELEMENTS TO CUSTOMIZE LAYOUT", (SCREEN_W//2, 30), C_CYAN, font_xl, center=True)
        
        rov = self.btn_reset.collidepoint(mx, my)
        pygame.draw.rect(surf, (180,50,50) if rov else (130,40,40), self.btn_reset, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_reset, 2, border_radius=8)
        txt(surf, "RESET TO DEFAULT", self.btn_reset.center, C_WHITE, font_sm, center=True)
        
        aov = self.btn_accept.collidepoint(mx, my)
        pygame.draw.rect(surf, (50,180,80) if aov else (40,130,60), self.btn_accept, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_accept, 2, border_radius=8)
        txt(surf, "ACCEPT", self.btn_accept.center, C_WHITE, font_sm, center=True)
        
        bov = self.btn_back.collidepoint(mx, my)
        pygame.draw.rect(surf, (80,80,100) if bov else (50,50,70), self.btn_back, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_back, 1, border_radius=8)
        txt(surf, "BACK", self.btn_back.center, C_WHITE, font_sm, center=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Profile Screen
# ═══════════════════════════════════════════════════════════════════════════════
class ProfileScreen:
    """Displays per-player profile stats: W/L ratio, KD, games, waves, etc."""

    _MODE_LABELS = {
        "easy":     ("Easy",     ( 60, 180, 100)),
        "fallen":   ("Fallen",   (160,  60, 220)),
        "frosty":   ("Frosty",   ( 60, 180, 255)),
        "infernal": ("Infernal", (255, 100,  30)),
        "hardcore": ("Hardcore", (255,  50,  50)),
        "sandbox":  ("Sandbox",  (120, 120, 140)),
    }

    def __init__(self, screen, save_data):
        self.screen      = screen
        self.save_data   = save_data
        self.running     = True
        self.t           = 0.0
        self.scroll      = 0
        cx = SCREEN_W // 2
        self._cx         = cx
        self.btn_back    = pygame.Rect(cx - 110, SCREEN_H - 68, 220, 46)
        # nick editing state
        self._nick_editing  = False
        self._nick_input    = save_data.get("player_nick", "Player")
        self._nick_cursor_t = 0.0   # blink timer

    def _nick_rect(self, cy):
        cx = self._cx
        return pygame.Rect(cx - 160, cy + 118, 320, 38)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self._nick_editing:
                self._nick_cursor_t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if self._nick_editing:
                        if ev.key == pygame.K_RETURN or ev.key == pygame.K_ESCAPE:
                            # save nick
                            nick = self._nick_input.strip() or "Player"
                            self._nick_input = nick
                            self.save_data["player_nick"] = nick
                            from game_core import write_save as _ws
                            _ws(self.save_data)
                            self._nick_editing = False
                        elif ev.key == pygame.K_BACKSPACE:
                            self._nick_input = self._nick_input[:-1]
                        else:
                            if ev.unicode and len(self._nick_input) < 20:
                                self._nick_input += ev.unicode
                    else:
                        if ev.key == pygame.K_ESCAPE:
                            self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    cy = 120 - self.scroll
                    nr = self._nick_rect(cy)
                    if nr.collidepoint(ev.pos):
                        self._nick_editing = True
                        self._nick_cursor_t = 0.0
                    elif self.btn_back.collidepoint(ev.pos):
                        if self._nick_editing:
                            nick = self._nick_input.strip() or "Player"
                            self._nick_input = nick
                            self.save_data["player_nick"] = nick
                            from game_core import write_save as _ws
                            _ws(self.save_data)
                            self._nick_editing = False
                        else:
                            self.running = False
                    else:
                        if self._nick_editing:
                            nick = self._nick_input.strip() or "Player"
                            self._nick_input = nick
                            self.save_data["player_nick"] = nick
                            from game_core import write_save as _ws
                            _ws(self.save_data)
                            self._nick_editing = False
                if ev.type == pygame.MOUSEWHEEL:
                    if not self._nick_editing:
                        self.scroll = max(0, self.scroll - ev.y * 30)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        surf = self.screen
        mx, my = pygame.mouse.get_pos()
        _draw_menu_bg(surf, overlay_alpha=140)

        pst = self.save_data.get("profile_stats", {})
        wins   = pst.get("total_wins",   0)
        losses = pst.get("total_losses", 0)
        games  = pst.get("total_games",  0)
        waves  = pst.get("total_waves",  0)
        kills  = pst.get("total_kills",  0)

        wl_ratio  = f"{wins}/{losses}" if (wins or losses) else "—"
        wl_pct    = f"{int(wins/max(1,games)*100)}%" if games else "—"
        kd_approx = f"{kills}" if kills else "—"
        avg_waves = f"{waves//max(1,games)}" if games else "—"

        # ── Header ────────────────────────────────────────────────────────────
        hdr = pygame.Surface((SCREEN_W, 78), pygame.SRCALPHA)
        hdr.fill((8, 10, 20, 220))
        surf.blit(hdr, (0, 0))
        pygame.draw.line(surf, (45, 50, 75), (0, 78), (SCREEN_W, 78), 1)
        hf  = pygame.font.SysFont("segoeui", 38, bold=True)
        hs  = hf.render("PROFILE", True, (200, 215, 255))
        surf.blit(hs, hs.get_rect(center=(self._cx, 39)))

        cx = self._cx
        cy = 120 - self.scroll

        # ── Avatar circle ─────────────────────────────────────────────────────
        pygame.draw.circle(surf, (25, 30, 55), (cx, cy + 60), 56)
        pygame.draw.circle(surf, (70, 90, 160), (cx, cy + 60), 56, 2)
        af = pygame.font.SysFont("segoeui", 42, bold=True)
        _nick_for_av = self.save_data.get("player_nick", "Player")
        av = af.render(_nick_for_av[0].upper() if _nick_for_av else "?", True, (140, 160, 220))
        surf.blit(av, av.get_rect(center=(cx, cy + 60)))

        # ── Player nick (editable) ──────────────────────────────────────────
        nick_display = self._nick_input if self._nick_editing else self.save_data.get("player_nick", "Player")
        nr = self._nick_rect(cy)
        if self._nick_editing:
            # input box
            pygame.draw.rect(surf, (18, 22, 42), nr, border_radius=8)
            pygame.draw.rect(surf, (80, 130, 255), nr, 2, border_radius=8)
            nf2 = pygame.font.SysFont("segoeui", 24, bold=True)
            # cursor blink
            show_cur = int(self._nick_cursor_t * 2) % 2 == 0
            disp_text = nick_display + ("|" if show_cur else " ")
            ns2 = nf2.render(disp_text, True, (210, 230, 255))
            surf.blit(ns2, ns2.get_rect(center=nr.center))
            # hint
            hf2 = pygame.font.SysFont("segoeui", 13)
            hs2 = hf2.render("Enter to confirm", True, (60, 80, 140))
            surf.blit(hs2, hs2.get_rect(center=(cx, nr.bottom + 10)))
        else:
            nf = pygame.font.SysFont("segoeui", 26, bold=True)
            ns = nf.render(nick_display, True, (210, 220, 255))
            surf.blit(ns, ns.get_rect(center=(cx, cy + 137)))
            # pencil edit hint on hover
            hov_nick = nr.collidepoint(mx, my)
            if hov_nick:
                pygame.draw.rect(surf, (30, 36, 60), nr, border_radius=8)
                pygame.draw.rect(surf, (50, 70, 120), nr, 1, border_radius=8)
                surf.blit(ns, ns.get_rect(center=(cx, cy + 137)))
                ef = pygame.font.SysFont("segoeui", 13)
                es = ef.render("✏  Edit name", True, (80, 110, 200))
                surf.blit(es, es.get_rect(center=(cx, nr.bottom + 10)))

        lf  = pygame.font.SysFont("segoeui", 16)
        ls  = lf.render(f"{games} games played", True, (100, 115, 160))
        surf.blit(ls, ls.get_rect(center=(cx, cy + 158)))

        # ── Big W/L ratio card ────────────────────────────────────────────────
        card_y = cy + 188
        CARD_W, CARD_H = 860, 110
        card_rect = pygame.Rect(cx - CARD_W//2, card_y, CARD_W, CARD_H)
        cs = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        pygame.draw.rect(cs, (12, 14, 28, 240), (0, 0, CARD_W, CARD_H), border_radius=16)
        surf.blit(cs, card_rect.topleft)
        pygame.draw.rect(surf, (40, 48, 80), card_rect, 1, border_radius=16)

        # W/L big display
        wl_f  = pygame.font.SysFont("consolas", 52, bold=True)
        wl_lbl = pygame.font.SysFont("segoeui", 14, bold=True)

        col_w  = CARD_W // 4
        stats_row = [
            ("W / L",       wl_ratio,  (100, 210, 100) if wins >= losses else (210, 100, 100)),
            ("WIN RATE",    wl_pct,    (100, 180, 255)),
            ("WINS",        str(wins),  (60, 200, 120)),
            ("LOSSES",      str(losses),(200, 80, 80)),
        ]
        for si, (label, val, col) in enumerate(stats_row):
            sx = card_rect.x + col_w * si + col_w // 2
            vs = wl_f.render(val, True, col)
            surf.blit(vs, vs.get_rect(center=(sx, card_rect.y + 54)))
            lb = wl_lbl.render(label, True, (80, 90, 130))
            surf.blit(lb, lb.get_rect(center=(sx, card_rect.y + 88)))

        # ── Second stats row ──────────────────────────────────────────────────
        row2_y = card_y + CARD_H + 16
        ROW2 = [
            ("TOTAL KILLS",   kd_approx,  (255, 180, 40),  240),
            ("AVG WAVES",     avg_waves,  (120, 200, 255), 240),
            ("TOTAL WAVES",   str(waves), (160, 140, 255), 240),
        ]
        r2w = (CARD_W - 24) // 3
        for ri, (label, val, col, cw) in enumerate(ROW2):
            rx = cx - CARD_W//2 + ri * (r2w + 12)
            r2 = pygame.Rect(rx, row2_y, r2w, 88)
            rs = pygame.Surface((r2w, 88), pygame.SRCALPHA)
            pygame.draw.rect(rs, (12, 14, 28, 230), (0, 0, r2w, 88), border_radius=12)
            surf.blit(rs, r2.topleft)
            pygame.draw.rect(surf, (40, 48, 80), r2, 1, border_radius=12)
            vf2 = pygame.font.SysFont("consolas", 30, bold=True)
            vs2 = vf2.render(val, True, col)
            surf.blit(vs2, vs2.get_rect(center=(r2.centerx, r2.y + 38)))
            lb2 = pygame.font.SysFont("segoeui", 13, bold=True).render(label, True, (70, 80, 120))
            surf.blit(lb2, lb2.get_rect(center=(r2.centerx, r2.y + 68)))

        # ── Per-mode breakdown ────────────────────────────────────────────────
        sect_y = row2_y + 88 + 28
        sf  = pygame.font.SysFont("segoeui", 16, bold=True)
        sec = sf.render("STATS BY MODE", True, (100, 120, 200))
        surf.blit(sec, (cx - CARD_W//2, sect_y))
        pygame.draw.line(surf, (40, 55, 100),
                         (cx - CARD_W//2, sect_y + 22),
                         (cx + CARD_W//2, sect_y + 22), 1)

        wins_by_mode   = pst.get("wins_by_mode",   {})
        losses_by_mode = pst.get("losses_by_mode", {})
        all_modes = sorted(set(list(wins_by_mode.keys()) + list(losses_by_mode.keys())))

        if not all_modes:
            nof = pygame.font.SysFont("segoeui", 18)
            nos = nof.render("No games played yet. Go win some!", True, (70, 80, 120))
            surf.blit(nos, nos.get_rect(center=(cx, sect_y + 60)))
        else:
            tile_w = min(260, (CARD_W - (len(all_modes)-1)*12) // max(1,len(all_modes)))
            tile_h = 74
            tile_x0 = cx - (len(all_modes) * tile_w + (len(all_modes)-1)*12) // 2
            for mi, mode_key in enumerate(all_modes):
                lbl, acc = self._MODE_LABELS.get(mode_key, (mode_key.title(), (140,140,160)))
                mw = wins_by_mode.get(mode_key, 0)
                ml = losses_by_mode.get(mode_key, 0)
                mg = mw + ml
                mr = f"{mw}W / {ml}L"
                tx = tile_x0 + mi * (tile_w + 12)
                ty = sect_y + 32
                tile = pygame.Rect(tx, ty, tile_w, tile_h)
                ts2 = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
                pygame.draw.rect(ts2, (12, 14, 28, 230), (0, 0, tile_w, tile_h), border_radius=12)
                surf.blit(ts2, tile.topleft)
                pygame.draw.rect(surf, (*acc, 180), tile, 1, border_radius=12)
                mf1 = pygame.font.SysFont("segoeui", 16, bold=True)
                mf2 = pygame.font.SysFont("consolas", 18, bold=True)
                mf3 = pygame.font.SysFont("segoeui", 12)
                surf.blit(mf1.render(lbl, True, acc),
                          mf1.render(lbl, True, acc).get_rect(midleft=(tile.x + 12, tile.y + 20)))
                wl_s = mf2.render(mr, True, (200, 210, 230))
                surf.blit(wl_s, wl_s.get_rect(midleft=(tile.x + 12, tile.y + 48)))
                gm_s = mf3.render(f"{mg} games", True, (70, 80, 120))
                surf.blit(gm_s, gm_s.get_rect(midright=(tile.right - 10, tile.y + 64)))

        # ── Back button ───────────────────────────────────────────────────────
        hov  = self.btn_back.collidepoint(mx, my)
        bb   = pygame.Surface((self.btn_back.w, self.btn_back.h), pygame.SRCALPHA)
        pygame.draw.rect(bb, (70, 30, 30, 220) if hov else (40, 22, 22, 200),
                         (0, 0, self.btn_back.w, self.btn_back.h), border_radius=10)
        surf.blit(bb, self.btn_back.topleft)
        pygame.draw.rect(surf, (180, 70, 70) if hov else (100, 45, 45),
                         self.btn_back, 1, border_radius=10)
        bk_f = pygame.font.SysFont("segoeui", 22, bold=True)
        bk_s = bk_f.render("← BACK", True, (240, 200, 200) if hov else (180, 150, 150))
        surf.blit(bk_s, bk_s.get_rect(center=self.btn_back.center))


class SettingsScreen:
    _TABS = ["AUDIO", "GRAPHICS", "DISPLAY"]

    def __init__(self, screen, save_data):
        self.screen    = screen
        self.t         = 0.0
        self.running   = True
        self.save_data = save_data
        self._drag_music = False
        self._drag_sfx   = False
        self._tab        = 0
        self._tab_anim   = [0.0, 0.0, 0.0]   # hover lerp per tab
        self._toggle_hover = {}               # key -> 0..1

        cx = SCREEN_W // 2
        self._cx = cx

        # ── Tab bar ───────────────────────────────────────────────────────────
        TAB_W, TAB_H = 200, 44
        TAB_GAP      = 10
        total_tabs   = len(self._TABS) * TAB_W + (len(self._TABS) - 1) * TAB_GAP
        tab_x0       = cx - total_tabs // 2
        self._tab_rects = [
            pygame.Rect(tab_x0 + i * (TAB_W + TAB_GAP), 92, TAB_W, TAB_H)
            for i in range(len(self._TABS))
        ]

        # ── Content card ──────────────────────────────────────────────────────
        CARD_W = 960; CARD_H = 490
        self._card = pygame.Rect(cx - CARD_W // 2, 148, CARD_W, CARD_H)

        # ── Sliders (AUDIO tab) ───────────────────────────────────────────────
        SL_X = self._card.x + 72
        SL_W = self._card.w - 144
        self._bar_music = pygame.Rect(SL_X, self._card.y + 108, SL_W, 12)
        self._bar_sfx   = pygame.Rect(SL_X, self._card.y + 228, SL_W, 12)

        # ── GRAPHICS toggles ──────────────────────────────────────────────────
        self._gfx_toggles = [
            ("colored_range",     "Colored Range Rings"),
            ("screen_shake",      "Screen Shake"),
            ("particles",         "Particles & Effects"),
            ("show_damage",       "Damage / Money Numbers"),
            ("compact_numbers",   "Compact Numbers  (1k)"),
            ("show_grid",         "Show Grid"),
            ("show_fps",          "Show FPS"),
            ("show_range_always", "Always Show Range"),
            ("low_quality",       "Low Detail Mode"),
            ("unlock_fps",        "Unlock FPS"),
            ("no_tower_details",  "No Tower Details"),
            ("upgrade_preview",   "Upgrade Preview Range"),
        ]
        self._aud_toggles = [
            ("music_muted", "Mute Music"),
            ("sfx_muted",   "Mute SFX"),
        ]
        self._misc_toggles = [
            ("auto_skip",            "Auto Skip"),
            ("sell_confirm",         "Confirm Before Sell"),
            ("fast_forward_default", "Auto X2 Speed"),
            ("linux_mode",           "Linux Mode"),
        ]
        self._toggle_rects_cache = {}

        # ── DISPLAY buttons ───────────────────────────────────────────────────
        CX = self._card.centerx
        # Window mode buttons — y+78 leaves room for section header at y+30
        self.btn_windowed   = pygame.Rect(CX - 240, self._card.y + 78, 220, 48)
        self.btn_fullscreen = pygame.Rect(CX + 20,  self._card.y + 78, 220, 48)
        # Resolution buttons — y+200
        _bw = (self._card.w - 144) // len(_RESOLUTIONS)
        self._res_btns = [
            pygame.Rect(self._card.x + 72 + i * (_bw + 6), self._card.y + 200, _bw - 6, 44)
            for i in range(len(_RESOLUTIONS))
        ]
        # Style buttons — y+370
        _sw  = (self._card.w - 144 - 30) // 4
        _sx0 = self._card.x + 72
        self.btn_style_void     = pygame.Rect(_sx0,                self._card.y + 370, _sw, 48)
        self.btn_style_modern   = pygame.Rect(_sx0 + (_sw + 10),   self._card.y + 370, _sw, 48)
        self.btn_style_vertical = pygame.Rect(_sx0 + (_sw + 10)*2, self._card.y + 370, _sw, 48)
        self.btn_style_gothic   = pygame.Rect(_sx0 + (_sw + 10)*3, self._card.y + 370, _sw, 48)

        # ── Back button ───────────────────────────────────────────────────────
        self.btn_back = pygame.Rect(cx - 110, SCREEN_H - 64, 220, 44)

        # ── Linux Mode warning modal state ───────────────────────────────────
        self._linux_warn_active = False   # показывать полноэкранное предупреждение
        self._linux_warn_btn    = pygame.Rect(SCREEN_W // 2 - 140, SCREEN_H - 160, 280, 52)

    # ── Slider helpers ────────────────────────────────────────────────────────
    def _music_bar(self): return self._bar_music
    def _sfx_bar(self):   return self._bar_sfx

    def _set_music_vol(self, mx):
        bar = self._bar_music
        SETTINGS["music_volume"] = round(max(0.0, min(1.0, (mx - bar.x) / bar.w)), 2)
        if not SETTINGS["music_muted"]: _apply_audio_settings()

    def _set_sfx_vol(self, mx):
        bar = self._bar_sfx
        SETTINGS["sfx_volume"] = round(max(0.0, min(1.0, (mx - bar.x) / bar.w)), 2)

    def _toggle_rects_left(self):  return []
    def _toggle_rects_right(self): return []

    def _get_tab_toggles(self, tab_i):
        if tab_i in self._toggle_rects_cache:
            return self._toggle_rects_cache[tab_i]
        if tab_i == 0:   keys = self._aud_toggles + self._misc_toggles
        elif tab_i == 1: keys = self._gfx_toggles
        else:            return []
        usable_w = self._card.w - 144
        TW = (usable_w - 24) // 2
        TH = 46; GAP = 10
        CX = self._card.x + 72
        start_y = (self._bar_sfx.bottom + 52) if tab_i == 0 else (self._card.y + 54)
        rects = []
        for i, (k, lbl) in enumerate(keys):
            col = i % 2; row = i // 2
            x = CX + col * (TW + 24)
            y = start_y + row * (TH + GAP)
            rects.append((pygame.Rect(x, y, TW, TH), k, lbl))
        self._toggle_rects_cache[tab_i] = rects
        return rects

    # ── Event handling ────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0; self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._handle_click(ev.pos)
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    self._drag_music = False; self._drag_sfx = False
                if ev.type == pygame.MOUSEMOTION:
                    if self._drag_music: self._set_music_vol(ev.pos[0])
                    if self._drag_sfx:   self._set_sfx_vol(ev.pos[0])
            self._draw(); pygame.display.flip()
        save_settings()
        _sync_compact()

    def _handle_click(self, pos):
        # ── Linux Mode modal intercept — блокирует все клики под собой ──────────
        if self._linux_warn_active:
            if self._linux_warn_btn.collidepoint(pos):
                self._linux_warn_active = False
            return
        if self.btn_back.collidepoint(pos):
            self.running = False; return
        for i, tr in enumerate(self._tab_rects):
            if tr.collidepoint(pos):
                self._tab = i; return
        if self._tab == 0:
            bm = self._bar_music
            if pygame.Rect(bm.x, bm.y - 14, bm.w, bm.h + 28).collidepoint(pos):
                self._drag_music = True; self._set_music_vol(pos[0]); return
            bs = self._bar_sfx
            if pygame.Rect(bs.x, bs.y - 14, bs.w, bs.h + 28).collidepoint(pos):
                self._drag_sfx = True; self._set_sfx_vol(pos[0]); return
        if self._tab == 2:
            if self.btn_windowed.collidepoint(pos):
                SETTINGS["windowed"] = True; self.screen = _apply_display_mode(); return
            if self.btn_fullscreen.collidepoint(pos):
                SETTINGS["windowed"] = False; self.screen = _apply_display_mode(); return
            for i, rb in enumerate(self._res_btns):
                if rb.collidepoint(pos):
                    SETTINGS["resolution"] = _RESOLUTIONS[i]
                    self.screen = _apply_display_mode(); return
            if self.btn_style_void.collidepoint(pos):     SETTINGS["menu_style"] = 0; return
            if self.btn_style_modern.collidepoint(pos):   SETTINGS["menu_style"] = 1; return
            if self.btn_style_vertical.collidepoint(pos): SETTINGS["menu_style"] = 2; return
            if self.btn_style_gothic.collidepoint(pos):   SETTINGS["menu_style"] = 3; return
        _ARCH_KEYS = {"linux_mode"}
        for rect, key, _ in self._get_tab_toggles(self._tab):
            if rect.collidepoint(pos):
                SETTINGS[key] = not SETTINGS[key]
                if key == "music_muted": _apply_audio_settings()
                if key == "linux_mode" and SETTINGS[key]:
                    _apply_arch_linux_fix()
                    self._linux_warn_active = True
                self._toggle_rects_cache.pop(self._tab, None)
                return

    # ── Drawing helpers ───────────────────────────────────────────────────────
    def _draw_section_header(self, surf, label, color, x, y, width):
        """Draws a section label with accent bar and gradient underline."""
        # left accent bar
        bar_h = 18
        bar_s = pygame.Surface((3, bar_h), pygame.SRCALPHA)
        r, g, b = color
        for by in range(bar_h):
            a = int(255 * (1 - abs(by - bar_h / 2) / (bar_h / 2)) ** 0.5)
            pygame.draw.line(bar_s, (r, g, b, a), (0, by), (2, by))
        surf.blit(bar_s, (x, y + 1))
        # label
        f = pygame.font.SysFont("segoeui", 13, bold=True)
        s = f.render(label, True, color)
        surf.blit(s, (x + 10, y))
        # gradient underline
        line_y = y + s.get_height() + 5
        ul_s = pygame.Surface((width, 2), pygame.SRCALPHA)
        for dx in range(width):
            frac = dx / max(1, width - 1)
            a = int(160 * (1.0 - frac ** 1.2))
            pygame.draw.line(ul_s, (r, g, b, a), (dx, 0), (dx, 1))
        surf.blit(ul_s, (x, line_y))

    def _draw_slider(self, surf, bar, vol, muted, label, accent, icon=""):
        t = self.t
        # label row
        lf = pygame.font.SysFont("segoeui", 17, bold=True)
        pf = pygame.font.SysFont("consolas", 15, bold=True)
        pct_s = pf.render(f"{int(vol * 100)}%", True,
                          accent if not muted else (80, 80, 110))
        lbl_text = (icon + "  " if icon else "") + label
        ls = lf.render(lbl_text, True, (200, 210, 240) if not muted else (90, 95, 130))
        surf.blit(ls, (bar.x, bar.y - 24))
        surf.blit(pct_s, pct_s.get_rect(midright=(bar.right, bar.y - 17)))

        # track shadow
        shadow_r = pygame.Rect(bar.x + 2, bar.y + 2, bar.w, bar.h + 4)
        sh = pygame.Surface((shadow_r.w, shadow_r.h), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 60), (0, 0, shadow_r.w, shadow_r.h), border_radius=8)
        surf.blit(sh, shadow_r.topleft)

        # track background
        pygame.draw.rect(surf, (18, 20, 38), bar, border_radius=8)
        pygame.draw.rect(surf, (35, 38, 62), bar, 1, border_radius=8)

        # filled portion
        fw = max(0, int(bar.w * vol))
        if fw > 0:
            col = accent if not muted else (50, 52, 78)
            fill_r = pygame.Rect(bar.x, bar.y, fw, bar.h)
            # gradient fill
            fill_s = pygame.Surface((fw, bar.h), pygame.SRCALPHA)
            for px in range(fw):
                frac = px / max(1, fw - 1)
                r2 = int(col[0] * (0.6 + 0.4 * frac))
                g2 = int(col[1] * (0.6 + 0.4 * frac))
                b2 = int(col[2] * (0.6 + 0.4 * frac))
                pygame.draw.line(fill_s, (r2, g2, b2, 255), (px, 0), (px, bar.h - 1))
            mask_s = pygame.Surface((fw, bar.h), pygame.SRCALPHA)
            pygame.draw.rect(mask_s, (255,255,255,255), (0,0,fw,bar.h), border_radius=8)
            fill_s.blit(mask_s, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(fill_s, bar.topleft)

        # knob
        kx = bar.x + fw
        ky = bar.centery
        pulse = 0.5 + 0.5 * math.sin(t * 3.0)
        knob_col = accent if not muted else (70, 72, 100)
        # outer glow
        glow_s = pygame.Surface((36, 36), pygame.SRCALPHA)
        ga = int(60 + 30 * pulse) if not muted else 20
        pygame.draw.circle(glow_s, (*knob_col, ga), (18, 18), 16)
        surf.blit(glow_s, (kx - 18, ky - 18))
        # knob body
        pygame.draw.circle(surf, (230, 235, 255), (kx, ky), 11)
        pygame.draw.circle(surf, knob_col, (kx, ky), 11, 2)
        pygame.draw.circle(surf, (255, 255, 255), (kx, ky), 4)

    def _draw_toggle(self, surf, rect, label, active):
        mx, my = pygame.mouse.get_pos()
        hov = rect.collidepoint(mx, my)
        key = label  # use label as hover key

        # lerp hover
        if key not in self._toggle_hover:
            self._toggle_hover[key] = 0.0
        target = 1.0 if hov else 0.0
        self._toggle_hover[key] += (target - self._toggle_hover[key]) * 0.25
        h = self._toggle_hover[key]

        # background
        if active:
            r2, g2, b2 = 20, 75, 45
            brd = (50, 190, 95)
        else:
            r2 = int(22 + h * 12); g2 = int(24 + h * 12); b2 = int(42 + h * 16)
            brd = (int(55 + h * 40), int(60 + h * 40), int(90 + h * 50))

        bg_s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(bg_s, (r2, g2, b2, 215), (0, 0, rect.w, rect.h), border_radius=10)
        # subtle top highlight
        pygame.draw.rect(bg_s, (255, 255, 255, 12), (1, 1, rect.w - 2, rect.h // 2), border_radius=9)
        surf.blit(bg_s, rect.topleft)
        pygame.draw.rect(surf, brd, rect, 1, border_radius=10)

        # label
        f = pygame.font.SysFont("segoeui", 16, bold=True)
        tc = (210, 250, 220) if active else (int(120 + h * 60), int(130 + h * 60), int(165 + h * 50))
        s = f.render(label, True, tc)
        surf.blit(s, s.get_rect(midleft=(rect.x + 14, rect.centery)))

        # toggle pill
        pill_w, pill_h = 36, 18
        pill_x = rect.right - pill_w - 10
        pill_y = rect.centery - pill_h // 2
        pill_bg = (38, 175, 78) if active else (30, 32, 55)
        pygame.draw.rect(surf, pill_bg, (pill_x, pill_y, pill_w, pill_h), border_radius=9)
        dot_x = pill_x + pill_w - 11 if active else pill_x + 11
        # dot shadow
        pygame.draw.circle(surf, (0, 0, 0, 60), (dot_x + 1, pill_y + pill_h // 2 + 1), 7)
        pygame.draw.circle(surf, (255, 255, 255), (dot_x, pill_y + pill_h // 2), 7)

    def _draw_option_btn(self, surf, btn, label, active, accent, mx, my):
        """Generic option button (windowed/fullscreen/resolution/style)."""
        hov = btn.collidepoint(mx, my)
        bg_s = pygame.Surface((btn.w, btn.h), pygame.SRCALPHA)
        if active:
            pygame.draw.rect(bg_s, (*accent, 50), (0, 0, btn.w, btn.h), border_radius=11)
            surf.blit(bg_s, btn.topleft)
            pygame.draw.rect(surf, accent, btn, 2, border_radius=11)
        else:
            col = (28, 30, 54, 210) if not hov else (35, 38, 65, 220)
            pygame.draw.rect(bg_s, col, (0, 0, btn.w, btn.h), border_radius=11)
            surf.blit(bg_s, btn.topleft)
            brd = (60, 65, 100) if not hov else (90, 100, 150)
            pygame.draw.rect(surf, brd, btn, 1, border_radius=11)
        f = pygame.font.SysFont("segoeui", 17, bold=True)
        tc = (220, 240, 255) if active else (int(110 + hov * 50), int(120 + hov * 50), int(165 + hov * 50))
        s = f.render(label, True, tc)
        surf.blit(s, s.get_rect(center=btn.center))

    def _draw(self):
        surf = self.screen
        t    = self.t
        mx, my = pygame.mouse.get_pos()
        _draw_menu_bg(surf, overlay_alpha=130)

        # ── Full-screen dark overlay for depth ────────────────────────────────
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((4, 6, 16, 100))
        surf.blit(ov, (0, 0))

        cx = self._cx
        card = self._card

        # ── Header bar ────────────────────────────────────────────────────────
        hdr = pygame.Surface((SCREEN_W, 82), pygame.SRCALPHA)
        for hy in range(82):
            frac = hy / 82
            a = int(240 - 60 * frac)
            pygame.draw.line(hdr, (8, 10, 22, a), (0, hy), (SCREEN_W, hy))
        surf.blit(hdr, (0, 0))
        # header accent line
        for dx in range(SCREEN_W):
            frac = abs(dx - SCREEN_W / 2) / (SCREEN_W / 2)
            a = int(180 * (1 - frac ** 2))
            pulse = 0.5 + 0.5 * math.sin(t * 1.5)
            col_r = int(50 + 30 * pulse)
            col_g = int(80 + 40 * pulse)
            col_b = int(180 + 60 * pulse)
            pygame.draw.line(surf, (col_r, col_g, col_b, a), (dx, 81), (dx, 82))

        # title with icon
        hf  = pygame.font.SysFont("segoeui", 36, bold=True)
        hs  = hf.render("SETTINGS", True, (215, 225, 255))
        surf.blit(hs, hs.get_rect(center=(cx, 41)))

        # ── Tab bar ───────────────────────────────────────────────────────────
        _TAB_ACCENTS = [(70, 140, 255), (60, 200, 140), (160, 120, 255)]
        _TAB_ICONS   = [">>", ">>", ">>"]
        for i, (tr, lbl) in enumerate(zip(self._tab_rects, self._TABS)):
            active = (i == self._tab)
            hov    = tr.collidepoint(mx, my)
            acc    = _TAB_ACCENTS[i]

            # lerp
            target = 1.0 if (hov or active) else 0.0
            self._tab_anim[i] += (target - self._tab_anim[i]) * 0.2
            h2 = self._tab_anim[i]

            tab_s = pygame.Surface((tr.w, tr.h), pygame.SRCALPHA)
            if active:
                pygame.draw.rect(tab_s, (*acc, 45), (0, 0, tr.w, tr.h), border_radius=12)
                surf.blit(tab_s, tr.topleft)
                pygame.draw.rect(surf, acc, tr, 2, border_radius=12)
                # bottom glow strip
                glow_s = pygame.Surface((tr.w - 20, 3), pygame.SRCALPHA)
                for gx in range(tr.w - 20):
                    gfrac = abs(gx - (tr.w - 20) / 2) / ((tr.w - 20) / 2)
                    ga = int(220 * (1 - gfrac ** 2))
                    pygame.draw.line(glow_s, (*acc, ga), (gx, 0), (gx, 2))
                surf.blit(glow_s, (tr.x + 10, tr.bottom - 2))
            else:
                col2 = (int(18 + h2 * 14), int(20 + h2 * 14), int(36 + h2 * 20))
                pygame.draw.rect(tab_s, (*col2, 200), (0, 0, tr.w, tr.h), border_radius=12)
                surf.blit(tab_s, tr.topleft)
                brd2 = (int(45 + h2 * 35), int(50 + h2 * 35), int(78 + h2 * 45))
                pygame.draw.rect(surf, brd2, tr, 1, border_radius=12)

            # icon + label
            tf = pygame.font.SysFont("segoeui", 17, bold=True)
            tc = acc if active else (int(100 + h2 * 70), int(110 + h2 * 70), int(150 + h2 * 60))
            ts = tf.render(lbl, True, tc)
            surf.blit(ts, ts.get_rect(center=tr.center))

        # ── Content card ──────────────────────────────────────────────────────
        card_s = pygame.Surface((card.w, card.h), pygame.SRCALPHA)
        # layered bg
        pygame.draw.rect(card_s, (10, 12, 26, 245), (0, 0, card.w, card.h), border_radius=20)
        surf.blit(card_s, card.topleft)
        # border with tab accent tint
        acc_main = _TAB_ACCENTS[self._tab]
        pygame.draw.rect(surf, (int(35 + acc_main[0] * 0.08), int(38 + acc_main[1] * 0.06), int(65 + acc_main[2] * 0.08)), card, 1, border_radius=20)

        PAD = 72   # horizontal padding inside card
        lx  = card.x + PAD
        w_inner = card.w - PAD * 2

        # ══ AUDIO tab ═════════════════════════════════════════════════════════
        if self._tab == 0:
            acc = _TAB_ACCENTS[0]

            # Music
            self._draw_section_header(surf, "MUSIC", acc, lx, card.y + 30, w_inner)
            self._draw_slider(surf, self._bar_music,
                              SETTINGS["music_volume"], SETTINGS["music_muted"],
                              "Music Volume", acc)

            # SFX
            sfx_acc = _TAB_ACCENTS[1]
            self._draw_section_header(surf, "SOUND EFFECTS", sfx_acc, lx, card.y + 150, w_inner)
            self._draw_slider(surf, self._bar_sfx,
                              SETTINGS["sfx_volume"], SETTINGS["sfx_muted"],
                              "SFX Volume", sfx_acc)

            # Other toggles
            other_y = self._bar_sfx.bottom + 36
            misc_acc = (160, 120, 255)
            self._draw_section_header(surf, "OTHER", misc_acc, lx, other_y, w_inner)
            for rect, key, lbl in self._get_tab_toggles(0):
                self._draw_toggle(surf, rect, lbl, SETTINGS[key])

        # ══ GRAPHICS tab ══════════════════════════════════════════════════════
        elif self._tab == 1:
            acc = _TAB_ACCENTS[1]
            self._draw_section_header(surf, "VISUAL OPTIONS", acc, lx, card.y + 22, w_inner)
            for rect, key, lbl in self._get_tab_toggles(1):
                self._draw_toggle(surf, rect, lbl, SETTINGS[key])

        # ══ DISPLAY tab ═══════════════════════════════════════════════════════
        elif self._tab == 2:
            acc = _TAB_ACCENTS[2]
            is_windowed = SETTINGS.get("windowed", False)

            # Window mode
            self._draw_section_header(surf, "WINDOW MODE", acc, lx, card.y + 32, w_inner)
            for btn, label, active in [
                (self.btn_windowed,   "Windowed",  is_windowed),
                (self.btn_fullscreen, "Fullscreen", not is_windowed),
            ]:
                self._draw_option_btn(surf, btn, label, active, acc, mx, my)

            # Resolution
            self._draw_section_header(surf, "RESOLUTION", acc, lx, card.y + 158, w_inner)
            cur_res = SETTINGS.get("resolution", "1920x1080")
            for rb, res in zip(self._res_btns, _RESOLUTIONS):
                self._draw_option_btn(surf, rb, res, res == cur_res, (60, 200, 140), mx, my)

            hint_f = pygame.font.SysFont("segoeui", 13)
            hint_s = hint_f.render("Changes apply immediately. Restart may be needed.", True, (60, 68, 100))
            surf.blit(hint_s, hint_s.get_rect(center=(card.centerx, card.y + 262)))

            # Menu style
            self._draw_section_header(surf, "MENU STYLE", acc, lx, card.y + 330, w_inner)
            _STYLE_LABELS = ["Void", "Modern", "Vertical", "Gothic"]
            _style_btns   = [self.btn_style_void, self.btn_style_modern,
                             self.btn_style_vertical, self.btn_style_gothic]
            cur_style = SETTINGS.get("menu_style", 0)
            for idx2, (s_btn, s_lbl) in enumerate(zip(_style_btns, _STYLE_LABELS)):
                self._draw_option_btn(surf, s_btn, s_lbl, cur_style == idx2, acc, mx, my)

        # ── Back button ───────────────────────────────────────────────────────
        hov = self.btn_back.collidepoint(mx, my)
        bb  = pygame.Surface((self.btn_back.w, self.btn_back.h), pygame.SRCALPHA)
        r_col = (70, 22, 22, 230) if hov else (38, 18, 18, 210)
        pygame.draw.rect(bb, r_col, (0, 0, self.btn_back.w, self.btn_back.h), border_radius=11)
        pygame.draw.rect(bb, (255,255,255,10), (1,1,self.btn_back.w-2,self.btn_back.h//2), border_radius=10)
        surf.blit(bb, self.btn_back.topleft)
        brd_col = (200, 70, 70) if hov else (100, 40, 40)
        pygame.draw.rect(surf, brd_col, self.btn_back, 1, border_radius=11)
        bk_f = pygame.font.SysFont("segoeui", 20, bold=True)
        bk_s = bk_f.render("← BACK", True, (245, 200, 200) if hov else (170, 130, 130))
        surf.blit(bk_s, bk_s.get_rect(center=self.btn_back.center))

        # ── Linux Mode full-screen warning modal ─────────────────────────────
        if self._linux_warn_active:
            # ── Затемнение ────────────────────────────────────────────────────
            _dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            _dim.fill((0, 4, 12, 210))
            surf.blit(_dim, (0, 0))

            # ── Параметры карточки ────────────────────────────────────────────
            CW, CH = 620, 310
            CX = SCREEN_W // 2 - CW // 2
            CY = SCREEN_H // 2 - CH // 2

            # Фон карточки — очень тёмный, почти чёрный с лёгким синим оттенком
            _card_s = pygame.Surface((CW, CH), pygame.SRCALPHA)
            _card_s.fill((4, 10, 22, 248))
            surf.blit(_card_s, (CX, CY))

            # Внешнее свечение (несколько слоёв)
            for _gi, _ga in [(6, 18), (4, 30), (2, 55), (1, 90)]:
                pygame.draw.rect(surf, (0, 120, 220, _ga),
                                 (CX - _gi, CY - _gi, CW + _gi * 2, CH + _gi * 2), 1, border_radius=4 + _gi)
            # Основная рамка
            pygame.draw.rect(surf, (0, 160, 255), (CX, CY, CW, CH), 1, border_radius=4)

            # Тонкая верхняя полоска-акцент
            pygame.draw.line(surf, (0, 200, 255), (CX + 1, CY + 1), (CX + CW - 2, CY + 1))

            # ── Шрифты ────────────────────────────────────────────────────────
            _f_head  = pygame.font.SysFont("segoeui", 11, bold=True)
            _f_title = pygame.font.SysFont("segoeui", 30, bold=True)
            _f_body  = pygame.font.SysFont("segoeui", 15)
            _f_hint  = pygame.font.SysFont("segoeui", 13)

            # Надпись категории сверху (как в Subnautica — маленькие капсы)
            _cat = _f_head.render("SYSTEM  //  LINUX MODE", True, (0, 160, 220))
            surf.blit(_cat, _cat.get_rect(centerx=SCREEN_W // 2, top=CY + 18))

            # Горизонтальный разделитель под категорией
            pygame.draw.line(surf, (0, 80, 140), (CX + 24, CY + 36), (CX + CW - 24, CY + 36), 1)

            # Заголовок
            _title_s = _f_title.render("Совместимость не гарантирована", True, (200, 230, 255))
            surf.blit(_title_s, _title_s.get_rect(centerx=SCREEN_W // 2, top=CY + 48))

            # Основной текст — лаконично, без буллетов
            _body_lines = [
                "Режим разработан для Arch Linux + KDE Plasma + Wayland.",
                "На других системах поведение может отличаться.",
                "Для применения изменений перезапустите игру.",
            ]
            _ty = CY + 106
            for _bl in _body_lines:
                _bs = _f_body.render(_bl, True, (120, 160, 200))
                surf.blit(_bs, _bs.get_rect(centerx=SCREEN_W // 2, top=_ty))
                _ty += 26

            # Нижний разделитель
            pygame.draw.line(surf, (0, 80, 140), (CX + 24, CY + CH - 80), (CX + CW - 24, CY + CH - 80), 1)

            # ── Кнопка "Продолжить" ───────────────────────────────────────────
            btn = self._linux_warn_btn
            mx, my = pygame.mouse.get_pos()
            _hov = btn.collidepoint(mx, my)

            # Фон кнопки
            _btn_col = (0, 140, 220, 200) if _hov else (0, 80, 160, 180)
            _btn_s = pygame.Surface((btn.w, btn.h), pygame.SRCALPHA)
            _btn_s.fill(_btn_col)
            surf.blit(_btn_s, btn.topleft)
            # Рамка кнопки
            pygame.draw.rect(surf, (0, 200, 255) if _hov else (0, 120, 200), btn, 1)
            # Верхний блик
            if _hov:
                _shine = pygame.Surface((btn.w - 2, btn.h // 2), pygame.SRCALPHA)
                _shine.fill((255, 255, 255, 14))
                surf.blit(_shine, (btn.x + 1, btn.y + 1))

            _btn_lbl = _f_title.render("ПРОДОЛЖИТЬ", True, (200, 240, 255) if _hov else (140, 200, 240))
            surf.blit(_btn_lbl, _btn_lbl.get_rect(center=btn.center))

            # Подсказка под кнопкой
            _hint_s = _f_hint.render("нажмите для продолжения", True, (40, 90, 130))
            surf.blit(_hint_s, _hint_s.get_rect(centerx=SCREEN_W // 2, top=btn.bottom + 8))


# ═══════════════════════════════════════════════════════════════════════════════
# Skin system
# ═══════════════════════════════════════════════════════════════════════════════
import json as _json_mod

SKINS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skins.json")

# Skin definitions: id, unit_name, name, rarity, description
ALL_SKIN_DEFS = [
    {
        "id":        "archer_star",
        "unit_name": "Archer",
        "name":      "Star Archer",
        "rarity":    "apex",
        "desc":      "Shoots stars instead of arrows. Unique look.",
        "free":      True,   # can be claimed for free in shop
    },
    {
        "id":        "redball_true",
        "unit_name": "Red Ball",
        "name":      "True Red Ball",
        "rarity":    "rare",
        "desc":      "The legendary ball from Red Ball 4. Eyes included.",
        "price":     1000,
    },
]

def load_skins():
    """Load skins save data: {owned: [...], equipped: {unit_name: skin_id}}"""
    if os.path.exists(SKINS_FILE):
        try:
            with open(SKINS_FILE, "r") as f:
                return _json_mod.load(f)
        except: pass
    return {"owned": [], "equipped": {}}

def write_skins(data):
    try:
        with open(SKINS_FILE, "w") as f:
            _json_mod.dump(data, f)
    except: pass

def get_equipped_skin(unit_name):
    """Return skin_id equipped on unit, or None."""
    data = load_skins()
    return data.get("equipped", {}).get(unit_name)

def equip_skin(unit_name, skin_id):
    data = load_skins()
    data.setdefault("equipped", {})[unit_name] = skin_id
    write_skins(data)

def unequip_skin(unit_name):
    data = load_skins()
    data.setdefault("equipped", {}).pop(unit_name, None)
    write_skins(data)

def own_skin(skin_id):
    data = load_skins()
    return skin_id in data.get("owned", [])

def grant_skin(skin_id):
    data = load_skins()
    if skin_id not in data.get("owned", []):
        data.setdefault("owned", []).append(skin_id)
        write_skins(data)


# ── Skin Picker Screen ─────────────────────────────────────────────────────────
class SkinPickerScreen:
    """Overlay to pick a skin for a unit. Default skin shown as first card."""
    def __init__(self, screen, unit_name, skin_defs):
        self.screen    = screen
        self.unit_name = unit_name
        self.skins     = skin_defs   # only owned skins passed in
        self.running   = True
        self.t         = 0.0
        # Build full list: default first, then owned skins
        # Each entry: {"id": None = default, or skin_id, "name": ..., ...}
        self._all_options = [{"id": None, "name": "Default"}] + list(skin_defs)
        # Layout
        self._cw = 200
        self._ch = 280
        self._gap = 20
        # Panel size based on number of options
        n = len(self._all_options)
        self._pw = self._gap + n * (self._cw + self._gap)
        self._ph = 80 + self._ch + 60
        self._px = SCREEN_W // 2 - self._pw // 2
        self._py = SCREEN_H // 2 - self._ph // 2
        # Close button — top-right of panel
        self._close_r = pygame.Rect(self._px + self._pw - 44, self._py + 8, 36, 36)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._handle_click(ev.pos)
            self._draw()
            pygame.display.flip()

    def _card_rect(self, idx):
        x = self._px + self._gap + idx * (self._cw + self._gap)
        y = self._py + 56
        return pygame.Rect(x, y, self._cw, self._ch)

    def _handle_click(self, pos):
        # Close button
        if self._close_r.collidepoint(pos):
            self.running = False; return
        # Click outside panel — close
        panel = pygame.Rect(self._px, self._py, self._pw, self._ph)
        if not panel.collidepoint(pos):
            self.running = False; return
        # Card clicks
        cur = get_equipped_skin(self.unit_name)
        for i, opt in enumerate(self._all_options):
            if self._card_rect(i).collidepoint(pos):
                if opt["id"] is None:
                    unequip_skin(self.unit_name)
                else:
                    if cur == opt["id"]:
                        unequip_skin(self.unit_name)
                    else:
                        equip_skin(self.unit_name, opt["id"])
                self.running = False; return

    def _draw(self):
        surf = self.screen
        t    = self.t
        # Dim background
        dim = _get_dim_surf(); dim.fill((0, 0, 0, 210))
        surf.blit(dim, (0, 0))

        px2, py2 = self._px, self._py
        pw, ph   = self._pw, self._ph
        cx = px2 + pw // 2

        # Panel
        draw_rect_alpha(surf, (16, 20, 34), (px2, py2, pw, ph), 248, 18)
        pygame.draw.rect(surf, (80, 140, 220), pygame.Rect(px2, py2, pw, ph), 2, border_radius=18)

        # Title
        tf = pygame.font.SysFont("segoeui", 22, bold=True)
        ts = tf.render(f"Skins: {self.unit_name}", True, (200, 220, 255))
        surf.blit(ts, ts.get_rect(center=(cx, py2 + 28)))

        # Close button
        mx2, my2 = pygame.mouse.get_pos()
        c_hov = self._close_r.collidepoint(mx2, my2)
        pygame.draw.rect(surf, (120, 40, 40) if c_hov else (70, 30, 30), self._close_r, border_radius=7)
        pygame.draw.rect(surf, (200, 80, 80), self._close_r, 2, border_radius=7)
        xs = pygame.font.SysFont("consolas", 18, bold=True).render("✕", True, (240, 120, 120))
        surf.blit(xs, xs.get_rect(center=self._close_r.center))

        cur_eq = get_equipped_skin(self.unit_name)

        for i, opt in enumerate(self._all_options):
            card = self._card_rect(i)
            cx3, cy3 = card.x, card.y
            cw2, ch2 = self._cw, self._ch
            is_default = (opt["id"] is None)
            is_eq = (cur_eq is None) if is_default else (cur_eq == opt["id"])

            # Card background
            if is_default:
                bg_col = (30, 38, 55)
                brd_col = (255, 220, 50) if is_eq else (80, 100, 140)
            else:
                rd2 = RARITY_DATA.get(opt.get("rarity", "early_access"), RARITY_DATA["early_access"])
                bg_col = rd2["color"]
                brd_col = (255, 220, 50) if is_eq else rd2["border"]

            card_s = pygame.Surface((cw2, ch2), pygame.SRCALPHA)
            pygame.draw.rect(card_s, (*bg_col, 230), (0, 0, cw2, ch2), border_radius=14)
            surf.blit(card_s, (cx3, cy3))
            pygame.draw.rect(surf, brd_col, card, 3 if is_eq else 2, border_radius=14)

            # Preview area
            pcx = cx3 + cw2 // 2
            pcy = cy3 + 100

            if is_default:
                # Default — show plain unit circle
                _col_map2 = {
                    "Archer": C_ARCHER, "Assassin": C_ASSASSIN,
                    "Accelerator": C_ACCEL, "Lifestealer": C_LIFESTEALER,
                }
                uc = _col_map2.get(self.unit_name, (120, 120, 160))
                pygame.draw.circle(surf, (20, 15, 35), (pcx, pcy), 38)
                pygame.draw.circle(surf, uc, (pcx, pcy), 30)
                pygame.draw.circle(surf, (255, 255, 255), (pcx, pcy), 30, 2)
                df2 = pygame.font.SysFont("segoeui", 13)
                ds3 = df2.render("default", True, (140, 150, 180))
                surf.blit(ds3, ds3.get_rect(center=(pcx, pcy + 48)))
            elif opt["id"] == "archer_star":
                # Star Archer preview
                pygame.draw.circle(surf, (30, 20, 50), (pcx, pcy), 38)
                pygame.draw.circle(surf, (200, 160, 40), (pcx, pcy), 30)
                pygame.draw.circle(surf, (255, 220, 80), (pcx, pcy), 20)
                for si3 in range(5):
                    sa3 = math.radians(t * 100 + si3 * 72)
                    ssx2 = pcx + int(math.cos(sa3) * 38)
                    ssy2 = pcy + int(math.sin(sa3) * 38)
                    # mini star
                    spts = []
                    for pi2 in range(10):
                        r2 = 5 if pi2 % 2 == 0 else 2
                        a2 = math.radians(-90 + pi2 * 36)
                        spts.append((ssx2 + int(math.cos(a2)*r2), ssy2 + int(math.sin(a2)*r2)))
                    pygame.draw.polygon(surf, (255, 220, 60), spts)

            # Name
            nf2 = pygame.font.SysFont("segoeui", 16, bold=True)
            ns2 = nf2.render(opt["name"], True, C_WHITE)
            surf.blit(ns2, ns2.get_rect(center=(pcx, cy3 + ch2 - 52)))

            # Status label
            if is_eq:
                st_lbl = "✓ SELECTED"
                st_col = (100, 255, 120)
            else:
                st_lbl = "click to select"
                st_col = (130, 140, 170)
            stf2 = pygame.font.SysFont("segoeui", 12)
            sts3 = stf2.render(st_lbl, True, st_col)
            surf.blit(sts3, sts3.get_rect(center=(pcx, cy3 + ch2 - 30)))

            # Hover highlight
            if card.collidepoint(mx2, my2):
                hov_s = pygame.Surface((cw2, ch2), pygame.SRCALPHA)
                pygame.draw.rect(hov_s, (255, 255, 255, 18), (0, 0, cw2, ch2), border_radius=14)
                surf.blit(hov_s, (cx3, cy3))


# ── Shop Screen ────────────────────────────────────────────────────────────────
class ShopScreen:
    """Shop with tabs: Skins, Currency Exchange."""

    SHARD_TO_COINS = 50   # 1 shard = 50 coins

    def __init__(self, screen, save_data):
        self.screen    = screen
        self.save_data = save_data
        self.t         = 0.0
        self.running   = True
        self.msg       = ""
        self.msg_timer = 0.0
        self.btn_back  = pygame.Rect(20, 20, 130, 44)

        # Tabs: 0 = Skins, 1 = Exchange, 2 = Passes
        self.active_tab = 0
        tab_labels = ["🎨  SKINS", "💱  EXCHANGE", "🎫  PASSES"]
        tab_w, tab_h = 200, 40
        tab_start_x = SCREEN_W // 2 - (len(tab_labels) * tab_w + (len(tab_labels)-1)*8) // 2
        self.tab_rects  = []
        self.tab_labels = tab_labels
        for i in range(len(tab_labels)):
            self.tab_rects.append(pygame.Rect(tab_start_x + i*(tab_w+8), 76, tab_w, tab_h))

        # Exchange state
        self._ex_input   = ["", ""]
        self._ex_active  = [False, False]
        self._ex_input_r = [pygame.Rect(0,0,0,0), pygame.Rect(0,0,0,0)]
        self._ex_btn_r   = [pygame.Rect(0,0,0,0), pygame.Rect(0,0,0,0)]

    # ──────────────────────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self.msg_timer > 0:
                self.msg_timer -= dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if any(self._ex_active):
                            self._ex_active = [False, False]
                        else:
                            self.running = False
                    else:
                        self._handle_key(ev)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._handle_click(ev.pos)
            self._draw()
            pygame.display.flip()

    def _handle_key(self, ev):
        for i in range(2):
            if not self._ex_active[i]:
                continue
            if ev.key == pygame.K_RETURN:
                self._do_exchange(i)
                self._ex_active[i] = False
            elif ev.key == pygame.K_BACKSPACE:
                self._ex_input[i] = self._ex_input[i][:-1]
            elif ev.unicode.isdigit() and len(self._ex_input[i]) < 9:
                self._ex_input[i] += ev.unicode

    def _handle_click(self, pos):
        if self.btn_back.collidepoint(pos):
            self.running = False
            return
        for i, r in enumerate(self.tab_rects):
            if r.collidepoint(pos):
                self.active_tab = i
                self._ex_active = [False, False]
                return
        if self.active_tab == 0:
            self._handle_skins_click(pos)
        elif self.active_tab == 1:
            self._handle_exchange_click(pos)
        else:
            self._handle_passes_click(pos)

    def _handle_skins_click(self, pos):
        for i, skin in enumerate(ALL_SKIN_DEFS):
            btn = self._skin_btn_rect(i)
            if btn and btn.collidepoint(pos):
                if own_skin(skin["id"]):
                    cur = get_equipped_skin(skin["unit_name"])
                    if cur == skin["id"]:
                        unequip_skin(skin["unit_name"])
                        self.msg = f"Unequipped {skin['name']}"
                    else:
                        equip_skin(skin["unit_name"], skin["id"])
                        self.msg = f"Equipped {skin['name']}!"
                elif skin.get("free"):
                    grant_skin(skin["id"])
                    equip_skin(skin["unit_name"], skin["id"])
                    self.msg = f"Skin {skin['name']} unlocked and equipped!"
                elif skin.get("price"):
                    price = skin["price"]
                    coins = self.save_data.get("coins", 0)
                    if coins >= price:
                        self.save_data["coins"] = coins - price
                        write_save(self.save_data)
                        grant_skin(skin["id"])
                        equip_skin(skin["unit_name"], skin["id"])
                        self.msg = f"Purchased {skin['name']}!"
                    else:
                        self.msg = f"Not enough coins! Need {price}."
                else:
                    self.msg = "Skin unavailable"
                self.msg_timer = 2.5

    def _handle_exchange_click(self, pos):
        for i in range(2):
            if self._ex_input_r[i].collidepoint(pos):
                self._ex_active = [False, False]
                self._ex_active[i] = True
                return
            if self._ex_btn_r[i].collidepoint(pos):
                self._do_exchange(i)
                return
        self._ex_active = [False, False]

    def _do_exchange(self, direction):
        raw = self._ex_input[direction].strip()
        if not raw or not raw.isdigit():
            self.msg = "Enter a valid amount!"; self.msg_timer = 2.0; return
        amount = int(raw)
        if amount <= 0:
            self.msg = "Amount must be > 0!"; self.msg_timer = 2.0; return
        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)
        rate   = self.SHARD_TO_COINS
        if direction == 0:
            cost = amount * rate
            if coins < cost:
                self.msg = f"Need {fmt_num(cost)} coins! (you have {fmt_num(coins)})"; self.msg_timer = 3.0; return
            self.save_data["coins"]  = coins  - cost
            self.save_data["shards"] = shards + amount
            self.msg = f"Exchanged {fmt_num(cost)} coins -> +{fmt_num(amount)} shards!"
        else:
            if shards < amount:
                self.msg = f"Need {fmt_num(amount)} shards! (you have {fmt_num(shards)})"; self.msg_timer = 3.0; return
            self.save_data["shards"] = shards - amount
            self.save_data["coins"]  = coins  + amount * rate
            self.msg = f"Exchanged {fmt_num(amount)} shards -> +{fmt_num(amount*rate)} coins!"
        write_save(self.save_data)
        self._ex_input[direction] = ""
        self.msg_timer = 3.0

    def _handle_passes_click(self, pos):
        EA_PRICE = 50000
        for pass_id, btn in getattr(self, '_pass_buy_btns', []):
            if btn and btn.collidepoint(pos):
                coins = self.save_data.get("coins", 0)
                if pass_id == "early_access":
                    if self.save_data.get("early_access_purchased", False):
                        self.msg = "Early Access already owned!"; self.msg_timer = 2.5
                    elif coins >= EA_PRICE:
                        self.save_data["coins"] = coins - EA_PRICE
                        self.save_data["early_access_purchased"] = True
                        write_save(self.save_data)
                        self.msg = "Early Access purchased!"
                        self.msg_timer = 3.0
                    else:
                        self.msg = f"Need {fmt_num(EA_PRICE)} coins!"
                        self.msg_timer = 2.5
                return

    # ── Pass definitions ──────────────────────────────────────────────────────
    _PASSES = [
        {
            "id":       "early_access",
            "name":     "Early Access",
            "subtitle": "Get access to Early Access content",
            "price":    50000,
            "currency": "coins",
            "color":    (20,  80,  65),
            "border":   (60, 220, 180),
            "text":     (60, 220, 180),
            "shimmer":  (120, 255, 220),
            "icon":     "🔓",
            "perks": [
                "Access to future EA-exclusive towers",
                "Early preview of new content",
            ],
            "owned_key": "early_access_purchased",
        },
    ]

    def _draw_passes(self, surf, t, cx, mx, my):
        self._pass_buy_btns = []

        # Section title
        tf5 = pygame.font.SysFont("segoeui", 22, bold=True)
        ts5 = tf5.render("Choose a Pass to unlock exclusive content and perks.", True, (140, 150, 170))
        surf.blit(ts5, ts5.get_rect(center=(cx, 132)))

        card_w, card_h = 380, 380
        n_passes = len(self._PASSES)
        total_w  = n_passes * card_w + (n_passes - 1) * 28
        start_x  = cx - total_w // 2
        card_y   = 158

        for i, p in enumerate(self._PASSES):
            cx2 = start_x + i * (card_w + 28)
            cr  = pygame.Rect(cx2, card_y, card_w, card_h)

            owned = bool(p["owned_key"] and self.save_data.get(p["owned_key"], False))
            coming_soon = p["price"] is None

            # Card background
            card_s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_alpha = 240 if (not coming_soon) else 160
            pygame.draw.rect(card_s, (*p["color"], bg_alpha), (0, 0, card_w, card_h), border_radius=18)

            # Border — gold if owned, normal otherwise
            brd = (220, 180, 40) if owned else p["border"]
            brd_w = 3 if (owned or not coming_soon) else 1
            pygame.draw.rect(card_s, (*brd, 255), (0, 0, card_w, card_h), brd_w, border_radius=18)

            # Shimmer scan line
            if not coming_soon:
                scan = int((t * 70 + i * 40) % (card_h + 40)) - 20
                sh_s = pygame.Surface((card_w, 3), pygame.SRCALPHA)
                sh_s.fill((*p["shimmer"], 50))
                card_s.blit(sh_s, (0, scan))

            surf.blit(card_s, (cx2, card_y))

            # "COMING SOON" overlay
            if coming_soon:
                ov = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 100))
                pygame.draw.rect(ov, (0,0,0,0), (0, 0, card_w, card_h), border_radius=18)
                surf.blit(ov, (cx2, card_y))
                cs_f = pygame.font.SysFont("segoeui", 22, bold=True)
                cs_s = cs_f.render("COMING SOON", True, (120, 120, 140))
                surf.blit(cs_s, cs_s.get_rect(center=(cx2 + card_w // 2, card_y + card_h // 2)))

            # Icon + Name
            icon_f = pygame.font.SysFont("segoeui", 36, bold=True)
            icon_s = icon_f.render(p["icon"], True, p["text"])
            surf.blit(icon_s, icon_s.get_rect(center=(cx2 + card_w // 2, card_y + 36)))

            name_f = pygame.font.SysFont("segoeui", 26, bold=True)
            name_col = (255, 220, 80) if owned else p["text"]
            name_s = name_f.render(("✓ " if owned else "") + p["name"], True, name_col)
            surf.blit(name_s, name_s.get_rect(center=(cx2 + card_w // 2, card_y + 76)))

            sub_f = pygame.font.SysFont("segoeui", 15)
            sub_col = (160, 200, 180) if not coming_soon else (90, 95, 110)
            sub_s = sub_f.render(p["subtitle"], True, sub_col)
            surf.blit(sub_s, sub_s.get_rect(center=(cx2 + card_w // 2, card_y + 102)))

            # Separator
            pygame.draw.line(surf, (*p["border"], 180) if not coming_soon else (60, 65, 80),
                             (cx2 + 16, card_y + 118), (cx2 + card_w - 16, card_y + 118), 1)

            # Perks list
            perk_f = pygame.font.SysFont("segoeui", 15)
            for j, perk in enumerate(p["perks"]):
                pc = p["text"] if not coming_soon else (80, 85, 100)
                perk_s = perk_f.render(f"  ✦  {perk}", True, pc)
                surf.blit(perk_s, (cx2 + 18, card_y + 130 + j * 26))

            # Price / buy button
            btn_y = card_y + card_h - 62
            if owned:
                ok_f = pygame.font.SysFont("segoeui", 17, bold=True)
                ok_s = ok_f.render("✓  Owned", True, (80, 240, 140))
                surf.blit(ok_s, ok_s.get_rect(center=(cx2 + card_w // 2, btn_y + 20)))
            elif not coming_soon:
                coins = self.save_data.get("coins", 0)
                can_buy = coins >= p["price"]
                btn_r = pygame.Rect(cx2 + 20, btn_y, card_w - 40, 48)
                hov5 = btn_r.collidepoint(mx, my)
                if can_buy:
                    pulse5 = abs(math.sin(t * 2.5))
                    r5 = int(p["color"][0] + 20 + pulse5 * 15)
                    g5 = int(p["color"][1] + 40 + pulse5 * 30)
                    b5 = int(p["color"][2] + 20 + pulse5 * 10)
                    bg5 = (min(255,r5 + (20 if hov5 else 0)),
                           min(255,g5 + (20 if hov5 else 0)),
                           min(255,b5 + (20 if hov5 else 0)))
                    bd5 = p["shimmer"] if hov5 else p["border"]
                else:
                    bg5 = (50, 28, 28)
                    bd5 = (130, 55, 55)
                pygame.draw.rect(surf, bg5, btn_r, border_radius=10)
                pygame.draw.rect(surf, bd5, btn_r, 2, border_radius=10)

                bf5 = pygame.font.SysFont("segoeui", 18, bold=True)
                ico_c3 = load_icon("coin_ico", 18)
                if can_buy:
                    price_str = f"  {fmt_num(p['price'])} coins"
                    buy_lbl = "PURCHASE"
                else:
                    price_str = f"  Need {fmt_num(p['price'] - coins)} more"
                    buy_lbl = price_str
                # Draw icon + price inside button
                btn_text = bf5.render(f"{fmt_num(p['price'])} coins", True,
                                       C_GOLD if can_buy else (150, 80, 80))
                ico_surf = ico_c3
                tw5 = (ico_surf.get_width() + 4 if ico_surf else 0) + btn_text.get_width()
                bx5 = btn_r.centerx - tw5 // 2
                if ico_surf:
                    surf.blit(ico_surf, (bx5, btn_r.centery - 9))
                    surf.blit(btn_text, (bx5 + ico_surf.get_width() + 4,
                                         btn_r.centery - btn_text.get_height() // 2))
                else:
                    surf.blit(btn_text, btn_text.get_rect(center=btn_r.center))
                self._pass_buy_btns.append((p["id"], btn_r))

    def _skin_btn_rect(self, idx):
        cx = SCREEN_W // 2
        card_w, card_h = 320, 420
        x = cx - card_w // 2
        y = 130 + idx * (card_h + 20)
        return pygame.Rect(x + card_w // 2 - 110, y + card_h - 56, 220, 44)

    # ── Draw ────────────────────────────────────────────────────────────────
    def _draw(self):
        surf = self.screen
        surf.fill((8, 10, 18))
        t  = self.t
        cx = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()

        # Stars background
        random.seed(55)
        for i in range(220):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(t * 0.7 + i * 0.4)) * 120 + 40)
            pygame.draw.circle(surf, (br, br, min(255, br + 40)), (sx, sy), 1)
        random.seed()

        # Header bar
        pygame.draw.rect(surf, (14, 18, 32), (0, 0, SCREEN_W, 70))
        pygame.draw.line(surf, C_BORDER, (0, 70), (SCREEN_W, 70), 2)
        hf = pygame.font.SysFont("segoeui", 36, bold=True)
        hs = hf.render("SHOP", True, (255, 200, 80))
        surf.blit(hs, hs.get_rect(center=(cx, 35)))

        # Back button
        hov_b = self.btn_back.collidepoint(mx, my)
        pygame.draw.rect(surf, (110, 50, 50) if hov_b else (80, 40, 40), self.btn_back, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_back, 2, border_radius=8)
        txt(surf, "<- BACK", self.btn_back.center, C_WHITE, font_md, center=True)

        # Currency HUD
        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)
        _hud_f = pygame.font.SysFont("segoeui", 20, bold=True)
        ico_coin = load_icon("coin_ico", 28)
        coin_s   = _hud_f.render(f"  {fmt_num(coins)}", True, C_WHITE)
        cw2 = (ico_coin.get_width() if ico_coin else 0) + coin_s.get_width() + 16
        coin_bg = pygame.Rect(SCREEN_W - cw2 - 12, 8, cw2, 34)
        draw_rect_alpha(surf, (20, 20, 10), (coin_bg.x, coin_bg.y, coin_bg.w, coin_bg.h), 170, 8)
        pygame.draw.rect(surf, (160, 120, 20), coin_bg, 1, border_radius=8)
        if ico_coin:
            surf.blit(ico_coin, (coin_bg.x + 8, coin_bg.y + (34 - ico_coin.get_height()) // 2))
            surf.blit(coin_s, (coin_bg.x + 8 + ico_coin.get_width(), coin_bg.y + (34 - coin_s.get_height()) // 2))
        else:
            surf.blit(_hud_f.render(f"Coin {fmt_num(coins)}", True, C_WHITE), (coin_bg.x + 8, coin_bg.y + 7))
        ico_sh  = load_icon("shard_ico", 24)
        shard_s = _hud_f.render(f"  {fmt_num(shards)}", True, C_WHITE)
        sw2 = (ico_sh.get_width() if ico_sh else 0) + shard_s.get_width() + 16
        shard_bg = pygame.Rect(coin_bg.x - sw2 - 8, 8, sw2, 34)
        draw_rect_alpha(surf, (5, 20, 30), (shard_bg.x, shard_bg.y, shard_bg.w, shard_bg.h), 170, 8)
        pygame.draw.rect(surf, (40, 120, 180), shard_bg, 1, border_radius=8)
        if ico_sh:
            surf.blit(ico_sh, (shard_bg.x + 8, shard_bg.y + (34 - ico_sh.get_height()) // 2))
            surf.blit(shard_s, (shard_bg.x + 8 + ico_sh.get_width(), shard_bg.y + (34 - shard_s.get_height()) // 2))
        else:
            surf.blit(_hud_f.render(f"Shard {fmt_num(shards)}", True, (100, 200, 255)), (shard_bg.x + 8, shard_bg.y + 7))

        # Tabs
        tab_colors = [
            ((255, 200, 80),  (255, 180, 30),  (50, 38, 8)),
            ((80,  200, 255), (40,  160, 220), (8,  28, 45)),
            ((60,  220, 180), (20,  140, 110), (5,  30, 22)),
        ]
        tf2 = pygame.font.SysFont("segoeui", 18, bold=True)
        for i, (r, lbl) in enumerate(zip(self.tab_rects, self.tab_labels)):
            active = (i == self.active_tab)
            tc, tc2, bg = tab_colors[i]
            hov_t = r.collidepoint(mx, my)
            fill = bg if not active else tuple(min(255, c+10) for c in bg)
            if hov_t and not active:
                fill = tuple(min(255, c+15) for c in fill)
            pygame.draw.rect(surf, fill, r, border_radius=10)
            border_c = tc if active else (60, 70, 90)
            pygame.draw.rect(surf, border_c, r, 3 if active else 2, border_radius=10)
            if active:
                gw_s = pygame.Surface((r.w, 4), pygame.SRCALPHA)
                gw_s.fill((*tc, 180))
                surf.blit(gw_s, (r.x, r.bottom - 4))
            ts3 = tf2.render(lbl, True, tc if active else (160, 170, 190))
            surf.blit(ts3, ts3.get_rect(center=r.center))

        # Tab content
        if self.active_tab == 0:
            self._draw_skins(surf, t, cx, mx, my)
        elif self.active_tab == 1:
            self._draw_exchange(surf, t, cx, mx, my)
        else:
            self._draw_passes(surf, t, cx, mx, my)

        # Toast message
        if self.msg_timer > 0:
            alpha = min(255, int(self.msg_timer * 160))
            ms = pygame.font.SysFont("segoeui", 22, bold=True).render(self.msg, True, (255, 220, 80))
            bg_s = pygame.Surface((ms.get_width() + 32, 40), pygame.SRCALPHA)
            pygame.draw.rect(bg_s, (0, 0, 0, min(200, alpha)), (0, 0, bg_s.get_width(), bg_s.get_height()), border_radius=10)
            surf.blit(bg_s, bg_s.get_rect(center=(cx, SCREEN_H - 48)))
            ms.set_alpha(alpha)
            surf.blit(ms, ms.get_rect(center=(cx, SCREEN_H - 48)))

    def _draw_skins(self, surf, t, cx, mx, my):
        card_w, card_h = 320, 420
        n = len(ALL_SKIN_DEFS)
        cols = min(n, max(1, (SCREEN_W - 80) // (card_w + 30)))
        total_w = cols * card_w + (cols - 1) * 24
        start_x = cx - total_w // 2
        start_y = 132

        for i, skin in enumerate(ALL_SKIN_DEFS):
            col = i % cols
            row = i // cols
            x = start_x + col * (card_w + 24)
            y = start_y + row * (card_h + 20)
            is_owned    = own_skin(skin["id"])
            is_equipped = (get_equipped_skin(skin["unit_name"]) == skin["id"])
            rarity = skin["rarity"]
            rd = RARITY_DATA.get(rarity, RARITY_DATA["early_access"])

            card_s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_s, (*rd["color"], 230), (0, 0, card_w, card_h), border_radius=18)
            brd_col = (255, 220, 50) if is_equipped else rd["border"]
            pygame.draw.rect(card_s, (*brd_col, 255), (0, 0, card_w, card_h), 3, border_radius=18)
            surf.blit(card_s, (x, y))

            badge_f = pygame.font.SysFont("consolas", 14, bold=True)
            if rarity == "apex":
                bs2 = _render_gradient_text(rarity.upper(), badge_f, _APEX_GRAD_COLORS)
            else:
                bs2 = badge_f.render(rarity.upper(), True, rd["text_col"])
            bsw2 = bs2.get_width() + 14
            badge_r2 = pygame.Rect(x + card_w - bsw2 - 8, y + 8, bsw2, 24)
            draw_rect_alpha(surf, rd["color"], (badge_r2.x, badge_r2.y, badge_r2.w, badge_r2.h), 220, 6)
            pygame.draw.rect(surf, rd["border"], badge_r2, 1, border_radius=6)
            surf.blit(bs2, (badge_r2.x + 7, badge_r2.y + 4))

            preview_cx = x + card_w // 2
            preview_cy = y + 160
            if skin["id"] == "archer_star":
                pygame.draw.circle(surf, (30, 20, 50),    (preview_cx, preview_cy), 44)
                pygame.draw.circle(surf, (200, 160, 40),  (preview_cx, preview_cy), 36)
                pygame.draw.circle(surf, (255, 220, 80),  (preview_cx, preview_cy), 28)
                pygame.draw.circle(surf, (255, 255, 160), (preview_cx, preview_cy), 18)
                for si in range(5):
                    sa2 = math.radians(t * 90 + si * 72)
                    sx2 = preview_cx + int(math.cos(sa2) * 40)
                    sy2 = preview_cy + int(math.sin(sa2) * 40)
                    star_pts = []
                    for pi2 in range(10):
                        r2 = 7 if pi2 % 2 == 0 else 3
                        a2 = math.radians(-90 + pi2 * 36 + t * 90 + si * 72)
                        star_pts.append((sx2 + int(math.cos(a2) * r2), sy2 + int(math.sin(a2) * r2)))
                    pygame.draw.polygon(surf, (255, 220, 60), star_pts)
                    pygame.draw.polygon(surf, (255, 255, 160), star_pts, 1)
                bow_a = math.radians(t * 30)
                bx2 = preview_cx + int(math.cos(bow_a) * 28)
                by2 = preview_cy + int(math.sin(bow_a) * 28)
                pygame.draw.line(surf, (200, 160, 40), (preview_cx, preview_cy), (bx2, by2), 3)
                pygame.draw.circle(surf, (255, 240, 100), (bx2, by2), 5)
            elif skin["id"] == "redball_true":
                _bob = math.sin(t * 2.5) * 6
                pcx, pcy = preview_cx, int(preview_cy + _bob)
                shadow_s = pygame.Surface((80, 20), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_s, (0, 0, 0, 60), (0, 0, 80, 20))
                surf.blit(shadow_s, (pcx - 40, preview_cy + 42))
                pygame.draw.circle(surf, (160, 10, 10),  (pcx, pcy), 46)
                pygame.draw.circle(surf, (220, 30, 30),  (pcx, pcy), 42)
                hl_s = pygame.Surface((84, 84), pygame.SRCALPHA)
                pygame.draw.circle(hl_s, (255, 80, 80, 120), (28, 28), 28)
                surf.blit(hl_s, (pcx - 42, pcy - 42))
                pygame.draw.circle(surf, (255, 160, 160), (pcx - 14, pcy - 16), 9)
                pygame.draw.circle(surf, (255, 220, 220), (pcx - 16, pcy - 18), 4)
                pygame.draw.circle(surf, (255, 255, 255), (pcx - 14, pcy - 4), 11)
                pygame.draw.circle(surf, (255, 255, 255), (pcx + 12, pcy - 4), 11)
                pygame.draw.circle(surf, (30, 20, 10),   (pcx - 11, pcy - 4), 6)
                pygame.draw.circle(surf, (30, 20, 10),   (pcx + 15, pcy - 4), 6)
                pygame.draw.circle(surf, (255, 255, 255), (pcx - 9,  pcy - 7), 2)
                pygame.draw.circle(surf, (255, 255, 255), (pcx + 17, pcy - 7), 2)
                smile_rect = pygame.Rect(pcx - 16, pcy + 8, 32, 20)
                pygame.draw.arc(surf, (160, 10, 10), smile_rect, math.radians(200), math.radians(340), 3)
                for bx_off, by_off in [(-22, 6), (22, 6)]:
                    blush = pygame.Surface((14, 8), pygame.SRCALPHA)
                    pygame.draw.ellipse(blush, (255, 120, 120, 100), (0, 0, 14, 8))
                    surf.blit(blush, (pcx + bx_off - 7, pcy + by_off))

            nf = pygame.font.SysFont("segoeui", 22, bold=True)
            ns = nf.render(skin["name"], True, C_WHITE)
            surf.blit(ns, ns.get_rect(center=(preview_cx, y + 290)))
            df = pygame.font.SysFont("segoeui", 14)
            ds = df.render(skin["desc"], True, (200, 195, 220))
            surf.blit(ds, ds.get_rect(center=(preview_cx, y + 316)))
            uf = pygame.font.SysFont("segoeui", 13)
            if rarity == "apex":
                us = _render_gradient_text(f"Unit: {skin['unit_name']}", uf, _APEX_GRAD_COLORS)
            else:
                us = uf.render(f"Unit: {skin['unit_name']}", True, rd["text_col"])
            surf.blit(us, us.get_rect(center=(preview_cx, y + 336)))

            btn = pygame.Rect(x + card_w // 2 - 110, y + card_h - 56, 220, 44)
            if is_equipped:
                btn_col = (20, 80, 20);   btn_brd = (80, 220, 80);   btn_lbl = "EQUIPPED"
            elif is_owned:
                btn_col = (30, 50, 100);  btn_brd = (80, 140, 255);  btn_lbl = "EQUIP"
            elif skin.get("free"):
                btn_col = (80, 50, 0);    btn_brd = (255, 180, 40);  btn_lbl = "CLAIM FOR FREE"
            elif skin.get("price"):
                btn_col = (60, 45, 0);    btn_brd = (220, 170, 30);  btn_lbl = f"BUY  {skin['price']} coins"
            else:
                btn_col = (50, 30, 60);   btn_brd = (140, 80, 180);  btn_lbl = "LOCKED"
            if btn.collidepoint(mx, my):
                btn_col = tuple(min(255, c + 30) for c in btn_col)
            pygame.draw.rect(surf, btn_col, btn, border_radius=10)
            pygame.draw.rect(surf, btn_brd, btn, 2, border_radius=10)
            bf2 = pygame.font.SysFont("segoeui", 17, bold=True)
            bs3 = bf2.render(btn_lbl, True, C_WHITE)
            surf.blit(bs3, bs3.get_rect(center=btn.center))
            if is_equipped:
                eq_s = pygame.font.SysFont("consolas", 11, bold=True).render("EQUIPPED", True, (255, 240, 80))
                surf.blit(eq_s, eq_s.get_rect(center=(preview_cx, y + 362)))

    def _draw_exchange(self, surf, t, cx, mx, my):
        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)
        rate   = self.SHARD_TO_COINS

        card_w, card_h = 420, 330
        gap     = 60
        total_w = card_w * 2 + gap
        start_x = cx - total_w // 2
        start_y = 148

        title_f = pygame.font.SysFont("segoeui",  22, bold=True)
        rate_f  = pygame.font.SysFont("consolas", 14)
        input_f = pygame.font.SysFont("consolas", 24, bold=True)
        btn_f   = pygame.font.SysFont("segoeui",  18, bold=True)
        label_f = pygame.font.SysFont("segoeui",  15)
        bal_f   = pygame.font.SysFont("segoeui",  15)

        configs = [
            {
                "title":      "Coins  ->  Shards",
                "color":      (255, 200, 60),
                "bg":         (28, 24, 8),
                "border":     (200, 160, 20),
                "rate_txt":   f"Rate:  1 shard  =  {rate} coins",
                "input_lbl":  "Shards to receive:",
                "bal_lbl":    f"Your coins:  {fmt_num(coins)}",
                "preview_fn": lambda amt: f"Cost: {fmt_num(amt * rate)} coins  +  {fmt_num(amt)} shards",
                "btn_lbl":    "Exchange -> Shards",
            },
            {
                "title":      "Shards  ->  Coins",
                "color":      (80, 200, 255),
                "bg":         (6, 20, 34),
                "border":     (40, 140, 200),
                "rate_txt":   f"Rate:  1 shard  =  {rate} coins",
                "input_lbl":  "Shards to spend:",
                "bal_lbl":    f"Your shards:  {fmt_num(shards)}",
                "preview_fn": lambda amt: f"Spend: {fmt_num(amt)} shards  +  {fmt_num(amt * rate)} coins",
                "btn_lbl":    "Exchange -> Coins",
            },
        ]

        for i, cfg in enumerate(configs):
            cx_card = start_x + i * (card_w + gap)
            cy_card = start_y
            r_card  = pygame.Rect(cx_card, cy_card, card_w, card_h)

            card_s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_s, (*cfg["bg"], 230), (0, 0, card_w, card_h), border_radius=18)
            surf.blit(card_s, r_card.topleft)
            pygame.draw.rect(surf, cfg["border"], r_card, 2, border_radius=18)

            ccx = cx_card + card_w // 2

            # Title
            ts = title_f.render(cfg["title"], True, cfg["color"])
            surf.blit(ts, ts.get_rect(center=(ccx, cy_card + 32)))

            # Rate
            rs = rate_f.render(cfg["rate_txt"], True, (160, 170, 190))
            surf.blit(rs, rs.get_rect(center=(ccx, cy_card + 58)))

            # Balance
            bl_s = bal_f.render(cfg["bal_lbl"], True, (180, 195, 210))
            surf.blit(bl_s, bl_s.get_rect(center=(ccx, cy_card + 80)))

            # Separator
            pygame.draw.line(surf, cfg["border"],
                             (cx_card + 24, cy_card + 98), (cx_card + card_w - 24, cy_card + 98), 1)

            # Input label
            il_s = label_f.render(cfg["input_lbl"], True, (200, 210, 220))
            surf.blit(il_s, il_s.get_rect(center=(ccx, cy_card + 118)))

            # Input field
            inp_r = pygame.Rect(cx_card + 60, cy_card + 133, card_w - 120, 44)
            self._ex_input_r[i] = inp_r
            is_active = self._ex_active[i]
            inp_bg  = (20, 30, 50) if i == 1 else (30, 26, 8)
            inp_brd = cfg["color"] if is_active else tuple(c // 2 for c in cfg["color"])
            pygame.draw.rect(surf, inp_bg,  inp_r, border_radius=8)
            pygame.draw.rect(surf, inp_brd, inp_r, 2, border_radius=8)
            disp = self._ex_input[i]
            if is_active and int(t * 2) % 2 == 0:
                disp += "|"
            inp_s = input_f.render(disp if disp else "0", True,
                                   cfg["color"] if self._ex_input[i] else (80, 90, 100))
            surf.blit(inp_s, inp_s.get_rect(center=inp_r.center))

            # Preview
            try:
                amt = int(self._ex_input[i]) if self._ex_input[i] else 0
            except ValueError:
                amt = 0
            if amt > 0:
                prev_s = rate_f.render(cfg["preview_fn"](amt), True, cfg["color"])
                surf.blit(prev_s, prev_s.get_rect(center=(ccx, cy_card + 196)))

            # Confirm button
            btn_r = pygame.Rect(cx_card + 60, cy_card + 218, card_w - 120, 46)
            self._ex_btn_r[i] = btn_r
            hov_btn = btn_r.collidepoint(mx, my)
            b_fill  = tuple(min(255, c + (25 if hov_btn else 0)) for c in cfg["bg"])
            pygame.draw.rect(surf, b_fill,      btn_r, border_radius=10)
            pygame.draw.rect(surf, cfg["color"], btn_r, 2, border_radius=10)
            bs4 = btn_f.render(cfg["btn_lbl"], True, cfg["color"])
            surf.blit(bs4, bs4.get_rect(center=btn_r.center))

            # Hover card glow
            if r_card.collidepoint(mx, my):
                glow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*cfg["color"], 12), (0, 0, card_w, card_h), border_radius=18)
                surf.blit(glow, r_card.topleft)

        # Footer hint
        info_f = pygame.font.SysFont("segoeui", 16)
        hint = f"1 shard = {rate} coins  |  Click field, type amount, press Enter or the button"
        info_s = info_f.render(hint, True, (90, 100, 120))
        surf.blit(info_s, info_s.get_rect(center=(cx, start_y + card_h + 36)))


# ── Main Menu ───────────────────────────────────────────────────────────────────
# ── Cross-platform serif font loader ──────────────────────────────────────────
def _load_serif_font(size, bold=False):
    """Load a serif font that works on both Linux and Windows."""
    candidates = [
        # Windows
        "C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/timesbd.ttf"  if bold else "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/garamond.ttf",
        # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"    if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"            if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"             if bold else "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/linux-libertine/LinLibertineSB.ttf",
        "/usr/share/fonts/truetype/gentium/GenBasB.ttf"                    if bold else "/usr/share/fonts/truetype/gentium/GenBasR.ttf",
        # macOS
        "/Library/Fonts/Georgia Bold.ttf" if bold else "/Library/Fonts/Georgia.ttf",
        "/Library/Fonts/Times New Roman Bold.ttf" if bold else "/Library/Fonts/Times New Roman.ttf",
    ]
    for path in candidates:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    return pygame.font.SysFont("georgia,timesnewroman,serif", size, bold=bold)


# ── Shared menu background loader ─────────────────────────────────────────────
_menu_bg_cache = {}
def _get_menu_bg():
    """Return (surface, is_image) for menu_theme.png, cached after first load."""
    if "surf" in _menu_bg_cache:
        return _menu_bg_cache["surf"], _menu_bg_cache["is_image"]
    bg_path = os.path.join(_ICON_DIR, "menu_theme.png")
    try:
        raw = pygame.image.load(bg_path).convert()
        surf = pygame.transform.smoothscale(raw, (SCREEN_W, SCREEN_H))
        _menu_bg_cache["surf"] = surf
        _menu_bg_cache["is_image"] = True
        return surf, True
    except Exception:
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            t2 = y / SCREEN_H
            r = int(4 + 14*t2); g = int(4 + 2*t2); b = int(10 + 6*t2)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))
        _menu_bg_cache["surf"] = surf
        _menu_bg_cache["is_image"] = False
        return surf, False

def _draw_menu_bg(target_surf, overlay_alpha=80):
    """Blit menu_theme.png + dark overlay onto target_surf."""
    bg, is_image = _get_menu_bg()
    target_surf.blit(bg, (0, 0))
    if is_image and overlay_alpha > 0:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, overlay_alpha))
        target_surf.blit(ov, (0, 0))


# ── Particle helpers for the main menu ────────────────────────────────────────
class _MenuParticle:
    __slots__ = ("x","y","size","speed","alpha","drift","color")
    def __init__(self):
        self.reset()
    def reset(self):
        self.x     = random.uniform(0, SCREEN_W)
        self.y     = random.uniform(0, SCREEN_H)
        self.size  = random.uniform(0.5, 2.5)
        self.speed = random.uniform(0.1, 0.5)
        self.alpha = random.randint(30, 160)
        self.drift = random.uniform(-0.15, 0.15)
        self.color = random.choice([(160,20,20),(200,50,10),(180,100,20),(100,10,10)])
    def update(self):
        self.y -= self.speed
        self.x += self.drift
        self.alpha -= 0.3
        if self.y < -5 or self.alpha <= 0:
            self.reset(); self.y = SCREEN_H + 5
    def draw(self, surf):
        if self.alpha <= 0: return
        s = pygame.Surface((int(self.size*2+2), int(self.size*2+2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(self.alpha)),
                           (int(self.size+1), int(self.size+1)), max(1, int(self.size)))
        surf.blit(s, (int(self.x-self.size), int(self.y-self.size)))


class _MenuEmber:
    __slots__ = ("x","y","vx","vy","life","max_life","size")
    def __init__(self):
        self.reset()
    def reset(self):
        self.x        = random.uniform(SCREEN_W*0.05, SCREEN_W*0.95)
        self.y        = SCREEN_H + random.uniform(0, 30)
        self.vx       = random.uniform(-0.6, 0.6)
        self.vy       = random.uniform(-2.5, -0.8)
        self.life     = random.uniform(0.6, 1.0)
        self.max_life = self.life
        self.size     = random.uniform(1.0, 3.5)
    def update(self, dt):
        self.x  += self.vx
        self.vy += 0.01
        self.y  += self.vy
        self.life -= dt * 0.6
        if self.life <= 0: self.reset()
    def draw(self, surf):
        ratio = self.life / self.max_life
        alpha = int(220 * ratio)
        s = pygame.Surface((int(self.size*2+2), int(self.size*2+2)), pygame.SRCALPHA)
        r_size = max(1, int(self.size * ratio + 0.5))
        pygame.draw.circle(s, (255, int(120*ratio), 0, alpha),
                           (int(self.size+1), int(self.size+1)), r_size)
        surf.blit(s, (int(self.x-self.size), int(self.y-self.size)))


class _MenuDrip:
    __slots__ = ("x","y","speed","length","alpha","done")
    def __init__(self, x, start_y):
        self.x      = x
        self.y      = start_y
        self.speed  = random.uniform(0.8, 2.5)
        self.length = random.randint(10, 50)
        self.alpha  = random.randint(140, 220)
        self.done   = False
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_H * 0.72: self.done = True
    def draw(self, surf):
        s = pygame.Surface((4, self.length), pygame.SRCALPHA)
        for i in range(self.length):
            a = int(self.alpha * (1 - i/self.length))
            pygame.draw.line(s, (10, 8, 18, a), (2, i), (2, i))
        surf.blit(s, (self.x-2, int(self.y-self.length)))
        pygame.draw.circle(surf, (15, 10, 25), (self.x, int(self.y)), 3)




# ── Void Heart particle classes ───────────────────────────────────────────────

class _VoidDot:
    """Small black/dark floating speck — Hollow Knight void aesthetic."""
    __slots__ = ("x","y","size","speed","drift","alpha","color")
    def __init__(self):
        self.reset()
    def reset(self):
        self.x     = random.uniform(0, SCREEN_W)
        self.y     = random.uniform(0, SCREEN_H)
        self.size  = random.uniform(1.0, 3.5)
        self.speed = random.uniform(0.05, 0.35)
        self.drift = random.uniform(-0.12, 0.12)
        self.alpha = random.randint(60, 180)
        # mostly near-black, occasional very dark navy/purple
        self.color = random.choice([
            (5, 5, 8), (8, 6, 10), (12, 8, 15), (6, 8, 14),
            (20, 12, 30), (10, 10, 10),
        ])
    def update(self):
        self.y -= self.speed
        self.x += self.drift
        self.alpha -= 0.25
        if self.y < -5 or self.alpha <= 0:
            self.reset(); self.y = SCREEN_H + 5
    def draw(self, surf):
        if self.alpha <= 0: return
        sz = max(1, int(self.size))
        s = pygame.Surface((sz*2+2, sz*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(self.alpha)),
                           (sz+1, sz+1), sz)
        surf.blit(s, (int(self.x-sz), int(self.y-sz)))


class _VoidMote:
    """Pale blue-white glowing mote — like the light specks in the void art."""
    __slots__ = ("x","y","vx","vy","life","max_life","size","hue")
    def __init__(self):
        self.reset()
    def reset(self):
        self.x        = random.uniform(SCREEN_W*0.02, SCREEN_W*0.98)
        self.y        = random.uniform(SCREEN_H*0.3, SCREEN_H)
        self.vx       = random.uniform(-0.4, 0.4)
        self.vy       = random.uniform(-1.2, -0.3)
        self.life     = random.uniform(0.7, 1.0)
        self.max_life = self.life
        self.size     = random.uniform(1.0, 2.8)
        # soft white / icy blue
        self.hue      = random.choice([
            (200, 220, 255), (180, 210, 255), (220, 235, 255), (240, 245, 255),
        ])
    def update(self, dt):
        self.x   += self.vx
        self.vy  -= 0.005
        self.y   += self.vy
        self.life -= dt * 0.45
        if self.life <= 0: self.reset()
    def draw(self, surf):
        ratio = self.life / self.max_life
        alpha = int(200 * ratio)
        sz    = max(1, int(self.size * (0.5 + 0.5*ratio)))
        s = pygame.Surface((sz*2+4, sz*2+4), pygame.SRCALPHA)
        # outer glow
        pygame.draw.circle(s, (*self.hue, int(alpha*0.35)), (sz+2, sz+2), sz+2)
        # inner bright dot
        pygame.draw.circle(s, (*self.hue, alpha), (sz+2, sz+2), sz)
        surf.blit(s, (int(self.x-sz-2), int(self.y-sz-2)))


class _VoidWisp:
    """Slow drifting translucent void tendril / wisp — large, very faint."""
    __slots__ = ("x","y","vx","vy","life","max_life","radius","color")
    def __init__(self):
        self.reset(start_offscreen=True)
    def reset(self, start_offscreen=False):
        self.x        = random.uniform(-60, SCREEN_W+60)
        self.y        = SCREEN_H + random.uniform(20, 120) if start_offscreen else random.uniform(0, SCREEN_H)
        self.vx       = random.uniform(-0.3, 0.3)
        self.vy       = random.uniform(-0.5, -0.15)
        self.life     = random.uniform(0.6, 1.0)
        self.max_life = self.life
        self.radius   = random.randint(18, 50)
        self.color    = random.choice([
            (30, 30, 45), (20, 25, 50), (15, 15, 30), (40, 20, 55),
        ])
    def update(self, dt):
        self.x   += self.vx
        self.y   += self.vy
        self.life -= dt * 0.22
        if self.life <= 0: self.reset()
    def draw(self, surf):
        ratio = self.life / self.max_life
        alpha = int(55 * ratio * ratio)
        if alpha < 2: return
        r = max(3, self.radius)
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r+1, r+1), r)
        surf.blit(s, (int(self.x-r-1), int(self.y-r-1)))


class MainMenu:
    # ── Fonts (class-level, created once) ────────────────────────────────────
    _font_title  = None
    _font_sub    = None
    _font_btn    = None
    _font_ver    = None

    # ── Heavy surfaces cached at class level so they're built only once ──────
    _bg_surf_cached     = None
    _bg_is_image_cached = False
    _vig_surf_cached    = None

    @classmethod
    def _ensure_fonts(cls):
        if cls._font_title is not None:
            return
        base_h = SCREEN_H
        cls._font_title = _load_serif_font(max(40, int(base_h * 0.10)), bold=True)
        cls._font_sub   = _load_serif_font(max(14, int(base_h * 0.026)))
        cls._font_btn   = _load_serif_font(max(18, int(base_h * 0.038)), bold=True)
        cls._font_ver   = _load_serif_font(max(11, int(base_h * 0.020)))

    @classmethod
    def _ensure_heavy_surfaces(cls):
        if cls._bg_surf_cached is None:
            _bg_path = os.path.join(_ICON_DIR, "menu_theme.png")
            try:
                _raw_bg = pygame.image.load(_bg_path).convert()
                cls._bg_surf_cached     = pygame.transform.smoothscale(_raw_bg, (SCREEN_W, SCREEN_H))
                cls._bg_is_image_cached = True
            except Exception:
                cls._bg_surf_cached = pygame.Surface((SCREEN_W, SCREEN_H))
                for _y in range(SCREEN_H):
                    _t2 = _y / SCREEN_H
                    _r = int(4  + 14*_t2); _g = int(4 + 2*_t2); _b = int(10 + 6*_t2)
                    pygame.draw.line(cls._bg_surf_cached, (_r, _g, _b), (0, _y), (SCREEN_W, _y))
                cls._bg_is_image_cached = False
        if cls._vig_surf_cached is None:
            cls._vig_surf_cached = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            for _y in range(0, SCREEN_H, 2):
                for _x in range(0, SCREEN_W, 4):
                    _dx = (_x - SCREEN_W/2) / (SCREEN_W/2)
                    _dy = (_y - SCREEN_H/2) / (SCREEN_H/2)
                    _d  = min(1.0, math.sqrt(_dx*_dx + _dy*_dy))
                    _a  = int(190 * _d * _d)
                    pygame.draw.line(cls._vig_surf_cached, (0,0,0,_a), (_x,_y), (_x+3,_y))

    # Button definitions: (attr_name, label, accent_color)
    # Main trio drawn separately; small row uses emoji labels
    _BTN_DEFS = [
        ("btn_play",         "\u25B6",           ( 60, 160, 255)),
        ("btn_loadout",      "\U0001F6E1",        (120,  80, 220)),
        ("btn_shop",         "\U0001F6D2",        (255, 180,  40)),
        ("btn_skilltree",    "\U0001F333",        ( 60, 200, 140)),
        ("btn_achievements", "\U0001F3C6",        (200, 160,  20)),
        ("btn_quests",       "\U0001F4DC",        (160,  80, 220)),
        ("btn_profile",      "\U0001F464",        ( 80, 180, 220)),
        ("btn_settings",     "\u2699",            ( 60, 130, 180)),
        ("btn_quit",         "\U0001F6AA",        (180,  50,  50)),
        ("btn_multiplayer",  "\U0001F310",        ( 20, 160, 220)),
    ]
    # Indices into _BTN_DEFS for the three main buttons and the small row
    _MAIN_IDX  = (0, 1, 2)       # play, loadout, shop
    _SMALL_IDX = (3, 4, 5, 6, 9, 7, 8)  # skilltree, achievements, quests, profile, multiplayer, settings, quit

    def __init__(self, screen, save_data=None, first_open=True):
        self.screen    = screen
        self.t         = 0.0 if first_open else 999.0
        self.action    = None
        self.save_data = save_data or {}

        self._ensure_fonts()
        self._ensure_heavy_surfaces()

        cx           = SCREEN_W // 2
        cy_main      = int(SCREEN_H * 0.50)   # vertical centre of big-button row

        # ── Big three: LOADOUT | PLAY | SHOP ─────────────────────────────────
        play_w,    play_h    = 200, 200
        side_w,    side_h    = 160, 160
        side_gap             = 28   # gap between side btn and play btn

        self.btn_play    = pygame.Rect(cx - play_w//2,
                                       cy_main - play_h//2,
                                       play_w, play_h)
        self.btn_loadout = pygame.Rect(self.btn_play.left - side_gap - side_w,
                                       cy_main - side_h//2,
                                       side_w, side_h)
        self.btn_shop    = pygame.Rect(self.btn_play.right + side_gap,
                                       cy_main - side_h//2,
                                       side_w, side_h)

        # ── Small bottom row with emoji ───────────────────────────────────────
        sm_w, sm_h = 90, 90
        sm_gap     = 14
        _sm_btns   = ["btn_skilltree", "btn_achievements", "btn_quests", "btn_profile", "btn_multiplayer", "btn_settings", "btn_quit"]
        _total_sm  = len(_sm_btns) * sm_w + (len(_sm_btns) - 1) * sm_gap
        _sm_x0     = cx - _total_sm // 2
        _sm_y      = cy_main + play_h//2 + 36
        for _si, _attr in enumerate(_sm_btns):
            setattr(self, _attr,
                    pygame.Rect(_sm_x0 + _si * (sm_w + sm_gap), _sm_y, sm_w, sm_h))


        # ── Void particles: black/dark drifting dots, glowing motes, void wisps
        self._particles  = [_VoidDot()    for _ in range(90)]
        self._embers     = [_VoidMote()   for _ in range(60)]
        self._void_wisps = [_VoidWisp()   for _ in range(30)]
        self._drips      = []
        self._drip_timer = 0.0

        # Per-button hover glow (0..1) — one entry per _BTN_DEFS entry
        self._hover_anim = [0.0] * len(self._BTN_DEFS)

        # emoji-capable font for small buttons
        self._emoji_font = None

        # Reuse cached background and vignette
        self._bg_surf    = self.__class__._bg_surf_cached
        self._bg_is_image = self.__class__._bg_is_image_cached
        self._vig_surf   = self.__class__._vig_surf_cached

        # Title glow cache
        self._title_cache = {}

        # Fade-in only on first open
        self._fade_alpha = 255 if first_open else 0

        # ── Hardcore button (used by _draw_modern) ────────────────────────────
        hc_w, hc_h = 180, 52
        self.btn_hardcore = pygame.Rect(SCREEN_W - hc_w - 18, SCREEN_H - hc_h - 18, hc_w, hc_h)

    # ── Title surface with pulsing glow ──────────────────────────────────────
    def _get_title_surf(self, glow_phase):
        key = int(glow_phase * 20) % 40
        if key in self._title_cache:
            return self._title_cache[key]
        f = self._font_title
        # Void/pale silver-white main color, soft blue-white glow
        VOID_WHITE  = (220, 225, 240)
        VOID_GLOW   = (120, 150, 210)
        main = f.render("pyTDS", True, VOID_WHITE)
        gs   = 0.5 + 0.5 * math.sin(glow_phase)
        ga   = int(55 + 60 * gs)
        gw   = int(main.get_width()  * (1.025 + 0.015*gs))
        gh   = int(main.get_height() * (1.025 + 0.015*gs))
        glow = pygame.transform.smoothscale(f.render("pyTDS", True, VOID_GLOW), (gw, gh))
        glow.set_alpha(ga)
        pad  = 16

        # ── Decorative divider (subtitle removed) ────────────────────────────
        div_w    = main.get_width() + 80
        div_h    = 3
        div_surf = pygame.Surface((div_w, div_h), pygame.SRCALPHA)
        for dx in range(div_w):
            frac  = abs(dx - div_w / 2) / (div_w / 2)
            alpha = int((1 - frac ** 2) * (120 + 80 * gs))
            r_c   = int(80  + 80  * gs)
            g_c   = int(100 + 80  * gs)
            b_c   = int(180 + 60  * gs)
            pygame.draw.line(div_surf, (r_c, g_c, b_c, alpha), (dx, 0), (dx, div_h - 1))

        total_h = gh + pad + div_h + 10
        total_w = max(gw + pad, div_w + pad)
        comp    = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        cx_loc  = total_w // 2

        comp.blit(glow, (cx_loc - gw // 2, (gh + pad - gh) // 2))
        comp.blit(main, (cx_loc - main.get_width() // 2, (gh + pad - main.get_height()) // 2))

        div_y = gh + pad - 4
        comp.blit(div_surf, (cx_loc - div_w // 2, div_y))

        self._title_cache[key] = comp
        return comp

    # ── Ornament line ─────────────────────────────────────────────────────────
    @staticmethod
    def _draw_ornament(surf, cx, y, width, color, alpha=180):
        s = pygame.Surface((width, 4), pygame.SRCALPHA)
        for x in range(width):
            a = int(alpha * math.sin(math.pi * x / width))
            pygame.draw.line(s, (*color, a), (x, 1), (x, 2))
        surf.blit(s, (cx - width//2, y))

    # ── Button drawing ────────────────────────────────────────────────────────
    def _draw_fancy_btn(self, surf, rect, label, h, accent, idx):
        # Slide-in animation
        btn_start = 0.5 + idx * 0.08
        progress  = min(1.0, max(0.0, (self.t - btn_start) / 0.35))
        progress  = 1.0 - (1.0 - progress) ** 3
        if progress <= 0: return
        anim_y    = int(28 * (1.0 - progress))
        alpha_val = int(255 * progress)

        GOLD      = (200, 160,  60)
        GOLD_BR   = (255, 210,  80)
        GRAY      = (120, 120, 130)
        LIGHT_GR  = (180, 180, 190)
        VOID_BG   = (10, 8, 18)

        # Solid dark void background — always visible, brightens on hover
        btn_s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        base_a = int(195 + h * 40)
        pygame.draw.rect(btn_s, (*VOID_BG, base_a),
                         (0, 0, rect.w, rect.h), border_radius=6)
        # Accent colour tint on hover
        if h > 0.05:
            pygame.draw.rect(btn_s, (accent[0], accent[1], accent[2], int(h * 35)),
                             (0, 0, rect.w, rect.h), border_radius=6)

        # Border blends gray→gold on hover — always solid
        bc = (
            int(GOLD[0]*h + GRAY[0]*(1-h)),
            int(GOLD[1]*h + GRAY[1]*(1-h)),
            int(GOLD[2]*h + GRAY[2]*(1-h)),
        )
        border_a = min(255, int(160 + 95*h))
        pygame.draw.rect(btn_s, (bc[0], bc[1], bc[2], border_a),
                         (0, 0, rect.w, rect.h), width=2, border_radius=6)

        # Top/bottom gold lines appear on hover
        if h > 0.05:
            la = min(255, int(h * 200))
            pygame.draw.line(btn_s, (GOLD[0], GOLD[1], GOLD[2], la), (8, 0),        (rect.w-8, 0))
            pygame.draw.line(btn_s, (GOLD[0], GOLD[1], GOLD[2], la), (8, rect.h-1), (rect.w-8, rect.h-1))

        # Bottom colour stripe — accent glow under emoji
        stripe_a = min(255, int(h * 200 + 55))
        stripe_s = pygame.Surface((max(1, rect.w - 20), 3), pygame.SRCALPHA)
        pygame.draw.rect(stripe_s, (accent[0], accent[1], accent[2], stripe_a),
                         (0, 0, max(1, rect.w - 20), 3))
        btn_s.blit(stripe_s, (10, rect.h - 7))

        if alpha_val < 255: btn_s.set_alpha(alpha_val)
        surf.blit(btn_s, (rect.x, rect.y + anim_y))

        # Emoji label — render with emoji font, centred in button
        if label:
            LIGHT_GR = (210, 210, 220)
            tc = (
                int(GOLD_BR[0]*h + LIGHT_GR[0]*(1-h)),
                int(GOLD_BR[1]*h + LIGHT_GR[1]*(1-h)),
                int(GOLD_BR[2]*h + LIGHT_GR[2]*(1-h)),
            )
            em_size = max(18, int(rect.h * 0.52))
            if not hasattr(self, '_emoji_font_big') or getattr(self, '_emoji_font_big_size', 0) != em_size or getattr(self, '_emoji_font_big_linux', None) != SETTINGS.get('linux_mode', False):
                self._emoji_font_big = _get_emoji_font(em_size, bold=False)
                self._emoji_font_big_size = em_size
                self._emoji_font_big_linux = SETTINGS.get('linux_mode', False)
            em_s = self._emoji_font_big.render(label, True, tc)
            lx = rect.centerx - em_s.get_width() // 2
            ly = rect.centery - em_s.get_height() // 2 + anim_y
            if alpha_val < 255:
                em_s.set_alpha(alpha_val)
            surf.blit(em_s, (lx, ly))

        # (no side ornaments)

    def run(self):
        clock = pygame.time.Clock()
        self.action = None
        while self.action is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos = ev.pos
                    if self.btn_play.collidepoint(pos):
                        diff = DifficultyMenu(self.screen, self.save_data).run()
                        if diff != "back":
                            if diff == "play_frosty":
                                game_core.CURRENT_MAP = "frosty"
                                self.action = diff

                            elif diff == "play_sandbox":
                                game_core.CURRENT_MAP = "straight"
                                self.action = diff
                            else:
                                map_choice = MapSelectMenu(self.screen).run()
                                if map_choice != "back":
                                    game_core.CURRENT_MAP = map_choice
                                    self.action = diff
                    if self.btn_loadout.collidepoint(pos):      self.action = "loadout"
                    if self.btn_shop.collidepoint(pos):         self.action = "shop"
                    if self.btn_skilltree.collidepoint(pos):    self.action = "skilltree"
                    if self.btn_achievements.collidepoint(pos): self.action = "achievements"
                    if self.btn_quests.collidepoint(pos):       self.action = "quests"
                    if self.btn_profile.collidepoint(pos):      self.action = "profile"
                    if self.btn_settings.collidepoint(pos):     self.action = "settings"
                    if self.btn_quit.collidepoint(pos):         self.action = "quit"
                    if self.btn_multiplayer.collidepoint(pos):  self.action = "multiplayer"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw(self):
        # ── Style dispatch ────────────────────────────────────────────────────
        if SETTINGS.get("menu_style", 0) == 1:
            self._draw_modern(); return
        if SETTINGS.get("menu_style", 0) == 2:
            self._draw_vertical(); return
        if SETTINGS.get("menu_style", 0) == 3:
            self._draw_gothic(); return

        surf = self.screen
        t    = self.t
        cx   = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()
        dt   = 1/60.0  # approximate

        GOLD      = (200, 160,  60)
        GOLD_BR   = (255, 210,  80)
        BLOOD_RED = (140,  10,  10)
        GRAY      = (120, 120, 130)
        DIM_RED   = ( 80,   5,   5)

        # ── Background ───────────────────────────────────────────────────────
        _draw_menu_bg(surf, overlay_alpha=80)

        # ── Void wisps (behind dots) ──────────────────────────────────────────
        for w in self._void_wisps:
            w.update(dt); w.draw(surf)

        # ── Void dots (black specks) ──────────────────────────────────────────
        for p in self._particles:
            p.update(); p.draw(surf)

        # ── Void motes (glowing light specks) ────────────────────────────────
        for e in self._embers:
            e.update(dt); e.draw(surf)

        # ── Fog gradient at bottom ────────────────────────────────────────────
        fog = pygame.Surface((SCREEN_W, int(SCREEN_H*0.22)), pygame.SRCALPHA)
        for fy in range(fog.get_height()):
            a = int(70 * (1 - fy / fog.get_height()))
            pygame.draw.rect(fog, (4, 5, 14, a), (0, fy, SCREEN_W, 1))
        surf.blit(fog, (0, SCREEN_H - fog.get_height()))

        # ── Vignette ─────────────────────────────────────────────────────────
        surf.blit(self._vig_surf, (0, 0))

        # ── Title ─────────────────────────────────────────────────────────────
        title_surf = self._get_title_surf(t * 1.4)
        ty = int(SCREEN_H * 0.12)
        surf.blit(title_surf, (cx - title_surf.get_width()//2, ty))

        # ── Drips ────────────────────────────────────────────────────────────
        self._drip_timer -= dt
        if self._drip_timer <= 0:
            self._drip_timer = random.uniform(0.4, 1.2)
            ts_tmp = self._font_title.render("pyTDS", True, (255,255,255))
            tw     = ts_tmp.get_width()
            tx     = cx - tw//2
            self._drips.append(_MenuDrip(
                x       = random.randint(tx+10, tx+tw-10),
                start_y = ty + ts_tmp.get_height() - 8,
            ))
        self._drips = [d for d in self._drips if not d.done]
        for d in self._drips:
            d.update(); d.draw(surf)

        # ── Ornament lines below title ────────────────────────────────────────
        # (ornament lines removed)

        # (subtitle removed)

        # ── Hover animation update ────────────────────────────────────────────
        for i, (attr, _label, _acc) in enumerate(self._BTN_DEFS):
            hovered = getattr(self, attr).collidepoint(mx, my)
            target  = 1.0 if hovered else 0.0
            speed   = 0.18 if hovered else 0.38
            self._hover_anim[i] += (target - self._hover_anim[i]) * speed

        # ── Main trio: LOADOUT | PLAY | SHOP ─────────────────────────────────
        for idx in self._MAIN_IDX:
            attr, label, accent = self._BTN_DEFS[idx]
            rect = getattr(self, attr)
            self._draw_fancy_btn(surf, rect, label, self._hover_anim[idx], accent, idx)

        # ── Small bottom row with emoji ───────────────────────────────────────
        # Rebuild emoji font if linux_mode changed
        if self._emoji_font is None or getattr(self, '_emoji_font_linux', None) != SETTINGS.get('linux_mode', False):
            self._emoji_font = _get_emoji_font(22, bold=True)
            self._emoji_font_linux = SETTINGS.get('linux_mode', False)

        for idx in self._SMALL_IDX:
            attr, label, accent = self._BTN_DEFS[idx]
            rect = getattr(self, attr)
            h    = self._hover_anim[idx]
            self._draw_fancy_btn(surf, rect, label, h, accent, idx)

        # ── Coins + Shards — bottom-left, stacked like the reference UI ─────────
        pad_x = 18
        pad_y = SCREEN_H - 18
        ico_size = 54

        def _draw_resource(ico_name, label_text, value, col, ico_col_fallback, bottom_y):
            ico = load_icon(ico_name, ico_size)
            lbl_f = pygame.font.SysFont("segoeui", 18, bold=False)
            val_f = pygame.font.SysFont("segoeui", 28, bold=True)
            lbl_s = lbl_f.render(label_text, True, (210, 200, 180))
            val_s = val_f.render(fmt_num(value), True, col)
            text_w = max(lbl_s.get_width(), val_s.get_width())
            ico_w  = ico.get_width() if ico else ico_size
            total_w = ico_w + 10 + text_w + 18
            total_h = max(ico_size, lbl_s.get_height() + val_s.get_height() + 4) + 12
            bx = pad_x
            by = bottom_y - total_h
            # dark pill background
            draw_rect_alpha(surf, (12, 10, 8), (bx, by, total_w, total_h), 180, 10)
            # icon
            if ico:
                surf.blit(ico, (bx + 8, by + (total_h - ico.get_height()) // 2))
            else:
                pygame.draw.circle(surf, ico_col_fallback,
                                   (bx + 8 + ico_size//2, by + total_h//2), ico_size//2 - 2)
            tx = bx + ico_w + 16
            ty_lbl = by + (total_h - lbl_s.get_height() - val_s.get_height() - 4) // 2
            surf.blit(lbl_s, (tx, ty_lbl))
            surf.blit(val_s, (tx, ty_lbl + lbl_s.get_height() + 4))
            return by - 8  # return top edge minus gap for stacking

        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)

        # Draw shards first (upper), then coins below it
        shards_top = _draw_resource("shard_ico", "Shards", shards, C_WHITE, (180, 60, 220),  pad_y - 6)
        _draw_resource(             "coin_ico",  "Coins", coins,  C_WHITE, (210, 150,  20),  shards_top)

        # (hint removed)

        # ── Version ───────────────────────────────────────────────────────────
        ver_s = self._font_ver.render("v1.3  ALPHA", True, DIM_RED)
        ver_s.set_alpha(110)
        surf.blit(ver_s, (SCREEN_W - ver_s.get_width() - 14, SCREEN_H - ver_s.get_height() - 14))

        # ── Fade-in overlay ───────────────────────────────────────────────────
        if self._fade_alpha > 0:
            fade = pygame.Surface((SCREEN_W, SCREEN_H))
            fade.fill((0, 0, 0))
            fade.set_alpha(int(self._fade_alpha))
            surf.blit(fade, (0, 0))
            self._fade_alpha = max(0, self._fade_alpha - 5)



    # ── Style 2: Classic / Vertical buttons ──────────────────────────────────
    def _draw_vertical(self):
        surf = self.screen
        t    = self.t
        cx   = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()

        # background + vignette
        _draw_menu_bg(surf, overlay_alpha=100)
        surf.blit(self._vig_surf, (0, 0))

        # subtle grid
        gs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for gx in range(0, SCREEN_W, 80):
            pygame.draw.line(gs, (255, 255, 255, 5), (gx, 0), (gx, SCREEN_H))
        for gy in range(0, SCREEN_H, 80):
            pygame.draw.line(gs, (255, 255, 255, 5), (0, gy), (SCREEN_W, gy))
        surf.blit(gs, (0, 0))

        dt = 1 / 60.0
        for e in self._embers:
            e.update(dt); e.draw(surf)

        # title
        title_f = pygame.font.SysFont("segoeui", 72, bold=True)
        pulse   = 0.5 + 0.5 * math.sin(t * 1.2)
        title_col = (int(180 + 60*pulse), int(200 + 40*pulse), 255)
        ts_sh = title_f.render("pyTDS", True, (0, 0, 0))
        ts_sh.set_alpha(120)
        ty = int(SCREEN_H * 0.18)
        surf.blit(ts_sh, ts_sh.get_rect(center=(cx + 3, ty + 3)))
        ts_main = title_f.render("pyTDS", True, title_col)
        surf.blit(ts_main, ts_main.get_rect(center=(cx, ty)))
        line_w = int(340 * min(1.0, t / 0.8))
        for lx in range(-line_w // 2, line_w // 2):
            frac  = abs(lx) / max(1, line_w // 2)
            cv    = int(120 + 100 * pulse)
            pygame.draw.line(surf, (80, cv, 255), (cx + lx, ty + 52), (cx + lx, ty + 54))

        # vertical buttons
        BTN_W, BTN_H, BTN_GAP = 320, 52, 12
        BTNS = [
            ("btn_play",         "\u25B6  PLAY",         ( 60, 160, 255)),
            ("btn_loadout",      "\U0001F6E1  LOADOUT",  (120,  80, 220)),
            ("btn_shop",         "\U0001F6D2  SHOP",     (255, 180,  40)),
            ("btn_skilltree",    "\U0001F333  SKILL TREE",( 60, 200, 140)),
            ("btn_achievements", "\U0001F3C6  ACHIEVEMENTS",(200,160, 20)),
            ("btn_quests",       "\U0001F4DC  QUESTS",   (160,  80, 220)),
            ("btn_profile",      "\U0001F464  PROFILE",  ( 80, 180, 220)),
            ("btn_settings",     "\u2699  SETTINGS",     ( 60, 130, 180)),
            ("btn_multiplayer",  "\U0001F310  MULTIPLAYER", ( 20, 160, 220)),
            ("btn_quit",         "\U0001F6AA  QUIT",     (180,  50,  50)),
        ]
        total_h = len(BTNS) * BTN_H + (len(BTNS) - 1) * BTN_GAP
        start_y = int(SCREEN_H * 0.5) - total_h // 2

        lf = pygame.font.SysFont("segoeui", 22, bold=True)

        for vi, (attr, label, accent) in enumerate(BTNS):
            r = pygame.Rect(cx - BTN_W // 2, start_y + vi * (BTN_H + BTN_GAP), BTN_W, BTN_H)
            setattr(self, attr, r)

            hov  = r.collidepoint(mx, my)
            prog = min(1.0, max(0.0, (t - 0.3 - vi * 0.07) / 0.3))
            prog = 1.0 - (1.0 - prog) ** 3
            if prog <= 0: continue

            slide_x = int(60 * (1.0 - prog))
            alpha_v = int(255 * prog)
            draw_r  = r.move(slide_x, 0)

            bg = (accent[0]//6+18, accent[1]//6+18, accent[2]//6+22)
            if hov: bg = (min(255,bg[0]+20), min(255,bg[1]+20), min(255,bg[2]+28))
            bs = pygame.Surface((BTN_W, BTN_H), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*bg, int(220*prog)), (0,0,BTN_W,BTN_H), border_radius=10)
            bh2 = int(BTN_H * 0.6); by2 = (BTN_H - bh2) // 2
            pygame.draw.rect(bs, (*accent, int((180+75*int(hov))*prog)), (0,by2,4,bh2), border_radius=2)
            brd = accent if hov else (accent[0]//2, accent[1]//2, accent[2]//2)
            pygame.draw.rect(bs, (*brd, int((80+140*int(hov))*prog)), (0,0,BTN_W,BTN_H), 1, border_radius=10)
            surf.blit(bs, draw_r.topleft)

            lbl_s = lf.render(label, True, (255,255,255) if hov else (180,190,210))
            lbl_s.set_alpha(alpha_v)
            surf.blit(lbl_s, lbl_s.get_rect(midleft=(draw_r.x+18, draw_r.centery)))

            if hov and prog >= 1.0:
                arr = pygame.Surface((14,14), pygame.SRCALPHA)
                pygame.draw.polygon(arr, (*accent, 200), [(0,3),(8,7),(0,11)])
                surf.blit(arr, (draw_r.right-18, draw_r.centery-7))

        # coins + shards
        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)
        ico_m  = load_icon("coin_ico",  30)
        ico_sh = load_icon("shard_ico", 26)
        cf2    = pygame.font.SysFont("segoeui", 20, bold=True)
        coin_s  = cf2.render(f" {fmt_num(coins)}",  True, C_WHITE)
        shard_s = cf2.render(f" {fmt_num(shards)}", True, C_WHITE)
        cw2 = (ico_m.get_width()  if ico_m  else 0) + coin_s.get_width()  + 16
        sw3 = (ico_sh.get_width() if ico_sh else 0) + shard_s.get_width() + 16
        coin_bg2  = pygame.Rect(SCREEN_W - cw2  - 10, 8, cw2,  30)
        shard_bg2 = pygame.Rect(coin_bg2.x - sw3 - 8, 8, sw3, 30)
        draw_rect_alpha(surf, (20,20,10), (coin_bg2.x, coin_bg2.y, coin_bg2.w, coin_bg2.h), 150, 6)
        draw_rect_alpha(surf, (5,20,30),  (shard_bg2.x,shard_bg2.y,shard_bg2.w,shard_bg2.h),150, 6)
        pygame.draw.rect(surf, (160,120,20), coin_bg2,  1, border_radius=6)
        pygame.draw.rect(surf, (40,120,180), shard_bg2, 1, border_radius=6)
        bx3 = coin_bg2.x + 8
        if ico_m:
            surf.blit(ico_m,  (bx3, coin_bg2.y  + (30-ico_m.get_height())//2))
            surf.blit(coin_s, (bx3+ico_m.get_width(), coin_bg2.y+(30-coin_s.get_height())//2))
        else:
            surf.blit(coin_s, coin_s.get_rect(midleft=(bx3, coin_bg2.centery)))
        bx4 = shard_bg2.x + 8
        if ico_sh:
            surf.blit(ico_sh,  (bx4, shard_bg2.y+(30-ico_sh.get_height())//2))
            surf.blit(shard_s, (bx4+ico_sh.get_width(), shard_bg2.y+(30-shard_s.get_height())//2))
        else:
            surf.blit(shard_s, shard_s.get_rect(midleft=(bx4, shard_bg2.centery)))

        ver = font_sm.render("v1.3", True, (50, 58, 80))
        surf.blit(ver, (10, SCREEN_H - 20))

        if self._fade_alpha > 0:
            fade = pygame.Surface((SCREEN_W, SCREEN_H))
            fade.fill((0, 0, 0))
            fade.set_alpha(self._fade_alpha)
            surf.blit(fade, (0, 0))
            self._fade_alpha = max(0, self._fade_alpha - 6)


    def _draw_gothic(self):
        """Gothic / Dark Tower Defense style menu — matches the screenshot aesthetic."""
        surf = self.screen
        t    = self.t
        cx   = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()
        dt   = 1 / 60.0

        # ── Background ───────────────────────────────────────────────────────
        _draw_menu_bg(surf, overlay_alpha=160)

        # Dark vignette overlay
        vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for vy in range(SCREEN_H):
            frac = vy / SCREEN_H
            a = int(80 * (1.0 - abs(frac - 0.5) * 2))
            pygame.draw.line(vig, (0, 0, 0, a), (0, vy), (SCREEN_W, vy))
        surf.blit(vig, (0, 0))

        # Scanlines effect
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for sy in range(0, SCREEN_H, 4):
            pygame.draw.line(scan, (0, 0, 0, 18), (0, sy), (SCREEN_W, sy))
        surf.blit(scan, (0, 0))

        # ── Animated dust particles ───────────────────────────────────────────
        for e in self._embers:
            e.update(dt); e.draw(surf)

        # ── Title ─────────────────────────────────────────────────────────────
        GOLD     = (200, 170,  60)
        GOLD_BR  = (255, 215,  80)
        TITLE_Y  = int(SCREEN_H * 0.15)

        tf = pygame.font.SysFont("georgia", 74, bold=True)
        # shadow
        sh = tf.render("TOWER DEFENSE", True, (0, 0, 0))
        sh.set_alpha(180)
        surf.blit(sh, sh.get_rect(center=(cx + 4, TITLE_Y + 4)))
        # main
        pulse = 0.5 + 0.5 * math.sin(t * 1.5)
        tc = (int(200 + 40*pulse), int(170 + 30*pulse), int(50 + 20*pulse))
        ts = tf.render("TOWER DEFENSE", True, tc)
        surf.blit(ts, ts.get_rect(center=(cx, TITLE_Y)))

        # gold underline
        uw = int(500 * min(1.0, t / 1.0))
        line_col = (int(180 + 60*pulse), int(140 + 50*pulse), 30)
        pygame.draw.line(surf, line_col,
                         (cx - uw // 2, TITLE_Y + 50),
                         (cx + uw // 2, TITLE_Y + 50), 2)

        # ── Buttons ───────────────────────────────────────────────────────────
        BTN_W, BTN_H, BTN_GAP = 300, 52, 8
        BTNS = [
            ("btn_play",         "PLAY"),
            ("btn_loadout",      "LOADOUT"),
            ("btn_shop",         "SHOP"),
            ("btn_skilltree",    "SKILL TREE"),
            ("btn_achievements", "ACHIEVEMENTS"),
            ("btn_quests",       "QUESTS"),
            ("btn_profile",      "PROFILE"),
            ("btn_settings",     "SETTINGS"),
            ("btn_multiplayer",  "MULTIPLAYER"),
            ("btn_quit",         "QUIT"),
        ]
        total_h = len(BTNS) * BTN_H + (len(BTNS) - 1) * BTN_GAP
        start_y = cx  # vertical center

        # center buttons vertically in bottom 65% of screen
        start_y = int(SCREEN_H * 0.38)

        bf = pygame.font.SysFont("georgia", 22, bold=True)

        for bi, (attr, label) in enumerate(BTNS):
            prog = min(1.0, max(0.0, (t - 0.2 - bi * 0.06) / 0.35))
            prog = 1.0 - (1.0 - prog) ** 3
            if prog <= 0:
                r = pygame.Rect(cx - BTN_W // 2, start_y + bi * (BTN_H + BTN_GAP), BTN_W, BTN_H)
                setattr(self, attr, r)
                continue

            r = pygame.Rect(cx - BTN_W // 2, start_y + bi * (BTN_H + BTN_GAP), BTN_W, BTN_H)
            setattr(self, attr, r)
            hov = r.collidepoint(mx, my)

            # button body
            bs = pygame.Surface((BTN_W, BTN_H), pygame.SRCALPHA)
            if hov:
                pygame.draw.rect(bs, (60, 40, 5, int(220*prog)),   (0, 0, BTN_W, BTN_H))
            else:
                pygame.draw.rect(bs, (10, 10, 12, int(200*prog)),  (0, 0, BTN_W, BTN_H))

            # left gold accent bar
            bar_h = int(BTN_H * 0.55)
            bar_y = (BTN_H - bar_h) // 2
            bar_col = (int((160+60*pulse)), int((120+40*pulse)), 20) if hov else (100, 75, 10)
            pygame.draw.rect(bs, (*bar_col, int(255*prog)), (0, bar_y, 3, bar_h))

            # border
            brd = (int(160+60*pulse), int(120+40*pulse), 20) if hov else (60, 45, 8)
            pygame.draw.rect(bs, (*brd, int(180*prog)), (0, 0, BTN_W, BTN_H), 1)

            surf.blit(bs, r.topleft)

            # label
            lbl_col = (int(220+30*pulse), int(195+25*pulse), int(80+30*pulse)) if hov else (190, 175, 120)
            ls = bf.render(label, True, lbl_col)
            ls.set_alpha(int(255 * prog))
            surf.blit(ls, ls.get_rect(midleft=(r.x + 18, r.centery)))

            # hover arrow
            if hov and prog >= 1.0:
                arr_col = (int(200+50*pulse), int(160+40*pulse), 30)
                arr = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.polygon(arr, arr_col, [(0, 2), (8, 5), (0, 8)])
                surf.blit(arr, (r.right - 16, r.centery - 5))

        # ── Coins / Shards ────────────────────────────────────────────────────
        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)
        ico_m  = load_icon("coin_ico",  30)
        ico_sh = load_icon("shard_ico", 26)
        cf2    = pygame.font.SysFont("segoeui", 20, bold=True)
        coin_s  = cf2.render(f" {fmt_num(coins)}",  True, (220, 195, 80))
        shard_s = cf2.render(f" {fmt_num(shards)}", True, (120, 200, 255))
        cw2 = (ico_m.get_width()  if ico_m  else 0) + coin_s.get_width()  + 16
        sw3 = (ico_sh.get_width() if ico_sh else 0) + shard_s.get_width() + 16
        coin_bg2  = pygame.Rect(SCREEN_W - cw2  - 10, 8, cw2,  30)
        shard_bg2 = pygame.Rect(coin_bg2.x - sw3 - 8, 8, sw3, 30)
        draw_rect_alpha(surf, (20, 14,  2), (coin_bg2.x,  coin_bg2.y,  coin_bg2.w,  coin_bg2.h),  180, 6)
        draw_rect_alpha(surf, ( 5, 10, 22), (shard_bg2.x, shard_bg2.y, shard_bg2.w, shard_bg2.h), 180, 6)
        pygame.draw.rect(surf, (120, 85, 10), coin_bg2,  1, border_radius=6)
        pygame.draw.rect(surf, (30,  80, 150), shard_bg2, 1, border_radius=6)
        bx3 = coin_bg2.x + 8
        if ico_m:
            surf.blit(ico_m,  (bx3, coin_bg2.y + (30 - ico_m.get_height()) // 2))
            surf.blit(coin_s, (bx3 + ico_m.get_width(), coin_bg2.y + (30 - coin_s.get_height()) // 2))
        else:
            surf.blit(coin_s, coin_s.get_rect(midleft=(bx3, coin_bg2.centery)))
        bx4 = shard_bg2.x + 8
        if ico_sh:
            surf.blit(ico_sh,  (bx4, shard_bg2.y + (30 - ico_sh.get_height()) // 2))
            surf.blit(shard_s, (bx4 + ico_sh.get_width(), shard_bg2.y + (30 - shard_s.get_height()) // 2))
        else:
            surf.blit(shard_s, shard_s.get_rect(midleft=(bx4, shard_bg2.centery)))

        ver = font_sm.render("v1.3", True, (60, 50, 20))
        surf.blit(ver, (10, SCREEN_H - 20))

        if self._fade_alpha > 0:
            fade = pygame.Surface((SCREEN_W, SCREEN_H))
            fade.fill((0, 0, 0))
            fade.set_alpha(self._fade_alpha)
            surf.blit(fade, (0, 0))
            self._fade_alpha = max(0, self._fade_alpha - 6)

    def _draw_modern(self):
        surf = self.screen
        surf.fill((10, 13, 20))
        t = self.t
        cx = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()

        # ── Animated background ───────────────────────────────────────────────
        random.seed(77)
        for i in range(280):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H)
            phase = sx * 0.007 + i * 0.3
            br = int(abs(math.sin(t * 0.8 + phase)) * 140 + 40)
            size = 1 if i % 3 != 0 else 2
            pygame.draw.circle(surf, (br, br, min(255, br + 30)), (sx, sy), size)
        random.seed()

        # ── Decorative line ───────────────────────────────────────────────────
        line_y = 230
        line_progress = min(1.0, max(0.0, t / 1.2))  # замедлено с 0.5 до 1.2 секунд
        line_progress = 1.0 - (1.0 - line_progress) ** 3  # cubic ease-out
        max_dx = int(500 * line_progress)
        
        for dx2 in range(-max_dx, max_dx + 1):
            frac = abs(dx2) / max(1, max_dx)
            c_val = int(80 + (1 - frac) * 120)
            pygame.draw.line(surf, (c_val // 3, c_val // 2, c_val),
                             (cx + dx2, line_y), (cx + dx2, line_y + 1))

        # ── Title ─────────────────────────────────────────────────────────────
        float_y = math.sin(t * 1.5) * 8
        ty = 155 + float_y

        hue_shift = math.sin(t * 1.1) * 0.5 + 0.5
        r3 = int(120 + hue_shift * 135)
        g3 = int(160 + hue_shift * 70)
        
        glow_s = pygame.Surface((800, 180), pygame.SRCALPHA)
        glow_base_alpha = int(abs(math.sin(t * 1.2)) * 30 + 20)
        for i in range(8):
            w = 750 - i * 75
            h = 140 - i * 14
            r_rect = pygame.Rect((800 - w) // 2, (180 - h) // 2, w, h)
            pygame.draw.ellipse(glow_s, (r3 // 3, g3 // 4, 80, glow_base_alpha), r_rect)
        surf.blit(glow_s, glow_s.get_rect(center=(cx, ty)))

        title_font = pygame.font.SysFont("impact", 86)
        title_str = "pyTDS"
        
        ts_shadow = title_font.render(title_str, True, (8, 12, 20))
        surf.blit(ts_shadow, ts_shadow.get_rect(center=(cx + 4, ty + 6)))
        surf.blit(ts_shadow, ts_shadow.get_rect(center=(cx, ty + 7)))
        
        ts_main = title_font.render(title_str, True, (r3, g3, 255))
        surf.blit(ts_main, ts_main.get_rect(center=(cx, ty)))
        
        ts_bright = title_font.render(title_str, True, (255, 255, 255))
        ts_bright.set_alpha(70)
        surf.blit(ts_bright, ts_bright.get_rect(center=(cx, ty - 3)))

        if not hasattr(self, '_btn_hovers'):
            self._btn_hovers = {}
            self._grad_cache = {}

        # ── Buttons ───────────────────────────────────────────────────────────
        def draw_fancy_btn(rect, label, hov, idx, accent=(80, 120, 255)):
            btn_start_t = 0.8 + idx * 0.1
            btn_progress = min(1.0, max(0.0, (t - btn_start_t) / 0.4))
            btn_progress = 1.0 - (1.0 - btn_progress) ** 3
            if btn_progress <= 0: return
            
            anim_y = int(30 * (1.0 - btn_progress))
            alpha_val = int(255 * btn_progress)
            
            ar, ag, ab = accent
            
            if hov and btn_progress == 1.0:
                bg_l = (int(35 + ar*0.1), int(45 + ag*0.1), int(60 + ab*0.15))
                bg_d = (int(18 + ar*0.05), int(22 + ag*0.05), int(35 + ab*0.1))
            else:
                hov = False
                bg_l = (22, 26, 38)
                bg_d = (12, 15, 24)
            
            cache_key = (rect.w, rect.h, hov, bg_l, bg_d)
            if cache_key not in self._grad_cache:
                btn_s = pygame.Surface((rect.w + 12, rect.h + 16), pygame.SRCALPHA)
                
                shd_y = 6 if hov else 4
                pygame.draw.rect(btn_s, (0,0,0, 70), (6, 4 + shd_y, rect.w, rect.h), border_radius=12)
                if hov:
                    pygame.draw.rect(btn_s, (0,0,0, 40), (6, 8 + shd_y, rect.w, rect.h), border_radius=12)
                
                grad = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                for y in range(rect.h):
                    pr = y / max(1, rect.h - 1)
                    r = int(bg_l[0] + (bg_d[0] - bg_l[0]) * pr)
                    g = int(bg_l[1] + (bg_d[1] - bg_l[1]) * pr)
                    b = int(bg_l[2] + (bg_d[2] - bg_l[2]) * pr)
                    pygame.draw.line(grad, (r, g, b, 255), (0, y), (rect.w, y))
                
                pygame.draw.ellipse(grad, (255,255,255,12), (-int(rect.w*0.2), -int(rect.h*0.5), int(rect.w*1.4), int(rect.h*1.1)))
                
                mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=12)
                grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                btn_s.blit(grad, (6, 4))
                
                brd_c = tuple(min(255, int(c * (1.3 if hov else 0.8))) for c in accent)
                pygame.draw.rect(btn_s, (*brd_c, 255 if hov else 150), (6, 4, rect.w, rect.h), 2, border_radius=12)
                
                stripe = pygame.Surface((4, rect.h - 12), pygame.SRCALPHA)
                stripe.fill((*accent, 220 if hov else 140))
                btn_s.blit(stripe, (6 + 3, 4 + 6))
                
                self._grad_cache[cache_key] = btn_s

            y_shift = -2 if hov else 0
            
            cached_s = self._grad_cache[cache_key]
            if alpha_val < 255:
                temp = cached_s.copy()
                temp.set_alpha(alpha_val)
                surf.blit(temp, (rect.x - 6, rect.y - 4 + y_shift + anim_y))
            else:
                surf.blit(cached_s, (rect.x - 6, rect.y - 4 + y_shift + anim_y))

            if hov:
                if label not in self._btn_hovers:
                    self._btn_hovers[label] = t
                else:
                    while t - self._btn_hovers[label] >= 1.5:
                        self._btn_hovers[label] += 1.5
            
            if label in self._btn_hovers:
                local_t = t - self._btn_hovers[label]
                if local_t < 1.5:
                    ray_t = local_t / 1.5
                    ray_x = int(rect.w * 2.5 * ray_t) - int(rect.w * 0.8)
                    ray_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    for i in range(20):
                        alpha = max(0, 60 - abs(i - 10) * 6)
                        if alpha > 0:
                            pygame.draw.line(ray_surf, (255, 255, 255, alpha), 
                                             (ray_x + i * 2 + 30, -5), 
                                             (ray_x + i * 2 - 20, rect.h + 5), 4)
                    
                    mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=12)
                    ray_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    if alpha_val < 255:
                        ray_surf.set_alpha(alpha_val)
                    surf.blit(ray_surf, (rect.x, rect.y + y_shift + anim_y))
                else:
                    del self._btn_hovers[label]

            lf = pygame.font.SysFont("segoeui", 26, bold=True)
            txt_c = C_WHITE if hov else (190, 200, 220)
            
            ts_shadow = lf.render(label, True, (10, 15, 25))
            if alpha_val < 255: ts_shadow.set_alpha(alpha_val)
            surf.blit(ts_shadow, ts_shadow.get_rect(center=(rect.centerx, rect.centery + y_shift + anim_y + 2)))
            
            ls2 = lf.render(label, True, txt_c)
            if alpha_val < 255: ls2.set_alpha(alpha_val)
            surf.blit(ls2, ls2.get_rect(center=(rect.centerx, rect.centery + y_shift + anim_y)))
            
            if hov:
                dot_x = rect.centerx - ls2.get_width()//2 - 18
                dot_y = rect.centery + y_shift + anim_y
                dot_r = int(abs(math.sin(t * 6)) * 3 + 3)
                if alpha_val < 255:
                    dot_s = pygame.Surface((dot_r*2+4, dot_r*2+4), pygame.SRCALPHA)
                    pygame.draw.circle(dot_s, (*accent, alpha_val), (dot_r+2, dot_r+2), dot_r)
                    pygame.draw.circle(dot_s, (*C_WHITE[:3], alpha_val), (dot_r+2, dot_r+2), dot_r//2)
                    surf.blit(dot_s, (dot_x - dot_r - 2, dot_y - dot_r - 2))
                else:
                    pygame.draw.circle(surf, accent, (dot_x, dot_y), dot_r)
                    pygame.draw.circle(surf, C_WHITE, (dot_x, dot_y), dot_r//2)

        draw_fancy_btn(self.btn_play,        "PLAY",          self.btn_play.collidepoint(mx, my),         0, (60, 160, 255))
        draw_fancy_btn(self.btn_loadout,     "LOADOUT",       self.btn_loadout.collidepoint(mx, my),      1, (120, 80, 220))
        draw_fancy_btn(self.btn_shop,        "SHOP",          self.btn_shop.collidepoint(mx, my),         2, (255, 180, 40))
        draw_fancy_btn(self.btn_skilltree,   "SKILL TREE",    self.btn_skilltree.collidepoint(mx, my),    3, (60, 200, 140))
        draw_fancy_btn(self.btn_achievements,"ACHIEVEMENTS",  self.btn_achievements.collidepoint(mx, my), 4, (200, 160, 20))
        draw_fancy_btn(self.btn_settings,    "SETTINGS",      self.btn_settings.collidepoint(mx, my),     5, (60, 130, 180))
        draw_fancy_btn(self.btn_multiplayer, "MULTIPLAYER",   self.btn_multiplayer.collidepoint(mx, my),  6, (20, 160, 220))
        draw_fancy_btn(self.btn_quit,        "QUIT",          self.btn_quit.collidepoint(mx, my),         7, (180, 50, 50))

        # ── Coin counter ──────────────────────────────────────────────────────
        coins = self.save_data.get("coins", 0)
        ico_m = load_icon("coin_ico", 34)
        coin_s = pygame.font.SysFont("segoeui", 22, bold=True).render(f" {fmt_num(coins)}", True, C_WHITE)
        total_cw = (ico_m.get_width() if ico_m else 0) + coin_s.get_width() + 16
        coin_bg = pygame.Rect(SCREEN_W - total_cw - 10, 8, total_cw, 34)
        draw_rect_alpha(surf, (20, 20, 10), (coin_bg.x, coin_bg.y, coin_bg.w, coin_bg.h), 160, 8)
        pygame.draw.rect(surf, (160, 120, 20), coin_bg, 1, border_radius=8)
        if ico_m:
            surf.blit(ico_m, (coin_bg.x + 8, coin_bg.y + (34 - ico_m.get_height()) // 2))
            surf.blit(coin_s, (coin_bg.x + 8 + ico_m.get_width(), coin_bg.y + (34 - coin_s.get_height()) // 2))
        else:
            surf.blit(coin_s, coin_s.get_rect(midleft=(coin_bg.x + 8, coin_bg.centery)))

        # ── Shard counter ─────────────────────────────────────────────────────
        shards = self.save_data.get("shards", 0)
        ico_sh = load_icon("shard_ico", 28)
        shard_col2 = C_WHITE
        shard_s2 = pygame.font.SysFont("segoeui", 22, bold=True).render(f" {fmt_num(shards)}", True, C_WHITE)
        total_sw = (ico_sh.get_width() if ico_sh else 0) + shard_s2.get_width() + 16
        shard_bg = pygame.Rect(coin_bg.x - total_sw - 8, 8, total_sw, 34)
        draw_rect_alpha(surf, (5, 20, 30), (shard_bg.x, shard_bg.y, shard_bg.w, shard_bg.h), 160, 8)
        pygame.draw.rect(surf, (40, 120, 180), shard_bg, 1, border_radius=8)
        if ico_sh:
            surf.blit(ico_sh, (shard_bg.x + 8, shard_bg.y + (34 - ico_sh.get_height()) // 2))
            surf.blit(shard_s2, (shard_bg.x + 8 + ico_sh.get_width(), shard_bg.y + (34 - shard_s2.get_height()) // 2))
        else:
            shard_lbl2 = pygame.font.SysFont("segoeui", 22, bold=True).render(f"◆ {fmt_num(shards)}", True, C_WHITE)
            surf.blit(shard_lbl2, shard_lbl2.get_rect(midleft=(shard_bg.x + 8, shard_bg.centery)))

        ver = font_sm.render("v1.3", True, (40, 48, 65))
        surf.blit(ver, (10, SCREEN_H - 20))

        # ── HARDCORE BETA button — bottom-left ────────────────────────────────
        hc_btn   = self.btn_hardcore
        hc_hov   = hc_btn.collidepoint(mx, my)
        # pulsing red glow behind button
        glow_alpha = int(abs(math.sin(t * 2.4)) * 60 + 30)
        glow_surf  = pygame.Surface((hc_btn.w + 24, hc_btn.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (210, 40, 20, glow_alpha),
                         (0, 0, hc_btn.w + 24, hc_btn.h + 24), border_radius=14)
        surf.blit(glow_surf, (hc_btn.x - 12, hc_btn.y - 12))
        # button body
        hc_bg  = (100, 18, 8) if hc_hov else (72, 10, 4)
        hc_brd_col = (255, 80, 30) if hc_hov else (int(160 + abs(math.sin(t * 2.4)) * 60), 40, 18)
        pygame.draw.rect(surf, hc_bg,      hc_btn, border_radius=10)
        pygame.draw.rect(surf, hc_brd_col, hc_btn, 2, border_radius=10)
        # skull icon (drawn inline — no file needed)
        sk_x = hc_btn.x + 12
        sk_y = hc_btn.centery
        sk_r = 10
        pygame.draw.circle(surf, (230, 60, 30), (sk_x + sk_r, sk_y - 1), sk_r)
        pygame.draw.rect(surf, (230, 60, 30), (sk_x + 2, sk_y + 6, sk_r * 2 - 4, 7), border_radius=2)
        for ex, ey in [(sk_x + sk_r - 4, sk_y - 3), (sk_x + sk_r + 4, sk_y - 3)]:
            pygame.draw.circle(surf, hc_bg, (ex, ey), 3)
        # label
        hc_f1  = pygame.font.SysFont("consolas", 18, bold=True)
        hc_f2  = pygame.font.SysFont("segoeui",  12, bold=False)
        hc_lbl = hc_f1.render("HARDCORE", True, (255, 100, 60) if hc_hov else (210, 65, 30))
        hc_sub = hc_f2.render("BETA", True, (255, 200, 50))
        text_x = hc_btn.x + 36
        pass  # placeholder end of removed method

class QuestsScreen:
    """Displays all quest lines with progress tracking."""

    # ── Castbound quest definitions ───────────────────────────────────────────
    _ALL_STAGES = {
        "easy_runs","fallen_runs","frosty_run","pay_coins","pay_shards",
        "all_achievements","all_towers","max_skilltree","all_skins","moon_lord","done"
    }
    _CB_QUESTS = [
        {
            "id":    "easy_runs",
            "title": "Warmup",
            "desc":  "Complete Easy difficulty 7 times.",
            "stage": "easy_runs",
            "done_stages": {"fallen_runs","frosty_run","pay_coins","pay_shards",
                            "all_achievements","all_towers","max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "fallen_runs",
            "title": "Fallen Veteran",
            "desc":  "Complete Fallen difficulty 7 times.",
            "stage": "fallen_runs",
            "done_stages": {"frosty_run","pay_coins","pay_shards",
                            "all_achievements","all_towers","max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "frosty_run",
            "title": "Into the Cold",
            "desc":  "Complete Frosty difficulty.",
            "stage": "frosty_run",
            "done_stages": {"pay_coins","pay_shards",
                            "all_achievements","all_towers","max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "pay_coins",
            "title": "A Strange Offer",
            "desc":  "Pay Castbound 20 000 coins.",
            "stage": "pay_coins",
            "done_stages": {"pay_shards","all_achievements","all_towers",
                            "max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "pay_shards",
            "title": "Crystal Toll",
            "desc":  "Pay Castbound 5 000 shards.",
            "stage": "pay_shards",
            "done_stages": {"all_achievements","all_towers",
                            "max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "all_achievements",
            "title": "Completionist",
            "desc":  "Unlock every achievement.",
            "stage": "all_achievements",
            "done_stages": {"all_towers","max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "all_towers",
            "title": "Tower Collector",
            "desc":  "Own every tower in the game.",
            "stage": "all_towers",
            "done_stages": {"max_skilltree","all_skins","moon_lord","done"},
        },
        {
            "id":    "max_skilltree",
            "title": "Master of Skills",
            "desc":  "Max out the entire Skill Tree.",
            "stage": "max_skilltree",
            "done_stages": {"all_skins","moon_lord","done"},
        },
        {
            "id":    "all_skins",
            "title": "Collector",
            "desc":  "Own every skin in the game.",
            "stage": "all_skins",
            "done_stages": {"moon_lord","done"},
        },
        {
            "id":    "moon_lord",
            "title": "The Moon Lord",
            "desc":  "Defeat the Moon Lord.",
            "stage": "moon_lord",
            "done_stages": {"done"},
        },
    ]

    # ── Placeholder future quests ─────────────────────────────────────────────
    _FUTURE_QUESTS = []

    def __init__(self, screen, save_data):
        self.screen    = screen
        self.save_data = save_data
        self.t         = 0.0
        self.running   = True
        self._result   = None   # None = just back, "castbound" = open dialog
        self.btn_back  = pygame.Rect(SCREEN_W // 2 - 130, SCREEN_H - 74, 260, 50)
        # Castbound talk button — only visible when quest is in progress
        self.btn_talk  = pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H - 136, 300, 50)

        # ── Tabs ─────────────────────────────────────────────────────────────
        self._tab       = "daily"   # "daily" or "castbound"
        tab_w, tab_h    = 200, 38
        tab_y           = 94
        cx_tab          = SCREEN_W // 2
        self._tab_daily = pygame.Rect(cx_tab - tab_w - 4, tab_y, tab_w, tab_h)
        self._tab_cb    = pygame.Rect(cx_tab + 4,          tab_y, tab_w, tab_h)

        # ── Daily quest state ─────────────────────────────────────────────────
        self._claim_anim  = {}   # quest_id → float (0..1) for flash animation
        self._load_daily()

        MainMenu._ensure_heavy_surfaces()
        self._wisps = [_VoidWisp() for _ in range(20)]
        self._dots  = [_VoidDot()  for _ in range(60)]
        self._motes = [_VoidMote() for _ in range(30)]

    def _load_daily(self):
        """Reload daily quest state from save."""
        _, self._dq_quests, self._dq_progress, self._dq_claimed = _load_daily_quests(self.save_data)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            # Animate claim flashes
            for k in list(self._claim_anim):
                self._claim_anim[k] = max(0.0, self._claim_anim[k] - dt * 1.5)
                if self._claim_anim[k] <= 0:
                    del self._claim_anim[k]
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Tab switching
                    if self._tab_daily.collidepoint(ev.pos):
                        self._tab = "daily"; self._load_daily()
                    elif self._tab_cb.collidepoint(ev.pos):
                        self._tab = "castbound"
                    elif self.btn_back.collidepoint(ev.pos):
                        self.running = False
                    # Castbound talk button
                    quest_stage = self.save_data.get("castbound_quest", None)
                    if self._tab == "castbound" and quest_stage != "done" and self.btn_talk.collidepoint(ev.pos):
                        self._result = "castbound"
                        self.running = False
                    # Daily quest claim buttons
                    if self._tab == "daily":
                        for qid, btn_rect in getattr(self, "_claim_btns", {}).items():
                            if btn_rect.collidepoint(ev.pos):
                                if _claim_daily_reward(self.save_data, qid):
                                    self._claim_anim[qid] = 1.0
                                    self._load_daily()
            self._draw()
            pygame.display.flip()
        return self._result

    def _quest_status(self, q):
        """Return 'done', 'active', or 'locked' for a castbound quest entry."""
        stage = self.save_data.get("castbound_quest", None)
        if stage in q["done_stages"]:
            return "done"
        if stage == q["stage"]:
            return "active"
        return "locked"

    def _draw_quest_card(self, surf, rx, ry, rw, rh, title, desc, status,
                         extra_line=None, accent=None):
        """Draw a single quest card at (rx, ry) with size (rw, rh)."""
        STATUS_COLORS = {
            "done":   ((30, 80, 40),   (60, 200, 80),  "✔  COMPLETE"),
            "active": ((40, 20, 80),   (140, 80, 255), "►  IN PROGRESS"),
            "locked": ((20, 20, 30),   (70, 70, 90),   "** LOCKED"),
            "soon":   ((10, 10, 20),   (50, 50, 70),   ".. COMING SOON"),
        }
        bg_col, brd_col, status_lbl = STATUS_COLORS[status]

        card = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.rect(card, (*bg_col, 210), (0, 0, rw, rh), border_radius=10)
        pygame.draw.rect(card, (*brd_col, 255), (0, 0, rw, rh), 2, border_radius=10)

        # Left status stripe
        stripe_col = brd_col if status != "locked" else (50, 50, 60)
        pygame.draw.rect(card, (*stripe_col, 200), (0, 8, 4, rh - 16), border_radius=2)

        surf.blit(card, (rx, ry))

        # Title
        tf = pygame.font.SysFont("segoeui", 20, bold=True)
        title_col = (240, 240, 255) if status != "locked" else (100, 100, 120)
        ts = tf.render(title, True, title_col)
        surf.blit(ts, (rx + 16, ry + 10))

        # Description
        df = pygame.font.SysFont("segoeui", 15)
        desc_col = (180, 180, 210) if status != "locked" else (70, 70, 90)
        ds = df.render(desc, True, desc_col)
        surf.blit(ds, (rx + 16, ry + 34))

        # Extra progress line
        if extra_line:
            ef = pygame.font.SysFont("segoeui", 14)
            es = ef.render(extra_line, True, (160, 200, 255))
            surf.blit(es, (rx + 16, ry + rh - 22))

        # Status badge — right-aligned
        bf = pygame.font.SysFont("segoeui", 14, bold=True)
        bs = bf.render(status_lbl, True, brd_col)
        surf.blit(bs, (rx + rw - bs.get_width() - 14,
                       ry + rh // 2 - bs.get_height() // 2))

    def _draw(self):
        surf   = self.screen
        t      = self.t
        cx     = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()
        dt     = 1 / 60.0

        # ── Background ───────────────────────────────────────────────────────
        _draw_menu_bg(surf, overlay_alpha=80)
        for w in self._wisps:  w.update(dt); w.draw(surf)
        for p in self._dots:   p.update();   p.draw(surf)
        for e in self._motes:  e.update(dt); e.draw(surf)
        if MainMenu._vig_surf_cached is not None:
            surf.blit(MainMenu._vig_surf_cached, (0, 0))

        # ── Header ────────────────────────────────────────────────────────────
        pulse  = 0.5 + 0.5 * math.sin(t * 1.6)
        hdr_col = (
            int(130 + 70  * pulse),
            int(90  + 50  * pulse),
            int(220 + 35  * pulse),
        )
        hf = pygame.font.SysFont("segoeui", 42, bold=True)
        hs = hf.render("QUESTS", True, hdr_col)

        # Glow behind header
        glow_s = pygame.Surface((hs.get_width() + 60, hs.get_height() + 24), pygame.SRCALPHA)
        ga = int(40 + 30 * pulse)
        pygame.draw.rect(glow_s, (100, 50, 200, ga), glow_s.get_rect(), border_radius=12)
        surf.blit(glow_s, glow_s.get_rect(center=(cx, 50)))
        surf.blit(hs, hs.get_rect(center=(cx, 50)))

        # ── Tabs ──────────────────────────────────────────────────────────────
        for tab_id, tab_rect, label in [
            ("daily",      self._tab_daily, "[ DAILY ]"),
            ("castbound",  self._tab_cb,    "[ CASTBOUND ]"),
        ]:
            active   = self._tab == tab_id
            hov      = tab_rect.collidepoint(mx, my)
            bg_col   = (40, 20, 80)  if active else ((25, 12, 50) if hov else (12, 6, 24))
            brd_col  = (180, 100, 255) if active else ((100, 60, 180) if hov else (50, 30, 90))
            pygame.draw.rect(surf, bg_col,  tab_rect, border_radius=8)
            pygame.draw.rect(surf, brd_col, tab_rect, 2, border_radius=8)
            if active:
                pygame.draw.rect(surf, brd_col, (tab_rect.x, tab_rect.bottom - 2, tab_rect.w, 2))
            tf = pygame.font.SysFont("segoeui", 18, bold=True)
            tc = (230, 200, 255) if active else (140, 110, 200)
            ts = tf.render(label, True, tc)
            surf.blit(ts, ts.get_rect(center=tab_rect.center))

        # Divider line under tabs
        pygame.draw.rect(surf, (60, 30, 110), (cx - 220, self._tab_daily.bottom, 440, 1))

        # ── Content by tab ────────────────────────────────────────────────────
        if self._tab == "daily":
            self._draw_daily(surf, t, cx, mx, my, pulse)
        else:
            self._draw_castbound(surf, t, cx, mx, my, pulse)

        # ── Back button ───────────────────────────────────────────────────────
        hov = self.btn_back.collidepoint(mx, my)
        bg_c  = (60, 30, 120) if hov else (28, 16, 55)
        brd_c = (160, 100, 255) if hov else (80, 50, 140)
        pygame.draw.rect(surf, bg_c,  self.btn_back, border_radius=10)
        pygame.draw.rect(surf, brd_c, self.btn_back, 2, border_radius=10)
        bbf = pygame.font.SysFont("segoeui", 22, bold=True)
        bbs = bbf.render("← BACK", True, (220, 200, 255) if hov else (150, 120, 200))
        surf.blit(bbs, bbs.get_rect(center=self.btn_back.center))

    def _draw_daily(self, surf, t, cx, mx, my, pulse):
        """Draw the daily quests tab content."""
        today_str = _get_today_str()

        # Time until next reset
        now      = _dt.datetime.now()
        tomorrow = _dt.datetime.combine(_dt.date.today() + _dt.timedelta(days=1), _dt.time.min)
        secs_left = int((tomorrow - now).total_seconds())
        h_left, rem = divmod(secs_left, 3600)
        m_left = rem // 60
        reset_lbl = f"Resets in: {h_left:02d}:{m_left:02d}"

        rf = pygame.font.SysFont("segoeui", 16)
        rs = rf.render(reset_lbl, True, (140, 120, 200))
        surf.blit(rs, (cx - rs.get_width() // 2, self._tab_daily.bottom + 8))

        card_w   = min(700, SCREEN_W - 80)
        card_h   = 116
        card_gap = 12
        start_x  = cx - card_w // 2
        start_y  = self._tab_daily.bottom + 34

        self._claim_btns = {}

        for i, q in enumerate(self._dq_quests):
            qid     = q["id"]
            target  = q["target"]
            prog    = min(self._dq_progress.get(qid, 0), target)
            claimed = qid in self._dq_claimed
            done    = prog >= target

            # Slide-in
            slide_t = min(1.0, max(0.0, (t - i * 0.10) / 0.35))
            slide_t = 1.0 - (1.0 - slide_t) ** 3

            ry  = start_y + i * (card_h + card_gap)
            rx  = start_x + int(30 * (1.0 - slide_t))

            # Claim flash
            flash_v = self._claim_anim.get(qid, 0.0)

            # Card background
            if claimed:
                bg_c  = (20, 60, 28)
                brd_c = (50, 160, 70)
            elif done:
                bg_c  = (60, 45, 10)
                brd_c = (220, 180, 40)
            else:
                bg_c  = (16, 12, 32)
                brd_c = (70, 50, 120)

            if flash_v > 0:
                brd_c = (int(brd_c[0] + (255-brd_c[0])*flash_v),
                         int(brd_c[1] + (255-brd_c[1])*flash_v),
                         int(brd_c[2]))

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (*bg_c, 210), (0, 0, card_w, card_h), border_radius=12)
            pygame.draw.rect(card_surf, (*brd_c, 255), (0, 0, card_w, card_h), 2, border_radius=12)

            # Left stripe
            pygame.draw.rect(card_surf, (*brd_c, 200), (0, 8, 4, card_h - 16), border_radius=2)

            # Title
            title_col = (240, 240, 255) if not claimed else (130, 220, 140)
            tf2 = pygame.font.SysFont("segoeui", 21, bold=True)
            ts2 = tf2.render(q["title"], True, title_col)
            card_surf.blit(ts2, (16, 9))

            # Description
            df2 = pygame.font.SysFont("segoeui", 15)
            ds2 = df2.render(q["desc"], True, (170, 160, 210))
            card_surf.blit(ds2, (16, 34))

            # ── Reward row (prominent, right-aligned block) ───────────────────
            _ico_size = 20
            _rwf_lbl = pygame.font.SysFont("segoeui", 13)
            _rwf_val = pygame.font.SysFont("segoeui", 17, bold=True)
            _lbl_s   = _rwf_lbl.render("REWARD", True, (110, 100, 160))
            # Position: top-right corner of card
            _rw_right = card_w - 14
            _rw_top   = 8

            # Draw label above icons
            card_surf.blit(_lbl_s, (_rw_right - _lbl_s.get_width(), _rw_top))
            _rw_top += _lbl_s.get_height() + 2

            # Coin reward
            _rw_x_cur = _rw_right
            if q["shards"] > 0:
                _shard_s = _rwf_val.render(f"{q['shards']}", True, (100, 210, 255))
                _rw_x_cur -= _shard_s.get_width()
                card_surf.blit(_shard_s, (_rw_x_cur, _rw_top))
                _rw_x_cur -= _ico_size + 2
                _shard_ico = load_icon("shard_ico", _ico_size)
                if _shard_ico:
                    card_surf.blit(_shard_ico, (_rw_x_cur, _rw_top - 1))
                _rw_x_cur -= 8
            if q["coins"] > 0:
                _coin_s = _rwf_val.render(f"{q['coins']}", True, (240, 200, 70))
                _rw_x_cur -= _coin_s.get_width()
                card_surf.blit(_coin_s, (_rw_x_cur, _rw_top))
                _rw_x_cur -= _ico_size + 2
                _coin_ico = load_icon("coin_ico", _ico_size)
                if _coin_ico:
                    card_surf.blit(_coin_ico, (_rw_x_cur, _rw_top - 1))

            # ── Progress bar ──────────────────────────────────────────────────
            bar_x, bar_y = 16, 57
            bar_w = card_w - 180   # leave room for reward block on right
            bar_h = 11
            pygame.draw.rect(card_surf, (30, 20, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            fill_w = int(bar_w * prog / max(target, 1))
            if fill_w > 0:
                bar_col = (80, 200, 100) if claimed else ((220, 170, 30) if done else (100, 80, 200))
                pygame.draw.rect(card_surf, bar_col, (bar_x, bar_y, fill_w, bar_h), border_radius=5)

            # Progress text + percentage
            pf  = pygame.font.SysFont("segoeui", 14, bold=True)
            pct = int(100 * prog / max(target, 1))
            ps  = pf.render(f"{prog} / {target}  ({pct}%)", True, (180, 165, 220))
            card_surf.blit(ps, (bar_x, bar_y + 14))

            card_surf.set_alpha(int(255 * slide_t))
            surf.blit(card_surf, (rx, ry))

            # Claim button (drawn directly on surf so it can be hit-tested)
            btn_w, btn_h = 130, 38
            btn_rx = rx + card_w - btn_w - 14
            btn_ry = ry + card_h - btn_h - 10
            btn_rect = pygame.Rect(btn_rx, btn_ry, btn_w, btn_h)
            self._claim_btns[qid] = btn_rect

            if claimed:
                pygame.draw.rect(surf, (20, 55, 28), btn_rect, border_radius=8)
                pygame.draw.rect(surf, (40, 130, 55), btn_rect, 2, border_radius=8)
                bf2 = pygame.font.SysFont("segoeui", 16, bold=True)
                bs2 = bf2.render("[v] CLAIMED", True, (80, 200, 100))
                surf.blit(bs2, bs2.get_rect(center=btn_rect.center))
            elif done:
                hov_b = btn_rect.collidepoint(mx, my)
                bg_b  = (80, 60, 10) if hov_b else (50, 40, 8)
                brd_b = (255, 210, 50) if hov_b else (180, 150, 30)
                pygame.draw.rect(surf, bg_b,  btn_rect, border_radius=8)
                pygame.draw.rect(surf, brd_b, btn_rect, 2, border_radius=8)
                bf2 = pygame.font.SysFont("segoeui", 16, bold=True)
                bs2 = bf2.render("CLAIM", True, (255, 220, 60) if hov_b else (200, 170, 30))
                surf.blit(bs2, bs2.get_rect(center=btn_rect.center))
            else:
                pygame.draw.rect(surf, (20, 15, 35), btn_rect, border_radius=8)
                pygame.draw.rect(surf, (55, 40, 90), btn_rect, 2, border_radius=8)
                bf2 = pygame.font.SysFont("segoeui", 15)
                bs2 = bf2.render("IN PROGRESS", True, (90, 75, 130))
                surf.blit(bs2, bs2.get_rect(center=btn_rect.center))

    def _draw_castbound(self, surf, t, cx, mx, my, pulse):

        card_w  = min(680, SCREEN_W - 80)
        card_h  = 72
        card_gap = 10
        start_x = cx - card_w // 2
        start_y = self._tab_daily.bottom + 34

        stage       = self.save_data.get("castbound_quest", None)
        easy_runs   = self.save_data.get("castbound_easy_runs", 0)
        fallen_runs = self.save_data.get("castbound_fallen_runs", 0)
        frosty_done = self.save_data.get("castbound_frosty_run", False)
        abn_kills   = self.save_data.get("castbound_abnormal_kills", 0)

        for i, q in enumerate(self._CB_QUESTS):
            status = self._quest_status(q)
            ry = start_y + i * (card_h + card_gap)

            # Slide-in animation
            slide_t = min(1.0, max(0.0, (t - i * 0.07) / 0.3))
            slide_t = 1.0 - (1.0 - slide_t) ** 3
            alpha = int(255 * slide_t)
            anim_x = int(30 * (1.0 - slide_t))

            # Extra progress info
            extra = None
            qid = q["id"]
            if qid == "easy_runs":
                n = min(easy_runs, 7)
                extra = f"Progress: {n} / 7 runs" if status == "active" else (f"Completed: {n} / 7" if status == "done" else None)
            elif qid == "fallen_runs":
                n = min(fallen_runs, 7)
                extra = f"Progress: {n} / 7 runs" if status == "active" else (f"Completed: {n} / 7" if status == "done" else None)
            elif qid == "frosty_run":
                extra = "Progress: 1 / 1" if status == "done" else ("In progress..." if status == "active" else None)
            elif qid == "all_achievements":
                from game_core import ACHIEVEMENT_DEFS
                unlocked = load_achievements().get("unlocked", [])
                n = len(unlocked); total = len(ACHIEVEMENT_DEFS)
                extra = f"Progress: {n} / {total}" if status in ("active","done") else None
            elif qid == "all_towers":
                _owned = list(self.save_data.get("owned_units", []))
                n_owned = len(set(_owned))
                total_t = len({u["name"] for u in ALL_UNITS_POOL})
                extra = f"Progress: {n_owned} / {total_t} towers" if status in ("active","done") else None
            elif qid == "max_skilltree":
                st = self.save_data.get("skill_tree", {})
                total_pts = sum(st.values())
                extra = f"Skill points spent: {total_pts}" if status in ("active","done") else None
            elif qid == "all_skins":
                owned_skins = load_skins().get("owned", [])
                n = len(owned_skins); total_sk = len(ALL_SKIN_DEFS)
                extra = f"Progress: {n} / {total_sk} skins" if status in ("active","done") else None

            # Draw card to temp surface for alpha/slide-in
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            self._draw_quest_card(card_surf, 0, 0, card_w, card_h,
                                  q["title"], q["desc"], status, extra)
            card_surf.set_alpha(alpha)
            surf.blit(card_surf, (start_x + anim_x, ry))

        # ── Talk to Castbound button ──────────────────────────────────────────
        quest_stage = self.save_data.get("castbound_quest", None)
        _show_btn = quest_stage != "done"

        if _show_btn:
            hov_t = self.btn_talk.collidepoint(mx, my)
            if quest_stage is None:
                bg_t  = (20, 60, 30) if hov_t else (10, 30, 18)
                brd_t = (80, 220, 100) if hov_t else (50, 150, 70)
                lbl_t = "▶  Start Castbound Quest"
                lbl_c = (180, 255, 180) if hov_t else (120, 200, 140)
            else:
                cb_p  = 0.5 + 0.5 * math.sin(t * 3.0)
                bg_t  = (30, 10, 60) if hov_t else (16, 6, 36)
                brd_t = (int(100 + 80*cb_p), int(40 + 20*cb_p), int(180 + 60*cb_p))
                lbl_t = "◈  Talk to Castbound"
                lbl_c = (210, 150, 255) if hov_t else (150, 90, 220)
            pygame.draw.rect(surf, bg_t,  self.btn_talk, border_radius=10)
            pygame.draw.rect(surf, brd_t, self.btn_talk, 2, border_radius=10)
            btf = pygame.font.SysFont("segoeui", 22, bold=True)
            bts = btf.render(lbl_t, True, lbl_c)
            surf.blit(bts, bts.get_rect(center=self.btn_talk.center))


# ── Castbound Dialog ───────────────────────────────────────────────────────────
class CastboundDialog:
    """Mysterious NPC dialog for the 10-stage Castbound quest chain."""

    # Coins cost for stage 4, shards cost for stage 5
    _COIN_COST  = 20000
    _SHARD_COST = 5000

    # Quest stages (in order):
    #   None           → not started
    #   "easy_runs"    → beat Easy x7
    #   "fallen_runs"  → beat Fallen x7
    #   "frosty_run"   → beat Frosty x1
    #   "pay_coins"    → pay 20k coins
    #   "pay_shards"   → pay 5k shards
    #   "all_achievements" → unlock all achievements
    #   "all_towers"   → own all towers
    #   "max_skilltree"→ max skill tree
    #   "all_skins"    → own all skins
    #   "moon_lord"    → defeat Moon Lord
    #   "done"         → all done

    def __init__(self, screen, save_data):
        self.screen    = screen
        self.save_data = save_data
        self._t        = 0.0
        self._done     = False
        self._result   = "menu"

        # Dialog box dimensions
        dw, dh = 680, 340
        self._rect = pygame.Rect(
            SCREEN_W // 2 - dw // 2,
            SCREEN_H // 2 - dh // 2,
            dw, dh
        )

        # Typewriter state
        self._phase         = "nag"
        self._full_text     = ""
        self._visible_chars = 0
        self._char_timer    = 0.0
        self._char_delay    = 0.042
        self._reply_text    = ""
        self._reply_chars   = 0
        self._reply_timer   = 0.0
        self._quest_timer   = 0.0
        self._quest_pause   = 5.0
        self._quest_paused  = False

        # Moon Lord reveal
        self._ml_phase      = 0
        self._ml_text1      = "Good job. Now fight the.."
        self._ml_text2      = "Moon Lord"
        self._ml_chars1     = 0
        self._ml_chars2     = 0
        self._ml_timer      = 0.0
        self._ml_char_delay = 0.12
        self._ml_shake_t    = 0.0

        # Pay-choice buttons (coins/shards)
        bw, bh = 160, 44
        cx = self._rect.centerx
        by = self._rect.bottom - 64
        self._btn_pay = pygame.Rect(cx - bw - 10, by, bw, bh)
        self._btn_no  = pygame.Rect(cx + 10,       by, bw, bh)
        # What currency the pay prompt is for ("coins" or "shards")
        self._pay_mode = "coins"

        # Fonts & icons
        self._f_main = pygame.font.SysFont("segoeui", 26, bold=True)
        self._f_sub  = pygame.font.SysFont("segoeui", 20, bold=False)
        self._f_btn  = pygame.font.SysFont("segoeui", 22, bold=True)
        self._coin_ico  = load_icon("coin_ico",  26)
        self._shard_ico = load_icon("shard_ico", 26)

        # ── Gather all quest-check data ──────────────────────────────────────
        qs = self.save_data.get("castbound_quest", None)

        easy_runs    = self.save_data.get("castbound_easy_runs",   0)
        fallen_runs  = self.save_data.get("castbound_fallen_runs", 0)
        frosty_done  = self.save_data.get("castbound_frosty_run",  False)

        coins  = self.save_data.get("coins",  0)
        shards = self.save_data.get("shards", 0)

        unlocked_ach = load_achievements().get("unlocked", [])
        all_ach_done = len(unlocked_ach) >= len(ACHIEVEMENT_DEFS)

        _owned_raw = list(self.save_data.get("owned_units", []))
        _all_towers = {u["name"] for u in ALL_UNITS_POOL}
        all_towers_done = _all_towers.issubset(set(_owned_raw))

        st = self.save_data.get("skill_tree", {})
        # "max skill tree" = every defined skill is at a non-zero level.
        # We consider it maxed when total points >= a threshold — check skill_tree.py isn't
        # loaded here, so we use a heuristic: all skills from save have > 0 and there are
        # at least 6 distinct skills with points.
        _st_skills = [k for k, v in st.items() if v > 0]
        all_skills_maxed = len(_st_skills) >= 6 and all(v >= 5 for v in st.values() if v)

        owned_skins  = load_skins().get("owned", [])
        all_skins_done = len(owned_skins) >= len(ALL_SKIN_DEFS)

        # ── State machine: decide what dialog to show ────────────────────────
        if qs is None:
            # Not started — ask player to begin
            self._start_choice_text("To prove yourself, complete my trials. Begin?")

        elif qs == "easy_runs":
            if easy_runs >= 7:
                self._advance_quest("fallen_runs")
                self._start_nag("Warmup done. Now beat Fallen 7 times.")
            else:
                self._start_nag(f"Keep going. Easy runs: {easy_runs}/7")

        elif qs == "fallen_runs":
            if fallen_runs >= 7:
                self._advance_quest("frosty_run")
                self._start_nag("Good. Now conquer the Frosty world once.")
            else:
                self._start_nag(f"Not done yet. Fallen runs: {fallen_runs}/7")

        elif qs == "frosty_run":
            if frosty_done:
                self._advance_quest("pay_coins")
                self._start_nag("Cold enough. Now pay me 20 000 coins.")
            else:
                self._start_nag("Beat Frosty once. Can't be that hard.")

        elif qs == "pay_coins":
            # Show pay dialog for coins
            self._pay_mode = "coins"
            self._start_choice_text("Pay me 20 000 coins to continue.")

        elif qs == "pay_shards":
            # Show pay dialog for shards
            self._pay_mode = "shards"
            self._start_choice_text("Now pay me 5 000 shards.")

        elif qs == "all_achievements":
            if all_ach_done:
                self._advance_quest("all_towers")
                self._start_nag("Impressive. Now own every tower.")
            else:
                n = len(unlocked_ach); total = len(ACHIEVEMENT_DEFS)
                self._start_nag(f"Not all achievements. You have {n}/{total}.")

        elif qs == "all_towers":
            if all_towers_done:
                self._advance_quest("max_skilltree")
                self._start_nag("Nice collection. Max out your skill tree.")
            else:
                n = len(set(_owned_raw) & _all_towers); total = len(_all_towers)
                self._start_nag(f"You only have {n}/{total} towers. Get more.")

        elif qs == "max_skilltree":
            if all_skills_maxed:
                self._advance_quest("all_skins")
                self._start_nag("Skills maxed. Now collect every skin.")
            else:
                self._start_nag("Skill tree not maxed. Keep investing.")

        elif qs == "all_skins":
            if all_skins_done:
                self._advance_quest("moon_lord")
                self._start_moon_lord()
            else:
                n = len(owned_skins); total = len(ALL_SKIN_DEFS)
                self._start_nag(f"Only {n}/{total} skins. Collect them all.")

        elif qs == "moon_lord":
            # Launch fight immediately
            self._done   = True
            self._result = "moon_lord_fight"

        elif qs == "done":
            _owned_cb = list(self.save_data.get("owned_units", []))
            if "Castbound" not in _owned_cb:
                _owned_cb.append("Castbound")
                self.save_data["owned_units"] = _owned_cb
                write_save(self.save_data)
            self._start_nag("You've proven yourself.\nYou deserve this.\nUnlocked Castbound.")

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _advance_quest(self, new_stage):
        self.save_data["castbound_quest"] = new_stage
        write_save(self.save_data)

    def _start_nag(self, text):
        self._phase       = "nag"
        self._reply_text  = text
        self._reply_chars = 0
        self._reply_timer = 0.0
        self._quest_timer = 0.0

    def _start_choice_text(self, text):
        """Typewrite text then show Pay / No buttons."""
        self._phase         = "typing"
        self._full_text     = text
        self._visible_chars = 0
        self._char_timer    = 0.0

    def _start_moon_lord(self):
        self._phase      = "moon_lord"
        self._ml_phase   = 0
        self._ml_chars1  = 0
        self._ml_chars2  = 0
        self._ml_timer   = 0.0
        self._ml_shake_t = 0.0

    # ── Drawing helpers ───────────────────────────────────────────────────────
    def _draw_panel(self):
        surf = self.screen
        r    = self._rect
        panel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (8, 6, 18, 230), (0, 0, r.w, r.h), border_radius=14)
        pygame.draw.rect(panel, (180, 140, 255, 180), (0, 0, r.w, r.h), 2, border_radius=14)
        surf.blit(panel, (r.x, r.y))
        title_s = self._f_main.render("CASTBOUND", True, (160, 100, 255))
        surf.blit(title_s, (r.centerx - title_s.get_width() // 2, r.y + 14))
        pygame.draw.line(surf, (100, 70, 180),
                         (r.x + 20, r.y + 50), (r.right - 20, r.y + 50), 1)

    def _draw_typewriter(self, text_visible):
        surf   = self.screen
        r      = self._rect
        base_x = r.x + 30
        base_y = r.y + 68
        x_cur  = base_x
        for ch in text_visible:
            cs = self._f_main.render(ch, True, (230, 220, 255))
            surf.blit(cs, (x_cur, base_y))
            x_cur += cs.get_width()
        # If fully typed and coins mode, draw icon after text
        if len(text_visible) == len(self._full_text):
            ico = self._coin_ico if self._pay_mode == "coins" else self._shard_ico
            if ico:
                surf.blit(ico, (x_cur + 6,
                                base_y + (self._f_main.get_height() - ico.get_height()) // 2))

    def _draw_reply(self):
        surf    = self.screen
        r       = self._rect
        visible = self._reply_text[:self._reply_chars]
        lines   = visible.split("\n")
        line_h  = self._f_main.get_height() + 8
        base_y  = r.y + 68
        for i, line in enumerate(lines):
            col = (220, 180, 255) if i == 2 else (255, 200, 80)
            lbl = self._f_main.render(line, True, col)
            surf.blit(lbl, (r.centerx - lbl.get_width() // 2, base_y + i * line_h))

    def _draw_buttons(self, mx, my):
        surf = self.screen
        if self._pay_mode == "coins":
            pay_label = "Pay"
            pay_color = (60, 200, 80)
        else:
            pay_label = "Pay"
            pay_color = (60, 140, 220)
        for btn, label, ac in [
            (self._btn_pay, pay_label, pay_color),
            (self._btn_no,  "No",      (200, 60, 60)),
        ]:
            hov = btn.collidepoint(mx, my)
            bg  = (*ac, 200) if hov else (20, 16, 36, 210)
            brd = ac if hov else (130, 100, 200)
            bs  = pygame.Surface((btn.w, btn.h), pygame.SRCALPHA)
            pygame.draw.rect(bs, bg,  (0, 0, btn.w, btn.h), border_radius=8)
            pygame.draw.rect(bs, brd, (0, 0, btn.w, btn.h), 2, border_radius=8)
            surf.blit(bs, (btn.x, btn.y))
            lbl = self._f_btn.render(label, True, (255, 255, 255))
            surf.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                            btn.centery - lbl.get_height() // 2))

    def _draw_moon_lord(self):
        surf   = self.screen
        r      = self._rect
        cx     = r.centerx
        base_y = r.y + 68
        if self._ml_phase == 0:
            return
        visible1 = self._ml_text1[:self._ml_chars1]
        lbl1 = self._f_main.render(visible1, True, (255, 200, 80))
        surf.blit(lbl1, (cx - lbl1.get_width() // 2, base_y))
        if self._ml_phase >= 2 and self._ml_chars2 > 0:
            visible2 = self._ml_text2[:self._ml_chars2]
            ml_font  = pygame.font.SysFont("segoeui", 38, bold=True)
            ml_surf  = ml_font.render(visible2, True, (220, 30, 30))
            shake_mag = min(6, int(self._ml_shake_t * 2))
            shake_x   = random.randint(-shake_mag, shake_mag)
            shake_y   = random.randint(-shake_mag, shake_mag)
            dest_x = cx - ml_surf.get_width() // 2 + shake_x
            dest_y = base_y + self._f_main.get_height() + 18 + shake_y
            surf.blit(ml_surf, (dest_x, dest_y))

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while not self._done:
            dt     = clock.tick(60) / 1000.0
            self._t += dt
            mx, my = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self._phase == "choice":
                        if self._btn_no.collidepoint(ev.pos):
                            self._start_nag("bye")
                        elif self._btn_pay.collidepoint(ev.pos):
                            if self._pay_mode == "coins":
                                coins = self.save_data.get("coins", 0)
                                qs    = self.save_data.get("castbound_quest", None)
                                if qs is None:
                                    # Starting quest — no coin cost, just advance
                                    self._advance_quest("easy_runs")
                                    self._start_nag("Good. Beat Easy 7 times. Start now.")
                                elif qs == "pay_coins":
                                    if coins < self._COIN_COST:
                                        self._start_nag("you are poor")
                                    else:
                                        self.save_data["coins"] = coins - self._COIN_COST
                                        self._advance_quest("pay_shards")
                                        self._start_nag("Good. Now pay 5 000 shards.")
                            elif self._pay_mode == "shards":
                                shards = self.save_data.get("shards", 0)
                                if shards < self._SHARD_COST:
                                    self._start_nag("Not enough shards.")
                                else:
                                    self.save_data["shards"] = shards - self._SHARD_COST
                                    self._advance_quest("all_achievements")
                                    self._start_nag("Now unlock every achievement.")

            # ── Update typewriter ──────────────────────────────────────────────
            if self._phase == "typing":
                self._char_timer += dt
                while self._char_timer >= self._char_delay and self._visible_chars < len(self._full_text):
                    self._char_timer -= self._char_delay
                    self._visible_chars += 1
                if self._visible_chars >= len(self._full_text):
                    self._phase = "choice"

            elif self._phase in ("reply", "nag"):
                self._reply_timer += dt
                while self._reply_timer >= self._char_delay and self._reply_chars < len(self._reply_text):
                    self._reply_timer -= self._char_delay
                    self._reply_chars += 1
                if self._reply_chars >= len(self._reply_text):
                    self._quest_timer += dt
                    pause = 3.0 if "\n" in self._reply_text else 1.8
                    if self._quest_timer > pause:
                        self._done = True

            elif self._phase == "moon_lord":
                self._ml_timer   += dt
                self._ml_shake_t += dt
                if self._ml_phase == 0:
                    if self._ml_timer >= 2.0:
                        self._ml_phase = 1; self._ml_timer = 0.0
                elif self._ml_phase == 1:
                    while self._ml_timer >= self._char_delay and self._ml_chars1 < len(self._ml_text1):
                        self._ml_timer -= self._char_delay; self._ml_chars1 += 1
                    if self._ml_chars1 >= len(self._ml_text1):
                        self._ml_phase = 2; self._ml_timer = 0.0; self._ml_shake_t = 0.0
                elif self._ml_phase == 2:
                    while self._ml_timer >= self._ml_char_delay and self._ml_chars2 < len(self._ml_text2):
                        self._ml_timer -= self._ml_char_delay; self._ml_chars2 += 1
                    if self._ml_chars2 >= len(self._ml_text2):
                        self._ml_phase = 3
                elif self._ml_phase == 3:
                    if self._ml_timer >= 3.0:
                        self._done = True

            # ── Draw ──────────────────────────────────────────────────────────
            dim = _get_dim_surf(); dim.fill((0, 0, 0, 140))
            self.screen.blit(dim, (0, 0))
            self._draw_panel()

            if self._phase == "typing":
                self._draw_typewriter(self._full_text[:self._visible_chars])
            elif self._phase == "choice":
                self._draw_typewriter(self._full_text)
                self._draw_buttons(mx, my)
            elif self._phase in ("reply", "nag"):
                self._draw_reply()
            elif self._phase == "moon_lord":
                self._draw_moon_lord()

            pygame.display.flip()

        return self._result


# ── Loadout Screen ──────────────────────────────────────────────────────────────
ALL_UNITS_POOL = [
    {"name": "Assassin",       "rarity": "starter"},
    {"name": "Militant",       "rarity": "starter"},
    {"name": "Twitgunner",     "rarity": "starter"},
    {"name": "Korzhik",        "rarity": "apex"},
    {"name": "Conduit",        "rarity": "rare"},
    {"name": "Accelerator",    "rarity": "epic"},
    {"name": "Frostcelerator", "rarity": "epic"},
    {"name": "Lifestealer",    "rarity": "common"},
    {"name": "Archer",         "rarity": "rare"},
    {"name": "Red Ball",       "rarity": "rare"},
    {"name": "Farm",           "rarity": "starter"},
    {"name": "Swarmer",        "rarity": "common"},
    {"name": "Freezer",        "rarity": "starter"},
    {"name": "Frost Blaster",  "rarity": "common"},
    {"name": "Sledger",        "rarity": "common"},
    {"name": "Gladiator",      "rarity": "starter"},
    {"name": "Toxic Gunner",   "rarity": "common"},
    {"name": "Slasher",        "rarity": "rare"},
    {"name": "Cowboy",         "rarity": "starter"},
    {"name": "Hallow Punk",    "rarity": "rare"},
    {"name": "Spotlight Tech", "rarity": "common"},
    {"name": "Snowballer",     "rarity": "rare"},
    {"name": "Commando",       "rarity": "starter"},
    {"name": "Warlock",      "rarity": "epic"},
    {"name": "Caster",       "rarity": "epic"},
    {"name": "Jester",       "rarity": "apex"},
    {"name": "Rubber Duck",  "rarity": "common"},
    {"name": "Harvester",   "rarity": "epic"},
    {"name": "Control Panel", "rarity": "apex"},
    {"name": "Castbound",    "rarity": "singularity"},

]

# Coin cost to unlock units (None = not purchasable / exclusive)
UNIT_SHOP_PRICES = {
    "Assassin":       None,
    "Twitgunner":     None,
    "Korzhik":        None,   # Mythic — purchased with 1500 shards
    "Conduit":        3000,   # Early Access — free
    "Militant":       300,
    "Archer":         1000,
    "Swarmer":        600,
    "Lifestealer":    300,
    "Accelerator":    4000,
    "Red Ball":       500,
    "Farm":           200,
    "Frostcelerator": None,
    "Freezer":        300,
    "Frost Blaster":  750,
    "Sledger":        2000,
    "Gladiator":      2500,
    "Toxic Gunner":   800,
    "Slasher":        3000,
    "Golden Cowboy":  None,  # legacy key kept for save compat
    "Cowboy":         None,
    "Hallow Punk":    600,
    "Spotlight Tech": 2000,
    "Snowballer":     700,
    "Commando":       400,
    "hacker_laser_effects_test": None,
    "Caster": 7500,
    "Warlock": 3000,
    "Jester": None,
    "Rubber Duck": 1300,
    "Harvester":   5000,
    "Control Panel": None,   # Early Access — free to unlock
    "Castbound":     None,   # не продаётся — открывается за убийство Moon Lord
}

# ── Base stats for detail panel ───────────────────────────────────────────────
# Format: cost, limit, damage, firerate, range, income (None if not applicable)
UNIT_BASE_STATS = {
    # cost = PLACE_COST from units.py (in-game placement price)
    "Assassin":       {"cost": 300,  "limit": 5,  "damage": 50,   "firerate": 1.2,  "range": 7,  "income": None},
    "Militant":       {"cost": 600,  "limit": 6,  "damage": 30,   "firerate": 1.5,  "range": 6,  "income": None},
    "Twitgunner":     {"cost": 350,  "limit": 6,  "damage": 20,   "firerate": 3.0,  "range": 6,  "income": None},
    "Lifestealer":    {"cost": 400,  "limit": 5,  "damage": 40,   "firerate": 1.0,  "range": 6,  "income": None},
    "Archer":         {"cost": 600,  "limit": 8,  "damage": 45,   "firerate": 1.1,  "range": 9,  "income": None},
    "Red Ball":       {"cost": 1250, "limit": 4,  "damage": 80,   "firerate": 0.8,  "range": 7,  "income": None},
    "Farm":           {"cost": 250,  "limit": 5,  "damage": 0,    "firerate": 0.0,  "range": 0,  "income": 150},
    "Cowboy":         {"cost": 550,  "limit": 4,  "damage": 60,   "firerate": 1.0,  "range": 8,  "income": 50},
    "Swarmer":        {"cost": 900,  "limit": 14, "damage": 25,   "firerate": 2.0,  "range": 7,  "income": None},
    "Freezer":        {"cost": 400,  "limit": 5,  "damage": 20,   "firerate": 1.0,  "range": 7,  "income": None},
    "Frost Blaster":  {"cost": 800,  "limit": 4,  "damage": 55,   "firerate": 1.2,  "range": 8,  "income": None},
    "Sledger":        {"cost": 950,  "limit": 3,  "damage": 200,  "firerate": 0.5,  "range": 6,  "income": None},
    "Gladiator":      {"cost": 525,  "limit": 6,  "damage": 150,  "firerate": 0.9,  "range": 5,  "income": None},
    "Toxic Gunner":   {"cost": 525,  "limit": 5,  "damage": 40,   "firerate": 1.5,  "range": 7,  "income": None},
    "Slasher":        {"cost": 1700, "limit": 3,  "damage": 300,  "firerate": 0.7,  "range": 6,  "income": None},
    "Hallow Punk":    {"cost": 300,  "limit": 4,  "damage": 65,   "firerate": 1.1,  "range": 7,  "income": None},
    "Spotlight Tech": {"cost": 3250, "limit": 3,  "damage": 120,  "firerate": 1.0,  "range": 10, "income": None},
    "Snowballer":     {"cost": 400,  "limit": 4,  "damage": 50,   "firerate": 1.3,  "range": 7,  "income": None},
    "Commando":       {"cost": 900,  "limit": 5,  "damage": 55,   "firerate": 1.2,  "range": 8,  "income": None},
    "Accelerator":    {"cost": 5000, "limit": 2,  "damage": 500,  "firerate": 0.3,  "range": 15, "income": None},
    "Frostcelerator": {"cost": 3500, "limit": 2,  "damage": 550,  "firerate": 0.3,  "range": 14, "income": None},
    "Warlock":        {"cost": 4200, "limit": 3,  "damage": 250,  "firerate": 0.6,  "range": 8,  "income": None},
    "Caster":         {"cost": 7500, "limit": 2,  "damage": 400,  "firerate": 0.5,  "range": 9,  "income": None},
    "Jester":         {"cost": 650,  "limit": 4,  "damage": 100,  "firerate": 1.5,  "range": 7,  "income": None},
    "Korzhik":        {"cost": 600,  "limit": 6,  "damage": 350,  "firerate": 0.8,  "range": 7,  "income": None},
    "Conduit":        {"cost": 1800, "limit": 3,  "damage": 60,   "firerate": 1.2,  "range": 5,  "income": None},
    "Rubber Duck":    {"cost": 500,  "limit": 3,  "damage": 70,   "firerate": 1.0,  "range": 5,  "income": None},
    "Harvester":      {"cost": 2000, "limit": 5,  "damage": 80,   "firerate": 1.0,  "range": 6,  "income": 80},
    "Control Panel":  {"cost": 5000, "limit": 1,  "damage": 0,    "firerate": 0.0,  "range": 6,  "income": None},
    "hacker_laser_effects_test": {"cost": 7500, "limit": 1, "damage": 9999, "firerate": 9.9, "range": 20, "income": None},
    "Castbound":      {"cost": 400,  "limit": 5,  "damage": 4,    "firerate": 0.8,  "range": 6.2,"income": None},
}

# ── Tower descriptions — fill in your own later ───────────────────────────────
UNIT_DESCRIPTIONS = {
    "Assassin":       "Silent but deadly. Clear out enemies with fatal stabs, whirlwind slashes, and throwing knives!",
    "Militant":       "Trained with an assault rifle, this tower deals medium damage at a fast firerate.",
    "Twitgunner":     "The starter tower of the game.",
    "Lifestealer":    "Steal enemies life and convert it to money",
    "Archer":         "Shoot a piercing arrow that bounces towards nearby enemies. Pick between Fire, Stun, & EXP arrows.",
    "Red Ball":       "Bounces at enemies dealing high single target damage. Felyne's tower",
    "Farm":           "Earn extra cash per wave. The higher the upgrade, the higher the income.",
    "Cowboy":         "There ain't enough room for the two of us pardner... Gain cash on reload.",
    "Swarmer":        "OH NOES, THE BEES! Attack enemies with bees that do damage over time",
    "Freezer":        "Brrr! Build up chill to slow and freeze enemies in their tracks!",
    "Frost Blaster":  "Pierce multiple enemies with an ice rifle, freezing them in place!",
    "Sledger":        "Bash zombies with powerful blows and freeze them.",
    "Gladiator":      "Slash nearby enemies, deal area damage, and parry incoming attacks!",
    "Toxic Gunner":   "Shoot a burst of poison bullets that slow down enemies!",
    "Slasher":        "Stabs nearby enemies and applies bleed on higher levels",
    "Hallow Punk":    "A mad explosives expert capable of knocking back and burning enemies.",
    "Spotlight Tech": "A cliff tower with great range that deals damage over time with burn, applies confusion, and helps to combat hidden enemies.",
    "Snowballer":     "A jolly snowball fighter who prefers to fight in the best way they know how!",
    "Commando":       "Shoot enemies with dual laser guns and launches missiles.",
    "Accelerator":    "Charge a laser and release massive damage at deadly rates!",
    "Frostcelerator": "A frozen variant of the Accelerator. Chills targets on impact.",
    "Warlock":        "A hybrid melee and ranged tower that fights with eldritch magic. Capable of knocking back enemies and applying bleed.",
    "Caster":         "A boss killer with good aoe ability",
    "Jester":         "I have a ton of tricks in my pockets! Cycle through and throw debuff bombs at enemies!",
    "Korzhik":        "Zigres's friend. Catgirl.",
    "Conduit":        "Draws charge from nearby towers and unleashes chain lightning. The more allies, the stronger the mega-discharge!",
    "Rubber Duck":    "Exclusive squeaky menace. Don't underestimate it.",
    "Harvester":      "A haunted scarecrow that fires piercing bolts and can summon thorns to slow enemies.",
    "Control Panel":  "A remote support station. Use 'Remote Control' to buff a nearby tower with boosted Range, Damage, or Firerate for a chosen duration.",
    "hacker_laser_effects_test": "??? ERROR 404 UNIT NOT FOUND ???",
    "Castbound":      "\"The culmination of a journey forged into the ultimate tower\"",
}

class LoadoutScreen:
    """
    Layout (1920x1080):
      - Top bar (0..70): title, back, coins
      - Vertical divider at x = SCREEN_W * 0.40 = 768
      - LEFT zone  (x 0..768):  empty space + loadout slots at the bottom
      - RIGHT zone (x 768..1920): scrollable rarity sections with unit cards
      - No bottom strip outside the left zone — slots live inside the left area
    """

    _RARITY_ORDER = ["starter", "common", "rare", "epic", "apex", "singularity", "early_access"]
    _RARITY_HDR_COL = {
        "starter":      (180, 180, 190),
        "common":       ( 80, 210,  80),
        "rare":         ( 80, 150, 255),
        "epic":         (200, 100, 255),
        "apex":         (255, 210,  40),
        "early_access": ( 60, 220, 180),
        "singularity":  (180,  50, 255),
    }
    _RARITY_HDR_LINE = {
        "starter":      (100, 100, 110),
        "common":       ( 40, 120,  40),
        "rare":         ( 40,  80, 180),
        "epic":         (120,  40, 180),
        "apex":         (180, 140,   0),
        "early_access": ( 20, 140, 110),
        "singularity":  ( 80,   0, 160),
    }

    # Layout split: left zone = 40%, right zone = 60%
    _SPLIT    = 0.40
    # Card geometry inside right zone
    _CW       = 155
    _CH       = 195
    _COLS     = 5
    _HGAP     = 14
    _VGAP     = 16
    _SEC_PAD_T = 32
    _SEC_PAD_B = 18

    def __init__(self, screen, save_data):
        self.screen    = screen
        self.save_data = save_data
        self.t         = 0.0
        self.running   = True
        self.loadout   = list(save_data.get("loadout", ["Assassin", None, None, None, None]))
        while len(self.loadout) < 5:
            self.loadout.append(None)
        if "owned_units" not in self.save_data:
            self.save_data["owned_units"] = ["Assassin"]
        self.selected  = None   # (rarity, idx) or None
        self.scroll_y  = 0
        self.btn_back  = pygame.Rect(20, 20, 120, 40)
        self.msg       = ""
        self.msg_timer = 0.0
        self._card_hits = []
        self._buy_hits  = []
        self._shard_buy_hits = []
        # Detail panel state
        self.detail_unit   = None   # unit name shown in left detail panel
        self._slot_select  = False  # True = waiting for slot click after EQUIP
        self._btn_equip    = None
        self._btn_unequip  = None

    # ── helpers ──────────────────────────────────────────────────────────────
    def _owned_units(self):
        owned = self.save_data.get("owned_units", ["Assassin"])
        if self.save_data.get("frostcelerator_unlocked"):
            if "Frostcelerator" not in owned:
                owned = list(owned) + ["Frostcelerator"]
        if "hacker_laser_effects_test" not in owned:
            owned = list(owned) + ["hacker_laser_effects_test"]
        # Cowboy is a starter — always owned (rename migration from Golden Cowboy)
        if "Cowboy" not in owned and "Golden Cowboy" not in owned:
            owned = list(owned) + ["Cowboy"]
        # Migrate old Golden Cowboy save entries to Cowboy
        owned = ["Cowboy" if u == "Golden Cowboy" else u for u in owned]

        # Rubber Duck — разблокирован по умолчанию
        # Harvester — требует покупки за 5000 монет
        # Twitgunner — стартер, всегда доступен
        if "Twitgunner" not in owned:
            owned = list(owned) + ["Twitgunner"]
        # Control Panel unlocked via shards (apex rarity)
        # Rubber Duck — покупается за 1300 монет

        return owned

    def _show_msg(self, text, dur=2.5):
        self.msg = text; self.msg_timer = dur

    def _units_for_rarity(self, rarity):
        return [u for u in ALL_UNITS_POOL if u["rarity"] == rarity]

    def _section_height(self, rarity):
        n      = len(self._units_for_rarity(rarity))
        n_rows = max(1, math.ceil(n / self._COLS))
        return 30 + self._SEC_PAD_T + n_rows * (self._CH + self._VGAP) + self._SEC_PAD_B

    def _total_content_h(self):
        return sum(self._section_height(r) for r in self._RARITY_ORDER)

    def _card_cx(self, col, panel_x):
        panel_w       = SCREEN_W - panel_x
        cards_total_w = self._COLS * self._CW + (self._COLS - 1) * self._HGAP
        x0            = panel_x + (panel_w - cards_total_w) // 2 + self._CW // 2
        return x0 + col * (self._CW + self._HGAP)

    # ── slot rects — inside left zone, anchored to bottom ────────────────────
    def _slot_rects(self, left_w):
        SLOT_W, SLOT_H = 110, 100
        SLOT_BOTTOM    = SCREEN_H - 14   # 14px from screen bottom
        n     = 5
        total = n * SLOT_W + (n - 1) * 12
        x0    = (left_w - total) // 2
        y0    = SLOT_BOTTOM - SLOT_H
        return [pygame.Rect(x0 + i * (SLOT_W + 12), y0, SLOT_W, SLOT_H) for i in range(n)]

    # ── run ──────────────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self.msg_timer > 0: self.msg_timer -= dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
                if ev.type == pygame.MOUSEWHEEL:
                    mx2, _ = pygame.mouse.get_pos()
                    if mx2 >= int(SCREEN_W * self._SPLIT):
                        self.scroll_y = max(0, self.scroll_y - ev.y * 36)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._handle_click(ev.pos)
            self._draw()
            pygame.display.flip()
        self.save_data["loadout"] = self.loadout
        write_save(self.save_data)

    def _handle_click(self, pos):
        left_w = int(SCREEN_W * self._SPLIT)

        if self.btn_back.collidepoint(pos):
            self.running = False; return

        # Skin buttons on slot cards
        for skin_btn, uname in getattr(self, '_skin_btns', []):
            if skin_btn.collidepoint(pos):
                unit_skins = [s for s in ALL_SKIN_DEFS if s["unit_name"] == uname and own_skin(s["id"])]
                if not unit_skins: return
                # Open skin picker for this unit
                SkinPickerScreen(self.screen, uname, unit_skins).run()
                return

        owned = self._owned_units()

        for btn_r, u in self._buy_hits:
            if btn_r.collidepoint(pos):
                price = UNIT_SHOP_PRICES.get(u["name"], 0)
                coins = self.save_data.get("coins", 0)
                if coins >= price:
                    self.save_data["coins"] -= price
                    ol = list(self.save_data.get("owned_units", ["Assassin"]))
                    ol.append(u["name"])
                    self.save_data["owned_units"] = ol
                    write_save(self.save_data)
                    self._show_msg(f"{u['name']} unlocked!")
                else:
                    self._show_msg(f"Need {price} coins!")
                return

        for btn_r, u in self._shard_buy_hits:
            if btn_r.collidepoint(pos):
                SHARD_PRICES = {"Jester": 300, "Korzhik": 1500, "Control Panel": 1500}
                price = SHARD_PRICES.get(u["name"], 0)
                shards = self.save_data.get("shards", 0)
                if shards >= price:
                    self.save_data["shards"] = shards - price
                    ol = list(self.save_data.get("owned_units", ["Assassin"]))
                    ol.append(u["name"])
                    self.save_data["owned_units"] = ol
                    write_save(self.save_data)
                    self._show_msg(f"{u['name']} unlocked!")
                else:
                    self._show_msg(f"Need {price} shards!")
                return

        for card_r, rarity, idx in self._card_hits:
            if card_r.collidepoint(pos):
                key = (rarity, idx)
                units_r = self._units_for_rarity(rarity)
                if idx < len(units_r):
                    uname = units_r[idx]["name"]
                    if self.detail_unit == uname:
                        self.detail_unit = None
                        self._slot_select = False
                    else:
                        self.detail_unit = uname
                        self._slot_select = False
                    self.selected = None
                return

        # EQUIP / CANCEL button in detail panel
        if self._btn_equip and self._btn_equip.collidepoint(pos):
            if self._slot_select:
                self._slot_select = False
                self._show_msg("Cancelled")
            else:
                self._slot_select = True
                self._show_msg("Choose a slot")
            return

        # UNEQUIP button in detail panel
        if self._btn_unequip and self._btn_unequip.collidepoint(pos):
            uname = self.detail_unit
            for k in range(5):
                if self.loadout[k] == uname:
                    self.loadout[k] = None
            self._show_msg(f"{uname} unequipped")
            return

        for si, sr in enumerate(self._slot_rects(left_w)):
            if sr.collidepoint(pos):
                if self._slot_select and self.detail_unit:
                    uname = self.detail_unit
                    if uname not in owned:
                        self._show_msg("Not unlocked!")
                        self._slot_select = False; return
                    # Remove from other slot if already placed
                    for k in range(5):
                        if self.loadout[k] == uname and k != si:
                            self.loadout[k] = None; break
                    self.loadout[si] = uname
                    self._slot_select = False
                    self._show_msg(f"{uname} equipped!")
                elif self.selected is not None:
                    sel_r, sel_i = self.selected
                    units_r = self._units_for_rarity(sel_r)
                    if sel_i < len(units_r):
                        uname = units_r[sel_i]["name"]
                        if uname not in owned:
                            self._show_msg("Not unlocked!")
                            self.selected = None; return
                        for k in range(5):
                            if self.loadout[k] == uname and k != si:
                                self.loadout[k] = None; break
                        self.loadout[si] = uname
                        self.selected = None
                elif self.loadout[si] is not None:
                    self.loadout[si] = None
                return

    # ── draw ─────────────────────────────────────────────────────────────────
    def _draw(self):
        TOP     = 70        # below top bar
        BOTTOM  = SCREEN_H  # full height (slots near bottom)
        left_w  = int(SCREEN_W * self._SPLIT)   # e.g. 768
        panel_x = left_w                         # right zone starts here
        self._skin_btns = []   # reset each frame

        surf = self.screen
        surf.fill(C_BG)

        # ── Top bar ──────────────────────────────────────────────────────────
        pygame.draw.rect(surf, C_PANEL,  (0, 0, SCREEN_W, 70))
        pygame.draw.line(surf, C_BORDER, (0, 70), (SCREEN_W, 70), 2)
        txt(surf, "LOADOUT", (SCREEN_W // 2, 35), C_CYAN, font_xl, center=True)

        mx, my = pygame.mouse.get_pos()

        # Coins
        coins  = self.save_data.get("coins", 0)
        ico_c  = load_icon("coin_ico", 28)
        coin_s = font_lg.render(f" {fmt_num(coins)}", True, C_WHITE)
        tcw    = (ico_c.get_width() if ico_c else 0) + coin_s.get_width()
        ccx    = SCREEN_W - 14 - tcw
        if ico_c:
            surf.blit(ico_c,  (ccx, 18 + (coin_s.get_height() - ico_c.get_height()) // 2))
            surf.blit(coin_s, (ccx + ico_c.get_width(), 18))
        else:
            txt(surf, f"Coins: {fmt_num(coins)}", (SCREEN_W - 14, 18), C_GOLD, font_lg, right=True)

        # Shards (shown to the left of coins)
        shards   = self.save_data.get("shards", 0)
        ico_sh   = load_icon("shard_ico", 22)
        shard_col = C_WHITE
        shard_s  = font_lg.render(f" {fmt_num(shards)}", True, C_WHITE)
        tsw      = (ico_sh.get_width() if ico_sh else 0) + shard_s.get_width()
        scx      = ccx - tsw - 24
        if ico_sh:
            surf.blit(ico_sh,  (scx, 18 + (shard_s.get_height() - ico_sh.get_height()) // 2))
            surf.blit(shard_s, (scx + ico_sh.get_width(), 18))
        else:
            shard_lbl = font_lg.render(f"◆ {fmt_num(shards)}", True, C_WHITE)
            surf.blit(shard_lbl, shard_lbl.get_rect(right=ccx - 24, centery=29))

        # Back button
        hov_b = self.btn_back.collidepoint(mx, my)
        pygame.draw.rect(surf, (110,50,50) if hov_b else (80,40,40), self.btn_back, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_back, 2, border_radius=8)
        txt(surf, "← BACK", self.btn_back.center, C_WHITE, font_md, center=True)

        # ── Vertical divider ─────────────────────────────────────────────────
        pygame.draw.line(surf, C_BORDER, (panel_x, TOP), (panel_x, SCREEN_H), 2)

        # ── LEFT zone — background + detail panel + loadout slots ─────────────
        # Subtle background tint
        left_bg = pygame.Surface((left_w, SCREEN_H - TOP), pygame.SRCALPHA)
        left_bg.fill((12, 15, 24, 180))
        surf.blit(left_bg, (0, TOP))

        # ── LOADOUT SLOTS — bottom of left zone ──────────────────────────────
        slot_rects = self._slot_rects(left_w)

        _col_map_slot = {
            "Assassin": C_ASSASSIN,        "Lifestealer": C_LIFESTEALER,
            "Militant": C_MILITANT,        "Swarmer":     C_SWARMER,
            "Archer":   C_ARCHER,          "Red Ball":    C_REDBALL,
            "Farm":     C_FARM,            "Freezer":     C_FREEZER,
            "Frost Blaster": C_FROSTBLASTER, "Sledger":   C_SLEDGER,
            "Gladiator": C_GLADIATOR,      "Toxic Gunner": C_TOXICGUN,
            "Slasher":  C_SLASHER,         "Golden Cowboy": C_GCOWBOY, "Cowboy": C_GCOWBOY,
            "Hallow Punk": C_HALLOWPUNK,   "Spotlight Tech": C_SPOTLIGHT,
            "Jester":   C_JESTER,
            "Harvester": C_HARVESTER,
        }

        # Slot-select hint arrow
        if self._slot_select:
            hint_s = font_md.render("▼  Choose a slot  ▼", True, (80, 220, 140))
            surf.blit(hint_s, hint_s.get_rect(center=(left_w // 2, slot_rects[0].top - 48)))

        for si, sr in enumerate(slot_rects):
            uname = self.loadout[si]
            hov3  = sr.collidepoint(mx, my)
            # Highlight empty slots when in slot-select mode
            if self._slot_select and not uname:
                bg_col = (20, 60, 40)
            elif self._slot_select and uname:
                bg_col = (50, 35, 10)
            elif hov3:
                bg_col = (50, 60, 90)
            else:
                bg_col = C_SLOT_BG
            pygame.draw.rect(surf, bg_col, sr, border_radius=8)
            bd_col = (60, 200, 100) if (self._slot_select and not uname and hov3) else \
                     (80, 200, 100) if self._slot_select else C_BORDER
            pygame.draw.rect(surf, bd_col, sr, 2, border_radius=8)

            if uname:
                rarity = next((u["rarity"] for u in ALL_UNITS_POOL if u["name"] == uname), "starter")
                rd     = RARITY_DATA[rarity]
                icx, icy = sr.centerx, sr.centery - 10
                eq_skin_id = get_equipped_skin(uname)
                skin_def = next((s for s in ALL_SKIN_DEFS if s["id"] == eq_skin_id), None) if eq_skin_id else None
                if skin_def and skin_def["id"] == "archer_star":
                    pygame.draw.circle(surf, (30, 20, 50), (icx, icy), 22)
                    pygame.draw.circle(surf, (200, 160, 40), (icx, icy), 18)
                    pygame.draw.circle(surf, (255, 220, 80), (icx, icy), 12)
                    for si2 in range(5):
                        sa2 = math.radians(self.t * 120 + si2 * 72)
                        ssx = icx + int(math.cos(sa2) * 22)
                        ssy = icy + int(math.sin(sa2) * 22)
                        pygame.draw.circle(surf, (255, 220, 60), (ssx, ssy), 3)
                else:
                    _draw_tower_icon(surf, uname, icx, icy, self.t, size=20)
                txt(surf, uname, (sr.centerx, sr.bottom - 20), C_WHITE, font_sm, center=True)
                if rarity == "apex":
                    _blit_apex_label(surf, rd["label"], font_sm, (sr.centerx, sr.bottom - 7), center=True)
                elif rarity == "singularity":
                    _pos = (sr.centerx, sr.bottom - 7)
                    for _ox, _oy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        _so = font_sm.render(rd["label"], True, (200, 0, 255))
                        surf.blit(_so, _so.get_rect(center=(_pos[0]+_ox, _pos[1]+_oy)))
                    _sc = font_sm.render(rd["label"], True, (0, 0, 0))
                    surf.blit(_sc, _sc.get_rect(center=_pos))
                else:
                    _lbl2 = rd.get("label", rarity.replace("_"," ").title() if "_" in rarity else rarity.capitalize())
                    rs2 = font_sm.render(_lbl2, True, rd["text_col"])
                    surf.blit(rs2, rs2.get_rect(center=(sr.centerx, sr.bottom - 7)))
            else:
                txt(surf, f"SLOT {si+1}", (sr.centerx, sr.centery), (60,70,100), font_sm, center=True)

        # ── DETAIL PANEL — upper left zone ───────────────────────────────────
        self._btn_equip   = None
        self._btn_unequip = None

        SLOT_TOP = slot_rects[0].top - 50   # top of slot area (including label)
        DETAIL_TOP  = TOP + 8
        DETAIL_H    = SLOT_TOP - DETAIL_TOP - 8
        DETAIL_AREA = pygame.Rect(8, DETAIL_TOP, left_w - 16, DETAIL_H)

        if self.detail_unit:
            uname = self.detail_unit
            rarity = next((u["rarity"] for u in ALL_UNITS_POOL if u["name"] == uname), "starter")
            rd = RARITY_DATA[rarity]
            # Build stats from a fresh level-0 instance so values are always accurate
            _name_to_cls_ld = {
                "Assassin": Assassin, "Accelerator": Accelerator,
                "Frostcelerator": Frostcelerator,
                "Lifestealer": Lifestealer, "Archer": Archer,
                "Militant": Militant, "Swarmer": Swarmer,
                "Red Ball": RedBall, "Farm": Farm,
                "Freezer": Freezer, "Frost Blaster": FrostBlaster,
                "Sledger": Sledger, "Gladiator": Gladiator,
                "Toxic Gunner": ToxicGunner, "Slasher": Slasher,
                "Cowboy": GoldenCowboy, "Golden Cowboy": GoldenCowboy,
                "Hallow Punk": HallowPunk, "Spotlight Tech": SpotlightTech,
                "Snowballer": Snowballer,
                "Commando": Commando, "Caster": Caster,
                "hacker_laser_effects_test": Caster,
                "Warlock": Warlock, "Jester": Jester,
                "Soul Weaver": SoulWeaver, "Rubber Duck": RubberDuck,
                "Harvester": Harvester, "Twitgunner": Twitgunner,
                "Korzhik": Felyne, "Conduit": Conduit,
                "Control Panel": ControlPanel, "ControlPanel": ControlPanel,
                "Castbound": Castbound,
            }
            _cls_ld = _name_to_cls_ld.get(uname)
            _static = UNIT_BASE_STATS.get(uname, {})
            if _cls_ld:
                try:
                    _inst = _cls_ld(0, 0)
                    _inst.level = 0
                    _inst._apply_level() if hasattr(_inst, '_apply_level') else None
                    stats = {
                        "cost":     _static.get("cost", getattr(_inst, "PLACE_COST", None)),
                        "limit":    _static.get("limit", UNIT_LIMITS.get(getattr(_inst, "NAME", uname))),
                        "damage":   getattr(_inst, "damage", None),
                        "firerate": getattr(_inst, "firerate", None),
                        "range":    getattr(_inst, "range_tiles", None),
                        "income":   _static.get("income", None),
                    }
                except Exception:
                    stats = _static
            else:
                stats = _static
            desc  = UNIT_DESCRIPTIONS.get(uname, "")
            is_equipped = uname in self.loadout

            PANEL_X = DETAIL_AREA.x
            PANEL_Y = DETAIL_AREA.y
            PANEL_W = DETAIL_AREA.w
            PANEL_H = DETAIL_AREA.h

            # Background card
            bg_surf = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (10, 12, 20, 235), (0, 0, PANEL_W, PANEL_H), border_radius=14)
            glow_col = rd["border"]
            pygame.draw.rect(bg_surf, (*glow_col, 90), (0, 0, PANEL_W, PANEL_H), 2, border_radius=14)
            surf.blit(bg_surf, (PANEL_X, PANEL_Y))

            # Layout: LEFT = name + stats flush to left edge, tower visual centered horizontally
            TEXT_X  = PANEL_X + 10   # text starts at left edge of panel

            # ── Tower name & rarity — top-left ───────────────────────────────
            name_f = pygame.font.SysFont("segoeui", 26, bold=True)
            rar_f  = pygame.font.SysFont("segoeui", 17, bold=True)
            name_s = name_f.render(uname, True, C_WHITE)
            if rarity == "apex":
                rar_s = _render_gradient_text(rd["label"], rar_f, _APEX_GRAD_COLORS)
                surf.blit(name_s, (TEXT_X, PANEL_Y + 10))
                surf.blit(rar_s,  (TEXT_X, PANEL_Y + 10 + name_s.get_height() + 3))
            elif rarity == "singularity":
                rar_s = rar_f.render(rd["label"], True, (0, 0, 0))
                surf.blit(name_s, (TEXT_X, PANEL_Y + 10))
                _ry = PANEL_Y + 10 + name_s.get_height() + 3
                for _ox, _oy in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)]:
                    _ro = rar_f.render(rd["label"], True, (200, 0, 255))
                    surf.blit(_ro, (TEXT_X + _ox, _ry + _oy))
                surf.blit(rar_s, (TEXT_X, _ry))
            else:
                _lbl3 = rd.get("label", rarity.replace("_"," ").title() if "_" in rarity else rarity.capitalize())
                rar_s  = rar_f.render(_lbl3, True, rd["text_col"])
                surf.blit(name_s, (TEXT_X, PANEL_Y + 10))
                surf.blit(rar_s,  (TEXT_X, PANEL_Y + 10 + name_s.get_height() + 3))

            # ── STATS — icon + value rows, left-aligned ───────────────────────
            stat_f  = pygame.font.SysFont("segoeui", 18, bold=True)
            ICO_SZ  = 22
            ROW_H   = 32
            STAT_Y0 = PANEL_Y + 10 + name_s.get_height() + rar_s.get_height() + 16

            stat_defs = [
                ("money_ico",    "cost",     "{}"),
                ("limit_ico",    "limit",    "{}"),
                ("damage_ico",   "damage",   "{}"),
                ("firerate_ico", "firerate", "{:.2f}"),
                ("range_ico",    "range",    "{}"),
            ]
            if stats.get("income") is not None:
                stat_defs.append(("money_ico", "income", "${}"))

            for ri, (ico_name, key, fmt) in enumerate(stat_defs):
                sy = STAT_Y0 + ri * ROW_H
                if sy + ROW_H > PANEL_Y + PANEL_H - 95:
                    break
                # Icon
                ico_img = load_icon(ico_name, ICO_SZ)
                ico_y   = sy + (ROW_H - ICO_SZ) // 2
                if ico_img:
                    surf.blit(ico_img, (TEXT_X, ico_y))
                    val_x = TEXT_X + ICO_SZ + 8
                else:
                    # Fallback colored circle
                    pygame.draw.circle(surf, (100, 120, 160), (TEXT_X + ICO_SZ // 2, sy + ROW_H // 2), ICO_SZ // 2)
                    val_x = TEXT_X + ICO_SZ + 8
                val = stats.get(key)
                val_str = fmt.format(val) if val is not None else "—"
                val_s = stat_f.render(val_str, True, C_WHITE)
                surf.blit(val_s, (val_x, sy + (ROW_H - val_s.get_height()) // 2))

            # ── Tower visual — centered horizontally in the panel ─────────────
            VIS_CX = PANEL_X + PANEL_W // 2
            VIS_CY = PANEL_Y + (PANEL_H - 90) // 2 + 10   # above description strip
            _draw_tower_icon(surf, uname, VIS_CX, VIS_CY, self.t, size=110 if uname == "Castbound" else 72)

            # ── SKINS button — left side, above description ───────────────────
            has_skins = any(s["unit_name"] == uname and own_skin(s["id"]) for s in ALL_SKIN_DEFS)
            SK_BTN_W  = int(PANEL_W * 0.30)
            SK_BTN_H  = 34
            SK_BTN_X  = PANEL_X + 8
            SK_BTN_Y  = PANEL_Y + PANEL_H - 72 - 44 - SK_BTN_H - 6  # just above desc strip
            sk_btn_r  = pygame.Rect(SK_BTN_X, SK_BTN_Y, SK_BTN_W, SK_BTN_H)
            sk_hov    = sk_btn_r.collidepoint(mx, my)
            eq_sk     = get_equipped_skin(uname) if has_skins else None
            if has_skins:
                sk_bg  = (100, 50, 160) if sk_hov else (72, 30, 120)
                sk_brd = (200, 140, 255) if sk_hov else (150, 90, 220)
            else:
                sk_bg  = (35, 28, 50)
                sk_brd = (70, 55, 90)
            pygame.draw.rect(surf, sk_bg,  sk_btn_r, border_radius=8)
            pygame.draw.rect(surf, sk_brd, sk_btn_r, 2, border_radius=8)
            sk_f   = pygame.font.SysFont("segoeui", 16, bold=True)
            sk_lbl = "★ SKINS" if has_skins else "NO SKINS"
            sk_col = (220, 180, 255) if has_skins else (80, 65, 100)
            sk_s   = sk_f.render(sk_lbl, True, sk_col)
            # truncate label if too wide
            while sk_s.get_width() > SK_BTN_W - 10 and len(sk_lbl) > 4:
                sk_lbl = sk_lbl[:-1]
                sk_s   = sk_f.render(sk_lbl + "…", True, sk_col)
            surf.blit(sk_s, sk_s.get_rect(center=sk_btn_r.center))
            if has_skins:
                self._skin_btns.append((sk_btn_r, uname))

            # ── Description strip — bottom of panel ───────────────────────────
            DESC_H  = 72
            DESC_Y  = PANEL_Y + PANEL_H - DESC_H - 44
            desc_bg = pygame.Surface((PANEL_W - 4, DESC_H), pygame.SRCALPHA)
            desc_bg.fill((5, 8, 15, 210))
            surf.blit(desc_bg, (PANEL_X + 2, DESC_Y))

            desc_f = pygame.font.SysFont("segoeui", 16, italic=True) if uname == "Castbound" else pygame.font.SysFont("segoeui", 16)
            words  = desc.split()
            lines2 = []
            cur_line = ""
            for w2 in words:
                test = (cur_line + " " + w2).strip()
                if desc_f.size(test)[0] < PANEL_W - 20:
                    cur_line = test
                else:
                    if cur_line: lines2.append(cur_line)
                    cur_line = w2
            if cur_line: lines2.append(cur_line)
            for li, ln in enumerate(lines2[:4]):
                ls3 = desc_f.render(ln, True, C_WHITE)
                surf.blit(ls3, (PANEL_X + 10, DESC_Y + 6 + li * 17))

            # ── EQUIP / UNEQUIP button — centered, 50% width, above bottom ─────
            BTN_H  = 44
            BTN_W  = int(PANEL_W * 0.50)
            BTN_Y  = PANEL_Y + PANEL_H - BTN_H - 18
            btn_r2 = pygame.Rect(PANEL_X + (PANEL_W - BTN_W) // 2, BTN_Y, BTN_W, BTN_H)
            btn_f  = pygame.font.SysFont("segoeui", 22, bold=True)

            if is_equipped:
                hov_u = btn_r2.collidepoint(mx, my)
                bg2   = (80, 82, 95) if hov_u else (55, 57, 68)
                bd2   = (180, 185, 200) if hov_u else (120, 125, 145)
                pygame.draw.rect(surf, bg2, btn_r2, border_radius=10)
                pygame.draw.rect(surf, bd2, btn_r2, 2, border_radius=10)
                ul_s  = btn_f.render("UNEQUIP", True, C_WHITE)
                surf.blit(ul_s, ul_s.get_rect(center=btn_r2.center))
                self._btn_unequip = btn_r2
            else:
                hov_e = btn_r2.collidepoint(mx, my)
                pulse = abs(math.sin(self.t * 2.2))
                g_val = int(150 + pulse * 35)
                bg2   = (25, g_val, 55) if hov_e else (18, 110, 45)
                bd2   = (70, 255, 110) if hov_e else (45, 195, 85)
                pygame.draw.rect(surf, bg2, btn_r2, border_radius=10)
                pygame.draw.rect(surf, bd2, btn_r2, 2, border_radius=10)
                eq_lbl = "CANCEL" if self._slot_select else "EQUIP"
                eq_s   = btn_f.render(eq_lbl, True, C_WHITE)
                surf.blit(eq_s, eq_s.get_rect(center=btn_r2.center))
                self._btn_equip = btn_r2

        else:
            # No unit selected — show hint
            hint_f = pygame.font.SysFont("segoeui", 20)
            hint_s = hint_f.render("Select a tower to view details", True, (55, 65, 88))
            surf.blit(hint_s, hint_s.get_rect(center=(left_w // 2, TOP + (SLOT_TOP - TOP) // 2)))


        # ── RIGHT zone — scrollable rarity sections ──────────────────────────
        CONTENT_TOP = TOP
        CONTENT_BOT = SCREEN_H
        CONTENT_H   = CONTENT_BOT - CONTENT_TOP
        RIGHT_W     = SCREEN_W - panel_x

        total_h    = self._total_content_h()
        max_scroll = max(0, total_h - CONTENT_H + 20)
        self.scroll_y = min(self.scroll_y, max_scroll)

        # Scrollbar
        if max_scroll > 0:
            sbx = SCREEN_W - 8
            pygame.draw.rect(surf, (40,45,60),   (sbx-4, CONTENT_TOP, 6, CONTENT_H), border_radius=3)
            tsh = CONTENT_H + max_scroll
            th  = max(30, int(CONTENT_H * CONTENT_H / tsh))
            ty  = CONTENT_TOP + int((CONTENT_H - th) * self.scroll_y / max_scroll)
            pygame.draw.rect(surf, (100,120,180), (sbx-4, ty, 6, th), border_radius=3)

        surf.set_clip(pygame.Rect(panel_x, CONTENT_TOP, RIGHT_W - 12, CONTENT_H))

        owned = self._owned_units()
        self._card_hits = []
        self._buy_hits  = []
        self._shard_buy_hits = []

        sec_y   = CONTENT_TOP + 8 - self.scroll_y
        label_f = pygame.font.SysFont("segoeui", 18, bold=True)
        price_f = pygame.font.SysFont("consolas", 12, bold=True)
        lock_f  = pygame.font.SysFont("segoeui", 20)
        excl_f  = pygame.font.SysFont("segoeui", 11)

        for rarity in self._RARITY_ORDER:
            units_sec = self._units_for_rarity(rarity)
            sec_h     = self._section_height(rarity)
            hdr_col   = self._RARITY_HDR_COL[rarity]
            hdr_line  = self._RARITY_HDR_LINE[rarity]

            hdr_y = sec_y + 5
            if CONTENT_TOP - 36 < hdr_y < CONTENT_BOT + 10:
                _rarity_label = rarity.replace("_", " ").title() if "_" in rarity else rarity.capitalize()
                if rarity in RARITY_DATA and "label" in RARITY_DATA[rarity] and ("_" in rarity or rarity in ("apex", "singularity")):
                    _rarity_label = RARITY_DATA[rarity]["label"]
                if rarity == "apex":
                    ls2 = _render_gradient_text(_rarity_label, label_f, _APEX_GRAD_COLORS)
                    surf.blit(ls2, (panel_x + 16, hdr_y))
                elif rarity == "singularity":
                    _hx, _hy = panel_x + 16, hdr_y
                    for _ox, _oy in [(-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)]:
                        _go = label_f.render(_rarity_label, True, (200, 0, 255))
                        surf.blit(_go, (_hx + _ox, _hy + _oy))
                    ls2 = label_f.render(_rarity_label, True, (0, 0, 0))
                    surf.blit(ls2, (_hx, _hy))
                else:
                    ls2 = label_f.render(_rarity_label, True, hdr_col)
                    surf.blit(ls2, (panel_x + 16, hdr_y))
                ul_y = hdr_y + ls2.get_height() + 2
                pygame.draw.line(surf, hdr_line,
                                 (panel_x + 16, ul_y), (SCREEN_W - 16, ul_y), 1)

            for i, u in enumerate(units_sec):
                col_i = i % self._COLS
                row_i = i // self._COLS
                cx2   = self._card_cx(col_i, panel_x)
                cy2   = sec_y + 28 + self._SEC_PAD_T + row_i * (self._CH + self._VGAP) + self._CH // 2

                if cy2 + self._CH // 2 < CONTENT_TOP - 4 or cy2 - self._CH // 2 > CONTENT_BOT + 4:
                    continue

                is_owned = u["name"] in owned
                is_sel   = (self.selected == (rarity, i)) and is_owned

                draw_unit_card(surf, u["name"], rarity, cx2, cy2,
                               self._CW, self._CH,
                               self.t if is_owned else 0.0, is_sel)

                card_r = pygame.Rect(cx2 - self._CW // 2, cy2 - self._CH // 2,
                                     self._CW, self._CH)

                if is_owned:
                    self._card_hits.append((card_r, rarity, i))
                else:
                    dim = pygame.Surface((self._CW, self._CH), pygame.SRCALPHA)
                    dim.fill((0, 0, 0, 160))
                    mask = pygame.Surface((self._CW, self._CH), pygame.SRCALPHA)
                    pygame.draw.rect(mask, (255,255,255,255),
                                     (0,0,self._CW,self._CH), border_radius=16)
                    dim.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
                    surf.blit(dim, card_r.topleft)

                    if rarity == "apex":
                        SHARD_PRICES = {"Jester": 300, "Korzhik": 1500, "Control Panel": 1500}
                        shard_price = SHARD_PRICES.get(u["name"])
                        if shard_price is not None:
                            shards_have = self.save_data.get("shards", 0)
                            can_buy_s   = shards_have >= shard_price
                            btn_r       = pygame.Rect(cx2 - 52, cy2 + 22, 104, 24)
                            btn_hov     = btn_r.collidepoint(mx, my)
                            btn_bg  = (60, 90, 10) if (can_buy_s and btn_hov) else \
                                      (40, 60,  8) if can_buy_s else (70, 55, 10)
                            btn_bd  = (200, 220, 40) if can_buy_s else (140, 110, 20)
                            pygame.draw.rect(surf, btn_bg, btn_r, border_radius=5)
                            pygame.draw.rect(surf, btn_bd, btn_r, 2, border_radius=5)
                            ico_sh2 = load_icon("shard_ico", 12)
                            ps2     = price_f.render(f" {shard_price}", True,
                                                     (255,220,60) if can_buy_s else (140,120,40))
                            pw3   = (ico_sh2.get_width() if ico_sh2 else 0) + ps2.get_width()
                            px4   = btn_r.centerx - pw3 // 2
                            if ico_sh2:
                                surf.blit(ico_sh2, (px4, btn_r.centery - 6))
                                surf.blit(ps2, (px4 + ico_sh2.get_width(),
                                                btn_r.centery - ps2.get_height()//2))
                            else:
                                lbl_sh = price_f.render(f"◆ {shard_price}", True,
                                                        (255,220,60) if can_buy_s else (140,120,40))
                                surf.blit(lbl_sh, lbl_sh.get_rect(center=btn_r.center))
                            self._shard_buy_hits.append((btn_r, u))
                    else:
                        price = UNIT_SHOP_PRICES.get(u["name"], 0)
                        if price is not None:
                            can_buy = self.save_data.get("coins", 0) >= price
                            btn_r   = pygame.Rect(cx2 - 48, cy2 + 22, 96, 24)
                            btn_hov = btn_r.collidepoint(mx, my)
                            btn_bg  = (40,110,40) if (can_buy and btn_hov) else \
                                      (26,68,26) if can_buy else (70,26,26)
                            btn_bd  = (80,200,80) if can_buy else (160,55,55)
                            pygame.draw.rect(surf, btn_bg, btn_r, border_radius=5)
                            pygame.draw.rect(surf, btn_bd, btn_r, 2, border_radius=5)
                            ico_m = load_icon("coin_ico", 12)
                            ps    = price_f.render(f" {price}", True,
                                                   C_GOLD if can_buy else (140,95,95))
                            pw2   = (ico_m.get_width() if ico_m else 0) + ps.get_width()
                            px3   = btn_r.centerx - pw2 // 2
                            if ico_m:
                                surf.blit(ico_m, (px3, btn_r.centery - 6))
                                surf.blit(ps, (px3 + ico_m.get_width(),
                                               btn_r.centery - ps.get_height()//2))
                            else:
                                surf.blit(ps, ps.get_rect(center=btn_r.center))
                            self._buy_hits.append((btn_r, u))

            sec_y += sec_h

        surf.set_clip(None)

        # ── Message ──────────────────────────────────────────────────────────
        if self.msg_timer > 0:
            ms = font_ru_lg.render(self.msg, True, C_GOLD)
            draw_rect_alpha(surf, (0,0,0),
                            (SCREEN_W//2 - ms.get_width()//2 - 10,
                             SCREEN_H//2 - 20, ms.get_width()+20, 36), 180, 8)
            surf.blit(ms, ms.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))


# ── Pause Menu ──────────────────────────────────────────────────────────────────
class PauseMenu:
    def __init__(self, screen):
        self.screen = screen
        cw, ch = 300, 280
        cx, cy = SCREEN_W//2, SCREEN_H//2
        self.panel = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
        self.btn_resume   = pygame.Rect(cx - 110, cy - 70, 220, 50)
        self.btn_settings = pygame.Rect(cx - 110, cy - 5,  220, 50)
        self.btn_menu     = pygame.Rect(cx - 110, cy + 60, 220, 50)

    def draw(self):
        draw_rect_alpha(self.screen, C_BLACK, (0, 0, SCREEN_W, SCREEN_H), 160)
        draw_rect_alpha(self.screen, (20, 25, 40), self.panel, 240, 12)
        pygame.draw.rect(self.screen, C_BORDER, self.panel, 2, border_radius=12)
        txt(self.screen, "PAUSED", (SCREEN_W//2, self.panel.y + 30), C_CYAN, font_xl, center=True)
        mx, my = pygame.mouse.get_pos()
        for btn, label in [
            (self.btn_resume,   "▶  RESUME"),
            (self.btn_settings, "SETTINGS"),
            (self.btn_menu,     "⌂  MAIN MENU"),
        ]:
            hov = btn.collidepoint(mx, my)
            bg = (60, 80, 130) if hov else (35, 45, 70)
            pygame.draw.rect(self.screen, bg, btn, border_radius=8)
            pygame.draw.rect(self.screen, C_BORDER, btn, 2, border_radius=8)
            txt(self.screen, label, btn.center, C_WHITE, font_lg, center=True)

    def handle_click(self, pos):
        if self.btn_resume.collidepoint(pos):   return "resume"
        if self.btn_settings.collidepoint(pos): return "settings"
        if self.btn_menu.collidepoint(pos):     return "menu"
        return None


# ── Game ───────────────────────────────────────────────────────────────────────



class Game:
    def __init__(self, save_data=None, mode="easy", admin_mode=False):
        self.save_data = save_data or load_save()
        self.screen = _apply_display_mode()
        pygame.display.set_caption("Tower Defense")
        self.clock=pygame.time.Clock(); self.running=True
        self._elapsed=0.0      # total play time in seconds (affected by speed)
        self._real_elapsed=0.0  # real wall-clock play time (unaffected by speed)
        self._end_coin_reward=0  # coins earned this run
        self.player_hp=100; self.player_maxhp=100; self.money=600
        self.enemies=[]; self.units=[]; self.effects=[]
        self._peer_units = []  # populated by MultiplayerGame subclass
        self.mode=mode
        if mode=="fallen":
            self.wave_mgr=WaveManager(wave_data=FALLEN_WAVE_DATA, max_waves=FALLEN_MAX_WAVES)
            self.wave_mgr._mode="fallen"
            self.player_hp=150; self.player_maxhp=150
        elif mode=="draft":
            self.wave_mgr=WaveManager(wave_data=FALLEN_WAVE_DATA, max_waves=FALLEN_MAX_WAVES)
            self.wave_mgr._mode="draft"
            self.player_hp=150; self.player_maxhp=150
            self.draft_active = False
            self.draft_cards = []
            self.waves_to_next_draft = random.randint(1, 4)
            self.draft_mod_range_duration = 0
            self.draft_mod_damage_duration = 0
            self.draft_mod_upgrade_cost = 1.0
            self.draft_mod_firerate = 1.0
            self.draft_mod_dmg5_timer = 0.0
            self._draft_state_hash = 0
        elif mode=="frosty":
            self.wave_mgr=WaveManager(wave_data=FROSTY_WAVE_DATA, max_waves=FROSTY_MAX_WAVES)
            self.wave_mgr._mode="frosty"
            self.player_hp=200; self.player_maxhp=200
            self._frosty_lane=0

        elif mode=="infernal" and _INFERNAL_AVAILABLE:
            self.wave_mgr=WaveManager(wave_data=INFERNAL_WAVE_DATA, max_waves=INFERNAL_MAX_WAVES)
            self.wave_mgr._mode="infernal"
            self.player_hp=250; self.player_maxhp=250
            self.money=700
            self._infernal_challenger=False
            self._challenger_wave_mgr=None
            self._challenger_radius_applied=False
            self._challenger_wave6_done=False
            self._challenger_screen_shown=False
        elif mode=="hardcore":
            self.wave_mgr=WaveManager(wave_data=HARDCORE_WAVE_DATA, max_waves=HARDCORE_MAX_WAVES)
            self.wave_mgr._mode="hardcore"
            self.player_hp=100; self.player_maxhp=100
            self.money=700
        else:
            self.wave_mgr=WaveManager()
            self.wave_mgr._mode="easy"
        # ── Apply Skill Tree bonuses ──────────────────────────────────────────
        _sd = self.save_data
        _st_lvls = _sd.get("skill_tree", {})
        # Hardcore: skill tree is disabled entirely
        if mode == "hardcore":
            _st_lvls = {}
        _bb_lvl = _st_lvls.get("bigger_budget", 0)
        if _bb_lvl > 0:
            self.money = int(self.money * (1.0 + _bb_lvl * 0.01))
        self._sk_range_bonus  = _st_lvls.get("enhanced_optics", 0) * 0.005
        # Push debuff/AoE multipliers to game_core so units.py can read them
        game_core.DEBUFF_MULT = 1.0 + _st_lvls.get("fight_dirty", 0) * 0.01
        game_core.AOE_MULT    = 1.0 + _st_lvls.get("improved_gunpowder", 0) * 0.005
        self._sk_aoe_bonus    = _st_lvls.get("improved_gunpowder", 0) * 0.005
        self._sk_debuff_bonus = _st_lvls.get("fight_dirty", 0) * 0.01
        self._sk_wave_bonus   = _st_lvls.get("stonks", 0) * 0.005
        _scav_lvl = _st_lvls.get("scavenger", 0)
        self._sk_scavenger_n  = max(10, 29 - _scav_lvl) if _scav_lvl > 0 else 0
        self._sk_kill_counter = 0
        _prec_lvl = _st_lvls.get("precision", 0)
        self._sk_precision_n  = max(15, 29 - _prec_lvl) if _prec_lvl > 0 else 0
        self._sk_shot_counter = 0
        # Frosty background music state
        self._frosty_bgm_active = False   # True while alternating frostymode/frostymode2 is playing
        self._frosty_bgm_track = 1        # 1 or 2 — which track plays next
        self._frosty_bgm_stopped = False  # True once wave 40 starts (don't restart)
        self.ui=UI(self.save_data)
        self.ui.admin_mode = admin_mode or (mode == "sandbox")
        self.ui.cost_mult = 1.4 if mode == "hardcore" else 1.0
        # Apply fast-forward default setting
        if SETTINGS.get("fast_forward_default", False):
            self.ui._speed_idx = 4  # 2x speed (index 4 in _SPEED_STEPS)
        self._fallen_king_music_timer = None  # countdown until FallenKing spawns after music starts
        self._fallen_king_spawned = False
        self._fallen_king_shake = 0.0
        # Unit ceremony for wave 40
        self._ceremony_phase = None
        self._ceremony_timer = 0.0
        self._ceremony_flash_alpha = 0
        self._ceremony_flash_color = (255,255,255)
        self._ceremony_unit_states = []
        self.game_over=False; self.win=False
        self._end_btn=pygame.Rect(SCREEN_W//2-200,SCREEN_H//2+130,400,70)
        # ── Free Robux screamer state ──────────────────────────────────────────
        self._screamer_timer = 0.0   # countdown; >0 means screamer is showing
        self._screamer_img   = None  # cached scaled image
        self._screamer_snd   = None  # cached sound
        self._boss_enemy=None; self._wave_leaked=False
        # Fallen mode boss bars: track first appearances
        self._fallen_boss_bars = {}  # class → enemy ref (first ever seen, only in fallen mode from waves)
        # Frosty mode: remember which enemies already got a boss bar (per run)
        self._frosty_bossbar_seen = set()
        self.console=DevConsole()
        self.paused = False
        self.pause_menu = PauseMenu(self.screen)
        self.return_to_menu = False
        self._restart_mode  = None
        self.admin_mode = admin_mode or (mode == "sandbox")  # stays True after admin-panel restarts
        self._ability_cycle_idx = 0    # index into self.units for F-key ability cycling
        # Frosty wave-40: Frost Spirit music → delayed spawn
        self._frost_spirit_music_timer = None
        self._frost_spirit_spawned = False
        # generic scheduled spawns (for delayed summon abilities)
        self._scheduled_spawns = []  # [{"t":float,"cls":type,"x":float,"y":float,"wp":int,"fp":path|None,"from_wave":bool,"free_kill":bool}]
        # Achievement manager
        self.ach_mgr = AchievementManager()
        self._wave_coin_accum = 0.0  # fractional coin accumulator for per-wave rewards
        self._last_coin_wave = 0  # last wave number for which profile coins were paid
        # track if easy-mode boss was let through (free_pass ach)
        self._easy_boss_leaked = False
        self._easy_boss_let_through = False  # boss reached end with hp < player hp
        self._wave_ever_leaked = False  # for frosty_perfect achievement
        self._max_units_placed = 0      # peak simultaneous units on field (for fallen_duo)
        # ── Batch-2 achievement tracking ──────────────────────────────────────
        self._sold_this_run = False          # No Refunds: True if any sell happened
        self._cowboy_income_total = 0        # Gold Rush: $ earned from Cowboys only
        self._cowboy_only_run = True         # Gold Rush: False if any non-Cowboy kill reward tallied
        self._idle_timer = 0.0              # Why: real seconds with no input
        self._idle_achieved = False          # Why: grant once per session
        self._auto_skip_ever_off = False     # Speedrunner: True if auto_skip was ever disabled
        # Absolute Zero: longest continuous freeze streak on any boss
        self._boss_freeze_timers = {}        # id(enemy) → continuous frozen seconds
        # Overkill: grant once detected
        self._overkill_granted = False
        # ── Profile stat tracking ──────────────────────────────────────────────
        self._total_kills  = 0    # enemies killed this run
        self._total_earned = 0    # total money earned from kills this run
        self._towers_placed_count = 0  # towers placed this run (daily quest tracking)

        # Apply saved loadout to slot types
        _name_to_cls = {"Assassin": Assassin, "Accelerator": Accelerator,
                        "Frostcelerator": Frostcelerator,
                        "Lifestealer": Lifestealer,
                        "Archer": Archer,
                        "Militant": Militant,
                        "Swarmer": Swarmer,
                        "Red Ball": RedBall, "Farm": Farm,
                        "Freezer": Freezer, "Frost Blaster": FrostBlaster,
                        "Sledger": Sledger, "Gladiator": Gladiator,
                        "Toxic Gunner": ToxicGunner, "Slasher": Slasher,
                        "Golden Cowboy": GoldenCowboy,  # legacy save compat
                        "Cowboy": GoldenCowboy,
                        "Hallow Punk": HallowPunk,
                        "Spotlight Tech": SpotlightTech,
                        "Snowballer": Snowballer,
                        "Commando": Commando,
                        "hacker_laser_effects_test": Caster,
                        "Caster": Caster,
                        "Warlock": Warlock,
                        "Jester": Jester,
                        "Soul Weaver": SoulWeaver,
                        "Rubber Duck": RubberDuck,
                        "Harvester": Harvester,
                        "Twitgunner": Twitgunner,
                        "Korzhik": Felyne,
                        "Conduit": Conduit,
                        "Control Panel": ControlPanel,
                        "ControlPanel": ControlPanel,
                        "CtrlPanel": ControlPanel,
                        "Castbound": Castbound}
        _loadout = self.save_data.get("loadout", ["Assassin", "Accelerator", None, None, None])
        while len(_loadout) < 5: _loadout.append(None)
        self.ui.SLOT_TYPES = [_name_to_cls.get(n) if n else None for n in _loadout]
        # ── Achievement: naked_run — start game with no units equipped ──
        if mode not in ("sandbox",) and all(s is None for s in self.ui.SLOT_TYPES):
            self.ach_mgr.try_grant("naked_run")
        # ── Achievement: has_skin — player owns at least one skin ──
        if self.save_data.get("skins"):
            self.ach_mgr.try_grant("has_skin")
        # Sandbox mode: empty loadout, infinite money
        if mode == "sandbox":
            self.natural_spawn_stopped = True
            self.player_hp = 10000; self.player_maxhp = 10000
            self.money = 9999999999
            self.ui.SLOT_TYPES = [None, None, None, None, None]
        # Hardcore: 1.5× placement and upgrade cost multiplier
        self._hc_cost_mult = 1.4 if mode == "hardcore" else 1.0
        # Frosty: force the map
        if mode == "frosty":
            game_core.CURRENT_MAP = "frosty"


        # ── Frosty BGM: start on game init ───────────────────────────────────
        if self.mode == "frosty":
            _bgm1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sound", "frostymode1.mp3")
            try:
                pygame.mixer.music.load(_bgm1)
                pygame.mixer.music.set_volume(0.0 if SETTINGS.get("music_muted") else SETTINGS.get("music_volume", 0.7))
                pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
                pygame.mixer.music.play(0)
                self._frosty_bgm_active = True
                self._frosty_bgm_track = 1
            except Exception:
                pass

    def _pause_caster_sfx(self, pause):
        pass


    def _give_wave_coins(self, wave_num):
        if self.mode not in ("easy", "fallen", "frosty", "infernal", "hardcore"): return
        if wave_num <= self._last_coin_wave: return
        waves_done = wave_num - self._last_coin_wave
        self._last_coin_wave = wave_num
        # Easy: 200 total / 20 waves = 10 per wave
        # Fallen: 750 total / 40 waves = 18.75 per wave
        # Frosty: 1500 total / 40 waves = 37.5 per wave
        # Infernal: 500 total / 34 waves ≈ 14.7 per wave
        # Hardcore: no coins/shards — in-game money given per wave (see wave bonus section)
        if self.mode == "hardcore":
            return
        rate = {"easy": 12.5, "fallen": 18.75, "frosty": 37.5, "infernal": 14.7}.get(self.mode, 12.5)
        self._wave_coin_accum += waves_done * rate
        whole = int(self._wave_coin_accum)
        if whole > 0:
            self._wave_coin_accum -= whole
            self._end_coin_reward += whole
            self.save_data["coins"] = self.save_data.get("coins", 0) + whole
            write_save(self.save_data)


    def _apply_stun(self, unit, duration):
        unit._stun_timer = max(getattr(unit,"_stun_timer",0), duration)

    def _broadcast(self, data):
        pass

    def draw_map(self, offset=(0,0)):
        surf=self.screen; surf.fill(C_BG)
        ox,oy=offset

        # ── Show Grid ─────────────────────────────────────────────────────────
        if SETTINGS.get("show_grid", False):
            _grid_surf = pygame.Surface((SCREEN_W, SLOT_AREA_Y), pygame.SRCALPHA)
            for _gx in range(0, SCREEN_W, TILE):
                pygame.draw.line(_grid_surf, (255, 255, 255, 18), (_gx, 0), (_gx, SLOT_AREA_Y))
            for _gy in range(0, SLOT_AREA_Y, TILE):
                pygame.draw.line(_grid_surf, (255, 255, 255, 18), (0, _gy), (SCREEN_W, _gy))
            surf.blit(_grid_surf, (0, 0))
        random.seed(42)
        if not SETTINGS.get("low_quality", False):
            for _ in range(300):
                gx=random.randint(0,SCREEN_W); gy=random.randint(55,SLOT_AREA_Y-10)
                on_any_path=False
                path=get_map_path()
                for pi in range(len(path)-1):
                    ax,ay=path[pi]; bx,by=path[pi+1]
                    if ax==bx:
                        mnx,mxx=ax-PATH_H-10,ax+PATH_H+10
                        mny,mxy=min(ay,by)-5,max(ay,by)+5
                        if mnx<=gx<=mxx and mny<=gy<=mxy: on_any_path=True; break
                    else:
                        mny,mxy=ay-PATH_H-10,ay+PATH_H+10
                        mnx,mxx=min(ax,bx)-5,max(ax,bx)+5
                        if mny<=gy<=mxy and mnx<=gx<=mxx: on_any_path=True; break
                if not on_any_path:
                    pygame.draw.circle(surf,(32,44,32),(gx+ox,gy+oy),2)
        random.seed()

        if game_core.CURRENT_MAP=="zigzag":
            path=get_map_path()
            # Draw each segment
            for pi in range(len(path)-1):
                ax,ay=path[pi]; bx,by=path[pi+1]
                if ax==bx:  # vertical
                    rx=ax-PATH_H+ox; ry=min(ay,by)+oy
                    rw=PATH_H*2; rh=abs(by-ay)
                else:  # horizontal
                    rx=min(ax,bx)+ox; ry=ay-PATH_H+oy
                    rw=abs(bx-ax); rh=PATH_H*2
                pygame.draw.rect(surf,C_PATH,(rx,ry,rw,rh))
            # Fill corner joints — square patch at every turn point (waypoints 1..n-2)
            for pi in range(1, len(path)-1):
                cx2,cy2=path[pi]
                pygame.draw.rect(surf,C_PATH,
                    (cx2-PATH_H+ox, cy2-PATH_H+oy, PATH_H*2, PATH_H*2))
            # Draw borders on each segment (after fills so borders go on top)
            for pi in range(len(path)-1):
                ax,ay=path[pi]; bx,by=path[pi+1]
                if ax==bx:  # vertical
                    # only draw the sides, not across corners
                    top=min(ay,by); bot=max(ay,by)
                    pygame.draw.line(surf,C_DARKGRAY,(ax-PATH_H+ox,top+oy),(ax-PATH_H+ox,bot+oy),2)
                    pygame.draw.line(surf,C_DARKGRAY,(ax+PATH_H+ox,top+oy),(ax+PATH_H+ox,bot+oy),2)
                    for y in range(top,bot,40):
                        pygame.draw.line(surf,(70,75,90),(ax+ox,y+oy),(ax+ox,y+20+oy),2)
                else:  # horizontal
                    lft=min(ax,bx); rgt=max(ax,bx)
                    pygame.draw.line(surf,C_DARKGRAY,(lft+ox,ay-PATH_H+oy),(rgt+ox,ay-PATH_H+oy),2)
                    pygame.draw.line(surf,C_DARKGRAY,(lft+ox,ay+PATH_H+oy),(rgt+ox,ay+PATH_H+oy),2)
                    for x in range(lft,rgt,40):
                        pygame.draw.line(surf,(70,75,90),(x+ox,ay+oy),(x+20+ox,ay+oy),2)
            # Start/end markers
            sx0,sy0=path[0]
            pygame.draw.rect(surf,(60,20,20),(sx0+ox,sy0-PATH_H+oy,12,PATH_H*2))
            txt(surf,"S",(sx0+6+ox,sy0-5+oy),C_RED,font_sm,center=True)
            # End marker at right exit
            pygame.draw.rect(surf,(20,60,20),(SCREEN_W-12+ox,846-PATH_H+oy,12,PATH_H*2))
            txt(surf,"E",(SCREEN_W-6+ox,846-5+oy),C_GREEN,font_sm,center=True)
        elif game_core.CURRENT_MAP=="event":
            from game_core import _EVENT_PATH
            _ep = _EVENT_PATH
            # Тёмно-красный фон с угольными прожилками — атмосфера ивента
            # Draw each segment as a road strip
            _ev_path_col = (80, 30, 55)      # тёмно-пурпурный путь
            _ev_border_col = (160, 40, 80)   # рубиновые бордюры
            _ev_dash_col = (120, 50, 90)     # штриховые линии
            for pi in range(len(_ep)-1):
                ax,ay=_ep[pi]; bx,by=_ep[pi+1]
                if ax==bx:  # vertical
                    rx=ax-PATH_H+ox; ry=min(ay,by)+oy
                    rw=PATH_H*2; rh=abs(by-ay)
                else:  # horizontal
                    rx=min(ax,bx)+ox; ry=ay-PATH_H+oy
                    rw=abs(bx-ax); rh=PATH_H*2
                pygame.draw.rect(surf,_ev_path_col,(rx,ry,rw,rh))
            # Fill corner joints
            for pi in range(1, len(_ep)-1):
                cx2,cy2=_ep[pi]
                pygame.draw.rect(surf,_ev_path_col,
                    (cx2-PATH_H+ox, cy2-PATH_H+oy, PATH_H*2, PATH_H*2))
            # Borders and dashes
            for pi in range(len(_ep)-1):
                ax,ay=_ep[pi]; bx,by=_ep[pi+1]
                if ax==bx:  # vertical
                    top=min(ay,by); bot=max(ay,by)
                    pygame.draw.line(surf,_ev_border_col,(ax-PATH_H+ox,top+oy),(ax-PATH_H+ox,bot+oy),2)
                    pygame.draw.line(surf,_ev_border_col,(ax+PATH_H+ox,top+oy),(ax+PATH_H+ox,bot+oy),2)
                    for y in range(top,bot,40):
                        pygame.draw.line(surf,_ev_dash_col,(ax+ox,y+oy),(ax+ox,y+20+oy),2)
                else:  # horizontal
                    lft=min(ax,bx); rgt=max(ax,bx)
                    pygame.draw.line(surf,_ev_border_col,(lft+ox,ay-PATH_H+oy),(rgt+ox,ay-PATH_H+oy),2)
                    pygame.draw.line(surf,_ev_border_col,(lft+ox,ay+PATH_H+oy),(rgt+ox,ay+PATH_H+oy),2)
                    for x in range(lft,rgt,40):
                        pygame.draw.line(surf,_ev_dash_col,(x+ox,ay+oy),(x+20+ox,ay+oy),2)
            # Пылающие декоративные угольки на поворотах
            _ev_t = pygame.time.get_ticks()*0.001
            for pi in range(1, len(_ep)-1):
                cx2,cy2=_ep[pi]
                for fi in range(4):
                    fa=math.radians(_ev_t*80+fi*90)
                    fx=cx2+ox+int(math.cos(fa)*(PATH_H-6))
                    fy=cy2+oy+int(math.sin(fa)*(PATH_H-6))
                    fc=int(abs(math.sin(_ev_t*3+fi))*120+80)
                    pygame.draw.circle(surf,(fc,fc//4,0),(fx,fy),3)
            # Старт и финиш
            sx0,sy0=_ep[0]
            pygame.draw.rect(surf,(60,10,10),(sx0+ox,sy0-PATH_H+oy,12,PATH_H*2))
            txt(surf,"S",(sx0+6+ox,sy0-5+oy),C_RED,font_sm,center=True)
            exlast,eylast=_ep[-1]
            pygame.draw.rect(surf,(10,60,10),(SCREEN_W-12+ox,eylast-PATH_H+oy,12,PATH_H*2))
            txt(surf,"E",(SCREEN_W-6+ox,eylast-5+oy),C_GREEN,font_sm,center=True)
        elif game_core.CURRENT_MAP=="frosty":
            from game_core import _FROSTY_CX, _FROSTY_CY, _FROSTY_PATHS, _FROSTY_ARM
            cx_f = _FROSTY_CX + ox
            cy_f = _FROSTY_CY + oy
            road_w = PATH_H * 2   # corridor width in pixels (~84px)

            # ── Vertical arm: top edge → center → bottom of playfield ──
            v_top    = 0
            v_bottom = SCREEN_H - 155   # stop at slot panel top
            pygame.draw.rect(surf, C_PATH,
                (cx_f - PATH_H, v_top + oy, road_w, v_bottom - v_top))
            # Side borders
            pygame.draw.line(surf, C_DARKGRAY,
                (cx_f - PATH_H, v_top + oy), (cx_f - PATH_H, v_bottom + oy), 2)
            pygame.draw.line(surf, C_DARKGRAY,
                (cx_f + PATH_H, v_top + oy), (cx_f + PATH_H, v_bottom + oy), 2)
            # Centre dashes
            for yy in range(v_top, v_bottom, 40):
                pygame.draw.line(surf, (70,75,90),
                    (cx_f, yy + oy), (cx_f, min(yy + 20, v_bottom) + oy), 2)

            # ── Horizontal arm: equal arm length each side of center ──
            h_left  = max(0, _FROSTY_CX - _FROSTY_ARM)
            h_right = min(SCREEN_W, _FROSTY_CX + _FROSTY_ARM)
            pygame.draw.rect(surf, C_PATH,
                (h_left + ox, cy_f - PATH_H, h_right - h_left, road_w))
            # Side borders
            pygame.draw.line(surf, C_DARKGRAY,
                (h_left + ox, cy_f - PATH_H), (h_right + ox, cy_f - PATH_H), 2)
            pygame.draw.line(surf, C_DARKGRAY,
                (h_left + ox, cy_f + PATH_H), (h_right + ox, cy_f + PATH_H), 2)
            # Centre dashes
            for xx in range(h_left, h_right, 40):
                pygame.draw.line(surf, (70,75,90),
                    (xx + ox, cy_f), (min(xx + 20, h_right) + ox, cy_f), 2)

            # ── START markers — small red squares at each of the 4 entry edges ──
            # Top
            pygame.draw.rect(surf, (60,20,20),
                (cx_f - PATH_H, v_top + oy, road_w, 14))
            txt(surf, "S", (cx_f, v_top + 7 + oy), C_RED, font_sm, center=True)
            # Bottom
            pygame.draw.rect(surf, (60,20,20),
                (cx_f - PATH_H, v_bottom - 14 + oy, road_w, 14))
            txt(surf, "S", (cx_f, v_bottom - 7 + oy), C_RED, font_sm, center=True)
            # Left
            pygame.draw.rect(surf, (60,20,20),
                (h_left + ox, cy_f - PATH_H, 14, road_w))
            txt(surf, "S", (h_left + 7 + ox, cy_f), C_RED, font_sm, center=True)
            # Right
            pygame.draw.rect(surf, (60,20,20),
                (h_right - 14 + ox, cy_f - PATH_H, 14, road_w))
            txt(surf, "S", (h_right - 7 + ox, cy_f), C_RED, font_sm, center=True)

            # ── END marker — green circle at the cross center ──
            pygame.draw.circle(surf, (20, 80, 20),  (cx_f, cy_f), PATH_H + 6)
            pygame.draw.circle(surf, (60, 200, 60), (cx_f, cy_f), PATH_H + 6, 3)
            txt(surf, "E", (cx_f, cy_f), C_WHITE, font_sm, center=True)
        elif game_core.CURRENT_MAP in ("uturn", "labyrinth"):
            # Generic multi-segment path renderer for new maps
            _path_data = {
                "uturn":     (_UTURN_PATH,     (55, 80, 30),   (100, 180, 50),  (75, 100, 45)),
                "labyrinth": (_LABYRINTH_PATH,  (20, 60, 70),  (40,  180, 200), (30, 90,  100)),
            }
            _pts, _col, _brd_col, _dash_col = _path_data[game_core.CURRENT_MAP]
            # Fill segments
            for pi in range(len(_pts)-1):
                ax,ay = _pts[pi]; bx,by = _pts[pi+1]
                if ax==bx:  # vertical
                    pygame.draw.rect(surf, _col, (ax-PATH_H+ox, min(ay,by)+oy, PATH_H*2, abs(by-ay)))
                else:       # horizontal
                    pygame.draw.rect(surf, _col, (min(ax,bx)+ox, ay-PATH_H+oy, abs(bx-ax), PATH_H*2))
            # Corner joints
            for pi in range(1, len(_pts)-1):
                cx2,cy2 = _pts[pi]
                pygame.draw.rect(surf, _col, (cx2-PATH_H+ox, cy2-PATH_H+oy, PATH_H*2, PATH_H*2))
            # Borders and dashes
            for pi in range(len(_pts)-1):
                ax,ay = _pts[pi]; bx,by = _pts[pi+1]
                if ax==bx:
                    top=min(ay,by); bot=max(ay,by)
                    pygame.draw.line(surf,_brd_col,(ax-PATH_H+ox,top+oy),(ax-PATH_H+ox,bot+oy),2)
                    pygame.draw.line(surf,_brd_col,(ax+PATH_H+ox,top+oy),(ax+PATH_H+ox,bot+oy),2)
                    for y in range(top,bot,40):
                        pygame.draw.line(surf,_dash_col,(ax+ox,y+oy),(ax+ox,y+20+oy),2)
                else:
                    lft=min(ax,bx); rgt=max(ax,bx)
                    pygame.draw.line(surf,_brd_col,(lft+ox,ay-PATH_H+oy),(rgt+ox,ay-PATH_H+oy),2)
                    pygame.draw.line(surf,_brd_col,(lft+ox,ay+PATH_H+oy),(rgt+ox,ay+PATH_H+oy),2)
                    for x in range(lft,rgt,40):
                        pygame.draw.line(surf,_dash_col,(x+ox,ay+oy),(x+20+ox,ay+oy),2)
            # Start marker
            sx0,sy0 = _pts[0]
            pygame.draw.rect(surf,(60,20,20),(sx0+ox,sy0-PATH_H+oy,12,PATH_H*2))
            txt(surf,"S",(sx0+6+ox,sy0-5+oy),C_RED,font_sm,center=True)
            # End marker
            ex0,ey0 = _pts[-1]
            pygame.draw.rect(surf,(20,60,20),(SCREEN_W-12+ox,ey0-PATH_H+oy,12,PATH_H*2))
            txt(surf,"E",(SCREEN_W-6+ox,ey0-5+oy),C_GREEN,font_sm,center=True)
        else:  # straight map
            pygame.draw.rect(surf,C_PATH,(ox,PATH_Y-PATH_H+oy,SCREEN_W,PATH_H*2))
            pygame.draw.line(surf,C_DARKGRAY,(ox,PATH_Y-PATH_H+oy),(SCREEN_W+ox,PATH_Y-PATH_H+oy),2)
            pygame.draw.line(surf,C_DARKGRAY,(ox,PATH_Y+PATH_H+oy),(SCREEN_W+ox,PATH_Y+PATH_H+oy),2)
            for x in range(0,SCREEN_W,40):
                pygame.draw.line(surf,(70,75,90),(x+ox,PATH_Y+oy),(x+20+ox,PATH_Y+oy),2)
            pygame.draw.rect(surf,(60,20,20),(ox,PATH_Y-PATH_H+oy,12,PATH_H*2))
            txt(surf,"S",(6+ox,PATH_Y-5+oy),C_RED,font_sm,center=True)
            pygame.draw.rect(surf,(20,60,20),(SCREEN_W-12+ox,PATH_Y-PATH_H+oy,12,PATH_H*2))
            txt(surf,"E",(SCREEN_W-6+ox,PATH_Y-5+oy),C_GREEN,font_sm,center=True)

    def run(self):
        while self.running:
            _fps_cap = 720 if SETTINGS.get("unlock_fps") else FPS
            raw_dt = min(self.clock.tick(_fps_cap) / 1000.0, 0.05)
            dt = raw_dt * getattr(self.ui.admin_panel, '_game_speed', 1.0)
            dt *= self.ui._SPEED_STEPS[self.ui._speed_idx]

            for ev in pygame.event.get():
                # ── Why achievement: reset idle timer on any input ────────────
                if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                               pygame.MOUSEMOTION, pygame.KEYDOWN, pygame.KEYUP):
                    self._idle_timer = 0.0
                if ev.type == pygame.QUIT:
                    try: pygame.mixer.music.stop()
                    except: pass
                    self.running = False; return
                if ev.type == pygame.USEREVENT + 1:
                    if not self.game_over and not self.win:
                        if self.mode == "frosty" and self._frosty_bgm_active and not self._frosty_bgm_stopped:
                            # Alternate between frostymode1 and frostymode2
                            self._frosty_bgm_track = 2 if self._frosty_bgm_track == 1 else 1
                            _bgm = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "assets", "sound", f"frostymode{self._frosty_bgm_track}.mp3")
                            try:
                                pygame.mixer.music.load(_bgm)
                                pygame.mixer.music.set_volume(0.0 if SETTINGS.get("music_muted") else SETTINGS.get("music_volume", 0.7))
                                pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
                                pygame.mixer.music.play(0)
                            except Exception:
                                pass
                        else:
                            try: pygame.mixer.music.play(0, start=8.7)
                            except: pass
                if ev.type == pygame.MOUSEWHEEL and self.admin_mode:
                    if self.ui.admin_panel.visible:
                        self.ui.admin_panel.handle_scroll(ev.y); continue
                if self.console.visible:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_F1: self.console.toggle()
                        else: self.console.handle_key(ev, self)
                    continue
                # Admin panel input fields intercept keyboard when active
                if self.admin_mode and self.ui.admin_panel.visible:
                    if ev.type == pygame.KEYDOWN:
                        if self.ui.admin_panel._hp_input_active or self.ui.admin_panel._money_input_active:
                            self.ui.admin_panel.handle_key(ev, self)
                            continue
                if self.paused:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        action = self.pause_menu.handle_click(ev.pos)
                        if action == "resume": self.paused = False
                        elif action == "settings":
                            SettingsScreen(self.screen, self.save_data).run()
                        elif action == "menu":
                            self.paused = False; self.running = False
                            self.return_to_menu = True
                            try: pygame.mixer.music.stop()
                            except: pass
                    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                        self.paused = False
                    continue
                if ev.type == pygame.KEYDOWN and not self.game_over and not self.win:
                    if ev.key == pygame.K_ESCAPE:
                        if self.ui._thorn_place_mode:
                            self.ui._thorn_place_mode  = False
                            self.ui._thorn_place_owner = None
                            self.ui.show_msg("Thorns placement cancelled.", 1.5)
                        elif self.ui.drag_unit:
                            self.ui.drag_unit = None; self.ui.selected_slot = None
                        elif not self.paused: self.paused = True
                    if ev.key == pygame.K_F1: self.console.toggle()
                    # ── F9: skip castbound quest stage (debug) ─────────────────
                    if ev.key == pygame.K_F9:
                        _cq = self.save_data.get("castbound_quest", None)
                        _STAGE_ORDER = [
                            "easy_runs","fallen_runs","frosty_run","pay_coins","pay_shards",
                            "all_achievements","all_towers","max_skilltree","all_skins","moon_lord","done"
                        ]
                        if _cq is None:
                            self.save_data["castbound_quest"] = "easy_runs"
                            self.save_data["castbound_easy_runs"] = 0
                            write_save(self.save_data)
                            self.ui.show_msg("[DEBUG] Castbound: quest started (easy x7)", 3.0)
                        elif _cq in _STAGE_ORDER:
                            idx = _STAGE_ORDER.index(_cq)
                            if idx + 1 < len(_STAGE_ORDER):
                                # Prefill current stage as complete
                                if _cq == "easy_runs":
                                    self.save_data["castbound_easy_runs"] = 7
                                elif _cq == "fallen_runs":
                                    self.save_data["castbound_fallen_runs"] = 7
                                elif _cq == "frosty_run":
                                    self.save_data["castbound_frosty_run"] = True
                                next_s = _STAGE_ORDER[idx + 1]
                                self.save_data["castbound_quest"] = next_s
                                write_save(self.save_data)
                                self.ui.show_msg(f"[DEBUG] Castbound: skipped to {next_s}", 3.0)
                            else:
                                self.ui.show_msg("[DEBUG] Castbound: already at last stage", 2.0)
                        else:
                            self.ui.show_msg("[DEBUG] Castbound: unknown stage", 2.0)
                    if ev.key == pygame.K_e and self.ui.open_unit:
                        u = self.ui.open_unit; cost = u.upgrade_cost()
                        if cost is not None:
                            cost = int(cost * getattr(self.ui, 'cost_mult', 1.0))
                            if cost and self.money >= cost:
                                # Strip Enhanced Optics bonus before upgrade so it doesn't stack
                                if getattr(self, '_sk_range_bonus', 0) > 0:
                                    u.range_tiles = getattr(u, '_base_range_tiles', u.range_tiles)
                                u.upgrade(); self.money -= cost
                                # Re-apply Enhanced Optics range bonus on the fresh post-upgrade range
                                if getattr(self, '_sk_range_bonus', 0) > 0:
                                    u._base_range_tiles = u.range_tiles
                                    u.range_tiles = round(u.range_tiles * (1.0 + self._sk_range_bonus), 4)
                            elif cost: self.ui.show_msg("Not enough money!")
                            else: self.ui.show_msg("Max level!")
                        else: self.ui.show_msg("Max level!")
                    if ev.key == pygame.K_x and self.ui.open_unit:
                        u = self.ui.open_unit
                        _sv = self.ui._sell_value(u)
                        _res_lvl = self.save_data.get("skill_tree", {}).get("resourcefulness", 0)
                        if _res_lvl > 0: _sv = int(_sv * (1.0 + _res_lvl * 0.012))
                        self.money += _sv
                        self.units.remove(u); self.ui.open_unit = None
                        self._ability_cycle_idx = 0  # reset cycle on sell
                    if ev.key == pygame.K_f:
                        # Cycle through units in placement order, activate the first
                        # ready ability found starting from _ability_cycle_idx.
                        # Each press advances to the next unit that has a ready ability.
                        _units_with_ability = [
                            u for u in self.units
                            if (u.ability and u.ability.ready()) or
                               (getattr(u, 'ability2', None) and u.ability2.ready()) or
                               (getattr(u, 'ability3', None) and u.ability3.ready())
                        ]
                        if _units_with_ability:
                            # Clamp cycle index to current list length
                            self._ability_cycle_idx = self._ability_cycle_idx % len(self.units)
                            # Find next unit in placement order that has a ready ability
                            _activated = False
                            for _offset in range(len(self.units)):
                                _idx = (self._ability_cycle_idx + _offset) % len(self.units)
                                _u = self.units[_idx]
                                _ab  = _u.ability if (_u.ability and _u.ability.ready()) else None
                                _ab2 = getattr(_u, 'ability2', None)
                                _ab2 = _ab2 if (_ab2 and _ab2.ready()) else None
                                _ab3 = getattr(_u, 'ability3', None)
                                _ab3 = _ab3 if (_ab3 and _ab3.ready()) else None
                                _best = _ab or _ab2 or _ab3
                                if _best:
                                    if isinstance(_u, Harvester) and _best is _u.ability:
                                        # Harvester Thorns needs player to pick a location
                                        self.ui._thorn_place_mode  = True
                                        self.ui._thorn_place_owner = _u
                                        self.ui.show_msg("Click on the path to place Thorns  [RMB / Esc to cancel]", 4.0)
                                    else:
                                        _best.activate(self.enemies, self.effects)
                                    # Advance cycle index past this unit for next press
                                    self._ability_cycle_idx = (_idx + 1) % len(self.units)
                                    _activated = True
                                    break
                    slot_keys = {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2,pygame.K_4:3,pygame.K_5:4}
                    if ev.key in slot_keys and not self.console.visible:
                        idx = slot_keys[ev.key]; UType = self.ui.SLOT_TYPES[idx]
                        if UType is None: pass
                        elif self.mode != "sandbox" and self.money < int(UType.PLACE_COST * getattr(self.ui, 'cost_mult', 1.0)): self.ui.show_msg("Not enough money!")
                        elif self.mode != "sandbox" and (lambda lim, own: lim is not None and sum(1 for u in own if type(u)==UType) >= lim)(UNIT_LIMITS.get(UType.NAME), [u for u in self.units if not getattr(u,'_mp_peer',False)]): self.ui.show_msg(f"Limit: {UNIT_LIMITS.get(UType.NAME)} {UType.NAME}!")
                        else:
                            mx2, my2 = pygame.mouse.get_pos()
                            self.ui.selected_slot = idx
                            self.ui.drag_unit = UType(mx2, my2)
                            _sk_rng = getattr(self, '_sk_range_bonus', 0)
                            if _sk_rng > 0:
                                self.ui.drag_unit._base_range_tiles = self.ui.drag_unit.range_tiles
                                self.ui.drag_unit.range_tiles = round(self.ui.drag_unit.range_tiles * (1.0 + _sk_rng), 4)
                if self.game_over or self.win:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        if self._end_btn.collidepoint(ev.pos):
                            try: pygame.mixer.music.stop()
                            except: pass
                            if self.admin_mode and not self.win:
                                # Lost in admin-mode: bounce back to sandbox
                                self._restart_mode = "sandbox"
                                self.running = False
                            else:
                                self.running = False; self.return_to_menu = True
                elif not self.game_over:
                    if getattr(self, 'draft_active', False):
                        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                            # Draft Card layout coordinates (must match draw loop)
                            card_w, card_h = 300, 400
                            gap = 60
                            total_w = 2 * card_w + gap
                            start_x = SCREEN_W // 2 - total_w // 2
                            start_y = SCREEN_H // 2 - card_h // 2
                            for i, c in enumerate(self.draft_cards):
                                r = pygame.Rect(start_x + i * (card_w + gap), start_y, card_w, card_h)
                                if r.collidepoint(ev.pos):
                                    cid = c["id"]
                                    if cid == "remove_tower" and self.units:
                                        import random
                                        self.units.remove(random.choice(self.units))
                                    elif cid == "range_down":
                                        self.draft_mod_range_duration += 5
                                    elif cid == "upgrade_cost":
                                        self.draft_mod_upgrade_cost += 0.15
                                    elif cid == "half_money":
                                        self.money //= 2
                                    elif cid == "level_down" and self.units:
                                        import random
                                        u = random.choice(self.units)
                                        if u.level > 0:
                                            u.level -= 1
                                    elif cid == "damage_down":
                                        self.draft_mod_damage_duration += 5
                                    elif cid == "firerate_down":
                                        self.draft_mod_firerate *= 1.25
                                    elif cid == "rollback":
                                        self.wave_mgr.wave = max(1, self.wave_mgr.wave - 3)
                                        self.wave_mgr.state = "idle"
                                        self.wave_mgr._between_timer = 5.0
                                    elif cid == "zero_money":
                                        self.money = 0
                                    elif cid == "damage_5":
                                        self.draft_mod_dmg5_timer = 15.0
                                    elif cid == "all_jesters":
                                        new_units = []
                                        for u in self.units:
                                            new_units.append(Jester(u.px, u.py))
                                        self.units = new_units
                                    
                                    self._draft_state_hash += 1
                                    self.draft_active = False
                                    break
                        continue # block other interactions while draft is active

                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                        if self.ui._thorn_place_mode:
                            self.ui._thorn_place_mode  = False
                            self.ui._thorn_place_owner = None
                            self.ui.show_msg("Thorns placement cancelled.", 1.5)
                        elif getattr(self.ui, '_rc_open', False):
                            self.ui._rc_open = False
                        elif self.ui.drag_unit:
                            self.ui.drag_unit = None; self.ui.selected_slot = None
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        _pre_open = self.ui.open_unit
                        _pre_units_len = len(self.units)
                        _pre_open_lvl = getattr(_pre_open, 'level', -1) if _pre_open else -1
                        delta = self.ui.handle_click(ev.pos, self.units, self.money,
                                                     self.effects, self.enemies,
                                                     self.wave_mgr.wave, self.save_data, self.mode,
                                                     wave_mgr=self.wave_mgr)
                        # Apply Resourcefulness to sell value
                        if delta > 0 and _pre_open is not None and len(self.units) < _pre_units_len:
                            _res_lvl = self.save_data.get("skill_tree", {}).get("resourcefulness", 0)
                            if _res_lvl > 0:
                                delta = int(delta * (1.0 + _res_lvl * 0.012))
                            # No Refunds: mark that a sell happened this run
                            self._sold_this_run = True
                        self.money += delta
                        # ── Putana buyout: клик по ней с 1000$ → мгновенная смерть ──
                        if _INFERNAL_AVAILABLE and self.mode == "infernal":
                            for e in self.enemies:
                                if (e.alive and isinstance(e, Putana)
                                        and dist((e.x, e.y), ev.pos) <= e.radius + 8):
                                    cost = Putana.BUYOUT_COST
                                    if self.money >= cost:
                                        self.money -= cost
                                        e.instant_kill()
                                        if SETTINGS.get("show_damage", True):
                                            self.effects.append(FloatingText(e.x, e.y - 30, f"-${cost} RANSOM!", (255, 180, 220)))
                                    else:
                                        self.ui.show_msg(f"Need ${cost} to ransom!", 2.0)
                                    break
                    if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                        _pre_len = len(self.units)
                        delta = self.ui.handle_release(ev.pos, self.units, self.money)
                        if delta < 0 and len(self.units) > _pre_len:
                            self._towers_placed_count += 1
                        self.money += delta
                    if ev.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                        if getattr(self.ui, '_rc_open', False):
                            sl = getattr(self.ui, '_rc_slider_rect', None)
                            if sl and sl.collidepoint(ev.pos):
                                slider_x = sl.x + 10
                                slider_w = sl.w - 20
                                frac = max(0.0, min(1.0, (ev.pos[0] - slider_x) / slider_w))
                                self.ui._rc_duration = max(5, min(120, int(5 + frac * 115)))

            if not self.game_over and not self.win:
                self._elapsed += raw_dt
                self._real_elapsed += raw_dt
            prev_wave = self.wave_mgr.wave
            
            if self.mode == "draft":
                self.ui.cost_mult = self.draft_mod_upgrade_cost
                for u in self.units:
                    if not hasattr(u, '_draft_synced') or u._draft_synced != (self._draft_state_hash, u.level):
                        if hasattr(u, '_apply_level'):
                            u._apply_level()
                            if getattr(self, '_sk_range_bonus', 0) > 0:
                                u._base_range_tiles = u.range_tiles
                                u.range_tiles = round(u.range_tiles * (1.0 + self._sk_range_bonus), 4)
                            if self.draft_mod_dmg5_timer > 0:
                                u.damage = 5
                            elif self.draft_mod_damage_duration > 0:
                                u.damage *= 0.5
                            u.firerate *= self.draft_mod_firerate
                            if self.draft_mod_range_duration > 0:
                                u.range_tiles *= 0.8
                        u._draft_synced = (self._draft_state_hash, u.level)
            
            if not self.paused and not self.game_over and not self.win and not getattr(self, 'draft_active', False):
                if self.mode == "draft":
                    if self.draft_mod_dmg5_timer > 0:
                        self.draft_mod_dmg5_timer -= dt
                        if self.draft_mod_dmg5_timer <= 0:
                            self.draft_mod_dmg5_timer = 0
                            self._draft_state_hash += 1

                # ── Auto-skip: automatically skip prep/between timers if enabled ──
                if SETTINGS.get("auto_skip", False):
                    if getattr(self.wave_mgr, 'can_skip', lambda: False)():
                        _do_s = getattr(self.wave_mgr, 'do_skip', None)
                        if _do_s: _do_s()
                if not getattr(self,'natural_spawn_stopped',False):
                    _pre_count = len(self.enemies)
                    self.wave_mgr.update(dt,self.enemies)
                    # Frosty mode: assign each newly spawned enemy a lane path
                    if self.mode == "frosty" and len(self.enemies) > _pre_count:
                        for ne in self.enemies[_pre_count:]:
                            lane = self._frosty_lane % 4
                            fp = get_frosty_path(lane)
                            ne._frosty_path = fp
                            ne.x = float(fp[0][0])
                            ne.y = float(fp[0][1])
                            ne._wp_index = 1
                            self._frosty_lane += 1
                if self.wave_mgr.wave!=prev_wave:
                    if self.mode == "draft":
                        if self.draft_mod_range_duration > 0: self.draft_mod_range_duration -= 1
                        if self.draft_mod_damage_duration > 0: self.draft_mod_damage_duration -= 1
                        self._draft_state_hash += 1
                        self.waves_to_next_draft -= 1
                        if self.waves_to_next_draft <= 0:
                            self.draft_active = True
                            import random
                            self.draft_cards = random.sample(_DRAFT_CARDS, 2)
                            self.waves_to_next_draft = random.randint(1, 4)

                    self._wave_leaked=False
                    # Wave just advanced — immediately pay coins for the completed wave
                    self._give_wave_coins(prev_wave)
                    # ── Free Robux screamer ────────────────────────────────────
                    if SETTINGS.get("free_robux", False) and self._screamer_timer <= 0:
                        self._screamer_timer = 10.0  # show for 10 seconds
                        # Load sound once
                        if self._screamer_snd is None:
                            try:
                                _snd_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screamer.mp3")
                                self._screamer_snd = pygame.mixer.Sound(_snd_path)
                            except Exception: self._screamer_snd = False
                        if self._screamer_snd:
                            try:
                                self._screamer_snd.stop()
                                self._screamer_snd.play()
                            except Exception: pass
                        # Load and scale image once
                        if self._screamer_img is None:
                            try:
                                _img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screamer.png")
                                _raw = pygame.image.load(_img_path).convert()
                                self._screamer_img = pygame.transform.scale(_raw, (SCREEN_W, SCREEN_H))
                            except Exception: self._screamer_img = False
    

                for n in [e for e in self.enemies if isinstance(e,Necromancer) and e.alive]:
                    if n.should_summon():
                        for _ in range(5):
                            s2=Enemy(self.wave_mgr.wave); s2.free_kill=True
                            s2.x=n.x; s2.y=n.y; s2._wp_index=getattr(n,'_wp_index',1)
                            self.enemies.append(s2)
    
                # FallenNecromancer summons skeletons
                for n in [e for e in self.enemies if isinstance(e,FallenNecromancer) and e.alive]:
                    if n.should_summon():
                        for _ in range(4):
                            s2=SkeletonEnemy(self.wave_mgr.wave); s2.free_kill=True
                            s2.x=n.x; s2.y=n.y; s2._wp_index=getattr(n,'_wp_index',1)
                            if hasattr(n,'_frosty_path'): s2._frosty_path=n._frosty_path
                            self.enemies.append(s2)
    
                # FrostNecromancer summons frosty enemies
                for n in [e for e in self.enemies if isinstance(e,FrostNecromancer) and e.alive]:
                    if n.should_summon():
                        pool = (FrostUndead, FrostInvader, MegaFrostMystery)
                        for _ in range(5):
                            Sp = random.choice(pool)
                            s2 = Sp(self.wave_mgr.wave); s2.free_kill=True
                            s2.x=n.x; s2.y=n.y; s2._wp_index=getattr(n,'_wp_index',1)
                            if hasattr(n,'_frosty_path'): s2._frosty_path=n._frosty_path
                            self.enemies.append(s2)
    
                # FrostHero: Curse Wave stun (TFK-like)
                for fh in [e for e in self.enemies if isinstance(e,FrostHero) and e.alive]:
                    if fh._curse_active and fh._curse_ring_r<300:
                        for u in self.units:
                            if math.hypot(u.px-fh.x, u.py-fh.y) <= 300:
                                self._apply_stun(u, 3.0)
    
                # FrostSpirit abilities
                for fs in [e for e in self.enemies if isinstance(e,FrostSpirit) and e.alive]:
                    # 1) forward ice column: freeze towers/units in column for 4s
                    if getattr(fs, "_ice_column_timer", 999) <= 0:
                        fs._ice_column_timer = random.uniform(10,15)
                        path = getattr(fs, "_frosty_path", None) or get_map_path()
                        ti = min(getattr(fs, "_wp_index", 1), len(path)-1)
                        tx,ty = path[ti]
                        dx,dy = (tx-fs.x),(ty-fs.y)
                        d = math.hypot(dx,dy) or 1.0
                        ux,uy = dx/d, dy/d
                        width = 120.0
                        length = 560.0
                        for u in self.units:
                            vx,vy = (u.px-fs.x),(u.py-fs.y)
                            proj = vx*ux + vy*uy
                            if proj < 0 or proj > length: continue
                            perp = abs(vx*uy - vy*ux)
                            if perp <= width*0.5:
                                self._apply_stun(u, 4.0)
                    # 2) icicles: 50 impacts, stun 5s (towers/units)
                    if getattr(fs, "_icicles_timer", 999) <= 0:
                        fs._icicles_timer = random.uniform(20,25)
                        if self.units:
                            for _ in range(50):
                                tgt = random.choice(self.units)
                                self._apply_stun(tgt, 5.0)
                    # 3) summon pack: 5 enemies with weighted type + per-type delays
                    if getattr(fs, "_summon_pack_timer", 999) <= 0:
                        fs._summon_pack_timer = 30.0
                        fp = getattr(fs, "_frosty_path", None)
                        wp = getattr(fs, "_wp_index", 1)
                        t_acc = 0.0
                        for _ in range(5):
                            r = random.random()
                            if r < 0.30:
                                cls = FrostAcolyte; delay = 1.5
                            elif r < 0.70:
                                cls = FrostHunter; delay = 0.75
                            else:
                                cls = FrostInvader; delay = 0.25
                            t_acc += delay
                            self._scheduled_spawns.append({
                                "t": t_acc,
                                "cls": cls,
                                "x": fs.x,
                                "y": fs.y,
                                "wp": wp,
                                "fp": fp,
                                "from_wave": True,
                                "free_kill": True,
                            })
    
                # FrostMage: snowball stun a random unit every 7–15s
                for fm in [e for e in self.enemies if isinstance(e,FrostMage) and e.alive]:
                    if getattr(fm, "_snowball_timer", 999) <= 0 and self.units:
                        tgt=random.choice(self.units)
                        self._apply_stun(tgt, 2.5)
                        fm._snowball_timer=random.uniform(7,15)
    
                # FallenKing: hero summon + sword lunge stun
                for k in [e for e in self.enemies if isinstance(e,FallenKing) and e.alive]:
                    if k.should_summon_hero():
                        path = getattr(k,'_frosty_path',None) or get_map_path()
                        # Spawn hero slightly behind king on the path (negative offset)
                        hero=FallenHero(self.wave_mgr.wave)
                        hero.x = k.x - random.uniform(30, 80)
                        hero.y = float(path[min(k._wp_index, len(path)-1)-1][1]) if k._wp_index > 0 else k.y
                        hero._wp_index = max(1, k._wp_index - 1)
                        if hasattr(k,'_frosty_path'): hero._frosty_path=k._frosty_path
                        hero.free_kill=True
                        self.enemies.append(hero)
                    # 'armed' state: pick nearest unit and start lunge
                    if k._sword_state=='armed' and self.units:
                        best=min(self.units, key=lambda u: math.hypot(u.px-k.x, u.py-k.y))
                        k._sword_target_unit=best
                        k._sword_tx=best.px; k._sword_ty=best.py
                        k._sword_state='leaving'
                        k._sword_hit=False
                    # 'striking' state: deal stun once
                    if k._sword_state=='striking' and not k._sword_hit:
                        k._sword_hit=True
                        if k._sword_target_unit and k._sword_target_unit in self.units:
                            self._apply_stun(k._sword_target_unit, 5.0)
                    # override freeze immunity
                    k._frost_frozen=False; k.frozen=False
    
                # Wave 40 in fallen mode: music → flash → FallenKing
                if self.mode=="fallen" and self.wave_mgr.wave==40 and not self._fallen_king_spawned:
                    if self._fallen_king_music_timer is None:
                        _music_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"assets","sound","fallenking.mp3")
                        try:
                            pygame.mixer.music.load(_music_path)
                            pygame.mixer.music.play(0)
                            pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
                        except Exception:
                            pass
                        self._fallen_king_music_timer=8.025
                        self._ceremony_phase='waiting'
                        self._ceremony_timer=0.0
                        self._ceremony_flash_alpha=0
                        self._ceremony_flash_color=(255,255,255)
                    else:
                        self._fallen_king_music_timer-=dt
                        self._ceremony_timer+=dt
    
                        # Flash starts 1 second before boss (at music_timer == 1.0)
                        time_to_spawn=self._fallen_king_music_timer
    
                        if time_to_spawn<=1.0 and self._ceremony_phase=='waiting':
                            self._ceremony_phase='flash_in'
                            self._ceremony_timer=0.0
    
                        if self._ceremony_phase=='flash_in':
                            # 0.2s to reach full white
                            self._ceremony_flash_color=(255,255,255)
                            self._ceremony_flash_alpha=min(255,int(self._ceremony_timer/0.2*255))
                            if self._ceremony_timer>=0.2:
                                self._ceremony_phase='flash_hold'
    
                        elif self._ceremony_phase=='flash_hold':
                            # Hold full white, transition to purple as boss approaches
                            # Purple starts at 0.4s remaining
                            if time_to_spawn<=0.4:
                                purple_t=1.0-(time_to_spawn/0.4)
                                r=int(255*(1-purple_t)+180*purple_t)
                                g=int(255*(1-purple_t)+0*purple_t)
                                b=int(255*(1-purple_t)+255*purple_t)
                                self._ceremony_flash_color=(r,g,b)
                            self._ceremony_flash_alpha=255
    
                        # Spawn boss + instantly kill flash
                        if self._fallen_king_music_timer<=0:
                            self._fallen_king_spawned=True
                            self._fallen_king_shake=1.2
                            fk=FallenKing(40); fk.x=-60.0; fk._from_wave=True
                            self.enemies.append(fk)
                            self._ceremony_flash_alpha=0
                            self._ceremony_phase='done'
    
                if self.mode=="frosty" and self.wave_mgr.wave==40 and not self._frost_spirit_spawned:
                    if self._frosty_bgm_active and not self._frosty_bgm_stopped:
                        self._frosty_bgm_stopped = True
                        self._frosty_bgm_active = False
                        try: pygame.mixer.music.stop()
                        except: pass
                    if self._frost_spirit_music_timer is None:
                        _music_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"assets","sound","frostspirit.mp3")
                        try:
                            pygame.mixer.music.load(_music_path)
                            pygame.mixer.music.play(0)
                        except Exception:
                            pass
                        self._frost_spirit_music_timer = 27.0
                    else:
                        self._frost_spirit_music_timer -= dt
                        if self._frost_spirit_music_timer <= 0:
                            self._frost_spirit_spawned = True
                            fs = FrostSpirit(40)
                            fs._from_wave = True
                            from game_core import get_frosty_path as _gfp
                            fp = _gfp(0)  # top lane for FrostSpirit
                            fs._frosty_path = fp
                            fs.x = float(fp[0][0]); fs.y = float(fp[0][1]); fs._wp_index = 1
                            self.enemies.append(fs)
    
                # Process scheduled delayed spawns (Frost Spirit summon pack)
                if self._scheduled_spawns:
                    new_sched=[]
                    for item in self._scheduled_spawns:
                        item["t"] -= dt
                        if item["t"] > 0:
                            new_sched.append(item); continue
                        cls=item["cls"]
                        baby=cls(self.wave_mgr.wave)
                        baby.x=item["x"]; baby.y=item["y"]
                        baby._wp_index=item.get("wp",1)
                        fp=item.get("fp")
                        if fp is not None: baby._frosty_path=fp
                        if item.get("from_wave", False): baby._from_wave=True
                        if item.get("free_kill", False): baby.free_kill=True
                        self.enemies.append(baby)
                    self._scheduled_spawns = new_sched
    
                # flash_out no longer needed — flash dies instantly on spawn
    

    

    
                dead_reached=[]
                for e in self.enemies:
                    if not e.alive: continue
                    # Reversed enemy: walks backward along path and deals collision damage
                    if getattr(e,'_reversed',False):
                        e._bob += dt * 4
                        # Always use the correct path for the current map
                        _path = getattr(e, '_frosty_path', None) or get_map_path()
                        _wp = getattr(e, '_wp_index', 1)

                        # Target = the waypoint the enemy already passed (index _wp - 2),
                        # which is the one BEFORE the next waypoint (_wp - 1 is current pos target).
                        # _wp_index points to the NEXT waypoint to reach going forward,
                        # so the waypoint the enemy is currently between is _wp-1 → _wp.
                        # Going backward: head toward _wp-1 (already passed), clamped to 0.
                        _target_idx = max(0, _wp - 1)
                        _ptx, _pty = _path[_target_idx]
                        _dx = _ptx - e.x; _dy = _pty - e.y
                        _d = math.hypot(_dx, _dy)
                        _step = e.speed * dt * 1.5
                        if _d <= _step + 1:
                            # Snap to waypoint and decrement index so next tick targets
                            # the waypoint before that
                            e.x = float(_ptx); e.y = float(_pty)
                            e._wp_index = max(1, _wp - 1)
                        else:
                            e.x += _dx / _d * _step
                            e.y += _dy / _d * _step

                        # If enemy reached the very first waypoint — stop confusion
                        _start = _path[0]
                        if e._wp_index <= 1 and math.hypot(e.x - _start[0], e.y - _start[1]) < 8:
                            e._reversed = False
                            e._jester_conf_timer = 0.0
                            e._wp_index = 1
                            continue

                        # Tick confusion timer while reversed so it can expire mid-movement
                        _ct = getattr(e, '_jester_conf_timer', 0.0)
                        if _ct > 0:
                            e._jester_conf_timer = _ct - dt
                            if e._jester_conf_timer <= 0:
                                e._reversed = False
                                e._jester_conf_timer = 0.0

                        continue
    
                    if e.update(dt):
                        if isinstance(e,FastBoss):
                            e.alive=False
                        elif getattr(e,'_confused',False):
                            pass  # confused enemy walked backward — don't count as leaked
                        else:
                            dead_reached.append(e)
    
                for e in dead_reached:
                    self.player_hp=max(0,self.player_hp-max(1,int(e.hp))); e.alive=False
                    e._reward_paid=True  # reached end — no kill reward
                    # SpecterEnemy (???) — мгновенное поражение если дойдёт до базы
                    if _INFERNAL_AVAILABLE and getattr(e, 'INSTANT_DEFEAT', False) and self.mode != "sandbox":
                        self.player_hp = 0
                if dead_reached: self._wave_leaked=True
                if self.player_hp<=0 and dead_reached and self.mode != "sandbox":
                    self.game_over=True
                    # ── Achievement: Жертва Короля ─ lose to FallenKing at wave 40 in Fallen
                    if self.mode=="fallen" and self.wave_mgr.wave==40:
                        if any(isinstance(e,FallenKing)
                               for e in dead_reached):
                            self.ach_mgr.try_grant("king_victim")
                    # ── Profile stats: record loss ────────────────────────────
                    _mode_key = self.mode if self.mode else "easy"
                    _pst = self.save_data.setdefault("profile_stats", {})
                    _pst["total_games"]  = _pst.get("total_games", 0) + 1
                    _pst["total_losses"] = _pst.get("total_losses", 0) + 1
                    _pst.setdefault("losses_by_mode", {})[_mode_key] = _pst.get("losses_by_mode", {}).get(_mode_key, 0) + 1
                    _pst["total_waves"]  = _pst.get("total_waves", 0) + self.wave_mgr.wave
                    _pst["best_wave_" + _mode_key] = max(_pst.get("best_wave_" + _mode_key, 0), self.wave_mgr.wave)
                    # ── grand_slam chain broken on loss — reset
                    self.save_data["_gs_chain"] = []
                    write_save(self.save_data)
                    try:
                        pygame.mixer.music.set_endevent(0)
                        pygame.mixer.music.stop()
                    except: pass
    
                # Kill rewards: give money + floating text for freshly killed enemies
                for e in self.enemies:
                    if not e.alive and not getattr(e,"_reward_paid",False) and not getattr(e,"free_kill",False):
                        e._reward_paid=True
                        self._total_kills += 1
                        reward=e.KILL_REWARD

                        # Scavenger: every N kills -> 1.5x reward
                        _scav_n = getattr(self, "_sk_scavenger_n", 0)
                        if _scav_n > 0 and reward > 0:
                            self._sk_kill_counter += 1
                            if self._sk_kill_counter >= _scav_n:
                                self._sk_kill_counter = 0
                                reward = int(reward * 1.5)
                        # easy mode gives no kill reward; all other modes (incl. hardcore) do
                        if reward>0 and self.mode != "easy":
                            self.money+=reward
                            if SETTINGS.get("show_damage", True):
                                self.effects.append(FloatingText(e.x, e.y-e.radius-10, f"+{reward}"))

                # Global tick: jester confusion CD and timer (runs regardless of Jester alive/on field)
                for e in self.enemies:
                    if not e.alive: continue
                    _cd = getattr(e, '_jester_conf_cd', 0.0)
                    if _cd > 0 and not getattr(e, '_reversed', False):
                        e._jester_conf_cd = max(0.0, _cd - dt)
                    # Tick stun immunity cooldown
                    _si = getattr(e, '_stun_immune_cd', 0.0)
                    if _si > 0:
                        e._stun_immune_cd = max(0.0, _si - dt)
                    # Skip conf_timer decrement for reversed enemies — already ticked above
                    if getattr(e, '_reversed', False): continue
                    _ct = getattr(e, '_jester_conf_timer', 0.0)
                    if _ct > 0:
                        e._jester_conf_timer = _ct - dt
                        if e._jester_conf_timer <= 0:
                            e._reversed = False
                            e._jester_conf_timer = 0.0
    
                # Frost Spirit: reward per 2.5% hp lost (12_500 each step)
                if self.mode != "easy":
                    for fs in [e for e in self.enemies if isinstance(e, FrostSpirit) and e.alive and not getattr(e, "free_kill", False)]:
                        maxhp = max(1.0, float(fs.maxhp))
                        lost = max(0.0, min(1.0, 1.0 - float(fs.hp)/maxhp))
                        steps = int(lost / 0.025)
                        paid = int(getattr(fs, "_reward_steps_paid", 0))
                        if steps > paid:
                            delta = steps - paid
                            fs._reward_steps_paid = steps
                            amt = 12500 * delta
                            self.money += amt
                            if SETTINGS.get("show_damage", True):
                                self.effects.append(FloatingText(fs.x, fs.y-fs.radius-18, f"+{amt}"))
    
                _x5k = getattr(self,"_x5000_dmg",False)
                for u in self.units:
                    # Stun: frozen by FallenKing sword
                    if getattr(u,'_stun_timer',0)>0:
                        u._stun_timer-=dt
                        if u._stun_timer<=0: u._stun_timer=0
                        continue  # skip update while stunned
                    if self._ceremony_phase not in (None,'done'):
                        continue
                    # Conduit: pass unit list for charge collection
                    if isinstance(u, Conduit):
                        u._all_units = self.units
                    if _x5k:
                        _orig_dmg = u.damage
                        u.damage = u.damage * 5000
                    # Silyach debuff: -75% damage for 8s
                    _sil_db = getattr(u, '_silyach_debuff', 0.0)
                    if _sil_db > 0 and _INFERNAL_AVAILABLE:
                        _orig_dmg_sil = u.damage
                        u.damage = u.damage * Silyach.DEBUFF_DAMAGE_MULT
                        u.update(dt,self.enemies,self.effects,self.money)
                        u.damage = _orig_dmg_sil
                    else:
                        u.update(dt,self.enemies,self.effects,self.money)
                    if _x5k:
                        u.damage = _orig_dmg
                    # Tick ControlPanel ability cooldown manually
                    if isinstance(u, ControlPanel) and u.ability is not None:
                        if u.ability.cd_left > 0:
                            u.ability.cd_left = max(0.0, u.ability.cd_left - dt)
                    # No ability CD sandbox cheat
                    if getattr(getattr(getattr(self, 'ui', None), 'admin_panel', None), '_no_ability_cd', False):
                        for ab_attr in ('ability', 'ability2', 'ability3'):
                            ab = getattr(u, ab_attr, None)
                            if ab is not None and hasattr(ab, 'cd_left'):
                                ab.cd_left = 0.0
                # Collect Lifestealer blood money
                for u in self.units:
                    if isinstance(u,Lifestealer):
                        pm=getattr(u,'_pending_money',0)
                        if pm>0: self.money+=pm; u._pending_money=0

                # Castbound: track damage dealt → charge Terraprisma bar
                _CB_CHARGE_MAX = 1500
                for u in self.units:
                    if not isinstance(u, Castbound):
                        continue
                    # Init attrs if missing
                    if not hasattr(u, '_terraprisma_charge'):
                        u._terraprisma_charge = 0.0
                        u._terraprisma_last_total = getattr(u, 'total_damage', 0.0)
                        u._terraprismas = []
                    # Delta damage this tick
                    cur_total = getattr(u, 'total_damage', 0.0)
                    delta = max(0.0, cur_total - u._terraprisma_last_total)
                    u._terraprisma_last_total = cur_total
                    u._terraprisma_charge += delta
                    # Spawn Terraprisma when bar full, max 3
                    while u._terraprisma_charge >= _CB_CHARGE_MAX and len(u._terraprismas) < 3:
                        u._terraprisma_charge -= _CB_CHARGE_MAX
                        idx = len(u._terraprismas)
                        u._terraprismas.append(Terraprisma(u, idx))
                    if u._terraprisma_charge >= _CB_CHARGE_MAX and len(u._terraprismas) >= 3:
                        u._terraprisma_charge = _CB_CHARGE_MAX  # cap when full
                    # Update Terraprismas
                    if not hasattr(self, '_all_terraprismas'):
                        self._all_terraprismas = []
                    u._terraprismas = [
                        tp for tp in u._terraprismas
                        if tp.update(dt, self.enemies, self.effects)
                    ]
                    # Re-index after expiry
                    for i, tp in enumerate(u._terraprismas):
                        tp.index = i
    

                # SoulWeaver: inject refs, tick kills → stacks, tick buff expirations
                for u in self.units:
                    if isinstance(u, SoulWeaver):
                        u._units_ref = self.units
                        u._game_ref  = self
                # Award soul stacks for enemies killed this tick
                for e in self.enemies:
                    if not e.alive and not getattr(e, '_sw_counted', False):
                        e._sw_counted = True
                        for u in self.units:
                            if isinstance(u, SoulWeaver):
                                if dist((e.x, e.y), (u.px, u.py)) <= u.range_tiles * TILE:
                                    u.notify_kill(e)
                                    # Check chain explosion
                                    # find which unit killed it (closest attacker in range)
                                    killer = None
                                    best_d = 9999
                                    for ku in self.units:
                                        if isinstance(ku, SoulWeaver): continue
                                        d2 = dist((ku.px, ku.py), (e.x, e.y))
                                        if d2 <= ku.range_tiles * TILE and d2 < best_d:
                                            best_d = d2; killer = ku
                                    if killer:
                                        u.check_chain(killer, e, self.enemies, self.effects)
                _sw_tick_buffs(self.units)
    
                # Collect GoldenCowboy cash shot income
                for u in self.units:
                    if isinstance(u,GoldenCowboy):
                        earned=u.collect_income()
                        if earned>0:
                            self.money+=earned
                            self._cowboy_income_total += earned  # Gold Rush tracking
                            if SETTINGS.get("show_damage", True):
                                self.effects.append(FloatingText(u.px,u.py-30,f"+${earned}",(255,220,60)))
    
                # Kill rewards (second pass — catches kills from unit attacks this tick)
                for e in self.enemies:
                    if not e.alive and not getattr(e,'_reward_paid',False) and not getattr(e,'free_kill',False):
                        e._reward_paid=True
                        reward=e.KILL_REWARD
                        if reward>0 and self.mode != "easy":
                            self.money+=reward
                            self._cowboy_only_run = False  # Gold Rush: kill reward voids cowboy-only run
                            if SETTINGS.get("show_damage", True):
                                self.effects.append(FloatingText(e.x, e.y-e.radius-10, f"+{reward}"))

    
                new_enemies=[]
                for e in self.enemies:
                    if not e.alive and isinstance(e,BreakerEnemy) and not getattr(e,'_spawned',False):
                        e._spawned=True
                        Sp=random.choice(BREAKER_POOL); baby=Sp(self.wave_mgr.wave)
                        baby.x=e.x; baby.y=e.y; baby._wp_index=getattr(e,'_wp_index',1)
                        if hasattr(e,'_frosty_path'): baby._frosty_path=e._frosty_path
                        baby.free_kill=True; new_enemies.append(baby)
                    # FrostMystery: spawns 1 random enemy (SnowyEnemy or FrozenEnemy)
                    # MegaFrostMystery: spawns 2 random enemies
                    if (not e.alive and isinstance(e,(FrostMystery, MegaFrostMystery)) and not getattr(e,'_spawned',False)):
                        e._spawned=True
                        mult = 2 if isinstance(e, MegaFrostMystery) else 1
                        for _ in range(mult):
                            cls = random.choice([SnowyEnemy, FrozenEnemy])
                            baby = cls(self.wave_mgr.wave)
                            baby.x=e.x; baby.y=e.y; baby._wp_index=getattr(e,'_wp_index',1)
                            if hasattr(e,'_frosty_path'): baby._frosty_path=e._frosty_path
                            baby.free_kill=True; new_enemies.append(baby)
                    # FallenBreaker spawns 1 fallen variant
                    if not e.alive and isinstance(e,FallenBreaker) and not getattr(e,'_spawned',False):
                        e._spawned=True
                        Sp=random.choice(FALLEN_BREAKER_POOL); baby=Sp(self.wave_mgr.wave)
                        baby.x=e.x; baby.y=e.y; baby._wp_index=getattr(e,'_wp_index',1)
                        if hasattr(e,'_frosty_path'): baby._frosty_path=e._frosty_path
                        baby.free_kill=True; new_enemies.append(baby)
                    # PossessedArmor spawns inner ghost on death
                    if not e.alive and isinstance(e,PossessedArmor) and not e._spawned_inner:
                        e._spawned_inner=True
                        inner=PossessedArmorInner(self.wave_mgr.wave)
                        inner.x=e.x; inner.y=e.y; inner._wp_index=getattr(e,'_wp_index',1)
                        if hasattr(e,'_frosty_path'): inner._frosty_path=e._frosty_path
                        new_enemies.append(inner)
                    # MysteryEnemy spawns a random enemy on death
                    if not e.alive and isinstance(e,MysteryEnemy) and not e._spawned_mystery:
                        e._spawned_mystery=True
                        Sp=random.choice(MYSTERY_SPAWN_POOL)
                        baby=Sp(self.wave_mgr.wave)
                        baby.x=e.x; baby.y=e.y; baby._wp_index=getattr(e,'_wp_index',1)
                        if hasattr(e,'_frosty_path'): baby._frosty_path=e._frosty_path
                        baby.free_kill=True; new_enemies.append(baby)

                    # ── INFERNAL mode death spawns ─────────────────────────────
                    if _INFERNAL_AVAILABLE and self.mode in ("infernal",):
                        # Snowball → SnowCorpse
                        if not e.alive and isinstance(e, Snowball) and not getattr(e,'_spawned_corpse',False):
                            e._spawned_corpse=True
                            c=SnowCorpse(self.wave_mgr.wave, e.x, e.y, getattr(e,'_wp_index',1))
                            c.free_kill=True; new_enemies.append(c)
                        # Furnace → 3 Embers
                        if not e.alive and isinstance(e, Furnace) and not getattr(e,'_spawned_embers',False):
                            e._spawned_embers=True
                            for _ in range(3):
                                em=Ember(self.wave_mgr.wave, e.x, e.y, getattr(e,'_wp_index',1))
                                em.free_kill=True; new_enemies.append(em)
                        # InfernalMystery → random drop
                        if not e.alive and isinstance(e, InfernalMystery) and not getattr(e,'_spawned',False):
                            e._spawned=True
                            for drop in e.get_mystery_drop():
                                drop.free_kill=True; new_enemies.append(drop)

                # ── INFERNAL mode active-enemy abilities ──────────────────────
                if _INFERNAL_AVAILABLE and self.mode == "infernal":
                    # Furnace: stun units in radius 100 periodically
                    for f in [e for e in self.enemies if isinstance(e, Furnace) and e.alive]:
                        if f.should_stun():
                            for u in self.units:
                                if math.hypot(u.px-f.x, u.py-f.y) <= 100:
                                    self._apply_stun(u, 1.5)
                    # Stomp: stun NEARBY units only
                    for s in [e for e in self.enemies if isinstance(e, Stomp) and e.alive]:
                        if s.should_stomp():
                            for u in self.units:
                                if math.hypot(u.px-s.x, u.py-s.y) <= s.stomp_radius:
                                    self._apply_stun(u, 1.2)
                    # Terpila rage: stun 1 random unit every 3s when in rage
                    for t in [e for e in self.enemies if isinstance(e, Terpila) and e.alive]:
                        if t.should_rage_stun() and self.units:
                            self._apply_stun(random.choice(self.units), 3.0)
                    # Confusilionale: stun 1 unit (simplified — friendly-fire not implemented yet)
                    for c in [e for e in self.enemies if isinstance(e, Confusilionale) and e.alive]:
                        if c.should_confuse() and self.units:
                            self._apply_stun(random.choice(self.units), 2.5)
                    # Silyach (Cigarette): debuff damage of random unit for 8s
                    for s in [e for e in self.enemies if isinstance(e, Silyach) and e.alive]:
                        if s.should_debuff() and self.units:
                            u = random.choice(self.units)
                            u._silyach_debuff = Silyach.DEBUFF_DURATION
                    # Apply/decay Silyach debuff to units
                    for u in self.units:
                        db = getattr(u, '_silyach_debuff', 0.0)
                        if db > 0:
                            u._silyach_debuff = db - dt
                    # Kolobok: jump stun
                    for k in [e for e in self.enemies if isinstance(e, Kolobok) and e.alive]:
                        if k.should_jump():
                            for u in self.units:
                                if math.hypot(u.px-k.x, u.py-k.y) <= k.jump_radius:
                                    self._apply_stun(u, 2.0)
                    # GrandmaEnemy: rolling pin stun
                    for g in [e for e in self.enemies if isinstance(e, GrandmaEnemy) and e.alive]:
                        if g.should_stun() and self.units:
                            for u in self.units:
                                if math.hypot(u.px-g.x, u.py-g.y) <= g.rolling_pin_radius:
                                    self._apply_stun(u, 1.8)
                    # FateCollector reached base → bonus money (handled below in dead_reached)
                    # Untouchable: block non-allowed unit attacks
                    # (unit.update already dealt dmg; we cancel it for Untouchable if attacker wrong)
                    # — complex to fully wire; left as design note; HP=1 so dies fast from allowed units

                    # ── Challenger phase transition ────────────────────────────
                    if (not self._infernal_challenger
                            and self.wave_mgr.state == "done"
                            and not any(e.alive for e in self.enemies)):
                        self._infernal_challenger = True
                        self._challenger_wave_mgr = WaveManager(
                            wave_data=CHALLENGER_WAVE_DATA,
                            max_waves=CHALLENGER_MAX_WAVES)
                        # Reduce all unit radii by 10%
                        if not self._challenger_radius_applied:
                            self._challenger_radius_applied = True
                            for u in self.units:
                                u.range_tiles = u.range_tiles * 0.90
                        self.ui.show_msg("🔥 MASS GRAVE 🔥 - all towers range -10%!", 6.0)

                    # Switch wave manager to challenger
                    if self._infernal_challenger and self._challenger_wave_mgr:
                        self.wave_mgr = self._challenger_wave_mgr
                        self._challenger_wave_mgr = None

                    # Challenger wave 6: no enemies, just -10 HP
                    if (self._infernal_challenger
                            and self.wave_mgr.wave == 6
                            and not self._challenger_wave6_done
                            and self.wave_mgr.state == "waiting"):
                        self._challenger_wave6_done = True
                        self.player_hp = max(1, self.player_hp - CHALLENGER_WAVE6_HP_DAMAGE)
                        self.ui.show_msg(f"Wave 6: -10 HP! HP = {self.player_hp}", 4.0)

                # FateCollector reached base → +500$ per collector
                if _INFERNAL_AVAILABLE:
                    for e in dead_reached:
                        if isinstance(e, FateCollector):
                            self.money += FateCollector.REACH_BONUS
                            if SETTINGS.get("show_damage", True):
                                self.effects.append(FloatingText(e.x, e.y-30, f"+{FateCollector.REACH_BONUS}$", (255,220,60)))

                # ── FateCollector kill penalty (-100$) ────────────────────────
                if _INFERNAL_AVAILABLE:
                    for e in self.enemies:
                        if (not e.alive and not getattr(e,'_reward_paid',False)
                                and isinstance(e, FateCollector)
                                and not getattr(e,'free_kill',False)):
                            e._reward_paid = True
                            # negative reward: player LOSES money
                            penalty = abs(e.KILL_REWARD)
                            self.money = max(0, self.money - penalty)
                            if SETTINGS.get("show_damage", True):
                                self.effects.append(FloatingText(e.x, e.y-e.radius-10, f"-{penalty}$", (255,80,80)))

                _base_keep = (BreakerEnemy, FallenBreaker, PossessedArmor, FrostMystery)
                if _INFERNAL_AVAILABLE and self.mode == "infernal":
                    _keep = _base_keep + (Snowball, Furnace, InfernalMystery)
                else:
                    _keep = _base_keep
                self.enemies=[e for e in self.enemies if e.alive or isinstance(e, _keep)]+new_enemies
    
                gds=[e for e in self.enemies if isinstance(e,GraveDigger) and e.alive]
                self._boss_enemy=gds[0] if gds else (
                    self._boss_enemy if self._boss_enemy and self._boss_enemy.alive else None)
    
                # Track first wave-spawned appearances of fallen bosses for boss bars
                if self.mode=="fallen":
                    _fallen_bar_classes=(FallenGiant,FallenJester,FallenSquire,FallenKing,FallenShield,FallenHonorGuard)
                    for e in self.enemies:
                        if not e.alive: continue
                        if not getattr(e,'_from_wave',False): continue
                        cls=type(e)
                        if cls in _fallen_bar_classes and cls not in self._fallen_boss_bars:
                            self._fallen_boss_bars[cls]=e
                    # Always keep FallenKing bar updated to current alive instance
                        fk_alive=[e for e in self.enemies if isinstance(e,FallenKing) and e.alive]
                        if fk_alive:
                            self._fallen_boss_bars[FallenKing]=fk_alive[0]
    
                # Frosty boss bars: only on FIRST wave-spawned appearance (no sandbox spawns)
                if self.mode=="frosty":
                    _frosty_bar_classes=(
                        SnowMinion, FrostHunter, FrostAcolyte,
                        FrostUndead, FrostInvader, FrostRavager,
                        Yeti, FrostMage, FrostHero,
                    )
                    for e in self.enemies:
                        if not e.alive: continue
                        if not getattr(e,'_from_wave',False): continue
                        cls=type(e)
                        if cls in _frosty_bar_classes and cls not in self._frosty_bossbar_seen:
                            self._frosty_bossbar_seen.add(cls)
                            self._fallen_boss_bars[cls]=e
    
                # Frost Spirit: boss bar always (including sandbox)
                fs_alive = [e for e in self.enemies if isinstance(e, FrostSpirit) and e.alive]
                if fs_alive:
                    self._fallen_boss_bars[FrostSpirit] = fs_alive[0]
    
                # tf_test: always track 1M miniboss and TFK in boss bars regardless of mode
    
                _skipped_pending = getattr(self.wave_mgr, '_lmoney_pay_pending', False)
                if ((self.wave_mgr.state in ("waiting", "between", "done")
                        and not any(e.alive for e in self.enemies) and not self.wave_mgr._lmoney_paid)
                        or _skipped_pending):
                    # For skipped waves: look up lmoney for the wave that was skipped,
                    # and do NOT award bmoney (wave clear bonus) since it wasn't cleared normally.
                    if _skipped_pending:
                        _pw = self.wave_mgr._lmoney_pending_wave or (self.wave_mgr.wave - 1)
                        _saved_wave = self.wave_mgr.wave
                        self.wave_mgr.wave = _pw
                        lm = self.wave_mgr.wave_lmoney()
                        self.wave_mgr.wave = _saved_wave
                        bm = 0  # no wave-clear bonus on skip
                    else:
                        lm=self.wave_mgr.wave_lmoney(); bm=self.wave_mgr.wave_bmoney()
                    if self.mode == "hardcore":
                        _hc_w = self.wave_mgr.wave
                        _HC_LM = {
                            1:204,  2:250,  3:298,  4:347,  5:400,
                            6:446,  7:496,  8:546,  9:596,  10:647,
                            11:698, 12:759, 13:800, 14:851, 15:874,
                            16:954, 17:978, 18:995, 19:1057, 20:1109,
                            21:1161,22:1213,23:1265,24:1317,25:1421,
                            26:1467,27:1526,28:1579,29:1634,30:1684,
                            31:1734,32:1795,33:1813,34:1875,35:2000,
                            36:2100,37:2200,38:2300,39:2400,40:2500,
                            41:2600,42:2700,43:2800,44:2900,45:3000,
                            46:3100,47:3200,48:3300,49:3400,50:15000,
                        }
                        _HC_BM = {
                            1:0,   2:50,  3:59,  4:69,  5:80,
                            6:94,  7:99,  8:109, 9:119, 10:129,
                            11:139,12:156,13:160,14:170,15:180,
                            16:190,17:200,18:205,19:211,20:221,
                            21:232,22:242,23:253,24:273,25:286,
                            26:297,27:305,28:315,29:334,30:336,
                            31:341,32:349,33:359,34:364,35:380,
                            36:400,37:450,38:500,39:550,40:600,
                            41:650,42:700,43:750,44:800,45:850,
                            46:900,47:950,48:1000,49:1050,50:0,
                        }
                        lm = _HC_LM.get(_hc_w, 0)
                        bm = _HC_BM.get(_hc_w, 0)
                    elif self.mode == "frosty":
                        if lm: lm += 150
                        if bm: bm += 150
                    elif self.mode == "infernal":
                        if lm: lm += 300
                        if bm: bm += 300
                    # Apply Stonks skill bonus to wave rewards
                    _sw = getattr(self, "_sk_wave_bonus", 0)
                    if _sw > 0:
                        if lm: lm = int(lm * (1.0 + _sw))
                        if bm: bm = int(bm * (1.0 + _sw))
                    # Farm income — only count OWN farms (not peer farms)
                    own_farms = [u for u in self.units if isinstance(u, Farm)]
                    farm_income = sum(u.income for u in own_farms)
                    if farm_income>0:
                        self.money+=farm_income
                        self.ui.show_msg(f"+{farm_income} Farm income",2.5)
                    _timer_expired = (getattr(self.wave_mgr, '_prev_wave_timer_expired', False)
                                      if _skipped_pending else
                                      getattr(self.wave_mgr, '_timer_expired', False))
                    if self._wave_leaked or _timer_expired:
                        if lm: self.money+=lm; self.ui.show_msg(f"+{lm} Wave bonus",2.5)
                    else:
                        msgs=[]
                        if lm: self.money+=lm; msgs.append(f"+{lm} Wave bonus")
                        if bm: self.money+=bm; msgs.append(f"+{bm} Wave clear")
                        if msgs: self.ui.show_msg("  |  ".join(msgs),3.0)
                    # (per-wave profile coins handled by the wave-advance hook above)
                    self.wave_mgr._lmoney_paid=True; self.wave_mgr._bonus_paid=True
                    self.wave_mgr._lmoney_pay_pending=False; self.wave_mgr._lmoney_pending_wave=None
                    # MP: send wave bonuses to client (NOT farm — client counts own farms itself)
                    if getattr(self, 'is_host', False):
                        client_bonus = (lm or 0) + (bm or 0)
                        if client_bonus > 0:
                            self._broadcast({"type": "wave_bonus", "amount": client_bonus,
                                             "leaked": self._wave_leaked})
                        # Tell client to collect their own farm income
                        self._broadcast({"type": "farm_income"})
    
                fk_pending = (self.mode=="fallen" and self.wave_mgr.wave==40 and
                              (not self._fallen_king_spawned or
                               any(isinstance(e,FallenKing) and e.alive for e in self.enemies)))

                if self.wave_mgr.state=="done" and not any(e.alive for e in self.enemies) and not fk_pending:
                    if not self.win:
                        # ── Ensure all waves paid (covers state=done skipping the waiting block) ──
                        self._give_wave_coins(self.wave_mgr.wave)
                        # Flush leftover fractional accumulator (e.g. 0.5 from Fallen odd waves)
                        if self.mode in ("easy", "fallen", "frosty", "infernal") and self._wave_coin_accum >= 0.5:
                            self._end_coin_reward += 1
                            self.save_data["coins"] = self.save_data.get("coins", 0) + 1
                            self._wave_coin_accum = 0.0
                        write_save(self.save_data)
                        # ── Grant achievements on win ──
                        if self.mode == "fallen":
                            self.ach_mgr.try_grant("fallen_angel")
                            # fallen_duo: win Fallen with at most 2 units placed total
                            if getattr(self, "_max_units_placed", 0) <= 2:
                                self.ach_mgr.try_grant("fallen_duo")
                        elif self.mode == "frosty":
                            self.ach_mgr.try_grant("frosty_clear")
                            # Reward: unlock Frostcelerator
                            if not self.save_data.get("frostcelerator_unlocked"):
                                self.save_data["frostcelerator_unlocked"] = True
                                if "Frostcelerator" not in self.save_data.get("owned_units", []):
                                    self.save_data.setdefault("owned_units", []).append("Frostcelerator")
                                write_save(self.save_data)
                                self.ui.show_msg("❄ Frostcelerator Unlocked!", 5.0)
                            # Also unlock Spotlight Tech
                            if "Spotlight Tech" not in self.save_data.get("owned_units", []):
                                self.save_data.setdefault("owned_units", []).append("Spotlight Tech")
                                write_save(self.save_data)
                                self.ui.show_msg("🔦 Spotlight Tech Unlocked!", 5.0)
                        elif self.mode == "easy":
                            self.ach_mgr.try_grant("first_path")
                            if getattr(self, "_easy_boss_let_through", False):
                                self.ach_mgr.try_grant("free_pass")
                        elif self.mode == "infernal":
                            # Reward: unlock Rubber Duck
                            if "Rubber Duck" not in self.save_data.get("owned_units", []):
                                self.save_data.setdefault("owned_units", []).append("Rubber Duck")
                                write_save(self.save_data)
                                self.ui.show_msg("🐥 Rubber Duck unlocked!", 6.0)
                            # April Fools 2026 event achievement
                            if game_core.CURRENT_MAP == "event":
                                self.ach_mgr.try_grant("april_fools_2026")
                        # ── grand_slam: track Easy→Fallen→Frosty→Hardcore chain ──
                        if self.mode in ("easy", "fallen", "frosty", "hardcore"):
                            chain = self.save_data.get("_gs_chain", [])
                            chain.append(self.mode)
                            self.save_data["_gs_chain"] = chain[-4:]
                            write_save(self.save_data)
                            if self.save_data["_gs_chain"] == ["easy", "fallen", "frosty", "hardcore"]:
                                self.ach_mgr.try_grant("grand_slam")
                        # frosty perfect (no leaks)
                        if self.mode == "frosty" and not getattr(self, "_wave_ever_leaked", False):
                            self.ach_mgr.try_grant("frosty_perfect")
                        # last_stand: win with 1 HP
                        if self.player_hp == 1:
                            self.ach_mgr.try_grant("last_stand")
                        # No Refunds: beat Fallen without selling anything
                        if self.mode == "fallen" and not self._sold_this_run:
                            self.ach_mgr.try_grant("no_refunds")
                        # Speedrunner: beat Fallen with auto_skip always on
                        if self.mode == "fallen" and not self._auto_skip_ever_off:
                            self.ach_mgr.try_grant("speedrunner")
                        # ── Castbound quest: track mode runs ─────────────────
                        _cq = self.save_data.get("castbound_quest")
                        if self.mode == "easy" and _cq == "easy_runs":
                            _er = self.save_data.get("castbound_easy_runs", 0) + 1
                            self.save_data["castbound_easy_runs"] = _er
                            write_save(self.save_data)
                        elif self.mode == "fallen" and _cq == "fallen_runs":
                            _fr = self.save_data.get("castbound_fallen_runs", 0) + 1
                            self.save_data["castbound_fallen_runs"] = _fr
                            write_save(self.save_data)
                        elif self.mode == "frosty" and _cq == "frosty_run":
                            self.save_data["castbound_frosty_run"] = True
                            write_save(self.save_data)
                        # ── Daily quest tracking on WIN ───────────────────────
                        _dl_today, _dl_quests, _dl_prog, _dl_claimed = _load_daily_quests(self.save_data)
                        _dl_dq = self.save_data.setdefault("daily_quests", {})
                        _dl_pr = _dl_dq.setdefault("progress", {})
                        for _dlq in _dl_quests:
                            _dlqid = _dlq["id"]
                            if _dlqid in _dl_claimed:
                                continue
                            _dltype = _dlq.get("type")
                            _dltgt  = _dlq.get("target", 1)
                            _dlcur  = _dl_pr.get(_dlqid, 0)
                            if _dltype == "win_mode" and self.mode == _dlq.get("mode"):
                                _dl_pr[_dlqid] = min(_dlcur + 1, _dltgt)
                            elif _dltype == "kills":
                                _dl_pr[_dlqid] = min(_dlcur + getattr(self, "_total_kills", 0), _dltgt)
                            elif _dltype == "waves":
                                _dl_pr[_dlqid] = min(max(_dlcur, self.wave_mgr.wave), _dltgt)
                            elif _dltype == "earn_coins":
                                _dl_pr[_dlqid] = min(max(_dlcur, getattr(self, "_total_earned", 0)), _dltgt)
                            elif _dltype == "towers_placed":
                                _dl_pr[_dlqid] = min(max(_dlcur, getattr(self, "_towers_placed_count", 0)), _dltgt)
                            elif _dltype == "no_leak_win" and not getattr(self, "_wave_ever_leaked", False):
                                _dl_pr[_dlqid] = 1
                            elif _dltype == "waves_mode" and self.mode == _dlq.get("mode"):
                                _dl_pr[_dlqid] = min(max(_dlcur, self.wave_mgr.wave), _dltgt)
                        write_save(self.save_data)
                        # ── Profile stats: record win ────────────────────
                        _mode_key_w = self.mode if self.mode else "easy"
                        _pst_w = self.save_data.setdefault("profile_stats", {})
                        _pst_w["total_games"] = _pst_w.get("total_games", 0) + 1
                        _pst_w["total_wins"]  = _pst_w.get("total_wins", 0) + 1
                        _pst_w.setdefault("wins_by_mode", {})[_mode_key_w] = _pst_w.get("wins_by_mode", {}).get(_mode_key_w, 0) + 1
                        _pst_w["total_waves"] = _pst_w.get("total_waves", 0) + self.wave_mgr.wave
                        _pst_w["total_kills"] = _pst_w.get("total_kills", 0) + getattr(self, "_total_kills", 0)
                        _pst_w["total_earned"] = _pst_w.get("total_earned", 0) + getattr(self, "_total_earned", 0)
                        write_save(self.save_data)
                        self.win=True
                        try:
                            pygame.mixer.music.set_endevent(0)
                            pygame.mixer.music.stop()
                        except: pass
    
                # ── Achievement: Богач ─ > 5000 coins at once ──
                if not self.game_over and not self.win:
                    self.ach_mgr.try_grant("rich") if self.money > 5000 else None
                    # 100k coins
                    if self.save_data.get("coins", 0) >= 100000:
                        self.ach_mgr.try_grant("millionaire")
                    # Shard milestones
                    shards_now = self.save_data.get("shards", 0)
                    if shards_now >= 500:  self.ach_mgr.try_grant("shard_500")
                    if shards_now >= 1000: self.ach_mgr.try_grant("shard_1000")
                    # Collector achievements
                    owned_count = len(self.save_data.get("owned_units", []))
                    if owned_count >= 10: self.ach_mgr.try_grant("collector_10")
                    if owned_count >= 20: self.ach_mgr.try_grant("collector_20")


                # Track leaks for frosty_perfect
                if dead_reached:
                    self._wave_ever_leaked = True

                # Track peak units on field (for fallen_duo achievement)
                if len(self.units) > getattr(self, "_max_units_placed", 0):
                    self._max_units_placed = len(self.units)

                # ── Achievement: free_pass ─ GraveDigger (easy final boss) leaks with hp < player_hp ──
                if self.mode == "easy" and not self.game_over:
                    for e in dead_reached:
                        if isinstance(e, GraveDigger):
                            if e.hp < self.player_hp:
                                self._easy_boss_let_through = True
    
    
                # ────────────────────────────────────────────────────────────
                # ── Batch-2 per-frame achievement checks ─────────────────────
                # ────────────────────────────────────────────────────────────

                # ── Why: idle for 1 real hour (3600 s) ───────────────────────
                if not self._idle_achieved:
                    self._idle_timer += raw_dt
                    if self._idle_timer >= 3600.0:
                        self._idle_achieved = True
                        self.ach_mgr.try_grant("why")

                # ── Hacker: admin panel opened in sandbox ─────────────────────
                if self.mode == "sandbox" and getattr(self.ui, '_hacker_panel_opened', False):
                    self.ach_mgr.try_grant("hacker")

                # ── Speedrunner: track if auto_skip was ever disabled ─────────
                if not SETTINGS.get("auto_skip", False):
                    self._auto_skip_ever_off = True

                # ── Capitalist: 8 Farms all at max level (index 5) ───────────
                _farms = [u for u in self.units if isinstance(u, Farm)]
                if len(_farms) >= 8 and all(u.level >= len(FARM_LEVELS) - 1 for u in _farms):
                    self.ach_mgr.try_grant("capitalist")

                # ── Moonwalk: 15 enemies reversed simultaneously ──────────────
                _rev_count = sum(1 for e in self.enemies if e.alive and getattr(e, '_reversed', False))
                if _rev_count >= 15:
                    self.ach_mgr.try_grant("moonwalk")

                # ── Gold Rush: $10 000 earned exclusively from Cowboys ─────────
                # (tracked via cowboy income; non-cowboy kill rewards void the run)
                if self._cowboy_only_run and self._cowboy_income_total >= 10000:
                    self.ach_mgr.try_grant("gold_rush")

                # ── Overkill: Freeze + Burn + Armor Shred on one boss at once ─
                if not self._overkill_granted:
                    _BOSS_CLASSES = (NormalBoss, SlowBoss, HiddenBoss, FastBoss,
                                     OtchimusPrime, FallenKing)
                    for _e in self.enemies:
                        if not _e.alive: continue
                        if not isinstance(_e, _BOSS_CLASSES): continue
                        _has_freeze = (getattr(_e, '_frost_frozen', False)
                                       or getattr(_e, '_fb_freeze_timer', 0.0) > 0
                                       or getattr(_e, '_sledger_freeze_timer', 0.0) > 0)
                        _has_burn   = (getattr(_e, '_fire_timer', 0.0) > 0
                                       or getattr(_e, '_jester_burn_dur', 0.0) > 0)
                        _has_shred  = getattr(_e, '_fb_armor_shredded', False)
                        if _has_freeze and _has_burn and _has_shred:
                            self._overkill_granted = True
                            self.ach_mgr.try_grant("overkill")
                            break

                # ── Absolute Zero: boss frozen for 15 s straight ─────────────
                _BOSS_CLASSES_AZ = (NormalBoss, SlowBoss, HiddenBoss, FastBoss,
                                    OtchimusPrime, FallenKing)
                _live_boss_ids = set()
                for _e in self.enemies:
                    if not _e.alive: continue
                    if not isinstance(_e, _BOSS_CLASSES_AZ): continue
                    _eid = id(_e)
                    _live_boss_ids.add(_eid)
                    _is_frozen_now = (getattr(_e, '_frost_frozen', False)
                                      or getattr(_e, '_fb_freeze_timer', 0.0) > 0
                                      or getattr(_e, '_sledger_freeze_timer', 0.0) > 0)
                    if _is_frozen_now:
                        self._boss_freeze_timers[_eid] = self._boss_freeze_timers.get(_eid, 0.0) + dt
                        if self._boss_freeze_timers[_eid] >= 15.0:
                            self.ach_mgr.try_grant("absolute_zero")
                    else:
                        self._boss_freeze_timers[_eid] = 0.0
                # Clean up dead bosses from the dict
                for _eid in list(self._boss_freeze_timers):
                    if _eid not in _live_boss_ids:
                        del self._boss_freeze_timers[_eid]

                # ────────────────────────────────────────────────────────────
                self.ach_mgr.update(dt)
    
                self.effects=[ef for ef in self.effects if ef.update(dt)]
                self.ui.update(dt)
                if self._fallen_king_shake>0:
                    self._fallen_king_shake=max(0, self._fallen_king_shake-dt)
    
            if self.paused:
                self.draw()
                self.pause_menu.draw()
            else:
                self.draw()
            if self.game_over or self.win:
                self._draw_end_screen()
            if SETTINGS.get("show_fps", False):
                _fps_val = int(self.clock.get_fps())
                _fps_cap = 720 if SETTINGS.get("unlock_fps") else FPS
                _fps_col = (80,255,80) if _fps_val >= _fps_cap - 10 else ((255,200,40) if _fps_val>=30 else (255,60,60))
                _fps_s = pygame.font.SysFont("consolas", 18, bold=True).render(f"FPS: {_fps_val} / {_fps_cap}", True, _fps_col)
                self.screen.blit(_fps_s, (8, 8))
            # ── Free Robux screamer overlay ────────────────────────────────────
            if self._screamer_timer > 0:
                self._screamer_timer -= dt
                if self._screamer_timer <= 0:
                    # Timer just expired — stop sound
                    if self._screamer_snd:
                        try: self._screamer_snd.stop()
                        except Exception: pass
                if self._screamer_img:
                    self.screen.blit(self._screamer_img, (0, 0))
            self._mp_overlay_hook()   # multiplayer overlay injected here
            pygame.display.flip()
        # Reset skill tree globals so they dont bleed into menu
        game_core.DEBUFF_MULT = 1.0
        game_core.AOE_MULT    = 1.0

    def _mp_overlay_hook(self):
        """Called every frame just before pygame.display.flip().
        Overridden by MultiplayerGame subclass to draw peer cursor + leaderboard."""
        pass

    def draw(self):
        fk_shake=(0,0)
        if self._fallen_king_shake>0 and SETTINGS.get("screen_shake", True):
            intensity=min(20, self._fallen_king_shake*16)
            fk_shake=(random.randint(-int(intensity),int(intensity)),
                      random.randint(-int(intensity),int(intensity)))
        shake=fk_shake
        self.draw_map(offset=shake)
        can_detect=any(getattr(u,'hidden_detection',False) for u in self.units)
        mx,my=pygame.mouse.get_pos()

        # Draw poison puddles FIRST (under everything)
        for u in self.units:
            if hasattr(u, '_draw_puddles_only'):
                u._draw_puddles_only(self.screen)

        for u in self.units:
            if SETTINGS.get("no_tower_details", False):
                u.draw_simple(self.screen)
            else:
                u.draw(self.screen)
        # Draw peer (other player's) units in the same pass for correct layering
        for u in getattr(self, '_peer_units', []):
            try:
                if SETTINGS.get("no_tower_details", False):
                    u.draw_simple(self.screen)
                else:
                    u.draw(self.screen)
            except Exception: pass
        for e in self.enemies:
            if not e.alive: continue
            hov=dist((e.x,e.y),(mx,my))<e.radius+5
            if hov: continue
            e.draw(self.screen,detected=can_detect)
        # Draw fire effect on burning enemies (Archer flame + Jester fire bomb)
        _ft=pygame.time.get_ticks()*0.001
        _lq = SETTINGS.get("low_quality", False)
        _fire_surf = getattr(self, '_fire_surf_cache', None)
        if _fire_surf is None:
            self._fire_surf_cache = pygame.Surface((60,60),pygame.SRCALPHA)
            _fire_surf = self._fire_surf_cache
        _ice_surf = getattr(self, '_ice_surf_cache', None)
        if _ice_surf is None:
            self._ice_surf_cache = pygame.Surface((80,80),pygame.SRCALPHA)
            _ice_surf = self._ice_surf_cache
        _conf_surf = getattr(self, '_conf_surf_cache', None)
        if _conf_surf is None:
            self._conf_surf_cache = pygame.Surface((70,70),pygame.SRCALPHA)
            _conf_surf = self._conf_surf_cache
        for e in self.enemies:
            if not e.alive: continue
            has_archer_fire = getattr(e,'_fire_timer',0) > 0
            has_jester_fire = getattr(e,'_jester_burn_dur',0.0) > 0
            if not has_archer_fire and not has_jester_fire: continue
            cx,cy=int(e.x),int(e.y)
            if not _lq:
                _fire_surf.fill((0,0,0,0))
                for i in range(6):
                    a=math.radians(i*60+_ft*200)
                    flick=abs(math.sin(_ft*14+i*1.1))
                    fx=30+int(math.cos(a)*(e.radius-4+flick*4))
                    fy=30+int(math.sin(a)*(e.radius-4+flick*4))
                    r2=int(4+flick*4)
                    pygame.draw.circle(_fire_surf,(255,int(60+flick*100),0,200),(fx,fy),r2)
                    pygame.draw.circle(_fire_surf,(255,220,50,120),(fx,fy),r2-2)
                self.screen.blit(_fire_surf,(cx-30,cy-30))
            # Timer bar
            if has_jester_fire:
                frac=max(0,min(1,getattr(e,'_jester_burn_dur',0)/4.0))
            else:
                frac=max(0,min(1,e._fire_timer/3.0))
            bw=e.radius*2+4; bx2=cx-bw//2; by2=cy-e.radius-14
            pygame.draw.rect(self.screen,(60,20,0),(bx2,by2,bw,4),border_radius=2)
            pygame.draw.rect(self.screen,(255,100,0),(bx2,by2,int(bw*frac),4),border_radius=2)

        # Draw Jester ice bomb slow overlay
        _jt = pygame.time.get_ticks() * 0.001
        for e in self.enemies:
            if not e.alive: continue
            itimer = getattr(e, '_jester_ice_timer', 0.0)
            if itimer <= 0: continue
            cx2, cy2 = int(e.x), int(e.y)
            frac = max(0.0, min(1.0, itimer / 3.0))
            alpha = int(frac * 150) + 40
            if not _lq:
                _ice_surf.fill((0,0,0,0))
                pygame.draw.circle(_ice_surf, (100, 180, 255, alpha), (40, 40), e.radius + 7)
                pygame.draw.circle(_ice_surf, (200, 240, 255, alpha // 2), (40, 40), e.radius + 3, 2)
                # Spinning snowflake spokes
                spin = _jt * 60
                for i in range(6):
                    a = math.radians(spin + i * 60)
                    x1 = 40 + int(math.cos(a) * 4);  y1 = 40 + int(math.sin(a) * 4)
                    x2 = 40 + int(math.cos(a) * (e.radius + 6)); y2 = 40 + int(math.sin(a) * (e.radius + 6))
                    pygame.draw.line(_ice_surf, (180, 230, 255, min(255, alpha + 60)), (x1, y1), (x2, y2), 1)
                    mid_x = 40 + int(math.cos(a) * (e.radius // 2 + 3))
                    mid_y = 40 + int(math.sin(a) * (e.radius // 2 + 3))
                    pa2 = -math.sin(a); pb2 = math.cos(a)
                    pygame.draw.line(_ice_surf, (180, 230, 255, alpha),
                        (int(mid_x + pa2*4), int(mid_y + pb2*4)),
                        (int(mid_x - pa2*4), int(mid_y - pb2*4)), 1)
                self.screen.blit(_ice_surf, (cx2 - 40, cy2 - 40))
            # Timer bar
            bw = e.radius * 2 + 8; bx3 = cx2 - bw // 2; by3 = cy2 - e.radius - 14
            pygame.draw.rect(self.screen, (20, 60, 120), (bx3, by3, bw, 4), border_radius=2)
            pygame.draw.rect(self.screen, (100, 200, 255), (bx3, by3, int(bw * frac), 4), border_radius=2)

        # Draw Jester confusion overlay — purple aura + fast flickering ? marks
        _jqt = pygame.time.get_ticks() * 0.001
        _jqt_ms = pygame.time.get_ticks()
        _qf = pygame.font.SysFont("consolas", 15, bold=True)
        for e in self.enemies:
            if not e.alive: continue
            ctimer = getattr(e, '_jester_conf_timer', 0.0)
            if ctimer <= 0: continue
            cx2, cy2 = int(e.x), int(e.y)
            ca2 = int(min(1.0, ctimer / 2.0) * 160) + 40
            if not _lq:
                _conf_surf.fill((0,0,0,0))
                pygame.draw.circle(_conf_surf, (180, 40, 255, ca2), (35, 35), e.radius + 9)
                pygame.draw.circle(_conf_surf, (220, 100, 255, ca2 // 2), (35, 35), e.radius + 4, 2)
                self.screen.blit(_conf_surf, (cx2 - 35, cy2 - 35))
            # Fast flickering ? marks
            _qf2 = pygame.font.SysFont("consolas", 14, bold=True)
            for qi in range(6):
                phase_ms = (qi * 137 + id(e) // 100) % 1000
                blink_period = 80 + qi * 15
                if ((_jqt_ms + phase_ms) % blink_period) < (blink_period // 2):
                    continue
                _seed_val = (id(e) + qi * 31 + int(_jqt * 8)) % 1000
                random.seed(_seed_val)
                scatter_r = e.radius + random.randint(8, 20)
                scatter_a = math.radians(random.randint(0, 359))
                random.seed()
                qx = cx2 + int(math.cos(scatter_a) * scatter_r)
                qy = cy2 + int(math.sin(scatter_a) * scatter_r)
                q_col = random.choice([(230, 120, 255), (255, 80, 220), (200, 60, 255)])
                qs2 = _qf2.render("?", True, q_col)
                qs2.set_alpha(min(255, ca2 + 60))
                self.screen.blit(qs2, qs2.get_rect(center=(qx, qy)))
        # Draw frost effects from Frostcelerators
        for u in self.units:
            if isinstance(u, Frostcelerator):
                u.draw_enemy_frost(self.screen, self.enemies)

        # Draw Castbound burn/slow debuff effects
        for u in self.units:
            if isinstance(u, Castbound):
                u.draw_debuffs(self.screen, self.enemies)

        # Draw Terraprismas
        for u in self.units:
            if isinstance(u, Castbound):
                for tp in getattr(u, '_terraprismas', []):
                    tp.draw(self.screen)

        # Draw ice arrow slow overlay + timer bar
        _t_now = pygame.time.get_ticks() * 0.001
        for e in self.enemies:
            if not e.alive: continue
            if not getattr(e, '_ice_arrow_slowed', False): continue
            cx2, cy2 = int(e.x), int(e.y)
            timer = getattr(e, '_ice_arrow_timer', 0.0)
            frac  = max(0.0, min(1.0, timer / 0.5))
            # Icy circle overlay (like frost slow)
            ice_s = pygame.Surface((80, 80), pygame.SRCALPHA)
            alpha = int(frac * 140) + 40
            pygame.draw.circle(ice_s, (140, 210, 255, alpha), (40, 40), e.radius + 5)
            pygame.draw.circle(ice_s, (200, 240, 255, alpha // 2), (40, 40), e.radius + 2, 2)
            # Spinning ice crystal dots
            spin = _t_now * 180
            for i in range(6):
                a = math.radians(spin + i * 60)
                px2 = 40 + int(math.cos(a) * (e.radius + 6))
                py2 = 40 + int(math.sin(a) * (e.radius + 6))
                pygame.draw.circle(ice_s, (180, 230, 255, 200), (px2, py2), 2)
            self.screen.blit(ice_s, (cx2 - 40, cy2 - 40))
            # Timer bar above enemy
            bw = e.radius * 2 + 8
            bx3 = cx2 - bw // 2
            by3 = cy2 - e.radius - 14
            pygame.draw.rect(self.screen, (20, 60, 100), (bx3, by3, bw, 5), border_radius=2)
            pygame.draw.rect(self.screen, (100, 200, 255), (bx3, by3, int(bw * frac), 5), border_radius=2)

        # Draw Sledger chill/freeze overlays
        _sledge_t = pygame.time.get_ticks() * 0.001
        for e in self.enemies:
            if not e.alive: continue
            is_sledge_frozen = getattr(e, 'frozen', False) and getattr(e, '_sledger_freeze_timer', 0.0) > 0
            sledge_slow = getattr(e, '_sledger_slow', 0.0)
            if not is_sledge_frozen and sledge_slow <= 0: continue
            cx2, cy2 = int(e.x), int(e.y)
            if is_sledge_frozen:
                # Full freeze — bright solid overlay
                ice_s = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(ice_s, (160, 225, 255, 170), (40, 40), e.radius + 9)
                pygame.draw.circle(ice_s, (210, 245, 255, 90),  (40, 40), e.radius + 5, 3)
                # 6-spoke snowflake
                for i in range(6):
                    a = math.radians(i * 60)
                    x1 = 40 + int(math.cos(a) * 5);  y1 = 40 + int(math.sin(a) * 5)
                    x2 = 40 + int(math.cos(a) * (e.radius + 7)); y2 = 40 + int(math.sin(a) * (e.radius + 7))
                    pygame.draw.line(ice_s, (255, 255, 255, 130), (x1, y1), (x2, y2), 1)
                self.screen.blit(ice_s, (cx2 - 40, cy2 - 40))
                # Freeze timer bar
                ft = getattr(e, '_sledger_freeze_timer', 0.0)
                # find max freeze dur from any sledger
                max_fd = max((u._freeze_dur for u in self.units if isinstance(u, Sledger)), default=1.5)
                frac_f = max(0.0, min(1.0, ft / max_fd))
                bw = e.radius * 2 + 10; bx3 = cx2 - bw // 2; by3 = cy2 - e.radius - 16
                pygame.draw.rect(self.screen, (15, 50, 90),  (bx3, by3, bw, 5), border_radius=2)
                pygame.draw.rect(self.screen, (140, 220, 255), (bx3, by3, int(bw * frac_f), 5), border_radius=2)
            else:
                # Chilled (slowed) — translucent blue tint, intensity by slow amount
                frac_s = min(1.0, sledge_slow / 0.80)
                alpha  = int(frac_s * 110) + 25
                chill_s = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(chill_s, (80, 180, 255, alpha), (30, 30), e.radius + 4)
                self.screen.blit(chill_s, (cx2 - 30, cy2 - 30))
                # Spinning ice dots proportional to chill level
                spin2 = _sledge_t * 120
                n_dots = max(1, int(frac_s * 4))
                for i in range(n_dots):
                    a = math.radians(spin2 + i * (360 // n_dots))
                    px3 = cx2 + int(math.cos(a) * (e.radius + 5))
                    py3 = cy2 + int(math.sin(a) * (e.radius + 5))
                    pygame.draw.circle(self.screen, (140, 210, 255), (px3, py3), 2)

        # Draw Toxic Gunner poison overlay
        _tg_t = pygame.time.get_ticks() * 0.001
        for e in self.enemies:
            if not e.alive: continue
            pt = getattr(e, '_tg_poison_time', 0.0)
            sl = getattr(e, '_tg_slow', 0.0)
            if pt <= 0 and sl <= 0: continue
            cx2, cy2 = int(e.x), int(e.y)
            if pt > 0:
                # Purple-acid toxic aura (new design)
                ps = pygame.Surface((60, 60), pygame.SRCALPHA)
                ga2 = int(min(1.0, pt / 3.0) * 110) + 30
                pygame.draw.circle(ps, (110, 40, 200, ga2), (30, 30), e.radius + 5)  # purple glow
                pygame.draw.circle(ps, (180, 230, 0, ga2 // 2), (30, 30), e.radius + 2, 2)  # acid ring
                self.screen.blit(ps, (cx2 - 30, cy2 - 30))
                # Spinning acid dots
                for i in range(3):
                    a2 = math.radians(_tg_t * 140 + i * 120)
                    px4 = cx2 + int(math.cos(a2) * (e.radius + 7))
                    py4 = cy2 + int(math.sin(a2) * (e.radius + 7))
                    pygame.draw.circle(self.screen, (180, 230, 0), (px4, py4), 3)   # acid yellow
                    pygame.draw.circle(self.screen, (140, 80, 220), (px4, py4), 2)  # purple center

        # Draw Slasher bleed overlay
        for e in self.enemies:
            if not e.alive: continue
            stacks = getattr(e, '_slash_bleed', 0)
            if stacks <= 0: continue
            cx2, cy2 = int(e.x), int(e.y)
            frac_b = min(1.0, stacks / 30)
            bs = pygame.Surface((60, 60), pygame.SRCALPHA)
            ba2 = int(frac_b * 120) + 20
            pygame.draw.circle(bs, (180, 20, 20, ba2), (30, 30), e.radius + 4)
            self.screen.blit(bs, (cx2 - 30, cy2 - 30))
            # Drip dots
            for i in range(min(stacks, 5)):
                a2 = math.radians(_tg_t * -90 + i * 72)
                px4 = cx2 + int(math.cos(a2) * (e.radius + 6))
                py4 = cy2 + int(math.sin(a2) * (e.radius + 6))
                pygame.draw.circle(self.screen, (220, 40, 40), (px4, py4), 2)

        # Draw Spotlight Tech — Expose (yellow) and Confusion (purple) overlays
        _sp_t = pygame.time.get_ticks() * 0.001
        for e in self.enemies:
            if not e.alive: continue
            cx2, cy2 = int(e.x), int(e.y)
            # Expose overlay — yellow glow
            if getattr(e, '_exposed', False):
                es2 = pygame.Surface((60, 60), pygame.SRCALPHA)
                pulse2 = int(abs(math.sin(_sp_t * 5)) * 60 + 80)
                pygame.draw.circle(es2, (255, 240, 60, pulse2), (30, 30), e.radius + 6)
                pygame.draw.circle(es2, (255, 255, 120, 80), (30, 30), e.radius + 2, 2)
                self.screen.blit(es2, (cx2 - 30, cy2 - 30))
            # Confusion overlay — purple aura + fast flickering ? marks
            if getattr(e, '_confused', False):
                cs3 = pygame.Surface((70, 70), pygame.SRCALPHA)
                ct2 = getattr(e, '_confused_timer', 0.0)
                ca3 = int(min(1.0, ct2 / 0.5) * 160) + 40
                pygame.draw.circle(cs3, (180, 60, 255, ca3), (35, 35), e.radius + 8)
                self.screen.blit(cs3, (cx2 - 35, cy2 - 35))
                # Fast flickering ? marks
                _conf_ms = pygame.time.get_ticks()
                _conf_t = _conf_ms * 0.001
                qf2 = pygame.font.SysFont("consolas", 14, bold=True)
                for i in range(6):
                    phase_ms2 = (i * 113 + id(e) // 100) % 1000
                    blink_p2 = 75 + i * 18
                    if ((_conf_ms + phase_ms2) % blink_p2) < (blink_p2 // 2):
                        continue
                    _seed2 = (id(e) + i * 29 + int(_conf_t * 8)) % 1000
                    random.seed(_seed2)
                    sc_r = e.radius + random.randint(8, 20)
                    sc_a = math.radians(random.randint(0, 359))
                    random.seed()
                    qx = cx2 + int(math.cos(sc_a) * sc_r)
                    qy = cy2 + int(math.sin(sc_a) * sc_r)
                    q_c = random.choice([(220, 100, 255), (255, 60, 200), (190, 50, 255)])
                    qs2 = qf2.render("?", True, q_c)
                    qs2.set_alpha(ca3)
                    self.screen.blit(qs2, qs2.get_rect(center=(qx, qy)))



        if SETTINGS.get("particles", True) and not SETTINGS.get("low_quality", False):
            for ef in self.effects: ef.draw(self.screen)
        else:
            # When particles off or low_quality, still draw FloatingText (money/damage numbers), skip visual effects
            for ef in self.effects:
                if isinstance(ef, FloatingText): ef.draw(self.screen)

        extra_bars=None

        # Build fallen boss bars list
        fallen_bars=None
        fallen_bars=[]
        _bar_cfg={
                FallenGiant:       ("FALLEN GIANT",        (160,80,220)),
                FallenJester:      ("FALLEN JESTER",       (200,60,220)),
                FallenSquire:      ("FALLEN SQUIRE",       (140,70,200)),
                FallenShield:      ("FALLEN SHIELD",       (80,160,220)),
                FallenHonorGuard:  ("FALLEN HONOR GUARD",  (220,180,60)),
                FallenKing:        ("FALLEN KING",         (200,100,255)),
                # Frosty bosses
                SnowMinion:        ("SNOW MINION",         (100,200,255)),
                FrostHunter:       ("FROST HUNTER",        (60,160,240)),
                FrostAcolyte:      ("FROST ACOLYTE",       (120,190,255)),
                FrostUndead:       ("FROST UNDEAD",        (90,200,255)),
                FrostInvader:      ("FROST INVADER",       (70,170,255)),
                FrostRavager:      ("FROST RAVAGER",       (80,200,255)),
                Yeti:             ("YETI",                (220,248,255)),
                FrostMage:         ("FROST MAGE",          (140,220,255)),
                FrostHero:         ("FROST HERO",          (160,230,255)),
                FrostSpirit:       ("FROST SPIRIT",        (220,248,255)),
            }
        # ── Infernal boss bars ─────────────────────────────────────────────
        if _INFERNAL_AVAILABLE and self.mode == "infernal":
            _bar_cfg.update({
                Furnace:        ("FURNACE",           (255, 140, 20)),
                Terpila:        ("PATIENT",         (180,  60, 220)),
                Putana:         ("PUTANA",          (255, 120, 180)),
                Silyach:        ("CIGARETTE",        (200, 200, 160)),
                Confusilionale: ("CONFUSIONALE",    ( 80, 220, 160)),
                Wheelchair:     ("INVALID",         (100, 160, 240)),
                Kolobok:        ("KOLOBOK",         (255, 210,  40)),
            })
            for _inf_cls, (_inf_lbl, _inf_col) in list(_bar_cfg.items()):
                if _inf_cls not in (Furnace, Terpila, Putana, Silyach,
                                    Confusilionale, Wheelchair, Kolobok): continue
                _inf_e = next((e for e in self.enemies
                               if isinstance(e, _inf_cls) and e.alive), None)
                if _inf_e:
                    self._fallen_boss_bars[_inf_cls] = _inf_e
        for cls,(label,col) in _bar_cfg.items():
            e=self._fallen_boss_bars.get(cls)
            if e and e.alive:
                fallen_bars.append((label,e.hp,e.maxhp,col))
        if not fallen_bars: fallen_bars=None

        # Set _game_ref BEFORE ui.draw so admin button works on first frame
        if self.admin_mode:
            self.ui._game_ref = self

        # Sync skill bonus to UI for upgrade menu range display
        self.ui._sk_range_bonus = getattr(self, '_sk_range_bonus', 0)

        self.ui.draw(self.screen,self.units,self.money,self.wave_mgr,
                     self.player_hp,self.player_maxhp,self.enemies,
                     self._boss_enemy,
                     extra_bars,fallen_bars,self.mode)



        # Admin panel overlay
        if self.admin_mode:
            self.ui.admin_panel.draw(self.screen,self.units,pygame.time.get_ticks()*0.001,game_ref=self,ui_ref=self.ui)
        self.console.draw(self.screen)

        # Ceremony flash overlay (original fallen mode)
        if self._ceremony_flash_alpha>0:
            col=getattr(self,'_ceremony_flash_color',(255,255,255))
            fl=pygame.Surface((SCREEN_W,SCREEN_H))
            fl.fill(col); fl.set_alpha(self._ceremony_flash_alpha)
            self.screen.blit(fl,(0,0))

        # Draw stun indicator on stunned units
        for u in self.units:
            st=getattr(u,'_stun_timer',0)
            if st>0:
                cx,cy=int(u.px),int(u.py)
                s2=pygame.Surface((40,40),pygame.SRCALPHA)
                pygame.draw.circle(s2,(255,220,50,160),(20,20),16)
                self.screen.blit(s2,(cx-20,cy-20))
                txt(self.screen,f"{st:.1f}",(cx,cy-28),(255,220,50),font_sm,center=True)

        if self.game_over or self.win:
            self._draw_end_screen()

        if getattr(self, 'draft_active', False):
            # Dim background
            draw_rect_alpha(self.screen, C_BLACK, (0,0,SCREEN_W,SCREEN_H), 180)
            
            title_font=pygame.font.SysFont("consolas",60,bold=True)
            ts = title_font.render("CHOOSE YOUR CURSE", True, (255, 80, 80))
            self.screen.blit(ts, ts.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 280)))

            card_w, card_h = 300, 400
            gap = 60
            total_w = 2 * card_w + gap
            start_x = SCREEN_W // 2 - total_w // 2
            start_y = SCREEN_H // 2 - card_h // 2
            
            title_f = pygame.font.SysFont("segoeui", 26, bold=True)
            desc_f = pygame.font.SysFont("segoeui", 18)
            
            mx, my = pygame.mouse.get_pos()
            for i, c in enumerate(self.draft_cards):
                r = pygame.Rect(start_x + i * (card_w + gap), start_y, card_w, card_h)
                hov = r.collidepoint((mx, my))
                
                bg_col = (40, 20, 25) if hov else (25, 15, 20)
                brd_col = (255, 100, 100) if hov else (150, 40, 40)
                
                draw_rect_alpha(self.screen, bg_col, r, 240, 16)
                pygame.draw.rect(self.screen, brd_col, r, 3, border_radius=16)
                
                # Title
                ts = title_f.render(c["title"], True, (255, 150, 150))
                self.screen.blit(ts, ts.get_rect(centerx=r.centerx, top=r.top + 30))
                
                # Description
                import textwrap
                words = textwrap.wrap(c["desc"], width=24)
                for line_idx, line in enumerate(words):
                    ls = desc_f.render(line, True, (200, 200, 200))
                    self.screen.blit(ls, ls.get_rect(centerx=r.centerx, top=r.top + 100 + line_idx * 28))


        # Achievement toasts — always drawn on top
        self.ach_mgr.draw(self.screen)

    def _draw_end_screen(self):
        surf=self.screen
        is_win=self.win
        # Dim background
        draw_rect_alpha(surf,C_BLACK,(0,0,SCREEN_W,SCREEN_H),180)

        # === TITLE BANNER (full width, same as before) ===
        banner_h=72
        banner_col=(30,180,60) if is_win else (180,30,30)
        pygame.draw.rect(surf,banner_col,(0,SCREEN_H//2-280,SCREEN_W,banner_h))
        title_font=pygame.font.SysFont("consolas",80,bold=True)
        title_text="TRIUMPH!" if is_win else "DEFEAT!"
        title_col=(255,230,50) if is_win else (255,100,100)
        ts=title_font.render(title_text,True,title_col)
        gs=pygame.Surface((ts.get_width()+60,ts.get_height()+14),pygame.SRCALPHA)
        glow_c=(80,255,80,40) if is_win else (255,80,80,40)
        gs.fill(glow_c)
        surf.blit(gs,(SCREEN_W//2-gs.get_width()//2,SCREEN_H//2-280+(banner_h-ts.get_height())//2-5))
        surf.blit(ts,ts.get_rect(center=(SCREEN_W//2,SCREEN_H//2-280+banner_h//2)))

        # === PANELS — centered together ===
        gap=20
        cp_w,cp_h=220,280
        panel_w,panel_h=480,280
        total_panels_w=cp_w+gap+panel_w
        start_x=SCREEN_W//2-total_panels_w//2
        panel_y=SCREEN_H//2-190

        # Coins panel (left)
        cp_x=start_x
        cp_y=panel_y
        draw_rect_alpha(surf,(10,12,22),(cp_x,cp_y,cp_w,cp_h),230,14)
        pygame.draw.rect(surf,(50,55,80),(cp_x,cp_y,cp_w,cp_h),2,border_radius=14)
        ico_m=load_icon("coin_ico",64)
        if ico_m:
            surf.blit(ico_m,(cp_x+cp_w//2-32,cp_y+22))
        reward=self._end_coin_reward  # coins earned during this run (per wave)
        total_coins=self.save_data.get("coins",0)
        cf=pygame.font.SysFont("segoeui",28,bold=True)
        cs=cf.render(f"{total_coins} Coins",True,C_GOLD)
        surf.blit(cs,cs.get_rect(center=(cp_x+cp_w//2,cp_y+cp_h-52)))
        if reward>0:
            rs2=pygame.font.SysFont("segoeui",22).render(f"+{reward} earned",True,(100,220,100))
            surf.blit(rs2,rs2.get_rect(center=(cp_x+cp_w//2,cp_y+cp_h-22)))

        # Stats panel (right)
        panel_x=start_x+cp_w+gap
        draw_rect_alpha(surf,(10,12,22),(panel_x,panel_y,panel_w,panel_h),230,14)
        pygame.draw.rect(surf,(50,55,80),(panel_x,panel_y,panel_w,panel_h),2,border_radius=14)

        elapsed=int(self._elapsed)
        mins=elapsed//60; secs=elapsed%60
        # True Fallen comment removed
        mode_label={"easy":"Easy","fallen":"Fallen","sandbox":"Sandbox","frosty":"Frosty"}.get(self.mode,self.mode.title())
        rows=[
            ("Time:", f"{mins}m {secs:02d}s"),
            ("Wave:",           str(self.wave_mgr.wave)),
            ("Difficulty:",     mode_label),
        ]
        row_font=pygame.font.SysFont("segoeui",30)
        val_font=pygame.font.SysFont("segoeui",30,bold=True)
        ry=panel_y+36
        for label,value in rows:
            ls=row_font.render(label,True,(180,180,200))
            vs=val_font.render(value,True,C_WHITE)
            surf.blit(ls,(panel_x+28,ry))
            surf.blit(vs,(panel_x+panel_w-28-vs.get_width(),ry))
            ry+=70

        # === RETURN TO LOBBY BUTTON ===
        btn=self._end_btn
        mx,my=pygame.mouse.get_pos()
        hov=btn.collidepoint(mx,my)
        bg=(60,100,60) if (hov and is_win) else ((100,60,60) if hov else (35,45,65))
        brd=(100,220,100) if is_win else (220,80,80)
        pygame.draw.rect(surf,bg,btn,border_radius=14)
        pygame.draw.rect(surf,brd,btn,2,border_radius=14)
        bf=pygame.font.SysFont("segoeui",34,bold=True)
        bs=bf.render("Return To Lobby",True,C_WHITE)
        surf.blit(bs,bs.get_rect(center=btn.center))

# ── Multiplayer — вынесено в assets/multiplayer.py ───────────────────────────
# Импортируется лениво при нажатии кнопки MULTIPLAYER, чтобы не тормозить старт
def _run_multiplayer(screen, save_data):
    import importlib.util, sys, os
    try:
        _mp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "assets", "multiplayer.py")
        spec = importlib.util.spec_from_file_location("multiplayer", _mp_path)
        _mp  = importlib.util.module_from_spec(spec)
        sys.modules["multiplayer"] = _mp
        spec.loader.exec_module(_mp)
        # ── Inject profile nick into multiplayer module ───────────────────────
        _profile_nick = save_data.get("player_nick", "Player") or "Player"
        # Patch common name attributes the multiplayer module may expose
        for _attr in ("DEFAULT_NAME", "default_name", "player_name",
                      "MY_NAME", "my_name", "local_name", "nickname"):
            if hasattr(_mp, _attr):
                setattr(_mp, _attr, _profile_nick)
        # Also store in save_data so multiplayer can read it
        save_data.setdefault("player_nick", _profile_nick)
        return _mp.run_multiplayer(screen, save_data)
    except Exception as e:
        screen.fill((18,22,30))
        ef = pygame.font.SysFont("segoeui", 28).render(
            f"Failed to load assets/multiplayer.py: {e}", True, (255,80,80))
        screen.blit(ef, ef.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
        pygame.display.flip()
        import time; time.sleep(3)
        return save_data

# ── (old override removed — new MainMenu above handles everything) ────────────

    def _removed_run(self):
        clock = pygame.time.Clock()
        self.action = None
        while self.action is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pos = ev.pos
                    if self.t < 0.8: continue
                    if self.btn_play.collidepoint(pos):
                        diff = DifficultyMenu(self.screen, self.save_data).run()
                        if diff != "back":
                            if diff == "play_frosty":
                                if True:
                                    game_core.CURRENT_MAP = "frosty"
                                    self.action = diff

                            elif diff == "play_sandbox":
                                game_core.CURRENT_MAP = "straight"
                                self.action = diff
                            else:
                                map_choice = MapSelectMenu(self.screen).run()
                                if map_choice != "back":
                                    game_core.CURRENT_MAP = map_choice
                                    self.action = diff
                    if self.btn_loadout.collidepoint(pos):      self.action = "loadout"
                    if self.btn_shop.collidepoint(pos):         self.action = "shop"
                    if self.btn_skilltree.collidepoint(pos):    self.action = "skilltree"
                    if self.btn_achievements.collidepoint(pos): self.action = "achievements"
                    if self.btn_settings.collidepoint(pos):     self.action = "settings"
                    if self.btn_quit.collidepoint(pos):         self.action = "quit"
                    if self.btn_multiplayer.collidepoint(pos):  self.action = "multiplayer"
                    if self.btn_hardcore.collidepoint(pos):
                        map_choice = MapSelectMenu(self.screen).run()
                        if map_choice != "back":
                            game_core.CURRENT_MAP = map_choice
                            self.action = "play_hardcore"
            self._draw()
            pygame.display.flip()
        return self.action


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("START")
    # Apply saved display settings (fullscreen/windowed + resolution) on startup
    screen = _apply_display_mode()
    pygame.display.set_caption("Tower Defense")
    save_data = load_save()
    print("save_data loaded:", list(save_data.keys()))
    _first_open = True

    while True:
        print("Creating MainMenu...")
        menu = MainMenu(screen, save_data, first_open=_first_open)
        _first_open = False
        print("Running MainMenu...")
        action = menu.run()
        print("action:", action)

        if action == "quit":
            pygame.quit(); sys.exit()

        elif action == "multiplayer":
            save_data = _run_multiplayer(screen, save_data)

        elif action == "achievements":
            AchievementsScreen(screen).run()

        elif action == "quests":
            qs_result = QuestsScreen(screen, save_data).run()
            save_data = load_save()
            if qs_result == "castbound":
                action = "castbound"
                continue  # re-enter loop to handle castbound

        elif action == "shop":
            ShopScreen(screen, save_data).run()
            save_data = load_save()

        elif action == "skilltree":
            import importlib.util as _ilu2, os as _os2
            if "skill_tree" not in _sys.modules:
                _st_path = _os2.path.join(_os2.path.dirname(_os2.path.abspath(__file__)),
                                          "assets", "skill_tree.py")
                _spec2 = _ilu2.spec_from_file_location("skill_tree", _st_path)
                _st_mod = _ilu2.module_from_spec(_spec2)
                _sys.modules["skill_tree"] = _st_mod
                _spec2.loader.exec_module(_st_mod)
            else:
                _st_mod = _sys.modules["skill_tree"]
            _st_mod.SkillTreeScreen(screen, save_data).run()
            save_data = load_save()

        elif action == "profile":
            ProfileScreen(screen, save_data).run()
            save_data = load_save()

        elif action == "settings":
            SettingsScreen(screen, save_data).run()
            save_data = load_save()

        elif action == "castbound":
            cb_result = CastboundDialog(screen, save_data).run()
            save_data = load_save()
            if cb_result == "moon_lord_fight":
                # Launch Moon Lord fight immediately after dialog closes
                try:
                    _ml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "moon_lord_fight.py")
                    import importlib.util as _ml_ilu
                    _ml_spec = _ml_ilu.spec_from_file_location("moon_lord_fight", _ml_path)
                    _ml_mod = _ml_ilu.module_from_spec(_ml_spec)
                    _ml_spec.loader.exec_module(_ml_mod)
                    _ml_mod.run_moon_lord_fight(screen, save_data)
                    save_data = load_save()
                    # Grant Zenith unlock if Moon Lord was defeated
                    if save_data.get("moon_lord_defeated"):
                        save_data["castbound_zenith_unlocked"] = True
                        save_data["castbound_quest"] = "done"  # переводим квест в done
                        # Разблокируем Castbound как юнит (если ещё не разблокирован)
                        _owned = save_data.get("owned_units", [])
                        if "Castbound" not in _owned:
                            _owned = list(_owned) + ["Castbound"]
                            save_data["owned_units"] = _owned
                        from game_core import write_save as _ws
                        _ws(save_data)
                except Exception as _ml_e:
                    import traceback; traceback.print_exc()
                    input("Moon Lord fight error — press Enter to continue...")

        elif action == "loadout":
            ls = LoadoutScreen(screen, save_data)
            ls.run()
            save_data = load_save()

        elif action in ("play_easy", "play_sandbox", "play_fallen", "play_frosty", "play_infernal", "play_hardcore", "play_draft"):
            if action == "play_sandbox": mode = "sandbox"
            elif action == "play_fallen": mode = "fallen"
            elif action == "play_frosty": mode = "frosty"
            elif action == "play_infernal": mode = "infernal"
            elif action == "play_hardcore": mode = "hardcore"
            elif action == "play_draft": mode = "draft"
            else: mode = "easy"
            print("Starting game mode:", mode)
            try:
                game = Game(save_data, mode=mode)
                print("Game created, running...")
                game.run()
                print("Game ended, return_to_menu:", game.return_to_menu)
                # Handle restart from sandbox admin panel
                while getattr(game, '_restart_mode', None):
                    restart = game._restart_mode
                    game._restart_mode = None
                    save_data = load_save()
                    game = Game(save_data, mode=restart, admin_mode=True)
                    game.run()
            except Exception as e:
                import traceback; traceback.print_exc()
                input("Press Enter to continue...")
            save_data = load_save()