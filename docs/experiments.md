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

## 2026-09-29：文档外问题 Top-1 距离观察

- 题集：新增 data/ood_dev_cases.json 与 data/ood_test_cases.json，各4题，主题无关（unrelated）与主题相关但缺少答案（related_but_missing）各2题。分别与原有9道开发题、5道独立测试题合并观察，测试集结果不用于调参。
- 标注依据是两份入库文档是否支持回答，不是模型常识或项目代码能否提供答案。answerable 表示知识库可回答，不保证本次 Top-1 候选证据足够。
- 固定条件：sentence-transformers/all-MiniLM-L6-v2、FAISS IndexFlatL2（平方L2距离）、两文档、paragraph、9块、Top-1。配置中的 chunk_size=150、overlap=30 不参与当前段落切块。
- 用户运行 test_ood_data.py 通过（共8个唯一ID），并运行 observe_distances.py 保存开发13条、测试9条结果到 docs/distances_development.json 和 docs/distances_test.json。助手读取脚本确认，并实际执行无模型的一致性检查：记录与题集、配置、来源和块文本对应，距离有限且非负；重新汇总保存距离。助手没有重新计算 Embedding 或调用生成模型。

| 数据集 | 类别 | 数量 | 最小距离 | 中位数 | 最大距离 |
|---|---|---:|---:|---:|---:|
| 开发 | answerable | 9 | 0.4126 | 0.6047 | 0.8885 |
| 开发 | unrelated | 2 | 1.8552 | 1.8797 | 1.9041 |
| 开发 | related_but_missing | 2 | 0.7762 | 0.8231 | 0.8701 |
| 独立测试 | answerable | 5 | 0.5942 | 0.6583 | 1.1497 |
| 独立测试 | unrelated | 2 | 1.8325 | 1.8329 | 1.8332 |
| 独立测试 | related_but_missing | 2 | 0.9731 | 1.0204 | 1.0678 |

开发集中，缺少切块大小的 ood_dev_4（0.7762）和缺少注意力头数量的 ood_dev_3（0.8701），距离都小于证据足够的 ops_dev_1（0.8885）。因此“距离不超过阈值即放行”的单一规则无法将这些开发样例全部正确区分。

独立测试中，ood_test_4（0.9731）返回来源元数据说明，但没有保留天数；ood_test_3（1.0678）返回位置编码的作用，但没有数学公式。test_1（1.1497）仍返回 chunk_id=2，是已知的排序失败；知识库有证据不等于当前 Top-1 提供了完整证据。两组距离范围重叠不能直接等同于生成层拒答错误。

这些少量主题无关题距离较大，不能据此证明可稳定拒答。当前只完成检索距离诊断，没有设置拒答阈值、修改服务行为或测量实际生成拒答率。开发集相关缺证据中位数以保存的原始距离计算为0.8231，替代此前基于显示值估算的近似值。

复现（Windows CMD，项目根目录）：先在 observe_distances.py 设置 SPLIT="development"，运行下列命令；再改为 SPLIT="test"，执行同一命令。当前脚本保存为 test；同一 split 重跑会覆盖对应结果文件。

```bat
uv run python observe_distances.py
```

下一步：先在开发集逐题区分“知识库证据是否存在”与“当前候选证据是否足够”，再设计生成/拒答行为的验证；独立测试保持留出用途，不据此挑选阈值或改写题目。

## 2026-09-29：代表性开发样例的生成与拒答验证

- 为收束验证投入，采用3道代表性开发题，不再实现13题交互标注工具。check_generation.py 直接读取 docs/distances_development.json 的候选块，复用 build_qa_prompt 与 LLMClient；没有重跑检索、设置距离阈值或修改提示词，独立测试集没有参与。
- 代码配置使用 deepseek-chat、max_tokens=300；未显式设置 temperature。人工候选充分性仅用于记录，没有传入提示词。每题生成一次，完整提示词与回答保存于 docs/generation_development.json。
- 用户报告已运行；助手读取脚本与保存报告确认以下结果，未重新调用API。

| 开发题 | 人工候选判断 | 保存的实际生成表现 | 本次判定 |
|---|---|---|---|
| ops_dev_1 | 充分：说明来源元数据的作用 | 回答帮助用户核实答案出处，引用 data/rag_operations.txt 的 chunk_id=6 | 正确作答，引用块支持该答案 |
| ood_dev_1 | 不充分：候选只讨论Transformer，没有法国首都信息 | 仅回答 I don't know. | 成功拒答 |
| ood_dev_3 | 不充分：说明多头注意力作用，没有具体头数 | 仅回答 I don't know. | 成功拒答 |

