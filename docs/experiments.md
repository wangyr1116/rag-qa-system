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

## 2026-10-09：真实文档的Markdown结构切块

- 六篇展开后的FastAPI英文资料已核对SHA-256匹配、无残留代码引用占位符。paragraph切分为714块，76块仅标题，98块含奇数个三反引号围栏。
- 用户实现markdown_sections；助手实际验证共76块，无孤立标题块，围栏配对；小样例验证代码注释不作为标题、末节保留、未闭合围栏报错通过。
- 助手仅用缓存AutoTokenizer计数（含特殊token），并读取缓存sentence_bert_config.json确认SentenceTransformer的max_seq_length为256；这与tokenizer自身512上限不同。35/76块超过256，最长663 tokens；尚未计算Embedding或运行生成。
- 各文件块数/超限数：body 11/4、handling-errors 13/7、path-params 20/6、query-params 6/3、response-model 22/12、response-status-code 4/3。
- 下一步先加超长块校验，再实现针对长小节的切分；未切换默认服务策略，未开展检索效果比较。

## 2026-10-09：入库文本块长度保护

- 用户在VectorStore.build_index参数检查后、修改元数据和调用encode前加入validate_chunk_lengths；使用实际模型tokenizer（padding=False、truncation=False）及max_seq_length，报告超限数量和前五个编号/长度。
- 助手实际临时离线验证：模拟tokenizer返回256 token时允许FAISS建索引；返回257时抛ValueError，encode未被调用，原索引与文本/来源元数据保持不变。语法与Git差异检查通过，未实例化真实模型、未调用生成API、未新增脚本。
- 保护只覆盖入库文本块；查询长度保护尚未实现。当前35个超长Markdown小节仍未修复，不能以已加校验认定资料已可入库。

## 2026-10-09：小节内按token预算组合完整单元

- 用户实现split_markdown_section，代码围栏作为整体，其他正文按空行分段，每块保留小节标题并按传入的计数函数与limit校验。
- 助手实际用小样例验证恰好预算通过、单元超预算报错、标题重复保留、正文重组无遗漏和含空行代码保持完整。
- 六篇展开文档使用缓存tokenizer、256预算：69/76个小节成功得到105个合格块，7个小节明确报错；handling-errors有3个、response-model有3个、response-status-code有1个。这7个小节尚未生成合格块，不能宣称全部资料已经入库。未计算Embedding、未调用API或新增评测脚本。

## 2026-10-09：超长单元兜底切分

- 用户实现split_large_unit并接入小节预算组合：正文按行、代码按行组合并补围栏及Code excerpt (may be incomplete).标记；单行加标题仍超限时报错。
- 助手实际使用缓存tokenizer检查全部76小节成功生成127块，最大255 tokens；各文件块数/最大token：body 15/255、handling-errors 26/254、path-params 28/253、query-params 10/250、response-model 40/253、response-status-code 8/254。共12个代码片段标记。
- 标题保留、围栏配对、过滤新增说明和围栏后非空白内容行顺序及缩进与原小节一致，单行仍超限错误路径通过。空白分隔可能变化，代码片段不保证独立运行。尚未建索引、运行检索或生成，不能宣称检索效果提升。

## 2026-10-10：六题真实语料开发基线与标注局限

- 用户运行eval_retrieval.py：markdown_tokens、127块、Top-3、六题单证据字符串+来源匹配，4/6（66.7%）；六题标注证据均存在于某个块。用户输出中的第5题Top-3为110/118/107，第6题为83/13/84。助手读取脚本确认配置与路径归一化，不重跑向量检索。
- 助手使用缓存tokenizer重建相同切块并读取对应块：第6题#13明确陈述Pydantic模型参数来自request body，属于单一证据字符串导致的漏判；第5题#118仅陈述过滤private data，对题目所问所有未声明字段的支持不足，暂记候选证据偏弱，不按完整支持通过。
- 原4/6是指定证据字符串命中率，不是答案准确率，也不等于2题真正缺证据。下一步仅为开发标注增加经人工核对的可替代完整证据，并复用既有评测函数；改口径后另记结果，不能称为检索性能提升。未用独立测试调参，未调用生成API。

## 2026-10-10：标注修正与第5题召回诊断

