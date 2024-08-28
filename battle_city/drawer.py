from itertools import product

from pygame.rect import Rect

from battle_city.basic import Direction
from battle_city.monsters.wall import Wall, Metal, Water, TinyWall, Base, Tree, Snow

from pygame.image import load as img_load
from pygame.transform import rotate
from pygame import Surface

from os import path

import pygame
import pygame.display
import pygame.draw


DIR = path.abspath(path.dirname(__file__))
IMAGES_DIR = path.join(DIR, '..', 'images')


class Drawer(object):
    game = None  # type: game.Game
    time = 0 # type: int
    show_borders = False

    SCREEN_WIDTH = 800 + 250
    SCREEN_HEIGHT = 600
    OFFSET_X = 32 + 250
    OFFSET_Y = 32

    OFFSET_LABELS_X = 550 + 250
    OFFSET_LABELS_Y = 32
    FONT_SIZE = 24

    PLAYER_COLORS = [
        (255, 255, 0),
        (0, 255, 0),
        (255, 0, 0),
        (0, 128, 255),
    ]

    def __init__(self, game, show_borders=False):
        pygame.init()
        pygame.display.set_caption('BATTLE CITY AI')
        self.time = 0
        self.background = Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.screen = pygame.display.set_mode(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)
        self.font = pygame.font.SysFont('monospace', self.FONT_SIZE, bold=True)
        self.player_font = pygame.font.SysFont('monospace', 20, bold=True)
        self.npc_font = pygame.font.SysFont('monospace', 18, bold=True)
        self.mess_font = pygame.font.SysFont('songti', 15, bold=False)
        self.game = game
        self.show_borders = show_borders
        self.player_map = {0: 4, 1: 3, 2: 2, 3: 1}
        if game.game_mode == 'normal' or game.game_mode == 'team':
            self.map_function = lambda x: self.player_map[0]
        elif game.game_mode == 'fight':
            self.map_function = lambda x: self.player_map[x]
        else:
            self.map_function = lambda x: self.player_map[x % game.team_count]
        

    def load_textures(self):
        self.IMAGES = dict(
            NPC_1=self._load_pack('npc_1'),
            NPC_2=self._load_pack('npc_2'),
            BULLET=self._load_pack('bullet'),
            FREEZE=self._load_simple('freeze'),
            COIN=self._load_simple('coin'),
        )

        for player_num, frame in product([1, 2, 3, 4], [1, 2]):
            key = 'PLAYER_{}_{}'.format(player_num, frame)
            path_key = 'player_{}{}'.format(player_num, frame)
            self.IMAGES[key] = self._load_pack(path_key)

        self.WALLS = {
            TinyWall: self._load_simple('wall'),
            Metal: self._load_simple('metal'),
            Water: self._load_simple('water'),
            Base: self._load_simple('base'),
            Tree: self._load_simple('tree'),
            Snow: self._load_simple('snow'),
        }

    @staticmethod
    def _load_pack(name):
        pathfile = path.join(IMAGES_DIR, '%s.png' % name)
        image = img_load(pathfile)

        return {
            Direction.UP: image,
            Direction.LEFT: rotate(image, 90),
            Direction.DOWN: rotate(image, 180),
            Direction.RIGHT: rotate(image, 270),
        }

    @staticmethod
    def _load_simple(name):
        pathfile = path.join(IMAGES_DIR, '%s.png' % name)
        return img_load(pathfile)

    def render(self):
        self._support_events()

        self.time = self.time + 1
        if self.time >= 100:
            self.time = 0
    
        self._render_background()
        self._render_players()
        self._render_bullets()
        self._render_npcs()
        self._render_text()
        self._render_message_text()
        self._post_render()

    def _post_render(self):
        pygame.display.flip()

    def _support_events(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit(0)

    def _render_background(self):
        self.screen.blit(self.background, (0, 0))

    def bake_static_background(self):
        surface = Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self._render_solid_colors(surface)
        self._render_walls(surface)
        self._render_bases(surface)
        self._render_coins(surface)
        self.background = surface

    def _render_solid_colors(self, surface: Surface):
        surface.fill((0x5f, 0x57, 0x4f))
        rect_size = (self.OFFSET_X, self.OFFSET_Y, self.game.WIDTH, self.game.HEIGHT)
        pygame.draw.rect(surface, (0, 0, 0), rect_size)

    def _render_players(self):
        players = self.game.alive_players
        for player in players:
            player_pack = 'PLAYER_{}'.format(self.map_function(player.player_id))
            image_pack = self._get_frame(player, player_pack)

            if self.show_borders:
                self._draw_rectangle(player.get_grid_position())
                self._draw_rectangle(player.position, color=(0, 0xFF, 0))
            self._blit(image_pack, player)
            if player.is_freeze and self.time % 30 < 15:
                self._blit('FREEZE', player)

            # add number on tank
            color = (255, 255, 255)
            image = self.player_font.render(str(player.player_id), 1, color)
            cords = (self.OFFSET_X + player.position.x+8, self.OFFSET_Y + player.position.y+8)
            self.screen.blit(image, cords)

    def _render_npcs(self):
        npcs = self.game.npcs
        for npc in npcs:
            image = self._get_frame(npc, 'NPC')
            if self.show_borders:
                self._draw_rectangle(npc.get_grid_position())
                self._draw_rectangle(npc.position, color=(0, 0xFF, 0))
            self._blit(image, npc)

            # add number on tank
            color = (255, 255, 0)
            image = self.npc_font.render(str(npc.player_id), 1, color)
            cords = (self.OFFSET_X + npc.position.x+8, self.OFFSET_Y + npc.position.y+8)
            self.screen.blit(image, cords)

    def _get_frame(self, obj, img: str):
        prediction = self.time * obj.speed * 0.8 % 2 < 1
        image_pack = '{}_{}'.format(img, 1 if prediction else 2)
        return image_pack

    def _render_bullets(self):
        for bullet in self.game.bullets:
            if self.show_borders:
                self._draw_rectangle(bullet.get_grid_position())
                self._draw_rectangle(bullet.position, color=(0, 0xFF, 0))
            self._blit('BULLET', bullet)

    def _render_walls(self, surface):
        for wall in self.game.walls: 
            position = wall.position
            cords = (self.OFFSET_X + position.x, self.OFFSET_Y + position.y)
            xx = position.x % Wall.SIZE
            yy = position.y % Wall.SIZE
            area = (xx, yy, position.width, position.height)
            image = self.WALLS[type(wall)]
            surface.blit(image, cords, area)

    def _render_bases(self, surface):
        for wall in self.game.bases:
            position = wall.position
            cords = (self.OFFSET_X + position.x, self.OFFSET_Y + position.y)
            xx = position.x % Wall.SIZE
            yy = position.y % Wall.SIZE
            area = (xx, yy, position.width, position.height)
            image = self.WALLS[type(wall)]
            surface.blit(image, cords, area)

    def _render_coins(self, surface):
        for coin in self.game.coins:
            position = coin.position
            cords = (self.OFFSET_X + position.x, self.OFFSET_Y + position.y)
            surface.blit(self.IMAGES['COIN'], cords)

    def _render_text(self):
        npcs_left = self.game.npcs_left
        npcs_in_area = len(self.game.npcs)
        time_left = self.game.time_left
        self._render_label('title', 'BATTLE CITY AI', (0, 0))
        self._render_label('npc_left', 'NPCs left:    {:03d}'.format(npcs_left), (0, 40))
        self._render_label('npc', 'NPCs in area: {:03d}'.format(npcs_in_area), (0, 60))
        self._render_label('time', 'Time left:    {:03d}'.format(time_left), (0, 80))

        if not self.game.is_ready():
            self._render_label('not-ready', 'NOT READY', (0, 100))
        elif self.game.is_over():
            self._render_label('over', 'GAME OVER', (0, 120), color=(255, 0, 0))

        for num, player in enumerate(self.game.players, start=1):
            # name_label = player.nick or 'P%s' % player.player_id
            name_label = 'P%s' % (player.player_id)
            info_label = self._get_info_label(player)
            label = '{:10} {:06d}'.format(name_label, player.score)
            # color = self.PLAYER_COLORS[player.player_id]
            color = self.PLAYER_COLORS[2+(player.player_id + 1) % 2]
            self._render_label('p-%s' % num, label, (0, 140 + 30 * num), color, self.player_font)
            self._render_label('p-info-%s' % num, info_label, (0, 155 + 30 * num), color, self.player_font)

            # add target
            target_name = '{:10} {:06d}'.format(name_label, player.target)
            self._render_label('p-%s' % num, target_name, (0, 350 + 20 * num), color, self.player_font)

    def _wrap_text(self, text, font, max_width):
        words = list(text)
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def _render_message_text(self):
        messages = self.game.messages
        y_offset = self.SCREEN_HEIGHT - self.mess_font.get_height() - 60
        for mess in reversed(messages):
            mess = f"{mess['coop_source']} to {mess['coop_target']}: {mess['coop_content']}"
            wrap_lines = self._wrap_text(mess, self.mess_font, 250)
            for line in reversed(wrap_lines):
                image = self.mess_font.render(line, 1, (0xff, 0xf1, 0xe8))
                new_cords = (32, y_offset)
                self.screen.blit(image, new_cords)
                y_offset -= self.mess_font.get_height()
                if y_offset < 32:
                    break
            if y_offset < 32:
                break

    def _get_info_label(self, player):
        if player.is_game_over and self.time < 50:
            return 'KILLED'
        elif not player.connection:
            return 'WAIT'
        elif player.is_freeze:
            return 'FREEZE'
        else:
            return ''

    def _render_label(self, id: str,  label: str, cords, color=(0xff, 0xf1, 0xe8), font_=None):
        font_ = font_ if font_ else self.font
        image = font_.render(label, 1, color)
        new_cords = (self.OFFSET_LABELS_X + cords[0], self.OFFSET_LABELS_Y + cords[1])
        self.screen.blit(image, new_cords)

    def _blit(self, image_name, monster, rect=None):
        image_pack = self.IMAGES[image_name]

        if isinstance(image_pack, dict):
            image = image_pack[monster.direction]
        else:
            image = image_pack

        position = rect or monster.position
        cords = (self.OFFSET_X + position.x, self.OFFSET_Y + position.y)
        self.screen.blit(image, cords)

    def _draw_rectangle(self, rect, color=(0xFF, 0, 0)):
        nrect = Rect(
            self.OFFSET_X + rect.x,
            self.OFFSET_Y + rect.y,
            rect.width,
            rect.height,
        )
        pygame.draw.rect(self.screen, color, nrect)
