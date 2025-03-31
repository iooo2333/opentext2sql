import json
import os

#   把内容添加进json文件


def add_ddl_traindata(table_name, input_ddl,  filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append({"table_name": table_name, "input_ddl": input_ddl})

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_question_sql_traindata(input_question, input_sql, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(
        {"id": len(data)+1, "question": input_question, "sql": input_sql})
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_question_tables_traindata(input_question, input_tabels, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(
        {"id": len(data)+1, "question": input_question, "tabels": input_tabels})

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_documentation_train(input_documentation, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append({"id": len(data)+1, "content": input_documentation})

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


#   加载训练集
def train_all_documentation(train, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        raise "no train data of documentation"
    for documentation_data in data:
        documentation = documentation_data["content"]
        train.add_documentation(documentation=documentation)


def train_all_documentation_table(train, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        raise "no train data of documentation"
    for documentation_data in data:
        documentation = documentation_data["content"]
        train.add_ddl(ddl=documentation)


def train_all_sql(train, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        raise "no train data of sql and question"
    for sql_data in data:
        question = sql_data["question"]
        train.add_question_sql(question)
