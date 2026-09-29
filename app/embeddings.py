"""Тонкий LangChain adapter к REST embeddings Yandex AI Studio."""

import httpx
from langchain_core.embeddings import Embeddings

from app.config import Settings


class EmbeddingError(RuntimeError):
    """Внешний сервис не вернул пригодный вектор; подробности не раскрывают ключ."""


class YandexEmbeddings(Embeddings):
    def __init__(self, settings: Settings):
        self.settings = settings

    def _embed(self, text: str, model_uri: str) -> list[float]:
        if not self.settings.yandex_folder_id or not self.settings.yandex_api_key:
            raise EmbeddingError("Не настроены YANDEX_FOLDER_ID и YANDEX_API_KEY")
        try:
            response = httpx.post(
                self.settings.embeddings_url,
                headers={"Authorization": f"Api-Key {self.settings.yandex_api_key}"},
                json={"modelUri": model_uri, "text": text},
                timeout=30,
            )
            response.raise_for_status()
            vector = [float(value) for value in response.json()["embedding"]]
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
            raise EmbeddingError("Yandex embeddings недоступны или вернули некорректный ответ") from exc
        if len(vector) != 256:
            raise EmbeddingError("Размер embedding не равен 256; проверьте модель")
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text, self.settings.doc_embedding_model) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, self.settings.query_embedding_model)
