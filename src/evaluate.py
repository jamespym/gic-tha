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

QUESTIONS_PATH = config.PROJECT_ROOT / "eval" / "questions.json"
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
    answer_match = re.search(r"\b(Yes|No)\b", text, re.IGNORECASE)

    passed = answer_match.group(1).lower() == "yes" if answer_match else False
    return passed, text


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


def _print_summary(results: list[dict]) -> None:
    dims = ["retrieval_passed", "correctness_passed", "faithfulness_passed"]
    labels = {"retrieval_passed": "Retrieval", "correctness_passed": "Correctness", "faithfulness_passed": "Faithfulness"}

    print("\n=== Pass rates by dimension ===")
    for dim in dims:
        scores = [r[dim] for r in results if r[dim] is not None]
        pct = sum(scores) / len(scores) * 100
        print(f"  {labels[dim]:<15} {sum(scores)}/{len(scores)} passed ({pct:.0f}%)")

    print("\n=== Retrieval pass rate by question type ===")
    by_type_r: dict[str, list[bool]] = {}
    for r in results:
        if r["retrieval_passed"] is not None:
            by_type_r.setdefault(r["type"], []).append(r["retrieval_passed"])
    for t, scores in sorted(by_type_r.items()):
        pct = sum(scores) / len(scores) * 100
        print(f"  {t:<15} {sum(scores)}/{len(scores)} passed ({pct:.0f}%)")

    print("\n=== Retrieval pass rate by source_type ===")
    by_source: dict[str, list[bool]] = {}
    for r in results:
        if r["retrieval_passed"] is not None:
            st = r["source_type"] or "n/a"
            by_source.setdefault(st, []).append(r["retrieval_passed"])
    for st, scores in sorted(by_source.items()):
        pct = sum(scores) / len(scores) * 100
        print(f"  {st:<15} {sum(scores)}/{len(scores)} passed ({pct:.0f}%)")

    print("\n=== Correctness pass rate by question type ===")
    by_type_c: dict[str, list[bool]] = {}
    for r in results:
        if r["correctness_passed"] is not None:
            by_type_c.setdefault(r["type"], []).append(r["correctness_passed"])
    for t, scores in sorted(by_type_c.items()):
        pct = sum(scores) / len(scores) * 100
        print(f"  {t:<15} {sum(scores)}/{len(scores)} passed ({pct:.0f}%)")

    print("\n=== Correctness pass rate by source_type ===")
    by_source_c: dict[str, list[bool]] = {}
    for r in results:
        if r["correctness_passed"] is not None:
            st = r["source_type"] or "n/a"
            by_source_c.setdefault(st, []).append(r["correctness_passed"])
    for st, scores in sorted(by_source_c.items()):
        pct = sum(scores) / len(scores) * 100
        print(f"  {st:<15} {sum(scores)}/{len(scores)} passed ({pct:.0f}%)")

    print("\n=== Faithfulness pass rate by question type ===")
    by_type_f: dict[str, list[bool]] = {}
    for r in results:
        if r["faithfulness_passed"] is not None:
            by_type_f.setdefault(r["type"], []).append(r["faithfulness_passed"])
    for t, scores in sorted(by_type_f.items()):
        pct = sum(scores) / len(scores) * 100
        print(f"  {t:<15} {sum(scores)}/{len(scores)} passed ({pct:.0f}%)")


def run_eval() -> None:
    """Run the full evaluation suite and save results."""
    questions = json.loads(QUESTIONS_PATH.read_text())

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

        retrieval_passed, _ = _score_retrieval(question, top_chunks)
        faithfulness_passed, faithfulness_reason = _score_faithfulness(answer, top_chunks)
        if is_negative:
            correctness_passed, correctness_reason = None, "skipped — negative question"
        else:
            correctness_passed, correctness_reason = _score_correctness(question, expected, answer)

        print(f"  Retrieval:    {'PASS' if retrieval_passed else 'FAIL'}")
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
    run_eval()
