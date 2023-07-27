import time
from datetime import datetime

import openai
# import vertexai
# from vertexai.preview.language_models import TextGenerationModel

#---------------------------------------------------------------------------------------------#

class ChatGPT:

    def __init__(self, model='gpt-3.5-turbo', azure_engine=False, call_time_interval=0):
        self.last_call = datetime(2023, 1, 1, 0, 0, 0, 0)
        self.total_cost = 0
        self.model = model
        self.azure_engine = azure_engine
        self.call_time_interval = call_time_interval

    def define_context(self, context="You are an assistant."):

        self.messages = [{"role": "system", "content" : context}]

    def add_few_shots(self, shots):

        for shot in shots:
            self.messages.extend([{"role": k, "content" : v} for k, v in shot.items()])

    def ask(self, message, max_tokens=512, temperature=1, top_p=1, request_timeout=100):

        self.messages.append({"role": "user", "content" : message})

        while (datetime.now() - self.last_call).seconds < self.call_time_interval:
            time.sleep(2)

        if self.azure_engine is True:
            completion = openai.ChatCompletion.create(
                messages=self.messages,
                engine=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                request_timeout=request_timeout)
            
        else:
            completion = openai.ChatCompletion.create(
                messages=self.messages,
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                request_timeout=request_timeout)

        self.last_call = datetime.now()

        usage = completion['usage']
        self.answer = completion.choices[0]['message']['content']
        self.messages.append({"role": "assistant", "content" : self.answer})
        
        cost = usage['total_tokens']*0.002/1000
        self.total_cost += cost

        print(f"Cost: ${cost} - Total cost: ${self.total_cost}")

        return self.answer

# class PaLM:

#     def __init__(self, project_id):
#         self.last_call = datetime(2023, 1, 1, 0, 0, 0, 0)
#         self.messages = ""
#         self.project_id = project_id

#     def define_context(self, context="You are an assistant."):

#         self.messages = f"{context}\n\n"

#     def add_few_shots(self, shots):

#         for shot in shots:
#             self.messages += f"input: {shot['user']}\noutput: {shot['assistant']}\n\n"

#     def ask(self, message, model="text-bison@001", max_tokens=512, temperature=1, top_p=1):

#         self.messages += f"input: {message}\noutput: "

#         vertexai.init(project=self.project_id, location="us-central1")
#         model = TextGenerationModel.from_pretrained(model)
        
#         self.response = model.predict(
#             self.messages,
#             max_output_tokens=max_tokens,
#             temperature=temperature,
#             top_p=top_p,)
        
#         self.last_call = datetime.now()

#         return self.response.text
