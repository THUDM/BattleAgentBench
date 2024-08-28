import json
import os.path
import random
import asyncio
from asyncio import sleep, start_server, wait, get_event_loop, Queue
import time
from battle_city.game import Game
from battle_city.action_handler import ActionHandler
from battle_city.connection import PlayerConnection

from argparse import ArgumentParser

parser = ArgumentParser(description='Server of battle city')
parser.add_argument('--ip', type=str, help='ip of server to listen', default='127.0.0.1')
parser.add_argument('--port', type=int, help='port of server to listen', default=8888)
parser.add_argument('--map', type=str, help='path to map', default='s1')
parser.add_argument('--max-players', type=int, default=1)
parser.add_argument('--hidden-window', action='store_true', default=False)
parser.add_argument('--speed', type=float, default=1, help='tick speed in milliseconds')
parser.add_argument('--turn-off-after-end', action='store_true', default=False, help='turn off server when game is end. Good option for machine learning')
parser.add_argument('--show-collision-border', action='store_true', default=False, help='show borders with collisions')
parser.add_argument('--mode', type=str, help='normal, team, fight, team_fight', default='normal')
parser.add_argument('--exp', type=str, help='experiment', default='server_test')
parser.add_argument('--seed', type=int, help='seed', default=0)

LOG_PATH = "./battle_city/log"

start_time = time.time()

async def notify_players(game):
    for player in game.alive_players:
        await ActionHandler.action_world(None, player, game)

async def wait_for_all_acts(game, timeout=180):
    async def get_action_with_timeout(player):
        try:
            action_data = await asyncio.wait_for(player.connection.action_queue.get(), timeout)
            return action_data
        except asyncio.TimeoutError:
            return None

    tasks = [get_action_with_timeout(player) for player in game.alive_players]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    timeout_occurred = False
    for data in results:
        if data is not None:
            # print(data['player_id'], game.alive_players)
            player = [player for player in game.alive_players if player.player_id == data['player_id']]
            if player:
                await handle_action(data, player[0], game)
        else:
            timeout_occurred = True
    return timeout_occurred

async def game_loop(game: Game, speed: float=0.033):
    consecutive_timeouts = 0
    while True:
        if not game.is_over() and game.is_ready():
            if all([player.connection for player in game.alive_players]) and game.ticks % game.turn_ticks == 0:
                await notify_players(game)
                timeout_occurred = await wait_for_all_acts(game)

                if timeout_occurred:
                    consecutive_timeouts += 1
                    print(f"Consecutive timeouts: {consecutive_timeouts}")
                else:
                    consecutive_timeouts = 0

                if consecutive_timeouts >= 2:
                    print("Two consecutive timeouts occurred. Ending the game.")
                    break
        await game.step()
        await sleep(speed)

    print("Game loop ended due to consecutive timeouts.")
    exit(0)


def handle_connection(game):

    async def callback(reader, writer):
        connection = PlayerConnection(reader, writer)
        player = game.set_next_player(connection)
        if player is not None:
            await handle_actions(connection, player=player, game=game)

        writer.close()

    return callback


async def handle_actions(connection, player, game):
    while True:
        try:
            data = await connection.read()
            # print(round(time.time()-start_time, 2), player.player_id, data)
            data['player_id'] = player.player_id
            # print(data)
            game.logger.logger.info(data)
        except ConnectionError:
            return
        if data is None:
            return
        if 'action' in data and data['action'] in ['shoot', 'rotate', 'noop']:
            await connection.action_queue.put(data)
        else:
            await handle_action(data, player, game)


async def handle_action(data: dict, player, game):
    action = 'action_' + data.get('action', 'undefined')
    action_undefined = ActionHandler.action_undefined
    method = getattr(ActionHandler, action, action_undefined)
    await method(data=data, player=player, game=game)


def run():
    args = parser.parse_args()
    if args.seed:
        random.seed(args.seed)

    time_str = time.strftime('-%Y%m%d%H%M%S', time.localtime(time.time()))
    game = Game(
        turn_off_after_end=args.turn_off_after_end,
        max_players=args.max_players,
        show_borders=args.show_collision_border,
        mode=args.mode,
        log_path=os.path.join(LOG_PATH, args.exp+time_str),
        stage=args.map,
        seed=args.seed
    )
    game.load_map()
    if not args.hidden_window:
        game.set_drawer()
    loop = get_event_loop()
    coro_server = start_server(
        handle_connection(game), args.ip, args.port,
        # loop=loop,
    )

    server = loop.run_until_complete(coro_server)
    loop.run_until_complete(game_loop(game, 33 / args.speed / 1000))

    try:
        loop.run_forever()
    except EOFError:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == "__main__":
    run()
