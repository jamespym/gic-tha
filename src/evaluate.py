import json
import re
from datetime import datetime

from openai import OpenAI

from . import config
from .index import load_index
from .retrieve import retrieve
from .generate import generate


_client = OpenAI(api_key=config.OPENAI_API_KEY)

QUESTIONS_PATH = config.PROJECT_ROOT / "eval" / "questions.json"
RESULTS_DIR = config.PROJECT_ROOT / "eval" / "results"


def _judge(question: str, expected_answer: str, answer: str) -> dict:
    """Call LLM judge and return {"score": int, "reason": str}."""
    prompt = config.JUDGE_PROMPT.format(
        question=question,
        expected_answer=expected_answer,
        answer=answer,
    )
    response = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = response.choices[0].message.content.strip()

    score_match = re.search(r"Score:\s*([1-5])", text)
    reason_match = re.search(r"Reason:\s*(.+)", text)

    score = int(score_match.group(1)) if score_match else 0
    reason = reason_match.group(1).strip() if reason_match else text

    return {"score": score, "reason": reason}


def _print_summary(results: list[dict]) -> None:
    """Print avg scores by question type and source_type."""
    print("\n=== Results by type ===")
    by_type: dict[str, list[int]] = {}
    for r in results:
        t = r["type"]
        by_type.setdefault(t, []).append(r["score"])
    for t, scores in sorted(by_type.items()):
        avg = sum(scores) / len(scores)
        print(f"  {t:<15} n={len(scores)}  avg={avg:.2f}")

    print("\n=== Results by source_type ===")
    by_source: dict[str, list[int]] = {}
    for r in results:
        st = r["source_type"] or "n/a"
        by_source.setdefault(st, []).append(r["score"])
    for st, scores in sorted(by_source.items()):
        avg = sum(scores) / len(scores)
        print(f"  {st:<15} n={len(scores)}  avg={avg:.2f}")

    overall = sum(r["score"] for r in results) / len(results)
    print(f"\n  Overall: n={len(results)}  avg={overall:.2f}")


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

        print(f"[{qid}] {question}")
        print(f"  Expected: {expected}")
        top_chunks = retrieve(question, faiss_index, bm25_index, chunks)
        generated = generate(question, top_chunks)
        answer = generated["answer"]
        print(f"  Answer:   {answer}")
        print("  Chunks retrieved:")
        for i, chunk in enumerate(top_chunks, 1):
            print(f"    [{i}] [{chunk.page_start}-{chunk.page_end}] {chunk.section}")
            print(f"        {chunk.text[:150].strip()}...")

        judgment = _judge(question, expected, answer)
        score = judgment["score"]
        reason = judgment["reason"]
        print(f"  Score: {score}/5 — {reason}\n")

        results.append({
            "id": qid,
            "type": q["type"],
            "source_type": q["source_type"],
            "question": question,
            "expected_answer": expected,
            "answer": answer,
            "score": score,
            "reason": reason,
            "sources": generated["sources"],
        })

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"eval_{timestamp}.json"
    output_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_path}")

    _print_summary(results)


if __name__ == "__main__":
    run_eval()
