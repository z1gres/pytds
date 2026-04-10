"""
skill_tree.py  — Skill Tree screen for Tower Defense
Сохраняется в savegame.json под ключом "skill_tree": {skill_id: level, ...}
"""

import pygame
import math
import sys

# ── Skill definitions ──────────────────────────────────────────────────────────
# Each skill: id, name, desc, max_levels, effect_per_level, unit (coin/stat label),
#             base_cost, exp_value, requires (id, min_level) or None
#             color accent, position in tree (col, row)  — used for layout only

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
        "col": 0, "row": 1,
    },
    # ── Column 1: Debuff / Crits ───────────────────────────────────────────────
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
        "col": 0, "row": 3,
    },
    # ── Column 2: Economy ────────────────────────────────────────────────────
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
        "col": 1, "row": 3,
    },
]

# Build lookup
SKILL_BY_ID = {s["id"]: s for s in SKILLS}


def _level_cost(skill, level_1based):
    """Cost to buy the Nth level (1-indexed)."""
    return int(skill["base_cost"] * (skill["exp_value"] ** (level_1based - 1)))


def _total_cost(skill, levels):
    """Total coins spent for `levels` levels."""
    return sum(_level_cost(skill, i+1) for i in range(levels))


def skill_tree_bonus(skill_id, save_data):
    """Return current bonus value (float multiplier or int) for a skill."""
    levels = save_data.get("skill_tree", {}).get(skill_id, 0)
    if levels == 0:
        return 0
    sk = SKILL_BY_ID[skill_id]
    # return total % increase (or shot reduction)
    if skill_id == "enhanced_optics":      return levels * 0.005   # +0.5% per level
    if skill_id == "improved_gunpowder":   return levels * 0.005
    if skill_id == "fight_dirty":          return levels * 0.01
    if skill_id == "precision":            return 29 - levels       # shots needed
    if skill_id == "resourcefulness":      return 0.3333 + levels * 0.012
    if skill_id == "bigger_budget":        return levels * 0.01
    if skill_id == "stonks":               return levels * 0.005
    if skill_id == "scavenger":            return 29 - levels
    return 0


# ── Layout constants ───────────────────────────────────────────────────────────
_COL_X  = [340, 760]           # x centres for columns 0 and 1
_ROW_Y  = [180, 360, 540, 720] # y centres for rows 0-3
_NODE_W = 300
_NODE_H = 110

_C_BG      = (14, 18, 28)
_C_PANEL   = (22, 28, 44)
_C_BORDER  = (60, 70, 100)
_C_WHITE   = (230, 235, 245)
_C_GOLD    = (255, 200, 50)
_C_GRAY    = (120, 130, 150)
_C_RED     = (220, 60, 60)
_C_GREEN   = (80, 200, 100)
_C_LOCKED  = (50, 55, 70)
_C_LOCKED_TEXT = (90, 100, 120)


