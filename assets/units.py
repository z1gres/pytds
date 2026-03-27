# ═══════════════════════════════════════════════════════════════════════════════
# units.py  —  все юниты, способности, снаряды
# ═══════════════════════════════════════════════════════════════════════════════
import pygame, math, random, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import game_core as _game_core_ref
from game_core import (
    SCREEN_W, SCREEN_H, PATH_Y, PATH_H, SLOT_AREA_Y, TILE,
    C_WHITE, C_BLACK, C_GOLD, C_ASSASSIN, C_ACCEL,
    font_sm, font_md, font_lg,
    get_map_path, dist, txt, draw_rect_alpha, load_icon,
    UNIT_LIMITS,
    SwordEffect, WhirlwindEffect, FloatingText, BloodSlashEffect,
)

def _dm(): """Return current debuff duration multiplier from skill tree."""; return getattr(_game_core_ref, "DEBUFF_MULT", 1.0)
def _am(): """Return current AoE radius multiplier from skill tree."""; return getattr(_game_core_ref, "AOE_MULT", 1.0)
from enemies import (
    Enemy, HiddenEnemy, BreakerEnemy, ArmoredEnemy, ScoutEnemy, TankEnemy,
    NormalBoss, SlowBoss, HiddenBoss, FastBoss, Necromancer, GraveDigger,
    OtchimusPrime, AbnormalEnemy, QuickEnemy, SkeletonEnemy,
    FallenDreg, FallenSquire, FallenSoul, FallenEnemy, FallenGiant, FallenHazmat,
    PossessedArmor, FallenNecromancer, CorruptedFallen, FallenJester,
    NecroticSkeleton, FallenBreaker, FallenRusher, FallenHonorGuard,
    FallenShield, FallenHero, FallenKing,
)

class WhirlwindAbility:
    name="Whirlwind Slash"; cooldown=10.0; dmg_base=15
    def __init__(self, owner): self.owner=owner; self.cd_left=0.0
    @property
    def damage(self): return self.dmg_base+self.owner._whirl_bonus
    def update(self, dt):
        if self.cd_left>0: self.cd_left-=dt
    def ready(self): return self.cd_left<=0
    def activate(self, enemies, effects):
        if not self.ready(): return
        self.cd_left=self.cooldown
        ox,oy=self.owner.px,self.owner.py; r=self.owner.range_tiles*TILE
        hd=getattr(self.owner,'hidden_detection',False)
        for e in enemies:
            if e.alive and dist((e.x,e.y),(ox,oy))<=r:
                if getattr(e,'_reversed',False): continue
                if e.IS_HIDDEN and not hd: continue
                e.take_damage(self.damage)
        effects.append(WhirlwindEffect(ox,oy,self.owner.range_tiles))

# ── Unit base ──────────────────────────────────────────────────────────────────
TARGET_MODES = ["First", "Last", "Lowest HP", "Highest HP", "Nearest", "Farthest", "Random"]

class Unit:
    hidden_detection=False
    def __init__(self, px, py):
        self.px=float(px); self.py=float(py)
        self.level=0; self.ability=None; self.cd_left=0.0
        self.total_damage=0
        self.target_mode="First"
    def update(self, dt, enemies, effects, money):
        if self.cd_left>0: self.cd_left-=dt
        if self.ability: self.ability.update(dt)
        self._try_attack(enemies, effects)
    def _try_attack(self, enemies, effects): pass
    def draw(self, surf): pass
    def draw_range(self, surf):
        r=int(self.range_tiles*TILE)
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(255,255,255,22),(r,r),r)
        pygame.draw.circle(s,(255,255,255,60),(r,r),r,2)
        surf.blit(s,(int(self.px)-r,int(self.py)-r))
    def get_info(self): return {}
    def upgrade_cost(self): return None
    def upgrade(self): pass
    def _get_rightmost(self, enemies, count=1):
        return self._get_targets(enemies, count)
    def _get_targets(self, enemies, count=1):
        r=self.range_tiles*TILE; pool=[]
        for e in enemies:
            if not e.alive: continue
            if getattr(e,'_reversed',False): continue
            if e.IS_HIDDEN and not self.hidden_detection and not getattr(e,"_exposed",False): continue
            if dist((e.x,e.y),(self.px,self.py))<=r: pool.append(e)
        if not pool: return []
        mode=getattr(self,'target_mode','First')
        if mode=="First":       pool.sort(key=lambda e:-e.x)
        elif mode=="Last":      pool.sort(key=lambda e:e.x)
        elif mode=="Lowest HP": pool.sort(key=lambda e:e.hp)
        elif mode=="Highest HP":pool.sort(key=lambda e:-e.hp)
        elif mode=="Nearest":   pool.sort(key=lambda e:dist((e.x,e.y),(self.px,self.py)))
        elif mode=="Farthest":  pool.sort(key=lambda e:-dist((e.x,e.y),(self.px,self.py)))
        return pool[:count]

ASSASSIN_LEVELS=[(4.5,0.608,3,None),(6.5,0.508,3,450),(6.5,0.508,3,550),(16.5,0.358,3,1500),(28.5,0.358,4,2500)]

class Assassin(Unit):
    PLACE_COST=300; COLOR=C_ASSASSIN; NAME="Assassin"; _whirl_bonus=0
    def __init__(self, px, py): super().__init__(px,py); self._apply_level()
    def _apply_level(self):
        d,fr,r,_=ASSASSIN_LEVELS[self.level]
        self.damage=d; self.firerate=fr; self.range_tiles=r
        self.hidden_detection=(self.level>=1)
        if self.level>=2 and self.ability is None: self.ability=WhirlwindAbility(self)
        b=0
        if self.level>=3: b+=15
        if self.level>=4: b+=10
        self._whirl_bonus=b
    def upgrade_cost(self):
        if self.level>=len(ASSASSIN_LEVELS)-1: return None
        return ASSASSIN_LEVELS[self.level+1][3]
    def upgrade(self):
        if self.level<len(ASSASSIN_LEVELS)-1: self.level+=1; self._apply_level()
    def _try_attack(self, enemies, effects):
        if self.cd_left>0: return
        t=self._get_rightmost(enemies,1)
        if t:
            self.cd_left=self.firerate; t[0].take_damage(self.damage)
            self.total_damage+=self.damage
            angle=math.degrees(math.atan2(t[0].y-self.py,t[0].x-self.px))
            effects.append(SwordEffect(self.px,self.py,angle))
    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        pygame.draw.circle(surf,(70,40,100),(cx,cy),27)
        pygame.draw.circle(surf,self.COLOR,(cx,cy),21)
        pygame.draw.line(surf,(220,220,255),(cx+12,cy-27),(cx+27,cy-12),4)
        pygame.draw.line(surf,(180,180,220),(cx+18,cy-21),(cx+15,cy-18),7)
        if self.hidden_detection: pygame.draw.circle(surf,(100,255,100),(cx+21,cy-21),6)
        for i in range(self.level): pygame.draw.circle(surf,C_GOLD,(cx-10+i*7,cy+33),3)
    def get_info(self):
        return {"Damage":self.damage,"Range":self.range_tiles,
                "Firerate":f"{self.firerate:.3f}","HidDet":"YES" if self.hidden_detection else "no"}

ACCEL_LEVELS=[(12,0.208,7,None,False),(15,0.208,7,2000,False),(25,0.208,7,4500,False),
              (32,0.208,7,10000,False),(34,0.158,7,17000,True),(36,0.108,7,27000,True)]

class Accelerator(Unit):
    PLACE_COST=5000; COLOR=C_ACCEL; NAME="Accelerator"; hidden_detection=False
    def __init__(self, px, py):
        super().__init__(px,py); self._laser_targets=[]; self._laser_t=0.0
        self.mini_ops=[]; self._op_cd=0.0
        self._apply_level()
    def _apply_level(self):
        d,fr,r,_,dual=ACCEL_LEVELS[self.level]
        self.damage=d; self.firerate=fr; self.range_tiles=r; self.dual=dual
        self.hidden_detection=(self.level>=1)
    def upgrade_cost(self):
        next_lv=self.level+1
        if next_lv>=len(ACCEL_LEVELS): return None
        return ACCEL_LEVELS[next_lv][3]
    def upgrade(self):
        next_lv=self.level+1
        if next_lv>=len(ACCEL_LEVELS): return
        self.level=next_lv; self._apply_level()
    def update(self, dt, enemies, effects, money):
        self._laser_t+=dt
        if self.cd_left>0: self.cd_left-=dt
        targets=self._get_rightmost(enemies,2 if self.dual else 1)
        self._laser_targets=targets
        if self.cd_left<=0 and targets:
            self.cd_left=self.firerate
            for t in targets:
                t.take_damage(self.damage)
                self.total_damage+=self.damage
        for m in self.mini_ops: m.update(dt, enemies)
        self.mini_ops=[m for m in self.mini_ops if m.alive]
    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        spin=self._laser_t*180
        for i in range(4):
            a=math.radians(spin+i*90)
            pygame.draw.circle(surf,(160,100,255),(int(cx+math.cos(a)*27),int(cy+math.sin(a)*27)),5)
        pygame.draw.circle(surf,(40,20,80),(cx,cy),27)
        pygame.draw.circle(surf,C_ACCEL,(cx,cy),20)
        # Inner ring detail
        pygame.draw.circle(surf,(160,80,255),(cx,cy),20,2)
        # Lightning bolt symbol
        bolt=[(cx+4,cy-14),(cx-3,cy-1),(cx+5,cy-1),(cx-4,cy+14),(cx+3,cy+1),(cx-5,cy+1)]
        pygame.draw.polygon(surf,(220,180,255),bolt)
        pygame.draw.polygon(surf,(255,240,255),bolt,1)
        for i in range(self.level): pygame.draw.circle(surf,C_GOLD,(cx-14+i*7,cy+36),3)
        for target in self._laser_targets:
            if not target.alive: continue
            tx,ty=int(target.x),int(target.y); tv=self._laser_t
            s2=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            flicker=int(abs(math.sin(tv*22))*3)
            for width,color,alpha in [(20+flicker,(120,40,255),18),(13,(160,80,255),35),
                                       (8,(200,130,255),70),(4,(230,190,255),140),(2,(255,240,255),220)]:
                pygame.draw.line(s2,(*color,alpha),(cx,cy),(tx,ty),width)
            surf.blit(s2,(0,0))
            fs=pygame.Surface((40,40),pygame.SRCALPHA)
            fr2=int(abs(math.sin(tv*18))*8)+6
            pygame.draw.circle(fs,(220,180,255,100),(20,20),fr2+4)
            pygame.draw.circle(fs,(255,240,255,180),(20,20),fr2)
            surf.blit(fs,(tx-20,ty-20))
        for m in self.mini_ops: m.draw(surf)
    def get_info(self):
        return {"Damage":self.damage,"Range":self.range_tiles,
                "Firerate":f"{self.firerate:.4f}","Dual":"YES" if self.dual else "no","HidDet":"YES"}

# ── Frostcelerator ─────────────────────────────────────────────────────────────
C_FROST      = (60, 200, 255)
C_FROST_DARK = (20, 80, 140)
C_FROST_ICE  = (180, 240, 255)

FROST_LEVELS = [
    (5,  0.20, 7, None),
    (7,  0.17, 7, 500),
    (9,  0.15, 7, 2000),
    (11, 0.13, 8, 5000),
    (14, 0.11, 8, 10000),
]

