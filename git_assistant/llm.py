import os
import time
import random

from datetime import datetime

import openai

#---------------------------------------------------------------------------------------------#

def set_openai_environment(application):
    openai.api_key = os.getenv(f"api_key_{application}")
    openai.api_base = os.getenv(f"api_base_{application}")
    openai.api_type = os.getenv(f"api_type_{application}")
    openai.api_version = os.getenv(f"api_version_{application}")

# define a retry decorator
def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (openai.error.RateLimitError,),
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())

                # Sleep for the delay
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                raise e

    return wrapper

class ChatGPT:

    def __init__(self, model='gpt-3.5-turbo', azure_engine=False):
        self.total_cost = 0
        self.model = model
        self.azure_engine = azure_engine

    def define_context(self, context="You are an assistant."):

        self.messages = [{"role": "system", "content" : context}]

    def add_few_shots(self, shots):

        for shot in shots:
            self.messages.extend([{"role": k, "content" : v} for k, v in shot.items()])

    @retry_with_exponential_backoff
    def ask(self, message, max_tokens=512, temperature=1, top_p=1, request_timeout=100):

        self.messages.append({"role": "user", "content" : message})

        args = {
            'messages': self.messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'request_timeout': request_timeout
        }

        if self.azure_engine is True:
            args['engine'] = self.model            
        else:
            args['model'] = self.model  
        
        completion = openai.ChatCompletion.create(**args)

        self.answer = completion.choices[0]['message']['content']
        self.messages.append({"role": "assistant", "content" : self.answer})

        # usage = completion['usage']
        # cost = usage['total_tokens']*0.002/1000
        # self.total_cost += cost
        # print(f"Cost: ${cost} - Total cost: ${self.total_cost}")

        return self.answer