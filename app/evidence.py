"""Детерминированная оценка retrieval по утверждённой политике P-01."""

from dataclasses import dataclass
from typing import Any

from app.config import Settings


@dataclass(frozen=True)
class Evidence:
    level: str
    reason: str | None
    snippet_id: int | None
    cosine_distance: float | None
    bm25_score: float | None

    def diagnostics(self, settings: Settings) -> dict[str, Any]:
        return {
            "level": self.level,
            "top_snippet_id": self.snippet_id,
            "cosine_distance": self.cosine_distance,
            "bm25_score": self.bm25_score,
            "max_cosine_distance": settings.evidence_max_cosine_distance,
            "min_bm25_score": settings.evidence_min_bm25_score,
        }


def evaluate_evidence(retrieval: dict[str, Any], settings: Settings) -> Evidence:
    """Только первый RRF-фрагмент может открыть путь к ответу без review."""
    results = retrieval["results"]
    if not results:
        return Evidence("none", "В базе знаний нет подходящих фрагментов", None, None, None)

    snippet_id = results[0]["snippet_id"]
    semantic = next((item for item in retrieval["semantic"] if item["snippet_id"] == snippet_id), None)
    lexical = next((item for item in retrieval["lexical"] if item["snippet_id"] == snippet_id), None)
    distance = float(semantic["cosine_distance"]) if semantic else None
    bm25 = float(lexical["bm25_score"]) if lexical else None
    if semantic is None or lexical is None:
        reason = "Первый фрагмент не подтверждён одновременно семантическим и лексическим поиском"
    elif distance > settings.evidence_max_cosine_distance:
        reason = "Семантическое расстояние до первого фрагмента слишком велико"
    elif bm25 < settings.evidence_min_bm25_score:
        reason = "Лексическое совпадение первого фрагмента недостаточно"
    else:
        return Evidence("strong", None, snippet_id, distance, bm25)
    return Evidence("weak", reason, snippet_id, distance, bm25)
