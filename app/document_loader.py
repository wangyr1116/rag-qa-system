from pathlib import Path
def load_text_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with path.open("r", encoding="utf-8") as f:
        return f.read()

def load_text_files(file_paths: list[str]) -> list[tuple[str, str]]:
    documents = []

    for file_path in file_paths:
        text = load_text_file(file_path)
        documents.append((file_path, text))

    return documents