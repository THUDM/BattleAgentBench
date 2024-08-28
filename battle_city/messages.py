def get_monster_serialized_data(monster, action='change'):
    return dict(
        status='data',
        action=action,
        id=monster.id.hex,
        type=monster.get_type(),
        speed=monster.speed,
        position=monster.get_position(),
        is_freeze=monster.is_freeze,
        parent=monster.parent and monster.parent.id.hex,
        direction=monster.direction.value,
    )


def get_monster_serialized_move_data(monster):
    return dict(
        status='data',
        action='move',
        id=monster.id.hex,
        position=monster.get_position(),
    )


def get_basic_data(monster):
    return dict(
        type=monster.get_type(),
        id=monster.id.hex,
        position=monster.get_position(),
    )


def get_world_data(player, game):
    return dict(
        id=player.id.hex,
        cords=[get_basic_data(monster) for monster in game.get_all_chain()]
    )

def get_mon_data(monster, type=None, id=None, position=True, direction=False, health=True):
    mon_dict = []
    if id:
        mon_dict.append(monster.player_id)
    if position:
        mon_dict.append(monster.get_position()['x'])
        mon_dict.append(monster.get_position()['y'])
    if direction:
        mon_dict.append(monster.direction.value)
    if health:
        mon_dict.append(monster.health)
    if type:
        mon_dict.append(monster.get_type())
    return mon_dict

def get_game_status(player, game):
    status = dict(
        own_id=player.player_id,
        turn_number=game.time_total - game.time_left,
        stage=game.stage
        # map_coins=[get_mon_data(monster) for monster in game.coins]
    )
    # print('---', player.player_id, player.target)
    if game.game_mode == 'normal' or game.game_mode == 'team':
        team_tanks = game.alive_players
        status['team_tanks'] = [get_mon_data(monster, id=True, direction=True) for monster in team_tanks]
        status['enemy_tanks'] = [get_mon_data(monster, id=True, direction=True) for monster in game.npcs]
        status['team_target'] = [[monster.player_id, monster.target] for monster in game.alive_players]
        # team_ids = [m.player_id for m in game.alive_players]
        # for monster in game.alive_players:
        #     if monster.target in team_ids:
        #         print('--------target error', monster.player_id, monster.target)

        own_base = []
        enemy_base = []
        if game.game_mode == 'normal':
            for monster in game.bases:
                enemy_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])
        else:
            for monster in game.bases:
                if game.base_map[monster.base_id] == 0:
                    own_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])
                else:
                    enemy_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])

        # if enemy_base:
        status['own_base'] = own_base
        status['enemy_base'] = enemy_base

        team_ids = [m.player_id for m in team_tanks]
        for monster in team_tanks:
            if monster.target in team_ids or (own_base and monster.target in own_base):
                print('--------target error', monster.player_id, monster.target)
                print(team_ids)
    elif game.game_mode == 'fight':
        team_tanks = [monster for monster in game.alive_players if monster.player_id == player.player_id]
        status['team_tanks'] = [get_mon_data(monster, id=True, direction=True) for monster in team_tanks]
        status['enemy_tanks'] = [get_mon_data(monster, id=True, direction=True) for monster in game.npcs]
        enemy_players = [get_mon_data(monster, id=True, direction=True) for monster in game.alive_players if monster.player_id != player.player_id]
        status['enemy_tanks'] += enemy_players
        status['team_target'] = [[monster.player_id, monster.target] for monster in team_tanks]

        own_base = []
        enemy_base = []
        for monster in game.bases:
            if game.base_map[monster.base_id] == player.player_id:
                own_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])
            else:
                enemy_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])
        # if own_base:
        status['own_base'] = own_base
        # if enemy_base:
        status['enemy_base'] = enemy_base

        team_ids = [m.player_id for m in team_tanks]
        for monster in team_tanks:
            if monster.target in team_ids or (own_base and monster.target in own_base):
                print('--------target error', monster.player_id, monster.target)
                print(team_ids)
    else:
        # team fight
        team_tanks = []
        enemy_tanks = []
        for alive_p in game.alive_players:
            if alive_p.player_id % game.team_count == player.player_id % game.team_count:
                team_tanks.append(alive_p)
            else:
                enemy_tanks.append(alive_p)
        status['team_tanks'] = [get_mon_data(monster, id=True, direction=True) for monster in team_tanks]
        status['enemy_tanks'] = [get_mon_data(monster, id=True, direction=True) for monster in game.npcs]
        enemy_players = [get_mon_data(monster, id=True, direction=True) for monster in enemy_tanks]
        status['enemy_tanks'] += enemy_players
        status['team_target'] = [[monster.player_id, monster.target] for monster in team_tanks]

        own_base = []
        enemy_base = []
        for monster in game.bases:
            if game.base_map[monster.base_id] % game.team_count == player.player_id % game.team_count:
                own_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])
            else:
                enemy_base.append([monster.base_id, monster.get_position()['x'], monster.get_position()['y']])

        # if own_base:
        status['own_base'] = own_base
        # if enemy_base:
        status['enemy_base'] = enemy_base

        team_ids = [m.player_id for m in team_tanks]
        for monster in team_tanks:
            if monster.target in team_ids or (own_base and monster.target in own_base):
                print('--------target error', monster.player_id, monster.target)
                print(team_ids)

    # status['coop_info'] = [[list(k), v] for k, v in game.cooperation.items()
    #                         if k[0] == player.player_id or k[1] == player.player_id]
    status['coop_info'] = [[[item['coop_source'], item['coop_target']], item['coop_content']] for item in game.cooperation
                           if item['coop_source'] == player.player_id or item['coop_target'] == player.player_id]

    status['map_walls'] = [get_mon_data(monster, type=True, health=False) for monster in game.walls]

    return status


def get_start_game_data():
    return dict(
        status='game',
        action='start',
    )


def get_over_game_data(game):
    players = sorted(game.alive_players, key=lambda player: -player.score)
    try:
        player = players[0]
    except (KeyError, IndexError):
        return dict(
            status='game',
            action='over',
            winner=None,
        )

    return dict(
        status='game',
        action='over',
        winner=player.id.hex,
    )


def get_tick_game_data(game):
    return dict(
        status='game',
        action='info',
        ticks_left=game.time_left,
        npcs_left=len(game.npcs),
    )


def get_remove_monster_data(monster):
    return dict(
        status='data',
        action='destroy',
        id=monster.id.hex,
    )