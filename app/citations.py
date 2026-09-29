import re

CITATION_PATTERN = re.compile(
    r"\[source: (?P<source>[^,\]]+), chunk_id: (?P<chunk_id>\d+)\]"
)


def find_valid_citations(
    answer: str,
    sources: list[dict],
) -> list[dict]:
    available_sources = {
        (item["source"], item["chunk_id"]): item
        for item in sources
    }

    citations = []
    seen_keys = set()

    for match in CITATION_PATTERN.finditer(answer):
        key = (
            match.group("source"),
            int(match.group("chunk_id")),
        )

        if key in available_sources and key not in seen_keys:
            citations.append(available_sources[key])
            seen_keys.add(key)

    return citations