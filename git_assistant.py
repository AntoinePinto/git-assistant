
# import sys
# import logging
# import time
# import streamlit as st
# from tqdm import tqdm

# # Configurez le niveau de journalisation
# logging.basicConfig(level=logging.INFO)

# # Créer un format de journalisation
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# # Créer un gestionnaire de journalisation pour afficher les messages en console
# console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setFormatter(formatter)

# # Ajouter le gestionnaire de journalisation à root logger
# logging.getLogger('').addHandler(console_handler)

# def my_func():
#     for i in stqdm(range(5), desc="Progression", unit="étape"):
#         time.sleep(1)
#         logging.info("Ceci est un avertissement depuis my_func")

# st.title("Affichage des informations de journalisation dans Streamlit")

# with st.spinner('En cours...'):
#     my_func()

# sys.exit()
# from logging import _Level
# import sys
# import logging
# import streamlit as st

# # Configurez le niveau de journalisation
# logging.basicConfig(level=logging.INFO)



# # Redirigez les messages de journalisation vers le flux de sortie de Streamlit
# class StreamlitHandler(logging.Handler):
    
#     def __init__(self):
#         self.info = st.empty()
    
#     def emit(self, record):
#         msg = self.format(record)
#         self.info.empty()
#         self.info = st.markdown(f"<i>{msg}</i>", unsafe_allow_html=True)
#         self.flush()

# # Ajoutez le gestionnaire de journalisation personnalisé à la liste des gestionnaires
# logging.getLogger().addHandler(StreamlitHandler())


# def my_func():
#     import time
#     # Votre code ici
#     for i in range(5):
#         time.sleep(1)
#         logging.info("Ceci est un avertissement depuis my_func")

# with st.spinner('...'):
#     my_func()



# sys.exit()

import os
import sys

import streamlit as st

from stqdm import stqdm

sys.path.append('rsc/scripts')
import streamlit_utils
import llm
from git_utils import git_assistant

# Initialisation
streamlit_utils.initialize_session_state()
streamlit_utils.config_page_appearance(layout='centered')

if 'writer' not in st.session_state:
    ## Defining LLM writer
    provider = "PERSO"

    for k, v in st.secrets['OPEN_AI'][provider].items():
        os.environ[k] = v
    
    azure_engine = st.secrets['OPEN_AI'][provider]['api_type_CHAT_GPT'] == "azure"

    st.session_state['writer'] = llm.ChatGPT(model=os.getenv("engine_CHAT_GPT"), azure_engine=azure_engine)
    st.session_state['expander_structure'] = True

col0, col1, col2 = st.columns([0.5, 1, 0.5])
with col1:
    application = st.radio("Your generated README", ["Q&A Repository", "README Generator"], index=0, horizontal=True, label_visibility="collapsed")

with st.expander(label='GitHub Repository URL', expanded=True):
    repo_url = st.text_input("GitHub Repository URL", label_visibility='collapsed')
    st.session_state['REPO_TITLE'] = repo_url.split('/')[-1]
    submit_github_url = st.button('Submit')

if submit_github_url:
    with st.spinner('...'):
        st.session_state['gitty'] = git_assistant(repo_url=repo_url, writer=st.session_state['writer'], progress_bar_func=stqdm)
        st.session_state['gitty'].clone_repository()
        st.session_state['gitty'].get_files_content()
        st.session_state['gitty'].get_summary_concat(max_len_summary_concat=14000)
        st.session_state['gitty'].get_global_summary()

if (application == "README Generator") & ("gitty" in st.session_state):

    st.write("1. Generate README Structure")
    with st.expander(label='README structure', expanded=st.session_state['expander_structure']):
        col0, col1, col2 = st.columns([0.5, 1, 0.5])
        with col1:
            gen_readme_structure = st.button("Generate/Re-Generate README Structure")
            if gen_readme_structure:
                with st.spinner('...'):
                    st.session_state['structure'] = st.session_state['gitty'].generate_readme_structure()
                st.session_state['expander_structure'] = True

        if "structure" in st.session_state:
            st.session_state['gen'] = st.markdown(st.session_state['structure'], unsafe_allow_html=True)

    st.write("2. Generate README Content")
    with st.expander(label='README Content', expanded=False):
        if "structure" in st.session_state:
            col0, col1, col2 = st.columns([0.5, 1, 0.5])
            with col1:
                gen_readme_content = st.button("Generate/Re-Generate README Content")
                if gen_readme_content:
                    with st.spinner('...'):
                        st.session_state['readme'] = st.session_state['gitty'].generate_readme()

            if "readme" in st.session_state:
                col0, col1, col2 = st.columns([0.5, 1, 0.5])
                with col1:
                    output = st.radio("Your generated README", ["Markdown Output", "Markdown Code"], index=0, horizontal=True, label_visibility="collapsed")
                
                if output == "Markdown Output":
                    final_output = st.markdown(st.session_state['readme'], unsafe_allow_html=True)        
                else:
                    final_output = st.code(st.session_state['readme'], "markdown")
        else:
            st.markdown("First of all, generate a README Structure in section 1.", unsafe_allow_html=True)

if (application == "Q&A Repository") & ("gitty" in st.session_state):

    if 'messages' not in st.session_state:
        st.session_state['messages'] = [['assistant', "Ask a question about the repository."]]
        st.session_state['gitty'].initialize_chatbot()

    for role, message in st.session_state['messages']:
        with st.chat_message(role, avatar=st.session_state['img'][role]):
            st.markdown(message, unsafe_allow_html=True)

    user_msg = st.chat_input(placeholder='Question?')

    if user_msg:
        # Add and print user message
        st.session_state['messages'].append(['user', user_msg])
        with st.chat_message('user', avatar=st.session_state['img']['user']):
            st.markdown(user_msg, unsafe_allow_html=True)

        with st.spinner('...'):
            response = st.session_state['gitty'].chatbot_question(question=user_msg)

        # Add and print assistant message
        st.session_state['messages'].append(['assistant', response])
        with st.chat_message('assistant', avatar=st.session_state['img']['assistant']):
            st.markdown(response, unsafe_allow_html=True)



    



