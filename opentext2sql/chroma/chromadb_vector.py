import json
from typing import List
import uuid
import pandas as pd
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ..base.base import TrainModel


from typing import Union
import hashlib


def deterministic_uuid(content: Union[str, bytes]) -> str:
    """Creates deterministic UUID on hash value of string or byte content.

    Args:
        content: String or byte representation of data.

    Returns:
        UUID of the content.
    """
    if isinstance(content, str):
        content_bytes = content.encode("utf-8")
    elif isinstance(content, bytes):
        content_bytes = content
    else:
        raise ValueError(f"Content type {type(content)} not supported !")

    hash_object = hashlib.sha256(content_bytes)
    hash_hex = hash_object.hexdigest()
    namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
    content_uuid = str(uuid.uuid5(namespace, hash_hex))

    return content_uuid


class ChromaDB_VectorStore(TrainModel):

    def __init__(self, config=None):
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        TrainModel.__init__(self, config=config)
        if config is None:
            config = {}

        path = config.get("path", "./train_data")
        self.embedding_function = config.get("embedding_function", default_ef)
        curr_client = config.get("client", "persistent")
        collection_metadata = config.get("collection_metadata", None)
        self.n_results_question = config.get(
            "n_results_question", config.get("n_results", 10))
        self.n_results_documentation = config.get(
            "n_results_documentation", config.get("n_results", 10))
        self.n_results_documentation_doc = config.get(
            "n_results_documentation_doc", config.get("n_results", 10))

        if curr_client == "persistent":
            self.chroma_client = chromadb.PersistentClient(
                path=path, settings=Settings(
                    anonymized_telemetry=False, allow_reset=True),

            )
        elif curr_client == "in-memory":
            self.chroma_client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )
        elif isinstance(curr_client, chromadb.api.client.Client):
            # 允许直接提供客户端
            self.chroma_client = curr_client
        else:
            raise ValueError(
                f"Unsupported client was set in config: {curr_client}")

        #   创建数据库连接
        self.doc = self.chroma_client.get_or_create_collection(
            name="documentation",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        self.doc_table = self.chroma_client.get_or_create_collection(
            name="documentation_table",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )
        self.questions = self.chroma_client.get_or_create_collection(
            name="sql",
            embedding_function=self.embedding_function,
            metadata=collection_metadata,
        )

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding = self.embedding_function([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    @staticmethod
    def _extract_documents(query_results) -> list:
        if query_results is None:
            return []

        if "documents" in query_results:
            documents = query_results["documents"]

            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    return documents[0]

            return documents

    #   添加训练数据

    def build_documentation_train_data(self, documentation: str, **kwargs) -> str:
        self.add_documentation_train(documentation, self.documentation_file)
        id = deterministic_uuid(documentation) + "-doc"
        self.doc.add(
            documents=documentation,
            embeddings=self.generate_embedding(documentation),
            ids=id,
        )
        return id

    def build_documentation_table_train_data(self, documentation: str, **kwargs) -> str:
        self.add_documentation_train(
            documentation, self.documentation_table_file)
        id = deterministic_uuid(documentation) + "-doc-table"
        self.doc_table.add(
            documents=documentation,
            embeddings=self.generate_embedding(documentation),
            ids=id,
        )
        return id

    def build_question_sql_train_data(self, question: str, sql: str, **kwargs) -> str:
        self.add_question_sql_traindata(question, sql, self.sql_output_file)
        id = deterministic_uuid(question) + "-sql"
        self.questions.add(
            documents=question,
            embeddings=self.generate_embedding(question),
            ids=id,
        )
        return id

    def get_relate_question(self, question: str, **kwargs) -> list:
        emb = self.generate_embedding(question)
        return ChromaDB_VectorStore._extract_documents(
            self.questions.query(
                query_embeddings=[emb],
                n_results=self.n_results_question,
            )
        )

    def get_relate_doc(self, question: str, **kwargs) -> list:
        emb = self.generate_embedding(question)
        return ChromaDB_VectorStore._extract_documents(
            self.doc.query(
                query_embeddings=[emb],
                n_results=self.n_results_documentation,
            )
        )

    def get_relate_doc_table(self, question: str, **kwargs) -> list:
        emb = self.generate_embedding(question)
        return ChromaDB_VectorStore._extract_documents(
            self.doc_table.query(
                query_embeddings=[emb],
                n_results=self.n_results_documentation_doc,
            )
        )
