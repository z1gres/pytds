"""
multiplayer.py  —  UDP multiplayer client for pyTDS
Server: when-jury.gl.at.ply.gg:33699  (tunnels to 127.0.0.1:8484)
"""
import pygame, math, random, socket, threading, queue, json, time, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import game_core as _gc
from game_core import (
    SCREEN_W, SCREEN_H, TILE, C_WHITE, C_BLACK, C_GOLD, C_BG,
    font_sm, font_md, font_lg, txt, draw_rect_alpha, load_icon, fmt_num,
    UNIT_LIMITS,
)

# ── Tunnel address ────────────────────────────────────────────────────────────
MP_HOST = "when-jury.gl.at.ply.gg"
MP_PORT = 33699
PING_INTERVAL = 2.0
STATE_INTERVAL = 0.1   # send game state 10 Hz
CURSOR_INTERVAL = 0.05 # send cursor 20 Hz
GLOBAL_UNIT_LIMIT_MP = 80  # doubled for 2 players

# ── UDP transport ─────────────────────────────────────────────────────────────
class UDPClient:
    def __init__(self):
        self.sock      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.0)
        self.server    = None
        self.in_q      = queue.Queue()
        self._running  = False
        self._send_q   = queue.Queue()

    def connect(self, host=MP_HOST, port=MP_PORT):
        import socket as _s
        addr = (_s.gethostbyname(host), port)
        self.server   = addr
        self._running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._send_loop, daemon=True).start()

    def send(self, data: dict):
        if self.server:
            self._send_q.put(data)

    def _recv_loop(self):
        self.sock.settimeout(0.5)
        while self._running:
            try:
                raw, _ = self.sock.recvfrom(65535)
                msg = json.loads(raw.decode())
                self.in_q.put(msg)
            except socket.timeout:
                pass
            except Exception:
                pass

    def _send_loop(self):
        while self._running:
            try:
                data = self._send_q.get(timeout=0.5)
                raw  = json.dumps(data, separators=(',', ':')).encode()
                self.sock.sendto(raw, self.server)
            except queue.Empty:
                pass
            except Exception:
                pass

    def stop(self):
        self._running = False
        try: self.sock.close()
        except: pass

    def poll(self):
        """Return all pending messages."""
        msgs = []
        while True:
            try:
                msgs.append(self.in_q.get_nowait())
            except queue.Empty:
                break
        return msgs

# ── Shared drawing helpers ────────────────────────────────────────────────────
def _draw_bg(surf):
    surf.fill((12, 14, 22))
    random.seed(7)
    for _ in range(120):
        sx = random.randint(0, SCREEN_W)
        sy = random.randint(0, SCREEN_H)
        pygame.draw.circle(surf, (30, 35, 55), (sx, sy), 1)
    random.seed()

