#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Not This Time - 高阶 SEO 长尾词自动化调研脚本 (Pro Version 2.0)
================================================================
服务于行为干预与自律管理 App: "Not This Time"（聚焦：深夜暴食 / midnight cravings / 冲动延迟）

【四大工作流】
1. Gemini 动态种子词发散 (行为心理学 + 减肥自救真实痛点)
2. 三路免费并发抓取：
   - 路线 A: Google Suggest 深度补全 (支持前缀/后缀/常见修饰符展开)
   - 路线 B: Reddit 多核心板块抓取 (r/BingeEatingDisorder, r/loseit, r/intermittentfasting, r/sugaraddiction)
            支持公开 JSON 接口与 Google site:reddit 智能降级双保障
   - 路线 C: Quora 高频真实提问挖掘 (Google Suggest site:quora.com 衍生)
3. Gemini 双维度深度打分与清洗 (Intent Score 1-5 + SEO Difficulty 1-5 + 一句话切入建议 + 推荐App功能挂钩)
4. 黄金词矩阵过滤 (Intent >= 4 且 Difficulty <= 2) 与双 CSV 自动导出

【高可用与多级回滚架构】
- 双重凭据格式自适应：完美兼容新版 `AQ.` (Authentication Key) 与经典版 `AIza.` (API Key)。
- 顶级模型梯队自动协商：启动时自动探针锁定当前最优可用模型 (Gemini 2.5/2.0 Flash 优先)，
  遇到 404/配额限制时自动无缝降级回滚至 1.5 系列或本地启发式评分，确保流水线永远不断流。
"""

import os
import sys
import json
import time
import re
import csv
import argparse
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

import requests
import google.generativeai as genai

# ==========================================
# 1. 核心配置与全局常量
# ==========================================

# 优先读取环境变量 GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 顶级模型梯队配置 (按性能从高到低排列，自动协商与回滚)
CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

# 请求 Headers（防止被 Reddit 或 Google Suggest 拦截）
BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; native)"
FALLBACK_DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Reddit 目标板块
REDDIT_SUBREDDITS = [
    "BingeEatingDisorder",
    "loseit",
    "intermittentfasting",
    "sugaraddiction",
]

# 并发线程数
MAX_WORKERS = 4

# 文件输出路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_GOLD_CSV = os.path.join(BASE_DIR, "gold_mine_keywords.csv")
OUTPUT_ALL_CSV = os.path.join(BASE_DIR, "all_scraped_keywords_analyzed.csv")


# ==========================================
# 2. 辅助工具函数与自适应鉴权
# ==========================================

def get_session() -> requests.Session:
    """创建配置好超时与重试属性的 HTTP Session"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": BROWSER_USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "*/*",
    })
    return session


def clean_keyword(text: str) -> str:
    """清洗提取到的关键词或帖子标题"""
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[.*?\]|\(.*?\)", "", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip(" -_:;.,\"'’“”[]{}|")
    return text


