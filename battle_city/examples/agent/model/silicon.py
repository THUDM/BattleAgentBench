import openai
import os, json

async def model_call(prompt, history=None, system=None, do_sample=False, model_type="THUDM/glm-4-9b-chat"):
    message = []
    if system:
        message.append({
            "role": "system",
            "content": system
        })
    
    if history:
        for chat in history:
            message.append({
                "role": "user",
                "content": chat[0]
            })
            message.append({
                "role": "assistant",
                "content": chat[1]
            })
    
    message.append({
        "role": "user",
        "content": prompt
    })

    openai.api_base="https://api.siliconflow.cn/v1"
    key = ''

    print(prompt)
    resp = openai.ChatCompletion.create(
        model=model_type,
        messages=message,
        # temperature=0,
        do_sample=do_sample,
        api_key=key,
        timeout=600
    )

    output = resp["choices"][0]["message"]["content"]
    print(output)
    llm_data = {'model': model_type, 'input': prompt, 'output': output}

    return output, llm_data
