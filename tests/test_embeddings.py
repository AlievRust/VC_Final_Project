"""Проверка границы Yandex API без сетевого вызова и реального ключа."""

import unittest
from unittest.mock import Mock, patch

from app.config import Settings
from app.embeddings import EmbeddingError, YandexEmbeddings


class YandexEmbeddingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            yandex_folder_id="folder",
            yandex_api_key="test-key",
            doc_embedding_model="emb://folder/text-search-doc/latest",
            query_embedding_model="emb://folder/text-search-query/latest",
        )

    @patch("app.embeddings.httpx.post")
    def test_document_and_query_use_different_models(self, post: Mock) -> None:
        response = Mock()
        response.json.return_value = {"embedding": [0.1] * 256}
        post.return_value = response
        adapter = YandexEmbeddings(self.settings)
        self.assertEqual(len(adapter.embed_documents(["текст"])[0]), 256)
        self.assertEqual(len(adapter.embed_query("вопрос")), 256)
        self.assertEqual(post.call_args_list[0].kwargs["json"]["modelUri"], self.settings.doc_embedding_model)
        self.assertEqual(post.call_args_list[1].kwargs["json"]["modelUri"], self.settings.query_embedding_model)
        self.assertEqual(post.call_args_list[0].kwargs["headers"]["Authorization"], "Api-Key test-key")

    @patch("app.embeddings.httpx.post")
    def test_wrong_dimension_is_rejected(self, post: Mock) -> None:
        response = Mock()
        response.json.return_value = {"embedding": [0.1] * 3}
        post.return_value = response
        with self.assertRaises(EmbeddingError):
            YandexEmbeddings(self.settings).embed_query("вопрос")


if __name__ == "__main__":
    unittest.main()
