# ═══════════════════════════════════════════════════════════════════════════════
# enemies.py  —  все враги, волновые данные, WaveManager
# ═══════════════════════════════════════════════════════════════════════════════
import pygame, math, random, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from game_core import (
    SCREEN_W, SCREEN_H, PATH_Y, PATH_H, SLOT_AREA_Y, TILE, MAX_WAVES,
    C_WHITE, C_HP_BG, C_HP_FG, C_HP_FG2, C_GOLD,
    get_map_path, spawn_enemy_at_start,
    font_sm, font_md, txt, draw_rect_alpha, dist,
)

class Enemy:
    DISPLAY_NAME="Normal"
    BASE_HP=8; BASE_SPEED=55; KILL_REWARD=8
    IS_HIDDEN=False; ARMOR=0.0

    def __init__(self, wave=1):
        path = get_map_path()
        self.x=float(path[0][0]); self.y=float(path[0][1])
        self.hp=max(1, self.BASE_HP)
        self.maxhp=self.hp
        self.speed=self.BASE_SPEED+(wave-1)*3
        self.alive=True; self.radius=17
        self._bob=random.uniform(0,math.pi*2)
        self.free_kill=False
        self.frozen=False
        self._wp_index=1  # next waypoint index

    def update(self, dt):
        if self.frozen: self._bob+=dt*4; return False
        self._bob+=dt*4
        path = getattr(self, '_frosty_path', None) or get_map_path()


        if self._wp_index >= len(path):
            self.alive=False; return True
        tx, ty = path[self._wp_index]
        dx = tx - self.x; dy = ty - self.y
        dist_to_wp = math.hypot(dx, dy)
        step = self.speed * dt
        if dist_to_wp <= step + 1:
            self.x = float(tx); self.y = float(ty)
            self._wp_index += 1
            if self._wp_index >= len(path):
                self.alive=False; return True
        else:
            self.x += dx/dist_to_wp * step
            self.y += dy/dist_to_wp * step
        return False

    def take_damage(self, dmg):
        self.hp-=dmg*(1.0-self.ARMOR)
        if self.hp<=0: self.alive=False

    def _draw_hp_bar(self, surf, bw, bh, border_col=None):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        bx=cx-bw//2; by=cy-self.radius-10
        pygame.draw.rect(surf,C_HP_BG,(bx,by,bw,bh),border_radius=2)
        fill=max(0,int(bw*self.hp/self.maxhp))
        if fill:
            col=C_HP_FG2 if self.hp/self.maxhp>0.5 else C_HP_FG
            pygame.draw.rect(surf,col,(bx,by,fill,bh),border_radius=2)
        if border_col:
            pygame.draw.rect(surf,border_col,(bx,by,bw,bh),1,border_radius=2)

    def _hover_label(self, surf):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        mods=[]
        if self.ARMOR>0: mods.append(f"Armor {int(self.ARMOR*100)}%")
        if self.IS_HIDDEN: mods.append("Hidden")
        if getattr(self,'_stun_immune',False): mods.append("Stun Immune")
        slow_res=getattr(self,'SLOW_RESISTANCE',0)
        if slow_res>=1.0: mods.append("Slow Immune")
        elif slow_res>0: mods.append(f"Slow Res {int(slow_res*100)}%")
        label=self.DISPLAY_NAME+("  ["+", ".join(mods)+"]" if mods else "")
        txt(surf,label,(cx,cy-self.radius-28),C_GOLD,font_sm,center=True)
        txt(surf,f"HP {int(self.hp)}/{int(self.maxhp)}",(cx,cy-self.radius-16),C_WHITE,font_sm,center=True)

    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(160,50,50),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,100,100),(cx-5,cy-5),7)
        pygame.draw.circle(surf,C_WHITE,(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,30,5)
        if hovered: self._hover_label(surf)

class TankEnemy(Enemy):
    DISPLAY_NAME="Slow"; BASE_HP=30; BASE_SPEED=28
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=max(1,self.BASE_HP); self.maxhp=self.hp
        self.speed=self.BASE_SPEED+(wave-1); self.radius=22
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob); cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(100,60,20),(cx,cy),self.radius)
        pygame.draw.circle(surf,(160,110,60),(cx-6,cy-6),8)
        pygame.draw.circle(surf,(200,160,90),(cx,cy),self.radius,3)
        self._draw_hp_bar(surf,36,5)
        if hovered: self._hover_label(surf)

class ScoutEnemy(Enemy):
    DISPLAY_NAME="Fast"; BASE_HP=10; BASE_SPEED=140
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=max(1,self.BASE_HP); self.maxhp=self.hp
        self.speed=self.BASE_SPEED+(wave-1)*5; self.radius=12
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.6)*3; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(40,140,180),(cx,cy),self.radius)
        pygame.draw.circle(surf,(140,230,255),(cx-3,cy-3),5)
        pygame.draw.circle(surf,(180,240,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,22,4)
        if hovered: self._hover_label(surf)

class NormalBoss(Enemy):
    DISPLAY_NAME="Normal Boss"; BASE_HP=200; BASE_SPEED=55
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=200; self.maxhp=200
        self.speed=self.BASE_SPEED; self.radius=26
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.8)*1.5; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pygame.draw.circle(s,(180,20,20,35),(48,48),46); surf.blit(s,(cx-48,cy-48))
        pygame.draw.circle(surf,(180,140,20),(cx,cy),self.radius+3,3)
        pygame.draw.circle(surf,(130,20,20),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,50,50),(cx-7,cy-7),11)
        pygame.draw.circle(surf,(240,200,60),(cx,cy),self.radius,2)
        for i in range(5):
            a=math.radians(-90+i*36)
            sx2=cx+math.cos(a)*(self.radius+2); sy2=cy+math.sin(a)*(self.radius+2)
            ex2=cx+math.cos(a)*(self.radius+10); ey2=cy+math.sin(a)*(self.radius+10)
            pygame.draw.line(surf,(240,200,60),(int(sx2),int(sy2)),(int(ex2),int(ey2)),2)
        self._draw_hp_bar(surf,50,6,(240,200,60))
        if hovered: self._hover_label(surf)

class HiddenEnemy(Enemy):
    DISPLAY_NAME="Hidden"; BASE_HP=8; BASE_SPEED=55; IS_HIDDEN=True
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=max(1,self.BASE_HP); self.maxhp=self.hp
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        alpha=180 if detected else (220 if hovered else 128)
        s=pygame.Surface((60,60),pygame.SRCALPHA)
        pygame.draw.circle(s,(120,240,120,alpha),(30,30),self.radius)
        pygame.draw.circle(s,(216,255,216,alpha),(25,25),6)
        pygame.draw.circle(s,(240,255,240,alpha//2),(30,30),self.radius,2)
        surf.blit(s,(cx-30,cy-30))
        if detected or hovered: self._draw_hp_bar(surf,30,5,(100,255,100))
        if hovered: self._hover_label(surf)

class BreakerEnemy(Enemy):
    DISPLAY_NAME="Breaker"; BASE_HP=30; BASE_SPEED=55
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=30; self.maxhp=30; self.speed=self.BASE_SPEED; self.radius=18
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(140,100,20),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,180,60),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(255,220,80),(cx,cy),self.radius,2)
        for i in range(3):
            a=math.radians(i*120+30)
            x1=cx+int(math.cos(a)*4); y1=cy+int(math.sin(a)*4)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(60,40,0),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,30,5,(255,220,80))
        if hovered: self._hover_label(surf)

class ArmoredEnemy(Enemy):
    DISPLAY_NAME="Armored"; BASE_HP=25; BASE_SPEED=55; ARMOR=0.20
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=max(1,self.BASE_HP); self.maxhp=self.hp; self.radius=19
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(80,90,110),(cx,cy),self.radius)
        pygame.draw.circle(surf,(140,160,190),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(180,200,220),(cx,cy),self.radius,3)
        for i in range(4):
            a=math.radians(i*90+45)
            x1=cx+int(math.cos(a)*8); y1=cy+int(math.sin(a)*8)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(200,220,255),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,32,5,(180,200,220))
        if hovered: self._hover_label(surf)

class SlowBoss(Enemy):
    DISPLAY_NAME="Slow Boss"; BASE_HP=25; BASE_SPEED=28
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=25; self.maxhp=25; self.speed=self.BASE_SPEED; self.radius=34
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((108,108),pygame.SRCALPHA)
        pygame.draw.circle(s,(140,80,20,40),(54,54),53); surf.blit(s,(cx-54,cy-54))
        pygame.draw.circle(surf,(200,140,30),(cx,cy),self.radius+5,5)
        pygame.draw.circle(surf,(120,60,10),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,120,50),(cx-8,cy-8),12)
        pygame.draw.circle(surf,(240,180,60),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,60,7,(200,140,30))
        if hovered: self._hover_label(surf)

class HiddenBoss(NormalBoss):
    DISPLAY_NAME="Hidden Boss"; IS_HIDDEN=True
    def __init__(self, wave=1): super().__init__(wave)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.8)*1.5; cx,cy=int(self.x),int(self.y+bob)
        base_alpha=50 if (not detected and not hovered) else 255
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pygame.draw.circle(s,(96,216,96,min(60,base_alpha)),(48,48),46); surf.blit(s,(cx-48,cy-48))
        fa=base_alpha
        sa=pygame.Surface((self.radius*2+24,self.radius*2+24),pygame.SRCALPHA)
        off=10
        pygame.draw.circle(sa,(96,192,96,fa),(self.radius+off,self.radius+off),self.radius+3,3)
        pygame.draw.circle(sa,(48,120,48,fa),(self.radius+off,self.radius+off),self.radius)
        pygame.draw.circle(sa,(144,255,144,fa),(self.radius+off-7,self.radius+off-7),11)
        pygame.draw.circle(sa,(216,255,216,fa),(self.radius+off,self.radius+off),self.radius,2)
        surf.blit(sa,(cx-self.radius-off,cy-self.radius-off))
        if detected or hovered:
            for i in range(5):
                a=math.radians(-90+i*36)
                sx2=cx+math.cos(a)*(self.radius+2); sy2=cy+math.sin(a)*(self.radius+2)
                ex2=cx+math.cos(a)*(self.radius+10); ey2=cy+math.sin(a)*(self.radius+10)
                pygame.draw.line(surf,(180,240,180),(int(sx2),int(sy2)),(int(ex2),int(ey2)),2)
            self._draw_hp_bar(surf,50,6,(180,240,180))
        if hovered: self._hover_label(surf)

class Necromancer(Enemy):
    DISPLAY_NAME="Necromancer"; BASE_HP=360; BASE_SPEED=55
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=360; self.maxhp=360; self.speed=self.BASE_SPEED
        self.radius=26; self._summon_timer=5.0
    def update(self, dt):
        self._summon_timer-=dt; return super().update(dt)
    def should_summon(self):
        if self._summon_timer<=0: self._summon_timer=5.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.8)*1.5; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pygame.draw.circle(s,(80,0,120,40),(48,48),46); surf.blit(s,(cx-48,cy-48))
        pygame.draw.circle(surf,(100,0,160),(cx,cy),self.radius+3,3)
        pygame.draw.circle(surf,(60,0,100),(cx,cy),self.radius)
        pygame.draw.circle(surf,(160,80,220),(cx-6,cy-6),8)
        pygame.draw.circle(surf,(200,100,255),(cx,cy),self.radius,2)
        for i in range(4):
            a=math.radians(i*90+self._bob*20)
            px2=cx+int(math.cos(a)*(self.radius+6)); py2=cy+int(math.sin(a)*(self.radius+6))
            pygame.draw.circle(surf,(220,220,255),(px2,py2),3)
        self._draw_hp_bar(surf,50,6,(200,100,255))
        if hovered: self._hover_label(surf)

class GraveDigger(Enemy):
    DISPLAY_NAME="Grave Digger"; BASE_HP=5000; BASE_SPEED=30
    def __init__(self, wave=1):
        super().__init__(1)
        self.hp=5000; self.maxhp=5000; self.speed=self.BASE_SPEED; self.radius=38
        self._rot=0.0
        self._spawned_fb=False
        self.hw_mode=False
    def update(self, dt):
        self._rot+=dt*90; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        pulse=int(abs(math.sin(self._rot/90*math.pi))*20)
        s=pygame.Surface((132,132),pygame.SRCALPHA)
        pygame.draw.circle(s,(60,180,60,36+pulse),(66,66),62); surf.blit(s,(cx-66,cy-66))
        for i in range(8):
            a=math.radians(self._rot+i*45)
            rx=cx+int(math.cos(a)*(self.radius+8)); ry=cy+int(math.sin(a)*(self.radius+8))
            pygame.draw.circle(surf,(100,220,100),(rx,ry),5)
        pygame.draw.circle(surf,(30,100,30),(cx,cy),self.radius+5,6)
        pygame.draw.circle(surf,(20,60,20),(cx,cy),self.radius)
        pygame.draw.circle(surf,(80,200,80),(cx-10,cy-10),14)
        pygame.draw.circle(surf,(140,255,140),(cx,cy),self.radius,2)
        shovel_a=math.radians(self._rot*0.5)
        sx2=cx+int(math.cos(shovel_a)*10); sy2=cy+int(math.sin(shovel_a)*10)
        ex2=cx+int(math.cos(shovel_a)*(self.radius+5)); ey2=cy+int(math.sin(shovel_a)*(self.radius+5))
        pygame.draw.line(surf,(200,180,100),(sx2,sy2),(ex2,ey2),5)
        if hovered: self._hover_label(surf)

