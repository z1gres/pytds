# ══════════════════════════════════════════════════════════════════════════════
# MULTIPLAYER SYSTEM — assets/multiplayer.py
# Лежит в папке assets/, импортирует game.py из родительской папки
# ══════════════════════════════════════════════════════════════════════════════

import sys, os
# Добавляем папку с game.py (родительская по отношению к assets/) в путь поиска
_GAME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _GAME_DIR not in sys.path:
    sys.path.insert(0, _GAME_DIR)

import socket
import threading
import queue
import pygame
import time as _time
import math
import random
import os

import game_core as _game_core

# Импортируем всё необходимое из основного файла игры
from game import (
    # Constants & colors
    SCREEN_W, SCREEN_H, FPS, TILE,
    C_BG, C_WHITE, C_BLACK, C_GOLD, C_CYAN, C_BORDER,
    PATH_Y, PATH_H, SLOT_AREA_Y,
    # Fonts
    font_sm, font_md, font_lg,
    # Helpers
    txt, draw_rect_alpha, dist, load_icon, load_save, write_save,
    # Map
    get_map_path,
    # Enemy classes
    Enemy, TankEnemy, ScoutEnemy, NormalBoss, HiddenEnemy,
    BreakerEnemy, ArmoredEnemy, SlowBoss, HiddenBoss,
    Necromancer, FastBoss, OtchimusPrime, GraveDigger,
    AbnormalEnemy, QuickEnemy, SkeletonEnemy,
    FallenDreg, FallenSquire, FallenSoul, FallenEnemy,
    FallenGiant, FallenHazmat, PossessedArmorInner, PossessedArmor,
    FallenNecromancer, CorruptedFallen, FallenJester,
    NecroticSkeleton, FallenBreaker, FallenRusher,
    FallenHonorGuard, FallenShield, FallenHero,
    FallenKing, TrueFallenKing,
    # Unit classes
    Assassin, Accelerator, Frostcelerator, Xw5ytUnit,
    Lifestealer, Archer, RedBall, Farm, Freezer,
    # Unit level data
    ASSASSIN_LEVELS, ACCEL_LEVELS, FROST_LEVELS, XW5YT_LEVELS,
    LIFESTEALER_LEVELS, ARCHER_LEVELS, REDBALL_LEVELS, FARM_LEVELS, FREEZER_LEVELS,
    # Game classes
    Game, FloatingText, MapSelectMenu,
    # UI
    C_LIFESTEALER, C_LIFESTEALER_DARK,
    C_ARCHER, C_ARCHER_DARK,
    C_REDBALL, C_REDBALL_DARK,
    C_FARM, C_FARM_DARK,
)
import game as _game_module

MP_PORT    = 7777
MP_TICKRATE = 10  # network ticks per second (lower = less traffic, better for bad connections)


# ── Low-level TCP framing ─────────────────────────────────────────────────────
import json
import zlib

def _send_msg(sock, data: dict):
    try:
        raw = json.dumps(data, separators=(',', ':')).encode("utf-8")
        compressed = zlib.compress(raw, level=1)   # fast compression
        header = len(compressed).to_bytes(4, "big")
        sock.sendall(header + compressed)
        return True
    except Exception:
        return False


def _recv_msg(sock):
    """Receive one length-prefixed message. Blocks until data arrives or socket closes."""
    try:
        header = b""
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                return None
            header += chunk
        length = int.from_bytes(header, "big")
        if length == 0 or length > 10 * 1024 * 1024:
            return None
        data = b""
        while len(data) < length:
            chunk = sock.recv(min(65536, length - len(data)))
            if not chunk:
                return None
            data += chunk
        # Auto-detect: zlib compressed starts with 0x78 0x9C or 0x78 0x01 etc.
        if len(data) >= 2 and data[0] == 0x78:
            try:
                return json.loads(zlib.decompress(data).decode("utf-8"))
            except Exception:
                pass
        # Fallback: raw JSON
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None


# ── MPServer ──────────────────────────────────────────────────────────────────
class MPServer:
    def __init__(self):
        self.conn = None
        self.in_q    = queue.Queue()
        self._send_q = queue.Queue()
        self.running = False
        self.server_sock = None
        self.client_connected = False

    def start(self, port=MP_PORT):
        self.running = True
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(("0.0.0.0", port))
        self.server_sock.listen(1)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        self.server_sock.settimeout(120)
        try:
            conn, _ = self.server_sock.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            try:
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            except (AttributeError, OSError): pass
            self.conn = conn
            self.client_connected = True
            threading.Thread(target=self._recv_loop, daemon=True).start()
            threading.Thread(target=self._send_loop, daemon=True).start()
        except Exception:
            pass

    def _recv_loop(self):
        while self.running:
            msg = _recv_msg(self.conn)
            if msg is None:
                self.client_connected = False
                break
            self.in_q.put(msg)

    def _send_loop(self):
        while self.running:
            try:
                data = self._send_q.get(timeout=0.5)
                if self.conn and self.client_connected:
                    if not _send_msg(self.conn, data):
                        self.client_connected = False
            except queue.Empty:
                pass

    def broadcast(self, data: dict):
        if self.client_connected:
            if data.get("type") == "state":
                while not self._send_q.empty():
                    try:
                        old = self._send_q.get_nowait()
                        if old.get("type") != "state":
                            self._send_q.put(old)
                    except queue.Empty:
                        break
            self._send_q.put(data)

    def send_start(self, map_name: str):
        if self.conn:
            _send_msg(self.conn, {"type": "start", "map": map_name})

    def stop(self):
        self.running = False
        try: self.server_sock.close()
        except: pass
        try: self.conn.close()
        except: pass