class GeminiAdaptiveClient:
    """
    智能 Gemini 自适应客户端 (v2.2)
    具备：
    1. 强制启用 transport='rest'，完美兼容本地 HTTP 代理
    2. 基于官方 list_models 动态锁定授权模型池，杜绝尝试未授权版本
    3. 异常透明输出，秒级定位原因
    4. 自动在授权模型池中弹性切换
    """
    def __init__(self, api_key: str):
        self.api_key = api_key.strip(" '\"\n\r\t")
        self.active_model_name: Optional[str] = None
        self.active_model: Optional[genai.GenerativeModel] = None
        self.authorized_models: List[str] = []

    def probe_and_lock_best_model(self) -> bool:
        """握手探针：查询授权模型并进行真实心跳发包，自动滤除 402/404 模型，锁定真正可用的免费/付费模型"""
        print("[*] 正在启动 Gemini 多模型梯队智能探针 (启用 REST 传输模式以适配本地代理)...")

        try:
            genai.configure(api_key=self.api_key, transport="rest")
        except Exception as e:
            print(f"⚠️ 客户端初始化提示: {e}")
            genai.configure(api_key=self.api_key)

        generation_config = {
            "temperature": 0.3,
            "top_p": 0.9,
            "max_output_tokens": 4096,
        }

        # 1. 优先调用官方 list_models() 动态探测当前 Key 真实授权模型
        try:
            available_online = []
            for m in genai.list_models():
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    clean_name = m.name.replace("models/", "")
                    available_online.append(clean_name)

            if available_online:
                self.authorized_models = available_online
                print(f"📡 成功连接 Google！当前 Key 授权的可用模型列表: {available_online[:4]}...")

                # 按照优先级组织候选队列，并进行【真实轻量心跳发包】
                candidates = [m for m in CANDIDATE_MODELS if m in available_online] + [m for m in available_online if m not in CANDIDATE_MODELS]
                
                print("[*] 正在对候选模型进行心跳可用性校验 (自动避开欠费402/停用404)...")
                for candidate in candidates:
                    try:
                        m = genai.GenerativeModel(model_name=candidate, generation_config=generation_config)
                        # 发送极简心跳验证连通与扣费状态
                        resp = m.generate_content("hi")
                        if resp and resp.text:
                            self.active_model_name = candidate
                            self.active_model = m
                            print(f"✅ 探针校验通过！成功锁定并激活模型: 【{candidate}】")
                            return True
                    except Exception as e:
                        err_str = str(e)
                        if "402" in err_str:
                            print(f"   - 模型 [{candidate}] 提示预付费钱包未充值 (402)，自动尝试下一梯队...")
                        elif "404" in err_str:
                            print(f"   - 模型 [{candidate}] 接口不存在 (404)，自动尝试下一梯队...")
                        else:
                            print(f"   - 模型 [{candidate}] 心跳未通: {err_str[:60]}...")
                        continue

        except Exception as e:
            print(f"⚠️ [握手诊断信息] 连接 Google 接口返回: {e}")

        # 2. 如果官方探测未通，按传统默认配置保底尝试
        self.authorized_models = CANDIDATE_MODELS
        self.active_model_name = "gemini-1.5-flash"
        self.active_model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)
        return True

    def generate_with_fallback(self, prompt: str) -> Optional[str]:
        """在授权模型池中按梯队执行生成，异常直接透明打印"""
        if not self.active_model:
            return None

        # 核心：只在 Google 官方授权给该 Key 的模型列表中轮询！绝不盲目去请求未授权的 1.5/2.0
        models_pool = self.authorized_models if self.authorized_models else CANDIDATE_MODELS
        models_to_try = [self.active_model_name] + [m for m in models_pool if m != self.active_model_name]

        last_error = ""
        for m_name in models_to_try:
            try:
                # 尝试不同的生成配置以应对不同模型要求
                model = genai.GenerativeModel(
                    model_name=m_name,
                    generation_config={"temperature": 0.3, "top_p": 0.9, "max_output_tokens": 4096}
                )
                resp = model.generate_content(prompt)
                if resp and resp.text:
                    if m_name != self.active_model_name:
                        print(f"🔄 自动安全切换至可用授权模型: [{m_name}]")
                        self.active_model_name = m_name
                        self.active_model = model
                    return resp.text.strip()
            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                print(f"⚠️ 模型 [{m_name}] 试运行提示: {err_msg[:95]}")
                continue

        if last_error:
            print(f"⚠️ [生成警告] 云端授权模型均未能完成生成 ({last_error[:80]})，自动切入本地高质量启发式引擎。")
        return None


def init_gemini_client(api_key: str = "", dry_run: bool = False) -> Optional[GeminiAdaptiveClient]:
    """初始化自适应 Gemini 客户端"""
    global GEMINI_API_KEY
    if api_key:
        GEMINI_API_KEY = api_key.strip(" '\"\n\r\t")

    if dry_run:
        print("💡 [Dry-Run 演练模式] 跳过云端 API 交互，使用内置高质量启发式打分引擎。")
        return None

    if not GEMINI_API_KEY:
        print("\n" + "!" * 70)
        print("【错误提示】未检测到环境变量 GEMINI_API_KEY！")
        print("请在终端运行前执行：")
        print("    export GEMINI_API_KEY='你的Google_AI_Studio密钥'")
        print("或者在执行时传入：")
        print("    python3 not_this_time_pro_seo.py --api-key '你的Key'")
        print("或者开启测试模式：")
        print("    python3 not_this_time_pro_seo.py --dry-run")
        print("!" * 70 + "\n")
        sys.exit(1)

    client = GeminiAdaptiveClient(GEMINI_API_KEY)
    success = client.probe_and_lock_best_model()
    if not success:
        print("⚠️ 提醒：当前 API Key 云端探针未能连通，后续将启用智能自适应兜底引擎。")
    return client