class FastBoss(Enemy):
    DISPLAY_NAME="Fast Boss"; BASE_HP=500; BASE_SPEED=200
    def __init__(self):
        super().__init__(1)
        self.hp=500; self.maxhp=500; self.speed=self.BASE_SPEED; self.radius=19
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*300
        return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*2)*2; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((84,84),pygame.SRCALPHA)
        pygame.draw.circle(s,(255,100,0,40),(42,42),41); surf.blit(s,(cx-42,cy-42))
        for i in range(6):
            a=math.radians(self._rot+i*60)
            rx=cx+int(math.cos(a)*(self.radius+6)); ry=cy+int(math.sin(a)*(self.radius+6))
            pygame.draw.circle(surf,(255,200,50),(rx,ry),3)
        pygame.draw.circle(surf,(200,80,0),(cx,cy),self.radius+3,3)
        pygame.draw.circle(surf,(255,120,20),(cx,cy),self.radius)
        pygame.draw.circle(surf,(255,240,100),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(255,200,100),(cx,cy),self.radius,2)
        if hovered: self._hover_label(surf)

# ── Otchimus Prime ─────────────────────────────────────────────────────────────
class OtchimusPrime(Enemy):
    DISPLAY_NAME="optimus prime 3000 super scary"; BASE_HP=40000; BASE_SPEED=15
    def __init__(self):
        super().__init__(1)
        self.hp=25000; self.maxhp=25000; self.speed=self.BASE_SPEED; self.radius=43
        self._rot=0.0; self._summon_timer=20.0
        self.phase2_armor=False
    def take_damage(self, dmg, bypass_armor=False):
        if self.phase2_armor and not bypass_armor: return
        self.hp-=dmg
        if self.hp<=0: self.alive=False
    def update(self, dt):
        self._rot+=dt*60; self._summon_timer-=dt
        return super().update(dt)
    def should_summon(self):
        if self._summon_timer<=0: self._summon_timer=20.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((156,156),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/60*math.pi*0.5))*30)
        pygame.draw.circle(s,(255,60,60,24+pulse),(78,78),74); surf.blit(s,(cx-78,cy-78))
        for i in range(12):
            a=math.radians(self._rot+i*30)
            rx=cx+int(math.cos(a)*(self.radius+14)); ry=cy+int(math.sin(a)*(self.radius+14))
            pygame.draw.line(surf,(200,50,50),(cx,cy),(rx,ry),3)
        pygame.draw.circle(surf,(140,20,20),(cx,cy),self.radius+6,7)
        pygame.draw.circle(surf,(80,10,10),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,60,60),(cx-10,cy-10),17)
        pygame.draw.circle(surf,(255,100,100),(cx,cy),self.radius,3)
        for dx in [-10,10]:
            pygame.draw.circle(surf,(255,220,0),(cx+dx,cy-7),6)
            pygame.draw.circle(surf,(255,80,0),(cx+dx,cy-7),3)
        self._draw_hp_bar(surf,80,8,(255,80,80))
        if hovered: self._hover_label(surf)

# ── Bouncing HP circle (Отчимус Прайм phase 2) ────────────────────────────────
class BounceCircle:
    def __init__(self):
        self.x=float(random.randint(150,SCREEN_W-150))
        self.y=float(random.randint(80,SLOT_AREA_Y-80))
        while abs(self.y-PATH_Y)<PATH_H+40:
            self.y=float(random.randint(80,SLOT_AREA_Y-80))
        self.outer_r=40
        self.inner_r=38.0
        self.shrink_speed=12.0
        self.hovered=False
        self.done=False
        self.hit=False

    def update(self, dt, mx, my):
        if self.done: return
        self.inner_r-=self.shrink_speed*dt
        if self.inner_r<=0:
            self.done=True; return
        if dist((mx,my),(self.x,self.y))<=self.outer_r:
            self.hovered=True
            self.hit=True; self.done=True
        else:
            self.hovered=False

    def draw(self, surf):
        if self.done: return
        s=pygame.Surface((144,144),pygame.SRCALPHA)
        cx,cy=60,60
        pygame.draw.circle(s,(255,200,50,180),(cx,cy),self.outer_r,3)
        r=max(1,int(self.inner_r))
        frac=self.inner_r/38.0
        col=(int(255*(1-frac)),int(200*frac),50,220)
        pygame.draw.circle(s,col,(cx,cy),r,3)
        pygame.draw.circle(s,(255,255,255,80),(cx,cy),r)
        surf.blit(s,(int(self.x)-72,int(self.y)-72))

# ── New enemy types (not yet used in waves) ───────────────────────────────────

class AbnormalEnemy(Enemy):
    DISPLAY_NAME="Abnormal"; BASE_HP=11; BASE_SPEED=55; KILL_REWARD=8
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=11; self.maxhp=11; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=17
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(180,60,60),(cx,cy),self.radius)
        pygame.draw.circle(surf,(230,110,110),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(255,180,180),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,30,5)
        if hovered: self._hover_label(surf)

class QuickEnemy(Enemy):
    DISPLAY_NAME="Quick"; BASE_HP=12; BASE_SPEED=140; KILL_REWARD=8
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=12; self.maxhp=12; self.speed=self.BASE_SPEED+(wave-1)*5; self.radius=12
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.6)*3; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(60,180,140),(cx,cy),self.radius)
        pygame.draw.circle(surf,(140,255,210),(cx-3,cy-3),5)
        pygame.draw.circle(surf,(180,255,230),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,22,4)
        if hovered: self._hover_label(surf)

class SkeletonEnemy(Enemy):
    DISPLAY_NAME="Skeleton"; BASE_HP=55; BASE_SPEED=55; KILL_REWARD=60
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=55; self.maxhp=55; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=17
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(200,200,190),(cx,cy),self.radius)
        pygame.draw.circle(surf,(240,240,230),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(255,255,255),(cx,cy),self.radius,2)
        # bone cross marks
        pygame.draw.line(surf,(150,150,140),(cx-7,cy-7),(cx+7,cy+7),2)
        pygame.draw.line(surf,(150,150,140),(cx+7,cy-7),(cx-7,cy+7),2)
        self._draw_hp_bar(surf,30,5,(220,220,210))
        if hovered: self._hover_label(surf)

class FallenDreg(Enemy):
    DISPLAY_NAME="Fallen Dreg"; BASE_HP=80; BASE_SPEED=83; ARMOR=0.20; KILL_REWARD=120
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=80; self.maxhp=80; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=17
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(120,50,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,100,220),(cx-5,cy-5),6)
        pygame.draw.circle(surf,(200,130,240),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,30,5,(180,100,220))
        if hovered: self._hover_label(surf)

class FallenSquire(Enemy):
    DISPLAY_NAME="Fallen Squire"; BASE_HP=400; BASE_SPEED=42; ARMOR=0.0; KILL_REWARD=656
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=400; self.maxhp=400; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=24
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*1.5; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(100,40,140),(cx,cy),self.radius)
        pygame.draw.circle(surf,(160,90,200),(cx-6,cy-6),8)
        pygame.draw.circle(surf,(200,140,240),(cx,cy),self.radius,3)
        for i in range(4):
            a=math.radians(i*90+45)
            x1=cx+int(math.cos(a)*8); y1=cy+int(math.sin(a)*8)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(220,180,255),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,40,5,(180,100,220))
        if hovered: self._hover_label(surf)

class FallenSoul(Enemy):
    DISPLAY_NAME="Fallen Soul"; BASE_HP=150; BASE_SPEED=55; IS_HIDDEN=True; ARMOR=0.20; KILL_REWARD=180
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=150; self.maxhp=150; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=16
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        alpha=180 if detected else (220 if hovered else 128)
        s=pygame.Surface((60,60),pygame.SRCALPHA)
        pygame.draw.circle(s,(168,72,240,alpha),(30,30),self.radius)
        pygame.draw.circle(s,(240,144,255,alpha),(25,25),6)
        pygame.draw.circle(s,(255,192,255,alpha//2),(30,30),self.radius,2)
        surf.blit(s,(cx-30,cy-30))
        if detected or hovered: self._draw_hp_bar(surf,30,5,(200,120,255))
        if hovered: self._hover_label(surf)

class FallenEnemy(Enemy):
    DISPLAY_NAME="Fallen"; BASE_HP=200; BASE_SPEED=140; KILL_REWARD=360
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=200; self.maxhp=200; self.speed=self.BASE_SPEED+(wave-1)*5; self.radius=14
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.4)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(140,30,180),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,80,240),(cx-3,cy-3),6)
        pygame.draw.circle(surf,(220,110,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,26,4,(200,80,240))
        if hovered: self._hover_label(surf)

class FallenGiant(Enemy):
    DISPLAY_NAME="Fallen Giant"; BASE_HP=3000; BASE_SPEED=28; KILL_REWARD=5000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=3000; self.maxhp=3000; self.speed=self.BASE_SPEED+(wave-1); self.radius=31
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((120,120),pygame.SRCALPHA)
        pygame.draw.circle(s,(100,20,140,35),(60,60),58); surf.blit(s,(cx-60,cy-60))
        pygame.draw.circle(surf,(80,20,120),(cx,cy),self.radius+5,5)
        pygame.draw.circle(surf,(60,10,90),(cx,cy),self.radius)
        pygame.draw.circle(surf,(160,80,210),(cx-8,cy-8),12)
        pygame.draw.circle(surf,(180,100,230),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,55,7,(180,100,230))
        if hovered: self._hover_label(surf)

class FallenHazmat(Enemy):
    DISPLAY_NAME="Fallen Hazmat"; BASE_HP=200; BASE_SPEED=55; ARMOR=0.30; KILL_REWARD=480
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=200; self.maxhp=200; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=19
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(50,120,80),(cx,cy),self.radius)
        pygame.draw.circle(surf,(80,200,120),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(100,220,140),(cx,cy),self.radius,3)
        # hazmat symbol lines
        for i in range(3):
            a=math.radians(i*120+90)
            x1=cx+int(math.cos(a)*4); y1=cy+int(math.sin(a)*4)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(200,255,200),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,34,5,(80,200,120))
        if hovered: self._hover_label(surf)

class PossessedArmorInner(Enemy):
    """The inner ghost that spawns when PossessedArmor dies."""
    DISPLAY_NAME="Poss. Armor (inner)"; BASE_HP=150; BASE_SPEED=55; ARMOR=0.0
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=150; self.maxhp=150; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=17
        self.free_kill=True
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(160,160,200),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,200,240),(cx-5,cy-5),6)
        pygame.draw.circle(surf,(220,220,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,30,5,(200,200,240))
        if hovered: self._hover_label(surf)

class PossessedArmor(Enemy):
    DISPLAY_NAME="Possessed Armor"; BASE_HP=300; BASE_SPEED=55; ARMOR=0.50; KILL_REWARD=1650
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=300; self.maxhp=300; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=24
        self._spawned_inner=False
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(80,80,110),(cx,cy),self.radius)
        pygame.draw.circle(surf,(140,140,180),(cx-6,cy-6),8)
        pygame.draw.circle(surf,(180,180,220),(cx,cy),self.radius,3)
        for i in range(6):
            a=math.radians(i*60+30)
            x1=cx+int(math.cos(a)*8); y1=cy+int(math.sin(a)*8)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(200,200,240),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,40,5,(180,180,220))
        if hovered: self._hover_label(surf)

class FallenNecromancer(Enemy):
    DISPLAY_NAME="Fallen Necromancer"; BASE_HP=3000; BASE_SPEED=28; KILL_REWARD=3000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=3000; self.maxhp=3000; self.speed=self.BASE_SPEED+(wave-1); self.radius=26
        self._summon_timer=5.0
    def update(self, dt):
        self._summon_timer-=dt; return super().update(dt)
    def should_summon(self):
        if self._summon_timer<=0: self._summon_timer=5.0; return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.8)*1.5; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pygame.draw.circle(s,(120,0,80,40),(48,48),46); surf.blit(s,(cx-48,cy-48))
        pygame.draw.circle(surf,(150,0,100),(cx,cy),self.radius+3,3)
        pygame.draw.circle(surf,(100,0,70),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,80,160),(cx-6,cy-6),8)
        pygame.draw.circle(surf,(240,100,180),(cx,cy),self.radius,2)
        for i in range(4):
            a=math.radians(i*90+self._bob*20)
            px2=cx+int(math.cos(a)*(self.radius+6)); py2=cy+int(math.sin(a)*(self.radius+6))
            pygame.draw.circle(surf,(255,200,220),(px2,py2),3)
        self._draw_hp_bar(surf,50,6,(240,100,180))
        if hovered: self._hover_label(surf)

class CorruptedFallen(Enemy):
    DISPLAY_NAME="Corrupted Fallen"; BASE_HP=1000; BASE_SPEED=120; KILL_REWARD=1200
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=1000; self.maxhp=1000; self.speed=self.BASE_SPEED+(wave-1)*4; self.radius=17
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.3)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(160,20,120),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,60,180),(cx-5,cy-5),6)
        pygame.draw.circle(surf,(240,80,200),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,28,4,(220,60,180))
        if hovered: self._hover_label(surf)

