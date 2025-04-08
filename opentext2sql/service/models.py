
from pydantic import BaseModel

from typing import Optional, Union, Literal

class InputMessage(BaseModel):
    input: str

    model_config = {
        "json_schema_extra": {  # 添加案例
            "examples": [
                {
                    "input": "查询项目(f70500e70a2e4d428a61c2806662d046)中，最近三个月的材料订单数量及对应的供应商信息。",
                }
            ]
        },

    }


# 针对 SQLite 的 db_config 模型
class DBConfigSQLite(BaseModel):
    dialect: Literal["sqlite"]
    database: str

# 针对 PostgreSQL 的 db_config 模型
class DBConfigPostgreSQL(BaseModel):
    dialect: Literal["postgresql"]
    host: str
    port: str
    database: str
    username: str
    password: str

# 整体配置模型
class ConfigRequest(BaseModel):
    train_model_name: str
    excel_filename: Optional[str] = None  # excel_filename 非必须
    # 联合类型，支持两种不同的 db_config 配置
    db_config: Union[DBConfigSQLite, DBConfigPostgreSQL]
    model_name: str
    openai_api_base: str
    openai_api_key: str

   