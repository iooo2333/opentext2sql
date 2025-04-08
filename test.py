from opentext2sql.agent.create_agent import Text2SqlAgentAutoSelectTable, Text2SqlAgentAutoSelectAspect
from opentext2sql.chroma.chromadb_vector import ChromaDB_VectorStore
import os

ALI_KEY = os.environ.get("ALI_KEY")
config = {
    "train_data_directory": "./train_data/",
    "excel_filename": "train_data.xlsx",
    "db_config": {
        "dialect": "sqlite",
        "database": "my_database.db",
    },
    "model_name": "qwen-plus",
    "openai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai_api_key": ALI_KEY
}

my_train = ChromaDB_VectorStore(config=config)
my_train.build_tabel_schema_train_data_from_conn()  # 获取表结构 必须要的
my_train.build_grouped_tables()
my_train.build_train_data_from_excel("train_data")

agent = Text2SqlAgentAutoSelectTable(
    my_train, use_exmple_question=True, save_flow_graph=True)
# agent = Text2SqlAgentAutoSelectAspect(
#     my_train, use_exmple_question=True, save_flow_graph=True)
# dbret = agent.ask("查询")
# # print(dbret)
