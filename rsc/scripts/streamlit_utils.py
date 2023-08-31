import base64
import json
import os
import sys

import streamlit as st
import openai

from PIL import Image

from easyenvi import EasyEnvironment

def add_local_background(image_file):

    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
        background-attachment: local;
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

def hide_header_footer():

    st.markdown("""
    <style>
    #MainMenu , header, footer {visibility: hidden;}

    /* This code gets the first element on the sidebar,
    and overrides its default styling */
    section[data-testid="stSidebar"] div:first-child {
    top: 0;
    height: 100vh;
    }
    </style>
    """,
    unsafe_allow_html=True)


def initialize_session_state():

    if 'img' not in st.session_state:

        if not check_password():
            sys.exit()

        st.session_state['img'] = {
            'tab_logo': 'rsc/img/tab_logo.png',
            'background': 'rsc/img/background.png',
            'assistant': '🤖',
            'user': '👤'
        }

        with open('rsc/credentials/GCP_credentials.json', 'w') as fp:
            json.dump(dict(st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]), fp)


        st.session_state['envi'] = EasyEnvironment(
            local_path='',
            
            gcloud_project_id='my-gcp-project-387112',
            gcloud_credential_path="rsc/credentials/GCP_credentials.json",
            GCS_path='gs://my-gcp-project-gcs-bucket/git-assistant/'
        )




def config_page_appearance(header=None, layout='wide'):
    st.set_page_config(page_title="Git Assistant", page_icon = Image.open(st.session_state['img']['tab_logo']), layout=layout)
    add_local_background(st.session_state['img']['background'])

    if header is not None:
        st.markdown(f"""<p style="color:#E20023;font-size:48px;">{header}</p>""",
                    unsafe_allow_html=True)
        
def openai_config(application, provider):

    if os.path.exists('.streamlit/secrets.toml'):
        secrets = st.secrets["OPEN_AI"][provider][application]

    openai.api_key = secrets['api_key']
    openai.api_base = secrets['api_base']
    openai.api_type = secrets['api_type']
    openai.api_version = secrets['api_version']

def check_url_token():
    url_params = st.experimental_get_query_params()
    if 'token' not in url_params:
        sys.exit()

    if url_params['token'][0] != st.secrets['token_url']:
        sys.exit()

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""

        if os.path.exists('.streamlit/secrets.toml'):
            password = st.secrets["password"]
        else:
            with open('rsc/credentials/password.json', 'r') as f:
                password = json.load(f)['password']

        if st.session_state["password"] == password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "PASSWORD", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "PASSWORD", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

def divide_text(text, tokenizer, max_token=3500):
    tokens = tokenizer.encode(text)
    sub_texts = [tokenizer.decode(tokens[i:i+max_token]) for i in range(0, len(tokens), max_token)]
    
    return sub_texts