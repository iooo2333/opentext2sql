import pandas as pd
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate
import json


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


group_tables_system = """你的任务是读取并理解数据库中所有的表的表名和表结构,分析表结构中的字段。
                        判断哪些表是属于同一方面,或同一业务,或者是查询时需要同时使用的。
                        你需要把这些判断为同一方面或同一业务,或者是查询时需要同时使用的表,放在一起,并且概括这方面的内容或者业务是什么。
                        放在一起的规则如下：
                        1,同一个表可以出现在多个方面的内容或业务中。例如字典表和用户表这些每个业务或方面都需要的表,应该在每个分组中出现。
                        2,注意观测表连接的字段,根据字段连接的逻辑创建多个有重叠表的内容分组。
                        3,每个同一方面,或同一业务,或者是查询时需要同时使用的分组,最多不能超过10张表。注意为每个分组概括一个精简的内容描述。
                        4,你需要把所有的表都分出去,不要遗漏表。

                        只返回你的分组结果,不要返回任何其他内容!
                        返回的格式案例如下:
                       "采购合同业务": [
                            "material_contract",
                            "material_contract_details",
                        ],
                        "材料入库业务": [
                            "material_warehouse_put",
                            "project_info"
                        ]
                        严格按照格式案例回复!
"""
group_tables_prompt = ChatPromptTemplate.from_messages(
    [("system", group_tables_system), ("placeholder", "{messages}")]
)


def get_grouped_tables(content, llm):

    class NodesMoreQuestion:
        def __init__(self, llm_choose):  # 构造方法
            self.llm_choose = llm_choose

        def group_tables_node(state: State):
            generate_similar_question = group_tables_prompt | llm
            message = generate_similar_question.invoke(state)  # 使用query_gen去执行
            return {"messages": [message]}

    workflow = StateGraph(State)
    workflow.add_node("group_tables_node",
                      NodesMoreQuestion.group_tables_node)
    workflow.add_edge(START, "group_tables_node")
    app = workflow.compile()

    for event in app.stream(
        {"messages": [("user", content)]}
    ):
        print(event)
    key = next(iter(event))
    state = event[key]
    messages = state.get("messages", [])
    ai_message = messages[-1]
    json_string = ai_message.content
    fixed_json_string = "{" + json_string + "}"
    data = json.loads(fixed_json_string)

    return data
