import re
from typing import Any
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langchain_core.messages import ToolMessage
import io
from functools import wraps
import time
from PIL import Image
import sqlparse


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数 {func.__name__} 执行时间: {end_time - start_time:.4f} 秒")
        return result
    return wrapper


def draw_graph(graph, filename):
    try:
        image = Image.open(io.BytesIO(
            graph.get_graph().draw_mermaid_png()))  # 这里需要联网
        image.save(filename)
    except Exception:
        print("绘图失败")
        pass


def extract_table_names(sql_query):
    parsed = sqlparse.parse(sql_query)
    table_names = set()
    table_name_pattern = r'\bFROM\s+([^\s\(\)\,]+)|\bJOIN\s+([^\s\(\)\,]+)'

    for statement in parsed:
        statement_str = str(statement).lower()
        matches = re.findall(table_name_pattern, statement_str, re.IGNORECASE)

        for match in matches:
            for name in match:
                if name:
                    table_name = name.split('.')[-1]
                    table_name = re.sub(r'("|`|\'|;)', '', table_name)
                    table_names.add(table_name)

    return list(table_names)
