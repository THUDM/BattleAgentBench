import json
from .cn_single_one import single_one_action_prompt
from .cn_single_three import single_three_action_prompt
from .cn_double_one2 import double_one_action_coop_prompt2, double_one_reply_prompt2
from .cn_double_one2_wo_coop import double_one_action_prompt2
from .cn_double_two import double_two_action_prompt
from .cn_coop_one import coop_one_action_coop_prompt, coop_one_reply_prompt
from .cn_coop_two import coop_two_action_coop_prompt, coop_two_reply_prompt

from .agent import BaseAgent
from .agent_util_data import split_team_tanks, sort_tanks, check_front_info, check_around_info, remove_option_border, make_tank_base_str, make_coop_str, check_result
from .agent_util_extract import extract_action, extract_intention, check_and_make_action, check_and_make_target_action, check_and_make_coop, check_and_make_reply, check_and_make_coop2

class SingleOneAgent(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):
        own_tank, _ = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank])

        base_info = make_tank_base_str(game_status['enemy_base'], True)
        front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)

        if self.history:
            before_action = json.dumps(self.history[-1], ensure_ascii=False)
        else:
            before_action = '无'

        input_prompt = single_one_action_prompt % (game_status['turn_number'], own_info, base_info, front_info, before_action)
        if touched_border:
            input_prompt = remove_option_border(input_prompt, touched_border[0])
        if touched_wall_direction:
            input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        operation, params = extract_action(answer)
        intention = extract_intention(answer, lang)
        action_data = check_and_make_action(answer, operation)
        if action_data:
            self.history.append(operation)
        return action_data, intention, None, llm_data

class SingleThreeAgent(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):
        own_tank, _ = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank])
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks)
        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)

        if self.history:
            before_action = json.dumps(self.history[-1], ensure_ascii=False)
        else:
            before_action = '无'

        input_prompt = single_three_action_prompt % (game_status['turn_number'], own_info, base_info, enemy_info, front_info, before_action)
        if touched_border:
            input_prompt = remove_option_border(input_prompt, touched_border[0])
        if touched_wall_direction:
            input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        operation, params = extract_action(answer)
        intention = extract_intention(answer, lang)
        action_data = check_and_make_action(answer, operation)
        if action_data:
            self.history.append(operation)
        return action_data, intention, None, llm_data

class DoubleOneAgent2(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):
        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank])

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        target_info = json.dumps(game_status['team_target'])
        coop_info = make_coop_str(game_status['coop_info'][-5:])

        if self.history:
            before_operation = self.history[-1]['operation']
            if before_operation[0] != 'ERROR':
                pre_result = check_result(before_operation, own_tank, enemy_tanks+game_status['enemy_base'], only_front,
                                          self.history[-1]['own_tank'], self.history[-1]['enemy_tanks']+self.history[-1]['enemy_base'], self.history[-1]['front_info'])
                self.history[-1]['result'] = pre_result
                before_action = f'Target {before_operation[1]}: {before_operation[0]}'
            else:
                before_action = before_operation[0]
            before_result = self.history[-1]['result']
        else:
            before_action = '无'
            before_result = '无'

        input_prompt = double_one_action_coop_prompt2 % (game_status['turn_number'], own_info, other_info, own_base_info, base_info, enemy_info, target_info, coop_info, around_info, before_action, before_result)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_coop_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data, error_text = check_and_make_target_action(answer, operation, params, sorted_tanks + [-1, 200], base_ids)

        coop_operation, coop_params = extract_action(answer, 'coop2')
        coop_data = check_and_make_coop2(answer, coop_operation, coop_params, player_id, self.target, self.coop_target, other_tank_ids)

        if action_data:
            if params[0] != '200':
                # if self.target and self.target != int(params[0]) and coop_data and coop_data['action'] != 'send':
                #     coop_data = {'action': 'stop_cooperation', 'coop_source': player_id, 'coop_target': self.coop_target}
                self.target = int(params[0])
            else:
                action_data['target'] = self.target
            # self.history.append(f'{operation} {params[0]}: {params[1]}')
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': [params[1], self.target],
                'result': None
            })
        else:
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': ['ERROR'],
                'result': f'操作格式不合法：{error_text}'
            })

        return action_data, intention, coop_data, llm_data

    async def reply(self, message_data, player_id, lang='en', rule=True):
        content = f"{message_data['coop_source']}: {message_data['coop_content']}"
        game_status = message_data['game_status']

        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank])

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)
        
        target_info = json.dumps(game_status['team_target'])
        coop_info = make_coop_str(game_status['coop_info'][-5:])

        if self.history:
            before_action = json.dumps(self.history[-1], ensure_ascii=False)
        else:
            before_action = '无'

        input_prompt = double_one_reply_prompt2 % (game_status['turn_number'], own_info, other_info, own_base_info, base_info, enemy_info, target_info, coop_info, around_info, content)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_reply_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data = check_and_make_reply(answer, operation, params, message_data)

        return action_data, intention, llm_data

