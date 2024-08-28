import re
import json
from time import sleep

MAP_SIZE = 512
TANK_SIZE = 32
WALL_SIZE = 8

def check_border_line(position_x, position_y, direction):
    lines = []
    if direction == 'left' and position_x == 0:
        lines.append('left')
    elif direction == 'right' and position_x + TANK_SIZE == MAP_SIZE:
        lines.append('right')
    if direction == 'up' and position_y == 0:
        lines.append('up')
    elif direction == 'down' and position_y + TANK_SIZE == MAP_SIZE:
        lines.append('down')
    return lines

def check_touched_wall(position_x, position_y, direction, walls):
    touched_walls = []
    touched_directions = []
    # first wall
    for wall in walls:
        wall_x, wall_y, wall_type = wall[0], wall[1], wall[2]
        if wall_type == 'metal' or wall_type == 'water':
            wall_size = 32
        else:
            wall_size = 8
        if direction == 'left' and wall_x+wall_size == position_x and position_y-(wall_size-1) <= wall_y <= position_y + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('left')
            continue
        if direction == 'right' and wall_x-TANK_SIZE == position_x and position_y-(wall_size-1) <= wall_y <= position_y + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('right')
            continue
        if direction == 'up' and wall_y+wall_size == position_y and position_x-(wall_size-1) <= wall_x <= position_x + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('up')
            continue
        if direction == 'down' and wall_y-TANK_SIZE == position_y and position_x-(wall_size-1) <= wall_x <= position_x + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('down')
            continue
    # gird, second wall
    gird_walls = []
    gird_directions = []
    for wall in walls:
        wall_x, wall_y, wall_type = wall[0], wall[1], wall[2]
        if wall_type == 'metal' or wall_type == 'water':
            continue
        if direction == 'left' and wall_x+WALL_SIZE*2 == position_x and position_y <= wall_y <= position_y + TANK_SIZE-WALL_SIZE:
            gird_walls.append(wall)
            gird_directions.append('left')
            continue
        if direction == 'right' and wall_x-WALL_SIZE == position_x+TANK_SIZE and position_y <= wall_y <= position_y + TANK_SIZE-WALL_SIZE:
            gird_walls.append(wall)
            gird_directions.append('right')
            continue
        if direction == 'up' and wall_y+WALL_SIZE*2 == position_y and position_x <= wall_x <= position_x + TANK_SIZE-WALL_SIZE:
            gird_walls.append(wall)
            gird_directions.append('up')
            continue
        if direction == 'down' and wall_y-WALL_SIZE == position_y+TANK_SIZE and position_x <= wall_x <= position_x + TANK_SIZE-WALL_SIZE:
            gird_walls.append(wall)
            gird_directions.append('down')
            continue
    final_walls = touched_walls if touched_walls else gird_walls
    final_directions = touched_directions if touched_directions else gird_directions
    return final_directions, final_walls

def check_touched_tank(position_x, position_y, direction, walls):
    touched_walls = []
    touched_directions = []
    for wall in walls:
        wall_x, wall_y = wall[1], wall[2]
        if direction == 'left' and wall_x+TANK_SIZE == position_x and position_y-(TANK_SIZE-1) <= wall_y <= position_y + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('left')
            continue
        if direction == 'right' and wall_x == position_x+TANK_SIZE and position_y-(TANK_SIZE-1) <= wall_y <= position_y + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('right')
            continue
        if direction == 'up' and wall_y+TANK_SIZE == position_y and position_x-(TANK_SIZE-1) <= wall_x <= position_x + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('up')
            continue
        if direction == 'down' and wall_y == position_y+TANK_SIZE and position_x-(TANK_SIZE-1) <= wall_x <= position_x + TANK_SIZE-1:
            touched_walls.append(wall)
            touched_directions.append('down')
            continue
    return touched_directions, touched_walls

def remove_option_border(org_prompt, direction):
    new_prompt = re.sub(rf'- #Move_{direction}#.+?\n', '', org_prompt)
    return new_prompt

def compute_distance(tank, walls):
    pos_x, pos_y = tank[1], tank[2]
    wall_dis = []
    for wall in walls:
        wall_distance = abs(pos_x - wall[0]) + abs(pos_y-wall[1])
        wall_dis.append(wall_distance)
    return wall_dis

def compute_tank_distance(own_tank, tanks):
    position_x, position_y = own_tank[1], own_tank[2]
    dis = []
    for wall in tanks:
        wall_distance = abs(position_x - wall[1]) + abs(position_y - wall[2])
        dis.append(wall_distance)
    return dis

