import os

import numpy as np
import openai

def get_files_content(folder):

    # List ignored files if exists
    if os.path.exists(f"{folder}/.gitignore"):
        with open(f"{folder}/.gitignore") as f:
            ignored = f.read().split('\n')
    else:
        ignored = []

    files_content = {}
    for root, _, filenames in os.walk(f"{folder}"):
        for filename in filenames:
            path = os.path.join(root, filename).replace("\\", "/")
            is_ignored = np.sum([path.startswith(f) for f in ignored]) > 0
            if (not path.startswith(f"{folder}/.git")) & (not path.startswith("README")) & (not is_ignored):
                with open(path) as f:
                    try:
                        files_content[path] = f.read()
                    except UnicodeDecodeError:
                        files_content[path] = "Not a text convertible file"

                    if len(files_content[path]) > 50000:
                        files_content.pop(path)

    return files_content

def get_files_description_concat(files_description):
    files_description_concat = ""
    for filename, content in files_description.items():
        desc = content.replace('\n', '')
        files_description_concat += f"File located in {filename}: {desc}\n\n"
    return files_description_concat

def get_repo_detailed_description(files_description_concat, writer):

    CONTEXT = """You write repository description for code professionnal.
    """

    PROMPT = f"""Write a long and detailed description of how the following repository works.

    REPOSITORY FILES:
    ```
    {files_description_concat}
    ```
    """

    writer.messages = [{'role': 'system', 'content': CONTEXT},
                    {'role': 'user', 'content': PROMPT}]

    completion = openai.ChatCompletion.create(
                    messages=writer.messages,
                    engine=writer.model,
                    max_tokens=3000,
                    temperature=0.5,
                    top_p=1,
                    request_timeout=60)

    desc = completion.choices[0]['message']['content']

    return desc

def tranform_structure(structure):

    structure_markdown = f""

    titles = []
    for section in structure['sections']:
        titles.append(section['title'])
        structure_markdown += f"\n## {section['title']}"
        if 'subsections' in section:
            for subsection in section['subsections']:
                titles.append(subsection['title'])
                structure_markdown += f"\n### {subsection['title']}"

    return structure_markdown, titles