class FallenJester(Enemy):
    DISPLAY_NAME="Fallen Jester"; BASE_HP=10000; BASE_SPEED=28; KILL_REWARD=100
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=10000; self.maxhp=10000; self.speed=self.BASE_SPEED; self.radius=34
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*120; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((120,120),pygame.SRCALPHA)
        pygame.draw.circle(s,(200,0,200,30),(60,60),58); surf.blit(s,(cx-60,cy-60))
        for i in range(6):
            a=math.radians(self._rot+i*60)
            rx=cx+int(math.cos(a)*(self.radius+8)); ry=cy+int(math.sin(a)*(self.radius+8))
            col2=(255,80,255) if i%2==0 else (255,200,80)
            pygame.draw.circle(surf,col2,(rx,ry),6)
        pygame.draw.circle(surf,(120,0,120),(cx,cy),self.radius+5,5)
        pygame.draw.circle(surf,(90,0,90),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,80,220),(cx-8,cy-8),12)
        pygame.draw.circle(surf,(255,100,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,60,7,(220,80,220))
        if hovered: self._hover_label(surf)

class NecroticSkeleton(Enemy):
    DISPLAY_NAME="Necrotic Skeleton"; BASE_HP=1400; BASE_SPEED=120; KILL_REWARD=1400
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=1400; self.maxhp=1400; self.speed=self.BASE_SPEED+(wave-1)*4; self.radius=18
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.3)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(170,190,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(210,230,200),(cx-5,cy-5),6)
        pygame.draw.circle(surf,(230,250,220),(cx,cy),self.radius,2)
        pygame.draw.line(surf,(100,120,90),(cx-6,cy-6),(cx+6,cy+6),2)
        pygame.draw.line(surf,(100,120,90),(cx+6,cy-6),(cx-6,cy+6),2)
        self._draw_hp_bar(surf,30,4,(210,230,200))
        if hovered: self._hover_label(surf)

class FallenBreaker(Enemy):
    DISPLAY_NAME="Fallen Breaker"; BASE_HP=30; BASE_SPEED=55; ARMOR=0.30; KILL_REWARD=50
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=30; self.maxhp=30; self.speed=self.BASE_SPEED; self.radius=18
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(120,40,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,80,220),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(200,100,240),(cx,cy),self.radius,2)
        for i in range(3):
            a=math.radians(i*120+30)
            x1=cx+int(math.cos(a)*4); y1=cy+int(math.sin(a)*4)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(80,0,100),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,30,5,(180,80,220))
        if hovered: self._hover_label(surf)

class FallenRusher(Enemy):
    DISPLAY_NAME="Fallen Rusher"; BASE_HP=350; BASE_SPEED=140; ARMOR=0.40; KILL_REWARD=1500
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=350; self.maxhp=350; self.speed=self.BASE_SPEED+(wave-1)*5; self.radius=13
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.6)*3; cx,cy=int(self.x),int(self.y+bob)
        pygame.draw.circle(surf,(160,30,100),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,70,160),(cx-3,cy-3),5)
        pygame.draw.circle(surf,(240,100,180),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,24,4,(220,70,160))
        if hovered: self._hover_label(surf)

class FallenHonorGuard(Enemy):
    DISPLAY_NAME="Fallen Honor Guard"; BASE_HP=75000; BASE_SPEED=22  # slightly slower than Slow (28)
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=75000; self.maxhp=75000; self.speed=self.BASE_SPEED; self.radius=38
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*60; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((144,144),pygame.SRCALPHA)
        pygame.draw.circle(s,(120,0,180,30),(72,72),70); surf.blit(s,(cx-72,cy-72))
        for i in range(8):
            a=math.radians(self._rot+i*45)
            rx=cx+int(math.cos(a)*(self.radius+10)); ry=cy+int(math.sin(a)*(self.radius+10))
            col2=(200,80,255) if i%2==0 else (140,40,200)
            pygame.draw.circle(surf,col2,(rx,ry),6)
        pygame.draw.circle(surf,(80,0,130),(cx,cy),self.radius+6,6)
        pygame.draw.circle(surf,(60,0,100),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,80,230),(cx-10,cy-10),16)
        pygame.draw.circle(surf,(200,100,255),(cx,cy),self.radius,2)
        for i in range(6):
            a=math.radians(i*60+self._rot*0.3)
            x1=cx+int(math.cos(a)*10); y1=cy+int(math.sin(a)*10)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(160,60,220),(x1,y1),(x2,y2),2)
        self._draw_hp_bar(surf,66,8,(180,80,230))
        if hovered: self._hover_label(surf)

class FallenShield(Enemy):
    DISPLAY_NAME="Fallen Shield"; BASE_HP=8000; BASE_SPEED=55; ARMOR=0.40
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=8000; self.maxhp=8000; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=26
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        # Shield shape using polygon
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pygame.draw.circle(s,(100,40,160,30),(48,48),46); surf.blit(s,(cx-48,cy-48))
        pygame.draw.circle(surf,(80,30,130),(cx,cy),self.radius+5,6)
        pygame.draw.circle(surf,(60,20,100),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,120,255),(cx-6,cy-6),10)
        # Shield cross
        pygame.draw.line(surf,(180,100,240),(cx,cy-self.radius+5),(cx,cy+self.radius-5),3)
        pygame.draw.line(surf,(180,100,240),(cx-self.radius+5,cy),(cx+self.radius-5,cy),3)
        pygame.draw.circle(surf,(220,140,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,46,6,(200,120,255))
        if hovered: self._hover_label(surf)

class FallenHero(Enemy):
    DISPLAY_NAME="Fallen Hero"; BASE_HP=2500; BASE_SPEED=55; ARMOR=0.25
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=2500; self.maxhp=2500; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=20
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((72,72),pygame.SRCALPHA)
        pygame.draw.circle(s,(160,50,200,30),(36,36),34); surf.blit(s,(cx-36,cy-36))
        pygame.draw.circle(surf,(110,30,160),(cx,cy),self.radius+2,3)
        pygame.draw.circle(surf,(80,20,120),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,100,240),(cx-5,cy-5),7)
        pygame.draw.circle(surf,(220,130,255),(cx,cy),self.radius,2)
        # sword icon
        pygame.draw.line(surf,(220,200,255),(cx+5,cy-self.radius+2),(cx+5,cy+self.radius-2),2)
        pygame.draw.line(surf,(200,180,230),(cx,cy-5),(cx+10,cy-5),2)
        self._draw_hp_bar(surf,36,5,(200,100,240))
        if hovered: self._hover_label(surf)


class FallenKing(Enemy):
    DISPLAY_NAME="Fallen King"; BASE_HP=175000; BASE_SPEED=9; ARMOR=0.05; SLOW_RESISTANCE=0.5
    IS_HIDDEN=False

    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=175000; self.maxhp=175000
        self.speed=self.BASE_SPEED; self.radius=41
        self._base_speed=self.BASE_SPEED
        self._path_x=self.x; self._path_y=float(get_map_path()[0][1])

        # Charge (speed burst + hidden)
        self._charge_timer=random.uniform(7,15)
        self._charging=False
        self._charge_dur=0.0

        # Sword attack — state machine
        # states: 'idle', 'leaving', 'striking', 'returning'
        self._sword_state='idle'
        self._sword_timer=random.uniform(9,15)
        self._sword_target_unit=None   # the unit we're going to hit
        self._sword_tx=0.0; self._sword_ty=0.0  # target position
        self._sword_hit=False          # already dealt stun this attack
        self._sword_move_speed=220.0   # px/s when leaving/returning

        # Hero summon
        self._summon_timer=random.uniform(7,15)

    def take_damage(self, dmg):
        eff=dmg*(1.0-self.ARMOR)
        self.hp-=eff
        if self.hp<=0: self.alive=False

    def update(self, dt):
        self._bob+=dt*4

        # ── Charge phase ──────────────────────────────────────────────────
        if not self._charging:
            self._charge_timer-=dt
            if self._charge_timer<=0:
                self._charging=True; self._charge_dur=1.0
                self.speed=55; self.IS_HIDDEN=True
                # Clear any cached original speeds so slows don't restore to charge speed
                self._ice_arrow_slowed=False
                self._frost_slowed=False
                if hasattr(self,'_ice_arrow_orig_speed'): self._ice_arrow_orig_speed=self._base_speed
                if hasattr(self,'_frost_orig_speed'): self._frost_orig_speed=self._base_speed
        else:
            self._charge_dur-=dt
            if self._charge_dur<=0:
                self._charging=False; self._charge_timer=random.uniform(7,15)
                self.speed=self._base_speed; self.IS_HIDDEN=False
                # Clear any slow effects that captured charge speed as "original"
                self._ice_arrow_slowed=False
                self._frost_slowed=False
                if hasattr(self,'_ice_arrow_orig_speed'): self._ice_arrow_orig_speed=self._base_speed
                if hasattr(self,'_frost_orig_speed'): self._frost_orig_speed=self._base_speed

        # ── Sword attack state machine ────────────────────────────────────
        if self._sword_state=='idle':
            self._sword_timer-=dt
            if self._sword_timer<=0:
                self._sword_state='armed'   # will pick target in game.update (needs units list)

        elif self._sword_state=='leaving':
            # Move toward target unit's position
            dx=self._sword_tx-self.x; dy=self._sword_ty-self.y
            d=math.hypot(dx,dy)
            step=self._sword_move_speed*dt
            if d<=step+4:
                self.x=self._sword_tx; self.y=self._sword_ty
                self._sword_state='striking'
                self._sword_dur=0.4  # brief pause at target
            else:
                self.x+=dx/d*step; self.y+=dy/d*step

        elif self._sword_state=='striking':
            self._sword_dur-=dt
            if self._sword_dur<=0:
                self._sword_state='returning'

        elif self._sword_state=='returning':
            # Move back to path Y at same X progress
            dx=self._path_x-self.x; dy=self._path_y-self.y
            d=math.hypot(dx,dy)
            step=self._sword_move_speed*dt
            if d<=step+4:
                self.x=self._path_x; self.y=self._path_y
                self._sword_state='idle'
                self._sword_timer=random.uniform(9,15)
                self._sword_target_unit=None
                self._sword_hit=False
            else:
                self.x+=dx/d*step; self.y+=dy/d*step

        # ── Hero summon ───────────────────────────────────────────────────
        self._summon_timer-=dt

        # ── Path movement (only when idle/armed, not during sword lunge) ──
        if self._sword_state in ('idle','armed') and not self.frozen:
            path = get_map_path()
            if self._wp_index < len(path):
                tx, ty = path[self._wp_index]
                dx = tx - self.x; dy = ty - self.y
                d = math.hypot(dx, dy)
                step = self.speed * dt
                if d <= step + 1:
                    self.x = float(tx); self.y = float(ty)
                    self._wp_index += 1
                else:
                    self.x += dx/d*step; self.y += dy/d*step
            self._path_x=self.x; self._path_y=self.y

        if self._wp_index >= len(get_map_path()):
            self.alive=False; return True
        return False

    def should_summon_hero(self):
        if self._summon_timer<=0:
            self._summon_timer=random.uniform(7,15); return True
        return False

    def draw(self, surf, hovered=False, detected=False):
        if self.IS_HIDDEN and not detected and not hovered: return
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        # Big aura
        s=pygame.Surface((168,168),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._bob*0.5))*40)+20
        aura_col=(180,30,255,pulse) if not self._charging else (255,255,255,pulse)
        pygame.draw.circle(s,aura_col,(84,84),79); surf.blit(s,(cx-84,cy-84))
        # Orbiting jewels
        for i in range(6):
            a=math.radians(self._bob*40+i*60)
            rx=cx+int(math.cos(a)*(self.radius+14))
            ry=cy+int(math.sin(a)*(self.radius+14))
            col2=(220,120,255) if i%2==0 else (160,60,220)
            pygame.draw.circle(surf,col2,(rx,ry),7)
        # Body
        pygame.draw.circle(surf,(60,0,100),(cx,cy),self.radius+7,7)
        pygame.draw.circle(surf,(40,0,70),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,100,255),(cx-11,cy-11),17)
        pygame.draw.circle(surf,(220,130,255),(cx,cy),self.radius,3)
        # Crown spikes
        for i in range(5):
            a=math.radians(-90+i*36)
            sx2=cx+int(math.cos(a)*(self.radius+2)); sy2=cy+int(math.sin(a)*(self.radius+2))
            ex2=cx+int(math.cos(a)*(self.radius+18)); ey2=cy+int(math.sin(a)*(self.radius+18))
            pygame.draw.line(surf,(255,200,80),(int(sx2),int(sy2)),(int(ex2),int(ey2)),3)
        # Sword during lunge
        if self._sword_state in ('leaving','striking'):
            pygame.draw.line(surf,(255,240,100),(cx,cy),(cx+41,cy-41),6)
            pygame.draw.line(surf,(255,220,80),(cx+26,cy-53),(cx+53,cy-26),5)
            # Red flash on strike
            if self._sword_state=='striking':
                fs=pygame.Surface((72,72),pygame.SRCALPHA)
                pygame.draw.circle(fs,(255,80,80,120),(36,36),34)
                surf.blit(fs,(cx-36,cy-36))
        self._draw_hp_bar(surf,70,9,(200,100,255))
        if hovered: self._hover_label(surf)

