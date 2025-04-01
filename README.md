## RAG Training SQL Generator

本项目提供一套基于 RAG 思想的 SQL 生成训练流程，通过训练问答数据自动构造 SQL 查询。利用 ChromaDB 作为向量存储，并结合多个智能体实现表选择和表分组，从而支持多种数据库配置（例如 PostgreSQL 和 SQLite），并通过 Excel 文件自动构建训练数据。

This project provides a RAG-based training framework for generating SQL queries. By training on question-SQL pairs, it automatically constructs SQL queries. Using ChromaDB as the vector store and multiple agents (for table selection and table grouping), this package supports multiple database configurations (e.g., PostgreSQL and SQLite) and automatically builds training data from an Excel file.

---

## 特性 | Features

- **多数据库支持**
  支持 PostgreSQL、SQLite 等多种数据库配置。(基于 SQLAlchemy)
- **自动训练数据构建**
  - 自动获取数据库表结构并构建向量训练模型。
  - 按照表结构自动分组（支持智能体自动选择）。
  - 从 Excel 文件中加载 question-SQL 训练数据。
  - 添加辅助大模型生成 SQL 的文档说明（针对表结构与查询策略）。
- **智能体生成 SQL**
  提供两个智能体：
  - `Text2SqlAgentAutoSelectTable`：自动选择相关表，提取表的 DDL 信息，再结合文档信息生成 SQL。
  - `Text2SqlAgentAutoSelectAspect`：通过表分组信息，进一步提升 SQL 生成的准确性。
- **流程图绘制**
  支持生成训练流程的图形化展示，帮助用户直观理解模型处理流程。
- **大规模数据库适配**
  针对上百张表的数据库，优化表结构匹配和文档信息的传递，提高 SQL 生成的精确度和效率。

---

## 安装 | Installation

确保你已安装 Python 3.6 或更高版本。使用 pip 安装（请将 `your-package-name` 替换为你实际发布的包名）：

```
bash
pip install opentext2sql
```

---

## 使用方法 | Usage

### 1. 定义配置文件

根据数据库类型定义配置，例如：

- **PostgreSQL 配置：**

  ```
  config = {
    "train_data_directory": "./train_data/",
    "excel_filename": "train_data.xlsx",
    "db_config": {
      "dialect": "postgresql",
      "host": host,
      "port": port,
      "database": database,
      "username": username,
      "password": password
    },
    "model_name": model_name,
    "openai_api_base": openai_api_base,
    "openai_api_key": openai_api_key
  }
  ```

- **SQLite 配置：**

  ```
  config = {
    "train_data_directory": "./train_data/",
    "excel_filename": "train_data.xlsx",
    "db_config": {
      "dialect": "sqlite",
      "database": "my_database.db"
    },
    "model_name": model_name,
    "openai_api_base": openai_api_base,
    "openai_api_key": openai_api_key
  }
  ```

### 2. 创建训练模型并构建训练数据

利用配置初始化训练模型，并构建训练数据：

```
python复制编辑my_train = ChromaDB_VectorStore(config=config)

# 自动构建训练数据
my_train.build_tabel_schema_train_data_from_conn()   # 获取表结构（必须）
my_train.build_grouped_tables()                        # 将表按照类别分组（用于 Text2SqlAgentAutoSelectAspect）
my_train.build_train_data_from_excel("train_data.xlsx")  # 从 Excel 加载 question-SQL 训练数据
my_train.build_question_sql_train_data("question","sql")               # 添加 question-SQL 案例
my_train.build_documentation_table_train_data("doc")        # 添加表和分组类型的文档信息
my_train.build_documentation_train_data("doc")              # 添加生成 SQL 的文档说明
```

Excel 文件示例：

| id  | question          | sql                               |
| --- | ----------------- | --------------------------------- |
| 1   | 查询某个项目中的… | SELECT … FROM … JOIN … GROUP BY … |

### 3. 创建智能体

根据训练模型创建两个智能体，用于自动生成 SQL：

