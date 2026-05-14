"""
Vector DB 저장소 모듈

역할:
- Pinecone index 연결
- Document chunking
- embedding 후 upsert
- namespace를 사용하지 않고 metadata filtering 기반으로 저장
- metadata filter 기반 similarity search 제공
"""

import hashlib
import os
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

load_dotenv()


DEFAULT_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "finance-dot-news")
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small",
)
DEFAULT_DIMENSION = 1536


def get_pinecone_client():
    api_key = os.getenv("PINECONE_API_KEY")

    if not api_key:
        raise RuntimeError("PINECONE_API_KEY가 설정되지 않았습니다.")

    return Pinecone(api_key=api_key)


def ensure_pinecone_index(
    index_name: str = DEFAULT_INDEX_NAME,
    dimension: int = DEFAULT_DIMENSION,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
):
    pc = get_pinecone_client()

    existing_indexes = [index.name for index in pc.list_indexes()]

    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(
                cloud=cloud,
                region=region,
            ),
        )

    return pc.Index(index_name)


def get_embeddings():
    return OpenAIEmbeddings(
        model=DEFAULT_EMBEDDING_MODEL,
    )


def get_vector_store(index_name: str = DEFAULT_INDEX_NAME):
    ensure_pinecone_index(index_name=index_name)

    embeddings = get_embeddings()

    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
    )


def build_text_splitter(
    chunk_size: int = 700,
    chunk_overlap: int = 100,
):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )


def _build_document_id(document: Document, chunk_index: int):
    metadata = document.metadata or {}

    raw_id = "|".join([
        str(metadata.get("data_type", "")),
        str(metadata.get("stock_code", "")),
        str(metadata.get("company_name", "")),
        str(metadata.get("source_url", "")),
        str(metadata.get("date", "")),
        document.page_content[:100],
    ])

    base_id = hashlib.md5(raw_id.encode("utf-8")).hexdigest()

    return f"{base_id}_{chunk_index}"


def split_documents(documents: List[Document]):
    splitter = build_text_splitter()

    return splitter.split_documents(documents)


def build_chunk_ids(chunks: List[Document]):
    ids = []

    for index, chunk in enumerate(chunks):
        ids.append(_build_document_id(chunk, index))

    return ids


def upsert_documents(
    documents: List[Document],
    index_name: str = DEFAULT_INDEX_NAME,
):
    if not documents:
        return {
            "status": "skip",
            "message": "적재할 document가 없습니다.",
            "count": 0,
        }

    vector_store = get_vector_store(index_name=index_name)

    chunks = split_documents(documents)
    ids = build_chunk_ids(chunks)

    if not chunks:
        return {
            "status": "skip",
            "message": "chunk 생성 결과가 없습니다.",
            "count": 0,
        }

    vector_store.add_documents(
        documents=chunks,
        ids=ids,
    )

    return {
        "status": "success",
        "message": "Vector DB 적재 완료",
        "count": len(chunks),
        "index_name": index_name,
    }


def similarity_search(
    query: str,
    metadata_filter: Optional[Dict[str, Any]] = None,
    k: int = 5,
    index_name: str = DEFAULT_INDEX_NAME,
):
    vector_store = get_vector_store(index_name=index_name)

    return vector_store.similarity_search(
        query=query,
        k=k,
        filter=metadata_filter or {},
    )


def similarity_search_with_score(
    query: str,
    metadata_filter: Optional[Dict[str, Any]] = None,
    k: int = 5,
    index_name: str = DEFAULT_INDEX_NAME,
):
    vector_store = get_vector_store(index_name=index_name)

    return vector_store.similarity_search_with_score(
        query=query,
        k=k,
        filter=metadata_filter or {},
    )