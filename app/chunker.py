import re
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

def chunk_markdown_sections(text: str) -> list[str]:
    chunks, headings, body = [], [], []
    in_code = False

    def flush():
        content = "\n".join(body).strip()
        if content:
            prefix = "\n".join(title for _, title in headings)
            chunks.append(f"{prefix}\n\n{content}".strip())
        body.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            body.append(line)
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading and not in_code:
            flush()
            level = len(heading.group(1))
            while headings and headings[-1][0] >= level:
                headings.pop()
            title = re.sub(r"\s+\{[^{}]*\}\s*$", "", line)
            headings.append((level, title))
        else:
            body.append(line)

    if in_code:
        raise ValueError("Markdown 代码围栏未闭合")
    flush()
    return chunks
def split_large_unit(prefix: str, unit: str, count_tokens, limit: int) -> list[str]:
    is_code = unit.startswith("```")
    lines = unit.splitlines()
    opening = lines[0] if is_code else ""
    content_lines = lines[1:-1] if is_code else lines

    def wrap(selected_lines):
        content = "\n".join(selected_lines)
        if is_code:
            return (
                "Code excerpt (may be incomplete).\n"
                f"{opening}\n{content}\n```"
            )
        return content

    pieces = []
    current = []
    for line in content_lines:
        single = f"{prefix}\n\n{wrap([line])}"
        if count_tokens(single) > limit:
            raise ValueError("单行加标题仍超限，需要更细的切分")
        candidate = f"{prefix}\n\n{wrap(current + [line])}"
        if current and count_tokens(candidate) > limit:
            pieces.append(wrap(current))
            current = []
        current.append(line)

    if current:
        pieces.append(wrap(current))
    return pieces
def split_markdown_section(section: str, count_tokens, limit: int) -> list[str]:
    prefix, separator, body = section.partition("\n\n")
    if not separator:
        raise ValueError("小节缺少标题与正文分隔")

    parts = re.split(
        r"(^```[^\n]*\n.*?^```[ \t]*$)",
        body,
        flags=re.MULTILINE | re.DOTALL,
    )
    units = []
    for part in parts:
        if part.startswith("```"):
            units.append(part.strip())
        else:
            units.extend(p.strip() for p in part.split("\n\n") if p.strip())
    normalized = []
    for unit in units:
        if count_tokens(f"{prefix}\n\n{unit}") <= limit:
            normalized.append(unit)
        else:
            normalized.extend(split_large_unit(prefix, unit, count_tokens, limit))
    units = normalized
    chunks = []
    current = ""
    for unit in units:
        single = f"{prefix}\n\n{unit}"
        if count_tokens(single) > limit:
            raise ValueError(
                f"单个内容单元超过 {limit} token：{prefix}"
            )
        combined = f"{current}\n\n{unit}" if current else unit
        candidate = f"{prefix}\n\n{combined}"
        if count_tokens(candidate) <= limit:
            current = combined
        else:
            chunks.append(f"{prefix}\n\n{current}")
            current = unit

    if current:
        chunks.append(f"{prefix}\n\n{current}")
    return chunks
def chunk_document(
    text: str,
    strategy: str,
    chunk_size: int = 150,
    overlap: int = 30,
    count_tokens=None,
    max_tokens: int | None = None,
) -> list[str]:
    if strategy == "fixed":
        return chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

    if strategy == "paragraph":
        return chunk_by_paragraph(text)
    if strategy == "markdown_sections":
        return chunk_markdown_sections(text)
    if strategy == "markdown_tokens":
        if count_tokens is None or max_tokens is None:
            raise ValueError("markdown_tokens 需要计数函数和 token 上限")
        chunks = []
        for section in chunk_markdown_sections(text):
            chunks.extend(
                split_markdown_section(section, count_tokens, max_tokens)
            )
        return chunks
    raise ValueError(f"unknown chunking strategy: {strategy}")
