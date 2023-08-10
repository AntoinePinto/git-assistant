import json
import os
import subprocess
import sys
import time

import numpy as np
import openai
import streamlit as st

sys.path.append('rsc/scripts')
import streamlit_utils
import llm
import utils

# Initialisation
streamlit_utils.initialize_session_state()
streamlit_utils.config_page_appearance(layout='centered')

if 'writer' not in st.session_state:
    ## Defining LLM writer
    streamlit_utils.openai_config('ChatGPT')
    st.session_state['writer'] = llm.ChatGPT(model="gpt-3.5-turbo-16k")
    st.session_state['expander_structure'] = True
    st.session_state['appli'] = None
    st.session_state["action"] = None

def understand_repo():
    
    with st.spinner('...'):
        if not os.path.exists(st.session_state['REPO_TITLE']):
            subprocess.run(["git", "clone", repo_url], check=True, capture_output=True, text=True)

    # GET FILES CONTENT
    st.session_state['files'] = {'content': utils.get_files_content(folder=st.session_state['REPO_TITLE'])}

    # GET FILES DESCRIPTION

    CONTEXT = """You are a powerful Git assistant that explain how a specific files works. You give informations that the user will use to create a README file."""
    PROMPT = """Describe the content of the file {filename} in less than {max_words} words. Here is the content.\n\n{content}"""

    nb_char_repo = np.sum([len(v) for k, v in st.session_state['files']['content'].items()])
    summary_factor = 15000 / nb_char_repo

    st.session_state['files']['description'] = {}
    sub_msg1 = st.empty()
    for filename, content in st.session_state['files']['content'].items():

        st.session_state['writer'].define_context(context=CONTEXT)

        max_words = 50 + round(len(content) * summary_factor / 10)

        response = st.session_state['writer'].ask(
            PROMPT.format(filename=filename, content=content, max_words=max_words),
            temperature=0,
            request_timeout=30)

        st.session_state['files']['description'][filename] = response
        
        sub_msg1.empty()
        sub_msg1 = st.markdown(f"<i><strong>{filename}</strong>: {response}...</i>", 
                                unsafe_allow_html=True)

    sub_msg1.empty()

    # CONCAT FILES DESCRIPTION

    st.session_state['files']['files_description_concat'] = utils.get_files_description_concat(st.session_state['files']['description'])

    # GET REPO DETAILED DESCRIPTION

    repo_detailed_description = utils.get_repo_detailed_description(
        st.session_state['files']['files_description_concat'],
        writer=st.session_state['writer']
        )
    st.session_state['files']['repo_detailed_description'] = repo_detailed_description

    pass

def generate_readme_structure():
        # GENERATE README STRUCTURE

        CONTEXT = """According to a Git repository, your role is to suggest a README structure with only # Section and ## Subsections names. 
        The names of the sections and sub-sections you choose must suit the purpose of the repository.

        Here's an example of the structure:

        {
        "title": "My Project Name",
        "sections": [
            {
            "title": "Introduction"
            },
            {
            "title": "Installation"
            },
            {
            "title": "Use",
            "subsections": [
                {
                "title": "Configuration"
                },
                {
                "title": "Examples"
                }
            ]
            },
            {
            "title": "Contribute"
            },
            {
            "title": "License"
            }
        ]
        }


        You return only the structure in JSON format.
        """

        PROMPT = f"""Suggest the README structure with only # Section and ## Subsections.

        REPOSITORY DESCRIPTION:```
        {st.session_state['files']['repo_detailed_description']}
        ```

        Return only the JSON format.
        """

        st.session_state['writer'].define_context(context=CONTEXT)

        structure_str = st.session_state['writer'].ask(message=PROMPT, temperature=0.7, request_timeout=60)

        st.session_state['files']['structure'] = json.loads(structure_str)

        structure_markdown, titles = utils.tranform_structure(st.session_state['files']['structure'])

        st.session_state['generated_readme'] = ""
        for section in st.session_state['files']['structure']['sections']:
            st.session_state['generated_readme'] += f"""<h1 style="font-size: 20px; line-height: 0;"># {section['title']}</h1>"""
            if 'subsections' in section:
                for subsection in section['subsections']:
                    st.session_state['generated_readme'] += f"""<h1 style="font-size: 14px; line-height: 0;">## {subsection['title']}</h1>""" 

        # st.session_state['files'] = st.session_state['env'].local.load("files.pickle")
        # st.session_state['generated_readme'] = st.session_state['files']['generated_readme']

