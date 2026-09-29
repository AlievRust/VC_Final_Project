"""Синхронная загрузка документа: внешние вызовы до транзакции БД."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.chunking import chunk_text
from app.config import Settings
from app.embeddings import YandexEmbeddings
from app.models import AuditRun, Document, Snippet
from app.search import BM25Index


class DocumentValidationError(ValueError):
    """Ошибка пользовательского содержимого."""


def validate_document(title: str, text: str, settings: Settings) -> tuple[str, str]:
    title, text = title.strip(), text.strip()
    if not title or len(title) > 255:
        raise DocumentValidationError("Название должно содержать от 1 до 255 символов")
    if not text or len(text) > settings.max_document_chars:
        raise DocumentValidationError(f"Текст должен содержать от 1 до {settings.max_document_chars} символов")
    return title, text


class DocumentService:
    def __init__(self, sessions: sessionmaker[Session], settings: Settings, embeddings: YandexEmbeddings, index: BM25Index):
        self.sessions = sessions
        self.settings = settings
        self.embeddings = embeddings
        self.index = index

    def add(self, title: str, text: str) -> Document:
        title, text = validate_document(title, text, self.settings)
        chunks = chunk_text(text, self.settings.chunk_size, self.settings.chunk_overlap)
        vectors = self.embeddings.embed_documents(chunks)
        if len(vectors) != len(chunks):
            raise RuntimeError("Для части фрагментов не получены embeddings")
        # Новый BM25 строится до commit, но публикуется только после него.
        with self.index.lock:
            with self.sessions.begin() as session:
                document = Document(title=title, text=text)
                session.add(document)
                session.flush()
                session.add_all(Snippet(document_id=document.id, chunk_index=i, text=chunk, embedding=vector) for i, (chunk, vector) in enumerate(zip(chunks, vectors)))
                session.add(AuditRun(action="document.created", entity_id=document.id, details={"title": title, "chunks": len(chunks)}))
                session.flush()
                snapshot = self.index.build(session)
            self.index.publish(snapshot)
        return document

    def delete(self, document_id: int) -> bool:
        with self.index.lock:
            with self.sessions.begin() as session:
                document = session.get(Document, document_id)
                if document is None:
                    return False
                session.add(AuditRun(action="document.deleted", entity_id=document_id, details={"title": document.title}))
                session.delete(document)
                session.flush()
                snapshot = self.index.build(session)
            self.index.publish(snapshot)
        return True

    def list(self) -> list[Document]:
        with self.sessions() as session:
            return list(session.scalars(select(Document).order_by(Document.created_at.desc(), Document.id.desc())).all())

    def get(self, document_id: int) -> Document | None:
        with self.sessions() as session:
            return session.get(Document, document_id)
