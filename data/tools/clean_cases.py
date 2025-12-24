import json, re, random, collections
from pathlib import Path

IN_PATH = Path("cases.jsonl")
OUT_CLEAN = Path("cases.cleaned.jsonl")
OUT_STATS = Path("stats.json")
OUT_SAMPLE = Path("samples_for_kimi.jsonl")

TIME_TITLE_RE = re.compile(r"^\d+\s+(?:day|days|hour|hours|minute|minutes|week|weeks|month|months)\b", re.I)

def is_time_title(title: str) -> bool:
    title = (title or "").strip()
    return bool(TIME_TITLE_RE.search(title))

def clean_forum(forum_raw: str) -> str:
    """把 'English Support Quick solution available ...' 提取成 'English Support'"""
    if not forum_raw:
        return ""
    s = forum_raw.strip()
    # 常见格式：以 'English Support' 开头
    # 取前 1~4 个词，直到 'Support' 结束
    m = re.match(r"^(.+?\bSupport)\b", s)
    if m:
        return m.group(1).strip()
    return s.split(" Quick solution available", 1)[0].strip()

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u2026", "...")  # 统一省略号
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(s: str):
    # 简单英文token（足够先跑出主题信号）
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{1,}", s.lower())

def bigrams(tokens):
    return [tokens[i] + " " + tokens[i+1] for i in range(len(tokens)-1)]

def main(sample_n=200, seed=42):
    random.seed(seed)

    total = 0
    time_titles = 0
    forums = collections.Counter()
    tok = collections.Counter()
    bi = collections.Counter()

    rows = []
    with IN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            total += 1

            title = normalize_text(obj.get("title", ""))
            problem = normalize_text(obj.get("problem", ""))
            solution = normalize_text(obj.get("solution", ""))
            forum = clean_forum(obj.get("forum", ""))

            if is_time_title(title):
                time_titles += 1
                title = ""  # 丢弃噪声标题

            analysis_text = normalize_text(" ".join([title, problem]).strip())

            clean = {
                "case_id": obj.get("case_id"),
                "source": obj.get("source"),
                "topic_url": obj.get("topic_url"),
                "title": title,
                "forum": forum,
                "problem": problem,
                "solution": solution,
                "analysis_text": analysis_text,
                "captured_at": obj.get("captured_at"),
            }
            rows.append(clean)

            if forum:
                forums[forum] += 1

            # 高频主题统计：先用 analysis_text
            tokens = tokenize(analysis_text)
            for t in tokens:
                tok[t] += 1
            for b in bigrams(tokens):
                bi[b] += 1

    # 写清洗结果
    with OUT_CLEAN.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 抽样给 Kimi：分层思路更好，但先随机也能起步
    sample = random.sample(rows, k=min(sample_n, len(rows)))
    with OUT_SAMPLE.open("w", encoding="utf-8") as f:
        for r in sample:
            # 给 Kimi 的字段尽量精简：便于阅读与归纳
            f.write(json.dumps({
                "case_id": r["case_id"],
                "topic_url": r["topic_url"],
                "text": r["analysis_text"],
                "solution": r["solution"]
            }, ensure_ascii=False) + "\n")

    stats = {
        "total": total,
        "time_title_rows": time_titles,
        "forums_top10": forums.most_common(10),
        "tokens_top30": tok.most_common(30),
        "bigrams_top30": bi.most_common(30),
    }
    OUT_STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Wrote:", OUT_CLEAN, OUT_STATS, OUT_SAMPLE)

if __name__ == "__main__":
    main()

