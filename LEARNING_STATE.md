# 学习状态（替换更新，不追加聊天流水账）

更新：2026-09-30。接续核验依据：读取项目代码、实验记录与 Git 状态；本轮未运行模型或 API。此前验证保留原执行主体与结论边界。

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
- 用户正确判断“先说不知道，再给出候选块不支持的答案”属于拒答失败，能以候选证据约束解释原因；已完成生成检查脚本的两处填空。
- 已表现出理解：向量数量与维度、模型/FAISS 分工、距离非答案保证、列表/字典、return、请求期与启动期分工。
- 已练习：enumerate、列表推导式、JSON、布尔计数、argparse；仍需独立迁移检验，不能等同熟练掌握。
- 曾混淆容器类型与维数、append 与类型转换、start=1；已纠正。
- 曾因嵌套循环缩进错误重复评测 q5，已修复；继续关注缩进和变量作用范围。

## 实验与 Git
- 已建立开发/独立测试分离：开发集现为9题，独立测试集5题，均含 source 字段；独立测试题不参与调参。用户以两文档、paragraph、Top-1 实际运行：开发集9/9、独立测试集4/5。新增第二文档的四题均命中；test_1 仍为排序失败（证据存在但 Top-1 返回 chunk_id=2、距离1.1497）。题集大小改变，不能将2/3与4/5解释为同口径提升。细节、局限和复现命令见 docs/experiments.md。
- 2026-09-20 本轮实际核验 HEAD：fb11308，已提交 eval_retrieval.py 参数化、README.md、AGENTS.md、LEARNING_STATE.md、docs/experiments.md；等待提交步骤已完成。此前 77c63e3（段落切块 smoke test）、e257d38（评测）。无远程仓库配置。
- 2026-09-29 用户完成阶段验收：test_eval_data.py 输出开发集9题、测试集5题、共14个唯一 id；test_prepare.py 通过；test_multi_document.py 通过并命中 data/rag_operations.txt 的 chunk_id=6。后者加载本地 Embedding 成功。
- 2026-09-29 已完成本地提交 `feat: add traceable multi-document retrieval`，包含多文档检索、来源追踪、两类题集评测、`/prepare`、引用校验和对应轻量检查。根目录未跟踪的 main.py 未纳入提交，保留不动。