- 结论：这3题的本次输出符合预期，可以结束当前小样例验证；不能据此宣称稳定拒答或泛化能力。检查直接调用生成客户端，没有覆盖完整API链路，也未通过本脚本调用引用过滤函数；此处引用支持性由阅读原文确认。
- 判定按答案含义进行：若先说不知道又补充无证据支持的答案，仍记为拒答失败，不能仅搜索拒答短语。
- 运行命令（Windows CMD，项目根目录且已设置 DEEPSEEK_API_KEY）：`uv run python check_generation.py`。结果文件存在时脚本会停止，防止误重跑；中途失败可能留下部分结果，应先检查而非直接删除重试。
- 后续重心转回功能与演示闭环，不再为本轮新增验证脚本。

## 2026-09-30：自定义资料目录与演示检索遗漏

- 用户通过 RAG_DOCUMENT_DIR=knowledge 加载虚构的 demo.md；助手实际请求 /documents 确认1份文档3块。原两文档可通过清除该变量后重启恢复，旧评测前也应清除变量。
- 问题：Who maintains the Cedar project handbook? 用户提供Top-1页面结果：候选为手册简介#0，回答 I don't know.。
- 助手调用 /search（Top-3，无生成调用）确认排序：简介#0距离0.4212866723537445；包含Maya Chen的维护者段#1距离0.42264994978904724；更新周期段#2距离0.547207772731781。知识库有答案，但Top-1未向生成层提供对应证据。
- 用户将页面 top_k 从1改为3后报告完成。助手检查代码确认修改；未独立读取这次生成答案，因此不记录为助手已核验的正确答案/引用。未使用独立测试集调参，不能据此认为Top-3普遍最优。
- 本模块已提交为 `a5bfa7a feat: support custom document directories`（2026-09-30 接续核验）；README与学习状态已同步。

## 2026-09-30：页面展示答案引用

- 用户完成 app/static/index.html：从 /query 的 citations 渲染可展开的来源、块编号和原文，与 sources 候选证据分区展示；无引用时显示说明。
- 请求开始时清空旧引用，避免等待或失败时残留上一题引用；助手读取最终差异确认位置正确，git diff --check 通过。
- 用户报告完成；助手未独立读取浏览器答案，未重发生成请求。不能将此记录视为实际答案正确性或所有页面分支的验收。
- 引用标签匹配候选块不等于语义支持校验，也不证明模型实际依赖该块。

## 2026-09-30：生成服务超时与异常映射

- 用户设置 LLMClient 的 timeout=30.0、max_retries=0，并在 /query 增加 SDK 异常分支。网络超时不等于整个接口的总耗时上限。
- 助手实际执行临时离线检查：TestClient 不进入上下文，不执行 lifespan；模拟 pipeline.ask 分别抛出 APITimeoutError、APIConnectionError、RateLimitError、APIStatusError。四个响应状态分别为504、503、503、502，且 detail 与预期中文提示完全一致。
- 模拟 OpenAI 构造函数确认收到 timeout=30.0 和 max_retries=0；py_compile 与 git diff --check 通过。临时检查未保存为新增脚本。
- 未实例化 Embedding、未调用真实生成 API、未读取真实密钥；以上验证覆盖异常到 HTTP 响应的转换，不证明真实网络超时或浏览器展示已验收。

## 2026-09-30：成功问答的分阶段耗时

- 用户实现 RAGPipeline.ask 的局部计时，返回 timings_ms（prepare、generation、total），页面展示三项毫秒数。prepare 含检索和提示词构建；generation 含首次客户端初始化及生成；total 含引用过滤，不含启动建索引、HTTP传输和页面渲染。仅覆盖成功请求。
- 用户报告 test_prepare.py 通过。助手实际临时模拟 perf_counter 读数10.0、10.125、10.625、10.650，断言结果分别为125.0、500.0、650.0 ms；相同读数产生全零耗时也通过，原答案和来源字段保留。
- 未加载模型或调用外部 API，未新增检查脚本，浏览器实际展示尚未独立验收。