- **自动选择表的智能体：**

  ```
  python复制编辑agent_1 = Text2SqlAgentAutoSelectTable(
    my_train,
    use_exmple_question=True,
    save_flow_graph=True
  )
  ```

- **自动选择分组的智能体：**

  ```
  python复制编辑agent_2 = Text2SqlAgentAutoSelectAspect(
    my_train,
    use_exmple_question=True,
    save_flow_graph=True
  )
  ```

### 4. 使用智能体生成 SQL 或直接查询

```
# 使用智能体直接查询
result = agent_1.ask("查询有哪些歌手")
print("查询结果:", result)

# 生成 SQL 语句
sql_query = agent_1.generate_sql(input="查询有哪些歌手")
print("生成的 SQL:", sql_query)
```

---

## 实现的技术路线 | Technical Approach

本项目的设计理念是在 vanna 技术的基础上进行升级，同时参考 chat2db 的思路，从而更好地应对大规模数据库的 SQL 查询需求。具体技术路线和创新点如下：

1. **基于向量训练模型构建知识库**
   - **数据内容：** 向量库中包含数据库表结构（DDL）、文档信息以及问答案例（仅存储案例问题，不存储 SQL）。
   - **文档分离：** 为提高大模型的提示效果，项目中将文档信息分为两个独立向量库：
     - 帮助选表的文档
     - 帮助生成 SQL 的文档
2. **智能体工作流中的多节点信息利用**
   - **第一智能体：表匹配与 SQL 生成**
     - 首先，利用向量匹配获取与用户问题最相似的案例问题。
     - 如果匹配到相似案例，则按照该案例所对应的表结构和相关文档信息生成 SQL；
     - 如果未匹配到足够相似的案例，则大模型自主判断并定位问题对应的表，同时借助文档提示信息，使用匹配到的表结构（DDL）生成 SQL。
     - 另外，案例问题与 SQL 的关联存储在独立的 JSON 文件中，可提升向量匹配的准确性和追溯性。
   - **第二智能体：表分类与智能筛选**
     - 采用表分组策略，先由大模型判断用户问题所属的业务类别，再获取对应分类下的表结构（DDL）。
     - 用户可以选择使用自动分类工具对数据库中的表进行分组，或上传自定义的专业业务分类方式，灵活适配不同业务场景。
3. **与现有方案的对比**
   - **vanna 路线**
     - **原理：** 先匹配用户问题的相似向量内容（DDL、文档、question-sql），将所有内容一次性传递给大模型生成 SQL。
     - **不足：** 匹配的 DDL 和 question-sql 可能不够精准；在拥有上百张表的数据库中，很难准确匹配到对应表的结构信息。
   - **chat2db 路线**
     - **原理：** 先根据用户问题提取相关表名及对应的 DDL，再传递给大模型生成 SQL。
     - **不足：** 在大规模数据库中，同样难以精确匹配到正确的表结构。
   - **本项目优势**
     - **灵活信息利用：** 通过在智能体工作流的不同节点使用向量匹配到的信息，先判断案例问题的匹配情况，再动态选择最合适的生成策略。
     - **文档信息精细划分：** 分别为选表和生成 SQL 提供专用文档提示，提高生成准确性。
     - **大规模数据库适应性：** 采用表分组及智能筛选策略，能够更好地处理上百张表的复杂数据库场景。
     - **企业级定制：** 既支持直接查询（类似 chat2db 的应用场景，如电商数据分析），又支持基于训练的专业开发（类似 vanna 的定制化需求）。

---

## 完整代码案例 | Complete Example

