"""Проверки поиска без внешней модели и PostgreSQL."""

import unittest

from rank_bm25 import BM25Okapi

from app.chunking import chunk_text
from app.search import BM25Index, IndexedSnippet, rrf, tokenize


class ChunkingTests(unittest.TestCase):
    def test_natural_boundaries_and_size(self) -> None:
        text = "Первый короткий абзац.\n\nВторой абзац с более длинным пояснением.\n\nТретий абзац."
        chunks = chunk_text(text, 55, 8)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 55 for chunk in chunks))
        self.assertIn("Первый короткий абзац.", chunks[0])

    def test_long_word_split(self) -> None:
        chunks = chunk_text("а" * 90, 30, 5)
        self.assertTrue(all(len(chunk) <= 30 for chunk in chunks))
        self.assertGreater(len(chunks), 1)


class RankingTests(unittest.TestCase):
    def test_rrf_rewards_agreement(self) -> None:
        ranks = rrf([[1, 2], [2, 3]], 60)
        self.assertEqual(ranks[0][0], 2)
        self.assertEqual({row[0] for row in ranks}, {1, 2, 3})

    def test_bm25_returns_match_even_with_negative_idf(self) -> None:
        index = BM25Index()
        index.rows = [IndexedSnippet(1, 1, "Документ", "отпуск")]
        index.engine = BM25Okapi([tokenize("отпуск")])
        self.assertEqual(index.search("отпуск", 3)[0][0].id, 1)
        self.assertEqual(index.search("инцидент", 3), [])


if __name__ == "__main__":
    unittest.main()