class TrueFallenKing(FallenKing):
    """True Fallen King — enraged form with 4 unique abilities."""
    DISPLAY_NAME="True Fallen King"; BASE_HP=175000; BASE_SPEED=8; ARMOR=0.10; SLOW_RESISTANCE=0.8

    def __init__(self):
        super().__init__(1)
        self.hp=175000; self.maxhp=175000
        self.radius=43; self._base_speed=self.BASE_SPEED

        # Ability 1: Curse Wave — AoE stun all units in 300px
        self._curse_timer=random.uniform(12,20)
        self._curse_active=False
        self._curse_dur=0.0
        self._curse_ring_r=0.0

        # Ability 2: Blood Charge — fast dash, leaves fire trail
        self._bcharge_timer=random.uniform(8,14)
        self._bcharging=False
        self._bcharge_dur=0.0
        self._fire_trail=[]  # list of [x, y, life]

        # Ability 3: Dark Summon — summon FallenShield + FallenHero pairs
        self._dark_summon_timer=random.uniform(10,18)

        # Ability 4: Phase Shift — brief invulnerability at <50% HP
        self._phase_shift_cooldown=25.0
        self._phase_shift_active=False
        self._phase_shift_dur=0.0
        self._phase_shift_triggered=False

    def take_damage(self, dmg):
        if self._phase_shift_active: return
        eff=dmg*(1.0-self.ARMOR)
        self.hp-=eff
        if self.hp<=0: self.alive=False

    def update(self, dt):
        self._bob+=dt*4

        # ── Curse Wave ───────────────────────────────────────────
        if not self._curse_active:
            self._curse_timer-=dt
            if self._curse_timer<=0:
                self._curse_active=True; self._curse_dur=0.6; self._curse_ring_r=0.0
        else:
            self._curse_dur-=dt; self._curse_ring_r+=dt*500
            if self._curse_dur<=0:
                self._curse_active=False; self._curse_timer=random.uniform(12,20)

        # ── Blood Charge ─────────────────────────────────────────
        if not self._bcharging:
            self._bcharge_timer-=dt
            if self._bcharge_timer<=0:
                self._bcharging=True; self._bcharge_dur=1.2
                self.speed=90; self.IS_HIDDEN=True
                self._ice_arrow_slowed=False; self._frost_slowed=False
                if hasattr(self,"_ice_arrow_orig_speed"): self._ice_arrow_orig_speed=self._base_speed
                if hasattr(self,"_frost_orig_speed"): self._frost_orig_speed=self._base_speed
        else:
            self._bcharge_dur-=dt
            self._fire_trail.append([self.x, self.y, 1.4])
            if self._bcharge_dur<=0:
                self._bcharging=False; self._bcharge_timer=random.uniform(8,14)
                self.speed=self._base_speed; self.IS_HIDDEN=False
                self._ice_arrow_slowed=False; self._frost_slowed=False
                if hasattr(self,"_ice_arrow_orig_speed"): self._ice_arrow_orig_speed=self._base_speed
                if hasattr(self,"_frost_orig_speed"): self._frost_orig_speed=self._base_speed
        self._fire_trail=[p for p in self._fire_trail if p[2]>0]
        for p in self._fire_trail: p[2]-=dt

        # ── Dark Summon timer ─────────────────────────────────────
        self._dark_summon_timer-=dt

        # ── Phase Shift ───────────────────────────────────────────
        if self._phase_shift_active:
            self._phase_shift_dur-=dt
            if self._phase_shift_dur<=0:
                self._phase_shift_active=False; self._phase_shift_triggered=False
        else:
            self._phase_shift_cooldown-=dt
            if self._phase_shift_cooldown<=0:
                self._phase_shift_triggered=False; self._phase_shift_cooldown=25.0
            if not self._phase_shift_triggered and self.hp/self.maxhp<0.5:
                self._phase_shift_active=True; self._phase_shift_dur=2.0
                self._phase_shift_triggered=True

        # ── Path movement ─────────────────────────────────────────
        if not self.frozen:
            path=get_map_path()
            if self._wp_index<len(path):
                tx,ty=path[self._wp_index]
                dx=tx-self.x; dy=ty-self.y
                d=math.hypot(dx,dy); step=self.speed*dt
                if d<=step+1:
                    self.x=float(tx); self.y=float(ty); self._wp_index+=1
                else:
                    self.x+=dx/d*step; self.y+=dy/d*step
            self._path_x=self.x; self._path_y=self.y
        if self._wp_index>=len(get_map_path()):
            self.alive=False; return True
        return False

    def should_dark_summon(self):
        if self._dark_summon_timer<=0:
            self._dark_summon_timer=random.uniform(10,18); return True
        return False

    def draw(self, surf, hovered=False, detected=False):
        if self.IS_HIDDEN and not detected and not hovered: return
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)

        # Fire trail
        for p in self._fire_trail:
            frac=max(0.0, min(1.0, p[2]/1.4))
            alpha=int(frac*180)
            r2=int(frac*18)+4
            fs2=pygame.Surface((72,72),pygame.SRCALPHA)
            pygame.draw.circle(fs2,(255,min(255,int(96*frac)),0,alpha),(36,36),r2)
            pygame.draw.circle(fs2,(255,200,50,min(255,alpha//2+1)),(36,36),r2+5,2)
            surf.blit(fs2,(int(p[0])-36,int(p[1])-36))

        # Phase Shift glow
        if self._phase_shift_active:
            ps=pygame.Surface((240,240),pygame.SRCALPHA)
            palpha=int(abs(math.sin(self._bob*8))*120)+80
            pygame.draw.circle(ps,(255,255,255,palpha),(120,120),96)
            surf.blit(ps,(cx-120,cy-120))

        # Main aura
        s=pygame.Surface((180,180),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._bob*0.5))*50)+30
        aura_col=(255,255,255,pulse) if self._phase_shift_active else (255,20,20,pulse)
        pygame.draw.circle(s,aura_col,(90,90),84); surf.blit(s,(cx-90,cy-90))

        # Curse Wave ring
        if self._curse_active and self._curse_ring_r < 320:
            cr=int(self._curse_ring_r)
            ring_alpha=max(0,int((1.0-self._curse_ring_r/255)*200))
            rs=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            pygame.draw.circle(rs,(192,0,255,ring_alpha),(cx,cy),cr,5)
            pygame.draw.circle(rs,(255,60,255,ring_alpha//2),(cx,cy),cr+10,2)
            surf.blit(rs,(0,0))

        for i in range(6):
            a=math.radians(self._bob*40+i*60)
            rx=cx+int(math.cos(a)*(self.radius+14)); ry=cy+int(math.sin(a)*(self.radius+14))
            col2=(255,255,255) if self._phase_shift_active else ((255,60,60) if i%2==0 else (180,10,10))
            pygame.draw.circle(surf,col2,(rx,ry),8)
        pygame.draw.circle(surf,(120,0,0),(cx,cy),self.radius+7,7)
        body_col=(200,200,220) if self._phase_shift_active else (80,0,0)
        pygame.draw.circle(surf,body_col,(cx,cy),self.radius)
        pygame.draw.circle(surf,(255,80,80),(cx-11,cy-11),17)
        border_col=(255,255,255) if self._phase_shift_active else (255,40,40)
        pygame.draw.circle(surf,border_col,(cx,cy),self.radius,3)
        for i in range(5):
            a=math.radians(-90+i*36)
            sx2=cx+int(math.cos(a)*(self.radius+2)); sy2=cy+int(math.sin(a)*(self.radius+2))
            ex2=cx+int(math.cos(a)*(self.radius+20)); ey2=cy+int(math.sin(a)*(self.radius+20))
            spike_col=(255,255,100) if self._phase_shift_active else (255,80,30)
            pygame.draw.line(surf,spike_col,(int(sx2),int(sy2)),(int(ex2),int(ey2)),3)
        if self._sword_state in ('leaving','striking'):
            pygame.draw.line(surf,(255,100,50),(cx,cy),(cx+41,cy-41),6)
            pygame.draw.line(surf,(255,60,20),(cx+26,cy-53),(cx+53,cy-26),5)
            if self._sword_state=='striking':
                fs=pygame.Surface((72,72),pygame.SRCALPHA)
                pygame.draw.circle(fs,(255,30,30,140),(36,36),34)
                surf.blit(fs,(cx-36,cy-36))

        # Phase Shift label
        if self._phase_shift_active:
            pf=pygame.font.SysFont("consolas",13,bold=True)
            ps2=pf.render("IMMUNE",True,(255,255,200))
            surf.blit(ps2,ps2.get_rect(center=(cx,cy-self.radius-31)))

        self._draw_hp_bar(surf,80,10,(255,40,40))
        if hovered: self._hover_label(surf)

# ══════════════════════════════════════════════════════════════════════════════
# FROSTY MODE ENEMIES
# Цветовая палитра: ледяные голубые / белые / серебристые тона
# ══════════════════════════════════════════════════════════════════════════════

class FrozenEnemy(Enemy):
    DISPLAY_NAME="Frozen"; BASE_HP=10; BASE_SPEED=68; KILL_REWARD=12
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=10; self.maxhp=10; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=15
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.4)*2; cx,cy=int(self.x),int(self.y+bob)
        # Hexagonal crystal shape
        pts=[(cx+int(math.cos(math.radians(60*i-30))*self.radius),
              cy+int(math.sin(math.radians(60*i-30))*self.radius)) for i in range(6)]
        pygame.draw.polygon(surf,(100,190,240),pts)
        pygame.draw.polygon(surf,(200,240,255),pts,2)
        # Inner highlight shard
        inner=[(cx+int(math.cos(math.radians(60*i-30))*7),
                cy+int(math.sin(math.radians(60*i-30))*7)) for i in range(6)]
        pygame.draw.polygon(surf,(220,248,255),inner)
        # Snowflake cross
        for a in [0,90]:
            ang=math.radians(a)
            pygame.draw.line(surf,(160,220,255),
                (cx+int(math.cos(ang)*3),cy+int(math.sin(ang)*3)),
                (cx+int(math.cos(ang)*self.radius-1),cy+int(math.sin(ang)*self.radius-1)),1)
            pygame.draw.line(surf,(160,220,255),
                (cx-int(math.cos(ang)*3),cy-int(math.sin(ang)*3)),
                (cx-int(math.cos(ang)*self.radius-1),cy-int(math.sin(ang)*self.radius-1)),1)
        self._draw_hp_bar(surf,26,4,(180,230,255))
        if hovered: self._hover_label(surf)

class SnowyEnemy(Enemy):
    DISPLAY_NAME="Snowy"; BASE_HP=16; BASE_SPEED=28; KILL_REWARD=20
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=16; self.maxhp=16; self.speed=self.BASE_SPEED+(wave-1); self.radius=20
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.8); cx,cy=int(self.x),int(self.y+bob)
        # Snowy blob: layered circles to look fluffy
        for dx2,dy2,r2 in [(-6,-5,8),(6,-5,8),(0,-8,7),(-5,5,7),(5,5,7),(0,3,9)]:
            pygame.draw.circle(surf,(210,230,248),(cx+dx2,cy+dy2),r2)
        pygame.draw.circle(surf,(240,248,255),(cx,cy),self.radius)
        pygame.draw.circle(surf,(210,230,255),(cx,cy),self.radius,2)
        # Coal eyes
        pygame.draw.circle(surf,(40,50,60),(cx-5,cy-4),3)
        pygame.draw.circle(surf,(40,50,60),(cx+5,cy-4),3)
        # Carrot nose dot
        pygame.draw.circle(surf,(255,140,40),(cx,cy),2)
        self._draw_hp_bar(surf,30,4,(210,235,255))
        if hovered: self._hover_label(surf)

class PackedIceEnemy(Enemy):
    DISPLAY_NAME="Packed Ice"; BASE_HP=75; BASE_SPEED=55; KILL_REWARD=100
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=75; self.maxhp=75; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=20
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((56,56),pygame.SRCALPHA)
        pygame.draw.rect(s,(60,160,220,200),(4,4,48,48),border_radius=6)
        pygame.draw.rect(s,(120,200,255,120),(8,8,20,20),border_radius=3)
        pygame.draw.rect(s,(180,230,255,80),(26,26,18,18),border_radius=2)
        pygame.draw.rect(s,(80,190,240,255),(4,4,48,48),3,border_radius=6)
        surf.blit(s,(cx-28,cy-28))
        pygame.draw.circle(surf,(160,220,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,34,5,(80,190,255))
        if hovered: self._hover_label(surf)

class SnowMinion(Enemy):
    DISPLAY_NAME="Snow Minion"; BASE_HP=200; BASE_SPEED=38; KILL_REWARD=800
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=200; self.maxhp=200; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=30
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*80; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.7); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((108,108),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/80*math.pi))*30)
        pygame.draw.circle(s,(140,200,255,30+pulse),(54,54),52); surf.blit(s,(cx-54,cy-54))
        for i in range(5):
            a=math.radians(self._rot+i*72)
            rx=cx+int(math.cos(a)*(self.radius+10)); ry=cy+int(math.sin(a)*(self.radius+10))
            pygame.draw.circle(surf,(200,240,255),(rx,ry),4)
        pygame.draw.circle(surf,(60,140,210),(cx,cy),self.radius+4,5)
        pygame.draw.circle(surf,(40,100,180),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,230,255),(cx-8,cy-8),12)
        pygame.draw.circle(surf,(200,240,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,54,6,(140,210,255))
        if hovered: self._hover_label(surf)

class FrostMystery(Enemy):
    DISPLAY_NAME="Frost Mystery"; BASE_HP=50; BASE_SPEED=55; KILL_REWARD=300
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=50; self.maxhp=50; self.speed=self.BASE_SPEED+(wave-1)*3; self.radius=14
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*200; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.8)*3; cx,cy=int(self.x),int(self.y+bob)
        for i in range(4):
            a=math.radians(self._rot+i*90)
            rx=cx+int(math.cos(a)*(self.radius-2)); ry=cy+int(math.sin(a)*(self.radius-2))
            pygame.draw.circle(surf,(100,200,255),(rx,ry),4)
        pygame.draw.circle(surf,(30,130,200),(cx,cy),self.radius)
        pygame.draw.circle(surf,(120,210,255),(cx-3,cy-3),5)
        pygame.draw.circle(surf,(160,230,255),(cx,cy),self.radius,2)
        qf=pygame.font.SysFont("consolas",12,bold=True)
        qs=qf.render("?",True,(220,248,255))
        surf.blit(qs,qs.get_rect(center=(cx,cy)))
        self._draw_hp_bar(surf,26,4,(100,200,255))
        if hovered: self._hover_label(surf)