```
from opentext2sql.agent.create_agent import Text2SqlAgentAutoSelectTable, Text2SqlAgentAutoSelectAspect
from opentext2sql.chroma.chromadb_vector import ChromaDB_VectorStore

def main():
    # 配置 PostgreSQL 数据库
    config = {
      "train_data_directory": "./train_data/",
      "excel_filename": "train_data.xlsx",
      "db_config": {
        "dialect": "postgresql",
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password
      },
      "model_name": model_name,
      "openai_api_base": openai_api_base,
      "openai_api_key": openai_api_key
    }

    # 初始化训练模型并构建训练数据
    my_train = ChromaDB_VectorStore(config=config)
    my_train.build_tabel_schema_train_data_from_conn()   # 获取表结构
    my_train.build_grouped_tables()                        # 自动分组表
    # 可选训练内容 可以不添加
    my_train.build_train_data_from_excel("train_data.xlsx")  # 从 Excel 加载训练数据
    my_train.build_question_sql_train_data("question","sql")               # 添加 question-SQL 案例
    my_train.build_documentation_table_train_data("doc")        # 添加表和分组类型的文档信息
    my_train.build_documentation_train_data("doc")              # 添加生成 SQL 的文档说明

    # 创建智能体（以自动选择表的智能体为例）
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

---

1. ## 快速上手指南 | Quick Start Guide

   1. **获取代码**

      - **通过 pip 安装：**
        如果项目已发布至 PyPI，可以直接运行：

        ```
        pip install opentext2sql
        ```

      - **或克隆仓库：**
        将代码克隆到本地或下载最新版本：

        ```
        git clone https://github.com/iooo2333/opentext2sql.git
        cd opentext2sql
        ```

   2. **安装依赖**

      - **pip 安装：**
        使用 pip 安装时，依赖会自动处理。

      - **克隆仓库后：**
        运行以下命令安装所有依赖：

        ```
        pip install -r requirements.txt
        ```

   3. **准备数据**

      - 修改配置文件（或在代码中定义 `config`），选择适合的数据库类型（例如 PostgreSQL 或 SQLite）。
      - 准备 Excel 文件（例如 `train_data.xlsx`），确保数据格式符合示例要求。

   4. **运行示例代码**

      - 运行完整代码案例，查看查询结果和生成的 SQL 语句。

   5. **调试与扩展**

      - 根据需要调整智能体参数或自定义表分组，进一步优化 SQL 生成策略。

---

## 常见问题 | FAQ

- **如何更新训练数据？**
  修改 Excel 文件后，删除训练数据库，重新运行训练数据构建步骤即可更新数据。
- **如何调整 SQL 生成策略？**
  可选择不同的智能体，或调整表的分组配置，以帮助大模型更好地理解数据库结构。
- **如何生成流程图？**
  设置 `save_flow_graph=True` 后，流程图将自动保存到指定路径，直观展示模型处理流程。

---

## 后续更新计划

项目未来将陆续添加以下功能和改进：

1. **前端页面制作**
   制作易于使用的前端页面，使非专业开发人员也能直接连接数据库、生成 SQL 并查询数据，满足数据分析需求或后端 SQL 编写等场景。
2. **更新英文提示词的大模型**
   针对 ChatGPT、Claude 等英语模型优化提示词，使其在生成 SQL 和处理数据库查询时表现更佳。
3. **增加检查节点功能**
   提供可选的检查节点功能，帮助用户在执行查询失败后对关键步骤或数据进行校验，重新生成 sql。
4. **基于向量数据训练模型**
   利用现有的向量数据训练模型，设计更多专注于数据库查询的智能体，尝试不同可能。
5. **测试更多数据库连接**
   扩展项目的数据库连接测试范围，确保支持更多类型的数据库，并提高兼容性与稳定性。
6. **增加更多向量数据库支持**
   除了传统关系型数据库，未来将添加对更多向量数据库的支持，以满足不断变化的数据存储与检索需求。

## 贡献 | Contributing

欢迎大家对本项目进行改进或提出建议。请通过 GitHub 提交 Issue 或 Pull Request，共同完善该项目。

---

## 许可 | License

本项目采用 [MIT 许可证](LICENSE)。
This project is licensed under the MIT License.

---

## 联系方式 | Contact

如果在使用过程中遇到问题或有任何疑问，请通过 GitHub Issues 或邮件1766980815@qq.com与我们联系。

如果你认为这个项目有价值，或者也想为这个项目提供支持，请联系我们，谢谢。
