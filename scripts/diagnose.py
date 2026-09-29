"""Выводит результаты CP3 без назначения порога evidence."""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


def post(base_url: str, path: str, payload: dict) -> dict:
    request = Request(base_url + path, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=120) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="Диагностика retrieval на контрольных вопросах")
    parser.add_argument("--base-url", default="http://localhost")
    parser.add_argument("--load-fixtures", action="store_true", help="добавить 5 учебных документов в текущую базу")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    if args.load_fixtures:
        for path in sorted((ROOT / "examples" / "demo_documents").glob("*.md")):
            created = post(base_url, "/kb/documents", {"title": path.stem, "text": path.read_text(encoding="utf-8")})
            print(f"Добавлен документ #{created['id']}: {created['title']}")
    questions = json.loads((ROOT / "examples" / "questions.json").read_text(encoding="utf-8"))
    for number, case in enumerate(questions, 1):
        result = post(base_url, "/kb/retrieve", {"question": case["question"]})
        print(f"\n{number}. {case['question']} (ответ в KB: {'да' if case['answerable'] else 'нет'})")
        for row in result["results"][:3]:
            semantic = next((item for item in result["semantic"] if item["snippet_id"] == row["snippet_id"]), None)
            lexical = next((item for item in result["lexical"] if item["snippet_id"] == row["snippet_id"]), None)
            print(f"  {row['title']} #{row['snippet_id']}: cosine={semantic['cosine_distance'] if semantic else '-'}; BM25={lexical['bm25_score'] if lexical else '-'}; RRF={row['rrf_score']:.5f}")


if __name__ == "__main__":
    main()
