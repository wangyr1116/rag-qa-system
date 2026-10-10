import os
from pathlib import Path

def resolve_source_paths() -> list[str]:
    directory = os.getenv("RAG_DOCUMENT_DIR", "").strip()
    if not directory:
        return ["data/sample.txt", "data/rag_operations.txt"]
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"资料目录不存在或不是文件夹：{root}")
    paths = sorted(
        path for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}  # TODO 1：扩展名转小写后属于 .txt 或 .md
    )
    if not paths:
        raise ValueError(f"资料目录中没有 txt 或 md 文件：{root}")
    empty_paths = [path for path in paths if not path.read_text(encoding="utf-8").strip()]
    if empty_paths:
        raise ValueError(f"资料文件内容为空：{empty_paths}")
    return [str(path) for path in paths]  # TODO 2：将 Path 对象转为字符串

SOURCE_PATHS = resolve_source_paths()
CHUNKING = os.getenv("RAG_CHUNKING", "paragraph").strip()
if CHUNKING not in {"fixed", "paragraph", "markdown_sections", "markdown_tokens"}:
    raise ValueError(f"未知切块策略：{CHUNKING}")
CHUNK_SIZE, CHUNK_OVERLAP = 150, 30