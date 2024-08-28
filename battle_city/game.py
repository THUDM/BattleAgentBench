from battle_city.collections.sliced_array import SlicedArray
from battle_city.monsters import Player, NPC, Bullet, Wall, Spawner
from battle_city.logic import GameLogic
from battle_city.logger import Logger
from battle_city.drawer import Drawer

from battle_city.map_maker import MapMaker

from battle_city import messages
from battle_city.basic import StageInfo

from typing import List, Dict
from asyncio import wait, Lock
import asyncio
from itertools import chain
from random import shuffle


class Game(object):
    players = None  # type: List[Player]
    npcs = None  # type:  List[NPC]
    bullets = None # type: List[Bullet]
    walls = None  # type: List[Wall]
    coins = None  # type: List[Coin]
    player_spawns = None  # type: Dict[str, Spawner]
    npc_spawns = None  # type: List[Spawner]
    logic = None  # type: GameLogic
    drawer = None  # type: Drawer
    ready = False  # type: False
    step_lock = None  # type: Lock
    npcs_left = 0  # type: int
    ticks = 0  # type: int
    max_players = 2
    show_borders = False

    messages = []
    cooperation = []

    was_ready = False
    was_over = False
    turn_off_after_end = False

    WIDTH = 512
    HEIGHT = 512

    MAX_NPC_IN_AREA = 5

    def __init__(self, turn_off_after_end=False, max_players=2, show_borders=False, mode='team', log_path='game_data.log',
                 time_total=100, total_npcs=10, game_map='single1', team_count=1, stage='s1', seed=0):
        self.npcs = []
        self.bullets = []
        self.walls = SlicedArray()
        self.player_spawns = {}
        self.npc_spawns = []
        self.players = []
        self.alive_players = []
        self.coins = SlicedArray()
        self.connections = []

        self.turn_ticks = 17
        self.ticks = 0
        self.turn_off_after_end = turn_off_after_end
        self.show_borders = show_borders

        self.stage = stage
        stage_info = StageInfo[stage]
        self.game_map = stage_info['game_map'] if 'game_map' in stage_info else game_map
        # normal, team, fight, team_fight
        self.game_mode = stage_info['mode'] if 'mode' in stage_info else mode
        self.team_count = stage_info['team_count'] if 'team_count' in stage_info else team_count
        self.total_npcs = stage_info['total_npcs'] if 'total_npcs' in stage_info else total_npcs
        self.npcs_left = self.total_npcs
        self.time_total = stage_info['time_total'] if 'time_total' in stage_info else time_total
        self.time_left = self.time_total
        self.max_players = stage_info['max_players'] if 'max_players' in stage_info else max_players
        self.seed = seed

        self.bases = SlicedArray()
        # self.base_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        self.base_map = {100: 0, 101: 1, 102: 2, 103: 3}
        self.touch_base = False
        self.logger = Logger(log_path)

        self.logic = GameLogic(self)
        self.drawer = None
        self.step_lock = Lock()

    def load_map(self):
        data_map = MapMaker.load_data_from_name(self.game_map)
        mm = MapMaker(self, data_map)
        if self.seed:
            mm.shuffle_data()
        mm.make()

        self.players = [
            Player(player_id, *self.player_spawns[player_id])
            for player_id in range(self.max_players)
        ]
        # shuffle(self.players)
        self.alive_players = self.players[:]  # copy list

    def set_drawer(self):
        self.drawer = Drawer(self, show_borders=self.show_borders)
        self.drawer.load_textures()
        self.drawer.bake_static_background()

    def set_next_player(self, connection):
        self.connections.append(connection)
        for player in self.players:
            if player.ready:
                continue
            player.set_connection(connection)
            return player 
        else:
            return None

    def is_ready(self):
        return all(player.ready for player in self.players)

    def is_over(self):
        team_end = len(self.bases) == 1

        # # all other bases
        base_ids = [self.base_map[b.base_id] for b in self.bases]
        fight_end = len(base_ids) == 1

        # # all other bases
        team_fight_end = len(base_ids) == 1
        return (
                self.time_left <= 0
                or len(self.alive_players) < 1
                or len(self.bases) == 0
                or (self.game_mode == 'normal' and self.touch_base)
                or (self.game_mode == 'team' and team_end)
                or (self.game_mode == 'fight' and fight_end)
                or (self.game_mode == 'team_fight' and team_fight_end)
        )

    def get_monsters_chain(self):
        return chain(
            self.alive_players,
            self.npcs,
            self.bullets,
        )

    def get_all_chain(self):
        return chain(
            self.alive_players,
            self.npcs,
            self.bullets,
            self.walls,
            self.coins,
        )

    def get_tanks_chain(self):
        return chain(self.alive_players, self.npcs)

    async def broadcast(self, data):
        events = [
            connection.write(data)
            for connection in self.connections
        ]
        if events:
            await wait(events)

    async def send_informations(self):
        for monster in self.get_monsters_chain():
            data = messages.get_monster_serialized_move_data(monster)
            await self.broadcast(data)

    async def step(self):
        is_ready = self.is_ready()
        is_over = self.is_over()

        if not self.was_ready and is_ready:
            self.was_ready = True
            for p in self.alive_players:
                data = messages.get_game_status(p, self)
                data['status'] = 'start_status'
                data['seed'] = self.seed
                await p.connection.write(data)
            await self.broadcast(messages.get_start_game_data())

        if is_over and not self.was_over:
            self.was_over = True

            if self.time_left <= 0 or len(self.alive_players) < 1 or len(self.bases) == 0:
                win_state = 0
            else:
                win_state = 1
            for p in self.alive_players:
                data = messages.get_game_status(p, self)
                data['status'] = 'final_status'
                data['win_state'] = win_state
                await p.connection.write(data)
            await self.broadcast(messages.get_over_game_data(self))
            if self.turn_off_after_end:
                await asyncio.sleep(8)
                exit(0)  # little dangerous lol

        if is_ready and not is_over:
            await self.logic.step()
            await self.send_informations()
        if self.drawer is not None:
            self.drawer.render()
