import os.path
import time
from random import randint, choice
from .agent import agent_type
from .agent.model import model_config

import json

from argparse import ArgumentParser

parser = ArgumentParser(description='Client of battle city')
parser.add_argument('--is-silent', action='store_true', default=False)
parser.add_argument('--a_type', type=str, help='ip of server to listen', default='server')
parser.add_argument('--model', type=str, help='ip of server to listen', default='glm4')
parser.add_argument('--exp', type=str, help='experiment', default='client_test')
parser.add_argument('--sync', action='store_true', default=False, help='show borders with collisions')

LOG_PATH = "./battle_city/log"

state_to_agent = {
    's1': 'single_one',
    's3': 'single_three',
    'd1': 'double_one2',
    'd2': 'double_two',
    'c1': 'double_one2',
    'c2': 'coop_one',
    'c3': 'coop_two',
    'c1_wo_coop': 'double_one2_wo_coop',
    'c2_wo_coop': 'double_two',
    'c3_wo_coop': 'double_one2_wo_coop',
}

class Game(object):

    def __init__(self, loop, reader, writer, a_type, model, exp_name, sync):
        self.loop = loop
        self.reader = reader
        self.writer = writer
        self.first_tick = False
        self.start = False
        # Agent Initialize
        time_str = time.strftime('-%Y%m%d%H%M%S', time.localtime(time.time()))
        self.log_path = os.path.join(LOG_PATH, exp_name+time_str)
        self.model = model
        self.a_type = a_type
        if a_type == 'server':
            self.agent = None
        else:
            if self.model == 'random':
                self.agent = agent_type[self.model](None, self.log_path)
            else:
                self.agent = agent_type[a_type](model_config[model], self.log_path)
        self.player_id = None
        self.last_act_time = 0
        self.action_number = 0
        self.sync = sync

    async def loop_game(self):
        """
        sometimes execute any random action
        for example this tank make random choices (is a dummy tank!)
        """
        if not self.first_tick:
            if not self.agent:
                await self.send(action='greet', name='PYTHON', need_stage='')
            else:
                await self.send(action='greet', name='PYTHON')
            self.first_tick = True
            await self.send(action='set_speed', speed=1)
            time.sleep(1)

        if not self.sync:
            if self.start:
                await self.send(action='world')

            # turn_time = 0.4
            turn_time = 1.2
            if self.last_act_time < turn_time:
                self.call_soon(turn_time-self.last_act_time)
            else:
                self.call_soon(0.01)

    async def act(self, word_data):
        start_time = time.time()
        print('act')
        # act_dict, _ = await self.agent.chat(word_data, self.player_id, lang='cn')
        # if act_dict:
        #     await self.send(**act_dict)
        act_dict, _, coop_dict, llm_data = await self.agent.act(word_data, self.player_id, lang='cn')
        if act_dict:
            self.last_act_time = round(time.time()-start_time, 2)
            act_dict['act_time'] = self.last_act_time
            self.action_number += 1
            act_dict['action_number'] = self.action_number
            llm_data['action_data'] = act_dict
            await self.send(**act_dict)
        else:
            self.action_number += 1
            await self.send(action='noop', action_number=self.action_number)
        if coop_dict:
            llm_data['coop_data'] = coop_dict
            if 'coop_target' in coop_dict and coop_dict['coop_target']:
                await self.send(**coop_dict)
                if coop_dict['action'] == 'stop_cooperation':
                    self.agent.coop_target = None
        self.agent.log_data(llm_data)

    async def reply(self, message_data):
        act_dict, _, llm_data = await self.agent.reply(message_data, self.player_id, lang='cn')
        if act_dict:
            llm_data['reply_data'] = act_dict
            await self.send(**act_dict)
        self.agent.log_data(llm_data)

    async def process_reply(self, message_data):
        if message_data['coop_content'] == 'Agree':
            self.agent.coop_target = message_data['coop_source']
            act_dict = {'action': 'setup_cooperation', 'coop_source': message_data['coop_target'], 'coop_target': message_data['coop_source'],
                        'coop_content': message_data['coop_data']}
            if 'coop_goal' in message_data:
                act_dict['coop_goal'] = message_data['coop_goal']
            await self.send(**act_dict)
            # self.agent.log_data({'coop_data': act_dict})

    async def act_rand(self, word_data):
        # rand action
        action = randint(0, 1)
        if action == 0:  # set direction
            direction = choice(['up', 'down', 'left', 'right'])
            await self.send(action='rotate', direction=direction)
        else:  # SHOT SHOT
            await self.send(action='shoot')

    def call_soon(self, time):
        loop.call_later(time, self._loop)

    async def receive(self, data):
        """
        get json from server and do something
        for example show on console data
        """

        status = data.get('status')
        if status == 'data':
            if data.get('action') == 'move':
                return  # too many data ;_;
        elif status == 'game_status':
            print('show')
            await self.act(data)
        elif status == 'send':
            # print(data)
            await self.reply(data)
        elif status == 'reply':
            await self.process_reply(data)
        elif status == 'game':
            action = data.get('action')
            if action == 'start':
                self.start = True
            elif action == 'over':
                self.start = False
        elif status == 'OK' and 'player_id' in data:
            self.player_id = data['player_id']
            if 'stage' in data:
                if self.model == 'random':
                    self.agent = agent_type[self.model](None, self.log_path)
                else:
                    self.agent = agent_type[state_to_agent[data['stage']]](model_config[self.model], self.log_path)
        elif status == 'reward' or status == 'final_status' or status == 'start_status':
            print('reward data')
            self.agent.log_data(data)

        # if is_silent:
        #     return
        if status == 'ERROR':
            print(self._get_color(data), data, '\033[0m')

    async def send(self, **data):
        if data is None:
            return
        print(data)
        raw_data = json.dumps(data)
        writer = self.writer
        writer.write(raw_data.encode())
        writer.write(b'\n')
        await writer.drain()

    def _loop(self):
        return ensure_future(self.loop_game())

    @staticmethod
    def _get_color(data):
        status = data.get('status')
        if status == 'ERROR':
            return '\033[91m'  # red color
        if status == 'OK':
            return '\033[35m'  # purple color
        if status == 'game':
            return '\033[34m'  # blue color
        if status == 'game':
            action = data.get('action')
            if action == 'spawn':
                return '\033[92m'  # green color
            if action == 'destroy':
                return '\033[93m'  # orange color
        return '\033[0m'  # default color


from asyncio import get_event_loop, open_connection, ensure_future

async def handle_client(loop):
    reader, writer = await open_connection('127.0.0.1', 8888,
                                           # loop=loop,
                                           limit=256 * 1000)
    print('\033[1mCONNECTED!\033[0m')

    args = parser.parse_args()
    game = Game(loop, reader, writer, args.a_type, args.model, args.exp, args.sync)
    loop.call_soon(game._loop)

    while True:
        raw_data = await reader.readline()
        data = json.loads(raw_data)
        await game.receive(data)


if __name__ == "__main__":
    loop = get_event_loop()
    handler = handle_client(loop)
    loop.run_until_complete(handler)
    loop.close()
