from .basic_prompt.agent import RandomAgent
from .basic_prompt.agent_standard import SingleOneAgent, SingleThreeAgent
from .basic_prompt.agent_standard import DoubleTwoAgent, DoubleOneAgent2, DoubleOneAgent2WOCoop
from .basic_prompt.agent_standard import CoopOneAgent, CoopTwoAgent

agent_type = {
    'single_one': SingleOneAgent,
    'single_three': SingleThreeAgent,
    'double_one2': DoubleOneAgent2,
    'double_one2_wo_coop': DoubleOneAgent2WOCoop,
    'double_two': DoubleTwoAgent,
    'coop_one': CoopOneAgent,
    'coop_two': CoopTwoAgent,
    'random': RandomAgent
}
