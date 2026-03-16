from openai import OpenAI
from .ingest import Chunk
from . import config

# Instantiated once at module level — reused across both LLM calls per generate() invocation
_client = OpenAI(api_key=config.OPENAI_API_KEY)


def _format_sources(chunks: list[Chunk]) -> str:
    """Format chunks into a numbered source block for injection into the prompt.

    Example output:
        [1] Section: Revenue | Pages 53-54
        <chunk text>

        [2] Section: Net Income | Pages 55-55
        <chunk text>
    """
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        header = f"[{i}] Section: {chunk.section} | Pages {chunk.page_start}-{chunk.page_end}"
        parts.append(f"{header}\n{chunk.text}")
    return "\n\n".join(parts)


def _call_llm(prompt: str, model: str = config.LLM_MODEL) -> str:
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _check_hallucination(query: str, answer: str, sources: str) -> dict:
    """Single-pass hallucination check
    Returns:
        {
            "passed": bool,
            "verdict": str,   # e.g. "PASS" or "FAIL: SCOPE"
            "reason": str,    # the one-sentence explanation from the model
        }
    """
    prompt = config.HALLUCINATION_PROMPT.format(
        query=query,
        answer=answer,
        sources=sources,
    )
    raw = _call_llm(prompt, model=config.HALLUCINATION_MODEL).strip()

    # Expected format: "PASS - reason" or "FAIL: SCOPE - reason"
    if " - " in raw:
        verdict, reason = raw.split(" - ", maxsplit=1)
    else:
        verdict, reason = raw, ""

    return {
        "passed": verdict.strip().upper().startswith("PASS"),
        "verdict": verdict.strip(),
        "reason": reason.strip(),
    }


def generate(query: str, chunks: list[Chunk]) -> dict:
    """
    Returns:
        {
            "answer": str,                        # GPT-4o answer with [p.X] citations
            "hallucination_check": {
                "passed": bool,
                "verdict": str,                   # e.g. "PASS" or "FAIL: SCOPE"
                "reason": str,                    # one-sentence explanation
            },
            "sources": list[dict],                # [{"section", "pages", "excerpt"}, ...]
        }
    """
    sources_text = _format_sources(chunks)

    prompt = config.GENERATION_PROMPT.format(query=query, sources=sources_text)
    answer = _call_llm(prompt)

    hallucination = _check_hallucination(query, answer, sources_text)

    # sources list: structured metadata + short excerpt for display / eval
    sources = [
        {
            "section": chunk.section,
            "pages": f"{chunk.page_start}-{chunk.page_end}",
            "excerpt": chunk.text[:200],
        }
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "hallucination_check": hallucination,  # {"passed", "verdict", "reason"}
        "sources": sources,
    }


if __name__ == "__main__":
    import sys
    from .index import load_index
    from .retrieve import retrieve

    chunks_all, faiss_index, bm25_index = load_index()
    query = sys.argv[1] if len(sys.argv) > 1 else "What is the total net revenue?"
    top_chunks = retrieve(query, faiss_index, bm25_index, chunks_all)
    result = generate(query, top_chunks)

    print(result["answer"])
    print()
    hc = result["hallucination_check"]
    print(f"Hallucination check: {hc['verdict']}")
    if hc["reason"]:
        print(f"Reason: {hc['reason']}")
    print()
    for s in result["sources"]:
        print(f"  [{s['pages']}] {s['section']}: {s['excerpt'][:100]}...")
