"""Локальная интеграционная проверка БД без вызова Yandex; удаляет свои данные."""

from uuid import uuid4

from sqlalchemy import func, select

from app.config import Settings
from app.db import create_session_factory
from app.documents import DocumentService
from app.models import AuditRun, Snippet
from app.search import BM25Index, retrieve


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        # Детерминированный вектор служит только для проверки SQL/жизненного цикла.
        vector = [0.0] * 256
        vector[0] = 1.0
        vector[1] = 1.0 if "отпуск" in text.lower() else 0.1
        return vector


def main() -> None:
    settings = Settings.from_env()
    sessions = create_session_factory(settings)
    index = BM25Index()
    index.reload(sessions)
    service = DocumentService(sessions, settings, FakeEmbeddings(), index)
    title = f"smoke-{uuid4().hex}"
    document = None
    try:
        document = service.add(title, "Заявку на отпуск подают за 14 дней.")
        with sessions() as session:
            assert session.scalar(select(func.count()).select_from(Snippet).where(Snippet.document_id == document.id)) == 1
        result = retrieve("Когда подают отпуск?", sessions, index, FakeEmbeddings(), settings)
        assert any(row["document_id"] == document.id for row in result["results"])
        assert index.search("отпуск", 5)
        print("Добавление, pgvector, BM25 и RRF: PASS")
    finally:
        if document is not None:
            assert service.delete(document.id)
            with sessions() as session:
                assert session.scalar(select(func.count()).select_from(Snippet).where(Snippet.document_id == document.id)) == 0
                assert session.scalar(select(func.count()).select_from(AuditRun).where(AuditRun.entity_id == document.id)) >= 2
            assert not any(row.document_id == document.id for row in index.rows)
            print("Каскадное удаление, перестройка BM25 и аудит: PASS")


if __name__ == "__main__":
    main()
