# this script is for building a function to call for chatgpt 4 model
# with designated API

import yaml
from openai import OpenAI

with open('open_ai_api.yaml', 'r') as f:
    config = yaml.safe_load(f)
api_key = config['key']


def chat_completion(messages, model='gpt-4-1106-preview'):
    client = OpenAI(api_key=api_key)

    # call the OpenAI API
    answer = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=150,
        temperature=0.7
    )

    response = answer.choices[0].message.content
    return response


if __name__ == '__main__':
    sample_messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'What is machine learning?'}
    ]
    print(chat_completion(sample_messages))
