import json

DATASETS = {
    "development": "data/ood_dev_cases.json",
    "test": "data/ood_test_cases.json",
}
REQUIRED_FIELDS = {"id", "question", "category", "reason"}
CATEGORIES = {"unrelated", "related_but_missing"}
all_ids = set()

for dataset_name, dataset_path in DATASETS.items():
    with open(dataset_path, encoding="utf-8") as f:
        cases = json.load(f)
    assert isinstance(cases, list) and cases, dataset_name
    category_counts = dict.fromkeys(CATEGORIES, 0)

    for case in cases:
        assert isinstance(case, dict), case
        missing_fields = REQUIRED_FIELDS - set(case.keys())
        assert not missing_fields, f"missing fields: {missing_fields}"
        for field in REQUIRED_FIELDS:
            assert isinstance(case[field], str) and case[field].strip(), field
        assert case["id"] not in all_ids, f"duplicate id: {case['id']}"
        all_ids.add(case["id"])
        assert case["category"] in CATEGORIES, case["category"]
        category_counts[case["category"]] += 1  # 用当前题的类别选择计数项

    assert all(count > 0 for count in category_counts.values()), category_counts
    print(f"{dataset_name}: {len(cases)} cases checked; {category_counts}")

print(f"total: {len(all_ids)} unique ids")