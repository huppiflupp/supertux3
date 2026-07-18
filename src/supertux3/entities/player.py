"""Der Spieler-Pinguin „Pengu"."""
from __future__ import annotations

import pygame

from .entity import Entity
from ..engine.animation import Animation
from ..settings import (
    MOVE_ACCEL, AIR_ACCEL, MAX_RUN_SPEED, GROUND_FRICTION,
    JUMP_SPEED, JUMP_CUTOFF, COYOTE_TIME, JUMP_BUFFER, STOMP_BOUNCE,
)

LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
DUCK_KEYS = (pygame.K_DOWN, pygame.K_s)

HITBOX_W, HITBOX_H = 12, 22
SPRITE_OFF_X = (HITBOX_W - 20) // 2   # Sprite ist 20 breit
SPRITE_OFF_Y = HITBOX_H - 24          # Sprite ist 24 hoch, unten bündig


class Player(Entity):
    def __init__(self, x: float, y: float, assets):
        super().__init__(x, y, HITBOX_W, HITBOX_H)
        self.anims = {
            "idle": Animation(assets.player["idle"], fps=3),
            "walk": Animation(assets.player["walk"], fps=12),
            "jump": Animation(assets.player["jump"], fps=1),
            "fall": Animation(assets.player["fall"], fps=1),
            "duck": Animation(assets.player["duck"], fps=1),
        }
        self.state = "idle"
        self.coyote = 0.0
        self.buffer = 0.0
        self.prev_jump = False
        self.jump_active = False
        self.ducking = False
        self.invuln = 0.0
        self.coins = 0

    # --- Steuerung ---------------------------------------------------
    def update(self, dt: float, level) -> None:
        keys = pygame.key.get_pressed()
        left = any(keys[k] for k in LEFT_KEYS)
        right = any(keys[k] for k in RIGHT_KEYS)
        jump_held = any(keys[k] for k in JUMP_KEYS)
        self.ducking = any(keys[k] for k in DUCK_KEYS) and self.on_ground

        move = (1 if right else 0) - (1 if left else 0)
        accel = MOVE_ACCEL if self.on_ground else AIR_ACCEL
        if move != 0 and not self.ducking:
            self.vx += move * accel * dt
            self.vx = max(-MAX_RUN_SPEED, min(MAX_RUN_SPEED, self.vx))
            self.facing = move
        elif self.on_ground:
            # Reibung
            fr = GROUND_FRICTION * dt
            if abs(self.vx) <= fr:
                self.vx = 0.0
            else:
                self.vx -= fr * (1 if self.vx > 0 else -1)

        # Sprung: Coyote-Zeit + Eingabepuffer
        self.coyote = COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        jump_pressed = jump_held and not self.prev_jump
        self.buffer = JUMP_BUFFER if jump_pressed else max(0.0, self.buffer - dt)
        if self.buffer > 0 and self.coyote > 0 and not self.ducking:
            self.vy = -JUMP_SPEED
            self.on_ground = False
            self.coyote = 0.0
            self.buffer = 0.0
            self.jump_active = True
            level.game.audio.play("jump")
        # variabler Sprung: Taste früh losgelassen -> Aufstieg kappen
        if self.jump_active and not jump_held and self.vy < 0:
            self.vy *= JUMP_CUTOFF
            self.jump_active = False
        if self.vy >= 0:
            self.jump_active = False
        self.prev_jump = jump_held

        self.apply_gravity(dt)
        self.move_and_collide(level.tilemap, dt)

        if self.invuln > 0:
            self.invuln -= dt

        self._update_anim(dt)

    def _update_anim(self, dt: float) -> None:
        if not self.on_ground:
            self.state = "jump" if self.vy < 0 else "fall"
        elif self.ducking:
            self.state = "duck"
        elif abs(self.vx) > 8:
            self.state = "walk"
        else:
            self.state = "idle"
        anim = self.anims[self.state]
        if self.state == "walk":
            # Laufanimation an Tempo koppeln
            anim.frame_time = 1.0 / max(6.0, 4.0 + abs(self.vx) * 0.09)
        anim.update(dt)

    # --- Kampf / Treffer --------------------------------------------
    def bounce(self) -> None:
        self.vy = -STOMP_BOUNCE
        self.jump_active = False

    def hurt(self) -> bool:
        """Nimmt Schaden, wenn nicht unverwundbar. True = tatsächlich getroffen."""
        if self.invuln > 0 or self.dead:
            return False
        self.invuln = 1.5
        return True

    # --- Zeichnen ----------------------------------------------------
    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.invuln > 0 and int(self.invuln * 20) % 2 == 0:
            return  # Blinken bei Unverwundbarkeit
        img = self.anims[self.state].image
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        ox, oy = camera.offset
        surface.blit(img, (round(self.x) + SPRITE_OFF_X - ox, round(self.y) + SPRITE_OFF_Y - oy))
