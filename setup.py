# setup.py

from setuptools import setup, find_packages

setup(
    name="git-assistant",
    version="1.0.3",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "git-assistant = git_assistant:main"
        ]
    },
    install_requires=[
        "easyenvi==1.0.4", 
        "fsspec==2023.6.0",
        "GitPython==3.1.32",
        "nbconvert==7.8.0",
        "nbformat==5.9.2",  
        "numpy==1.24.4",   
        "openai==0.27.10",
        "pwinput==1.0.3"
    ],
)