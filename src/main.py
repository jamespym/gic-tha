import sys
from pathlib import Path

from . import config
from .ingest import ingest
from .index import build_and_save, load_index


def _print_result(result: dict) -> None:
    print("\n" + result["answer"])

    print("\nSources:")
    for s in result["sources"]:
        print(f"  [{s['pages']}] {s['section']}")
        print(f"      {s['excerpt']}...")


def ingest_main(pdf_path: Path) -> None:
    """Parse PDF and build FAISS + BM25 indexes."""
    if not pdf_path.exists():
        sys.exit(f"Error: file not found: {pdf_path}")

    print(f"Ingesting {pdf_path} ...")
    chunks = ingest(pdf_path)
    print(f"  {len(chunks)} chunks extracted. Building indexes ...")
    build_and_save(chunks)
    print(f"  Indexes saved to {config.INDEX_DIR}")


def query_main(query: str = "") -> None:
    """Answer one question or run an interactive REPL."""
    from .retrieve import retrieve
    from .generate import generate

    print("Loading indexes and models ...")
    chunks, faiss_index, bm25_index = load_index()
    print("Ready.\n")

    if query:
        top_chunks = retrieve(query, faiss_index, bm25_index, chunks)
        result = generate(query, top_chunks)
        _print_result(result)
    else:
        print("Enter a question (or 'quit' to exit).")
        while True:
            try:
                query = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not query or query.lower() in {"quit", "exit", "q"}:
                break
            top_chunks = retrieve(query, faiss_index, bm25_index, chunks)
            result = generate(query, top_chunks)
            _print_result(result)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""

    if command == "ingest":
        ingest_main(Path(sys.argv[2]))
    elif command == "query":
        query_main(" ".join(sys.argv[2:]))
    else:
        print("Usage:")
        print("  python -m src.main ingest <pdf_path>")
        print("  python -m src.main query [question]")
