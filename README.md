# RAG Training SQL Generator

本项目提供了一套基于 RAG 思想的 SQL 生成训练流程，通过训练问答数据自动构造 SQL 查询。利用 ChromaDB 作为向量存储，并提供两个不同的智能体（自动选择表和表分组）来生成 SQL。本项目支持多种数据库配置（例如 PostgreSQL 和 SQLite），并且通过 Excel 文件自动构建训练数据。

This project provides a RAG-based training framework for generating SQL queries. By training on question-SQL pairs, it automatically constructs SQL queries. Using ChromaDB as the vector store and two different agents (one for table selection and one for table grouping), this package supports multiple database configurations (e.g., PostgreSQL and SQLite) and automatically builds training data from an Excel file.

---

## 特性 | Features

- **多数据库支持**  
  支持 PostgreSQL、SQLite 等多种数据库配置。

- **自动训练数据构建**

  - 自动获取数据库表结构。
  - 根据表结构进行分组（用于智能体自动选择）。
  - 从 Excel 文件中加载 question-SQL 训练数据。
  - 添加辅助大模型生成 SQL 的文档信息（针对表结构与查询策略）。

- **智能体生成 SQL**  
  提供两个智能体：

  - `Text2SqlAgentAutoSelectTable`：自动选择相关表，获取表的 DDL 信息，再结合文档生成 SQL。
  - `Text2SqlAgentAutoSelectAspect`：自动选择表分组信息，进一步提升生成 SQL 的准确性。

- **流程图绘制**  
  支持生成训练流程的图形化展示，帮助用户直观理解模型处理流程。

---

## 安装 | Installation

确保你已安装 Python 3.6 或更高版本。安装时请使用 pip（请将 `your-package-name` 替换为你实际发布的包名）：

```bash
pip install your-package-name
```

## 使用方法 | Usage

本项目主要包含以下步骤：

### 1. 定义配置文件

根据数据库类型定义配置。例如：

- **PostgreSQL 配置：**

  ```
  python复制编辑config = {
    "train_data_directory": "./train_data/",
    "excel_filename": "train_data.xlsx",
    "db_config": {
      "dialect": "postgresql",
      "host": "ddnscd.gis-data.cn",
      "port": "7435",
      "database": "AItest4",
      "username": "postgres",
      "password": "pg@gisdata"
    },
    "model_name": "qwen-plus",
    "openai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai_api_key": "sk-3b127055020546ba973a8d0923e68a53"
  }
  ```

- **SQLite 配置：**

  ```
  python复制编辑config = {
    "train_data_directory": "./train_data/",
    "excel_filename": "train_data.xlsx",
    "db_config": {
      "dialect": "sqlite",
      "database": "my_database.db"
    },
    "model_name": "qwen-plus",
    "openai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "openai_api_key": "sk-3b127055020546ba973a8d0923e68a53"
  }
  ```

### 2. 创建 RAG 训练模型并添加训练数据

利用配置初始化训练模型，并构建训练数据：

```
python复制编辑my_train = ChromaDB_VectorStore(config=config)

# 自动构建训练数据
my_train.build_tabel_schema_train_data_from_conn()   # 获取表结构（必须）
my_train.build_grouped_tables()                        # 将表按照类别分组（用于 Text2SqlAgentAutoSelectAspect）
my_train.build_train_data_from_excel("train_data.xlsx")  # 从 Excel 加载 question-SQL 训练数据
my_train.build_question_sql_train_data()               # 添加 question-SQL 案例
my_train.build_documentation_table_train_data()        # 添加表和分组类型的文档信息
my_train.build_documentation_train_data()              # 添加生成 SQL 的文档说明
```

Excel 文件的排列示例如下：

| id  | question                       | sql                                                                                                                                                                                                                                   |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 查询某个项目中材料订单的总金额 | SELECT mo.project_id, SUM(MOD.order_num \* MOD.price) AS total_amount FROM material_order mo JOIN material_order_details MOD ON mo.ID = MOD.order_id WHERE mo.project_id = 'f70500e70a2e4d428a61c2806662d046' GROUP BY mo.project_id; |

### 3. 创建智能体

根据训练模型创建两个智能体，用于自动生成 SQL：