def generate_readme():

    structure_markdown, titles = utils.tranform_structure(st.session_state['files']['structure'])

    CONTEXT = "Your role is to generate README.md files for a Git repository."

    PROMPT = f"""According to the following README structure and by learning from the repository files, generate a README file.
    
    README structure:
    ```
    {structure_markdown}
    ```

    Repository files:
    ```
    {st.session_state['files']['files_description_concat']}
    ```"""

    st.session_state['writer'].define_context(context=CONTEXT)

    st.session_state['response'] = st.session_state['writer'].ask(message=PROMPT, max_tokens=3000, temperature=0.7, request_timeout=60)

col0, col1, col2 = st.columns([0.5, 1, 0.5])
with col1:
    application = st.radio("Your generated README", ["Q&A Repository", "README Generator"], index=0, horizontal=True, label_visibility="collapsed")

a, b, c = st.columns([0.000001, 1, 0.000001])
with b:
    with st.expander(label='GitHub Repository URL', expanded=True):
        repo_url = st.text_input("GitHub Repository URL", label_visibility='collapsed')
        st.session_state['REPO_TITLE'] = repo_url.split('/')[-1]
        submit_github_url = st.button('Submit')

    if submit_github_url:
        with st.spinner('...'):
            understand_repo()


if (application == "README Generator"):

    col0, col1, col2 = st.columns([0.6, 1, 0.5])
    with col1:
        if "files" in st.session_state:
            gen_readme_structure = st.button("Generate a new README Structure")
            if gen_readme_structure:
                with st.spinner('...'):
                    generate_readme_structure()
                st.session_state['expander_structure'] = True

    a, b, c = st.columns([0.000001, 1, 0.000001])
    
    col0, col1, col2 = st.columns([0.6, 1, 0.5])
    with col1:
        if "generated_readme" in st.session_state:
            gen_readme = st.button("Generate the complete README file")
            if gen_readme:
                st.session_state['expander_structure'] = False
                with st.spinner('...'):
                    generate_readme()

    with b:
        if "generated_readme" in st.session_state:
            with st.expander(label='README structure', expanded=st.session_state['expander_structure']):
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    st.session_state['gen'] = st.markdown(st.session_state['generated_readme'], unsafe_allow_html=True)

    if 'response' in st.session_state:

        a, b, c = st.columns([0.000001, 1, 0.000001])

        with b:
            col0, col1, col2 = st.columns([0.5, 1, 0.5])
            with col1:
                output = st.radio("Your generated README", ["Markdown Output", "Markdown Code"], index=0, horizontal=True, label_visibility="collapsed")
            
            if output == "Markdown Output":
                final_output = st.markdown(st.session_state['response'], unsafe_allow_html=True)        
            else:
                final_output = st.code(st.session_state['response'], "markdown")

if (application == "Q&A Repository") & ("files" in st.session_state):

    if 'messages' not in st.session_state:

        st.session_state['messages'] = [['assistant', "Ask a question about the repository."]]
        
        CONTEXT = f"""You answer questions about the following repository. It is described by file.

        REPOSITORY FILES:
        ```
        {st.session_state['files']['files_description_concat']}
        ```

        Your answer should be in HTML and highlighting with <strong> the important informations.
        """

        st.session_state['writer'].define_context(context=CONTEXT)

    for role, message in st.session_state['messages']:
        with st.chat_message(role, avatar=st.session_state['img'][role]):
            st.markdown(message, unsafe_allow_html=True)

    user_msg = st.chat_input(placeholder='Question?')

    if user_msg:
        # Add and print user message
        st.session_state['messages'].append(['user', user_msg])
        with st.chat_message('user', avatar=st.session_state['img']['user']):
            st.markdown(user_msg, unsafe_allow_html=True)

        streamlit_utils.openai_config("ChatGPT")
        with st.spinner('...'):
            response = st.session_state['writer'].ask(message=user_msg, temperature=0.7)

        # Add and print assistant message
        st.session_state['messages'].append(['assistant', response])
        with st.chat_message('assistant', avatar=st.session_state['img']['assistant']):
            st.markdown(response, unsafe_allow_html=True)



    



