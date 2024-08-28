from . import gpt
from . import silicon

model_call = {
    'gpt': gpt.model_call,
    'sili': silicon.model_call
}

model_config = {
    'gpt4om': {
        'model_type': 'gpt-4o-mini',
        'do_sample': False,
        'call_func': model_call['gpt'],
    },
    'gpt3.5': {
        'model_type': 'gpt-3.5-turbo-0125',
        'do_sample': False,
        'call_func': model_call['gpt'],
    },
    'llama3-8b': {
        'model_type': 'meta-llama/Meta-Llama-3-8B-Instruct',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
    'mistral-7b': {
        'model_type': 'mistralai/Mistral-7B-Instruct-v0.2',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
    'gemma2-9b': {
        'model_type': 'google/gemma-2-9b-it',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
    'glm4-9b': {
        'model_type': 'THUDM/glm-4-9b-chat',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
    'qwen2-7b': {
        'model_type': 'Qwen/Qwen2-7B-Instruct',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
    'yi-9b': {
        'model_type': '01-ai/Yi-1.5-9B-Chat-16K',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
    'int-7b': {
        'model_type': 'internlm/internlm2_5-7b-chat',
        'do_sample': False,
        'call_func': model_call['sili'],
    },
}

