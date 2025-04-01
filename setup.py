from setuptools import setup, find_packages

setup(
    name="opentext2sql",
    version="0.1.0",
    author="iooo2333",
    description="A simple math utilities package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/iooo2333/opentext2sql",
    packages=find_packages(exclude=["test_env", "train_data"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "langchain_core",
        "langgraph",
        "Pillow",
        "sqlparse",
        "pandas",
        "chromadb",
        "sqlalchemy",
        "langchain_openai",
        "psycopg2",
    ],
)
