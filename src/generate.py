from openai import OpenAI
from .ingest import Chunk
from . import config

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


def _call_llm(prompt: str) -> str:
    response = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content


def generate(query: str, chunks: list[Chunk]) -> dict:
    """
    Returns:
        {
            "answer": str,          # GPT-4o answer with [N] citations
            "sources": list[dict],  # [{"section", "pages", "excerpt"}, ...]
        }
    """
    sources_text = _format_sources(chunks)
    prompt = config.GENERATION_PROMPT.format(query=query, sources=sources_text)
    answer = _call_llm(prompt)

    sources = [
        {
            "section": chunk.section,
            "pages": f"{chunk.page_start}-{chunk.page_end}",
            "excerpt": chunk.text[:350],
        }
        for chunk in chunks
    ]

    return {"answer": answer, "sources": sources}


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
    for s in result["sources"]:
        print(f"  [{s['pages']}] {s['section']}: {s['excerpt'][:400]}...")
