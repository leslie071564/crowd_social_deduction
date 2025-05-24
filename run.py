
import os
import json
import openai
from pydantic import BaseModel
import typing

""" Switch to gpt-x model: 
from dotenv import load_dotenv
load_dotenv()
openai.organization = os.environ.get("OPENAI_ORGANIZATION") 
openai.api_key = os.environ.get("OPENAI_API_KEY")
"""
vllm_client = openai.OpenAI(
    #base_url="http://localhost:4040/v1",  # on lab server.
    base_url="https://tulip.kuee.kyoto-u.ac.jp/LlamaServer_saffron7/v1",  # access from outside.
    api_key="EMPTY"
)

class MafiaPrediction(BaseModel):
    mafias: list[str]
    game_outcome: typing.Literal['Mafia wins', 'Bystander wins']
    reason: str 

def single_eval(game, ratio):
    # load template from file.
    with open('./data/mafia/game_rules.txt', 'r', encoding='utf-8') as file:
        template = file.read()

    # take only partial of the game log.
    game_log= game['log']
    N = int(len(game_log) * ratio)
    game_log = '\n'.join(game_log[:N])
     
    # get the assessment.
    sys_prompt = template
    usr_prompt = game_log + '\n' + '...'
    
    """
    print('###')
    print(sys_prompt + '\n)
    print('###')
    print(usr_prompt + '\n')
    """

    reply = llm_api_call(vllm_client, sys_prompt, usr_prompt, context=None, 
                 model_type=None, temperature=1.5, response_format=MafiaPrediction)
    print(str(reply) + '\n')

    return reply

def llm_api_call(client, sys_prompt, usr_prompt, context=None, 
                 model_type=None, temperature=1.0, **kwargs):
    # messages.
    messages = []
    if sys_prompt is not None:
        messages.append({
            "role": "system",
            "content": [
                {
                "type": "text",
                "text": sys_prompt,
                }
            ]
            })
    if context:
        messages += context

    if usr_prompt:
        messages.append({
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": usr_prompt,
                }
            ]
            })
        
    # set model type. 
    if model_type is None:
        model_type = client.models.list().data[0].id
    
    # collect response.
    if 'response_format' in kwargs:
        completion = client.beta.chat.completions.parse(
            model=model_type, 
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        reply = completion.choices[0].message.parsed

    else:
        completion = client.chat.completions.create(
            model=model_type, 
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        reply = completion.choices[0].message.content

    return reply


if __name__ == '__main__':
    N_TRIAL = 5
    RATIO = 0.3
    # load game logs.
    with open('./mafia.json', "r") as F:
        data = json.load(F)

    prediction_results = []
    for game_data in data[:10]: 
        predictions = []
        for agent_id in range(N_TRIAL):
            print(f'#### (Game {game_data["id"]}) {game_data["win"]} wins, agent {agent_id} ####')
            result = single_eval(game_data, ratio=RATIO)
            predictions.append({'agent_id': agent_id, 'ratio': RATIO, 
                                'mafias': result.mafias, 'win': result.game_outcome, 'reason': result.reason})

        game_data['predictions'] = predictions
        prediction_results.append(game_data)
        #print(result.mafias)

    # save to file.
    output_fn = './predictions.json'
    with open(output_fn, 'w') as F:
        json.dump(prediction_results, F, indent=4)  # indent for pretty formatting, optional
    print(f'saved {len(data)} game logs to file: {output_fn}')