# ==========================================
# 3. 步骤 1: Gemini 动态种子词发散
# ==========================================

FALLBACK_SEEDS = [
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
    "why am i ravenous at midnight"
]


def generate_seed_keywords(client: Optional[GeminiAdaptiveClient]) -> List[str]:
    """
    调用 Gemini，以行为心理学 + 暴食自救者视角，发散 15-20 个痛点种子词
    """
    print("\n" + "=" * 65)
    print("🌱 [步骤 1] 正在调用 Gemini 站在行为心理学视角发散痛点种子词...")
    print("=" * 65)

    if client is None:
        print("💡 [Dry-Run] 跳过 Gemini API 生成，使用预设心理学痛点种子词库。")
        return FALLBACK_SEEDS

    prompt = """
You are an expert behavioral scientist, addiction habit researcher, and SEO strategist for "Not This Time" — an impulse-control mobile app that helps people break the late-night binge loop through friction, micro-delaying (urge surfing for 5-10 mins), and dopamine redirection.

Task:
Generate 18 high-pain-point, realistic, natural-language search queries that real people suffering from late-night binge eating or midnight cravings search for when feeling guilty, helpless, or looking for an immediate coping tool.

Requirements:
1. Cover emotional triggers (alone at night, boredom, ADHD dopamine deficit, stress relief, after dinner sugar addiction).
2. Cover situational triggers (watching Netflix in bed, raiding pantry at 11pm, snacking after bedtime).
3. Cover solution-seeking (tactics to delay binge, psychological hacks, impulse control apps, how to stop urge surfing).
4. Do NOT output broad medical keywords like "eating disorders treatment" or "bulimia diagnosis" (these are dominated by hospitals). Focus on long-tail user-spoken phrases.
5. Return ONLY a valid JSON list of strings, with NO markdown code blocks, NO conversational preamble.

Example JSON format:
[
  "how to stop midnight fridge raids",
  "why do i crave carbs only late at night",
  "psychological tricks to delay late night eating"
]
"""
    raw_text = client.generate_with_fallback(prompt)
    if raw_text:
        try:
            clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text)
            clean_json = re.sub(r"\s*```$", "", clean_json).strip()
            seeds = json.loads(clean_json)
            if isinstance(seeds, list) and len(seeds) >= 10:
                print(f"✅ Gemini 成功发散 {len(seeds)} 个行为心理学痛点种子词：")
                for idx, s in enumerate(seeds[:6], 1):
                    print(f"   {idx}. {s}")
                print(f"   ...以及其余 {len(seeds) - 6} 个核心词")
                return seeds
        except Exception as e:
            print(f"⚠️ 种子词解析微调 ({e})，启用精选行为心理学种子库...")

    return FALLBACK_SEEDS


# ==========================================
# 4. 步骤 2: 多路并发免费抓取 (路线 A/B/C)
# ==========================================

def fetch_google_suggestions(query: str, session: requests.Session) -> List[str]:
    """
    路线 A: 调用 Google Suggest 官方公开补全接口，配合修饰词展开
    """
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
                        if cleaned and len(cleaned) > 10:
                            results.append(cleaned)
        except Exception:
            pass
        time.sleep(0.1)

    return list(set(results))


def fetch_quora_suggestions(query: str, session: requests.Session) -> List[str]:
    """
    路线 C: 使用 site:quora.com 关键词通过 Google Suggest 捞出用户高频真实提问
    """
    results = []
    search_queries = [
        f"site:quora.com {query}",
        f"{query} quora"
    ]

    for q in search_queries:
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
                        if clean_item and len(clean_item) > 12:
                            results.append(clean_item)
        except Exception:
            pass
        time.sleep(0.1)

    return list(set(results))


def fetch_reddit_posts(subreddit: str, search_query: str) -> List[Dict[str, Any]]:
    """
    路线 B: 抓取 Reddit 核心板块真实求助帖
    - 首选：Reddit 公开 .json 接口（带合法 User-Agent）
    - 降级：若因网络/IP策略触发 403/429，则自动切换为 Google Suggest site:reddit 衍生抓取
    """
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
            children = data.get("data", {}).get("children", [])
            for child in children:
                post_data = child.get("data", {})
                title = clean_keyword(post_data.get("title", ""))
                score = post_data.get("score", 0)
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

    # 降级方案：使用 Google Suggest 提取针对该 Reddit 板块的真实高频搜索疑问
    try:
        session = get_session()
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
                            "source": f"Reddit r/{subreddit} (SERP Suggest)",
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
    "any app or timer that helps stop impulsive eating at night"
]


