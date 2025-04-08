
from pydantic import BaseModel

from typing import Dict

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


class ConfigRequest(BaseModel):
    train_: str
    excel_filename: str
    db_config: Dict[str, str]
    model_name: str
    openai_api_base: str
    openai_api_key: str


