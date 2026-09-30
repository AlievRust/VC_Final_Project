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
    cases = [json.loads(line) for line in (ROOT / "tests_data" / "kb_questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    documents = get(base_url, "/kb/documents")
    if len(documents) != 5 or len(cases) != 10:
        raise SystemExit(f"Ожидались 5 документов и 10 вопросов; найдено {len(documents)} и {len(cases)}")

    run_ids: list[int] = []
    passed = 0
    for number, case in enumerate(cases, 1):
        result = ask(base_url, case["question"])
        run_ids.append(result["run_id"])
        actual_sources = {row["title"] for row in result["sources"]}
        expected_sources = set(case["expected_sources"])
        accepted = (
            result["needs_review"] == case["expected_needs_review"]
            and (
                not actual_sources and bool(result["review_reason"])
                if case["expected_needs_review"]
                else expected_sources <= actual_sources and bool(result["answer"])
            )
        )
        passed += bool(accepted)
        print(f"{number:02d} {'PASS' if accepted else 'FAIL'} · {case['question']}")
        print(f"   Ответ: {result['answer']}")
        print(f"   needs_review={result['needs_review']}; причина={result['review_reason'] or '—'}; источники={[row['title'] for row in result['sources']]}")
        for source in result["sources"]:
            print(f"   Цитата: {source['quote']}")

    history = get(base_url, "/kb/history")
    review = get(base_url, "/kb/history?needs_review=true")
    exported = get(base_url, "/kb/history/export")
    audit = get(base_url, "/kb/audit")
    history_ids = {row["id"] for row in history}
    review_ids = {row["id"] for row in review}
    audit_ids = {row["entity_id"] for row in audit if row["action"] == "question.asked"}
    export_ids = {row["id"] for row in exported}
    export_logged = any(row["action"] == "history.exported" and row["details"].get("count") == len(exported) for row in audit)
    persisted = set(run_ids) <= history_ids and set(run_ids) <= audit_ids and set(run_ids) <= export_ids and export_logged
    expected_review_ids = {run_ids[i] for i, case in enumerate(cases) if case["expected_needs_review"]}
    persisted = persisted and expected_review_ids <= review_ids
    print(f"Итог: {passed}/10 по статусам и источникам; история/аудит/экспорт={'PASS' if persisted else 'FAIL'}")
    if passed != 10 or not persisted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
