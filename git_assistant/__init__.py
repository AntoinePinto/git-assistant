import argparse
import os
import time

from datetime import datetime

import openai
import pwinput

from easyenvi import EasyEnvironment

from . import llm
from .git_utils import git_assistant, is_git_repo

txt_readme_structure = """Here is the generated README structure. I stored it in {local_path}/structure_md.md:
{structure}

What do you want to do ?
 1 - Generate a new README structure
 2 - Generate README content according to this structure
Tap 1 or 2.
Note: If you want to modify this structure by yourself, please modify the file {local_path}/structure_md.md then tap 2"""

def interact(message, role='git-assistant', func=print):
    return func(f"\n\033[1m({role})\033[0m: {message}")

def main():

    parser = argparse.ArgumentParser(description="Git Assistant Tool")
    subparsers = parser.add_subparsers(dest="command")

    generate_readme_parser = subparsers.add_parser("generate-readme", help="Generate the README.md file using generative AI.")
    generate_readme_parser.add_argument("--repo_url", type=str, help="GitHub repository URL", required=False)
    generate_readme_parser.add_argument("--gpt_model", type=str, help="OPEN AI GPT model", required=False)

    chatbot_parser = subparsers.add_parser("chatbot", help="Interact with a chatbot and ask questions about the repository.")
    chatbot_parser.add_argument("--repo_url", type=str, help="GitHub repository URL", required=False)
    chatbot_parser.add_argument("--gpt_model", type=str, help="OPEN AI GPT model", required=False)

    args = parser.parse_args()

    gpt_model = args.gpt_model  
    if gpt_model is None:
        gpt_model = "gpt-3.5-turbo-16k-0613"

    # provider = "VA"
    # for k, v in st.secrets['OPEN_AI'][provider].items():
    #     os.environ[k] = v
    # llm.set_openai_environment('CHAT_GPT')
    # writer = llm.ChatGPT(model=gpt_model, azure_engine=True)

    if (args.repo_url is None) & (not is_git_repo('.')):
        raise "You are not in the root of a .git repository."

    interact(message="Please copy/paste your OpenAI API token. Tutorial to get your free API token : https://www.youtube.com/watch?v=EQQjdwdVQ-M")
    openai.api_key = interact(message="OPEN AI TOKEN: ", role="user", func=pwinput.pwinput)
    writer = llm.ChatGPT(model=gpt_model)

    gitty = git_assistant(repo_url=args.repo_url, folder=".", writer=writer)
    output = gitty.get_files_content()

    if output is not None:
        raise output

    local_path = gitty.folder + '/.gitassistant'
    if not os.path.exists(local_path):
        os.mkdir(local_path)

    env = EasyEnvironment(local_path=local_path)

    files = os.listdir(local_path)

    if args.gpt_model is None:
        interact(f"I will use {gpt_model} gpt model for this application. See the documentation if you want to specify another model: https://github.com/AntoinePinto/git-assistant")
        time.sleep(2)

    if 'metadata.pickle' not in files:
        interact(f"I haven't been initialised in this repository.")
        metadata = {}
        initialise = "Y"
        time.sleep(0.5)
    else:
        metadata = env.local.load('metadata.pickle')
        last_update = metadata['last_update'].strftime('%Y-%m-%d %H:%M')
        interact(f"I have been initialisased in this repository on {last_update}. Do you want to re-initialise?\nNote: Re-initialise if you want to consider recent changes.")
        initialise = interact(f"Response [Y or N]:", role='user', func=input)
        if initialise == "N":
            gitty.summary_concat = metadata['content']

    if initialise == "Y":
        interact(f"Initialising...")
        gitty.initialise(max_token=16000)
        metadata = {'content': gitty.summary_concat, 'last_update': datetime.now()}
        env.local.save(metadata, 'metadata.pickle')

    if args.command == "generate-readme":

        choice = "0"
        while choice != "2":
            if ('structure_md.md' in files) & (choice == "0"):
                gitty.structure_md = env.local.load('structure_md.md')
            else:
                interact("Generating README structure...")
                gitty.get_global_summary()
                structure_md = gitty.generate_readme_structure()
                env.local.save(structure_md, 'structure_md.md')
            interact(txt_readme_structure.format(structure=gitty.structure_md, local_path=local_path))
            choice = interact(f"Response [1 or 2]: ", role='user', func=input)
        
        gitty.structure_md = env.local.load('structure_md.md')
        interact("Generating README content...")
        readme = gitty.generate_readme(max_token=16000)
        env.local.save(readme, 'README.md')

        interact(f"The README has been successfully generated! It has been stored into {local_path}/README.md")

    elif args.command == "chatbot":

        gitty.initialize_chatbot()

        interact(f"Hello, I am your git assistant, do you have a question about this repository?")

        while True:
            user_msg = interact(f"Question: ", role='user', func=input)
            response = gitty.chatbot_question(question=user_msg)
            interact(response)

if __name__ == "__main__":
    main()