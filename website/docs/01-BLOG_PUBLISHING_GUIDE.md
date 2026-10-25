# Not This Time 博客发文与日常运维实操指南

本文档为 **Not This Time（我忍住啦）** 官方网站博客系统的日常更新与内容管理指南。

系统基于 **Astro 静态站点生成器** 与 **GitHub Actions 自动化 CI/CD** 构建。日常发文推荐使用 **GitHub 网页端 0 占用方案**，无需在本地电脑保存任何文件，也无需打开终端敲代码。

---

## 🚀 核心写作流程（云端 0 占用）

### 第一步：在 GitHub 网页新建文章

1. 浏览器打开博文存放目录：  
   👉 **[点击进入 GitHub 文章目录](https://github.com/feeline03/notthistime/tree/main/website/src/content/blog)**
2. 点击右上角 **`Add file` ➔ `Create new file`**。
3. **命名规范**：
   - 英文小写，用连字符 `-` 连接，必须以 `.md` 结尾。
   - 例如：`how-to-delay-late-night-snacking.md`
   - *（该文件名会自动成为该文章的线上 URL 路径：`/blog/how-to-delay-late-night-snacking/`）*

---

### 第二步：编写头部元数据 (Frontmatter)

在新建的 Markdown 文件最顶部，必须包含以下被 `---` 包裹的元数据。系统已开启 `z.coerce.date()` 智能容错：

```markdown
---
title: "你的文章主标题（包含核心搜索词）"
description: "1~2 句话的核心摘要，供 Google 搜索结果和社交卡片展示"
pubDate: "2026-10-25"
category: "Mindful Eating"
readingTime: "4 min read"
tags: ["late-night-snacking", "urge-surfing", "habit-loop"]
---
```

#### 字段说明：
| 字段名 | 必填 | 说明 |
| :--- | :---: | :--- |
| `title` | **是** | 文章大标题（页面唯一的 `<h1>`，也是 Google 搜索结果的标题） |
| `description` | **是** | **SEO 核心摘要**（吸引点击的关键，建议 100~160 字符） |
| `pubDate` | **是** | 发布日期，格式 `YYYY-MM-DD`（带引号或不带引号均可） |
| `category` | 否 | 分类标签（如 `Mindful Eating`、`Behavioral Science`） |
| `readingTime` | 否 | 预估阅读时间（如 `5 min read`），默认 `4 min read` |
| `tags` | 否 | 标签数组，例如 `["tag1", "tag2"]` |
| `draft` | 否 | 草稿标识。如果设为 `draft: true`，构建时自动忽略，不予上线 |

---

### 第三步：即时发布 vs 定时发布

* **即时发布（当天立刻上线）**：
  - `pubDate` 填写**当天或过去**的日期（如 `"2026-10-24"`）。
  - 保存后 GitHub Actions 会在 1 分钟内自动编译上线。
* **定时发布（未来排期上线）**：
  - `pubDate` 填写**未来**的日期（如 `"2026-10-28"`）。
  - 保存后，文章会暂存在仓库中，但 Astro 会**自动对所有读者和 Google 蜘蛛保持隐藏**（不生成 HTML、不在列表展示、不写入 Sitemap）。
  - GitHub Actions 每日凌晨自动巡检，到了设定的日期当天早上，文章会自动出现在官网上。
* **草稿暂存**：
  - 添加 `draft: true` 即可无限期草稿暂存，时间到了也不会发布。

---

### 第四步：正文排版规范

系统已配置专有的 **Typography 系统**，无需手动写 CSS 即可自动呈现舒适排版：

1. **标题层级**：正文请直接使用二级标题 `##` 和三级标题 `###`（一级标题 `<h1>` 会自动从 `title` 渲染）。
2. **重点金句**：使用引用块 `>`，会自动渲染为带有蓝色高亮边框和深蓝渐变背景的精致卡片。
3. **列表**：使用 `-` 或数字序号，系统已适配圆点符号与行间距。
4. **底层转化模块已自动化**：每篇文章底部系统会自动插入 **“厌倦了用意志力对抗深夜零食？下载 Not This Time”** 的高转化 App Store 下载卡片，正文中无需手动贴下载广告。

---

### 第五步：保存并发布

1. 点击网页右上角绿色的 **`Commit changes...`** 按钮。
2. 在弹出的浮窗中再次点击 **`Commit changes`** 确认。
3. 稍候 1~2 分钟，刷新线上页面即可看到新内容。