class SkillTreeScreen:
    def __init__(self, screen, save_data):
        self.screen = screen
        self.save_data = save_data
        self.W = screen.get_width()
        self.H = screen.get_height()
        self.t = 0.0
        self.tooltip = None       # skill id currently hovered
        self.selected = None      # skill id selected / clicked
        self.msg = ""             # feedback message
        self.msg_t = 0.0

        # fonts
        self.f_title = pygame.font.SysFont("segoeui", 36, bold=True)
        self.f_head  = pygame.font.SysFont("segoeui", 20, bold=True)
        self.f_body  = pygame.font.SysFont("segoeui", 17)
        self.f_small = pygame.font.SysFont("segoeui", 15)
        self.f_cost  = pygame.font.SysFont("consolas", 16, bold=True)

        # Upgrade button (shown in detail panel)
        self.btn_upgrade = pygame.Rect(self.W // 2 + 60, self.H - 120, 240, 52)
        self.btn_back    = pygame.Rect(30, 30, 160, 46)

        # Node rects, keyed by skill id
        self.node_rects = {}
        for sk in SKILLS:
            cx = _COL_X[sk["col"]]
            cy = _ROW_Y[sk["row"]]
            r = pygame.Rect(cx - _NODE_W//2, cy - _NODE_H//2, _NODE_W, _NODE_H)
            self.node_rects[sk["id"]] = r

    # ── helpers ───────────────────────────────────────────────────────────────
    def _st(self):
        return self.save_data.setdefault("skill_tree", {})

    def _lvl(self, sid):
        return self._st().get(sid, 0)

    def _coins(self):
        return self.save_data.get("coins", 0)

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
            req_name = SKILL_BY_ID[rid]["name"]
            return False, f"Requires {req_name} lvl {rlvl}"
        cost = _level_cost(skill, lvl + 1)
        if self._coins() < cost:
            return False, f"Need {cost} coins"
        return True, ""

    def _upgrade(self, skill):
        ok, reason = self._can_upgrade(skill)
        if not ok:
            self.msg = reason; self.msg_t = 2.0; return
        lvl = self._lvl(skill["id"])
        cost = _level_cost(skill, lvl + 1)
        self._st()[skill["id"]] = lvl + 1
        self.save_data["coins"] = self._coins() - cost
        # persist
        from game_core import write_save
        write_save(self.save_data)
        self.msg = f"Upgraded {skill['name']} to lvl {lvl+1}!"
        self.msg_t = 2.0

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            self.t += dt
            if self.msg_t > 0: self.msg_t -= dt

            mx, my = pygame.mouse.get_pos()
            self.tooltip = None
            for sid, r in self.node_rects.items():
                if r.collidepoint(mx, my):
                    self.tooltip = sid

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.collidepoint(ev.pos):
                        return
                    # node click
                    for sid, r in self.node_rects.items():
                        if r.collidepoint(ev.pos):
                            self.selected = sid
                            break
                    # upgrade button
                    if self.btn_upgrade.collidepoint(ev.pos) and self.selected:
                        self._upgrade(SKILL_BY_ID[self.selected])

            self._draw()
            pygame.display.flip()

    # ── drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        surf = self.screen
        surf.fill(_C_BG)
        self._draw_bg(surf)
        self._draw_arrows(surf)
        self._draw_nodes(surf)
        self._draw_detail_panel(surf)
        self._draw_header(surf)

    def _draw_bg(self, surf):
        # subtle animated grid
        import random
        random.seed(42)
        for i in range(120):
            sx = random.randint(0, self.W)
            sy = random.randint(0, self.H)
            phase = sx * 0.006 + i * 0.25
            br = int(abs(math.sin(self.t * 0.6 + phase)) * 80 + 20)
            pygame.draw.circle(surf, (br, br, min(255, br + 40)), (sx, sy), 1)
        random.seed()

    def _draw_arrows(self, surf):
        for sk in SKILLS:
            if sk["requires"] is None:
                continue
            rid = sk["requires"][0]
            r_from = self.node_rects[rid]
            r_to   = self.node_rects[sk["id"]]
            x1 = r_from.centerx; y1 = r_from.bottom + 4
            x2 = r_to.centerx;   y2 = r_to.top - 4
            col = (80, 100, 160)
            if self._req_met(sk):
                col = (100, 200, 120)
            pygame.draw.line(surf, col, (x1, y1), (x2, y2), 3)
            # arrowhead
            angle = math.atan2(y2 - y1, x2 - x1)
            for da in (0.5, -0.5):
                ax = x2 - math.cos(angle + da) * 12
                ay = y2 - math.sin(angle + da) * 12
                pygame.draw.line(surf, col, (x2, y2), (int(ax), int(ay)), 3)

    def _draw_nodes(self, surf):
        mx, my = pygame.mouse.get_pos()
        for sk in SKILLS:
            sid = sk["id"]
            r = self.node_rects[sid]
            lvl = self._lvl(sid)
            max_lvl = sk["max_levels"]
            locked = not self._req_met(sk)
            hov = r.collidepoint(mx, my)
            sel = (self.selected == sid)
            accent = sk["color"] if not locked else _C_LOCKED

            # Background
            bg = _C_LOCKED if locked else (_C_PANEL if not sel else tuple(max(0, c - 10) for c in _C_PANEL))
            if hov and not locked:
                bg = tuple(min(255, c + 12) for c in bg)
            s_bg = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(s_bg, (*bg, 230), (0, 0, r.w, r.h), border_radius=12)
            surf.blit(s_bg, r.topleft)

            # Border
            brd_col = accent if (sel or hov) else tuple(c // 2 for c in accent)
            pygame.draw.rect(surf, brd_col, r, 2, border_radius=12)

            # Left accent stripe
            stripe = pygame.Surface((5, r.h - 12), pygame.SRCALPHA)
            stripe.fill((*accent, 160 if not locked else 60))
            surf.blit(stripe, (r.x + 3, r.y + 6))

            # Name
            name_col = _C_LOCKED_TEXT if locked else _C_WHITE
            ns = self.f_head.render(sk["name"], True, name_col)
            surf.blit(ns, (r.x + 18, r.y + 10))

            # Effect label
            eff_col = _C_LOCKED_TEXT if locked else accent
            es = self.f_small.render(sk["effect_label"], True, eff_col)
            surf.blit(es, (r.x + 18, r.y + 36))

            # Progress bar
            bar_x = r.x + 18; bar_y = r.y + r.h - 28
            bar_w = r.w - 36; bar_h = 10
            pygame.draw.rect(surf, (30, 35, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            if lvl > 0:
                fill_w = int(bar_w * lvl / max_lvl)
                fill_col = accent if not locked else _C_LOCKED
                pygame.draw.rect(surf, fill_col, (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            # level text
            lvl_s = self.f_small.render(f"Lv {lvl}/{max_lvl}", True, _C_GRAY if locked else _C_WHITE)
            surf.blit(lvl_s, (r.right - lvl_s.get_width() - 12, r.y + r.h - 26))

    def _draw_detail_panel(self, surf):
        # Right panel
        px = self.W // 2 + 20
        py = 80
        pw = self.W - px - 30
        ph = self.H - py - 20
        s = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(s, (18, 22, 38, 220), (0, 0, pw, ph), border_radius=14)
        surf.blit(s, (px, py))
        pygame.draw.rect(surf, (60, 70, 110), pygame.Rect(px, py, pw, ph), 2, border_radius=14)

        if self.selected is None:
            hint = self.f_body.render("Select skill for details", True, _C_GRAY)
            surf.blit(hint, hint.get_rect(center=(px + pw // 2, py + ph // 2)))
            return

        sk = SKILL_BY_ID[self.selected]
        lvl = self._lvl(self.selected)
        locked = not self._req_met(sk)
        accent = sk["color"] if not locked else _C_LOCKED
        tx = px + 20; ty = py + 18

        # Skill name
        ns = self.f_title.render(sk["name"], True, accent)
        surf.blit(ns, (tx, ty)); ty += 44

        # Level progress
        pbar_w = pw - 40
        pygame.draw.rect(surf, (30, 35, 50), (tx, ty, pbar_w, 14), border_radius=6)
        if lvl > 0:
            fw = int(pbar_w * lvl / sk["max_levels"])
            pygame.draw.rect(surf, accent, (tx, ty, fw, 14), border_radius=6)
        lvl_s = self.f_body.render(f"Level: {lvl} / {sk['max_levels']}", True, _C_WHITE)
        surf.blit(lvl_s, (tx, ty + 20)); ty += 50

        # Description
        for line in sk["desc"].split("\n"):
            ds = self.f_body.render(line, True, _C_GRAY)
            surf.blit(ds, (tx, ty)); ty += 26
        ty += 10

        # Current effect
        if lvl > 0:
            bonus = skill_tree_bonus(self.selected, self.save_data)
            if self.selected in ("precision", "scavenger"):
                effect_str = f"Currently: {int(bonus)} shots/kills to bonus"
            else:
                effect_str = f"Currently: +{bonus * 100:.1f}%"
            es = self.f_body.render(effect_str, True, accent)
            surf.blit(es, (tx, ty)); ty += 30

        # Next level cost
        if lvl < sk["max_levels"]:
            next_cost = _level_cost(sk, lvl + 1)
            total_c = _total_cost(sk, lvl)
            ok, reason = self._can_upgrade(sk)
            cost_col = _C_GREEN if ok else _C_RED
            cs = self.f_body.render(f"Cost: {next_cost} coins (total: {_total_cost(sk, lvl+1)})", True, cost_col)
            surf.blit(cs, (tx, ty)); ty += 26
            if not ok:
                rs = self.f_small.render(reason, True, _C_RED)
                surf.blit(rs, (tx, ty)); ty += 22
        else:
            ms = self.f_body.render("MAX LEVEL", True, _C_GOLD)
            surf.blit(ms, (tx, ty)); ty += 26

        # Coin balance
        coin_s = self.f_body.render(f"Coins: {self._coins()}", True, _C_GOLD)
        surf.blit(coin_s, (tx, ty)); ty += 30

        # Upgrade button
        if lvl < sk["max_levels"]:
            ok2, _ = self._can_upgrade(sk)
            btn_col = (30, 100, 50) if ok2 else (60, 30, 30)
            btn_brd = (80, 220, 100) if ok2 else (180, 60, 60)
            br = self.btn_upgrade
            br.x = px + 20; br.y = py + ph - 72; br.w = pw - 40; br.h = 48
            pygame.draw.rect(surf, btn_col, br, border_radius=12)
            pygame.draw.rect(surf, btn_brd, br, 2, border_radius=12)
            label = "UPGRADE" if ok2 else "LOCKED"
            ls = self.f_head.render(label, True, _C_WHITE)
            surf.blit(ls, ls.get_rect(center=br.center))

        # Feedback msg
        if self.msg and self.msg_t > 0:
            alpha = min(255, int(self.msg_t * 255))
            ms_surf = self.f_body.render(self.msg, True, _C_GREEN)
            ms_surf.set_alpha(alpha)
            surf.blit(ms_surf, ms_surf.get_rect(center=(px + pw // 2, py + ph - 90)))

    def _draw_header(self, surf):
        # Title
        ts = self.f_title.render("SKILL TREE", True, (120, 180, 255))
        surf.blit(ts, ts.get_rect(midleft=(220, 42)))

        # Coin display
        coin_s = self.f_head.render(f"Coins: {self._coins()}", True, _C_GOLD)
        surf.blit(coin_s, coin_s.get_rect(midright=(self.W // 2 - 40, 42)))

        # Back button
        b = self.btn_back
        hov = b.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf, (28, 36, 62) if hov else (18, 22, 38), b, border_radius=10)
        pygame.draw.rect(surf, (80, 120, 220) if hov else (50, 70, 140), b, 2, border_radius=10)
        bs = self.f_head.render("← Back", True, _C_WHITE)
        surf.blit(bs, bs.get_rect(center=b.center))