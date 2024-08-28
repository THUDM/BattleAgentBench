import json
import os
import pandas as pd

import heapq
import math

MAP_SIZE = 512
TANK_SIZE = 32
WALL_SIZE = 32
ATTACK_BASE_SCORE = 200
ATTACK_NPC_SCORE = 5
ATTACK_ENEMY_SCORE = 10
BE_ATTACK_BY_NPC = -5
BE_ATTACK_BY_ENEMY = -10

class AStarNode:
    def __init__(self, x, y, g, h, parent):
        self.x = x
        self.y = y
        self.g = g  # Cost from start to the current node
        self.h = h  # Heuristic cost estimate from the current node to the target
        self.f = g + h  # Total cost
        self.parent = parent  # Parent node

    def __lt__(self, other):
        return self.f < other.f

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(point, with_direction=False):
    neighbors = [
        (point[0] - 32, point[1], 'left'),
        (point[0] + 32, point[1], 'right'),
        (point[0], point[1] - 32, 'up'),
        (point[0], point[1] + 32, 'down'),
    ]
    if with_direction:
        return [(x, y, z) for x, y, z in neighbors if 0 <= x <= MAP_SIZE-TANK_SIZE and 0 <= y <= MAP_SIZE-TANK_SIZE]
    else:
        return [(x, y) for x, y, z in neighbors if 0 <= x <= MAP_SIZE-TANK_SIZE and 0 <= y <= MAP_SIZE-TANK_SIZE]

