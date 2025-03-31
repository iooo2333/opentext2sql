import pandas as pd
import sqlparse
import re
from .build_train_data import add_question_sql_traindata, add_question_tables_traindata
#   获取sql中的表名


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


def get_traindata_from_excel(excel_file, sql_output_file):
    df = pd.read_excel(excel_file)
    for index, row in df.iterrows():
        question = str(row[1])
        sql = str(row[2])
        tables = ",".join(extract_table_names(sql))
        add_question_sql_traindata(question, sql, sql_output_file)
