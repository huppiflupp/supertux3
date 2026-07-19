"""Buddy-System: Tier-Powerups, die dem Pinguin helfen.

* Schildkröte  -> Item einsammeln -> ~10 s Schutzschild (Spieler.shield_t).
* Giraffe      -> Item einsammeln -> Begleiter erscheint und legt seinen Hals
                  als temporäre, begehbare Brücke über die nächste Lücke.

Die Giraffe erzeugt an der Abgrundkante ein solides Brücken-Rechteck
(`bridge_rect`), das ``Level.solid_entity_rects()`` mitzählt.
"""
from __future__ import annotations

import math

import pygame

from .entity import Entity
from ..settings import TILE

SHIELD_DURATION = 10.0     # Sekunden Schutzschild pro Schildkröte
NECK_H = 12                # Dicke des Brücken-Halses in Pixeln
GAP_REACH = 4              # so viele Kacheln vor Pengu wird nach einer Kante gesucht
GAP_MAX = 8                # breiteste überbrückbare Lücke (Kacheln)


class TurtleItem(Entity):
    """Schwebendes Schildkröten-Powerup: verleiht ein Schutzschild."""

    def __init__(self, x, y, assets):
        img = assets.turtle
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.12) % (math.pi * 2)

    def update(self, dt, level):
        self.t += dt * 2.5
        self.y = self.base_y + math.sin(self.t) * 4.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class GiraffeItem(Entity):
    """Schwebendes Giraffen-Powerup: ruft einen Giraffen-Begleiter."""

    def __init__(self, x, y, assets):
        base = assets.giraffe
        h = 30
        w = max(1, round(base.get_width() * h / base.get_height()))
        img = pygame.transform.smoothscale(base, (w, h))
        super().__init__(x, y, w, h)
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.1) % (math.pi * 2)

    def update(self, dt, level):
        self.t += dt * 2.5
        self.y = self.base_y + math.sin(self.t) * 4.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


FRIEND_DURATION = 20.0     # Sekunden Begleit-Freund
FRIEND_RANGE = 220.0       # Reichweite, in der der Freund Gegner beschießt


class FriendItem(Entity):
    """Schwebendes Freund-Powerup: ruft einen kämpfenden Begleiter."""

    def __init__(self, x, y, assets):
        img = assets.friend
        super().__init__(x, y, img.get_width(), img.get_height())
        self.img = img
        self.base_y = float(y)
        self.t = (x * 0.1) % (math.pi * 2)

    def update(self, dt, level):
        self.t += dt * 2.5
        self.y = self.base_y + math.sin(self.t) * 4.0

    def draw(self, surface, camera):
        ox, oy = camera.offset
        surface.blit(self.img, (round(self.x) - ox, round(self.y) - oy))


class Friend(Entity):
    """Begleiter-Pinguin: folgt Pengu und wirft Fische auf nahe Gegner."""

    def __init__(self, player, assets):
        img = assets.friend
        super().__init__(player.x, player.y, img.get_width(), img.get_height())
        self.img = img
        self.player = player
        self.assets = assets
        self.life = FRIEND_DURATION
        self.cd = 0.6
        self.t = 0.0
        self.remove = False

    def _nearest_enemy(self, level):
        best, bd = None, FRIEND_RANGE
        for e in level.enemies:
            if getattr(e, "squashed", False) or getattr(e, "remove", False):
                continue
            d = math.hypot(e.cx - self.cx, e.cy - self.cy)
            if d < bd:
                best, bd = e, d
        return best

    def update(self, dt, level):
        self.t += dt
        self.life -= dt
        if self.life <= 0:
            self.remove = True
            return
        p = self.player
        # hinter Pengu herlaufen (leichtes Wippen)
        side = -1 if p.facing >= 0 else 1
        self.x = p.cx + side * (TILE * 1.5) - self.w / 2
        self.y = (p.y + p.h) - self.h - abs(math.sin(self.t * 5)) * 3
        self.facing = -side
        # nahe Gegner beschießen (Fisch in level.friendly -> plättet Gegner)
        self.cd = max(0.0, self.cd - dt)
        if self.cd <= 0:
            e = self._nearest_enemy(level)
            if e is not None:
                from .projectiles import Projectile
                d = 1 if e.cx > self.cx else -1
                fish = self.assets.fish
                level.friendly.append(
                    Projectile(self.cx, self.cy - 4, d * 300.0, -120.0,
                               fish, grav=700.0, life=2.0, spin=True))
                self.facing = d
                self.cd = 1.1
                level.game.audio.play("throw")

    def draw(self, surface, camera):
        ox, oy = camera.offset
        img = self.img
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        # zeitliches Ende blinken
        if self.life < 3.0 and int(self.life * 10) % 2 == 0:
            return
        surface.blit(img, (round(self.x) - ox, round(self.y) - oy))