def split_team_tanks(player_id, game_status):
    own_tank = []
    other_tanks = []
    for tank in game_status['team_tanks']:
        if tank[0] == player_id:
            own_tank.append(tank)
        else:
            other_tanks.append(tank)
    return own_tank[-1], other_tanks

def sort_walls(own_tank, map_walls):
    wall_dis = compute_distance(own_tank, map_walls)
    return wall_dis

def sort_tanks(own_tank, enemy_tanks):
    tank_distance = compute_tank_distance(own_tank, enemy_tanks)
    sorted_tanks = sorted(enumerate(tank_distance), key=lambda x: x[-1])
    sorted_tanks = [enemy_tanks[idx][0] for idx, _ in sorted_tanks]
    return sorted_tanks

def get_nearst_walls(own_tank, map_walls):
    metals = [w for w in map_walls if w[2] == 'metal']
    dis_metals = compute_distance(own_tank, metals)
    sorted_metals = sorted(enumerate(dis_metals), key=lambda x: x[-1])
    sorted_metals = [metals[idx] for idx, _ in sorted_metals]
    waters = [w for w in map_walls if w[2] == 'water']
    dis_waters = compute_distance(own_tank, waters)
    sorted_waters = sorted(enumerate(dis_waters), key=lambda x: x[-1])
    sorted_waters = [waters[idx] for idx, _ in sorted_waters]
    return sorted_metals + sorted_waters

def check_around_info(own_tank, game_status):
    direct_map = {'up': '上方', 'down': '下方', 'left': '左方', 'right': '右方'}
    all_info = []
    own_direct = own_tank[3]
    only_front = None
    for direct in direct_map.keys():
        touched_border = check_border_line(own_tank[1], own_tank[2], direct)
        touched_wall_direction, touched_walls = check_touched_wall(own_tank[1], own_tank[2], direct, game_status['map_walls'])
        touched_tank_direction, touched_tanks = check_touched_tank(own_tank[1], own_tank[2], direct, game_status['enemy_tanks'])
        touched_own_direction, touched_owns = check_touched_tank(own_tank[1], own_tank[2], direct, game_status['own_base'])
        touched_base_direction, touched_bases = check_touched_tank(own_tank[1], own_tank[2], direct, game_status['enemy_base'])
        print(touched_border, touched_wall_direction, touched_tank_direction)
        has_something = True
        if touched_border:
            front_info = '为地图边界'
            if direct == own_direct:
                front_info += '，无法继续向前移动，需要调整坦克方向'
        elif touched_wall_direction:
            if touched_walls[0][-1] == 'metal':
                front_info = '有金属墙'
                if direct == own_direct:
                    front_info += '阻挡，无法继续向前移动，只能调整坦克方向'
            elif touched_walls[0][-1] == 'water':
                front_info = '有水'
                if direct == own_direct:
                    front_info += '阻挡，无法继续向前移动，只能调整坦克方向'
            else:
                front_info = '有wall'
                if direct == own_direct:
                    front_info += '阻挡（编号200），无法继续向前移动，需要射击或调整坦克方向'
        elif touched_tank_direction:
            front_info = '有敌方坦克'
            if direct == own_direct:
                front_info += '阻挡，应立即射击消灭'
        elif touched_own_direction:
            front_info = '有我方基地'
            if direct == own_direct:
                front_info += '阻挡，无法继续向前移动，只能调整坦克方向'
        elif touched_base_direction:
            front_info = '有敌方基地'
            if direct == own_direct:
                front_info += '阻挡，应立即射击消灭'
        else:
            has_something = False
            front_info = '无障碍物'
        if direct == own_direct:
            final_str = f'{direct_map[direct]}（前方）：{front_info}'
            only_front = front_info
        else:
            final_str = f'{direct_map[direct]}：{front_info}'
        all_info.append(final_str)

    return '\n'.join(all_info), only_front

