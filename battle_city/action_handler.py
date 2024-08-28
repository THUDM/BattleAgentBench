from battle_city.game import Game
from battle_city.basic import Direction
from battle_city.monsters import Player

from battle_city import messages


class ActionHandler(object):

    @staticmethod
    async def write_ok(player: Player, **data):
        await player.connection.write_ok(**data)

    @staticmethod
    async def write_error(player: Player, error: str):
        await player.connection.write_error(error)

    @classmethod
    async def can_has_action(cls, game: Game, player: Player):
        if player.had_action:
            await cls.write_error(player, 'too many actions per turn')
            return False
        else:
            await cls.set_had_action(player, game)
            return True

    @classmethod
    async def action_undefined(cls, data: dict, player: Player, game: Game):
        await cls.write_error(player, 'unknown action')

    @classmethod
    async def action_rotate(cls, data: dict, player: Player, game: Game):
        raw_direction = data.get('direction', '').lower()
        try:
            direction = Direction(raw_direction)
        except ValueError:
            await cls.write_error(player, 'unknown direction')
            return

        # with await game.step_lock:
        async with game.step_lock:
            if not await cls.can_has_action(game, player):
                print('move error')
                return
            player.set_speed(1)
            player.set_direction(direction)
            player.action_number = data['action_number']
            # print('player', direction)
            if 'target' in data:
                player.target = data['target']
            await cls.set_had_action(player, game)
        await cls.write_ok(
            player,
            direction=direction.value,
            position=player.get_position()
        )

    @classmethod
    async def action_set_speed(cls, data: dict, player: Player, game: Game):
        speed = data.get('speed')
        if not isinstance(speed, int):
            await cls.write_error(player, 'speed has wrong value')
            return

        # with await game.step_lock:
        async with game.step_lock:
            # if not await cls.can_has_action(game, player):
            #     print('set speed error')
            #     return
            player.set_speed(speed)
            # await cls.set_had_action(player, game)
        await cls.write_ok(player, speed=player.speed)

    @classmethod
    async def action_shoot(cls, data: dict, player: Player, game: Game):
        # with await game.step_lock:
        async with game.step_lock:
            if not await cls.can_has_action(game, player):
                print('shoot error')
                return
            player.set_speed(0)
            player.set_shot()
            player.action_number = data['action_number']
            # print('player shoot')
            if 'target' in data:
                player.target = data['target']
            await cls.set_had_action(player, game)
        await cls.write_ok(player)

    @classmethod
    async def action_noop(cls, data: dict, player: Player, game: Game):
        # with await game.step_lock:
        async with game.step_lock:
            player.set_speed(0)
            player.action_number = data['action_number']

    @classmethod
    async def action_greet(cls, data: dict, player: Player, game: Game):
        if player.ready:
            await cls.write_error(player, 'you are greeted before')
            return

        try:
            name = data['name']
        except KeyError:
            await cls.write_error(player, 'name is undefined')
            return

        if not isinstance(name, str):
            await cls.write_error(player, 'name has wrong type')
            return

        name = name.strip()
        if not name:
            await cls.write_error(player, 'name is blank')
            return

        if len(name) > 10:
            await cls.write_error(player, 'name is too long (max is 10)')
            return

        player.set_nick(name)
        world_data = messages.get_world_data(player, game)
        world_data['player_id'] = player.player_id
        if 'need_stage' in data:
            world_data['stage'] = game.stage
        await cls.write_ok(player, **world_data)

    @classmethod
    async def action_world(cls, data: dict, player: Player, game: Game):
        data = messages.get_game_status(player, game)
        data['status'] = 'game_status'
        # print(data)
        await player.connection.write(data)

    @classmethod
    async def action_send(cls, data: dict, player: Player, game: Game):
        game.messages.append(data)
        target_player_id = data['coop_target']
        target_player = [p for p in game.alive_players if p.player_id == target_player_id]
        if target_player:
            data['status'] = 'send'
            data['game_status'] = messages.get_game_status(target_player[0], game)
            await target_player[0].connection.write(data)

    @classmethod
    async def action_reply(cls, data: dict, player: Player, game: Game):
        game.messages.append(data)
        data['status'] = 'reply'
        target_player_id = data['coop_target']
        target_player = [p for p in game.alive_players if p.player_id == target_player_id]
        if target_player:
            await target_player[0].connection.write(data)

    @classmethod
    async def action_setup_cooperation(cls, data: dict, player: Player, game: Game):
        # source = data['coop_source']
        # target = data['coop_target']
        # if 'coop_content' in data:
        #     game.cooperation[(source, target)] = data['coop_content']
        # if 'coop_goal' in data:
        #     player.target = data['coop_goal']
        #     game.cooperation[(source, target)] = data['coop_goal']
        game.cooperation.append(data)

    @classmethod
    async def action_stop_cooperation(cls, data: dict, player: Player, game: Game):
        # source = data['coop_source']
        # target = data['coop_target']
        # del game.cooperation[(source, target)]
        game.cooperation.append(data)

    @staticmethod
    async def set_had_action(player: Player, game: Game):
        player.set_had_action()
        data = messages.get_monster_serialized_data(player)
        await game.broadcast(data)

