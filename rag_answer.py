"""
rag_answer.py — Sprint 2 + Sprint 3: Retrieval & Grounded Answer
"""

import os
import importlib
import re
import time
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

TOP_K_SEARCH = 3
TOP_K_SELECT = 2
TOP_K_HYBRID = 2

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
MAX_LLM_RETRIES = 2
INITIAL_RETRY_WAIT = 1.5

_SPARSE_INDEX_CACHE: Dict[str, Any] = {}
_CHROMA_CLIENT = None
_CHROMA_COLLECTION = None
_LOCAL_CROSS_ENCODER = None


def _get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


def _tokenize_for_bm25(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _get_chroma_collection():
    global _CHROMA_CLIENT, _CHROMA_COLLECTION

    if _CHROMA_COLLECTION is not None:
        return _CHROMA_COLLECTION

    chromadb = importlib.import_module("chromadb")
    from index import CHROMA_DB_DIR

    _CHROMA_CLIENT = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    _CHROMA_COLLECTION = _CHROMA_CLIENT.get_collection("rag_lab")
    return _CHROMA_COLLECTION


def _load_sparse_corpus() -> List[Dict[str, Any]]:
    collection = _get_chroma_collection()
    results = collection.get(include=["documents", "metadatas"])

    documents = results.get("documents", []) or []
    metadatas = results.get("metadatas", []) or []
    ids = results.get("ids", []) or []

    corpus = []
    for idx, (doc, meta) in enumerate(zip(documents, metadatas)):
        corpus.append(
            {
                "id": ids[idx] if idx < len(ids) else f"chunk_{idx}",
                "text": doc or "",
                "metadata": meta or {},
            }
        )
    return corpus


def retrieve_dense(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    from index import get_embedding

    collection = _get_chroma_collection()
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []
    for doc, meta, distance in zip(docs, metas, distances):
        score = 1 - float(distance)
        retrieved.append(
            {
                "text": doc,
                "metadata": meta or {},
                "score": score,
            }
        )

    retrieved.sort(key=lambda x: x["score"], reverse=True)
    return retrieved


def retrieve_sparse(query: str, top_k: int = TOP_K_SEARCH) -> List[Dict[str, Any]]:
    cache_key = "default"
    BM25Okapi = importlib.import_module("rank_bm25").BM25Okapi

    if cache_key not in _SPARSE_INDEX_CACHE:
        corpus = _load_sparse_corpus()
        tokenized_corpus = [_tokenize_for_bm25(chunk["text"]) for chunk in corpus]
        _SPARSE_INDEX_CACHE[cache_key] = {
            "corpus": corpus,
            "bm25": BM25Okapi(tokenized_corpus),
        }

    cache = _SPARSE_INDEX_CACHE[cache_key]
    corpus = cache["corpus"]
    bm25 = cache["bm25"]

    if not corpus:
        return []

    tokenized_query = _tokenize_for_bm25(query)
    if not tokenized_query:
        return []

    scores = bm25.get_scores(tokenized_query)
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results: List[Dict[str, Any]] = []
    for idx in ranked_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        chunk = corpus[idx]
        results.append(
            {
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "score": score,
            }
        )

    return results


def retrieve_hybrid(
    query: str,
    top_k: int = TOP_K_HYBRID,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
) -> List[Dict[str, Any]]:
    dense_results = retrieve_dense(query, top_k=top_k)
    sparse_results = retrieve_sparse(query, top_k=top_k)

    if not dense_results and not sparse_results:
        return []

    def chunk_key(chunk: Dict[str, Any]) -> str:
        metadata = chunk.get("metadata", {}) or {}
        source = metadata.get("source", "")
        section = metadata.get("section", "")
        text = chunk.get("text", "")
        return f"{source}||{section}||{text}"

    dense_rank_map = {chunk_key(chunk): rank for rank, chunk in enumerate(dense_results, start=1)}
    sparse_rank_map = {chunk_key(chunk): rank for rank, chunk in enumerate(sparse_results, start=1)}

    merged: Dict[str, Dict[str, Any]] = {}
    all_chunks = dense_results + sparse_results

    for chunk in all_chunks:
        key = chunk_key(chunk)
        if key not in merged:
            merged[key] = {
                "text": chunk.get("text", ""),
                "metadata": chunk.get("metadata", {}) or {},
                "score": 0.0,
            }

        dense_rank = dense_rank_map.get(key)
        sparse_rank = sparse_rank_map.get(key)

        dense_score = dense_weight * (1.0 / (60.0 + dense_rank)) if dense_rank is not None else 0.0
        sparse_score = sparse_weight * (1.0 / (60.0 + sparse_rank)) if sparse_rank is not None else 0.0
        merged[key]["score"] += dense_score + sparse_score

    fused_results = sorted(merged.values(), key=lambda chunk: chunk["score"], reverse=True)
    return fused_results[:top_k]


def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int = TOP_K_SELECT) -> List[Dict[str, Any]]:
    global _LOCAL_CROSS_ENCODER

    if not candidates:
        return []

    try:
        if _LOCAL_CROSS_ENCODER is None:
            from sentence_transformers import CrossEncoder
            _LOCAL_CROSS_ENCODER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        pairs = [[query, chunk["text"]] for chunk in candidates]
        scores = _LOCAL_CROSS_ENCODER.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in ranked[:top_k]]
    except Exception:
        return candidates[:top_k]


