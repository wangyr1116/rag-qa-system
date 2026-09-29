# 检索实验记录

## 数据、指标与证据来源
- 数据：data/sample.txt 与 data/rag_operations.txt，两篇短英文文档；开发集：data/eval_cases.json，共 9 题；独立测试集：data/test_cases.json，共 5 题。
- 模型：sentence-transformers/all-MiniLM-L6-v2；索引：FAISS IndexFlatL2，返回平方L2距离，越小越近。
- 每题命中：Top K 中至少一个块包含 evidence 的完整原样字符串；每题最多计数一次。
- evidence_available：全部块中是否至少一块包含完整 evidence，用于区分证据切断与检索排序问题。
- 下列结果来自用户提供的运行输出，2026-09-19整理；本次文档维护没有重新运行模型。

## 已观察结果
| 切块方式 | 字符大小 | 字符重叠 | 块数 | K | 命中题数 |
|---|---:|---:|---:|---:|---:|
| fixed | 150 | 30 | 15 | 3 | 2/5 |
| fixed | 300 | 30 | 7 | 3 | 5/5 |
| paragraph | 不适用 | 不适用 | 6 | 3 | 5/5 |
| paragraph | 不适用 | 不适用 | 6 | 1 | 5/5 |
| paragraph（开发集） | 不适用 | 不适用 | 6 | 1 | 7/7 |
| paragraph（独立测试集） | 不适用 | 不适用 | 6 | 1 | 2/3 |
| paragraph（两文档、开发集） | 不适用 | 不适用 | 9 | 1 | 9/9 |
| paragraph（两文档、独立测试集） | 不适用 | 不适用 | 9 | 1 | 4/5 |

fixed150：q1/q2完整证据存在且命中；q3/q4/q5完整证据不在任何单块中。提高K不能补回单块内不存在的完整字符串。
q5返回文本虽缺少标注前缀“A RAG”，仍包含语义上可回答的信息，因此严格匹配失败不等于不能回答。

## 复现命令（Windows CMD，项目根目录）
前两条切块方式切换已由用户实际验证：
```bat
uv run python eval_retrieval.py --chunking fixed --top-k 3
uv run python eval_retrieval.py --chunking paragraph --top-k 3
```
段落Top1也已验证：
```bat
uv run python eval_retrieval.py --chunking paragraph --top-k 1
```
下面完整参数命令与边界命令已由用户于2026-09-20运行验证；300字符结果与此前手动修改参数取得的结果一致：
```bat
uv run python eval_retrieval.py --chunking fixed --chunk-size 300 --overlap 30 --top-k 3
uv run python eval_retrieval.py --chunking fixed --chunk-size 30 --overlap 30
```
第一条实际7块、5/5；第二条实际输出参数错误并退出，未出现模型加载进度。证据来源为用户粘贴的运行日志，非助手本轮复跑。评测不调用DeepSeek，但首次加载Embedding可能联网下载。

2026-09-20：用户在未调整参数的前提下运行 `uv run python eval_retrieval.py --chunking paragraph --top-k 1`。开发集为 7/7，独立测试集为 2/3。评测脚本现用 `evaluate_cases` 分别读取两个题集；独立测试结果只记录，不用于本轮调参。

独立测试逐题诊断：test_1 未命中，`evidence_available=True`，但 Top-1 返回 `chunk_id=2`、平方 L2 距离 1.1497，未返回含目标 evidence 的块；这是排序失败，不是证据被切断。test_2 命中（chunk_id=2，距离0.6146）；test_3 命中（chunk_id=5，距离0.6991）。

2026-09-28：用户将每题的 `source` 纳入题集，并让评测按服务的两文档集合构建索引。以 paragraph、Top-1 实际运行：开发集 9/9，独立测试集 4/5。新增的第二文档开发题 `ops_dev_1`/`ops_dev_2` 命中，新增独立测试题 `ops_test_1`/`ops_test_2` 命中；原 `test_1` 仍是唯一失败。初始重试曾出现 Hugging Face 连接拒绝，随后权重从缓存成功加载且完整评测输出完成。独立测试集由 3 题扩到 5 题，因此 2/3 与 4/5 不构成同口径的性能提升比较。

## 结论边界
- 这是五题证据字符串命中率，不是问答准确率，也不是标准相关文档Recall的完整评估。
- 题集仍很小，开发集与原文用词接近，已参与调参；独立测试集只有5题、来自两篇短文档。9/9 与 4/5 不能证明泛化，只能暴露当前配置在留出问法上的一次失败。
- 不同策略的块数和检索文本量不同，Top K相同不等于上下文预算相同。
- 段落切块没有最大长度保护；真实文档需要考虑超长段落和模型截断。
- 当前服务与多文档评测都使用 paragraph 策略；离线证据命中率仍不能直接作为生成答案质量或线上服务质量。
- 若要比较语义可回答性、生成正确性、引用质量，需要独立指标和更多题目。
