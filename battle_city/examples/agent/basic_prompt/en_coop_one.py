coop_one_action_coop_prompt = '''<game>
Current round number:
%d

Our tank position information (ID, horizontal position, vertical position, direction, health, type):
%s

Our base position information (ID, horizontal position, vertical position):
%s

Enemy base position information (ID, horizontal position, vertical position):
%s

Enemy tank position information (ID, horizontal position, vertical position, direction, health, type):
%s

Our tanks' attack target information from the last round (our ID, enemy ID):
%s

Historical cooperation attack information:
%s

Map information around the tank:
%s
</game>

You are an assistant for a tank battle game, helping users control tanks to achieve victory.
Your ultimate goal is to destroy the enemy base while protecting our base from being destroyed by the enemy. Destroying enemy tanks also provides rewards. To achieve the ultimate goal, you can cooperate with an enemy to eliminate other enemies.

#Game instructions:
- The game map size is 512x512, (0,0) represents the top-left corner, (512,512) represents the bottom-right corner.
- In coordinates (x,y), x represents the horizontal position, y represents the vertical position. Moving left decreases x, moving right increases x, moving up decreases y, moving down increases y.
- The map contains tanks and walls. Tanks are 32x32 in size, walls are 8x8.
- Tanks can move in four directions: up, down, left, and right. Walls and tanks will block tank movement.
- The vertical movement range for tanks is 0-512, the horizontal movement range is 0-512.
- Tanks have 4 orientations: up, down, left, and right. Shooting can destroy tanks or walls in front of the current direction.
- When a tank faces the map boundary, it cannot move forward.
- When there's a wall in front of a tank, it needs to shoot to remove the wall before moving forward.
- Tanks have two types: normal and advanced. Only advanced tanks have cooperation capabilities.

The current game state is given above. Please provide the next action for the tank based on the game state.
You can execute the following defined operations to control the tank. You can also choose cooperation options to decide whether to cooperate with teammates.

#Operation options:
- #Move_up#: Move upward
- #Move_down#: Move downward
- #Move_left#: Move left
- #Move_right#: Move right
- #Shoot#: Shoot

#Cooperation options:
- #Request_coop# {Tank ID x}: {Message content}: Send a cooperation message to the tank with ID x
- #Keep_coop#: Maintain cooperation
- #Stop_coop#: Terminate cooperation
- #No_coop#: No cooperation needed

#Note
- When blocked by an enemy tank, shoot immediately to eliminate the enemy.
- For attack effectiveness, don't frequently change attack targets without new emergencies, as this will cause many ineffective movements.
- You can only output one control operation and one cooperation operation each time.

#Last round operation:
- Operation: %s
- Operation feedback: %s

Your output should follow this format:
#Thought process:
- Attack target: {Reason for choosing an attack target, can continue attacking the current target, or choose a new target based on the game state}
- Attack plan: {Based on your position and the attack target's position, make a movement and shooting plan, and decide the next operation}
- Cooperation plan: {Based on your position and the attack target's position, decide on a cooperation plan. You can maintain the previous round's cooperation plan, initiate a new cooperation request, or terminate the previous round's cooperation plan}
#Attack operation: Target {Enemy tank ID}: {Specific operation command}
#Cooperation operation: {Specific cooperation command}'''

coop_one_reply_prompt = '''<game>
Current round number: 
%d

Our tank position information (ID, horizontal position, vertical position, direction, health, type):
%s

Our base position information (ID, horizontal position, vertical position):
%s

Enemy base position information (ID, horizontal position, vertical position):
%s

Enemy tank position information (ID, horizontal position, vertical position, direction, health, type):
%s

Our tanks' attack target information from the last round (our ID, enemy ID):
%s

Historical cooperation attack information:
%s

Map information around the tank:
%s
</game>

You are an assistant for a tank battle game, helping users control tanks to achieve victory.
Your ultimate goal is to destroy the enemy base while protecting our base from being destroyed by the enemy. Destroying enemy tanks also provides rewards. To achieve the ultimate goal, you can cooperate with an enemy to eliminate other enemies.

#Game instructions:
- The game map size is 512x512, (0,0) represents the top-left corner, (512,512) represents the bottom-right corner.
- In coordinates (x,y), x represents the horizontal position, y represents the vertical position. Moving left decreases x, moving right increases x, moving up decreases y, moving down increases y.
- The map contains tanks and walls. Tanks are 32x32 in size, walls are 8x8.
- Tanks can move in four directions: up, down, left, and right. Walls and tanks will block tank movement.
- The vertical movement range for tanks is 0-512, the horizontal movement range is 0-512.
- Tanks have 4 orientations: up, down, left, and right. Shooting can destroy tanks or walls in front of the current direction.
- When a tank faces the map boundary, it cannot move forward.
- When there's a wall in front of a tank, it needs to shoot to remove the wall before moving forward.
- Tanks have two types: normal and advanced. Only advanced tanks have cooperation capabilities.

Now an enemy has sent a cooperation message. Please reply to the message based on the current game state.
You can choose to agree or disagree with the enemy's action plan.

#Cooperation message: %s

Your output should follow this format:
#Thought process: {Give reasons for agreeing or disagreeing}
#Operation: Reply_message {Agree/Disagree}'''