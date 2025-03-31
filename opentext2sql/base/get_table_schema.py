from .build_train_data import add_ddl_traindata
import os
from sqlalchemy import inspect


# def get_table_schema_to_json_from_conn(engine, filename):

#     if os.path.exists(filename):
#         # 打开文件并清空内容
#         with open(filename, 'w') as file:
#             file.truncate(0)  # 清空文件内容

#     with engine.connect() as conn:
#         inspector = inspect(conn)
#         # 获取所有表名
#         tables = inspector.get_table_names()

#         for table in tables:
#             # 获取表注释（作为表别名）
#             table_comment = inspector.get_table_comment(table)
#             table_alias = table_comment.get(
#                 "text", "") if table_comment else ""

#             # 构造保存内容
#             lines = []
#             lines.append(f"表名: {table}")
#             lines.append(f"表别名: {table_alias}")
#             lines.append("")

#             # 获取字段信息
#             columns = inspector.get_columns(table)
#             for col in columns:
#                 column_name = col.get("name")
#                 data_type = str(col.get("type"))
#                 # is_nullable = col.get("nullable", True)
#                 # default = col.get("default", None)
#                 # 有些数据库支持字段注释，可作为别名；如果不支持则为空字符串
#                 column_comment = col.get("comment", "")

#                 lines.append(f"字段: {column_name}")
#                 lines.append(f"  别名: {column_comment}")
#                 lines.append(f"  类型: {data_type}")
#                 lines.append("")

#             content = "\n".join(lines)

#             # 假设 add_ddl_traindata 为你预先定义的保存函数
#             add_ddl_traindata(table, content, filename)
#             print(f"表 {table} 的结构已保存到 {filename}")


def get_table_schema_to_json_from_conn(engine, filename):
    import os
    from sqlalchemy import inspect

    # 清空或创建文件
    if os.path.exists(filename):
        with open(filename, 'w') as file:
            file.truncate()

    with engine.connect() as conn:
        inspector = inspect(conn)
        # 获取数据库方言类型
        dialect_name = engine.dialect.name
        print(dialect_name)

        # 获取所有表名
        tables = inspector.get_table_names()
        print(tables)

        for table in tables:
            # 处理表注释（SQLite不支持）
            if dialect_name == 'sqlite':
                table_alias = ""
            else:
                table_comment = inspector.get_table_comment(table)
                table_alias = table_comment.get(
                    'text', '') if table_comment else ''

            # 构造表结构信息
            content_lines = [
                f"表名: {table}",
                f"表别名: {table_alias}",
                ""
            ]

            # 处理字段信息
            for column in inspector.get_columns(table):
                column_name = column['name']
                column_type = str(column['type'])
                column_comment = column.get('comment', '')  # 自动处理无注释的情况

                content_lines.extend([
                    f"字段: {column_name}",
                    f"  别名: {column_comment}",
                    f"  类型: {column_type}",
                    ""
                ])

            # 写入文件
            add_ddl_traindata(
                table,
                '\n'.join(content_lines),
                filename
            )
            print(f"表 {table} 的结构已保存到 {filename}")
