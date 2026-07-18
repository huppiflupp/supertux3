"""Die eigentliche Spiel-Szene."""
from __future__ import annotations

import pygame

from ..engine.scene import Scene
from ..engine.camera import Camera
from ..world.level import Level
from ..settings import (
    VIRTUAL_W, VIRTUAL_H, SKY_TOP, SKY_BOTTOM, WHITE, UI_SHADOW,
)


def _sky_gradient(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(SKY_TOP[i] + (SKY_BOTTOM[i] - SKY_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (w, y))
    return surf


class PlayScene(Scene):
    def __init__(self, game, level_name: str = "level1.json"):
        super().__init__(game)
        self.level_name = level_name

    def on_enter(self) -> None:
        self.level = Level.load(self.game, self.level_name)
        self.camera = Camera(self.level.width_px, self.level.height_px)
        self.camera.update(self.level.player.rect, 0.0, snap=True)
        self.font = pygame.font.Font(None, 34)
        self.big_font = pygame.font.Font(None, 76)
        self.mode = "play"           # play | dead | complete
        self.timer = 0.0
        self._build_background()
        if self.level.music:
            self.game.audio.play_music(self.level.music)

    def _build_background(self) -> None:
        self.sky = _sky_gradient(VIRTUAL_W, VIRTUAL_H)
        self.bg = None
        if self.game.assets.background is not None:
            src = self.game.assets.background
            scale = VIRTUAL_H / src.get_height()
            self.bg = pygame.transform.smoothscale(
                src, (int(src.get_width() * scale), VIRTUAL_H)
            )

    # --- Events ------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from .menu import MenuScene
                self.game.scenes.switch(MenuScene(self.game))
            elif event.key == pygame.K_m:
                self.game.audio.toggle_mute()
            elif event.key == pygame.K_r and self.mode == "play":
                self._respawn(full=True)

    # --- Update ------------------------------------------------------
    def update(self, dt: float) -> None:
        lvl = self.level
        if self.mode == "play":
            lvl.player.update(dt, lvl)
            for e in lvl.enemies:
                e.update(dt, lvl)
            for c in lvl.coins:
                c.update(dt, lvl)
            self._collisions()
            lvl.enemies = [e for e in lvl.enemies if not e.remove]
            if lvl.player.y > lvl.height_px + 40:
                self._die()
            self.camera.update(lvl.player.rect, dt)
        elif self.mode == "dead":
            self.timer -= dt
            lvl.player.vy += 1400 * dt
            lvl.player.y += lvl.player.vy * dt
            if self.timer <= 0:
                self._after_death()
        elif self.mode == "complete":
            self.timer -= dt
            for c in lvl.coins:
                c.update(dt, lvl)
            if self.timer <= 0:
                from .gameover import ResultScene
                self.game.scenes.switch(ResultScene(self.game, won=True,
                                                    coins=lvl.player.coins,
                                                    total=lvl.total_coins))

    def _collisions(self) -> None:
        p = self.level.player
        prect = p.rect
        # Münzen
        remaining = []
        for c in self.level.coins:
            if prect.colliderect(c.rect):
                p.coins += 1
                self.game.audio.play("coin")
            else:
                remaining.append(c)
        self.level.coins = remaining
        # Gegner
        for e in self.level.enemies:
            if e.squashed or not prect.colliderect(e.rect):
                continue
            if p.vy > 0 and (prect.bottom - e.rect.top) <= 24:
                e.stomp()
                p.bounce()
                self.game.audio.play("stomp")
            elif p.hurt():
                self.game.audio.play("hurt")
                p.vx = -240 * p.facing
                p.vy = -320
                self.game.lives -= 1
                if self.game.lives <= 0:
                    self._die()
        # Ziel
        if self.level.goal and prect.colliderect(self.level.goal.rect):
            self.mode = "complete"
            self.timer = 2.0
            self.game.audio.play("win")

    def _die(self) -> None:
        self.mode = "dead"
        self.timer = 1.2
        self.level.player.vy = -520
        self.game.audio.play("hurt")

    def _after_death(self) -> None:
        if self.game.lives <= 0:
            from .gameover import ResultScene
            self.game.scenes.switch(ResultScene(self.game, won=False,
                                                coins=self.level.player.coins,
                                                total=self.level.total_coins))
        else:
            self._respawn(full=False)

    def _respawn(self, full: bool) -> None:
        if full:
            self.on_enter()
            return
        p = self.level.player
        sx, sy = self.level.spawn_px
        p.x = float(sx)
        p.y = float(sy - p.h)
        p.vx = p.vy = 0.0
        p.invuln = 1.5
        p.dead = False
        self.mode = "play"
        self.camera.update(p.rect, 0.0, snap=True)

    # --- Draw --------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.sky, (0, 0))
        if self.bg is not None:
            bw = self.bg.get_width()
            start = -int(self.camera.x * 0.4) % bw
            x = start - bw
            while x < VIRTUAL_W:
                surface.blit(self.bg, (x, 0))
                x += bw
        for img, px, py in self.level.props:
            surface.blit(img, (px - self.camera.offset[0], py - self.camera.offset[1]))
        self.level.tilemap.draw(surface, self.camera)
        for c in self.level.coins:
            c.draw(surface, self.camera)
        if self.level.goal:
            self.level.goal.draw(surface, self.camera)
        for e in self.level.enemies:
            e.draw(surface, self.camera)
        self.level.player.draw(surface, self.camera)
        self._draw_hud(surface)
        if self.mode == "complete":
            self._center_text(surface, "Geschafft!", self.big_font, (255, 240, 120))

    def _text(self, surface, text, font, pos, color=WHITE) -> None:
        shadow = font.render(text, True, UI_SHADOW)
        surface.blit(shadow, (pos[0] + 1, pos[1] + 1))
        surface.blit(font.render(text, True, color), pos)

    def _center_text(self, surface, text, font, color) -> None:
        img = font.render(text, True, color)
        rect = img.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2))
        sh = font.render(text, True, UI_SHADOW)
        surface.blit(sh, rect.move(2, 2))
        surface.blit(img, rect)

    def _draw_hud(self, surface) -> None:
        self._text(surface, f"Münzen {self.level.player.coins}/{self.level.total_coins}",
                   self.font, (6, 4), (255, 240, 120))
        self._text(surface, f"Leben {self.game.lives}", self.font, (6, 20))
        name = self.font.render(self.level.name, True, WHITE)
        self._text(surface, self.level.name, self.font,
                   (VIRTUAL_W - name.get_width() - 6, 4))
