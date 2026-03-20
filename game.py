import pygame
import math
import random
import sys
import json
import os

pygame.init()




# Map/path constants live in assets/game_core.py — add assets/ to path first
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
    get_map_path, get_frosty_path, spawn_enemy_at_start,
    font_sm, font_md, font_lg, font_xl, font_ru, font_ru_lg,
    SAVE_FILE, load_icon, RARITY_DATA, UNIT_LIMITS,
    load_save, write_save, dist, txt, draw_rect_alpha,
    SwordEffect, WhirlwindEffect, FloatingText, BloodSlashEffect,
    ACHIEVEMENTS_FILE, ACHIEVEMENT_DEFS, load_achievements, grant_achievement,
)




# fonts imported from game_core


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
    FallenDreg, FallenSquire, FallenSoul, FallenEnemy, FallenGiant, FallenHazmat,
    PossessedArmorInner, PossessedArmor, FallenNecromancer, CorruptedFallen,
    FallenJester, NecroticSkeleton, FallenBreaker, FallenRusher, FallenHonorGuard,
    FallenShield, FallenHero, FallenKing,
    TrueFallenKing,
    WAVE_DATA, FALLEN_WAVE_DATA, FALLEN_MAX_WAVES,
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
from units import (
    WhirlwindAbility, Unit, TARGET_MODES,
    Assassin, ASSASSIN_LEVELS,
    Accelerator, ACCEL_LEVELS,
    Frostcelerator, FROST_LEVELS,
    Hixw5ytAbility, Pokaxw5ytAbility, ChiterAbility, Xw5ytUnit, XW5YT_LEVELS,
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
    C_TOXICGUN, C_TOXICGUN_DARK,
    Slasher, SLASHER_LEVELS,
    C_SLASHER, C_SLASHER_DARK,
    GoldenCowboy, GCOWBOY_LEVELS,
    C_GCOWBOY, C_GCOWBOY_DARK,
    HallowPunk, HallowPunkRocket, HALLOWPUNK_LEVELS,
    C_HALLOWPUNK, C_HALLOWPUNK_DARK,
    SpotlightTech, SPOTLIGHTTECH_LEVELS,
    C_SPOTLIGHT, C_SPOTLIGHT_DARK,
    C_FREEZER, C_FREEZER_DARK,
    Commander, COMMANDER_LEVELS, COMMANDER_LEVEL_NAMES,
    C_COMMANDER, C_COMMANDER_DARK,
    Snowballer, SNOWBALLER_LEVELS,
    SnowballerOld, SNOWBALLER_OLD_LEVELS,
    SNOWBALLER_LEVEL_NAMES,
    C_SNOWBALLER, C_SNOWBALLER_DARK,
    Commando, COMMANDO_LEVELS,
    C_COMMANDO, C_COMMANDO_DARK,
    SPAWN_MAP, CONSOLE_HELP,
    C_LIFESTEALER, C_LIFESTEALER_DARK,
    C_FROST, C_FROST_DARK, C_FROST_ICE,
    C_XW5YT, C_ARCHER, C_ARCHER_DARK,
    C_FARM, C_FARM_DARK, C_REDBALL, C_REDBALL_DARK,
    draw_xw5yt_icon,
)

