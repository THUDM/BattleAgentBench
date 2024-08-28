from battle_city.basic import Direction
from battle_city.monsters.tank import Tank

from random import random, randint, choice


class NPC(Tank):
    player_id = 0
    direction = Direction.DOWN
    speed = 1
    health = 1

    def do_something(self, game) -> bool:
        if random() > 0.4:
            return False

        action = randint(1, 2)
        if action == 1:
            directions = [
                Direction.UP, Direction.DOWN,
                Direction.LEFT, Direction.RIGHT,
            ]
            direction = choice(directions)
            self.set_direction(direction)
        else:
            self.set_shot()

        return True


def compute_distance(source, targets):
    dis = []
    for target in targets:
        wall_distance = abs(source.position.x - target.position.x) \
                        + abs(source.position.y - target.position.y)
        dis.append(wall_distance)
    return dis

def compute_action_plan(s_pos, source, target):
    plan = []
    tar_pos = target.old_position if target.position.x % 2 !=0 or target.position.y % 2 !=0 else target.position
    diff_x = s_pos.x - tar_pos.x
    diff_y = s_pos.y - tar_pos.y
    if abs(diff_x) < 32:
        if diff_y <= 0:
            if source.direction != Direction.DOWN:
                plan.append(Direction.DOWN)
            plan.append('shoot')
        elif diff_y > 0:
            if source.direction != Direction.UP:
                plan.append(Direction.UP)
            plan.append('shoot')
    elif abs(diff_y) < 32:
        if diff_x <= 0:
            if source.direction != Direction.RIGHT:
                plan.append(Direction.RIGHT)
            plan.append('shoot')
        elif diff_x > 0:
            if source.direction != Direction.LEFT:
                plan.append(Direction.LEFT)
            plan.append('shoot')
    elif diff_x <= -32:
        if diff_y <= -32:
            if abs(diff_x) > abs(diff_y):
                # plan.append(f'enemy is in down right, plan: move right until {ene_tank[1]}; turn down and shoot')
                plan.append(Direction.RIGHT)
            else:
                # plan.append(f'enemy is in down right, plan: move down until {ene_tank[2]}; turn right and shoot')
                plan.append(Direction.DOWN)
        else:
            if abs(diff_x) > abs(diff_y):
                # plan.append(f'enemy is in up right, plan: move right until {ene_tank[1]}; turn up and shoot')
                plan.append(Direction.RIGHT)
            else:
                # plan.append(f'enemy is in up right, plan: move up until {ene_tank[2]}; turn right and shoot')
                plan.append(Direction.UP)
    elif diff_x >= 32:
        if diff_y <= -32:
            if abs(diff_x) > abs(diff_y):
                # plan.append(f'enemy is in down left, plan: move left until {ene_tank[1]}; turn down and shoot')
                plan.append(Direction.LEFT)
            else:
                # plan.append(f'enemy is in down left, plan: move down until {ene_tank[2]}; turn left and shoot')
                plan.append(Direction.DOWN)
        else:
            if abs(diff_x) > abs(diff_y):
                # plan.append(f'enemy is in up left, plan: move left until {ene_tank[1]}; turn up and shoot')
                plan.append(Direction.LEFT)
            else:
                # plan.append(f'enemy is in up left, plan: move up until {ene_tank[2]}; turn left and shoot')
                plan.append(Direction.UP)
    # print(source.player_id, 'plan', plan)
    return plan


