from .ingest import Chunk
from .index import load_index
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
import faiss
import numpy as np
from . import config

def _dense_retrieve(query: str, chunks: list[Chunk], faiss_index: faiss.Index, top_k: int) -> list[tuple[int, float]]:
    embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5") 
    query_vector = embedding_model.encode(query, normalize_embeddings=True)
    scores, indices = faiss_index.search(query_vector.reshape(1, -1), top_k)
    
    return list(zip(indices[0].tolist(), scores[0].tolist()))

def _sparse_retrieve(query: str, chunks: list[Chunk], bm25_index: BM25Okapi, top_k: int) -> list[tuple[int, float]]:
    scores = bm25_index.get_scores(query.lower().split())
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [(int(i), float(scores[i])) for i in top_indices]

def _rrf_fusion(dense_results: list[tuple[int, float]],
                sparse_results: list[tuple[int, float]],
                k: int = 60) -> list[int]:
    
    rrf_scores = {}
    # Accumulates chunk's score using RRF formula
    for rank, (chunk_id, _) in enumerate(dense_results):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank  + 1)
    for rank, (chunk_id, _) in enumerate(sparse_results):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank  + 1)
    
    return sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)

def _rerank(query: str, candidates: list[int], chunks: list[Chunk], top_k: int) -> list[Chunk]:
    """
    top_indices: index of the scores array
    candidates: list of chunk ids
    candidates[i]: 
    """
    xencoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    pairs = [(query, chunks[i].text) for i in candidates]
    scores = xencoder.predict(pairs) # Relevance score
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [chunks[candidates[i]] for i in top_indices]
    