def a_star(map, start, end):
    open_set = []
    heapq.heappush(open_set, AStarNode(start[0], start[1], 0, heuristic(start, end), None))
    g_score = {start: 0}
    closed_set = set()

    while open_set:
        current_node = heapq.heappop(open_set)
        current = (current_node.x, current_node.y)

        if current == end:
            path = []
            while current_node:
                path.append((current_node.x, current_node.y))
                current_node = current_node.parent
            return path[::-1]

        closed_set.add(current)

        for neighbor in get_neighbors(current):
            if neighbor in closed_set or map[neighbor[0]//32][neighbor[1]//32] == 1:
                continue

            tentative_g_score = g_score[current] + 1

            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                g_score[neighbor] = tentative_g_score
                heapq.heappush(open_set, AStarNode(neighbor[0], neighbor[1], tentative_g_score, heuristic(neighbor, end), current_node))

    return []

def shortest_path(tank1, tank2, walls):
    assert len(tank1) == 2, len(tank2) == 2
    if walls:
        assert len(walls[0]) == 2
    map = [[0]*16 for _ in range(16)]

    for wall in walls:
        wx, wy = wall
        map[wx // 32][wy // 32] = 1

    tank1_start = (tank1[0] - tank1[0] % 32, tank1[1] - tank1[1] % 32)
    tank2_end = (tank2[0] - tank2[0] % 32, tank2[1] - tank2[1] % 32)

    path = a_star(map, tank1_start, tank2_end)

    if path:
        return [(x, y) for x, y in path]  # center of 32x32 blocks
    else:
        return None

def compute_distance(first_data, final_data):
    tank_first = [tank for tank in first_data['team_tanks'] if tank[0] == first_data['own_id']][0][1:3]
    tank_final = [tank for tank in final_data['team_tanks'] if tank[0] == first_data['own_id']][0][1:3]

    bases = first_data['enemy_base']
    org_dists = []
    for base in bases:
        wall_first = first_data['map_walls']
        # print(tank_first, tank_final, base[1:3])
        wall_first = [w[:2] for w in wall_first if w[-1] in ['metal', 'water']]
        dist = len(shortest_path(tank_first, base[1:3], wall_first))
        # dist = heuristic(tank_first, base[1:3])
        org_dists.append(dist)

    bases = final_data['enemy_base']
    final_dists = []
    for base in bases:
        wall_first = final_data['map_walls']
        # print(tank_first, tank_final, base[1:3])
        wall_first = [w[:2] for w in wall_first if w[-1] in ['metal', 'water']]
        dist = len(shortest_path(tank_final, base[1:3], wall_first))
        # dist = heuristic(tank_final, base[1:3])
        final_dists.append(dist)
    org_dist = sum(org_dists) / len(org_dists)
    if final_dists:
        final_dist = sum(final_dists) / len(final_dists)
    else:
        final_dist = 0
    sub_dist = org_dist - final_dist
    return org_dist, final_dist, sub_dist

def test_astar():
    tank1_position = (64, 64)
    tank2_position = (320, 320)
    walls = [(96, 64), (64, 96), (192, 128)]

    path = shortest_path(tank1_position, tank2_position, walls)
    print(path)

def compute_next_direction_heuristic(source_tank, target_tank):
    diff_x = source_tank[0] - target_tank[0]
    diff_y = source_tank[1] - target_tank[1]
    next_directs = []
    if diff_x < 0:
        next_directs.append('right')
    elif diff_x > 0:
        next_directs.append('left')
    if diff_y < 0:
        next_directs.append('down')
    elif diff_y > 0:
        next_directs.append('up')
    return ' or '.join(next_directs)


def compute_next_action_without_wall(own_tank, enemy_tank, walls):
    tank_id, pos_x, pos_y, direction = own_tank
    diff_x = pos_x - enemy_tank[1]
    diff_y = pos_y - enemy_tank[2]
    next_direct = compute_next_direction_heuristic(own_tank[1:3], enemy_tank[1:3])
    can_shoot = False
    if abs(diff_x) < 32:
        if diff_y <= 0:
            if direction == 'down':
                can_shoot = True
        elif diff_y > 0:
            if direction == 'up':
                can_shoot = True
    elif abs(diff_y) < 32:
        if diff_x <= 0:
            if direction == 'right':
                can_shoot = True
        elif diff_x > 0:
            if direction == 'left':
                can_shoot = True
    return next_direct, can_shoot

def have_wall(text):
    check = '有wall阻挡，无法继续向前移动，需要射击或调整坦克方向' in text or '阻挡（编号200），无法继续向前移动，需要射击或调整坦克方向' in text
    return check

def compute_move(records, is_base_target=False):
    move_total, move_count = 0, 0
    shoot_total, shoot_count = 0, 0
    border_total, border_error = 0, 0
    wall_total, wall_error = 0, 0
    tank_total, tank_error = 0, 0
    metal_total, metal_error = 0, 0
    water_total, water_error = 0, 0
    for idx, recd in enumerate(records):
        game_data = recd['game_status']
        player_id = game_data['own_id']
        own_tank = [tank[:4] for tank in game_data['team_tanks'] if tank[0] == player_id]
        # own_tank = [tank for tank in game_data['team_tanks'][1:] if tank[0] == player_id]
        target_id = recd['action_data']['target']
        if recd['action_data']['action'] == 'shoot':
            action = 'shoot'
        else:
            action = recd['action_data']['direction']
        map_walls = [w[:2] for w in game_data['map_walls'] if w[-1] in ['metal', 'water']]
        if is_base_target and game_data['enemy_base']:
            target_tank = game_data['enemy_base']
        else:
            target_tank = [tank[:4] for tank in game_data['enemy_tanks'] + game_data['enemy_base'] if tank[0] == target_id]
            # target_tank = [tank for tank in game_data['enemy_tanks'][1:] if tank[0] == target_id]
        if own_tank and target_tank:
            next_action, can_shoot = compute_next_action_without_wall(own_tank[0], target_tank[0], map_walls)

            if action != 'shoot':
                move_total += 1
                if action in next_action:
                    move_count += 1
            else:
                shoot_total += 1
                if can_shoot:
                    shoot_count += 1

            if have_wall(recd['input']):
                wall_total += 1
                if action == own_tank[0][-1]:
                    wall_error += 1
                if not can_shoot and action == 'shoot' and own_tank[0][-1] in next_action:
                    shoot_count += 1
                    # print('wall')
            if '有金属墙阻挡，无法继续向前移动，只能调整坦克方向' in recd['input']:
                metal_total += 1
                if action == own_tank[0][-1] or (not can_shoot and action == 'shoot'):
                    metal_error += 1
            if '有水阻挡，无法继续向前移动，只能调整坦克方向' in recd['input']:
                water_total += 1
                if action == own_tank[0][-1] or (not can_shoot and action == 'shoot'):
                    water_error += 1
            if '为地图边界，无法继续向前移动，需要调整坦克方向' in recd['input']:
                border_total += 1
                if action == own_tank[0][-1] or (not can_shoot and action == 'shoot'):
                    border_error += 1
            if '有敌方坦克阻挡，应立即射击消灭' in recd['input']:
                tank_total += 1
                if action != 'shoot':
                    tank_error += 1
                if not can_shoot and action == 'shoot':
                    shoot_count += 1
                    # print('tank')
    print('---count---')
    print('record, move, wall, border, tank')
    print(len(records), move_total, wall_total, border_total, tank_total)
    move_total = 1 if move_total == 0 else move_total
    shoot_total = 1 if shoot_total == 0 else shoot_total
    wall_total = 1 if wall_total == 0 else wall_total
    border_total = 1 if border_total == 0 else border_total
    tank_total = 1 if tank_total == 0 else tank_total
    metal_total = 1 if metal_total == 0 else metal_total
    water_total = 1 if water_total == 0 else water_total
    move_acc = move_count * 1.0 / move_total
    shoot_acc = shoot_count * 1.0 / shoot_total
    move_percent = move_total * 1.0 / (move_total + shoot_total)
    wall_error = wall_error * 1.0 / wall_total
    border_error = border_error * 1.0 / border_total
    tank_error = tank_error * 1.0 / tank_total
    metal_error = metal_error * 1.0 / metal_total
    water_error = water_error * 1.0 / water_total
    return move_acc, shoot_acc, move_percent, move_total, shoot_total, wall_error, border_error, tank_error, metal_error, water_error

def compute_metric(input_path):
    with open(input_path) as f:
        data = f.readlines()
    data = [json.loads(line.strip()) for line in data if line.strip() != 'null']

    # compute format
    first_data = [line for line in data if 'status' in line and line['status'] == 'start_status']
    final_data = [line for line in data if 'status' in line and line['status'] == 'final_status']
    if first_data and final_data:
        first_data = first_data[0]
        final_data = final_data[0]
    else:
        return {}
    request_line = [line for line in data if 'input' in line]
    is_base_target = True if first_data['stage'] in ['s1', 's2', 's3'] else False
    is_coop = True if first_data['stage'] in ['d1', 'c1', 'c2', 'c3'] else False
    if is_coop:
        format_line = [line for line in request_line if 'action_data' in line and 'coop_data' in line]
        reply_line = [line for line in request_line if 'reply_data' in line]
        format_acc = (len(format_line)+len(reply_line)) * 1.0 / (len(request_line))
        print('coop_line', len(reply_line))
    else:
        format_line = [line for line in request_line if 'action_data' in line]
        format_acc = len(format_line) * 1.0 / (len(request_line))
    if not format_line:
        return {}
    if first_data['stage'] in ['d2', 'c2', 'c2_wo_coop']:
        team_id = first_data['own_id']
    elif first_data['stage'] in ['c1', 'c1_wo_coop']:
        team_id = first_data['own_id'] % 2
    elif first_data['stage'] in ['c3', 'c3_wo_coop']:
        team_id = first_data['own_id'] % 3
    else:
        team_id = 0
    print('-------')
    print('stage, seed, player_id, team_id, model, win state, turn number, request line, format_acc')
    print(first_data['stage'], first_data['seed'], first_data['own_id'], team_id, format_line[0]['model'], final_data['win_state'], final_data['turn_number'], len(request_line), round(format_acc, 2))

    # compute distance
    org_distance, final_distance, sub_distance = compute_distance(first_data, final_data)
    print('-------distance')
    print('org_distance, final_distance, sub_distance')
    print(round(org_distance, 2), round(final_distance, 2), round(sub_distance, 2))

    # compute reward score, npc, base, player
    reward_line = [line for line in data if 'status' in line and line['status'] == 'reward']
    att_base = [line for line in reward_line if line['score_type'] == 'ATTACK_BASE_SCORE']
    att_npc = [line for line in reward_line if line['score_type'] == 'ATTACK_NPC_SCORE']
    att_enemy = [line for line in reward_line if line['score_type'] == 'ATTACK_ENEMY_SCORE']
    by_npc = [line for line in reward_line if line['score_type'] == 'BE_ATTACK_BY_NPC']
    by_enemy = [line for line in reward_line if line['score_type'] == 'BE_ATTACK_BY_ENEMY']
    print('-------score')
    print('reward line, score, att_base, att_npc, att_enemy, by_npc, by_enemy')
    print(len(reward_line), len(att_base) + len(att_npc) + len(att_enemy), len(att_base), len(att_npc), len(att_enemy), len(by_npc), len(by_enemy))

    # compute move and wall error

    move_acc, shoot_acc, move_percent, move_total, shoot_total, wall_error, border_error, tank_error, metal_error, water_error = compute_move(format_line, is_base_target)
    print('-------other')
    print('move_acc, wall_err, border_err, tank_err, metal_err, water_err')
    print(round(move_acc, 2), round(wall_error, 2), round(border_error, 2), round(tank_error, 2),
          round(metal_error, 2), round(water_error, 2))
    
    return {
        'stage': first_data['stage'],
        'seed': first_data['seed'],
        'player_id': first_data['own_id'],
        'team_id': team_id,
        'model': format_line[0]['model'],
        'win_state': final_data['win_state'],
        'turn_number': final_data['turn_number'],
        'request_line': len(request_line),
        'format_acc': round(format_acc, 2),
        'org_distance': round(org_distance, 2),
        'final_distance': round(final_distance, 2),
        'sub_distance': round(sub_distance, 2),
        'reward_line': len(reward_line),
        'score': len(att_base) + len(att_npc) + len(att_enemy),
        'att_base': len(att_base),
        'att_npc': len(att_npc),
        'att_enemy': len(att_enemy),
        'by_npc': len(by_npc),
        'by_enemy': len(by_enemy),
        'move_acc': round(move_acc, 2),
        'shoot_acc': round(shoot_acc, 2),
        'move_percent': round(move_percent, 2),
        'move_total': move_total,
        'shoot_total': shoot_total,
        'wall_error': round(wall_error, 2),
        'border_error': round(border_error, 2),
        'tank_error': round(tank_error, 2),
        'metal_error': round(metal_error, 2),
        'water_error': round(water_error, 2)
    }

def compute_metric_from_dir(input_dir, start_file=None, end_file=None):
    all_result = []
    first_file = None
    last_file = None
    
    # Collect all file paths
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.startswith('client'):
                all_files.append((file, os.path.join(root, file)))

    # Sort files by file name
    all_files.sort(key=lambda x: x[0])

    for file, input_path in all_files:
        if start_file is not None and file < start_file:
            continue
        if end_file is not None and file > end_file:
            continue
        if first_file is None:
            first_file = file
        last_file = file
        print(input_path)
        file_result = compute_metric(input_path)
        file_result['file'] = file
        all_result.append(file_result)
    # save all result in csv format
    df = pd.DataFrame(all_result)
    df.to_csv(os.path.join(root, f'metric-{first_file[-10:]}-{last_file[-10:]}.csv'), index=False)


if __name__ == "__main__":
    # test_astar()
    # in_path = '../log/client_test-20240729164638'
    # compute_metric(in_path)
    in_path = '../log/'
    compute_metric_from_dir(in_path, start_file='client_test-20240731225647')