class Frostmite(Enemy):
    DISPLAY_NAME="Frostmite"; BASE_HP=32; BASE_SPEED=140; KILL_REWARD=100
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=32; self.maxhp=32; self.speed=self.BASE_SPEED+(wave-1)*4; self.radius=12
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*360; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*2)*3; cx,cy=int(self.x),int(self.y+bob)
        # 6-arm snowflake spines
        for i in range(6):
            a=math.radians(self._rot+i*60)
            x1=cx+int(math.cos(a)*3); y1=cy+int(math.sin(a)*3)
            x2=cx+int(math.cos(a)*self.radius); y2=cy+int(math.sin(a)*self.radius)
            pygame.draw.line(surf,(160,230,255),(x1,y1),(x2,y2),2)
            # side branches
            for br in [-0.4,0.4]:
                bx=cx+int(math.cos(a+br)*(self.radius-4)); by=cy+int(math.sin(a+br)*(self.radius-4))
                mx=cx+int(math.cos(a)*(self.radius//2)); my=cy+int(math.sin(a)*(self.radius//2))
                pygame.draw.line(surf,(120,200,240),(mx,my),(bx,by),1)
        # Core diamond
        d=5
        pygame.draw.polygon(surf,(80,180,240),[(cx,cy-d),(cx+d,cy),(cx,cy+d),(cx-d,cy)])
        pygame.draw.polygon(surf,(180,240,255),[(cx,cy-d),(cx+d,cy),(cx,cy+d),(cx-d,cy)],1)
        self._draw_hp_bar(surf,22,4,(130,220,255))
        if hovered: self._hover_label(surf)

class ColdMist(Enemy):
    DISPLAY_NAME="Cold Mist"; BASE_HP=80; BASE_SPEED=68; KILL_REWARD=300
    IS_HIDDEN=True
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=80; self.maxhp=80; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=19
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        alpha=180 if detected else (220 if hovered else 60)
        s=pygame.Surface((72,72),pygame.SRCALPHA)
        for dx2,dy2,r2,a2 in [(-8,-4,14,alpha),(8,-4,13,alpha),(0,-9,12,alpha),(-6,6,13,alpha),(6,6,14,alpha),(0,4,15,alpha)]:
            pygame.draw.circle(s,(200,230,255,a2),(36+dx2,36+dy2),r2)
        pygame.draw.circle(s,(220,245,255,max(20,alpha//2)),(36,36),self.radius,2)
        surf.blit(s,(cx-36,cy-36))
        if detected or hovered: self._draw_hp_bar(surf,32,5,(180,230,255))
        if hovered: self._hover_label(surf)

class Permafrost(Enemy):
    DISPLAY_NAME="Permafrost"; BASE_HP=650; BASE_SPEED=42; KILL_REWARD=800
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=650; self.maxhp=650; self.speed=self.BASE_SPEED+(wave-1); self.radius=26
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*40; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((84,84),pygame.SRCALPHA)
        pygame.draw.circle(s,(80,160,220,40),(42,42),40); surf.blit(s,(cx-42,cy-42))
        for i in range(6):
            a=math.radians(self._rot+i*60)
            x1=cx+int(math.cos(a)*14); y1=cy+int(math.sin(a)*14)
            x2=cx+int(math.cos(a)*(self.radius+6)); y2=cy+int(math.sin(a)*(self.radius+6))
            pygame.draw.line(surf,(160,220,255),(x1,y1),(x2,y2),3)
        pygame.draw.circle(surf,(50,120,190),(cx,cy),self.radius+4,5)
        pygame.draw.circle(surf,(30,80,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(140,200,255),(cx-7,cy-7),11)
        pygame.draw.circle(surf,(180,230,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,46,6,(100,190,255))
        if hovered: self._hover_label(surf)

class FrostHunter(Enemy):
    DISPLAY_NAME="Frost Hunter"; BASE_HP=1800; BASE_SPEED=28; KILL_REWARD=2800
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=1800; self.maxhp=1800; self.speed=self.BASE_SPEED+(wave-1); self.radius=32
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*60; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((120,120),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/60*math.pi))*25)
        pygame.draw.circle(s,(100,180,255,28+pulse),(60,60),58); surf.blit(s,(cx-60,cy-60))
        for i in range(8):
            a=math.radians(self._rot+i*45)
            rx=cx+int(math.cos(a)*(self.radius+8)); ry=cy+int(math.sin(a)*(self.radius+8))
            col2=(160,230,255) if i%2==0 else (80,160,220)
            pygame.draw.circle(surf,col2,(rx,ry),5)
        pygame.draw.circle(surf,(40,110,190),(cx,cy),self.radius+5,5)
        pygame.draw.circle(surf,(20,70,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(160,220,255),(cx-9,cy-9),14)
        pygame.draw.circle(surf,(200,240,255),(cx,cy),self.radius,2)
        pygame.draw.line(surf,(120,200,255),(cx,cy-self.radius+4),(cx,cy+self.radius-4),2)
        pygame.draw.line(surf,(120,200,255),(cx-self.radius+4,cy),(cx+self.radius-4,cy),2)
        self._draw_hp_bar(surf,58,7,(120,200,255))
        if hovered: self._hover_label(surf)

class UnstableIce(Enemy):
    DISPLAY_NAME="Unstable Ice"; BASE_HP=400; BASE_SPEED=140; KILL_REWARD=1000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=400; self.maxhp=400; self.speed=self.BASE_SPEED; self.radius=16
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*300; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*2)*3; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((60,60),pygame.SRCALPHA)
        pygame.draw.circle(s,(100,200,255,50),(30,30),28); surf.blit(s,(cx-30,cy-30))
        for i in range(5):
            a=math.radians(self._rot+i*72)
            x1=cx+int(math.cos(a)*4); y1=cy+int(math.sin(a)*4)
            x2=cx+int(math.cos(a)*(self.radius+4)); y2=cy+int(math.sin(a)*(self.radius+4))
            pygame.draw.line(surf,(180,240,255),(x1,y1),(x2,y2),2)
        pygame.draw.circle(surf,(60,170,230),(cx,cy),self.radius+2,3)
        pygame.draw.circle(surf,(100,200,255),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,248,255),(cx-4,cy-4),6)
        pygame.draw.circle(surf,(200,240,255),(cx,cy),self.radius,2)
        pygame.draw.line(surf,(30,100,180),(cx-6,cy-4),(cx+4,cy+6),2)
        pygame.draw.line(surf,(30,100,180),(cx+3,cy-7),(cx-2,cy+3),2)
        self._draw_hp_bar(surf,30,5,(100,200,255))
        if hovered: self._hover_label(surf)

class FrostWraith(Enemy):
    DISPLAY_NAME="Frost Wraith"; BASE_HP=600; BASE_SPEED=68; KILL_REWARD=1750
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=600; self.maxhp=600; self.speed=self.BASE_SPEED+(wave-1)*2; self.radius=22
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*120; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.9)*2; cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/120*math.pi))*40)+60
        pygame.draw.circle(s,(140,220,255,pulse),(48,48),44); surf.blit(s,(cx-48,cy-48))
        for i in range(5):
            a=math.radians(self._rot+i*72)
            rx=cx+int(math.cos(a)*(self.radius+7)); ry=cy+int(math.sin(a)*(self.radius+7))
            pygame.draw.circle(surf,(180,230,255),(rx,ry),4)
        pygame.draw.circle(surf,(60,130,200),(cx,cy),self.radius+3,4)
        pygame.draw.circle(surf,(30,90,170),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,240,255),(cx-6,cy-6),9)
        pygame.draw.circle(surf,(220,248,255),(cx,cy),self.radius,2)
        for i in range(3):
            a=math.radians(self._rot*0.3+180+i*25)
            tx2=cx+int(math.cos(a)*(self.radius+4+i*3)); ty2=cy+int(math.sin(a)*(self.radius+4+i*3))
            pygame.draw.circle(surf,(160,230,255),(tx2,ty2),max(1,3-i))
        self._draw_hp_bar(surf,40,5,(160,220,255))
        if hovered: self._hover_label(surf)

class FrostAcolyte(Enemy):
    DISPLAY_NAME="Frost Acolyte"; BASE_HP=3050; BASE_SPEED=28; KILL_REWARD=5000
    SLOW_RESISTANCE=1.0
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=3050; self.maxhp=3050; self.speed=self.BASE_SPEED+(wave-1); self.radius=28
        self._rot=0.0; self._stun_immune=True
    def update(self, dt):
        # Fully immune to freeze/slow — reset all slow/freeze state every frame
        self._frost_slowed=False; self._ice_arrow_slowed=False
        self.frozen=False; self._frost_frozen=False
        self._frost_freeze_timer=0.0
        self._rot+=dt*90; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.7); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((120,120),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/90*math.pi))*35)+50
        pygame.draw.circle(s,(100,200,255,pulse),(60,60),56); surf.blit(s,(cx-60,cy-60))
        for i in range(8):
            a=math.radians(self._rot+i*45)
            x1=cx+int(math.cos(a)*12); y1=cy+int(math.sin(a)*12)
            x2=cx+int(math.cos(a)*(self.radius+8)); y2=cy+int(math.sin(a)*(self.radius+8))
            pygame.draw.line(surf,(160,230,255),(x1,y1),(x2,y2),3)
        pygame.draw.circle(surf,(40,120,200),(cx,cy),self.radius+5,6)
        pygame.draw.circle(surf,(20,70,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,230,255),(cx-8,cy-8),13)
        pygame.draw.circle(surf,(210,245,255),(cx,cy),self.radius,3)
        for i in range(4):
            a=math.radians(i*90+self._rot*0.4)
            rx=cx+int(math.cos(a)*(self.radius+12)); ry=cy+int(math.sin(a)*(self.radius+12))
            pygame.draw.circle(surf,(220,248,255),(rx,ry),5)
            pygame.draw.circle(surf,(100,200,255),(rx,ry),5,1)
        self._draw_hp_bar(surf,52,7,(120,210,255))
        if hovered: self._hover_label(surf)


# ── New Frosty enemies ─────────────────────────────────────────────────────────
class FrostUndead(Enemy):
    DISPLAY_NAME="Frost Undead"; BASE_HP=800; BASE_SPEED=140; KILL_REWARD=3000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=800; self.maxhp=800
        self.speed=self.BASE_SPEED
        self.radius=20
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*150; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.2)*2; cx,cy=int(self.x),int(self.y+bob)
        # Bone-white icy body
        pygame.draw.circle(surf,(170,200,210),(cx,cy),self.radius+2,3)
        pygame.draw.circle(surf,(140,180,200),(cx,cy),self.radius)
        pygame.draw.circle(surf,(230,245,255),(cx-5,cy-5),7)
        # 3 spinning icy shard orbits
        for i in range(3):
            a=math.radians(self._rot+i*120)
            rx=cx+int(math.cos(a)*(self.radius+5)); ry=cy+int(math.sin(a)*(self.radius+5))
            pygame.draw.polygon(surf,(180,230,255),[(rx,ry-4),(rx+3,ry+3),(rx-3,ry+3)])
        # Skull X eyes
        pygame.draw.line(surf,(60,100,130),(cx-6,cy-4),(cx-2,cy),(1))
        pygame.draw.line(surf,(60,100,130),(cx-2,cy-4),(cx-6,cy),(1))
        pygame.draw.line(surf,(60,100,130),(cx+2,cy-4),(cx+6,cy),(1))
        pygame.draw.line(surf,(60,100,130),(cx+6,cy-4),(cx+2,cy),(1))
        pygame.draw.circle(surf,(220,248,255),(cx,cy),self.radius,2)
        self._draw_hp_bar(surf,40,5,(120,210,255))
        if hovered: self._hover_label(surf)

class FrostInvader(Enemy):
    DISPLAY_NAME="Frost Invader"; BASE_HP=4000; BASE_SPEED=55; KILL_REWARD=4000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=4000; self.maxhp=4000
        self.speed=self.BASE_SPEED+(wave-1)*2
        self.radius=24
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*70; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.8); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((96,96),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/70*math.pi))*30)+30
        pygame.draw.circle(s,(120,210,255,pulse),(48,48),44); surf.blit(s,(cx-48,cy-48))
        pygame.draw.circle(surf,(40,120,200),(cx,cy),self.radius+4,5)
        pygame.draw.circle(surf,(20,70,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,230,255),(cx-7,cy-7),11)
        pygame.draw.circle(surf,(210,245,255),(cx,cy),self.radius,3)
        self._draw_hp_bar(surf,48,6,(120,210,255))
        if hovered: self._hover_label(surf)

