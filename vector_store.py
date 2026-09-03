import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "data" / "rag_index"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
DOCUMENTS_PATH = INDEX_DIR / "documents.json"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    return _model


def rebuild_collection(documents):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if not documents:
        np.save(EMBEDDINGS_PATH, np.empty((0, 384), dtype=np.float32))
        DOCUMENTS_PATH.write_text("[]", encoding="utf-8")
        return 0

    embeddings = get_embedding_model().encode(
        [item["text"] for item in documents],
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).astype(np.float32)

    temp_embeddings = INDEX_DIR / "embeddings.tmp.npy"
    temp_documents = INDEX_DIR / "documents.tmp.json"
    np.save(temp_embeddings, embeddings)
    temp_documents.write_text(
        json.dumps(documents, ensure_ascii=False), encoding="utf-8"
    )
    temp_embeddings.replace(EMBEDDINGS_PATH)
    temp_documents.replace(DOCUMENTS_PATH)
    return len(documents)


def query_collection(query, top_k=4):
    if not query or top_k <= 0:
        return []
    if not EMBEDDINGS_PATH.exists() or not DOCUMENTS_PATH.exists():
        return []

    embeddings = np.load(EMBEDDINGS_PATH)
    documents = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))
    if not documents or embeddings.shape[0] == 0:
        return []

    query_embedding = get_embedding_model().encode(
        [query], normalize_embeddings=True, convert_to_numpy=True
    )[0].astype(np.float32)
    scores = embeddings @ query_embedding
    best_indexes = np.argsort(scores)[-min(top_k, len(documents)):][::-1]

    return [
        {
            "text": documents[int(index)]["text"],
            "source": documents[int(index)]["source"],
            "score": round(float(scores[index]), 4),
        }
        for index in best_indexes
    ]
