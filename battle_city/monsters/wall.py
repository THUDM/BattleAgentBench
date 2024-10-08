from battle_city.basic import Direction

from uuid import UUID, uuid4
from pygame import Rect


class Wall(object):
    id = None  # type: UUID
    position = None  # type: Rect
    SIZE = 32

    def __init__(self, x: int, y: int):
        self.id = uuid4()
        size = self.SIZE
        self.position = Rect(x, y, size, size)

    def get_type(self):
        return self.__class__.__name__.lower()

    def get_position(self):
        return dict(
            x=self.position.x,
            y=self.position.y,
        )

    def hurt(self) -> (bool, bool):
        """

        :return: (is_destroyed, is_touched)
        """
        return True, True

    def get_grid_position(self):
        return self.position


class TinyWall(Wall):
    SIZE = 8

    def get_grid_position(self):
        return Rect(
            (self.position.x >> 4) << 4,
            (self.position.y >> 4) << 4,
            16,
            16,
        )


class Metal(Wall):

    def hurt(self) -> (bool, bool):
        return False, True


class Water(Wall):

    def hurt(self):
        return False, False

class Base(Wall):
    def __init__(self, base_id, x: int, y: int):
        super().__init__(x, y)
        self.base_id = base_id

    def hurt(self):
        return True, True

class Tree(Wall):

    def hurt(self):
        return False, False

class Snow(Wall):

    def hurt(self):
        return False, False
