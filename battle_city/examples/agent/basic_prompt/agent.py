import json
import random
from tenacity import retry, stop_after_attempt, wait_fixed

from .agent_util_extract import make_action

class ModelCallError(Exception):
    pass

class BaseAgent:
    def __init__(self, model_config, log_path='agent_data.log'):
        self.history = []
        self.history_action = {}
        self.target = None
        self.coop_target = None

        self.model_config = model_config
        self.log_path = log_path

    def log_data(self, data):
        with open(self.log_path, 'a', encoding="utf-8") as fout:
            fout.write(json.dumps(data, ensure_ascii=False))
            fout.write('\n')

    def clear_history(self):
        self.history = []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(60), retry_error_cls=ModelCallError)
    async def model_call(self, prompt, history=None, system=None):
        try:
            return await self.model_config['call_func'](
                prompt, 
                history, 
                system, 
                self.model_config['do_sample'], 
                self.model_config['model_type']
            )
        except Exception as e:
            raise ModelCallError(f"Error calling model: {str(e)}")
        
class RandomAgent(BaseAgent):

    async def act(self, game_status, player_id, lang='en'):
        action = random.choice(['Shoot', 'Move_up', 'Move_down', 'Move_left', 'Move_right'])
        target_id = -1
        candidate_ids = [ba[0] for ba in game_status['enemy_base'] + game_status['enemy_tanks']]
        if candidate_ids:
            target_id = random.choice(candidate_ids)
        action_data = make_action(action, target_id)

        coop_data = {'action': 'No_coop'}

        llm_data = {'model': 'random', 'input': '', 'output': ''}
        llm_data['game_status'] = game_status
        return action_data, None, coop_data, llm_data
    
    async def reply(self, message_data, player_id, lang='en', rule=True):
        return None, None, None
