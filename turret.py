import pygame

import constants
from projectile import Projectile
from math import sin, cos, pi
import random


class Turret(pygame.sprite.Sprite):
    def __init__(self, tank, game, attributes):
        super().__init__()

        self._tank = tank
        self._game = game
        self._angle = 0  # angle of the turret relative to tank (doesn't change when tank rotates)
        self._absolute_angle = 0  # absolute angle of the turret (changes when tank rotates)

        self._projectiles = []

        self._rotation_speed = attributes["rotation_speed"]
        self._full_rotation = attributes["full_rotation"]
        self._max_left_angle = attributes["max_left_angle"]
        self._max_right_angle = attributes["max_right_angle"]
        self._cooldown = attributes["cooldown"]
        self._projectile_offsets = attributes["projectile_offsets"]
        self._projectiles_per_shot = attributes["projectiles_per_shot"]
        self._inaccuracy = attributes["inaccuracy"]

        self._projectile_offset_index = 0

        self._ammo = self._game.load_resource(attributes["ammo"])

        self._current_cooldown = 0

        self.image = attributes["texture"]
        self.original_image = attributes["texture"]
        # ^required, because repeatedly rotating the same image decreases its quality and increases size^

        self.rect = self.image.get_rect()
        self.rect.center = (self._tank.x, self._tank.y)

        self._projectile_next_id = self._game._my_player_id * constants.max_projectile_count

    def get_projectile_with_id(self, id):
        for projectile in self._projectiles:
            if projectile.id == id:
                return projectile
        return None

    def delete_projectile(self, id):
        projectile = self.get_projectile_with_id(id)
        projectile.kill()
        self._projectiles.remove(projectile)

    def update_projectile(self, id, x, y):
        projectile = self.get_projectile_with_id(id)
        projectile.update_from_server(x, y)

    def calculate_next_projectile_id(self):
        self._projectile_next_id += 1
        if self._projectile_next_id >= (self._game._my_player_id + 1) * constants.max_projectile_count:
            self._projectile_next_id = self._game._my_player_id * constants.max_projectile_count

    def add_projectile_from_server(self, projectile_id, projectile_x, projectile_y, projectile_angle):
        projectile = Projectile(projectile_id, self._tank, projectile_x, projectile_y, projectile_angle,
                                self, self._ammo)
        self._game.add_projectile(projectile)
        self._projectiles.append(projectile)

    def update(self, delta_time):
        self._current_cooldown -= delta_time

        if self._tank.angle + self._angle != self._absolute_angle:
            self._absolute_angle = self._tank.angle + self._angle
            self.image = pygame.transform.rotozoom(self.original_image, self._absolute_angle, 1)
            self.rect = self.image.get_rect()

        self.rect.center = (self._tank.x, self._tank.y)

    def rotate(self, direction):
        """rotates the turret. The angle is determined by multiplying direction with the turret rotation speed"""

        self._angle += direction * self._rotation_speed
        if not self._full_rotation:
            if self._angle < -self._max_left_angle:
                self._angle = -self._max_left_angle
            elif self._angle > self._max_right_angle:
                self._angle = self._max_right_angle

        self._absolute_angle = self._tank.angle + self._angle
        self.image = pygame.transform.rotozoom(self.original_image, self._absolute_angle, 1)
        self.rect = self.image.get_rect()
        self.rect.center = (self._tank.x, self._tank.y)

    def shoot(self):
        """creates a new projectile, moving in the direction the turret was facing"""

        if self._current_cooldown <= 0:
            self._current_cooldown = self._cooldown

            for i in range(self._projectiles_per_shot):
                offset = self._projectile_offsets[self._projectile_offset_index]

                # # x offset
                # projectile_x = offset[0] * cos(-self._absolute_angle * (pi / 180))
                # projectile_y = offset[0] * sin(-self._absolute_angle * (pi / 180))
                #
                # # y offset
                # projectile_x += -offset[1] * sin(self._absolute_angle * (pi / 180))
                # projectile_y += -offset[1] * cos(self._absolute_angle * (pi / 180))

                projectile_x = self._tank.x
                projectile_y = self._tank.y

                projectile_angle = self._absolute_angle  # - offset[2]
                projectile_angle += (random.random() - 0.5) * self._inaccuracy * 2

                projectile = Projectile(self._projectile_next_id, self._tank, projectile_x, projectile_y,
                                        projectile_angle, self, self._ammo)
                self._game.add_projectile(projectile)
                self._projectiles.append(projectile)
                self._game.send_projectile_add(projectile.id, projectile.x, projectile.y, projectile.angle)
                self.calculate_next_projectile_id()

                self._projectile_offset_index += 1
                self._projectile_offset_index %= len(self._projectile_offsets)

    def update_from_server(self, angle):
        self._angle = angle

    @property
    def game(self):
        return self._game

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