class Frostcelerator(Unit):
    PLACE_COST=3500; COLOR=C_FROST; NAME="Frostcelerator"; hidden_detection=True
    FREEZE_BUILD  = 5.0   # seconds of hits to freeze
    FREEZE_DUR    = 2.5   # seconds frozen
    SLOW_FACTOR   = 0.75  # enemy moves at 75% speed (25% slow)

    _TRI_ORBIT = 36

    def __init__(self, px, py):
        super().__init__(px,py)
        self._laser_targets=[]; self._laser_t=0.0
        self._shared_dmg=0.0  # total damage dealt by this tower
        self._aim_angle   = 0.0
        self._attack_lerp = 0.0
        self._tri_img     = None
        self._tri_cache   = {}
        try:
            import os as _os
            _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                               "assets", "image", "double_accelerator_triangles.png.png")
            self._tri_img = pygame.image.load(_p).convert_alpha()
        except Exception:
            self._tri_img = None
        self._apply_level()

    def _apply_level(self):
        d,fr,r,_=FROST_LEVELS[self.level]
        self.damage=d; self.firerate=fr; self.range_tiles=r

    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(FROST_LEVELS): return None
        return FROST_LEVELS[nxt][3]

    def upgrade(self):
        nxt=self.level+1
        if nxt>=len(FROST_LEVELS): return
        self.level=nxt; self._apply_level()

    def _freeze_enemy(self, e, secs):
        """Apply freeze to an enemy."""
        if not hasattr(e,'_frost_frozen'): e._frost_frozen=False
        e._frost_frozen=True
        e._frost_freeze_timer=getattr(e,'_frost_freeze_timer',0)+secs*_dm()
        e.frozen=True
        # Restore speed if was slowed
        if getattr(e,'_frost_slowed',False):
            e._frost_slowed=False
            if hasattr(e,'_frost_orig_speed'):
                e.speed=e._frost_orig_speed

    def _apply_slow(self, e):
        if getattr(e,'SLOW_RESISTANCE',0.0) >= 1.0: return
        if not getattr(e,'_frost_frozen',False) and not getattr(e,'_frost_slowed',False):
            e._frost_slowed=True
            e._frost_orig_speed=e.speed
            resistance=getattr(e,'SLOW_RESISTANCE',0.0)
            effective_factor=1.0-(1.0-self.SLOW_FACTOR)*resistance
            e.speed=e.speed*effective_factor

    def update(self, dt, enemies, effects, money):
        self._laser_t+=dt
        if self.cd_left>0: self.cd_left-=dt
        targets=self._get_rightmost(enemies,4)
        self._laser_targets=targets
        if targets:
            t0=targets[0]
            self._aim_angle=math.atan2(t0.y-self.py, t0.x-self.px)
            self._attack_lerp=min(1.0, self._attack_lerp+dt*8)
        else:
            self._attack_lerp=max(0.0, self._attack_lerp-dt*4)

        if self.cd_left<=0 and targets:
            self.cd_left=self.firerate
            total_dmg=0
            for t in targets:
                t.take_damage(self.damage)
                self.total_damage+=self.damage
                if not getattr(t,'_frost_frozen',False):
                    total_dmg+=self.damage
                    self._apply_slow(t)
            self._shared_dmg+=total_dmg
            # Every 1000 cumulative damage (outside freeze) → freeze all current targets for 5s
            if self._shared_dmg>=1000:
                freeze_count=int(self._shared_dmg//1000)
                self._shared_dmg=self._shared_dmg%1000
                for t in targets:
                    self._freeze_enemy(t, freeze_count*2.5)

        # Tick freeze timers
        for e in enemies:
            if not e.alive: continue
            if getattr(e,'_frost_frozen',False):
                e._frost_freeze_timer=getattr(e,'_frost_freeze_timer',0)-dt
                if e._frost_freeze_timer<=0:
                    e.frozen=False
                    e._frost_frozen=False

        # Remove slow from enemies no longer targeted
        target_ids={id(t) for t in targets}
        for e in enemies:
            if getattr(e,'_frost_slowed',False) and id(e) not in target_ids:
                if not getattr(e,'_frost_frozen',False):
                    e._frost_slowed=False
                    if hasattr(e,'_frost_orig_speed'):
                        e.speed=e._frost_orig_speed

    def _tri_positions(self):
        idle_left_a  = math.pi
        idle_right_a = 0.0
        aim_left_a   = self._aim_angle + math.pi / 2
        aim_right_a  = self._aim_angle - math.pi / 2
        t2 = self._attack_lerp
        left_a  = idle_left_a  + t2 * (aim_left_a  - idle_left_a)
        right_a = idle_right_a + t2 * (aim_right_a - idle_right_a)
        lx = self.px + math.cos(left_a)  * self._TRI_ORBIT
        ly = self.py + math.sin(left_a)  * self._TRI_ORBIT
        rx = self.px + math.cos(right_a) * self._TRI_ORBIT
        ry = self.py + math.sin(right_a) * self._TRI_ORBIT
        return (lx, ly), (rx, ry)

    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        # Aura
        pulse = int(abs(math.sin(self._laser_t*5))*50)+20
        aura=pygame.Surface((120,120),pygame.SRCALPHA)
        pygame.draw.circle(aura,(0,180,255,pulse//3),(60,60),56)
        pygame.draw.circle(aura,(40,200,255,pulse),(60,60),36)
        surf.blit(aura,(cx-60,cy-60))
        # Body
        pygame.draw.circle(surf,C_FROST_DARK,(cx,cy),27)
        pygame.draw.circle(surf,C_FROST,(cx,cy),20)
        pygame.draw.circle(surf,(180,240,255),(cx,cy),20,2)
        # Snowflake
        for i in range(6):
            a=math.radians(i*60+self._laser_t*20)
            ex=cx+int(math.cos(a)*16); ey=cy+int(math.sin(a)*16)
            pygame.draw.line(surf,(200,240,255),(cx,cy),(ex,ey),2)
            for sign in [-1,1]:
                bx=cx+int(math.cos(a)*9); by=cy+int(math.sin(a)*9)
                ba=a+sign*math.radians(60)
                ex2=bx+int(math.cos(ba)*5); ey2=by+int(math.sin(ba)*5)
                pygame.draw.line(surf,(220,250,255),(bx,by),(ex2,ey2),1)
        pygame.draw.circle(surf,(240,255,255),(cx,cy),3)
        for i in range(self.level):
            pygame.draw.circle(surf,C_FROST_ICE,(cx-14+i*7,cy+36),3)

        # Triangle positions
        (lx,ly),(rx,ry) = self._tri_positions()

        # Lasers from triangles
        for target in self._laser_targets:
            if not target.alive: continue
            tx,ty=int(target.x),int(target.y); tv=self._laser_t
            s2=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            flicker=int(abs(math.sin(tv*20))*2)
            for ox,oy in [(int(lx),int(ly)),(int(rx),int(ry))]:
                for width,col2,alp in [(18+flicker,(0,100,200),15),(11,(40,160,255),30),
                                        (7,(80,200,255),60),(4,(160,230,255),130),(2,(220,245,255),210)]:
                    pygame.draw.line(s2,(*col2,alp),(ox,oy),(tx,ty),width)
            surf.blit(s2,(0,0))
            fs=pygame.Surface((40,40),pygame.SRCALPHA)
            fr2=int(abs(math.sin(tv*16))*6)+5
            pygame.draw.circle(fs,(180,230,255,100),(20,20),fr2+4)
            pygame.draw.circle(fs,(220,245,255,180),(20,20),fr2)
            surf.blit(fs,(tx-20,ty-20))

        # Draw triangles
        tri_size = 36
        aim_deg = math.degrees(self._aim_angle)
        tri_img = None
        if self._tri_img:
            k = tri_size
            if k not in self._tri_cache:
                self._tri_cache[k] = pygame.transform.smoothscale(self._tri_img,(k,k))
            tri_img = self._tri_cache[k]
        for pos, side in [((lx,ly),1),((rx,ry),-1)]:
            px2,py2=int(pos[0]),int(pos[1])
            glow=pygame.Surface((tri_size+20,tri_size+20),pygame.SRCALPHA)
            ga=int(abs(math.sin(self._laser_t*6+side))*60)+30
            pygame.draw.circle(glow,(40,160,255,ga),((tri_size+20)//2,(tri_size+20)//2),(tri_size+20)//2)
            surf.blit(glow,(px2-(tri_size+20)//2,py2-(tri_size+20)//2))
            if tri_img:
                rot=-(aim_deg+side*90) + 90
                rotated=pygame.transform.rotate(tri_img,rot)
                surf.blit(rotated,rotated.get_rect(center=(px2,py2)))
            else:
                d=10
                pts=[(px2,py2-d),(px2+d,py2),(px2,py2+d),(px2-d,py2)]
                pygame.draw.polygon(surf,C_FROST,pts)
                pygame.draw.polygon(surf,(180,230,255),pts,2)

    def draw_enemy_frost(self, surf, enemies):
        """Draw frost/freeze overlays on enemies — called from game.draw."""
        for e in enemies:
            if not e.alive: continue
            frozen=getattr(e,'_frost_frozen',False)
            slowed=getattr(e,'_frost_slowed',False)
            if not (frozen or slowed): continue
            cx,cy=int(e.x),int(e.y)
            if frozen:
                ice_s=pygame.Surface((80,80),pygame.SRCALPHA)
                pygame.draw.circle(ice_s,(180,230,255,160),(40,40),e.radius+8)
                pygame.draw.circle(ice_s,(220,245,255,80),(40,40),e.radius+4,3)
                for i in range(6):
                    a=math.radians(i*60)
                    x1=40+int(math.cos(a)*6); y1=40+int(math.sin(a)*6)
                    x2=40+int(math.cos(a)*(e.radius+6)); y2=40+int(math.sin(a)*(e.radius+6))
                    pygame.draw.line(ice_s,(255,255,255,120),(x1,y1),(x2,y2),1)
                surf.blit(ice_s,(cx-40,cy-40))
                timer=getattr(e,'_frost_freeze_timer',0)
                frac=max(0,min(1,timer/Frostcelerator.FREEZE_DUR))
                bw=e.radius*2+8; bx2=cx-bw//2; by2=cy-e.radius-14
                pygame.draw.rect(surf,(20,60,100),(bx2,by2,bw,5),border_radius=2)
                pygame.draw.rect(surf,C_FROST,(bx2,by2,int(bw*frac),5),border_radius=2)
            elif slowed:
                frac=min(1.0, self._shared_dmg/1000)
                alpha=int(frac*120)+40
                frost_s=pygame.Surface((60,60),pygame.SRCALPHA)
                pygame.draw.circle(frost_s,(140,210,255,alpha),(30,30),e.radius+4)
                surf.blit(frost_s,(cx-30,cy-30))
                for i in range(max(1,int(frac*6))):
                    a=math.radians(i*60+self._laser_t*80)
                    px2=cx+int(math.cos(a)*(e.radius+5)); py2=cy+int(math.sin(a)*(e.radius+5))
                    pygame.draw.circle(surf,C_FROST_ICE,(px2,py2),2)

    def get_info(self):
        return {"Damage":self.damage,"Range":self.range_tiles,
                "Firerate":f"{self.firerate:.4f}","Slow":"-25% spd","Freeze":"2.5s (once)","HidDet":"YES"}


# ── XW5YT ──────────────────────────────────────────────────────────────────────
C_XW5YT      = (40, 220, 80)
XW5YT_LEVELS = [(12,0.208,7,None,False),(15,0.208,7,2000,False),(25,0.208,7,4500,False),
                (32,0.208,7,10000,False),(34,0.158,7,17000,True),(36,0.108,7,27000,True)]

class Hixw5ytAbility:
    name="hixw5yt"; cooldown=25.0
    def __init__(self, owner): self.owner=owner; self.cd_left=0.0
    def update(self, dt):
        if self.cd_left>0: self.cd_left-=dt
    def ready(self): return self.cd_left<=0
    def activate(self, enemies, effects):
        if not self.ready(): return
        self.cd_left=self.cooldown
        self.owner._hixw5yt_active=True

class Pokaxw5ytAbility:
    name="pokaxw5yt"; cooldown=40.0
    def __init__(self, owner): self.owner=owner; self.cd_left=0.0
    def update(self, dt):
        if self.cd_left>0: self.cd_left-=dt
    def ready(self): return self.cd_left<=0
    def activate(self, enemies, effects):
        if not self.ready(): return
        self.cd_left=self.cooldown
        self.owner._pokaxw5yt_active=True

class ChiterAbility:
    name="chiter"; cooldown=35.0; BOOST_FR=0.050; BOOST_DUR=8.0
    def __init__(self, owner): self.owner=owner; self.cd_left=0.0
    def update(self, dt):
        if self.cd_left>0: self.cd_left-=dt
    def ready(self): return self.cd_left<=0
    def activate(self, enemies, effects):
        if not self.ready(): return
        self.cd_left=self.cooldown
        # Find all friendly units in range, boost their firerate
        r=self.owner.range_tiles*TILE
        for u in getattr(self.owner,'_game_units_ref',[]):
            if u is self.owner: continue
            if dist((u.px,u.py),(self.owner.px,self.owner.py))<=r:
                u._chiter_boost=self.BOOST_DUR
                u._chiter_old_fr=getattr(u,'_chiter_old_fr',u.firerate)
                u.firerate=self.BOOST_FR

class Xw5ytUnit(Unit):
    PLACE_COST=5000; COLOR=C_XW5YT; NAME="xw5yt"; hidden_detection=False
    def __init__(self, px, py):
        super().__init__(px,py)
        self._laser_targets=[]; self._laser_t=0.0
        self.ability2=None; self.ability3=None
        self._apply_level()
        self._hixw5yt_active=False
        self._pokaxw5yt_active=False
    def _apply_level(self):
        d,fr,r,_,dual=XW5YT_LEVELS[self.level]
        self.damage=d; self.firerate=fr; self.range_tiles=r; self.dual=dual
        self.hidden_detection=(self.level>=1)
        if self.level>=1 and not self.ability2:
            self.ability2=Pokaxw5ytAbility(self)
        if self.level>=2 and not self.ability:
            self.ability=Hixw5ytAbility(self)
        elif self.level<2:
            self.ability=None
        if self.level>=4 and not self.ability3:
            self.ability3=ChiterAbility(self)
        elif self.level<4:
            self.ability3=None
    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(XW5YT_LEVELS): return None
        return XW5YT_LEVELS[nxt][3]
    def upgrade(self):
        nxt=self.level+1
        if nxt<len(XW5YT_LEVELS): self.level=nxt; self._apply_level()
    def update(self, dt, enemies, effects, money):
        self._laser_t+=dt
        if self.cd_left>0: self.cd_left-=dt
        if self.ability: self.ability.update(dt)
        if self.ability2: self.ability2.update(dt)
        if self.ability3: self.ability3.update(dt)
        if self._hixw5yt_active: return  # frozen - don't attack
        targets=self._get_rightmost(enemies,2 if self.dual else 1)
        self._laser_targets=targets
        if self.cd_left<=0 and targets:
            self.cd_left=self.firerate
            for t in targets:
                t.take_damage(self.damage)
                self.total_damage+=self.damage
    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        s=pygame.Surface((135,135),pygame.SRCALPHA)
        pygame.draw.circle(s,(*C_XW5YT,35),(67,67),63); surf.blit(s,(cx-67,cy-67))
        pygame.draw.ellipse(surf,(10,40,15),(cx-30,cy+17,60,20))
        spin=self._laser_t*180
        for i in range(4):
            a=math.radians(spin+i*90)
            pygame.draw.circle(surf,(80,255,120),(int(cx+math.cos(a)*27),int(cy+math.sin(a)*27)),6)
        pygame.draw.circle(surf,(15,50,25),(cx,cy),27)
        pygame.draw.circle(surf,C_XW5YT,(cx,cy),20)
        pulse=int(abs(math.sin(self._laser_t*8))*6)+5
        pygame.draw.circle(surf,(200,255,220),(cx,cy),pulse)
        for i in range(self.level): pygame.draw.circle(surf,C_GOLD,(cx-14+i*7,cy+36),3)
        if not self._hixw5yt_active:
            for target in self._laser_targets:
                if not target.alive: continue
                tx,ty=int(target.x),int(target.y); tv=self._laser_t
                s2=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
                flicker=int(abs(math.sin(tv*22))*3)
                for width,color,alpha in [(20+flicker,(20,120,40),18),(13,(40,180,80),35),
                                           (8,(80,220,120),70),(4,(160,255,180),140),(2,(220,255,230),220)]:
                    pygame.draw.line(s2,(*color,alpha),(cx,cy),(tx,ty),width)
                bl=dist((cx,cy),(tx,ty))
                if bl>1:
                    for i in range(6):
                        frac=(i/5+tv*2.5)%1.0
                        sx2=int(cx+(tx-cx)*frac); sy2=int(cy+(ty-cy)*frac)
                        px2=-(ty-cy)/bl; py2=(tx-cx)/bl
                        offset=math.sin(tv*30+i*1.4)*(3+flicker)
                        pygame.draw.circle(s2,(100,255,150,160),
                                           (sx2+int(px2*offset),sy2+int(py2*offset)),random.randint(2,4))
                surf.blit(s2,(0,0))
                fs=pygame.Surface((40,40),pygame.SRCALPHA)
                fr2=int(abs(math.sin(tv*18))*8)+6
                pygame.draw.circle(fs,(150,255,200,100),(20,20),fr2+4)
                pygame.draw.circle(fs,(220,255,230,180),(20,20),fr2)
                surf.blit(fs,(tx-20,ty-20))
    def get_info(self):
        return {"Damage":self.damage,"Range":self.range_tiles,
                "Firerate":f"{self.firerate:.4f}","Dual":"YES" if self.dual else "no",
                "HidDet":"YES" if self.hidden_detection else "no"}

def draw_xw5yt_icon(surf, cx, cy, t, size=28):
    spin = t * 180
    glow_s = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
    pygame.draw.circle(glow_s, (*C_XW5YT, 40), (size*2, size*2), int(size*1.5))
    surf.blit(glow_s, (cx - size*2, cy - size*2))
    pygame.draw.ellipse(surf, (10, 40, 15), (cx - size//1.4, cy + size//1.8, int(size*1.4), size//2))
    orb_r = int(size * 0.65)
    for i in range(4):
        a = math.radians(spin + i * 90)
        ox2 = cx + int(math.cos(a) * orb_r)
        oy2 = cy + int(math.sin(a) * orb_r)
        pygame.draw.circle(surf, (80, 255, 120), (ox2, oy2), max(2, size // 7))
    pygame.draw.circle(surf, (15, 50, 25), (cx, cy), int(size * 0.65))
    pygame.draw.circle(surf, C_XW5YT, (cx, cy), int(size * 0.48))
    hi = max(1, size // 6)
    pygame.draw.circle(surf, (180, 255, 200), (cx - hi, cy - hi), hi + 1)
    pulse = int(abs(math.sin(t * 8)) * 3) + 2
    pygame.draw.circle(surf, (200, 255, 220), (cx, cy), pulse)

# ── Lifestealer ────────────────────────────────────────────────────────────────
C_LIFESTEALER      = (220, 40, 80)
C_LIFESTEALER_DARK = (100, 10, 30)

# (damage, firerate, range_tiles, upgrade_cost, money_pct)
LIFESTEALER_LEVELS = [
    (5.5,  0.650, 5.0, None, 0.10),
    (5.5,  0.600, 5.0, 350,  0.15),
    (6.5,  0.600, 5.5, 600,  0.20),
    (8.5,  0.600, 5.5, 800,  0.25),
    (9.5,  0.600, 5.5, 1300, 0.35),
    (11.5, 0.600, 6.0, 1700, 0.45),
]

class LifestealerBullet:
    """Visual: a small red orb flying toward a target enemy. Deals damage on arrival."""
    def __init__(self, ox, oy, target, damage, tracker_ref, tracker_key):
        self.x=float(ox); self.y=float(oy)
        self.target=target; self.alive=True
        self.speed=420.0
        self.damage=damage
        self._tracker=tracker_ref
        self._tkey=tracker_key
        self._hit=False
    def update(self, dt):
        if not self.target.alive:
            self.alive=False; return
        dx=self.target.x-self.x; dy=self.target.y-self.y
        d=math.hypot(dx,dy)
        if d<10:
            # Hit! Deal damage now
            if not self._hit:
                self._hit=True
                self.target.take_damage(self.damage)
                self._tracker[self._tkey]=self._tracker.get(self._tkey,0)+self.damage
            self.alive=False; return
        step=self.speed*dt
        self.x+=dx/d*step; self.y+=dy/d*step
    def draw(self, surf):
        cx,cy=int(self.x),int(self.y)
        s=pygame.Surface((20,20),pygame.SRCALPHA)
        pygame.draw.circle(s,(220,40,80,80),(10,10),8)
        pygame.draw.circle(s,(255,100,120,200),(10,10),5)
        pygame.draw.circle(s,(255,200,210,255),(10,10),2)
        surf.blit(s,(cx-10,cy-10))


class Lifestealer(Unit):
    PLACE_COST=400; COLOR=C_LIFESTEALER; NAME="Lifestealer"; hidden_detection=False

    def __init__(self, px, py):
        super().__init__(px,py)
        # Maps enemy id → total damage Lifestealer dealt to it (only from landed hits)
        self._dmg_tracker = {}
        self._bullets = []
        self._laser_t = 0.0
        self._apply_level()

    def _apply_level(self):
        d,fr,r,_,mp=LIFESTEALER_LEVELS[self.level]
        self.damage=d; self.firerate=fr; self.range_tiles=r; self.money_pct=mp

    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(LIFESTEALER_LEVELS): return None
        return LIFESTEALER_LEVELS[nxt][3]

    def upgrade(self):
        nxt=self.level+1
        if nxt<len(LIFESTEALER_LEVELS): self.level=nxt; self._apply_level()

    def _calc_reward(self, enemy):
        return max(1, int(enemy.maxhp * self.money_pct))

    def update(self, dt, enemies, effects, money):
        self._laser_t+=dt
        if self.cd_left>0: self.cd_left-=dt

        # Fire — spawn bullet that will deal damage when it lands
        targets=self._get_rightmost(enemies,1)
        if self.cd_left<=0 and targets:
            t=targets[0]
            self.cd_left=self.firerate
            eid=id(t)
            self._bullets.append(LifestealerBullet(
                self.px, self.py, t,
                self.damage, self._dmg_tracker, eid
            ))
            # total_damage tracked on hit inside bullet, but we track shots fired here for display
            self.total_damage+=self.damage

        # Update bullets (damage dealt inside bullet.update on arrival)
        for b in self._bullets: b.update(dt)
        self._bullets=[b for b in self._bullets if b.alive]

        # Check for kills / threshold — gather rewards
        earned=0
        dead_ids=set()
        for e in enemies:
            eid=id(e)
            if eid not in self._dmg_tracker: continue
            dealt=self._dmg_tracker[eid]
            threshold=e.maxhp*0.25
            if dealt>=threshold and not e.alive:
                earned+=self._calc_reward(e)
                dead_ids.add(eid)
        for eid in dead_ids:
            del self._dmg_tracker[eid]

        # Clean up trackers for enemies no longer in list
        alive_ids={id(e) for e in enemies}
        stale=[k for k in list(self._dmg_tracker) if k not in alive_ids]
        for k in stale: del self._dmg_tracker[k]

        self._pending_money=earned

    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        pygame.draw.circle(surf,C_LIFESTEALER_DARK,(cx,cy),27)
        pygame.draw.circle(surf,C_LIFESTEALER,(cx,cy),20)
        # Inner ring detail
        pygame.draw.circle(surf,(200,60,100),(cx,cy),20,2)
        # Cross / drain symbol
        pygame.draw.line(surf,(255,100,140),(cx,cy-13),(cx,cy+13),3)
        pygame.draw.line(surf,(255,100,140),(cx-9,cy-4),(cx+9,cy-4),3)
        # Fang drops at bottom
        for dx2 in [-7,7]:
            pts=[(cx+dx2,cy+13),(cx+dx2-3,cy+21),(cx+dx2,cy+25),(cx+dx2+3,cy+21)]
            pygame.draw.polygon(surf,(220,50,80),pts)
        # Rim glow
        pygame.draw.circle(surf,(255,80,120),(cx,cy),27,2)
        for i in range(self.level):
            pygame.draw.circle(surf,C_GOLD,(cx-7+i*7,cy+36),3)
        for b in self._bullets: b.draw(surf)

    def get_info(self):
        return {"Damage":self.damage,"Range":self.range_tiles,
                "Firerate":f"{self.firerate:.3f}","Money":f"{int(self.money_pct*100)}% HP"}


# ── Archer ─────────────────────────────────────────────────────────────────────
C_ARCHER      = (160, 100, 50)
C_ARCHER_DARK = (80,  45,  15)

# (damage, firerate, range_tiles, upgrade_cost, pierce_count)
ARCHER_LEVELS = [
    (4,  0.650, 5.5, None, 2),
    (4,  0.600, 5.5, 350,  3),
    (5,  0.600, 6.0, 600,  3),
    (7,  0.600, 6.0, 800,  4),
    (8,  0.600, 6.0, 1300, 5),
    (10, 0.600, 6.5, 1700, 6),
]

class ArcherArrow:
    """Arrow that homes toward its target — cannot miss."""
    def __init__(self, ox, oy, target, damage, pierce, flame=False, ice=False):
        self.x=float(ox); self.y=float(oy)
        self._target=target
        dx=target.x-ox; dy=target.y-oy
        d=math.hypot(dx,dy) or 1
        self.vx=dx/d; self.vy=dy/d
        self.speed=500.0
        self.damage=damage
        self.pierce_left=pierce
        self.alive=True
        self._hit_ids=set()
        self._dist_left=900.0
        self.flame=flame
        self.ice=ice
    def update(self, dt, enemies):
        if not self.alive: return
        step=self.speed*dt
        # Home toward primary target only if not yet hit
        if self._target and self._target.alive and id(self._target) not in self._hit_ids:
            dx=self._target.x-self.x; dy=self._target.y-self.y
            d=math.hypot(dx,dy) or 1
            self.vx=dx/d; self.vy=dy/d
        self.x+=self.vx*step; self.y+=self.vy*step
        self._dist_left-=step
        if self._dist_left<=0: self.alive=False; return
        for e in enemies:
            if not e.alive: continue
            if id(e) in self._hit_ids: continue
            if math.hypot(e.x-self.x, e.y-self.y) < e.radius+6:
                e.take_damage(self.damage)
                self._hit_ids.add(id(e))
                if self.flame:
                    e._fire_timer=3.0*_dm(); e._fire_tick=0.0
                if self.ice and not getattr(e,'_frost_frozen',False):
                    if getattr(e,'SLOW_RESISTANCE',0.0) < 1.0:
                        if not getattr(e,'_ice_arrow_slowed',False):
                            e._ice_arrow_orig_speed=e.speed
                        e._ice_arrow_slowed=True
                        e._ice_arrow_timer=0.6
                        e.speed=e._ice_arrow_orig_speed*0.55
                self.pierce_left-=1
                if self.pierce_left<=0:
                    self.alive=False; return
                # After hitting primary target, keep flying straight — no retarget
    def draw(self, surf):
        if not self.alive: return
        tail_x=self.x-self.vx*12; tail_y=self.y-self.vy*12
        if self.flame:
            pygame.draw.line(surf,(255,120,20),(int(tail_x),int(tail_y)),(int(self.x),int(self.y)),3)
            pygame.draw.circle(surf,(255,200,50),(int(self.x),int(self.y)),4)
        elif self.ice:
            pygame.draw.line(surf,(100,200,255),(int(tail_x),int(tail_y)),(int(self.x),int(self.y)),3)
            pygame.draw.circle(surf,(200,240,255),(int(self.x),int(self.y)),4)
        else:
            pygame.draw.line(surf,(100,60,20),(int(tail_x),int(tail_y)),(int(self.x),int(self.y)),3)
            pygame.draw.circle(surf,(200,140,60),(int(self.x),int(self.y)),3)


class Archer(Unit):
    PLACE_COST=400; COLOR=C_ARCHER; NAME="Archer"; hidden_detection=False

    def __init__(self, px, py):
        super().__init__(px,py)
        self._arrows=[]
        self._anim_t=0.0
        self.arrow_mode="arrow"  # "arrow", "ice_arrow", "flame_arrow"
        self._aim_angle=0.0      # radians, direction archer faces
        self._apply_level()

    def _apply_level(self):
        d,fr,r,_,pc=ARCHER_LEVELS[self.level]
        self.damage=d; self.firerate=fr; self.range_tiles=r; self.pierce=pc
        self.hidden_detection=(self.level>=4)

    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(ARCHER_LEVELS): return None
        return ARCHER_LEVELS[nxt][3]

    def upgrade(self):
        nxt=self.level+1
        if nxt<len(ARCHER_LEVELS): self.level=nxt; self._apply_level()

    def update(self, dt, enemies, effects, money):
        self._anim_t+=dt
        if self.cd_left>0: self.cd_left-=dt

        targets=self._get_rightmost(enemies,1)
        if self.cd_left<=0 and targets:
            t=targets[0]
            dx=t.x-self.px; dy=t.y-self.py
            self._aim_angle=math.atan2(dy,dx)
            self.cd_left=self.firerate
            self.total_damage+=self.damage
            use_flame = (self.arrow_mode=="flame_arrow" and self.level>=3)
            use_ice   = (self.arrow_mode=="ice_arrow"   and self.level>=2)
            self._arrows.append(ArcherArrow(self.px,self.py,t,self.damage,self.pierce,
                                             flame=use_flame, ice=use_ice))

        for a in self._arrows: a.update(dt, enemies)
        self._arrows=[a for a in self._arrows if a.alive]

        # Fire DoT tick on burning enemies
        for e in enemies:
            if not e.alive: continue
            ft=getattr(e,'_fire_timer',0)
            if ft>0:
                e._fire_timer=max(0, ft-dt)
                e._fire_tick=getattr(e,'_fire_tick',0)+dt
                if e._fire_tick>=0.5:
                    e._fire_tick-=0.5
                    e.take_damage(2)
            # Ice arrow slow tick
            if getattr(e,'_ice_arrow_slowed',False):
                e._ice_arrow_timer=getattr(e,'_ice_arrow_timer',0)-dt
                if e._ice_arrow_timer<=0:
                    e._ice_arrow_slowed=False
                    orig=getattr(e,'_ice_arrow_orig_speed',None)
                    if orig is not None: e.speed=orig

    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        # Base circles
        pygame.draw.circle(surf,C_ARCHER_DARK,(cx,cy),27)
        pygame.draw.circle(surf,C_ARCHER,(cx,cy),20)

        # Draw bow + arrow rotated toward aim angle
        # Build on a small surface centered at (32,32), then rotate and blit
        SIZE=66
        bow_surf=pygame.Surface((SIZE,SIZE),pygame.SRCALPHA)
        bx,by=SIZE//2,SIZE//2  # center of bow surface

        # cos/sin for perpendicular (bow arm is perpendicular to arrow direction)
        a=self._aim_angle
        ca=math.cos(a); sa=math.sin(a)
        # perpendicular direction (90 degrees CCW)
        pa=-sa; pb=ca

        # Arrow shaft: from -14 to +18 along aim direction
        ax0=int(bx+ca*(-14)); ay0=int(by+sa*(-14))
        ax1=int(bx+ca*18);    ay1=int(by+sa*18)
        pygame.draw.line(bow_surf,(210,160,80),(ax0,ay0),(ax1,ay1),2)

        # Arrowhead triangle at tip
        tip_x=bx+ca*18; tip_y=by+sa*18
        perp_x=pa*5;    perp_y=pb*5
        back_x=bx+ca*12; back_y=by+sa*12
        pygame.draw.polygon(bow_surf,(255,210,100),[
            (int(tip_x),int(tip_y)),
            (int(back_x+perp_x),int(back_y+perp_y)),
            (int(back_x-perp_x),int(back_y-perp_y))
        ])

        # Fletching at tail
        tail_x=bx+ca*(-14); tail_y=by+sa*(-14)
        pygame.draw.line(bow_surf,(180,120,60),
            (int(tail_x),int(tail_y)),
            (int(tail_x+pa*6-ca*4),int(tail_y+pb*6-sa*4)),2)
        pygame.draw.line(bow_surf,(180,120,60),
            (int(tail_x),int(tail_y)),
            (int(tail_x-pa*6-ca*4),int(tail_y-pb*6-sa*4)),2)

        # Bow arc: perpendicular to arrow, centered at a point slightly behind aim direction
        bow_cx=int(bx+ca*(-8)); bow_cy=int(by+sa*(-8))
        bow_arm=16
        pygame.draw.line(bow_surf,(220,170,90),
            (int(bow_cx+pa*bow_arm),int(bow_cy+pb*bow_arm)),
            (int(bow_cx-pa*bow_arm),int(bow_cy-pb*bow_arm)),3)
        # Bowstring
        pygame.draw.line(bow_surf,(200,200,180),
            (int(bow_cx+pa*bow_arm),int(bow_cy+pb*bow_arm)),
            (int(bx+ca*2),int(by+sa*2)),1)
        pygame.draw.line(bow_surf,(200,200,180),
            (int(bow_cx-pa*bow_arm),int(bow_cy-pb*bow_arm)),
            (int(bx+ca*2),int(by+sa*2)),1)

        surf.blit(bow_surf,(cx-SIZE//2,cy-SIZE//2))

        if self.hidden_detection:
            pygame.draw.circle(surf,(100,255,100),(cx+21,cy-21),6)
        for i in range(self.level):
            pygame.draw.circle(surf,C_GOLD,(cx-14+i*6,cy+36),3)
        for a in self._arrows: a.draw(surf)

    def get_info(self):
        info={"Damage":self.damage,"Range":self.range_tiles,
              "Firerate":f"{self.firerate:.3f}","Pierce":self.pierce,
              "HidDet":"YES" if self.hidden_detection else "no"}
        if self.arrow_mode=="flame_arrow" and self.level>=3: info["FlameArrow"]="ON"
        if self.arrow_mode=="ice_arrow"   and self.level>=2: info["IceArrow"]="ON"
        return info


# ── Farm ───────────────────────────────────────────────────────────────────────
C_FARM      = (80, 180, 60)
C_FARM_DARK = (40, 90,  25)

# (income_per_wave, upgrade_cost)
FARM_LEVELS = [
    (50,   None),
    (100,  200),
    (225,  600),
    (500,  1200),
    (900,  2500),
    (1600, 4500),
]

class Farm(Unit):
    PLACE_COST=250; COLOR=C_FARM; NAME="Farm"; hidden_detection=False
    range_tiles=0

    def __init__(self, px, py):
        super().__init__(px, py)
        self._anim_t=0.0
        self._apply_level()

    def _apply_level(self):
        self.income, _ = FARM_LEVELS[self.level]

    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(FARM_LEVELS): return None
        return FARM_LEVELS[nxt][1]

    def upgrade(self):
        if self.level<len(FARM_LEVELS)-1:
            self.level+=1; self._apply_level()

    def update(self, dt, enemies, effects, money):
        self._anim_t+=dt

    def draw_range(self, surf): pass  # Farm has no range

    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        # Leaf spikes around the circle
        for i in range(6):
            a=math.radians(i*60-90)
            tip_x=cx+int(math.cos(a)*33); tip_y=cy+int(math.sin(a)*33)
            l_x=cx+int(math.cos(a-0.4)*22); l_y=cy+int(math.sin(a-0.4)*22)
            r_x=cx+int(math.cos(a+0.4)*22); r_y=cy+int(math.sin(a+0.4)*22)
            pygame.draw.polygon(surf,(50,140,35),[(tip_x,tip_y),(l_x,l_y),(r_x,r_y)])
        pygame.draw.circle(surf,C_FARM_DARK,(cx,cy),27)
        pygame.draw.circle(surf,C_FARM,(cx,cy),20)
        # Coin ring detail
        pygame.draw.circle(surf,(100,210,70),(cx,cy),20,2)
        ico=load_icon("money_ico",27)
        if ico:
            surf.blit(ico,(cx-13,cy-13))
        else:
            txt(surf,"$",(cx,cy),C_GOLD,font_sm,center=True)
        for i in range(self.level):
            pygame.draw.circle(surf,C_GOLD,(cx-14+i*6,cy+36),3)

    def get_info(self):
        return {"Income":f"+{self.income}/wave","Level":self.level}


# ── Red Ball ───────────────────────────────────────────────────────────────────
C_REDBALL      = (220, 40,  40)
C_REDBALL_DARK = (120, 10,  10)

# (damage, firerate, upgrade_cost)  — range is always 7
REDBALL_LEVELS = [
    (15,  0.7, None),
    (25,  0.8, 750),
    (30,  0.8, 1250),
    (75,  0.6, 3000),
    (150, 0.6, 4000),
]

class RedBall(Unit):
    PLACE_COST=1000; COLOR=C_REDBALL; NAME="Red Ball"; hidden_detection=False
    RANGE_TILES=7

    def __init__(self, px, py):
        super().__init__(px,py)
        self._home_x=float(px); self._home_y=float(py)
        self._jump_x=float(px); self._jump_y=float(py)
        self._state="idle"   # idle | jumping | returning
        self._jump_speed=600.0
        self._target=None
        self.range_tiles=self.RANGE_TILES
        self._apply_level()

    def _apply_level(self):
        d,fr,_=REDBALL_LEVELS[self.level]
        self.damage=d; self.firerate=fr
        # hidden_detection unlocks at level 2 (3rd upgrade)
        self.hidden_detection = self.level >= 2

    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(REDBALL_LEVELS): return None
        return REDBALL_LEVELS[nxt][2]

    def upgrade(self):
        nxt=self.level+1
        if nxt<len(REDBALL_LEVELS): self.level=nxt; self._apply_level()

    def _get_rightmost(self, enemies, count=1):
        r=self.range_tiles*TILE; targets=[]
        for e in enemies:
            if not e.alive: continue
            if e.IS_HIDDEN and not self.hidden_detection: continue
            if dist((e.x,e.y),(self._home_x,self._home_y))<=r:
                targets.append(e)
        targets.sort(key=lambda e:-e.x); return targets[:count]

    def update(self, dt, enemies, effects, money):
        if self.cd_left>0: self.cd_left-=dt

        if self._state=="idle":
            if self.cd_left<=0:
                targets=self._get_rightmost(enemies,1)
                if targets:
                    self._target=targets[0]
                    self._jump_x=targets[0].x; self._jump_y=targets[0].y
                    self._state="jumping"
        elif self._state=="jumping":
            # Update target position while jumping
            if self._target and self._target.alive:
                self._jump_x=self._target.x; self._jump_y=self._target.y
            dx=self._jump_x-self.px; dy=self._jump_y-self.py
            d=math.hypot(dx,dy)
            step=self._jump_speed*dt
            if d<=step+2:
                # Hit
                self.px=self._jump_x; self.py=self._jump_y
                if self._target and self._target.alive:
                    self._target.take_damage(self.damage)
                    self.total_damage+=self.damage
                self._state="returning"
                self._target=None
                self.cd_left=self.firerate
            else:
                self.px+=dx/d*step; self.py+=dy/d*step
        elif self._state=="returning":
            dx=self._home_x-self.px; dy=self._home_y-self.py
            d=math.hypot(dx,dy)
            step=self._jump_speed*dt
            if d<=step+2:
                self.px=self._home_x; self.py=self._home_y
                self._state="idle"
            else:
                self.px+=dx/d*step; self.py+=dy/d*step

    def draw(self, surf):
        cx,cy=int(self.px),int(self.py)
        pygame.draw.circle(surf,C_REDBALL_DARK,(cx,cy),24)
        pygame.draw.circle(surf,C_REDBALL,(cx,cy),20)
        # Seam lines (like a cannonball / soccer ball)
        pygame.draw.arc(surf,(160,20,20),pygame.Rect(cx-14,cy-18,28,20),
                        math.radians(10),math.radians(170),2)
        pygame.draw.arc(surf,(160,20,20),pygame.Rect(cx-14,cy-2,28,20),
                        math.radians(190),math.radians(350),2)
        pygame.draw.line(surf,(160,20,20),(cx-20,cy),(cx+20,cy),2)
        # Bright spot (top-left sheen)
        pygame.draw.circle(surf,(255,100,100),(cx-7,cy-7),5)
        pygame.draw.circle(surf,(255,160,160),(cx-8,cy-8),2)
        # Dark rim
        pygame.draw.circle(surf,(180,20,20),(cx,cy),24,2)
        for i in range(self.level):
            pygame.draw.circle(surf,C_GOLD,(cx-10+i*6,cy+27),3)

    def draw_range(self, surf):
        r=int(self.RANGE_TILES*TILE)
        # Use home position when placed (ball may be jumping); px/py during drag
        ax=int(self._home_x); ay=int(self._home_y)
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(255,255,255,22),(r,r),r)
        pygame.draw.circle(s,(255,255,255,60),(r,r),r,2)
        surf.blit(s,(ax-r,ay-r))

    def get_info(self):
        return {"Damage":self.damage,"Range":self.RANGE_TILES,
                "Firerate":f"{self.firerate:.1f}",
                "HidDet":"YES" if self.hidden_detection else "no"}


CONSOLE_HELP=["help            - show all commands",
              "cash <N>        - give N money",
              "hp <N>          - set player hp to N",
              "skip            - skip to next wave",
              "spawn_enemy <t> - spawn enemy by type",
              "spawn_enemy help- list all enemy types",
              "upgrade_all     - upgrade all placed units to max level",
              "snep - toggle wave spawning",
              "fk_test - trigger fallen wave 40 (music + Fallen King)",
              "fs_test - trigger frosty wave 40 (music + Frost Spirit)",
              "5       - toggle x5000 damage for all units"]

SPAWN_MAP={
    "normal":           lambda w: Enemy(w),
    "hidden":           lambda w: HiddenEnemy(w),
    "breaker":          lambda w: BreakerEnemy(w),
    "armored":          lambda w: ArmoredEnemy(w),
    "scout":            lambda w: ScoutEnemy(w),
    "slow":             lambda w: TankEnemy(w),
    "normalboss":       lambda w: NormalBoss(w),
    "slowboss":         lambda w: SlowBoss(w),
    "hiddenboss":       lambda w: HiddenBoss(w),
    "fastboss":         lambda w: FastBoss(),
    "necromancer":      lambda w: Necromancer(w),
    "gravedigger":      lambda w: GraveDigger(w),
    "optimusprime":     lambda w: OtchimusPrime(),
    "abnormal":         lambda w: AbnormalEnemy(w),
    "quick":            lambda w: QuickEnemy(w),
    "skeleton":         lambda w: SkeletonEnemy(w),
    "fallendreg":       lambda w: FallenDreg(w),
    "fallensquire":     lambda w: FallenSquire(w),
    "fallensoul":       lambda w: FallenSoul(w),
    "fallen":           lambda w: FallenEnemy(w),
    "fallengiant":      lambda w: FallenGiant(w),
    "fallenhazmat":     lambda w: FallenHazmat(w),
    "possessedarmor":   lambda w: PossessedArmor(w),
    "fallennecro":      lambda w: FallenNecromancer(w),
    "corruptedfallen":  lambda w: CorruptedFallen(w),
    "fallenjester":     lambda w: FallenJester(w),
    "necroticskeleton": lambda w: NecroticSkeleton(w),
    "fallenbreaker":    lambda w: FallenBreaker(w),
    "fallenrusher":     lambda w: FallenRusher(w),
    "fallenguard":      lambda w: FallenHonorGuard(w),
    "fallenshield":     lambda w: FallenShield(w),
    "fallenhero":       lambda w: FallenHero(w),
    "fallenking":       lambda w: FallenKing(w),
}
# ── Freezer ────────────────────────────────────────────────────────────────────
C_FREEZER      = (80, 200, 255)
C_FREEZER_DARK = (20, 70, 120)

# (damage, firerate, range_tiles, upgrade_cost, slow_pct, slow_dur)
FREEZER_LEVELS = [
    (3,  0.9, 4.0, None, 0.05, 3.0),   # lv0
    (5,  0.7, 4.5, 300,  0.10, 3.0),   # lv1
    (8,  0.7, 5.0, 500,  0.10, 3.0),   # lv2
    (10, 0.5, 5.5, 700,  0.12, 4.0),   # lv3
    (15, 0.3, 6.0, 1200, 0.15, 5.0),   # lv4 (max)
]

class FreezerBullet:
    """Ice bullet that homes to target, deals damage and slows on hit."""
    def __init__(self, ox, oy, target, damage, slow_pct, slow_dur):
        self.x = float(ox); self.y = float(oy)
        self.target = target
        self.speed = 460.0
        self.damage = damage
        self.slow_pct = slow_pct
        self.slow_dur = slow_dur
        self.alive = True
        self._hit = False

    def update(self, dt):
        if not self.target.alive:
            self.alive = False; return
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        d = math.hypot(dx, dy)
        if d < 10:
            if not self._hit:
                self._hit = True
                self.target.take_damage(self.damage)
                # Apply slow: stack with existing slow (keep strongest)
                cur_slow = getattr(self.target, '_freezer_slow', 0.0)
                if self.slow_pct > cur_slow:
                    orig = getattr(self.target, '_freezer_orig_speed', None)
                    if orig is None:
                        self.target._freezer_orig_speed = self.target.speed
                    self.target._freezer_slow = self.slow_pct
                    self.target.speed = self.target._freezer_orig_speed * (1.0 - self.slow_pct)
                # Refresh/extend timer
                self.target._freezer_timer = self.slow_dur
            self.alive = False; return
        step = self.speed * dt
        self.x += dx / d * step
        self.y += dy / d * step

    def draw(self, surf):
        if not self.alive: return
        cx, cy = int(self.x), int(self.y)
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 200, 255, 80),  (10, 10), 8)
        pygame.draw.circle(s, (180, 240, 255, 220), (10, 10), 5)
        pygame.draw.circle(s, (240, 255, 255, 255), (10, 10), 2)
        surf.blit(s, (cx - 10, cy - 10))


class Freezer(Unit):
    PLACE_COST = 400; COLOR = C_FREEZER; NAME = "Freezer"; hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._bullets = []
        self._apply_level()

    def _apply_level(self):
        d, fr, r, _, sp, sd = FREEZER_LEVELS[self.level]
        self.damage = d; self.firerate = fr; self.range_tiles = r
        self._slow_pct = sp; self._slow_dur = sd

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(FREEZER_LEVELS): return None
        return FREEZER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(FREEZER_LEVELS): self.level = nxt; self._apply_level()

    def update(self, dt, enemies, effects, money):
        if self.cd_left > 0: self.cd_left -= dt
        # Tick slow timers on all enemies
        for e in enemies:
            if not e.alive: continue
            t = getattr(e, '_freezer_timer', 0.0)
            if t > 0:
                e._freezer_timer = t - dt
                if e._freezer_timer <= 0:
                    # Restore speed
                    orig = getattr(e, '_freezer_orig_speed', None)
                    if orig is not None:
                        e.speed = orig
                    e._freezer_slow = 0.0
                    e._freezer_orig_speed = None

        targets = self._get_rightmost(enemies, 1)
        if self.cd_left <= 0 and targets:
            t = targets[0]
            self.cd_left = self.firerate
            self._bullets.append(FreezerBullet(
                self.px, self.py, t,
                self.damage, self._slow_pct, self._slow_dur
            ))
            self.total_damage += self.damage

        for b in self._bullets: b.update(dt)
        self._bullets = [b for b in self._bullets if b.alive]

    def draw(self, surf):
        t = pygame.time.get_ticks() * 0.001
        cx, cy = int(self.px), int(self.py)
        # Outer ring
        pygame.draw.circle(surf, C_FREEZER_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_FREEZER, (cx, cy), 21)
        # Snowflake arms (6-pointed)
        for i in range(6):
            a = math.radians(i * 60 + t * 15)
            ex = cx + int(math.cos(a) * 16)
            ey = cy + int(math.sin(a) * 16)
            pygame.draw.line(surf, (200, 240, 255), (cx, cy), (ex, ey), 2)
            # Small branch off each arm
            for side in (-1, 1):
                ba = a + math.radians(side * 45)
                bx = cx + int(math.cos(a) * 9) + int(math.cos(ba) * 5)
                bby = cy + int(math.sin(a) * 9) + int(math.sin(ba) * 5)
                pygame.draw.line(surf, (160, 220, 255),
                                 (cx + int(math.cos(a) * 9), cy + int(math.sin(a) * 9)),
                                 (bx, bby), 1)
        # Centre dot
        pygame.draw.circle(surf, (240, 255, 255), (cx, cy), 5)
        pygame.draw.circle(surf, C_FREEZER, (cx, cy), 27, 2)
        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_FREEZER, (cx - 7 + i * 7, cy + 36), 3)
        # Bullets
        for b in self._bullets: b.draw(surf)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,22), (r, r), r)
        pygame.draw.circle(s, (255,255,255,60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        return {"Damage": self.damage, "Range": self.range_tiles,
                "Firerate": f"{self.firerate:.1f}",
                "Slow": f"{int(self._slow_pct*100)}% / {self._slow_dur:.0f}s"}


# ── FrostBlaster ───────────────────────────────────────────────────────────────
C_FROSTBLASTER      = (80, 200, 255)
C_FROSTBLASTER_DARK = (20, 60, 110)

# Tuple layout:
#   (damage, firerate, range_tiles, upgrade_cost,
#    hidden_detection, slow_pct, slow_dur, freeze_hits, freeze_dur,
#    armor_shred,     defense_drop,  proj_speed)
#
# slow_pct   = fraction of speed removed (0.50 = 50 % slow)
# slow_dur   = seconds the slow lasts
# freeze_hits= how many hits on same enemy to trigger freeze (0 = no freeze)
# freeze_dur = seconds of freeze
# armor_shred= flat ARMOR reduction applied once per enemy on first hit (lv2+)
# defense_drop=flat extra damage multiplier via defense_drop on lv4 (35 %)
# proj_speed = bullet travel speed
FROSTBLASTER_LEVELS = [
    # lv0 – place cost 800
    (4,  0.608, 6.0, None, False, 0.50, 0.45, 3, 0.45, 0.00, 0.00, 420.0),
    # lv1 – upgrade 350
    (4,  0.508, 7.2,  350, True,  0.50, 0.60, 3, 0.60, 0.00, 0.00, 420.0),
    # lv2 – upgrade 1350
    (7,  0.508, 7.2, 1350, True,  0.75, 0.60, 3, 0.60, 0.15, 0.00, 420.0),
    # lv3 – upgrade 3200
    (8,  0.308, 7.8, 3200, True,  0.75, 0.60, 3, 0.60, 0.15, 0.00, 420.0),
    # lv4 – upgrade 8500
    (53, 0.908,10.2, 8500, True,  0.75, 1.50, 3, 1.50, 0.15, 0.35, 450.0),
]


class FrostBlasterBullet:
    """
    Piercing ice bullet – no pierce limit, hits every enemy it passes through.
    Homing: continuously steers toward its primary target so it never misses.
    Applies slow (and optionally freeze stacks) on each enemy hit.
    """
    def __init__(self, ox, oy, target, damage, slow_pct, slow_dur,
                 freeze_hits, freeze_dur, armor_shred, defense_drop, speed,
                 owner):
        self.x = float(ox); self.y = float(oy)
        self._target = target   # keep reference for homing
        # Initial direction
        dx = target.x - ox; dy = target.y - oy
        d = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.speed = speed
        self.damage = damage
        self.slow_pct = slow_pct
        self.slow_dur = slow_dur
        self.freeze_hits = freeze_hits
        self.freeze_dur = freeze_dur
        self.armor_shred = armor_shred
        self.defense_drop = defense_drop
        self.owner = owner
        self.alive = True
        self._hit_ids = set()
        self._dist_left = 1100.0
        self._homed = False  # True once target is hit or dead

    def update(self, dt, enemies):
        if not self.alive: return

        # Homing: steer toward primary target while it's alive and not yet hit
        if self._target and self._target.alive and id(self._target) not in self._hit_ids:
            dx = self._target.x - self.x
            dy = self._target.y - self.y
            d = math.hypot(dx, dy)
            if d > 1:
                # Perfect tracking — always point directly at target
                self.vx = dx / d
                self.vy = dy / d

        step = self.speed * dt
        self.x += self.vx * step
        self.y += self.vy * step
        self._dist_left -= step
        if self._dist_left <= 0:
            self.alive = False; return
        for e in enemies:
            if not e.alive: continue
            if id(e) in self._hit_ids: continue
            if math.hypot(e.x - self.x, e.y - self.y) < e.radius + 7:
                self._hit_ids.add(id(e))
                if self.armor_shred > 0 and not getattr(e, '_fb_armor_shredded', False):
                    e._fb_armor_shredded = True
                    e.ARMOR = max(0.0, e.ARMOR - self.armor_shred)
                eff_dmg = self.damage * (1.0 + self.defense_drop) if self.defense_drop > 0 else self.damage
                e.take_damage(eff_dmg)
                self.owner.total_damage += eff_dmg
                orig = getattr(e, '_fb_orig_speed', None)
                if orig is None:
                    e._fb_orig_speed = e.speed
                cur_slow = getattr(e, '_fb_slow_pct', 0.0)
                if getattr(e, 'SLOW_RESISTANCE', 0.0) >= 1.0:
                    e._fb_slow_timer = self.slow_dur
                elif self.slow_pct > cur_slow:
                    e._fb_slow_pct = self.slow_pct
                    resistance = getattr(e, 'SLOW_RESISTANCE', 0.0)
                    e.speed = e._fb_orig_speed * (1.0 - self.slow_pct * resistance)
                    e._fb_slow_timer = self.slow_dur * _dm()
                if self.freeze_hits > 0:
                    hits = getattr(e, '_fb_hit_count', 0) + 1
                    e._fb_hit_count = hits
                    if hits >= self.freeze_hits:
                        e._fb_hit_count = 0
                        e.frozen = True
                        e._fb_freeze_timer = getattr(e, '_fb_freeze_timer', 0) + self.freeze_dur * _dm()

    def draw(self, surf):
        if not self.alive: return
        cx, cy = int(self.x), int(self.y)
        tail_x = self.x - self.vx * 14; tail_y = self.y - self.vy * 14
        # Glowing ice bolt
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (80, 180, 255, 60),   (12, 12), 10)
        pygame.draw.circle(s, (160, 230, 255, 200),  (12, 12), 6)
        pygame.draw.circle(s, (220, 248, 255, 255),  (12, 12), 3)
        surf.blit(s, (cx - 12, cy - 12))
        pygame.draw.line(surf, (120, 200, 255),
                         (int(tail_x), int(tail_y)), (cx, cy), 3)


class FrostBlaster(Unit):
    PLACE_COST = 800
    COLOR = C_FROSTBLASTER
    NAME = "Frost Blaster"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._bullets = []
        self._anim_t = 0.0
        self._aim_angle = 0.0
        self._apply_level()

    def _apply_level(self):
        row = FROSTBLASTER_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self.hidden_detection, self._slow_pct, self._slow_dur,
         self._freeze_hits, self._freeze_dur,
         self._armor_shred, self._defense_drop, self._proj_speed) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(FROSTBLASTER_LEVELS): return None
        return FROSTBLASTER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(FROSTBLASTER_LEVELS):
            self.level = nxt; self._apply_level()

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt
        if self.cd_left > 0: self.cd_left -= dt

        # Tick slow timers on all enemies
        for e in enemies:
            if not e.alive: continue
            # Slow timer
            st = getattr(e, '_fb_slow_timer', 0.0)
            if st > 0:
                e._fb_slow_timer = st - dt
                if e._fb_slow_timer <= 0:
                    orig = getattr(e, '_fb_orig_speed', None)
                    if orig is not None: e.speed = orig
                    e._fb_orig_speed = None
                    e._fb_slow_pct = 0.0
            # Freeze timer
            ft = getattr(e, '_fb_freeze_timer', 0.0)
            if ft > 0 and getattr(e, 'frozen', False):
                e._fb_freeze_timer = ft - dt
                if e._fb_freeze_timer <= 0:
                    e.frozen = False
                    e._fb_freeze_timer = 0.0

        # Fire
        targets = self._get_rightmost(enemies, 1)
        if self.cd_left <= 0 and targets:
            t = targets[0]
            dx = t.x - self.px; dy = t.y - self.py
            self._aim_angle = math.atan2(dy, dx)
            self.cd_left = self.firerate
            self._bullets.append(FrostBlasterBullet(
                self.px, self.py, t,
                self.damage, self._slow_pct, self._slow_dur,
                self._freeze_hits, self._freeze_dur,
                self._armor_shred, self._defense_drop, self._proj_speed,
                self
            ))

        for b in self._bullets: b.update(dt, enemies)
        self._bullets = [b for b in self._bullets if b.alive]

    def draw(self, surf):
        t = self._anim_t
        cx, cy = int(self.px), int(self.py)

        # Outer dark ring with pulse
        pulse = int(abs(math.sin(t * 3)) * 4)
        pygame.draw.circle(surf, C_FROSTBLASTER_DARK, (cx, cy), 27 + pulse)
        pygame.draw.circle(surf, C_FROSTBLASTER, (cx, cy), 21)

        # Rotating ice crystal arms (4-point star, rotates slowly)
        for i in range(4):
            a = math.radians(i * 90 + t * 30)
            ex = cx + int(math.cos(a) * 16); ey = cy + int(math.sin(a) * 16)
            pygame.draw.line(surf, (180, 230, 255), (cx, cy), (ex, ey), 2)
            # Small branch tips
            for sign in (-1, 1):
                ba = a + math.radians(sign * 45)
                mx2 = cx + int(math.cos(a) * 10) + int(math.cos(ba) * 5)
                my2 = cy + int(math.sin(a) * 10) + int(math.sin(ba) * 5)
                pygame.draw.line(surf, (140, 210, 255),
                                 (cx + int(math.cos(a) * 10), cy + int(math.sin(a) * 10)),
                                 (mx2, my2), 1)

        # Aim direction indicator
        a = self._aim_angle
        ex2 = cx + int(math.cos(a) * 22); ey2 = cy + int(math.sin(a) * 22)
        pygame.draw.line(surf, (220, 248, 255), (cx, cy), (ex2, ey2), 3)
        # Tip circle
        pygame.draw.circle(surf, (220, 248, 255), (ex2, ey2), 4)

        # Centre dot
        pygame.draw.circle(surf, (240, 255, 255), (cx, cy), 5)
        pygame.draw.circle(surf, C_FROSTBLASTER, (cx, cy), 27, 2)

        # Hidden detection indicator
        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_FROSTBLASTER, (cx - 7 + i * 7, cy + 36), 3)

        # Bullets
        for b in self._bullets: b.draw(surf)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,22), (r, r), r)
        pygame.draw.circle(s, (255,255,255,60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        info = {
            "Damage":   self.damage,
            "Range":    self.range_tiles,
            "Firerate": f"{self.firerate:.3f}",
            "Slow":     f"{int(self._slow_pct*100)}%/{self._slow_dur:.2f}s",
            "Freeze":   f"x{self._freeze_hits} hits/{self._freeze_dur:.2f}s",
        }
        if self.hidden_detection: info["HidDet"] = "YES"
        if self._armor_shred > 0: info["ArmorShred"] = f"-{int(self._armor_shred*100)}%"
        if self._defense_drop > 0: info["DefDrop"] = f"-{int(self._defense_drop*100)}%"
        return info


# ── Sledger ────────────────────────────────────────────────────────────────────
C_SLEDGER      = (80, 180, 255)
C_SLEDGER_DARK = (20, 55, 110)

# Tuple layout:
#  (damage, swingrate, range_tiles, upgrade_cost,
#   max_hits,          # enemies hit per swing
#   slow_per_hit,      # fraction of speed removed per hit (stacks)
#   max_slow,          # cap on stacking slow fraction
#   slow_dur,          # seconds slow lasts after last hit
#   freeze_dur,        # seconds enemy is frozen when slow exceeds max_slow (0=no freeze)
#   double_dmg_frozen, # bool: deal 2x to already-frozen/chilled enemies
#   def_drop_per_hit,  # ARMOR drop per swing per enemy hit (0=none), max 33%
#   aftershock_dmg_pct)# fraction of damage dealt as delayed aftershock (0=none)
#
# Slow stacks up: each swing adds slow_per_hit to enemy's current slow,
# capped at max_slow.  Once slow >= max_slow the enemy is frozen for freeze_dur
# (lv3+).  A single Sledger cannot freeze the same enemy on two consecutive swings.

SLEDGER_LEVELS = [
    # lv0 – place $950
    (7,  1.208, 7.0, None, 2, 0.15, 0.45, 4.0, 0.0,  False, 0.00, 0.00),
    # lv1 – +$400
    (11, 1.208, 7.0,  400, 2, 0.25, 0.45, 4.0, 0.0,  False, 0.00, 0.00),
    # lv2 – +$1650
    (24, 1.208, 7.0, 1650, 3, 0.25, 0.45, 4.0, 0.0,  False, 0.00, 0.00),
    # lv3 – +$3200  (freeze unlocked)
    (24, 1.208, 7.0, 3200, 3, 0.30, 0.60, 4.0, 1.5,  False, 0.00, 0.00),
    # lv4 – +$8250  (double dmg to frozen, more hits, bigger slow ramp)
    (24, 1.208, 7.0, 8250, 4, 0.45, 0.80, 5.0, 2.5,  True,  0.00, 0.00),
    # lv5 – +$22500 (aftershock 20%, defense drop, 6 max hits)
    (24, 1.208, 7.0,22500, 6, 0.80, 0.80, 6.0, 1.75, True,  0.10, 0.20),
]
# Max defense drop cap
_SLEDGER_MAX_DEF_DROP = 0.33


class Sledger(Unit):
    PLACE_COST    = 950
    COLOR         = C_SLEDGER
    NAME          = "Sledger"
    hidden_detection = False   # never gains hidden detection

    def __init__(self, px, py):
        super().__init__(px, py)
        self._swing_t   = 0.0   # animation timer
        self._aim_angle = 0.0   # radians toward last target
        self._aftershocks = []  # list of (timer, x, y, vx, vy, dmg)
        self._apply_level()

    # ── level data ────────────────────────────────────────────────────────
    def _apply_level(self):
        row = SLEDGER_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._max_hits, self._slow_per_hit, self._max_slow,
         self._slow_dur, self._freeze_dur,
         self._double_frozen, self._def_drop, self._aftershock_pct) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(SLEDGER_LEVELS): return None
        return SLEDGER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(SLEDGER_LEVELS):
            self.level = nxt; self._apply_level()

    # ── helpers ────────────────────────────────────────────────────────────
    def _apply_chill(self, e):
        """Stack slow on enemy; freeze if slow exceeds max and lv3+."""
        if getattr(e, 'SLOW_RESISTANCE', 1.0) >= 1.0: return  # freeze immune
        if getattr(e, 'frozen', False): return                  # already frozen

        orig = getattr(e, '_sledger_orig_speed', None)
        if orig is None:
            e._sledger_orig_speed = e.speed

        cur  = getattr(e, '_sledger_slow', 0.0)
        new  = min(cur + self._slow_per_hit, self._max_slow)
        e._sledger_slow  = new
        e._sledger_timer = self._slow_dur
        resistance = getattr(e, 'SLOW_RESISTANCE', 1.0)
        e.speed = e._sledger_orig_speed * (1.0 - new * resistance)

        # Freeze when slow >= max (lv3+)
        if self._freeze_dur > 0 and new >= self._max_slow:
            last_frozen_by = getattr(e, '_sledger_last_frozen', None)
            if last_frozen_by is not id(self):
                e._sledger_last_frozen = id(self)
                e.frozen = True
                e._sledger_freeze_timer = self._freeze_dur * _dm()
                # Reset chill so it can build again
                e._sledger_slow = 0.0

    def _swing(self, enemies, effects):
        """Perform one hammer swing: hit up to max_hits enemies in range."""
        r = self.range_tiles * TILE
        pool = []
        for e in enemies:
            if not e.alive: continue
            if getattr(e, '_reversed', False): continue
            # No hidden detection — but at lv1+ pierce can hit hidden indirectly
            # (we just don't target them; collateral hits handled below)
            if e.IS_HIDDEN and not self.hidden_detection: continue
            if dist((e.x, e.y), (self.px, self.py)) <= r:
                pool.append(e)

        mode = getattr(self, 'target_mode', 'First')
        if   mode == "First":       pool.sort(key=lambda e: -e.x)
        elif mode == "Last":        pool.sort(key=lambda e:  e.x)
        elif mode == "Lowest HP":   pool.sort(key=lambda e:  e.hp)
        elif mode == "Highest HP":  pool.sort(key=lambda e: -e.hp)
        elif mode == "Nearest":     pool.sort(key=lambda e:  dist((e.x,e.y),(self.px,self.py)))
        elif mode == "Farthest":    pool.sort(key=lambda e: -dist((e.x,e.y),(self.px,self.py)))
        elif mode == "Random":      random.shuffle(pool)

        targets = pool[:self._max_hits]
        if not targets: return

        # Aim toward primary target
        t0 = targets[0]
        self._aim_angle = math.atan2(t0.y - self.py, t0.x - self.px)

        for e in targets:
            # Damage — double if frozen/chilled and lv4+
            is_chilled = getattr(e, '_sledger_slow', 0.0) > 0 or getattr(e, 'frozen', False)
            dmg = self.damage
            if self._double_frozen and is_chilled:
                dmg *= 2

            e.take_damage(dmg)
            self.total_damage += dmg

            # Defense drop (lv5)
            if self._def_drop > 0:
                cur_armor = e.ARMOR
                drop = min(self._def_drop, max(0.0, _SLEDGER_MAX_DEF_DROP - getattr(e, '_sledger_def_dropped', 0.0)))
                if drop > 0:
                    e.ARMOR = max(0.0, cur_armor - drop)
                    e._sledger_def_dropped = getattr(e, '_sledger_def_dropped', 0.0) + drop

            self._apply_chill(e)

            # Aftershock (lv5): delayed shard 0.4s later
            if self._aftershock_pct > 0:
                # direction away from tower toward enemy
                dx = e.x - self.px; dy = e.y - self.py
                d = math.hypot(dx, dy) or 1
                self._aftershocks.append({
                    'timer': 0.4,
                    'x': self.px, 'y': self.py,
                    'vx': dx/d * 220, 'vy': dy/d * 220,
                    'dmg': self.damage * self._aftershock_pct,
                    'hit_ids': set(),
                })

    # ── tick slow timers ───────────────────────────────────────────────────
    def _tick_slows(self, enemies, dt):
        for e in enemies:
            if not e.alive: continue
            # Freeze timer
            ft = getattr(e, '_sledger_freeze_timer', 0.0)
            if ft > 0 and getattr(e, 'frozen', False):
                e._sledger_freeze_timer = ft - dt
                if e._sledger_freeze_timer <= 0:
                    e.frozen = False
                    e._sledger_freeze_timer = 0.0
                    e._sledger_last_frozen = None
            # Chill / slow timer
            st = getattr(e, '_sledger_timer', 0.0)
            if st > 0:
                e._sledger_timer = st - dt
                if e._sledger_timer <= 0:
                    orig = getattr(e, '_sledger_orig_speed', None)
                    if orig is not None: e.speed = orig
                    e._sledger_orig_speed = None
                    e._sledger_slow = 0.0

    # ── update ─────────────────────────────────────────────────────────────
    def update(self, dt, enemies, effects, money):
        self._swing_t += dt
        if self.cd_left > 0: self.cd_left -= dt

        self._tick_slows(enemies, dt)

        # Fire swing
        if self.cd_left <= 0:
            # need at least one valid target
            r = self.range_tiles * TILE
            has_target = any(
                e.alive and not getattr(e,'_reversed',False)
                and not (e.IS_HIDDEN and not self.hidden_detection)
                and dist((e.x,e.y),(self.px,self.py)) <= r
                for e in enemies
            )
            if has_target:
                self.cd_left = self.firerate
                self._swing(enemies, effects)

        # Update aftershock shards
        new_as = []
        for s in self._aftershocks:
            s['timer'] -= dt
            if s['timer'] <= 0:
                # shard fires — deal damage to enemies near its path
                sx, sy = s['x'], s['y']
                ex2 = sx + s['vx'] * 0.4; ey2 = sy + s['vy'] * 0.4
                for e in enemies:
                    if not e.alive: continue
                    if id(e) in s['hit_ids']: continue
                    # proximity to shard line
                    if dist((e.x, e.y), (ex2, ey2)) < e.radius + 30:
                        s['hit_ids'].add(id(e))
                        e.take_damage(s['dmg'])
                        self.total_damage += s['dmg']
                        self._apply_chill(e)
            else:
                new_as.append(s)
        self._aftershocks = new_as

    # ── draw ───────────────────────────────────────────────────────────────
    def draw(self, surf):
        t  = self._swing_t
        cx, cy = int(self.px), int(self.py)

        # Body
        pygame.draw.circle(surf, C_SLEDGER_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_SLEDGER,      (cx, cy), 21)
        pygame.draw.circle(surf, (160, 220, 255), (cx, cy), 21, 2)

        # Animated hammer swinging in aim direction
        a   = self._aim_angle
        swing_offset = math.sin(t * (math.pi * 2 / self.firerate)) * 0.5  # [-0.5..0.5] rad
        ha  = a + swing_offset
        ca, sa = math.cos(ha), math.sin(ha)

        # Handle
        hx1 = cx + int(ca * 8);  hy1 = cy + int(sa * 8)
        hx2 = cx + int(ca * 26); hy2 = cy + int(sa * 26)
        pygame.draw.line(surf, (160, 200, 230), (hx1, hy1), (hx2, hy2), 4)

        # Hammerhead (rectangle rotated)
        perp_x = -sa; perp_y = ca
        head_cx = cx + int(ca * 28); head_cy = cy + int(sa * 28)
        pts = [
            (int(head_cx + perp_x * 9 - ca * 5), int(head_cy + perp_y * 9 - sa * 5)),
            (int(head_cx - perp_x * 9 - ca * 5), int(head_cy - perp_y * 9 - sa * 5)),
            (int(head_cx - perp_x * 9 + ca * 8), int(head_cy - perp_y * 9 + sa * 8)),
            (int(head_cx + perp_x * 9 + ca * 8), int(head_cy + perp_y * 9 + sa * 8)),
        ]
        pygame.draw.polygon(surf, (100, 180, 255), pts)
        pygame.draw.polygon(surf, (200, 240, 255), pts, 2)

        # Frost glow on hammerhead
        gs = pygame.Surface((30, 30), pygame.SRCALPHA)
        glow_a = int(abs(math.sin(t * 3)) * 80 + 60)
        pygame.draw.circle(gs, (80, 200, 255, glow_a), (15, 15), 14)
        surf.blit(gs, (head_cx - 15, head_cy - 15))

        # Swing arc indicator on attack
        if self.cd_left > self.firerate * 0.7:
            arc_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            arc_r    = int(self.range_tiles * TILE)
            progress = 1.0 - (self.cd_left / self.firerate)
            alpha    = int(180 * max(0, 1 - progress * 3))
            arc_col  = (100, 200, 255, alpha)
            # Draw a cone arc (60° = ±30° from aim)
            cone_steps = 12
            for i in range(cone_steps):
                angle = a - math.radians(30) + math.radians(60 * i / cone_steps)
                x1 = cx + int(math.cos(angle) * 10)
                y1 = cy + int(math.sin(angle) * 10)
                x2 = cx + int(math.cos(angle) * arc_r)
                y2 = cy + int(math.sin(angle) * arc_r)
                pygame.draw.line(arc_surf, arc_col, (x1, y1), (x2, y2), 2)
            surf.blit(arc_surf, (0, 0))

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_SLEDGER, (cx - 10 + i * 6, cy + 36), 3)

        # Aftershock trails
        for s in self._aftershocks:
            frac = 1.0 - s['timer'] / 0.4
            tx2 = int(s['x'] + s['vx'] * (0.4 - s['timer']))
            ty2 = int(s['y'] + s['vy'] * (0.4 - s['timer']))
            alpha2 = int(200 * (1 - frac))
            ash = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(ash, (140, 220, 255, alpha2), (10, 10), 8)
            surf.blit(ash, (tx2 - 10, ty2 - 10))

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,22), (r, r), r)
        pygame.draw.circle(s, (255,255,255,60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        info = {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "Hits":     self._max_hits,
            "Slow":     f"+{int(self._slow_per_hit*100)}%/hit, max {int(self._max_slow*100)}%",
        }
        if self._freeze_dur > 0:
            info["Freeze"] = f"{self._freeze_dur:.2f}s @max slow"
        if self._double_frozen:
            info["IceBreaker"] = "2x vs frozen"
        if self._def_drop > 0:
            info["DefDrop"] = f"-{int(self._def_drop*100)}%/hit"
        if self._aftershock_pct > 0:
            info["Aftershock"] = f"{int(self._aftershock_pct*100)}% dmg"
        return info


# ── Gladiator ──────────────────────────────────────────────────────────────────
C_GLADIATOR      = (220, 180, 60)
C_GLADIATOR_DARK = (80,  60,  10)

# Tuple layout:
#  (damage, swingrate, range_tiles, upgrade_cost,
#   max_hits,           # enemies hit per 180° arc swing (infinite pierce)
#   hidden_detection)   # can target hidden enemies
#
# The Gladiator swings in a 180° arc centred on its aim direction,
# hitting ALL enemies within range whose angle from the tower falls
# within that arc — up to max_hits, sorted by target_mode.
# Passive: stun-block — every 1.25 s it can absorb one incoming stun.
GLADIATOR_LEVELS = [
    # lv0 – place $500
    (5,  1.008, 5.0, None, 3,  False),
    # lv1 – +$300
    (7,  1.008, 5.0,  300, 3,  False),
    # lv2 – +$550  (hidden detection, faster swing)
    (12, 0.758, 5.0,  550, 5,  True),
    # lv3 – +$1500
    (17, 0.758, 5.0, 1500, 7,  True),
    # lv4 – +$2500 (bigger range, much faster)
    (37, 0.508, 7.0, 2500, 9,  True),
    # lv5 – +$6000
    (57, 0.508, 8.0, 6000, 10, True),
]

# How wide the arc is (degrees, total width centred on aim angle)
_GLAD_ARC_DEG = 180.0


class Gladiator(Unit):
    PLACE_COST    = 500
    COLOR         = C_GLADIATOR
    NAME          = "Gladiator"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._swing_t        = 0.0
        self._aim_angle      = 0.0
        self._stun_block_cd  = 0.0
        self._stun_blocked   = False
        self._stun_block_flash = 0.0
        self._last_swing_t   = -999.0  # time of last actual swing
        self._apply_level()

    # ── level data ────────────────────────────────────────────────────────
    def _apply_level(self):
        row = GLADIATOR_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._max_hits, self.hidden_detection) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(GLADIATOR_LEVELS): return None
        return GLADIATOR_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(GLADIATOR_LEVELS):
            self.level = nxt; self._apply_level()

    # ── stun-block passive ────────────────────────────────────────────────
    def try_block_stun(self):
        """Called when something tries to stun this unit.
        Returns True if the stun was absorbed (blocked), False if it lands."""
        if self._stun_block_cd <= 0:
            self._stun_block_cd  = 1.25
            self._stun_blocked   = True
            self._stun_block_flash = 0.4
            return True   # blocked
        return False      # stun lands normally

    # ── swing ─────────────────────────────────────────────────────────────
    def _swing(self, enemies):
        """180° arc swing: hit up to _max_hits enemies in arc, infinite pierce."""
        r = self.range_tiles * TILE
        arc_half = math.radians(_GLAD_ARC_DEG / 2)

        # Collect all enemies in range
        pool = []
        for e in enemies:
            if not e.alive: continue
            if getattr(e, '_reversed', False): continue
            if e.IS_HIDDEN and not self.hidden_detection: continue
            dx = e.x - self.px; dy = e.y - self.py
            d  = math.hypot(dx, dy)
            if d > r: continue
            pool.append(e)

        if not pool: return

        # Sort by target_mode to pick primary target, then aim arc toward it
        mode = getattr(self, 'target_mode', 'First')
        sorted_pool = list(pool)
        if   mode == "First":       sorted_pool.sort(key=lambda e: -e.x)
        elif mode == "Last":        sorted_pool.sort(key=lambda e:  e.x)
        elif mode == "Lowest HP":   sorted_pool.sort(key=lambda e:  e.hp)
        elif mode == "Highest HP":  sorted_pool.sort(key=lambda e: -e.hp)
        elif mode == "Nearest":     sorted_pool.sort(key=lambda e:  dist((e.x,e.y),(self.px,self.py)))
        elif mode == "Farthest":    sorted_pool.sort(key=lambda e: -dist((e.x,e.y),(self.px,self.py)))

        primary = sorted_pool[0]
        self._aim_angle = math.atan2(primary.y - self.py, primary.x - self.px)

        # Now filter: keep only enemies within the 180° arc
        in_arc = []
        for e in pool:
            dx = e.x - self.px; dy = e.y - self.py
            angle = math.atan2(dy, dx)
            diff  = abs(math.atan2(math.sin(angle - self._aim_angle),
                                   math.cos(angle - self._aim_angle)))
            if diff <= arc_half:
                in_arc.append(e)

        # Re-sort in_arc by the same mode and cap at max_hits
        if   mode == "First":       in_arc.sort(key=lambda e: -e.x)
        elif mode == "Last":        in_arc.sort(key=lambda e:  e.x)
        elif mode == "Lowest HP":   in_arc.sort(key=lambda e:  e.hp)
        elif mode == "Highest HP":  in_arc.sort(key=lambda e: -e.hp)
        elif mode == "Nearest":     in_arc.sort(key=lambda e:  dist((e.x,e.y),(self.px,self.py)))
        elif mode == "Farthest":    in_arc.sort(key=lambda e: -dist((e.x,e.y),(self.px,self.py)))

        targets = in_arc[:self._max_hits]

        for e in targets:
            e.take_damage(self.damage)
            self.total_damage += self.damage

    # ── update ─────────────────────────────────────────────────────────────
    def update(self, dt, enemies, effects, money):
        self._swing_t += dt
        if self.cd_left > 0: self.cd_left -= dt

        # Tick stun-block cooldown
        if self._stun_block_cd > 0:
            self._stun_block_cd = max(0.0, self._stun_block_cd - dt)
        if self._stun_block_flash > 0:
            self._stun_block_flash = max(0.0, self._stun_block_flash - dt)
            if self._stun_block_flash <= 0:
                self._stun_blocked = False

        # Need at least one valid enemy in range to swing
        if self.cd_left <= 0:
            r = self.range_tiles * TILE
            has_target = any(
                e.alive
                and not getattr(e, '_reversed', False)
                and not (e.IS_HIDDEN and not self.hidden_detection)
                and dist((e.x, e.y), (self.px, self.py)) <= r
                for e in enemies
            )
            if has_target:
                self.cd_left = self.firerate
                self._last_swing_t = self._swing_t
                self._swing(enemies)
                arc_half = math.radians(_GLAD_ARC_DEG / 2)
                for _si in range(5):
                    _a = math.degrees(self._aim_angle - arc_half + arc_half * 2 * _si / 4)
                    effects.append(SwordEffect(self.px, self.py, _a))

    # ── draw ───────────────────────────────────────────────────────────────
    def draw(self, surf):
        t  = self._swing_t
        cx, cy = int(self.px), int(self.py)

        # Body — golden warrior
        pygame.draw.circle(surf, C_GLADIATOR_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_GLADIATOR,      (cx, cy), 21)
        pygame.draw.circle(surf, (255, 230, 120),  (cx, cy), 21, 2)

        # Stun-block flash — white ring when just blocked
        if self._stun_blocked:
            flash_alpha = int(255 * (self._stun_block_flash / 0.4))
            fs = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(fs, (255, 255, 255, flash_alpha), (40, 40), 32, 4)
            surf.blit(fs, (cx - 40, cy - 40))

        # Stun-block cooldown indicator — small arc around base
        if self._stun_block_cd > 0:
            ready_frac = 1.0 - (self._stun_block_cd / 1.25)
            arc_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            # Draw filled arc (progress circle)
            angle_end = int(ready_frac * 360)
            pygame.draw.arc(arc_surf, (255, 220, 80, 180),
                            pygame.Rect(5, 5, 50, 50),
                            math.radians(-90),
                            math.radians(-90 + angle_end), 3)
            surf.blit(arc_surf, (cx - 30, cy - 30))

        # Animated sword — only swings during actual attack window
        time_since_swing2 = self._swing_t - self._last_swing_t
        if 0 < time_since_swing2 < self.firerate * 0.85:
            swing_phase = min(1.0, time_since_swing2 / (self.firerate * 0.85))
            swing_a = self._aim_angle + math.radians(90 - swing_phase * 180)
        else:
            swing_a = self._aim_angle  # idle: point toward last target

        ca, sa = math.cos(swing_a), math.sin(swing_a)
        perp_x, perp_y = -sa, ca

        # Sword handle
        hx1 = cx + int(ca * 8);  hy1 = cy + int(sa * 8)
        hx2 = cx + int(ca * 30); hy2 = cy + int(sa * 30)
        pygame.draw.line(surf, (200, 160, 60), (hx1, hy1), (hx2, hy2), 4)

        # Crossguard
        gx1 = cx + int(ca * 16 + perp_x * 9); gy1 = cy + int(sa * 16 + perp_y * 9)
        gx2 = cx + int(ca * 16 - perp_x * 9); gy2 = cy + int(sa * 16 - perp_y * 9)
        pygame.draw.line(surf, (180, 140, 40), (gx1, gy1), (gx2, gy2), 3)

        # Blade
        bx1 = cx + int(ca * 18); by1 = cy + int(sa * 18)
        bx2 = cx + int(ca * 38); by2 = cy + int(sa * 38)
        pygame.draw.line(surf, (230, 220, 180), (bx1, by1), (bx2, by2), 3)
        # Blade tip glint
        pygame.draw.circle(surf, (255, 255, 220), (int(bx2), int(by2)), 3)

        # Swing arc trail — only shown briefly after a real swing

        # Hidden detection dot
        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_GLADIATOR, (cx - 10 + i * 6, cy + 36), 3)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,22), (r, r), r)
        pygame.draw.circle(s, (255,255,255,60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        block_str = "READY" if self._stun_block_cd <= 0 else f"{self._stun_block_cd:.1f}s"
        return {
            "Damage":    self.damage,
            "Firerate":  f"{self.firerate:.3f}",
            "Range":     self.range_tiles,
            "Arc Hits":  f"{self._max_hits} (180°)",
            "StunBlock": block_str,
            "HidDet":    "YES" if self.hidden_detection else "no",
        }


# ── Toxic Gunner ───────────────────────────────────────────────────────────────
C_TOXICGUN      = (80, 200, 60)
C_TOXICGUN_DARK = (20, 60, 10)

# Tuple layout:
#  (damage, firerate, burst, cooldown, range_tiles, upgrade_cost,
#   slow_pct,      # slowdown fraction per shot (stacks, non-permanent — refreshes timer)
#   slow_dur,      # seconds slow lasts after last hit
#   poison_dmg,    # damage per tick (0 = no poison)
#   poison_tick,   # seconds between ticks
#   poison_time,   # total poison duration in seconds
#   def_drop_pct,  # ARMOR drop per poison tick (0 = none), max 50%
#   hidden_detection)
#
# Burst mechanic: fires `burst` shots with `firerate` gap between shots,
# then waits `cooldown` seconds before next burst.
# Each shot applies one stack of slow (stacks up to 30% total at lv4).
# Poison is re-applied on each hit; timer refreshes, does not stack dmg.

TOXICGUN_LEVELS = [
    # lv0 – place $525
    (1, 0.108, 4,  1.2,  6.7, None,  0.10, 6.0, 1, 1.0,  6.0, 0.00, False),
    # lv1 – +$200
    (1, 0.108, 8,  0.6,  6.7,  200,  0.10, 6.0, 1, 1.0,  6.0, 0.00, False),
    # lv2 – +$750
    (1, 0.108, 8,  0.6,  8.0,  750,  0.20, 6.0, 2, 1.0,  6.0, 0.00, False),
    # lv3 – +$3000
    (1, 0.108, 10, 0.6,  8.0, 3000,  0.20, 6.0, 2, 1.0,  6.0, 0.03, True),
    # lv4 – +$14000
    (5, 0.108, 20, 0.0,  8.0,14000,  0.30,10.0, 8, 1.0, 10.0, 0.03, True),
]

_TOXICGUN_MAX_SLOW    = 0.30   # max accumulated slow fraction
_TOXICGUN_MAX_DEFDROP = 0.50   # max armor reduction


class ToxicGunnerBullet:
    """Single pellet that homes toward target, applies slow + poison on hit."""
    def __init__(self, ox, oy, target, damage, slow_pct, slow_dur,
                 poison_dmg, poison_tick, poison_time, def_drop):
        self.x = float(ox); self.y = float(oy)
        self._target = target
        dx = target.x - ox; dy = target.y - oy
        d  = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.speed = 520.0
        self.damage     = damage
        self.slow_pct   = slow_pct
        self.slow_dur   = slow_dur
        self.poison_dmg = poison_dmg
        self.poison_tick= poison_tick
        self.poison_time= poison_time
        self.def_drop   = def_drop
        self.alive = True
        self._dist_left = 800.0

    def update(self, dt, enemies):
        if not self.alive: return
        # Home toward target while alive
        if self._target and self._target.alive:
            dx = self._target.x - self.x; dy = self._target.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.vx = dx / d; self.vy = dy / d
        step = self.speed * dt
        self.x += self.vx * step; self.y += self.vy * step
        self._dist_left -= step
        if self._dist_left <= 0:
            self.alive = False; return
        for e in enemies:
            if not e.alive: continue
            if math.hypot(e.x - self.x, e.y - self.y) < e.radius + 5:
                self._hit(e)
                self.alive = False; return

    def _hit(self, e):
        e.take_damage(self.damage)
        # Slow stack (non-permanent: refreshes timer, stacks up to max)
        if self.slow_pct > 0 and getattr(e,'SLOW_RESISTANCE',0.0) < 1.0:
            orig = getattr(e, '_tg_orig_speed', None)
            if orig is None:
                e._tg_orig_speed = e.speed
            cur = getattr(e, '_tg_slow', 0.0)
            new = min(cur + self.slow_pct, _TOXICGUN_MAX_SLOW)
            e._tg_slow = new
            e._tg_timer = self.slow_dur
            resistance = getattr(e, 'SLOW_RESISTANCE', 0.0)
            e.speed = e._tg_orig_speed * (1.0 - new * resistance)
        # Poison (refresh, don't stack damage)
        if self.poison_dmg > 0:
            e._tg_poison_dmg   = self.poison_dmg
            e._tg_poison_tick  = self.poison_tick
            e._tg_poison_time  = self.poison_time
            e._tg_poison_timer = self.poison_time   # restart full duration
            e._tg_tick_timer   = self.poison_tick   # first tick after one interval
        # Defense drop per hit (applied on poison tick instead; tracked here)
        e._tg_def_drop_per_tick = self.def_drop

    def draw(self, surf):
        if not self.alive: return
        cx, cy = int(self.x), int(self.y)
        s = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(s, (60, 180, 40, 80),  (7, 7), 6)
        pygame.draw.circle(s, (120, 240, 80, 220), (7, 7), 4)
        pygame.draw.circle(s, (200, 255, 150, 255),(7, 7), 2)
        surf.blit(s, (cx - 7, cy - 7))


class ToxicGunner(Unit):
    PLACE_COST       = 525
    COLOR            = C_TOXICGUN
    NAME             = "Toxic Gunner"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._bullets      = []
        self._burst_left   = 0       # shots remaining in current burst
        self._burst_cd     = 0.0     # cooldown between bursts
        self._shot_cd      = 0.0     # firerate between shots within burst
        self._anim_t       = 0.0
        self._apply_level()

    def _apply_level(self):
        row = TOXICGUN_LEVELS[self.level]
        (self.damage, self.firerate, self._burst_count, self._cooldown,
         self.range_tiles, _, self._slow_pct, self._slow_dur,
         self._poison_dmg, self._poison_tick, self._poison_time,
         self._def_drop, self.hidden_detection) = row
        self._burst_left = 0

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(TOXICGUN_LEVELS): return None
        return TOXICGUN_LEVELS[nxt][5]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(TOXICGUN_LEVELS):
            self.level = nxt; self._apply_level()

    def _tick_poison(self, enemies, dt):
        for e in enemies:
            if not e.alive: continue
            pt = getattr(e, '_tg_poison_time', 0.0)
            if pt <= 0: continue
            e._tg_poison_time = pt - dt
            if e._tg_poison_time <= 0:
                e._tg_poison_time = 0.0
                continue
            # tick
            e._tg_tick_timer = getattr(e, '_tg_tick_timer', 0.0) - dt
            if e._tg_tick_timer <= 0:
                e._tg_tick_timer += getattr(e, '_tg_poison_tick', 1.0)
                pdmg = getattr(e, '_tg_poison_dmg', 0)
                if pdmg > 0:
                    e.take_damage(pdmg)
                    self.total_damage += pdmg
                # defense drop per tick
                dd = getattr(e, '_tg_def_drop_per_tick', 0.0)
                if dd > 0:
                    dropped = getattr(e, '_tg_total_def_drop', 0.0)
                    if dropped < _TOXICGUN_MAX_DEFDROP:
                        apply = min(dd, _TOXICGUN_MAX_DEFDROP - dropped)
                        e.ARMOR = max(0.0, e.ARMOR - apply)
                        e._tg_total_def_drop = dropped + apply
            # tick slow timer
            st = getattr(e, '_tg_timer', 0.0)
            if st > 0:
                e._tg_timer = st - dt
                if e._tg_timer <= 0:
                    orig = getattr(e, '_tg_orig_speed', None)
                    if orig is not None: e.speed = orig
                    e._tg_orig_speed = None
                    e._tg_slow = 0.0

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt
        self._tick_poison(enemies, dt)

        # Between bursts: count down cooldown
        if self._burst_left <= 0:
            if self._burst_cd > 0:
                self._burst_cd -= dt
            if self._burst_cd <= 0:
                targets = self._get_targets(enemies, 1)
                if targets:
                    self._burst_left = self._burst_count
                    self._shot_cd    = 0.0
                    # Aim at the locked target for this burst
                    self._last_aim = math.atan2(targets[0].y - self.py, targets[0].x - self.px)
        else:
            if self._shot_cd > 0:
                self._shot_cd -= dt
            if self._shot_cd <= 0:
                targets = self._get_targets(enemies, 1)
                if targets:
                    t2 = targets[0]
                    self._last_aim = math.atan2(t2.y - self.py, t2.x - self.px)
                    self._shot_cd = self.firerate
                    self._burst_left -= 1
                    self._bullets.append(ToxicGunnerBullet(
                        self.px, self.py, t2,
                        self.damage, self._slow_pct, self._slow_dur,
                        self._poison_dmg, self._poison_tick, self._poison_time,
                        self._def_drop
                    ))
                    self.total_damage += self.damage
                    if self._burst_left <= 0:
                        self._burst_cd = self._cooldown
                else:
                    self._burst_left = 0
                    self._burst_cd   = self._cooldown

        for b in self._bullets: b.update(dt, enemies)
        self._bullets = [b for b in self._bullets if b.alive]

    def draw(self, surf):
        t  = self._anim_t
        cx, cy = int(self.px), int(self.py)

        # Outer glow
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        ga = int(abs(math.sin(t * 4)) * 50 + 30)
        pygame.draw.circle(glow, (60, 200, 40, ga), (35, 35), 33)
        surf.blit(glow, (cx - 35, cy - 35))

        pygame.draw.circle(surf, C_TOXICGUN_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_TOXICGUN,      (cx, cy), 21)
        pygame.draw.circle(surf, (140, 255, 100),  (cx, cy), 21, 2)

        # Barrel pointing toward last target
        a  = getattr(self, '_last_aim', 0.0)
        ca, sa = math.cos(a), math.sin(a)
        bx1 = cx + int(ca * 10); by1 = cy + int(sa * 10)
        bx2 = cx + int(ca * 30); by2 = cy + int(sa * 30)
        pygame.draw.line(surf, (100, 220, 70), (bx1, by1), (bx2, by2), 5)
        pygame.draw.circle(surf, (160, 255, 120), (bx2, by2), 4)

        # Toxic barrel rings
        for i in range(3):
            ring_x = cx + int(ca * (14 + i * 6))
            ring_y = cy + int(sa * (14 + i * 6))
            pygame.draw.circle(surf, (60, 160, 40), (ring_x, ring_y), 3)

        # Hidden/flying detection
        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_TOXICGUN, (cx - 8 + i * 6, cy + 36), 3)

        # Bullets
        for b in self._bullets: b.draw(surf)

    def _try_attack(self, enemies, effects):
        pass  # attack logic handled entirely in update()

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,22), (r, r), r)
        pygame.draw.circle(s, (255,255,255,60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        return {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Burst":    f"{self._burst_count} / cd {self._cooldown:.1f}s",
            "Range":    self.range_tiles,
            "Slow":     f"+{int(self._slow_pct*100)}% max {int(_TOXICGUN_MAX_SLOW*100)}%",
            "Poison":   f"{self._poison_dmg}/tick {self._poison_time:.0f}s" if self._poison_dmg else "none",
        }


# ── Slasher ────────────────────────────────────────────────────────────────────
C_SLASHER      = (160, 30, 30)
C_SLASHER_DARK = (50,  10, 10)

# Tuple layout:
#  (damage, swingrate, range_tiles, upgrade_cost,
#   crit_every,        # deal crit hit every N-th swing
#   crit_mult,         # crit damage multiplier
#   hidden_detection,
#   bleed_stacks_per_hit, # bleed stacks added per swing (lv2+)
#   bleed_max_stacks,  # total max stacks before bleed explosion
#   bleed_base_dmg)    # flat bleed tick damage per stack (scales with HP at ~0.5% maxhp per stack)
#
# Bleed: each stack deals damage once (1s delay between ticks).
# At max stacks → burst damage = stacks × bleed_base_dmg × enemy_hp_factor, then stacks reset.
# Single target — does NOT pierce.

SLASHER_LEVELS = [
    # lv0 – place $1500
    (6,  0.508, 6.0, None,  3, 1.75, False, 0, 30, 0),
    # lv1 – +$1250
    (6,  0.408, 6.0, 1250,  3, 2.50, True,  0, 30, 0),
    # lv2 – +$3500  (bleed unlocked)
    (20, 0.708, 6.5, 3500,  3, 3.00, True,  1, 30, 1),
    # lv3 – +$6500
    (45, 0.608, 7.0, 6500,  3, 3.50, True,  2, 30, 1),
    # lv4 – +$20000
    (60, 0.508, 7.5,20000,  3, 4.00, True,  3, 30, 2),
]

_SLASHER_BLEED_HP_FACTOR = 0.005  # per stack: 0.5% of enemy maxhp


class Slasher(Unit):
    PLACE_COST       = 1700
    COLOR            = C_SLASHER
    NAME             = "Slasher"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._swing_t      = 0.0
        self._aim_angle    = 0.0
        self._last_swing_t = -999.0
        self._hit_count    = 0    # counts hits for crit rhythm
        self._apply_level()

    def _apply_level(self):
        row = SLASHER_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._crit_every, self._crit_mult,
         self.hidden_detection,
         self._bleed_per_hit, self._bleed_max, self._bleed_base_dmg) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(SLASHER_LEVELS): return None
        return SLASHER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(SLASHER_LEVELS):
            self.level = nxt; self._apply_level()

    def _do_swing(self, enemies, effects):
        targets = self._get_targets(enemies, 1)
        if not targets: return
        e = targets[0]
        self._aim_angle = math.atan2(e.y - self.py, e.x - self.px)
        self._last_swing_t = self._swing_t
        self._hit_count += 1

        # Critical hit every N swings
        is_crit = (self._hit_count % self._crit_every == 0)
        dmg = self.damage * self._crit_mult if is_crit else self.damage
        e.take_damage(dmg)
        self.total_damage += dmg

        # Bleed (lv2+)
        if self._bleed_per_hit > 0:
            cur = getattr(e, '_slash_bleed', 0)
            new = min(cur + self._bleed_per_hit, self._bleed_max)
            e._slash_bleed = new
            e._slash_bleed_owner = id(self)
            # Bleed burst at max stacks
            if new >= self._bleed_max:
                burst = self._bleed_max * self._bleed_base_dmg * max(1, int(e.maxhp * _SLASHER_BLEED_HP_FACTOR * self._bleed_max))
                e.take_damage(burst)
                self.total_damage += burst
                e._slash_bleed = 0
            else:
                # Each stack deals 1 tick damage with 1s delay
                e._slash_bleed_tick = getattr(e, '_slash_bleed_tick', 0.0)
                e._slash_bleed_timer = getattr(e, '_slash_bleed_timer', 0.0)
                if e._slash_bleed_timer <= 0:
                    e._slash_bleed_timer = 1.0  # tick every 1s

        # Visual effect — blood slash, crit version if applicable
        effects.append(BloodSlashEffect(self.px, self.py,
                                        math.degrees(self._aim_angle),
                                        is_crit=is_crit))

    def _tick_bleed(self, enemies, dt):
        for e in enemies:
            if not e.alive: continue
            stacks = getattr(e, '_slash_bleed', 0)
            if stacks <= 0: continue
            timer = getattr(e, '_slash_bleed_timer', 0.0) - dt
            e._slash_bleed_timer = timer
            if timer <= 0:
                e._slash_bleed_timer = 1.0
                tick_dmg = stacks * self._bleed_base_dmg
                if tick_dmg > 0:
                    e.take_damage(tick_dmg)
                    self.total_damage += tick_dmg

    def update(self, dt, enemies, effects, money):
        self._swing_t += dt
        if self.cd_left > 0: self.cd_left -= dt
        self._tick_bleed(enemies, dt)

        if self.cd_left <= 0:
            r = self.range_tiles * TILE
            has = any(
                e.alive and not getattr(e,'_reversed',False)
                and not (e.IS_HIDDEN and not self.hidden_detection)
                and dist((e.x,e.y),(self.px,self.py)) <= r
                for e in enemies
            )
            if has:
                self.cd_left = self.firerate
                self._do_swing(enemies, effects)

    def draw(self, surf):
        t  = self._swing_t
        cx, cy = int(self.px), int(self.py)

        pygame.draw.circle(surf, C_SLASHER_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_SLASHER,      (cx, cy), 21)
        pygame.draw.circle(surf, (220, 80, 80),   (cx, cy), 21, 2)

        # Knife pointing at aim angle, animates on hit
        time_since = t - self._last_swing_t
        if 0 < time_since < self.firerate * 0.6:
            swing_p = time_since / (self.firerate * 0.6)
            knife_a = self._aim_angle + math.radians(60 - swing_p * 120)
        else:
            knife_a = self._aim_angle

        ca, sa = math.cos(knife_a), math.sin(knife_a)
        pa, pb = -sa, ca   # perpendicular

        # Blade
        kx1 = cx + int(ca * 8);  ky1 = cy + int(sa * 8)
        kx2 = cx + int(ca * 32); ky2 = cy + int(sa * 32)
        pygame.draw.line(surf, (220, 200, 200), (kx1, ky1), (kx2, ky2), 2)
        # Tip
        pygame.draw.circle(surf, (255, 230, 230), (kx2, ky2), 3)
        # Guard
        gx1 = int(cx + ca * 14 + pa * 7); gy1 = int(cy + sa * 14 + pb * 7)
        gx2 = int(cx + ca * 14 - pa * 7); gy2 = int(cy + sa * 14 - pb * 7)
        pygame.draw.line(surf, (180, 60, 60), (gx1, gy1), (gx2, gy2), 3)

        # Crit flash (every _crit_every hits)
        next_crit = self._crit_every - (self._hit_count % self._crit_every)
        if next_crit == 1 and 0 < time_since < 0.15:
            fl = pygame.Surface((60, 60), pygame.SRCALPHA)
            fa = int(220 * (1 - time_since / 0.15))
            pygame.draw.circle(fl, (255, 80, 80, fa), (30, 30), 28)
            surf.blit(fl, (cx - 30, cy - 30))

        # Swing trail
        if 0 < time_since < 0.14:
            arc_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            alpha = int(160 * (1 - time_since / 0.14))
            arc_r = int(self.range_tiles * TILE)
            for i in range(10):
                a = self._aim_angle + math.radians(40 - 80 * i / 9)
                pygame.draw.line(arc_s, (220, 60, 60, alpha),
                    (cx + int(math.cos(a)*8), cy + int(math.sin(a)*8)),
                    (cx + int(math.cos(a)*arc_r), cy + int(math.sin(a)*arc_r)), 2)
            surf.blit(arc_s, (0, 0))

        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        for i in range(self.level):
            pygame.draw.circle(surf, C_SLASHER, (cx - 8 + i * 6, cy + 36), 3)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,22), (r, r), r)
        pygame.draw.circle(s, (255,255,255,60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        next_crit = self._crit_every - (self._hit_count % self._crit_every)
        info = {
            "Damage":    self.damage,
            "Firerate":  f"{self.firerate:.3f}",
            "Range":     self.range_tiles,
            "Crit":      f"x{self._crit_mult} every {self._crit_every} hits (in {next_crit})",
            "HidDet":    "YES" if self.hidden_detection else "no",
        }
        if self._bleed_per_hit > 0:
            stacks = 0  # can't easily show per-enemy here
            info["Bleed"] = f"+{self._bleed_per_hit}/hit, burst @{self._bleed_max}"
        return info


# ── Cowboy (formerly Golden Cowboy) ────────────────────────────────────────────
C_GCOWBOY      = (220, 180, 40)
C_GCOWBOY_DARK = (80,  60,  10)

# Tuple layout:
#  (damage, firerate, range_tiles, upgrade_cost,
#   cash_shot,     # fire this many shots then spin + generate income
#   income,        # $ generated after cash_shot shots
#   spin_time,     # seconds the cowboy spins (cannot fire during spin)
#   hidden_detection)
#
# Mechanics:
#  - Fires normally, counting shots per enemy hit
#  - Every cash_shot hits → spin gun for spin_time, generate income $
#  - During spin: cannot fire
#  - Shots that miss (no enemy in range) still count toward cash_shot if
#    the trigger fires anyway — but we only count actual hits for authenticity

GCOWBOY_LEVELS = [
    # lv0 – place $550
    (2,  1.008,  9.0, None, 6,  35, 1.7, False),
    # lv1 – +$300
    (2,  0.808,  9.0,  300, 6,  35, 1.7, False),
    # lv2 – +$400  (hidden detection, +dmg, +range)
    (4,  0.808, 12.0,  400, 6,  65, 1.7, True),
    # lv3 – +$1000
    (12, 0.608, 12.5, 1000, 6,  65, 1.3, True),
    # lv4 – +$3500
    (15, 0.358, 13.0, 3500, 12, 90, 1.3, True),
    # lv5 – +$12000
    (18, 0.358, 13.5,12000, 12,160, 1.0, True),
]


class GoldenCowboy(Unit):
    PLACE_COST       = 550
    COLOR            = C_GCOWBOY
    NAME             = "Cowboy"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._shot_count   = 0      # shots fired toward cash_shot threshold
        self._spin_timer   = 0.0   # time remaining in spin
        self._spinning     = False
        self._spin_t       = 0.0   # animation timer
        self._aim_angle    = 0.0
        self._pending_income = 0   # income to deliver to game
        self._apply_level()

    def _apply_level(self):
        row = GCOWBOY_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._cash_shot, self._income, self._spin_time,
         self.hidden_detection) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(GCOWBOY_LEVELS): return None
        return GCOWBOY_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(GCOWBOY_LEVELS):
            self.level = nxt; self._apply_level()

    def update(self, dt, enemies, effects, money):
        self._spin_t += dt

        # Spin phase — no firing
        if self._spinning:
            self._spin_timer -= dt
            if self._spin_timer <= 0:
                self._spinning = False
                self._spin_timer = 0.0
            return

        # Normal fire
        if self.cd_left > 0: self.cd_left -= dt
        if self.cd_left <= 0:
            targets = self._get_targets(enemies, 1)
            if targets:
                t = targets[0]
                self._aim_angle = math.atan2(t.y - self.py, t.x - self.px)
                self.cd_left = self.firerate
                t.take_damage(self.damage)
                self.total_damage += self.damage
                self._shot_count += 1

                # Cash shot threshold reached
                if self._shot_count >= self._cash_shot:
                    self._shot_count = 0
                    self._spinning = True
                    self._spin_timer = self._spin_time
                    self._pending_income += self._income

    def collect_income(self):
        """Called by game loop to collect pending income."""
        earned = self._pending_income
        self._pending_income = 0
        return earned

    def draw(self, surf):
        t  = self._spin_t
        cx, cy = int(self.px), int(self.py)

        # Outer glow (golden)
        glow = pygame.Surface((66, 66), pygame.SRCALPHA)
        ga = int(abs(math.sin(t * 3)) * 60 + 40)
        pygame.draw.circle(glow, (220, 180, 40, ga), (33, 33), 31)
        surf.blit(glow, (cx - 33, cy - 33))

        pygame.draw.circle(surf, C_GCOWBOY_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_GCOWBOY,      (cx, cy), 21)
        pygame.draw.circle(surf, (255, 230, 100), (cx, cy), 21, 2)

        if self._spinning:
            # Spinning gun animation — rotates fast
            spin_a = t * 12.0  # fast spin radians
            for i in range(2):
                a = spin_a + i * math.pi
                bx = cx + int(math.cos(a) * 18); by = cy + int(math.sin(a) * 18)
                pygame.draw.line(surf, (255, 220, 80), (cx, cy), (bx, by), 4)
                pygame.draw.circle(surf, (255, 240, 140), (bx, by), 4)
            # Money flash
            flash_s = pygame.Surface((50, 20), pygame.SRCALPHA)
            frac = 1.0 - (self._spin_timer / self._spin_time)
            fa2 = int(max(0, 200 * (1 - frac * 2)))
            mf = pygame.font.SysFont("segoeui", 14, bold=True)
            ms = mf.render(f"+${self._income}", True, (255, 230, 60))
            ms.set_alpha(fa2)
            surf.blit(ms, ms.get_rect(center=(cx, cy - 36)))
        else:
            # Gun barrel pointing at aim angle
            a  = self._aim_angle
            ca, sa = math.cos(a), math.sin(a)
            bx1 = cx + int(ca * 8);  by1 = cy + int(sa * 8)
            bx2 = cx + int(ca * 30); by2 = cy + int(sa * 30)
            pygame.draw.line(surf, (200, 160, 40), (bx1, by1), (bx2, by2), 5)
            pygame.draw.circle(surf, (255, 220, 80), (bx2, by2), 4)
            # Barrel ring
            pygame.draw.circle(surf, (255, 200, 60),
                                (cx + int(ca * 20), cy + int(sa * 20)), 3)

        # Hat brim decoration
        pygame.draw.ellipse(surf, (160, 110, 20),
                            (cx - 16, cy - 32, 32, 8))
        pygame.draw.ellipse(surf, (200, 150, 40),
                            (cx - 10, cy - 36, 20, 10))

        # Cash shot counter above unit
        shots_left = self._cash_shot - self._shot_count
        sf2 = pygame.font.SysFont("consolas", 11, bold=True)
        cs2 = sf2.render(str(shots_left), True, (255, 230, 80))
        surf.blit(cs2, cs2.get_rect(center=(cx, cy - 42)))

        # Hidden detection dot
        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_GCOWBOY, (cx - 10 + i * 6, cy + 36), 3)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 22), (r, r), r)
        pygame.draw.circle(s, (255, 255, 255, 60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        shots_left = self._cash_shot - self._shot_count
        return {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "CashShot": f"${self._income} in {shots_left}/{self._cash_shot}",
            "SpinTime": f"{self._spin_time:.1f}s",
            "HidDet":   "YES" if self.hidden_detection else "no",
        }


# ── Hallow Punk ────────────────────────────────────────────────────────────────
C_HALLOWPUNK      = (200, 80, 200)
C_HALLOWPUNK_DARK = (60,  15,  60)

# Tuple layout:
#  (damage, firerate, range_tiles, upgrade_cost,
#   splash_radius,   # explosion radius in tiles
#   knockback,       # pixels pushed back on hit
#   burn_dmg,        # burn damage per tick (0 = no burn)
#   burn_time,       # burn duration seconds
#   burn_tick,       # seconds between burn ticks
#   hidden_detection)
#
# Mechanics:
#  - Fires a homing rocket toward the first (farthest) enemy in range
#  - On impact: AOE explosion hits all enemies within splash_radius tiles
#  - All hit enemies are knocked back by knockback pixels
#  - Lv1+: burn applied to all hit enemies
#  - No hidden detection at any level

HALLOWPUNK_LEVELS = [
    # lv0 – place $300
    (10, 5.008, 7.0, None,  5.0, 12.5, 0, 0.0, 0.5, False),
    # lv1 – +$300
    (10, 4.008, 7.0,  300,  5.0, 12.5, 1, 3.0, 0.5, False),
    # lv2 – +$2000  (flying det, more dmg, faster rocket)
    (30, 4.008, 8.0, 2000,  5.0, 17.5, 2, 3.0, 0.5, False),
    # lv3 – +$8500  (big damage, bigger explosion)
    (120,4.008, 8.0, 8500,  6.0, 17.5, 3, 5.0, 0.5, False),
]

_HALLOWPUNK_ROCKET_SPEED_BASE = 380.0
_HALLOWPUNK_ROCKET_SPEED_LV2  = 480.0


class HallowPunkRocket:
    """Homing rocket that explodes on impact dealing AOE damage + knockback + burn."""
    def __init__(self, ox, oy, target, damage, splash_r, knockback,
                 burn_dmg, burn_time, burn_tick, speed, level):
        self.x = float(ox); self.y = float(oy)
        self._target = target
        dx = target.x - ox; dy = target.y - oy
        d  = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.speed   = speed
        self.damage  = damage
        self.splash_r= splash_r * TILE * _am()
        self.knockback = knockback
        self.burn_dmg  = burn_dmg
        self.burn_time = burn_time
        self.burn_tick = burn_tick
        self.level     = level
        self.alive = True
        self._exploded = False
        self._dist_left = 1400.0
        self._trail = []   # list of (x, y, age) for smoke trail

    def _explode(self, enemies):
        for e in enemies:
            if not e.alive: continue
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d <= self.splash_r:
                e.take_damage(self.damage)
                # Knockback — push enemy backward along its path direction
                if self.knockback > 0 and not getattr(e, 'frozen', False):
                    push = self.knockback * max(0.2, 1.0 - d / self.splash_r)
                    path = getattr(e, '_frosty_path', None)
                    if path is None:
                        from game_core import get_map_path as _gmp
                        path = _gmp()
                    wp = getattr(e, '_wp_index', 1)
                    wp_idx = min(wp, len(path) - 1)
                    wpx, wpy = path[wp_idx]
                    dx2 = wpx - e.x; dy2 = wpy - e.y
                    d2 = math.hypot(dx2, dy2) or 1
                    # Push opposite to movement direction (backward)
                    e.x -= (dx2 / d2) * push
                    e.y -= (dy2 / d2) * push
                # Burn (lv1+)
                if self.burn_dmg > 0:
                    e._fire_timer = max(getattr(e, '_fire_timer', 0.0), self.burn_time * _dm())
                    e._fire_tick  = getattr(e, '_fire_tick', 0.0)
                    e._fire_dmg   = self.burn_dmg
                    e._fire_tick_interval = self.burn_tick

    def update(self, dt, enemies):
        if not self.alive: return
        # Store trail point
        self._trail.append((self.x, self.y, 0.0))
        self._trail = [(x, y, a + dt) for x, y, a in self._trail if a < 0.3]

        # Home on target
        if self._target and self._target.alive:
            dx = self._target.x - self.x; dy = self._target.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.vx = dx / d; self.vy = dy / d
            if d < 12:
                self._explode(enemies)
                self.alive = False; return
        else:
            # Target died — check any enemy nearby
            for e in enemies:
                if not e.alive: continue
                if math.hypot(e.x - self.x, e.y - self.y) < 20:
                    self._explode(enemies)
                    self.alive = False; return

        step = self.speed * dt
        self.x += self.vx * step; self.y += self.vy * step
        self._dist_left -= step
        if self._dist_left <= 0:
            self._explode(enemies)
            self.alive = False

    def draw(self, surf):
        if not self.alive: return
        # Smoke trail
        for tx, ty, age in self._trail:
            alpha = max(0, min(255, int(180 * (1 - age / 0.3))))
            if alpha <= 0: continue
            ts = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(ts, (180, 100, 200, alpha), (5, 5), 4)
            surf.blit(ts, (int(tx) - 5, int(ty) - 5))
        # Rocket body
        cx, cy = int(self.x), int(self.y)
        angle = math.degrees(math.atan2(self.vy, self.vx))
        rs = pygame.Surface((22, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(rs, (220, 100, 220), (0, 1, 18, 6))
        pygame.draw.polygon(rs, (255, 150, 255), [(18, 4), (22, 1), (22, 7)])
        import pygame.transform as _pt
        rot = _pt.rotate(rs, -angle)
        surf.blit(rot, rot.get_rect(center=(cx, cy)))


class HallowPunk(Unit):
    PLACE_COST       = 300
    COLOR            = C_HALLOWPUNK
    NAME             = "Hallow Punk"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._rockets  = []
        self._anim_t   = 0.0
        self._aim_angle= 0.0
        self._apply_level()

    def _apply_level(self):
        row = HALLOWPUNK_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._splash_r, self._knockback,
         self._burn_dmg, self._burn_time, self._burn_tick,
         self.hidden_detection) = row
        self._rocket_speed = (_HALLOWPUNK_ROCKET_SPEED_LV2
                               if self.level >= 2 else _HALLOWPUNK_ROCKET_SPEED_BASE)

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(HALLOWPUNK_LEVELS): return None
        return HALLOWPUNK_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(HALLOWPUNK_LEVELS):
            self.level = nxt; self._apply_level()

    def _tick_burn(self, enemies, dt):
        for e in enemies:
            if not e.alive: continue
            ft = getattr(e, '_fire_timer', 0.0)
            if ft <= 0: continue
            e._fire_timer = max(0.0, ft - dt)
            e._fire_tick  = getattr(e, '_fire_tick', 0.0) + dt
            tick_interval = getattr(e, '_fire_tick_interval', 0.5)
            if e._fire_tick >= tick_interval:
                e._fire_tick -= tick_interval
                bdmg = getattr(e, '_fire_dmg', 1)
                e.take_damage(bdmg)
                self.total_damage += bdmg

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt
        if self.cd_left > 0: self.cd_left -= dt
        self._tick_burn(enemies, dt)

        if self.cd_left <= 0:
            targets = self._get_targets(enemies, 1)
            if targets:
                t = targets[0]
                self._aim_angle = math.atan2(t.y - self.py, t.x - self.px)
                self.cd_left = self.firerate
                self._rockets.append(HallowPunkRocket(
                    self.px, self.py, t,
                    self.damage, self._splash_r, self._knockback,
                    self._burn_dmg, self._burn_time, self._burn_tick,
                    self._rocket_speed, self.level
                ))
                self.total_damage += self.damage

        for r in self._rockets: r.update(dt, enemies)
        self._rockets = [r for r in self._rockets if r.alive]

    def draw(self, surf):
        t  = self._anim_t
        cx, cy = int(self.px), int(self.py)

        # Outer glow
        glow = pygame.Surface((66, 66), pygame.SRCALPHA)
        ga = int(abs(math.sin(t * 2.5)) * 50 + 30)
        pygame.draw.circle(glow, (180, 60, 180, ga), (33, 33), 31)
        surf.blit(glow, (cx - 33, cy - 33))

        pygame.draw.circle(surf, C_HALLOWPUNK_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_HALLOWPUNK,      (cx, cy), 21)
        pygame.draw.circle(surf, (240, 140, 240),    (cx, cy), 21, 2)

        # Launcher tube pointing at aim angle
        a  = self._aim_angle
        ca, sa = math.cos(a), math.sin(a)
        bx1 = cx + int(ca * 6);  by1 = cy + int(sa * 6)
        bx2 = cx + int(ca * 28); by2 = cy + int(sa * 28)
        pygame.draw.line(surf, (160, 60, 160), (bx1, by1), (bx2, by2), 7)
        pygame.draw.line(surf, (220, 120, 220), (bx1, by1), (bx2, by2), 4)
        pygame.draw.circle(surf, (240, 160, 240), (bx2, by2), 5)

        # Explosion radius indicator when hovering (draw_range handles this)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_HALLOWPUNK, (cx - 6 + i * 6, cy + 36), 3)

        # Rockets
        for r in self._rockets: r.draw(surf)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 22), (r, r), r)
        pygame.draw.circle(s, (255, 255, 255, 60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))
        # Also show explosion radius
        er = int(self._splash_r * TILE)
        es = pygame.Surface((er * 2, er * 2), pygame.SRCALPHA)
        pygame.draw.circle(es, (220, 80, 220, 18), (er, er), er)
        pygame.draw.circle(es, (220, 80, 220, 50), (er, er), er, 1)
        surf.blit(es, (int(self.px) - er, int(self.py) - er))

    def get_info(self):
        info = {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "Splash":   f"{self._splash_r} tiles",
            "Knockback":f"{self._knockback}px",
        }
        if self._burn_dmg > 0:
            info["Burn"] = f"{self._burn_dmg}/tick {self._burn_time:.0f}s"
        return info


# ── Spotlight Tech ─────────────────────────────────────────────────────────────
C_SPOTLIGHT      = (255, 230, 80)
C_SPOTLIGHT_DARK = (80,  65,  10)

# Tuple:
#  (damage, firerate, range_tiles, upgrade_cost,
#   beam_radius,    # circle radius under beam in tiles (enemy hit zone)
#   burn_dmg,       # fire damage per tick (0=no fire)
#   burn_time,      # seconds fire lasts
#   burn_tick,      # seconds between fire ticks
#   expose_hidden,  # lv2+: hidden enemies in beam become exposed
#   conf_thresh,    # lv4: confusion trigger after this much accumulated dmg
#   hidden_detection)
SPOTLIGHTTECH_LEVELS = [
    # lv0  $3250
    (4,  0.308, 7.0, None,  3.0, 0, 0.0,  0.25, False, 0,    True),
    # lv1  +$1800  (burn unlocked, bigger circle)
    (4,  0.308, 7.0, 1800,  3.6, 1, 2.0,  0.25, False, 0,    True),
    # lv2  +$4800  (+4 dmg, +1 range, hidden det, bigger circle, burn 2, expose)
    (8,  0.308, 8.0, 4800,  4.2, 2, 2.0,  0.25, True,  0,    True),
    # lv3  +$12500  (+4 dmg, faster firerate, longer burn, bigger burn)
    (12, 0.208, 8.0, 12500, 4.2, 5, 4.0,  0.25, True,  0,    True),
    # lv4  +$20000  (bigger circle, burn 7, 6s, confusion every 1800 dmg, 7.5s cd)
    (12, 0.208, 8.0, 20000, 5.0, 7, 6.0,  0.25, True,  1800, True),
]

_SPOTLIGHT_BEAM_ROT_SPEED = 3.5   # radians/sec sweep speed
_SPOTLIGHT_CONFUSE_DUR    = 2.5   # seconds confusion lasts
_SPOTLIGHT_CONFUSE_CD     = 7.5   # seconds cooldown between confusions


class SpotlightTech(Unit):
    PLACE_COST       = 3250
    COLOR            = C_SPOTLIGHT
    NAME             = "Spotlight Tech"
    hidden_detection = True

    def __init__(self, px, py):
        super().__init__(px, py)
        self._beam_angle   = 0.0
        self._target_angle = 0.0
        self._anim_t       = 0.0
        self._conf_accum   = 0.0
        self._conf_cd      = 0.0   # cooldown timer
        self._last_enemies = []
        self._apply_level()

    def _apply_level(self):
        row = SPOTLIGHTTECH_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._beam_r, self._burn_dmg, self._burn_time, self._burn_tick,
         self._expose_hidden, self._conf_thresh,
         self.hidden_detection) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(SPOTLIGHTTECH_LEVELS): return None
        return SPOTLIGHTTECH_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(SPOTLIGHTTECH_LEVELS):
            self.level = nxt; self._apply_level()

    def _confuse_enemies(self, enemies):
        range_px  = self.range_tiles * TILE
        beam_r_px = self._beam_r * TILE
        bx = self.px + math.cos(self._beam_angle) * range_px
        by = self.py + math.sin(self._beam_angle) * range_px
        for e in enemies:
            if not e.alive: continue
            if dist((e.x, e.y), (bx, by)) <= beam_r_px:
                e._confused = True
                e._confused_timer = _SPOTLIGHT_CONFUSE_DUR

    def _tick_burn(self, enemies, dt):
        for e in enemies:
            if not e.alive: continue
            ft = getattr(e, '_st_fire_timer', 0.0)
            if ft <= 0: continue
            e._st_fire_timer = max(0.0, ft - dt)
            e._st_fire_tick  = getattr(e, '_st_fire_tick', 0.0) + dt
            if e._st_fire_tick >= self._burn_tick:
                e._st_fire_tick -= self._burn_tick
                e.take_damage(self._burn_dmg)
                self.total_damage += self._burn_dmg

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt
        if self.cd_left > 0: self.cd_left -= dt
        if self._conf_cd > 0: self._conf_cd -= dt
        if self._burn_dmg > 0:
            self._tick_burn(enemies, dt)

        # Tick confusion
        for e in enemies:
            if not e.alive: continue
            ct = getattr(e, '_confused_timer', 0.0)
            if ct > 0:
                e._confused_timer = ct - dt
                if e._confused_timer <= 0:
                    e._confused = False; e._confused_timer = 0.0

        self._last_enemies = enemies
        targets = self._get_targets(enemies, 1)
        if not targets: return

        t0 = targets[0]
        self._target_angle = math.atan2(t0.y - self.py, t0.x - self.px)

        # Rotate beam
        diff = math.atan2(math.sin(self._target_angle - self._beam_angle),
                          math.cos(self._target_angle - self._beam_angle))
        max_rot = _SPOTLIGHT_BEAM_ROT_SPEED * dt
        self._beam_angle += math.copysign(min(abs(diff), max_rot), diff)

        # Attack
        if self.cd_left <= 0:
            self.cd_left = self.firerate
            range_px  = self.range_tiles * TILE
            beam_r_px = self._beam_r * TILE

            # Find actual beam end (shortened to closest in-cone target)
            actual_len = range_px
            beam_half  = math.radians(22)
            for e in self._last_enemies:
                if not e.alive: continue
                dx2 = e.x - self.px; dy2 = e.y - self.py
                d2  = math.hypot(dx2, dy2)
                if d2 < 1 or d2 > range_px: continue
                at = math.atan2(dy2, dx2)
                ad = abs(math.atan2(math.sin(at - self._beam_angle),
                                    math.cos(at - self._beam_angle)))
                if ad <= beam_half and d2 < actual_len:
                    actual_len = d2
                    break

            # Circle center = beam end
            bx = self.px + math.cos(self._beam_angle) * actual_len
            by = self.py + math.sin(self._beam_angle) * actual_len

            for e in enemies:
                if not e.alive: continue
                if e.IS_HIDDEN and not self._expose_hidden and not self.hidden_detection: continue
                # Hit only enemies inside the circle at beam end
                if dist((e.x, e.y), (bx, by)) > beam_r_px: continue

                e.take_damage(self.damage)
                self.total_damage += self.damage
                self._conf_accum  += self.damage

                if self._expose_hidden and e.IS_HIDDEN:
                    e._exposed = True; e._exposed_timer = self.firerate + 0.5

                if self._burn_dmg > 0:
                    e._st_fire_timer = self._burn_time * _dm(); e._st_fire_tick = 0.0

            # Confusion (lv4, with cooldown)
            if self._conf_thresh > 0 and self._conf_accum >= self._conf_thresh and self._conf_cd <= 0:
                self._conf_accum = 0.0
                self._conf_cd    = _SPOTLIGHT_CONFUSE_CD
                self._confuse_enemies(enemies)

        # Tick exposed
        for e in enemies:
            if not e.alive: continue
            et = getattr(e, '_exposed_timer', 0.0)
            if et > 0:
                e._exposed_timer = et - dt
                if e._exposed_timer <= 0:
                    e._exposed = False; e._exposed_timer = 0.0

    def draw(self, surf):
        t   = self._anim_t
        cx, cy = int(self.px), int(self.py)
        a   = self._beam_angle
        ca, sa = math.cos(a), math.sin(a)
        pa, pb = -sa, ca

        # ── Beam: one thick semi-transparent ray ──
        range_px = self.range_tiles * TILE

        # Only draw beam + circle if there's a target in range
        has_target = any(
            e.alive and not (e.IS_HIDDEN and not self.hidden_detection)
            and dist((e.x, e.y), (self.px, self.py)) <= range_px
            for e in getattr(self, '_last_enemies', [])
        )

        if has_target:
            # Shorten beam to closest in-cone target
            actual_beam_len = range_px
            beam_half = math.radians(22)
            for e in getattr(self, '_last_enemies', []):
                if not e.alive: continue
                dx2 = e.x - self.px; dy2 = e.y - self.py
                d2  = math.hypot(dx2, dy2)
                if d2 < 1 or d2 > range_px: continue
                angle_to   = math.atan2(dy2, dx2)
                angle_diff = abs(math.atan2(math.sin(angle_to - self._beam_angle),
                                            math.cos(angle_to - self._beam_angle)))
                if angle_diff <= beam_half and d2 < actual_beam_len:
                    actual_beam_len = d2
                    break

            beam_end_x = cx + int(ca * actual_beam_len)
            beam_end_y = cy + int(sa * actual_beam_len)

            beam_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.line(beam_s, (255, 240, 100, 90),  (cx, cy), (beam_end_x, beam_end_y), 22)
            pygame.draw.line(beam_s, (255, 255, 180, 140), (cx, cy), (beam_end_x, beam_end_y), 8)
            pygame.draw.line(beam_s, (255, 255, 240, 200), (cx, cy), (beam_end_x, beam_end_y), 3)
            surf.blit(beam_s, (0, 0))

            # Small circle at beam end — ÷8 of original (÷2 of last version)
            beam_r_px   = self._beam_r * TILE
            circle_size = max(3, int(beam_r_px * 0.27))
            bx2 = beam_end_x; by2 = beam_end_y
            gs = pygame.Surface((circle_size * 2 + 4, circle_size * 2 + 4), pygame.SRCALPHA)
            cx3, cy3 = circle_size + 2, circle_size + 2
            pygame.draw.circle(gs, (255, 248, 120, 130), (cx3, cy3), circle_size)
            pygame.draw.circle(gs, (255, 255, 200, 200), (cx3, cy3), max(2, circle_size - 1), 2)
            surf.blit(gs, (bx2 - circle_size - 2, by2 - circle_size - 2))

        # ── Tower body ──
        pygame.draw.circle(surf, C_SPOTLIGHT_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_SPOTLIGHT,      (cx, cy), 21)
        pygame.draw.circle(surf, (255, 250, 180),  (cx, cy), 21, 2)

        # Rotating lamp head
        head_cx = cx + int(ca * 14); head_cy = cy + int(sa * 14)
        pts = [
            (int(head_cx + pa * 8  - ca * 6), int(head_cy + pb * 8  - sa * 6)),
            (int(head_cx - pa * 8  - ca * 6), int(head_cy - pb * 8  - sa * 6)),
            (int(head_cx - pa * 4  + ca * 9), int(head_cy - pb * 4  + sa * 9)),
            (int(head_cx + pa * 4  + ca * 9), int(head_cy + pb * 4  + sa * 9)),
        ]
        pygame.draw.polygon(surf, (180, 140, 20), pts)
        pygame.draw.polygon(surf, C_SPOTLIGHT, pts, 2)

        # Lens glow
        lx = cx + int(ca * 20); ly = cy + int(sa * 20)
        ls = pygame.Surface((20, 20), pygame.SRCALPHA)
        p2 = int(abs(math.sin(t * 4)) * 40 + 180)
        pygame.draw.circle(ls, (255, 250, 150, p2), (10, 10), 8)
        pygame.draw.circle(ls, (255, 255, 220, 255), (10, 10), 4)
        surf.blit(ls, (lx - 10, ly - 10))

        # Confusion charge bar (lv4)
        if self._conf_thresh > 0:
            frac_c = min(1.0, self._conf_accum / self._conf_thresh)
            cd_frac = max(0.0, 1.0 - self._conf_cd / _SPOTLIGHT_CONFUSE_CD) if self._conf_cd > 0 else 1.0
            bw = 44; bx3 = cx - bw // 2; by3 = cy - 44
            pygame.draw.rect(surf, (40, 30, 10),   (bx3, by3, bw, 5), border_radius=2)
            bar_col = (255, 200, 30) if self._conf_cd <= 0 else (150, 120, 30)
            pygame.draw.rect(surf, bar_col, (bx3, by3, int(bw * frac_c), 5), border_radius=2)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_SPOTLIGHT, (cx - 10 + i * 6, cy + 36), 3)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, 22), (r, r), r)
        pygame.draw.circle(s, (255, 255, 255, 60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        conf_str = (f"{int(self._conf_accum)}/{self._conf_thresh} (cd {self._conf_cd:.1f}s)"
                    if self._conf_thresh else "—")
        return {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "BeamCircle": f"{self._beam_r} tiles",
            "Burn":     f"{self._burn_dmg}/tick {self._burn_time:.0f}s" if self._burn_dmg else "—",
            "Expose":   "YES" if self._expose_hidden else "lv2+",
            "Confuse":  conf_str,
        }

# ═══════════════════════════════════════════════════════════════════════════════
# Commander  (REWORK)
# ═══════════════════════════════════════════════════════════════════════════════
C_COMMANDER      = (220, 160, 60)
C_COMMANDER_DARK = (80,  50,  10)

# Tuple: (damage, firerate, range_tiles, upgrade_cost,
#         buff_pct,        # passive firerate buff to nearby units (0.10 = 10% faster)
#         cta_buff_pct,    # Call to Arms ability extra buff (0 = ability not unlocked)
#         hidden_detection)
#
# Mechanic:
#  - Passively boosts firerate of all units in buff_range by buff_pct
#  - lv2+: Call to Arms ability — temporary bonus buff_pct on top of passive, 15s cd 30s dur
#  - lv2: unlocks hidden + lead + fly detection

COMMANDER_LEVEL_NAMES = [None, "Leadership", "Call to Arms", "Intense Training", "Strength in Numbers"]

COMMANDER_LEVELS = [
    # lv0  place $2500
    # dmg   fr     rng   cost   buff%  cta%   hid
    ( 10,  0.608,  7.0,  None,  0.10,  0.0,  False),
    # lv1  Leadership  +$400
    ( 10,  0.608,  7.0,   400,  0.15,  0.0,  False),
    # lv2  Call to Arms  +$2450
    ( 25,  0.608, 10.0,  2450,  0.15,  0.10,  True),
    # lv3  Intense Training  +$4500
    ( 40,  0.608, 12.0,  4500,  0.175, 0.15,  True),
    # lv4  Strength in Numbers  +$14000
    ( 60,  0.608, 14.0, 14000,  0.20,  0.20,  True),
]

_CMD_BUFF_RANGE   = 12.0   # tiles — fixed buff radius (same all levels)
_CMD_CTA_CD       = 15.0   # Call to Arms cooldown seconds
_CMD_CTA_DUR      = 30.0   # Call to Arms duration seconds


class CallToArmsAbility:
    """Temporarily adds cta_buff_pct on top of passive buff for 30s, 15s cd."""
    name = "Call to Arms"
    cooldown = _CMD_CTA_CD

    def __init__(self, owner):
        self.owner       = owner
        self.cd_left     = 0.0
        self._active_timer = 0.0
        self._boosted    = []

    def update(self, dt):
        if self.cd_left > 0: self.cd_left -= dt
        if self._active_timer > 0:
            self._active_timer -= dt
            if self._active_timer <= 0: self._expire()

    def ready(self): return self.cd_left <= 0 and self._active_timer <= 0

    def activate(self, enemies_or_units=None, effects=None):
        units = getattr(self.owner, '_game_units_ref', None) or []
        if not self.ready(): return False
        self.cd_left = self.cooldown
        self._active_timer = _CMD_CTA_DUR
        r = _CMD_BUFF_RANGE * TILE
        self._boosted = []
        for u in units:
            if u is self.owner: continue
            if dist((u.px, u.py), (self.owner.px, self.owner.py)) <= r:
                base = getattr(u, '_cmd_orig_fr', u.firerate)
                # Apply both passive + CTA buff
                total_mult = 1.0 - (self.owner.buff_pct + self.owner.cta_buff_pct)
                u._cmd_cta_orig = base
                u.firerate = base * total_mult
                u._cmd_cta_active = True
                self._boosted.append(u)
        return True

    def _expire(self):
        for u in self._boosted:
            if hasattr(u, '_cmd_cta_orig'):
                # Restore to passive-buffed value
                base = u._cmd_cta_orig
                u.firerate = base * (1.0 - self.owner.buff_pct)
                del u._cmd_cta_orig
            u._cmd_cta_active = False
        self._boosted = []

    @property
    def is_active(self): return self._active_timer > 0


class Commander(Unit):
    PLACE_COST       = 650
    COLOR            = C_COMMANDER
    NAME             = "Commander"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._aim_angle   = 0.0
        self._shoot_flash = 0.0
        self._anim_t      = 0.0
        self.buff_range   = _CMD_BUFF_RANGE
        self._apply_level()

    def _apply_level(self):
        row = COMMANDER_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self.buff_pct, self.cta_buff_pct,
         self.hidden_detection) = row
        # Unlock CTA ability at lv2
        if self.level >= 2 and self.ability is None:
            self.ability = CallToArmsAbility(self)

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(COMMANDER_LEVELS): return None
        return COMMANDER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(COMMANDER_LEVELS): self.level = nxt; self._apply_level()

    def _apply_buff(self, units):
        r = self.buff_range * TILE
        for u in units:
            if u is self: continue
            in_range = dist((u.px, u.py), (self.px, self.py)) <= r
            if in_range:
                if not getattr(u, '_cmd_cta_active', False):
                    if not hasattr(u, '_cmd_orig_fr'):
                        u._cmd_orig_fr = u.firerate
                    u.firerate = u._cmd_orig_fr * (1.0 - self.buff_pct)
                    u._cmd_in_range = True
            else:
                if getattr(u, '_cmd_in_range', False):
                    u._cmd_in_range = False
                    if not getattr(u, '_cmd_cta_active', False):
                        if hasattr(u, '_cmd_orig_fr'):
                            u.firerate = u._cmd_orig_fr
                            del u._cmd_orig_fr

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt
        if self.cd_left > 0: self.cd_left -= dt
        if self._shoot_flash > 0: self._shoot_flash -= dt
        if self.ability: self.ability.update(dt)
        targets = self._get_targets(enemies, 1)
        if self.cd_left <= 0 and targets:
            t = targets[0]
            self._aim_angle = math.atan2(t.y - self.py, t.x - self.px)
            self.cd_left = self.firerate
            t.take_damage(self.damage)
            self.total_damage += self.damage
            self._shoot_flash = 0.12

    def update_buff(self, units):
        self._game_units_ref = units
        self._apply_buff(units)

    def draw(self, surf):
        t = self._anim_t
        cx, cy = int(self.px), int(self.py)
        # Buff aura
        r_px = int(self.buff_range * TILE)
        aura_s = pygame.Surface((r_px*2, r_px*2), pygame.SRCALPHA)
        pulse_a = int(abs(math.sin(t*1.5))*18+10)
        pygame.draw.circle(aura_s, (220,170,60,pulse_a), (r_px,r_px), r_px)
        pygame.draw.circle(aura_s, (255,200,80,40),      (r_px,r_px), r_px, 2)
        surf.blit(aura_s, (cx-r_px, cy-r_px))
        # CTA glow
        if self.ability and self.ability.is_active:
            glow_r = int(r_px*1.08)
            glow_s = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
            ga = int(abs(math.sin(t*5))*60+60)
            pygame.draw.circle(glow_s, (255,240,120,ga), (glow_r,glow_r), glow_r, 4)
            surf.blit(glow_s, (cx-glow_r, cy-glow_r))
        # Body
        pygame.draw.circle(surf, C_COMMANDER_DARK, (cx,cy), 27)
        pygame.draw.circle(surf, C_COMMANDER,      (cx,cy), 21)
        pygame.draw.circle(surf, (255,220,100),    (cx,cy), 21, 2)
        # Hat
        pygame.draw.ellipse(surf, (160,110,20), (cx-15, cy-33, 30, 8))
        pygame.draw.ellipse(surf, (200,150,40), (cx-9,  cy-37, 18, 9))
        # Gun
        ca, sa = math.cos(self._aim_angle), math.sin(self._aim_angle)
        bx1=cx+int(ca*8); by1=cy+int(sa*8); bx2=cx+int(ca*28); by2=cy+int(sa*28)
        pygame.draw.line(surf, (180,140,50), (bx1,by1), (bx2,by2), 4)
        pygame.draw.circle(surf, (230,190,80), (bx2,by2), 3)
        if self._shoot_flash > 0:
            frac = self._shoot_flash/0.12
            fl = pygame.Surface((20,20), pygame.SRCALPHA)
            pygame.draw.circle(fl, (255,240,100,int(200*frac)), (10,10), int(8*frac))
            surf.blit(fl, (bx2-10, by2-10))
        # CTA ability ring
        if self.ability:
            cd_frac = max(0.0, 1.0 - self.ability.cd_left/_CMD_CTA_CD)
            ring_r = 30
            ring_s = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
            if self.ability.is_active:
                rc = (255,240,80,200)
            elif self.ability.ready():
                rc = (255,220,60,180)
            else:
                rc = (160,130,30,100)
            if cd_frac < 1.0 and not self.ability.is_active:
                ae = int(cd_frac*360)
                if ae > 0:
                    pygame.draw.arc(ring_s, rc, pygame.Rect(2,2,ring_r*2,ring_r*2),
                                    math.radians(-90), math.radians(-90+ae), 3)
            elif self.ability.ready():
                pygame.draw.circle(ring_s, (255,240,60,80), (ring_r+2,ring_r+2), ring_r, 3)
            surf.blit(ring_s, (cx-ring_r-2, cy-ring_r-2))
        # Detection dots
        if self.hidden_detection:
            pygame.draw.circle(surf, (100,255,100), (cx+21, cy-21), 6)
        for i in range(self.level):
            pygame.draw.circle(surf, C_COMMANDER, (cx-10+i*7, cy+36), 3)

    def draw_range(self, surf):
        try:
            import game_core as _gc
            colored = _gc.SETTINGS.get("colored_range", False)
        except Exception:
            colored = False
        col = C_COMMANDER if colored else (255,255,255)
        r = int(self.range_tiles*TILE)
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col,22), (r,r), r)
        pygame.draw.circle(s, (*col,60), (r,r), r, 2)
        surf.blit(s, (int(self.px)-r, int(self.py)-r))
        rb = int(self.buff_range*TILE)
        sb = pygame.Surface((rb*2, rb*2), pygame.SRCALPHA)
        pygame.draw.circle(sb, (255,200,60,14), (rb,rb), rb)
        pygame.draw.circle(sb, (255,200,60,50), (rb,rb), rb, 2)
        surf.blit(sb, (int(self.px)-rb, int(self.py)-rb))

    def get_info(self):
        info = {
            "Damage":    self.damage,
            "Firerate":  f"{self.firerate:.3f}",
            "Range":     self.range_tiles,
            "Buff":      f"+{int(self.buff_pct*100)}% faster",
        }
        if self.cta_buff_pct > 0:
            info["CtaBuff"] = f"+{int(self.cta_buff_pct*100)}% CTA"
        if self.hidden_detection:
            info["HidDet"] = "Hidden Detection"
        return info