## 历史里程碑（当前行动以新版计划为准）
1. 已完成提交核验并进入新阶段；不重复参数验证，不再扩展CLI选项。
2. 开发/独立测试分离和双题集评测函数、以及无需模型/API 的数据结构检查已由用户完成；测试集成绩只记录，不据此调参。test_1 已确认属于“证据存在于块中，但 Top-1 排序未返回”的失败。VectorStore 的来源、块编号与距离已贯通至评测和 API；`/search` 可无密钥运行，`/query` 缺少密钥时返回503；服务配置可由 `/config` 和 `/documents` 读取；多文档服务和来源映射测试均已验证；服务与该测试已统一使用 paragraph 策略。
3. 已完成文档外距离观察模块：data/ood_dev_cases.json 与 data/ood_test_cases.json 各4题、两类各2题；test_ood_data.py 由用户运行通过。observe_distances.py 复用服务配置建索引，分别观察开发13题与测试9题，结果保存在 docs/distances_development.json 和 docs/distances_test.json；当前 SPLIT="test"。助手实际检查报告与题集、配置、来源文本一致，并汇总原始距离；未重跑模型。具体统计与限制见 docs/experiments.md。
4. 开发集相关但缺证据题距离小于部分证据足够题，单一“小距离放行”阈值不能完美区分当前样例；独立测试距离范围也重叠，但 test_1 仍是已知排序失败。answerable 是知识库层标签，不代表 Top-1 证据足够。本轮没有设置阈值或验证生成拒答率。
5. 文档外距离观察模块已提交：本轮实际核实 HEAD 为 `84633da feat: add out-of-document retrieval distance diagnostics`，包含题集、观察脚本、两份距离报告和记录；核验时工作区仅有未跟踪的根目录 main.py，保留不动。此前“待用户自行提交”描述已过时。
6. 用户已确认调整带教投入：根据实际掌握程度、实习目标与核实的岗位需求动态取舍，区分项目必需与教学扩展，避免持续增加低收益验证工具。此前提出的13题交互标注脚本 diagnose_evidence.py 暂不要求实现。
7. 生成层小样例验证已完成：用户运行 check_generation.py，复用开发集保存的Top-1候选块；助手读取代码及 docs/generation_development.json 确认 ops_dev_1 正确回答且引用对应块，ood_dev_1 与 ood_dev_3 均仅回答 I don't know.。本轮助手没有重发模型请求。详细条件与限制见 docs/experiments.md；未设置距离阈值、未修改提示词、未使用独立测试集调参。这三题单次结果不证明稳定拒答，也不是完整API验收。
8. 2026-09-30 核实生成验证模块已提交为 `e0d9c11 test: check generation grounding on development examples`。随后用户完成 app/static/index.html 和首页 FileResponse：同源调用 /query，固定Top-1，显示答案、候选来源、等待及错误状态。用户提供来源元数据问题的成功页面结果；助手读取代码确认，并在用户修复路由后实际GET验证首页返回200且包含表单、/documents返回2份文档9块；未重发生成请求。重复首页路由和误删文档列表接口的问题已修复。README已补本地演示说明。本次用户明确要求助手执行提交；默认后续仍由用户提交。根目录 main.py 保留不动。
9. 页面模块已提交为 `908601c feat: add browser question answering page`。2026-09-30 用户完成自定义资料目录模块：settings.py 通过 RAG_DOCUMENT_DIR 读取目录第一层UTF-8 txt/md文件，未设置时保留原两文档；Markdown按普通文本处理。knowledge/demo.md 是虚构示例手册。助手已实际GET确认1份文档3块，并通过 /search 定位维护者问题的Top-1排序失败：简介#0排第一，含Maya Chen的#1排第二。页面已由用户改为Top-3，用户随后报告完成；助手确认代码修改，未独立读取该次生成答案或重发API请求。细节见 docs/experiments.md。
10. 2026-09-30 接续实际核实 HEAD 为 `a5bfa7a feat: support custom document directories`，资料目录模块及记录已提交；核验时工作区仅有未跟踪的根目录 main.py，保留不动。默认后续仍由用户提交。运行旧评测前清除 RAG_DOCUMENT_DIR；新增资料需重启重建索引。页面错误分支与按钮状态尚未逐项浏览器验收。页面引用模块已由用户完成：展示后端 citations 的来源、块编号和可展开原文，空列表显示说明；请求开始时清空旧引用。助手读取差异确认实现与清空位置正确，git diff --check 通过；用户报告完成，助手未独立查看浏览器答案或调用生成 API，具体页面输出及错误分支仍未独立核验。接续核实本模块及记录已提交为 `6f06a66 feat: display answer citations in browser`；核验时仅根目录 main.py 未跟踪。生成异常处理模块已由用户完成：客户端 timeout=30.0、max_retries=0；/query 按具体异常优先的顺序处理超时、连接失败、限流及其他上游状态错误。助手实际通过 TestClient 跳过 lifespan、注入模拟 pipeline 验证四个 HTTP 分支及 detail：504/503/503/502；模拟客户端构造确认超时与重试参数，语法和差异检查通过。未加载模型、未调用真实 API，未验证真实网络超时或浏览器错误展示。用户能判断异常顺序影响，已纠正为“异常抛出后按顺序匹配 except”。接续已核实异常处理模块提交为 `35e4af7 fix: handle generation timeouts and upstream errors`，工作区仅根目录 main.py 未跟踪。下一小步为成功问答返回准备阶段、生成阶段与问答流程总耗时，并在页面显示；准备阶段包含检索与提示词构建，不能标成纯检索耗时。用户已实现并报告 test_prepare.py 链路检查通过；助手读取后端和页面差异，实际用模拟计时验证 prepare=125.0、generation=500.0、total=650.0 ms，以及全零耗时情况通过；未调用真实模型、未独立验收浏览器显示。局部计时变量已使用，解释了共享实例属性可能被并发请求覆盖；尚不据此认定独立掌握。2026-10-09核实耗时模块已提交为 `c739627 feat: expose question answering stage timings`；工作区仅根目录main.py未跟踪，不新增评测脚本。继续功能与工程实践，不重复距离/拒答实验，不默认新增评测脚本。

