# 学习状态（替换更新，不追加聊天流水账）

更新：2026-09-29。状态依据：文件/Git 检查 + 用户提供的运行结果与保存报告 + 助手实际执行无模型的报告一致性检查；本轮未重新运行模型或 API。

## 目标与方式
本硕双九、软件工程，2026级研一，目标为 2027 年寒假在北京寻找 LLM 应用 / RAG / Agent 实习，不以当前秋招为目标。Python 能阅读，独立组织代码需带练。固定带教格式为：先讲问题与数据流，再给精确文件位置、15--40行左右的代码支架/挖空、逐行解释、命令与验收；每任务聚合1--3个紧密改动，保持中等颗粒度，避免过碎问答或大段成品，减少重复说明和无效往返。用户完成后解释结果再继续。核心代码由用户修改；助手在节点提醒状态记录、Git 检查和会话切换；用户自行执行 Git 提交。规则见 AGENTS.md。

## 当前实现
- 文档读取、固定字符与段落切块、MiniLM Embedding、FAISS IndexFlatL2、提示词、DeepSeek、FastAPI /query 已实现。
- 用户已验证问答、文档外拒答样例及非法请求 422；仅少量人工样例，不证明稳定拒答。
- app/main.py 与 test_multi_document.py 当前均使用 paragraph 策略；test_retrieval.py 包含付费模型调用，未在本轮运行。
- VectorStore 的检索结果已返回 `source`、`chunk_id`、`score`；多文档评测和 API 都按每个块对应的来源列表构建索引，用户已验证评测诊断输出来源字段。
- `POST /search` 已实现并由用户实际验证：在未设置 DEEPSEEK_API_KEY 时，服务仍可启动并返回带来源、块编号、距离、文本块的检索结果；LLM 在 `/query` 首次使用时才初始化。
- 用户实际验证：未设置 DEEPSEEK_API_KEY 时，`POST /query` 返回 HTTP 503 和 `{"detail":"未找到 DEEPSEEK_API_KEY"}`，而非启动期崩溃或不明 500。
- 服务配置已集中到 app/settings.py；用户已完成将服务切换为 `paragraph` 策略，并将 `chunk_document` 同时接入 app/main.py 与 test_multi_document.py。该选择来自既有开发集结果，未使用独立测试集调参；本轮仅核对代码，未重新运行 API。
- 服务已支持两个本地文档入库：data/sample.txt 与 data/rag_operations.txt。用户实际验证 `/search` 返回第二份文档的 `chunk_id=15`，来源为 data/rag_operations.txt；每个块的来源通过与 chunks 同下标的 sources 列表保存。
- test_multi_document.py 已由用户实际运行通过：验证特定问题命中第二份文档、返回 chunk/source 与同下标列表一致，并验证 chunks/sources 数量不一致时抛出 ValueError；只加载本地 Embedding，不调用 DeepSeek。
- 用户实际验证 `GET /documents`：服务已加载两份文档；固定切块时为19块。段落策略下预期为9块，尚未在本轮通过该端点重新记录。
- test_eval_data.py 已升级为开发/测试题集的数据结构检查，要求 `source` 属于 SOURCE_PATHS；题集现为开发集9题、测试集5题、共14个唯一 id，不加载模型或调用 API。
- eval_retrieval.py 仅检索评测，不调用生成模型；`evaluate_cases` 会分别评测 data/eval_cases.json（开发集）和 data/test_cases.json（独立测试集），并按服务相同的两文档集合建立索引。
- `POST /prepare` 已实现并由用户实际验证：无需 DeepSeek 密钥，返回问题、候选证据和带 `[source, chunk_id]` 标签的完整 prompt。`ask()` 现返回 `sources`（候选证据）与 `citations`（答案中出现且能在候选证据内验证的引用）两个不同字段。
- test_prepare.py 使用 FakeVectorStore 与 FakeLLMClient 验证检索结果进入带标签的 prompt、生成层收到该 prompt、有效引用被保留、虚构引用被过滤；不加载模型、不读 API Key，用户实际运行通过。
- --top-k、--chunking 切换和 top_k=0 拦截已由用户验证。
- --chunk-size、--overlap 已由用户于2026-09-20验证：fixed30/30提前报参数错误；fixed300/30、Top3得到7块、5/5。参数化里程碑完成。固定参数校验在读样本文档之后、模型实例化之前。

