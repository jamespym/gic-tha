import json
import re
from datetime import datetime
from openai import OpenAI
from . import config
from .ingest import Chunk
from .index import load_index
from .retrieve import retrieve
from .generate import generate

_client = OpenAI(api_key=config.OPENAI_API_KEY)

RESULTS_DIR = config.PROJECT_ROOT / "eval" / "results"


def _format_context(chunks: list[Chunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Section: {chunk.section} | Pages {chunk.page_start}-{chunk.page_end}\n{chunk.text}")
    return "\n\n".join(parts)


def _call_judge(prompt: str) -> tuple[bool, str]:
    """Call LLM judge and return (passed, reason)."""
    response = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = response.choices[0].message.content.strip()
    answer_match = re.search(r"Answer:\s*(Yes|No)", text, re.IGNORECASE)
    explanation_match = re.search(r"Explanation:\s*(.+)", text, re.IGNORECASE)
    passed = answer_match.group(1).lower() == "yes" if answer_match else False
    reason = explanation_match.group(1).strip() if explanation_match else text
    return passed, reason


def _score_retrieval(question: str, chunks: list[Chunk]) -> tuple[bool, str]:
    prompt = config.RETRIEVAL_JUDGE_PROMPT.format(
        question=question,
        context=_format_context(chunks),
    )
    return _call_judge(prompt)


def _score_correctness(question: str, expected_answer: str, answer: str) -> tuple[bool, str]:
    prompt = config.CORRECTNESS_JUDGE_PROMPT.format(
        question=question,
        expected_answer=expected_answer,
        answer=answer,
    )
    return _call_judge(prompt)


def _score_faithfulness(answer: str, chunks: list[Chunk]) -> tuple[bool, str]:
    prompt = config.FAITHFULNESS_JUDGE_PROMPT.format(
        answer=answer,
        context=_format_context(chunks),
    )
    return _call_judge(prompt)


def _build_summary(results: list[dict]) -> dict:
    """Compute all summary tables as a serialisable dict."""
    def _pass_rate(items: list[bool]) -> dict:
        return {"passed": sum(items), "total": len(items), "pct": round(sum(items) / len(items) * 100)}

    def _group(dim: str, key: str) -> dict:
        groups: dict[str, list[bool]] = {}
        for r in results:
            if r[dim] is not None:
                groups.setdefault(r[key] or "n/a", []).append(r[dim])
        return {k: _pass_rate(v) for k, v in sorted(groups.items())}

    dims = ["retrieval_passed", "correctness_passed", "faithfulness_passed"]
    return {
        "by_dimension":                  {dim: _pass_rate([r[dim] for r in results if r[dim] is not None]) for dim in dims},
        "retrieval_by_question_type":    _group("retrieval_passed",    "type"),
        "retrieval_by_source_type":      _group("retrieval_passed",    "source_type"),
        "correctness_by_question_type":  _group("correctness_passed",  "type"),
        "correctness_by_source_type":    _group("correctness_passed",  "source_type"),
        "faithfulness_by_question_type": _group("faithfulness_passed", "type"),
    }


def _print_summary(summary: dict) -> None:
    labels = {"retrieval_passed": "Retrieval", "correctness_passed": "Correctness", "faithfulness_passed": "Faithfulness"}

    print("\n=== Pass rates by dimension ===")
    for dim, s in summary["by_dimension"].items():
        print(f"  {labels[dim]:<15} {s['passed']}/{s['total']} passed ({s['pct']}%)")

    sections = [
        ("=== Retrieval pass rate by question type ===",    "retrieval_by_question_type"),
        ("=== Retrieval pass rate by source_type ===",      "retrieval_by_source_type"),
        ("=== Correctness pass rate by question type ===",  "correctness_by_question_type"),
        ("=== Correctness pass rate by source_type ===",    "correctness_by_source_type"),
        ("=== Faithfulness pass rate by question type ===", "faithfulness_by_question_type"),
    ]
    for header, key in sections:
        print(f"\n{header}")
        for label, s in summary[key].items():
            print(f"  {label:<15} {s['passed']}/{s['total']} passed ({s['pct']}%)")


def run_eval(questions_file: str = "questions.json") -> None:
    questions = json.loads((config.PROJECT_ROOT / "eval" / questions_file).read_text())

    print("Loading indexes and models...")
    chunks, faiss_index, bm25_index = load_index()
    print(f"Loaded {len(chunks)} chunks. Running {len(questions)} questions...\n")

    results = []
    for q in questions:
        qid = q["id"]
        question = q["question"]
        expected = q["expected_answer"]
        is_negative = q["source_type"] is None

        print(f"[{qid}] {question}")
        top_chunks = retrieve(question, faiss_index, bm25_index, chunks)
        generated = generate(question, top_chunks)
        answer = generated["answer"]
        print(f"  Answer: {answer}")

        faithfulness_passed, faithfulness_reason = _score_faithfulness(answer, top_chunks)
        if is_negative:
            retrieval_passed, retrieval_reason = None, "skipped — negative question"
        else:
            retrieval_passed, retrieval_reason = _score_retrieval(question, top_chunks)
        correctness_passed, correctness_reason = _score_correctness(question, expected, answer)

        print(f"  Retrieval:    {'PASS' if retrieval_passed else 'FAIL' if retrieval_passed is not None else 'SKIP'}")
        print(f"  Correctness:  {'PASS' if correctness_passed else 'FAIL' if correctness_passed is not None else 'SKIP'}")
        print(f"  Faithfulness: {'PASS' if faithfulness_passed else 'FAIL'}\n")

        results.append({
            "id": qid,
            "type": q["type"],
            "source_type": q["source_type"],
            "question": question,
            "expected_answer": expected,
            "answer": answer,
            "retrieval_passed": retrieval_passed,
            "retrieval_reason": retrieval_reason,
            "correctness_passed": correctness_passed,
            "correctness_reason": correctness_reason,
            "faithfulness_passed": faithfulness_passed,
            "faithfulness_reason": faithfulness_reason,
            "sources": generated["sources"],
        })

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = _build_summary(results)
    output_path = RESULTS_DIR / f"eval_{timestamp}.json"
    output_path.write_text(json.dumps({"results": results, "summary": summary}, indent=2))
    print(f"\nResults saved to {output_path}")

    _print_summary(summary)


if __name__ == "__main__":
    import sys
    run_eval(sys.argv[1] if len(sys.argv) > 1 else "questions.json")
