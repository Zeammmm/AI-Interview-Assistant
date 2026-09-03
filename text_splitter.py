import re


def split_text(text, chunk_size=500, chunk_overlap=80):
    """把文本切成有少量重叠的块。"""
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须大于等于 0 且小于 chunk_size")

    text = re.sub(r"\r\n?", "\n", text or "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            search_start = start + chunk_size // 2
            split_at = max(
                text.rfind("\n\n", search_start, end),
                text.rfind("\n", search_start, end),
                text.rfind("。", search_start, end),
                text.rfind("！", search_start, end),
                text.rfind("？", search_start, end),
            )
            if split_at > start:
                end = split_at + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - chunk_overlap, start + 1)

    return chunks
