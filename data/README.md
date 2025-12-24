## 数据说明

### 文件说明

- cases.jsonl：从 WPML 官网 Available Solutions 抓下来的“原始样本集”（raw dump），一行一个 case（JSON Lines 格式）

- cases.cleaned.jsonl：对 cases.jsonl 做了最小必要清洗后的“可直接给下游用”的版本（cleaned/normalized），同样一行一个 case

- 从全量 case 中抽出来的一小批“样本子集”，用于发给 Kimi（或人工）做快速归纳、打标、生成/校验 taxonomy signals 等工作

### 选用了什么数据

为了快速将系统落地，选用了 WPML support 中的 available solution。

这么做可以强对其目标岗位，且面向真实的开发场景，对其用户以及开发者的需求。

### 怎么获取数据集

这里使用了 python 脚本从官网直接抓取：

入口页面：https://wpml.org/forums/available-solutions/

从列表页做分页遍历（典型做法是按 page 参数或按“Next”链接一直走到为空为止）。

列表页里每条 solution card 会给出一个链接（以及有时会出现带 #post-xxxxx 的锚点链接）。你现在的数据里既有 topic 根链接，也有 带 #post 的链接，说明当时我们抓取时把这两类 URL 都纳入了。

对每个条目的目标页面（topic_url）做一次 HTTP GET，然后解析 HTML，抽取并落盘为 JSONL：

- case_id：sha1(topic_url) 的前 16 位（这是可以被严格验证的；例如第一条的 case_id 正好是该 URL 的 sha1 前缀）
- source：固定值 wpml_available_solutions
- topic_url
- title
- forum
- problem
- solution
- captured_at：抓取时间戳

这套设计的好处是：可增量、可追溯、可重跑。JSONL 一行一条，抓多少写多少，不需要一次性把全量握在内存里。

具体的脚本为：[fetch_data.py](./tools/fetch_data.py)

### 怎么做的数据清洗

0) 清洗的总体原则什么这么做

forum 是一个结构化维度（过滤/统计/建索引分区），不能混进 Problem/Solution 的正文噪声。

如果不切干净，后续做聚合指标、做 routing（比如按论坛/语言分流）会直接失真。

具体怎么做（规则）

以固定分隔符切断：遇到 " Quick solution available" 就截断，保留左侧并 strip()。

伪代码等价于：

```
if forum:
    forum = forum.split(" Quick solution available", 1)[0].strip()
```

2) Title 字段纠错与规范化
做了什么

你清洗了两类标题问题：

把“相对时间”当标题的情况置空
清洗后 title="" 的有 750 条。这些对应清洗前的 title 形如：

20 hours, 58 minutes ago

3 days ago

1 day, 2 hours ago
等（抓错了 DOM 节点，把时间戳抓成标题了）。

不做重清洗（不大量删样本、不重写 problem/solution、不复杂去重），因为目标是先跑通 MVP（分类/检索/引用）。

只修影响下游的结构问题：字段污染、标题抓错、输入文本不统一、字符规范化。

这也体现在结果：1801 条原样保留（清洗前后行数相同），只做字段规范化和新增派生字段。

1) Forum 字段清洗
做了什么

把 forum 从“整张卡片拼接文本”里抽取出真正的论坛名：

清洗前：forum = "English Support Quick solution available Problem: ... Solution: ..."

清洗后：forum = "English Support"

在 1801 条里，有 1767 条做了该抽取；另外 34 条原始就是空字符串，清洗后仍为空（不编造）。

把 Unicode 省略号 “…” 统一成 ASCII 的 “...”
清洗前标题里包含 “…” 的有 67 条，清洗后都变为 “...”。

为什么这么做

标题抓错为“xx hours ago”会严重污染检索/embedding：它对语义没有帮助，还会把大量样本的“标题”变成同一类噪声。

省略号统一是典型工程规范化：减少不可见字符差异，避免后续 tokenization/测试快照/字符串匹配出现“看起来一样但不相等”的问题。

具体怎么做（规则）

相对时间标题置空：用一个正则判断“是否由数字 + 时间单位 (+ ago) 组成”，命中则置空。
一个与你数据效果一致的正则（等价实现）是：
```
RE_BAD_TITLE = re.compile(
    r'^\s*(?:\d+\s*(?:minute|minutes|hour|hours|day|days|week|weeks|month|months)\s*,?\s*)+(?:ago)?\s*$',
    re.I
)
if title and RE_BAD_TITLE.match(title):
    title = ""
```

省略号替换（所有字段统一做）：
```
s = s.replace("…", "...")
```

3) Problem 字段的轻量规范化
做了什么

problem 基本保持原样；仅在极少数记录里做了同样的省略号规范化（你数据里是 4 条）。

为什么这么做

problem 是你后续分类与检索的核心输入，不希望“重写文本”带来语义漂移。

只做字符级规范化，既能保证稳定性，也不破坏原意。

具体怎么做（规则）
```
problem = problem.replace("…", "...").strip()
```
没有做 HTML tag 清理（你这批数据里 <h3>...</h3> 这类内容被视为“问题现象的一部分”，保留更利于 Support 场景）。

4) 新增 analysis_text（这是清洗里最关键的“为下游准备”）
做了什么

在 cases.cleaned.jsonl 里新增字段 analysis_text，并且规则是严格一致的：
```
如果 title 非空：
analysis_text = title + " " + problem

如果 title 为空：
analysis_text = problem
```
你这 1801 条记录里，该规则 100% 一致（不存在例外）。

为什么这么做

下游（RuleClassifier / embedding / 检索）希望有一个稳定的单字段输入，不要每次都在代码里拼来拼去。

拼接 title + problem 能补充主题语义；但当 title 明显无效（相对时间）时，宁可不用，避免噪声。

刻意不把 solution 拼进去：避免“答案泄漏到问题侧表征”，不然分类/检索会虚高，线上效果反而差。

```
具体怎么做（规则）
analysis_text = (f"{title} {problem}".strip() if title else problem)
```

5) 你当时“没有做”的清洗（也是一种明确选择）

这些在你现在的 cleaned 文件里都看得出来你没做（或刻意延后）：

不按 topic 去重/合并（同一 topic 的 #post-xxxxx 变体仍在）

不做大规模截断、分段、chunking（那是入库/索引阶段再做）

不做复杂语言检测、PII 识别/擦除（先跑 MVP）

原因就是你当时说的策略：先求能跑起来，再迭代质量。

具体参见该脚本：[clean_cases.py](./tools/clean_cases.py)