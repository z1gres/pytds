"""
lang.py  —  Full EN / RU localisation for pyTDS
Usage:
    from lang import t, set_lang, get_lang
    label = t("settings.audio")   # returns "AUDIO" or "АУДИО"
"""

_LANG = "en"  # default; overwritten by game.py after settings load

_STRINGS = {

    # ══════════════════════════════════════════════════════════════════
    # SETTINGS SCREEN
    # ══════════════════════════════════════════════════════════════════
    "settings.title":              {"en": "SETTINGS",                   "ru": "НАСТРОЙКИ"},
    "settings.tab.audio":          {"en": "AUDIO",                      "ru": "АУДИО"},
    "settings.tab.graphics":       {"en": "GRAPHICS",                   "ru": "ГРАФИКА"},
    "settings.tab.display":        {"en": "DISPLAY",                    "ru": "ДИСПЛЕЙ"},
    "settings.tab.language":       {"en": "LANGUAGE",                   "ru": "ЯЗЫК"},

    "settings.audio.section":      {"en": "AUDIO OPTIONS",              "ru": "ПАРАМЕТРЫ ЗВУКА"},
    "settings.music_volume":       {"en": "Music Volume",               "ru": "Громкость музыки"},
    "settings.sfx_volume":         {"en": "SFX Volume",                 "ru": "Громкость эффектов"},
    "settings.mute_music":         {"en": "Mute Music",                 "ru": "Выкл. музыку"},
    "settings.mute_sfx":           {"en": "Mute SFX",                   "ru": "Выкл. эффекты"},
    "settings.auto_skip":          {"en": "Auto Skip",                  "ru": "Авто-пропуск"},
    "settings.sell_confirm":       {"en": "Confirm Before Sell",        "ru": "Подтверждение продажи"},
    "settings.fast_forward":       {"en": "Auto X2 Speed",              "ru": "Авто x2 скорость"},
    "settings.linux_mode":         {"en": "Linux Mode",                 "ru": "Режим Linux"},
    "settings.wave_navigator":     {"en": "Wave Navigator Button",      "ru": "Кнопка навигатора волн"},
    "wavenav.title":               {"en": "Wave Navigator",             "ru": "Навигатор волн"},
    "wavenav.line1":               {"en": "Enables the WAVES button: browse waves and jump to any of them.", "ru": "Включает кнопку WAVES: просмотр волн и переход к любой из них."},
    "wavenav.line2":               {"en": "WARNING: while this is ON, you will earn NO coin rewards.", "ru": "ВНИМАНИЕ: пока она включена, монеты-награды начисляться НЕ будут."},
    "wavenav.line3":               {"en": "Turn it off to earn rewards again.", "ru": "Выключите её, чтобы снова получать награды."},
    "wavenav.continue":            {"en": "Got it",                     "ru": "Понятно"},

    "settings.gfx.section":        {"en": "VISUAL OPTIONS",             "ru": "ВИЗУАЛЬНЫЕ НАСТРОЙКИ"},
    "settings.colored_range":      {"en": "Colored Range Rings",        "ru": "Цветные кольца радиуса"},
    "settings.screen_shake":       {"en": "Screen Shake",               "ru": "Тряска экрана"},
    "settings.particles":          {"en": "Particles & Effects",        "ru": "Частицы и эффекты"},
    "settings.show_damage":        {"en": "Damage / Money Numbers",     "ru": "Числа урона и монет"},
    "settings.compact_numbers":    {"en": "Compact Numbers  (1k)",      "ru": "Сжатые числа (1k)"},
    "settings.show_grid":          {"en": "Show Grid",                  "ru": "Показывать сетку"},
    "settings.show_fps":           {"en": "Show FPS",                   "ru": "Показывать FPS"},
    "settings.show_range_always":  {"en": "Always Show Range",          "ru": "Всегда показывать радиус"},
    "settings.low_quality":        {"en": "Low Detail Mode",            "ru": "Низкая детализация"},
    "settings.unlock_fps":         {"en": "Unlock FPS",                 "ru": "Разблокировать FPS"},
    "settings.no_tower_details":   {"en": "No Tower Details",           "ru": "Без деталей башен"},
    "settings.upgrade_preview":    {"en": "Upgrade Preview Range",      "ru": "Предпросмотр апгрейда"},

    "settings.display.section":    {"en": "WINDOW MODE",                "ru": "РЕЖИМ ОКНА"},
    "settings.windowed":           {"en": "Windowed",                   "ru": "В окне"},
    "settings.fullscreen":         {"en": "Fullscreen",                 "ru": "Полноэкранный"},
    "settings.resolution":         {"en": "RESOLUTION",                 "ru": "РАЗРЕШЕНИЕ"},
    "settings.res_hint":           {"en": "Changes apply immediately. Restart may be needed.",
                                    "ru": "Изменения применяются сразу. Может потребоваться перезапуск."},
    "settings.menu_style":         {"en": "MENU STYLE",                 "ru": "СТИЛЬ МЕНЮ"},
    "settings.style.void":         {"en": "Void",                       "ru": "Пустота"},
    "settings.style.modern":       {"en": "Modern",                     "ru": "Модерн"},
    "settings.style.vertical":     {"en": "Vertical",                   "ru": "Вертикальный"},
    "settings.style.gothic":       {"en": "Gothic",                     "ru": "Готика"},

    "settings.lang.section":       {"en": "SELECT LANGUAGE",            "ru": "ВЫБЕРИТЕ ЯЗЫК"},
    "settings.lang.hint":          {"en": "Language change applies immediately.",
                                    "ru": "Язык меняется сразу."},

    # ══════════════════════════════════════════════════════════════════
    # LINUX MODE MODAL
    # ══════════════════════════════════════════════════════════════════
    "linux.category":              {"en": "SYSTEM  //  LINUX MODE",
                                    "ru": "СИСТЕМА  //  РЕЖИМ LINUX"},
    "linux.title":                 {"en": "Compatibility not guaranteed",
                                    "ru": "Совместимость не гарантирована"},
    "linux.line1":                 {"en": "Designed for Arch Linux + KDE Plasma + Wayland.",
                                    "ru": "Режим разработан для Arch Linux + KDE Plasma + Wayland."},
    "linux.line2":                 {"en": "Behaviour may differ on other systems.",
                                    "ru": "На других системах поведение может отличаться."},
    "linux.line3":                 {"en": "Restart the game to apply changes.",
                                    "ru": "Для применения изменений перезапустите игру."},
    "linux.continue":              {"en": "CONTINUE",                   "ru": "ПРОДОЛЖИТЬ"},
    "linux.click_hint":            {"en": "click to continue",          "ru": "нажмите для продолжения"},

    # ══════════════════════════════════════════════════════════════════
    # GENERAL UI
    # ══════════════════════════════════════════════════════════════════
    "ui.back":                     {"en": "← BACK",                     "ru": "← НАЗАД"},
    "ui.back_short":               {"en": "Back",                       "ru": "Назад"},
    "ui.confirm":                  {"en": "CONFIRM",                    "ru": "ПОДТВЕРДИТЬ"},
    "ui.confirm_q":                {"en": "CONFIRM?",                   "ru": "ПОДТВЕРДИТЬ?"},
    "ui.accept":                   {"en": "ACCEPT",                     "ru": "ПРИНЯТЬ"},
    "ui.close":                    {"en": "Close",                      "ru": "Закрыть"},
    "ui.cancel":                   {"en": "CANCEL",                     "ru": "ОТМЕНА"},
    "ui.reset":                    {"en": "RESET TO DEFAULT",           "ru": "СБРОСИТЬ ПО УМОЛЧАНИЮ"},
    "ui.max_level":                {"en": "✓ MAX LEVEL",                "ru": "✓ МАКС. УРОВЕНЬ"},
    "ui.cant_upgrade_partner":     {"en": "Can't upgrade partner's tower",
                                    "ru": "Нельзя апгрейдить башню партнёра"},
    "ui.partner_tower":            {"en": "Partner's tower",            "ru": "Башня партнёра"},

    # ══════════════════════════════════════════════════════════════════
    # MAIN MENU
    # ══════════════════════════════════════════════════════════════════
    "menu.play":                   {"en": "PLAY",                       "ru": "ИГРАТЬ"},
    "menu.loadout":                {"en": "LOADOUT",                    "ru": "СНАРЯЖЕНИЕ"},
    "menu.settings":               {"en": "SETTINGS",                   "ru": "НАСТРОЙКИ"},
    "menu.profile":                {"en": "PROFILE",                    "ru": "ПРОФИЛЬ"},
    "menu.skill_tree":             {"en": "SKILL TREE",                 "ru": "ДРЕВО НАВЫКОВ"},
    "menu.quit":                   {"en": "QUIT",                       "ru": "ВЫЙТИ"},

    # ══════════════════════════════════════════════════════════════════
    # MODE / MAP SELECT
    # ══════════════════════════════════════════════════════════════════
    "mode.select":                 {"en": "SELECT MODE",                "ru": "ВЫБОР РЕЖИМА"},
    "map.select":                  {"en": "SELECT MAP",                 "ru": "ВЫБОР КАРТЫ"},

    "mode.easy":                   {"en": "EASY",                       "ru": "ЛЁГКИЙ"},
    "mode.fallen":                 {"en": "FALLEN",                     "ru": "ПАДШИЙ"},
    "mode.frosty":                 {"en": "FROSTY",                     "ru": "МОРОЗНЫЙ"},
    "mode.infernal":               {"en": "INFERNAL",                   "ru": "ИНФЕРНАЛЬНЫЙ"},
    "mode.sandbox":                {"en": "SANDBOX",                    "ru": "ПЕСОЧНИЦА"},
    "mode.hardcore":               {"en": "HARDCORE",                   "ru": "ХАРДКОР"},

    "mode.easy.desc":              {"en": "Classic tower defence. Good for beginners.",
                                    "ru": "Классическая башенная защита. Хорошо для новичков."},
    "mode.fallen.desc":            {"en": "Tougher enemies with unique mechanics.",
                                    "ru": "Более сильные враги с уникальной механикой."},
    "mode.frosty.desc":            {"en": "4-lane icy battlefield. Manage all lanes at once.",
                                    "ru": "4-полосное ледяное поле боя. Управляйте всеми линиями."},
    "mode.infernal.desc":          {"en": "Extreme challenge for veteran players.",
                                    "ru": "Экстремальный вызов для опытных игроков."},
    "mode.sandbox.desc":           {"en": "No rules. Build anything, experiment freely.",
                                    "ru": "Без правил. Стройте всё что угодно."},
    "mode.hardcore.desc":          {"en": "One life. No mistakes allowed.",
                                    "ru": "Одна жизнь. Ошибки не прощаются."},

    "mode.stat.hp":                {"en": "HP:",                        "ru": "ОЖ:"},
    "mode.stat.start_cash":        {"en": "Starting cash:",             "ru": "Начальные деньги:"},
    "mode.stat.hp_inf":            {"en": "HP: ∞",                      "ru": "ОЖ: ∞"},
    "mode.stat.cash_inf":          {"en": "Starting cash: ∞",          "ru": "Нач. деньги: ∞"},

    # Map names
    "map.bridge":                  {"en": "The Bridge",                 "ru": "Мост"},
    "map.sturn":                   {"en": "S-Turn",                     "ru": "S-Поворот"},
    "map.4lane":                   {"en": "4-lane",                     "ru": "4 полосы"},
    "map.april_fools":             {"en": "April Fools 2026",           "ru": "День дурака 2026"},
    "map.uturn":                   {"en": "U-Turn",                     "ru": "U-Поворот"},
    "map.labyrinth":               {"en": "Labyrinth",                  "ru": "Лабиринт"},

    # ══════════════════════════════════════════════════════════════════
    # IN-GAME HUD
    # ══════════════════════════════════════════════════════════════════
    "hud.wave":                    {"en": "Wave:",                      "ru": "Волна:"},
    "hud.wave_sandbox":            {"en": "SANDBOX",                    "ru": "ПЕСОЧНИЦА"},
    "hud.hp":                      {"en": "HP",                        "ru": "ОЖ"},
    "hud.money":                   {"en": "Money",                      "ru": "Деньги"},
    "hud.lives":                   {"en": "Lives",                      "ru": "Жизни"},
    "hud.speed":                   {"en": "SPEED",                      "ru": "СКОРОСТЬ"},
    "hud.paused":                  {"en": "PAUSED",                     "ru": "ПАУЗА"},
    "hud.next_wave":               {"en": "Next Wave",                  "ru": "Следующая волна"},
    "hud.start_wave":              {"en": "START WAVE",                 "ru": "НАЧАТЬ ВОЛНУ"},
    "hud.coins":                   {"en": "Coins:",                     "ru": "Монеты:"},
    "hud.time_left":               {"en": "Time Left:",                 "ru": "Осталось времени:"},

    # ══════════════════════════════════════════════════════════════════
    # TOWER PANEL / UPGRADE MENU
    # ══════════════════════════════════════════════════════════════════
    "tower.upgrade":               {"en": "UPGRADE",                    "ru": "УЛУЧШИТЬ"},
    "tower.sell":                  {"en": "Sell:",                      "ru": "Продать:"},
    "tower.sell_btn":              {"en": "SELL",                       "ru": "ПРОДАТЬ"},
    "tower.sell_val":              {"en": "Sell: ${val}",               "ru": "Продать: ${val}"},
    "tower.place":                 {"en": "Place",                      "ru": "Поставить"},
    "tower.level":                 {"en": "Level:",                     "ru": "Уровень:"},
    "tower.stats":                 {"en": "STATS",                      "ru": "ХАРАКТЕРИСТИКИ"},
    "tower.ability":               {"en": "Ability",                    "ru": "Способность"},
    "tower.ability_ready":         {"en": "CLICK / [F]",               "ru": "КЛИК / [F]"},
    "tower.ability_cd":            {"en": "CD {cd:.1f}s",               "ru": "КД {cd:.1f}с"},
    "tower.zenith_award":          {"en": "⚔ Zenith (Award)",           "ru": "⚔ Зенит (Награда)"},
    "tower.target_mode":           {"en": "Target Mode:",               "ru": "Режим цели:"},

    # Targeting modes
    "target.first":                {"en": "First",                      "ru": "Первый"},
    "target.last":                 {"en": "Last",                       "ru": "Последний"},
    "target.weakest":              {"en": "Weakest",                    "ru": "Слабейший"},
    "target.strongest":            {"en": "Strongest",                  "ru": "Сильнейший"},
    "target.closest":              {"en": "Closest",                    "ru": "Ближайший"},
    "target.farthest":             {"en": "Farthest",                   "ru": "Дальний"},
    "target.random":               {"en": "Random",                     "ru": "Случайный"},

    # Tower stat labels
    "stat.damage":                 {"en": "Damage",                     "ru": "Урон"},
    "stat.firerate":               {"en": "Firerate",                   "ru": "Скорострельность"},
    "stat.range":                  {"en": "Range",                      "ru": "Дальность"},
    "stat.income":                 {"en": "Income",                     "ru": "Доход"},
    "stat.hidden_det":             {"en": "HidDet",                     "ru": "ОбнСкрытых"},
    "stat.yes":                    {"en": "YES",                        "ru": "ДА"},
    "stat.no":                     {"en": "no",                         "ru": "нет"},

    # ══════════════════════════════════════════════════════════════════
    # SANDBOX ADMIN PANEL
    # ══════════════════════════════════════════════════════════════════
    "sandbox.title":               {"en": "SANDBOX ADMIN PANEL",        "ru": "ПАНЕЛЬ АДМИНИСТРАТОРА"},
    "sandbox.tab.enemies":         {"en": "ENEMIES",                    "ru": "ВРАГИ"},
    "sandbox.tab.units":           {"en": "UNITS",                      "ru": "ЮНИТЫ"},
    "sandbox.tab.map":             {"en": "MAP",                        "ru": "КАРТА"},
    "sandbox.tab.mode":            {"en": "MODE",                       "ru": "РЕЖИМ"},
    "sandbox.tab.misc":            {"en": "MISC",                       "ru": "РАЗНОЕ"},
    "sandbox.drag_hint":           {"en": "DRAG ELEMENTS TO CUSTOMIZE LAYOUT",
                                    "ru": "ПЕРЕТАЩИТЕ ЭЛЕМЕНТЫ ДЛЯ НАСТРОЙКИ ИНТЕРФЕЙСА"},

    # HUD widget labels (layout editor)
    "hud.widget.wave":             {"en": "Wave Info",                  "ru": "Информация о волне"},
    "hud.widget.hp":               {"en": "HP Bar",                     "ru": "Полоса ОЖ"},
    "hud.widget.money":            {"en": "Money Counter",              "ru": "Счётчик денег"},
    "hud.widget.upgrade":          {"en": "Upgrade Menu",               "ru": "Меню улучшений"},

    # ══════════════════════════════════════════════════════════════════
    # GAME OVER / VICTORY SCREENS
    # ══════════════════════════════════════════════════════════════════
    "end.victory":                 {"en": "TRIUMPH!",                   "ru": "ТРИУМФ!"},
    "end.defeat":                  {"en": "DEFEAT!",                    "ru": "ПОРАЖЕНИЕ!"},
    "end.wave":                    {"en": "Wave:",                      "ru": "Волна:"},
    "end.play_again":              {"en": "PLAY AGAIN",                 "ru": "ИГРАТЬ СНОВА"},
    "end.main_menu":               {"en": "MAIN MENU",                  "ru": "ГЛАВНОЕ МЕНЮ"},
    "end.next":                    {"en": "NEXT",                       "ru": "ДАЛЕЕ"},

    # ══════════════════════════════════════════════════════════════════
    # LOADOUT SCREEN
    # ══════════════════════════════════════════════════════════════════
    "loadout.title":               {"en": "LOADOUT",                    "ru": "СНАРЯЖЕНИЕ"},
    "loadout.slot":                {"en": "SLOT {n}",                   "ru": "СЛОТ {n}"},
    "loadout.coins":               {"en": "Coins: {n}",                 "ru": "Монеты: {n}"},

    # ══════════════════════════════════════════════════════════════════
    # PROFILE SCREEN
    # ══════════════════════════════════════════════════════════════════
    "profile.win_rate":            {"en": "WIN RATE",                   "ru": "ПОБЕДЫ %"},
    "profile.wins":                {"en": "WINS",                       "ru": "ПОБЕДЫ"},
    "profile.default_nick":        {"en": "Player",                     "ru": "Игрок"},

    # ══════════════════════════════════════════════════════════════════
    # SKILL TREE
    # ══════════════════════════════════════════════════════════════════
    "skill.title":                 {"en": "SKILL TREE",                 "ru": "ДРЕВО НАВЫКОВ"},
    "skill.coins":                 {"en": "Coins: {n}",                 "ru": "Монеты: {n}"},
    "skill.back":                  {"en": "← Back",                     "ru": "← Назад"},
    "skill.select_hint":           {"en": "Select skill for details",   "ru": "Выберите навык для подробностей"},
    "skill.level":                 {"en": "Level: {cur} / {max}",       "ru": "Уровень: {cur} / {max}"},
    "skill.lv_badge":              {"en": "Lv {cur}/{max}",             "ru": "Ур {cur}/{max}"},
    "skill.cost":                  {"en": "Cost: {cost} coins (total: {total})",
                                    "ru": "Цена: {cost} монет (итого: {total})"},
    "skill.max_level":             {"en": "MAX LEVEL",                  "ru": "МАКС. УРОВЕНЬ"},
    "skill.req_level":             {"en": "Requires {name} lvl {lvl}",  "ru": "Требуется {name} ур. {lvl}"},
    "skill.need_coins":            {"en": "Need {n} coins",             "ru": "Нужно {n} монет"},
    "skill.upgraded":              {"en": "Upgraded {name} to lvl {lvl}!",
                                    "ru": "{name} улучшен до ур. {lvl}!"},
    "skill.effect_shots":          {"en": "Currently: {n} shots/kills to bonus",
                                    "ru": "Сейчас: {n} выстрелов/убийств до бонуса"},
    "skill.effect_pct":            {"en": "Currently: +{pct:.1f}%",     "ru": "Сейчас: +{pct:.1f}%"},

    # Individual skill names & descriptions
    "skill.enhanced_optics.name":      {"en": "Enhanced Optics",        "ru": "Улучшенная оптика"},
    "skill.enhanced_optics.desc":      {"en": "Tower range +0.5% per level.",
                                        "ru": "Дальность башен +0.5% за уровень."},
    "skill.enhanced_optics.effect":    {"en": "+0.5% range",            "ru": "+0.5% дальность"},

    "skill.improved_gunpowder.name":   {"en": "Improved Gunpowder",     "ru": "Улучшенный порох"},
    "skill.improved_gunpowder.desc":   {"en": "AoE radius +0.5% per level.\nRequires: Enhanced Optics 10.",
                                        "ru": "Радиус АоЕ +0.5% за уровень.\nТребуется: Улучшенная оптика 10."},
    "skill.improved_gunpowder.effect": {"en": "+0.5% AoE",              "ru": "+0.5% АоЕ"},

    "skill.fight_dirty.name":          {"en": "Fight Dirty",            "ru": "Грязная борьба"},
    "skill.fight_dirty.desc":          {"en": "Debuff duration +1% per level.\nRequires: Improved Gunpowder 10.",
                                        "ru": "Длительность дебаффов +1% за уровень.\nТребуется: Улучшенный порох 10."},
    "skill.fight_dirty.effect":        {"en": "+1% debuff dur.",        "ru": "+1% длит. дебаффов"},

    "skill.precision.name":            {"en": "Precision",              "ru": "Точность"},
    "skill.precision.desc":            {"en": "Every X shots is a crit (x1.25).\nStarts at 29, -1 per level.\nRequires: Fight Dirty 10.",
                                        "ru": "Каждый X выстрел — крит (x1.25).\nНачинает с 29, -1 за уровень.\nТребуется: Грязная борьба 10."},
    "skill.precision.effect":          {"en": "−1 shot to crit",        "ru": "−1 выстрел до крита"},

    "skill.resourcefulness.name":      {"en": "Resourcefulness",        "ru": "Бережливость"},
    "skill.resourcefulness.desc":      {"en": "Sell refund +1.2% per level.",
                                        "ru": "Возврат при продаже +1.2% за уровень."},
    "skill.resourcefulness.effect":    {"en": "+1.2% sell value",       "ru": "+1.2% при продаже"},

    "skill.bigger_budget.name":        {"en": "Bigger Budget",          "ru": "Большой бюджет"},
    "skill.bigger_budget.desc":        {"en": "Starting gold +1% per level.\nRequires: Resourcefulness 10.",
                                        "ru": "Начальное золото +1% за уровень.\nТребуется: Бережливость 10."},
    "skill.bigger_budget.effect":      {"en": "+1% start cash",         "ru": "+1% нач. деньги"},

    "skill.stonks.name":               {"en": "Stonks",                 "ru": "Стонкс"},
    "skill.stonks.desc":               {"en": "Wave clear reward +0.5% per level.\nRequires: Bigger Budget 10.",
                                        "ru": "Награда за волну +0.5% за уровень.\nТребуется: Большой бюджет 10."},
    "skill.stonks.effect":             {"en": "+0.5% wave reward",      "ru": "+0.5% награда волны"},

    "skill.scavenger.name":            {"en": "Scavenger",              "ru": "Мародёр"},
    "skill.scavenger.desc":            {"en": "Every X kills gives 1.5x reward.\nStarts at 29, -1 per level.\nRequires: Stonks 10.",
                                        "ru": "Каждое X убийство даёт 1.5x награду.\nНачинает с 29, -1 за уровень.\nТребуется: Стонкс 10."},
    "skill.scavenger.effect":          {"en": "−1 kill to bonus",       "ru": "−1 убийство до бонуса"},

    # ══════════════════════════════════════════════════════════════════
    # DRAFT CARDS  (curse cards)
    # ══════════════════════════════════════════════════════════════════
    "draft.choose_curse":          {"en": "CHOOSE YOUR CURSE",          "ru": "ВЫБЕРИ СВОЁ ПРОКЛЯТИЕ"},

    "draft.remove_tower":          {"en": "Remove a random tower",
                                    "ru": "Удалить рандомную башню"},
    "draft.range_down":            {"en": "All towers range -20% for 5 waves",
                                    "ru": "Дальность всех башен -20% на 5 волн"},
    "draft.upgrade_cost":          {"en": "Upgrade costs +15%",
                                    "ru": "Цена на апгрейды +15%"},
    "draft.half_money":            {"en": "Money split in half",
                                    "ru": "Деньги делятся на 2"},
    "draft.level_down":            {"en": "Random tower loses 1 level",
                                    "ru": "Рандомная башня теряет 1 уровень"},
    "draft.damage_down":           {"en": "All towers damage -50% for 5 waves",
                                    "ru": "Урон всех башен -50% на 5 волн"},
    "draft.firerate_down":         {"en": "Fire rate -20%",
                                    "ru": "Фаеррейт -20%"},
    "draft.rollback":              {"en": "Roll back 3 waves",
                                    "ru": "Откат на 3 волны назад"},
    "draft.zero_money":            {"en": "Wipes money to zero",
                                    "ru": "Списывает деньги до нуля"},
    "draft.damage_5":              {"en": "All towers deal 5 damage for 15 seconds",
                                    "ru": "Урон 5 всем башням на 15 секунд"},
    "draft.all_jesters":           {"en": "All towers replaced with Jester Lv.1 permanently",
                                    "ru": "Все башни заменяются на Jester 1 лвла навсегда"},

    # Draft card titles
    "draft.title.sacrifice":       {"en": "Sacrifice",                  "ru": "Жертва"},
    "draft.title.myopia":          {"en": "Myopia",                     "ru": "Близорукость"},
    "draft.title.inflation":       {"en": "Inflation",                  "ru": "Инфляция"},
    "draft.title.taxes":           {"en": "Taxes",                      "ru": "Налоги"},
    "draft.title.amnesia":         {"en": "Amnesia",                    "ru": "Амнезия"},
    "draft.title.weakness":        {"en": "Weakness",                   "ru": "Слабость"},
    "draft.title.lethargy":        {"en": "Lethargy",                   "ru": "Летаргия"},
    "draft.title.time_loop":       {"en": "Time Loop",                  "ru": "Петля времени"},
    "draft.title.bankruptcy":      {"en": "Bankruptcy",                 "ru": "Банкротство"},
    "draft.title.nerf_gun":        {"en": "Nerf Gun",                   "ru": "Нерфган"},
    "draft.title.circus":          {"en": "Circus",                     "ru": "Цирк"},

    # ══════════════════════════════════════════════════════════════════
    # BOSS LABELS
    # ══════════════════════════════════════════════════════════════════
    "boss.grave_digger":           {"en": "☠ GRAVE DIGGER",             "ru": "☠ МОГИЛЬЩИК"},
    "boss.fallen_giant":           {"en": "FALLEN GIANT",               "ru": "ПАДШИЙ ГИГАНТ"},
    "boss.fallen_jester":          {"en": "FALLEN JESTER",              "ru": "ПАДШИЙ ШУТ"},
    "boss.fallen_squire":          {"en": "FALLEN SQUIRE",              "ru": "ПАДШИЙ ОРУЖЕНОСЕЦ"},
    "boss.fallen_shield":          {"en": "FALLEN SHIELD",              "ru": "ПАДШИЙ ЩИТ"},
    "boss.fallen_honor_guard":     {"en": "FALLEN HONOR GUARD",         "ru": "ПАДШИЙ ГВАРДЕЕЦ"},
    "boss.fallen_king":            {"en": "FALLEN KING",                "ru": "ПАДШИЙ КОРОЛЬ"},

    # ══════════════════════════════════════════════════════════════════
    # TOWER / UNIT ABILITY NAMES
    # ══════════════════════════════════════════════════════════════════
    "ability.whirlwind":           {"en": "Whirlwind Slash",            "ru": "Вихревой удар"},
    "ability.call_to_arms":        {"en": "Call to Arms",               "ru": "Призыв к оружию"},

    # ══════════════════════════════════════════════════════════════════
    # UNIT NAMES
    # ══════════════════════════════════════════════════════════════════
    "unit.assassin":               {"en": "Assassin",                   "ru": "Ассасин"},
    "unit.accelerator":            {"en": "Accelerator",                "ru": "Ускоритель"},
    "unit.frostcelerator":         {"en": "Frostcelerator",             "ru": "Морозоускоритель"},
    "unit.lifestealer":            {"en": "Lifestealer",                "ru": "Жизневор"},
    "unit.archer":                 {"en": "Archer",                     "ru": "Лучник"},
    "unit.archer_prime":           {"en": "Archer Prime",               "ru": "Лучник Прайм"},
    "unit.farm":                   {"en": "Farm",                       "ru": "Ферма"},
    "unit.red_ball":               {"en": "Red Ball",                   "ru": "Красный шар"},
    "unit.militant":               {"en": "Militant",                   "ru": "Солдат"},
    "unit.freezer":                {"en": "Freezer",                    "ru": "Морозилка"},
    "unit.frost_blaster":          {"en": "Frost Blaster",              "ru": "Морозный бластер"},
    "unit.sledger":                {"en": "Sledger",                    "ru": "Кувалда"},
    "unit.gladiator":              {"en": "Gladiator",                  "ru": "Гладиатор"},
    "unit.toxic_gunner":           {"en": "Toxic Gunner",               "ru": "Токсичный стрелок"},
    "unit.slasher":                {"en": "Slasher",                    "ru": "Рубака"},
    "unit.cowboy":                 {"en": "Cowboy",                     "ru": "Ковбой"},
    "unit.hallow_punk":            {"en": "Hallow Punk",                "ru": "Hallow Punk"},
    "unit.spotlight_tech":         {"en": "Spotlight Tech",             "ru": "Прожектор"},
    "unit.commander":              {"en": "Commander",                  "ru": "Командир"},
    "unit.snowballer":             {"en": "Snowballer",                 "ru": "Снежкомёт"},
    "unit.commando":               {"en": "Commando",                   "ru": "Коммандос"},
    "unit.caster":                 {"en": "Caster",                     "ru": "Каст"},
    "unit.warlock":                {"en": "Warlock",                    "ru": "Чернокнижник"},
    "unit.jester":                 {"en": "Jester",                     "ru": "Шут"},

    # ══════════════════════════════════════════════════════════════════
    # UNIT UPGRADE LEVEL NAMES
    # ══════════════════════════════════════════════════════════════════
    "upgrade.commander.1":         {"en": "Leadership",                 "ru": "Лидерство"},
    "upgrade.commander.2":         {"en": "Call to Arms",               "ru": "Призыв к оружию"},
    "upgrade.commander.3":         {"en": "Intense Training",           "ru": "Интенсивные тренировки"},
    "upgrade.commander.4":         {"en": "Strength in Numbers",        "ru": "Сила в числе"},

    "upgrade.snowballer.1":        {"en": "Snow Day",                   "ru": "Снежный день"},
    "upgrade.snowballer.2":        {"en": "Frigid Temperatures",        "ru": "Трескучий мороз"},
    "upgrade.snowballer.3":        {"en": "Snowball Cannon",            "ru": "Пушка снежков"},

    # ══════════════════════════════════════════════════════════════════
    # UNIT SPECIAL EFFECTS & FLOATING TEXT
    # ══════════════════════════════════════════════════════════════════
    "fx.venom_frenzy":             {"en": "VENOM FRENZY!",              "ru": "ЯД БЕШЕНСТВО!"},
    "fx.splash":                   {"en": "Splash! -{n}",               "ru": "Взрыв! -{n}"},

    # ══════════════════════════════════════════════════════════════════
    # RARITY LABELS
    # ══════════════════════════════════════════════════════════════════
    "rarity.starter":              {"en": "STARTER",                    "ru": "СТАРТЕР"},
    "rarity.common":               {"en": "COMMON",                     "ru": "ОБЫЧНЫЙ"},
    "rarity.rare":                 {"en": "RARE",                       "ru": "РЕДКИЙ"},
    "rarity.epic":                 {"en": "EPIC",                       "ru": "ЭПИЧЕСКИЙ"},
    "rarity.exclusive":            {"en": "EXCLUSIVE",                  "ru": "ЭКСКЛЮЗИВНЫЙ"},
    "rarity.mythic":               {"en": "MYTHIC",                     "ru": "МИФИЧЕСКИЙ"},

    # ══════════════════════════════════════════════════════════════════
    # BADGE LABELS  (profile)
    # ══════════════════════════════════════════════════════════════════
    "badge.early_access":          {"en": "Early Access",               "ru": "Ранний доступ"},
    "badge.apex":                  {"en": "Apex",                       "ru": "Апекс"},
    "badge.singularity":           {"en": "SINGULARITY",                "ru": "СИНГУЛЯРНОСТЬ"},

    # ══════════════════════════════════════════════════════════════════
    # ACHIEVEMENTS
    # ══════════════════════════════════════════════════════════════════
    "ach.first_path.name":         {"en": "First Path",                 "ru": "Первый путь"},
    "ach.first_path.desc":         {"en": "Beat Easy mode",             "ru": "Пройди лёгкий режим"},
    "ach.fallen_angel.name":       {"en": "Fallen Angel",               "ru": "Падший ангел"},
    "ach.fallen_angel.desc":       {"en": "Beat Fallen mode",           "ru": "Пройди режим Падший"},
    "ach.frosty_clear.name":       {"en": "Frosty Path",                "ru": "Морозный путь"},
    "ach.frosty_clear.desc":       {"en": "Beat Frosty mode",           "ru": "Пройди Морозный режим"},
    "ach.king_victim.name":        {"en": "King's Victim",              "ru": "Жертва Короля"},
    "ach.king_victim.desc":        {"en": "Lose to Fallen King on wave 40",
                                    "ru": "Проиграй Падшему Королю на волне 40"},
    "ach.free_pass.name":          {"en": "Free Pass",                  "ru": "Вольный пропуск"},
    "ach.free_pass.desc":          {"en": "Beat Easy without killing final boss",
                                    "ru": "Пройди Лёгкий, не убив финального босса"},
    "ach.rich.name":               {"en": "Rich",                       "ru": "Богатей"},
    "ach.rich.desc":               {"en": "Have 5,000+ coins at once",  "ru": "Накопи 5000+ монет за раз"},
    "ach.frosty_perfect.name":     {"en": "Ice Fortress",               "ru": "Ледяная крепость"},
    "ach.frosty_perfect.desc":     {"en": "Beat Frosty with no HP loss","ru": "Пройди Морозный без потери ОЖ"},
    "ach.last_stand.name":         {"en": "Last Stand",                 "ru": "Последний рубеж"},
    "ach.last_stand.desc":         {"en": "Beat any mode with 1 HP left",
                                    "ru": "Пройди любой режим с 1 ОЖ"},
    "ach.collector_10.name":       {"en": "Collector",                  "ru": "Коллекционер"},
    "ach.collector_10.desc":       {"en": "Unlock 10+ units",           "ru": "Разблокируй 10+ юнитов"},
    "ach.collector_20.name":       {"en": "Collection Master",          "ru": "Мастер коллекции"},
    "ach.collector_20.desc":       {"en": "Unlock 20+ units",           "ru": "Разблокируй 20+ юнитов"},
    "ach.millionaire.name":        {"en": "Millionaire",                "ru": "Миллионер"},
    "ach.millionaire.desc":        {"en": "Have 100,000+ coins",        "ru": "Накопи 100 000+ монет"},
    "ach.shard_500.name":          {"en": "Sparkling",                  "ru": "Блестящий"},
    "ach.shard_500.desc":          {"en": "Gather 500 shards",          "ru": "Собери 500 осколков"},
    "ach.shard_1000.name":         {"en": "Crystal",                    "ru": "Кристалл"},
    "ach.shard_1000.desc":         {"en": "Gather 1000 shards",         "ru": "Собери 1000 осколков"},
    "ach.april_fools_2026.name":   {"en": "April Fools 2026",           "ru": "День дурака 2026"},
    "ach.april_fools_2026.desc":   {"en": "Beat April Fools 2026",      "ru": "Пройди День дурака 2026"},
    "ach.has_skin.name":           {"en": "Stylist",                    "ru": "Стилист"},
    "ach.has_skin.desc":           {"en": "Own at least 1 skin",        "ru": "Владей хотя бы 1 скином"},
    "ach.naked_run.name":          {"en": "Lightweight",                "ru": "Налегке"},
    "ach.naked_run.desc":          {"en": "Start game with no units equipped",
                                    "ru": "Начни игру без экипированных юнитов"},
    "ach.fallen_duo.name":         {"en": "Duo",                        "ru": "Дуэт"},
    "ach.fallen_duo.desc":         {"en": "Beat Fallen with max 2 units",
                                    "ru": "Пройди Падший с максимум 2 юнитами"},
    "ach.grand_slam.name":         {"en": "Grand Slam",                 "ru": "Большой шлем"},
    "ach.grand_slam.desc":         {"en": "Beat every difficulty in a row",
                                    "ru": "Пройди все сложности подряд"},
    "ach.capitalist.name":         {"en": "Capitalist",                 "ru": "Капиталист"},
    "ach.capitalist.desc":         {"en": "Place 8 Farms all upgraded to max level",
                                    "ru": "Поставь 8 Ферм все улучшенные до максимума"},
    "ach.overkill.name":           {"en": "Overkill",                   "ru": "Перебор"},
    "ach.overkill.desc":           {"en": "Apply every debuff to a boss at once",
                                    "ru": "Примени все дебаффы к боссу одновременно"},
    "ach.moonwalk.name":           {"en": "Moonwalk",                   "ru": "Лунная походка"},
    "ach.moonwalk.desc":           {"en": "Have 15 enemies walking in confusion",
                                    "ru": "Доведи 15 врагов до состояния замешательства"},
    "ach.why.name":                {"en": "Why",                        "ru": "Зачем"},
    "ach.why.desc":                {"en": "Do nothing for 1 hour",      "ru": "Ничего не делай 1 час"},
    "ach.gold_rush.name":          {"en": "Gold Rush",                  "ru": "Золотая лихорадка"},
    "ach.gold_rush.desc":          {"en": "Earn $10,000 in one game using only Cowboys",
                                    "ru": "Заработай $10 000 за одну игру только Ковбоями"},
    "ach.hacker.name":             {"en": "Hacker",                     "ru": "Хакер"},
    "ach.hacker.desc":             {"en": "Open the admin panel in Sandbox mode",
                                    "ru": "Открой панель администратора в режиме Песочница"},
    "ach.no_refunds.name":         {"en": "No Refunds",                 "ru": "Без возврата"},
    "ach.no_refunds.desc":         {"en": "Beat Fallen without selling any tower",
                                    "ru": "Пройди Падший, не продав ни одной башни"},
    "ach.absolute_zero.name":      {"en": "Absolute Zero",              "ru": "Абсолютный ноль"},
    "ach.absolute_zero.desc":      {"en": "Keep a boss frozen for 15 seconds straight",
                                    "ru": "Держи босса замороженным 15 секунд подряд"},
    "ach.speedrunner.name":        {"en": "Speedrunner",                "ru": "Спидраннер"},
    "ach.speedrunner.desc":        {"en": "Beat Fallen with Auto-skip on all game",
                                    "ru": "Пройди Падший с авто-пропуском на всю игру"},

    # ══════════════════════════════════════════════════════════════════
    # DAILY QUESTS
    # ══════════════════════════════════════════════════════════════════
    "dq.easy_victory.title":       {"en": "Easy Victory",               "ru": "Лёгкая победа"},
    "dq.easy_victory.desc":        {"en": "Win 1 game on Easy difficulty.",
                                    "ru": "Выиграй 1 игру на Лёгкой сложности."},
    "dq.double_easy.title":        {"en": "Double Easy",                "ru": "Двойная лёгкость"},
    "dq.double_easy.desc":         {"en": "Win 2 games on Easy difficulty.",
                                    "ru": "Выиграй 2 игры на Лёгкой сложности."},
    "dq.fallen_victor.title":      {"en": "Fallen Victor",              "ru": "Победитель Падшего"},
    "dq.fallen_victor.desc":       {"en": "Win 1 game on Fallen difficulty.",
                                    "ru": "Выиграй 1 игру на Падшей сложности."},
    "dq.frost_conqueror.title":    {"en": "Frost Conqueror",            "ru": "Покоритель мороза"},
    "dq.frost_conqueror.desc":     {"en": "Win 1 game on Frosty difficulty.",
                                    "ru": "Выиграй 1 игру на Морозной сложности."},
    "dq.infernal_run.title":       {"en": "Infernal Run",               "ru": "Инфернальный забег"},
    "dq.infernal_run.desc":        {"en": "Win 1 game on Infernal difficulty.",
                                    "ru": "Выиграй 1 игру на Инфернальной сложности."},
    "dq.pest_control.title":       {"en": "Pest Control",               "ru": "Дезинсекция"},
    "dq.pest_control.desc":        {"en": "Kill 100 enemies in any game.",
                                    "ru": "Убей 100 врагов в любой игре."},
    "dq.slaughter.title":          {"en": "Slaughter",                  "ru": "Резня"},
    "dq.slaughter.desc":           {"en": "Kill 300 enemies in any game.",
                                    "ru": "Убей 300 врагов в любой игре."},
    "dq.massacre.title":           {"en": "Massacre",                   "ru": "Бойня"},
    "dq.massacre.desc":            {"en": "Kill 500 enemies in any game.",
                                    "ru": "Убей 500 врагов в любой игре."},
    "dq.survivor.title":           {"en": "Survivor",                   "ru": "Выживший"},
    "dq.survivor.desc":            {"en": "Survive 5 waves in a single game.",
                                    "ru": "Выживи в 5 волнах в одной игре."},
    "dq.veteran.title":            {"en": "Veteran",                    "ru": "Ветеран"},
    "dq.veteran.desc":             {"en": "Survive 10 waves in a single game.",
                                    "ru": "Выживи в 10 волнах в одной игре."},
    "dq.war_machine.title":        {"en": "War Machine",                "ru": "Машина войны"},
    "dq.war_machine.desc":         {"en": "Survive 15 waves in a single game.",
                                    "ru": "Выживи в 15 волнах в одной игре."},
    "dq.early_investor.title":     {"en": "Early Investor",             "ru": "Ранний инвестор"},
    "dq.early_investor.desc":      {"en": "Earn 2 000 coins in one game.",
                                    "ru": "Заработай 2 000 монет в одной игре."},
    "dq.capitalist_q.title":       {"en": "Capitalist",                 "ru": "Капиталист"},
    "dq.capitalist_q.desc":        {"en": "Earn 5 000 coins in one game.",
                                    "ru": "Заработай 5 000 монет в одной игре."},
    "dq.tycoon.title":             {"en": "Tycoon",                     "ru": "Магнат"},
    "dq.tycoon.desc":              {"en": "Earn 10 000 coins in one game.",
                                    "ru": "Заработай 10 000 монет в одной игре."},
    "dq.builder.title":            {"en": "Builder",                    "ru": "Строитель"},
    "dq.builder.desc":             {"en": "Place 5 towers in one game.",
                                    "ru": "Поставь 5 башен в одной игре."},
    "dq.army_builder.title":       {"en": "Army Builder",               "ru": "Строитель армии"},
    "dq.army_builder.desc":        {"en": "Place 15 towers in one game.",
                                    "ru": "Поставь 15 башен в одной игре."},
    "dq.flawless.title":           {"en": "Flawless",                   "ru": "Безупречно"},
    "dq.flawless.desc":            {"en": "Win a game without letting any enemy through.",
                                    "ru": "Выиграй игру, не пропустив ни одного врага."},
    "dq.hardcore_attempt.title":   {"en": "Hardcore Attempt",           "ru": "Хардкорная попытка"},
    "dq.hardcore_attempt.desc":    {"en": "Reach wave 10 in Hardcore mode.",
                                    "ru": "Доберись до волны 10 в режиме Хардкор."},

    # ══════════════════════════════════════════════════════════════════
    # MULTIPLAYER
    # ══════════════════════════════════════════════════════════════════
    "mp.nick_taken":               {"en": "Nickname '{nick}' is already taken by the host! Change it in Profile.",
                                    "ru": "Никнейм «{nick}» уже занят хостом! Смени его в Профиле."},
}


def set_lang(code: str):
    """Set active language. code = 'en' or 'ru'."""
    global _LANG
    _LANG = code if code in ("en", "ru") else "en"


def get_lang() -> str:
    return _LANG


def t(key: str, **kwargs) -> str:
    """
    Translate key into the active language.
    Falls back to English, then to the key itself.
    Supports simple .format() style kwargs, e.g. t("mp.nick_taken", nick="Bob")
    """
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_LANG) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text