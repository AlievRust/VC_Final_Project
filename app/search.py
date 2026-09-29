"""Независимые поиски BM25 и pgvector, затем объединение рангов RRF."""

from dataclasses import dataclass
import re
from threading import RLock

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.embeddings import YandexEmbeddings
from app.models import Document, Snippet


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


def rrf(rankings: list[list[int]], k: int) -> list[tuple[int, float]]:
    """Возвращает только итоговый порядок; значения RRF не являются confidence."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, snippet_id in enumerate(ranking, start=1):
            scores[snippet_id] = scores.get(snippet_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


@dataclass(frozen=True)
class IndexedSnippet:
    id: int
    document_id: int
    title: str
    text: str


class BM25Index:
    """Копия поискового текста из PostgreSQL; reload вызывается после commit."""

    def __init__(self) -> None:
        self.lock = RLock()
        self.rows: list[IndexedSnippet] = []
        self.engine: BM25Okapi | None = None

    @staticmethod
    def build(session: Session) -> tuple[list[IndexedSnippet], BM25Okapi | None]:
        """Готовит новый индекс из видимого в транзакции состояния БД."""
        records = session.execute(select(Snippet, Document.title).join(Document).order_by(Snippet.id)).all()
        rows = [IndexedSnippet(row.id, row.document_id, title, row.text) for row, title in records]
        engine = BM25Okapi([tokenize(row.text) or [""] for row in rows]) if rows else None
        return rows, engine

    def publish(self, snapshot: tuple[list[IndexedSnippet], BM25Okapi | None]) -> None:
        """Публикует индекс после успешного commit под общим lock."""
        self.rows, self.engine = snapshot

    def reload(self, sessions: sessionmaker[Session]) -> None:
        with self.lock, sessions() as session:
            self.publish(self.build(session))

    def search(self, query: str, limit: int) -> list[tuple[IndexedSnippet, float]]:
        tokens = tokenize(query)
        with self.lock:
            if not tokens or self.engine is None:
                return []
            scores = self.engine.get_scores(tokens)
            matching = [(i, float(score)) for i, score in enumerate(scores) if set(tokens) & set(tokenize(self.rows[i].text))]
            ranked = sorted(matching, key=lambda pair: (-pair[1], self.rows[pair[0]].id))
            return [(self.rows[i], score) for i, score in ranked[:limit]]


def retrieve(question: str, sessions: sessionmaker[Session], index: BM25Index, embeddings: YandexEmbeddings, settings: Settings) -> dict:
    """Диагностика CP3; здесь сознательно нет evidence threshold и генерации."""
    vector = embeddings.embed_query(question)
    distance = Snippet.embedding.cosine_distance(vector).label("distance")
    with index.lock:
        with sessions() as session:
            matches = session.execute(
                select(Snippet, Document.title, distance)
                .join(Document)
                .order_by(distance, Snippet.id)
                .limit(settings.vector_top_k)
            ).all()
        semantic = [
            {"snippet_id": snippet.id, "document_id": snippet.document_id, "title": title, "text": snippet.text, "cosine_distance": float(dist), "rank": rank}
            for rank, (snippet, title, dist) in enumerate(matches, 1)
        ]
        lexical = [
            {"snippet_id": row.id, "document_id": row.document_id, "title": row.title, "text": row.text, "bm25_score": score, "rank": rank}
            for rank, (row, score) in enumerate(index.search(question, settings.bm25_top_k), 1)
        ]
    fused = rrf([[row["snippet_id"] for row in semantic], [row["snippet_id"] for row in lexical]], settings.rrf_k)
    by_id = {row["snippet_id"]: row for row in semantic + lexical}
    results = [{"snippet_id": snippet_id, "document_id": by_id[snippet_id]["document_id"], "title": by_id[snippet_id]["title"], "text": by_id[snippet_id]["text"], "rrf_score": score} for snippet_id, score in fused[: settings.fusion_top_k]]
    return {"question": question, "semantic": semantic, "lexical": lexical, "results": results, "note": "RRF используется только для ранжирования; пороги evidence пока не утверждены"}
