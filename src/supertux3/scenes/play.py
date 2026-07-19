"""Die eigentliche Spiel-Szene mit Effekten, Power-Ups und Progression."""
from __future__ import annotations

import random

import pygame

from ..engine.scene import Scene
from ..engine.camera import Camera
from ..engine.particles import Particles
from ..engine.weather import Weather
from ..world.level import Level
from ..entities.collectible import Coin, GrowItem, Star, FishItem
from ..entities.projectiles import Projectile
from ..settings import (
    VIRTUAL_W, VIRTUAL_H, SKY_TOP, SKY_BOTTOM, WHITE, UI_SHADOW,
    SPRING_SPEED, LEVEL_FILES, TILE,
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
        self.rain_t = 0.0           # Fischregen-Restzeit
        self.rain_spawn = 0.0
        self.plane_x = -80.0
        def _icon(img, h=22):
            w = max(1, round(img.get_width() * h / img.get_height()))
            return pygame.transform.smoothscale(img, (w, h))
        A = self.game.assets
        self.icons = {"coin": _icon(A.coin[0]), "heart": _icon(A.heart),
                      "star": _icon(A.star), "clock": _icon(A.clock),
                      "fish": _icon(A.fish, 20)}
        self.weather = Weather(self.level.weather, self.level.wind)
        self._build_background()
        track = f"{self.game.music_choice}.ogg" if self.game.music_choice else self.level.music
        if track:
            self.game.audio.play_music(track)

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
                from .worldmap import WorldMapScene
                self.game.scenes.switch(WorldMapScene(self.game, self.index))
            elif key == pygame.K_m:
                self.game.audio.toggle_mute()
                self.game.save_progress()
            elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.game.audio.change_music_volume(-0.1)
                self.game.save_progress()
            elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.game.audio.change_music_volume(0.1)
                self.game.save_progress()
            elif key == pygame.K_g:
                self.game.quality = "fast" if self.game.quality == "smooth" else "smooth"
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
            for fr in lvl.friendly:
                fr.update(dt, lvl)
            for bx in lvl.boxes:
                bx.update(dt, lvl)
            for fi in lvl.fish_items:
                fi.update(dt, lvl)
            for ri in lvl.rain_items:
                ri.update(dt, lvl)
            for fi2 in lvl.friend_items:
                fi2.update(dt, lvl)
            for fr2 in lvl.friends:
                fr2.update(dt, lvl)
            lvl.friends = [f for f in lvl.friends if not getattr(f, "remove", False)]
            for ti in lvl.turtle_items:
                ti.update(dt, lvl)
            for gi in lvl.giraffe_items:
                gi.update(dt, lvl)
            for g in lvl.giraffes:
                g.update(dt, lvl)
            if self.rain_t > 0:
                self._update_fish_rain(dt)
            self.weather.update(dt)
            self.elapsed += dt

            self._player_effects()
            self._collisions()
            lvl.enemies = [e for e in lvl.enemies if not getattr(e, "remove", False)]
            lvl.projectiles = [pr for pr in lvl.projectiles if not getattr(pr, "remove", False)]
            lvl.friendly = [fr for fr in lvl.friendly if not getattr(fr, "remove", False)]
            lvl.boxes = [bx for bx in lvl.boxes if not getattr(bx, "remove", False)]

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

        # Fisch-Powerup
        rem = []
        for fi in lvl.fish_items:
            if prect.colliderect(fi.rect):
                p.give_throw()
                self.particles.sparkle(fi.cx, fi.cy, color=(150, 210, 245))
                self.particles.text(fi.cx, fi.y, "Fisch-Wurf!", (150, 210, 245), self.font)
                self.game.audio.play("grow")
            else:
                rem.append(fi)
        lvl.fish_items = rem

        # Fischregen-Powerup
        rem = []
        for ri in lvl.rain_items:
            if prect.colliderect(ri.rect):
                self._start_fish_rain()
                self.particles.sparkle(ri.cx, ri.cy, color=(150, 210, 245), n=26)
                self.particles.text(ri.cx, ri.y, "FISCHREGEN!", (255, 236, 120), self.big_font)
            else:
                rem.append(ri)
        lvl.rain_items = rem

        # Schildkröte -> Schutzschild
        # Kämpfender Freund
        rem = []
        for fi2 in lvl.friend_items:
            if prect.colliderect(fi2.rect):
                from ..entities.buddy import Friend
                lvl.friends.append(Friend(p, self.game.assets))
                self.particles.sparkle(fi2.cx, fi2.cy, color=(150, 245, 160))
                self.particles.text(fi2.cx, fi2.y, "Freund!", (150, 245, 160), self.font)
                self.game.audio.play("grow")
            else:
                rem.append(fi2)
        lvl.friend_items = rem

        rem = []
        for ti in lvl.turtle_items:
            if prect.colliderect(ti.rect):
                from ..entities.buddy import SHIELD_DURATION
                p.shield_t = SHIELD_DURATION
                self.particles.sparkle(ti.cx, ti.cy, color=(150, 240, 190), n=20)
                self.particles.text(ti.cx, ti.y, "Schild!", (150, 240, 190), self.font)
                self.game.audio.play("grow")
            else:
                rem.append(ti)
        lvl.turtle_items = rem

        # Giraffe -> Brücken-Begleiter (nur einer gleichzeitig)
        rem = []
        for gi in lvl.giraffe_items:
            if prect.colliderect(gi.rect):
                from ..entities.buddy import Giraffe
                if not lvl.giraffes:
                    lvl.giraffes.append(Giraffe(p, self.game.assets))
                self.particles.sparkle(gi.cx, gi.cy, color=(240, 198, 98), n=20)
                self.particles.text(gi.cx, gi.y, "Giraffe!", (240, 198, 98), self.font)
                self.game.audio.play("grow")
            else:
                rem.append(gi)
        lvl.giraffe_items = rem

        # Loot-Box von unten anschlagen
        if p.bumped:
            for box in lvl.boxes:
                if getattr(box, "remove", False):
                    continue
                if abs(box.rect.bottom - prect.top) <= 8 and \
                        box.rect.left < prect.right and box.rect.right > prect.left:
                    box.remove = True
                    self._pop_loot(box)
                    self.particles.stomp(box.rect.centerx, box.rect.bottom)
                    self.camera.add_shake(2.5, 0.15)
                    self.game.audio.play("stomp")
                    break

        # geworfene/regnende Fische plätten Gegner (und knacken Boxen)
        for fr in lvl.friendly:
            for e in lvl.enemies:
                if getattr(e, "squashed", False) or getattr(e, "remove", False):
                    continue
                if fr.rect.colliderect(e.rect):
                    self._defeat_enemy(e)
                    fr.remove = True
                    break
            if not fr.remove:
                for box in lvl.boxes:
                    if not getattr(box, "remove", False) and fr.rect.colliderect(box.rect):
                        box.remove = True
                        self._pop_loot(box)
                        self.particles.stomp(box.rect.centerx, box.rect.centery)
                        fr.remove = True
                        break

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

    def _defeat_enemy(self, e):
        if getattr(e, "is_boss", False):
            if e.hit() and e.defeated:
                self.particles.poof(e.rect.centerx, e.rect.centery, color=(200, 230, 255), n=40)
                self.camera.add_shake(8.0, 0.5)
                self._win()
        elif hasattr(e, "stomp"):
            e.stomp()
        else:
            e.remove = True
        self.particles.stomp(e.rect.centerx, e.rect.centery)
        self.particles.text(e.rect.centerx, e.rect.top, "+100", WHITE, self.font)
        self.game.audio.play("stomp")

    def _pop_loot(self, box):
        A = self.game.assets
        cx = box.rect.centerx
        ty = box.rect.top - TILE
        r = random.random()
        if r < 0.5:
            self.level.coins.append(Coin(cx - 12, ty, A))
            self.level.total_coins += 1
        elif r < 0.72:
            self.level.items.append(GrowItem(cx - A.item_grow.get_width() // 2, ty, A))
        elif r < 0.88:
            self.level.fish_items.append(FishItem(cx - A.fish.get_width() // 2, ty, A))
        else:
            self.level.stars.append(Star(cx - 12, ty, A))
            self.level.total_stars += 1
        self.particles.sparkle(box.rect.centerx, box.rect.top, n=14)

    def _start_fish_rain(self):
        self.rain_t = 7.0
        self.rain_spawn = 0.0
        self.plane_x = -80.0
        self.game.audio.play("win")

    def _update_fish_rain(self, dt):
        self.rain_t -= dt
        self.plane_x += 300 * dt
        if self.plane_x > VIRTUAL_W + 80:
            self.plane_x = -80.0
        self.rain_spawn -= dt
        if self.rain_spawn <= 0:
            self.rain_spawn = 0.1
            A = self.game.assets
            wx = self.camera.x + self.plane_x + 20
            self.level.friendly.append(
                Projectile(wx, self.camera.y - 20, random.uniform(-30, 30), 80.0,
                           A.fish, grav=520.0, life=6.0, spin=True))
        if self.rain_t < 0:
            self.rain_t = 0.0

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
            from .worldmap import WorldMapScene
            self.game.scenes.switch(WorldMapScene(self.game, nxt))
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
        for bx in self.level.boxes:
            bx.draw(surface, cam)
        for cp in self.level.checkpoints:
            cp.draw(surface, cam)
        for sp in self.level.springs:
            sp.draw(surface, cam)
        for c in self.level.coins:
            c.draw(surface, cam)
        for it in self.level.items:
            it.draw(surface, cam)
        for fi in self.level.fish_items:
            fi.draw(surface, cam)
        for ri in self.level.rain_items:
            ri.draw(surface, cam)
        for ti in self.level.turtle_items:
            ti.draw(surface, cam)
        for gi in self.level.giraffe_items:
            gi.draw(surface, cam)
        for fi2 in self.level.friend_items:
            fi2.draw(surface, cam)
        for st in self.level.stars:
            st.draw(surface, cam)
        if self.level.goal:
            self.level.goal.draw(surface, cam)
        for g in self.level.giraffes:
            g.draw(surface, cam)
        for fr2 in self.level.friends:
            fr2.draw(surface, cam)
        for e in self.level.enemies:
            e.draw(surface, cam)
        for pr in self.level.projectiles:
            pr.draw(surface, cam)
        for fr in self.level.friendly:
            fr.draw(surface, cam)
        self.level.player.draw(surface, cam)
        self._draw_shield(surface, cam)
        self.particles.draw(surface, cam)
        if self.rain_t > 0:                      # Flugzeug beim Fischregen (Bildschirm-fix)
            surface.blit(self.game.assets.plane, (int(self.plane_x), 24))
        self.weather.draw(surface)               # Regen/Schnee/Nebel-Overlay
        self._draw_hud(surface)
        if self.mode == "complete":
            self._center_text(surface, "Geschafft!", self.big_font, (255, 240, 120))
        if self.paused:
            self._draw_pause(surface)

    def _draw_shield(self, surface, cam):
        """Rotierendes, leicht blinkendes Schutzschild um Pengu."""
        p = self.level.player
        if p.shield_t <= 0:
            return
        # kurz vor Ablauf blinken lassen
        if p.shield_t < 2.0 and int(p.shield_t * 10) % 2 == 0:
            return
        img = self.game.assets.shield
        ang = (self.elapsed * 90) % 360
        rot = pygame.transform.rotozoom(img, ang, 1.0)
        ox, oy = cam.offset
        cx = p.cx - ox
        cy = p.cy - oy
        surface.blit(rot, (int(cx - rot.get_width() / 2),
                           int(cy - rot.get_height() / 2)))

    def _text(self, surface, text, font, pos, color=WHITE):
        surface.blit(font.render(text, True, UI_SHADOW), (pos[0] + 2, pos[1] + 2))
        surface.blit(font.render(text, True, color), pos)

    def _center_text(self, surface, text, font, color):
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2))
        surface.blit(font.render(text, True, UI_SHADOW), rect.move(3, 3))
        surface.blit(img, rect)

    def _stat(self, surface, icon, text, y, color=WHITE):
        surface.blit(icon, (10, y))
        self._text(surface, text, self.font, (10 + icon.get_width() + 6, y - 2), color)

    def _draw_hud(self, surface):
        p = self.level.player
        self._stat(surface, self.icons["coin"], f"{p.coins}/{self.level.total_coins}",
                   8, (255, 240, 120))
        self._stat(surface, self.icons["heart"], f"{self.game.lives}", 34)
        y = 60
        if self.level.total_stars:
            self._stat(surface, self.icons["star"],
                       f"{self.level.stars_collected}/{self.level.total_stars}", y, (255, 232, 120))
            y += 26
        m, s = divmod(int(self.elapsed), 60)
        self._stat(surface, self.icons["clock"], f"{m}:{s:02d}", y, (200, 220, 245))
        # Wurf-Indikator, wenn Fisch-Powerup aktiv
        if p.can_throw:
            fish = self.icons["fish"]
            surface.blit(fish, (VIRTUAL_W - fish.get_width() - 12, VIRTUAL_H - fish.get_height() - 12))
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
        lines = ["ESC/P = weiter    ·    R = neu    ·    Q = Welt-Karte",
                 "M = Ton    ·    +/- = Lautstärke    ·    G = Grafik glatt/schnell"]
        for i, ln in enumerate(lines):
            img = self.font.render(ln, True, (215, 225, 240))
            rect = img.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2 + 60 + i * 32))
            surface.blit(self.font.render(ln, True, UI_SHADOW), rect.move(2, 2))
            surface.blit(img, rect)
