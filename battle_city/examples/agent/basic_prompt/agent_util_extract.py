import re
import json

basic_operation = [
    r"#?(Move_up)#?",
    r"#?(Move_down)#?",
    r"#?(Move_left)#?",
    r"#?(Move_right)#?",
    r"#?(Shoot)#?",
]
adv_operation = [
    r"(Target)\s*{?(-?\d+)}?:\s*#?(Move_up|Move_down|Move_left|Move_right|Shoot)#?",
    r"#?(Send_message)#?\s*(.+):\s*(.+)",
    r"#?(Reply_message)#?\s*(.+)",
]
coop_operation = [
    r"#?(Request_coop)#?\s*{?(\d+)}?",
    r"#?(Keep_coop)#?",
    r"#?(Stop_coop)#?",
    r"#?(No_coop)#?",
]
coop_operation2 = [
    r"#?(Request_coop)#?\s*{?(\d+)}?:\s*(.+)",
    r"#?(Keep_coop)#?",
    r"#?(Stop_coop)#?",
    r"#?(No_coop)#?",
]
all_operation = {
    'basic': basic_operation,
    'adv': adv_operation,
    'coop': coop_operation,
    'coop2': coop_operation2
}

def extract_action(answer, op_type='basic'):
    ops = all_operation[op_type]
    # if answer.__contains__('#操作:'):
    #     op_text = answer.split('#操作:')[-1]
    # else:
    #     op_text = ''
    op_text = answer
    for regex in ops:
        matches = re.findall(regex, op_text)
        if matches:
            m = matches[-1]
            if isinstance(m, tuple):
                operation = m[0]
                param = m[1:]
            else:
                operation = m
                param = None

            return operation, param
    return None, None

def extract_intention(answer, lang='en'):
    if lang == 'en':
        matches = re.findall(r"#Thinking Process: (.+)", answer)
    else:
        matches = re.findall(r"长期计划: (.+)\n- 当前操作", answer, re.DOTALL)

    if matches:
        return matches[-1]
    else:
        return None

def extract_content(answer, lang='en'):
    if lang == 'en':
        matches = re.findall(r"#Message Content: (.+)", answer)
    else:
        matches = re.findall(r"#消息内容: (.+)", answer)

    if matches:
        return matches[-1]
    else:
        return None

def make_action(operation, target=-1):
    action = {'target': target}
    if operation == 'Shoot':
        action['action'] = 'shoot'
    else:
        action['action'] = 'rotate'
        if operation == 'Move_up':
            action['direction'] = 'up'
        elif operation == 'Move_down':
            action['direction'] = 'down'
        elif operation == 'Move_left':
            action['direction'] = 'left'
        elif operation == 'Move_right':
            action['direction'] = 'right'
    return action

def make_message(mess_type, content, source, target, coop_content):
    action = {'action': mess_type, 'coop_content': content, 'coop_source': source, 'coop_target': target, 'coop_data': coop_content}
    return action

def check_and_make_target_action(answer, operation, params, sorted_tanks, base_ids=None):
    error_text = None
    # print(operation, params)
    if operation == 'Target' and len(params) == 2 and ((int(params[0]) in sorted_tanks) or (base_ids and int(params[0]) in base_ids)):
        action_data = make_action(params[1], int(params[0]))
    else:
        print('No Valid Operation! Model Output is:', answer)
        action_data = None
        error_text = re.sub(r'#思考过程.*?\n#', '', answer, flags=re.DOTALL)
    return action_data, error_text

def check_and_make_action(answer, operation):
    if operation:
        action_data = make_action(operation)
    else:
        print('No Valid Operation! Model Output is:', answer)
        action_data = None
    return action_data

def check_and_make_coop(answer, coop_op, params, player_id, target, coop_target, other_tank_ids):
    if coop_op == 'Request_coop' and len(params) == 1:
        if target and target != -1 and int(params[0]) in other_tank_ids:
            content = f'请一起攻击{target}号坦克'
            coop_data = {'action': 'send', 'coop_source': player_id, 'coop_target': int(params[0]), 'coop_goal': target, 'coop_content': content}
        else:
            coop_data = {'action': 'send', 'coop_source': player_id}
    elif coop_op == 'Stop_coop':
        coop_data = {'action': 'stop_cooperation', 'coop_source': player_id, 'coop_content': '停止协作'}
        if coop_target:
            coop_data['coop_target'] = coop_target
    elif coop_op == 'Keep_coop' or coop_op == 'No_coop':
        coop_data = {'action': coop_op}
    else:
        print('No Valid Cooperation! Model Output is:', answer)
        coop_data = None
    return coop_data

def check_and_make_coop2(answer, coop_op, params, player_id, target, coop_target, other_tank_ids):
    if coop_op == 'Request_coop' and len(params) == 2:
        if int(params[0]) in other_tank_ids:
            content = params[1]
            coop_data = {'action': 'send', 'coop_source': player_id, 'coop_target': int(params[0]), 'coop_content': content}
        else:
            coop_data = {'action': 'send', 'coop_source': player_id}
    elif coop_op == 'Stop_coop':
        coop_data = {'action': 'stop_cooperation', 'coop_source': player_id, 'coop_content': '停止协作'}
        if coop_target:
            coop_data['coop_target'] = coop_target
    elif coop_op == 'Keep_coop' or coop_op == 'No_coop':
        coop_data = {'action': coop_op}
    else:
        print('No Valid Cooperation! Model Output is:', answer)
        coop_data = None
    return coop_data

def check_and_make_reply(answer, operation, params, message_data):
    if operation and params:
        action_data = make_message('reply', params[0], message_data['coop_target'], message_data['coop_source'], message_data['coop_content'])
        if 'coop_goal' in message_data:
            action_data['coop_goal'] = message_data['coop_goal']
    else:
        print('No Valid Operation! Model Output is:', answer)
        action_data = None
    return action_data