class MegaFrostMystery(Enemy):
    DISPLAY_NAME="Mega Frost Mystery"; BASE_HP=600; BASE_SPEED=55; KILL_REWARD=1500
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=600; self.maxhp=600
        self.speed=self.BASE_SPEED+(wave-1)*3
        self.radius=16
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*260; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*1.8)*3; cx,cy=int(self.x),int(self.y+bob)
        for i in range(6):
            a=math.radians(self._rot+i*60)
            rx=cx+int(math.cos(a)*(self.radius+2)); ry=cy+int(math.sin(a)*(self.radius+2))
            pygame.draw.circle(surf,(120,220,255),(rx,ry),4)
        pygame.draw.circle(surf,(30,130,200),(cx,cy),self.radius+2)
        pygame.draw.circle(surf,(180,240,255),(cx-3,cy-3),6)
        pygame.draw.circle(surf,(200,240,255),(cx,cy),self.radius+2,2)
        qf=pygame.font.SysFont("consolas",12,bold=True)
        qs=qf.render("??",True,(235,252,255))
        surf.blit(qs,qs.get_rect(center=(cx,cy)))
        self._draw_hp_bar(surf,36,5,(100,200,255))
        if hovered: self._hover_label(surf)

class FrostRavager(Enemy):
    DISPLAY_NAME="Frost Ravager"; BASE_HP=25000; BASE_SPEED=28; KILL_REWARD=20000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=25000; self.maxhp=25000
        self.speed=self.BASE_SPEED+(wave-1)
        self.radius=38
        # Blue dash (like TFK blood charge, but icy)
        self._dash_timer=random.uniform(8,14)
        self._dashing=False
        self._dash_dur=0.0
        self._base_speed=self.speed
        self._ice_trail=[]  # [x,y,life]
        self._rot=0.0
        self._stun_immune=True
    def update(self, dt):
        self._rot+=dt*40
        if not self._dashing:
            self._dash_timer-=dt
            if self._dash_timer<=0:
                self._dashing=True; self._dash_dur=1.2
                self.speed=max(self._base_speed, 90)
                self._ice_arrow_slowed=False; self._frost_slowed=False
        else:
            self._dash_dur-=dt
            self._ice_trail.append([self.x, self.y, 1.4])
            if self._dash_dur<=0:
                self._dashing=False; self._dash_timer=random.uniform(8,14)
                self.speed=self._base_speed
                self._ice_arrow_slowed=False; self._frost_slowed=False
        self._ice_trail=[p for p in self._ice_trail if p[2]>0]
        for p in self._ice_trail: p[2]-=dt
        return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        for p in self._ice_trail:
            frac=max(0.0, min(1.0, p[2]/1.4))
            alpha=int(frac*160)
            r2=int(frac*18)+6
            fs2=pygame.Surface((80,80),pygame.SRCALPHA)
            pygame.draw.circle(fs2,(80,200,255,alpha),(40,40),r2)
            pygame.draw.circle(fs2,(200,245,255,min(255,alpha//2+1)),(40,40),r2+6,2)
            surf.blit(fs2,(int(p[0])-40,int(p[1])-40))
        s=pygame.Surface((180,180),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot))*50)+20
        pygame.draw.circle(s,(60,150,220,pulse),(90,90),86); surf.blit(s,(cx-90,cy-90))
        # Armored plates (outer ring segments)
        for i in range(6):
            a=math.radians(self._rot*0.3+i*60)
            ax=cx+int(math.cos(a)*(self.radius+4)); ay=cy+int(math.sin(a)*(self.radius+4))
            bx=cx+int(math.cos(a+0.4)*(self.radius+10)); by=cy+int(math.sin(a+0.4)*(self.radius+10))
            pygame.draw.line(surf,(80,160,220),(ax,ay),(bx,by),4)
        pygame.draw.circle(surf,(30,90,170),(cx,cy),self.radius+6,7)
        pygame.draw.circle(surf,(10,50,130),(cx,cy),self.radius)
        pygame.draw.circle(surf,(180,220,255),(cx-12,cy-12),18)
        # Visor slit
        pygame.draw.line(surf,(120,220,255),(cx-12,cy-5),(cx+12,cy-5),3)
        pygame.draw.circle(surf,(200,240,255),(cx,cy),self.radius,3)
        self._draw_hp_bar(surf,80,10,(120,210,255))
        if hovered: self._hover_label(surf)

class TricksterElf(Enemy):
    DISPLAY_NAME="Trickster Elf"; BASE_HP=2500; BASE_SPEED=28; KILL_REWARD=2500; ARMOR=0.25
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=2500; self.maxhp=2500
        self.speed=self.BASE_SPEED+(wave-1)
        self.radius=22
        self._rot=0.0
    def update(self, dt):
        self._rot+=dt*120; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob)*2; cx,cy=int(self.x),int(self.y+bob)
        # Outer ring
        pygame.draw.circle(surf,(30,100,75),(cx,cy),self.radius+3,3)
        # Body: deep green
        pygame.draw.circle(surf,(20,80,55),(cx,cy),self.radius)
        # Face highlight
        pygame.draw.circle(surf,(100,200,160),(cx-7,cy-7),10)
        pygame.draw.circle(surf,(140,220,190),(cx,cy),self.radius,2)
        # Elf ears (side triangles)
        pygame.draw.polygon(surf,(30,110,70),
            [(cx-self.radius-1,cy-3),(cx-self.radius+5,cy-10),(cx-self.radius+5,cy+4)])
        pygame.draw.polygon(surf,(30,110,70),
            [(cx+self.radius+1,cy-3),(cx+self.radius-5,cy-10),(cx+self.radius-5,cy+4)])
        # Tall pointy hat (wobbles with _rot)
        a=math.radians(self._rot*0.4)
        hx=cx+int(math.cos(a)*8); hy=cy-self.radius-2+int(math.sin(a)*2)
        pygame.draw.polygon(surf,(190,70,210),[(hx,hy-14),(hx-11,hy+4),(hx+11,hy+4)])
        pygame.draw.polygon(surf,(230,160,255),[(hx,hy-14),(hx-11,hy+4),(hx+11,hy+4)],2)
        # Hat brim
        pygame.draw.ellipse(surf,(160,50,180),(hx-13,hy,26,7))
        self._draw_hp_bar(surf,46,6,(180,240,220))
        if hovered: self._hover_label(surf)

class Yeti(Enemy):
    DISPLAY_NAME="Yeti"; BASE_HP=10000; BASE_SPEED=28; KILL_REWARD=10000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=10000; self.maxhp=10000
        self.speed=self.BASE_SPEED+(wave-1)*5
        self.radius=34
        self._rot=0.0
        self._stun_immune=True
    def update(self, dt):
        self._rot+=dt*60; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        # Fur aura
        s=pygame.Surface((140,140),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/60*math.pi))*45)+25
        pygame.draw.circle(s,(240,250,255,pulse),(70,70),66); surf.blit(s,(cx-70,cy-70))
        # Shaggy fur bumps around edge
        for i in range(10):
            a=math.radians(self._rot*0.2+i*36)
            fx=cx+int(math.cos(a)*(self.radius+5)); fy=cy+int(math.sin(a)*(self.radius+5))
            pygame.draw.circle(surf,(200,230,240),(fx,fy),6)
        # Main body
        pygame.draw.circle(surf,(170,210,230),(cx,cy),self.radius+6,7)
        pygame.draw.circle(surf,(210,235,245),(cx,cy),self.radius)
        # Face
        pygame.draw.circle(surf,(255,255,255),(cx-10,cy-10),16)
        pygame.draw.circle(surf,(230,245,255),(cx,cy),self.radius,3)
        # Beady red eyes
        pygame.draw.circle(surf,(220,40,40),(cx-7,cy-7),4)
        pygame.draw.circle(surf,(220,40,40),(cx+7,cy-7),4)
        pygame.draw.circle(surf,(255,100,100),(cx-8,cy-8),2)
        pygame.draw.circle(surf,(255,100,100),(cx+6,cy-8),2)
        # Fang
        pygame.draw.polygon(surf,(255,255,255),[(cx-3,cy+4),(cx+3,cy+4),(cx,cy+10)])
        self._draw_hp_bar(surf,70,9,(180,230,255))
        if hovered: self._hover_label(surf)

class FrostMage(Enemy):
    DISPLAY_NAME="Frost Mage"; BASE_HP=12500; BASE_SPEED=55; KILL_REWARD=12500
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=12500; self.maxhp=12500
        self.speed=self.BASE_SPEED+(wave-1)*2
        self.radius=30
        self._rot=0.0
        self._stun_immune=True
        self._snowball_timer=random.uniform(7,15)
    def update(self, dt):
        self._rot+=dt*70
        self._snowball_timer-=dt
        return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((132,132),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/70*math.pi))*35)+35
        pygame.draw.circle(s,(140,220,255,pulse),(66,66),62); surf.blit(s,(cx-66,cy-66))
        pygame.draw.circle(surf,(50,140,220),(cx,cy),self.radius+5,6)
        pygame.draw.circle(surf,(20,80,170),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,240,255),(cx-10,cy-10),15)
        pygame.draw.circle(surf,(220,248,255),(cx,cy),self.radius,3)
        # staff
        pygame.draw.line(surf,(220,248,255),(cx+18,cy-18),(cx+36,cy+22),4)
        pygame.draw.circle(surf,(120,220,255),(cx+36,cy+22),7)
        self._draw_hp_bar(surf,72,9,(140,220,255))
        if hovered: self._hover_label(surf)

class FrostHero(Enemy):
    DISPLAY_NAME="Frost Hero"; BASE_HP=25000; BASE_SPEED=28; KILL_REWARD=30000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=25000; self.maxhp=25000
        self.speed=self.BASE_SPEED+(wave-1)
        self.radius=40
        self._rot=0.0
        self._stun_immune=True
        # Curse Wave like TrueFallenKing (handled in game.py for unit stun)
        self._curse_timer=random.uniform(12,20)
        self._curse_active=False
        self._curse_dur=0.0
        self._curse_ring_r=0.0
    def update(self, dt):
        self._rot+=dt*45
        if not self._curse_active:
            self._curse_timer-=dt
            if self._curse_timer<=0:
                self._curse_active=True; self._curse_dur=0.6; self._curse_ring_r=0.0
        else:
            self._curse_dur-=dt; self._curse_ring_r+=dt*520
            if self._curse_dur<=0:
                self._curse_active=False; self._curse_timer=random.uniform(12,20)
        return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.5); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((200,200),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot*0.6))*60)+25
        pygame.draw.circle(s,(160,230,255,pulse),(100,100),94); surf.blit(s,(cx-100,cy-100))
        if self._curse_active and self._curse_ring_r < 320:
            cr=int(self._curse_ring_r)
            ring_alpha=max(0,int((1.0-self._curse_ring_r/255)*180))
            rs=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            pygame.draw.circle(rs,(120,200,255,ring_alpha),(cx,cy),cr,5)
            pygame.draw.circle(rs,(220,248,255,ring_alpha//2),(cx,cy),cr+10,2)
            surf.blit(rs,(0,0))
        pygame.draw.circle(surf,(60,150,220),(cx,cy),self.radius+7,7)
        pygame.draw.circle(surf,(20,90,180),(cx,cy),self.radius)
        pygame.draw.circle(surf,(240,255,255),(cx-12,cy-12),20)
        pygame.draw.circle(surf,(220,248,255),(cx,cy),self.radius,3)
        self._draw_hp_bar(surf,92,11,(160,230,255))
        if hovered: self._hover_label(surf)

class DeepFreeze(Enemy):
    DISPLAY_NAME="Deep Freeze"; BASE_HP=12000; BASE_SPEED=55; KILL_REWARD=10000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=10000; self.maxhp=10000
        self.speed=self.BASE_SPEED+(wave-1)*2
        self.radius=30
        self._rot=0.0
        self._stun_immune=True
    def update(self, dt):
        self._rot+=dt*60; return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((132,132),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/60*math.pi))*40)+25
        pygame.draw.circle(s,(100,200,255,pulse),(66,66),62); surf.blit(s,(cx-66,cy-66))
        pygame.draw.circle(surf,(40,130,210),(cx,cy),self.radius+5,6)
        pygame.draw.circle(surf,(10,70,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(220,248,255),(cx-10,cy-10),15)
        pygame.draw.circle(surf,(200,240,255),(cx,cy),self.radius,3)
        self._draw_hp_bar(surf,72,9,(120,210,255))
        if hovered: self._hover_label(surf)

class FrostNecromancer(Enemy):
    DISPLAY_NAME="Frost Necromancer"; BASE_HP=30000; BASE_SPEED=28; KILL_REWARD=40000
    def __init__(self, wave=1):
        super().__init__(wave)
        self.hp=30000; self.maxhp=30000
        self.speed=self.BASE_SPEED+(wave-1)
        self.radius=34
        self._summon_timer=5.0
        self._rot=0.0
        self._stun_immune=True
    def update(self, dt):
        self._rot+=dt*60
        self._summon_timer-=dt
        return super().update(dt)
    def should_summon(self):
        if self._summon_timer<=0:
            self._summon_timer=5.0
            return True
        return False
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.6); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((156,156),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/60*math.pi))*35)+25
        pygame.draw.circle(s,(120,220,255,pulse),(78,78),74); surf.blit(s,(cx-78,cy-78))
        pygame.draw.circle(surf,(40,120,200),(cx,cy),self.radius+6,7)
        pygame.draw.circle(surf,(20,70,160),(cx,cy),self.radius)
        pygame.draw.circle(surf,(200,240,255),(cx-10,cy-10),16)
        pygame.draw.circle(surf,(220,248,255),(cx,cy),self.radius,3)
        # tiny "bone" marks
        for i in range(3):
            a=math.radians(self._rot+i*120)
            x1=cx+int(math.cos(a)*6); y1=cy+int(math.sin(a)*6)
            x2=cx+int(math.cos(a)*(self.radius-2)); y2=cy+int(math.sin(a)*(self.radius-2))
            pygame.draw.line(surf,(220,248,255),(x1,y1),(x2,y2),3)
        self._draw_hp_bar(surf,78,9,(140,220,255))
        if hovered: self._hover_label(surf)

