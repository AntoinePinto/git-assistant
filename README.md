# Git Assistant

Git Assistant is a tool harnessing the power of generative AI to assist Git users.

*   **chatbot**: Engage with a chatbot to question a repository.
*   **generate-readme**: Automatically generate comprehensive README.md files describing Git repositories.

## Web Interface

Access to the git-assistant web interface: https://git-assistant.streamlit.app/

https://github.com/AntoinePinto/git-assistant/assets/76919407/dd16f1d1-3066-49d3-947f-775af0819195

## Command line Interface

With command line interface, you need to specify you OpenAI API token. Tutorial to get your free API token : https://www.youtube.com/watch?v=EQQjdwdVQ-M"

### Installation

Install `git-assistant` within your environment.

```
pip install git-assistant
```

### Generate a README file

To generate a README.md file for a local git repository, execute the following command **in a local git repository**.

```
git-assistant generate-readme
```

For a remote repository, provide the `repo_url` parameter. For example:

```
git-assistant generate-readme --repo_url=https://github.com/AntoinePinto/easyenvi
```

### Interact with the chatbot

To engage with a chatbot associated with a local git repository, execute the following command inside a **local git repository**.

```
git-assistant chatbot
```

For a chatbot linked to a remote repository, specify the `repo_url` parameter. For example:

```
git-assistant chatbot --repo_url=https://github.com/AntoinePinto/easyenvi
```

## Specify GPT model

To select a specific GPT model, utilize the `gpt_model`` parameter. For example:

```
git-assistant generate-readme --gpt_model=gpt-4-0613
```