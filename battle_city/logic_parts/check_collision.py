from asyncio import get_event_loop

from pygame.rect import Rect

from battle_city.basic import Direction
from battle_city.logic_parts.base import LogicPart
from battle_city.monsters.monster import Monster
from battle_city.monsters.player import Player
from battle_city.monsters.npc import NPC
from battle_city.monsters.wall import Base, TinyWall

from battle_city import messages

from math import ceil, floor

ATTACK_BASE_SCORE = 200
ATTACK_NPC_SCORE = 5
ATTACK_ENEMY_SCORE = 10
ATTACK_WALL_SCORE = 0
ATTACK_TEAM_SCORE = -10
ATTACK_OWN_BASE = -20
BE_ATTACK_BY_NPC = -5
BE_ATTACK_BY_ENEMY = -10


class CheckCollisionsLogicPart(LogicPart):
    is_must_refresh_background = False

    async def do_it(self):
        await self.check_bullets_with_player()
        await self.check_bullets_with_npc()
        await self.check_bullets_yourself()
        await self.check_bullets_with_walls()
        await self.check_tank_yourself()
        await self.check_tank_collisions_with_walls()
        await self.check_player_collisions_with_coins()
        if self.game.game_mode == 'normal' and len(self.game.bases) == 1:
            await self.check_player_touch_with_walls()

        if self.is_must_refresh_background:
            self.is_must_refresh_background = False
            self.refresh_background()

    async def check_tank_yourself(self):
        game = self.game

        tanks = list(game.get_tanks_chain())
        for tank_a, tank_b in self.check_collision(tanks, tanks):
            if tank_a is tank_b:
                continue

            # we need to check who was in this field first
            old_col_a = tank_b.check_collision_with_old_position(tank_a)
            old_col_b = tank_a.check_collision_with_old_position(tank_b)

            if old_col_a and old_col_b:
                self._move_monster_with_monster(tank_a, tank_b, 0)
                self._move_monster_with_monster(tank_a, tank_b, 1)
            elif old_col_a:
                self.move_monster_with_static_obj(tank_a, tank_b.position)
            elif old_col_b:
                self.move_monster_with_static_obj(tank_b, tank_a.position)

    def _move_monster_with_monster(self, monster_a, monster_b, axis):
        pos_a = monster_a.position[axis]
        pos_b = monster_b.position[axis]
        old_pos_a = monster_a.old_position[axis]
        old_pos_b = monster_b.old_position[axis]
        diff = pos_a - pos_b

        if old_pos_a - pos_a == 0 and old_pos_b - pos_b == 0:
            return

        if diff > 0:
            diff -= monster_b.position[axis + 2]
        elif diff < 0:
            diff += monster_a.position[axis + 2]
        half_diff = diff / 2

        monster_a.position[axis] -= floor(half_diff)
        monster_b.position[axis] += ceil(half_diff)

    async def check_bullets_with_player(self):
        game = self.game
        players = game.alive_players
        bullets = game.bullets

        for player, bullet in self.check_collision(players, bullets):
            if bullet.parent is player:
                continue
            await self.remove_from_group(bullet, bullets)

            if isinstance(bullet.parent, Player):
                is_team = bullet.parent.player_id % game.team_count == player.player_id % game.team_count
                if game.game_mode == 'normal' or game.game_mode == 'team' or (game.game_mode == 'team_fight' and is_team):
                    # bullet.parent.score += 5
                    await self.freeze(player)
                else:
                    bullet.parent.score += ATTACK_ENEMY_SCORE
                    player.health -= 1
                    game.logger.logger.info(f'player shoot player: {bullet.parent.player_id}-{player.player_id}, '
                                            f'obtain score: {ATTACK_ENEMY_SCORE}, current score: {bullet.parent.score}, current health: {bullet.parent.health}, '
                                            f'obtain score: {BE_ATTACK_BY_ENEMY}, current score: {player.score}, current health: {player.health}'
                                            )
                    reward_data = {
                        'action_number': bullet.parent.action_number,
                        'score_type': 'ATTACK_ENEMY_SCORE',
                        'action_score': ATTACK_ENEMY_SCORE,
                        'current_score': bullet.parent.score
                    }
                    await bullet.parent.connection.write_reward(reward_data)
                    reward_data = {
                        'action_number': player.action_number,
                        'score_type': 'BE_ATTACK_BY_ENEMY',
                        'action_score': BE_ATTACK_BY_ENEMY,
                        'current_score': player.score
                    }
                    await player.connection.write_reward(reward_data)
                    if player.health <= 0:
                        player.set_game_over()
                        data = messages.get_game_status(player, self.game)
                        data['status'] = 'final_status'
                        data['win_state'] = -1
                        await player.connection.write(data)
                        await self.remove_from_group(player, self.game.alive_players)

            else:
                player.health -= 1
                game.logger.logger.info(f'npc shoot player: {bullet.parent.player_id}-{player.player_id}, obtain score: {BE_ATTACK_BY_NPC}, current score: {player.score}, current health: {player.health}')
                reward_data = {
                    'action_number': player.action_number,
                    'score_type': 'BE_ATTACK_BY_NPC',
                    'action_score': BE_ATTACK_BY_NPC,
                    'current_score': player.score
                }
                await player.connection.write_reward(reward_data)
                if player.health <= 0:
                    player.set_game_over()
                    data = messages.get_game_status(player, self.game)
                    data['status'] = 'final_status'
                    data['win_state'] = -1
                    await player.connection.write(data)
                    await self.remove_from_group(player, self.game.alive_players)

    async def check_bullets_with_npc(self):
        game = self.game
        npcs = game.npcs
        bullets = game.bullets

        for npc, bullet in self.check_collision(npcs, bullets):
            if bullet.parent is npc:
                continue

            await self.remove_from_group(bullet, bullets)
            if isinstance(bullet.parent, Player):
                bullet.parent.score += ATTACK_NPC_SCORE
                game.logger.logger.info(f'player shoot npc: {bullet.parent.player_id}-{npc.player_id}, obtain score: {ATTACK_NPC_SCORE}, current score: {bullet.parent.score}, current health: {bullet.parent.health}')
                await self.remove_from_group(npc, npcs)
                reward_data = {
                    'status': 'reward',
                    'action_number': bullet.parent.action_number,
                    'score_type': 'ATTACK_NPC_SCORE',
                    'action_score': ATTACK_NPC_SCORE,
                    'current_score': bullet.parent.score
                }
                await bullet.parent.connection.write(reward_data)

    async def check_bullets_yourself(self):
        game = self.game
        bullets = game.bullets

        for bullet in bullets:
            if not self.is_monster_in_area(bullet):
                await self.remove_from_group(bullet, bullets)

        def callback(bullet):
            return bullet.get_grid_position()

        for bullet_a, bullet_b in self.check_collision(bullets, bullets, callback):
            if bullet_a is bullet_b:
                continue

            await self.remove_from_group(bullet_a, bullets)
            await self.remove_from_group(bullet_b, bullets)

    async def check_bullets_with_walls(self):
        bullets = self.game.bullets

        for bullet in bullets:
            await self.check_bullet_with_walls(bullet)

    async def check_bullet_with_walls(self, bullet):
        game = self.game
        bullets = game.bullets
        walls = game.walls
        bases = game.bases
        is_touched_once = False
        is_destroyed_once = False

        with_collision_walls = bullet.check_collision_with_group(
            group=walls,
            rect=bullet.get_grid_position()
        )
        with_collision_bases = bullet.check_collision_with_group(
            group=bases,
            rect=bullet.get_grid_position()
        )
        wall_and_base = with_collision_walls + with_collision_bases
        for wall in wall_and_base:
            is_destroyed, is_touched = wall.hurt()

            if is_touched:
                is_touched_once = True
            if is_destroyed:
                is_destroyed_once = True

        if is_touched_once:
            await self.remove_from_group(bullet, bullets)

        if is_destroyed_once:
            self.is_must_refresh_background = True
            # I know, ugly :/
            if bullet.direction is Direction.DOWN:
                min_y = min(wall.position.y for wall in wall_and_base)
                walls_to_destroy = (
                    wall for wall in wall_and_base
                    if wall.position.y == min_y
                )
            elif bullet.direction is Direction.UP:
                max_y = max(wall.position.y for wall in wall_and_base)
                walls_to_destroy = (
                    wall for wall in wall_and_base
                    if wall.position.y == max_y
                )
            elif bullet.direction is Direction.RIGHT:
                min_x = min(wall.position.x for wall in wall_and_base)
                walls_to_destroy = (
                    wall for wall in wall_and_base
                    if wall.position.x == min_x
                )
            elif bullet.direction is Direction.LEFT:
                max_x = max(wall.position.x for wall in wall_and_base)
                walls_to_destroy = (
                    wall for wall in wall_and_base
                    if wall.position.x == max_x
                )
            else:
                walls_to_destroy = []

            for wall in walls_to_destroy:
                is_destroyed, _ = wall.hurt()
                if is_destroyed:
                    if not isinstance(wall, Base):
                        await self.remove_from_group(wall, walls)
                        # if isinstance(bullet.parent, Player):
                        #     bullet.parent.score += ATTACK_WALL_SCORE
                        #     game.logger.logger.info(f'player shoot wall: {bullet.parent.player_id}, obtain score: {ATTACK_WALL_SCORE}, current score: {bullet.parent.score}')
                    else:
                        if isinstance(bullet.parent, Player):
                            not_own_in_team = game.base_map[wall.base_id] != 0
                            not_own_in_fight = game.base_map[wall.base_id] != bullet.parent.player_id
                            not_own_in_team_fight = game.base_map[wall.base_id] % game.team_count != bullet.parent.player_id % game.team_count
                            if game.game_mode == 'normal' or (game.game_mode == 'team' and not_own_in_team) or (game.game_mode == 'fight' and not_own_in_fight) or (game.game_mode == 'team_fight' and not_own_in_team_fight):
                                await self.remove_from_group(wall, bases)
                                bullet.parent.score += ATTACK_BASE_SCORE
                                game.logger.logger.info(f'player shoot base: {bullet.parent.player_id}, obtain score: {ATTACK_BASE_SCORE}, current score: {bullet.parent.score}')
                                reward_data = {
                                    'status': 'reward',
                                    'action_number': bullet.parent.action_number,
                                    'score_type': 'ATTACK_BASE_SCORE',
                                    'action_score': ATTACK_BASE_SCORE,
                                    'current_score': bullet.parent.score
                                }
                                await bullet.parent.connection.write(reward_data)
                                # base owner game over
                                base_owner = []
                                if game.game_mode == 'fight':
                                    base_owner = [p for p in game.alive_players if p.player_id == game.base_map[wall.base_id]]
                                elif game.game_mode == 'team_fight':
                                    base_owner = [p for p in game.alive_players if p.player_id % game.team_count == game.base_map[wall.base_id] % game.team_count]
                                for player in base_owner:
                                    player.set_game_over()
                                    data = messages.get_game_status(player, self.game)
                                    data['status'] = 'final_status'
                                    data['win_state'] = -1
                                    await player.connection.write(data)
                                    await self.remove_from_group(player, self.game.alive_players)
                            # else:
                            #     game.logger.logger.info(f'player shoot own_base: {bullet.parent.player_id}, obtain score: {ATTACK_OWN_BASE}, current score: {bullet.parent.score}')
                            #     # bullet.parent.score += ATTACK_OWN_BASE
                            #     reward_data = {
                            #         'status': 'reward',
                            #         'action_number': bullet.parent.action_number,
                            #         'score_type': 'ATTACK_OWN_BASE',
                            #         'action_score': ATTACK_OWN_BASE,
                            #         'current_score': bullet.parent.score
                            #     }
                            #     await bullet.parent.connection.write(reward_data)
                        else:
                            not_own_in_team = game.base_map[wall.base_id] != 1  # for npc
                            if (game.game_mode == 'team' and not_own_in_team) or game.game_mode == 'fight' or game.game_mode == 'team_fight':
                                await self.remove_from_group(wall, bases)
                                # base owner game over
                                base_owner = []
                                if game.game_mode == 'team':
                                    base_owner = [p for p in game.alive_players]
                                elif game.game_mode == 'fight':
                                    base_owner = [p for p in game.alive_players if p.player_id == game.base_map[wall.base_id]]
                                elif game.game_mode == 'team_fight':
                                    base_owner = [p for p in game.alive_players if p.player_id % game.team_count == game.base_map[wall.base_id] % game.team_count]
                                for player in base_owner:
                                    # game.logger.logger.info(f'npc shoot base: {bullet.parent.player_id}-{player.player_id}, obtain score: {BE_ATTACK_BY_NPC}, current score: {player.score}, current health: {player.health}')
                                    # reward_data = {
                                    #     'action_number': player.action_number,
                                    #     'score_type': 'BE_ATTACK_BY_NPC',
                                    #     'action_score': BE_ATTACK_BY_NPC,
                                    #     'current_score': player.score
                                    # }
                                    # await player.connection.write(reward_data)

                                    player.set_game_over()
                                    data = messages.get_game_status(player, self.game)
                                    data['status'] = 'final_status'
                                    data['win_state'] = -1
                                    await player.connection.write(data)
                                    await self.remove_from_group(player, self.game.alive_players)

    async def freeze(self, player: Player):
        player.set_freeze()
        data = messages.get_monster_serialized_data(player, action='freeze')
        await self.game.broadcast(data)

    def is_monster_in_area(self, monster):
        position = monster.position

        width = self.game.WIDTH
        height = self.game.HEIGHT

        return (
            position.left >= 0 and position.right <= width and
            position.top >= 0 and position.bottom <= height
        )

    async def check_tank_collisions_with_walls(self):
        walls = self.game.walls
        bases = self.game.bases
        for monster in self.game.get_tanks_chain():
            # small probability to infinity loop - we need to cancel on 5th try
            for i in range(5):
                # check_collision is very greedy - in future we need quadtree structure
                collision_walls = monster.check_collision_with_group(
                    group=walls,
                    rect=monster.get_grid_position(),
                )
                collision_bases = monster.check_collision_with_group(
                    group=bases,
                    rect=monster.get_grid_position(),
                )
                collision_walls = collision_walls + collision_bases
                if not collision_walls:
                    break
                rect = collision_walls[0].get_grid_position()
                self.move_monster_with_static_obj(monster, rect)

        for monster in self.game.get_tanks_chain():
            if monster.position.left < 0:
                monster.position.x = 0
            elif monster.position.right > self.game.WIDTH:
                monster.position.x = self.game.WIDTH - monster.SIZE

            if monster.position.top < 0:
                monster.position.y = 0
            elif monster.position.bottom > self.game.HEIGHT:
                monster.position.y = self.game.HEIGHT - monster.SIZE

    async def check_player_touch_with_walls(self):
        base = [b for b in self.game.bases][0]
        for monster in self.game.alive_players:
            if monster.position.x + monster.SIZE == base.position.x and base.position.y - (monster.SIZE-1) <= monster.position.y <= base.position.y + (monster.SIZE-1) \
                or monster.position.x == base.position.x + base.SIZE and base.position.y - (monster.SIZE-1) <= monster.position.y <= base.position.y + (monster.SIZE-1) \
                or monster.position.y + monster.SIZE == base.position.y and base.position.x - (monster.SIZE-1) <= monster.position.x <= base.position.x + (monster.SIZE-1) \
                or monster.position.y == base.position.y + base.SIZE and base.position.x - (monster.SIZE-1) <= monster.position.x <= base.position.x + (monster.SIZE-1):
                self.game.touch_base = True
                break

    async def check_player_collisions_with_coins(self):
        players = self.game.alive_players
        coins = self.game.coins

        for player, coin in self.check_collision(players, coins):
            await self.remove_from_group(coin, self.game.coins)
            self.is_must_refresh_background = True
            player.score += 100

    @classmethod
    def move_monster_with_static_obj(cls, monster, rect: Rect):
        cls.move_monster_with_static_obj_axis(monster, rect, axis=0)
        cls.move_monster_with_static_obj_axis(monster, rect, axis=1)

    @staticmethod
    def get_border_diff(pos_a, pos_b, axis: int) -> int:
        """
        :return: for axis=0 A.left - B.right, for axis=1 A.top - B.bottom

        """
        return pos_a[axis] - pos_b[axis] - pos_b[axis + 2]

    @classmethod
    def move_monster_with_static_obj_axis(
            cls, monster: Monster, other_pos: Rect, axis: int):
        monster_pos = monster.position

        # we need to detect direction of move using diff
        diff = monster.position[axis] - monster.old_position[axis]

        # according to diff we can move monster to selected side of other
        if diff > 0:
            monster_pos[axis] += cls.get_border_diff(other_pos, monster_pos, axis)
        elif diff < 0:
            monster_pos[axis] -= cls.get_border_diff(monster_pos, other_pos, axis)

    def refresh_background(self):
        if not self.game.drawer:
            return
        loop = get_event_loop()
        loop.call_soon(self.game.drawer.bake_static_background)

    async def remove_from_group(self, monster, group):
        try:
            group.remove(monster)
        except ValueError:
            return

        data = messages.get_remove_monster_data(monster)
        await self.game.broadcast(data)

    @staticmethod
    def check_collision(group_a, group_b, callback=None):
        callback = callback or (lambda m: m.position)
        for monster in group_a:
            rect = callback(monster)
            collisions = monster.check_collision_with_group(group_b, rect, callback)
            for collision in collisions:
                yield (monster, collision)