class FrostSpirit(Enemy):
    DISPLAY_NAME="Frost Spirit"; BASE_HP=200000; BASE_SPEED=26; KILL_REWARD=0
    def __init__(self, wave=1):
        super().__init__(1)
        self.hp=200000; self.maxhp=200000
        # slightly slower than TankEnemy (28)
        self.speed=self.BASE_SPEED
        self.radius=56
        self._rot=0.0
        self._stun_immune=True
        # rewards: 12_500 per each 2.5% hp lost (handled in game.py)
        self._reward_steps_paid=0
        # abilities timers (handled in game.py)
        self._ice_column_timer=random.uniform(10,15)
        self._icicles_timer=random.uniform(20,25)
        self._summon_pack_timer=30.0
    def update(self, dt):
        self._rot+=dt*35
        self._ice_column_timer-=dt
        self._icicles_timer-=dt
        self._summon_pack_timer-=dt
        return super().update(dt)
    def draw(self, surf, hovered=False, detected=False):
        bob=math.sin(self._bob*0.4); cx,cy=int(self.x),int(self.y+bob)
        s=pygame.Surface((280,280),pygame.SRCALPHA)
        pulse=int(abs(math.sin(self._rot/50))*60)+40
        pygame.draw.circle(s,(220,248,255,pulse),(140,140),132); surf.blit(s,(cx-140,cy-140))
        pygame.draw.circle(surf,(120,220,255),(cx,cy),self.radius+10,10)
        pygame.draw.circle(surf,(60,150,220),(cx,cy),self.radius+4,6)
        pygame.draw.circle(surf,(20,90,180),(cx,cy),self.radius)
        pygame.draw.circle(surf,(255,255,255),(cx-16,cy-16),24)
        pygame.draw.circle(surf,(220,248,255),(cx,cy),self.radius,4)
        # scythe silhouette
        pygame.draw.line(surf,(220,248,255),(cx+24,cy-34),(cx+70,cy+30),8)
        pygame.draw.circle(surf,(220,248,255),(cx+72,cy+32),14,4)
        self._draw_hp_bar(surf,110,12,(220,248,255))
        if hovered: self._hover_label(surf)


# ── Frosty breaker pool ────────────────────────────────────────────────────────
FROST_MYSTERY_POOL_SNOWY  = SnowyEnemy
FROST_MYSTERY_POOL_FROZEN = FrozenEnemy

# ── Frosty wave data (40 waves × 25 coins = 1000 total) ───────────────────────
FROSTY_MAX_WAVES = 40
FROSTY_WAVE_DATA = [
    None,                                                                                                                    # 0
    ([(FrozenEnemy,4)],                                                                          204, 40),                   # 1
    ([(FrozenEnemy,8)],                                                                          250, 50),                   # 2
    ([(FrozenEnemy,8),(SnowyEnemy,3)],                                                           298, 59),                   # 3
    ([(SnowyEnemy,8),(FrozenEnemy,3)],                                                           347, 69),                   # 4
    ([(FrozenEnemy,8),(PackedIceEnemy,1)],                                                       400, 80),                   # 5
    ([(PackedIceEnemy,3),(SnowyEnemy,8)],                                                        446, 94),                   # 6
    ([(SnowMinion,1),(SnowyEnemy,8)],                                                            496, 99),                   # 7
    ([(PackedIceEnemy,3),(FrozenEnemy,6),(SnowyEnemy,6)],                                        546, 109),                  # 8
    ([(PackedIceEnemy,5),(FrostMystery,3)],                                                      596, 119),                  # 9
    ([(PackedIceEnemy,6),(Frostmite,5),(SnowMinion,1)],                                          647, 129),                  # 10
    ([(Frostmite,5),(PackedIceEnemy,2),(FrozenEnemy,5),(SnowyEnemy,6),(SnowMinion,1)],           698, 139),                  # 11
    ([(ColdMist,6),(SnowMinion,1)],                                                              759, 156),                  # 12
    ([(FrostMystery,12)],                                                                        800, 160),                  # 13
    ([(Frostmite,2),(Permafrost,1),(SnowMinion,2)],                                              851, 170),                  # 14
    ([(ColdMist,3),(PackedIceEnemy,3),(FrostHunter,1),(SnowMinion,2)],             874, 180),                  # 15
    ([(UnstableIce,2),(FrostMystery,8),(PackedIceEnemy,5)],                                      954, 190),                  # 16
    ([(Permafrost,1),(UnstableIce,1),(SnowyEnemy,6),(Frostmite,6),(ColdMist,6)],                 978, 200),                  # 17
    ([(FrostMystery,2),(FrostWraith,1),(Frostmite,2)],                                          995, 205),                  # 18
    ([(SnowMinion,2),(ColdMist,3),(Frostmite,3),(Permafrost,1),(FrostAcolyte,1)],              1057, 211),                  # 19
    ([(FrostHunter,1),(FrostAcolyte,1)],                                                       1109, 221),                  # 20
    ([(Permafrost,1),(UnstableIce,1),(Frostmite,1),(SnowMinion,2),(FrostAcolyte,1)],            1161, 232),                  # 21
    ([(UnstableIce,2),(SnowMinion,2),(FrostHunter,1),(FrostAcolyte,1)],                          1213, 242),                  # 22
    ([(Frostmite,2),(FrostWraith,1),(FrostUndead,2),(FrostMystery,2),(Permafrost,2)],            1265, 253),                  # 23
    ([(UnstableIce,2),(ColdMist,3),(SnowMinion,2),(FrostInvader,1)],                             1317, 273),                  # 24
    ([(FrostAcolyte,3),(MegaFrostMystery,5)],                                                    1421, 286),                  # 25
    ([(UnstableIce,2),(FrostUndead,1),(FrostHunter,2),(FrostWraith,5),(FrostMystery,6)],         1467, 297),                  # 26
    ([(UnstableIce,3),(FrostInvader,1),(MegaFrostMystery,3),(FrostUndead,4)],                    1526, 305),                  # 27
    ([(FrostInvader,1),(UnstableIce,2),(Permafrost,5),(MegaFrostMystery,3),(FrostRavager,1)],    1579, 315),                  # 28
    ([(FrostWraith,5),(ColdMist,6),(FrostAcolyte,3),(TricksterElf,2)],                           1634, 334),                  # 29
    ([(FrostInvader,2),(FrostMystery,4),(FrostUndead,3),(Yeti,1)],                               1684, 336),                  # 30
    ([(FrostUndead,1),(MegaFrostMystery,14),(UnstableIce,3),(FrostWraith,6)],                    1734, 341),                  # 31
    ([(FrostInvader,3),(FrostWraith,5),(MegaFrostMystery,3),(FrostMage,1)],                     1795, 349),                  # 32
    ([(Yeti,2),(FrostHunter,6)],                                                                 1813, 359),                  # 33
    ([(UnstableIce,3),(FrostAcolyte,2),(TricksterElf,2),(FrostHunter,4),(FrostRavager,1)],       1875, 364),                  # 34
    ([(FrostRavager,1),(UnstableIce,4),(FrostHero,1),(FrostHunter,3),(FrostRavager,1)],          2000, 380),                  # 35
    ([(DeepFreeze,3),(MegaFrostMystery,5),(FrostMage,2),(Yeti,1),(FrostUndead,6)],               2100, 400),                  # 36
    ([(Yeti,1),(DeepFreeze,2),(MegaFrostMystery,6),(FrostUndead,6),(FrostHunter,5)],             2200, 450),                  # 37
    ([(FrostRavager,1),(FrostHero,1),(FrostNecromancer,1),(TricksterElf,2),(FrostWraith,2)],    2300, 500),                  # 38
    ([(FrostHero,2),(DeepFreeze,2),(FrostHunter,4)],                                             5000,  0),                   # 39
    ([(FrostInvader,3),(FrostRavager,1),(FrostMage,3),(FrostHunter,5),(UnstableIce,7),
      (FrostUndead,8),(MegaFrostMystery,10),(Yeti,1),(FrostHero,2),(DeepFreeze,2),
      (FrostNecromancer,1),(FrostSpirit,1)],                                                0,     0),                   # 40
]

# ── Boss Rush wave data (20 волн) ─────────────────────────────────────────────
# Концепция: каждые ~2 волны появляется босс(ы), плюс мясо для нагрузки.
# Стартовые деньги: 800. Деньги как в Fallen.
BOSS_RUSH_WAVE_DATA = [
    None,                                                                                                                      # 0
    # Разминка — лёгкие враги
    ([(Enemy,8),(ScoutEnemy,5)],                                                              204, 40),                        # 1
    # Первый мини-босс
    ([(TankEnemy,6),(NormalBoss,1),(Enemy,10)],                                               250, 50),                        # 2
    ([(BreakerEnemy,8),(ScoutEnemy,8),(HiddenEnemy,6)],                                       298, 59),                        # 3
    # Necromancer дебютирует
    ([(TankEnemy,8),(Necromancer,1),(Enemy,10)],                                              347, 69),                        # 4
    ([(BreakerEnemy,10),(HiddenEnemy,8),(NormalBoss,2)],                                      400, 80),                        # 5
    # Slow Boss
    ([(TankEnemy,10),(SlowBoss,1),(NormalBoss,2),(ScoutEnemy,10)],                            446, 94),                        # 6
    ([(BreakerEnemy,12),(HiddenBoss,1),(HiddenEnemy,10)],                                     496, 99),                        # 7
    # Fallen враги начинаются
    ([(FallenDreg,5),(FallenSquire,1),(Necromancer,2),(NormalBoss,2)],                        546, 109),                       # 8
    ([(FallenSoul,6),(FallenEnemy,8),(SlowBoss,2)],                                           596, 119),                       # 9
    # GraveDigger — финальник Easy
    ([(FallenGiant,1),(FallenDreg,8),(FallenHazmat,5),(GraveDigger,1)],                       647, 129),                       # 10
    ([(FallenSquire,3),(FallenNecromancer,1),(FallenEnemy,6),(NecroticSkeleton,2)],           698, 139),                       # 11
    ([(FallenGiant,2),(FallenHazmat,8),(CorruptedFallen,4),(SlowBoss,2)],                     759, 156),                       # 12
    ([(FallenJester,1),(FallenRusher,6),(FallenBreaker,8),(FallenHazmat,6)],                  800, 160),                       # 13
    # FallenShield + Honor Guard
    ([(FallenShield,1),(FallenHero,3),(FallenGiant,2),(FallenNecromancer,1)],                 851, 170),                       # 14
    ([(FallenHonorGuard,1),(FallenGiant,3),(FallenRusher,8),(CorruptedFallen,6)],             954, 190),                       # 15
    # Frost боссы входят
    ([(FrostHunter,2),(FrostRavager,1),(FallenHero,4),(FallenGiant,2)],                      1109, 221),                       # 16
    ([(Yeti,1),(FrostMage,1),(FallenHonorGuard,1),(FallenNecromancer,2),(FallenGiant,3)],    1317, 273),                       # 17
    # Финальный забег — всё вместе
    ([(FrostHero,2),(FrostNecromancer,1),(FallenHonorGuard,1),(FallenShield,1),(Yeti,1),(FallenGiant,4)], 2000, 380),          # 18
    ([(FrostRavager,2),(FrostHero,2),(FallenHonorGuard,2),(FallenGiant,5),(FrostMage,2)],    2300, 500),                       # 19
    # Финал — все финальники вместе
    ([(GraveDigger,1),(FallenHonorGuard,1),(FrostHero,3),(FrostNecromancer,1),(FrostRavager,2),(FallenGiant,5)], 5000, 0),     # 20
]
BOSS_RUSH_MAX_WAVES = 20


FALLEN_BREAKER_POOL=[FallenEnemy, FallenDreg, FallenSoul, FallenHazmat]

# ── Wave data ──────────────────────────────────────────────────────────────────
BREAKER_POOL=[HiddenEnemy,Enemy,ScoutEnemy,TankEnemy,NormalBoss]