class DoubleOneAgent2WOCoop(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):

        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank])

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        if self.history:
            before_operation = self.history[-1]['operation']
            if before_operation[0] != 'ERROR':
                pre_result = check_result(before_operation, own_tank, enemy_tanks+game_status['enemy_base'], only_front,
                                          self.history[-1]['own_tank'], self.history[-1]['enemy_tanks']+self.history[-1]['enemy_base'], self.history[-1]['front_info'])
                self.history[-1]['result'] = pre_result
                before_action = f'Target {before_operation[1]}: {before_operation[0]}'
            else:
                before_action = before_operation[0]
            before_result = self.history[-1]['result']
        else:
            before_action = '无'
            before_result = '无'

        input_prompt = double_one_action_prompt2 % (game_status['turn_number'], own_info, other_info, own_base_info, base_info, enemy_info, around_info, before_action, before_result)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_target_action_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data, error_text = check_and_make_target_action(answer, operation, params, sorted_tanks + [-1, 200], base_ids)
        if action_data:
            if params[0] != '200':
                self.target = int(params[0])
            else:
                action_data['target'] = self.target
            # self.history.append(f'{operation} {params[0]}: {params[1]}')
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': [params[1], self.target],
                'result': None
            })
        else:
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': ['ERROR'],
                'result': f'操作格式不合法：{error_text}'
            })
        return action_data, intention, None, llm_data
    
class DoubleTwoAgent(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):

        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank])

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        if self.history:
            before_operation = self.history[-1]['operation']
            if before_operation[0] != 'ERROR':
                pre_result = check_result(before_operation, own_tank, enemy_tanks+game_status['enemy_base'], only_front,
                                          self.history[-1]['own_tank'], self.history[-1]['enemy_tanks']+self.history[-1]['enemy_base'], self.history[-1]['front_info'])
                self.history[-1]['result'] = pre_result
                before_action = f'Target {before_operation[1]}: {before_operation[0]}'
            else:
                before_action = before_operation[0]
            before_result = self.history[-1]['result']
        else:
            before_action = '无'
            before_result = '无'

        input_prompt = double_two_action_prompt % (game_status['turn_number'], own_info, own_base_info, base_info, enemy_info, around_info, before_action, before_result)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_target_action_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data, error_text = check_and_make_target_action(answer, operation, params, sorted_tanks + [-1, 200], base_ids)
        if action_data:
            if params[0] != '200':
                self.target = int(params[0])
            else:
                action_data['target'] = self.target
            # self.history.append(f'{operation} {params[0]}: {params[1]}')
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': [params[1], self.target],
                'result': None
            })
        else:
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': ['ERROR'],
                'result': f'操作格式不合法：{error_text}'
            })
        return action_data, intention, None, llm_data