## 当前断点与下一步（2026-10-10）

- 用户目标：2027年寒假开始的北京LLM应用/RAG/Agent实习；RAG外再做独立Agent，主项目按最终质量决定。是否可学期中延续3–4个月、每周4天到岗待与学校确认，不能默认满足。
- 已实现真实FastAPI六篇固定版本资料下载、代码引用展开、带标题的token预算切块、超限入库保护；新资料服务已核验6篇127块。模型max_seq_length=256，最终块最大255 tokens，代码片段不保证独立运行。
- 检索进展：向量、BM25及RRF已实现。固定两路各Top-10、RRF常数60、最终Top-3。用户在补全等价证据标注后的开发集报告向量5/6、融合6/6；助手检查实现并复核早一轮排序，未独立重跑最新标注统计。原4/6、旧口径5/6保留，不把标注修正本身称算法提升。
- 用户已将固定融合接入RAGPipeline.retrieve，/search、/prepare、/query共用；两路各Top-10、RRF常数60，默认最终Top-3，保留请求top_k控制最终数量。服务结果含rrf_score和ranks，不含原向量score或lexical_score；/config公开策略。用户运行test_prepare.py通过；助手读取差异确认，并实际请求本地/config、/documents、/search、/prepare：6篇127块，HTTPException问题返回3条，两接口候选完全一致且三条标签与原文均进入prompt；第一条#18，vector=2、lexical=7，rrf_score=0.031054405392392875。未调用/query或重跑评测；新语料生成答案、干净环境部署及成本/耗时对比尚未验收。
- data/fastapi_test_cases.json六题已冻结，当前SHA256仍为eb888ad99dceeec3cebdedb33fc116f00bde69dd6bf1d261f53e12b72a08a563；用户实际完成独立测试并提供完整输出：向量3/6、融合4/6；第2题新增命中，第3/5题两路最终均未匹配指定证据，其他命中保持。助手核验冻结文件哈希未变并读取输出，未重跑留出检索。固定方案验收已收束，不用其输出挑参数、换标注或追分；详细条件及边界见experiments。
- 结果无论提高/持平/退步，记录同口径事实，不反复试留出集。若发现实现缺陷应修复并说明重跑原因；若是标注歧义保留原结果并单独记录人工核查，不静默改题。
- 2026-10-10核实HEAD为 `7eb8057 feat: serve hybrid retrieval with explicit score semantics`，融合服务接入及记录已提交；根目录main.py未跟踪，保留不动。用户提供真实首页生成结果：HTTPException问题正确回答应raise，引用#18原文直接支持；准备25.7 ms、生成991.1 ms、总流程1016.8 ms。助手读取用户输出并核对支持关系，未重发生成请求或独立查看浏览器。该次演示完成，不代表整体准确率或稳定延迟；费用尚未计量。
- 独立目录复现已完成：用户报告本地克隆rag-qa-system-repro、uv sync --locked及8001服务验收通过；助手核实副本HEAD为7eb8057、工作区干净，并实际请求8001/config、/documents、/search，确认固定配置、6篇127块、候选18/36/16及首项分数一致。复用模型缓存，不等于全新电脑或容器部署，未重发生成。原项目新增文档记录待用户提交。下一小步为减少支架的独立Python修改：/config公开启动时实际Embedding上限与索引维度；不重复检索评测。
- 后续RAG顺序：固定方案的服务接入（准确区分L2/BM25/RRF字段与策略）、真实问题的演示与交付复现、一次减少支架的独立修改；再进入独立Agent的两个只读工具/参数校验/终止与失败出口。六篇六题只作第一阶段证据，按场景需要扩资料与问题覆盖，不靠堆框架或追加小脚本弥补代表性不足。
- 用户Python尚不熟，新代码需中文通俗解释输入输出、容器内数据、分支/循环执行顺序；保持15–40行、中等颗粒度支架，已掌握内容合并练习。细节见docs/experiments.md；整体计划见docs/learning_plan.md。

## 新会话验收
应能准确说明当前断点、服务/评测配置差异、指标含义，并提供下一小步；无需读取整段历史。
