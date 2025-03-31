from .prompt import Prompts
from .tool_function import timer, draw_graph, extract_table_names
from langgraph.graph import END, StateGraph, START
import json
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage
from langgraph.graph.message import AnyMessage, add_messages


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class Text2SqlAgentAutoSelectTableNodes():
    def __init__(self, train_model):
        self.train_model = train_model

    #   获取所有表名
    def get_all_tables_node(self):
        schema_file = self.train_model.table_schema_file

        def node(state: State) -> dict[str, list[AIMessage]]:
            with open(schema_file, 'r', encoding='utf-8') as file:
                data = json.load(file)  # 解析 JSON 文件为 Python 数据结构
            tables = [table['table_name'] for table in data]
            return_content = ",".join(tables)
            return {
                "messages": [
                    AIMessage(
                        content=return_content,
                    )
                ]
            }
        return node

    #   获取选择表名和业务的doc
    def get_document_for_table_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[-1]  # 获取获取aimessage 或者 toolmessage
            query = ai_message.content
            documentations = train_model.get_relate_doc_table(query)
            content = "以下是一些建议，用来帮助你判断用户想查的内容在哪一部分表中 : " + \
                "。".join(documentations)
            return {
                "messages": [
                    AIMessage(
                        content=content,
                    )
                ]
            }
        return node

    #   确定相关表名
    def get_relate_table_node(self):
        train_model = self.train_model

        def node(state: State):
            user_question = state.get("messages", [])[0].content
            doc = state.get("messages", [])[-1].content
            tables = state.get("messages", [])[-2].content
            better_content = "用户的问题是:"+user_question+"。以下是所有的表名" + tables+"。"+doc
            invoke_message = {"messages": [better_content]}

            get_relate_table = Prompts.get_relate_table_prompt | train_model.get_llm()
            message = get_relate_table.invoke(invoke_message)  # 使用LLM去执行
            return {"messages": [message]}
        return node

    #   获取表结构
    def get_ddl_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[-1]  # 获取获取aimessage 或者 toolmessage
            content = ai_message.content
            print("llm选择的表是:")
            print(content)
            split_list = content.split(',')
            schema = train_model.get_schema_from_train_data(split_list)
            content = "{"+','.join(schema)+"}"
            return {
                "messages": [
                    AIMessage(
                        content=content,
                    )
                ]
            }
        return node

    def get_document_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[0]  # 获取获取aimessage 或者 toolmessage
            query = ai_message.content
            documentations = train_model.get_relate_doc(query)
            content = "以下是与用户想要查询的问题相关的专业知识 : " + "。".join(documentations)
            return {
                "messages": [
                    AIMessage(
                        content=content,
                    )
                ]
            }
        return node

    def generate_sql_node(self):
        train_model = self.train_model
        db_dialect = train_model.db_dialect

        def node(state: State):
            user_question = state.get("messages", [])[0].content
            doc = state.get("messages", [])[-1].content
            doc_ddl = state.get("messages", [])[-2].content
            better_content = "用户的问题是:"+user_question+"。" + \
                doc+"。以下是相关表的表结构"+doc_ddl+"。使用的数据库是:" + db_dialect
            invoke_message = {"messages": [better_content]}

            generate_sql = Prompts.generate_sql_prompt | train_model.get_llm()
            message = generate_sql.invoke(invoke_message)
            return {"messages": [message]}
        return node

    def get_relate_question_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[0]  # 获取获取aimessage 或者 toolmessage
            query = ai_message.content
            relate_question = train_model.get_relate_question(query)
            content = "案例问题:" + "["+"。".join(relate_question) + "]"
            return {
                "messages": [
                    AIMessage(
                        content=content,
                    )
                ]
            }
        return node

    def judge_question_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            user_question = state.get("messages", [])[-2].content
            doc = state.get("messages", [])[-1].content
            better_content = "用户的问题是:"+user_question+"。"+doc
            invoke_message = {"messages": [better_content]}

            check_error = Prompts.judge_question_prompt | train_model.get_llm()
            message = check_error.invoke(invoke_message)
            return {"messages": [message]}
        return node

    def get_one_sql_and_schema_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[-1]
            question = ai_message.content.split("。")[0]
            print(question)
            relate_sql = train_model.get_sql_from_question([question])[0]
            table_list = extract_table_names(relate_sql)
            schemas = train_model.get_schema_from_train_data(table_list)

            relate_sql_to_str = "{"+relate_sql + \
                "[相关表结构:" + schemas[0] + "]"+"}"
            return {
                "messages": [
                    AIMessage(
                        content=relate_sql_to_str,
                    )
                ]
            }
        return node

    def generate_sql_only_example_node(self):
        train_model = self.train_model
        db_dialect = train_model.db_dialect

        def node(state: State):
            user_question = state.get("messages", [])[0].content
            summary = state.get("messages", [])[-1].content
            better_content = "用户的问题是:"+user_question + \
                "。以下是案例和表结构" + summary + "。使用的数据库是:" + db_dialect
            invoke_message = {"messages": [better_content]}
            generate_sql = Prompts.generate_sql_only_example_prompt | train_model.get_llm()
            message = generate_sql.invoke(invoke_message)
            return {"messages": [message]}
        return node

    def db_query_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[-1]  # 获取获取aimessage 或者 toolmessage
            content = ai_message.content.replace("/n", "").strip()
            content = train_model.extract_sql(content)
            db_return = train_model.run_sql(content)
            if isinstance(db_return, str):  # 如果已经是字符串，不做处理
                db_return = "查询失败"
            else:
                db_return = "查询成功"
            return {
                "messages": [
                    AIMessage(
                        content=db_return,
                    )
                ]
            }
        return node

    def check_error_node(self):
        train_model = self.train_model

        def node(state: State):
            user_question = state.get("messages", [])[0].content
            wrong_sql = state.get("messages", [])[-2].content
            wrong = state.get("messages", [])[-1].content
            better_content = "用户的问题是:" + user_question + \
                "。错误sql:" + wrong_sql + "。错误原因:" + wrong
            invoke_message = {"messages": [better_content]}
            check_error = Prompts.check_error_prompt | train_model.get_llm()
            message = check_error.invoke(invoke_message)
            return {"messages": [message]}
        return node


