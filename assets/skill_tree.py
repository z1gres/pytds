import pygame
import math
import sys
import random

# ── Skill definitions ──────────────────────────────────────────────────────────
SKILLS = [
    # ── Column 0: Range / Area ────────────────────────────────────────────────
    {
        "id": "enhanced_optics",
        "name": "Enhanced Optics",
        "desc": "Tower range +0.5% per level.",
        "max_levels": 20,
        "effect_label": "+0.5% range",
        "base_cost": 3,
        "exp_value": 1.55,
        "requires": None,
        "color": (60, 160, 255),
        "icon": "🔭",
        "col": 0, "row": 0,
    },
    {
        "id": "improved_gunpowder",
        "name": "Improved Gunpowder",
        "desc": "AoE radius +0.5% per level.\nRequires: Enhanced Optics 10.",
        "max_levels": 25,
        "effect_label": "+0.5% AoE",
        "base_cost": 3,
        "exp_value": 1.52,
        "requires": ("enhanced_optics", 10),
        "color": (255, 140, 40),
        "icon": "💥",
        "col": 0, "row": 1,
    },
    {
        "id": "fight_dirty",
        "name": "Fight Dirty",
        "desc": "Debuff duration +1% per level.\nRequires: Improved Gunpowder 10.",
        "max_levels": 25,
        "effect_label": "+1% debuff dur.",
        "base_cost": 3,
        "exp_value": 1.58,
        "requires": ("improved_gunpowder", 10),
        "color": (180, 60, 255),
        "icon": "☠",
        "col": 0, "row": 2,
    },
    {
        "id": "precision",
        "name": "Precision",
        "desc": "Every X shots is a crit (x1.25).\nStarts at 29, -1 per level.\nRequires: Fight Dirty 10.",
        "max_levels": 15,
        "effect_label": "−1 shot to crit",
        "base_cost": 4,
        "exp_value": 1.72,
        "requires": ("fight_dirty", 10),
        "color": (255, 60, 80),
        "icon": "🎯",
        "col": 0, "row": 3,
    },
    # ── Column 1: Economy ────────────────────────────────────────────────────
    {
        "id": "resourcefulness",
        "name": "Resourcefulness",
        "desc": "Sell refund +1.2% per level.",
        "max_levels": 25,
        "effect_label": "+1.2% sell value",
        "base_cost": 2,
        "exp_value": 1.55,
        "requires": None,
        "color": (60, 200, 80),
        "icon": "♻",
        "col": 1, "row": 0,
    },
    {
        "id": "bigger_budget",
        "name": "Bigger Budget",
        "desc": "Starting gold +1% per level.\nRequires: Resourcefulness 10.",
        "max_levels": 25,
        "effect_label": "+1% start cash",
        "base_cost": 2,
        "exp_value": 1.60,
        "requires": ("resourcefulness", 10),
        "color": (255, 220, 50),
        "icon": "💰",
        "col": 1, "row": 1,
    },
    {
        "id": "stonks",
        "name": "Stonks",
        "desc": "Wave clear reward +0.5% per level.\nRequires: Bigger Budget 10.",
        "max_levels": 20,
        "effect_label": "+0.5% wave reward",
        "base_cost": 4,
        "exp_value": 1.62,
        "requires": ("bigger_budget", 10),
        "color": (100, 240, 160),
        "icon": "📈",
        "col": 1, "row": 2,
    },
    {
        "id": "scavenger",
        "name": "Scavenger",
        "desc": "Every X kills gives 1.5x reward.\nStarts at 29, -1 per level.\nRequires: Stonks 10.",
        "max_levels": 20,
        "effect_label": "−1 kill to bonus",
        "base_cost": 4,
        "exp_value": 1.68,
        "requires": ("stonks", 10),
        "color": (255, 180, 80),
        "icon": "🗡",
        "col": 1, "row": 3,
    },
]

SKILL_BY_ID = {s["id"]: s for s in SKILLS}


def _level_cost(skill, level_1based):
    return int(skill["base_cost"] * (skill["exp_value"] ** (level_1based - 1)))


def _total_cost(skill, levels):
    return sum(_level_cost(skill, i + 1) for i in range(levels))


def skill_tree_bonus(skill_id, save_data):
    levels = save_data.get("skill_tree", {}).get(skill_id, 0)
    if levels == 0:
        return 0
    if skill_id == "enhanced_optics":    return levels * 0.005
    if skill_id == "improved_gunpowder": return levels * 0.005
    if skill_id == "fight_dirty":        return levels * 0.01
    if skill_id == "precision":          return 29 - levels
    if skill_id == "resourcefulness":    return 0.3333 + levels * 0.012
    if skill_id == "bigger_budget":      return levels * 0.01
    if skill_id == "stonks":             return levels * 0.005
    if skill_id == "scavenger":          return 29 - levels
    return 0