# ═══════════════════════════════════════════════════════════════════════════════
# Snowballer  (REWORK)
# ═══════════════════════════════════════════════════════════════════════════════
C_SNOWBALLER      = (180, 230, 255)
C_SNOWBALLER_DARK = (40,  80,  130)

# Tuple layout:
#  (damage, firerate, range_tiles, upgrade_cost,
#   slow_pct, slow_max, slow_dur,   # slow per hit / cap / seconds
#   freeze_thresh,                  # slow fraction that triggers freeze (0 = no freeze)
#   freeze_time,                    # seconds enemy stays frozen
#   flying_detection,
#   explosive,                      # lv3+: snowballs AoE-explode on impact
#   splash_r,                       # AoE radius in tiles (0 if not explosive)
#   max_hits,                       # how many enemies the AoE damages (0 = all in radius)
#   defense_bypass)                 # lv3+: ignore armor/defense

# Tuple: (damage, firerate, range_tiles, upgrade_cost,
#          slow_pct, slow_max, slow_dur,
#          freeze_thresh, freeze_time,
#          explosive, splash_r, defense_bypass)
# upgrade_name stored separately below
SNOWBALLER_LEVEL_NAMES = [None, "Snow Day", "Frigid Temperatures", "Snowball Cannon"]
SNOWBALLER_LEVELS = [
    # lv0  place $400
    # dmg   fr     rng  cost  sl%   slmax  sldr  frz_t  frz_s  expl   spl   defbyp  hidet
    (  6,  2.258,  6.0, None, 0.15,  0.30,  2.5,  0.0,  0.0,  False, 0.0,  False,  False),
    # lv1  Snow Day  +$75
    (  7,  2.008,  8.0,   75, 0.15,  0.40,  2.5,  0.0,  0.0,  False, 0.0,  False,  False),
    # lv2  Frigid Temperatures  +$375
    ( 12,  2.008, 10.0,  375, 0.20,  0.60,  3.0,  0.0,  0.0,  False, 0.0,  False,  False),
    # lv3  Snowball Cannon  +$1650 → explosive AoE, freeze, defense bypass, hidden detect
    ( 30,  1.758, 10.0, 1650, 0.30,  0.60,  3.0,  0.60, 2.0,  True,  4.0,  True,   True),
]

