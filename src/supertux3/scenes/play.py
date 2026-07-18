"""Die eigentliche Spiel-Szene mit Effekten, Power-Ups und Progression."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..engine.camera import Camera
from ..engine.particles import Particles
from ..world.level import Level
from ..settings import (
    VIRTUAL_W, VIRTUAL_H, SKY_TOP, SKY_BOTTOM, WHITE, UI_SHADOW,
    SPRING_SPEED, LEVEL_FILES,
)


def _sky_gradient(w, h):
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(SKY_TOP[i] + (SKY_BOTTOM[i] - SKY_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (w, y))
    return surf


class PlayScene(Scene):
    def __init__(self, game, index: int = 0, level_name: str | None = None):
        super().__init__(game)
        self.custom = level_name is not None
        self.index = index
        self.level_name = level_name if self.custom else LEVEL_FILES[index]

    def on_enter(self):
        if not self.custom:
            self.game.level_index = self.index
        self.level = Level.load(self.game, self.level_name)
        self.camera = Camera(self.level.width_px, self.level.height_px)
        self.camera.update(self.level.player.rect, 0.0, snap=True)
        self.particles = Particles()
        self.font = pygame.font.Font(None, 34)
        self.big_font = pygame.font.Font(None, 76)
        self.mode = "play"          # play | dead | complete
        self.timer = 0.0
        self.elapsed = 0.0          # Spielzeit (für Bestzeit)
        self.paused = False
        self.ride = None            # aktuell getragene Plattform
        self._build_background()
        if self.level.music:
            self.game.audio.play_music(self.level.music)

    def _build_background(self):
        self.sky = _sky_gradient(VIRTUAL_W, VIRTUAL_H)
        self.bg = None
        src = self.game.assets.background(self.level.background_name)
        if src is not None:
            scale = VIRTUAL_H / src.get_height()
            self.bg = pygame.transform.smoothscale(
                src, (int(src.get_width() * scale), VIRTUAL_H))

    # --- Events ------------------------------------------------------
    def handle_event(self, event):
        from ..engine.controls import nav
        act = nav(event)
        if self.paused:
            key = event.key if event.type == pygame.KEYDOWN else None
            if act in ("pause", "back", "confirm") or key == pygame.K_p:
                self.paused = False
            elif key == pygame.K_r:
                self.paused = False
                self.on_enter()
            elif key == pygame.K_q:
                from .levelselect import LevelSelectScene
                self.game.scenes.switch(LevelSelectScene(self.game))
            elif key == pygame.K_m:
                self.game.audio.toggle_mute()
                self.game.save_progress()
            elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.game.audio.change_music_volume(-0.1)
                self.game.save_progress()
            elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.game.audio.change_music_volume(0.1)
                self.game.save_progress()
            return
        if act in ("pause", "back") or (event.type == pygame.KEYDOWN and event.key == pygame.K_p):
            self.paused = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            self.game.audio.toggle_mute()
            self.game.save_progress()

    # --- Update ------------------------------------------------------
    def update(self, dt):
        if self.paused:
            return
        lvl = self.level
        self.particles.update(dt)

        if self.mode == "play":
            for pf in lvl.platforms:
                pf.update(dt, lvl)
            # getragene Plattform mitnehmen
            if self.ride is not None:
                lvl.player.x += self.ride.dx
                lvl.player.y += self.ride.dy

            lvl.player.update(dt, lvl)
            self._recompute_ride()

            for e in lvl.enemies:
                e.update(dt, lvl)
            for c in lvl.coins:
                c.update(dt, lvl)
            for it in lvl.items:
                it.update(dt, lvl)
            for st in lvl.stars:
                st.update(dt, lvl)
            for sp in lvl.springs:
                sp.update(dt, lvl)
            for pr in lvl.projectiles:
                pr.update(dt, lvl)
            self.elapsed += dt

            self._player_effects()
            self._collisions()
            lvl.enemies = [e for e in lvl.enemies if not getattr(e, "remove", False)]
            lvl.projectiles = [pr for pr in lvl.projectiles if not getattr(pr, "remove", False)]

            if lvl.player.y > lvl.height_px + 80:
                self._die()
            self.camera.update(lvl.player.rect, dt)

        elif self.mode == "dead":
            self.timer -= dt
            lvl.player.vy += 1400 * dt
            lvl.player.y += lvl.player.vy * dt
            self.camera.update(lvl.player.rect, dt)
            if self.timer <= 0:
                self._after_death()

        elif self.mode == "complete":
            self.timer -= dt
            for c in lvl.coins:
                c.update(dt, lvl)
            self.camera.update(lvl.player.rect, dt)
            if self.timer <= 0:
                self._next_level()

    def _recompute_ride(self):
        self.ride = None
        p = self.level.player
        if p.vy < 0:
            return
        feet = p.rect.bottom
        for pf in self.level.platforms:
            r = pf.rect
            if abs(feet - r.top) <= 4 and p.rect.right > r.left + 2 and p.rect.left < r.right - 2:
                self.ride = pf
                p.on_ground = True
                break

    def _player_effects(self):
        p = self.level.player
        if p.ev_jumped:
            self.particles.dust(p.cx, p.y + p.h, n=6)
        if p.ev_landed:
            self.particles.dust(p.cx, p.y + p.h, n=8)
            self.camera.add_shake(min(4.0, p.land_vy * 0.006), 0.18)

    def _collisions(self):
        lvl = self.level
        p = lvl.player
        prect = p.rect

        # Münzen
        rem = []
        for c in lvl.coins:
            if prect.colliderect(c.rect):
                p.coins += 1
                self.particles.coin(c.cx, c.cy)
                self.game.audio.play("coin")
            else:
                rem.append(c)
        lvl.coins = rem

        # Wachstums-Items
        rem = []
        for it in lvl.items:
            if prect.colliderect(it.rect):
                if p.grow():
                    self.game.audio.play("grow")
                    self.particles.sparkle(it.cx, it.cy)
                    self.particles.text(it.cx, it.y, "Größe!", (255, 230, 120), self.font)
                else:
                    p.coins += 5
                    self.particles.coin(it.cx, it.cy)
            else:
                rem.append(it)
        lvl.items = rem

        # Sterne
        rem = []
        for st in lvl.stars:
            if prect.colliderect(st.rect):
                lvl.stars_collected += 1
                self.particles.sparkle(st.cx, st.cy, color=(255, 236, 120), n=20)
                self.particles.text(st.cx, st.y, "Stern!", (255, 232, 120), self.font)
                self.game.audio.play("star")
            else:
                rem.append(st)
        lvl.stars = rem

        # Sprungfedern
        for sp in lvl.springs:
            if prect.colliderect(sp.rect) and p.vy > 0 and prect.bottom <= sp.rect.top + 18:
                p.vy = -SPRING_SPEED
                p.jump_active = False
                p.scale_x, p.scale_y = 0.7, 1.4
                sp.trigger()
                self.ride = None
                self.particles.dust(sp.cx, sp.rect.top, n=8, tone=(200, 220, 255))
                self.camera.add_shake(2.5, 0.15)
                self.game.audio.play("spring")

        # Checkpoints
        for cp in lvl.checkpoints:
            if not cp.active and prect.colliderect(cp.rect):
                cp.active = True
                lvl.spawn_px = (cp.x, cp.rect.bottom)
                self.particles.sparkle(cp.cx, cp.y, color=(150, 255, 170))
                self.particles.text(cp.cx, cp.y, "Checkpoint!", (150, 255, 170), self.font)
                self.game.audio.play("checkpoint")

        # Projektile (z.B. Boss-Eisbälle)
        for pr in lvl.projectiles:
            if prect.colliderect(pr.rect):
                pr.remove = True
                self._hurt_player(p)
                if p.dead or self.mode == "dead":
                    break

        # Gegner
        for e in lvl.enemies:
            if getattr(e, "squashed", False) or not prect.colliderect(e.rect):
                continue
            is_boss = getattr(e, "is_boss", False)
            stomping = getattr(e, "stompable", False) and p.vy > 0 and (prect.bottom - e.rect.top) <= 24
            if is_boss:
                if stomping and e.hit():
                    p.bounce(1.1)
                    self.particles.stomp(e.rect.centerx, e.rect.top)
                    self.camera.add_shake(4.0, 0.25)
                    self.game.audio.play("stomp")
                    if e.defeated:
                        self.particles.poof(e.rect.centerx, e.rect.centery,
                                            color=(200, 230, 255), n=40)
                        self.camera.add_shake(8.0, 0.5)
                        self._win()
                elif not stomping and e.invuln <= 0:
                    self._hurt_player(p)
            elif stomping:
                e.stomp()
                p.bounce()
                self.particles.stomp(e.rect.centerx, e.rect.centery)
                self.particles.text(e.rect.centerx, e.rect.top, "+100", WHITE, self.font)
                self.camera.add_shake(3.0, 0.18)
                self.game.audio.play("stomp")
            else:
                self._hurt_player(p)
            if self.mode != "play":
                break

        # Ziel
        if self.mode == "play" and lvl.goal and prect.colliderect(lvl.goal.rect):
            self._win()

    def _hurt_player(self, p):
        out = p.take_hit()
        if out == "die":
            self._die()
        elif out == "shrink":
            p.vx = -240 * p.facing
            p.vy = -300
            self.particles.poof(p.cx, p.cy, color=(255, 210, 210), n=16)
            self.camera.add_shake(4.0, 0.25)
            self.game.audio.play("hurt")

    def _win(self):
        self.mode = "complete"
        self.timer = 2.2
        p = self.level.player
        self.particles.sparkle(p.rect.centerx, p.rect.centery, color=(255, 240, 140), n=30)
        self.game.audio.play("win")

    def _die(self):
        if self.mode == "dead":
            return
        self.mode = "dead"
        self.timer = 1.3
        p = self.level.player
        p.vy = -520
        p.invuln = 2.0
        self.particles.poof(p.cx, p.cy, color=(60, 66, 90), n=26)
        self.camera.add_shake(6.0, 0.3)
        self.game.lives -= 1
        self.game.audio.play("hurt")

    def _after_death(self):
        if self.custom:
            from .editor import EditorScene
            self.game.scenes.switch(EditorScene(self.game, self.level_name))
            return
        if self.game.lives <= 0:
            from .gameover import ResultScene
            self.game.scenes.switch(ResultScene(self.game, won=False,
                                                coins=self.level.player.coins,
                                                total=self.level.total_coins))
        else:
            self._respawn()

    def _respawn(self):
        p = self.level.player
        p._set_power("small")
        sx, sy = self.level.spawn_px
        p.x = float(sx)
        p.y = float(sy - p.h)
        p.vx = p.vy = 0.0
        p.invuln = 1.5
        self.ride = None
        self.mode = "play"
        self.camera.update(p.rect, 0.0, snap=True)

    def _next_level(self):
        if self.custom:
            from .editor import EditorScene
            self.game.scenes.switch(EditorScene(self.game, self.level_name))
            return
        self.game.record_result(self.index, self.level.player.coins,
                                self.level.stars_collected, self.elapsed)
        nxt = self.index + 1
        self.game.unlocked = max(self.game.unlocked, nxt)
        if nxt < len(LEVEL_FILES):
            self.game.scenes.switch(PlayScene(self.game, nxt))
        else:
            from .gameover import ResultScene
            self.game.scenes.switch(ResultScene(self.game, won=True,
                                                coins=self.level.player.coins,
                                                total=self.level.total_coins,
                                                game_complete=True))

    # --- Draw --------------------------------------------------------
    def draw(self, surface):
        surface.blit(self.sky, (0, 0))
        if self.bg is not None:
            bw = self.bg.get_width()
            start = -int(self.camera.x * 0.4) % bw
            x = start - bw
            while x < VIRTUAL_W:
                surface.blit(self.bg, (x, 0))
                x += bw
        cam = self.camera
        for img, px, py in self.level.props:
            surface.blit(img, (px - cam.offset[0], py - cam.offset[1]))
        self.level.tilemap.draw(surface, cam)
        for pf in self.level.platforms:
            pf.draw(surface, cam)
        for cp in self.level.checkpoints:
            cp.draw(surface, cam)
        for sp in self.level.springs:
            sp.draw(surface, cam)
        for c in self.level.coins:
            c.draw(surface, cam)
        for it in self.level.items:
            it.draw(surface, cam)
        for st in self.level.stars:
            st.draw(surface, cam)
        if self.level.goal:
            self.level.goal.draw(surface, cam)
        for e in self.level.enemies:
            e.draw(surface, cam)
        for pr in self.level.projectiles:
            pr.draw(surface, cam)
        self.level.player.draw(surface, cam)
        self.particles.draw(surface, cam)
        self._draw_hud(surface)
        if self.mode == "complete":
            self._center_text(surface, "Geschafft!", self.big_font, (255, 240, 120))
        if self.paused:
            self._draw_pause(surface)

    def _text(self, surface, text, font, pos, color=WHITE):
        surface.blit(font.render(text, True, UI_SHADOW), (pos[0] + 2, pos[1] + 2))
        surface.blit(font.render(text, True, color), pos)

    def _center_text(self, surface, text, font, color):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(3, 3))
        surface.blit(img, rect)

    def _draw_hud(self, surface):
        p = self.level.player
        self._text(surface, f"Münzen {p.coins}/{self.level.total_coins}",
                   self.font, (10, 8), (255, 240, 120))
        self._text(surface, f"Leben {self.game.lives}", self.font, (10, 36))
        if self.level.total_stars:
            self._text(surface, f"Sterne {self.level.stars_collected}/{self.level.total_stars}",
                       self.font, (10, 64), (255, 232, 120))
        m, s = divmod(int(self.elapsed), 60)
        self._text(surface, f"Zeit {m}:{s:02d}", self.font, (10, 92), (200, 220, 245))
        name = self.font.render(self.level.name, True, WHITE)
        self._text(surface, self.level.name, self.font, (VIRTUAL_W - name.get_width() - 10, 8))
        boss = self.level.boss
        if boss is not None and not boss.remove:
            title = "Schattenkönig" if boss.variant == "shadow" else "Frostkönig"
            col_t = (200, 160, 255) if boss.variant == "shadow" else (180, 220, 255)
            img = self.font.render(title, True, col_t)
            self._text(surface, title, self.font, (VIRTUAL_W // 2 - img.get_width() // 2, 8), col_t)
            bw = 36
            x0 = VIRTUAL_W // 2 - (boss.max_hp * (bw + 8)) // 2
            for i in range(boss.max_hp):
                col = (255, 90, 90) if i < boss.hp else (70, 80, 96)
                pygame.draw.rect(surface, col, (x0 + i * (bw + 8), 40, bw, 14),
                                 border_radius=3)

    def _draw_pause(self, surface):
        veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        veil.fill((10, 14, 28, 170))
        surface.blit(veil, (0, 0))
        self._center_text(surface, "Pause", self.big_font, WHITE)
        lines = ["ESC/P = weiter    ·    R = neu    ·    Q = Level-Auswahl",
                 "M = Ton    ·    +/- = Musiklautstärke"]
        for i, ln in enumerate(lines):
            img = self.font.render(ln, True, (215, 225, 240))
            rect = img.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2 + 60 + i * 32))
            surface.blit(self.font.render(ln, True, UI_SHADOW), rect.move(2, 2))
            surface.blit(img, rect)