WAVE_DATA=[
    None,
    ([(Enemy,3)],200,70),
    ([(Enemy,5)],350,122),
    ([(Enemy,8),(ScoutEnemy,4)],500,175),
    ([(ScoutEnemy,4),(Enemy,6),(TankEnemy,4)],650,227),
    ([(Enemy,5),(TankEnemy,6)],800,280),
    ([(TankEnemy,4),(ScoutEnemy,8),(NormalBoss,1)],950,332),
    ([(TankEnemy,6),(ScoutEnemy,10),(NormalBoss,1)],1100,385),
    ([(Enemy,10),(TankEnemy,8),(HiddenEnemy,6)],1250,437),
    ([(NormalBoss,1),(TankEnemy,3),(HiddenEnemy,10),(ScoutEnemy,7)],1400,489),
    ([(TankEnemy,7),(ScoutEnemy,7),(BreakerEnemy,5)],1550,542),
    ([(BreakerEnemy,10),(HiddenEnemy,8),(NormalBoss,1)],1700,595),
    ([(Necromancer,1),(HiddenEnemy,10),(Enemy,10),(TankEnemy,5),(ScoutEnemy,6)],1850,647),
    ([(ArmoredEnemy,9),(BreakerEnemy,10)],2000,700),
    ([(ArmoredEnemy,12),(HiddenEnemy,10),(BreakerEnemy,15),(NormalBoss,2)],2150,752),
    ([(ArmoredEnemy,15),(NormalBoss,3),(Necromancer,2)],2300,805),
    ([(SlowBoss,1),(Enemy,20)],2450,857),
    ([(BreakerEnemy,30),(HiddenBoss,1)],2600,909),
    ([(ArmoredEnemy,10),(Necromancer,1),(ScoutEnemy,10),(HiddenEnemy,10)],2750,962),
    ([(BreakerEnemy,10),(NormalBoss,1),(SlowBoss,1),(TankEnemy,3)],2900,1014),
    ([(BreakerEnemy,20),(ArmoredEnemy,20),(HiddenEnemy,20),(Enemy,20),
      (TankEnemy,20),(ScoutEnemy,20),(SlowBoss,5),(NormalBoss,5)],5000,0),
]

FALLEN_MAX_WAVES = 40
FALLEN_WAVE_DATA = [
    None,                                                                                              # 0
    ([(AbnormalEnemy,5)],204,40),                                                                      # 1
    ([(AbnormalEnemy,8)],250,50),                                                                      # 2
    ([(QuickEnemy,4),(Enemy,6)],298,59),                                                               # 3
    ([(QuickEnemy,8),(AbnormalEnemy,8)],347,69),                                                       # 4
    ([(SkeletonEnemy,3),(QuickEnemy,6),(Enemy,5)],400,80),                                             # 5
    ([(SkeletonEnemy,6)],446,94),                                                                      # 6
    ([(FallenDreg,1),(Enemy,7)],496,99),                                                               # 7
    ([(FallenDreg,3),(SkeletonEnemy,4)],546,109),                                                      # 8
    ([(FallenSquire,1),(Enemy,5),(SkeletonEnemy,4)],596,119),                                          # 9
    ([(FallenDreg,3),(BreakerEnemy,4),(SkeletonEnemy,2)],647,129),                                     # 10
    ([(FallenSquire,1),(FallenDreg,3),(SkeletonEnemy,3),(BreakerEnemy,3)],698,139),                    # 11
    ([(FallenSoul,7)],759,156),                                                                        # 12
    ([(FallenDreg,3),(FallenSquire,1)],800,160),                                                       # 13
    ([(BreakerEnemy,6),(FallenSoul,6),(FallenEnemy,4)],851,170),                                       # 14
    ([(SkeletonEnemy,8),(BreakerEnemy,4),(FallenSquire,2)],874,180),                                   # 15
    ([(FallenDreg,4),(FallenSoul,6),(FallenSquire,2),(FallenGiant,1)],954,190),                        # 16
    ([(FallenHazmat,5),(FallenEnemy,2)],978,200),                                                      # 17
    ([(FallenGiant,1),(FallenHazmat,5)],995,205),                                                      # 18
    ([],255,211),                                                                                     # 19 — empty wave, just bonus money
    ([(FallenSquire,3),(FallenDreg,10),(FallenSoul,8),(PossessedArmor,1)],1109,221),                   # 20
    ([(FallenEnemy,5),(FallenHazmat,5),(SkeletonEnemy,5),(FallenSquire,3),(FallenNecromancer,1)],1161,232), # 21
    ([(BreakerEnemy,6),(FallenSquire,3),(PossessedArmor,2),(BreakerEnemy,5)],1213,242),                # 22
    ([(CorruptedFallen,4),(FallenSquire,5)],1265,253),                                                 # 23
    ([(FallenSquire,7),(FallenNecromancer,1)],1317,273),                                               # 24
    ([(PossessedArmor,1),(FallenHazmat,6),(CorruptedFallen,3),(FallenGiant,3),(FallenJester,1)],1421,286), # 25
    ([(NecroticSkeleton,1),(FallenGiant,3),(FallenBreaker,3)],1467,297),                               # 26
    ([(NecroticSkeleton,3),(FallenGiant,3),(FallenNecromancer,1),(FallenBreaker,5)],1526,305),         # 27
    ([(FallenRusher,10)],1579,315),                                                                    # 28
    ([(FallenHazmat,10),(FallenBreaker,10)],1634,334),                                                 # 29
    ([(FallenGiant,5),(NecroticSkeleton,5),(FallenShield,1)],1684,336),                                # 30
    ([(FallenGiant,3),(FallenHazmat,10),(FallenNecromancer,1),(FallenHero,5)],1734,341),               # 31
    ([(FallenBreaker,10),(FallenBreaker,5),(FallenJester,1)],1795,349),                                # 32
    ([(CorruptedFallen,7),(FallenGiant,3),(FallenNecromancer,3),(NecroticSkeleton,1)],1813,359),       # 33
    ([(FallenShield,1),(NecroticSkeleton,1),(FallenHero,2),(FallenRusher,3),(FallenNecromancer,1)],1875,364), # 34
    ([(FallenNecromancer,2),(FallenGiant,3),(BreakerEnemy,9),(NecroticSkeleton,1),(FallenHonorGuard,1)],2000,380), # 35
    ([(FallenGiant,4),(CorruptedFallen,8),(FallenHero,10)],2100,400),                                  # 36
    ([(CorruptedFallen,10),(FallenHero,5),(FallenNecromancer,3),(PossessedArmor,5),(FallenGiant,4),(FallenBreaker,3),(SkeletonEnemy,20)],2200,450), # 37
    ([(FallenShield,1),(NecroticSkeleton,3),(PossessedArmor,8),(FallenRusher,3),(FallenHero,5),(FallenBreaker,10)],2300,500), # 38
    ([(FallenHonorGuard,1),(FallenHero,5),(FallenGiant,5),(FallenRusher,6)],5000,0),                   # 39
    ([],0,0),                                                                                          # 40 — Fallen King wave (spawned via music trigger)
]

# ── WaveManager ────────────────────────────────────────────────────────────────
class WaveManager:
    # ── Per-wave DURATION tables ───────────────────────────────────────────────
    # Format: wave_number -> (wave_duration_seconds, skip_unlock_seconds or None)
    # wave_duration = how long the wave itself lasts (timer shown DURING the wave)
    # skip_unlock   = seconds remaining when skip button appears (None = no skip)
    # Between waves is always a fixed 5 seconds (no skip).
    _BETWEEN_TIME = 5.0  # fixed gap between every wave

    _EASY_WAVE_TIMES = {
        **{w: (60, 19) for w in range(1, 16)},       # 1-15:  1:00, skip at 0:19
        **{w: (90, 19) for w in range(16, 20)},      # 16-19: 1:30, skip at 0:19
        20: (None, None),                             # wave 20: no auto-timer (GraveDigger)
    }
    _FALLEN_WAVE_TIMES = {
        **{w: (60, 19) for w in range(1, 16)},       # 1-15:  1:00
        16: (80, 19),                                 # 16:    1:20
        17: (60, 19),                                 # 17:    1:00
        **{w: (75, 19) for w in range(18, 20)},      # 18-19: 1:15
        **{w: (60, 19) for w in range(20, 23)},      # 20-22: 1:00
        23: (75, 19),                                 # 23:    1:15
        24: (60, 19),                                 # 24:    1:00
        25: (70, 19),                                 # 25:    1:10
        26: (75, 19),                                 # 26:    1:15
        **{w: (60, 19) for w in range(27, 30)},      # 27-29: 1:00
        **{w: (80, 19) for w in range(30, 35)},      # 30-34: 1:20
        35: (20, None),                               # 35:    0:20, no skip
        36: (35, 19),                                 # 36:    0:35
        37: (40, 19),                                 # 37:    0:40
        38: (180, 19),                                # 38:    3:00
        39: (120, 19),                                # 39:    2:00
    }
    _FROSTY_WAVE_TIMES = {
        **{w: (45, 19) for w in range(1, 15)},       # 1-14:  0:45
        **{w: (60, 19) for w in range(15, 20)},      # 15-19: 1:00
        20: (90, 19),                                 # 20:    1:30
        **{w: (60, 19) for w in range(21, 25)},      # 21-24: 1:00
        **{w: (60, 19) for w in range(25, 30)},      # 25-29: 1:00
        35: (130, 19), 36: (130, 19),
        37: (180, 19), 38: (185, 19), 39: (185, 19),
        40: (None, None),
    }

    def __init__(self, wave_data=None, max_waves=None):
        self.wave_data = wave_data if wave_data is not None else WAVE_DATA
        self.max_waves = max_waves if max_waves is not None else MAX_WAVES
        self.wave=0; self.state="prep"; self.prep_timer=10.0
        self.spawn_queue=[]; self.spawn_timer=0.0; self.spawn_interval=0.9
        self._bonus_paid=False; self._lmoney_paid=False; self._gd_spawned=False
        # Which timing table to use (set by Game after construction)
        self._mode = "easy"
        # Wave-duration timer: counts down during spawning/waiting, shown to player
        self._wave_timer = None        # None when not active
        self._current_wave_time = None # total duration of this wave (for display)
        self._skip_unlock_at = None    # seconds remaining when skip unlocks

    def _build_queue(self, wn):
        if wn<1 or wn>self.max_waves or wn>=len(self.wave_data) or self.wave_data[wn] is None: return []
        groups,_,_=self.wave_data[wn]; q=[]
        for EClass,count in groups:
            for _ in range(count):
                try:
                    e=EClass(wn); e._from_wave=True; q.append(e)
                except Exception as ex:
                    import traceback; traceback.print_exc()
                    print(f"[WaveManager] ERROR creating {EClass} for wave {wn}: {ex}")
        random.shuffle(q); return q

    def _get_wave_time(self, wave_num):
        """Return (wave_duration, skip_unlock) for wave_num."""
        if self._mode == "fallen":
            tbl = self._FALLEN_WAVE_TIMES
        elif self._mode == "frosty":
            tbl = self._FROSTY_WAVE_TIMES
        else:
            tbl = self._EASY_WAVE_TIMES
        return tbl.get(wave_num, (60, 19))  # default 60s, skip at 19s

    def update(self, dt, enemies):
        alive_count=sum(1 for e in enemies if e.alive and not getattr(e,"free_kill",False))

        if self.state=="prep":
            # Initial 5-second countdown before wave 1
            self.prep_timer-=dt
            if self.prep_timer<=0: self._start_wave()

        elif self.state=="spawning":
            # Tick the wave-duration timer
            if self._wave_timer is not None:
                self._wave_timer -= dt

            # Spawn enemies
            self.spawn_timer-=dt
            if self.spawn_timer<=0 and self.spawn_queue:
                self.spawn_timer=self.spawn_interval
                enemies.append(self.spawn_queue.pop(0))
            if not self.spawn_queue and self.spawn_timer<=0:
                self.state="waiting"

        elif self.state=="waiting":
            # Wave timer still ticking after all enemies are spawned
            if self._wave_timer is not None:
                self._wave_timer -= dt

            if self.wave==20 and self.max_waves==MAX_WAVES and not self._gd_spawned:
                if alive_count==0:
                    enemies.append(GraveDigger()); self._gd_spawned=True
            else:
                # As soon as all enemies are dead — start 5s countdown immediately
                if alive_count==0:
                    self._wave_timer = None
                    self.state="between"
                    self.prep_timer = self._BETWEEN_TIME

        elif self.state=="between":
            # Fixed 5-second gap, no skip
            self.prep_timer-=dt
            if self.prep_timer<=0:
                if self.wave<self.max_waves: self._start_wave()
                else: self.state="done"

    def _start_wave(self):
        self.wave+=1; self.state="spawning"
        self.spawn_queue=self._build_queue(self.wave)
        self.spawn_timer=self.spawn_interval
        self._bonus_paid=False; self._lmoney_paid=False; self._gd_spawned=False
        # Start the wave-duration timer for this wave
        wt, su = self._get_wave_time(self.wave)
        if wt is not None:
            self._wave_timer = float(wt)
            self._current_wave_time = float(wt)
            self._skip_unlock_at = su
        else:
            self._wave_timer = None
            self._current_wave_time = None
            self._skip_unlock_at = None

    def time_left(self):
        """Returns seconds left on the current timer, or None."""
        if self.state in ("spawning", "waiting"):
            if self._wave_timer is not None:
                return max(0, self._wave_timer)
        elif self.state in ("prep", "between"):
            return max(0, self.prep_timer)
        return None

    def can_skip(self):
        """Returns True if the skip button should be active (only during the wave itself)."""
        if self.state not in ("spawning", "waiting"): return False
        tl = self.time_left()
        if tl is None: return False
        if self._skip_unlock_at is None: return False
        return tl <= self._skip_unlock_at

    def do_skip(self):
        """Skip the remaining wave timer — clears spawn queue and goes to between."""
        if self.state in ("spawning", "waiting"):
            self.spawn_queue = []
            self._wave_timer = None
            self.state = "between"
            self.prep_timer = self._BETWEEN_TIME
    def wave_lmoney(self):
        if 1<=self.wave<len(self.wave_data) and self.wave_data[self.wave]: return self.wave_data[self.wave][1]
        return 0
    def wave_bmoney(self):
        if 1<=self.wave<len(self.wave_data) and self.wave_data[self.wave]: return self.wave_data[self.wave][2]
        return 0