_SB_BALL_SPEED = 440.0


class SnowballerBall:
    """Homing snowball — on impact slow + optional AoE explosion."""
    def __init__(self, ox, oy, target, damage, slow_pct, slow_max, slow_dur,
                 freeze_thresh, freeze_time, explosive, splash_r, defense_bypass,
                 all_enemies_ref):
        self.x = float(ox); self.y = float(oy)
        self._target      = target
        dx = target.x - ox; dy = target.y - oy
        d  = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.speed        = _SB_BALL_SPEED
        self.damage       = damage
        self.slow_pct     = slow_pct
        self.slow_max     = slow_max
        self.slow_dur     = slow_dur
        self.freeze_thresh= freeze_thresh
        self.freeze_time  = freeze_time
        self.explosive    = explosive
        self.splash_r     = splash_r * TILE * _am()
        self.defense_bypass = defense_bypass
        self._enemies     = all_enemies_ref
        self.alive        = True
        self._dist_left   = 1400.0
        self._trail       = []
        self.puddle       = None

    def _apply_slow(self, e):
        if getattr(e,'SLOW_RESISTANCE',0.0) >= 1.0: return
        cur = getattr(e, '_sb_slow', 0.0)
        new = min(cur + self.slow_pct, self.slow_max)
        e._sb_slow = new
        e._sb_timer = self.slow_dur
        if not hasattr(e, '_sb_orig_speed'):
            e._sb_orig_speed = e.speed
        resistance = getattr(e, 'SLOW_RESISTANCE', 0.0)
        e.speed = e._sb_orig_speed * (1.0 - new * resistance)
        # Freeze check
        if self.freeze_thresh > 0 and new >= self.freeze_thresh and self.freeze_time > 0:
            e.frozen = True
            e._sb_freeze_timer = self.freeze_time * _dm()

    def _hit_enemy(self, e):
        if self.defense_bypass:
            e.hp -= self.damage
            if e.hp <= 0: e.alive = False
        else:
            e.take_damage(self.damage)
        self._apply_slow(e)

    def _explode(self):
        from game_core import dist as _dist
        if self.explosive:
            for e in self._enemies:
                if not e.alive: continue
                if _dist((e.x, e.y), (self.x, self.y)) <= self.splash_r:
                    self._hit_enemy(e)
        else:
            if self._target and self._target.alive:
                self._hit_enemy(self._target)

    def update(self, dt):
        if not self.alive: return
        self._trail.append((self.x, self.y, 0.0))
        self._trail = [(x, y, a + dt) for x, y, a in self._trail if a < 0.22]
        if self._target and self._target.alive:
            dx = self._target.x - self.x; dy = self._target.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.vx = dx / d; self.vy = dy / d
            if d < 14:
                self._explode(); self.alive = False; return
        else:
            for e in self._enemies:
                if e.alive and math.hypot(e.x - self.x, e.y - self.y) < 18:
                    self._explode(); self.alive = False; return
        step = self.speed * dt
        self.x += self.vx * step; self.y += self.vy * step
        self._dist_left -= step
        if self._dist_left <= 0:
            self._explode(); self.alive = False

    def draw(self, surf):
        if not self.alive: return
        for tx, ty, age in self._trail:
            a = max(0, int(160 * (1 - age / 0.22)))
            ts = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(ts, (200, 240, 255, a), (6, 6), 5)
            surf.blit(ts, (int(tx) - 6, int(ty) - 6))
        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(surf, (120, 180, 255), (cx, cy), 8)
        pygame.draw.circle(surf, (220, 245, 255), (cx, cy), 5)
        pygame.draw.circle(surf, (255, 255, 255),  (cx - 2, cy - 2), 2)