def transform_query(query: str, strategy: str = "expansion") -> List[str]:
    return [query]


def build_context_block(chunks: List[Dict[str, Any]]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        score = chunk.get("score", 0)
        text = chunk.get("text", "")

        header = f"[{i}] {source}"
        if section:
            header += f" | {section}"
        if score > 0:
            header += f" | score={score:.2f}"

        context_parts.append(f"{header}\n{text}")

    return "\n\n".join(context_parts)


def build_grounded_prompt(query: str, context_block: str) -> str:
    return f"""
You are an assistant that answers questions based ONLY on the retrieved context.
Strict rules:
1. Use only the information provided in the context.
2. If the context is insufficient to answer with certainty, respond exactly with: "Không đủ dữ liệu."
3. Do not make assumptions or fabricate any information.
4. When providing an answer, include citations using chunk indices such as [1], [2].
5. When possible, include the corresponding source/section from the cited chunks.
6. Keep the answer concise, clear, and in the same language as the question.

Question:
{query}

Context:
{context_block}

Answer:
"""


def _mock_answer_from_chunks(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "Không đủ dữ liệu."

    text = chunks[0].get("text", "").strip()
    if not text:
        return "Không đủ dữ liệu."

    sentences = re.split(r"(?<=[\.\!\?])\s+", text)
    short = " ".join(sentences[:2]).strip()
    if not short:
        short = text[:250].strip()

    return f"Dựa trên tài liệu đã truy xuất: {short}"


def call_llm(prompt: str, fallback_answer: str, max_retries: int = MAX_LLM_RETRIES, initial_wait: float = INITIAL_RETRY_WAIT) -> str:
    api_key = _get_gemini_api_key()
    if not api_key:
        return fallback_answer

    retry_count = 0
    wait_time = initial_wait

    while retry_count <= max_retries:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(LLM_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0, "max_output_tokens": 512},
            )

            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()

            return fallback_answer

        except Exception:
            if retry_count < max_retries:
                time.sleep(wait_time)
                retry_count += 1
                wait_time *= 2
                continue
            return fallback_answer

    return fallback_answer


def rag_answer(
    query: str,
    retrieval_mode: str = "dense",
    top_k_search: int = TOP_K_SEARCH,
    top_k_select: int = TOP_K_SELECT,
    use_rerank: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    config = {
        "retrieval_mode": retrieval_mode,
        "top_k_search": top_k_search,
        "top_k_select": top_k_select,
        "use_rerank": use_rerank,
    }

    effective_top_k = top_k_search
    if retrieval_mode == "hybrid":
        effective_top_k = min(top_k_search, TOP_K_HYBRID)

    if retrieval_mode == "dense":
        candidates = retrieve_dense(query, top_k=effective_top_k)
    elif retrieval_mode == "sparse":
        candidates = retrieve_sparse(query, top_k=effective_top_k)
    elif retrieval_mode == "hybrid":
        candidates = retrieve_hybrid(query, top_k=effective_top_k)
    else:
        raise ValueError(f"retrieval_mode không hợp lệ: {retrieval_mode}")

    if use_rerank:
        selected_chunks = rerank(query, candidates, top_k=top_k_select)
    else:
        selected_chunks = candidates[:top_k_select]

    context_block = build_context_block(selected_chunks)
    prompt = build_grounded_prompt(query, context_block)

    fallback_answer = _mock_answer_from_chunks(selected_chunks)
    answer = call_llm(prompt, fallback_answer=fallback_answer)

    sources = []
    seen = set()
    for chunk in selected_chunks:
        source = chunk.get("metadata", {}).get("source", "")
        if source and source not in seen:
            seen.add(source)
            sources.append(source)

    if verbose:
        print("=" * 60)
        print(f"Query: {query}")
        print(f"Mode: {retrieval_mode}")
        print(f"Candidates: {len(candidates)} | Selected: {len(selected_chunks)}")
        print("Sources:", sources)
        print("Answer:", answer)

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "chunks_used": selected_chunks,
        "config": config,
    }


def compare_retrieval_strategies(query: str) -> None:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print("=" * 60)

    strategies = ["dense", "hybrid"]

    for strategy in strategies:
        print(f"\n--- Strategy: {strategy} ---")
        try:
            result = rag_answer(query, retrieval_mode=strategy, verbose=False)
            print(f"Answer: {result['answer']}")
            print(f"Sources: {result['sources']}")
        except NotImplementedError as e:
            print(f"Chưa implement: {e}")
        except Exception as e:
            print(f"Lỗi: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 2 + 3: RAG Answer Pipeline")
    print("=" * 60)

    print("\n--- Sprint 3: So sánh strategies (với optimization) ---")
    print(f"\n[INFO] OPTIMIZATION:")
    print(f"  • call_llm() có retry logic với exponential backoff (max_retries={MAX_LLM_RETRIES})")
    print(f"  • Hybrid retrieval dùng TOP_K_HYBRID={TOP_K_HYBRID}")
    print(f"  • Dense/Sparse dùng TOP_K_SEARCH={TOP_K_SEARCH}")

    compare_retrieval_strategies("Ai phải phê duyệt để cấp quyền Level 3?")