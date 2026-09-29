"""Проверка решения backend: модель не может отменить сомнение retrieval или выдумать источник."""

import unittest
from unittest.mock import Mock, patch

from app.answers import AnswerDraft, AnswerService, decide_answer
from app.config import Settings
from app.evidence import evaluate_evidence


def retrieval(distance: float = 0.7, bm25: float | None = 3.0) -> dict:
    chunk = {"snippet_id": 42, "document_id": 7, "title": "Регламент", "text": "Отпуск согласуется за 14 дней."}
    return {
        "question": "Когда согласуют отпуск?",
        "semantic": [{**chunk, "cosine_distance": distance, "rank": 1}],
        "lexical": [{**chunk, "bm25_score": bm25, "rank": 1}] if bm25 is not None else [],
        "results": [{**chunk, "rrf_score": 0.03}],
    }


class EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings()

    def test_approved_thresholds_and_missing_lexical(self) -> None:
        self.assertEqual(evaluate_evidence(retrieval(), self.settings).level, "strong")
        self.assertEqual(evaluate_evidence(retrieval(distance=0.81), self.settings).level, "weak")
        self.assertEqual(evaluate_evidence(retrieval(bm25=1.0), self.settings).level, "weak")
        self.assertEqual(evaluate_evidence(retrieval(bm25=None), self.settings).level, "weak")

    def test_model_cannot_invent_source(self) -> None:
        draft = AnswerDraft(answer="Выдуманный ответ", source_ids=[999], confidence=0.99, insufficient_evidence=False)
        result = decide_answer(retrieval(), draft, self.settings)
        self.assertTrue(result["needs_review"])
        self.assertEqual(result["sources"], [])
        self.assertNotEqual(result["answer"], draft.answer)

    def test_backend_builds_quote_from_chunk(self) -> None:
        draft = AnswerDraft(answer="За 14 дней.", source_ids=[42], confidence=0.9, insufficient_evidence=False)
        result = decide_answer(retrieval(), draft, self.settings)
        self.assertFalse(result["needs_review"])
        self.assertEqual(result["sources"][0]["quote"], "Отпуск согласуется за 14 дней.")

    def test_low_confidence_and_model_doubt_force_review(self) -> None:
        draft = AnswerDraft(answer="Ответ", source_ids=[42], confidence=0.6, insufficient_evidence=False)
        self.assertTrue(decide_answer(retrieval(), draft, self.settings)["needs_review"])
        draft.confidence = 0.9
        draft.insufficient_evidence = True
        self.assertTrue(decide_answer(retrieval(), draft, self.settings)["needs_review"])

    @patch("app.answers.retrieve")
    def test_weak_retrieval_skips_model(self, mocked_retrieve: Mock) -> None:
        mocked_retrieve.return_value = retrieval(bm25=None)
        model = Mock()
        service = AnswerService(None, None, None, model, self.settings)
        result = service.ask("Когда согласуют отпуск?")
        self.assertTrue(result["needs_review"])
        model.generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
