def fuse_rankings(rankings: dict, top_k: int = 3) -> list[dict]:
    merged = {}
    for channel, results in rankings.items():
        for rank, item in enumerate(results, start=1):
            key = (item["source"], item["chunk_id"])
            if key not in merged:
                merged[key] = {
                    "source": item["source"],
                    "chunk_id": item["chunk_id"],
                    "chunk": item["chunk"],
                    "rrf_score": 0.0,
                    "ranks": {},
                }
            merged[key]["rrf_score"] += 1.0 / (60 + rank)
            merged[key]["ranks"][channel] = rank

    ordered = sorted(
        merged.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )
    return ordered[:top_k]