import hashlib
import json
import re
from ingest_fastapi_docs import TARGET, REVISION, download

PATTERN = re.compile(r"\{\*\s+\.\./\.\./(docs_src/[\w/]+\.py)[^}]*\*\}")
OUTPUT = TARGET.parent / "fastapi_expanded"

def main():
    manifest = json.loads((TARGET / "manifest.json").read_text(encoding="utf-8"))
    if manifest["revision"] != REVISION:
        raise ValueError("原始资料版本与下载器版本不一致")
    OUTPUT.mkdir(exist_ok=False)
    cache = {}
    records = []
    for item in manifest["documents"]:
        source = TARGET / item["file"]
        text = source.read_text(encoding="utf-8")
        references = []
        for match in PATTERN.finditer(text):
            path = match.group(1)
            if path not in cache:
                cache[path] = download(path).decode("utf-8")
            code = cache[path]
            replacement = f"```python\n{code.rstrip()}\n```"
            text = text.replace(match.group(0), replacement)
            references.append(path)
        if "{*" in text:
            raise ValueError(f"仍有未处理的引用：{source.name}")
        encoded = text.encode("utf-8")
        (OUTPUT / source.name).write_bytes(encoded)
        records.append({
            "file": source.name,
            "code_sources": sorted(set(references)),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        })
    (OUTPUT / "LICENSE").write_bytes((TARGET / "LICENSE").read_bytes())
    result = {"revision": REVISION, "documents": records}
    (OUTPUT / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已展开 {len(records)} 篇文档，下载 {len(cache)} 个代码文件")

if __name__ == "__main__":
    main()