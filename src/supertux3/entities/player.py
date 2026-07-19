"""Der Spieler-Pinguin „Pengu" mit Zuständen klein/groß und Juice."""
from __future__ import annotations

import pygame

from .entity import Entity
from ..engine.animation import Animation
from ..engine import controls
from ..settings import (
    MOVE_ACCEL, AIR_ACCEL, MAX_RUN_SPEED, GROUND_FRICTION,
    JUMP_SPEED, JUMP_CUTOFF, COYOTE_TIME, JUMP_BUFFER, STOMP_BOUNCE,
)

LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
JUMP_KEYS = (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
DUCK_KEYS = (pygame.K_DOWN, pygame.K_s)

# (sprite_w, sprite_h, hitbox_w, hitbox_h) je Zustand
FORM = {
    "small": (40, 48, 24, 44),
    "big":   (60, 72, 34, 66),
}


class Player(Entity):
    def __init__(self, x: float, y: float, assets):
        w, h = FORM["small"][2], FORM["small"][3]
        super().__init__(x, y, w, h)
        self.assets = assets
        self.power = "small"
        self._build_anims()
        self.state = "idle"
        self.coyote = 0.0
        self.buffer = 0.0
        self.prev_jump = False
        self.jump_active = False
        self.ducking = False
        self.invuln = 0.0
        self.coins = 0
        self.scale_x = 1.0
        self.scale_y = 1.0
        # Ereignis-Flags (von der Szene für Effekte ausgelesen)
        self.ev_jumped = False
        self.ev_landed = False
        self.land_vy = 0.0

    # --- Formwechsel -------------------------------------------------
    def _build_anims(self):
        frames = self.assets.player if self.power == "small" else self.assets.player_big
        self.anims = {
            "idle": Animation(frames["idle"], fps=3),
            "walk": Animation(frames["walk"], fps=12),
            "jump": Animation(frames["jump"], fps=1),
            "fall": Animation(frames["fall"], fps=1),
            "duck": Animation(frames["duck"], fps=1),
        }

    def _set_power(self, power: str):
        if power == self.power:
            return
        old_bottom = self.y + self.h
        sw, sh, hw, hh = FORM[power]
        self.power = power
        self.w, self.h = hw, hh
        self.x += (0)  # x-Mitte bleibt ~gleich (schmale Differenz ignorierbar)
        self.y = old_bottom - self.h    # Füße bleiben am Boden
        self._build_anims()

    def grow(self) -> bool:
        if self.power == "small":
            self._set_power("big")
            self.invuln = 0.6
            self.scale_x, self.scale_y = 0.7, 1.4
            return True
        return False

    # --- Steuerung ---------------------------------------------------
    def update(self, dt: float, level) -> None:
        self.ev_jumped = self.ev_landed = False
        was_ground = self.on_ground

        keys = pygame.key.get_pressed()
        km = level.game.keys
        js = level.game.joysticks
        jmove = controls.move_x(js)
        left = any(keys[k] for k in km["left"]) or jmove < 0
        right = any(keys[k] for k in km["right"]) or jmove > 0
        jump_held = any(keys[k] for k in km["jump"]) or controls.want_jump(js)
        self.ducking = (any(keys[k] for k in km["duck"]) or controls.want_duck(js)) and self.on_ground

        move = (1 if right else 0) - (1 if left else 0)
        accel = MOVE_ACCEL if self.on_ground else AIR_ACCEL
        if move != 0 and not self.ducking:
            self.vx += move * accel * dt
            self.vx = max(-MAX_RUN_SPEED, min(MAX_RUN_SPEED, self.vx))
            self.facing = move
        elif self.on_ground:
            fr = GROUND_FRICTION * dt
            self.vx = 0.0 if abs(self.vx) <= fr else self.vx - fr * (1 if self.vx > 0 else -1)

        self.coyote = COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        jump_pressed = jump_held and not self.prev_jump
        self.buffer = JUMP_BUFFER if jump_pressed else max(0.0, self.buffer - dt)
        if self.buffer > 0 and self.coyote > 0 and not self.ducking:
            self.vy = -JUMP_SPEED
            self.on_ground = False
            self.coyote = 0.0
            self.buffer = 0.0
            self.jump_active = True
            self.ev_jumped = True
            self.scale_x, self.scale_y = 0.8, 1.2
            level.game.audio.play("jump")
        if self.jump_active and not jump_held and self.vy < 0:
            self.vy *= JUMP_CUTOFF
            self.jump_active = False
        if self.vy >= 0:
            self.jump_active = False
        self.prev_jump = jump_held

        self.apply_gravity(dt)
        pre_vy = self.vy
        self.move_and_collide(level.tilemap, dt, level.platform_rects())

        # gelandet?
        if not was_ground and self.on_ground and pre_vy > 120:
            self.ev_landed = True
            self.land_vy = pre_vy
            self.scale_x, self.scale_y = 1.25, 0.78

        if self.invuln > 0:
            self.invuln -= dt

        # Squash/Stretch zurückfedern
        self.scale_x += (1.0 - self.scale_x) * min(1.0, 12 * dt)
        self.scale_y += (1.0 - self.scale_y) * min(1.0, 12 * dt)

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
            anim.frame_time = 1.0 / max(6.0, 4.0 + abs(self.vx) * 0.05)
        anim.update(dt)

    # --- Treffer / Kampf --------------------------------------------
    def bounce(self, strength: float = 1.0) -> None:
        self.vy = -STOMP_BOUNCE * strength
        self.jump_active = False
        self.scale_x, self.scale_y = 0.85, 1.15

    def take_hit(self) -> str:
        """Gibt 'die', 'shrink' oder 'none' zurück."""
        if self.invuln > 0 or self.dead:
            return "none"
        if self.power == "big":
            self._set_power("small")
            self.invuln = 1.6
            return "shrink"
        self.invuln = 1.5
        return "die"

    # --- Zeichnen ----------------------------------------------------
    def draw(self, surface: pygame.Surface, camera) -> None:
        if self.invuln > 0 and int(self.invuln * 20) % 2 == 0:
            return
        img = self.anims[self.state].image
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        iw, ih = img.get_size()
        sx = max(0.2, self.scale_x)
        sy = max(0.2, self.scale_y)
        if abs(sx - 1) > 0.01 or abs(sy - 1) > 0.01:
            img = pygame.transform.smoothscale(img, (max(1, int(iw * sx)), max(1, int(ih * sy))))
        ox, oy = camera.offset
        # unten-mittig auf der Hitbox verankern
        bx = self.x + self.w / 2
        by = self.y + self.h
        surface.blit(img, (int(bx - img.get_width() / 2 - ox),
                           int(by - img.get_height() - oy)))