# ── Palette ───────────────────────────────────────────────────────────────────
_C_BG          = (7,  10, 19)
_C_BG2         = (12, 18, 33)
_C_PANEL       = (13, 18, 32)
_C_WHITE       = (240, 244, 255)
_C_GOLD        = (255, 200, 50)
_C_GOLD_DIM    = (170, 132, 34)
_C_GRAY        = (140, 152, 180)
_C_GRAY2       = (92, 104, 135)
_C_RED         = (225, 70, 70)
_C_GREEN       = (72, 214, 104)
_C_LOCKED      = (58, 64, 88)
_C_LOCKED_TXT  = (112, 122, 152)


# ── geometry / drawing helpers ────────────────────────────────────────────────
def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _hex_pts(cx, cy, r, rot=0.0):
    return [(cx + math.cos(rot + math.radians(60 * i - 30)) * r,
             cy + math.sin(rot + math.radians(60 * i - 30)) * r) for i in range(6)]


def _draw_hex(surf, cx, cy, r, fill, border=None, bw=2, rot=0.0):
    pts = _hex_pts(cx, cy, r, rot)
    if fill is not None:
        pygame.draw.polygon(surf, fill, pts)
    if border is not None and bw > 0:
        pygame.draw.polygon(surf, border, pts, bw)


def _alpha_circle(surf, color, center, r, alpha):
    r = int(max(1, r))
    s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, max(0, min(255, int(alpha)))), (r + 1, r + 1), r)
    surf.blit(s, (int(center[0]) - r - 1, int(center[1]) - r - 1))


def _radial_glow(surf, color, center, r, alpha=None, layers=4):
    if alpha is None:
        alpha = 60
    step = max(2, r // (layers + 1))
    for i in range(layers, 0, -1):
        rr = r - (layers - i) * step
        a = int(alpha * (i / layers) ** 1.6)
        if rr > 1 and a > 0:
            _alpha_circle(surf, color, center, rr, a)


def _alpha_rect(surf, color, rect, alpha, radius=0):
    w, h = max(1, int(rect[2])), max(1, int(rect[3]))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    a = max(0, min(255, int(alpha)))
    if radius:
        pygame.draw.rect(s, (*color, a), pygame.Rect(0, 0, w, h), border_radius=max(1, int(radius)))
    else:
        s.fill((*color, a))
    surf.blit(s, (int(rect[0]), int(rect[1])))


def _cubic(p0, p1, p2, p3, n=26):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
        out.append((x, y))
    return out


def _polyline(surf, pts, color, width):
    if len(pts) > 1:
        pygame.draw.lines(surf, color, False, pts, max(1, int(width)))


def _point_on(pts, f):
    f = max(0.0, min(1.0, f))
    x = f * (len(pts) - 1)
    i = int(x)
    if i >= len(pts) - 1:
        return pts[-1]
    return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * (x - i),
            pts[i][1] + (pts[i + 1][1] - pts[i][1]) * (x - i))


