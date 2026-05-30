import pygame
import math
import sys

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


# ── TDS-style palette ─────────────────────────────────────────────────────────
_C_BG          = (8,  12, 22)
_C_BG2         = (12, 17, 30)
_C_PANEL       = (16, 21, 38)
_C_PANEL2      = (20, 27, 48)
_C_BORDER      = (38, 52, 90)
_C_BORDER_HOV  = (80, 110, 180)
_C_WHITE       = (240, 244, 255)
_C_GOLD        = (255, 200, 50)
_C_GOLD_DIM    = (180, 140, 30)
_C_GRAY        = (130, 142, 170)
_C_GRAY2       = (90,  100, 130)
_C_RED         = (220,  60,  60)
_C_GREEN       = (70,  210,  100)
_C_LOCKED      = (45,  50,  70)
_C_LOCKED_TXT  = (80,  90, 115)
_C_LOCKED_BAR  = (35,  40,  58)

# Layout — tree is left-centre, panel is right strip
_TREE_CX   = 480          # horizontal centre of the tree area
_COL_OFFX  = 200          # column x offset from tree centre (±)
_ROW_START = 155          # y of first row
_ROW_GAP   = 168          # gap between rows
_NODE_W    = 260
_NODE_H    = 118
_HEX_R     = 32           # hex icon radius

_PANEL_X   = _TREE_CX * 2 - 20   # right panel starts here (dynamic later)


def _col_row_to_xy(col, row):
    x = _TREE_CX + (col * 2 - 1) * _COL_OFFX
    y = _ROW_START + row * _ROW_GAP
    return x, y


def _draw_hexagon(surf, cx, cy, r, fill, border, bw=2):
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(surf, fill, pts)
    pygame.draw.polygon(surf, border, pts, bw)