# ── MPClient ──────────────────────────────────────────────────────────────────
class MPClient:
    def __init__(self):
        self.sock = None
        self.in_q    = queue.Queue()
        self._send_q = queue.Queue()
        self.running = False
        self.connected = False

    def connect(self, host, port=MP_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect((host, port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 10)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        except (AttributeError, OSError): pass
        self.sock.settimeout(None)
        self.running = True
        self.connected = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._send_loop, daemon=True).start()

    def wait_for_start(self, timeout=60):
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                msg = self.in_q.get(timeout=0.1)
                if msg.get("type") == "start":
                    return msg.get("map", "straight")
                self.in_q.put(msg)
            except queue.Empty:
                pass
            if not self.connected:
                return None
        return None

    def _recv_loop(self):
        while self.running:
            msg = _recv_msg(self.sock)
            if msg is None:
                self.connected = False
                break
            self.in_q.put(msg)

    def _send_loop(self):
        while self.running:
            try:
                data = self._send_q.get(timeout=0.5)
                if self.sock and self.connected:
                    if not _send_msg(self.sock, data):
                        self.connected = False
            except queue.Empty:
                pass

    def send(self, data: dict):
        if self.connected:
            self._send_q.put(data)

    def stop(self):
        self.running = False
        try: self.sock.close()
        except: pass


# ── Multiplayer Lobby UI ──────────────────────────────────────────────────────
class MultiplayerMenu:
    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        self.action = None
        cx = SCREEN_W // 2
        bw, bh = 300, 60
        self.btn_host = pygame.Rect(cx - bw//2, SCREEN_H//2 - 80, bw, bh)
        self.btn_join = pygame.Rect(cx - bw//2, SCREEN_H//2 + 10,  bw, bh)
        self.btn_back = pygame.Rect(cx - bw//2, SCREEN_H//2 + 100, bw, bh)

    def run(self):
        clock = pygame.time.Clock()
        while self.action is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); import sys; sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_host.collidepoint(ev.pos): self.action = "host"
                    if self.btn_join.collidepoint(ev.pos): self.action = "join"
                    if self.btn_back.collidepoint(ev.pos): self.action = "back"
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.action = "back"
            self._draw()
            pygame.display.flip()
        return self.action

    def _draw(self):
        self.screen.fill(C_BG)
        random.seed(99)
        for _ in range(180):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.1 + sx * 0.01)) * 160 + 60)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)
        random.seed()
        f = pygame.font.SysFont("consolas", 44, bold=True)
        title = f.render("MULTIPLAYER", True, (100, 200, 255))
        self.screen.blit(title, title.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 180)))
        sub = pygame.font.SysFont("segoeui", 22).render(
            "Кооперативный режим Fallen  •  +50% HP у врагов", True, (140, 140, 180))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 130)))
        mx, my = pygame.mouse.get_pos()
        for btn, label, col_h, col_n, brd in [
            (self.btn_host, "🖥  ЗАХОСТИТЬ КОМНАТУ", (40,100,60),  (25,65,38),  (80,200,110)),
            (self.btn_join, "🔗  ЗАЙТИ В КОМНАТУ",   (40,60,120),  (25,38,80),  (80,130,220)),
            (self.btn_back, "← НАЗАД",               (70,40,40),   (45,25,25),  (160,80,80)),
        ]:
            hov = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, col_h if hov else col_n, btn, border_radius=12)
            pygame.draw.rect(self.screen, brd, btn, 2, border_radius=12)
            lf = pygame.font.SysFont("segoeui", 26, bold=True)
            ls = lf.render(label, True, C_WHITE)
            self.screen.blit(ls, ls.get_rect(center=btn.center))