class CoopOneAgent(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):
        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank], with_type=True)

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks, with_type=True)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        target_info = json.dumps(game_status['team_target'])
        coop_info = make_coop_str(game_status['coop_info'][-5:])

        if self.history:
            before_operation = self.history[-1]['operation']
            if before_operation[0] != 'ERROR':
                pre_result = check_result(before_operation, own_tank, enemy_tanks+game_status['enemy_base'], only_front,
                                          self.history[-1]['own_tank'], self.history[-1]['enemy_tanks']+self.history[-1]['enemy_base'], self.history[-1]['front_info'])
                self.history[-1]['result'] = pre_result
                before_action = f'Target {before_operation[1]}: {before_operation[0]}'
            else:
                before_action = before_operation[0]
            before_result = self.history[-1]['result']
        else:
            before_action = '无'
            before_result = '无'

        input_prompt = coop_one_action_coop_prompt % (game_status['turn_number'], own_info, own_base_info, base_info, enemy_info, target_info, coop_info, around_info, before_action, before_result)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_coop_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data, error_text = check_and_make_target_action(answer, operation, params, sorted_tanks + [-1, 200], base_ids)

        coop_operation, coop_params = extract_action(answer, 'coop2')
        coop_data = check_and_make_coop2(answer, coop_operation, coop_params, player_id, self.target, self.coop_target, sorted_tanks)

        if action_data:
            if params[0] != '200':
                # if self.target and self.target != int(params[0]) and coop_data and coop_data['action'] != 'send':
                #     coop_data = {'action': 'stop_cooperation', 'coop_source': player_id, 'coop_target': self.coop_target}
                self.target = int(params[0])
            else:
                action_data['target'] = self.target
            # self.history.append(f'{operation} {params[0]}: {params[1]}')
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': [params[1], self.target],
                'result': None
            })
        else:
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': ['ERROR'],
                'result': f'操作格式不合法：{error_text}'
            })
        if coop_data and 'coop_target' in coop_data and coop_data['coop_target'] and coop_data['coop_target'] >= 10:
            # skip coop with npc tanks
            del coop_data['coop_target']

        return action_data, intention, coop_data, llm_data

    async def reply(self, message_data, player_id, lang='en', rule=True):
        content = f"{message_data['coop_source']}: {message_data['coop_content']}"
        game_status = message_data['game_status']

        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank], with_type=True)

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks, with_type=True)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        target_info = json.dumps(game_status['team_target'])
        coop_info = make_coop_str(game_status['coop_info'][-5:])

        if self.history:
            before_action = json.dumps(self.history[-1], ensure_ascii=False)
        else:
            before_action = '无'

        input_prompt = coop_one_reply_prompt % (game_status['turn_number'], own_info, own_base_info, base_info, enemy_info, target_info, coop_info, around_info, content)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_reply_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data = check_and_make_reply(answer, operation, params, message_data)

        return action_data, intention, llm_data