class Snowballer(Unit):
    PLACE_COST       = 400
    COLOR            = C_SNOWBALLER
    NAME             = "Snowballer"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._balls     = []
        self._puddles   = []
        self._flashes   = []
        self._aim_angle = 0.0
        self._apply_level()

    def _apply_level(self):
        row = SNOWBALLER_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._slow_pct, self._slow_max, self._slow_dur,
         self._freeze_thresh, self._freeze_time,
         self._explosive, self._splash_r, self._defense_bypass,
         self.hidden_detection) = row

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(SNOWBALLER_LEVELS): return None
        return SNOWBALLER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(SNOWBALLER_LEVELS): self.level = nxt; self._apply_level()

    def update(self, dt, enemies, effects, money):
        if self.cd_left > 0: self.cd_left -= dt
        targets = self._get_targets(enemies, 1)
        if self.cd_left <= 0 and targets:
            t = targets[0]
            self._aim_angle = math.atan2(t.y - self.py, t.x - self.px)
            self.cd_left = self.firerate
            self.total_damage += self.damage
            ball = SnowballerBall(self.px, self.py, t,
                                  self.damage, self._slow_pct, self._slow_max,
                                  self._slow_dur, self._freeze_thresh, self._freeze_time,
                                  self._explosive, self._splash_r, self._defense_bypass,
                                  enemies)
            self._balls.append(ball)

        for b in self._balls: b.update(dt)
        # Collect explosion flashes from newly dead explosive balls
        for b in self._balls:
            if not b.alive and b.explosive and b.splash_r > 0:
                self._flashes.append({"r": b.splash_r, "x": b.x, "y": b.y, "t": 0.22})
        self._balls = [b for b in self._balls if b.alive]
        self._flashes = [f for f in self._flashes if f["t"] > 0]
        for f in self._flashes: f["t"] -= dt

        # Tick freeze timers
        for e in enemies:
            if not e.alive: continue
            ft = getattr(e, '_sb_freeze_timer', 0.0)
            if ft > 0:
                e._sb_freeze_timer = ft - dt
                if e._sb_freeze_timer <= 0:
                    e.frozen = False

        # Tick slow timers
        for e in enemies:
            if not e.alive: continue
            t2 = getattr(e, '_sb_timer', 0.0)
            if t2 > 0:
                e._sb_timer = t2 - dt
                if e._sb_timer <= 0:
                    e._sb_slow = 0.0
                    if hasattr(e, '_sb_orig_speed'):
                        e.speed = e._sb_orig_speed
                        del e._sb_orig_speed

    def draw(self, surf):
        cx, cy = int(self.px), int(self.py)
        pygame.draw.circle(surf, C_SNOWBALLER_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_SNOWBALLER,      (cx, cy), 21)
        pygame.draw.circle(surf, (220, 245, 255),   (cx, cy), 21, 2)
        for i in range(4):
            a = math.radians(i * 45)
            sx2 = cx + int(math.cos(a) * 14); sy2 = cy + int(math.sin(a) * 14)
            pygame.draw.line(surf, (255, 255, 255), (cx, cy), (sx2, sy2), 2)
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 3)
        ca, sa = math.cos(self._aim_angle), math.sin(self._aim_angle)
        pygame.draw.line(surf, (160, 220, 255),
                         (cx + int(ca * 8), cy + int(sa * 8)),
                         (cx + int(ca * 26), cy + int(sa * 26)), 3)
        if self._explosive:
            pygame.draw.circle(surf, (255, 200, 50), (cx - 18, cy - 18), 5)
        # Draw explosion flashes
        for f in self._flashes:
            frac = max(0.0, f["t"] / 0.22)
            fr2 = max(1, int(f["r"] * (1.0 + (1-frac) * 0.5)))
            fa  = max(0, min(255, int(frac * 160)))
            fa3 = max(0, min(255, fa // 3))
            fs2 = pygame.Surface((fr2*2+4, fr2*2+4), pygame.SRCALPHA)
            pygame.draw.circle(fs2, (180, 230, 255, fa3), (fr2+2, fr2+2), fr2)
            pygame.draw.circle(fs2, (220, 245, 255, fa),  (fr2+2, fr2+2), fr2, 3)
            surf.blit(fs2, (int(f["x"])-fr2-2, int(f["y"])-fr2-2))
        for b in self._balls: b.draw(surf)
        for i in range(self.level):
            pygame.draw.circle(surf, C_SNOWBALLER, (cx - 10 + i * 7, cy + 36), 3)

    def draw_range(self, surf):
        try:
            import game_core as _gc
            colored = _gc.SETTINGS.get("colored_range", False)
        except Exception:
            colored = False
        col = C_SNOWBALLER if colored else (255, 255, 255)
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, 22), (r, r), r)
        pygame.draw.circle(s, (*col, 60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        info = {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "Slow":     f"+{int(self._slow_pct*100)}% max {int(self._slow_max*100)}% / {self._slow_dur:.0f}s",
        }
        if self._explosive:
            info["Splash"] = f"{self._splash_r:.1f} tiles"
            info["DefBypass"] = "YES"
        if self._freeze_thresh > 0:
            info["Freeze"] = f"@{int(self._freeze_thresh*100)}% slow → {self._freeze_time:.0f}s"
        if self.hidden_detection:
            info["FlyDet"] = "Flying Detection"
        return info


# ── SnowballerOld — original version kept for Sandbox ──────────────────────────
SNOWBALLER_OLD_LEVELS = [
    (8,  1.200, 6.0, None, 2.5, 0.20, 0.40, 3.0, False),
    (10, 1.100, 6.5,  350, 2.5, 0.25, 0.45, 3.5, False),
    (14, 1.000, 7.0,  700, 3.0, 0.30, 0.50, 4.0, False),
    (18, 0.900, 7.5, 2000, 3.5, 0.30, 0.55, 5.0, True),
    (24, 0.750, 8.0, 6000, 4.0, 0.35, 0.60, 6.0, True),
]

class SnowballerOldBall:
    def __init__(self, ox, oy, target, damage, splash_r, slow_pct, slow_max,
                 slow_dur, leave_puddle, all_enemies_ref):
        self.x = float(ox); self.y = float(oy)
        self._target = target
        dx = target.x - ox; dy = target.y - oy
        d = math.hypot(dx, dy) or 1
        self.vx = dx/d; self.vy = dy/d
        self.speed = _SB_BALL_SPEED
        self.damage = damage; self.splash_r = splash_r * TILE * _am()
        self.slow_pct = slow_pct; self.slow_max = slow_max
        self.slow_dur = slow_dur; self.leave_puddle = leave_puddle
        self._enemies = all_enemies_ref; self.alive = True
        self._dist_left = 1200.0; self._trail = []; self.puddle = None

    def _apply_slow(self, e):
        if getattr(e,'SLOW_RESISTANCE',0.0) >= 1.0: return
        cur = getattr(e, '_sb_slow', 0.0)
        new = min(cur + self.slow_pct, self.slow_max)
        e._sb_slow = new; e._sb_timer = self.slow_dur
        if not hasattr(e, '_sb_orig_speed'): e._sb_orig_speed = e.speed
        resistance = getattr(e, 'SLOW_RESISTANCE', 0.0)
        e.speed = e._sb_orig_speed * (1.0 - new * resistance)

    def _explode(self):
        from game_core import dist as _dist
        for e in self._enemies:
            if not e.alive: continue
            if _dist((e.x,e.y),(self.x,self.y)) <= self.splash_r:
                e.take_damage(self.damage); self._apply_slow(e)
        if self.leave_puddle:
            self.puddle = {"x":self.x,"y":self.y,"r":self.splash_r,"timer":2.0,
                           "slow_pct":self.slow_pct,"slow_max":self.slow_max,"slow_dur":self.slow_dur}

    def update(self, dt):
        if not self.alive: return
        self._trail.append((self.x,self.y,0.0))
        self._trail = [(x,y,a+dt) for x,y,a in self._trail if a<0.25]
        if self._target and self._target.alive:
            dx=self._target.x-self.x; dy=self._target.y-self.y
            d=math.hypot(dx,dy) or 1; self.vx=dx/d; self.vy=dy/d
            if d<14: self._explode(); self.alive=False; return
        else:
            for e in self._enemies:
                if e.alive and math.hypot(e.x-self.x,e.y-self.y)<18:
                    self._explode(); self.alive=False; return
        step=self.speed*dt; self.x+=self.vx*step; self.y+=self.vy*step
        self._dist_left-=step
        if self._dist_left<=0: self._explode(); self.alive=False

    def draw(self, surf):
        if not self.alive: return
        for tx,ty,age in self._trail:
            a=max(0,int(160*(1-age/0.25))); ts=pygame.Surface((12,12),pygame.SRCALPHA)
            pygame.draw.circle(ts,(200,240,255,a),(6,6),5); surf.blit(ts,(int(tx)-6,int(ty)-6))
        cx,cy=int(self.x),int(self.y)
        pygame.draw.circle(surf,(120,180,255),(cx,cy),8)
        pygame.draw.circle(surf,(220,245,255),(cx,cy),5)
        pygame.draw.circle(surf,(255,255,255),(cx-2,cy-2),2)

class SnowballerOld(Unit):
    PLACE_COST = 400; COLOR = C_SNOWBALLER; NAME = "SnowballerOld"; hidden_detection = False
    def __init__(self, px, py):
        super().__init__(px, py); self._balls=[]; self._puddles=[]; self._aim_angle=0.0; self._apply_level()
    def _apply_level(self):
        row=SNOWBALLER_OLD_LEVELS[self.level]
        (self.damage,self.firerate,self.range_tiles,_,
         self._splash_r,self._slow_pct,self._slow_max,self._slow_dur,self.hidden_detection)=row
    def upgrade_cost(self):
        nxt=self.level+1
        if nxt>=len(SNOWBALLER_OLD_LEVELS): return None
        return SNOWBALLER_OLD_LEVELS[nxt][3]
    def upgrade(self):
        nxt=self.level+1
        if nxt<len(SNOWBALLER_OLD_LEVELS): self.level=nxt; self._apply_level()
    def update(self, dt, enemies, effects, money):
        if self.cd_left>0: self.cd_left-=dt
        targets=self._get_targets(enemies,1)
        if self.cd_left<=0 and targets:
            t=targets[0]; self._aim_angle=math.atan2(t.y-self.py,t.x-self.px)
            self.cd_left=self.firerate; self.total_damage+=self.damage
            leave_puddle=(self.level>=3)
            ball=SnowballerOldBall(self.px,self.py,t,self.damage,self._splash_r,
                                   self._slow_pct,self._slow_max,self._slow_dur,leave_puddle,enemies)
            self._balls.append(ball)
        for b in self._balls: b.update(dt)
        for b in self._balls:
            if not b.alive and hasattr(b,'puddle') and b.puddle:
                self._puddles.append(b.puddle); b.puddle=None
        self._balls=[b for b in self._balls if b.alive]
        for e in enemies:
            if not e.alive: continue
            t2=getattr(e,'_sb_timer',0.0)
            if t2>0:
                e._sb_timer=t2-dt
                if e._sb_timer<=0:
                    e._sb_slow=0.0
                    if hasattr(e,'_sb_orig_speed'): e.speed=e._sb_orig_speed; del e._sb_orig_speed
        new_puddles=[]
        for p in self._puddles:
            p['timer']-=dt
            if p['timer']>0:
                for e in enemies:
                    if not e.alive: continue
                    if math.hypot(e.x-p['x'],e.y-p['y'])<=p['r']:
                        cur=getattr(e,'_sb_slow',0.0); new2=min(cur+p['slow_pct']*dt,p['slow_max'])
                        e._sb_slow=new2; e._sb_timer=p['slow_dur']
                        if not hasattr(e,'_sb_orig_speed'): e._sb_orig_speed=e.speed
                        e.speed=e._sb_orig_speed*(1.0-new2*getattr(e,'SLOW_RESISTANCE',1.0))
                new_puddles.append(p)
        self._puddles=new_puddles
    def draw(self, surf):
        for p in self._puddles:
            frac=p['timer']/2.0; pr=int(p['r'])
            ps=pygame.Surface((pr*2+2,pr*2+2),pygame.SRCALPHA); a=int(frac*80)
            pygame.draw.circle(ps,(140,200,255,a),(pr+1,pr+1),pr)
            pygame.draw.circle(ps,(180,230,255,a+20),(pr+1,pr+1),pr,2)
            surf.blit(ps,(int(p['x'])-pr-1,int(p['y'])-pr-1))
        cx,cy=int(self.px),int(self.py)
        pygame.draw.circle(surf,C_SNOWBALLER_DARK,(cx,cy),27)
        pygame.draw.circle(surf,C_SNOWBALLER,(cx,cy),21)
        pygame.draw.circle(surf,(220,245,255),(cx,cy),21,2)
        for i in range(4):
            a=math.radians(i*45); sx2=cx+int(math.cos(a)*14); sy2=cy+int(math.sin(a)*14)
            pygame.draw.line(surf,(255,255,255),(cx,cy),(sx2,sy2),2)
        pygame.draw.circle(surf,(255,255,255),(cx,cy),3)
        ca,sa=math.cos(self._aim_angle),math.sin(self._aim_angle)
        pygame.draw.line(surf,(160,220,255),(cx+int(ca*8),cy+int(sa*8)),(cx+int(ca*26),cy+int(sa*26)),3)
        if self.hidden_detection: pygame.draw.circle(surf,(100,255,100),(cx+21,cy-21),6)
        for b in self._balls: b.draw(surf)
        for i in range(self.level): pygame.draw.circle(surf,C_SNOWBALLER,(cx-10+i*7,cy+36),3)
    def draw_range(self, surf):
        r=int(self.range_tiles*TILE); s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(180,230,255,22),(r,r),r); pygame.draw.circle(s,(180,230,255,60),(r,r),r,2)
        surf.blit(s,(int(self.px)-r,int(self.py)-r))


# ═══════════════════════════════════════════════════════════════════════════════
# Commando
# ═══════════════════════════════════════════════════════════════════════════════
C_COMMANDO      = (80, 160, 80)
C_COMMANDO_DARK = (20, 55,  20)

# Tuple layout:
#  (damage, firerate, range_tiles, upgrade_cost,
#   burst,        # shots per burst
#   burst_cd,     # seconds pause after burst
#   pierce,       # how many enemies each bullet passes through
#   hidden_detection)
#
# Mechanic:
#  - Fires a burst of `burst` bullets rapidly, then reloads for burst_cd seconds
#  - Each bullet homes toward its target (first enemy) and pierces `pierce` enemies
#  - Lv2+: grenades — every burst fires one grenade that deals AoE damage in 3-tile radius
#  - Lv4: dual fire — two bullets per shot toward two closest enemies

COMMANDO_LEVELS = [
    # lv0  place $900
    (4,  0.12, 8.0, None, 4,  1.2, 1, False),
    # lv1  +$600
    (5,  0.11, 8.5,  600, 5,  1.1, 2, False),
    # lv2  +$1500  (grenade)
    (6,  0.10, 9.0, 1500, 6,  1.0, 2, False),
    # lv3  +$4000  (hidden det, faster fire)
    (8,  0.09, 9.5, 4000, 8,  0.9, 3, True),
    # lv4  +$10000  (dual fire, more pierce)
    (12, 0.08,10.0,10000, 10, 0.8, 4, True),
]

_COMMANDO_BULLET_SPEED = 560.0
_COMMANDO_GRENADE_SPEED = 340.0


class CommandoBullet:
    def __init__(self, ox, oy, target, damage, pierce, all_enemies_ref):
        self.x = float(ox); self.y = float(oy)
        self._target = target
        dx = target.x - ox; dy = target.y - oy
        d  = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.speed  = _COMMANDO_BULLET_SPEED
        self.damage = damage
        self.pierce_left = pierce
        self._enemies = all_enemies_ref
        self._hit_ids = set()
        self._dist_left = 900.0
        self.alive = True

    def update(self, dt):
        if not self.alive: return
        if self._target and self._target.alive and id(self._target) not in self._hit_ids:
            dx = self._target.x - self.x; dy = self._target.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.vx = dx / d; self.vy = dy / d
        step = self.speed * dt
        self.x += self.vx * step; self.y += self.vy * step
        self._dist_left -= step
        if self._dist_left <= 0:
            self.alive = False; return
        for e in self._enemies:
            if not e.alive or id(e) in self._hit_ids: continue
            if math.hypot(e.x - self.x, e.y - self.y) < e.radius + 5:
                e.take_damage(self.damage)
                self._hit_ids.add(id(e))
                self.pierce_left -= 1
                if self.pierce_left <= 0:
                    self.alive = False; return

    def draw(self, surf):
        if not self.alive: return
        cx, cy = int(self.x), int(self.y)
        tail_x = self.x - self.vx * 10; tail_y = self.y - self.vy * 10
        pygame.draw.line(surf, (140, 220, 100), (int(tail_x), int(tail_y)), (cx, cy), 2)
        pygame.draw.circle(surf, (200, 255, 150), (cx, cy), 3)


class CommandoGrenade:
    def __init__(self, ox, oy, target, damage, splash_r, all_enemies_ref):
        self.x = float(ox); self.y = float(oy)
        self._target = target
        dx = target.x - ox; dy = target.y - oy
        d  = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.speed  = _COMMANDO_GRENADE_SPEED
        self.damage = damage * 3  # grenade deals 3x bullet damage AoE
        self.splash_r = splash_r * _am()
        self._enemies = all_enemies_ref
        self._dist_left = 800.0
        self.alive = True
        self._exploded = False

    def _explode(self):
        from game_core import dist as _dist
        for e in self._enemies:
            if not e.alive: continue
            if _dist((e.x, e.y), (self.x, self.y)) <= self.splash_r:
                e.take_damage(self.damage)
        self._exploded = True

    def update(self, dt):
        if not self.alive: return
        if self._target and self._target.alive:
            dx = self._target.x - self.x; dy = self._target.y - self.y
            d  = math.hypot(dx, dy) or 1
            self.vx = dx / d; self.vy = dy / d
            if d < 16:
                self._explode(); self.alive = False; return
        step = self.speed * dt
        self.x += self.vx * step; self.y += self.vy * step
        self._dist_left -= step
        if self._dist_left <= 0:
            self._explode(); self.alive = False

    def draw(self, surf):
        if not self.alive: return
        cx, cy = int(self.x), int(self.y)
        gs = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(gs, (80, 160, 60, 200), (10, 10), 6)
        pygame.draw.circle(gs, (140, 220, 80, 255), (10, 10), 4)
        pygame.draw.rect(gs, (60, 120, 50), (8, 2, 4, 5))
        surf.blit(gs, (cx - 10, cy - 10))


class Commando(Unit):
    PLACE_COST       = 900
    COLOR            = C_COMMANDO
    NAME             = "Commando"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._bullets   = []
        self._grenades  = []
        self._burst_left = 0
        self._burst_timer = 0.0
        self._in_burst   = False
        self._burst_cd_left = 0.0
        self._aim_angle = 0.0
        self._anim_t    = 0.0
        self._apply_level()

    def _apply_level(self):
        row = COMMANDO_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._burst, self._burst_cd, self._pierce,
         self.hidden_detection) = row
        self._grenade_on = (self.level >= 2)
        self._dual_fire  = (self.level >= 4)

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(COMMANDO_LEVELS): return None
        return COMMANDO_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(COMMANDO_LEVELS): self.level = nxt; self._apply_level()

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt

        # Burst cooldown
        if self._burst_cd_left > 0:
            self._burst_cd_left -= dt
            for b in self._bullets: b.update(dt)
            for g in self._grenades: g.update(dt)
            self._bullets  = [b for b in self._bullets  if b.alive]
            self._grenades = [g for g in self._grenades if g.alive]
            return

        # Shoot timer
        if self.cd_left > 0: self.cd_left -= dt

        targets = self._get_targets(enemies, 2 if self._dual_fire else 1)

        if not self._in_burst:
            if self.cd_left <= 0 and targets:
                self._in_burst   = True
                self._burst_left = self._burst
        
        if self._in_burst and self.cd_left <= 0 and targets:
            t1 = targets[0]
            self._aim_angle = math.atan2(t1.y - self.py, t1.x - self.px)
            self.cd_left = self.firerate

            # Fire primary bullet
            b = CommandoBullet(self.px, self.py, t1, self.damage, self._pierce, enemies)
            self._bullets.append(b)
            self.total_damage += self.damage

            # Dual fire: second bullet at second target
            if self._dual_fire and len(targets) >= 2:
                b2 = CommandoBullet(self.px, self.py, targets[1], self.damage, self._pierce, enemies)
                self._bullets.append(b2)
                self.total_damage += self.damage

            self._burst_left -= 1

            # On first shot of burst, optionally launch grenade
            if self._grenade_on and self._burst_left == self._burst - 1:
                splash_r = 3.0 * TILE * _am()
                g = CommandoGrenade(self.px, self.py, t1,
                                    self.damage, splash_r, enemies)
                self._grenades.append(g)

            if self._burst_left <= 0:
                self._in_burst    = False
                self._burst_cd_left = self._burst_cd

        for b in self._bullets: b.update(dt)
        for g in self._grenades: g.update(dt)
        self._bullets  = [b for b in self._bullets  if b.alive]
        self._grenades = [g for g in self._grenades if g.alive]

    def draw(self, surf):
        t   = self._anim_t
        cx, cy = int(self.px), int(self.py)

        pygame.draw.circle(surf, C_COMMANDO_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_COMMANDO,      (cx, cy), 21)
        pygame.draw.circle(surf, (120, 200, 100), (cx, cy), 21, 2)

        # Gun — rectangular barrel with sight
        ca, sa = math.cos(self._aim_angle), math.sin(self._aim_angle)
        pa, pb = -sa, ca
        bx1 = cx + int(ca * 8);  by1 = cy + int(sa * 8)
        bx2 = cx + int(ca * 30); by2 = cy + int(sa * 30)
        # Barrel (thick)
        for w in [6, 4, 2]:
            col = (40, 100, 40) if w == 6 else (80, 160, 80) if w == 4 else (140, 220, 100)
            pygame.draw.line(surf, col, (bx1, by1), (bx2, by2), w)
        # Sight
        pygame.draw.circle(surf, (180, 255, 140), (bx2, by2), 3)

        # Ammo indicator (burst count)
        shots_left = max(0, self._burst - (self._burst - self._burst_left)) if self._in_burst else self._burst
        burst_frac = shots_left / max(1, self._burst)
        bw2 = 32; bh2 = 4
        bx3 = cx - bw2 // 2; by3 = cy - 42
        pygame.draw.rect(surf, (20, 40, 20), (bx3, by3, bw2, bh2), border_radius=2)
        bcol = (100, 220, 80) if burst_frac > 0.4 else (220, 200, 60)
        pygame.draw.rect(surf, bcol, (bx3, by3, int(bw2 * burst_frac), bh2), border_radius=2)

        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        for b in self._bullets: b.draw(surf)
        for g in self._grenades: g.draw(surf)

        for i in range(self.level):
            pygame.draw.circle(surf, C_COMMANDO, (cx - 10 + i * 7, cy + 36), 3)

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (80, 200, 80, 22), (r, r), r)
        pygame.draw.circle(s, (80, 200, 80, 60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        cd_str = f"reload {self._burst_cd_left:.1f}s" if self._burst_cd_left > 0 else "ready"
        info = {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "Burst":    f"{self._burst} shots / {self._burst_cd:.1f}s cd ({cd_str})",
            "Pierce":   self._pierce,
            "Grenade":  "YES" if self._grenade_on else "lv2+",
            "DualFire": "YES" if self._dual_fire  else "lv4+",
            "HidDet":   "YES" if self.hidden_detection else "no",
        }
        return info

# ── Caster ────────────────────────────────────────────────────────────────────────
C_HACKER      = (40, 200, 255)
C_HACKER_DARK = (10, 30, 80)

# (damage, firerate, range_tiles, upgrade_cost, hidden_detection)
CASTER_LEVELS = [
    (15, 0.19, 7.5, None,  False),   # lv0
    (18, 0.18, 7.5, 4500,  True),    # lv1
    (23, 0.18, 7.5, 7000,  True),    # lv2  — lightning strike unlocked
    (33, 0.15, 7.5, 10000, True),    # lv3
    (36, 0.10, 7.5, 16500, True),    # lv4
]

LIGHTNING_THRESHOLD = 2000   # damage needed to charge lightning
LIGHTNING_DAMAGE    = 300
LIGHTNING_RADIUS    = 120    # px — area for "most enemies" check

class HackerLaserTest(Unit):
    PLACE_COST = 7500
    COLOR      = C_HACKER
    NAME       = "Caster"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._apply_level()
        self._laser_t       = 0.0
        self._laser_targets = []
        self._charge        = 0.0   # damage accumulated for lightning
        self._lightning_flash = 0.0  # visual flash timer
        self._lightning_pos   = None  # (x,y) of last strike
        # Sound
        self._sfx = None
        self._sfx_channel = None
        try:
            import os as _os
            _sfx_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "assets", "sound", "caster_hit_sfx.mp3")
            self._sfx = pygame.mixer.Sound(_sfx_path)
        except Exception:
            self._sfx = None

    def _apply_level(self):
        d, fr, r, _, hd = CASTER_LEVELS[self.level]
        self.damage          = d
        self.firerate        = fr
        self.range_tiles     = r
        self.hidden_detection = hd
        self.cd_left         = 0.0

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(CASTER_LEVELS): return None
        return CASTER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt >= len(CASTER_LEVELS): return
        self.level = nxt
        self._apply_level()

    def _get_sfx_vol(self):
        from game_core import SETTINGS
        if SETTINGS.get("music_muted"): return 0.0
        return max(0.0, SETTINGS.get("music_volume", 0.7) / 6.0)

    def _find_densest_spot(self, enemies):
        """Return (x,y) of the spot with most enemies within LIGHTNING_RADIUS."""
        alive = [e for e in enemies if e.alive]
        if not alive: return None
        best_pos, best_count = None, 0
        for e in alive:
            count = sum(1 for o in alive if math.hypot(o.x - e.x, o.y - e.y) <= LIGHTNING_RADIUS)
            if count > best_count:
                best_count = count
                best_pos = (e.x, e.y)
        return best_pos

    def update(self, dt, enemies, effects, money):
        self._laser_t += dt
        if self.cd_left > 0:
            self.cd_left -= dt
        if self._lightning_flash > 0:
            self._lightning_flash -= dt

        # ALL alive enemies in range are targeted
        targets = self._get_targets(enemies, 9999)
        self._laser_targets = targets

        if self.cd_left <= 0 and targets:
            self.cd_left = self.firerate
            dmg_dealt = 0
            for t in targets:
                t.take_damage(self.damage)
                dmg_dealt += self.damage
            self.total_damage += dmg_dealt
            # Charge lightning (lv2+)
            if self.level >= 2:
                self._charge += dmg_dealt
                if self._charge >= LIGHTNING_THRESHOLD:
                    self._charge -= LIGHTNING_THRESHOLD
                    self._trigger_lightning(enemies, effects)
            # Play attack sound
            if self._sfx:
                try:
                    self._sfx.set_volume(self._get_sfx_vol())
                    if self._sfx_channel is None or not self._sfx_channel.get_busy():
                        self._sfx_channel = self._sfx.play()
                except Exception:
                    pass

    def _trigger_lightning(self, enemies, effects):
        pos = self._find_densest_spot(enemies)
        if pos is None: return
        self._lightning_pos   = pos
        self._lightning_flash = 0.5
        lx, ly = pos
        for e in enemies:
            if e.alive and math.hypot(e.x - lx, e.y - ly) <= LIGHTNING_RADIUS:
                e.take_damage(LIGHTNING_DAMAGE)

    def _zigzag_points(self, x1, y1, x2, y2, segments, amplitude, seed):
        import random as _r
        rng = _r.Random(seed)
        dx = x2 - x1; dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < 1: return [(x1,y1),(x2,y2)]
        px = -dy / length; py = dx / length
        pts = [(x1, y1)]
        for i in range(1, segments):
            t2 = i / segments
            bx = x1 + dx * t2; by = y1 + dy * t2
            taper = math.sin(t2 * math.pi)
            off = rng.uniform(-amplitude, amplitude) * taper
            pts.append((bx + px * off, by + py * off))
        pts.append((x2, y2))
        return pts

    def draw(self, surf):
        cx, cy = int(self.px), int(self.py)
        t = self._laser_t

        # ── Tower body ──────────────────────────────────────────────────────
        pulse = int(abs(math.sin(t * 5)) * 55) + 25
        aura2 = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(aura2, (0, 180, 255, pulse // 3), (60, 60), 56)
        pygame.draw.circle(aura2, (40, 200, 255, pulse), (60, 60), 36)
        surf.blit(aura2, (cx - 60, cy - 60))

        pygame.draw.circle(surf, (5, 15, 40), (cx, cy), 24)
        for i in range(6):
            a = math.radians(i * 60)
            fx = cx + int(math.cos(a) * 22); fy = cy + int(math.sin(a) * 22)
            pygame.draw.circle(surf, (20, 80, 140), (fx, fy), 4)
        pygame.draw.circle(surf, (10, 30, 70), (cx, cy), 19)

        for layer, speed, col, n in [(1, 70, (40,200,255), 6), (-1, 110, (100,220,255), 4)]:
            for i in range(n):
                a = math.radians(t * speed * layer + i * (360//n))
                x1b = cx + int(math.cos(a) * 9);  y1b = cy + int(math.sin(a) * 9)
                x2b = cx + int(math.cos(a) * 17); y2b = cy + int(math.sin(a) * 17)
                pygame.draw.line(surf, col, (x1b, y1b), (x2b, y2b), 2)

        core_r = int(abs(math.sin(t * 9)) * 4) + 4
        core_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, (80, 200, 255, 100), (20, 20), core_r + 6)
        pygame.draw.circle(core_surf, (160, 220, 255, 180), (20, 20), core_r + 2)
        pygame.draw.circle(core_surf, (220, 240, 255, 255), (20, 20), core_r)
        surf.blit(core_surf, (cx - 20, cy - 20))
        pygame.draw.circle(surf, C_HACKER, (cx, cy), 24, 2)

        # Level dots
        for i in range(self.level):
            pygame.draw.circle(surf, C_HACKER, (cx - 14 + i * 7, cy + 36), 3)

        # ── Lightning strike visual ─────────────────────────────────────────
        if self._lightning_flash > 0 and self._lightning_pos:
            lx, ly = int(self._lightning_pos[0]), int(self._lightning_pos[1])
            frac = self._lightning_flash / 0.5
            alpha = int(frac * 220)
            # Strike beam from sky (above screen) to target
            bolt_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            sky_y = max(0, ly - 300)
            seed_l = int(t * 60)
            for bolt_i in range(3):
                pts = self._zigzag_points(lx, sky_y, lx, ly, 12, 30 - bolt_i * 8, seed_l + bolt_i * 111)
                ipts = [(int(p[0]), int(p[1])) for p in pts]
                widths = [14, 7, 2]
                colors = [(40, 180, 255, int(alpha*0.3)), (120, 220, 255, int(alpha*0.6)), (230, 248, 255, alpha)]
                for j in range(len(ipts)-1):
                    pygame.draw.line(bolt_surf, colors[bolt_i], ipts[j], ipts[j+1], widths[bolt_i])
            surf.blit(bolt_surf, (0, 0))
            # Impact circle
            imp_r = int(LIGHTNING_RADIUS * frac)
            imp = pygame.Surface((LIGHTNING_RADIUS*2+40, LIGHTNING_RADIUS*2+40), pygame.SRCALPHA)
            hc = LIGHTNING_RADIUS + 20
            pygame.draw.circle(imp, (40, 160, 255, int(alpha*0.2)), (hc, hc), imp_r + 20)
            pygame.draw.circle(imp, (100, 210, 255, int(alpha*0.5)), (hc, hc), imp_r, 3)
            pygame.draw.circle(imp, (220, 248, 255, alpha), (hc, hc), max(4, imp_r//3))
            surf.blit(imp, (lx - hc, ly - hc))

        # ── Laser beams ─────────────────────────────────────────────────────
        if not self._laser_targets:
            return

        s2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        for target in self._laser_targets:
            if not target.alive:
                continue
            tx, ty = int(target.x), int(target.y)
            tv = self._laser_t

            pygame.draw.line(s2, (0, 100, 200, 10), (cx, cy), (tx, ty), 26)
            pygame.draw.line(s2, (0, 160, 255, 18), (cx, cy), (tx, ty), 14)

            seed_a = int(tv * 28) + id(target) % 9999
            pts_a = self._zigzag_points(cx, cy, tx, ty, 18, 22, seed_a)
            ia = [(int(p[0]), int(p[1])) for p in pts_a]
            for j in range(len(ia)-1):
                pygame.draw.line(s2, (0, 160, 255, 22),   ia[j], ia[j+1], 11)
            for j in range(len(ia)-1):
                pygame.draw.line(s2, (30, 200, 255, 40),  ia[j], ia[j+1], 6)

            seed_b = int(tv * 35) + id(target) % 9999 + 3333
            pts_b = self._zigzag_points(cx, cy, tx, ty, 16, 12, seed_b)
            ib = [(int(p[0]), int(p[1])) for p in pts_b]
            for j in range(len(ib)-1):
                pygame.draw.line(s2, (80, 210, 255, 80),  ib[j], ib[j+1], 4)
            for j in range(len(ib)-1):
                pygame.draw.line(s2, (160, 230, 255, 160), ib[j], ib[j+1], 2)

            seed_c = int(tv * 42) + id(target) % 9999 + 7777
            pts_c = self._zigzag_points(cx, cy, tx, ty, 14, 6, seed_c)
            ic = [(int(p[0]), int(p[1])) for p in pts_c]
            for j in range(len(ic)-1):
                pygame.draw.line(s2, (200, 240, 255, 220), ic[j], ic[j+1], 2)
            for j in range(len(ic)-1):
                pygame.draw.line(s2, (230, 248, 255, 255), ic[j], ic[j+1], 1)

            ir_base = int(abs(math.sin(tv * 22 + tx * 0.05)) * 14) + 8
            imp_size = 120
            imp = pygame.Surface((imp_size, imp_size), pygame.SRCALPHA)
            hc = imp_size // 2
            pygame.draw.circle(imp, (0,  140, 220, 18),  (hc, hc), ir_base + 30)
            pygame.draw.circle(imp, (20, 180, 255, 35),  (hc, hc), ir_base + 20)
            pygame.draw.circle(imp, (60, 210, 255, 70),  (hc, hc), ir_base + 12)
            pygame.draw.circle(imp, (120,220, 255, 130), (hc, hc), ir_base + 5)
            pygame.draw.circle(imp, (180,240, 255, 200), (hc, hc), ir_base)
            pygame.draw.circle(imp, (220,248, 255, 255), (hc, hc), max(2, ir_base - 4))
            import random as _r2
            spark_rng = _r2.Random(int(tv * 20) + tx)
            for _ in range(6):
                sa = spark_rng.uniform(0, math.pi * 2)
                sr = spark_rng.uniform(ir_base + 4, ir_base + 18)
                sx2 = hc + int(math.cos(sa) * sr)
                sy2 = hc + int(math.sin(sa) * sr)
                sx1 = hc + int(math.cos(sa) * (ir_base + 1))
                sy1 = hc + int(math.sin(sa) * (ir_base + 1))
                pygame.draw.line(imp, (140, 220, 255, 180), (sx1, sy1), (sx2, sy2), 1)
            surf.blit(imp, (tx - hc, ty - hc))

        surf.blit(s2, (0, 0))

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (40, 200, 255, 18), (r, r), r)
        pygame.draw.circle(s, (40, 200, 255, 55), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        info = {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.2f}",
            "Range":    self.range_tiles,
            "Targets":  "∞",
            "HidDet":   "YES" if self.hidden_detection else "no",
        }
        if self.level >= 2:
            info["Lightning"] = f"{int(self._charge)}/{LIGHTNING_THRESHOLD} ({LIGHTNING_DAMAGE} dmg)"
        return info

Caster = HackerLaserTest  # alias

# ── Accelerator+ (DoubleAccelerator) REMOVED — stubs for import compatibility ──
C_DACCEL      = (180, 80, 255)
C_DACCEL_DARK = (40, 10, 80)
DACCEL_LEVELS = []

class DoubleAccelerator(Unit):
    """Removed unit — stub only, cannot be placed."""
    PLACE_COST = 999999; COLOR = C_DACCEL; NAME = "Accelerator+"; hidden_detection = True
    def __init__(self, px, py):
        super().__init__(px, py)
        self.damage = 0; self.firerate = 1.0; self.range_tiles = 1
    def update(self, dt, enemies, effects, money): pass
    def draw(self, surf): pass
    def get_info(self): return {}


C_WARLOCK      = (160, 60, 220)
C_WARLOCK_DARK = (50,  10,  80)

# Tuple: (melee_dmg, melee_fr, melee_range, ranged_dmg, ranged_fr, ranged_range,
#          upgrade_cost, hidden_det, melee_pierce, knockback_dist)
WARLOCK_LEVELS = [
    # lv0
    (45,  2.0,  6.0,  25, 1.0, 12.0,  None,  False, 1,  0.0),
    # lv1
    (75,  2.0,  6.0,  40, 1.0, 13.0,  2500,  False, 1,  0.0),
    # lv2  — knockback 15px, hidden detect, ranged: 0.8 fr, +1 range, melee +0.5 range
    (140, 2.0,  6.5,  60, 0.8, 14.0,  6800,  True,  1,  15.0),
    # lv3
    (200, 2.0,  6.5, 115, 0.8, 14.0, 12000,  True,  1,  17.5),
    # lv4  — melee pierce 2
    (200, 1.808,6.5, 190, 0.8, 14.5, 22500,  True,  2,  17.5),
    # lv5  — ranged 0.708 fr
    (400, 1.808,7.5, 260, 0.708,17.0, 32500,  True,  2,  20.0),
]


class Warlock(Unit):
    PLACE_COST       = 4200
    COLOR            = C_WARLOCK
    NAME             = "Warlock"
    hidden_detection = False

    def __init__(self, px, py):
        super().__init__(px, py)
        self._melee_cd   = 0.0
        self._ranged_cd  = 0.0
        self._swing_t    = 0.0    # animation timer
        self._aim_angle  = 0.0
        self._orb_angle  = 0.0
        self._swing_flash = 0.0
        self._laser_flashes = []  # [(tx,ty,age)] red laser flashes
        self._hit_counters = {}
        self._apply_level()

    def _apply_level(self):
        row = WARLOCK_LEVELS[self.level]
        (self._melee_dmg, self._melee_fr, self._melee_range,
         self._ranged_dmg, self._ranged_fr, self._ranged_range,
         _, hd, self._melee_pierce, self._knockback_dist) = row
        self.hidden_detection = hd
        # expose for UI
        self.damage      = self._melee_dmg
        self.firerate    = self._melee_fr
        self.range_tiles = self._ranged_range

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(WARLOCK_LEVELS): return None
        return WARLOCK_LEVELS[nxt][6]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(WARLOCK_LEVELS):
            self.level = nxt; self._apply_level()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _enemies_in_range(self, enemies, range_tiles):
        r = range_tiles * TILE
        out = []
        for e in enemies:
            if not e.alive: continue
            if getattr(e, '_reversed', False): continue
            if e.IS_HIDDEN and not self.hidden_detection: continue
            if dist((e.x, e.y), (self.px, self.py)) <= r:
                out.append(e)
        return out

    def _sort_by_mode(self, pool):
        mode = getattr(self, 'target_mode', 'First')
        if   mode == "First":      pool.sort(key=lambda e: -e.x)
        elif mode == "Last":       pool.sort(key=lambda e:  e.x)
        elif mode == "Lowest HP":  pool.sort(key=lambda e:  e.hp)
        elif mode == "Highest HP": pool.sort(key=lambda e: -e.hp)
        elif mode == "Nearest":    pool.sort(key=lambda e:  dist((e.x,e.y),(self.px,self.py)))
        elif mode == "Farthest":   pool.sort(key=lambda e: -dist((e.x,e.y),(self.px,self.py)))

    # ── update ────────────────────────────────────────────────────────────────
    def update(self, dt, enemies, effects, money):
        self._swing_t  += dt
        self._orb_angle += dt * 120
        if self._melee_cd  > 0: self._melee_cd  -= dt
        if self._ranged_cd > 0: self._ranged_cd -= dt
        if self._swing_flash > 0: self._swing_flash -= dt

        # ── Melee ─────────────────────────────────────────────────────────
        if self._melee_cd <= 0:
            melee_pool = self._enemies_in_range(enemies, self._melee_range)
            if melee_pool:
                self._sort_by_mode(melee_pool)
                primary = melee_pool[0]
                self._aim_angle = math.atan2(primary.y - self.py, primary.x - self.px)
                arc_half = math.radians(90)
                hits = 0
                for e in melee_pool:
                    if hits >= self._melee_pierce: break
                    angle = math.atan2(e.y - self.py, e.x - self.px)
                    diff  = abs(math.atan2(math.sin(angle - self._aim_angle),
                                           math.cos(angle - self._aim_angle)))
                    if diff <= arc_half:
                        e.take_damage(self._melee_dmg)
                        self.total_damage += self._melee_dmg
                        hits += 1
                self._melee_cd   = self._melee_fr
                self._swing_flash = 0.18

        # ── Ranged — only enemies OUTSIDE melee range ──────────────────────
        if self._ranged_cd <= 0:
            all_ranged = self._enemies_in_range(enemies, self._ranged_range)
            melee_ids  = {id(e) for e in self._enemies_in_range(enemies, self._melee_range)}
            ranged_only = [e for e in all_ranged if id(e) not in melee_ids]
            if ranged_only:
                self._sort_by_mode(ranged_only)
                target = ranged_only[0]
                # Instant hit
                target.take_damage(self._ranged_dmg)
                self.total_damage += self._ranged_dmg
                if self._knockback_dist > 0:
                    eid = id(target)
                    self._hit_counters[eid] = self._hit_counters.get(eid, 0) + 1
                    if self._hit_counters[eid] >= 2:
                        self._hit_counters[eid] = 0
                        # Push backward along path (reverse direction of travel)
                        import game_core as _gc
                        path = getattr(target, '_frosty_path', None) or _gc.get_map_path()
                        wp = getattr(target, '_wp_index', 1)
                        # Forward direction = toward current waypoint
                        if wp < len(path):
                            wpx, wpy = path[wp]
                        else:
                            wpx, wpy = path[-1]
                        fwd_dx = wpx - target.x
                        fwd_dy = wpy - target.y
                        fwd_d = math.hypot(fwd_dx, fwd_dy) or 1
                        # Push opposite to travel direction
                        target.x -= fwd_dx / fwd_d * self._knockback_dist
                        target.y -= fwd_dy / fwd_d * self._knockback_dist
                        # If pushed past previous waypoint, snap back and decrement wp
                        if wp >= 2:
                            prev_x, prev_y = path[wp - 1]
                            ppx, ppy = path[wp - 2]
                            seg_dx = prev_x - ppx; seg_dy = prev_y - ppy
                            seg_d = math.hypot(seg_dx, seg_dy) or 1
                            # Check if target is now behind prev waypoint
                            dot = ((target.x - prev_x) * (-seg_dx / seg_d) +
                                   (target.y - prev_y) * (-seg_dy / seg_d))
                            if dot > 0:
                                target.x = float(prev_x)
                                target.y = float(prev_y)
                                target._wp_index = max(1, wp - 1)
                # Store laser flash
                self._laser_flashes.append([float(target.x), float(target.y), 0.5])
                self._ranged_cd = self._ranged_fr

        # ── Tick laser flashes ─────────────────────────────────────────────
        for f2 in self._laser_flashes:
            f2[2] -= dt
        self._laser_flashes = [f2 for f2 in self._laser_flashes if f2[2] > 0]

    # ── draw ─────────────────────────────────────────────────────────────────
    def draw(self, surf):
        cx, cy = int(self.px), int(self.py)
        t = self._swing_t

        # Aura
        pulse = int(abs(math.sin(t * 4)) * 50) + 20
        aura = pygame.Surface((110, 110), pygame.SRCALPHA)
        pygame.draw.circle(aura, (120, 30, 200, pulse // 3), (55, 55), 52)
        pygame.draw.circle(aura, (160, 60, 220, pulse),      (55, 55), 34)
        surf.blit(aura, (cx - 55, cy - 55))

        # Melee flash
        if self._swing_flash > 0:
            frac = self._swing_flash / 0.18
            a2 = math.radians(self._aim_angle)
            arc_r = int(self._melee_range * TILE)
            arc_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            alpha = int(frac * 80)
            for i in range(12):
                ang = a2 - math.radians(90) + math.radians(180 * i / 11)
                x1 = cx + int(math.cos(ang) * 10)
                y1 = cy + int(math.sin(ang) * 10)
                x2 = cx + int(math.cos(ang) * arc_r)
                y2 = cy + int(math.sin(ang) * arc_r)
                pygame.draw.line(arc_s, (220, 100, 255, alpha), (x1, y1), (x2, y2), 3)
            surf.blit(arc_s, (0, 0))

        # Body
        pygame.draw.circle(surf, C_WARLOCK_DARK, (cx, cy), 26)
        pygame.draw.circle(surf, C_WARLOCK,      (cx, cy), 20)
        pygame.draw.circle(surf, (200, 140, 255), (cx, cy), 20, 2)

        # Staff symbol
        pygame.draw.line(surf, (200, 140, 255), (cx, cy - 14), (cx, cy + 14), 3)
        pygame.draw.circle(surf, (230, 180, 255), (cx, cy - 14), 5)
        pygame.draw.circle(surf, (255, 220, 255), (cx, cy - 14), 3)

        # Orbiting orb
        oa = math.radians(self._orb_angle)
        ox2 = cx + int(math.cos(oa) * 22)
        oy2 = cy + int(math.sin(oa) * 22)
        orb_s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(orb_s, (180, 80, 255, 120), (10, 10), 8)
        pygame.draw.circle(orb_s, (230, 180, 255, 220), (10, 10), 5)
        surf.blit(orb_s, (ox2 - 10, oy2 - 10))

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_WARLOCK, (cx - 14 + i * 6, cy + 36), 3)

        # ── Ranged laser flashes (0.5s fade) ────────────────────────────────
        if self._laser_flashes:
            s2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            import random as _r
            for fl in self._laser_flashes:
                ox, oy = int(self.px), int(self.py)
                tx2, ty2 = int(fl[0]), int(fl[1])
                frac = fl[2] / 0.5  # 1.0 fresh → 0.0 gone
                tv = self._swing_t

                pygame.draw.line(s2, (180,0,0,  int(10*frac)), (ox,oy),(tx2,ty2), 22)
                pygame.draw.line(s2, (255,40,40, int(18*frac)), (ox,oy),(tx2,ty2), 14)

                for bolt_i in range(3):
                    seed = int(tv*30) + bolt_i*9999 + tx2
                    amp  = 18 - bolt_i*5
                    segs = 14
                    rng2 = _r.Random(seed)
                    dx2 = tx2-ox; dy2 = ty2-oy
                    ln = math.hypot(dx2,dy2) or 1
                    pvx = -dy2/ln; pvy = dx2/ln
                    pts = [(ox,oy)]
                    for i in range(1,segs):
                        t3 = i/segs
                        bx2 = ox+dx2*t3; by2 = oy+dy2*t3
                        taper = math.sin(t3*math.pi)
                        off = rng2.uniform(-amp,amp)*taper
                        pts.append((bx2+pvx*off, by2+pvy*off))
                    pts.append((tx2,ty2))
                    ipts = [(int(p2[0]),int(p2[1])) for p2 in pts]
                    if bolt_i==0:
                        for j in range(len(ipts)-1):
                            pygame.draw.line(s2,(200,0,0,int(22*frac)),ipts[j],ipts[j+1],11)
                        for j in range(len(ipts)-1):
                            pygame.draw.line(s2,(255,60,60,int(40*frac)),ipts[j],ipts[j+1],6)
                    elif bolt_i==1:
                        for j in range(len(ipts)-1):
                            pygame.draw.line(s2,(255,80,80,int(80*frac)),ipts[j],ipts[j+1],4)
                        for j in range(len(ipts)-1):
                            pygame.draw.line(s2,(255,160,160,int(160*frac)),ipts[j],ipts[j+1],2)
                    else:
                        for j in range(len(ipts)-1):
                            pygame.draw.line(s2,(255,200,200,int(220*frac)),ipts[j],ipts[j+1],2)
                        for j in range(len(ipts)-1):
                            pygame.draw.line(s2,(255,240,240,int(255*frac)),ipts[j],ipts[j+1],1)

                ir = int(abs(math.sin(tv*22+tx2*0.05))*10)+6
                imp = pygame.Surface((80,80),pygame.SRCALPHA)
                hc = 40
                pygame.draw.circle(imp,(180,0,0,   int(20*frac)),(hc,hc),ir+20)
                pygame.draw.circle(imp,(255,60,60,  int(50*frac)),(hc,hc),ir+10)
                pygame.draw.circle(imp,(255,120,120,int(130*frac)),(hc,hc),ir+4)
                pygame.draw.circle(imp,(255,200,200,int(220*frac)),(hc,hc),ir)
                surf.blit(imp,(tx2-hc,ty2-hc))
            surf.blit(s2,(0,0))

    def draw_range(self, surf):
        # Two circles: melee (red) and ranged (white)
        rm = int(self._melee_range  * TILE)
        rr = int(self._ranged_range * TILE)
        # Ranged (white, outer)
        s2 = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
        pygame.draw.circle(s2, (255, 255, 255, 18), (rr, rr), rr)
        pygame.draw.circle(s2, (255, 255, 255, 60), (rr, rr), rr, 2)
        surf.blit(s2, (int(self.px) - rr, int(self.py) - rr))
        # Melee (red, inner)
        s1 = pygame.Surface((rm * 2, rm * 2), pygame.SRCALPHA)
        pygame.draw.circle(s1, (255, 60,  60,  18), (rm, rm), rm)
        pygame.draw.circle(s1, (255, 60,  60,  80), (rm, rm), rm, 2)
        surf.blit(s1, (int(self.px) - rm, int(self.py) - rm))

    def get_info(self):
        info = {
            "Damage":        self._melee_dmg,
            "RangedDamage":  self._ranged_dmg,
            "RangedFR":      f"{self._ranged_fr:.3f}",
            "RangedRange":   self._ranged_range,
        }
        if self._knockback_dist > 0:
            info["Knockback"] = f"{self._knockback_dist}px / 2 hits"
        return info


WarlockUnit = Warlock  # alias


# ── Jester ─────────────────────────────────────────────────────────────────────
C_JESTER      = (220, 80, 160)
C_JESTER_DARK = (80, 20, 55)

# Tuple layout:
#  (damage, firerate, range_tiles, upgrade_cost,
#   burn_dmg,          # fire dot damage per tick
#   burn_dur,          # fire dot total duration (seconds)
#   burn_tick,         # fire dot tick interval
#   expl_range,        # explosion splash radius (tiles)
#   ice_pct,           # ice bomb: slowdown per hit (fraction)
#   ice_max,           # ice bomb: max slowdown (fraction)
#   ice_time,          # ice bomb: slow duration (seconds)
#   ice_def_drop,      # ice bomb: defense drop per hit (fraction, lv3+)
#   ice_expl_range,    # ice bomb: explosion radius (tiles, lv3+)
#   poison_dmg,        # poison bomb: damage per tick (0 = unavailable)
#   poison_time,       # poison bomb: puddle lifetime (seconds)
#   poison_tick,       # poison bomb: tick interval (seconds)
#   conf_time,         # confusion bomb: reversal duration (seconds, 0 = unavailable)
#   conf_cd,           # confusion bomb: per-enemy cooldown (seconds)
#   dual_bomb,         # True = fire two bombs per attack (lv4+)
#   hidden_detection)
#
# Bomb modes: "fire", "ice", "poison", "confusion"
# The Jester picks a target in range, throws a bomb that lands at target position
# applying flat splash (same dmg regardless of distance) up to 5 enemies.
# Poison bomb creates a ground puddle (no splash), lead-pierce via splash damage.

JESTER_LEVELS = [
    # lv0 – place $650
    # dmg  fr      rng  cost   bdmg btdur bttick  expr  ipct  imax  itm   idd   iexr  pdmg  ptm   ptk   cftm  cfcd  dual  hid
    (  4, 1.208,   7,   None,   0,   0.0,  1.0,   4,    0.0,  0.0,  0.0,  0.00, 4,    0,    0.0,  0.4,  0.0,  6.0,  False,False),
    # lv1 – +$400
    (  6, 1.008,   9.3, 400,    1,   4.0,  1.0,   4,    0.0,  0.0,  0.0,  0.00, 4,    0,    0.0,  0.4,  0.0,  6.0,  False,False),
    # lv2 – +$670  (unlocks ice bomb)
    ( 10, 1.008,  10.0, 670,    2,   4.0,  1.0,   4,    0.20, 0.50, 3.0,  0.00, 4,    0,    0.0,  0.4,  0.0,  6.0,  False,False),
    # lv3 – +$2750 (unlocks poison bomb, hidden det, enhanced ice)
    ( 30, 1.008,  10.0,2750,    8,   4.0,  1.0,   4,    0.40, 0.50, 3.0,  0.01, 7,    3,   30.0,  0.4,  0.0,  6.0,  False,True),
    # lv4 – +$8500 (unlocks confusion bomb, dual bombs, faster firerate)
    ( 50, 0.608,  13.0,8500,   14,   4.0,  1.0,   4,    0.50, 0.50, 3.0,  0.01, 7,    5,   30.0,  0.4,  2.0,  6.0,  True, True),
]

_JESTER_MAX_SPLASH_HITS = 5    # max enemies hit by splash
_JESTER_MAX_ICE_SLOW    = 0.50  # absolute max slow from ice bombs
_JESTER_MAX_DEFDROP     = 0.50  # max defense drop (ice chill drop)


class JesterBomb:
    """Projectile arc from Jester to target position, then explodes."""
    TRAVEL_SPEED = 480.0   # px per second

    def __init__(self, ox, oy, tx, ty, bomb_type, jester):
        self.ox = float(ox); self.oy = float(oy)
        self.tx = float(tx); self.ty = float(ty)
        self.bomb_type = bomb_type  # "fire", "ice", "poison", "confusion"
        self.jester = jester        # ref to owning unit for stats
        dx = self.tx - ox; dy = self.ty - oy
        d = math.hypot(dx, dy) or 1
        self.vx = dx / d; self.vy = dy / d
        self.x = float(ox); self.y = float(oy)
        self.alive = True
        self._arc_t = 0.0
        self._total_dist = d
        self._traveled  = 0.0

    # colour per type
    _TYPE_COLS = {
        "fire":      (255, 100, 30),
        "ice":       (80,  200, 255),
        "poison":    (80,  220, 60),
        "confusion": (200, 80,  255),
    }

    def update(self, dt, enemies, effects, total_damage_ref):
        if not self.alive: return
        step = self.TRAVEL_SPEED * dt
        self.x += self.vx * step
        self.y += self.vy * step
        self._traveled += step
        self._arc_t += dt
        if self._traveled >= self._total_dist:
            self._explode(enemies, effects, total_damage_ref)
            self.alive = False

    def _explode(self, enemies, effects, total_damage_ref):
        j = self.jester
        row = JESTER_LEVELS[j.level]
        (damage, _, _, _, bdmg, bdur, btick, expl_r,
         ipct, imax, itm, idd, iexr,
         pdmg, ptm, ptk, cftm, cfcd, _, hid) = row

        expl_px = expl_r * TILE   # explosion radius in pixels
        bt = self.bomb_type

        if bt == "poison":
            # Detect path orientation at puddle location for correct clip on Frosty map
            _path_horiz = True
            best_d = 1e9
            for _e in enemies:
                _ed = math.hypot(_e.x - self.tx, _e.y - self.ty)
                if _ed < best_d:
                    best_d = _ed
                    _ep = getattr(_e, '_frosty_path', None)
                    if _ep and len(_ep) >= 2:
                        _ddx = abs(_ep[-1][0] - _ep[0][0])
                        _ddy = abs(_ep[-1][1] - _ep[0][1])
                        _path_horiz = _ddx >= _ddy
            j._puddles.append({
                "x": self.tx, "y": self.ty,
                "r": expl_px,
                "timer": ptm,
                "tick_t": ptk,
                "dmg": pdmg,
                "def_drop_done": {},
                "_path_horiz": _path_horiz,
            })
            # Poison puddle explosion VFX
            effects.append(_JesterExplosionEffect(self.tx, self.ty, expl_px, (60, 200, 40)))
            return

        if bt == "confusion":
            # No damage, just apply confusion to non-boss enemies in splash
            hits = 0
            for e in enemies:
                if not e.alive: continue
                if getattr(e, '_reversed', False): continue
                if e.IS_HIDDEN and not j.hidden_detection: continue
                if dist((e.x, e.y), (self.tx, self.ty)) > expl_px: continue
                if hits >= _JESTER_MAX_SPLASH_HITS: break
                # Bosses are immune
                if getattr(e, 'IS_BOSS', False): continue
                now_cd = getattr(e, '_jester_conf_cd', 0.0)
                if now_cd > 0: continue
                e._jester_conf_cd = cfcd
                e._reversed = True
                e._jester_conf_timer = cftm * _dm()
                hits += 1
            effects.append(_JesterExplosionEffect(self.tx, self.ty, expl_px, (180, 60, 255)))
            return

        # Fire or Ice — deal splash damage (flat, all in radius equally), apply effects
        # Build candidate list in radius, sort by target mode
        candidates = []
        for e in enemies:
            if not e.alive: continue
            if getattr(e, '_reversed', False): continue
            if e.IS_HIDDEN and not j.hidden_detection: continue
            if dist((e.x, e.y), (self.tx, self.ty)) <= expl_px:
                candidates.append(e)
        # sort by target mode (same as unit targeting)
        mode = getattr(j, 'target_mode', 'First')
        if   mode == "First":       candidates.sort(key=lambda e: -e.x)
        elif mode == "Last":        candidates.sort(key=lambda e:  e.x)
        elif mode == "Lowest HP":   candidates.sort(key=lambda e:  e.hp)
        elif mode == "Highest HP":  candidates.sort(key=lambda e: -e.hp)
        elif mode == "Nearest":     candidates.sort(key=lambda e:  dist((e.x,e.y),(j.px,j.py)))
        elif mode == "Farthest":    candidates.sort(key=lambda e: -dist((e.x,e.y),(j.px,j.py)))
        candidates = candidates[:_JESTER_MAX_SPLASH_HITS]

        for e in candidates:
            # Splash damage does NOT ignore defense (uses normal take_damage)
            e.take_damage(damage)
            total_damage_ref[0] += damage

            if bt == "fire":
                # Apply burn
                e._jester_burn_dmg   = bdmg
                e._jester_burn_dur   = bdur * _dm()
                e._jester_burn_tick  = btick
                e._jester_burn_timer = btick   # first tick after one interval

            elif bt == "ice":
                if getattr(e, 'SLOW_RESISTANCE', 0.0) < 1.0:
                    resistance = getattr(e, 'SLOW_RESISTANCE', 0.0)
                    orig = getattr(e, '_jester_ice_orig_spd', None)
                    if orig is None:
                        e._jester_ice_orig_spd = e.speed
                    cur = getattr(e, '_jester_ice_slow', 0.0)
                    new = min(cur + ipct * (1.0 - resistance), _JESTER_MAX_ICE_SLOW)
                    e._jester_ice_slow = new
                    e._jester_ice_timer = itm * _dm()
                    e.speed = e._jester_ice_orig_spd * (1.0 - e._jester_ice_slow)
                    # Defense drop (lv3+)
                    if idd > 0:
                        dropped = getattr(e, '_jester_ice_defdrop', 0.0)
                        if dropped < _JESTER_MAX_DEFDROP:
                            apply_dd = min(idd, _JESTER_MAX_DEFDROP - dropped)
                            e.ARMOR = max(0.0, e.ARMOR - apply_dd)
                            e._jester_ice_defdrop = dropped + apply_dd

        col = (255, 80, 20) if bt == "fire" else (80, 200, 255)
        effects.append(_JesterExplosionEffect(self.tx, self.ty, expl_px, col))

    def draw(self, surf):
        if not self.alive: return
        # Arc trajectory: bomb bounces up in a parabola
        prog = self._traveled / max(1, self._total_dist)
        arc_off = math.sin(prog * math.pi) * 40  # peak height offset
        cx = int(self.x)
        cy = int(self.y - arc_off)
        col = self._TYPE_COLS.get(self.bomb_type, (200, 200, 200))
        # Shadow on ground
        sh = pygame.Surface((18, 8), pygame.SRCALPHA)
        shadow_alpha = int(prog * 80 + (1-prog) * 20)
        pygame.draw.ellipse(sh, (0, 0, 0, shadow_alpha), (0, 0, 18, 8))
        surf.blit(sh, (int(self.x) - 9, int(self.y) - 4))
        # Bomb body
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, 200), (10, 10), 7)
        pygame.draw.circle(s, (255, 255, 255, 120), (10, 10), 7, 1)
        # Fuse spark
        spark_col = (255, 220, 60) if self._arc_t % 0.12 < 0.06 else (255, 140, 20)
        pygame.draw.circle(s, (*spark_col, 255), (10, 4), 3)
        surf.blit(s, (cx - 10, cy - 10))


class _JesterExplosionEffect:
    """Flash ring effect for Jester bomb explosion."""
    def __init__(self, x, y, radius, color):
        self.x = x; self.y = y; self.radius = radius
        self.color = color; self.life = 0.4; self.t = 0.0

    def update(self, dt):
        self.t += dt
        return self.t < self.life

    def draw(self, surf):
        prog = self.t / self.life
        alpha = int(220 * (1 - prog))
        r = int(self.radius * (0.3 + 0.7 * prog))
        s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color[:3], alpha // 3), (r + 2, r + 2), r)
        pygame.draw.circle(s, (*self.color[:3], alpha),     (r + 2, r + 2), r, max(1, int(3 * (1-prog)) + 1))
        surf.blit(s, (int(self.x) - r - 2, int(self.y) - r - 2))


class JesterPuddleEffect:
    """Visual for lingering poison puddle on ground."""
    def __init__(self, x, y, r, total_time):
        self.x = x; self.y = y; self.r = r
        self.total_time = total_time; self.t = 0.0
        self._bubbles = [(random.uniform(-r, r), random.uniform(-r*0.5, r*0.5),
                          random.uniform(0.4, 1.6)) for _ in range(8)]

    def update(self, dt):
        self.t += dt
        return self.t < self.total_time

    def draw(self, surf):
        prog = self.t / self.total_time
        alpha = int(120 * (1 - prog * 0.6))
        rx = int(self.r); ry = int(self.r * 0.45)
        s = pygame.Surface((rx * 2 + 4, ry * 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (40, 180, 20, alpha), (2, 2, rx * 2, ry * 2))
        pygame.draw.ellipse(s, (80, 230, 40, min(255, alpha + 60)), (2, 2, rx * 2, ry * 2), 2)
        surf.blit(s, (int(self.x) - rx - 2, int(self.y) - ry - 2))
        # Bubbles
        tv = self.t
        for bx, by, spd in self._bubbles:
            ba = int(60 * (1 - prog))
            bubble_y = by - (tv * spd * 12) % (self.r * 0.8)
            bs = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(bs, (100, 255, 60, ba), (4, 4), 3)
            surf.blit(bs, (int(self.x + bx) - 4, int(self.y + bubble_y) - 4))


class Jester(Unit):
    PLACE_COST = 650
    COLOR      = C_JESTER
    NAME       = "Jester"
    hidden_detection = False

    # Available bomb types per level unlock
    _BOMB_UNLOCK = {0: ["fire"], 1: ["fire"], 2: ["fire","ice"],
                    3: ["fire","ice","poison"], 4: ["fire","ice","poison","confusion"]}

    def __init__(self, px, py):
        super().__init__(px, py)
        self._anim_t   = 0.0
        self._bombs    = []    # active bomb projectiles
        self._puddles  = []    # active poison puddles (dicts)
        self._puddle_vfx = []  # JesterPuddleEffect instances
        self.bomb_mode = "fire"
        self._apply_level()

    def _apply_level(self):
        row = JESTER_LEVELS[self.level]
        (self.damage, self.firerate, self.range_tiles, _,
         self._burn_dmg, self._burn_dur, self._burn_tick,
         self._expl_r,
         self._ice_pct, self._ice_max, self._ice_time, self._ice_def_drop, self._ice_expl_r,
         self._poison_dmg, self._poison_time, self._poison_tick,
         self._conf_time, self._conf_cd,
         self._dual, self.hidden_detection) = row
        # Clamp bomb mode to what's available at this level
        available = self._BOMB_UNLOCK.get(self.level, ["fire"])
        if self.bomb_mode not in available:
            self.bomb_mode = "fire"

    def upgrade_cost(self):
        nxt = self.level + 1
        if nxt >= len(JESTER_LEVELS): return None
        return JESTER_LEVELS[nxt][3]

    def upgrade(self):
        nxt = self.level + 1
        if nxt < len(JESTER_LEVELS):
            self.level = nxt
            self._apply_level()

    def _try_attack(self, enemies, effects):
        if self.cd_left > 0: return
        targets = self._get_targets(enemies, 1)
        if not targets: return
        self.cd_left = self.firerate
        t0 = targets[0]

        bomb_type = self.bomb_mode
        # For ice bomb: use ice explosion range
        self._throw_bomb(t0.x, t0.y, bomb_type, effects)
        if self._dual:
            # Second bomb targets same or next enemy
            t2_list = self._get_targets(enemies, 2)
            t2 = t2_list[1] if len(t2_list) >= 2 else t0
            self._throw_bomb(t2.x, t2.y, bomb_type, effects)

    def _throw_bomb(self, tx, ty, bomb_type, effects):
        b = JesterBomb(self.px, self.py, tx, ty, bomb_type, self)
        self._bombs.append(b)

    def update(self, dt, enemies, effects, money):
        self._anim_t += dt
        if self.cd_left > 0: self.cd_left -= dt
        self._try_attack(enemies, effects)

        # Update bombs
        dmg_ref = [0]
        for b in self._bombs:
            b.update(dt, enemies, effects, dmg_ref)
        self.total_damage += dmg_ref[0]
        self._bombs = [b for b in self._bombs if b.alive]

        # Tick burn on enemies
        for e in enemies:
            if not e.alive: continue
            bdur = getattr(e, '_jester_burn_dur', 0.0)
            if bdur > 0:
                e._jester_burn_dur = bdur - dt
                e._jester_burn_timer = getattr(e, '_jester_burn_timer', 0.0) - dt
                if e._jester_burn_timer <= 0:
                    e._jester_burn_timer = getattr(e, '_jester_burn_tick', 1.0)
                    bdmg = getattr(e, '_jester_burn_dmg', 0)
                    if bdmg > 0:
                        e.take_damage(bdmg)
                        self.total_damage += bdmg
                if e._jester_burn_dur <= 0:
                    e._jester_burn_dur = 0.0

        # Tick ice slow timers
        for e in enemies:
            if not e.alive: continue
            itimer = getattr(e, '_jester_ice_timer', 0.0)
            if itimer > 0:
                e._jester_ice_timer = itimer - dt
                if e._jester_ice_timer <= 0:
                    orig = getattr(e, '_jester_ice_orig_spd', None)
                    if orig is not None:
                        e.speed = orig
                    e._jester_ice_orig_spd = None
                    e._jester_ice_slow = 0.0

        # Tick confusion reversal
        for e in enemies:
            if not e.alive: continue
            if getattr(e, '_jester_conf_cd', 0.0) > 0:
                e._jester_conf_cd -= dt
            conf_timer = getattr(e, '_jester_conf_timer', 0.0)
            if conf_timer > 0:
                e._jester_conf_timer = conf_timer - dt
                if e._jester_conf_timer <= 0:
                    e._reversed = False
                    e._jester_conf_timer = 0.0

        # Tick puddles
        new_puddles = []
        for p in self._puddles:
            p["timer"] -= dt
            p["tick_t"] -= dt
            if p["tick_t"] <= 0:
                p["tick_t"] += p["tick_t_orig"] if "tick_t_orig" in p else self._poison_tick
                p["tick_t"] = self._poison_tick
                # Damage enemies in puddle
                for e in enemies:
                    if not e.alive: continue
                    if e.IS_HIDDEN and not self.hidden_detection: continue
                    if dist((e.x, e.y), (p["x"], p["y"])) <= p["r"] * 0.29:
                        e.take_damage(p["dmg"])
                        self.total_damage += p["dmg"]
            if p["timer"] > 0:
                new_puddles.append(p)
        self._puddles = new_puddles

        # Spawn puddle VFX when puddles are created (tracked by count mismatch)
        # Instead, we spawn them in _throw_bomb via effects (done in JesterBomb._explode already)

        # Update puddle VFX
        self._puddle_vfx = [v for v in self._puddle_vfx if v.update(dt)]

    def draw(self, surf):
        cx, cy = int(self.px), int(self.py)
        t = self._anim_t

        # Jester body — colorful magenta/pink
        pygame.draw.circle(surf, C_JESTER_DARK, (cx, cy), 27)
        pygame.draw.circle(surf, C_JESTER,      (cx, cy), 21)
        pygame.draw.circle(surf, (255, 160, 210), (cx, cy), 21, 2)

        # Jester hat — two-pointed fool hat above the circle
        hat_pts = [
            (cx - 10, cy - 20),
            (cx - 16, cy - 40),
            (cx,      cy - 26),
            (cx + 16, cy - 40),
            (cx + 10, cy - 20),
        ]
        pygame.draw.polygon(surf, (180, 40, 120), hat_pts)
        pygame.draw.polygon(surf, (255, 120, 200), hat_pts, 2)
        # Bell on each tip
        pygame.draw.circle(surf, C_GOLD, (cx - 16, cy - 40), 4)
        pygame.draw.circle(surf, C_GOLD, (cx + 16, cy - 40), 4)

        # Animated juggling bomb dots
        for i in range(3):
            a = math.radians(t * 90 * (1 + i * 0.3) + i * 120)
            bx2 = cx + int(math.cos(a) * (24 + i * 3))
            by2 = cy + int(math.sin(a) * (16 + i * 2))
            btype = ["fire", "ice", "poison"][i]
            bcol  = JesterBomb._TYPE_COLS[btype]
            bs = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(bs, (*bcol, 200), (5, 5), 4)
            surf.blit(bs, (bx2 - 5, by2 - 5))

        # Hidden detection indicator
        if self.hidden_detection:
            pygame.draw.circle(surf, (100, 255, 100), (cx + 21, cy - 21), 6)

        # Level pips
        for i in range(self.level):
            pygame.draw.circle(surf, C_JESTER, (cx - 10 + i * 7, cy + 36), 3)

        # Draw active bombs
        for b in self._bombs:
            b.draw(surf)

        # Draw puddle VFX
        for v in self._puddle_vfx:
            v.draw(surf)

        # Draw active puddles (via shared helper, so game loop can call it
        # before unit bodies to keep units visually on top)
        self._draw_puddles_only(surf)

    def _draw_puddles_only(self, surf):
        """Draw poison puddles: bright neon-green organic blob, no road clipping."""
        for p in self._puddles:
            frac = p["timer"] / max(0.01, self._poison_time)

            # 2x smaller than original (was 0.58 capped to PATH_H*0.82)
            r = int(p["r"] * 0.29)
            if r < 6:
                continue

            # ── Bake random geometry once per puddle ────────────────────────
            if "_blob_norm" not in p:
                rng    = random.Random(id(p))
                n_pts  = rng.randint(11, 16)
                norm_pts = []
                for i in range(n_pts):
                    a     = (i / n_pts) * math.pi * 2
                    # Y squish so blob fits road: 0.55 factor keeps it flat-ish
                    spoke = rng.uniform(0.70, 1.25)
                    norm_pts.append((math.cos(a) * spoke,
                                     math.sin(a) * spoke * 0.55))
                # Satellite drops: 2-4, spread outside so they exit road edges
                n_sat    = rng.randint(2, 4)
                norm_sats = []
                for _ in range(n_sat):
                    a  = rng.uniform(0, math.pi * 2)
                    d  = rng.uniform(1.15, 1.75)
                    sr = rng.uniform(0.07, 0.16)
                    norm_sats.append((math.cos(a) * d,
                                      math.sin(a) * d * 0.55,
                                      sr))
                p["_blob_norm"] = (norm_pts, norm_sats)

            norm_pts, norm_sats = p["_blob_norm"]

            # ── Alpha — stay mostly opaque, fade gently at end ───────────────
            alpha_main = max(30, min(240, int(230 * frac + 20)))
            alpha_q    = alpha_main & ~7   # quantise to reduce cache churn

            # ── Build / reuse cached SRCALPHA surface for main blob ──────────
            cache_key = (alpha_q, r)
            if p.get("_surf_key") != cache_key:
                # Extra margin for the outer glow ring
                half = int(r * 1.45) + 8
                size = half * 2
                bx = by = half   # blob centre inside surface

                ps = pygame.Surface((size, size), pygame.SRCALPHA)

                def sc(nx, ny):
                    return (int(bx + nx * r), int(by + ny * r))

                outer_px = [sc(nx * 1.35, ny * 1.35) for nx, ny in norm_pts]
                main_px  = [sc(nx,        ny       ) for nx, ny in norm_pts]
                inner_px = [sc(nx * 0.60, ny * 0.60) for nx, ny in norm_pts]
                core_px  = [sc(nx * 0.28, ny * 0.28) for nx, ny in norm_pts]

                # 1. Diffuse outer glow (large, very transparent)
                if len(outer_px) >= 3:
                    pygame.draw.polygon(ps,
                        (80, 255, 40, max(0, min(255, alpha_q // 4))), outer_px)

                # 2. Main body — full-opacity bright green
                if len(main_px) >= 3:
                    pygame.draw.polygon(ps,
                        (30, 230, 20, alpha_q), main_px)

                # 3. Inner lighter zone
                if len(inner_px) >= 3:
                    pygame.draw.polygon(ps,
                        (120, 255, 70, min(255, alpha_q + 40)), inner_px)

                # 4. Bright core highlight
                if len(core_px) >= 3:
                    pygame.draw.polygon(ps,
                        (200, 255, 160, min(255, alpha_q + 80)), core_px)

                # 5. Crisp neon outline
                if len(main_px) >= 3:
                    pygame.draw.polygon(ps,
                        (170, 255, 100, min(255, alpha_q + 70)), main_px, 2)

                p["_surf_cache"] = ps
                p["_surf_key"]   = cache_key

            ps   = p["_surf_cache"]
            size = ps.get_width()
            half = size // 2

            dest_x = int(p["x"]) - half
            dest_y = int(p["y"]) - half

            # ── Blit main blob — no clipping ─────────────────────────────────
            surf.blit(ps, (dest_x, dest_y))

            # ── Satellite dots drawn WITHOUT road clipping ───────────────────
            px0 = int(p["x"])
            py0 = int(p["y"])
            for nx, ny, nr in norm_sats:
                scx2 = px0 + int(nx * r)
                scy2 = py0 + int(ny * r)
                sr2  = max(3, int(nr * r))
                ds   = sr2 * 2 + 4
                dot_s = pygame.Surface((ds, ds), pygame.SRCALPHA)
                dc    = ds // 2
                # Glow halo
                pygame.draw.circle(dot_s,
                    (80, 255, 40, max(0, alpha_q // 3)), (dc, dc), sr2 + 2)
                # Body
                pygame.draw.circle(dot_s,
                    (30, 230, 20, alpha_q), (dc, dc), sr2)
                # Bright rim
                pygame.draw.circle(dot_s,
                    (170, 255, 100, min(255, alpha_q + 60)), (dc, dc), sr2, 1)
                surf.blit(dot_s, (scx2 - dc, scy2 - dc))

    def draw_range(self, surf):
        r = int(self.range_tiles * TILE)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 100, 180, 18), (r, r), r)
        pygame.draw.circle(s, (255, 100, 180, 60), (r, r), r, 2)
        surf.blit(s, (int(self.px) - r, int(self.py) - r))

    def get_info(self):
        info = {
            "Damage":   self.damage,
            "Firerate": f"{self.firerate:.3f}",
            "Range":    self.range_tiles,
            "SplashR":  f"{self._expl_r} tiles (max {_JESTER_MAX_SPLASH_HITS} hits)",
            "Mode":     self.bomb_mode,
        }
        if self._burn_dmg > 0:
            info["Burn"] = f"{self._burn_dmg}/tick {self._burn_dur:.0f}s"
        if self._ice_pct > 0:
            info["IceSlow"] = f"{int(self._ice_pct*100)}%/hit max {int(self._ice_max*100)}%"
        if self._poison_dmg > 0:
            info["Poison"] = f"{self._poison_dmg}/tick {self._poison_time:.0f}s"
        if self._conf_time > 0:
            info["Confuse"] = f"{self._conf_time:.0f}s / {self._conf_cd:.0f}s cd"
        return info