def check_front_info(own_tank, game_status):
    touched_border = check_border_line(own_tank[1], own_tank[2], own_tank[3])
    touched_wall_direction, touched_walls = check_touched_wall(own_tank[1], own_tank[2], own_tank[3], game_status['map_walls'])
    touched_tank_direction, touched_tanks = check_touched_tank(own_tank[1], own_tank[2], own_tank[3], game_status['enemy_tanks'])
    print(touched_border, touched_wall_direction, touched_tank_direction)
    front_info = '前方无障碍物'
    if touched_border:
        front_info = f'前方为地图边界，无法继续向前移动，需要调整坦克方向'
    elif touched_wall_direction:
        if touched_walls[0][-1] == 'metal':
            front_info = f'前方有金属墙阻挡，无法继续向前移动，只能调整坦克方向'
        elif touched_walls[0][-1] == 'water':
            front_info = f'前方有水阻挡，无法继续向前移动，只能调整坦克方向'
        else:
            front_info = f'前方有wall阻挡，无法继续向前移动，需要射击或调整坦克方向'
    elif touched_tank_direction:
        front_info = f'前方有敌方坦克阻挡，应立即射击消灭'
    return front_info, touched_border, touched_wall_direction, touched_tank_direction

def check_result(before_operation, own_tank, enemy_tanks, front_info, last_own_tank, last_enemy_tanks, last_front_info):
    target = [ene for ene in enemy_tanks if ene[0] == before_operation[1]]
    org_target = [ene for ene in last_enemy_tanks if ene[0] == before_operation[1]]
    if before_operation[0] == 'Shoot':
        if target and org_target and target[0][-1] == org_target[0][-1]:
            result_info = '目标血量未减少，目标可能目前不在攻击范围'
            if last_front_info != '无障碍物' and front_info == '无障碍物':
                result_info += '；前方障碍被消除'
        else:
            result_info = '射击目标成功'
    else:
        org_location = last_own_tank[1:3]
        new_location = own_tank[1:3]
        if org_location == new_location:
            result_info = '移动操作执行失败'
        else:
            result_info = '移动操作执行成功'
        if target and org_target:
            org_dis = compute_tank_distance(last_own_tank, org_target)[0]
            new_dis = compute_tank_distance(own_tank, target)[0]
            if new_dis < org_dis:
                result_info += '；与目标距离缩短'
            elif new_dis > org_dis:
                result_info += '；与目标距离增加'
    
    return result_info

def make_history(history):
    last_his = history[-10:]
    history_strs = ["会合：{}\n自己位置：({}, {})\n周围地图信息：{}\n操作：{}".format(
        item[0], item[1][1], item[1][2], item[2].replace('\n', '；'), item[3]
    ) for item in last_his]
    return '\n'.join(history_strs)

def make_history_with_intent(history):
    last_his = history[-5:]
    history_strs = ["会合：{}\n自己位置：({}, {})\n周围地图信息：{}\n思考过程：{}\n操作：{}".format(
        item[0], item[1][1], item[1][2], item[2].replace('\n', '；'), item[4], item[3]
    ) for item in last_his]
    return '\n'.join(history_strs)

def make_tank_base_str(tanks, is_base=False, with_type=False):
    if tanks:
        if is_base:
            tank_info = [f"{t[0]}, ({t[1]}, {t[2]})" for t in tanks]
        elif with_type:
            tank_info = []
            for t in tanks:
                if t[0] < 10:
                    tank_type = '高级'
                else:
                    tank_type = '普通'
                tank_info.append(f"{t[0]}, ({t[1]}, {t[2]}), {t[3]}, {t[4]}, {tank_type}")
        else:
            tank_info = [f"{t[0]}, ({t[1]}, {t[2]}, {t[3]}, {t[4]})" for t in tanks]
        tank_info = '\n'.join(tank_info)
    else:
        tank_info = '[]'
    return tank_info

def make_coop_str(coop_data):
    if coop_data:
        coop_info = [f"{s}发给{t}：{c}\n{t}回复{s}：同意" for (s, t), c in coop_data]
        coop_info = '\n'.join(coop_info)
    else:
        coop_info = '[]'
    return coop_info

def make_wall_map(own_tank, base, map_walls):
    walls = [w for w in map_walls if w[2] == 'metal' or w[2] == 'water']
    game_map = [['0']*16 for _ in range(16)]
    for wall in walls:
        wx, wy, _ = wall
        game_map[wy // 32][wx // 32] = '1'
    wall_str = [f"第{ind}行0-15列：{', '.join(line)}" for ind, line in enumerate(game_map)]
    ox, oy = own_tank[2] // 32, own_tank[1] // 32
    own_str = f"\n你的位置({own_tank[1]},{own_tank[2]})，相当于在{ox}行{oy}列"
    bx, by = base[2] // 32, base[1] // 32
    base_str = f"\n基地的位置({base[1]},{base[2]})，相当于在{bx}行{by}列"
    return '\n'.join(wall_str) + own_str + base_str