class Text2SqlAgentAutoSelectTable():
    def __init__(self, train_model, use_exmple_question=False, save_flow_graph=False):
        self.train_model = train_model
        nodes = Text2SqlAgentAutoSelectTableNodes(train_model=train_model)
        workflow = StateGraph(State)
        workflow.add_node("get_all_tables_node",
                          nodes.get_all_tables_node())
        workflow.add_node("get_document_for_table_node",
                          nodes.get_document_for_table_node())
        workflow.add_node("get_relate_table_node",
                          nodes.get_relate_table_node())
        workflow.add_node("get_ddl_node",
                          nodes.get_ddl_node())
        workflow.add_node("get_document_node",
                          nodes.get_document_node())

        workflow.add_node("generate_sql_node",
                          nodes.generate_sql_node())

        workflow.add_edge("get_all_tables_node", "get_document_for_table_node")
        workflow.add_edge("get_document_for_table_node",
                          "get_relate_table_node")
        workflow.add_edge("get_relate_table_node",
                          "get_ddl_node")
        workflow.add_edge("get_ddl_node",
                          "get_document_node")
        workflow.add_edge("get_document_node",
                          "generate_sql_node")

        if (use_exmple_question):
            def check_relate_question_node(state: State):
                messages = state.get("messages", [])
                ai_message = messages[-1]
                if ai_message.content != "没有":  # 这里只能是yes或者no
                    return "example"
                return "llm"
            workflow.add_conditional_edges(
                "judge_question_node",
                check_relate_question_node,
                {"example": "get_one_sql_and_schema_node",
                 "llm": "get_all_tables_node"},
            )

            workflow.add_node("get_relate_question_node",
                              nodes.get_relate_question_node())
            workflow.add_node("judge_question_node",
                              nodes.judge_question_node())
            workflow.add_node("get_one_sql_and_schema_node",
                              nodes.get_one_sql_and_schema_node())
            workflow.add_node("generate_sql_only_example_node",
                              nodes.generate_sql_only_example_node())
            workflow.add_edge(START, "get_relate_question_node")
            workflow.add_edge("get_relate_question_node",
                              "judge_question_node")
            workflow.add_edge("get_one_sql_and_schema_node",
                              "generate_sql_only_example_node")

        else:
            workflow.add_edge(START, "get_all_tables_node")

        self.app = workflow.compile()

        if (save_flow_graph):
            draw_graph(self.app, 'agent_Text2SqlAgentAutoSelectTable.png')

    def generate_sql(self, input):
        app = self.app
        print(input)
        for event in app.stream({"messages": [("user", input)]}):
            key = next(iter(event))  # 获取event的key\
            print(event)

        state = event[key]
        messages = state.get("messages", [])
        res_message = messages[-1]
        res = res_message.content
        sql = self.train_model.extract_sql(res)
        # print(sql)
        return sql

    def ask(self, input):
        sql = self.generate_sql(input=input)
        db_return = self.train_model.run_sql(sql)
        return db_return


