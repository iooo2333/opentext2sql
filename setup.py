from setuptools import setup, find_packages
import os
import io

setup(
    name="opentext2sql",
    version="0.1.2",
    author="iooo2333",
    description="A text to SQL conversion tool with web interface",
    long_description=io.open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/iooo2333/opentext2sql",
    packages=find_packages(exclude=["test_env", "train_data"]),
    include_package_data=True,
    package_data={
        "opentext2sql": ["build/**/*"],
    },
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
        "fastapi",
        "uvicorn",  # 用于运行FastAPI应用
    ],
    entry_points={
        'console_scripts': [
            'opentext2sql=opentext2sql.easy_start:start',
        ],
    },
)