class DevConsole:
    def __init__(self): self.visible=False; self.input_text=""; self.output_lines=[]; self.cursor_blink=0.0
    def toggle(self): self.visible=not self.visible
    def update(self, dt): self.cursor_blink=(self.cursor_blink+dt)%1.0
    def handle_key(self, ev, game):
        if not self.visible: return
        if ev.key==pygame.K_RETURN:
            self._execute(self.input_text.strip(),game); self.input_text=""
        elif ev.key==pygame.K_BACKSPACE: self.input_text=self.input_text[:-1]
        elif ev.key==pygame.K_ESCAPE: self.visible=False
        else:
            if ev.unicode and len(self.input_text)<60: self.input_text+=ev.unicode
    def _execute(self, cmd, game):
        self.output_lines.append(f"> {cmd}"); parts=cmd.split()
        if not parts: return
        c=parts[0].lower()
        if c=="help": self.output_lines+=CONSOLE_HELP
        elif c=="cash":
            if len(parts)>=2:
                try: n=int(parts[1]); game.money+=n; self.output_lines.append(f"  gave {n} money")
                except: self.output_lines.append("  invalid amount")
            else: self.output_lines.append("  usage: cash <N>")
        elif c=="hp":
            if len(parts)>=2:
                try:
                    n=int(parts[1]); game.player_hp=max(1,n); game.player_maxhp=max(game.player_maxhp,n)
                    self.output_lines.append(f"  hp set to {n}")
                except: self.output_lines.append("  invalid amount")
            else: self.output_lines.append("  usage: hp <N>")
        elif c=="skip":
            wm=game.wave_mgr
            if wm.state in ("prep","between"): wm.prep_timer=0.0
            elif wm.state=="spawning": wm.spawn_queue=[]; wm.state="waiting"
            elif wm.state=="waiting" and len(game.enemies)==0: wm.state="between"; wm.prep_timer=0.1
            self.output_lines.append("  skipped")
        elif c=="spawn_enemy":
            if len(parts)<2:
                self.output_lines.append("  usage: spawn_enemy <type>  |  spawn_enemy help")
            elif parts[1].lower()=="help":
                self.output_lines.append("  === Enemy types ===")
                for key,fn in SPAWN_MAP.items():
                    e_tmp=fn(1)
                    self.output_lines.append(f"  {key:<14} HP:{e_tmp.hp}  spd:{int(e_tmp.speed)}")
            else:
                key=parts[1].lower()
                if key not in SPAWN_MAP:
                    self.output_lines.append(f"  unknown type: {key}")
                    self.output_lines.append("  use: spawn_enemy help  to list all")
                else:
                    w=max(1,game.wave_mgr.wave)
                    count=1
                    if len(parts)>=3:
                        try: count=max(1,min(int(parts[2]),50))
                        except: self.output_lines.append("  invalid count, spawning 1")
                    for i in range(count):
                        e=SPAWN_MAP[key](w)
                        spawn_enemy_at_start(e, offset_x=-i*40); game.enemies.append(e)
                    self.output_lines.append(f"  spawned {count}x {key}  (HP:{e.hp})")
        elif c=="upgrade_all":
            total=0
            for u in game.units:
                while True:
                    cost=u.upgrade_cost()
                    if cost is None: break
                    if game.money<cost: break
                    if isinstance(u,Accelerator): u.upgrade()
                    else: u.upgrade()
                    game.money-=cost; total+=1
            self.output_lines.append(f"  upgraded {total} times across all units")
        elif c=="snep":
            game.natural_spawn_stopped = not getattr(game,'natural_spawn_stopped',False)
            state = "STOPPED" if game.natural_spawn_stopped else "RESUMED"
            self.output_lines.append(f"  natural enemy spawn: {state}")
        elif c=="test":
            game.natural_spawn_stopped = True
            game.player_hp = 10000; game.player_maxhp = 10000
            game.money += 9999999999
            self.output_lines.append("  test: snep ON, hp 10000, +9999999999 cash")
        elif c=="fk_test":
            # Simulate fallen mode wave 40: music → shake → FallenKing
            game.mode = "fallen"
            game.natural_spawn_stopped = True
            game._fallen_king_spawned = False
            game._fallen_king_music_timer = None
            game._fallen_king_shake = 0.0
            game.natural_spawn_stopped = False
            # Force wave manager to wave 40 state so the trigger fires
            game.wave_mgr.wave = 40
            game.wave_mgr.state = "waiting"
            self.output_lines.append("  fk_test: wave 40 queued — music starts now")
        elif c=="5":
            game._x5000_dmg = not getattr(game,"_x5000_dmg",False)
            state = "ON" if game._x5000_dmg else "OFF"
            self.output_lines.append(f"  x5000 damage: {state}")
        else: self.output_lines.append(f"  unknown: {c}")
        if len(self.output_lines)>18: self.output_lines=self.output_lines[-18:]
    def draw(self, surf):
        if not self.visible: return
        bx,by,bw,bh=100,80,900,440
        draw_rect_alpha(surf,C_BLACK,(bx,by,bw,bh),210,8)
        pygame.draw.rect(surf,C_CYAN,(bx,by,bw,bh),2,border_radius=8)
        txt(surf,"DEVELOPER CONSOLE  (F1 to close)",(bx+12,by+8),(100,200,255),font_sm)
        pygame.draw.line(surf,C_BORDER,(bx+8,by+28),(bx+bw-8,by+28),1)
        for i,line in enumerate(self.output_lines):
            col=(180,255,180) if line.startswith(">") else (200,200,200)
            txt(surf,line,(bx+12,by+34+i*19),col,font_sm)
        iy=by+bh-28
        pygame.draw.line(surf,C_BORDER,(bx+8,iy-4),(bx+bw-8,iy-4),1)
        cursor="|" if self.cursor_blink<0.5 else " "
        txt(surf,f"$ {self.input_text}{cursor}",(bx+12,iy),(180,255,180),font_sm)

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
    ("Necromancer", Necromancer,      (40,80,160),   80,    55),
    ("GraveDigger", GraveDigger,      (20,60,20),    300,   55),
    ("Fast Boss",   FastBoss,         (200,80,0),    500,   200),
    ("Optimus Prime",OtchimusPrime,    (80,10,10),    40000, 15),
    ("Abnormal",    AbnormalEnemy,    (180,60,60),   11,    55),
    ("Quick",       QuickEnemy,       (60,180,140),  12,    140),
    ("Skeleton",    SkeletonEnemy,    (200,200,190), 55,    55),
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
    ("F.Rusher",    FallenRusher,     (160,30,100),  350,   140),
    ("Poss.Armor",  PossessedArmor,   (80,80,110),   300,   55),
    ("F.HGuard",    FallenHonorGuard, (160,120,20),  75000, 22),
    ("F.Shield",    FallenShield,     (60,100,160),  8000,  55),
    ("F.Hero",      FallenHero,       (120,60,160),  2500,  55),
    ("F.King",      FallenKing,       (120,40,160),  150000,8),
    # Frosty extras
    ("Frost Undead", FrostUndead,     (60,170,230),  3250,  140),
    ("Frost Invader",FrostInvader,    (40,120,200),  4000,  55),
    ("Mega F.Myst.", MegaFrostMystery,(30,130,200),   600,  140),
    ("Frost Ravager",FrostRavager,    (20,80,170),  25000,  28),
    ("Trickster Elf",TricksterElf,    (20,70,60),    2500,  28),
    ("Yeti",         Yeti,            (80,150,220), 12000,  140),
    ("Frost Mage",   FrostMage,       (20,80,170),  12500,  55),
    ("Frost Hero",   FrostHero,       (20,90,180),  40000,  28),
    ("Deep Freeze",  DeepFreeze,      (10,70,160),  12000,  55),
    ("F.Necromancer",FrostNecromancer,(20,70,160),  30000,  28),
    ("Frost Spirit", FrostSpirit,     (20,90,180),  500000, 26),
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
        self._hp_input=""        # text field value
        self._hp_input_active=False  # is text field focused
        self._hp_input_rect=pygame.Rect(0,0,0,0)

    def toggle(self): self.visible=not self.visible; self.scroll=0; self._hp_input_active=False

    def handle_scroll(self, dy): self.scroll=max(0,self.scroll-dy*25)

    def handle_key(self, ev, game_ref):
        """Handle keyboard input for HP text field."""
        if not self._hp_input_active or not game_ref: return
        if ev.key==pygame.K_RETURN:
            try:
                val=int(self._hp_input)
                if val>0:
                    game_ref.player_hp=val
                    game_ref.player_maxhp=max(game_ref.player_maxhp,val)
            except: pass
            self._hp_input_active=False
        elif ev.key==pygame.K_BACKSPACE:
            self._hp_input=self._hp_input[:-1]
        elif ev.key==pygame.K_ESCAPE:
            self._hp_input_active=False
        else:
            if ev.unicode.isdigit() and len(self._hp_input)<7:
                self._hp_input+=ev.unicode

    def handle_click(self,pos,game_units,game_enemies,wave,save_data,ui_ref=None,game_ref=None):
        if not self.visible: return
        if self._close_btn.collidepoint(pos): self.visible=False; self._hp_input_active=False; return
        for key,tr in self._tab_rects.items():
            if tr.collidepoint(pos): self.tab=key; self.scroll=0; self._hp_input_active=False; return

        if self.tab=="misc" and game_ref:
            # HP input field click
            if self._hp_input_rect.collidepoint(pos):
                self._hp_input_active=True
                self._hp_input=""
                return
            else:
                self._hp_input_active=False

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
        pw,ph=660,520
        px,py=SCREEN_W//2-pw//2, 58
        draw_rect_alpha(surf,(12,15,25),(px,py,pw,ph),245,12)
        pygame.draw.rect(surf,C_BORDER,(px,py,pw,ph),2,border_radius=12)

        self._close_btn=pygame.Rect(px+pw-38,py+6,28,28)
        pygame.draw.rect(surf,(60,30,30),self._close_btn,border_radius=6)
        pygame.draw.rect(surf,(180,60,60),self._close_btn,1,border_radius=6)
        txt(surf,"✕",self._close_btn.center,(220,100,100),font_md,center=True)

        # Tabs
        self._tab_rects={}
        tabs=[("enemy","ENEMIES",(40,80,160)),("units","UNITS",(60,120,60)),("misc","MISC",(120,80,20))]
        for i,(key,label,tcol) in enumerate(tabs):
            tr=pygame.Rect(px+10+i*120,py+8,112,26)
            self._tab_rects[key]=tr
            active=(self.tab==key)
            bg=tuple(min(255,c+40) for c in tcol) if active else (25,30,50)
            pygame.draw.rect(surf,bg,tr,border_radius=6)
            pygame.draw.rect(surf,tcol if active else C_BORDER,tr,1,border_radius=6)
            txt(surf,label,tr.center,C_WHITE,font_sm,center=True)

        content_top=py+42; content_h=ph-48
        surf.set_clip(pygame.Rect(px+2,content_top,pw-4,content_h))
        self._card_rects=[]
        cols=5; cw=116; ch=96; gap=7
        start_x=px+12; start_y=content_top+8

        if self.tab=="enemy":
            for i,(label,cls,col,hp,spd) in enumerate(ADMIN_ENEMY_LIST):
                c=i%cols; r=i//cols
                cx2=start_x+c*(cw+gap); cy2=start_y+r*(ch+gap)-self.scroll
                cr=pygame.Rect(cx2,cy2,cw,ch)
                self._card_rects.append((cr,cls))
                if cy2+ch<content_top or cy2>content_top+content_h: continue
                pygame.draw.rect(surf,(20,25,40),cr,border_radius=8)
                pygame.draw.rect(surf,col,cr,2,border_radius=8)
                preview_surf=pygame.Surface((40,40),pygame.SRCALPHA)
                try:
                    tmp=cls(1); tmp.x=20; tmp.y=20; tmp.draw(preview_surf)
                except: pygame.draw.circle(preview_surf,col,(20,20),12)
                surf.blit(preview_surf,(cx2+cw//2-20,cy2+4))
                lf=pygame.font.SysFont("segoeui",12,bold=True)
                surf.blit(lf.render(label,True,C_WHITE),
                          pygame.Rect(0,0,cw,14).move(cx2,cy2+46).topleft)
                sf=pygame.font.SysFont("segoeui",11)
                hp_str=f"{hp//1000}k" if hp>=1000 else str(hp)
                surf.blit(sf.render(f"HP {hp_str}",True,(180,180,200)),(cx2+6,cy2+62))
                surf.blit(sf.render(f"SPD {spd}",True,(140,200,140)),(cx2+6,cy2+76))

        elif self.tab=="units":
            unit_list=[
                ("Assassin",Assassin,C_ASSASSIN),("Accelerator",Accelerator,C_ACCEL),
                ("Frostcel.",Frostcelerator,(60,200,255)),("xw5yt",Xw5ytUnit,C_XW5YT),
                ("Lifestealer",Lifestealer,(220,40,80)),("Archer",Archer,(200,160,60)),
                ("Farm",Farm,(80,180,60)),("Red Ball",RedBall,(220,40,40)),
                ("FrostBlast",FrostBlaster,C_FROSTBLASTER),
                ("Sledger",Sledger,C_SLEDGER),
                ("Gladiator",Gladiator,C_GLADIATOR),
                ("ToxicGun",ToxicGunner,C_TOXICGUN),
                ("Slasher",Slasher,C_SLASHER),
                ("GoldCowboy",GoldenCowboy,C_GCOWBOY),
                ("HallowPunk",HallowPunk,C_HALLOWPUNK),
                ("Freezer",Freezer,C_FREEZER),
                ("Snowballer",Snowballer,C_SNOWBALLER),
                ("SbOld",SnowballerOld,C_SNOWBALLER),
                ("Commander",Commander,C_COMMANDER),
                ("Commando",Commando,C_COMMANDO),
                ("Spotlight",SpotlightTech,C_SPOTLIGHT),
            ]
            active_cls=set(s for s in (ui_ref.SLOT_TYPES if ui_ref else []) if s)
            for i,(name,cls,col) in enumerate(unit_list):
                c=i%cols; r=i//cols
                cx2=start_x+c*(cw+gap); cy2=start_y+r*(ch+gap)-self.scroll
                cr=pygame.Rect(cx2,cy2,cw,ch)
                self._card_rects.append((cr,(cls,name)))
                if cy2+ch<content_top or cy2>content_top+content_h: continue
                is_active=cls in active_cls
                pygame.draw.rect(surf,(30,50,30) if is_active else (20,25,40),cr,border_radius=8)
                pygame.draw.rect(surf,(80,220,80) if is_active else col,cr,2,border_radius=8)
                if name=="Accelerator": draw_accel_icon(surf,cx2+cw//2,cy2+26,t,size=18)
                elif name=="Frostcel.": draw_frost_icon(surf,cx2+cw//2,cy2+26,t,size=18)
                elif name=="xw5yt": draw_xw5yt_icon(surf,cx2+cw//2,cy2+26,t,size=18)
                else:
                    pygame.draw.circle(surf,(20,15,35),(cx2+cw//2,cy2+26),18)
                    pygame.draw.circle(surf,col,(cx2+cw//2,cy2+26),14)
                lf=pygame.font.SysFont("segoeui",12,bold=True)
                surf.blit(lf.render(name,True,(120,255,120) if is_active else C_WHITE),
                          pygame.Rect(0,0,cw,14).move(cx2,cy2+48).topleft)

        elif self.tab=="misc":
            self._misc_btns=[]
            mx2,my2=pygame.mouse.get_pos()
            sf_h=pygame.font.SysFont("segoeui",14,bold=True)
            sf_s=pygame.font.SysFont("segoeui",13)
            bw=220; bh=40; gap2=12
            cx_center=px+pw//2
            y=content_top+20

            def mbtn(label,action,col=(35,50,85),brd=(70,110,200)):
                r=pygame.Rect(cx_center-bw//2,y,bw,bh)
                self._misc_btns.append((r,action))
                hov=r.collidepoint(mx2,my2)
                bg=tuple(min(255,c+25) for c in col) if hov else col
                pygame.draw.rect(surf,bg,r,border_radius=8)
                pygame.draw.rect(surf,brd,r,2,border_radius=8)
                ls=sf_h.render(label,True,C_WHITE)
                surf.blit(ls,ls.get_rect(center=r.center))
                return r

            def slabel(text):
                ts=sf_s.render(text,True,(100,130,180))
                surf.blit(ts,(cx_center-bw//2,y))

            # ── HP ──
            slabel("PLAYER HP")
            y+=20
            mbtn("❤  Full HP","hp_full",(25,65,25),(60,180,60))
            y+=bh+gap2
            mbtn("☠  Set HP to 1","hp_1",(70,20,20),(200,50,50))
            y+=bh+gap2

            # HP text input
            inp_r=pygame.Rect(cx_center-bw//2,y,bw,bh)
            self._hp_input_rect=inp_r
            active=self._hp_input_active
            pygame.draw.rect(surf,(18,22,35) if not active else (25,35,55),inp_r,border_radius=8)
            pygame.draw.rect(surf,(80,160,255) if active else (50,60,90),inp_r,2,border_radius=8)
            disp=self._hp_input if self._hp_input else "Custom HP..."
            col_d=(220,220,255) if self._hp_input else (80,90,120)
            cursor_s="|" if (active and pygame.time.get_ticks()//500%2==0) else ""
            surf.blit(sf_h.render(disp+cursor_s,True,col_d),
                      sf_h.render(disp+cursor_s,True,col_d).get_rect(center=inp_r.center))
            if active:
                hint=sf_s.render("Press ENTER to apply",True,(80,120,160))
                surf.blit(hint,hint.get_rect(centerx=cx_center,top=inp_r.bottom+4))
            y+=bh+gap2+24

            # ── ENEMIES ──
            slabel("ENEMIES")
            y+=20
            mbtn("💀  Kill All Enemies","kill_all",(70,18,18),(200,50,50))
            y+=bh+gap2+8

            # ── SPEED ──
            slabel("GAME SPEED")
            y+=20
            spd=self._game_speed
            for lbl,act,spd_val in [("0.5x","speed_05",0.5),("1x  (normal)","speed_1",1.0),
                                     ("2x","speed_2",2.0),("5x","speed_5",5.0)]:
                active_spd=(spd==spd_val)
                mbtn(("✓  " if active_spd else "    ")+lbl, act,
                     (20,60,20) if active_spd else (30,38,60),
                     (80,220,80) if active_spd else (60,90,160))
                y+=bh+gap2

        surf.set_clip(None)
        # Scrollbar for scrollable tabs
        if self.tab in ("enemy","units"):
            _sb_cols=5
            n_items=len(ADMIN_ENEMY_LIST) if self.tab=="enemy" else len(unit_list)
            rows=((n_items+_sb_cols-1)//_sb_cols)
            total_h=rows*(ch+gap)
            if total_h>content_h:
                max_scroll=total_h-content_h
                self.scroll=min(self.scroll,max_scroll)
                sb_h=max(20,int(content_h*content_h/total_h))
                sb_y=content_top+int((content_h-sb_h)*self.scroll/max_scroll)
                pygame.draw.rect(surf,(50,60,90),(px+pw-10,content_top,6,content_h),border_radius=3)
                pygame.draw.rect(surf,(100,140,220),(px+pw-10,sb_y,6,sb_h),border_radius=3)

# ── UI ─────────────────────────────────────────────────────────────────────────
class UI:
    SLOT_TYPES=[Assassin,Accelerator,None,None,None]
    def __init__(self):
        self.slots=self._build_slots(); self.selected_slot=None
        self.drag_unit=None; self.open_unit=None; self.msg=""; self.msg_timer=0.0
        self.admin_panel=AdminPanel()
    def _build_slots(self):
        slots=[]; gap=8
        total_w=5*SLOT_W+4*gap
        start_x=(SCREEN_W-total_w)//2
        for i in range(5): slots.append(pygame.Rect(start_x+i*(SLOT_W+gap),SLOT_AREA_Y+8,SLOT_W,SLOT_H))
        return slots
    def show_msg(self,text,dur=2.0): self.msg=text; self.msg_timer=dur
    def update(self,dt):
        if self.msg_timer>0: self.msg_timer-=dt
    def handle_click(self,pos,units,money,effects,enemies,wave=1,save_data=None,mode="easy"):
        # Admin panel
        if mode=="sandbox":
            if self.admin_panel.visible:
                self.admin_panel.handle_click(pos,units,enemies,wave,save_data,ui_ref=self,game_ref=getattr(self,'_game_ref',None))
                return 0
            ab_r=getattr(self,'_admin_btn_rect',None)
            if ab_r and ab_r.collidepoint(pos):
                self.admin_panel.toggle(); return 0
        for u in units:
            btn1=getattr(u,'_ability_btn_rect',None)
            if btn1 and btn1.collidepoint(pos):
                if u.ability and u.ability.ready(): u.ability.activate(enemies,effects)
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
            if btns.get("close") and btns["close"].collidepoint(pos): self.open_unit=None; return 0
            if btns.get("sell") and btns["sell"].collidepoint(pos):
                sell_val=self._sell_value(self.open_unit)
                units.remove(self.open_unit); self.open_unit=None; return sell_val
            if btns.get("upgrade") and btns["upgrade"].collidepoint(pos):
                cost=self.open_unit.upgrade_cost()
                if cost and money>=cost:
                    self.open_unit.upgrade()
                    return -cost
                self.show_msg("Not enough money!" if cost else "Max level!"); return 0
            # Archer arrow mode buttons
            if isinstance(self.open_unit, Archer):
                u=self.open_unit
                if btns.get("arrow_arrow") and btns["arrow_arrow"].collidepoint(pos):
                    u.arrow_mode="arrow"; return 0
                if btns.get("arrow_ice") and btns["arrow_ice"].collidepoint(pos):
                    if u.level>=2: u.arrow_mode="ice_arrow"
                    else: self.show_msg("Unlock at level 2!")
                    return 0
                if btns.get("arrow_flame") and btns["arrow_flame"].collidepoint(pos):
                    if u.level>=3: u.arrow_mode="flame_arrow"
                    else: self.show_msg("Unlock at level 3!")
                    return 0
            if btns.get("ability_sq") and btns["ability_sq"].collidepoint(pos):
                if self.open_unit.ability and self.open_unit.ability.ready():
                    self.open_unit.ability.activate(enemies,effects)
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
                self.open_unit=None
            return 0
        for u in units:
            if dist((u.px,u.py),pos)<20: self.open_unit=u; return 0
        for i,slot in enumerate(self.slots):
            if slot.collidepoint(pos):
                UType=self.SLOT_TYPES[i]
                if UType is None: return 0  # empty slot — silently ignore
                self.selected_slot=i; self.drag_unit=UType(*pos); return 0
        return 0
    def handle_release(self,pos,units,money):
        if self.drag_unit is None: return 0
        mx,my=pos
        UType=self.SLOT_TYPES[self.selected_slot]
        def _on_any_path(px2, py2):
            paths = []
            if game_core.CURRENT_MAP == "frosty":
                paths = list(getattr(game_core, "_FROSTY_PATHS", []))
            else:
                paths = [get_map_path()]
            for path in paths:
                for pi in range(len(path)-1):
                    ax,ay=path[pi]; bx,by=path[pi+1]
                    if ax==bx:
                        if abs(px2-ax)<=PATH_H+5 and min(ay,by)-5<=py2<=max(ay,by)+5: return True
                    else:
                        if abs(py2-ay)<=PATH_H+5 and min(ax,bx)-5<=px2<=max(ax,bx)+5: return True
            return False
        on_path = _on_any_path(mx, my)
        # Archer can be placed on the path; others cannot
        # units list may include peer units for collision — filter to own only for limit check
        own_units = [u for u in units if not getattr(u, '_mp_peer', False)]
        if (on_path and not (UType and UType.NAME=="Archer")) or my>SLOT_AREA_Y-10 or any(dist((u.px,u.py),pos)<36 for u in units):
            self.show_msg("Can't place here!"); self.drag_unit=None; self.selected_slot=None; return 0
        # Check money
        if money<UType.PLACE_COST:
            self.show_msg("Not enough money!"); self.drag_unit=None; self.selected_slot=None; return 0
        # Check placement limit against OWN units only
        limit=UNIT_LIMITS.get(UType.NAME)
        if limit is not None:
            count=sum(1 for u in own_units if type(u)==UType)
            if count>=limit:
                self.show_msg(f"Limit: {limit} {UType.NAME}!"); self.drag_unit=None; self.selected_slot=None; return 0
        u=UType(mx,my); units.append(u)
        self.drag_unit=None; self.selected_slot=None; return -UType.PLACE_COST
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
            btn_h=24; btn_w=(mw-20)//3
            arrow_btn_y=my+260
            btns["arrow_arrow"]=pygame.Rect(mx+8,               arrow_btn_y, btn_w, btn_h)
            btns["arrow_ice"]  =pygame.Rect(mx+8+btn_w+3,       arrow_btn_y, btn_w, btn_h)
            btns["arrow_flame"]=pygame.Rect(mx+8+(btn_w+3)*2,   arrow_btn_y, btn_w, btn_h)
        return menu,btns

    def _draw_unit_portrait(self, surf, u, rect):
        """Draw unit portrait in a rect."""
        cx,cy=rect.centerx,rect.centery
        pygame.draw.rect(surf,(20,15,35),rect,border_radius=6)
        pygame.draw.rect(surf,(60,50,90),rect,2,border_radius=6)
        t=pygame.time.get_ticks()*0.001
        if isinstance(u,Accelerator): draw_accel_icon(surf,cx,cy,t,size=30)
        elif isinstance(u,Xw5ytUnit): draw_xw5yt_icon(surf,cx,cy,t,size=30)
        elif isinstance(u,Frostcelerator): draw_frost_icon(surf,cx,cy,t,size=30)
        elif isinstance(u,Lifestealer):
            pygame.draw.circle(surf,C_LIFESTEALER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_LIFESTEALER,(cx,cy),22)
            for i in range(3):
                a=math.radians(t*200+i*120)
                ox2=int(cx+math.cos(a)*18); oy2=int(cy+math.sin(a)*18)
                pygame.draw.circle(surf,(180,30,60),(ox2,oy2),5)
        elif isinstance(u,Archer):
            pygame.draw.circle(surf,C_ARCHER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_ARCHER,(cx,cy),22)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)
        elif isinstance(u,RedBall):
            pygame.draw.circle(surf,C_REDBALL_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_REDBALL,(cx,cy),22)
        elif isinstance(u,Freezer):
            pygame.draw.circle(surf,C_FREEZER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_FREEZER,(cx,cy),22)
        elif isinstance(u,FrostBlaster):
            pygame.draw.circle(surf,C_FROSTBLASTER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_FROSTBLASTER,(cx,cy),22)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)
        elif isinstance(u,Sledger):
            pygame.draw.circle(surf,C_SLEDGER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_SLEDGER,(cx,cy),22)
            # Mini hammer icon
            t2=pygame.time.get_ticks()*0.001
            a2=math.atan2(0,1)+math.sin(t2*2)*0.3
            ca2,sa2=math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(160,210,240),(cx+int(ca2*4),cy+int(sa2*4)),(cx+int(ca2*16),cy+int(sa2*16)),3)
            hpts=[(cx+int(ca2*17)-int(-sa2*6),cy+int(sa2*17)-int(ca2*6)),
                  (cx+int(ca2*17)+int(-sa2*6),cy+int(sa2*17)+int(ca2*6)),
                  (cx+int(ca2*22)+int(-sa2*6),cy+int(sa2*22)+int(ca2*6)),
                  (cx+int(ca2*22)-int(-sa2*6),cy+int(sa2*22)-int(ca2*6))]
            pygame.draw.polygon(surf,(100,180,255),hpts)
        elif isinstance(u,Gladiator):
            pygame.draw.circle(surf,C_GLADIATOR_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_GLADIATOR,(cx,cy),22)
            pygame.draw.circle(surf,(255,230,120),(cx,cy),22,2)
            # Mini sword
            t2=pygame.time.get_ticks()*0.001
            a2=math.atan2(1,-1)+math.sin(t2*3)*0.2
            ca2,sa2=math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(230,220,180),(cx+int(ca2*5),cy+int(sa2*5)),(cx+int(ca2*20),cy+int(sa2*20)),3)
            pygame.draw.line(surf,(200,160,50),(cx+int(ca2*10+sa2*6),cy+int(sa2*10-ca2*6)),(cx+int(ca2*10-sa2*6),cy+int(sa2*10+ca2*6)),2)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)
        elif isinstance(u,ToxicGunner):
            t2=pygame.time.get_ticks()*0.001
            pygame.draw.circle(surf,C_TOXICGUN_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_TOXICGUN,(cx,cy),22)
            pygame.draw.circle(surf,(140,255,100),(cx,cy),22,2)
            a2=0.1+math.sin(t2*4)*0.15
            ca2,sa2=math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(100,220,70),(cx+int(ca2*5),cy+int(sa2*5)),(cx+int(ca2*20),cy+int(sa2*20)),5)
            for i in range(3):
                rx=cx+int(ca2*(9+i*5)); ry=cy+int(sa2*(9+i*5))
                pygame.draw.circle(surf,(60,160,40),(rx,ry),3)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)
        elif isinstance(u,Slasher):
            t2=pygame.time.get_ticks()*0.001
            pygame.draw.circle(surf,C_SLASHER_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_SLASHER,(cx,cy),22)
            pygame.draw.circle(surf,(220,80,80),(cx,cy),22,2)
            a2=math.radians(-40)+math.sin(t2*5)*0.15
            ca2,sa2=math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(220,200,200),(cx+int(ca2*5),cy+int(sa2*5)),(cx+int(ca2*20),cy+int(sa2*20)),2)
            pygame.draw.circle(surf,(255,230,230),(cx+int(ca2*20),cy+int(sa2*20)),3)
            pygame.draw.line(surf,(180,60,60),(cx+int(ca2*12-sa2*6),cy+int(sa2*12+ca2*6)),(cx+int(ca2*12+sa2*6),cy+int(sa2*12-ca2*6)),2)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)
        elif isinstance(u,GoldenCowboy):
            t2=pygame.time.get_ticks()*0.001
            pygame.draw.circle(surf,C_GCOWBOY_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_GCOWBOY,(cx,cy),22)
            pygame.draw.circle(surf,(255,230,100),(cx,cy),22,2)
            pygame.draw.ellipse(surf,(160,110,20),(cx-16,cy-32,32,8))
            pygame.draw.ellipse(surf,(200,150,40),(cx-10,cy-36,20,10))
            a2=0.2+math.sin(t2*2)*0.2
            ca2,sa2=math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(200,160,40),(cx+int(ca2*6),cy+int(sa2*6)),(cx+int(ca2*20),cy+int(sa2*20)),5)
            pygame.draw.circle(surf,(255,220,80),(cx+int(ca2*20),cy+int(sa2*20)),4)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)
        elif isinstance(u,HallowPunk):
            t2=pygame.time.get_ticks()*0.001
            pygame.draw.circle(surf,C_HALLOWPUNK_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_HALLOWPUNK,(cx,cy),22)
            pygame.draw.circle(surf,(240,140,240),(cx,cy),22,2)
            a2=0.3+math.sin(t2*2)*0.2
            ca2,sa2=math.cos(a2),math.sin(a2)
            pygame.draw.line(surf,(160,60,160),(cx+int(ca2*5),cy+int(sa2*5)),(cx+int(ca2*20),cy+int(sa2*20)),7)
            pygame.draw.line(surf,(220,120,220),(cx+int(ca2*5),cy+int(sa2*5)),(cx+int(ca2*20),cy+int(sa2*20)),4)
            pygame.draw.circle(surf,(240,160,240),(cx+int(ca2*20),cy+int(sa2*20)),5)
        elif isinstance(u,SpotlightTech):
            t2=pygame.time.get_ticks()*0.001
            pygame.draw.circle(surf,C_SPOTLIGHT_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_SPOTLIGHT,(cx,cy),22)
            pygame.draw.circle(surf,(255,250,180),(cx,cy),22,2)
            # Beam fan
            a2=u._beam_angle
            ca2,sa2=math.cos(a2),math.sin(a2)
            for i in range(5):
                frac=(i/4-0.5)*0.6
                ex2=cx+int((ca2*22+(-sa2)*frac*20)); ey2=cy+int((sa2*22+ca2*frac*20))
                alpha2=max(0,120-abs(i-2)*35)
                beam_s=pygame.Surface((4,4),pygame.SRCALPHA)
                pygame.draw.circle(beam_s,(255,240,80,alpha2),(2,2),2)
                surf.blit(beam_s,(ex2-2,ey2-2))
            # Lens glow
            lx2=cx+int(ca2*15); ly2=cy+int(sa2*15)
            gs2=pygame.Surface((16,16),pygame.SRCALPHA)
            gp=int(abs(math.sin(t2*4))*80+120)
            pygame.draw.circle(gs2,(255,245,100,gp),(8,8),7)
            surf.blit(gs2,(lx2-8,ly2-8))
        elif isinstance(u,Farm):
            pygame.draw.circle(surf,C_FARM_DARK,(cx,cy),28)
            pygame.draw.circle(surf,C_FARM,(cx,cy),22)
            ico_farm=load_icon("money_ico",22)
            if ico_farm:
                surf.blit(ico_farm,(cx-11,cy-11))
            else:
                txt(surf,"$",(cx,cy),C_GOLD,font_md,center=True)
        else:
            pygame.draw.circle(surf,(70,40,100),(cx,cy),28)
            pygame.draw.circle(surf,u.COLOR,(cx,cy),22)
            if u.hidden_detection:
                pygame.draw.circle(surf,(100,255,100),(cx+18,cy-18),5)

    def _sell_value(self, unit):
        """30% of place cost + all upgrade costs paid."""
        total=unit.PLACE_COST
        cls=type(unit)
        if cls==Assassin: levels=ASSASSIN_LEVELS; cost_idx=3
        elif cls==Accelerator: levels=ACCEL_LEVELS; cost_idx=3
        elif cls==Xw5ytUnit: levels=XW5YT_LEVELS; cost_idx=3
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
        elif cls==Commander: levels=COMMANDER_LEVELS; cost_idx=3
        elif cls==Commando: levels=COMMANDO_LEVELS; cost_idx=3
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
        elif cls==Xw5ytUnit:
            if nxt>=len(XW5YT_LEVELS): return None
            d,fr,r,_,dual=XW5YT_LEVELS[nxt]
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
            d,fr,r,_,pc=ARCHER_LEVELS[nxt]
            hd=nxt>=4
            return {"Damage":d,"Firerate":fr,"Range":r,"Pierce":pc,"HidDet":hd}
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
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "CashShot":f"${inc} / {cs} shots","SpinTime":f"{st:.1f}s"}
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
            if nxt>=len(SNOWBALLER_LEVELS): return None
            d,fr,r,_,sp,sm,sd,ft,fs,expl,sr,db=SNOWBALLER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Slow":f"{int(sp*100)}% max {int(sm*100)}% / {sd:.0f}s"}
            if expl: result["Splash"]=f"{sr} tiles"; result["DefBypass"]="YES"
            if ft>0: result["Freeze"]=f"@{int(ft*100)}% → {fs:.0f}s"
            return result
            if nxt>=len(SNOWBALLER_LEVELS): return None
            d,fr,r,_,sp,sm,sd,ft,fs,fly,expl,sr,mh,db=SNOWBALLER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Slow":f"{int(sp*100)}% max {int(sm*100)}% / {sd:.0f}s"}
            if expl: result["Splash"]=f"{sr} tiles"; result["DefBypass"]="YES"
            if ft>0: result["Freeze"]=f"@{int(ft*100)}% → {fs:.0f}s"
            if fly and not unit.hidden_detection: result["HidDet"]="Flying Det"
            return result
            if nxt>=len(SNOWBALLER_LEVELS): return None
            d,fr,r,_,sr,sp,sm,sd,hd=SNOWBALLER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Splash":f"{sr} tiles","Slow":f"{int(sp*100)}%/{sd:.0f}s max {int(sm*100)}%"}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Commander:
            if nxt>=len(COMMANDER_LEVELS): return None
            d,fr,r,_,bp,cta,hid=COMMANDER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"Buff":f"+{int(bp*100)}% faster"}
            if cta>0: result["CtaBuff"]=f"+{int(cta*100)}% CTA"
            if hid and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
            if nxt>=len(COMMANDER_LEVELS): return None
            d,fr,r,_,bp,cta,hid,lead,fly=COMMANDER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,"Buff":f"+{int(bp*100)}% faster"}
            if cta>0: result["CtaBuff"]=f"+{int(cta*100)}% CTA"
            if hid and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
            if nxt>=len(COMMANDER_LEVELS): return None
            d,fr,r,_,br,bm,hd=COMMANDER_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "BuffRange":f"{br} tiles","BuffMult":f"x{bm:.2f} firerate"}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        elif cls==Commando:
            if nxt>=len(COMMANDO_LEVELS): return None
            d,fr,r,_,burst,bcd,pierce,hd=COMMANDO_LEVELS[nxt]
            result={"Damage":d,"Firerate":fr,"Range":r,
                    "Burst":f"{burst} shots / {bcd:.1f}s cd","Pierce":pierce}
            if hd and not unit.hidden_detection: result["HidDet"]="Hidden Detection"
            return result
        return None

    def draw(self,surf,units,money,wave_mgr,player_hp,player_maxhp,enemies,
             boss_enemy=None,hidden_wave_active=False,hw_good_luck=False,extra_boss_bars=None,fallen_boss_bars=None,mode="easy"):
        wave=wave_mgr.wave; gl=hw_good_luck
        is_sandbox=(mode=="sandbox")
        pygame.draw.rect(surf,C_PANEL,(0,0,SCREEN_W,50))
        pygame.draw.line(surf,C_BORDER,(0,50),(SCREEN_W,50),2)
        if is_sandbox:
            # Admin panel button where wave counter would be
            ap_r=pygame.Rect(8,8,120,34)
            mx2,my2=pygame.mouse.get_pos()
            ap_hov=ap_r.collidepoint(mx2,my2)
            ap_open=getattr(self,'_admin_open',False)
            ap_bg=(50,80,130) if (ap_open or ap_hov) else (30,40,65)
            pygame.draw.rect(surf,ap_bg,ap_r,border_radius=6)
            pygame.draw.rect(surf,(80,140,255) if ap_open else C_BORDER,ap_r,2,border_radius=6)
            txt(surf,"⚙ ADMIN",ap_r.center,C_WHITE,font_md,center=True)
            self._admin_btn_rect=ap_r
        else:
            wave_str="good luck" if gl else f"WAVE  {wave}/{wave_mgr.max_waves}"
            txt(surf,wave_str,(18,14),C_RED if gl else C_CYAN,font_lg)
            tl=wave_mgr.time_left()
            if tl is not None and not gl: txt(surf,f"Next: {tl:.1f}s",(210,18),C_GOLD,font_sm)
        # HP bar — center top
        bx_hp=SCREEN_W//2-110; bw_hp=220; bh_hp=22
        ratio=max(0,player_hp/player_maxhp)
        pygame.draw.rect(surf,C_HP_BG,(bx_hp,14,bw_hp,bh_hp),border_radius=4)
        if ratio>0:
            col=C_HP_FG2 if ratio>0.4 else C_HP_FG
            pygame.draw.rect(surf,col,(bx_hp,14,int(bw_hp*ratio),bh_hp),border_radius=4)
        pygame.draw.rect(surf,C_BORDER,(bx_hp,14,bw_hp,bh_hp),2,border_radius=4)
        hp_str="good luck" if gl else f"HP  {player_hp}/{player_maxhp}"
        txt(surf,hp_str,(bx_hp+bw_hp//2,25),(255,80,80) if gl else C_WHITE,font_sm,center=True)
        bar_y=65
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
        # ── Bottom panel background ──────────────────────────────────────────
        panel_h = SCREEN_H - SLOT_AREA_Y
        pygame.draw.rect(surf, (14, 17, 26), (0, SLOT_AREA_Y, SCREEN_W, panel_h))
        pygame.draw.line(surf, (50, 58, 80), (0, SLOT_AREA_Y), (SCREEN_W, SLOT_AREA_Y), 2)

        # ── Money display — bottom left ──────────────────────────────────────
        money_cy = SLOT_AREA_Y + panel_h // 2
        ico_money = load_icon("money_ico", 36)
        if ico_money:
            surf.blit(ico_money, (14, money_cy - 18))
            mx_off = 14 + 36 + 6
        else:
            mx_off = 14
        if gl or is_sandbox:
            ms = pygame.font.SysFont("segoeui", 28, bold=True).render("∞", True, C_GOLD)
        else:
            ms = pygame.font.SysFont("segoeui", 28, bold=True).render(str(money), True, C_GOLD)
        surf.blit(ms, (mx_off, money_cy - ms.get_height() // 2))

        # ── Slot cards ───────────────────────────────────────────────────────
        _slot_font_name  = pygame.font.SysFont("segoeui", 17, bold=True)
        _slot_font_price = pygame.font.SysFont("segoeui", 15)
        ico_coin = load_icon("money_ico", 15)

        for i, slot in enumerate(self.slots):
            UType = self.SLOT_TYPES[i]
            sel   = (i == self.selected_slot)
            cx2   = slot.centerx
            # Determine availability
            cant_afford = UType is not None and not gl and not is_sandbox and money < UType.PLACE_COST
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
                # Big circle icon — centred in card, leaving room for text below
                icon_cy = slot.y + 52
                r_outer = 34
                r_inner = 28
                # Shadow ring
                pygame.draw.circle(surf, (10, 10, 18), (cx2, icon_cy), r_outer + 3)
                # Dark base
                pygame.draw.circle(surf, tuple(max(0, c - 60) for c in UType.COLOR),
                                   (cx2, icon_cy), r_outer)
                # Main colour (dimmed if unavailable)
                col_main = tuple(c // 3 for c in UType.COLOR) if unavailable else UType.COLOR
                pygame.draw.circle(surf, col_main, (cx2, icon_cy), r_inner)
                # Bright rim
                pygame.draw.circle(surf,
                                   tuple(min(255, c + 60) for c in UType.COLOR) if not unavailable else (60,60,70),
                                   (cx2, icon_cy), r_inner, 2)

                # Name
                name_col = (110, 115, 130) if unavailable else (210, 215, 230)
                ns = _slot_font_name.render(UType.NAME, True, name_col)
                surf.blit(ns, ns.get_rect(centerx=cx2, top=slot.y + 94))

                # Price row
                if gl:
                    ps = _slot_font_price.render("good luck", True, C_RED)
                    surf.blit(ps, ps.get_rect(centerx=cx2, top=slot.y + 114))
                elif over_limit:
                    ps = _slot_font_price.render("LIMIT", True, (200, 80, 80))
                    surf.blit(ps, ps.get_rect(centerx=cx2, top=slot.y + 114))
                else:
                    price_col = (200, 80, 80) if cant_afford else C_GOLD
                    price_str = str(UType.PLACE_COST)
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
                qs = pygame.font.SysFont("consolas", 22, bold=True).render("?", True, (60, 65, 90))
                surf.blit(qs, qs.get_rect(center=slot.center))
        mx2,my2=pygame.mouse.get_pos()
        for u in units:
            if dist((u.px,u.py),(mx2,my2))<22 and self.open_unit!=u: u.draw_range(surf)
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
            levels_map={Assassin:ASSASSIN_LEVELS,Accelerator:ACCEL_LEVELS,Frostcelerator:FROST_LEVELS,Xw5ytUnit:XW5YT_LEVELS,Lifestealer:LIFESTEALER_LEVELS,Archer:ARCHER_LEVELS,RedBall:REDBALL_LEVELS,FrostBlaster:FROSTBLASTER_LEVELS,Sledger:SLEDGER_LEVELS,Gladiator:GLADIATOR_LEVELS,ToxicGunner:TOXICGUN_LEVELS,Slasher:SLASHER_LEVELS,GoldenCowboy:GCOWBOY_LEVELS,HallowPunk:HALLOWPUNK_LEVELS,SpotlightTech:SPOTLIGHTTECH_LEVELS,Snowballer:SNOWBALLER_LEVELS,Commander:COMMANDER_LEVELS,Commando:COMMANDO_LEVELS}
            lvl_list=levels_map.get(cls,[])
            total_lvls=len(lvl_list)

            # Build stats list: (key, display_val, next_val_or_None)
            # HidDet: shown in stats only if already active; shown in "changes" if it unlocks next
            STAT_ICO={"Damage":"damage_ico","Firerate":"firerate_ico",
                      "Range":"range_ico","Slow":"slow_ico","HidDet":"hidden_detection_ico",
                      "FlameArrow":"flame_ico","IceArrow":"slow_ico","Income":"money_ico",
                      "Pierce":"pierce_ico","Freeze":"slow_ico"}
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
            elif cls==Xw5ytUnit:
                stats=[
                    ("HidDet","Hidden Detection" if u.hidden_detection else "lv1+", None),
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.4f}", f"{nxt['Firerate']:.4f}" if nxt else None),
                    ("Range",   u.range_tiles,   nxt.get("Range")    if nxt else None),
                ]
                if nxt and nxt.get("Dual") and not u.dual:
                    stats.append(("Dual_unlock",None,"+Dual target"))
                if u.level>=2:
                    stats.append(("Damage","hixw5yt: READY" if (u.ability and u.ability.ready()) else f"hixw5yt: {u.ability.cd_left:.0f}s" if u.ability else "hixw5yt: lv2+",None))
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
                hd_next=bool(nxt and nxt.get("HidDet") and not hd_now)
                flame_now=(u.arrow_mode=="flame_arrow" and u.level>=3)
                ice_now  =(u.arrow_mode=="ice_arrow"   and u.level>=2)
                flame_next=bool(nxt and (u.level+1)>=3 and not flame_now and u.arrow_mode=="flame_arrow")
                ice_next  =bool(nxt and (u.level+1)>=2 and not ice_now   and u.arrow_mode=="ice_arrow")
                stats=[]
                if hd_now:    stats.append(("HidDet","Hidden Detection",None))
                if flame_now: stats.append(("FlameArrow","Flame Arrow",None))
                if ice_now:   stats.append(("IceArrow","Ice Arrow",None))
                stats+=[
                    ("Damage",  u.damage,        nxt.get("Damage")   if nxt else None),
                    ("Firerate",f"{u.firerate:.3f}", f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",   u.range_tiles,   nxt.get("Range")    if nxt else None),
                    ("Pierce",  u.pierce,        nxt.get("Pierce")   if nxt else None),
                ]
                if hd_next:    stats.append(("HidDet_unlock",None,"Hidden Detection"))
                if flame_next: stats.append(("FlameArrow_unlock",None,"Flame Arrow"))
                if ice_next:   stats.append(("IceArrow_unlock",None,"Ice Arrow"))
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
                shots_left=u._cash_shot-u._shot_count
                stats=[]
                if hd_now: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,            nxt.get("Damage")    if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",  f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,         nxt.get("Range")    if nxt else None),
                    ("CashShot", f"${u._income}/{u._cash_shot} shots (in {shots_left})",
                                  nxt.get("CashShot") if nxt else None),
                    ("SpinTime", f"{u._spin_time:.1f}s", nxt.get("SpinTime") if nxt else None),
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
            elif cls==Commander:
                hd_next=bool(nxt and nxt.get("HidDet") and not u.hidden_detection)
                stats=[]
                if u.hidden_detection: stats.append(("HidDet","Hidden Detection",None))
                stats+=[
                    ("Damage",   u.damage,              nxt.get("Damage")   if nxt else None),
                    ("Firerate", f"{u.firerate:.3f}",    f"{nxt['Firerate']:.3f}" if nxt else None),
                    ("Range",    u.range_tiles,           nxt.get("Range")   if nxt else None),
                    ("Buff",     f"+{int(u.buff_pct*100)}% faster", nxt.get("Buff") if nxt else None),
                ]
                if u.cta_buff_pct>0:
                    stats.append(("CtaBuff",f"+{int(u.cta_buff_pct*100)}% CTA",nxt.get("CtaBuff") if nxt else None))
                elif nxt and nxt.get("CtaBuff"):
                    stats.append(("CtaBuff",None,nxt["CtaBuff"]))
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
            else:
                stats=[(k,v,None) for k,v in u.get_info().items()]

            STAT_COLORS={"HidDet":(80,255,120),"HidDet_unlock":(80,255,120),
                         "Damage":(255,120,80),"Firerate":(255,220,60),
                         "Range":(80,200,255),"Dual_unlock":(200,100,255),"Slow":(100,200,255),
                         "Money":(220,60,80),"Pierce":(200,160,80),
                         "FlameArrow":(255,130,30),"FlameArrow_unlock":(255,130,30),
                         "IceArrow":(100,200,255),"IceArrow_unlock":(100,200,255),
                         "Income":(100,220,80),"Ability":(200,150,255),"Ability_unlock":(200,150,255),
                         "Freeze":(160,230,255),"ArmorShred":(255,160,60),"DefDrop":(255,100,80),
                         "Hits":(200,200,100),"IceBreaker":(100,220,255),"Aftershock":(140,200,255),
                         "StunBlock":(255,220,80),
                         "Poison":(100,220,80),"Crit":(255,160,40),"Bleed":(200,40,40),
                         "CashShot":(255,220,60),"SpinTime":(200,180,100),
                         "Burn":(255,130,30),"Knockback":(200,160,255),"Splash":(220,100,220),
                         "BeamCircle":(255,240,80),"Expose":(100,255,200),"Confuse":(200,100,255)}

            # === TOP HALF: portrait left + STATS right ===
            # For Frostcelerator: stun bar at very top of card
            top_offset=4
            if isinstance(u,Frostcelerator):
                bar_x=mx_m+6; bar_w=mw-12; bar_y=my_m+top_offset+14
                frac=min(1.0,u._shared_dmg/1000)
                stun_s=font_sm.render(f"Stun: {int(u._shared_dmg)}/1000",True,(120,200,255))
                surf.blit(stun_s,(bar_x,my_m+top_offset))
                pygame.draw.rect(surf,(15,38,65),(bar_x,bar_y,bar_w,9),border_radius=4)
                pygame.draw.rect(surf,C_FROST,(bar_x,bar_y,int(bar_w*frac),9),border_radius=4)
                pygame.draw.rect(surf,(55,150,210),(bar_x,bar_y,bar_w,9),1,border_radius=4)
                top_offset+=26

            # Portrait square (left column)
            portrait_size=150
            portrait_rect=pygame.Rect(mx_m+6,my_m+top_offset,portrait_size,portrait_size)
            self._draw_unit_portrait(surf,u,portrait_rect)

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
                val_s=font_md.render(str(sval),True,(230,230,230))
                surf.blit(val_s,(rx+ICO_SZ+5,siy))
                siy+=22

            # === NAME + LEVEL + TOTAL DAMAGE strip ===
            strip_y=my_m+top_offset+portrait_size+6
            pygame.draw.rect(surf,(28,22,48),(mx_m+6,strip_y,mw-12,48),border_radius=5)
            txt(surf,u.NAME,(mx_m+10,strip_y+4),(210,190,255),font_lg)
            txt(surf,f"Level: {u.level}",(mx_m+10,strip_y+26),(140,130,175),font_md)
            td_s=font_md.render(f"Total Damage:",True,(160,155,185))
            td_n=font_lg.render(str(int(u.total_damage)),True,(240,220,100))
            surf.blit(td_s,(mx_m+mw-10-max(td_s.get_width(),td_n.get_width()),strip_y+4))
            surf.blit(td_n,(mx_m+mw-10-td_n.get_width(),strip_y+22))

            # === UPGRADE BUTTON ===
            cost=u.upgrade_cost()
            strip_y_actual=my_m+top_offset+portrait_size+6
            btns["upgrade"]=pygame.Rect(mx_m+6,strip_y_actual+54,mw-12,44)
            btn_bottom_y=my_m+menu.h-44
            btns["close"]=pygame.Rect(mx_m+6,btn_bottom_y,38,38)
            btns["sell"]=pygame.Rect(mx_m+48,btn_bottom_y,mw-54,38)
            if cls==Archer:
                btn_h=24; btn_w=(mw-20)//3
                arrow_btn_y=strip_y_actual+56
                btns["arrow_arrow"]=pygame.Rect(mx_m+8,               arrow_btn_y, btn_w, btn_h)
                btns["arrow_ice"]  =pygame.Rect(mx_m+8+btn_w+3,       arrow_btn_y, btn_w, btn_h)
                btns["arrow_flame"]=pygame.Rect(mx_m+8+(btn_w+3)*2,   arrow_btn_y, btn_w, btn_h)
                btns["upgrade"]=pygame.Rect(mx_m+6,strip_y_actual+54+btn_h+6,mw-12,44)
            up_rect=btns["upgrade"]
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
            else:
                txt(surf,"✓ MAX LEVEL",up_rect.center,(100,160,100),font_lg,center=True)

            # === LEVEL PROGRESS BARS ===
            dot_y=up_rect.bottom+8
            bar_total_w=mw-20
            bar_h=10
            if total_lvls>1:
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
            _upg_names_map = {Snowballer: SNOWBALLER_LEVEL_NAMES, Commander: COMMANDER_LEVEL_NAMES}
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
            changing=[(s,v,n) for s,v,n in stats if n is not None and (v is None or str(n)!=str(v))]
            ch_y=dot_y+20

            # === ARCHER ARROW MODE SELECTOR ===
            if cls==Archer:
                arrow_modes=[
                    ("arrow",     "Arrow",      (200,140,60),  (255,180,80)),
                    ("ice_arrow", "Ice Arrow",  (80,180,255),  (160,220,255)),
                    ("flame_arrow","Flame Arrow",(220,80,20),  (255,150,50)),
                ]
                for mode_key, mode_label, col_active, col_border in arrow_modes:
                    if mode_key=="arrow":       br=btns["arrow_arrow"]
                    elif mode_key=="ice_arrow": br=btns["arrow_ice"]
                    else:                       br=btns["arrow_flame"]
                    is_sel=(u.arrow_mode==mode_key)
                    locked=(mode_key=="ice_arrow" and u.level<2) or (mode_key=="flame_arrow" and u.level<3)
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
                        req_lvl="Lv2" if mode_key=="ice_arrow" else "Lv3"
                        lock_s=pygame.font.SysFont("consolas",9).render(req_lvl,True,(90,80,120))
                        surf.blit(lock_s,(br.right-lock_s.get_width()-2, br.y+2))

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
                        ico_drawn=True
                if not ico_drawn:
                    dot_s=font_md.render("●",True,sc)
                    surf.blit(dot_s,(xp,ch_y))
                xp+=ICO_SZ+5
                if sval is not None:
                    old_s=font_md.render(str(sval),True,(190,185,210))
                    surf.blit(old_s,(xp,ch_y)); xp+=old_s.get_width()+4
                if sval is not None:
                    arr_img=load_icon("arrow_ico",ARR_SZ)
                    if arr_img:
                        surf.blit(arr_img,(xp,ch_y+(16-ARR_SZ)//2)); xp+=ARR_SZ+4
                    else:
                        arr_s=font_md.render("→",True,(160,155,180))
                        surf.blit(arr_s,(xp,ch_y)); xp+=arr_s.get_width()+3
                new_s=font_md.render(str(snext),True,(100,220,100))
                surf.blit(new_s,(xp,ch_y))
                ch_y+=20


            # === ABILITY SQUARE — outside card, top-left ===
            if u.ability and u.level>=2:
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
            pygame.draw.rect(surf,(40,22,22),btns["close"],border_radius=5)
            pygame.draw.rect(surf,(100,40,40),btns["close"],1,border_radius=5)
            txt(surf,"X",btns["close"].center,(220,100,100),font_lg,center=True)

            sell_val=self._sell_value(u)
            pygame.draw.rect(surf,(170,28,28),btns["sell"],border_radius=5)
            pygame.draw.rect(surf,(230,65,65),btns["sell"],1,border_radius=5)
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
            # === TARGET PANEL — small card to the left of main menu ===
            tp_w=150; tp_h=72
            tp_x=mx_m - tp_w - 8
            tp_y=my_m + (menu.h - tp_h) // 2
            tp_rect=pygame.Rect(tp_x, tp_y, tp_w, tp_h)
            btns["target_panel"]=tp_rect

            draw_rect_alpha(surf,(20,16,36),
                            (tp_x,tp_y,tp_w,tp_h),248,8)
            pygame.draw.rect(surf,(55,44,82),tp_rect,2,border_radius=8)

            # Label
            lbl_s=font_sm.render("TARGET",True,(160,155,200))
            surf.blit(lbl_s,lbl_s.get_rect(centerx=tp_x+tp_w//2, top=tp_y+6))

            # Mode name
            cur_mode=getattr(u,'target_mode','First')
            mode_f=pygame.font.SysFont("segoeui",15,bold=True)
            mode_s=mode_f.render(cur_mode,True,(220,215,255))
            surf.blit(mode_s,mode_s.get_rect(centerx=tp_x+tp_w//2,centery=tp_y+36))

            # ◄ / ► arrow buttons
            arr_w=26; arr_h=26
            btn_prev=pygame.Rect(tp_x+6,        tp_y+tp_h-arr_h-6, arr_w, arr_h)
            btn_next=pygame.Rect(tp_x+tp_w-arr_w-6, tp_y+tp_h-arr_h-6, arr_w, arr_h)
            btns["target_prev"]=btn_prev
            btns["target_next"]=btn_next
            mx3,my3=pygame.mouse.get_pos()
            for br,label in ((btn_prev,"◄"),(btn_next,"►")):
                hov2=br.collidepoint(mx3,my3)
                pygame.draw.rect(surf,(50,60,100) if hov2 else (30,28,50),br,border_radius=5)
                pygame.draw.rect(surf,(100,140,220) if hov2 else (60,55,90),br,1,border_radius=5)
                arr_s=font_md.render(label,True,(200,200,255) if hov2 else (130,125,170))
                surf.blit(arr_s,arr_s.get_rect(center=br.center))

            # Cache final button positions for handle_click
            self._cached_btns=btns

        if self.drag_unit:
            mx2,my2=pygame.mouse.get_pos()
            self.drag_unit.px=mx2; self.drag_unit.py=my2
            # Keep RedBall home in sync with cursor during drag
            if isinstance(self.drag_unit,RedBall):
                self.drag_unit._home_x=float(mx2); self.drag_unit._home_y=float(my2)
            self.drag_unit.draw_range(surf); self.drag_unit.draw(surf)
        ab_entries=[]
        for u in units:
            if getattr(u,'ability2',None) and u.level>=1: ab_entries.append((u, u.ability2, 'ab2'))
            if u.ability and u.level>=2: ab_entries.append((u, u.ability, 'ab1'))
            if getattr(u,'ability3',None) and u.level>=4: ab_entries.append((u, u.ability3, 'ab3'))
        for idx,(u,ab,slot) in enumerate(ab_entries):
            bw3,bh3=160,48; bx3=SCREEN_W-bw3-8; by3=80+idx*(bh3+8)
            ready=ab.ready()
            pygame.draw.rect(surf,(30,70,80) if ready else (30,30,40),(bx3,by3,bw3,bh3),border_radius=8)
            pygame.draw.rect(surf,C_CYAN if ready else C_BORDER,(bx3,by3,bw3,bh3),2,border_radius=8)
            pygame.draw.circle(surf,u.COLOR,(bx3+26,by3+bh3//2),16)
            pygame.draw.circle(surf,C_WHITE,(bx3+26,by3+bh3//2),16,2)
            txt(surf,ab.name if ready else f"CD {ab.cd_left:.1f}s",(bx3+46,by3+8),C_WHITE if ready else (100,100,120),font_sm)
            if not ready:
                r3=1-(ab.cd_left/ab.cooldown)
                pygame.draw.rect(surf,(40,40,60),(bx3+46,by3+26,bw3-54,8),border_radius=3)
                pygame.draw.rect(surf,C_CYAN,(bx3+46,by3+26,int((bw3-54)*r3),8),border_radius=3)
            else:
                txt(surf,"CLICK / [F]",(bx3+46,by3+28),C_CYAN,font_sm)
            ab._btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
            if slot=='ab1': u._ability_btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
            elif slot=='ab2': u._ability2_btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
            elif slot=='ab3': u._ability3_btn_rect=pygame.Rect(bx3,by3,bw3,bh3)
        if self.msg_timer>0:
            alpha=min(255,int(self.msg_timer*255))
            s2=font_lg.render(self.msg,True,C_ORANGE); s2.set_alpha(alpha)
            surf.blit(s2,s2.get_rect(center=(SCREEN_W//2,SCREEN_H//2-60)))
        for e in enemies:
            if e.alive and dist((e.x,e.y),(mx2,my2))<e.radius+5:
                e.draw(surf,hovered=True,detected=True)

# ── Rarity card drawing helper ──────────────────────────────────────────────────
def draw_accel_icon(surf, cx, cy, t, size=28):
    spin = t * 180
    orb_r = int(size * 0.65)
    for i in range(4):
        a = math.radians(spin + i * 90)
        ox = cx + int(math.cos(a) * orb_r)
        oy = cy + int(math.sin(a) * orb_r)
        pygame.draw.circle(surf, (160, 100, 255), (ox, oy), max(2, size // 7))
    pygame.draw.circle(surf, (40, 20, 80), (cx, cy), int(size * 0.65))
    pygame.draw.circle(surf, C_ACCEL, (cx, cy), int(size * 0.48))
    hi = max(1, size // 6)
    pygame.draw.circle(surf, (200, 170, 255), (cx - hi, cy - hi), hi + 1)


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


def draw_unit_card(surf, unit_name, rarity_key, cx, cy, w=160, h=220, t=0.0, selected=False):
    rd = RARITY_DATA.get(rarity_key, RARITY_DATA["starter"])
    bx, by = cx - w//2, cy - h//2

    base_col = rd["color"]
    s_card = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s_card, (*base_col, 220), (0, 0, w, h), border_radius=18)

    border_col = rd["border"]
    if selected:
        border_col = (255, 220, 50)
        pygame.draw.rect(s_card, (255, 220, 50, 60), (0, 0, w, h), border_radius=18)
    pygame.draw.rect(s_card, (*border_col, 255), (0, 0, w, h), 3, border_radius=18)
    surf.blit(s_card, (bx, by))

    # Rarity badge top-right — bigger font and badge
    rlab = rd["label"]
    badge_col = rd["border"]
    badge_f = pygame.font.SysFont("consolas", 15, bold=True)
    bs = badge_f.render(rlab, True, rd["text_col"])
    bsw = bs.get_width() + 14
    badge_rect = pygame.Rect(bx + w - bsw - 6, by + 6, bsw, 26)
    pygame.draw.rect(surf, (*base_col, 240), badge_rect, border_radius=6)
    pygame.draw.rect(surf, badge_col, badge_rect, 1, border_radius=6)
    surf.blit(bs, (badge_rect.x + 7, badge_rect.y + 5))

    # Unit icon — bigger circles
    icon_cx, icon_cy = cx, cy - 30
    if unit_name == "Accelerator":
        draw_accel_icon(surf, icon_cx, icon_cy, t, size=32)
    elif unit_name == "Frostcelerator":
        draw_frost_icon(surf, icon_cx, icon_cy, t, size=32)
    elif unit_name == "xw5yt":
        draw_xw5yt_icon(surf, icon_cx, icon_cy, t, size=32)
    else:
        _col_map = {
            "Assassin": C_ASSASSIN,
            "Lifestealer": C_LIFESTEALER,
            "Archer": C_ARCHER,
            "Red Ball": C_REDBALL,
            "Farm": C_FARM,
            "Freezer": C_FREEZER,
            "Frost Blaster": C_FROSTBLASTER,
            "Sledger": C_SLEDGER,
            "Gladiator": C_GLADIATOR,
            "Toxic Gunner": C_TOXICGUN,
            "Slasher": C_SLASHER,
            "Golden Cowboy": C_GCOWBOY,
            "Hallow Punk": C_HALLOWPUNK,
            "Spotlight Tech": C_SPOTLIGHT,
            "Snowballer": C_SNOWBALLER,
            "Commander": C_COMMANDER,
            "Commando": C_COMMANDO,
        }
        unit_col = _col_map.get(unit_name, C_ASSASSIN)
        pygame.draw.circle(surf, (30, 20, 50), (icon_cx, icon_cy), 36)
        pygame.draw.circle(surf, unit_col, (icon_cx, icon_cy), 30)
        pygame.draw.circle(surf, (255, 255, 255), (icon_cx, icon_cy), 30, 2)

    # Unit name — bigger font
    name_f = pygame.font.SysFont("consolas", 17, bold=True)
    ns = name_f.render(unit_name, True, C_WHITE)
    surf.blit(ns, ns.get_rect(center=(cx, cy + 56)))

    cost_map = {"Assassin": 300, "Accelerator": 5000, "Frostcelerator": 3500, "Freezer": 400,
                "Lifestealer": 400, "Archer": 400, "Red Ball": 1000, "Farm": 250,
                "Frost Blaster": 800, "Sledger": 950, "Gladiator": 500,
                "Toxic Gunner": 525, "Slasher": 1700, "Golden Cowboy": 550,
                "Hallow Punk": 300, "Spotlight Tech": 3250,
                "Snowballer": 400, "Commander": 650, "Commando": 900}
    cost = cost_map.get(unit_name)
    if cost:
        ico_m = load_icon("money_ico", 18)
        cost_str = f" {cost}"
        cost_f = pygame.font.SysFont("consolas", 16, bold=True)
        cs = cost_f.render(cost_str, True, C_GOLD)
        if ico_m:
            total_w = ico_m.get_width() + cs.get_width()
            bx2 = cx - total_w // 2
            by2 = cy + 80 - cs.get_height() // 2
            surf.blit(ico_m, (bx2, by2 + (cs.get_height() - ico_m.get_height()) // 2))
            surf.blit(cs, (bx2 + ico_m.get_width(), by2))
        else:
            cs2 = cost_f.render(f"${cost}", True, C_GOLD)
            surf.blit(cs2, cs2.get_rect(center=(cx, cy + 80)))


# ── Difficulty Menu ─────────────────────────────────────────────────────────────
class MapSelectMenu:
    """Shown after difficulty selection — lets player pick a map."""

    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        cw, ch = 220, 260
        cx = SCREEN_W // 2
        gap = 60
        self.card_straight = pygame.Rect(cx - cw - gap//2, 200, cw, ch)
        self.card_zigzag   = pygame.Rect(cx + gap//2,       200, cw, ch)
        btn_w, btn_h = 220, 48
        self.btn_back = pygame.Rect(cx - btn_w//2, 200 + ch + 24, btn_w, btn_h)
        self.action = None

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
                    if self.card_straight.collidepoint(pos): self.action = "straight"
                    if self.card_zigzag.collidepoint(pos):   self.action = "zigzag"
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
        pr = pygame.Rect(rect.x + 16, rect.y + 16, rect.w - 32, rect.h - 70)
        pygame.draw.rect(surf, (18, 22, 30), pr, border_radius=6)
        pygame.draw.rect(surf, (50, 60, 80), pr, 1, border_radius=6)

        ph = 6  # path half-width in preview
        sx = pr.x; ex = pr.right
        sy = pr.y; ey = pr.bottom
        pw = pr.w; ph_h = pr.h

        if map_type == "straight":
            py = pr.centery
            pygame.draw.rect(surf, C_PATH, (pr.x, py-ph, pr.w, ph*2))
            pygame.draw.rect(surf, (60,20,20), (pr.x, py-ph, 8, ph*2))
            pygame.draw.rect(surf, (20,60,20), (pr.right-8, py-ph, 8, ph*2))
        else:
            # Scaled zigzag preview matching exact path
            pts = [(-45,290),(400,290),(400,846),(766,846),(766,106),(1167,106),(1167,846),(1920,846)]
            mnx, mxx = -45, 1920
            mny, mxy = 80, 880
            def sc(px2, py2):
                nx = pr.x + int((px2 - mnx) / (mxx - mnx) * pr.w)
                ny = pr.y + int((py2 - mny) / (mxy - mny) * ph_h)
                return nx, ny
            for i in range(len(pts)-1):
                ax,ay = pts[i]; bx2,by2 = pts[i+1]
                pax,pay = sc(ax,ay); pbx,pby = sc(bx2,by2)
                if ax==bx2:  # vertical
                    rx = min(pax,pbx)-ph; ry = min(pay,pby)
                    pygame.draw.rect(surf, C_PATH, (rx, ry, ph*2, abs(pby-pay)+1))
                else:  # horizontal
                    rx = min(pax,pbx); ry = min(pay,pby)-ph
                    pygame.draw.rect(surf, C_PATH, (rx, ry, abs(pbx-pax)+1, ph*2))
            s_pos = sc(-45, 290)
            e_pos = sc(1920, 846)
            pygame.draw.rect(surf, (60,20,20), (s_pos[0], s_pos[1]-ph, 8, ph*2))
            pygame.draw.rect(surf, (20,60,20), (e_pos[0]-8, e_pos[1]-ph, 8, ph*2))

        # Label
        label = "THE BRIDGE" if map_type == "straight" else "S-TURN"
        lf = pygame.font.SysFont("consolas", 18, bold=True)
        ls = lf.render(label, True, C_WHITE if hover or selected else (160, 170, 200))
        surf.blit(ls, ls.get_rect(center=(rect.centerx, rect.bottom - 36)))
        desc = "The Bridge" if map_type == "straight" else "S-Turn"
        df = pygame.font.SysFont("segoeui", 14)
        ds = df.render(desc, True, (120, 140, 170))
        surf.blit(ds, ds.get_rect(center=(rect.centerx, rect.bottom - 18)))

    def _draw(self):
        self.screen.fill(C_BG)
        random.seed(55)
        for _ in range(150):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.1 + sx * 0.01)) * 160 + 60)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)
        random.seed()

        tf = pygame.font.SysFont("consolas", 36, bold=True)
        ts = tf.render("SELECT MAP", True, (120, 200, 255))
        self.screen.blit(ts, ts.get_rect(center=(SCREEN_W//2, 150)))

        mx, my = pygame.mouse.get_pos()
        cur = game_core.CURRENT_MAP
        self._draw_map_preview(self.screen, self.card_straight, "straight",
                               self.card_straight.collidepoint(mx,my), cur=="straight")
        self._draw_map_preview(self.screen, self.card_zigzag, "zigzag",
                               self.card_zigzag.collidepoint(mx,my), cur=="zigzag")

        hov_back = self.btn_back.collidepoint(mx, my)
        bg = (60, 80, 140) if hov_back else (35, 42, 65)
        brd = (120, 160, 255) if hov_back else (70, 90, 140)
        pygame.draw.rect(self.screen, bg, self.btn_back, border_radius=10)
        pygame.draw.rect(self.screen, brd, self.btn_back, 2, border_radius=10)
        txt(self.screen, "← BACK", self.btn_back.center, C_WHITE, font_xl, center=True)


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
        ts = title_f.render("ВНИМАНИЕ", True, (pulse_r, 40, 40))
        surf.blit(ts, ts.get_rect(center=(SCREEN_W // 2, 320)))

        # Warning lines
        lines = [
            ("Продолжить?", (160, 200, 255)),
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
            (self.btn_continue, "Продолжить", (40, 160, 255)),
            (self.btn_back,     "Назад",      (180, 50,  50)),
        ]:
            hov = btn.collidepoint(mx, my)
            bg  = tuple(min(255, c + 30) for c in accent) if hov else tuple(c // 2 for c in accent)
            pygame.draw.rect(surf, bg,    btn, border_radius=10)
            pygame.draw.rect(surf, accent, btn, 2, border_radius=10)
            bf = pygame.font.SysFont("segoeui", 24, bold=True)
            bs = bf.render(label, True, C_WHITE)
            surf.blit(bs, bs.get_rect(center=btn.center))


class DifficultyMenu:
    def __init__(self, screen, save_data=None):
        self.screen = screen
        self.t = 0.0
        self.action = None
        self.save_data = save_data or {}
        card_w, card_h = 180, 240
        cx = SCREEN_W // 2
        # 4 cards: Easy, Fallen, Frosty, Sandbox
        total_cards_w = card_w * 4 + 40 * 3
        x0 = cx - total_cards_w // 2
        self.card_easy    = pygame.Rect(x0,                    220, card_w, card_h)
        self.card_fallen  = pygame.Rect(x0 + card_w + 40,     220, card_w, card_h)
        self.card_frosty  = pygame.Rect(x0 + card_w*2 + 80,   220, card_w, card_h)
        self.card_sandbox = pygame.Rect(x0 + card_w*3 + 120,  220, card_w, card_h)

        btn_w, btn_h = 260, 54
        self.btn_back = pygame.Rect(cx - btn_w//2, 220 + card_h + 20, btn_w, btn_h)

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
                    if self.card_easy.collidepoint(pos):    self.action = "play_easy"
                    if self.card_fallen.collidepoint(pos):  self.action = "play_fallen"
                    if self.card_frosty.collidepoint(pos):  self.action = "play_frosty"
                    if self.card_sandbox.collidepoint(pos): self.action = "play_sandbox"
                    if self.btn_back.collidepoint(pos):     self.action = "back"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw_mode_card(self, rect, label, ico_name, hover,
                        bg_col, bg_hov, border_col, border_hov, label_bg,
                        fill_icon=False):
        bg = bg_hov if hover else bg_col
        brd = border_hov if hover else border_col
        body_h = rect.h - 52
        body_rect = pygame.Rect(rect.x, rect.y, rect.w, body_h)
        pygame.draw.rect(self.screen, bg, body_rect,
                         border_top_left_radius=14, border_top_right_radius=14)

        if fill_icon:
            path = os.path.join(_ICON_DIR, f"{ico_name}.png")
            try:
                raw = pygame.image.load(path).convert_alpha()
                iw, ih = raw.get_size()
                scale = max(body_rect.w / iw, body_rect.h / ih)
                nw, nh = int(iw * scale), int(ih * scale)
                scaled = pygame.transform.smoothscale(raw, (nw, nh))
                ox = (nw - body_rect.w) // 2
                oy = (nh - body_rect.h) // 2
                clip = scaled.subsurface((ox, oy, body_rect.w, body_rect.h))
                mask_surf = pygame.Surface((body_rect.w, body_rect.h), pygame.SRCALPHA)
                pygame.draw.rect(mask_surf, (255,255,255,255), (0,0,body_rect.w,body_rect.h),
                                 border_top_left_radius=14, border_top_right_radius=14)
                result = clip.copy()
                result.blit(mask_surf, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
                self.screen.blit(result, (body_rect.x, body_rect.y))
            except Exception:
                ico = load_icon(ico_name, min(body_rect.w, body_rect.h) - 8)
                if ico:
                    self.screen.blit(ico, (rect.x + (rect.w - ico.get_width()) // 2,
                                           rect.y + (body_h - ico.get_height()) // 2))
        else:
            ico = load_icon(ico_name, 80)
            if ico:
                ico_x = rect.x + (rect.w - 80) // 2
                ico_y = rect.y + (body_h - 80) // 2
                self.screen.blit(ico, (ico_x, ico_y))
            else:
                pygame.draw.circle(self.screen, brd,
                                   (rect.centerx, rect.y + body_h//2), 36)

        label_rect = pygame.Rect(rect.x, rect.y + body_h, rect.w, 52)
        pygame.draw.rect(self.screen, label_bg, label_rect,
                         border_bottom_left_radius=14, border_bottom_right_radius=14)
        pygame.draw.rect(self.screen, brd, rect, 3, border_radius=14)
        lbl_s = font_xl.render(label, True, C_WHITE)
        self.screen.blit(lbl_s, lbl_s.get_rect(center=(rect.centerx, label_rect.centery)))

    def _draw(self):
        self.screen.fill(C_BG)
        random.seed(77)
        for _ in range(200):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.3 + sx * 0.01)) * 180 + 60)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)
        random.seed()

        title_font = pygame.font.SysFont("consolas", 40, bold=True)
        ts = title_font.render("SELECT MODE", True, (120, 180, 255))
        self.screen.blit(ts, ts.get_rect(center=(SCREEN_W//2, 160)))

        mx, my = pygame.mouse.get_pos()
        hov_easy    = self.card_easy.collidepoint(mx, my)
        hov_fallen  = self.card_fallen.collidepoint(mx, my)
        hov_frosty  = self.card_frosty.collidepoint(mx, my)
        hov_sandbox = self.card_sandbox.collidepoint(mx, my)

        self._draw_mode_card(
            self.card_easy, "EASY", "easy_ico", hov_easy,
            bg_col=(28, 68, 38), bg_hov=(38, 92, 50),
            border_col=(60, 140, 70), border_hov=(90, 210, 110),
            label_bg=(22, 55, 30), fill_icon=True
        )
        self._draw_mode_card(
            self.card_fallen, "FALLEN", "fallen_ico", hov_fallen,
            bg_col=(55, 20, 80), bg_hov=(80, 30, 120),
            border_col=(140, 60, 200), border_hov=(200, 100, 255),
            label_bg=(42, 14, 62), fill_icon=True
        )
        self._draw_mode_card(
            self.card_frosty, "FROSTY", "frosty_ico", hov_frosty,
            bg_col=(18, 55, 100), bg_hov=(28, 78, 140),
            border_col=(60, 160, 240), border_hov=(120, 210, 255),
            label_bg=(14, 42, 80), fill_icon=True
        )
        self._draw_mode_card(
            self.card_sandbox, "SANDBOX", "sandbox_ico", hov_sandbox,
            bg_col=(80, 68, 42), bg_hov=(108, 92, 56),
            border_col=(160, 130, 70), border_hov=(220, 185, 100),
            label_bg=(65, 55, 32), fill_icon=True
        )


        hov_back = self.btn_back.collidepoint(mx, my)
        bg = (60, 80, 140) if hov_back else (35, 42, 65)
        brd = (120, 160, 255) if hov_back else (70, 90, 140)
        pygame.draw.rect(self.screen, bg, self.btn_back, border_radius=10)
        pygame.draw.rect(self.screen, brd, self.btn_back, 2, border_radius=10)
        txt(self.screen, "← BACK", self.btn_back.center, C_WHITE, font_xl, center=True)



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
            ("Автор игры", (120, 140, 180), False),
            ("zigres", (255, 255, 255), True),
            ("", None, False),
            ("Автор юнита  «Freezer»", (120, 140, 180), False),
            ("xw5yt / leykio", (80, 200, 255), True),
            ("", None, False),
            ("Вдохновлено игрой", (120, 140, 180), False),
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
        bs = bf.render("← НАЗАД", True, C_WHITE)
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
        lbl = lf.render("ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО", True, (*border_col,))
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
        txt(surf, "← НАЗАД", self.btn_back.center, C_WHITE, font_md, center=True)

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
                cf2 = pygame.font.SysFont("segoeui", 20, bold=True)
                cs2 = cf2.render("✓", True, C_WHITE)
                surf.blit(cs2, cs2.get_rect(center=(icon_x, icon_y)))
            else:
                pygame.draw.circle(surf, (50, 55, 70), (icon_x, icon_y), 18)
                lf2 = pygame.font.SysFont("segoeui", 18)
                ls2 = lf2.render("🔒", True, (90, 95, 110))
                surf.blit(ls2, ls2.get_rect(center=(icon_x, icon_y)))

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
        cs3 = cf3.render(f"{done_ach}/{total_ach} разблокировано", True,
                         C_GOLD if done_ach == total_ach else (140, 145, 170))
        surf.blit(cs3, cs3.get_rect(bottomright=(SCREEN_W - 16, SCREEN_H - 10)))


# ── Global settings ──────────────────────────────────────────────────────────
SETTINGS = {
    "music_volume": 0.7,
    "music_muted": False,
    "colored_range": False,
}

def _apply_audio_settings():
    try:
        vol = 0.0 if SETTINGS["music_muted"] else SETTINGS["music_volume"]
        pygame.mixer.music.set_volume(vol)
    except Exception: pass

_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")

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

# ── Patch Unit.draw_range for colored range rings ─────────────────────────────
def _patched_draw_range(self, surf):
    r = int(self.range_tiles * TILE)
    if r <= 0: return
    col = self.COLOR if SETTINGS.get("colored_range", False) else (255, 255, 255)
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*col, 22), (r, r), r)
    pygame.draw.circle(s, (*col, 60), (r, r), r, 2)
    surf.blit(s, (int(self.px)-r, int(self.py)-r))
Unit.draw_range = _patched_draw_range


class SettingsScreen:
    def __init__(self, screen):
        self.screen = screen; self.t = 0.0; self.running = True
        cx = SCREEN_W // 2
        self.btn_back = pygame.Rect(cx - 130, SCREEN_H - 90, 260, 50)
        self._drag_vol = False

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(60) / 1000.0; self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: self.running = False
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1: self._handle_click(ev.pos)
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1: self._drag_vol = False
                if ev.type == pygame.MOUSEMOTION and self._drag_vol: self._set_vol_from_x(ev.pos[0])
            self._draw(); pygame.display.flip()
        save_settings()

    def _vol_bar_rect(self): return pygame.Rect(SCREEN_W//2 - 200, 320, 400, 18)

    def _set_vol_from_x(self, mx):
        bar = self._vol_bar_rect()
        SETTINGS["music_volume"] = round(max(0.0, min(1.0, (mx-bar.x)/bar.w)), 2)
        if not SETTINGS["music_muted"]: _apply_audio_settings()

    def _handle_click(self, pos):
        cx = SCREEN_W // 2
        if self.btn_back.collidepoint(pos): self.running = False; return
        if pygame.Rect(cx-110, 380, 220, 44).collidepoint(pos):
            SETTINGS["music_muted"] = not SETTINGS["music_muted"]; _apply_audio_settings(); return
        if pygame.Rect(cx-110, 450, 220, 44).collidepoint(pos):
            SETTINGS["colored_range"] = not SETTINGS["colored_range"]; return
        bar = self._vol_bar_rect()
        if pygame.Rect(bar.x, bar.y-10, bar.w, bar.h+20).collidepoint(pos):
            self._drag_vol = True; self._set_vol_from_x(pos[0])

    def _draw_toggle(self, surf, rect, label, active):
        pygame.draw.rect(surf, (50,160,80) if active else (60,60,80), rect, border_radius=10)
        pygame.draw.rect(surf, (80,220,100) if active else (90,90,120), rect, 2, border_radius=10)
        f = pygame.font.SysFont("segoeui", 20, bold=True)
        s = f.render(f"{label}: {'ВКЛ' if active else 'ВЫКЛ'}", True, (255,255,255))
        surf.blit(s, s.get_rect(center=rect.center))

    def _draw(self):
        surf = self.screen; surf.fill(C_BG); cx = SCREEN_W // 2
        random.seed(44)
        for _ in range(160):
            sx=random.randint(0,SCREEN_W); sy=random.randint(0,SCREEN_H)
            br=int(abs(math.sin(self.t+sx*0.012))*150+50)
            pygame.draw.circle(surf,(br,br,br),(sx,sy),1)
        random.seed()
        pygame.draw.rect(surf, C_PANEL, (0,0,SCREEN_W,70))
        pygame.draw.line(surf, C_BORDER, (0,70),(SCREEN_W,70),2)
        hs = pygame.font.SysFont("segoeui",36,bold=True).render("НАСТРОЙКИ",True,(180,200,255))
        surf.blit(hs, hs.get_rect(center=(cx,35)))
        vl = pygame.font.SysFont("segoeui",22,bold=True).render("Громкость музыки",True,(200,210,240))
        surf.blit(vl, vl.get_rect(center=(cx,285)))
        bar = self._vol_bar_rect()
        pygame.draw.rect(surf,(40,45,65),bar,border_radius=8)
        fw = int(bar.w*SETTINGS["music_volume"])
        if fw > 0:
            pygame.draw.rect(surf,(60,160,255) if not SETTINGS["music_muted"] else (80,80,80),
                             pygame.Rect(bar.x,bar.y,fw,bar.h),border_radius=8)
        pygame.draw.rect(surf,C_BORDER,bar,2,border_radius=8)
        kx = bar.x + fw
        pygame.draw.circle(surf,(200,220,255),(kx,bar.centery),12)
        pygame.draw.circle(surf,C_BORDER,(kx,bar.centery),12,2)
        ps = pygame.font.SysFont("consolas",16,bold=True).render(f"{int(SETTINGS['music_volume']*100)}%",True,C_GOLD)
        surf.blit(ps, ps.get_rect(center=(cx,bar.bottom+18)))
        self._draw_toggle(surf, pygame.Rect(cx-110,380,220,44), "Мут", SETTINGS["music_muted"])
        self._draw_toggle(surf, pygame.Rect(cx-110,450,220,44), "Цветной рейндж", SETTINGS["colored_range"])
        mx,my=pygame.mouse.get_pos(); hov=self.btn_back.collidepoint(mx,my)
        pygame.draw.rect(surf,(80,50,50) if hov else (50,35,35),self.btn_back,border_radius=10)
        pygame.draw.rect(surf,C_BORDER,self.btn_back,2,border_radius=10)
        bs = pygame.font.SysFont("segoeui",24,bold=True).render("← НАЗАД",True,C_WHITE)
        surf.blit(bs, bs.get_rect(center=self.btn_back.center))


# ── Main Menu ───────────────────────────────────────────────────────────────────
class MainMenu:
    def __init__(self, screen, save_data=None):
        self.screen = screen
        self.t = 0.0
        self.action = None
        self.save_data = save_data or {}
        btn_w, btn_h = 260, 54
        cx = SCREEN_W // 2
        self.btn_play    = pygame.Rect(cx - btn_w//2, 300, btn_w, btn_h)
        self.btn_loadout = pygame.Rect(cx - btn_w//2, 370, btn_w, btn_h)
        self.btn_quit    = pygame.Rect(cx - btn_w//2, 440, btn_w, btn_h)

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
                                if FrostyWarningScreen(self.screen).run() == "continue":
                                    game_core.CURRENT_MAP = "frosty"
                                    self.action = diff
                            else:
                                map_choice = MapSelectMenu(self.screen).run()
                                if map_choice != "back":
                                    game_core.CURRENT_MAP = map_choice
                                    self.action = diff
                    if self.btn_loadout.collidepoint(pos): self.action = "loadout"
                    if self.btn_quit.collidepoint(pos):    self.action = "quit"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw_btn(self, rect, label, hover):
        col = (60, 80, 140) if hover else (35, 42, 65)
        border = (120, 160, 255) if hover else (70, 90, 140)
        pygame.draw.rect(self.screen, col, rect, border_radius=10)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=10)
        txt(self.screen, label, rect.center, C_WHITE, font_xl, center=True)

    def _draw(self):
        self.screen.fill(C_BG)
        random.seed(77)
        for _ in range(200):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.3 + sx * 0.01)) * 180 + 60)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)
        random.seed()

        title_font = pygame.font.SysFont("consolas", 52, bold=True)
        glow_alpha = int(abs(math.sin(self.t * 1.2)) * 80 + 80)
        glow_s = pygame.Surface((600, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_s, (80, 120, 255, glow_alpha), (0, 0, 600, 80))
        self.screen.blit(glow_s, (SCREEN_W//2 - 300, 130))

        title_s = title_font.render("TOWER DEFENSE", True, (120, 180, 255))
        self.screen.blit(title_s, title_s.get_rect(center=(SCREEN_W//2, 170)))

        mx, my = pygame.mouse.get_pos()
        self._draw_btn(self.btn_play,    "▶  PLAY",    self.btn_play.collidepoint(mx, my))
        self._draw_btn(self.btn_loadout, "⚙  LOADOUT", self.btn_loadout.collidepoint(mx, my))
        self._draw_btn(self.btn_quit,    "✕  QUIT",    self.btn_quit.collidepoint(mx, my))

        ver = font_sm.render("v1.0", True, (50, 60, 80))
        self.screen.blit(ver, (10, SCREEN_H - 20))

        # Coins counter top-right
        coins = self.save_data.get("coins", 0)
        ico_m = load_icon("coin_ico", 30)
        coin_s = font_lg.render(f" {coins}", True, C_GOLD)
        total_cw = (ico_m.get_width() if ico_m else 0) + coin_s.get_width()
        cx2 = SCREEN_W - 14 - total_cw
        cy2 = 14
        if ico_m:
            self.screen.blit(ico_m, (cx2, cy2 + (coin_s.get_height() - ico_m.get_height())//2))
            self.screen.blit(coin_s, (cx2 + ico_m.get_width(), cy2))
        else:
            txt(self.screen, f"Coins: {coins}", (SCREEN_W-14, 14), C_GOLD, font_lg, right=True)


# ── Loadout Screen ──────────────────────────────────────────────────────────────
ALL_UNITS_POOL = [
    {"name": "Assassin",       "rarity": "starter"},
    {"name": "Accelerator",    "rarity": "epic"},
    {"name": "Frostcelerator", "rarity": "exclusive"},
    {"name": "Lifestealer",    "rarity": "starter"},
    {"name": "Archer",         "rarity": "epic"},
    {"name": "Red Ball",       "rarity": "rare"},
    {"name": "Farm",           "rarity": "common"},
    {"name": "Freezer",        "rarity": "common"},
    {"name": "Frost Blaster",  "rarity": "rare"},
    {"name": "Sledger",        "rarity": "epic"},
    {"name": "Gladiator",      "rarity": "epic"},
    {"name": "Toxic Gunner",   "rarity": "rare"},
    {"name": "Slasher",        "rarity": "epic"},
    {"name": "Golden Cowboy",  "rarity": "epic"},
    {"name": "Hallow Punk",    "rarity": "rare"},
    {"name": "Spotlight Tech", "rarity": "epic"},
    {"name": "Snowballer",     "rarity": "rare"},
    {"name": "Commander",      "rarity": "epic"},
    {"name": "Commando",       "rarity": "rare"},
]

# Coin cost to unlock units (None = not purchasable / exclusive)
UNIT_SHOP_PRICES = {
    "Assassin":       None,
    "Archer":         1000,
    "Lifestealer":    450,
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
    "Golden Cowboy":  3500,
    "Hallow Punk":    600,
    "Spotlight Tech": 5000,
    "Snowballer":     700,
    "Commander":      2000,
    "Commando":       800,
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

    _RARITY_ORDER = ["starter", "common", "rare", "epic", "exclusive"]
    _RARITY_HDR_COL = {
        "starter":   (180, 180, 190),
        "common":    ( 80, 210,  80),
        "rare":      ( 80, 150, 255),
        "epic":      (200, 100, 255),
        "exclusive": (255,  60,  60),
    }
    _RARITY_HDR_LINE = {
        "starter":   (100, 100, 110),
        "common":    ( 40, 120,  40),
        "rare":      ( 40,  80, 180),
        "epic":      (120,  40, 180),
        "exclusive": (160,  20,  20),
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

    # ── helpers ──────────────────────────────────────────────────────────────
    def _owned_units(self):
        owned = self.save_data.get("owned_units", ["Assassin"])
        if self.save_data.get("frostcelerator_unlocked"):
            if "Frostcelerator" not in owned:
                owned = list(owned) + ["Frostcelerator"]
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

        for card_r, rarity, idx in self._card_hits:
            if card_r.collidepoint(pos):
                key = (rarity, idx)
                self.selected = None if self.selected == key else key
                return

        for si, sr in enumerate(self._slot_rects(left_w)):
            if sr.collidepoint(pos):
                if self.selected is not None:
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
                        if uname == "Commander":
                            self._show_msg("Sandbox only!")
                            self.selected = None; return
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

        surf = self.screen
        surf.fill(C_BG)

        # ── Top bar ──────────────────────────────────────────────────────────
        pygame.draw.rect(surf, C_PANEL,  (0, 0, SCREEN_W, 70))
        pygame.draw.line(surf, C_BORDER, (0, 70), (SCREEN_W, 70), 2)
        txt(surf, "LOADOUT", (SCREEN_W // 2, 35), C_CYAN, font_xl, center=True)

        mx, my = pygame.mouse.get_pos()

        # Coins
        coins  = self.save_data.get("coins", 0)
        ico_c  = load_icon("coin_ico", 22)
        coin_s = font_lg.render(f" {coins}", True, C_GOLD)
        tcw    = (ico_c.get_width() if ico_c else 0) + coin_s.get_width()
        ccx    = SCREEN_W - 14 - tcw
        if ico_c:
            surf.blit(ico_c,  (ccx, 18 + (coin_s.get_height() - ico_c.get_height()) // 2))
            surf.blit(coin_s, (ccx + ico_c.get_width(), 18))
        else:
            txt(surf, f"Coins: {coins}", (SCREEN_W - 14, 18), C_GOLD, font_lg, right=True)

        # Back button
        hov_b = self.btn_back.collidepoint(mx, my)
        pygame.draw.rect(surf, (110,50,50) if hov_b else (80,40,40), self.btn_back, border_radius=8)
        pygame.draw.rect(surf, C_BORDER, self.btn_back, 2, border_radius=8)
        txt(surf, "← BACK", self.btn_back.center, C_WHITE, font_md, center=True)

        # ── Vertical divider ─────────────────────────────────────────────────
        pygame.draw.line(surf, C_BORDER, (panel_x, TOP), (panel_x, SCREEN_H), 2)

        # ── LEFT zone — background + loadout ────────────────────────────────
        # Subtle background tint
        left_bg = pygame.Surface((left_w, SCREEN_H - TOP), pygame.SRCALPHA)
        left_bg.fill((12, 15, 24, 180))
        surf.blit(left_bg, (0, TOP))

        # "Your loadout" label above slots
        slot_rects = self._slot_rects(left_w)
        lbl_y = slot_rects[0].top - 28

        _col_map_slot = {
            "Assassin": C_ASSASSIN,        "Lifestealer": C_LIFESTEALER,
            "Archer":   C_ARCHER,          "Red Ball":    C_REDBALL,
            "Farm":     C_FARM,            "Freezer":     C_FREEZER,
            "Frost Blaster": C_FROSTBLASTER, "Sledger":   C_SLEDGER,
            "Gladiator": C_GLADIATOR,      "Toxic Gunner": C_TOXICGUN,
            "Slasher":  C_SLASHER,         "Golden Cowboy": C_GCOWBOY,
            "Hallow Punk": C_HALLOWPUNK,   "Spotlight Tech": C_SPOTLIGHT,
        }

        for si, sr in enumerate(slot_rects):
            uname = self.loadout[si]
            hov3  = sr.collidepoint(mx, my)
            sel_slot = (self.selected is not None)   # highlight when selecting
            if sel_slot and not uname:
                bg_col = (35, 55, 80)
            elif hov3:
                bg_col = (50, 60, 90)
            else:
                bg_col = C_SLOT_BG
            pygame.draw.rect(surf, bg_col, sr, border_radius=8)
            bd_col = (80, 130, 200) if (sel_slot and not uname) else C_BORDER
            pygame.draw.rect(surf, bd_col, sr, 2, border_radius=8)

            if uname:
                rarity = next((u["rarity"] for u in ALL_UNITS_POOL if u["name"] == uname), "starter")
                rd     = RARITY_DATA[rarity]
                icx, icy = sr.centerx, sr.centery - 10
                if uname == "Accelerator":
                    draw_accel_icon(surf, icx, icy, self.t, size=20)
                elif uname == "Frostcelerator":
                    draw_frost_icon(surf, icx, icy, self.t, size=20)
                elif uname == "xw5yt":
                    draw_xw5yt_icon(surf, icx, icy, self.t, size=20)
                else:
                    uc = _col_map_slot.get(uname, C_ASSASSIN)
                    pygame.draw.circle(surf, (30,20,50), (icx, icy), 22)
                    pygame.draw.circle(surf, uc,         (icx, icy), 18)
                    pygame.draw.circle(surf, rd["border"],(icx, icy), 18, 2)
                txt(surf, uname, (sr.centerx, sr.bottom - 20), C_WHITE, font_sm, center=True)
                rs2 = font_sm.render(rd["label"], True, rd["text_col"])
                surf.blit(rs2, rs2.get_rect(center=(sr.centerx, sr.bottom - 7)))
            else:
                txt(surf, f"SLOT {si+1}", (sr.centerx, sr.centery), (60,70,100), font_sm, center=True)

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
                ls2 = label_f.render(rarity.capitalize(), True, hdr_col)
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

                    if rarity == "exclusive":
                        ls3 = lock_f.render("🔒", True, (200,130,130))
                        surf.blit(ls3, ls3.get_rect(center=(cx2, cy2 + 8)))
                        es  = excl_f.render("EXCLUSIVE", True, (220,65,65))
                        surf.blit(es, es.get_rect(center=(cx2, cy2 + 30)))
                    else:
                        ls3 = lock_f.render("🔒", True, (130,200,130))
                        surf.blit(ls3, ls3.get_rect(center=(cx2, cy2 - 18)))
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
        cw, ch = 300, 220
        cx, cy = SCREEN_W//2, SCREEN_H//2
        self.panel = pygame.Rect(cx - cw//2, cy - ch//2, cw, ch)
        self.btn_resume = pygame.Rect(cx - 110, cy - 30, 220, 50)
        self.btn_menu   = pygame.Rect(cx - 110, cy + 30, 220, 50)

    def draw(self, hayden_eligible=False):
        draw_rect_alpha(self.screen, C_BLACK, (0, 0, SCREEN_W, SCREEN_H), 160)
        draw_rect_alpha(self.screen, (20, 25, 40), self.panel, 240, 12)
        pygame.draw.rect(self.screen, C_BORDER, self.panel, 2, border_radius=12)
        txt(self.screen, "PAUSED", (SCREEN_W//2, self.panel.y + 30), C_CYAN, font_xl, center=True)
        mx, my = pygame.mouse.get_pos()
        for btn, label in [(self.btn_resume, "▶  RESUME"), (self.btn_menu, "⌂  MAIN MENU")]:
            hov = btn.collidepoint(mx, my)
            bg = (60, 80, 130) if hov else (35, 45, 70)
            pygame.draw.rect(self.screen, bg, btn, border_radius=8)
            pygame.draw.rect(self.screen, C_BORDER, btn, 2, border_radius=8)
            txt(self.screen, label, btn.center, C_WHITE, font_lg, center=True)

    def handle_click(self, pos):
        if self.btn_resume.collidepoint(pos): return "resume"
        if self.btn_menu.collidepoint(pos):   return "menu"
        return None


# ── Game ───────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, save_data=None, mode="easy"):
        self.screen=pygame.display.set_mode((SCREEN_W,SCREEN_H))
        pygame.display.set_caption("Tower Defense")
        self.clock=pygame.time.Clock(); self.running=True
        self._elapsed=0.0  # total play time in seconds
        self._end_coin_reward=0  # coins earned this run
        self.player_hp=100; self.player_maxhp=100; self.money=600
        self.enemies=[]; self.units=[]; self.effects=[]
        self.mode=mode
        if mode=="fallen":
            self.wave_mgr=WaveManager(wave_data=FALLEN_WAVE_DATA, max_waves=FALLEN_MAX_WAVES)
            self.player_hp=150; self.player_maxhp=150
        elif mode=="frosty":
            self.wave_mgr=WaveManager(wave_data=FROSTY_WAVE_DATA, max_waves=FROSTY_MAX_WAVES)
            self.player_hp=300; self.player_maxhp=300
            self._frosty_lane=0   # cycles 0-3: which of 4 entry paths next enemy gets
        else:
            self.wave_mgr=WaveManager()
        # Frosty background music state
        self._frosty_bgm_active = False   # True while alternating frostymode/frostymode2 is playing
        self._frosty_bgm_track = 1        # 1 or 2 — which track plays next
        self._frosty_bgm_stopped = False  # True once wave 40 starts (don't restart)
        self.ui=UI()
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
        self._boss_enemy=None; self._wave_leaked=False
        # Fallen mode boss bars: track first appearances
        self._fallen_boss_bars = {}  # class → enemy ref (first ever seen, only in fallen mode from waves)
        # Frosty mode: remember which enemies already got a boss bar (per run)
        self._frosty_bossbar_seen = set()
        self.console=DevConsole()
        self.save_data = save_data or load_save()
        self.paused = False
        self.pause_menu = PauseMenu(self.screen)
        self.return_to_menu = False
        self._hixw5yt_frozen = False   # time stopped, waiting for enemy click
        self._hixw5yt_owner = None     # which Xw5ytUnit triggered it
        # pokaxw5yt ability state
        self._pokaxw5yt_frozen = False
        self._pokaxw5yt_owner = None
        # Frosty wave-40: Frost Spirit music → delayed spawn
        self._frost_spirit_music_timer = None
        self._frost_spirit_spawned = False
        # generic scheduled spawns (for delayed summon abilities)
        self._scheduled_spawns = []  # [{"t":float,"cls":type,"x":float,"y":float,"wp":int,"fp":path|None,"from_wave":bool,"free_kill":bool}]
        # Stubs for attributes removed from singleplayer but still referenced by multiplayer.py
        self._hayden_active = False
        self._hayden_eligible = False
        self._hayden_combo = []
        self._hayden_timer = 0.0
        # hayden_console stub — no-op object so multiplayer.py calls don't crash
        class _NullConsole:
            visible = False
            def update(self, dt): pass
            def draw(self, surf): pass
            def handle_key(self, ev, game): pass
        self.hayden_console = _NullConsole()

        # Achievement manager
        self.ach_mgr = AchievementManager()
        self._wave_coin_accum = 0.0  # fractional coin accumulator for per-wave rewards
        self._last_coin_wave = 0  # last wave number for which profile coins were paid
        # track if easy-mode boss was let through (free_pass ach)
        self._easy_boss_leaked = False
        self._easy_boss_let_through = False  # boss reached end with hp < player hp

        # Apply saved loadout to slot types
        _name_to_cls = {"Assassin": Assassin, "Accelerator": Accelerator,
                        "Frostcelerator": Frostcelerator, "xw5yt": Xw5ytUnit,
                        "Lifestealer": Lifestealer,
                        "Archer": Archer, "Red Ball": RedBall, "Farm": Farm,
                        "Freezer": Freezer, "Frost Blaster": FrostBlaster,
                        "Sledger": Sledger, "Gladiator": Gladiator,
                        "Toxic Gunner": ToxicGunner, "Slasher": Slasher,
                        "Golden Cowboy": GoldenCowboy,
                        "Hallow Punk": HallowPunk,
                        "Spotlight Tech": SpotlightTech,
                        "Snowballer": Snowballer,
                        "Commander": Commander,
                        "Commando": Commando}
        _loadout = self.save_data.get("loadout", ["Assassin", "Accelerator", None, None, None])
        while len(_loadout) < 5: _loadout.append(None)
        self.ui.SLOT_TYPES = [_name_to_cls.get(n) if n else None for n in _loadout]
        # Sandbox mode: empty loadout, infinite money
        if mode == "sandbox":
            self.natural_spawn_stopped = True
            self.player_hp = 10000; self.player_maxhp = 10000
            self.money = 9999999999
            self.ui.SLOT_TYPES = [None, None, None, None, None]
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

    def _give_wave_coins(self, wave_num):
        if self.mode not in ("easy", "fallen", "frosty"): return
        if wave_num <= self._last_coin_wave: return
        waves_done = wave_num - self._last_coin_wave
        self._last_coin_wave = wave_num
        # Easy: 200 total / 20 waves = 10 per wave
        # Fallen: 750 total / 40 waves = 18.75 per wave
        # Frosty: 1500 total / 40 waves = 37.5 per wave
        rate = {"easy": 10.0, "fallen": 18.75, "frosty": 37.5}.get(self.mode, 10.0)
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
        random.seed(42)
        for _ in range(300):
            gx=random.randint(0,SCREEN_W); gy=random.randint(55,SLOT_AREA_Y-10)
            # skip dots on any path segment
            on_any_path=False
            path=get_map_path()
            for pi in range(len(path)-1):
                ax,ay=path[pi]; bx,by=path[pi+1]
                if ax==bx:  # vertical segment
                    mnx,mxx=ax-PATH_H-10,ax+PATH_H+10
                    mny,mxy=min(ay,by)-5,max(ay,by)+5
                    if mnx<=gx<=mxx and mny<=gy<=mxy: on_any_path=True; break
                else:  # horizontal segment
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
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            dt *= getattr(self.ui.admin_panel, '_game_speed', 1.0)

            for ev in pygame.event.get():
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
                if ev.type == pygame.MOUSEWHEEL and self.mode == "sandbox":
                    if self.ui.admin_panel.visible:
                        self.ui.admin_panel.handle_scroll(ev.y); continue
                if self.console.visible:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_F1: self.console.toggle()
                        else: self.console.handle_key(ev, self)
                    continue
                if self.paused:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        action = self.pause_menu.handle_click(ev.pos)
                        if action == "resume": self.paused = False
                        elif action == "menu":
                            self.paused = False; self.running = False
                            self.return_to_menu = True
                            try: pygame.mixer.music.stop()
                            except: pass
                    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                        self.paused = False
                    continue
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if not self.paused: self.paused = True
                    if ev.key == pygame.K_F1: self.console.toggle()
                    if ev.key == pygame.K_e and self.ui.open_unit:
                        u = self.ui.open_unit; cost = u.upgrade_cost()
                        if cost and self.money >= cost: u.upgrade(); self.money -= cost
                        elif cost: self.ui.show_msg("Not enough money!")
                        else: self.ui.show_msg("Max level!")
                    if ev.key == pygame.K_x and self.ui.open_unit:
                        u = self.ui.open_unit
                        self.money += self.ui._sell_value(u)
                    if ev.key == pygame.K_f:
                        # Activate ability of open_unit, or first ready ability
                        activated = False
                        target = self.ui.open_unit
                        if target is None:
                            # Find first unit with ready ability
                            for _u in self.units:
                                if _u.ability and _u.ability.ready():
                                    target = _u; break
                        if target:
                            if target.ability and target.ability.ready():
                                target.ability.activate(self.enemies, self.effects)
                                activated = True
                            elif not activated:
                                ab2 = getattr(target, 'ability2', None)
                                if ab2 and ab2.ready():
                                    ab2.activate(self.enemies, self.effects)
                        self.units.remove(u); self.ui.open_unit = None
                    slot_keys = {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2,pygame.K_4:3,pygame.K_5:4}
                    if ev.key in slot_keys and not self.console.visible:
                        idx = slot_keys[ev.key]; UType = self.ui.SLOT_TYPES[idx]
                        if UType is None: self.ui.show_msg("Coming soon!")
                        elif self.money < UType.PLACE_COST: self.ui.show_msg("Not enough money!")
                        else:
                            mx2, my2 = pygame.mouse.get_pos()
                            self.ui.selected_slot = idx; self.ui.drag_unit = UType(mx2, my2)
                if self.game_over or self.win:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        if self._end_btn.collidepoint(ev.pos):
                            self.running = False; self.return_to_menu = True
                            try: pygame.mixer.music.stop()
                            except: pass
                elif not self.game_over:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        delta = self.ui.handle_click(ev.pos, self.units, self.money,
                                                     self.effects, self.enemies,
                                                     self.wave_mgr.wave, self.save_data, self.mode)
                        self.money += delta
                        if self._hixw5yt_frozen:
                            for e in self.enemies:
                                if e.alive and dist((e.x,e.y),ev.pos) <= e.radius+8:
                                    e.alive = False; self._hixw5yt_frozen = False
                                    if self._hixw5yt_owner:
                                        self._hixw5yt_owner._hixw5yt_active = False
                                        self._hixw5yt_owner = None
                                    break
                        if self._pokaxw5yt_frozen:
                            for e in self.enemies:
                                if e.alive and dist((e.x,e.y),ev.pos) <= e.radius+8:
                                    e.alive = False; self._pokaxw5yt_frozen = False
                                    if self._pokaxw5yt_owner:
                                        self._pokaxw5yt_owner._pokaxw5yt_active = False
                                        self._pokaxw5yt_owner = None
                                    break
                    if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                        delta = self.ui.handle_release(ev.pos, self.units, self.money)
                        self.money += delta

            self._elapsed += dt
            prev_wave = self.wave_mgr.wave
            if not self.paused:
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
                    self._wave_leaked=False
                    # Wave just advanced — immediately pay coins for the completed wave
                    self._give_wave_coins(prev_wave)
    
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
    
                # Wave 40 in frosty mode: play frostspirit.mp3 → spawn Frost Spirit after 28s
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
    
                # hixw5yt: check if any Xw5ytUnit just activated the ability
                if not self._hixw5yt_frozen:
                    for u in self.units:
                        if isinstance(u, Xw5ytUnit) and u._hixw5yt_active:
                            self._hixw5yt_frozen = True
                            self._hixw5yt_owner = u
                            break
    
                # pokaxw5yt: check if any Xw5ytUnit just activated ability2
                if not self._pokaxw5yt_frozen:
                    for u in self.units:
                        if isinstance(u, Xw5ytUnit) and u._pokaxw5yt_active:
                            self._pokaxw5yt_frozen = True
                            self._pokaxw5yt_owner = u
                            break
    
                dead_reached=[]
                for e in self.enemies:
                    if not e.alive: continue
                    if self._hixw5yt_frozen: continue  # time stopped
                    # Reversed enemy: walks backward and deals collision damage
                    if getattr(e,'_reversed',False):
                        e.x -= e.speed * dt * 1.5
                        e._bob += dt * 4
                        if e.x < -60:
                            e.alive = False; continue
                        # Collide with other enemies
                        for other in self.enemies:
                            if other is e or not other.alive: continue
                            if getattr(other,'_reversed',False): continue
                            if dist((e.x,e.y),(other.x,other.y)) < e.radius + other.radius + 2:
                                dmg = min(e.hp, other.hp)
                                other.take_damage(dmg)
                                e.hp -= dmg
                                if not other.alive and not getattr(other,'_reward_paid',False) and not getattr(other,'free_kill',False):
                                    other._reward_paid=True
                                    if self.mode != "easy":
                                        self.money+=other.KILL_REWARD
                                        self.effects.append(FloatingText(other.x,other.y-other.radius-10,f"+{other.KILL_REWARD}"))
                                if e.hp <= 0:
                                    e.alive = False; break
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
                if dead_reached: self._wave_leaked=True
                if self.player_hp<=0 and dead_reached:
                    self.game_over=True
                    # ── Achievement: Жертва Короля ─ lose to FallenKing at wave 40 in Fallen
                    if self.mode=="fallen" and self.wave_mgr.wave==40:
                        if any(isinstance(e,FallenKing)
                               for e in dead_reached):
                            self.ach_mgr.try_grant("king_victim")
                    try:
                        pygame.mixer.music.set_endevent(0)
                        pygame.mixer.music.stop()
                    except: pass
    
                # Kill rewards: give money + floating text for freshly killed enemies
                for e in self.enemies:
                    if not e.alive and not getattr(e,'_reward_paid',False) and not getattr(e,'free_kill',False):
                        e._reward_paid=True
                        reward=e.KILL_REWARD
                        if reward>0 and self.mode != "easy":
                            self.money+=reward
                            self.effects.append(FloatingText(e.x, e.y-e.radius-10, f"+{reward}"))
    
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
                            self.effects.append(FloatingText(fs.x, fs.y-fs.radius-18, f"+{amt}"))
    
                _x5k = getattr(self,"_x5000_dmg",False)
                for u in self.units:
                    # Stun: frozen by FallenKing sword
                    if getattr(u,'_stun_timer',0)>0:
                        u._stun_timer-=dt
                        if u._stun_timer<=0: u._stun_timer=0
                        continue  # skip update while stunned
                    # Freeze during ceremony or hixw5yt
                    if self._ceremony_phase not in (None,'done'):
                        continue
                    if self._hixw5yt_frozen:
                        continue
                    # Give xw5yt chiter ability access to unit list
                    if isinstance(u, Xw5ytUnit) and u.ability3:
                        u.ability3.owner._game_units_ref = self.units
                    # Handle chiter boost expiry
                    boost=getattr(u,'_chiter_boost',0)
                    if boost>0:
                        u._chiter_boost=boost-dt
                        if u._chiter_boost<=0:
                            u._chiter_boost=0
                            u.firerate=getattr(u,'_chiter_old_fr',u.firerate)
                    if _x5k:
                        _orig_dmg = u.damage
                        u.damage = u.damage * 5000
                    u.update(dt,self.enemies,self.effects,self.money)
                    if _x5k:
                        u.damage = _orig_dmg
                # Collect Lifestealer blood money
                for u in self.units:
                    if isinstance(u,Lifestealer):
                        pm=getattr(u,'_pending_money',0)
                        if pm>0: self.money+=pm; u._pending_money=0
    
                # Commander: apply firerate buff to nearby units
                for u in self.units:
                    if isinstance(u, Commander):
                        u.update_buff(self.units)
    
                # Collect GoldenCowboy cash shot income
                for u in self.units:
                    if isinstance(u,GoldenCowboy):
                        earned=u.collect_income()
                        if earned>0:
                            self.money+=earned
                            self.effects.append(FloatingText(u.px,u.py-30,f"+${earned}",(255,220,60)))
    
                # Kill rewards (second pass — catches kills from unit attacks this tick)
                for e in self.enemies:
                    if not e.alive and not getattr(e,'_reward_paid',False) and not getattr(e,'free_kill',False):
                        e._reward_paid=True
                        reward=e.KILL_REWARD
                        if reward>0 and self.mode != "easy":
                            self.money+=reward
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
    
                self.enemies=[e for e in self.enemies if e.alive or isinstance(e,(BreakerEnemy,FallenBreaker,PossessedArmor,FrostMystery))]+new_enemies
    
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
    
                if (self.wave_mgr.state=="waiting"
                        and not any(e.alive for e in self.enemies) and not self.wave_mgr._lmoney_paid):
                    lm=self.wave_mgr.wave_lmoney(); bm=self.wave_mgr.wave_bmoney()
                    if self.mode == "frosty":
                        if lm: lm += 150
                        if bm: bm += 150
                    # Farm income — only count OWN farms (not peer farms)
                    own_farms = [u for u in self.units if isinstance(u, Farm)]
                    farm_income = sum(u.income for u in own_farms)
                    if farm_income>0:
                        self.money+=farm_income
                        self.ui.show_msg(f"+{farm_income} Farm income",2.5)
                    if self._wave_leaked:
                        if lm: self.money+=lm; self.ui.show_msg(f"+{lm} Wave bonus",2.5)
                    else:
                        msgs=[]
                        if lm: self.money+=lm; msgs.append(f"+{lm} Wave bonus")
                        if bm: self.money+=bm; msgs.append(f"+{bm} Wave clear")
                        if msgs: self.ui.show_msg("  |  ".join(msgs),3.0)
                    # (per-wave profile coins handled by the wave-advance hook above)
                    self.wave_mgr._lmoney_paid=True; self.wave_mgr._bonus_paid=True
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
                # True Fallen trigger: fallen mode + killed FallenKing + under 15 min
                tf_can_trigger = (
                    self.mode=="fallen"
                    and self._fallen_king_spawned
                    and not any(isinstance(e,FallenKing) and e.alive for e in self.enemies)
                    and self._elapsed < 900.0
                    and not getattr(self,"_tf_triggered_auto",False)
                )
                if tf_can_trigger and self.wave_mgr.state=="done" and not any(e.alive for e in self.enemies):
                    self._tf_triggered_auto = True
                    # Spawn the special 10k FK that triggers the tf_test animation
                    fk_tf = FallenKing(1)
                    fk_tf.hp = 10000; fk_tf.maxhp = 10000; fk_tf.x = -30.0
                    self.enemies.append(fk_tf)
                if self.wave_mgr.state=="done" and not any(e.alive for e in self.enemies) and not fk_pending :
                    if not self.win:
                        # ── Ensure all waves paid (covers state=done skipping the waiting block) ──
                        self._give_wave_coins(self.wave_mgr.wave)
                        # Flush leftover fractional accumulator (e.g. 0.5 from Fallen odd waves)
                        if self.mode in ("easy", "fallen", "frosty") and self._wave_coin_accum >= 0.5:
                            self._end_coin_reward += 1
                            self.save_data["coins"] = self.save_data.get("coins", 0) + 1
                            self._wave_coin_accum = 0.0
                        write_save(self.save_data)
                        # ── Grant achievements on win ──
                        if self.mode == "fallen":
                            self.ach_mgr.try_grant("fallen_angel")
                        elif self.mode == "frosty":
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
    
                    self.win=True
                    try:
                        pygame.mixer.music.set_endevent(0)
                        pygame.mixer.music.stop()
                    except: pass
    
                # ── Achievement: Богач ─ > 5000 coins at once ──
                if not self.game_over and not self.win:
                    self.ach_mgr.try_grant("rich") if self.money > 5000 else None
    
                # ── Achievement: free_pass ─ GraveDigger (easy final boss) leaks with hp < player_hp ──
                if self.mode == "easy" and not self.game_over:
                    for e in dead_reached:
                        if isinstance(e, GraveDigger):
                            if e.hp < self.player_hp:
                                self._easy_boss_let_through = True
    
    
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
            pygame.display.flip()

    def draw(self):
        fk_shake=(0,0)
        if self._fallen_king_shake>0:
            intensity=min(20, self._fallen_king_shake*16)
            fk_shake=(random.randint(-int(intensity),int(intensity)),
                      random.randint(-int(intensity),int(intensity)))
        shake=fk_shake
        self.draw_map(offset=shake)
        can_detect=any(getattr(u,'hidden_detection',False) for u in self.units)
        mx,my=pygame.mouse.get_pos()

        for u in self.units: u.draw(self.screen)
        # Draw peer (other player's) units in the same pass for correct layering
        for u in getattr(self, '_peer_units', []):
            try: u.draw(self.screen)
            except Exception: pass
        for e in self.enemies:
            if not e.alive: continue
            hov=dist((e.x,e.y),(mx,my))<e.radius+5
            if hov: continue
            e.draw(self.screen,detected=can_detect)
        # Draw fire effect on burning enemies
        _ft=pygame.time.get_ticks()*0.001
        for e in self.enemies:
            if not e.alive: continue
            if getattr(e,'_fire_timer',0)>0:
                cx,cy=int(e.x),int(e.y)
                fs=pygame.Surface((60,60),pygame.SRCALPHA)
                for i in range(6):
                    a=math.radians(i*60+_ft*200)
                    flick=abs(math.sin(_ft*14+i*1.1))
                    fx=30+int(math.cos(a)*(e.radius-4+flick*4))
                    fy=30+int(math.sin(a)*(e.radius-4+flick*4))
                    r2=int(4+flick*4)
                    pygame.draw.circle(fs,(255,int(60+flick*100),0,200),(fx,fy),r2)
                    pygame.draw.circle(fs,(255,220,50,120),(fx,fy),r2-2)
                self.screen.blit(fs,(cx-30,cy-30))
                # Small timer bar
                frac=max(0,min(1,e._fire_timer/3.0))
                bw=e.radius*2+4; bx2=cx-bw//2; by2=cy-e.radius-14
                pygame.draw.rect(self.screen,(60,20,0),(bx2,by2,bw,4),border_radius=2)
                pygame.draw.rect(self.screen,(255,100,0),(bx2,by2,int(bw*frac),4),border_radius=2)
        # Draw frost effects from Frostcelerators
        for u in self.units:
            if isinstance(u, Frostcelerator):
                u.draw_enemy_frost(self.screen, self.enemies)

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
                # Green toxic aura
                ps = pygame.Surface((60, 60), pygame.SRCALPHA)
                ga2 = int(min(1.0, pt / 3.0) * 100) + 30
                pygame.draw.circle(ps, (60, 200, 40, ga2), (30, 30), e.radius + 5)
                self.screen.blit(ps, (cx2 - 30, cy2 - 30))
                # Spinning toxic dots
                for i in range(3):
                    a2 = math.radians(_tg_t * 140 + i * 120)
                    px4 = cx2 + int(math.cos(a2) * (e.radius + 7))
                    py4 = cy2 + int(math.sin(a2) * (e.radius + 7))
                    pygame.draw.circle(self.screen, (100, 240, 60), (px4, py4), 3)

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
            # Confusion overlay — purple spinning ?
            if getattr(e, '_confused', False):
                cs3 = pygame.Surface((70, 70), pygame.SRCALPHA)
                ct2 = getattr(e, '_confused_timer', 0.0)
                ca3 = int(min(1.0, ct2 / 0.5) * 160) + 40
                pygame.draw.circle(cs3, (180, 60, 255, ca3), (35, 35), e.radius + 8)
                self.screen.blit(cs3, (cx2 - 35, cy2 - 35))
                # Spinning ? marks
                qf2 = pygame.font.SysFont("consolas", 14, bold=True)
                for i in range(3):
                    qa = math.radians(_sp_t * 200 + i * 120)
                    qx = cx2 + int(math.cos(qa) * (e.radius + 10))
                    qy = cy2 + int(math.sin(qa) * (e.radius + 10))
                    qs2 = qf2.render("?", True, (220, 100, 255))
                    qs2.set_alpha(ca3)
                    self.screen.blit(qs2, qs2.get_rect(center=(qx, qy)))

        # Draw glitch effects on pokaxw5yt-stunned enemies
        _gt=pygame.time.get_ticks()*0.001
        for e in self.enemies:
            if not e.alive: continue
            if not getattr(e,'_glitched',False): continue
            e._glitch_t=getattr(e,'_glitch_t',0.0)+0.016
            cx2,cy2=int(e.x),int(e.y)
            gs=pygame.Surface((80,80),pygame.SRCALPHA)
            # Glitch scanlines
            for gi in range(6):
                gy=int(((_gt*7+gi*11)%1.0)*60)
                gw=random.randint(20,60); gx=random.randint(0,20)
                col_g=random.choice([(0,255,80,60),(255,0,200,50),(0,200,255,50),(255,255,0,40)])
                pygame.draw.rect(gs,col_g,(gx,gy,gw,2))
            # Glitch offset copies of enemy circle
            for _ in range(3):
                ox3=random.randint(-8,8); oy3=random.randint(-8,8)
                col_g2=random.choice([(0,255,80,80),(255,0,180,80),(0,200,255,80)])
                pygame.draw.circle(gs,col_g2,(40+ox3,40+oy3),e.radius,2)
            # Corrupted ring
            pulse2=int(abs(math.sin(_gt*12))*6)+e.radius+2
            pygame.draw.circle(gs,(0,255,80,int(abs(math.sin(_gt*9))*180)+40),(40,40),pulse2,2)
            pygame.draw.circle(gs,(255,0,200,int(abs(math.sin(_gt*14+1))*120)+30),(40,40),pulse2+3,1)
            self.screen.blit(gs,(cx2-40,cy2-40))
            # Glitch text fragments
            if int(_gt*8)%3==0:
                gf=font_sm.render(random.choice(["ERR","0x"+str(random.randint(0,255)),"??","#!"]),True,
                                  random.choice([(0,255,80),(255,0,200),(0,200,255)]))
                self.screen.blit(gf,(cx2+random.randint(-20,20)-gf.get_width()//2,
                                     cy2-e.radius-18+random.randint(-4,4)))

        for ef in self.effects: ef.draw(self.screen)

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
        for cls,(label,col) in _bar_cfg.items():
            e=self._fallen_boss_bars.get(cls)
            if e and e.alive:
                fallen_bars.append((label,e.hp,e.maxhp,col))
        if not fallen_bars: fallen_bars=None

        self.ui.draw(self.screen,self.units,self.money,self.wave_mgr,
                     self.player_hp,self.player_maxhp,self.enemies,
                     self._boss_enemy,
                     False,False,extra_bars,fallen_bars,self.mode)


        # Admin panel
        if self.mode=="sandbox":
            self.ui._game_ref=self
            self.ui.admin_panel.draw(self.screen,self.units,pygame.time.get_ticks()*0.001,game_ref=self,ui_ref=self.ui)
        self.console.draw(self.screen)

        # Ceremony flash overlay (original fallen mode)
        if self._ceremony_flash_alpha>0:
            col=getattr(self,'_ceremony_flash_color',(255,255,255))
            fl=pygame.Surface((SCREEN_W,SCREEN_H))
            fl.fill(col); fl.set_alpha(self._ceremony_flash_alpha)
            self.screen.blit(fl,(0,0))
        # tf ceremony flash overlay
            fl=pygame.Surface((SCREEN_W,SCREEN_H))
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

        # hixw5yt time-freeze overlay
        if self._hixw5yt_frozen:
            grey=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            grey.fill((20,20,20,190))
            self.screen.blit(grey,(0,0))
            # Highlight clickable enemies
            mx2,my2=pygame.mouse.get_pos()
            for e in self.enemies:
                if not e.alive: continue
                hov=dist((e.x,e.y),(mx2,my2))<=e.radius+8
                pulse=int(abs(math.sin(pygame.time.get_ticks()*0.006))*80)+80
                ring=pygame.Surface((80,80),pygame.SRCALPHA)
                pygame.draw.circle(ring,(40,220,100,pulse),(40,40),e.radius+10,3)
                self.screen.blit(ring,(int(e.x)-40,int(e.y)-40))
                if hov:
                    pygame.draw.circle(self.screen,(80,255,140),(int(e.x),int(e.y)),e.radius+5,3)

        # pokaxw5yt freeze overlay
        if self._pokaxw5yt_frozen:
            grey=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            grey.fill((20,20,20,190))
            self.screen.blit(grey,(0,0))
            _pt=pygame.time.get_ticks()*0.001
            mx2,my2=pygame.mouse.get_pos()
            for e in self.enemies:
                if not e.alive: continue
                hov=dist((e.x,e.y),(mx2,my2))<=e.radius+8
                pulse=int(abs(math.sin(_pt*8))*80)+80
                ring=pygame.Surface((80,80),pygame.SRCALPHA)
                pygame.draw.circle(ring,(200,0,255,pulse),(40,40),e.radius+10,3)
                ox3=random.randint(-2,2); oy3=random.randint(-2,2)
                pygame.draw.circle(ring,(0,255,200,pulse//2),(40+ox3,40+oy3),e.radius+7,2)
                self.screen.blit(ring,(int(e.x)-40,int(e.y)-40))
                if hov:
                    pygame.draw.circle(self.screen,(255,0,200),(int(e.x),int(e.y)),e.radius+5,3)

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
        return _mp.run_multiplayer(screen, save_data)
    except Exception as e:
        screen.fill((18,22,30))
        ef = pygame.font.SysFont("segoeui", 28).render(
            f"Ошибка загрузки assets/multiplayer.py: {e}", True, (255,80,80))
        screen.blit(ef, ef.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
        pygame.display.flip()
        import time; time.sleep(3)
        return save_data

# ── Modified MainMenu: Multiplayer + Achievements buttons ─────────────────────
_OrigMainMenu = MainMenu

class MainMenu(_OrigMainMenu):
    def __init__(self, screen, save_data=None):
        super().__init__(screen, save_data)
        cx = SCREEN_W // 2
        btn_w, btn_h = 260, 54
        gap = 16
        # 5 buttons starting at y=248 with gap=16
        y0 = 248
        self.btn_play        = pygame.Rect(cx - btn_w//2, y0,              btn_w, btn_h)
        self.btn_loadout     = pygame.Rect(cx - btn_w//2, y0 + (btn_h+gap)*1, btn_w, btn_h)
        self.btn_mp          = pygame.Rect(cx - btn_w//2, y0 + (btn_h+gap)*2, btn_w, btn_h)
        self.btn_achievements= pygame.Rect(cx - btn_w//2, y0 + (btn_h+gap)*3, btn_w, btn_h)
        self.btn_settings    = pygame.Rect(cx - btn_w//2, y0 + (btn_h+gap)*4, btn_w, btn_h)
        self.btn_quit        = pygame.Rect(cx - btn_w//2, y0 + (btn_h+gap)*5, btn_w, btn_h)

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
                                if FrostyWarningScreen(self.screen).run() == "continue":
                                    game_core.CURRENT_MAP = "frosty"
                                    self.action = diff
                            else:
                                map_choice = MapSelectMenu(self.screen).run()
                                if map_choice != "back":
                                    game_core.CURRENT_MAP = map_choice
                                    self.action = diff
                    if self.btn_loadout.collidepoint(pos):      self.action = "loadout"
                    if self.btn_mp.collidepoint(pos):           self.action = "multiplayer"
                    if self.btn_achievements.collidepoint(pos): self.action = "achievements"
                    if self.btn_settings.collidepoint(pos):    self.action = "settings"
                    if self.btn_quit.collidepoint(pos):         self.action = "quit"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw(self):
        surf = self.screen
        surf.fill((10, 13, 20))
        t = self.t
        cx = SCREEN_W // 2
        mx, my = pygame.mouse.get_pos()

        # ── Animated background: drifting star particles ──────────────────────
        random.seed(77)
        for i in range(280):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H)
            phase = sx * 0.007 + i * 0.3
            br = int(abs(math.sin(t * 0.8 + phase)) * 140 + 40)
            size = 1 if i % 3 != 0 else 2
            pygame.draw.circle(surf, (br, br, min(255, br + 30)), (sx, sy), size)
        random.seed()

        # ── Decorative horizontal line under title ────────────────────────────
        line_y = 230
        for dx2 in range(-500, 501):
            frac = abs(dx2) / 500
            alpha = int((1 - frac ** 2) * 80)
            c_val = int(80 + (1 - frac) * 120)
            pygame.draw.line(surf, (c_val // 3, c_val // 2, c_val),
                             (cx + dx2, line_y), (cx + dx2, line_y + 1))

        # ── Title: "TOWER DEFENSE" single render with animated colour ─────────
        title_font = pygame.font.SysFont("consolas", 64, bold=True)
        sub_font   = pygame.font.SysFont("segoeui",  22)
        hue_shift = math.sin(t * 1.1) * 0.5 + 0.5
        r3 = int(80  + hue_shift * 140)
        g3 = int(140 + hue_shift * 80)
        # Glow ellipse behind title
        glow_alpha = int(abs(math.sin(t * 1.2)) * 60 + 40)
        glow_s = pygame.Surface((700, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_s, (r3 // 3, g3 // 3, 80, glow_alpha), (0, 0, 700, 90))
        surf.blit(glow_s, (cx - 350, 130))
        title_s = title_font.render("TOWER DEFENSE", True, (r3, g3, 255))
        surf.blit(title_s, title_s.get_rect(center=(cx, 170)))

        sub_s = sub_font.render("by zigres", True, (60, 70, 100))
        surf.blit(sub_s, sub_s.get_rect(center=(cx, 215)))

        # ── Buttons ────────────────────────────────────────────────────────────
        def draw_fancy_btn(rect, label, hov, accent=(80, 120, 255), icon_col=None):
            # Background gradient effect via two rects
            bg_dark  = (18, 22, 38) if not hov else (28, 36, 62)
            bg_light = (28, 35, 58) if not hov else (42, 55, 90)
            # Top half
            pygame.draw.rect(surf, bg_light,
                             pygame.Rect(rect.x, rect.y, rect.w, rect.h // 2),
                             border_top_left_radius=12, border_top_right_radius=12)
            # Bottom half
            pygame.draw.rect(surf, bg_dark,
                             pygame.Rect(rect.x, rect.y + rect.h // 2, rect.w, rect.h - rect.h // 2),
                             border_bottom_left_radius=12, border_bottom_right_radius=12)
            # Accent border
            brd_alpha = 200 if hov else 130
            brd_col = tuple(min(255, int(c * (1.3 if hov else 1.0))) for c in accent)
            pygame.draw.rect(surf, brd_col, rect, 2, border_radius=12)
            # Left accent stripe
            stripe = pygame.Surface((4, rect.h - 8), pygame.SRCALPHA)
            stripe.fill((*accent, brd_alpha))
            surf.blit(stripe, (rect.x + 2, rect.y + 4))
            # Label
            lf = pygame.font.SysFont("segoeui", 26, bold=True)
            ls2 = lf.render(label, True, C_WHITE if hov else (200, 210, 230))
            surf.blit(ls2, ls2.get_rect(center=rect.center))

        draw_fancy_btn(self.btn_play,        "PLAY",         self.btn_play.collidepoint(mx, my),        (60, 160, 255))
        draw_fancy_btn(self.btn_loadout,     "LOADOUT",      self.btn_loadout.collidepoint(mx, my),     (120, 80, 220))
        draw_fancy_btn(self.btn_mp,          "MULTIPLAYER",   self.btn_mp.collidepoint(mx, my),          (40, 180, 100))
        draw_fancy_btn(self.btn_achievements,"ACHIEVEMENTS",   self.btn_achievements.collidepoint(mx, my),(200, 160, 20))
        draw_fancy_btn(self.btn_settings,    "SETTINGS",      self.btn_settings.collidepoint(mx, my),    (60, 130, 180))
        draw_fancy_btn(self.btn_quit,        "QUIT",          self.btn_quit.collidepoint(mx, my),        (180, 50, 50))

        # ── Coin counter (top right) ───────────────────────────────────────────
        coins = self.save_data.get("coins", 0)
        ico_m = load_icon("coin_ico", 28)
        coin_s = pygame.font.SysFont("segoeui", 22, bold=True).render(f" {coins}", True, C_GOLD)
        total_cw = (ico_m.get_width() if ico_m else 0) + coin_s.get_width() + 16
        coin_bg = pygame.Rect(SCREEN_W - total_cw - 10, 8, total_cw, 34)
        draw_rect_alpha(surf, (20, 20, 10), (coin_bg.x, coin_bg.y, coin_bg.w, coin_bg.h), 160, 8)
        pygame.draw.rect(surf, (160, 120, 20), coin_bg, 1, border_radius=8)
        if ico_m:
            surf.blit(ico_m, (coin_bg.x + 8, coin_bg.y + (34 - ico_m.get_height()) // 2))
            surf.blit(coin_s, (coin_bg.x + 8 + ico_m.get_width(), coin_bg.y + (34 - coin_s.get_height()) // 2))
        else:
            surf.blit(coin_s, coin_s.get_rect(midleft=(coin_bg.x + 8, coin_bg.centery)))

        # ── Version (bottom left) ─────────────────────────────────────────────
        ver = font_sm.render("v1.2", True, (40, 48, 65))
        surf.blit(ver, (10, SCREEN_H - 20))

        # ── Changelog (top left) ──────────────────────────────────────────────
        cl_x, cl_y = 12, 58
        cl_w, cl_h = 310, 14 + len(_CHANGELOG) * 20 + 8
        draw_rect_alpha(surf, (12, 10, 22), (cl_x, cl_y, cl_w, cl_h), 200, 8)
        pygame.draw.rect(surf, (70, 50, 110), pygame.Rect(cl_x, cl_y, cl_w, cl_h), 1, border_radius=8)
        cy_cl = cl_y + 8
        for text, col, bold in _CHANGELOG:
            cf = pygame.font.SysFont("segoeui", 13, bold=bold)
            cs2 = cf.render(text, True, col)
            surf.blit(cs2, (cl_x + 8, cy_cl))
            cy_cl += 20


# ── Changelog widget (drawn in MainMenu._draw) ────────────────────────────────
_CHANGELOG = [
    ("CHANGELOG", (200, 180, 255), True),
    ("• Полный РЕБАЛАНС Фрости режима до играбельности", (160, 220, 255), False),
    ("• Ребаланс Snowballer", (200, 200, 200), False),
    ("  (старая версия доступна в sandbox)", (160, 160, 160), False),
    ("• Командир убран до реворка из-за очень", (255, 120, 100), False),
    ("  большого количества багов и недоработок", (255, 120, 100), False),
    ("  (доступен в sandbox)", (200, 100, 80), False),
    ("• Frostcelerator бафф", (160, 220, 255), False),
    ("", (200, 200, 200), False),
    ("В следующем обновлении:", (255, 230, 80), True),
    ("• Реворк командо", (200, 200, 200), False),
    ("• Ребаланс халов панк", (200, 200, 200), False),
    ("• У каждой волны свой таймер до перехода", (200, 200, 200), False),
    ("  на следующую, больше не будет зависеть", (200, 200, 200), False),
    ("  переход от убиты ли враги", (200, 200, 200), False),
    ("• Возможность скипать волны от таймера", (200, 200, 200), False),
]

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("START")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Tower Defense")
    save_data = load_save()
    print("save_data loaded:", list(save_data.keys()))

    while True:
        print("Creating MainMenu...")
        menu = MainMenu(screen, save_data)
        print("Running MainMenu...")
        action = menu.run()
        print("action:", action)

        if action == "quit":
            pygame.quit(); sys.exit()

        elif action == "achievements":
            AchievementsScreen(screen).run()

        elif action == "settings":
            SettingsScreen(screen).run()

        elif action == "loadout":
            ls = LoadoutScreen(screen, save_data)
            ls.run()
            save_data = load_save()

        elif action in ("play_easy", "play_sandbox", "play_fallen", "play_frosty"):
            if action == "play_sandbox": mode = "sandbox"
            elif action == "play_fallen": mode = "fallen"
            elif action == "play_frosty": mode = "frosty"
            else: mode = "easy"
            print("Starting game mode:", mode)
            try:
                game = Game(save_data, mode=mode)
                print("Game created, running...")
                game.run()
                print("Game ended, return_to_menu:", game.return_to_menu)
            except Exception as e:
                import traceback; traceback.print_exc()
                input("Press Enter to continue...")
            save_data = load_save()

        elif action == "multiplayer":
            save_data = _run_multiplayer(screen, save_data)