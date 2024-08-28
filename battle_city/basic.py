from enum import Enum


class Direction(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    UP = 'up'
    DOWN = 'down'


StageInfo = {
    's1': {'time_total': 60, 'total_npcs': 0, 'game_map': 'single1', 'max_players': 1, 'mode': 'normal'},
    's3': {'time_total': 60, 'total_npcs': 10, 'game_map': 'single30', 'max_players': 1, 'mode': 'normal'},
    'd1': {'time_total': 80, 'total_npcs': 10, 'game_map': 'double10', 'max_players': 2, 'mode': 'team'},
    'd2': {'time_total': 80, 'total_npcs': 10, 'game_map': 'multi30', 'max_players': 2, 'mode': 'fight'},
    'c1': {'time_total': 80, 'total_npcs': 10, 'game_map': 'multi30', 'max_players': 4, 'mode': 'team_fight', 'team_count': 2},
    'c2': {'time_total': 80, 'total_npcs': 10, 'game_map': 'multi20', 'max_players': 4, 'mode': 'fight'},
    'c3': {'time_total': 80, 'total_npcs': 10, 'game_map': 'coop30', 'max_players': 6, 'mode': 'team_fight', 'team_count': 3},
    'c1_wo_coop': {'time_total': 80, 'total_npcs': 10, 'game_map': 'multi30', 'max_players': 4, 'mode': 'team_fight', 'team_count': 2},
    'c2_wo_coop': {'time_total': 80, 'total_npcs': 10, 'game_map': 'multi20', 'max_players': 4, 'mode': 'fight'},
    'c3_wo_coop': {'time_total': 80, 'total_npcs': 10, 'game_map': 'coop30', 'max_players': 6, 'mode': 'team_fight', 'team_count': 3},
}
