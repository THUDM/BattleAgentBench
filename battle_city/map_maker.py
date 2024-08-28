from battle_city.monsters import Wall, Water, Metal, Spawner, Coin
from os import path
import numpy as np
import random

from battle_city.monsters.wall import TinyWall, Base, Tree, Snow

DIR = path.abspath(path.dirname(__file__))
MAPS_DIR = path.join(DIR, '..', 'maps')


class MapCharError(Exception):
    pass


class MapMaker(object):

    CHAR_TO_METHOD = {
        '.': 'empty',
        ' ': 'empty',
        '$': 'coin',
        '\n': 'empty',
        '#': 'brick',
        '@': 'metal',
        '~': 'water',
        '*': 'spawn',
        '1': 'player',
        '2': 'player',
        '3': 'player',
        '4': 'player',
        '5': 'player',
        '6': 'player',
        '7': 'player',
        '8': 'player',
        'A': 'base',
        'B': 'base',
        'C': 'base',
        'D': 'base',
    }
    CHAR_TO_ID = {
        'A': 100,
        'B': 101,
        'C': 102,
        'D': 103,
    }

    def __init__(self, game, data):
        self.game = game
        self.data = data

    @staticmethod
    def load_data_from_name(name):
        filepath = path.join(MAPS_DIR, '%s.map' % name)
        with open(filepath) as fp:
            lines = fp.readlines()[:16]
        return [list(line[:16].ljust(16, '.')) for line in lines]
    
    def get_index_of_char(self, char):
        # return index of char in data, data is a 16x16 array
        for i in range(16):
            for j in range(16):
                if self.data[i][j] == char:
                    return i, j
        raise MapCharError('char %s not found' % char)

    def get_part_of_index(self, index):
        # return part of index in a 16x16 array from left top, right top, left bottom, right bottom
        row, col = index
        if row < 8 and col < 8:
            return "left_top"
        elif row < 8 and col >= 8:
            return "right_top"
        elif row >= 8 and col < 8:
            return "left_bottom"
        else:
            return "right_bottom"
        
    def sample_index_from_part(self, part, puls=0):
        if part == "left_top":
            return random.randint(0, 7-puls), random.randint(0, 7-puls)
        elif part == "right_top":
            return random.randint(0, 7-puls), random.randint(puls+8, 15)
        elif part == "left_bottom":
            return random.randint(puls+8, 15), random.randint(0, 7-puls)
        else:
            return random.randint(puls+8, 15), random.randint(puls+8, 15)

    def update_data(self, index, part, label):
        plus = 3 if self.game.stage == 'c3' else 0
        while True:
            sampled_index = self.sample_index_from_part(part, plus)
            if self.data[sampled_index] in ['.', '#']:
                self.data[index] = '.'
                self.data[sampled_index] = label
                break

    def shuffle_data(self):
        self.data = np.array(self.data)
        for i in range(self.game.max_players):
            index = self.get_index_of_char(str(i+1))
            part = self.get_part_of_index(index)
            self.update_data(index, part, str(i+1))

    def make(self):
        methods = {
            char: getattr(self, 'make_%s' % name, self.make_unknown)
            for char, name in self.CHAR_TO_METHOD.items()
        }

        for tile_y, line in enumerate(self.data):
            for tile_x, char in enumerate(line):
                cords = (tile_x * 32, tile_y * 32)
                tile_cords = (tile_x, tile_y)
                method = methods.get(char, self.make_unknown)
                method(char, cords, tile_cords)

    def make_empty(self, char, cords, tile_cords):
        """
        Srsly do nothing
        """
        pass

    def make_brick(self, char, cords, tile_cords):
        x, y = cords
        for x_shift in range(0, Wall.SIZE, 8):
            for y_shift in range(0, Wall.SIZE, 8):
                wall = TinyWall(x + x_shift, y + y_shift)
                self.game.walls.append(wall)

    def make_coin(self, char, cords, tile_cords):
        coin = Coin(*cords)
        self.game.coins.append(coin)

    def make_water(self, char, cords, tile_cords):
        water = Water(*cords)
        self.game.walls.append(water)

    def make_metal(self, char, cords, tile_cords):
        metal = Metal(*cords)
        self.game.walls.append(metal)

    def make_base(self, char, cords, tile_cords):
        home = Base(self.CHAR_TO_ID[char], *cords)
        self.game.bases.append(home)

    def make_tree(self, char, cords, tile_cords):
        home = Tree(*cords)
        self.game.walls.append(home)

    def make_snow(self, char, cords, tile_cords):
        home = Snow(*cords)
        self.game.walls.append(home)

    def make_player(self, char, cords, tile_cords):
        number = int(char) - 1
        spawner = Spawner(*cords)
        self.game.player_spawns[number] = spawner

    def make_spawn(self, char, cords, tile_cords):
        spawner = Spawner(*cords)
        self.game.npc_spawns.append(spawner)

    def make_unknown(self, char, cords, tile_cords):
        raise MapCharError(char, tile_cords)
