import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

REVISION = "f5c6e9b4f9cadc1bf0f9a1fd672e621206b63007"
BASE = f"https://raw.githubusercontent.com/fastapi/fastapi/{REVISION}"
FILES = [
    "handling-errors.md", "response-status-code.md",
    "query-params.md", "path-params.md",
    "body.md", "response-model.md",
]
TARGET = Path(__file__).resolve().parent / "knowledge" / "fastapi"

def download(relative_path: str) -> bytes:
    with urlopen(f"{BASE}/{relative_path}", timeout=30) as response:
        return response.read()

def main():
    TARGET.mkdir(parents=True, exist_ok=False)
    records = []
    for name in FILES:
        relative = f"docs/en/docs/tutorial/{name}"
        content = download(relative)
        if not content.decode("utf-8").strip():
            raise ValueError(f"文档为空：{name}")
        (TARGET / name).write_bytes(content)
        records.append({
            "file": name,
            "url": f"{BASE}/{relative}",
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    (TARGET / "LICENSE").write_bytes(download("LICENSE"))
    manifest = {"revision": REVISION, "documents": records}
    (TARGET / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已保存 {len(records)} 篇文档：{TARGET}")

if __name__ == "__main__":
    main()