def _btn(surf, rect, label, hov, accent=(60, 130, 220)):
    bg  = tuple(min(255, c + 30) for c in accent) if hov else tuple(c // 2 for c in accent)
    brd = tuple(min(255, c + 80) for c in accent) if hov else accent
    pygame.draw.rect(surf, bg,  rect, border_radius=10)
    pygame.draw.rect(surf, brd, rect, 2, border_radius=10)
    f = pygame.font.SysFont("segoeui", 22, bold=True)
    s = f.render(label, True, C_WHITE)
    surf.blit(s, s.get_rect(center=rect.center))

def _input_box(surf, rect, text, active, placeholder=""):
    brd = (80, 160, 255) if active else (50, 60, 90)
    draw_rect_alpha(surf, (18, 22, 38), (rect.x, rect.y, rect.w, rect.h), 220, 8)
    pygame.draw.rect(surf, brd, rect, 2, border_radius=8)
    disp = text if text else placeholder
    col  = C_WHITE if text else (70, 80, 110)
    cursor = "|" if (active and (pygame.time.get_ticks() // 500) % 2 == 0) else ""
    f = pygame.font.SysFont("consolas", 20, bold=True)
    s = f.render(disp + cursor, True, col)
    surf.blit(s, s.get_rect(midleft=(rect.x + 10, rect.centery)))

# ── NickScreen ────────────────────────────────────────────────────────────────
class NickScreen:
    """Ask player for their nickname before entering lobby."""
    def __init__(self, screen, save_data):
        self.screen    = screen
        self.save_data = save_data
        self.nick      = save_data.get("mp_nick", "")
        self.active    = True
        cx = SCREEN_W // 2
        self.box  = pygame.Rect(cx - 220, SCREEN_H // 2 - 30, 440, 52)
        self.btn_ok   = pygame.Rect(cx - 120, SCREEN_H // 2 + 50, 240, 50)
        self.btn_back = pygame.Rect(cx - 120, SCREEN_H // 2 + 115, 240, 44)
        self.error = ""

    def run(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return None
                    elif ev.key == pygame.K_RETURN:
                        r = self._confirm()
                        if r: return r
                    elif ev.key == pygame.K_BACKSPACE:
                        self.nick = self.nick[:-1]
                    elif ev.unicode and len(self.nick) < 20:
                        self.nick += ev.unicode
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_ok.collidepoint(ev.pos):
                        r = self._confirm()
                        if r: return r
                    if self.btn_back.collidepoint(ev.pos):
                        return None
            self._draw(mx, my)
            pygame.display.flip()

    def _confirm(self):
        n = self.nick.strip()
        if not n:
            self.error = "Enter a nickname!"; return None
        self.save_data["mp_nick"] = n
        from game_core import write_save
        write_save(self.save_data)
        return n

    def _draw(self, mx, my):
        _draw_bg(self.screen)
        cx = SCREEN_W // 2
        f = pygame.font.SysFont("consolas", 38, bold=True)
        s = f.render("ENTER NICKNAME", True, (100, 200, 255))
        self.screen.blit(s, s.get_rect(center=(cx, SCREEN_H // 2 - 110)))
        _input_box(self.screen, self.box, self.nick, True, "Your nickname...")
        _btn(self.screen, self.btn_ok,   "CONFIRM", self.btn_ok.collidepoint(mx, my),   (40, 160, 80))
        _btn(self.screen, self.btn_back, "← BACK",  self.btn_back.collidepoint(mx, my), (140, 40, 40))
        if self.error:
            ef = pygame.font.SysFont("segoeui", 20).render(self.error, True, (255, 80, 80))
            self.screen.blit(ef, ef.get_rect(center=(cx, SCREEN_H // 2 + 20)))

# ── LobbyScreen (room list + create) ─────────────────────────────────────────
class LobbyScreen:
    def __init__(self, screen, net: UDPClient, nick: str):
        self.screen  = screen
        self.net     = net
        self.nick    = nick
        self.rooms   = []
        self.t       = 0.0
        self.scroll  = 0
        self.error   = ""
        self.error_t = 0.0
        self._last_refresh = 0.0
        cx = SCREEN_W // 2
        self.btn_create = pygame.Rect(cx + 20,  60, 260, 50)
        self.btn_back   = pygame.Rect(cx - 280, 60, 200, 50)
        self.btn_refresh= pygame.Rect(cx - 60,  60, 70,  50)
        # Create-room popup state
        self._popup      = False
        self._pop_name   = ""
        self._pop_pass   = ""
        self._pop_map    = "straight"
        self._pop_mode   = "easy"
        self._pop_active = "name"
        self._pop_name_box = pygame.Rect(cx - 260, SCREEN_H//2 - 120, 520, 48)
        self._pop_pass_box = pygame.Rect(cx - 260, SCREEN_H//2 - 40,  520, 48)
        self._pop_btn_ok   = pygame.Rect(cx - 130, SCREEN_H//2 + 160, 260, 50)
        self._pop_btn_cancel = pygame.Rect(cx - 130, SCREEN_H//2 + 225, 260, 44)
        self._map_btns  = []
        self._mode_btns = []
        self._room_rects = []
        self._join_popup = None   # room dict being joined (password prompt)
        self._join_pass  = ""
        self._join_pass_box = pygame.Rect(cx - 200, SCREEN_H//2 - 20, 400, 48)
        self._join_btn_ok = pygame.Rect(cx - 120, SCREEN_H//2 + 60, 240, 50)
        self._join_btn_cancel = pygame.Rect(cx - 120, SCREEN_H//2 + 125, 240, 44)
        self.result = None   # ("created", room_id) | ("joined", room_id, is_host, host_nick, map, mode)

    def run(self):
        clock = pygame.time.Clock()
        self._request_refresh()
        while self.result is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self.error_t > 0: self.error_t -= dt
            if self.t - self._last_refresh > 1.5:
                self._request_refresh()
            self._process_net()
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    self._on_key(ev)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._on_click(ev.pos, mx, my)
                if ev.type == pygame.MOUSEWHEEL:
                    self.scroll = max(0, self.scroll - ev.y * 40)
            self._draw(mx, my)
            pygame.display.flip()
        return self.result

    def _request_refresh(self):
        # Send 3x to fight UDP loss
        for _ in range(3):
            self.net.send({"type": "list_rooms"})
        self._last_refresh = self.t

    def _process_net(self):
        for msg in self.net.poll():
            t = msg.get("type")
            if t == "room_list":
                self.rooms = msg.get("rooms", [])
            elif t == "room_created":
                self.result = ("created", msg["room_id"])
            elif t == "room_joined":
                self.result = ("joined", msg["room_id"], msg.get("is_host", False),
                               msg.get("host_nick", ""), msg.get("map", "straight"),
                               msg.get("mode", "easy"))
            elif t == "error":
                self.error   = msg.get("msg", "Error")
                self.error_t = 3.0

    def _on_key(self, ev):
        if ev.key == pygame.K_ESCAPE:
            if self._popup:      self._popup = False
            elif self._join_popup: self._join_popup = None
            else:                self.result = ("back",)
            return
        if self._popup:
            if ev.key == pygame.K_TAB:
                self._pop_active = "pass" if self._pop_active == "name" else "name"
            elif ev.key == pygame.K_RETURN:
                self._do_create()
            elif ev.key == pygame.K_BACKSPACE:
                if self._pop_active == "name": self._pop_name = self._pop_name[:-1]
                else:                          self._pop_pass = self._pop_pass[:-1]
            elif ev.unicode:
                if self._pop_active == "name" and len(self._pop_name) < 40:
                    self._pop_name += ev.unicode
                elif self._pop_active == "pass" and len(self._pop_pass) < 20:
                    self._pop_pass += ev.unicode
        elif self._join_popup:
            if ev.key == pygame.K_RETURN:
                self._do_join(self._join_popup, self._join_pass)
            elif ev.key == pygame.K_BACKSPACE:
                self._join_pass = self._join_pass[:-1]
            elif ev.unicode and len(self._join_pass) < 20:
                self._join_pass += ev.unicode

    def _on_click(self, pos, mx, my):
        if self._join_popup:
            if self._join_btn_ok.collidepoint(pos):
                self._do_join(self._join_popup, self._join_pass)
            if self._join_btn_cancel.collidepoint(pos):
                self._join_popup = None; self._join_pass = ""
            if self._join_pass_box.collidepoint(pos): pass
            return
        if self._popup:
            if self._pop_name_box.collidepoint(pos): self._pop_active = "name"
            elif self._pop_pass_box.collidepoint(pos): self._pop_active = "pass"
            for r, m in self._map_btns:
                if r.collidepoint(pos): self._pop_map = m
            for r, m in self._mode_btns:
                if r.collidepoint(pos): self._pop_mode = m
            if self._pop_btn_ok.collidepoint(pos):     self._do_create()
            if self._pop_btn_cancel.collidepoint(pos): self._popup = False
            return
        if self.btn_back.collidepoint(pos):
            self.result = ("back",); return
        if self.btn_create.collidepoint(pos):
            self._popup = True; self._pop_name = f"{self.nick}'s Room"; return
        if self.btn_refresh.collidepoint(pos):
            self._request_refresh(); return
        for r, room in self._room_rects:
            if r.collidepoint(pos):
                if room.get("public", True):
                    self._do_join(room, "")
                else:
                    self._join_popup = room; self._join_pass = ""
                return

    def _do_create(self):
        name = self._pop_name.strip() or f"{self.nick}'s Room"
        self.net.send({"type": "create_room", "nick": self.nick,
                       "name": name, "password": self._pop_pass,
                       "map": self._pop_map, "mode": self._pop_mode})
        self._popup = False

    def _do_join(self, room, password):
        self.net.send({"type": "join_room", "nick": self.nick,
                       "room_id": room["id"], "password": password})

    def _draw(self, mx, my):
        surf = self.screen
        _draw_bg(surf)
        cx = SCREEN_W // 2
        f_title = pygame.font.SysFont("consolas", 36, bold=True)
        ts = f_title.render("MULTIPLAYER LOBBY", True, (100, 200, 255))
        surf.blit(ts, ts.get_rect(center=(cx, 32)))
        _btn(surf, self.btn_back,    "← BACK",   self.btn_back.collidepoint(mx, my),    (140, 40, 40))
        _btn(surf, self.btn_refresh, "⟳",        self.btn_refresh.collidepoint(mx, my), (40, 80, 140))
        _btn(surf, self.btn_create,  "+ CREATE ROOM", self.btn_create.collidepoint(mx, my), (40, 140, 60))
        # Server address hint
        hint_f = pygame.font.SysFont("segoeui", 14)
        hint_s = hint_f.render(f"Server: {MP_HOST}:{MP_PORT}", True, (60, 80, 120))
        surf.blit(hint_s, (10, SCREEN_H - 22))
        # Error
        if self.error_t > 0:
            ef = pygame.font.SysFont("segoeui", 22).render(self.error, True, (255, 80, 80))
            surf.blit(ef, ef.get_rect(center=(cx, 125)))
        # Room list
        list_top = 130; row_h = 72; list_w = 900
        list_x = cx - list_w // 2
        self._room_rects = []
        surf.set_clip(pygame.Rect(list_x - 4, list_top, list_w + 8, SCREEN_H - list_top - 20))
        if not self.rooms:
            nf = pygame.font.SysFont("segoeui", 26)
            ns = nf.render("No rooms found. Create one!", True, (80, 90, 120))
            surf.blit(ns, ns.get_rect(center=(cx, list_top + 80)))
        for i, room in enumerate(self.rooms):
            ry = list_top + i * (row_h + 8) - self.scroll
            r  = pygame.Rect(list_x, ry, list_w, row_h)
            self._room_rects.append((r, room))
            if ry + row_h < list_top or ry > SCREEN_H: continue
            hov = r.collidepoint(mx, my)
            state_col = (40, 80, 40) if room["state"] == "lobby" else (80, 40, 10)
            bg = tuple(min(255, c + 20) for c in state_col) if hov else state_col
            draw_rect_alpha(surf, bg, (r.x, r.y, r.w, r.h), 220, 10)
            brd = (80, 200, 100) if hov else (50, 100, 60)
            pygame.draw.rect(surf, brd, r, 2, border_radius=10)
            # Room name
            nf2 = pygame.font.SysFont("segoeui", 22, bold=True)
            ns2 = nf2.render(room["name"], True, C_WHITE)
            surf.blit(ns2, (r.x + 16, r.y + 8))
            # Host + crown
            hf = pygame.font.SysFont("segoeui", 17)
            hs = hf.render(f"👑 {room['host']}", True, (220, 180, 60))
            surf.blit(hs, (r.x + 16, r.y + 36))
            # Players / map / mode
            info_str = f"{room['players']}/{room['max']} players  •  {room['map']}  •  {room['mode']}"
            inf = hf.render(info_str, True, (140, 160, 200))
            surf.blit(inf, (r.x + 200, r.y + 36))
            # Lock icon
            if not room.get("public", True):
                lf2 = pygame.font.SysFont("segoeui", 20)
                ls2 = lf2.render("🔒", True, (220, 180, 60))
                surf.blit(ls2, (r.right - 50, r.y + 22))
            # State badge
            badge_col = (40, 180, 80) if room["state"] == "lobby" else (200, 100, 20)
            badge_txt = "OPEN" if room["state"] == "lobby" else "IN GAME"
            bf2 = pygame.font.SysFont("segoeui", 14, bold=True)
            bs2 = bf2.render(badge_txt, True, badge_col)
            surf.blit(bs2, (r.right - 90, r.y + 8))
        surf.set_clip(None)
        # Popups
        if self._popup:   self._draw_create_popup(surf, mx, my)
        if self._join_popup: self._draw_join_popup(surf, mx, my)

    def _draw_create_popup(self, surf, mx, my):
        cx = SCREEN_W // 2
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        pw, ph = 560, 520
        pr = pygame.Rect(cx - pw//2, SCREEN_H//2 - ph//2, pw, ph)
        draw_rect_alpha(surf, (14, 18, 30), (pr.x, pr.y, pr.w, pr.h), 245, 14)
        pygame.draw.rect(surf, (60, 100, 180), pr, 2, border_radius=14)
        tf = pygame.font.SysFont("consolas", 26, bold=True)
        ts = tf.render("CREATE ROOM", True, (120, 200, 255))
        surf.blit(ts, ts.get_rect(center=(cx, pr.y + 28)))
        lf = pygame.font.SysFont("segoeui", 18)
        surf.blit(lf.render("Room name:", True, (160, 170, 200)), (pr.x + 20, self._pop_name_box.y - 22))
        _input_box(surf, self._pop_name_box, self._pop_name, self._pop_active == "name", "My Room")
        surf.blit(lf.render("Password (leave blank = public):", True, (160, 170, 200)),
                  (pr.x + 20, self._pop_pass_box.y - 22))
        _input_box(surf, self._pop_pass_box, self._pop_pass, self._pop_active == "pass", "No password")
        # Map selector
        maps = [("straight","The Bridge"), ("zigzag","S-Turn"), ("uturn","U-Turn"), ("labyrinth","Labyrinth")]
        bw2 = (pw - 40) // len(maps); by2 = self._pop_pass_box.bottom + 28
        surf.blit(lf.render("Map:", True, (160, 170, 200)), (pr.x + 20, by2 - 20))
        self._map_btns = []
        for i, (mk, ml) in enumerate(maps):
            r2 = pygame.Rect(pr.x + 20 + i * (bw2 + 4), by2, bw2, 38)
            self._map_btns.append((r2, mk))
            sel = self._pop_map == mk
            bg2 = (30, 80, 160) if sel else ((20, 50, 100) if r2.collidepoint(mx, my) else (15, 30, 60))
            brd2 = (80, 160, 255) if sel else (40, 70, 120)
            pygame.draw.rect(surf, bg2, r2, border_radius=8)
            pygame.draw.rect(surf, brd2, r2, 2, border_radius=8)
            ms = pygame.font.SysFont("segoeui", 14, bold=sel).render(ml, True, C_WHITE)
            surf.blit(ms, ms.get_rect(center=r2.center))
        # Mode selector
        modes = [("easy","Easy"), ("fallen","Fallen"), ("frosty","Frosty"), ("sandbox","Sandbox")]
        by3 = by2 + 60
        surf.blit(lf.render("Mode:", True, (160, 170, 200)), (pr.x + 20, by3 - 20))
        self._mode_btns = []
        for i, (mk, ml) in enumerate(modes):
            r3 = pygame.Rect(pr.x + 20 + i * (bw2 + 4), by3, bw2, 38)
            self._mode_btns.append((r3, mk))
            sel = self._pop_mode == mk
            bg3 = (80, 30, 160) if sel else ((50, 20, 100) if r3.collidepoint(mx, my) else (30, 15, 60))
            brd3 = (180, 80, 255) if sel else (80, 40, 120)
            pygame.draw.rect(surf, bg3, r3, border_radius=8)
            pygame.draw.rect(surf, brd3, r3, 2, border_radius=8)
            ms2 = pygame.font.SysFont("segoeui", 14, bold=sel).render(ml, True, C_WHITE)
            surf.blit(ms2, ms2.get_rect(center=r3.center))
        _btn(surf, self._pop_btn_ok,     "CREATE",   self._pop_btn_ok.collidepoint(mx, my),     (40, 160, 60))
        _btn(surf, self._pop_btn_cancel, "CANCEL",   self._pop_btn_cancel.collidepoint(mx, my), (140, 40, 40))

    def _draw_join_popup(self, surf, mx, my):
        cx = SCREEN_W // 2
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        pw, ph = 460, 260
        pr = pygame.Rect(cx - pw//2, SCREEN_H//2 - ph//2, pw, ph)
        draw_rect_alpha(surf, (14, 18, 30), (pr.x, pr.y, pr.w, pr.h), 245, 14)
        pygame.draw.rect(surf, (180, 120, 20), pr, 2, border_radius=14)
        tf = pygame.font.SysFont("consolas", 24, bold=True)
        ts = tf.render(f"🔒  {self._join_popup['name']}", True, (220, 180, 60))
        surf.blit(ts, ts.get_rect(center=(cx, pr.y + 28)))
        lf = pygame.font.SysFont("segoeui", 18)
        surf.blit(lf.render("Enter password:", True, (160, 170, 200)),
                  (self._join_pass_box.x, self._join_pass_box.y - 22))
        _input_box(surf, self._join_pass_box, self._join_pass, True, "Password...")
        _btn(surf, self._join_btn_ok,     "JOIN",   self._join_btn_ok.collidepoint(mx, my),     (40, 140, 60))
        _btn(surf, self._join_btn_cancel, "CANCEL", self._join_btn_cancel.collidepoint(mx, my), (140, 40, 40))

# ── WaitRoomScreen (ждём второго игрока) ─────────────────────────────────────
class WaitRoomScreen:
    def __init__(self, screen, net: UDPClient, nick: str, room_id: str,
                 is_host: bool, host_nick: str, map_name: str, mode: str):
        self.screen    = screen
        self.net       = net
        self.nick      = nick
        self.room_id   = room_id
        self.is_host   = is_host
        self.host_nick = host_nick
        self.map_name  = map_name
        self.mode      = mode
        self.t         = 0.0
        self.players   = [nick]   # list of nicks in room
        self.error     = ""
        self.result    = None     # "start" | "back"
        cx = SCREEN_W // 2
        self.btn_start  = pygame.Rect(cx - 160, SCREEN_H - 160, 320, 56)
        self.btn_leave  = pygame.Rect(cx - 120, SCREEN_H - 90,  240, 44)
        # Map/mode selectors (host only)
        maps  = ["straight","zigzag","uturn","labyrinth"]
        modes = ["easy","fallen","frosty","sandbox"]
        bw = 160; bh = 40; gap = 10
        total_w = len(maps) * bw + (len(maps)-1) * gap
        self._map_rects  = [(pygame.Rect(cx - total_w//2 + i*(bw+gap), SCREEN_H//2 + 20, bw, bh), m)
                            for i, m in enumerate(maps)]
        total_w2 = len(modes) * bw + (len(modes)-1) * gap
        self._mode_rects = [(pygame.Rect(cx - total_w2//2 + i*(bw+gap), SCREEN_H//2 + 80, bw, bh), m)
                            for i, m in enumerate(modes)]

    def run(self):
        clock = pygame.time.Clock()
        while self.result is None:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            self._process_net()
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self._leave(); return "back"
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self._on_click(ev.pos)
            self._draw(mx, my)
            pygame.display.flip()
        return self.result

    def _process_net(self):
        for msg in self.net.poll():
            t = msg.get("type")
            if t == "player_joined":
                nick = msg.get("nick","?")
                if nick not in self.players:
                    self.players.append(nick)
            elif t == "player_left":
                nick = msg.get("nick","?")
                if nick in self.players:
                    self.players.remove(nick)
            elif t == "game_start":
                self.map_name = msg.get("map", self.map_name)
                self.mode     = msg.get("mode", self.mode)
                self.result   = "start"
            elif t == "promoted_host":
                self.is_host   = True
                self.host_nick = self.nick
            elif t == "error":
                self.error = msg.get("msg","")

    def _on_click(self, pos):
        if self.btn_leave.collidepoint(pos):
            self._leave(); self.result = "back"; return
        if self.is_host:
            for r, m in self._map_rects:
                if r.collidepoint(pos): self.map_name = m
            for r, m in self._mode_rects:
                if r.collidepoint(pos): self.mode = m
            if self.btn_start.collidepoint(pos):
                if len(self.players) < 2:
                    self.error = "Need 2 players to start!"; return
                self.net.send({"type":"start_game","map":self.map_name,"mode":self.mode})

    def _leave(self):
        self.net.send({"type":"leave_room"})

    def _draw(self, mx, my):
        surf = self.screen
        _draw_bg(surf)
        cx = SCREEN_W // 2
        f = pygame.font.SysFont("consolas", 32, bold=True)
        surf.blit(f.render("WAITING FOR PLAYERS", True, (100,200,255)),
                  f.render("WAITING FOR PLAYERS", True, (100,200,255)).get_rect(center=(cx, 40)))
        # Room ID badge
        rid_f = pygame.font.SysFont("consolas", 20)
        rid_s = rid_f.render(f"Room: {self.room_id}", True, (80,120,180))
        surf.blit(rid_s, rid_s.get_rect(center=(cx, 80)))
        # Players list
        py = 130
        for i, pnick in enumerate(self.players):
            is_h = (pnick == self.host_nick)
            col  = (220,180,60) if is_h else (160,200,255)
            crown = "👑 " if is_h else "   "
            pf = pygame.font.SysFont("segoeui", 26, bold=True)
            ps = pf.render(f"{crown}{pnick}", True, col)
            surf.blit(ps, ps.get_rect(center=(cx, py + i*44)))
        if len(self.players) < 2:
            wf = pygame.font.SysFont("segoeui", 20)
            ws = wf.render("Waiting for second player...", True, (80,100,140))
            surf.blit(ws, ws.get_rect(center=(cx, py + 100)))
        # Map/mode selectors (host only)
        if self.is_host:
            lf = pygame.font.SysFont("segoeui", 18)
            surf.blit(lf.render("Map:", True, (140,160,200)), (cx - 340, SCREEN_H//2 - 4))
            for r, m in self._map_rects:
                sel = self.map_name == m
                bg  = (30,80,160) if sel else ((20,50,100) if r.collidepoint(mx,my) else (12,25,50))
                brd = (80,160,255) if sel else (40,70,120)
                pygame.draw.rect(surf, bg, r, border_radius=8)
                pygame.draw.rect(surf, brd, r, 2, border_radius=8)
                ms = pygame.font.SysFont("segoeui", 15, bold=sel).render(m, True, C_WHITE)
                surf.blit(ms, ms.get_rect(center=r.center))
            surf.blit(lf.render("Mode:", True, (140,160,200)), (cx - 340, SCREEN_H//2 + 56))
            for r, m in self._mode_rects:
                sel = self.mode == m
                bg  = (80,30,160) if sel else ((50,20,100) if r.collidepoint(mx,my) else (30,12,60))
                brd = (180,80,255) if sel else (80,40,120)
                pygame.draw.rect(surf, bg, r, border_radius=8)
                pygame.draw.rect(surf, brd, r, 2, border_radius=8)
                ms2 = pygame.font.SysFont("segoeui", 15, bold=sel).render(m, True, C_WHITE)
                surf.blit(ms2, ms2.get_rect(center=r.center))
            # Start button
            can_start = len(self.players) >= 2
            acc = (40,160,60) if can_start else (40,60,40)
            _btn(surf, self.btn_start, "▶  START GAME", self.btn_start.collidepoint(mx,my), acc)
        else:
            wf2 = pygame.font.SysFont("segoeui", 22)
            ws2 = wf2.render("Waiting for host to start...", True, (80,120,160))
            surf.blit(ws2, ws2.get_rect(center=(cx, SCREEN_H - 160)))
        _btn(surf, self.btn_leave, "← LEAVE", self.btn_leave.collidepoint(mx,my), (140,40,40))
        if self.error:
            ef = pygame.font.SysFont("segoeui", 20).render(self.error, True, (255,80,80))
            surf.blit(ef, ef.get_rect(center=(cx, SCREEN_H - 200)))

# ── Leaderboard overlay ───────────────────────────────────────────────────────
class Leaderboard:
    """Top-right HUD showing both players: nick, money, units/limit."""
    W, H = 280, 130

    def draw(self, surf, my_nick, my_money, my_units, my_limit,
             peer_nick, peer_money, peer_units, peer_limit,
             host_nick, t):
        x = SCREEN_W - self.W - 8
        y = 8
        draw_rect_alpha(surf, (10,12,22), (x, y, self.W, self.H), 210, 10)
        pygame.draw.rect(surf, (50,70,120), (x, y, self.W, self.H), 2, border_radius=10)
        # Title
        tf = pygame.font.SysFont("segoeui", 14, bold=True)
        ts = tf.render("LEADERBOARD", True, (80,120,200))
        surf.blit(ts, ts.get_rect(centerx=x + self.W//2, top=y+6))
        # Rows
        rows = [
            (my_nick,   my_money,   my_units,   my_limit),
            (peer_nick, peer_money, peer_units, peer_limit),
        ]
        for i, (nick, money, units, limit) in enumerate(rows):
            ry = y + 30 + i * 46
            is_host = (nick == host_nick)
            # Crown for host
            crown = "👑 " if is_host else "   "
            nf = pygame.font.SysFont("segoeui", 17, bold=True)
            col = (220,180,60) if is_host else (160,210,255)
            ns = nf.render(f"{crown}{nick}", True, col)
            surf.blit(ns, (x+10, ry))
            # Money
            mf = pygame.font.SysFont("segoeui", 15)
            ms = mf.render(f"${fmt_num(money)}", True, (200,200,80))
            surf.blit(ms, (x+10, ry+20))
            # Units bar
            bar_x = x + 120; bar_y = ry + 22; bar_w = 140; bar_h = 12
            pygame.draw.rect(surf, (30,35,55), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            if limit > 0:
                fill = int(bar_w * min(1.0, units / limit))
                frac = units / limit
                fc = (int(60+frac*180), int(200-frac*140), 60)
                pygame.draw.rect(surf, fc, (bar_x, bar_y, fill, bar_h), border_radius=4)
            pygame.draw.rect(surf, (60,70,100), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)
            uf = pygame.font.SysFont("segoeui", 13)
            us = uf.render(f"{units}/{limit}", True, (160,170,200))
            surf.blit(us, (bar_x + bar_w + 4, bar_y - 1))

# ── PeerCursor ────────────────────────────────────────────────────────────────
class PeerCursor:
    """Draws the remote player's cursor with their nick above it."""
    def __init__(self, nick: str):
        self.nick = nick
        self.x    = 0.0
        self.y    = 0.0
        self._tx  = 0.0   # lerp target
        self._ty  = 0.0
        self.visible = False

    def update(self, tx, ty):
        self._tx = tx; self._ty = ty
        self.visible = True

    def tick(self, dt):
        spd = min(1.0, dt * 25)
        self.x += (self._tx - self.x) * spd
        self.y += (self._ty - self.y) * spd

    def draw(self, surf):
        if not self.visible: return
        cx, cy = int(self.x), int(self.y)
        # Arrow cursor shape
        pts = [(cx,cy),(cx+14,cy+10),(cx+8,cy+10),(cx+10,cy+18),(cx+6,cy+18),(cx+4,cy+10),(cx,cy+14)]
        pygame.draw.polygon(surf, (220,220,255), pts)
        pygame.draw.polygon(surf, (60,100,200), pts, 2)
        # Nick label
        nf = pygame.font.SysFont("segoeui", 15, bold=True)
        ns = nf.render(self.nick, True, (220,220,255))
        bg_r = pygame.Rect(cx + 16, cy - 4, ns.get_width()+8, ns.get_height()+4)
        draw_rect_alpha(surf, (10,12,28), (bg_r.x, bg_r.y, bg_r.w, bg_r.h), 180, 4)
        surf.blit(ns, (bg_r.x+4, bg_r.y+2))

# ── Unit name <-> class mapping (built lazily) ────────────────────────────────
_UNIT_MAP = None

def _get_unit_map():
    global _UNIT_MAP
    if _UNIT_MAP is not None:
        return _UNIT_MAP
    try:
        import units as _u
        _UNIT_MAP = {}
        for attr in dir(_u):
            cls = getattr(_u, attr)
            try:
                if isinstance(cls, type) and issubclass(cls, _u.Unit) and cls is not _u.Unit:
                    _UNIT_MAP[getattr(cls, 'NAME', attr)] = cls
            except Exception:
                pass
    except Exception:
        _UNIT_MAP = {}
    return _UNIT_MAP

def _unit_to_dict(u) -> dict:
    return {
        "type":  "place_unit",
        "name":  getattr(u, 'NAME', type(u).__name__),
        "x":     u.px,
        "y":     u.py,
        "level": u.level,
        "uid":   id(u),
        "target_mode": getattr(u, 'target_mode', 'First'),
    }

def _dict_to_unit(d):
    umap = _get_unit_map()
    cls  = umap.get(d.get("name"))
    if cls is None:
        return None
    try:
        u = cls(d["x"], d["y"])
        lvl = d.get("level", 0)
        for _ in range(lvl):
            u.upgrade()
        u.target_mode = d.get("target_mode", "First")
        u._mp_peer    = True   # mark as peer-owned
        u._mp_uid     = d.get("uid", id(u))
        return u
    except Exception:
        return None

# ── MultiplayerGame (subclass of Game) ───────────────────────────────────────
# Imported lazily so we don't pull in all of game.py at module load time.

class _MPGameFactory:
    """Builds a MultiplayerGame class once Game is available."""
    _cls = None

    @classmethod
    def get(cls, game_mod):
        if cls._cls is not None:
            return cls._cls

        Game = game_mod.Game

        class MultiplayerGame(Game):
            """
            Subclass of Game that:
              - doubles unit limits
              - syncs cursor / state / unit events over UDP
              - draws peer cursor + leaderboard via _mp_overlay_hook()
              - keeps peer units in self._peer_units (Game.draw() already renders them)
            """
            def __init__(self, save_data, net, nick, is_host,
                         host_nick, map_name, mode):
                # Patch limits before super().__init__ spawns the UI
                self._orig_limits = dict(UNIT_LIMITS)
                for k in list(UNIT_LIMITS.keys()):
                    UNIT_LIMITS[k] = (UNIT_LIMITS[k] or 5) * 2
                game_mod.GLOBAL_UNIT_LIMIT = GLOBAL_UNIT_LIMIT_MP

                import game_core as _gc2
                _gc2.CURRENT_MAP = map_name

                super().__init__(save_data, mode=mode)

                self.net       = net
                self.nick      = nick
                self.is_host   = is_host
                self.host_nick = host_nick

                # Peer state
                self._peer_units    = []
                self._peer_uid_map  = {}
                self.peer_cursor    = PeerCursor("?")
                self.leaderboard    = Leaderboard()

                # Timers
                self._cursor_t = 0.0
                self._state_t  = 0.0
                self._ping_t   = 0.0

                # Peer HUD data
                self._peer_nick         = ""
                self._peer_money        = 0
                self._peer_units_placed = 0
                self._peer_unit_limit   = GLOBAL_UNIT_LIMIT_MP

                # Track which own units we've already broadcast
                self._sent_unit_ids = set()
                # Chat
                self._chat_log      = []   # list of (nick, text, ticks)
                self._chat_open     = False
                self._chat_input    = ""
                self._chat_scroll   = 0
                self._last_speed_idx = 2   # track speed changes to broadcast

            # ── Called every frame just before pygame.display.flip() ──────────
            def _mp_overlay_hook(self):
                self._cursor_t += 1/60.0
                self._state_t  += 1/60.0
                self._ping_t   += 1/60.0

                # Send cursor
                if self._cursor_t >= CURSOR_INTERVAL:
                    self._cursor_t = 0.0
                    mx, my = pygame.mouse.get_pos()
                    self.net.send({"type": "cursor", "x": mx, "y": my})

                # Send game state
                if self._state_t >= STATE_INTERVAL:
                    self._state_t = 0.0
                    own = [u for u in self.units if not getattr(u, '_mp_peer', False)]
                    self.net.send({
                        "type":         "game_state",
                        "money":        self.money,
                        "units_placed": len(own),
                        "unit_limit":   GLOBAL_UNIT_LIMIT_MP,
                    })
                    # Broadcast any newly placed own units
                    for u in own:
                        uid = id(u)
                        if uid not in self._sent_unit_ids:
                            self._sent_unit_ids.add(uid)
                            d = _unit_to_dict(u)
                            d["uid"] = uid
                            self.net.send(d)

                # Ping
                if self._ping_t >= PING_INTERVAL:
                    self._ping_t = 0.0
                    self.net.send({"type": "ping"})

                # Process incoming messages
                self._process_net()

                # Tick peer cursor interpolation
                self.peer_cursor.tick(1/60.0)

                # Draw peer cursor
                self.peer_cursor.draw(self.screen)

                # Broadcast speed change
                cur_spd = self.ui._speed_idx
                if cur_spd != self._last_speed_idx:
                    self._last_speed_idx = cur_spd
                    self.net.send({"type": "speed_sync", "idx": cur_spd})

                # Draw leaderboard
                own2 = [u for u in self.units if not getattr(u, '_mp_peer', False)]
                self.leaderboard.draw(
                    self.screen,
                    self.nick,
                    self.money,
                    len(own2),
                    GLOBAL_UNIT_LIMIT_MP,
                    self._peer_nick or self.peer_cursor.nick,
                    self._peer_money,
                    self._peer_units_placed,
                    self._peer_unit_limit,
                    self.host_nick,
                    self._elapsed,
                )

                # Draw chat overlay
                _draw_chat_overlay(self.screen, self._chat_log, self._chat_open, self._chat_input)

            def _process_net(self):
                for msg in self.net.poll():
                    t = msg.get("type")
                    if t == "peer_cursor":
                        self.peer_cursor.nick = msg.get("nick", "?")
                        self.peer_cursor.update(msg.get("x", 0), msg.get("y", 0))

                    elif t == "peer_state":
                        self._peer_nick         = msg.get("nick", "?")
                        self._peer_money        = msg.get("money", 0)
                        self._peer_units_placed = msg.get("units_placed", 0)
                        self._peer_unit_limit   = msg.get("unit_limit", GLOBAL_UNIT_LIMIT_MP)
                        if self.peer_cursor.nick == "?":
                            self.peer_cursor.nick = self._peer_nick

                    elif t == "place_unit":
                        u = _dict_to_unit(msg)
                        if u is not None:
                            uid = msg.get("uid", id(u))
                            u._mp_uid = uid
                            self._peer_uid_map[uid] = u
                            self._peer_units.append(u)
                            self.units.append(u)   # add to main list so game updates it

                    elif t == "sell_unit":
                        uid = msg.get("uid")
                        u   = self._peer_uid_map.pop(uid, None)
                        if u:
                            if u in self._peer_units: self._peer_units.remove(u)
                            if u in self.units:       self.units.remove(u)

                    elif t == "upgrade_unit":
                        uid = msg.get("uid")
                        u   = self._peer_uid_map.get(uid)
                        if u:
                            target = msg.get("level", u.level + 1)
                            while u.level < target:
                                u.upgrade()

                    elif t == "wave_event":
                        if not self.is_host:
                            if msg.get("event") == "next_wave":
                                try: self.wave_mgr.force_next_wave()
                                except Exception: pass

                    elif t == "game_over":
                        self.running = False

                    elif t == "player_left":
                        _left_nick = msg.get('nick','?')
                        self._chat_log.append(("SYSTEM", f"{_left_nick} left the game", pygame.time.get_ticks()))
                        self.ui.show_msg(f"{_left_nick} disconnected!", 5.0)
                        self.peer_cursor.visible = False

                    elif t == "chat":
                        _cn = msg.get('nick','?')
                        _ct = msg.get('text','')
                        self._chat_log.append((_cn, _ct, pygame.time.get_ticks()))
                        self.ui.show_msg(f"[{_cn}]: {_ct}", 4.0)

                    elif t == "speed_sync":
                        _idx = msg.get("idx", 2)
                        self.ui._speed_idx = max(0, min(_idx, len(self.ui._SPEED_STEPS)-1))

            def run(self):
                """Override: pump chat events before parent run() sees them."""
                # We use a pre-event hook: _mp_overlay_hook fires every frame
                # just before flip() inside the parent run() loop.
                # For chat we need to intercept KEYDOWN events.
                # Strategy: monkey-patch pygame.event.get() for the duration of this run.
                import pygame as _pg
                _orig_get = _pg.event.get

                mp_self = self  # capture for closure

                def _filtered_get(*args, **kwargs):
                    events = _orig_get(*args, **kwargs)
                    out = []
                    for ev in events:
                        if mp_self._chat_open:
                            # Chat is open — consume keyboard, block ESC from pausing
                            if ev.type == _pg.KEYDOWN:
                                if ev.key == _pg.K_ESCAPE:
                                    mp_self._chat_open = False
                                    mp_self._chat_input = ""
                                elif ev.key == _pg.K_RETURN:
                                    t2 = mp_self._chat_input.strip()
                                    if t2:
                                        mp_self.net.send({"type": "chat", "text": t2})
                                        mp_self._chat_log.append((mp_self.nick, t2, _pg.time.get_ticks()))
                                    mp_self._chat_open = False
                                    mp_self._chat_input = ""
                                elif ev.key == _pg.K_BACKSPACE:
                                    mp_self._chat_input = mp_self._chat_input[:-1]
                                elif ev.unicode and len(mp_self._chat_input) < 80:
                                    mp_self._chat_input += ev.unicode
                                # Don't pass keyboard events to game while chat open
                            elif ev.type in (_pg.MOUSEBUTTONDOWN, _pg.MOUSEBUTTONUP):
                                out.append(ev)  # allow mouse clicks through
                        else:
                            # Chat closed — intercept T key to open chat
                            if ev.type == _pg.KEYDOWN and ev.key == _pg.K_t:
                                if not mp_self.paused and not mp_self.game_over and not mp_self.win:
                                    mp_self._chat_open = True
                                    mp_self._chat_input = ""
                                    continue
                            out.append(ev)
                    return out

                _pg.event.get = _filtered_get
                try:
                    super().run()
                finally:
                    _pg.event.get = _orig_get
                    self._restore()
                    self.net.send({"type": "leave_room"})
                return self.return_to_menu

            def _restore(self):
                UNIT_LIMITS.clear()
                UNIT_LIMITS.update(self._orig_limits)
                game_mod.GLOBAL_UNIT_LIMIT = 40

        cls._cls = MultiplayerGame
        return MultiplayerGame


# ── Chat overlay ─────────────────────────────────────────────────────────────
def _draw_chat_overlay(surf, chat_log, chat_open, chat_input):
    MAX_VISIBLE = 8
    BOX_W = 420; LINE_H = 22; PAD = 8; x = 8
    now = pygame.time.get_ticks()
    visible = []
    for nick, text, ts in reversed(chat_log):
        age = (now - ts) / 1000.0
        if not chat_open and age > 8.0:
            continue
        visible.append((nick, text, age))
        if len(visible) >= MAX_VISIBLE:
            break
    visible.reverse()
    base_y = SCREEN_H - 160 - (LINE_H + PAD if chat_open else 0)
    if visible:
        log_h = len(visible) * LINE_H + PAD * 2
        log_y = base_y - log_h
        draw_rect_alpha(surf, (8, 10, 18), (x, log_y, BOX_W, log_h), 180, 6)
        f = pygame.font.SysFont("segoeui", 15)
        for i, (nick, text, age) in enumerate(visible):
            alpha = max(60, 255 - int(age * 20)) if not chat_open else 255
            col = (180, 140, 60) if nick == "SYSTEM" else (100, 200, 255)
            prefix = "  ★ " if nick == "SYSTEM" else f"  {nick}: "
            line = (prefix + text)[:60]
            s = f.render(line, True, col)
            s.set_alpha(alpha)
            surf.blit(s, (x + PAD, log_y + PAD + i * LINE_H))
    if chat_open:
        ib_y = base_y
        draw_rect_alpha(surf, (12, 16, 28), (x, ib_y, BOX_W, LINE_H + PAD * 2), 220, 6)
        pygame.draw.rect(surf, (60, 120, 200), (x, ib_y, BOX_W, LINE_H + PAD * 2), 2, border_radius=6)
        hint = pygame.font.SysFont("segoeui", 14).render("ENTER send  •  ESC close", True, (60, 80, 120))
        surf.blit(hint, (x + PAD, ib_y - 18))
        cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        ts2 = pygame.font.SysFont("segoeui", 16, bold=True).render(chat_input + cursor, True, C_WHITE)
        surf.blit(ts2, (x + PAD, ib_y + PAD))
    else:
        hs = pygame.font.SysFont("segoeui", 13).render("T — chat", True, (50, 60, 90))
        surf.blit(hs, (x, SCREEN_H - 155))


# ── Entry point ──────────────────────────────────────────────────────────────
def run_multiplayer(screen, save_data: dict):
    """Called by game.py _run_multiplayer(). Returns updated save_data."""

    # 1. Ask for nickname
    nick = NickScreen(screen, save_data).run()
    if nick is None:
        return save_data

    # 2. Connect to server
    net = UDPClient()
    connecting_surf = screen.copy()
    screen.fill((12,14,22))
    cf = pygame.font.SysFont("segoeui", 28)
    cs = cf.render(f"Connecting to {MP_HOST}:{MP_PORT} ...", True, (100,180,255))
    screen.blit(cs, cs.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
    pygame.display.flip()
    try:
        net.connect(MP_HOST, MP_PORT)
        # Send 5 pings to fight UDP loss on first contact
        for _ in range(5):
            net.send({"type": "ping"})
            time.sleep(0.1)
        deadline = time.time() + 8.0
        got_pong = False
        while time.time() < deadline:
            for msg in net.poll():
                if msg.get("type") == "pong":
                    got_pong = True; break
            if got_pong: break
            # Keep sending pings while waiting
            net.send({"type": "ping"})
            time.sleep(0.2)
        if not got_pong:
            raise ConnectionError("No response from server")
    except Exception as e:
        screen.fill((12,14,22))
        ef = pygame.font.SysFont("segoeui", 26).render(f"Cannot connect: {e}", True, (255,80,80))
        screen.blit(ef, ef.get_rect(center=(SCREEN_W//2, SCREEN_H//2)))
        hf = pygame.font.SysFont("segoeui", 20).render("Make sure mp_server.py is running. Press any key.", True, (140,140,180))
        screen.blit(hf, hf.get_rect(center=(SCREEN_W//2, SCREEN_H//2+50)))
        pygame.display.flip()
        _wait_key()
        net.stop()
        return save_data

    # 3. Lobby
    while True:
        lobby = LobbyScreen(screen, net, nick)
        result = lobby.run()
        if result is None or result[0] == "back":
            net.stop()
            return save_data

        if result[0] == "created":
            room_id   = result[1]
            is_host   = True
            host_nick = nick
            map_name  = lobby._pop_map   # use what host selected in create popup
            mode      = lobby._pop_mode
        else:  # joined
            _, room_id, is_host, host_nick, map_name, mode = result

        # 4. Wait room
        wait = WaitRoomScreen(screen, net, nick, room_id, is_host, host_nick, map_name, mode)
        wr   = wait.run()
        if wr == "back":
            continue   # back to lobby list

        # 5. Play — load game module lazily and build subclass
        import importlib.util as _ilu2, sys as _sys2
        _gpath = os.path.join(_ROOT, "game.py")
        if "game" not in _sys2.modules:
            _spec = _ilu2.spec_from_file_location("game", _gpath)
            _mod  = _ilu2.module_from_spec(_spec)
            _sys2.modules["game"] = _mod
            _spec.loader.exec_module(_mod)
        _game_mod = _sys2.modules["game"]

        MPGame = _MPGameFactory.get(_game_mod)
        mp_game = MPGame(
            save_data, net, nick, is_host, host_nick,
            wait.map_name, wait.mode,
        )
        mp_game.screen = screen
        mp_game.run()   # _restore() is called inside run()
        save_data = mp_game.save_data
        # After game ends, go back to lobby
        net.send({"type": "list_rooms"})
        continue

def _wait_key():
    while True:
        for ev in pygame.event.get():
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                return
        time.sleep(0.05)
