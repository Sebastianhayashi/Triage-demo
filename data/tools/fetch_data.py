import re, json, time, hashlib
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE = "https://wpml.org/forums/available-solutions/"
HEADERS = {
    "User-Agent": "triage-research-bot/0.1 (contact: you@example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def fetch(url, retries=3, timeout=25):
    last = None
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last = e
            time.sleep(2 ** i)
    raise last

def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def strip_boilerplate(solution: str) -> str:
    # WPML 列表里常见的固定免责声明段落，去掉能减少噪声
    patterns = [
        r"If this solution does not.*$",
        r"Please note that this solution might be.*$",
        r"We highly recommend checking related known issues.*$",
    ]
    out = solution
    for p in patterns:
        out = re.sub(p, "", out, flags=re.IGNORECASE)
    return normalize_ws(out)

def parse_page(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # 入口：经验上 WPML 的列表正文在页面主内容区，且 topic 链接包含 /forums/topic/
    main = soup.find("main") or soup.find(id="primary") or soup.body

    topic_links = main.select('a[href*="/forums/topic/"]')
    # 去重，保持顺序
    seen = set()
    topic_urls = []
    for a in topic_links:
        href = a.get("href")
        if not href:
            continue
        if href in seen:
            continue
        seen.add(href)
        topic_urls.append(href)

    records = []
    for url in topic_urls:
        # 在列表页里，每个 topic 通常对应一个“块”，其中会出现 "Problem:" / "Solution:"
        # 这里用“从链接向上找容器”的方式更抗模板变化
        a = main.select_one(f'a[href="{url}"]')
        if not a:
            continue
        container = a
        for _ in range(6):
            if not container:
                break
            text = container.get_text(" ", strip=True)
            if "Problem:" in text and "Solution:" in text:
                break
            container = container.parent

        if not container:
            continue

        block_text = normalize_ws(container.get_text("\n", strip=True))
        # 解析 Problem/Solution（用文本分隔符，避免过度依赖 class）
        problem = ""
        solution = ""
        if "Problem:" in block_text and "Solution:" in block_text:
            # 粗切
            after_problem = block_text.split("Problem:", 1)[1]
            if "Solution:" in after_problem:
                problem_part, solution_part = after_problem.split("Solution:", 1)
                problem = normalize_ws(problem_part)
                solution = strip_boilerplate(solution_part)

        title = normalize_ws(a.get_text(" ", strip=True))
        forum = ""
        m = re.search(r"Started by:.*?in:\s*(.+)", block_text)
        if m:
            forum = normalize_ws(m.group(1))

        case_id = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        records.append({
            "case_id": case_id,
            "source": "wpml_available_solutions",
            "topic_url": url,
            "title": title,
            "forum": forum,
            "problem": problem,
            "solution": solution,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        })
    return records

def crawl(pages=20, sleep_s=1.2, out_path="cases.jsonl"):
    with open(out_path, "w", encoding="utf-8") as f:
        for p in range(1, pages + 1):
            url = BASE if p == 1 else f"{BASE}page/{p}/"
            html = fetch(url)
            recs = parse_page(html)

            for r in recs:
                if r["problem"] and r["solution"]:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

            time.sleep(sleep_s)
            print(f"page {p} -> {len(recs)} extracted")

if __name__ == "__main__":
    crawl(pages=50)  # 先抓 50 页（约 750 条）即可开始做频次归纳

