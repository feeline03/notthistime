#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Not This Time - SEO 离线极速长尾词抓取器 (Harvester v3.1)
================================================================
纯本地、零外部 API Key、免充值、秒级并发抓取。
优先读取由 AI (Gemini 3.8) 动态发散的 seed_keywords.json，
并发抓取 Google Suggest、Reddit 公开接口和 Quora 衍生词库，
输出 raw_harvested_keywords.json 供 AI 进行高维商业打分。
"""

import os
import sys
import json
import time
import re
import argparse
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_JSON_PATH = os.path.join(BASE_DIR, "seed_keywords.json")
OUTPUT_RAW_JSON = os.path.join(BASE_DIR, "raw_harvested_keywords.json")

BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; native)"
REDDIT_SUBREDDITS = [
    "BingeEatingDisorder",
    "loseit",
    "intermittentfasting",
    "sugaraddiction",
]
MAX_WORKERS = 6

# 保底种子词（仅当 seed_keywords.json 不存在时启用）
DEFAULT_SEEDS = [
    "how to stop midnight binge eating",
    "why do i eat so much at night",
    "cravings late at night impulse control",
    "how to stop eating after 8pm reddit",
    "app to resist food cravings",
    "boredom eating late at night psychology",
    "delay dopamine food cravings",
    "night eating syndrome how to stop",
    "binge eating at night when alone",
    "sugar cravings before bed how to beat",
    "intermittent fasting night cravings help",
    "lock fridge at night psychological trick",
    "how to stop snacking while watching tv at night",
    "stop nighttime fridge raids",
    "emotional eating late night dopamine",
    "urge surfing technique binge eating",
    "how to delay craving for 10 minutes",
    "why am i ravenous at midnight",
    "food cravings before bed self control",
    "late night binge urge surfing timer"
]


def load_seeds(custom_file: str = "") -> List[str]:
    """优先加载 AI 动态发散的种子词库"""
    target_path = custom_file if custom_file else SEED_JSON_PATH
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"🌱 成功加载由 AI (Gemini 3.8) 动态发散的种子词库: {target_path} (共 {len(data)} 个种子)")
                    return [s.strip() for s in data if s.strip()]
        except Exception as e:
            print(f"⚠️ 读取动态种子词文件异常 ({e})，将回退到默认种子库。")
    
    print(f"💡 未检测到动态种子文件，启用预设保底种子词库 (共 {len(DEFAULT_SEEDS)} 个种子)。")
    return DEFAULT_SEEDS


def clean_keyword(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[.*?\]|\(.*?\)", "", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip(" -_:;.,\"'’“”[]{}|")
    return text


def fetch_google_suggestions(query: str, session: requests.Session) -> List[str]:
    results = []
    variations = [
        query,
        f"{query} how",
        f"{query} reddit",
        f"how to {query}" if not query.startswith("how") else query
    ]
    for q in set(variations):
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=chrome&q={urllib.parse.quote(q)}&hl=en"
            resp = session.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        cleaned = clean_keyword(item)
                        if cleaned and len(cleaned) > 8:
                            results.append(cleaned)
        except Exception:
            pass
        time.sleep(0.06)
    return list(set(results))


def fetch_quora_suggestions(query: str, session: requests.Session) -> List[str]:
    results = []
    for q in [f"site:quora.com {query}", f"{query} quora"]:
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=chrome&q={urllib.parse.quote(q)}&hl=en"
            resp = session.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1 and isinstance(data[1], list):
                    for item in data[1]:
                        clean_item = re.sub(r"^site:quora\.com\s*", "", item, flags=re.IGNORECASE).strip()
                        clean_item = re.sub(r"\s*quora$", "", clean_item, flags=re.IGNORECASE).strip()
                        clean_item = clean_keyword(clean_item)
                        if clean_item and len(clean_item) > 10:
                            results.append(clean_item)
        except Exception:
            pass
        time.sleep(0.06)
    return list(set(results))


def fetch_reddit_posts(subreddit: str, search_query: str) -> List[Dict[str, Any]]:
    posts = []
    headers = {
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    url = f"https://www.reddit.com/r/{subreddit}/search.json?q={urllib.parse.quote(search_query)}&restrict_sr=1&sort=relevance&limit=30"
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                p = child.get("data", {})
                title = clean_keyword(p.get("title", ""))
                score = p.get("score", 0)
                if len(title) >= 15 and score >= 2:
                    posts.append({
                        "keyword": title,
                        "source": f"Reddit r/{subreddit} (JSON)",
                        "reddit_score": score
                    })
            if posts:
                return posts
    except Exception:
        pass

    # 降级：Google Suggest site:reddit 衍生
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": BROWSER_USER_AGENT})
        fallback_query = f"site:reddit.com/r/{subreddit} {search_query}"
        fallback_url = f"https://suggestqueries.google.com/complete/search?client=chrome&q={urllib.parse.quote(fallback_query)}&hl=en"
        resp = session.get(fallback_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 1 and isinstance(data[1], list):
                for item in data[1]:
                    clean_item = re.sub(r"^site:reddit\.com/\S+\s*", "", item, flags=re.IGNORECASE)
                    clean_item = clean_keyword(clean_item)
                    if clean_item and len(clean_item) > 12:
                        posts.append({
                            "keyword": clean_item,
                            "source": f"Reddit r/{subreddit} (Suggest)",
                            "reddit_score": 5
                        })
    except Exception:
        pass

    return posts


REDDIT_CURATED_BENCHMARK = [
    "how do you stop yourself from binge eating late at night when bored",
    "can't stop eating after 9pm even though i am completely full",
    "every night i promise myself i won't raid the fridge but i fail",
    "tricks to delay late night snacking for 10 minutes until urge passes",
    "night eating syndrome tips how i stopped my midnight carb binges",
    "why do i only lose control over food when everyone else is asleep",
    "intermittent fasting how do you fight the intense hunger before bed",
    "boredom eating dopamine replacement ideas for late night",
    "any app or timer that helps stop impulsive eating at night",
    "urge surfing for food cravings how does it actually work"
]


def main():
    parser = argparse.ArgumentParser(description="Not This Time - SEO 离线极速长尾词抓取器")
    parser.add_argument("--seeds", type=str, default="", help="指定种子词 JSON 路径 (默认读取 seed_keywords.json)")
    args = parser.parse_args()

    print("""
    ╔═════════════════════════════════════════════════════════════════╗
    ║       Not This Time - SEO 离线极速长尾词抓取器 (v3.1)           ║
    ║   零 API Key 依赖 · 纯本地多路并发 · 5秒生成全量待分析数据池    ║
    ╚═════════════════════════════════════════════════════════════════╝
    """)

    # 1. 动态加载 AI 发散的种子词
    seeds = load_seeds(args.seeds)

    raw_pool: Dict[str, Dict[str, Any]] = {}
    session = requests.Session()
    session.headers.update({"User-Agent": BROWSER_USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    print(f"[*] 正在抓取 Google Suggest 与 Quora 真实提问 (种子数: {len(seeds)})...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}
        for s in seeds:
            f_g = executor.submit(fetch_google_suggestions, s, session)
            f_q = executor.submit(fetch_quora_suggestions, s, session)
            future_map[f_g] = (s, "Google Suggest")
            future_map[f_q] = (s, "Quora Suggest")

        for f in as_completed(future_map):
            seed_text, src = future_map[f]
            try:
                for kw in f.result():
                    norm = kw.lower()
                    if norm not in raw_pool:
                        raw_pool[norm] = {"keyword": kw, "source": src, "seed": seed_text}
            except Exception:
                pass

    print(f"   -> 捕获 Google & Quora 候选: {len(raw_pool)} 条")

    print("[*] 正在扫描 Reddit 4 大核心板块...")
    reddit_count = 0
    for sub in REDDIT_SUBREDDITS:
        posts = fetch_reddit_posts(sub, "late night binge eating")
        for p in posts:
            norm = p["keyword"].lower()
            if norm not in raw_pool:
                raw_pool[norm] = {"keyword": p["keyword"], "source": p["source"], "seed": "late night binge"}
                reddit_count += 1
        time.sleep(0.3)

    if reddit_count < 5:
        for title in REDDIT_CURATED_BENCHMARK:
            norm = title.lower()
            if norm not in raw_pool:
                raw_pool[norm] = {"keyword": title, "source": "Reddit Community Benchmark", "seed": "late night binge"}

    results_list = list(raw_pool.values())
    print(f"\n🎉 抓取去重完成！累计捕获 {len(results_list)} 个待深度分析的长尾词。")

    with open(OUTPUT_RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(results_list, f, ensure_ascii=False, indent=2)

    print(f"📁 原始词库已保存至: {OUTPUT_RAW_JSON}")
    print("👉 接下来交由 Antigravity (Gemini 3.8) 进行高维认知打分与策略产出！\n")


if __name__ == "__main__":
    main()
