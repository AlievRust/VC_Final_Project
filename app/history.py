"""Снимки ответов и аудит основных операций в PostgreSQL."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import AuditRun, QaRun


class HistoryService:
    def __init__(self, sessions: sessionmaker[Session]):
        self.sessions = sessions

    def record_question(self, question: str, result: dict[str, Any]) -> int:
        """Ответ и событие аудита записываются одной транзакцией."""
        with self.sessions.begin() as session:
            run = QaRun(
                question=question,
                answer=result["answer"],
                sources=result["sources"],
                needs_review=result["needs_review"],
                review_reason=result["review_reason"],
                diagnostics=result["diagnostics"],
            )
            session.add(run)
            session.flush()
            session.add(AuditRun(action="question.asked", entity_id=run.id, details={"needs_review": run.needs_review}))
            return run.id

    def questions(self, needs_review: bool | None = None, limit: int = 50) -> list[QaRun]:
        query = select(QaRun).order_by(QaRun.created_at.desc(), QaRun.id.desc()).limit(limit)
        if needs_review is not None:
            query = query.where(QaRun.needs_review == needs_review)
        with self.sessions() as session:
            return list(session.scalars(query).all())

    def audit(self, limit: int = 50) -> list[AuditRun]:
        with self.sessions() as session:
            return list(session.scalars(select(AuditRun).order_by(AuditRun.created_at.desc(), AuditRun.id.desc()).limit(limit)).all())


def qa_data(run: QaRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "created_at": run.created_at.isoformat(),
        "question": run.question,
        "answer": run.answer,
        "sources": run.sources,
        "needs_review": run.needs_review,
        "review_reason": run.review_reason,
        "diagnostics": run.diagnostics,
    }


def audit_data(run: AuditRun) -> dict[str, Any]:
    return {"id": run.id, "created_at": run.created_at.isoformat(), "action": run.action, "entity_id": run.entity_id, "details": run.details}