- **自动选择表的智能体：**

  ```
  agent_1 = Text2SqlAgentAutoSelectTable(
    my_train,
    use_exmple_question=True,
    save_flow_graph=True
  )
  ```

- **自动选择分组的智能体：**

  ```
  agent_2 = Text2SqlAgentAutoSelectAspect(
    my_train,
    use_exmple_question=True,
    save_flow_graph=True
  )
  ```

### 4. 使用智能体生成 SQL 或直接查询

你可以使用智能体进行查询或生成 SQL 语句：

```
python复制编辑# 使用智能体直接查询
result = agent_1.ask("查询有哪些歌手")
print("查询结果:", result)

# 生成 SQL 语句
sql_query = agent_1.generate_sql(input="查询有哪些歌手")
print("生成的 SQL:", sql_query)
```

---

## 完整代码案例 | Complete Example

以下是一个完整示例，展示如何配置、构建训练数据、创建智能体以及生成 SQL 查询：

```
python复制编辑from your_package import (
    ChromaDB_VectorStore,
    Text2SqlAgentAutoSelectTable,
    Text2SqlAgentAutoSelectAspect
)

def main():
    # 配置 PostgreSQL 数据库
    config = {
      "train_data_directory": "./train_data/",
      "excel_filename": "train_data.xlsx",
      "db_config": {
        "dialect": "postgresql",
        "host": "ddnscd.gis-data.cn",
        "port": "7435",
        "database": "AItest4",
        "username": "postgres",
        "password": "pg@gisdata"
      },
      "model_name": "qwen-plus",
      "openai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "openai_api_key": "sk-3b127055020546ba973a8d0923e68a53"
    }

    # 初始化训练模型并构建训练数据
    my_train = ChromaDB_VectorStore(config=config)
    my_train.build_tabel_schema_train_data_from_conn()   # 获取表结构
    my_train.build_grouped_tables()                        # 自动分组表
    my_train.build_train_data_from_excel("train_data.xlsx")  # 从 Excel 加载训练数据
    my_train.build_question_sql_train_data()               # 添加 question-SQL 案例
    my_train.build_documentation_table_train_data()        # 添加表文档信息
    my_train.build_documentation_train_data()              # 添加生成 SQL 的文档说明

    # 创建智能体（这里以自动选择表的智能体为例）
    agent = Text2SqlAgentAutoSelectTable(
      my_train,
      use_exmple_question=True,
      save_flow_graph=True
    )

    # 使用智能体进行查询和生成 SQL
    query = "查询有哪些歌手"
    result = agent.ask(query)
    print("查询结果:", result)
    sql_query = agent.generate_sql(input=query)
    print("生成的 SQL:", sql_query)

if __name__ == "__main__":
    main()
```

## 快速上手指南 | Quick Start Guide

1. **下载代码或克隆仓库**
   将代码克隆到本地或下载最新版本。

2. **安装依赖**
   使用以下命令安装所有依赖：

   ```
   bash


   复制编辑
   pip install -r requirements.txt
   ```

3. **准备数据**

   - 修改配置文件（或在代码中定义 `config`），选择适合的数据库类型（PostgreSQL 或 SQLite）。
   - 准备 Excel 文件（例如 `train_data.xlsx`），确保数据格式符合示例要求。

4. **运行示例代码**
   运行完整代码案例，查看查询结果和生成的 SQL 语句。

5. **调试与扩展**
   根据需要调整智能体参数或自定义表分组，进一步优化 SQL 生成策略。

---

## 常见问题 | FAQ

- **如何更新训练数据？**
  修改 Excel 文件后，重新运行训练数据构建步骤即可更新数据。
- **如何调整 SQL 生成策略？**
  你可以修改智能体的参数或直接调整表的分组配置，以帮助大模型更好地理解数据库结构。
- **如何生成流程图？**
  设置 `save_flow_graph=True` 后，流程图将保存到指定路径，便于直观展示模型处理流程。

---

## 贡献 | Contributing

欢迎大家对本项目进行改进或提出建议。请通过 GitHub 提交 Issue 或 Pull Request，共同完善该项目。

---

## 许可 | License

本项目采用 [MIT 许可证](LICENSE)。
This project is licensed under the MIT License.

---

## 联系方式 | Contact

如果在使用过程中遇到问题或有任何疑问，请通过 GitHub Issues 或邮件与我们联系。