def _alpha_rect(surf, color, rect, alpha, radius=0):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    r = pygame.Rect(0, 0, rect[2], rect[3])
    if radius:
        pygame.draw.rect(s, (*color, alpha), r, border_radius=radius)
    else:
        s.fill((*color, alpha))
    surf.blit(s, (rect[0], rect[1]))


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


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
        self._anim     = {}   # sid -> float 0..1 (hover/select pulse)

        # Panel geometry (right third of screen)
        self._px = self.W - 360
        self._py = 0
        self._pw = 360
        self._ph = self.H

        # Fonts
        self.f_hdr   = pygame.font.SysFont("segoeui", 34, bold=True)
        self.f_title = pygame.font.SysFont("segoeui", 22, bold=True)
        self.f_sub   = pygame.font.SysFont("segoeui", 17, bold=True)
        self.f_body  = pygame.font.SysFont("segoeui", 15)
        self.f_sm    = pygame.font.SysFont("segoeui", 13)
        self.f_num   = pygame.font.SysFont("consolas", 15, bold=True)
        self.f_icon  = pygame.font.SysFont("segoeuisymbol", 22)

        # Back button
        self.btn_back = pygame.Rect(20, 18, 130, 40)

        # Node rects
        self.node_rects = {}
        for sk in SKILLS:
            cx, cy = _col_row_to_xy(sk["col"], sk["row"])
            r = pygame.Rect(cx - _NODE_W // 2, cy - _NODE_H // 2, _NODE_W, _NODE_H)
            self.node_rects[sk["id"]] = r
            self._anim[sk["id"]] = 0.0

        # Upgrade button rect (inside panel)
        self.btn_upg = pygame.Rect(self._px + 20, self.H - 90, self._pw - 40, 52)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _st(self):    return self.save_data.setdefault("skill_tree", {})
    def _lvl(self, s): return self._st().get(s, 0)
    def _coins(self): return self.save_data.get("coins", 0)

    def _req_met(self, skill):
        if skill["requires"] is None: return True
        rid, rlvl = skill["requires"]
        return self._lvl(rid) >= rlvl

    def _can_upgrade(self, skill):
        lvl = self._lvl(skill["id"])
        if lvl >= skill["max_levels"]: return False, "Max Level"
        if not self._req_met(skill):
            rid, rlvl = skill["requires"]
            return False, f"Need {SKILL_BY_ID[rid]['name']} lv{rlvl}"
        cost = _level_cost(skill, lvl + 1)
        if self._coins() < cost: return False, f"Need {cost} coins"
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

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self.msg_t > 0: self.msg_t -= dt

            mx, my = pygame.mouse.get_pos()
            self.hovered = None
            for sid, r in self.node_rects.items():
                if r.collidepoint(mx, my):
                    self.hovered = sid

            # Animate hover/select alpha
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
                            self.selected = sid; clicked_node = True; break
                    if not clicked_node and not pygame.Rect(self._px, 0, self._pw, self.H).collidepoint(ev.pos):
                        self.selected = None
                    if self.btn_upg.collidepoint(ev.pos) and self.selected:
                        self._upgrade(SKILL_BY_ID[self.selected])
                # Double click = upgrade
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    pass  # handled above

            self._draw()
            pygame.display.flip()

    # ── drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        surf = self.screen
        surf.fill(_C_BG)
        self._draw_bg_grid(surf)
        self._draw_connections(surf)
        self._draw_nodes(surf)
        self._draw_right_panel(surf)
        self._draw_topbar(surf)

    def _draw_bg_grid(self, surf):
        # Subtle dot grid — TDS style dark background
        import random
        rng = random.Random(17)
        tree_w = self._px
        for _ in range(80):
            x = rng.randint(0, tree_w)
            y = rng.randint(0, self.H)
            phase = x * 0.009 + y * 0.005
            br = int(abs(math.sin(self.t * 0.4 + phase)) * 25 + 15)
            pygame.draw.circle(surf, (br, br + 4, br + 20), (x, y), 1)

        # Faint vertical separator lines between columns
        for col in range(2):
            cx, _ = _col_row_to_xy(col, 0)
            for row in range(4):
                _, y1 = _col_row_to_xy(col, row)
                _, y2 = _col_row_to_xy(col, row + 1) if row < 3 else (0, y1 + _ROW_GAP)

    def _draw_connections(self, surf):
        """Draw TDS-style connector lines between nodes with dots."""
        for sk in SKILLS:
            if sk["requires"] is None:
                continue
            rid = sk["requires"][0]
            r_from = self.node_rects[rid]
            r_to   = self.node_rects[sk["id"]]

            req_met = self._req_met(sk)
            from_lvl = self._lvl(rid)
            req_lvl  = sk["requires"][1]
            progress = min(1.0, from_lvl / req_lvl) if req_lvl > 0 else 1.0

            # Line colour
            if req_met:
                base_col = (60, 200, 100)
                glow_col = (80, 255, 130)
            else:
                base_col = (50, 58, 85)
                glow_col = (80, 95, 130)

            x1, y1 = r_from.centerx, r_from.bottom - 8
            x2, y2 = r_to.centerx,   r_to.top + 8

            # Draw thick dark outline, then bright line
            pygame.draw.line(surf, _lerp_color((20, 25, 40), base_col, 0.3), (x1, y1), (x2, y2), 5)
            pygame.draw.line(surf, base_col, (x1, y1), (x2, y2), 2)

            # Animated dots flowing down the line if unlocked
            total_len = math.hypot(x2 - x1, y2 - y1)
            if total_len < 1: continue
            num_dots = max(2, int(total_len // 28))
            for i in range(num_dots):
                if req_met:
                    offset = (i / num_dots + self.t * 0.4) % 1.0
                else:
                    offset = i / num_dots
                    # Show progress partial dots
                    if offset > progress:
                        dot_col = (35, 42, 65)
                    else:
                        frac = offset / max(0.001, progress)
                        dot_col = _lerp_color((50, 58, 85), glow_col, frac)
                    bx = int(x1 + (x2 - x1) * offset)
                    by = int(y1 + (y2 - y1) * offset)
                    pygame.draw.circle(surf, dot_col, (bx, by), 4)
                    pygame.draw.circle(surf, _lerp_color(dot_col, (255,255,255), 0.3), (bx, by), 2)
                    continue
                bx = int(x1 + (x2 - x1) * offset)
                by = int(y1 + (y2 - y1) * offset)
                pulse = abs(math.sin(self.t * 3 + i * 1.2)) * 0.5 + 0.5
                dc = _lerp_color(base_col, glow_col, pulse)
                pygame.draw.circle(surf, dc, (bx, by), 4)
                pygame.draw.circle(surf, _C_WHITE, (bx, by), 2)

    def _draw_nodes(self, surf):
        mx, my = pygame.mouse.get_pos()

        for sk in SKILLS:
            sid    = sk["id"]
            r      = self.node_rects[sid]
            lvl    = self._lvl(sid)
            max_l  = sk["max_levels"]
            locked = not self._req_met(sk)
            hov    = (self.hovered == sid)
            sel    = (self.selected == sid)
            anim_t = self._anim[sid]
            accent = sk["color"] if not locked else _C_LOCKED
            maxed  = (lvl >= max_l)

            # ── Outer glow (selected/hover) ──
            if anim_t > 0.05 and not locked:
                glow_alpha = int(anim_t * 55)
                glow_r = pygame.Rect(r.x - 6, r.y - 6, r.w + 12, r.h + 12)
                _alpha_rect(surf, accent, (glow_r.x, glow_r.y, glow_r.w, glow_r.h), glow_alpha, 18)

            # ── Main card background ──
            if locked:
                bg_col = (18, 22, 35)
            elif maxed:
                bg_col = _lerp_color(_C_PANEL2, accent, 0.08)
            elif sel:
                bg_col = _lerp_color(_C_PANEL2, accent, 0.15)
            else:
                bg_col = _C_PANEL2 if not hov else _lerp_color(_C_PANEL2, accent, 0.08)

            _alpha_rect(surf, bg_col, (r.x, r.y, r.w, r.h), 245, 14)

            # ── Border ──
            if maxed and not locked:
                brd = _C_GOLD
                brd_w = 2
            elif sel:
                pulse = abs(math.sin(self.t * 3)) * 0.5 + 0.5
                brd = _lerp_color(accent, _C_WHITE, pulse * 0.4)
                brd_w = 2
            elif hov and not locked:
                brd = accent
                brd_w = 2
            else:
                brd = _lerp_color(_C_BORDER, accent, 0.3) if not locked else _C_BORDER
                brd_w = 1
            pygame.draw.rect(surf, brd, r, brd_w, border_radius=14)

            # ── Left accent bar ──
            bar_col = accent if not locked else _C_LOCKED
            bar_alpha = 200 if not locked else 80
            _alpha_rect(surf, bar_col, (r.x + 2, r.y + 10, 4, r.h - 20), bar_alpha, 2)

            # ── Hex icon badge ──
            hx = r.x + 36
            hy = r.centery - 10
            hex_fill = _lerp_color((20, 25, 42), accent, 0.25) if not locked else (25, 28, 42)
            hex_brd  = accent if not locked else _C_LOCKED
            _draw_hexagon(surf, hx, hy, _HEX_R, hex_fill, hex_brd, 2)

            # Icon letter (first letter of name as stand-in)
            icon_letter = sk["name"][0].upper()
            if locked:
                icon_letter = "🔒" if False else sk["name"][0]  # keep simple
                ic = self.f_title.render(icon_letter, True, _C_LOCKED_TXT)
            else:
                ic_col = _lerp_color(_C_WHITE, accent, 0.4)
                ic = self.f_title.render(icon_letter, True, ic_col)
            surf.blit(ic, ic.get_rect(center=(hx, hy)))

            # ── Name ──
            tx = r.x + 80
            name_col = _C_LOCKED_TXT if locked else (_C_GOLD if maxed else _C_WHITE)
            ns = self.f_sub.render(sk["name"], True, name_col)
            surf.blit(ns, (tx, r.y + 12))

            # ── Effect label ──
            eff_col = _C_LOCKED_TXT if locked else _lerp_color(_C_GRAY, accent, 0.5)
            es = self.f_body.render(sk["effect_label"], True, eff_col)
            surf.blit(es, (tx, r.y + 36))

            # ── Progress bar (TDS style — segmented) ──
            bar_x = r.x + 14
            bar_y = r.y + r.h - 30
            bar_w = r.w - 28
            bar_h = 8
            seg_gap = 2
            num_segs = min(max_l, 20)  # cap displayed segments
            seg_w = (bar_w - seg_gap * (num_segs - 1)) / num_segs
            filled_segs = int(lvl / max_l * num_segs)

            for i in range(num_segs):
                sx = bar_x + i * (seg_w + seg_gap)
                if i < filled_segs:
                    if maxed:
                        sc = _C_GOLD
                    else:
                        frac = i / max(1, num_segs - 1)
                        sc = _lerp_color(accent, _lerp_color(accent, _C_WHITE, 0.3), frac)
                elif locked:
                    sc = _C_LOCKED_BAR
                else:
                    sc = (28, 33, 52)
                pygame.draw.rect(surf, sc, (int(sx), bar_y, max(1, int(seg_w)), bar_h), border_radius=2)

            # Level text
            if maxed:
                lv_col = _C_GOLD
                lv_txt = "MAX"
            elif locked:
                lv_col = _C_LOCKED_TXT
                lv_txt = f"Lv {lvl}/{max_l}"
            else:
                lv_col = _C_GRAY
                lv_txt = f"Lv {lvl}/{max_l}"
            lvs = self.f_sm.render(lv_txt, True, lv_col)
            surf.blit(lvs, lvs.get_rect(midright=(r.right - 10, bar_y + bar_h // 2)))

            # ── Coin cost badge (top-right corner) ──
            if not maxed and not locked:
                next_cost = _level_cost(sk, lvl + 1)
                can_aff = self._coins() >= next_cost
                badge_col = (40, 80, 35) if can_aff else (70, 35, 35)
                badge_txt_col = _C_GREEN if can_aff else _C_RED
                cost_s = self.f_sm.render(f"⬡ {next_cost}", True, badge_txt_col)
                bw2 = cost_s.get_width() + 10
                bx2 = r.right - bw2 - 4
                by2 = r.y + 8
                _alpha_rect(surf, badge_col, (bx2, by2, bw2, 18), 200, 5)
                surf.blit(cost_s, (bx2 + 5, by2 + 2))

    def _draw_right_panel(self, surf):
        px, py, pw, ph = self._px, self._py, self._pw, self._ph

        # Panel background — dark with subtle gradient
        _alpha_rect(surf, (10, 14, 26), (px, py, pw, ph), 255)
        _alpha_rect(surf, (20, 28, 52), (px, py, pw, 4), 255)  # top accent line
        pygame.draw.line(surf, (35, 48, 82), (px, py), (px, py + ph), 2)

        if self.selected is None:
            # Hint
            hint_lines = ["← Select a skill", "to view details"]
            for i, line in enumerate(hint_lines):
                hs = self.f_body.render(line, True, _C_GRAY2)
                surf.blit(hs, hs.get_rect(center=(px + pw // 2, ph // 2 + i * 26)))
            return

        sk  = SKILL_BY_ID[self.selected]
        lvl = self._lvl(self.selected)
        locked = not self._req_met(sk)
        maxed  = (lvl >= sk["max_levels"])
        accent = sk["color"] if not locked else _C_LOCKED

        tx = px + 22
        ty = 30

        # ── Category tag ──
        cat_col = _lerp_color((20, 28, 50), accent, 0.35)
        cat_txt = "LOCKED" if locked else ("MAXED" if maxed else "ACTIVE" if lvl > 0 else "AVAILABLE")
        cat_surf = self.f_sm.render(cat_txt, True, accent if not locked else _C_LOCKED_TXT)
        tag_w = cat_surf.get_width() + 14
        _alpha_rect(surf, cat_col, (tx, ty, tag_w, 20), 200, 4)
        pygame.draw.rect(surf, accent if not locked else _C_LOCKED, (tx, ty, tag_w, 20), 1, border_radius=4)
        surf.blit(cat_surf, (tx + 7, ty + 3))
        ty += 30

        # ── Skill name ──
        name_col = _C_GOLD if maxed else (accent if not locked else _C_LOCKED_TXT)
        # Word-wrap name if long
        ns = self.f_hdr.render(sk["name"], True, name_col)
        if ns.get_width() > pw - 30:
            words = sk["name"].split()
            lines = []
            cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                if self.f_hdr.size(test)[0] > pw - 30:
                    if cur: lines.append(cur)
                    cur = w
                else:
                    cur = test
            if cur: lines.append(cur)
            for line in lines:
                ls = self.f_hdr.render(line, True, name_col)
                surf.blit(ls, (tx, ty)); ty += 36
        else:
            surf.blit(ns, (tx, ty)); ty += 40

        # ── Hex icon large ──
        big_hx = px + pw - 52
        big_hy = 80
        hex_fill = _lerp_color((14, 18, 32), accent, 0.3) if not locked else (20, 24, 38)
        _draw_hexagon(surf, big_hx, big_hy, 42, hex_fill, accent if not locked else _C_LOCKED, 2)
        ic_big = self.f_hdr.render(sk["name"][0].upper(), True, accent if not locked else _C_LOCKED_TXT)
        surf.blit(ic_big, ic_big.get_rect(center=(big_hx, big_hy)))

        # ── Divider ──
        pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - 22, ty), 1)
        ty += 14

        # ── Level bar (big, segmented) ──
        label_s = self.f_sm.render("LEVEL PROGRESS", True, _C_GRAY2)
        surf.blit(label_s, (tx, ty)); ty += 18
        bar_w = pw - 44
        bar_h = 14
        num_segs = min(sk["max_levels"], 25)
        seg_gap = 2
        seg_w = (bar_w - seg_gap * (num_segs - 1)) / num_segs
        filled = int(lvl / sk["max_levels"] * num_segs)
        for i in range(num_segs):
            sx = tx + i * (seg_w + seg_gap)
            if i < filled:
                sc = _C_GOLD if maxed else _lerp_color(accent, _lerp_color(accent, _C_WHITE, 0.4), i / max(1, num_segs - 1))
            else:
                sc = (25, 32, 55)
            pygame.draw.rect(surf, sc, (int(sx), ty, max(1, int(seg_w)), bar_h), border_radius=3)
        ty += bar_h + 6

        lvl_txt = f"{'MAX' if maxed else lvl} / {sk['max_levels']}"
        lvl_s = self.f_num.render(lvl_txt, True, _C_GOLD if maxed else _C_WHITE)
        surf.blit(lvl_s, (tx, ty)); ty += 26

        pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - 22, ty), 1)
        ty += 14

        # ── Description ──
        desc_label = self.f_sm.render("DESCRIPTION", True, _C_GRAY2)
        surf.blit(desc_label, (tx, ty)); ty += 18
        for line in sk["desc"].split("\n"):
            ds = self.f_body.render(line, True, _C_GRAY)
            surf.blit(ds, (tx, ty)); ty += 22
        ty += 8

        # ── Current effect ──
        if lvl > 0:
            pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - 22, ty), 1)
            ty += 14
            eff_label = self.f_sm.render("CURRENT EFFECT", True, _C_GRAY2)
            surf.blit(eff_label, (tx, ty)); ty += 18
            bonus = skill_tree_bonus(self.selected, self.save_data)
            if self.selected in ("precision", "scavenger"):
                effect_str = f"{int(bonus)} shots/kills to bonus"
            else:
                effect_str = f"+{bonus * 100:.1f}%"
            es = self.f_sub.render(effect_str, True, accent)
            surf.blit(es, (tx, ty)); ty += 28

        pygame.draw.line(surf, (28, 38, 65), (tx, ty), (px + pw - 22, ty), 1)
        ty += 14

        # ── Next level cost ──
        if not maxed:
            next_cost = _level_cost(sk, lvl + 1)
            total_next = _total_cost(sk, lvl + 1)
            ok, reason = self._can_upgrade(sk)
            cost_label = self.f_sm.render("UPGRADE COST", True, _C_GRAY2)
            surf.blit(cost_label, (tx, ty)); ty += 18
            cost_col = _C_GREEN if ok else _C_RED
            coin_s = self.f_sub.render(f"⬡ {next_cost}", True, cost_col)
            surf.blit(coin_s, (tx, ty))
            tot_s = self.f_sm.render(f"total: {total_next}", True, _C_GRAY2)
            surf.blit(tot_s, (tx + coin_s.get_width() + 12, ty + 3))
            ty += 28
            if not ok and reason and not locked:
                rs = self.f_sm.render(f"✖ {reason}", True, _C_RED)
                surf.blit(rs, (tx, ty)); ty += 20
            if locked:
                rid, rlvl = sk["requires"]
                lock_s = self.f_sm.render(f"🔒 Requires {SKILL_BY_ID[rid]['name']} lv{rlvl}", True, _C_RED)
                surf.blit(lock_s, (tx, ty)); ty += 20
        else:
            max_s = self.f_sub.render("✦ MAXED OUT ✦", True, _C_GOLD)
            surf.blit(max_s, max_s.get_rect(centerx=px + pw // 2, top=ty)); ty += 30

        # ── Coins balance ──
        coin_bal = self.f_sm.render("YOUR COINS", True, _C_GRAY2)
        surf.blit(coin_bal, (tx, ty)); ty += 18
        bal_s = self.f_sub.render(f"⬡ {self._coins()}", True, _C_GOLD)
        surf.blit(bal_s, (tx, ty)); ty += 30

        # ── Feedback message ──
        if self.msg and self.msg_t > 0:
            alpha = min(255, int(self.msg_t * 180))
            mc = _C_GREEN if self.msg_ok else _C_RED
            msg_s = self.f_body.render(self.msg, True, mc)
            msg_s.set_alpha(alpha)
            surf.blit(msg_s, msg_s.get_rect(centerx=px + pw // 2, bottom=self.H - 105))

        # ── Upgrade button ──
        if not maxed:
            ok2, _ = self._can_upgrade(sk)
            br = self.btn_upg
            br.x = px + 14; br.y = self.H - 82; br.w = pw - 28; br.h = 52

            if locked:
                btn_bg  = (28, 32, 52)
                btn_brd = (50, 58, 85)
                btn_txt = "LOCKED"
                txt_col = _C_LOCKED_TXT
            elif ok2:
                # Animated glow
                pulse = abs(math.sin(self.t * 2.5)) * 0.3
                btn_bg  = _lerp_color((20, 75, 35), _lerp_color(accent, (0,0,0), 0.3), 0.2)
                btn_brd = _lerp_color(_C_GREEN, _C_WHITE, pulse)
                btn_txt = f"UPGRADE  ⬡ {_level_cost(sk, lvl+1)}"
                txt_col = _C_WHITE
                # Extra glow border
                glow_r = pygame.Rect(br.x - 2, br.y - 2, br.w + 4, br.h + 4)
                _alpha_rect(surf, _C_GREEN, (glow_r.x, glow_r.y, glow_r.w, glow_r.h), int(pulse * 80), 14)
            else:
                btn_bg  = (50, 28, 28)
                btn_brd = _C_RED
                btn_txt = "CAN'T UPGRADE"
                txt_col = (180, 80, 80)

            _alpha_rect(surf, btn_bg, (br.x, br.y, br.w, br.h), 240, 12)
            pygame.draw.rect(surf, btn_brd, br, 2, border_radius=12)
            ls = self.f_sub.render(btn_txt, True, txt_col)
            surf.blit(ls, ls.get_rect(center=br.center))

    def _draw_topbar(self, surf):
        # Gradient top strip
        _alpha_rect(surf, (10, 14, 28), (0, 0, self._px, 70), 230)
        pygame.draw.line(surf, (30, 42, 72), (0, 70), (self._px, 70), 1)

        # Title
        ts = self.f_hdr.render("SKILL TREE", True, _C_WHITE)
        surf.blit(ts, ts.get_rect(midleft=(180, 35)))

        # Gold accent on title
        glow_ts = self.f_hdr.render("SKILL TREE", True, _C_GOLD)
        glow_ts.set_alpha(30)
        surf.blit(glow_ts, glow_ts.get_rect(midleft=(182, 37)))

        # Coin display
        coin_bg = pygame.Rect(self.W - self._pw - 260, 16, 220, 38)
        _alpha_rect(surf, (12, 17, 32), (coin_bg.x, coin_bg.y, coin_bg.w, coin_bg.h), 210, 8)
        pygame.draw.rect(surf, (60, 80, 130), coin_bg, 1, border_radius=8)
        coin_txt = self.f_sub.render(f"⬡  {self._coins()} coins", True, _C_GOLD)
        surf.blit(coin_txt, coin_txt.get_rect(center=coin_bg.center))

        # Column labels
        col_labels = ["Combat", "Economy"]
        for col in range(2):
            cx, _ = _col_row_to_xy(col, 0)
            ls = self.f_sm.render(col_labels[col].upper(), True, _C_GRAY2)
            surf.blit(ls, ls.get_rect(center=(cx, 80)))
            pygame.draw.line(surf, (30, 40, 68),
                             (cx - _NODE_W // 2, 92), (cx + _NODE_W // 2, 92), 1)

        # Back button
        b = self.btn_back
        hov = b.collidepoint(pygame.mouse.get_pos())
        bg_c = (25, 35, 62) if hov else (15, 20, 38)
        brd_c = (80, 120, 210) if hov else (45, 60, 100)
        _alpha_rect(surf, bg_c, (b.x, b.y, b.w, b.h), 230, 8)
        pygame.draw.rect(surf, brd_c, b, 1, border_radius=8)
        bs = self.f_body.render("◀  Back", True, _C_WHITE if hov else _C_GRAY)
        surf.blit(bs, bs.get_rect(center=b.center))