- 用户修复matches_evidence的显式字段分支后实际报告多证据Top-3命中5/6（83.3%）。原单证据4/6保留；该变化是标注覆盖修正，不是检索提升。
- 本轮localhost服务未运行，助手改用缓存模型路径并启用离线模式，实际计算127块Embedding并检索第5题完整排序；指定直接证据排第20，Top-10编号为110/118/107/96/112/114/90/106/104/91，前三及距离与用户基线一致。没有调用生成API。对Top-10只做重排无法补回第20位的指定证据，但更宽召回或其他策略尚未比较。
- 在引入关键词通道前冻结data/fastapi_test_cases.json六题，SHA-256为eb888ad99dceeec3cebdedb33fc116f00bde69dd6bf1d261f53e12b72a08a563；助手仅核对标注证据在语料中和ID不重复，没有对留出题运行检索，不用其结果选算法或参数。这是同语料留出问题小样本，不证明跨领域泛化，也未保证所有同义证据都已标注。
- 下一步用户用rank-bm25增加独立关键词候选通道，仅在开发题观察Top-10证据位置；向量Top-3判定保持基线，不提前称为混合检索成功。

## 2026-10-10：BM25独立关键词候选

- 用户增加rank-bm25依赖及VectorStore.search_lexical，报告第5题直接证据在关键词Top-10中排第7。助手读取实现确认小写、保留下划线的词匹配与BM25分数降序正确。
- 助手实际仅用缓存tokenizer重建文本块和BM25索引（未计算向量）复核全部开发题关键词证据排名为7/1/1/1/7/3；纯标点查询返回空列表通过。独立测试未运行。
- 关键词通道补充了候选，尚未证明最终Top-3改善；向量基线仍为用户报告5/6。下一步用户实现固定两路各Top-10、rank_constant=60的RRF融合，并在开发集并列比较最终Top-3，不直接相加BM25分数与L2距离，不切换线上检索。

## 2026-10-10：RRF融合与第5题另一处完整证据

- 用户实现fuse_rankings：同源/同chunk去重，每路排名贡献1/(60+rank)，降序；开发集报告向量Top-3和融合Top-3均5/6。助手读取代码确认，并实际离线重建127块索引复核六题两种判定相同，唯一未命中标注的是第5题。去重/贡献累加小样例通过。独立测试未运行，未调用生成API。
- 第5题固定每路Top-10的候选并集为17块，原指定证据#89在融合中排14（仅关键词rank7）。融合前三为#91/#112/#90；RRF分数约0.030415/0.029877/0.029631，前排是两路共同推荐的块。融合排序不再按L2距离。
- 助手随后读取#91，确认有完整等价支持：We want FastAPI to keep **filtering** the data using the response model. So that even though the function returns more data, the response will only include the fields declared in the response model. 原单句标注再次漏掉等价证据，不能以原5/6认定融合没有候选质量变化。
- 下一步用户为第5题补上经核对的evidence_any（原句与#91原句），固定算法与参数并列复跑；预期向量5/6、融合6/6，但尚未运行确认。保留旧口径，不将标注补全导致的数字变化本身称为算法提升；新开发集六题过小，不能声称稳定泛化。

## 2026-10-10：完善开发标注后的固定方案结果

- 用户补全第5题evidence_any后报告同口径开发六题：向量Top-3为5/6（83.3%），RRF Top-3为6/6（100%）；助手读取标注确认新增完整等价支持，未独立重跑该次统计。两路候选各10、RRF常数60、127块资料不变。
- 该比较显示本小开发集固定融合候选更好覆盖标注支持，不能解释为答案准确率、稳定提升或泛化保证。旧单证据及部分多证据口径成绩均保留。
- 助手核验留出文件校验值仍等于冻结值，下一步用户运行固定配置的六题留出比较；当前尚无独立测试结果。

## 2026-10-10：固定方案独立测试验收

