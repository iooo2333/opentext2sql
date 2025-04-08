from opentext2sql.agent.create_agent import Text2SqlAgentAutoSelectTable, Text2SqlAgentAutoSelectAspect
from opentext2sql.chroma.chromadb_vector import ChromaDB_VectorStore
from fastapi import FastAPI, Query
import traceback
from fastapi.middleware.cors import CORSMiddleware

from .models import InputMessage,ConfigRequest
from .utils import replace_nan_with_none
from typing import Dict, Any


app = FastAPI()


# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源（生产环境应指定具体域名）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)


agent = None
train_model = None

@app.post("/set_config/")

async def convert_config(config: ConfigRequest,model_type: str = Query(..., description="模型类型")):
    global agent
    global train_model
    config = config.dict()
    config["train_data_directory"] = "./train_data/"+config["train_model_name"]
    config["path"] = "./train_data/"+config["train_model_name"]
    print(config)
    train_model = ChromaDB_VectorStore(config=config)
    train_model.build_tabel_schema_train_data_from_conn()  # 获取表结构 必须要的

    if(model_type == "AutoSelectTable"):
        agent = Text2SqlAgentAutoSelectTable(
            train_model, use_exmple_question=True, save_flow_graph=True)
    if(model_type == "AutoSelectAspect"):
        train_model.build_grouped_tables()
        agent = Text2SqlAgentAutoSelectTable(
            train_model, use_exmple_question=True, save_flow_graph=True)


    
    return {"status": "success", "message": "Configuration saved successfully"}


@app.put("/sql_agent",)
async def get_sqlagent_reflection(
    input_message: InputMessage,
):
    try:
        content = input_message.model_dump()["input"]
        print(content)
        result, run_time = agent.ask(content)
        print(result)
        if isinstance(result, str):  # 如果已经是字符串，不做处理
            return {
                "code": 20000,
                "data": {"查询失败": "连接大模型API超时"
                         },
                "message": "请求成功"
            }
        else:
            if result.empty:
                return {
                    "code": 20000,
                    "data": {"查询失败": "没有在数据库中找到相关信息"
                             },
                    "message": "请求成功"
                }

        result = result.to_dict(orient="records")
        result_fixed = replace_nan_with_none(result)
        return {
            "code": 20000,
            "data": {"查询成功": result_fixed,
                     "查询时间": run_time
                     },
            "message": "请求成功"
        }

    except Exception as e:
        error_text = traceback.format_exc()
        print(error_text)
        err_dict = {
            "code": 20000,
            "data": {"查询失败": "程序出现异常"
                     },
            "message": "请求成功"
        }
        return err_dict