def check_touched_wall(s_pos, source, targets):
    touched_walls = []
    touched_directions = []
    for wall in targets:
        if source.direction == Direction.LEFT and wall.position.x+wall.SIZE == s_pos.x and s_pos.y-(wall.SIZE-1) <= wall.position.y <= s_pos.y + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.LEFT)
            continue
        if source.direction == Direction.RIGHT and wall.position.x == s_pos.x+source.SIZE and s_pos.y-(wall.SIZE-1) <= wall.position.y <= s_pos.y + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.RIGHT)
            continue
        if source.direction == Direction.UP and wall.position.y+wall.SIZE == s_pos.y and s_pos.x-(wall.SIZE-1) <= wall.position.x <= s_pos.x + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.UP)
            continue
        if source.direction == Direction.DOWN and wall.position.y == s_pos.y+source.SIZE and s_pos.x-(wall.SIZE-1) <= wall.position.x <= s_pos.x + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.DOWN)
            continue
    # gird
    gird_walls = []
    gird_directions = []
    for wall in targets:
        if source.direction == Direction.LEFT and wall.position.x+16 == s_pos.x and s_pos.y <= wall.position.y <= s_pos.y + 24:
            gird_walls.append(wall)
            gird_directions.append(Direction.LEFT)
            continue
        if source.direction == Direction.RIGHT and wall.position.x-8 == s_pos.x+source.SIZE and s_pos.y <= wall.position.y <= s_pos.y + 24:
            gird_walls.append(wall)
            gird_directions.append(Direction.RIGHT)
            continue
        if source.direction == Direction.UP and wall.position.y+16 == s_pos.y and s_pos.x <= wall.position.x <= s_pos.x + 24:
            gird_walls.append(wall)
            gird_directions.append(Direction.UP)
            continue
        if source.direction == Direction.DOWN and wall.position.y-8 == s_pos.y+source.SIZE and s_pos.x <= wall.position.x <= s_pos.x + 24:
            gird_walls.append(wall)
            gird_directions.append(Direction.DOWN)
            continue
    final_walls = touched_walls if touched_walls else gird_walls
    final_directions = touched_directions if touched_directions else gird_directions
    return final_directions, final_walls

def check_touched_tank(s_pos, source, targets):
    touched_walls = []
    touched_directions = []
    for wall in targets:
        w_pos = wall.old_position if wall.position.x % 2 !=0 or wall.position.y % 2 !=0 else wall.position
        if source.direction == Direction.LEFT and w_pos.x+wall.SIZE == s_pos.x and s_pos.y-(wall.SIZE-1) <= w_pos.y <= s_pos.y + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.LEFT)
            continue
        if source.direction == Direction.RIGHT and w_pos.x == s_pos.x+source.SIZE and s_pos.y-(wall.SIZE-1) <= w_pos.y <= s_pos.y + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.RIGHT)
            continue
        if source.direction == Direction.UP and w_pos.y+wall.SIZE == s_pos.y and s_pos.x-(wall.SIZE-1) <= w_pos.x <= s_pos.x + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.UP)
            continue
        if source.direction == Direction.DOWN and w_pos.y == s_pos.y+source.SIZE and s_pos.x-(wall.SIZE-1) <= w_pos.x <= s_pos.x + (source.SIZE-1):
            touched_walls.append(wall)
            touched_directions.append(Direction.DOWN)
            continue
    return touched_directions, touched_walls

class ADNPC(NPC):
    target = -1

    def do_something(self, game) -> bool:
        if len(game.alive_players) < 1:
            print(self.player_id, 'no players')
            return False
        players = game.alive_players
        # print('--', self.player_id, self.position.x, self.position.y, self.old_position.x, self.old_position.y)
        s_pos = self.old_position if self.position.x % 2 !=0 or self.position.y % 2 !=0 else self.position
        touched_tank_direction, touched_tanks = check_touched_tank(s_pos, self, players)
        if touched_tank_direction:
            # print(self.player_id, '-----------touch tank')
            # for wall in touched_tanks:
            #     print('**touch tank**', wall.position.x, wall.position.y)
            self.set_shot()
            print('npc shoot')
            return True

        # compute distance
        tank_distance = compute_distance(self, players)
        sorted_tanks = sorted(enumerate(tank_distance), key=lambda x: x[-1])
        target = players[sorted_tanks[0][0]]
        # print('**tank **', target.player_id, target.position.x, target.position.y, target.old_position.x, target.old_position.y)
        # wall_dis = compute_distance(self, game.walls)
        # wall_dis = sorted(list(zip(game.walls, wall_dis)), key=lambda x: x[-1])[:50]
        # for w, _ in wall_dis:
        #     print('**wall**', w.position.x, w.position.y, end=', ')
        # compute road
        # print(sorted_tanks)
        action = compute_action_plan(s_pos, self, players[sorted_tanks[0][0]])[0]
        if action == 'shoot':
            self.set_shot()
            print('npc shoot')
        else:
            touched_wall_direction, touched_walls = check_touched_wall(s_pos, self, game.walls)
            # for wall in touched_walls:
            #     print('**touch wall**', wall.position.x, wall.position.y)
            if action == self.direction and touched_wall_direction:
                # print(self.player_id, '---------touch wall')
                self.set_shot()
                print('npc shoot')
            else:
                self.set_direction(action)
                print('npc', action)

        return True
