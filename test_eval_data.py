import json
from app.settings import SOURCE_PATHS

REQUIRED_FIELDS = {
    "id",
    "question",
    "expected_answer",
    "evidence",
    "source",
}

DATASETS = {
    "development": "data/eval_cases.json",
    "test": "data/test_cases.json",
}

all_ids = set()

for dataset_name, dataset_path in DATASETS.items():
    with open(dataset_path, encoding="utf-8") as f:
        cases = json.load(f)

    assert cases, f"{dataset_name} must not be empty"

    for case in cases:
        missing_fields = REQUIRED_FIELDS - case.keys()

        assert not missing_fields, (
            f"{dataset_name} case is missing: {missing_fields}"
        )
        assert case["source"] in SOURCE_PATHS, (
            f"{dataset_name} has an unknown source: {case['source']}"
        )
        assert case["id"] not in all_ids, (
            f"duplicate id: {case['id']}"
        )

        all_ids.add(case["id"])

    print(f"{dataset_name}: {len(cases)} cases checked")

print(f"all datasets: {len(all_ids)} unique ids")
