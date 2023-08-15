import json
import os
import subprocess
import time

from tqdm import tqdm

import numpy as np

class git_assistant:

    def __init__(self, writer, repo_url=None, folder=None, progress_bar_func=tqdm):
        
        self.repo_url = repo_url
        
        if repo_url is not None:
            self.folder = repo_url.split('/')[-1]
        else:
            self.folder = folder

        self.writer = writer

        self.tqdm = progress_bar_func

    def clone_repository(self):
        if not os.path.exists(self.folder):
            subprocess.run(["git", "clone", self.repo_url], check=True, capture_output=True, text=True)

    def get_files_content(self, file_max_nb_char=50000):

        # List ignored files if exists
        if os.path.exists(f"{self.folder}/.gitignore"):
            with open(f"{self.folder}/.gitignore") as f:
                ignored = f.read().split('\n')
        else:
            ignored = []
        ignored = [i for i in ignored if i != ""]

        self.files = {'content': {}}
        for root, _, filenames in os.walk(f"{self.folder}"):
            for filename in filenames:
                path = os.path.join(root, filename).replace("\\", "/")
                is_ignored = np.sum([path.startswith(f) for f in ignored]) > 0
                if (not path.startswith(f"{self.folder}/.git")) & (not path.startswith("README")) & (not is_ignored):
                    with open(path) as f:
                        try:
                            self.files['content'][path] = f.read()
                        except UnicodeDecodeError:
                            self.files['content'][path] = "Not a text convertible file?"
                        if len(self.files['content'][path]) > file_max_nb_char:
                            self.files['content'][path] = "Number of char is too large for this file."

    def get_summary_concat(self,
                           max_len_summary_concat=8000,
                           context="You are a powerful Git assistant that explain how a specific files works. You give informations that the user will use to create a README file.",
                           prompt_template="Describe the content of the file {path} in less than {max_words} words. Here is the content.\n\n{content}"):

        total_len_repo = np.sum([len(v) for k, v in self.files['content'].items()])
        summary_factor = max_len_summary_concat / total_len_repo

        self.files['summary'] = {}
        self.summary_concat = ""
        for path, content in self.tqdm(self.files['content'].items()):

            max_words = 50 + round(len(content) * summary_factor / 10)
            prompt = prompt_template.format(path=path, content=content, max_words=max_words)

            self.writer.define_context(context=context)
            response = self.writer.ask(message=prompt, temperature=0, request_timeout=30)

            self.files['summary'][path] = response
            summary = response.replace('\n', '')
            self.summary_concat += f"File located in {path}: {summary}\n\n"

    def get_global_summary(self,
                           context="You write repository description for code professionnal.",
                           prompt_template="Write a long and detailed description of how the following repository works.\n\nREPOSITORY FILES:\n```\n{summary_concat}\n```"):

        prompt = prompt_template.format(summary_concat=self.summary_concat)

        self.writer.define_context(context=context)
        response = self.writer.ask(message=prompt, temperature=0, max_tokens=3000, request_timeout=60)
        
        self.global_summary = response

    def transform_structure(self, structure):

        structure_md = f""

        # titles = []
        for section in structure['sections']:
            # titles.append(section['title'])
            structure_md += f"\n## {section['title']}"
            if 'subsections' in section:
                for subsection in section['subsections']:
                    # titles.append(subsection['title'])
                    structure_md += f"\n### {subsection['title']}"

        return structure_md

    def generate_readme_structure(self,
                                  context="""According to a Git repository, your role is to suggest a README structure with only # Section and ## Subsections names. \nThe names of the sections and sub-sections you choose must suit the purpose of the repository.\n\nHere\'s an example of the structure:\n\n{\n"title": "My Project Name",\n"sections": [\n    {\n    "title": "Introduction"\n    },\n    {\n    "title": "Installation"\n    },\n    {\n    "title": "Use",\n    "subsections": [\n        {\n        "title": "Configuration"\n        },\n        {\n        "title": "Examples"\n        }\n    ]\n    },\n    {\n    "title": "Contribute"\n    },\n    {\n    "title": "License"\n    }\n]\n}\n\n\nYou return only the structure in JSON format.\n""",
                                  prompt_template="'Suggest the README structure with only # Section and ## Subsections.\n\nREPOSITORY DESCRIPTION:```\n{global_summary}\n```\n\nReturn only the JSON format.\n'"):
        
        prompt = prompt_template.format(global_summary=self.global_summary)

        self.writer.define_context(context=context)
        response = self.writer.ask(message=prompt, temperature=0.7, request_timeout=60)

        self.structure = json.loads(response) # JSONDecodeError
        self.structure_md = self.transform_structure(structure=self.structure)

        return self.structure_md

    def generate_readme(self,
                        context="Your role is to generate README.md files for a Git repository.",
                        prompt_template="According to the following README structure and by learning from the repository files, generate a README file.\n\nREADME structure:\n```\n{structure_markdown}\n```\n\nRepository files:\n```\n{summary_concat}\n```"):

        prompt = prompt_template.format(structure_markdown=self.structure_md, summary_concat=self.summary_concat)

        self.writer.define_context(context=context)
        response = self.writer.ask(message=prompt, temperature=0.7, max_tokens=3000, request_timeout=60)

        self.readme = response

        return self.readme

    def initialize_chatbot(self,
                           context_template="You answer questions about the following repository. It is described by file.\n\nREPOSITORY FILES:\n```\n{summary_concat}\n```\n\nYour answer should be in HTML and highlighting with <strong> the important informations.\n"):

        import copy
        self.chatbot = copy.deepcopy(self.writer)
        
        context = context_template.format(summary_concat=self.summary_concat)
        self.chatbot.define_context(context=context)
        
    def chatbot_question(self,
                         question):
        
        response = self.chatbot.ask(message=question, temperature=0.7, request_timeout=45,  sleep_timeout=10)
        return response