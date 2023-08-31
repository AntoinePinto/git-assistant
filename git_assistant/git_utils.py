import git
import json
import os
import subprocess
import time

from tqdm import tqdm

import nbformat
import numpy as np

from nbconvert import PythonExporter

def is_git_repo(path):
    try:
        git.Repo(path)
        return True
    except:
        return False

def round_10(v):
    return int((v + 5) // 10 * 10)

def read_ipynb(path):

    with open(path, 'r', encoding='utf-8') as notebook_file:
        notebook_content = notebook_file.read()

    nb = nbformat.reads(notebook_content, as_version=4)
    python_exporter = PythonExporter()
    python_code, _ = python_exporter.from_notebook_node(nb)

    return python_code

def text_content(path, file_max_nb_char):
    with open(path) as f:
        try:
            if str(path).split('.')[-1] == '.ipynb':
                text = read_ipynb(path)
            else:
                text = f.read()
        except UnicodeDecodeError:
            text = "Not a text convertible file?"
        if len(text) > file_max_nb_char:
            return "Number of char is too large for this file."

        return text

class git_assistant:

    def __init__(self, writer, repo_url=None, folder=None, progress_bar_func=tqdm):
        
        self.repo_url = repo_url
        
        if repo_url is not None:
            self.folder = repo_url.split('/')[-1]
            self.clone_repository()
        else:
            self.folder = folder
            if not is_git_repo(folder):
                raise "You are not in the root of a .git repository."

        self.writer = writer

        self.tqdm = progress_bar_func

    def clone_repository(self):
        if not os.path.exists(self.folder):
            subprocess.run(["git", "clone", self.repo_url], check=True, capture_output=True, text=True)

    def get_files_content(self, file_max_nb_char=30000, n_max_file=30):

        list_filenames = []
        if self.repo_url is not None:

            # List ignored files if exists
            if os.path.exists(f"{self.folder}/.gitignore"):
                with open(f"{self.folder}/.gitignore") as f:
                    ignored = f.read().split('\n')
            else:
                ignored = []
            ignored = [i for i in ignored if i != ""]

            for root, _, filenames in os.walk(f"{self.folder}"):
                for filename in filenames:
                    path = os.path.join(root, filename).replace("\\", "/")
                    is_ignored = np.sum([path.startswith(f) for f in ignored]) > 0
                    if (not path.startswith(f"{self.folder}/.git")) & (not is_ignored):
                        list_filenames.append(path)

        else:
            repo = git.Repo('.')
            filenames = repo.git.ls_files().splitlines()
            # filenames = subprocess.check_output("git ls-files", shell=True).splitlines()
            for filename in filenames:
                list_filenames.append(filename)

        if len(list_filenames) > n_max_file:
            return f"This repository contains too many files ({len(list_filenames)} readable files). To avoid exceeding the tool's expenditure, please use a smaller repository."
        
        if len(list_filenames) == 0:
            return "There is no easy-readable file (convertible to text) in this repository"

        self.files = {'content': {}}
        for filename in list_filenames:
            self.files['content'][filename] = text_content(filename, file_max_nb_char)

    def initialise(self,
                   max_token=4000,
                   min_len_summary = 50,
                   context="You are a powerful Git assistant that explain how a specific files works. You give informations that the user will use to create a README file.",
                   prompt_template="File content: ```{content}```\n\nWrite a description of this file with maximum {max_word} words."):

        len_total = np.sum([len(v) for k, v in self.files['content'].items()])
        
        self.files['summary'] = {}

        max_token_corrected = max_token - min_len_summary*len(self.files['content'])
        max_token_files = {k: round_10(min_len_summary + (max_token_corrected * len(v))/len_total) for k, v in self.files['content'].items()}

        self.files['summary'] = {}
        self.summary_concat = ""
        for path, content in self.tqdm(self.files['content'].items()):
            prompt = prompt_template.format(content=content, max_word=max_token_files[path])
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

        try:
            self.structure = json.loads(response) # JSONDecodeError
        except json.decoder.JSONDecodeError:
            raise Exception(f"json.decoder.JSONDecodeError: \n{response}")

        self.structure_md = self.transform_structure(structure=self.structure)

        return self.structure_md

    def generate_readme(self,
                        max_token=4000,
                        context="Your role is to generate README.md files for a Git repository.",
                        prompt_template="According to the following README structure and by learning from the repository files, generate very descriptive README file with maximum {max_words} words.\n\nREADME structure:\n```\n{structure_markdown}\n```\n\nRepository files:\n```\n{summary_concat}\n```"):

        prompt = prompt_template.format(max_words=max_token, structure_markdown=self.structure_md, summary_concat=self.summary_concat)

        self.writer.define_context(context=context)
        response = self.writer.ask(message=prompt, temperature=0.7, max_tokens=10000, request_timeout=100)

        self.readme = response

        return self.readme

    def initialize_chatbot(self,
                           context_template="You answer questions about the following repository. It is described by file.\n\nREPOSITORY FILES:\n```\n{summary_concat}\n```\n\nYour answer should be in HTML and highlighting with <strong> the important informations.\n"):

        import copy
        self.chatbot = copy.deepcopy(self.writer)
        self.chatbot.total_cost = 0
        
        context = context_template.format(summary_concat=self.summary_concat)
        self.chatbot.define_context(context=context)
        
    def chatbot_question(self,
                         question):
        
        response = self.chatbot.ask(message=question, temperature=0.7, request_timeout=45)
        return response