- 用户实际运行冻结的fastapi_test_cases.json六题：markdown_tokens、127块，向量Top-3为3/6（50.0%），两路各Top-10、常数60的RRF最终Top-3为4/6（66.7%）。助手读取用户完整输出并核验冻结文件SHA-256仍一致，没有重新运行留出检索。
- 逐题向量/融合命中：test_1 True/True，test_2 False/True，test_3 False/False，test_4 True/True，test_5 False/False，test_6 True/True。关键词Top-10证据排名为2/1/5/1/3/1；六题指定证据均存在于某个块。
- 融合新增第2题命中，没有原命中题退步；第3、5题虽在关键词候选中仍未进入最终Top-3。按此冻结标注记录剩余失败，不通过修改题目、标注、候选数、RRF常数追分。单证据字符串指标仍可能遗漏其他同义支持，当前未进一步人工审查留出候选，不能把未命中直接称答案错误。
- 同口径小样本净增1题，不能证明稳定或显著提升。独立测试含同一语料的新事实问题，不代表跨领域泛化；未调用生成模型，不是答案准确率评测。固定方案留出阶段收束，不继续重跑调参。
- README已补资料启动、两路检索对照、实际成绩和边界；线上仍为纯向量检索。下一步提交本批里程碑并切新会话，再接固定融合方案的API与明确结果字段，完成必要演示和交付验证。

## 2026-10-10：固定融合接入服务

- 接续核实资料与评测已提交为07c60f4。用户修改RAGPipeline.retrieve：两路各取10条，复用常数60的fuse_rankings，最终数量由请求top_k控制，默认3；/search、/prepare、/query共用入口。/config新增retrieval说明。
- 服务候选包含source、chunk_id、chunk、rrf_score、ranks；rrf_score越大越靠前，ranks为各路从1开始的候选名次，缺席表示未进入该路Top-10。没有将原平方L2距离或BM25分数混称融合分数，也不能把RRF分数当答案可信度。
- 用户实际运行test_prepare.py通过，假关键词通道返回空列表，验证两路请求数量、单路融合字段及原提示词/生成/引用链路；助手读取差异确认，git diff --check通过。
- 用户启动真实资料服务并报告6篇、两接口候选一致。助手实际请求本地/config、/documents、/search、/prepare复核：markdown_tokens、6篇127块、固定融合配置；问题Should I raise or return HTTPException?、top_k=3，两接口候选完全一致，三条来源标签和原文均进入prompt。
- 第一条来自handling-errors.md，chunk_id=18，vector名次2、lexical名次7，rrf_score=1/62+1/67=0.031054405392392875；正文直接说明raise而非return。该核验只确认服务接入及准备链路，不是新增检索评测或生成质量验收；未调用真实生成、未重跑留出集或调参。
- 下一步在首页用该问题做一次生成演示，检查答案、引用原文和阶段耗时；随后完成交付复现。

## 2026-10-10：真实资料首页生成演示

- 已核实融合服务接入提交为7eb8057。用户在首页提问Should I raise or return HTTPException?，提供完整页面输出：You should raise it, not return it.，引用handling-errors.md的chunk_id=18；候选编号18/36/16。
- 助手根据用户输出人工确认#18原文明示应raise而非return，与答案支持关系成立。用户页面显示准备25.7 ms、生成991.1 ms、流程1016.8 ms；准备包含融合检索与提示词构建，生成可能含首次客户端初始化，总流程还包含引用处理。本次未记录用量或费用。
- 这是用户实际执行的一次端到端演示；助手未独立浏览页面、未重发生成请求。只确认此样例成功，不证明整体答案准确率、稳定拒答或平均延迟，未开展前后耗时对比。下一步为独立目录的锁定依赖启动复现。

## 2026-10-10：独立目录启动复现

- 用户报告通过：从本地仓库克隆到D:\llm-learning\rag-qa-system-repro，uv sync --locked安装依赖，设置真实资料目录和markdown_tokens，按指导清空新窗口生成密钥，8001启动及/documents、/search通过。助手未重新安装依赖或读取环境密钥。
- 助手实际核实副本HEAD为7eb8057、Git工作区干净，并请求8001/config、/documents、/search：固定两路Top-10/RRF60/default Top-3，6篇127块；HTTPException问题返回18/36/16，首项rrf_score=0.031054405392392875、vector=2/lexical=7，与原服务一致。未调用生成接口或重跑题集。
- 该结果验证已提交代码在独立目录和新虚拟环境中的启动复现，仍可能共享uv及Embedding缓存，不代表全新电脑、容器或无缓存下载已通过。副本保留供用户复现使用；原目录继续作为学习主目录。