class HostWaitScreen:
    def __init__(self, screen, server: MPServer):
        self.screen = screen
        self.server = server
        self.t = 0.0
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self.local_ip = "127.0.0.1"
        self.btn_cancel = pygame.Rect(SCREEN_W//2 - 120, SCREEN_H//2 + 200, 240, 50)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); import sys; sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_cancel.collidepoint(ev.pos): return False
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return False
            if self.server.client_connected:
                return True
            self._draw()
            pygame.display.flip()

    def _draw(self):
        self.screen.fill(C_BG)
        random.seed(55)
        for _ in range(150):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 0.9 + sx * 0.01)) * 140 + 50)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)
        random.seed()
        cx = SCREEN_W // 2
        pulse = abs(math.sin(self.t * 1.8))
        for i in range(12):
            a = math.radians(i * 30 + self.t * 90)
            r = 55; fade = (i / 12) * pulse
            c = int(40 + fade * 180)
            px2 = int(cx + math.cos(a) * r); py2 = int(SCREEN_H//2 - 60 + math.sin(a) * r)
            pygame.draw.circle(self.screen, (min(255,c), min(255,c+40), min(255,c+80)), (px2, py2), 6)
        f1 = pygame.font.SysFont("consolas", 36, bold=True)
        s1 = f1.render("Ждём игрока...", True, (160, 200, 255))
        self.screen.blit(s1, s1.get_rect(center=(cx, SCREEN_H//2 + 30)))
        f2 = pygame.font.SysFont("segoeui", 22)
        s2 = f2.render("Дай другу эти данные для подключения:", True, (160, 160, 180))
        self.screen.blit(s2, s2.get_rect(center=(cx, SCREEN_H//2 + 80)))
        box = pygame.Rect(cx - 260, SCREEN_H//2 + 105, 520, 80)
        draw_rect_alpha(self.screen, (20, 30, 50), (box.x, box.y, box.w, box.h), 230, 10)
        pygame.draw.rect(self.screen, (80, 130, 220), box, 2, border_radius=10)
        f3 = pygame.font.SysFont("consolas", 28, bold=True)
        ip_str = f"IP: {self.local_ip}   PORT: {MP_PORT}"
        s3 = f3.render(ip_str, True, (100, 220, 255))
        self.screen.blit(s3, s3.get_rect(center=box.center))
        self.screen.blit(hint2, hint2.get_rect(center=(cx, SCREEN_H//2 + 220)))
        mx2, my2 = pygame.mouse.get_pos()
        hov = self.btn_cancel.collidepoint(mx2, my2)
        pygame.draw.rect(self.screen, (80,30,30) if hov else (50,20,20), self.btn_cancel, border_radius=8)
        pygame.draw.rect(self.screen, (180,60,60), self.btn_cancel, 2, border_radius=8)
        cf = pygame.font.SysFont("segoeui", 22, bold=True).render("Отмена", True, C_WHITE)
        self.screen.blit(cf, cf.get_rect(center=self.btn_cancel.center))


class JoinInputScreen:
    def __init__(self, screen):
        self.screen = screen
        self.t = 0.0
        self.ip_text = ""
        self.port_text = str(MP_PORT)
        self.active_field = "ip"
        self.error_msg = ""
        self.error_timer = 0.0
        cx = SCREEN_W // 2
        self.btn_connect = pygame.Rect(cx - 130, SCREEN_H//2 + 120, 260, 56)
        self.btn_back    = pygame.Rect(cx - 130, SCREEN_H//2 + 190, 260, 48)
        self.ip_rect     = pygame.Rect(cx - 220, SCREEN_H//2 - 30,  340, 52)
        self.port_rect   = pygame.Rect(cx + 130, SCREEN_H//2 - 30,  100, 52)
        self.cursor_blink = 0.0

    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            self.cursor_blink = (self.cursor_blink + dt) % 1.0
            if self.error_timer > 0: self.error_timer -= dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); import sys; sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return None
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.collidepoint(ev.pos): return None
                    if self.ip_rect.collidepoint(ev.pos):   self.active_field = "ip"
                    elif self.port_rect.collidepoint(ev.pos): self.active_field = "port"
                    if self.btn_connect.collidepoint(ev.pos):
                        result = self._try_connect()
                        if result: return result
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_TAB:
                        self.active_field = "port" if self.active_field == "ip" else "ip"
                    elif ev.key == pygame.K_RETURN:
                        result = self._try_connect()
                        if result: return result
                    elif ev.key == pygame.K_BACKSPACE:
                        if self.active_field == "ip": self.ip_text = self.ip_text[:-1]
                        else: self.port_text = self.port_text[:-1]
                    elif ev.unicode:
                        if self.active_field == "ip" and len(self.ip_text) < 40:
                            self.ip_text += ev.unicode
                        elif self.active_field == "port" and len(self.port_text) < 6:
                            if ev.unicode.isdigit(): self.port_text += ev.unicode
            self._draw()
            pygame.display.flip()

    def _try_connect(self):
        ip = self.ip_text.strip()
        try: port = int(self.port_text.strip())
        except ValueError:
            self.error_msg = "Неверный порт"; self.error_timer = 2.0; return None
        if not ip:
            self.error_msg = "Введи IP адрес"; self.error_timer = 2.0; return None
        return (ip, port)

    def _draw(self):
        self.screen.fill(C_BG)
        random.seed(77)
        for _ in range(150):
            sx = random.randint(0, SCREEN_W); sy = random.randint(0, SCREEN_H)
            br = int(abs(math.sin(self.t * 1.0 + sx * 0.01)) * 140 + 50)
            pygame.draw.circle(self.screen, (br, br, br), (sx, sy), 1)
        random.seed()
        cx = SCREEN_W // 2
        f1 = pygame.font.SysFont("consolas", 38, bold=True)
        s1 = f1.render("ЗАЙТИ В КОМНАТУ", True, (100, 180, 255))
        self.screen.blit(s1, s1.get_rect(center=(cx, SCREEN_H//2 - 130)))
        label_f = pygame.font.SysFont("segoeui", 20)
        lbl_ip = label_f.render("IP адрес (или ngrok хост)", True, (160, 160, 200))
        self.screen.blit(lbl_ip, (self.ip_rect.x, self.ip_rect.y - 24))
        lbl_pt = label_f.render("Порт", True, (160, 160, 200))
        self.screen.blit(lbl_pt, (self.port_rect.x, self.port_rect.y - 24))
        for rect, field, text in [
            (self.ip_rect, "ip", self.ip_text),
            (self.port_rect, "port", self.port_text),
        ]:
            active = (self.active_field == field)
            brd = (80,160,255) if active else (60,70,100)
            draw_rect_alpha(self.screen, (18,22,38), (rect.x,rect.y,rect.w,rect.h), 230, 8)
            pygame.draw.rect(self.screen, brd, rect, 2, border_radius=8)
            cursor = "|" if (active and self.cursor_blink < 0.5) else ""
            tf = pygame.font.SysFont("consolas", 24, bold=True)
            ts = tf.render(text + cursor, True, C_WHITE if active else (160,160,180))
            self.screen.blit(ts, ts.get_rect(midleft=(rect.x + 12, rect.centery)))
        mx2, my2 = pygame.mouse.get_pos()
        hov = self.btn_connect.collidepoint(mx2, my2)
        pygame.draw.rect(self.screen, (40,100,60) if hov else (25,65,38), self.btn_connect, border_radius=12)
        pygame.draw.rect(self.screen, (80,200,110), self.btn_connect, 2, border_radius=12)
        cf = pygame.font.SysFont("segoeui", 26, bold=True).render("Подключиться", True, C_WHITE)
        self.screen.blit(cf, cf.get_rect(center=self.btn_connect.center))
        hov2 = self.btn_back.collidepoint(mx2, my2)
        pygame.draw.rect(self.screen, (70,30,30) if hov2 else (45,20,20), self.btn_back, border_radius=8)
        pygame.draw.rect(self.screen, (160,60,60), self.btn_back, 2, border_radius=8)
        bf = pygame.font.SysFont("segoeui", 22, bold=True).render("← Назад", True, C_WHITE)
        self.screen.blit(bf, bf.get_rect(center=self.btn_back.center))
        if self.error_timer > 0:
            ef = pygame.font.SysFont("segoeui", 22).render(self.error_msg, True, (255,100,100))
            self.screen.blit(ef, ef.get_rect(center=(cx, self.btn_connect.y - 20)))


# ── Unit name maps ────────────────────────────────────────────────────────────
_MP_UNIT_NAME_MAP = {
    "Assassin": Assassin, "Accelerator": Accelerator,
    "Frostcelerator": Frostcelerator, "xw5yt": Xw5ytUnit,
    "Lifestealer": Lifestealer, "Archer": Archer,
    "Red Ball": RedBall, "Farm": Farm, "Freezer": Freezer,
}
_MP_UNIT_CLS_MAP = {v: k for k, v in _MP_UNIT_NAME_MAP.items()}


# ── MultiplayerGame ───────────────────────────────────────────────────────────
class MultiplayerGame(Game):
    MP_HP_MULT    = 1.5
    SYNC_INTERVAL = 1.0 / MP_TICKRATE

    def __init__(self, save_data, is_host: bool, net):
        super().__init__(save_data, mode="fallen")
        self.is_host = is_host
        self.net = net
        self._sync_timer = 0.0
        self._client_sync_timer = 0.0   # client: re-broadcasts own units every 2s
        self._ping_timer = 0.0          # send ping every 3s to keep connection alive
        self._peer_units = []
        self._connected = True
        self._waiting_start = not is_host
        self._peer_name = "Player 2" if is_host else "Player 1"
        self._mp_msg = ""
        self._mp_msg_timer = 0.0
        self._net_msg_count = 0  # total messages received (for debug badge)
        self._patch_enemy_hp()

    def _patch_enemy_hp(self):
        m = self.MP_HP_MULT
        for cls in [Enemy, TankEnemy, ScoutEnemy, NormalBoss, HiddenEnemy,
                    BreakerEnemy, ArmoredEnemy, SlowBoss, HiddenBoss,
                    Necromancer, FastBoss, OtchimusPrime, GraveDigger,
                    AbnormalEnemy, QuickEnemy, SkeletonEnemy,
                    FallenGiant, FallenJester, FallenSquire, FallenKing,
                    FallenShield, FallenHonorGuard, FallenRusher, FallenHero,
                    FallenBreaker, NecroticSkeleton, PossessedArmor,
                    TrueFallenKing]:
            orig = cls.BASE_HP
            cls._mp_orig_hp = orig
            cls.BASE_HP = int(orig * m)

    def _restore_enemy_hp(self):
        for cls in [Enemy, TankEnemy, ScoutEnemy, NormalBoss, HiddenEnemy,
                    BreakerEnemy, ArmoredEnemy, SlowBoss, HiddenBoss,
                    Necromancer, FastBoss, OtchimusPrime, GraveDigger,
                    AbnormalEnemy, QuickEnemy, SkeletonEnemy,
                    FallenGiant, FallenJester, FallenSquire, FallenKing,
                    FallenShield, FallenHonorGuard, FallenRusher, FallenHero,
                    FallenBreaker, NecroticSkeleton, PossessedArmor,
                    TrueFallenKing]:
            if hasattr(cls, "_mp_orig_hp"):
                cls.BASE_HP = cls._mp_orig_hp

    def _broadcast(self, data):
        if self.is_host: self.net.broadcast(data)
        else:            self.net.send(data)

    def _show_mp_msg(self, txt_str, dur=2.5):
        self._mp_msg = txt_str
        self._mp_msg_timer = dur

    def run(self):
        import sys
        if self.is_host and self.units:
            for u in self.units:
                self.net.broadcast({
                    "type": "place_unit",
                    "name": _MP_UNIT_CLS_MAP.get(type(u), ""),
                    "x": u.px, "y": u.py,
                    "uid": id(u), "level": u.level,
                })

        _mp_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mp_error.log")
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            dt *= getattr(self.ui.admin_panel, "_game_speed", 1.0)

            if self.player_hp == 1 and not self._hayden_active:
                self._hayden_eligible = True

            q = self.net.in_q
            while not q.empty():
                try:
                    msg = q.get_nowait()
                    self._handle_net_msg(msg)
                except queue.Empty:
                    break

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    try: pygame.mixer.music.stop()
                    except: pass
                    self.running = False; break

                if ev.type == pygame.USEREVENT + 1:
                    if not self.game_over and not self.win:
                        try: pygame.mixer.music.play(0, start=8.7)
                        except: pass

                if ev.type == pygame.USEREVENT + 2:
                    _mus = getattr(self, "_tf_music_path", None)
                    if _mus and os.path.exists(_mus):
                        try:
                            pygame.mixer.music.set_endevent(0)
                            pygame.mixer.music.load(_mus)
                            pygame.mixer.music.play(-1, start=0.0)
                        except: pass

                if ev.type == pygame.MOUSEWHEEL and self.mode == "sandbox":
                    if self.ui.admin_panel.visible:
                        self.ui.admin_panel.handle_scroll(ev.y); continue

                if self.hayden_console.visible:
                    if ev.type == pygame.KEYDOWN:
                        self.hayden_console.handle_key(ev, self)
                    continue

                if self.console.visible:
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_F1: self.console.toggle()
                        else: self.console.handle_key(ev, self)
                    continue

                if self.paused:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        action = self.pause_menu.handle_click(ev.pos)
                        if action == "resume":
                            self.paused = False
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
                        u = self.ui.open_unit
                        cost = u.upgrade_cost()
                        if cost and self.money >= cost:
                            u.upgrade(); self.money -= cost
                            self._broadcast({"type": "upgrade", "uid": id(u), "level": u.level})
                        elif cost: self.ui.show_msg("Not enough money!")
                        else:      self.ui.show_msg("Max level!")
                    if ev.key == pygame.K_x and self.ui.open_unit:
                        u = self.ui.open_unit
                        sell_val = self.ui._sell_value(u)
                        self.units.remove(u); self.ui.open_unit = None
                        self.money += sell_val
                        self.ui.show_msg(f"Sold for {sell_val}")
                        self._broadcast({"type": "sell", "uid": id(u)})
                    slot_keys = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2, pygame.K_4:3, pygame.K_5:4}
                    if ev.key in slot_keys and not self.console.visible:
                        idx = slot_keys[ev.key]
                        UType = self.ui.SLOT_TYPES[idx]
                        if UType is None: self.ui.show_msg("Coming soon!")
                        elif self.money < UType.PLACE_COST: self.ui.show_msg("Not enough money!")
                        else:
                            mx2, my2 = pygame.mouse.get_pos()
                            self.ui.selected_slot = idx
                            self.ui.drag_unit = UType(mx2, my2)
                    self._hw_on_key(ev.key)

                if (self.game_over or self.win):
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        if self._end_btn.collidepoint(ev.pos):
                            self.running = False; self.return_to_menu = True
                            try: pygame.mixer.music.stop()
                            except: pass
                elif not self.game_over:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        if self._skip_wave_timer >= 3.0 and self._skip_wave_btn.collidepoint(ev.pos):
                            self._do_skip_wave(); continue
                        delta = self.ui.handle_click(ev.pos, self.units, self.money,
                                                     self.effects, self.enemies,
                                                     self.wave_mgr.wave, self.save_data, self.mode)
                        self.money += delta
                    if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                        old_count = len(self.units)
                        all_units_for_check = self.units + self._peer_units
                        delta = self.ui.handle_release(ev.pos, all_units_for_check, self.money)
                        new_in_combined = [u for u in all_units_for_check
                                           if u not in self.units and u not in self._peer_units]
                        for u in new_in_combined:
                            self.units.append(u)
                        self.money += delta
                        if new_in_combined:
                            u = new_in_combined[-1]
                            self._broadcast({
                                "type": "place_unit",
                                "name": _MP_UNIT_CLS_MAP.get(type(u), ""),
                                "x": u.px, "y": u.py,
                                "uid": id(u), "level": u.level,
                            })

            if not self.paused:
                if not self.game_over:
                    if self.is_host:
                        self.update(dt)
                        for u in self._peer_units:
                            try: u.update(dt, self.enemies, self.effects, 0)
                            except: pass
                        self._sync_timer += dt
                        if self._sync_timer >= self.SYNC_INTERVAL:
                            self._sync_timer = 0.0
                            self._push_enemy_state()
                    else:
                        self._elapsed += dt
                        self.console.update(dt)
                        for u in self._peer_units:
                            try: u.update(dt, self.enemies, self.effects, 0)
                            except: pass
                        for e in self.enemies:
                            e._bob = getattr(e, '_bob', 0.0) + dt * 4
                        pre_hp = {id(e): e.hp for e in self.enemies if e.alive}
                        for u in self.units:
                            u.update(dt, self.enemies, self.effects, self.money)
                        for u in self.units:
                            if isinstance(u, Lifestealer):
                                pm = getattr(u, '_pending_money', 0)
                                if pm > 0: self.money += pm; u._pending_money = 0
                        dmg_events = []
                        for e in self.enemies:
                            pre = pre_hp.get(id(e))
                            if pre is not None and e.hp < pre and hasattr(e, '_net_id'):
                                dealt = round(pre - e.hp, 2)
                                dmg_events.append({"id": e._net_id, "dmg": dealt, "killed": e.hp <= 0})
                                if e.hp <= 0 and not getattr(e, '_reward_paid', False):
                                    e._reward_paid = True
                                    reward = getattr(type(e), 'KILL_REWARD', 8)
                                    if reward > 0:
                                        self.money += reward
                                        self.effects.append(FloatingText(e.x, e.y - 20, f"+{reward}"))
                        if dmg_events:
                            self.net.send({"type": "damage", "hits": dmg_events})
                        # Periodically re-send own units to host so packet loss doesn't hide them
                        self._client_sync_timer += dt
                        if self._client_sync_timer >= 2.0:
                            self._client_sync_timer = 0.0
                            units_snapshot = []
                            for u in self.units:
                                uname = _MP_UNIT_CLS_MAP.get(type(u), "")
                                if uname:
                                    units_snapshot.append({"uid": id(u), "name": uname,
                                                           "x": u.px, "y": u.py, "level": u.level})
                            if units_snapshot:
                                self.net.send({"type": "client_units", "units": units_snapshot})
                        self.effects = [ef for ef in self.effects if ef.update(dt)]
                        self.ui.update(dt)

            # Ping every 3s to keep connection alive through NAT/firewall
            self._ping_timer += dt
            if self._ping_timer >= 3.0:
                self._ping_timer = 0.0
                self._broadcast({"type": "ping"})

            self.draw()
            self._draw_mp_overlay()
            if self.paused:
                self.pause_menu.draw(self._hayden_eligible)
            self.hayden_console.update(dt)
            self.hayden_console.draw(self.screen)
            pygame.display.flip()

        self._restore_enemy_hp()
        self.net.stop()
        if not self.return_to_menu:
            pygame.quit(); sys.exit()

    def _push_enemy_state(self):
        enemies_data = []
        for e in self.enemies:
            if not e.alive: continue
            if not hasattr(e, '_net_id'): e._net_id = id(e)
            # Round aggressively to minimize JSON size
            enemies_data.append({
                "id": e._net_id, "cls": type(e).__name__,
                "x": round(e.x, 0), "y": round(e.y, 0),
                "hp": round(e.hp, 0), "maxhp": round(e.maxhp, 0),
            })
        units_data = []
        for u in self.units:
            uname = _MP_UNIT_CLS_MAP.get(type(u), "")
            if uname:
                units_data.append({"uid": id(u), "name": uname,
                                    "x": u.px, "y": u.py, "level": u.level})
        # Also include known peer (client) units so client always has full picture
        peer_data = []
        for u in self._peer_units:
            uname = _MP_UNIT_CLS_MAP.get(type(u), "")
            if uname:
                peer_data.append({"uid": getattr(u, "_mp_uid", id(u)), "name": uname,
                                   "x": u.px, "y": u.py, "level": u.level})
        self._broadcast({
            "type": "state", "enemies": enemies_data,
            "wave": self.wave_mgr.wave, "wave_state": self.wave_mgr.state,
            "player_hp": self.player_hp, "game_over": self.game_over,
            "win": self.win, "units": units_data, "peer_units": peer_data,
        })

    def _handle_net_msg(self, msg):
        self._net_msg_count = getattr(self, '_net_msg_count', 0) + 1
        mtype = msg.get("type")

        if mtype == "start":
            _game_module._game_core.CURRENT_MAP = msg.get("map", "straight")
            self._waiting_start = False

        elif mtype == "place_unit":
            name = msg.get("name", "")
            cls  = _MP_UNIT_NAME_MAP.get(name)
            if cls:
                x, y  = msg.get("x", 0), msg.get("y", 0)
                level = msg.get("level", 0)
                u = cls(x, y)
                for _ in range(level):
                    try: u.upgrade()
                    except: pass
                u._mp_peer = True
                u._mp_uid  = msg.get("uid")
                self._peer_units.append(u)
                self._show_mp_msg(f"{self._peer_name} поставил {name}")

        elif mtype == "upgrade":
            uid   = msg.get("uid")
            level = msg.get("level", 0)
            for u in self._peer_units:
                if getattr(u, "_mp_uid", None) == uid:
                    while u.level < level:
                        try: u.upgrade()
                        except: break
                    break

        elif mtype == "sell":
            uid = msg.get("uid")
            self._peer_units = [u for u in self._peer_units
                                 if getattr(u, "_mp_uid", None) != uid]

        elif mtype == "state":
            if not self.is_host:
                self.player_hp = msg.get("player_hp", self.player_hp)
                self.game_over = msg.get("game_over", self.game_over)
                self.win       = msg.get("win", self.win)
                self.wave_mgr.wave  = msg.get("wave", self.wave_mgr.wave)
                self.wave_mgr.state = msg.get("wave_state", self.wave_mgr.state)

                incoming = msg.get("enemies", [])
                _name_to_cls = {c.__name__: c for c in [
                    Enemy, TankEnemy, ScoutEnemy, NormalBoss, HiddenEnemy,
                    BreakerEnemy, ArmoredEnemy, SlowBoss, HiddenBoss,
                    Necromancer, FastBoss, OtchimusPrime, GraveDigger,
                    AbnormalEnemy, QuickEnemy, SkeletonEnemy,
                    FallenDreg, FallenSquire, FallenSoul, FallenEnemy,
                    FallenGiant, FallenHazmat, PossessedArmorInner, PossessedArmor,
                    FallenNecromancer, CorruptedFallen, FallenJester,
                    NecroticSkeleton, FallenBreaker, FallenRusher,
                    FallenHonorGuard, FallenShield, FallenHero,
                    FallenKing, TrueFallenKing,
                ]}
                existing = {getattr(e, '_net_id', None): e for e in self.enemies}
                new_enemies = []
                for ed in incoming:
                    nid = ed.get("id")
                    cls = _name_to_cls.get(ed.get("cls", ""))
                    if cls is None: continue
                    e = existing.get(nid)
                    if e is None or type(e) != cls:
                        try:
                            e = cls(1); e._net_id = nid
                        except Exception:
                            try:
                                e = Enemy.__new__(cls); Enemy.__init__(e, 1); e._net_id = nid
                            except Exception: continue
                    e.x = ed["x"]; e.y = ed["y"]
                    e.hp = ed["hp"]; e.maxhp = ed["maxhp"]
                    e.alive = True; e._reward_paid = False
                    new_enemies.append(e)
                # Only replace enemy list if we got a non-empty update
                # (empty list could mean corrupted packet, not actually 0 enemies)
                if new_enemies or not self.enemies:
                    self.enemies = new_enemies

                incoming_units = msg.get("units", [])
                if incoming_units:
                    existing_peer = {getattr(u, "_mp_uid", None): u for u in self._peer_units}
                    for ud in incoming_units:
                        uid   = ud.get("uid"); name = ud.get("name", ""); level = ud.get("level", 0)
                        cls   = _MP_UNIT_NAME_MAP.get(name)
                        if cls is None: continue
                        u = existing_peer.get(uid)
                        if u is None:
                            u = cls(ud["x"], ud["y"])
                            u._mp_peer = True; u._mp_uid = uid
                            self._peer_units.append(u); existing_peer[uid] = u
                        while u.level < level:
                            try: u.upgrade()
                            except: break
                    active_uids = {ud.get("uid") for ud in incoming_units}
                    self._peer_units = [u for u in self._peer_units
                                        if getattr(u, "_mp_uid", None) in active_uids]
                # "peer_units" = host's echo of what client units the host sees
                # Useful for debugging, but we trust our own self.units list

                self._fallen_boss_bars = {}
                _bar_cls = (FallenGiant, FallenJester, FallenSquire,
                            FallenKing, FallenShield, FallenHonorGuard, TrueFallenKing)
                for e in self.enemies:
                    if not e.alive: continue
                    cls2 = type(e)
                    if cls2 in _bar_cls and cls2 not in self._fallen_boss_bars:
                        self._fallen_boss_bars[cls2] = e
                fk_alive = [e for e in self.enemies
                            if isinstance(e, FallenKing) and not isinstance(e, TrueFallenKing) and e.alive]
                if fk_alive:
                    self._fallen_boss_bars[FallenKing] = fk_alive[0]

        elif mtype == "wave_bonus":
            if not self.is_host:
                bonus = msg.get("amount", 0)
                if bonus > 0:
                    self.money += bonus
                    self.ui.show_msg(f"+{bonus} Wave bonus", 3.0)

        elif mtype == "farm_income":
            if not self.is_host:
                own_farms = [u for u in self.units if isinstance(u, Farm)]
                fi = sum(u.income for u in own_farms)
                if fi > 0:
                    self.money += fi
                    self.ui.show_msg(f"+{fi} Farm income", 2.5)

        elif mtype == "client_units":
            if self.is_host:
                # Client re-synced its units — update peer_units list
                incoming = msg.get("units", [])
                existing_peer = {getattr(u, "_mp_uid", None): u for u in self._peer_units}
                for ud in incoming:
                    uid   = ud.get("uid"); name = ud.get("name", ""); level = ud.get("level", 0)
                    cls   = _MP_UNIT_NAME_MAP.get(name)
                    if cls is None: continue
                    u = existing_peer.get(uid)
                    if u is None:
                        u = cls(ud["x"], ud["y"])
                        u._mp_peer = True; u._mp_uid = uid
                        self._peer_units.append(u); existing_peer[uid] = u
                    while u.level < level:
                        try: u.upgrade()
                        except: break
                active_uids = {ud.get("uid") for ud in incoming}
                self._peer_units = [u for u in self._peer_units
                                    if getattr(u, "_mp_uid", None) in active_uids]

        elif mtype == "damage":
            if self.is_host:
                net_id_map = {getattr(e, '_net_id', None): e for e in self.enemies if e.alive}
                for hit in msg.get("hits", []):
                    e = net_id_map.get(hit.get("id"))
                    if e and e.alive:
                        was_alive = e.alive
                        e.take_damage(hit.get("dmg", 0))
                        if was_alive and not e.alive and hit.get("killed") \
                                and not getattr(e, '_reward_paid', False):
                            e._reward_paid = True

        elif mtype == "ping": pass  # keepalive — no action needed
        elif mtype == "game_over": self.game_over = True
        elif mtype == "win":       self.win = True

    def _draw_mp_overlay(self):
        surf = self.screen
        for u in self._peer_units:
            try:
                cx, cy = int(u.px), int(u.py)
                ring = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(ring, (80,160,255,45),  (35,35), 32)
                pygame.draw.circle(ring, (100,200,255,170), (35,35), 32, 3)
                surf.blit(ring, (cx-35, cy-35))
                peer_label = "P1" if self.is_host else "P2"
                nf = pygame.font.SysFont("consolas", 11, bold=True)
                ns = nf.render(peer_label, True, (100,220,255))
                surf.blit(ns, ns.get_rect(center=(cx, cy-26)))
            except Exception:
                pass

        badge_x = SCREEN_W - 190
        badge_y = SCREEN_H - 225
        connected = self.net.client_connected if self.is_host else self.net.connected
        status_col = (60,200,80) if connected else (220,60,60)
        status_txt = (("● P2 онлайн" if connected else "● P2 офлайн") if self.is_host
                      else ("● Хост онлайн" if connected else "● Хост офлайн"))
        sf = pygame.font.SysFont("segoeui", 15, bold=True)
        rf = pygame.font.SysFont("consolas", 12)
        ss = sf.render(status_txt, True, status_col)
        role_txt = "HOST" if self.is_host else "CLIENT"
        rs = rf.render(role_txt, True, (160,160,80))
        msg_count = getattr(self, '_net_msg_count', 0)
        ms = rf.render(f"msgs: {msg_count}", True, (100,130,160))
        enemy_ct = rf.render(f"enemies: {len(self.enemies)}", True, (120,150,180))
        peer_ct  = rf.render(f"peer units: {len(self._peer_units)}", True, (120,150,180))
        all_rows = [ss, rs, ms, enemy_ct, peer_ct]
        pw = max(r.get_width() for r in all_rows) + 16
        ph = sum(r.get_height() for r in all_rows) + 10
        draw_rect_alpha(surf, (10,12,22), (badge_x-pw//2, badge_y, pw, ph), 200, 6)
        pygame.draw.rect(surf, status_col, (badge_x-pw//2, badge_y, pw, ph), 1, border_radius=6)
        cy3 = badge_y + 4
        for row in all_rows:
            surf.blit(row, row.get_rect(centerx=badge_x, top=cy3))
            cy3 += row.get_height() + 1

        if self._mp_msg_timer > 0:
            self._mp_msg_timer -= 1/FPS
            alpha = min(255, int(self._mp_msg_timer * 200))
            mf = pygame.font.SysFont("segoeui", 20, bold=True)
            ms = mf.render(self._mp_msg, True, (100,220,255))
            ms.set_alpha(max(0, alpha))
            surf.blit(ms, ms.get_rect(center=(SCREEN_W//2, SCREEN_H-195)))


# ── Entry point для мультиплеера — вызывается из game.py ─────────────────────
def run_multiplayer(screen, save_data):
    """
    Вызывается из game.py когда пользователь нажимает MULTIPLAYER.
    Возвращает обновлённый save_data.
    """
    import sys

    mp_choice = MultiplayerMenu(screen).run()
    if mp_choice == "back":
        return save_data

    if mp_choice == "host":
        server = MPServer()
        try:
            server.start(MP_PORT)
        except Exception as e:
            screen.fill(C_BG)
            ef = pygame.font.SysFont("segoeui", 28).render(
                f"Ошибка запуска сервера: {e}", True, (255, 80, 80))
            screen.blit(ef, ef.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
            pygame.display.flip()
            _time.sleep(3)
            return save_data

        wait = HostWaitScreen(screen, server)
        got_client = wait.run()
        if not got_client:
            server.stop()
            return save_data

        map_choice = MapSelectMenu(screen).run()
        if map_choice == "back":
            server.stop()
            return save_data

        _game_module._game_core.CURRENT_MAP = map_choice
        server.send_start(map_choice)
        _time.sleep(0.15)
        game = MultiplayerGame(save_data, is_host=True, net=server)
        game.run()
        save_data = load_save()
        if not game.return_to_menu:
            pygame.quit(); sys.exit()

    elif mp_choice == "join":
        result = JoinInputScreen(screen).run()
        if result is None:
            return save_data
        ip, port = result
        client = MPClient()

        screen.fill(C_BG)
        cf2 = pygame.font.SysFont("segoeui", 30).render(
            f"Подключаемся к {ip}:{port}...", True, (100, 200, 255))
        screen.blit(cf2, cf2.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
        pygame.display.flip()
        try:
            client.connect(ip, port)
        except Exception as e:
            screen.fill(C_BG)
            ef2 = pygame.font.SysFont("segoeui", 28).render(
                f"Ошибка подключения: {e}", True, (255, 80, 80))
            screen.blit(ef2, ef2.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
            pygame.display.flip()
            _time.sleep(3)
            return save_data

        map_result = [None]
        wait_done  = [False]
        def _do_wait():
            map_result[0] = client.wait_for_start(timeout=60)
            wait_done[0]  = True
        wt = threading.Thread(target=_do_wait, daemon=True)
        wt.start()

        clock_w = pygame.time.Clock()
        t_anim  = 0.0
        cancelled = False
        while not wait_done[0]:
            dt_w = clock_w.tick(60) / 1000.0
            t_anim += dt_w
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    cancelled = True; break
            if cancelled: break
            screen.fill(C_BG)
            cx_w = SCREEN_W // 2
            for i in range(12):
                a = math.radians(i * 30 + t_anim * 180)
                fade = (i / 12) * abs(math.sin(t_anim * 1.5))
                c = int(40 + fade * 180)
                px3 = int(cx_w + math.cos(a) * 55)
                py3 = int(SCREEN_H//2 - 60 + math.sin(a) * 55)
                pygame.draw.circle(screen, (min(255,c), min(255,c+40), min(255,c+80)), (px3,py3), 6)
            wf = pygame.font.SysFont("segoeui", 32, bold=True).render(
                "Подключено! Ждём хоста...", True, (100, 200, 255))
            screen.blit(wf, wf.get_rect(center=(cx_w, SCREEN_H//2 + 30)))
            hf = pygame.font.SysFont("segoeui", 20).render(
                f"Подключено к {ip}:{port}   •   ESC — отмена", True, (100,100,140))
            screen.blit(hf, hf.get_rect(center=(cx_w, SCREEN_H//2 + 75)))
            pygame.display.flip()

        if cancelled:
            client.stop()
            return save_data

        got_map = map_result[0]
        if got_map is None:
            client.stop()
            screen.fill(C_BG)
            tf2 = pygame.font.SysFont("segoeui", 28).render(
                "Хост не ответил — timeout (60s)", True, (255,80,80))
            screen.blit(tf2, tf2.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
            pygame.display.flip()
            _time.sleep(3)
            return save_data

        _game_module._game_core.CURRENT_MAP = got_map
        game = MultiplayerGame(save_data, is_host=False, net=client)
        game.run()
        save_data = load_save()
        if not game.return_to_menu:
            pygame.quit(); sys.exit()

    return save_data