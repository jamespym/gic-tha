from pathlib import Path
from .ingest import Chunk
from sentence_transformers import SentenceTransformer
import faiss
from rank_bm25 import BM25Okapi
import pickle                                                                                        
import numpy as np
from . import config
from . import ingest

# Prepend headings
def _prepare_text(chunk: Chunk) -> str:
    prepended_text =  f"Section: {chunk.section} | Pages {chunk.page_start}-{chunk.page_end}\n{chunk.text}"
    return prepended_text

# FAISS - semantic search
def build_faiss_index(chunks: list[Chunk]) -> faiss.Index:
    texts = [_prepare_text(chunk) for chunk in chunks]
    
    embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5") 
    vectors = embedding_model.encode(texts, normalize_embeddings=True)
    
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim) #faiss.Index
    index.add(vectors)
    
    return index

# BM25 
def build_bm25_index(chunks: list[Chunk]) -> BM25Okapi:
    tokenized = [chunk.text.split() for chunk in chunks]
    return BM25Okapi(tokenized)

# Saving and Loading
def save_index(chunks: list[Chunk], faiss_index: faiss.Index, bm25_index: BM25Okapi) -> None:
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(faiss_index, str(config.INDEX_DIR / "faiss.index"))
    
    with open(config.INDEX_DIR / "bm25.pkl", "wb") as f:
        pickle.dump(bm25_index, f)
        
    with open(config.INDEX_DIR / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)
        
        
def build_and_save(chunks: list[Chunk]) -> None:
    faiss_index = build_faiss_index(chunks)
    bm25_index = build_bm25_index(chunks)
    save_index(chunks, faiss_index, bm25_index)

def load_index() -> tuple[list[Chunk], faiss.Index, BM25Okapi]:
    faiss_index = faiss.read_index(str(config.INDEX_DIR / "faiss.index"))
    with open(config.INDEX_DIR / "bm25.pkl", "rb") as f:
        bm25_index = pickle.load(f)
    with open(config.INDEX_DIR / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
        
    return chunks, faiss_index, bm25_index

if __name__ == "__main__":
    import sys
    from src.ingest import ingest

    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.pdf"
    chunks = ingest(Path(pdf_path))
    build_and_save(chunks)
    print(f"Indexed {len(chunks)} chunks → {config.INDEX_DIR}")


