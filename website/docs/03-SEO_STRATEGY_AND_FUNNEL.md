# Not This Time 官网 SEO 架构与高转化漏斗机制

本文档说明官网在搜索引擎优化（SEO）和流量转化（App Store Download Funnel）上的核心设计，供日后内容规划与增长策略参考。

---

## 🎯 核心价值主张与定位

- **产品定位**：一款专注于**“吃之前暂停 3 分钟”**的冲动阻断与行为干预 iOS App。
- **目标痛点**：深夜暴食、无意识吃零食、情绪进食、减肥期破戒自责、意志力耗竭。
- **差异化优势**：无账户注册、无复杂记录、100% 本地离线隐私保护、Urge Surfing 冲浪心理学、听觉锚定。

---

## 🔍 SEO 底层架构与规范

### 1. 结构化数据 (JSON-LD Schema)
- **首页**：
  - `SoftwareApplication`（标记为 iOS 健康/正念饮食类 App，标注下载链接与免费属性）。
  - `FAQPage`（常见问题解答富摘要，直接展示在 Google 搜索结果列表中）。
- **博客详情页**：
  - `BlogPosting`（标记标题、作者、发布日期、修改日期、正文与配图，利于 Google 抓取收录与展示精选摘要）。

### 2. 动态 Meta 与社交分享卡片
每个页面独立生成以下元标签（位于 `src/layouts/BaseLayout.astro`）：
- `canonical`（权威链接，避免重复内容惩罚）
- `og:title`, `og:description`, `og:image`, `og:type`, `og:url`（微信、Telegram、推特等社交平台预览卡片）
- `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`（大图分享卡片）

### 3. Sitemap 与 Robots
- 自动生成 `sitemap-index.xml` 和 `sitemap-0.xml`，所有 URL 自动适配当前子路径或独立域名。
- `public/robots.txt` 声明允许爬虫全站抓取，并指明 Sitemap 入口。

---

## 🧲 黄金长尾词选题策略（转化漏斗）

结合仓库中 `SEO_agent/gold_mine_keywords.csv` 的真实挖掘结果，以下长尾词具有**“极高搜索意图 + 极低竞争度”**，建议作为博客文章的持续选题来源：

| 选题关键词 | 核心痛点与切入角度 | 推荐行动召唤 (CTA) |
| :--- | :--- | :--- |
| `how do you stop yourself from binge eating late at night when bored` | 剖析深夜无聊时的多巴胺寻求与血糖波动 | 推荐使用 3 分钟倒计时阻断从“沙发到冰箱”的自动化路径 |
| `every night i promise myself i won't raid the fridge but i fail` | 深度共情意志力耗竭与自责羞耻感，提出“机制胜过毅力” | 引导使用 App 充当厨房前的物理缓冲区 |
| `tricks to delay late night snacking for 10 minutes until urge passes` | 拆解 Urge Surfing 冲浪心理学（冲动波峰 3~5 分钟回落） | 引导使用 3~10 分钟冲浪倒计时与听觉锚定 |
| `any app or timer that helps stop impulsive eating at night` | 对比卡路里记录软件（反人性、耗精力）vs 进食前阻断工具（单点极简） | 强调 Not This Time 的 0 记录、0 社交、专注抚慰白噪音体验 |

---

## 📈 高转化漏斗组件 (`AppCtaBanner`)

每篇博文的底部均自动注入 [`AppCtaBanner.astro`](file:///Users/wuhangyan/Documents/claude/notthistime/src/components/AppCtaBanner.astro) 组件：
- 核心文案：“*厌倦了用意志力对抗深夜零食？下载 Not This Time 开启 3 分钟行为干预*”
- 视觉呈现：高对比深色卡片 + 3 分钟真机定时界面截图 + 一键直达 App Store 按钮。
- 用户心理学：在读者被科普文章打动、认识到意志力无法对抗深夜本能的瞬间，提供立即可行、阻力最小的解决方案（一键下载 App）。