class Text2SqlAgentAutoSelectAspectNodes(Text2SqlAgentAutoSelectTableNodes):
    def __init__(self, train_model):
        self.train_model = train_model

    def get_all_aspects_node(self):
        table_grouped_file = self.train_model.table_grouped_file

        def node(state: State) -> dict[str, list[AIMessage]]:
            with open(table_grouped_file, 'r', encoding='utf-8') as file:
                data = json.load(file)  # 解析 JSON 文件为 Python 数据结构

            # 获取 JSON 顶层的所有键
            keys = list(data.keys()) if isinstance(data, dict) else []
            return_content = ",".join(keys)
            return {
                "messages": [
                    AIMessage(
                        content=return_content,
                    )
                ]
            }
        return node

    def get_relate_aspects_node(self):
        train_model = self.train_model

        def node(state: State):
            user_question = state.get("messages", [])[0].content
            doc = state.get("messages", [])[-1].content
            aspects = state.get("messages", [])[-2].content
            better_content = "用户的问题是:"+user_question+"。以下是所有的业务分类" + aspects+"。"+doc
            invoke_message = {"messages": [better_content]}

            get_relate_aspects = Prompts.get_relate_aspects_prompt | train_model.get_llm()
            message = get_relate_aspects.invoke(invoke_message)  # 使用LLM去执行
            return {"messages": [message]}
        return node

    def get_ddl_by_aspects_node(self):
        train_model = self.train_model

        def node(state: State) -> dict[str, list[AIMessage]]:
            messages = state.get("messages", [])
            ai_message = messages[-1]  # 获取获取aimessage 或者 toolmessage
            content = ai_message.content

            table_list = train_model.get_table_list_by_aspects(content)
            schema = train_model.get_schema_from_train_data(table_list)
            content = "{"+','.join(schema)+"}"
            return {
                "messages": [
                    AIMessage(
                        content=content,
                    )
                ]
            }

        return node


class Text2SqlAgentAutoSelectAspect():
    def __init__(self, train_model, use_exmple_question=False, save_flow_graph=False):
        self.train_model = train_model
        nodes = Text2SqlAgentAutoSelectAspectNodes(train_model=train_model)
        workflow = StateGraph(State)
        workflow.add_node("get_all_aspects_node",
                          nodes.get_all_aspects_node())
        workflow.add_node("get_document_for_table_node",
                          nodes.get_document_for_table_node())
        workflow.add_node("get_relate_aspects_node",
                          nodes.get_relate_aspects_node())
        workflow.add_node("get_ddl_by_aspects_node",
                          nodes.get_ddl_by_aspects_node())
        workflow.add_node("get_document_node",
                          nodes.get_document_node())
        workflow.add_node("generate_sql_node",
                          nodes.generate_sql_node())

        workflow.add_edge("get_all_aspects_node",
                          "get_document_for_table_node")
        workflow.add_edge("get_document_for_table_node",
                          "get_relate_aspects_node")
        workflow.add_edge("get_relate_aspects_node",
                          "get_ddl_by_aspects_node")
        workflow.add_edge("get_ddl_by_aspects_node",
                          "get_document_node")
        workflow.add_edge("get_document_node",
                          "generate_sql_node")
        if (use_exmple_question):
            def check_relate_question_node(state: State):
                messages = state.get("messages", [])
                ai_message = messages[-1]
                if ai_message.content != "没有":  # 这里只能是yes或者no
                    return "example"
                return "llm"
            workflow.add_conditional_edges(
                "judge_question_node",
                check_relate_question_node,
                {"example": "get_one_sql_and_schema_node",
                 "llm": "get_all_aspects_node"},
            )

            workflow.add_node("get_relate_question_node",
                              nodes.get_relate_question_node())
            workflow.add_node("judge_question_node",
                              nodes.judge_question_node())
            workflow.add_node("get_one_sql_and_schema_node",
                              nodes.get_one_sql_and_schema_node())
            workflow.add_node("generate_sql_only_example_node",
                              nodes.generate_sql_only_example_node())
            workflow.add_edge(START, "get_relate_question_node")
            workflow.add_edge("get_relate_question_node",
                              "judge_question_node")
            workflow.add_edge("get_one_sql_and_schema_node",
                              "generate_sql_only_example_node")

        else:
            workflow.add_edge(START, "get_all_aspects_node")

        self.app = workflow.compile()

        if (save_flow_graph):
            draw_graph(self.app, 'agent_Text2SqlAgentAutoSelectAspect.png')

    @timer
    def generate_sql(self, input):
        app = self.app
        print(input)
        for event in app.stream({"messages": [("user", input)]}):
            key = next(iter(event))  # 获取event的key\
            print(event)

        state = event[key]
        messages = state.get("messages", [])
        res_message = messages[-1]
        res = res_message.content
        sql = self.train_model.extract_sql(res)
        # print(sql)
        return sql

    @timer
    def ask(self, input):
        sql = self.generate_sql(input=input)
        db_return = self.train_model.run_sql(sql)
        return db_return
