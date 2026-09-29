"""Настройки, влияющие на разбиение и поиск, собраны в одном месте."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = "postgresql+psycopg://kb:kb@db:5432/kb"
    yandex_folder_id: str = ""
    yandex_api_key: str = ""
    embeddings_url: str = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
    doc_embedding_model: str = ""
    query_embedding_model: str = ""
    chunk_size: int = 1000
    chunk_overlap: int = 150
    vector_top_k: int = 5
    bm25_top_k: int = 5
    fusion_top_k: int = 5
    rrf_k: int = 60
    max_document_chars: int = 100_000

    @classmethod
    def from_env(cls) -> "Settings":
        folder = os.getenv("YANDEX_FOLDER_ID", "")
        result = cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            yandex_folder_id=folder,
            yandex_api_key=os.getenv("YANDEX_API_KEY", ""),
            embeddings_url=os.getenv("YANDEX_EMBEDDINGS_URL", cls.embeddings_url),
            doc_embedding_model=os.getenv("YANDEX_DOC_EMBEDDING_MODEL") or f"emb://{folder}/text-search-doc/latest",
            query_embedding_model=os.getenv("YANDEX_QUERY_EMBEDDING_MODEL") or f"emb://{folder}/text-search-query/latest",
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
            vector_top_k=int(os.getenv("VECTOR_TOP_K", "5")),
            bm25_top_k=int(os.getenv("BM25_TOP_K", "5")),
            fusion_top_k=int(os.getenv("FUSION_TOP_K", "5")),
            rrf_k=int(os.getenv("RRF_K", "60")),
        )
        if result.chunk_size < 8 or not 0 <= result.chunk_overlap <= result.chunk_size - 3:
            raise ValueError("CHUNK_SIZE должен быть не меньше 8, а CHUNK_OVERLAP — меньше CHUNK_SIZE на 3")
        if min(result.vector_top_k, result.bm25_top_k, result.fusion_top_k, result.rrf_k) < 1:
            raise ValueError("Параметры top-K и RRF_K должны быть положительными")
        return result
