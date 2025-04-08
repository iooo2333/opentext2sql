
from .excel_data_get import get_traindata_from_excel
from .get_table_schema import get_table_schema_to_json_from_conn
from .group_tables_graph import get_grouped_tables
from abc import abstractmethod
import json
from sqlalchemy import create_engine
from sqlalchemy import text
import re
from sqlalchemy.engine import URL
from langchain_openai import ChatOpenAI
import os
import pandas as pd
import traceback


def extract_error_info(error_text):
    """
    从完整的错误日志中提取有用的报错信息

    参数:
        error_text (str): 包含完整错误日志的字符串

    返回:
        str: 提取出的错误描述和触发错误的 SQL 行信息
    """
    # 尝试提取错误描述，如 "psycopg2.errors.SyntaxError: syntax error at or near "1""
    error_desc_match = re.search(r'(psycopg2\.errors\.[^\n]+)', error_text)
    if error_desc_match:
        error_desc = error_desc_match.group(1)
    else:
        error_desc = '未找到错误描述信息。'

    # 尝试提取出触发错误的 SQL 行，如 "LINE 14: ...AND mo.delivery_time >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"
    line_match = re.search(r'LINE\s+\d+:\s*(.*)', error_text)
    if line_match:
        error_line = line_match.group(1)
    else:
        error_line = '未找到具体的错误 SQL 行信息。'

    # 返回整合的信息
    return f"错误描述: {error_desc}\n错误SQL行: {error_line}"


def create_db_engine(config):

    # 处理 SQLite 特殊情况
    if config["dialect"] == "sqlite":
        db_url = f"sqlite:///{config['database']}"

    db_url = URL.create(
        drivername=config.get("dialect"),
        username=config.get("username"),
        password=config.get("password"),
        host=config.get("host"),
        port=config.get("port"),
        database=config.get("database")
    )

    # 创建 Engine
    engine = create_engine(db_url)

    return engine


class TrainModel:
    def __init__(self, config=None):
        if config is None:
            raise ValueError("config 参数不能为空！")

        # 检查必需的顶级配置项
        required_keys = [
            'train_data_directory',
            'db_config',
            'model_name',
            'openai_api_base',
            'openai_api_key'
        ]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"缺少必需的配置项: {key}")

        self.train_data_directory = config['train_data_directory']
        self.excel_filename = config['excel_filename']

        db_config = config['db_config']
        self.db_dialect = db_config["dialect"]

        self.connect_to_db = create_db_engine(db_config)

        # 拼接生成文件路径
        self.sql_output_file = os.path.join(
            self.train_data_directory, "train_data_question_sql.json")
        self.documentation_file = os.path.join(
            self.train_data_directory, "train_data_documentations.json")
        self.documentation_table_file = os.path.join(
            self.train_data_directory, "train_data_documentations_table.json")
        self.table_schema_file = os.path.join(
            self.train_data_directory, "train_data_table_schema.json")
        self.table_grouped_file = os.path.join(
            self.train_data_directory, "train_data_table_grouped.json")

        self.model_name = config['model_name']
        self.openai_api_base = config['openai_api_base']
        self.openai_api_key = config['openai_api_key']

    def get_llm(self):
        llm = ChatOpenAI(
            model_name=self.model_name,        # 提供的模型名称
            openai_api_base=self.openai_api_base,  # API地址
            openai_api_key=self.openai_api_key  # API 密钥
        )

        return llm

    def build_train_data_from_excel(self, excelfile):
        if not excelfile:
            raise "no excel"
        sql_output_file = self.train_data_directory + \
            "train_data_question_sql.json"
        get_traindata_from_excel(
            excelfile, sql_output_file)

    #   连接数据库获取表结构 保存到指定位置
    def build_tabel_schema_train_data_from_conn(self):    # 获取表结构
        get_table_schema_to_json_from_conn(
            self.connect_to_db, self.table_schema_file)

    #   创建添加doc
    @abstractmethod
    def build_documentation_train_data(self, doc):
        pass

    #   创建添加doc
    @abstractmethod
    def build_documentation_table_train_data(self, doc):
        pass

    #   创建添加question-sql训练数据
    @abstractmethod
    def build_question_sql_train_data(self, question, sql):
        pass

    # 通过表名获取表结构
    def get_schema_from_train_data(self, table_names_list):
        try:
            with open(self.table_schema_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        schema_list = []
        for ddl_data in data:

            table_name = ddl_data["table_name"]
            if table_name in table_names_list:
                schema_list.append("["+ddl_data["input_ddl"]+"]")
        return schema_list

    # 通过问题获取sql
    def get_sql_from_question(self, question_list):
        return_list = []
        try:
            with open(self.sql_output_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            raise "no train data of table and question"

        for sql_data in data:
            question = sql_data["question"]
            if question in question_list:
                sql = sql_data["sql"]
                sql_question = "[question:" + question + ",sql:" + sql + "]"
                return_list.append(sql_question)

        return return_list

    # 创建向量数据库 根据初始化的config中的文件创建
    def train_all(self):
        pass

    def log(self, message: str, title: str = "Info"):
        print(f"{title}: {message}")

    def extract_sql(self, llm_response: str) -> str:
        # If the llm_response contains a CTE (with clause), extract the last sql between WITH and ;
        sqls = re.findall(r"\bWITH\b .*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        # If the llm_response is not markdown formatted, extract last sql by finding select and ; in the response
        sqls = re.findall(r"SELECT.*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        # If the llm_response contains a markdown code block, with or without the sql tag, extract the last sql from it
        sqls = re.findall(r"```sql\n(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        sqls = re.findall(r"```(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self.log(title="Extracted SQL", message=f"{sql}")
            return sql

        return llm_response

    #   把一个doc添加进一个json文件里面
    def add_documentation_train(self, input_documentation, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        data.append({"id": len(data)+1, "content": input_documentation})

        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    #   把一个question-sql添加进一个json文件里面
    def add_question_sql_traindata(self, input_question, input_sql, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        data.append(
            {"id": len(data)+1, "question": input_question, "sql": input_sql})
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def run_sql(self, sql):
        try:
            with self.connect_to_db.connect() as conn:
                try:
                    result = conn.execute(
                        text(sql))  # 查询表数据
                    rows = result.fetchall()
                    # 获取列名
                    columns = result.keys()
                    # 创建 DataFrame
                    df = pd.DataFrame(rows, columns=columns)
                except Exception as e:
                    error_text = traceback.format_exc()
                    sql_err = extract_error_info(error_text)
                    return "查询错误:"+sql_err
                return df
        except:
            raise "no connect_to_db"

    def build_grouped_tables(self):
        try:
            with open(self.table_schema_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            raise "cant get schema"

        schema_list = []
        for ddl_data in data:
            table_name = ddl_data.get("table_name")
            input_ddl = ddl_data.get("input_ddl")
            if table_name and input_ddl:
                schema_list.append(
                    f"Table Name: {table_name}\nSchema:\n{input_ddl}\n")

        content = ".".join(schema_list)
        llm = self.get_llm()
        grouped_tables = get_grouped_tables(content, llm)
        with open(self.table_grouped_file, "w", encoding="utf-8") as f:
            json.dump(grouped_tables, f, ensure_ascii=False, indent=4)
        print(grouped_tables)
        return grouped_tables

    def get_table_list_by_aspects(self, aspects):
        try:
            with open(self.table_grouped_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            raise "没有找到文件"
        table_list = data.get(aspects, [])

        return table_list
