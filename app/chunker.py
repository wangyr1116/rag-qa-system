def chunk_text(text: str, chunk_size: int = 150, overlap: int = 30) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = start + chunk_size - overlap

    return chunks


def chunk_by_paragraph(text: str) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph:
            chunks.append(paragraph)
    return chunks


def chunk_document(
    text: str,
    strategy: str,
    chunk_size: int = 150,
    overlap: int = 30,
) -> list[str]:
    if strategy == "fixed":
        return chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

    if strategy == "paragraph":
        return chunk_by_paragraph(text)

    raise ValueError(f"unknown chunking strategy: {strategy}")
