from setuptools import setup, find_packages

setup(
    name="code-assistant",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pathlib>=1.0.1",
        "tqdm>=4.64.0",
    ],
    python_requires=">=3.8",
    description="A tool for analyzing and fixing code using LLM models through Ollama",
    author="Erik Rusek",
)