class CoopTwoAgent(BaseAgent):
    async def act(self, game_status, player_id, lang='en'):
        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank], with_type=True)

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank, with_type=True)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks, with_type=True)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        target_info = json.dumps(game_status['team_target'])
        coop_info = make_coop_str(game_status['coop_info'][-5:])

        if self.history:
            before_operation = self.history[-1]['operation']
            if before_operation[0] != 'ERROR':
                pre_result = check_result(before_operation, own_tank, enemy_tanks+game_status['enemy_base'], only_front,
                                          self.history[-1]['own_tank'], self.history[-1]['enemy_tanks']+self.history[-1]['enemy_base'], self.history[-1]['front_info'])
                self.history[-1]['result'] = pre_result
                before_action = f'Target {before_operation[1]}: {before_operation[0]}'
            else:
                before_action = before_operation[0]
            before_result = self.history[-1]['result']
        else:
            before_action = '无'
            before_result = '无'

        input_prompt = coop_two_action_coop_prompt % (game_status['turn_number'], own_info, other_info, own_base_info, base_info, enemy_info, target_info, coop_info, around_info, before_action, before_result)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_coop_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data, error_text = check_and_make_target_action(answer, operation, params, sorted_tanks + [-1, 200], base_ids)

        coop_operation, coop_params = extract_action(answer, 'coop2')
        coop_data = check_and_make_coop2(answer, coop_operation, coop_params, player_id, self.target, self.coop_target, other_tank_ids + sorted_tanks)

        if action_data:
            if params[0] != '200':
                # if self.target and self.target != int(params[0]) and coop_data and coop_data['action'] != 'send':
                #     coop_data = {'action': 'stop_cooperation', 'coop_source': player_id, 'coop_target': self.coop_target}
                self.target = int(params[0])
            else:
                action_data['target'] = self.target
            # self.history.append(f'{operation} {params[0]}: {params[1]}')
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': [params[1], self.target],
                'result': None
            })
        else:
            self.history.append({
                'own_tank': own_tank,
                'enemy_tanks': enemy_tanks,
                'enemy_base': game_status['enemy_base'],
                'front_info': only_front,
                'intention': intention,
                'operation': ['ERROR'],
                'result': f'操作格式不合法：{error_text}'
            })
        if coop_data and 'coop_target' in coop_data and coop_data['coop_target'] and coop_data['coop_target'] >= 10:
            # skip coop with npc tanks
            del coop_data['coop_target']

        return action_data, intention, coop_data, llm_data

    async def reply(self, message_data, player_id, lang='en', rule=True):
        content = f"{message_data['coop_source']}: {message_data['coop_content']}"
        game_status = message_data['game_status']

        own_tank, other_tank = split_team_tanks(player_id, game_status)
        own_info = make_tank_base_str([own_tank], with_type=True)

        other_tank_ids = [t[0] for t in other_tank]
        other_info = make_tank_base_str(other_tank, with_type=True)
        own_base_info = make_tank_base_str(game_status['own_base'], True)

        base_ids = [ba[0] for ba in game_status['enemy_base']]
        base_info = make_tank_base_str(game_status['enemy_base'], True)

        enemy_tanks = game_status['enemy_tanks']
        enemy_info = make_tank_base_str(enemy_tanks, with_type=True)
        sorted_tanks = sort_tanks(own_tank, enemy_tanks)
        sorted_info = json.dumps(sorted_tanks)

        # nearst_walls = get_nearst_walls(own_tank, game_status['map_walls'])
        # nearst_info = json.dumps(nearst_walls)
        # front_info, touched_border, touched_wall_direction, touched_tank_direction = check_front_info(own_tank, game_status)
        around_info, only_front = check_around_info(own_tank, game_status)

        target_info = json.dumps(game_status['team_target'])
        coop_info = make_coop_str(game_status['coop_info'][-5:])

        if self.history:
            before_action = json.dumps(self.history[-1], ensure_ascii=False)
        else:
            before_action = '无'

        input_prompt = coop_two_reply_prompt % (game_status['turn_number'], own_info, other_info, own_base_info, base_info, enemy_info, target_info, coop_info, around_info, content)
        # if touched_border:
        #     input_prompt = remove_option_border(input_prompt, touched_border[0])
        # if touched_wall_direction:
        #     input_prompt = remove_option_border(input_prompt, touched_wall_direction[0])
        answer, llm_data = await self.model_call(input_prompt, [], None)
        # answer, llm_data = rule_act(input_prompt, own_tank, [game_status['enemy_base'][0][0]], game_status['enemy_base'], touched_wall_direction, touched_tank_direction)
        llm_data['game_status'] = game_status

        # answer, llm_data = test_reply_data(input_prompt)

        operation, params = extract_action(answer, 'adv')
        intention = extract_intention(answer, lang)
        action_data = check_and_make_reply(answer, operation, params, message_data)

        return action_data, intention, llm_data
