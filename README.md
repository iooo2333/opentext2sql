<!-- en -->

# RAG Training SQL Generator

This project provides a RAG-based training framework for generating SQL queries. By training on question-SQL pairs, it automatically constructs SQL queries. Using ChromaDB as the vector store and multiple agents (for table selection and table grouping), this package supports multiple database configurations (e.g., PostgreSQL and SQLite) and automatically builds training data from an Excel file.

---

![Flowchart](/assets/flow.png)

## Quick Start

```
pip install opentext2sql
```

```
from opentext2sql.easy_start import start
start()
```

Then open [http://localhost:3000](http://localhost:3000/)
![App Screenshot](/assets/app.jpg)

## Features

- **Multi-Database Support**
  Supports PostgreSQL, SQLite, and other database configurations (based on SQLAlchemy).
- **Automatic Training Data Construction**
  - Automatically retrieves database table schemas and builds vector training models.
  - Groups tables by schema (supports agent-based automatic selection).
  - Loads question-SQL training data from Excel files.
  - Adds auxiliary documentation to assist LLMs in generating SQL (covering table structures and query strategies).
- **Agent-Based SQL Generation**
  Provides two agents:
  - `Text2SqlAgentAutoSelectTable`: Automatically selects relevant tables, extracts DDL information, and combines it with documentation to generate SQL.
  - `Text2SqlAgentAutoSelectAspect`: Improves SQL generation accuracy using table grouping information.
- **Flowchart Visualization**
  Generates graphical representations of the training workflow for intuitive understanding.
- **Large-Scale Database Adaptation**
  Optimized for databases with hundreds of tables, improving schema matching and documentation efficiency for precise SQL generation.

---

## Installation

Ensure Python 3.6+ is installed. Install via pip:

```
pip install opentext2sql
```

---

## Usage

### 1. Define Configuration

Configure based on your database type:

- **PostgreSQL Configuration:**

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

- **SQLite Configuration:**

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

### 2. Initialize Training Model and Build Data

```
my_train = ChromaDB_VectorStore(config=config)

# Build training data
my_train.build_tabel_schema_train_data_from_conn()   # Fetch table schemas (required)
my_train.build_grouped_tables()                      # Group tables by category (for Text2SqlAgentAutoSelectAspect)
my_train.build_train_data_from_excel("train_data.xlsx")  # Load question-SQL pairs from Excel
my_train.build_question_sql_train_data("question", "sql")  # Add question-SQL examples
my_train.build_documentation_table_train_data("doc")  # Add table/group documentation
my_train.build_documentation_train_data("doc")        # Add SQL generation guidelines
```

Excel Example:

| id  | question            | sql                               |
| :-- | :------------------ | :-------------------------------- |
| 1   | Query artists in... | SELECT … FROM … JOIN … GROUP BY … |

### 3. Create Agents

```
# Agent for auto table selection
agent_1 = Text2SqlAgentAutoSelectTable(
  my_train,
  use_exmple_question=True,
  save_flow_graph=True
)

# Agent for auto aspect selection
agent_2 = Text2SqlAgentAutoSelectAspect(
  my_train,
  use_exmple_question=True,
  save_flow_graph=True
)
```

### 4. Generate SQL or Execute Queries

```
# Direct query
result = agent_1.ask("List all artists")
print("Result:", result)

# Generate SQL
sql_query = agent_1.generate_sql(input="List all artists")
print("Generated SQL:", sql_query)
```

---

## Technical Approach

This project enhances the Vanna framework while incorporating Chat2DB's ideas to better handle large-scale database queries:

1. **Vector-Based Knowledge Base**
   - Stores table DDLs, documentation, and question examples (excluding SQL).
   - Separates documentation into two vector stores:
     - Table selection guidelines
     - SQL generation guidelines
2. **Multi-Stage Agent Workflow**
   - **Agent 1: Table Matching & SQL Generation**
     - Matches user questions to similar examples.
     - Uses matched DDLs/docs for SQL generation; falls back to LLM judgment if no close match exists.
   - **Agent 2: Table Grouping & Filtering**
     - Classifies questions by business aspect before fetching relevant DDLs.
3. **Advantages Over Alternatives**
   - **Vanna**: Prone to inaccurate DDL/question-SQL matches in large databases.
   - **Chat2DB**: Struggles with precise table selection at scale.
   - **This Project**:
     - Dynamically combines matched examples and LLM judgment.
     - Dedicated documentation for each workflow stage.
     - Handles 100+ table databases via smart grouping.

---

## Complete Example

```
from opentext2sql.agent.create_agent import Text2SqlAgentAutoSelectTable, Text2SqlAgentAutoSelectAspect
from opentext2sql.chroma.chromadb_vector import ChromaDB_VectorStore

def main():
    # PostgreSQL config
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

    # Initialize training
    my_train = ChromaDB_VectorStore(config=config)
    my_train.build_tabel_schema_train_data_from_conn()
    my_train.build_grouped_tables()
    my_train.build_train_data_from_excel("train_data.xlsx")

    # Create agent
    agent = Text2SqlAgentAutoSelectTable(my_train, use_exmple_question=True)

    # Query
    print(agent.ask("List artists"))

if __name__ == "__main__":
    main()
```

---

## Quick Start Guide

1. **Install**

   ```
   pip install opentext2sql
   ```

2. **Prepare Data**

   - Configure `config` for your database.
   - Prepare Excel file (e.g., `train_data.xlsx`).

3. **Run**
   Execute the example code to test SQL generation.

---

## FAQ

- **Updating Training Data**: Delete the training DB and rerun data construction.
- **Tuning SQL Generation**: Switch agents or adjust table groupings.
- **Flowchart Generation**: Set `save_flow_graph=True`.

---

## Roadmap

1. Web UI for non-technical users.
2. Optimized prompts for English LLMs (ChatGPT/Claude).
3. Validation nodes for error recovery.
4. Vector-based model training.
5. Expanded database compatibility.
6. Additional vector database support.

## Contributing

Issues and PRs are welcome!

---

## License

MIT.

---

## Contact

GitHub Issues or email [1766980815@qq.com](https://mailto:1766980815@qq.com/).

Let us know if you'd like to support this project!