def _coin(surf, cx, cy, r=7):
    pygame.draw.circle(surf, (120, 86, 20), (int(cx), int(cy)), r + 1)
    pygame.draw.circle(surf, _C_GOLD, (int(cx), int(cy)), r)
    pygame.draw.circle(surf, (255, 238, 160), (int(cx - r / 3), int(cy - r / 3)), max(1, r // 3))


class SkillTreeScreen:
    def __init__(self, screen, save_data):
        self.screen    = screen
        self.save_data = save_data
        self.W = screen.get_width()
        self.H = screen.get_height()
        self.t = 0.0
        self.selected  = None
        self.hovered   = None
        self.msg       = ""
        self.msg_t     = 0.0
        self.msg_ok    = True
        self._anim     = {sk["id"]: 0.0 for sk in SKILLS}

        # Everything is laid out for a 1080p canvas and scaled to the real height
        self.s = max(0.55, min(1.7, self.H / 1080.0))

        # Right info panel
        self._pw = self._sp(360)
        self._px = self.W - self._pw
        self._py = 0
        self._ph = self.H
        tree_w = self._px

        # Tree layout — root core at the bottom, branches climb upwards
        self._root_y  = int(self.H * 0.875)
        self._root    = (int(tree_w * 0.5), self._root_y)
        self._col_x   = [int(tree_w * 0.28), int(tree_w * 0.72)]
        self._row_y   = [int(self.H * (0.70 - i * 0.155)) for i in range(4)]
        self._orb_r   = self._sp(44)
        self._root_r  = self._sp(44)

        # Fonts
        self.f_hdr   = pygame.font.SysFont("segoeui", self._sp(32), bold=True)
        self.f_title = pygame.font.SysFont("segoeui", self._sp(21), bold=True)
        self.f_sub   = pygame.font.SysFont("segoeui", self._sp(16), bold=True)
        self.f_body  = pygame.font.SysFont("segoeui", self._sp(15))
        self.f_sm    = pygame.font.SysFont("segoeui", self._sp(13))
        self.f_tiny  = pygame.font.SysFont("segoeui", self._sp(11), bold=True)
        self.f_num   = pygame.font.SysFont("consolas", self._sp(15), bold=True)
        self._emoji_cache = {}

        # Clickable node areas (orb + labels underneath)
        self.node_rects = {}
        for sk in SKILLS:
            cx, cy = self._node_xy(sk)
            self.node_rects[sk["id"]] = pygame.Rect(
                cx - self._sp(92), cy - self._orb_r - self._sp(14),
                self._sp(184), self._orb_r * 2 + self._sp(94))

        self.btn_back = pygame.Rect(self._sp(24), self._sp(18), self._sp(132), self._sp(42))
        self.btn_upg  = pygame.Rect(self._px + self._sp(18), self.H - self._sp(84),
                                    self._pw - self._sp(36), self._sp(54))

        # Ambient background particles (deterministic)
        rng = random.Random(7)
        self._parts = [(rng.uniform(0, tree_w), rng.uniform(0, 1),
                        rng.uniform(5, 16), rng.uniform(0, math.tau), rng.uniform(8, 26))
                       for _ in range(64)]
        self._specks = [(rng.randint(0, tree_w), rng.randint(int(self.H * 0.07), self.H),
                         rng.randint(1, 2)) for _ in range(90)]

    # ── helpers ───────────────────────────────────────────────────────────────
    def _sp(self, v):
        """Scale a 1080p design value to the current screen height."""
        return max(1, int(round(v * self.s)))

    def _st(self):    return self.save_data.setdefault("skill_tree", {})
    def _lvl(self, s): return self._st().get(s, 0)
    def _coins(self): return self.save_data.get("coins", 0)

    def _node_xy(self, sk):
        return (self._col_x[sk["col"]], self._row_y[sk["row"]])

    def _req_met(self, skill):
        if skill["requires"] is None:
            return True
        rid, rlvl = skill["requires"]
        return self._lvl(rid) >= rlvl

    def _can_upgrade(self, skill):
        lvl = self._lvl(skill["id"])
        if lvl >= skill["max_levels"]:
            return False, "Max Level"
        if not self._req_met(skill):
            rid, rlvl = skill["requires"]
            return False, f"Need {SKILL_BY_ID[rid]['name']} lv{rlvl}"
        cost = _level_cost(skill, lvl + 1)
        if self._coins() < cost:
            return False, f"Need {cost} coins"
        return True, ""

    def _upgrade(self, skill):
        ok, reason = self._can_upgrade(skill)
        if not ok:
            self.msg = reason; self.msg_t = 2.5; self.msg_ok = False; return
        lvl = self._lvl(skill["id"])
        cost = _level_cost(skill, lvl + 1)
        self._st()[skill["id"]] = lvl + 1
        self.save_data["coins"] = self._coins() - cost
        try:
            from game_core import write_save
            write_save(self.save_data)
        except Exception:
            pass
        self.msg = f"Upgraded to Level {lvl + 1}!"
        self.msg_t = 2.0; self.msg_ok = True

    def _emoji(self, ch, size):
        key = (ch, size)
        cached = self._emoji_cache.get(key)
        if cached is not None:
            return cached
        font = pygame.font.SysFont("segoeuiemoji", max(8, int(size)))
        surf = font.render(ch, True, (255, 255, 255))
        self._emoji_cache[key] = surf
        return surf

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self.msg_t > 0:
                self.msg_t -= dt

            mx, my = pygame.mouse.get_pos()
            self.hovered = None
            for sid, r in self.node_rects.items():
                if r.collidepoint(mx, my):
                    self.hovered = sid

            for sid in self._anim:
                target = 1.0 if (sid == self.hovered or sid == self.selected) else 0.0
                self._anim[sid] += (target - self._anim[sid]) * min(1.0, dt * 10)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.collidepoint(ev.pos):
                        return
                    clicked_node = False
                    for sid, r in self.node_rects.items():
                        if r.collidepoint(ev.pos):
                            self.selected = sid
                            clicked_node = True
                            break
                    if not clicked_node and not pygame.Rect(self._px, 0, self._pw, self.H).collidepoint(ev.pos):
                        self.selected = None
                    if self.btn_upg.collidepoint(ev.pos) and self.selected:
                        self._upgrade(SKILL_BY_ID[self.selected])

            self._draw()
            pygame.display.flip()

    # ── drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        surf = self.screen
        self._draw_background(surf)
        self._draw_connections(surf)
        self._draw_root(surf)
        self._draw_nodes(surf)
        self._draw_right_panel(surf)
        self._draw_topbar(surf)

    def _draw_background(self, surf):
        tree_w = self._px
        for y in range(0, self.H, 4):
            f = y / max(1, self.H)
            pygame.draw.rect(surf, _lerp_color(_C_BG, _C_BG2, f), (0, y, tree_w, 4))
        _radial_glow(surf, (40, 110, 190), self._root, int(self.H * 0.30), 26, layers=5)
        for x, y, r in self._specks:
            br = int(abs(math.sin(self.t * 0.5 + x * 0.01 + y * 0.007)) * 18 + 12)
            pygame.draw.circle(surf, (br, br + 6, br + 22),
                               (x + int(math.sin(self.t * 0.2 + y) * 3), y), r)
        for bx, phase, size, ph, speed in self._parts:
            yy = (phase * self.H + self.t * speed) % self.H
            a = int((0.35 + 0.65 * abs(math.sin(self.t * 0.9 + ph))) * 55)
            _alpha_circle(surf, (120, 180, 255),
                          (bx + math.sin(self.t * 0.6 + ph) * 8, yy), size * 0.35, a)

    def _link_points(self, parent_xy, child_xy, parent_is_root=False, side=1):
        """Curved branch between two nodes; it bows outwards so it never crosses labels."""
        R = self._orb_r
        x1, y1 = parent_xy
        x2, y2 = child_xy
        sign = 1 if x2 >= x1 else -1
        if parent_is_root:
            start = (x1, y1 - self._root_r * 0.75)
            end   = (x2 - sign * R * 0.55, y2 + R * 0.60)
            dy = abs(start[1] - end[1])
            cp1 = (start[0] + sign * self._sp(60), start[1] - dy * 0.40)
            cp2 = (end[0] - sign * self._sp(10), end[1] + dy * 0.40)
        else:
            # Same column: route the branch along the outer side of the node labels
            off = side * self._sp(124)
            start = (x1 + side * R * 0.70, y1 - R * 0.55)
            end   = (x2 + side * R * 0.70, y2 + R * 0.55)
            dy = abs(start[1] - end[1])
            cp1 = (x1 + off, start[1] - dy * 0.25)
            cp2 = (x2 + off, end[1] + dy * 0.25)
        return _cubic(start, cp1, cp2, end, 30)

    def _draw_connections(self, surf):
        for sk in SKILLS:
            accent = sk["color"]
            side = -1 if sk["col"] == 0 else 1
            if sk["requires"] is None:
                pts = self._link_points(self._root, self._node_xy(sk), parent_is_root=True)
                prog = 1.0
                req_met = True
            else:
                rid, rlvl = sk["requires"]
                pts = self._link_points(self._node_xy(SKILL_BY_ID[rid]), self._node_xy(sk),
                                        side=side)
                from_lvl = self._lvl(rid)
                prog = min(1.0, from_lvl / rlvl) if rlvl else 1.0
                req_met = from_lvl >= rlvl

            dim = _lerp_color((34, 42, 62), _lerp_color(accent, _C_WHITE, 0.25), prog)
            _polyline(surf, pts, (14, 19, 31), self._sp(9))
            _polyline(surf, pts, dim, self._sp(4))
            if prog > 0.02:
                _polyline(surf, pts, _lerp_color(dim, _C_WHITE, 0.45), self._sp(1.5))

            for i in range(3):
                f = (self.t * 0.22 + i / 3.0) % 1.0
                if f > prog + 0.001:
                    continue
                p = _point_on(pts, f)
                _alpha_circle(surf, _lerp_color(accent, _C_WHITE, 0.4), p, self._sp(8), 60)
                _alpha_circle(surf, _C_WHITE, p, self._sp(3), 215)


    def _draw_root(self, surf):
        cx, cy = self._root
        r = self._root_r
        S = self._sp
        pulse = 0.5 + 0.5 * math.sin(self.t * 2.0)
        _radial_glow(surf, (90, 170, 255), (cx, cy), r + S(70), int(34 + pulse * 34))

        ring = pygame.Rect(cx - r - S(18), cy - r - S(18), 2 * (r + S(18)), 2 * (r + S(18)))
        for i in range(14):
            a0 = self.t * 0.55 + i * (math.tau / 14)
            pygame.draw.arc(surf, (64, 118, 190), ring, a0, a0 + 0.22, S(3))
        ring2 = pygame.Rect(cx - r - S(8), cy - r - S(8), 2 * (r + S(8)), 2 * (r + S(8)))
        for i in range(8):
            a0 = -self.t * 0.8 + i * (math.tau / 8)
            pygame.draw.arc(surf, (110, 190, 255), ring2, a0, a0 + 0.5, S(2))

        _draw_hex(surf, cx, cy, r, (15, 24, 42), (120, 195, 255), S(2), 0.0)
        _draw_hex(surf, cx, cy, r * 0.66, (22, 44, 74), (160, 225, 255), max(1, S(1)), math.pi / 6)
        pygame.draw.circle(surf, (150, 220, 255), (cx, cy), int(S(9) + pulse * S(3)))
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), max(2, S(4)))

        lbl = self.f_sm.render("TOWER CORE", True, (118, 168, 228))
        surf.blit(lbl, lbl.get_rect(centerx=cx, top=cy + r + S(16)))
        sub = self.f_tiny.render("POWER SOURCE", True, _C_GRAY2)
        surf.blit(sub, sub.get_rect(centerx=cx, top=cy + r + S(16) + lbl.get_height() + S(2)))

    def _draw_nodes(self, surf):
        R = self._orb_r
        S = self._sp
        for sk in SKILLS:
            sid   = sk["id"]
            cx, cy = self._node_xy(sk)
            lvl   = self._lvl(sid)
            max_l = sk["max_levels"]
            locked = not self._req_met(sk)
            hov    = (self.hovered == sid)
            sel    = (self.selected == sid)
            anim   = self._anim[sid]
            maxed  = (lvl >= max_l)
            accent = sk["color"] if not locked else (96, 104, 130)
            frac   = lvl / max_l

            if lvl > 0 or hov or sel:
                _radial_glow(surf, accent if not locked else _C_LOCKED,
                             (cx, cy), R + S(34), int(16 + anim * 55 + frac * 40))

            if sel:
                pulse = 0.5 + 0.5 * math.sin(self.t * 4)
                pygame.draw.circle(surf, _lerp_color(accent, _C_WHITE, pulse * 0.5),
                                   (cx, cy), R + S(20), max(1, S(2)))

            pygame.draw.circle(surf, (23, 28, 45), (cx, cy), R + S(9))
            pygame.draw.circle(surf, (40, 49, 76), (cx, cy), R + S(9), max(1, S(2)))

            rot = self.t * 0.12 + (self.t * 0.5 if hov else 0.0)
            body = _lerp_color((17, 22, 37), accent, 0.0 if locked else 0.20)
            _draw_hex(surf, cx, cy, R, body,
                      _lerp_color((48, 58, 90), accent, 0.0 if locked else 0.85), S(2), rot)
            _draw_hex(surf, cx, cy, R * 0.62,
                      _lerp_color(body, accent, 0.0 if locked else 0.38), None, 0, rot)

            if frac > 0:
                rect = pygame.Rect(cx - R - S(9), cy - R - S(9), 2 * (R + S(9)), 2 * (R + S(9)))
                col = _C_GOLD if maxed else accent
                pygame.draw.arc(surf, (0, 0, 0), rect,
                                math.pi / 2 - math.tau * frac - 0.02, math.pi / 2 + 0.02, S(7))
                pygame.draw.arc(surf, col, rect, math.pi / 2 - math.tau * frac, math.pi / 2, S(5))

            icon = self._emoji(sk["icon"], R * 1.05)
            if locked:
                icon = icon.copy()
                icon.fill((105, 112, 140, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(icon, icon.get_rect(center=(cx, cy)))

            if locked:
                bx, by = cx + int(R * 0.74), cy + int(R * 0.74)
                _alpha_circle(surf, (13, 17, 28), (bx, by), S(13), 240)
                pygame.draw.circle(surf, (74, 84, 112), (bx, by), S(13), 1)
                lk = self._emoji("🔒", S(14))
                surf.blit(lk, lk.get_rect(center=(bx, by)))

            if maxed:
                badge = self.f_tiny.render("MAX", True, (28, 22, 8))
                bw = badge.get_width() + S(12)
                br = pygame.Rect(cx - bw // 2, cy - R - S(22), bw, badge.get_height() + S(3))
                pygame.draw.rect(surf, _C_GOLD, br, border_radius=br.height // 2)
                surf.blit(badge, badge.get_rect(center=br.center))

            name_col = _C_LOCKED_TXT if locked else (_C_GOLD if maxed else _C_WHITE)
            ns = self.f_sub.render(sk["name"], True, name_col)
            surf.blit(ns, ns.get_rect(centerx=cx, top=cy + R + S(11)))

            lv_txt = "MAX LEVEL" if maxed else f"LV {lvl} / {max_l}"
            lv_col = _C_GOLD if maxed else (_C_LOCKED_TXT if locked else _C_GRAY2)
            ls = self.f_sm.render(lv_txt, True, lv_col)
            surf.blit(ls, ls.get_rect(centerx=cx, top=cy + R + S(11) + ns.get_height() + S(1)))

            if not maxed and not locked:
                cost = _level_cost(sk, lvl + 1)
                can = self._coins() >= cost
                if can and (hov or sel or lvl == 0):
                    txt = self.f_sm.render(str(cost), True, _C_GREEN if can else _C_RED)
                    w = txt.get_width() + S(26)
                    pr = pygame.Rect(cx - w // 2, cy + R + S(11) + ns.get_height() + ls.get_height() + S(4),
                                     w, txt.get_height() + S(6))
                    _alpha_rect(surf, (16, 30, 22), pr, 215, pr.height // 2)
                    pygame.draw.rect(surf, (46, 92, 60), pr, 1, border_radius=pr.height // 2)
                    _coin(surf, pr.x + S(10), pr.centery, S(5))
                    surf.blit(txt, txt.get_rect(midleft=(pr.x + S(17), pr.centery)))

    # ── right panel ───────────────────────────────────────────────────────────
    def _draw_right_panel(self, surf):
        px, py, pw, ph = self._px, self._py, self._pw, self._ph
        S = self._sp

        _alpha_rect(surf, _C_PANEL, (px, py, pw, ph), 252)
        pygame.draw.line(surf, (34, 46, 78), (px, py), (px, py + ph), max(1, S(2)))
        for i in range(S(46)):
            pygame.draw.line(surf, (24, 40, 68), (px + S(2) + i, py), (px + S(2) + i, py + ph), 1)

        if self.selected is None:
            _radial_glow(surf, (60, 110, 190), (px + pw // 2, py + ph // 2 - S(30)), S(120), 40)
            ic = self._emoji("🌳", S(64))
            ic = ic.copy(); ic.set_alpha(120)
            surf.blit(ic, ic.get_rect(center=(px + pw // 2, py + ph // 2 - S(70))))
            hs = self.f_title.render("SELECT A SKILL", True, _C_GRAY)
            surf.blit(hs, hs.get_rect(center=(px + pw // 2, py + ph // 2 + S(10))))
            for i, line in enumerate(["Click a node to inspect it,",
                                      "then spend coins to level it up."]):
                s = self.f_body.render(line, True, _C_GRAY2)
                surf.blit(s, s.get_rect(center=(px + pw // 2, py + ph // 2 + S(44) + i * S(22))))
            total = sum(self._lvl(s["id"]) for s in SKILLS)
            tmax = sum(s["max_levels"] for s in SKILLS)
            s = self.f_sm.render(f"TOTAL PROGRESS   {total} / {tmax}", True, _C_GOLD_DIM)
            surf.blit(s, s.get_rect(center=(px + pw // 2, py + ph // 2 + S(110))))
            return

        sk     = SKILL_BY_ID[self.selected]
        lvl    = self._lvl(self.selected)
        locked = not self._req_met(sk)
        maxed  = (lvl >= sk["max_levels"])
        accent = sk["color"] if not locked else _C_LOCKED

        tx = px + S(22)
        ty = S(26)

        cat_txt = "LOCKED" if locked else ("MAXED" if maxed else ("ACTIVE" if lvl > 0 else "AVAILABLE"))
        cat_surf = self.f_tiny.render(cat_txt, True, _C_LOCKED_TXT if locked else accent)
        tag_w = cat_surf.get_width() + S(16)
        _alpha_rect(surf, _lerp_color((18, 24, 42), accent, 0.28),
                    (tx, ty, tag_w, cat_surf.get_height() + S(6)), 220, S(5))
        pygame.draw.rect(surf, _C_LOCKED if locked else accent,
                         (tx, ty, tag_w, cat_surf.get_height() + S(6)), 1, border_radius=S(5))
        surf.blit(cat_surf, (tx + S(8), ty + S(3)))

        # Big node emblem
        ex, ey = px + pw - S(62), S(74)
        er = S(40)
        frac = lvl / sk["max_levels"]
        _radial_glow(surf, accent, (ex, ey), S(56), 55 if not locked else 20)
        pygame.draw.circle(surf, (20, 26, 43), (ex, ey), er)
        pygame.draw.circle(surf, (42, 52, 82), (ex, ey), er, max(1, S(2)))
        if frac > 0:
            rect = pygame.Rect(ex - er, ey - er, er * 2, er * 2)
            pygame.draw.arc(surf, _C_GOLD if maxed else accent, rect,
                            math.pi / 2 - math.tau * frac, math.pi / 2, S(4))
        ic = self._emoji(sk["icon"], er * 0.9)
        if locked:
            ic = ic.copy(); ic.fill((110, 118, 145, 255), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(ic, ic.get_rect(center=(ex, ey)))

        name_col = _C_GOLD if maxed else (accent if not locked else _C_LOCKED_TXT)
        words = sk["name"].split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if self.f_hdr.size(test)[0] > pw - S(150):
                if cur: lines.append(cur)
                cur = w
            else:
                cur = test
        if cur: lines.append(cur)
        ty += S(32)
        for line in lines:
            ls = self.f_hdr.render(line, True, name_col)
            surf.blit(ls, (tx, ty)); ty += ls.get_height() + S(4)
        ty += S(6)

        pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - S(22), ty), 1)
        ty += S(14)
        surf.blit(self.f_tiny.render("LEVEL PROGRESS", True, _C_GRAY2), (tx, ty)); ty += S(18)
        bar_w = pw - S(44)
        bar_h = S(14)
        num_segs = min(sk["max_levels"], 25)
        seg_gap = max(1, S(2))
        seg_w = (bar_w - seg_gap * (num_segs - 1)) / num_segs
        filled = int(lvl / sk["max_levels"] * num_segs)
        for i in range(num_segs):
            sx = tx + i * (seg_w + seg_gap)
            if i < filled:
                sc = _C_GOLD if maxed else _lerp_color(
                    accent, _lerp_color(accent, _C_WHITE, 0.45), i / max(1, num_segs - 1))
            else:
                sc = (24, 31, 52)
            pygame.draw.rect(surf, sc, (int(sx), ty, max(1, int(seg_w)), bar_h), border_radius=S(3))
        ty += bar_h + S(8)
        lvl_txt = "MAX" if maxed else f"LV {lvl} / {sk['max_levels']}"
        lvl_s = self.f_num.render(lvl_txt, True, _C_GOLD if maxed else _C_WHITE)
        surf.blit(lvl_s, (tx, ty)); ty += lvl_s.get_height() + S(10)

        pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - S(22), ty), 1)
        ty += S(14)
        surf.blit(self.f_tiny.render("DESCRIPTION", True, _C_GRAY2), (tx, ty)); ty += S(18)
        for line in sk["desc"].split("\n"):
            ds = self.f_body.render(line, True, _C_GRAY)
            surf.blit(ds, (tx, ty)); ty += ds.get_height() + S(5)
        ty += S(6)

        if lvl > 0:
            pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - S(22), ty), 1)
            ty += S(14)
            surf.blit(self.f_tiny.render("CURRENT EFFECT", True, _C_GRAY2), (tx, ty)); ty += S(18)
            bonus = skill_tree_bonus(self.selected, self.save_data)
            if self.selected in ("precision", "scavenger"):
                effect_str = f"{int(bonus)} shots/kills to bonus"
            else:
                effect_str = f"+{bonus * 100:.1f}%"
            es = self.f_sub.render(effect_str, True, accent)
            surf.blit(es, (tx, ty)); ty += es.get_height() + S(10)
            pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - S(22), ty), 1)
            ty += S(14)

        if not maxed:
            next_cost = _level_cost(sk, lvl + 1)
            total_next = _total_cost(sk, lvl + 1)
            ok, reason = self._can_upgrade(sk)
            surf.blit(self.f_tiny.render("UPGRADE COST", True, _C_GRAY2), (tx, ty)); ty += S(18)
            cost_col = _C_GREEN if ok else _C_RED
            cost_txt = self.f_sub.render(str(next_cost), True, cost_col)
            _coin(surf, tx + S(7), ty + cost_txt.get_height() // 2, S(7))
            surf.blit(cost_txt, (tx + S(19), ty))
            tot_s = self.f_sm.render(f"total {total_next}", True, _C_GRAY2)
            surf.blit(tot_s, (tx + S(19) + cost_txt.get_width() + S(12), ty + S(3)))
            ty += cost_txt.get_height() + S(12)
            if locked:
                rid, rlvl = sk["requires"]
                lock_s = self.f_sm.render(f"Requires {SKILL_BY_ID[rid]['name']} lv{rlvl}",
                                          True, _C_RED)
                surf.blit(lock_s, (tx, ty)); ty += lock_s.get_height() + S(4)
            elif not ok and reason:
                rs = self.f_sm.render(reason, True, _C_RED)
                surf.blit(rs, (tx, ty)); ty += rs.get_height() + S(4)
        else:
            max_s = self.f_sub.render("MAXED OUT", True, _C_GOLD)
            surf.blit(max_s, max_s.get_rect(centerx=px + pw // 2, top=ty)); ty += max_s.get_height() + S(10)

        pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - S(22), ty), 1)
        ty += S(14)
        surf.blit(self.f_tiny.render("YOUR COINS", True, _C_GRAY2), (tx, ty)); ty += S(18)
        bal = self.f_sub.render(str(self._coins()), True, _C_GOLD)
        _coin(surf, tx + S(7), ty + bal.get_height() // 2, S(7))
        surf.blit(bal, (tx + S(19), ty))

        if self.msg and self.msg_t > 0:
            alpha = min(255, int(self.msg_t * 180))
            mc = _C_GREEN if self.msg_ok else _C_RED
            msg_s = self.f_body.render(self.msg, True, mc)
            msg_s.set_alpha(alpha)
            surf.blit(msg_s, msg_s.get_rect(centerx=px + pw // 2, bottom=self.H - S(100)))

        if not maxed:
            ok2, _ = self._can_upgrade(sk)
            br = self.btn_upg
            br.x = px + S(18); br.y = self.H - S(82); br.w = pw - S(36); br.h = S(54)

            if locked:
                btn_bg, btn_brd, btn_txt, txt_col = (26, 30, 48), (52, 60, 88), "LOCKED", _C_LOCKED_TXT
            elif ok2:
                pulse = abs(math.sin(self.t * 2.5)) * 0.35
                btn_bg = _lerp_color((19, 62, 32), accent, 0.22)
                btn_brd = _lerp_color(_C_GREEN, _C_WHITE, pulse)
                btn_txt, txt_col = "UPGRADE", _C_WHITE
                _alpha_rect(surf, _C_GREEN, (br.x - S(3), br.y - S(3), br.w + S(6), br.h + S(6)),
                            int(30 + pulse * 70), S(15))
            else:
                btn_bg, btn_brd, btn_txt, txt_col = (48, 26, 26), _C_RED, "CAN'T UPGRADE", (185, 95, 95)

            _alpha_rect(surf, btn_bg, (br.x, br.y, br.w, br.h), 245, S(12))
            pygame.draw.rect(surf, btn_brd, br, max(1, S(2)), border_radius=S(12))
            ls = self.f_sub.render(btn_txt, True, txt_col)
            if ok2:
                cost_s = self.f_sub.render(str(_level_cost(sk, lvl + 1)), True, _C_GOLD)
                total_w = ls.get_width() + S(20) + cost_s.get_width()
                sx = br.centerx - total_w // 2
                surf.blit(ls, ls.get_rect(midleft=(sx, br.centery)))
                _coin(surf, sx + ls.get_width() + S(16), br.centery, S(7))
                surf.blit(cost_s, cost_s.get_rect(midleft=(sx + ls.get_width() + S(26), br.centery)))
            else:
                surf.blit(ls, ls.get_rect(center=br.center))

    def _draw_topbar(self, surf):
        S = self._sp
        _alpha_rect(surf, (9, 13, 26), (0, 0, self._px, S(74)), 236)
        pygame.draw.line(surf, (32, 45, 78), (0, S(74)), (self._px, S(74)), 1)

        ts = self.f_hdr.render("SKILL TREE", True, _C_WHITE)
        surf.blit(ts, (S(182), S(8)))
        glow_ts = self.f_hdr.render("SKILL TREE", True, (90, 170, 255))
        glow_ts.set_alpha(46)
        surf.blit(glow_ts, (S(184), S(9)))
        sub = self.f_sm.render("Climb the branches — each skill unlocks the next", True, _C_GRAY2)
        surf.blit(sub, (S(184), S(8) + ts.get_height() + S(2)))

        for col, name in ((0, "COMBAT"), (1, "ECONOMY")):
            cx = self._col_x[col]
            accent = SKILLS[col * 4]["color"]
            y = self._row_y[3] - S(104)
            lab = self.f_tiny.render(name, True, _lerp_color(_C_GRAY2, accent, 0.6))
            surf.blit(lab, lab.get_rect(center=(cx, y)))
            half = S(74)
            pygame.draw.line(surf, _lerp_color((34, 44, 70), accent, 0.4),
                             (cx - half, y + lab.get_height()), (cx + half, y + lab.get_height()), 1)

        pill = pygame.Rect(self._px - S(250), S(18), S(226), S(40))
        _alpha_rect(surf, (13, 19, 34), pill, 225, S(10))
        pygame.draw.rect(surf, (58, 78, 128), pill, 1, border_radius=S(10))
        _coin(surf, pill.x + S(20), pill.centery, S(9))
        coin_txt = self.f_title.render(f"{self._coins()}", True, _C_GOLD)
        surf.blit(coin_txt, coin_txt.get_rect(midleft=(pill.x + S(36), pill.centery)))
        lbl = self.f_sm.render("coins", True, _C_GRAY2)
        surf.blit(lbl, lbl.get_rect(midleft=(pill.x + S(44) + coin_txt.get_width(),
                                              pill.centery + S(1))))

        b = self.btn_back
        hov = b.collidepoint(pygame.mouse.get_pos())
        _alpha_rect(surf, (25, 35, 62) if hov else (15, 20, 38), (b.x, b.y, b.w, b.h), 235, S(9))
        pygame.draw.rect(surf, (80, 130, 220) if hov else (46, 62, 102), b, 1, border_radius=S(9))
        bs = self.f_body.render("<  BACK", True, _C_WHITE if hov else _C_GRAY)
        surf.blit(bs, bs.get_rect(center=b.center))