class Giraffe(Entity):
    """Begleiter, der Pengu folgt und über Lücken eine Hals-Brücke bildet."""

    def __init__(self, player, assets):
        img = assets.giraffe
        super().__init__(player.x, player.y, img.get_width(), img.get_height())
        self.img = img
        self.player = player
        self.bridge_rect: pygame.Rect | None = None
        self.t = 0.0

    # --- Brücken-Erkennung ------------------------------------------------
    def _detect_gap(self, level) -> pygame.Rect | None:
        """Sucht in Blickrichtung die nächste Boden-Lücke und liefert das
        Brücken-Rechteck, das sie schließt – oder None."""
        p = self.player
        tm = level.tilemap
        t = TILE
        # Bodenkachel-Zeile unter den Füßen
        gy = int(round(p.rect.bottom / t))
        d = 1 if p.facing >= 0 else -1
        front_tx = int((p.rect.right if d > 0 else p.rect.left) // t)

        # erste leere Kachel (Kante) in Blickrichtung finden
        edge = None
        for i in range(0, GAP_REACH + 1):
            tx = front_tx + d * i
            if tm.is_solid(tx, gy):
                continue
            edge = tx
            break
        if edge is None:
            return None

        # anderes Ufer suchen
        far = None
        for j in range(1, GAP_MAX + 2):
            tx = edge + d * j
            if tm.is_solid(tx, gy):
                far = tx
                break
        if far is None:
            return None    # zu breit oder kein Boden dahinter -> nicht überbrücken

        if d > 0:
            x0, x1 = edge * t, far * t
        else:
            x0, x1 = (far + 1) * t, (edge + 1) * t
        return pygame.Rect(int(x0), gy * t, int(x1 - x0), NECK_H)

    def update(self, dt, level):
        self.t += dt
        p = self.player
        # bestehende Brücke halten, bis Pengu drüber ist oder weit weg läuft
        if self.bridge_rect is not None:
            b = self.bridge_rect
            if p.rect.left > b.right + 4 or p.rect.right < b.left - TILE * 3:
                self.bridge_rect = None
        # neue Brücke bauen, sobald Pengu am Boden an eine Kante kommt
        if self.bridge_rect is None and p.on_ground:
            self.bridge_rect = self._detect_gap(level)

        # Position: an der nahen Brückenkante bzw. neben Pengu auf dem Boden
        if self.bridge_rect is not None:
            b = self.bridge_rect
            if p.facing >= 0:
                self.x = b.left - self.w
            else:
                self.x = b.right
            self.y = b.top - self.h
        else:
            side = -1 if p.facing >= 0 else 1
            self.x = p.cx + side * (TILE * 1.4) - self.w / 2
            self.y = (p.y + p.h) - self.h
        self.facing = p.facing

    def draw(self, surface, camera):
        ox, oy = camera.offset
        # Hals-Brücke (Rechteck) zeichnen, wenn aktiv
        if self.bridge_rect is not None:
            b = self.bridge_rect
            r = pygame.Rect(b.x - ox, b.y - oy, b.w, b.h)
            pygame.draw.rect(surface, (170, 112, 54), r, border_radius=4)
            pygame.draw.rect(surface, (240, 198, 98),
                             r.inflate(-2, -3), border_radius=4)
            for sx in range(r.left + 8, r.right - 4, 16):
                pygame.draw.circle(surface, (170, 112, 54), (sx, r.centery), 2)
        img = self.img
        if self.facing < 0:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (round(self.x) - ox, round(self.y) - oy))
