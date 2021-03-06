import constants
import pygame
from math import sin, cos, pi
from turret import Turret
from hp_bar import HPBar

FORWARD = 1
BACKWARD = 0


class Tank(pygame.sprite.Sprite):
    """
    Represents tank object in the game
    Attributes:
        _player_no: ID of the player that this tank belongs to
        ..other
    """

    def __init__(self, player_no, game, x, y, angle, attributes):
        super().__init__()
        self._player_no = player_no
        self._game = game

        self._x = x
        self._y = y
        self._velocity = pygame.math.Vector2(0, 0)
        self._angle = 0  # if the angle given in __init__ was not 0, the tank will be rotated later
        self._max_speed_multiplier = 1
        self._direction = FORWARD
        # direction in which the tank is moving (FORWARD/BACKWARD) - updated only when the tank starts moving

        self._hp = attributes["hp"]
        self._max_hp = self._hp
        self._max_speed = attributes["max_speed"]
        self._acceleration = attributes["acceleration"]
        self._deceleration = attributes["deceleration"]
        self._drag = attributes["drag"]
        self._turn_rate = attributes["turn_rate"]
        self._driftiness = attributes["driftiness"]

        turret_attributes = self._game.load_resource(attributes["turret"])
        self._turret = Turret(self, self._game, turret_attributes)

        self._hp_bar = HPBar(self, self._max_hp,
                             constants.hp_bar_width, constants.hp_bar_height, constants.hp_bar_y_offset,
                             constants.hp_bar_filled_color, constants.hp_bar_empty_color)

        shield_attributes = self._game.load_resource(attributes["shield"])
        self._shield_active = False
        self._shield_image = shield_attributes["texture"]
        self._shield_max_hp = shield_attributes["hp"]
        self._shield_hp = shield_attributes["hp"]
        self._shield_cooldown = shield_attributes["cooldown"]
        self._shield_current_cooldown = 0
        self._shield_decay = shield_attributes["decay"]

        self._shield_bar = HPBar(self, self._shield_max_hp,
                                 constants.shield_bar_width, constants.shield_bar_height, constants.shield_bar_y_offset,
                                 constants.shield_bar_filled_color, constants.shield_bar_empty_color)

        self._shield = pygame.sprite.Sprite()
        self._shield.image = self._shield_image
        self._shield.rect = self._shield_image.get_rect()

        self._in_collision = False
        self._collision_cooldown = 0

        self.image = attributes["texture"]
        self.original_image = attributes["texture"]
        # ^required, because repeatedly rotating the same image decreases its quality and increases size^
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        if angle != 0:
            self.rotate(angle)

        self.keys = []  # keys pressed by player

    # Override
    def kill(self):
        """
        Delete this tank from the board
        :return: None
        """
        self._hp_bar.kill()
        self._turret.kill()
        super().kill()

    def keyboard_input(self, keys):
        """
        Receives pressed keys, that will be used to determine user input when updating the tank
        :param ? keys: Input from the keyboard
        :return: None
        """
        self.keys = keys

    def handle_keyboard(self, delta_time):
        """
        Controls the tank, based on pressed keys
        :param float delta_time: Time elapsed since last call of this function
        :return: If no keys were pressed False else True
        :rtype: bool
        """

        if not self.keys:
            return False

        # forward/backward movement
        velocity_changed = False
        if self.keys[pygame.K_UP]:
            if self._direction == FORWARD or self._velocity.magnitude_squared() == 0:
                self.accelerate(self._acceleration * delta_time)
            else:
                self.apply_drag(-self._acceleration * delta_time)
                # if the tank is moving in the opposite direction, treat the input like drag
            velocity_changed = True

        if self.keys[pygame.K_DOWN]:
            if self._direction == BACKWARD or self._velocity.magnitude_squared() == 0:
                self.accelerate(-self._deceleration * delta_time)
            else:
                self.apply_drag(-self._deceleration * delta_time)
                # if the tank is moving in the opposite direction, treat the input like drag
            velocity_changed = True

        if not velocity_changed:
            self.apply_drag(-self._drag * delta_time)

        # turning the tank
        if self.keys[pygame.K_LEFT]:
            self.rotate(self._turn_rate * delta_time)
        if self.keys[pygame.K_RIGHT]:
            self.rotate(-self._turn_rate * delta_time)

        # controlling the turret
        if self.keys[pygame.K_q]:
            self.rotate_turret(delta_time)
        if self.keys[pygame.K_e]:
            self.rotate_turret(-delta_time)
        if self.keys[pygame.K_w]:
            self._turret.shoot()

        # activating the shield
        if self.keys[pygame.K_s]:
            if self._shield_current_cooldown <= 0:
                self.activate_shield()

        return True

    def save_my_data(self):
        """
        Returns all the most important variables of the tank
        :return: x, y, angle, hp and turret's angle of the tank
        :rtype: (int, int, float, float, float)
        """
        return self._x, self._y, self._angle, self._hp, self._turret.angle

    def update(self, delta_time):
        """
        Calculates physics for this client's tank and updates rotation and image position for all tanks
        :param float delta_time: Time elapsed since last call of this function
        :return: None
        """
        # Calculate physics only for this client's tank
        if self._player_no == self._game.my_player_id:
            x, y, angle, hp, turret_angle = self.save_my_data()

            self._collision_cooldown -= delta_time

            if self._shield_active:
                self.offset_shield_hp(-self._shield_decay * delta_time)
            else:
                self._shield_current_cooldown -= delta_time

            self.handle_keyboard(delta_time)

            if self._velocity.magnitude_squared() != 0:
                velocity_magnitude = self._velocity.magnitude()
                angle_vector = pygame.math.Vector2(-sin(self._angle * (pi / 180)),
                                                   -cos(self._angle * (pi / 180)))
                angle_vector *= velocity_magnitude

                if self._direction == BACKWARD:
                    angle_vector = angle_vector.rotate(180)
                    # if the tank is moving backward, invert the angle vector to make the interpolation work correctly
                    # (so the tank "front" is now on the back, and the velocity and angle vectors are closer together)

                if self._driftiness > 0:
                    speed_fraction = abs(velocity_magnitude) / (self._max_speed * self._max_speed_multiplier)
                    speed_fraction **= 3
                    # difference between slow and fast drifting is more noticeable when speed_fraction is raised to 3 power

                    lerp_factor = self._driftiness * speed_fraction
                    if lerp_factor > 1:
                        lerp_factor = 1
                    lerp_factor = 1 - (lerp_factor ** delta_time)

                    self._velocity = self._velocity.lerp(angle_vector, lerp_factor).normalize() * velocity_magnitude
                else:
                    self._velocity = angle_vector

                dx = self._velocity.x * delta_time
                dy = self._velocity.y * delta_time

                self._in_collision = False
                if self.check_x_move(dx):
                    self._x += dx
                else:
                    self._in_collision = True
                    self._velocity.x = 0
                if self.check_y_move(dy):
                    self._y += dy
                else:
                    self._in_collision = True
                    self._velocity.y = 0

                tile_speed = self._game.get_tile_at_screen_position(self._x, self._y).get_attribute("move_speed")
                self._max_speed_multiplier = tile_speed

                if self._in_collision:
                    self._max_speed_multiplier *= constants.object_collision_speed_multiplier
                    if self._collision_cooldown <= 0:
                        self._collision_cooldown = constants.object_collision_cooldown
                        self.offset_hp(-constants.object_collision_damage)

            self._game.send_tank_position(self._x, self._y, self._angle, self._hp, self._turret.angle,
                                          self._shield_active)
            # self._x, self._y, self._angle, self._hp, self._turret.angle = x, y, angle, hp, turret_angle

        # If it's not mine tank
        else:
            self.rotate_not_mine()
            if self._shield_active:
                self.offset_shield_hp(-self._shield_decay * delta_time)  # Update time of the shield

        # Update image for all tanks
        self.rect.center = (self._x, self._y)
        self._hp_bar.update_hp(self._hp)
        if self._shield_active:
            self._shield.rect.center = self.rect.center

    def accelerate(self, acceleration):
        """
        Applies acceleration in the direction the tank is facing
        :param float acceleration: Value of the acceleration
        :return: None
        """

        if self._velocity.magnitude_squared() == 0:
            self._direction = FORWARD if acceleration > 0 else BACKWARD

        self._velocity.x -= acceleration * sin(self._angle * (pi / 180))
        self._velocity.y -= acceleration * cos(self._angle * (pi / 180))

        max_speed_with_multiplier = self._max_speed * self._max_speed_multiplier

        if self._velocity.magnitude_squared() > max_speed_with_multiplier * max_speed_with_multiplier:
            self._velocity = self._velocity.normalize() * max_speed_with_multiplier

    def apply_drag(self, drag):
        """
        Slows down the tank by a given drag value
        :param float drag: Drag value
        :return: None
        """

        if self._velocity.magnitude_squared() == 0:
            return

        start_velocity = self._velocity.copy()

        drag_vector = self._velocity.normalize() * drag

        self._velocity.x += drag_vector.x
        self._velocity.y += drag_vector.y

        if start_velocity.x * self._velocity.x < 0 or start_velocity.y * self._velocity.y < 0:
            # aka if speeds before and after applying drag were in opposite directions
            self._velocity.x = 0
            self._velocity.y = 0

    def rotate_not_mine(self):
        """
        Rotates the image of the tank that does not belong to this client
        :return: None
        """
        self.image = pygame.transform.rotozoom(self.original_image, self._angle, 1)
        self.rect = self.image.get_rect()

    def rotate(self, angle):
        """
        Rotates this client's tank by a given angle
        :param float angle: Angle this tank should be rotated
        :return: None
        """
        self._angle += angle
        self._angle %= 360

        self.image = pygame.transform.rotozoom(self.original_image, self._angle, 1)
        self.rect = self.image.get_rect()
        # self.rect.center = (self._x, self._y)

    def rotate_turret(self, angle):
        """
        Rotates the tank turret by a given angle
        :param float angle: Angle this client's tank's turret should be rotated
        :return: None
        """
        self._turret.rotate(angle)

    def activate_shield(self):
        """
        Activates the shield if it is ready (cooldown <= 0)
        :return: None
        """
        if not self._shield_active:
            self._shield_active = True
            self._shield_current_cooldown = self._shield_cooldown
            self._shield_hp = self._shield_max_hp
            self._shield_bar.update_hp(self._shield_hp)
            self._game.add_hp_bar(self._shield_bar)
            self._shield.rect.center = self.rect.center
            self.groups()[0].add(self._shield)  # a bit hacky but whatever

    def offset_hp(self, value):
        """
        Changes the tank's hp by a given value
        :param float value: Value that the HP should be applied offset
        :return: None
        """
        if not self._shield_active:
            self._hp += value
            self._hp_bar.update_hp(self._hp)
        else:
            pass  # shields are completely invulnerable for now
            # self.offset_shield_hp(value)

    def offset_shield_hp(self, value):
        """
        Changes the tank's shield hp by a given value. Disables the shield if its hp is lesser or equal to 0
        :param float value: Value that the shield's HP should be applied offset
        :return: None
        """
        self._shield_hp += value

        if self._shield_hp <= 0:
            self.shield_deactivate()
        else:
            self._shield_bar.update_hp(self._shield_hp)

    def shield_deactivate(self):
        self._shield_active = False
        self._shield_current_cooldown = self._shield_cooldown
        self._shield.kill()  # a bit hacky but whatever
        self._game.remove_hp_bar(self._shield_bar)

    def check_y_move(self, value):
        """
        Checks if the tank can move to position (x, y+value)
        :param float value: Value how many tiles wants to move in Y-axis
        :return: If it's possible to move so
        :rtype: bool
        """
        if self._y + value < 0 or self._y + value > constants.window_height:
            return False
        if self._game.get_tile_at_screen_position(self._x, self._y + value).get_attribute("blocks_movement"):
            return False
        return True

    def check_x_move(self, value):
        """
        Checks if the tank can move to position (x+value, y)
        :param float value: Value how many tiles wants to move in Y-axis
        :return: If it's possible to move so
        :rtype: bool
        """

        if self._x + value < 0 or self._x + value > constants.window_width:
            return False
        if self._game.get_tile_at_screen_position(self._x + value, self._y).get_attribute("blocks_movement"):
            return False
        return True

    def update_values_from_server(self, x, y, tank_angle, hp, turret_angle, shield_active):
        """
        Updates values of the tank according to the information received from the server
        :param int x: New X coordinate of the tank's location
        :param int y: New Y coordinate of the tank's location
        :param float tank_angle: New tank angle
        :param float hp: New HP
        :param float turret_angle: New turret angle
        :return: None
        """
        self._x = x
        self._y = y
        self._angle = tank_angle
        self._hp = hp
        self._turret.update_from_server(turret_angle)
        if self._shield_active != shield_active:
            if self._shield_active:
                self.shield_deactivate()
            else:
                self.activate_shield()
        self._shield_active = shield_active

    @property
    def turret(self):
        return self._turret

    @property
    def player_no(self):
        return self._player_no

    @property
    def hp_bar(self):
        return self._hp_bar

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    @property
    def angle(self):
        return self._angle

    @property
    def hp(self):
        return self._hp

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def shield_active(self):
        return self._shield_active
