"""FastAPI routes для документов и прозрачной диагностики поиска CP3."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.config import Settings
from app.db import create_session_factory
from app.documents import DocumentService, DocumentValidationError
from app.embeddings import EmbeddingError, YandexEmbeddings
from app.search import BM25Index, retrieve

ROOT = Path(__file__).parent
settings = Settings.from_env()
sessions = create_session_factory(settings)
index = BM25Index()
embeddings = YandexEmbeddings(settings)
documents = DocumentService(sessions, settings, embeddings, index)
templates = Jinja2Templates(directory=str(ROOT / "templates"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    index.reload(sessions)
    yield


app = FastAPI(title="Система знаний команды", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


class DocumentInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1)


class RetrievalInput(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def document_data(document) -> dict:
    return {"id": document.id, "title": document.title, "text": document.text, "created_at": document.created_at.isoformat()}


@app.exception_handler(EmbeddingError)
async def embedding_error_handler(_: Request, __: EmbeddingError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=502, content={"detail": "Сервис embeddings недоступен; проверьте настройки Yandex AI Studio"})


@app.get("/health")
def health() -> dict:
    with sessions() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/kb/documents")
def list_documents() -> list[dict]:
    return [document_data(document) for document in documents.list()]


@app.post("/kb/documents", status_code=201)
def add_document(data: DocumentInput) -> dict:
    try:
        return document_data(documents.add(data.title, data.text))
    except DocumentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/kb/documents/{document_id}")
def get_document(document_id: int) -> dict:
    document = documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return document_data(document)


@app.delete("/kb/documents/{document_id}", status_code=204)
def delete_document(document_id: int) -> None:
    if not documents.delete(document_id):
        raise HTTPException(status_code=404, detail="Документ не найден")


@app.post("/kb/retrieve")
def retrieve_api(data: RetrievalInput) -> dict:
    return retrieve(data.question.strip(), sessions, index, embeddings, settings)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(request.url_for("documents_page"), status_code=303)


@app.get("/documents", response_class=HTMLResponse)
def documents_page(request: Request):
    return templates.TemplateResponse(request, "documents.html", {"documents": documents.list(), "error": None})


@app.post("/documents", response_class=HTMLResponse)
async def documents_form(request: Request, title: str = Form(""), text_value: str = Form(""), file: UploadFile | None = File(None)):
    try:
        if file and file.filename:
            suffix = Path(file.filename).suffix.lower()
            if suffix not in {".txt", ".md"}:
                raise DocumentValidationError("Поддерживаются только файлы .txt и .md")
            data = await file.read(settings.max_document_chars * 4 + 1)
            if len(data) > settings.max_document_chars * 4:
                raise DocumentValidationError("Файл слишком большой")
            try:
                text_value = data.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise DocumentValidationError("Файл должен быть в UTF-8") from exc
            title = title or Path(file.filename).stem
        documents.add(title, text_value)
        return RedirectResponse(request.url_for("documents_page"), status_code=303)
    except (DocumentValidationError, EmbeddingError) as exc:
        return templates.TemplateResponse(request, "documents.html", {"documents": documents.list(), "error": str(exc)}, status_code=422)


@app.get("/documents/{document_id}", response_class=HTMLResponse)
def document_page(request: Request, document_id: int):
    document = documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return templates.TemplateResponse(request, "document.html", {"document": document})


@app.post("/documents/{document_id}/delete")
def delete_document_form(request: Request, document_id: int):
    if not documents.delete(document_id):
        raise HTTPException(status_code=404, detail="Документ не найден")
    return RedirectResponse(request.url_for("documents_page"), status_code=303)


@app.get("/questions", response_class=HTMLResponse)
def questions_page(request: Request):
    return templates.TemplateResponse(request, "questions.html", {"result": None, "error": None})


@app.post("/questions", response_class=HTMLResponse)
def questions_form(request: Request, question: str = Form(...)):
    if not question.strip():
        return templates.TemplateResponse(request, "questions.html", {"result": None, "error": "Введите вопрос"}, status_code=422)
    try:
        result = retrieve(question.strip(), sessions, index, embeddings, settings)
        return templates.TemplateResponse(request, "questions.html", {"result": result, "error": None})
    except EmbeddingError as exc:
        return templates.TemplateResponse(request, "questions.html", {"result": None, "error": str(exc)}, status_code=502)


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html", {})