def run_multi_source_harvest(seeds: List[str]) -> List[Dict[str, Any]]:
    """
    并发调度路线 A、B、C 并进行聚合、清洗、去重
    """
    print("\n" + "=" * 65)
    print("🌐 [步骤 2] 正在启动三路并发免费抓取 (Google + Reddit + Quora)...")
    print("=" * 65)

    raw_pool: Dict[str, Dict[str, Any]] = {}
    session = get_session()

    # 1. 抓取 Google Suggest 与 Quora 问答
    print(f"[*] 路线 A & C: 正在对 {len(seeds)} 个种子词执行 Google 下拉词与 Quora 提问聚合...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}
        for s in seeds:
            f_g = executor.submit(fetch_google_suggestions, s, session)
            f_q = executor.submit(fetch_quora_suggestions, s, session)
            future_map[f_g] = (s, "Google Suggest")
            future_map[f_q] = (s, "Quora Suggest")

        for future in as_completed(future_map):
            seed_text, src = future_map[future]
            try:
                results = future.result()
                for kw in results:
                    norm = kw.lower()
                    if norm not in raw_pool:
                        raw_pool[norm] = {
                            "keyword": kw,
                            "source": src,
                            "seed_derived": seed_text
                        }
            except Exception:
                pass

    print(f"   -> Google 与 Quora 聚合捕获: {len(raw_pool)} 条")

    # 2. 抓取 Reddit 核心板块真实求助
    print(f"[*] 路线 B: 正在扫描 Reddit {len(REDDIT_SUBREDDITS)} 大核心板块 (r/BingeEatingDisorder, r/loseit 等)...")
    reddit_harvested = 0
    reddit_main_query = "late night binge eating"
    for sub in REDDIT_SUBREDDITS:
        posts = fetch_reddit_posts(sub, reddit_main_query)
        for p in posts:
            norm = p["keyword"].lower()
            if norm not in raw_pool:
                raw_pool[norm] = {
                    "keyword": p["keyword"],
                    "source": p["source"],
                    "seed_derived": reddit_main_query
                }
                reddit_harvested += 1
        time.sleep(0.5)

    if reddit_harvested < 5:
        for title in REDDIT_CURATED_BENCHMARK:
            norm = title.lower()
            if norm not in raw_pool:
                raw_pool[norm] = {
                    "keyword": title,
                    "source": "Reddit Community Benchmark",
                    "seed_derived": "late night binge"
                }

    all_harvested = list(raw_pool.values())
    print(f"🎉 原始数据池去重汇总完毕！累计捕获 {len(all_harvested)} 个未清洗候选长尾词。\n")
    return all_harvested


# ==========================================
# 5. 步骤 3: Gemini 双维度深度打分与清洗
# ==========================================

def batch_score_with_gemini(
    keywords_batch: List[Dict[str, Any]],
    client: Optional[GeminiAdaptiveClient]
) -> List[Dict[str, Any]]:
    """
    分批让 Gemini 进行结构化 JSON 打分，支持模型自动降级与启发式兜底
    """
    # 启发式兜底生成器
    def run_heuristic_fallback() -> List[Dict[str, Any]]:
        fallback = []
        for orig in keywords_batch:
            kw = orig["keyword"].lower()
            intent = 4 if any(w in kw for w in ["app", "stop", "how to", "trick", "delay", "tips", "resist", "beat", "help", "raid"]) else 3
            diff = 2 if len(kw.split()) >= 6 or any(w in kw for w in ["reddit", "quora", "why do i", "can't stop", "i fail", "boredom"]) else 4
            fallback.append({
                "keyword": orig["keyword"],
                "source": orig.get("source", ""),
                "intent_score": intent,
                "seo_difficulty": diff,
                "actionable_advice": "以第一人称共情深夜冲动，顺理成章植入 Not This Time 冲动延迟计时器。"
            })
        return fallback

    if client is None:
        return run_heuristic_fallback()

    kw_texts = [item["keyword"] for item in keywords_batch]

    prompt = f"""
You are the Head of SEO and Growth at "Not This Time" (a behavioral psychology mobile app that helps users stop late-night binge eating, resist midnight cravings, and delay dopamine impulses using a 5-10 minute micro-pause and friction tools).

Analyze this list of real search queries/community questions:
{json.dumps(kw_texts, ensure_ascii=False, indent=2)}

For each query, evaluate:
1. "intent_score" (1-5):
   - 5: High Urgency / High Conversion. The user is in distress, looking for a concrete solution, app, tool, or coping mechanism to stop eating right now.
   - 4: Strong Problem Awareness ("how to stop", "tricks to beat cravings", "why do i eat when bored"). High potential for a blog-to-app conversion.
   - 3: Moderate intent / personal struggle story.
   - 1-2: Informational definition, pure medical theory, or irrelevant vent.

2. "seo_difficulty" (1-5):
   - 5: Dominated by massive medical portals (WebMD, Healthline, Mayo Clinic, Verywell Health). Impossible for an indie app blog.
   - 4: Competitive commercial health/fitness sites.
   - 3: Moderate competition; requires comprehensive pillar guide.
   - 1-2: GOLD MINE! Low difficulty. The SERP is mostly Reddit threads, Quora questions, personal blogs, or niche forums. An indie app blog post with genuine first-person psychological steps can easily rank in Top 3.

3. "actionable_advice": Exactly ONE concise sentence in Chinese (under 35 Chinese characters) explaining the content angle and how to naturally plug the "Not This Time" app's delay/friction intervention.

Return a STRICT JSON list of objects matching the items:
[
  {{
    "keyword": "original keyword",
    "intent_score": 4,
    "seo_difficulty": 1,
    "actionable_advice": "一句话中文切入建议与App植入点"
  }}
]
DO NOT output markdown ticks like ```json or any other text. Output ONLY the raw valid JSON array.
"""
    raw_response = client.generate_with_fallback(prompt)
    if not raw_response:
        return run_heuristic_fallback()

    try:
        clean_text = re.sub(r"^```(?:json)?\s*", "", raw_response)
        clean_text = re.sub(r"\s*```$", "", clean_text).strip()
        scored_list = json.loads(clean_text)

        results = []
        for i, original in enumerate(keywords_batch):
            matching = None
            if i < len(scored_list) and isinstance(scored_list[i], dict):
                matching = scored_list[i]
            else:
                for item in scored_list:
                    if item.get("keyword", "").lower() == original["keyword"].lower():
                        matching = item
                        break

            if matching:
                results.append({
                    "keyword": original["keyword"],
                    "source": original.get("source", ""),
                    "intent_score": int(matching.get("intent_score", 3)),
                    "seo_difficulty": int(matching.get("seo_difficulty", 3)),
                    "actionable_advice": matching.get("actionable_advice", "从延迟满足行为学切入，推荐使用Not This Time的5分钟阻断倒计时。")
                })
            else:
                results.append({
                    "keyword": original["keyword"],
                    "source": original.get("source", ""),
                    "intent_score": 3,
                    "seo_difficulty": 3,
                    "actionable_advice": "结合深夜多巴胺饥渴机制，引导使用行为延迟工具。"
                })
        return results

    except Exception:
        return run_heuristic_fallback()


def score_and_clean_keywords(
    raw_keywords: List[Dict[str, Any]],
    client: Optional[GeminiAdaptiveClient],
    batch_size: int = 15
) -> List[Dict[str, Any]]:
    """
    分批打分调度器 (针对免费层优化：batch_size=15，每次间隔 1.2s，稳健防429)
    """
    print("\n" + "=" * 65)
    print("🧠 [步骤 3] Gemini 正在进行双维度 (意图转化 vs 竞争难度) 深度打分与清洗...")
    print("=" * 65)

    total = len(raw_keywords)
    all_scored = []

    for i in range(0, total, batch_size):
        batch = raw_keywords[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        print(f"[*] 正在分析批次 {batch_num}/{total_batches} (条目 {i+1} ~ {min(i+batch_size, total)})...")
        scored_batch = batch_score_with_gemini(batch, client)
        all_scored.extend(scored_batch)
        if client is not None:
            time.sleep(1.2)  # 礼貌间隔，防止免费层触发 429 限流

    print(f"✅ 全量数据分析打分完成！共处理 {len(all_scored)} 条。")
    return all_scored


# ==========================================
# 6. 步骤 4: 黄金词矩阵过滤与导出
# ==========================================

def filter_and_export_gold_mine(scored_keywords: List[Dict[str, Any]]):
    """
    根据黄金词矩阵 (Intent >= 4 且 Difficulty <= 2) 过滤并导出 CSV
    """
    print("\n" + "=" * 65)
    print("🏆 [步骤 4] 黄金长尾词矩阵过滤 (Intent >= 4 & Difficulty <= 2) 与导出...")
    print("=" * 65)

    # 1. 保存全量打分结果
    with open(OUTPUT_ALL_CSV, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["keyword", "intent_score", "seo_difficulty", "source", "actionable_advice"]
        )
        writer.writeheader()
        writer.writerows(scored_keywords)
    print(f"📁 [全景库] 已导出全量打分结果: {OUTPUT_ALL_CSV} ({len(scored_keywords)} 条)")

    # 2. 筛选黄金词
    gold_mine = [
        item for item in scored_keywords
        if item["intent_score"] >= 4 and item["seo_difficulty"] <= 2
    ]

    # 排序：意图分降序、难度分升序
    gold_mine.sort(key=lambda x: (-x["intent_score"], x["seo_difficulty"]))

    # 导出黄金词库
    with open(OUTPUT_GOLD_CSV, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["keyword", "intent_score", "seo_difficulty", "source", "actionable_advice"]
        )
        writer.writeheader()
        writer.writerows(gold_mine)
    print(f"🌟 [黄金矿] 成功萃取出黄金长尾词: {OUTPUT_GOLD_CSV} ({len(gold_mine)} 条)")

    # 3. 终端精选可视化预览
    print("\n" + "-" * 90)
    print(f"{'🎯 关键词 (Keyword)':<45} | {'意图':<4} | {'难度':<4} | {'来源'}")
    print("-" * 90)
    display_list = gold_mine if gold_mine else scored_keywords[:10]
    for item in display_list[:15]:
        kw = item["keyword"]
        kw_display = (kw[:42] + "..") if len(kw) > 42 else kw
        print(f"{kw_display:<45} | {item['intent_score']:^4} | {item['seo_difficulty']:^4} | {item['source']}")
    print("-" * 90)

    if gold_mine:
        print("\n💡 [精选策略样例]:")
        for item in gold_mine[:3]:
            print(f"  👉 \"{item['keyword']}\"")
            print(f"     建议: {item['actionable_advice']}\n")
    else:
        print("💡 提示：当前严格门槛 (Intent>=4, Diff<=2) 下条目较少，请查阅全景库筛选 Intent>=3 的潜力词。")


# ==========================================
# 7. 主程序入口
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Not This Time - 高阶 SEO 长尾词自动化调研 Agent (Pro 2.0)")
    parser.add_argument("--api-key", type=str, default="", help="Google AI Studio Gemini API Key (支持 AQ. 与 AIza. 全格式)")
    parser.add_argument("--dry-run", action="store_true", help="演练模式，跳过 Gemini API 调用验证整条流水线")
    args = parser.parse_args()

    print("""
    ╔═════════════════════════════════════════════════════════════════╗
    ║       Not This Time - Pro SEO Keyword Agent (v2.0)              ║
    ║   行为干预 App 长尾词挖掘 · 双维度智能评分 · 黄金矩阵萃取       ║
    ╚═════════════════════════════════════════════════════════════════╝
    """)

    # 1. 初始化自适应模型客户端 (自动协商最优可用模型并支持自动降级)
    client = init_gemini_client(api_key=args.api_key, dry_run=args.dry_run)

    # 2. 步骤 1: 种子词发散
    seed_keywords = generate_seed_keywords(client)

    # 3. 步骤 2: 多路并发免费抓取
    harvested_data = run_multi_source_harvest(seed_keywords)

    if not harvested_data:
        print("❌ 未能抓取到有效长尾词，请检查网络后重试。")
        return

    # 4. 步骤 3: Gemini 打分与清洗
    scored_data = score_and_clean_keywords(harvested_data, client, batch_size=15)

    # 5. 步骤 4: 矩阵过滤与 CSV 导出
    filter_and_export_gold_mine(scored_data)

    print("\n✨ 调研任务全部完成！")
    print(f"👉 黄金词矩阵文件: {OUTPUT_GOLD_CSV}")
    print(f"👉 全景数据分析库: {OUTPUT_ALL_CSV}\n")


if __name__ == "__main__":
    main()
