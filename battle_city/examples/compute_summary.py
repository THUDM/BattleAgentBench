import pandas as pd

def compute_single(data, stage='s1'):
    stage_data = data[data['stage'] == stage]
    stage_data = stage_data.groupby(['stage', 'model']).mean().round(2).reset_index()

    return stage_data

def agg_function(x):
    columns_to_sum = {'sub_distance', 'reward_line', 'score', 'att_base', 'att_npc', 'att_enemy', 'by_npc', 'by_enemy'}
    if x.name in columns_to_sum:
        result = x.sum()
    elif x.name == 'win_state':
        result = x.max()
    else:
        result = x.mean()
    return result

def compute_team(data, stage='d1'):
    stage_data = data[data['stage'] == stage]
    if stage_data.empty:
        return stage_data

    count = 0
    stage_data = stage_data.groupby(['stage', 'seed', 'model', 'team_id']).agg(agg_function).reset_index()
    # Perform operations for each unique combination of (stage, seed, model)
    for (stage, seed, model), group in stage_data.groupby(['stage', 'seed', 'model']):
        # Find the first team in this group (assuming the team with the smallest team_id is the first team)
        first_team = group.loc[group['team_id'] == 0]
    
        if not first_team.empty:
            # Check the win_state of the first team
            if first_team['win_state'].iloc[0] == 0:
                count += 1
                print('check', count, stage, seed, model)
                # Filter all teams with win_state of 0 in this group
                teams_with_zero_win = group.loc[group['win_state'] == 0]
                # print(teams_with_zero_win)
                if len(teams_with_zero_win) < 2:
                    continue
    
                # Check if the score of the first team is higher than all other teams with win_state of 0 in this group
                print(first_team['score'].iloc[0], teams_with_zero_win[teams_with_zero_win['team_id'] != 0]['score'].max())
                if first_team['score'].iloc[0] > teams_with_zero_win[teams_with_zero_win['team_id'] != 0]['score'].max():
                    # If so, set the win_state of the first team to 1
                    stage_data.loc[(stage_data['stage'] == stage) &
                                (stage_data['seed'] == seed) &
                                (stage_data['model'] == model) &
                                (stage_data['team_id'] == 0), 'win_state'] = 1
            # If the win_state of the first team is -1, set it to 0
            elif first_team['win_state'].iloc[0] == -1:
                print('set -1 to 0')
                stage_data.loc[(stage_data['stage'] == stage) &
                                (stage_data['seed'] == seed) &
                                (stage_data['model'] == model) &
                                (stage_data['team_id'] == 0), 'win_state'] = 0

    # Only keep data where team_id is 0
    stage_data = stage_data[stage_data['team_id']==0]
    stage_data = stage_data.groupby(['stage', 'model']).mean().round(2).reset_index()

    return stage_data

def add_experiment_number(latest_data):
    # Create a new column to store group name
    # latest_data['group'] = 0
    latest_data['group_name'] = ''

    # Initialize group number and group name
    # group_number = 1
    current_group_name = ''

    # Iterate through the dataframe
    for i in range(len(latest_data)):
        if i == 0:
            # The first row always belongs to the first group
            # latest_data.loc[i, 'group'] = group_number
            current_group_name = latest_data.loc[i, 'model']
            latest_data.loc[i, 'group_name'] = current_group_name
        else:
            # Check if 'state' and 'seed' of the current row are different from the previous row
            if (latest_data.loc[i, 'stage'] != latest_data.loc[i-1, 'stage']) or \
            (latest_data.loc[i, 'seed'] != latest_data.loc[i-1, 'seed']):
                # If different, increase the group number and update the group name
                # group_number += 1
                current_group_name = latest_data.loc[i, 'model']
            
            # Assign group number and group name to the current row
            # latest_data.loc[i, 'group'] = group_number
            latest_data.loc[i, 'group_name'] = current_group_name

# Read Excel file
latest_file_path = '../log/metric-0823172950-0824034908-six-small.xlsx'
latest_data = pd.read_excel(latest_file_path).drop(columns=['file'])

add_experiment_number(latest_data)
latest_data = latest_data.drop('model', axis=1)
latest_data = latest_data.rename(columns={'group_name': 'model'})

# Get model list of latest data where stage=='s1'
model_order = latest_data[latest_data['stage'] == latest_data.loc[0, 'stage']]['model'].unique()

# Define the sorting order for stage and model
stage_order = ['s1', 's3', 'd1', 'd2', 'c1', 'c2', 'c3']

# Process data according to different stages
s1_data = compute_single(latest_data, stage='s1')
s3_data = compute_single(latest_data, stage='s3')
d2_data = compute_team(latest_data, stage='d2')
c2_data = compute_team(latest_data, stage='c2')
d1_data = compute_team(latest_data, stage='d1')
c1_data = compute_team(latest_data, stage='c1')
c3_data = compute_team(latest_data, stage='c3')
c1_woc_data = compute_team(latest_data, stage='c1_wo_coop')
c2_woc_data = compute_team(latest_data, stage='c2_wo_coop')
c3_woc_data = compute_team(latest_data, stage='c3_wo_coop')
grouped_latest_data = pd.concat([s1_data, s3_data, d1_data, d2_data, c1_data, c2_data, c3_data, c1_woc_data, c2_woc_data, c3_woc_data])

# Create sorting mappings for stage and model
stage_sort_key = {v: i for i, v in enumerate(stage_order)}
model_sort_key = {v: i for i, v in enumerate(model_order)}

# Apply sorting mappings
grouped_latest_data['stage_order'] = grouped_latest_data['stage'].map(stage_sort_key)
grouped_latest_data['model_order'] = grouped_latest_data['model'].map(model_sort_key)

# Sort first by stage, then by model
sorted_latest_data = grouped_latest_data.sort_values(by=['stage_order', 'model_order'])

# Remove auxiliary columns used for sorting
sorted_latest_data = sorted_latest_data.drop(columns=['stage_order', 'model_order'])

# Save the correctly sorted data as a new Excel file
sorted_output_file_path = latest_file_path + '-sorted.xlsx'
sorted_latest_data.to_excel(sorted_output_file_path, index=False)