## 理解程度
- 已完成文档外题集与距离观察脚本练习；用户追问排序的必要性，已解释逐题排序用于定位类别交错，min/max/median 统计不依赖事先排序。尚不据此认定独立掌握。
- 已表现出理解：向量数量与维度、模型/FAISS 分工、距离非答案保证、列表/字典、return、请求期与启动期分工。
- 已练习：enumerate、列表推导式、JSON、布尔计数、argparse；仍需独立迁移检验，不能等同熟练掌握。
- 曾混淆容器类型与维数、append 与类型转换、start=1；已纠正。
- 曾因嵌套循环缩进错误重复评测 q5，已修复；继续关注缩进和变量作用范围。

## 实验与 Git
- 已建立开发/独立测试分离：开发集现为9题，独立测试集5题，均含 source 字段；独立测试题不参与调参。用户以两文档、paragraph、Top-1 实际运行：开发集9/9、独立测试集4/5。新增第二文档的四题均命中；test_1 仍为排序失败（证据存在但 Top-1 返回 chunk_id=2、距离1.1497）。题集大小改变，不能将2/3与4/5解释为同口径提升。细节、局限和复现命令见 docs/experiments.md。
- 2026-09-20 本轮实际核验 HEAD：fb11308，已提交 eval_retrieval.py 参数化、README.md、AGENTS.md、LEARNING_STATE.md、docs/experiments.md；等待提交步骤已完成。此前 77c63e3（段落切块 smoke test）、e257d38（评测）。无远程仓库配置。
- 2026-09-29 用户完成阶段验收：test_eval_data.py 输出开发集9题、测试集5题、共14个唯一 id；test_prepare.py 通过；test_multi_document.py 通过并命中 data/rag_operations.txt 的 chunk_id=6。后者加载本地 Embedding 成功。
- 2026-09-29 已完成本地提交 `feat: add traceable multi-document retrieval`，包含多文档检索、来源追踪、两类题集评测、`/prepare`、引用校验和对应轻量检查。根目录未跟踪的 main.py 未纳入提交，保留不动。

## 下一步（从这里继续）
1. 已完成提交核验并进入新阶段；不重复参数验证，不再扩展CLI选项。
2. 开发/独立测试分离和双题集评测函数、以及无需模型/API 的数据结构检查已由用户完成；测试集成绩只记录，不据此调参。test_1 已确认属于“证据存在于块中，但 Top-1 排序未返回”的失败。VectorStore 的来源、块编号与距离已贯通至评测和 API；`/search` 可无密钥运行，`/query` 缺少密钥时返回503；服务配置可由 `/config` 和 `/documents` 读取；多文档服务和来源映射测试均已验证；服务与该测试已统一使用 paragraph 策略。
3. 已完成文档外距离观察模块：data/ood_dev_cases.json 与 data/ood_test_cases.json 各4题、两类各2题；test_ood_data.py 由用户运行通过。observe_distances.py 复用服务配置建索引，分别观察开发13题与测试9题，结果保存在 docs/distances_development.json 和 docs/distances_test.json；当前 SPLIT="test"。助手实际检查报告与题集、配置、来源文本一致，并汇总原始距离；未重跑模型。具体统计与限制见 docs/experiments.md。
4. 开发集相关但缺证据题距离小于部分证据足够题，单一“小距离放行”阈值不能完美区分当前样例；独立测试距离范围也重叠，但 test_1 仍是已知排序失败。answerable 是知识库层标签，不代表 Top-1 证据足够。本轮没有设置阈值或验证生成拒答率。
5. 下一小步：在开发样例上明确区分知识库可回答性、候选证据充分性与生成拒答行为，先做证据充分性的逐题诊断，再设计生成层验证。独立测试结果只记录，不据此调参。此模块已到记录/Git检查节点，待用户自行提交；最近已核实提交仍为 bd2c82f，根目录 main.py 保留不动。

## 新会话验收
应能准确说明当前断点、服务/评测配置差异、指标含义，并提供下一小步；无需读取整段历史。
