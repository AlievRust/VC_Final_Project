"""Приёмка CP6 на пяти документах и десяти контрольных вопросах."""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


def get(base_url: str, path: str):
    with urlopen(base_url + path, timeout=30) as response:
        return json.load(response)


def ask(base_url: str, question: str):
    request = Request(
        base_url + "/kb/ask",
        data=json.dumps({"question": question}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description="Приёмка ответов, истории и аудита")
    parser.add_argument("--base-url", default="http://api:8000")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    cases = json.loads((ROOT / "examples" / "questions.json").read_text(encoding="utf-8"))
    documents = get(base_url, "/kb/documents")
    if len(documents) != 5 or len(cases) != 10:
        raise SystemExit(f"Ожидались 5 документов и 10 вопросов; найдено {len(documents)} и {len(cases)}")

    run_ids: list[int] = []
    passed = 0
    for number, case in enumerate(cases, 1):
        result = ask(base_url, case["question"])
        run_ids.append(result["run_id"])
        accepted = bool(result["sources"]) and not result["needs_review"] if case["answerable"] else result["needs_review"] and bool(result["review_reason"])
        passed += bool(accepted)
        print(f"{number:02d} {'PASS' if accepted else 'FAIL'} · {case['question']}")
        print(f"   Ответ: {result['answer']}")
        print(f"   needs_review={result['needs_review']}; причина={result['review_reason'] or '—'}; источники={[row['title'] for row in result['sources']]}")
        for source in result["sources"]:
            print(f"   Цитата: {source['quote']}")

    history = get(base_url, "/kb/history")
    review = get(base_url, "/kb/history?needs_review=true")
    audit = get(base_url, "/kb/audit")
    history_ids = {row["id"] for row in history}
    review_ids = {row["id"] for row in review}
    audit_ids = {row["entity_id"] for row in audit if row["action"] == "question.asked"}
    persisted = set(run_ids) <= history_ids and set(run_ids) <= audit_ids
    expected_review_ids = {run_ids[i] for i, case in enumerate(cases) if not case["answerable"]}
    persisted = persisted and expected_review_ids <= review_ids
    print(f"Итог: {passed}/10 по статусам и источникам; история/аудит={'PASS' if persisted else 'FAIL'}")
    if passed != 10 or not persisted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
