# setup.py

from setuptools import setup, find_packages

setup(
    name="git-assistant",
    version="1.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "git-assistant = git_assistant:main"
        ]
    },
    install_requires=["pwinput", "easyenvi", "nbformat", "nbconvert", "openai", "GitPython"
    ],
)