import hashlib
import json
from pathlib import Path

from document_reader import read_document
from knowledge_loader import ALLOWED_SUFFIXES, KNOWLEDGE_DIR
from text_splitter import split_text
from vector_store import query_collection, rebuild_collection


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "data" / "rag_cache"


def _cache_path(file_path):
    stat = file_path.stat()
    fingerprint = hashlib.sha1(
        f"{file_path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}".encode("utf-8")
    ).hexdigest()
    return CACHE_DIR / f"{fingerprint}.json"


def _load_or_create_chunks(file_path):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _cache_path(file_path)
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    chunks = split_text(read_document(file_path))
    cache_path.write_text(
        json.dumps(chunks, ensure_ascii=False), encoding="utf-8"
    )
    return chunks


def rebuild_rag_index():
    documents = []
    errors = []

    for file_path in sorted(KNOWLEDGE_DIR.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        try:
            print(f"[RAG] 正在处理：{file_path.name}")
            chunks = _load_or_create_chunks(file_path)
            for index, chunk in enumerate(chunks):
                chunk_id = hashlib.sha1(
                    f"{file_path.name}:{index}:{chunk}".encode("utf-8")
                ).hexdigest()
                documents.append({
                    "id": chunk_id,
                    "text": chunk,
                    "source": file_path.name,
                    "chunk_index": index,
                })
        except Exception as exc:
            errors.append(f"{file_path.name}: {exc}")

    print(f"[RAG] 文本处理完成，开始生成 {len(documents)} 个向量。")
    count = rebuild_collection(documents)
    print(f"[RAG] 索引保存完成，共 {count} 个文本块。")
    return count, errors


def search_knowledge(query, top_k=4):
    return query_collection(query, top_k=top_k)


def build_rag_context(query, top_k=4):
    matches = search_knowledge(query, top_k=top_k)
    if not matches:
        return ""

    return "\n\n".join(
        f"【来源：{item['source']}】\n{item['text']}" for item in matches
    )
