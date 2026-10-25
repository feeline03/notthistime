# Not This Time (我忍住啦) - Official Website & SEO Blog

The official website and behavioral science blog for **Not This Time** (iOS App: [App Store Link](https://apps.apple.com/app/6769012887)).

Built with **Astro**, **Tailwind CSS**, and **Astro Content Collections**. Engineered for zero client-side JavaScript overhead, near-instant first paint, top Lighthouse scores, and robust search engine indexing.

---

## 📚 官网文档中心 (Website & Blog Documentation)

所有关于官网与博客的运营、发文与架构指南均已集中整理在 [`website/docs/`](./website/docs/) 目录下：

- 📖 **[发文与日常运维实操指南](./website/docs/01-BLOG_PUBLISHING_GUIDE.md)**：包含 GitHub 网页端 0 占用写作、即时发布 vs 未来定时发布、排版规范。
- 🛠 **[系统架构与自动化部署说明](./website/docs/02-ARCHITECTURE_AND_DEPLOYMENT.md)**：包含 GitHub Pages 子路径与独立域名双模自适应、GitHub Actions CI/CD 与每日定时 Cron 巡检。
- 🎯 **[SEO 架构与高转化漏斗机制](./website/docs/03-SEO_STRATEGY_AND_FUNNEL.md)**：包含 Schema 结构化数据、黄金长尾词选题策略与 App 转化漏斗设计。

---

## 🚀 Features & Architecture

- **Astro Static Site Generator:** 100% pre-rendered HTML for maximum speed and SEO crawlability.
- **Dynamic Dual-Mode Base URL:**
  - **GitHub Pages Subpath:** Operates smoothly under `/notthistime/` (`https://feeline03.github.io/notthistime/`).
  - **Custom Domain Ready:** Automatically switches to root `/` when deploying to `notthistime.site` or when a `CNAME` is present / `CUSTOM_DOMAIN=true`.
- **SEO & Structured Data:**
  - Dynamic Open Graph cards, Twitter summary tags, and canonical links on all pages.
  - JSON-LD Structured Data: `SoftwareApplication`, `FAQPage`, and `BlogPosting`.
  - Automatic `sitemap-index.xml` and `sitemap-0.xml` generation via `@astrojs/sitemap`.
- **Markdown / Content Collections:** Type-safe blog management with frontmatter validation in `website/src/content/config.ts`.
- **High-Conversion Funnel Design:** Integrated App Store CTA blocks with app screenshots across home and blog articles.
- **Automated CI/CD:** Push to `main` automatically triggers GitHub Actions to build and publish to GitHub Pages.

---

## 🛠 Local Development

```bash
# Navigate to website directory
cd website

# Install dependencies
npm install

# Start local dev server (default runs at http://localhost:4321/notthistime/)
npm run dev

# Build for production (GitHub Pages subpath)
npm run build

# Preview production build locally
npm run preview
```

### Testing Custom Domain Mode Locally

```bash
cd website
CUSTOM_DOMAIN=true npm run build
```

---

## ✍️ How to Publish New Blog Posts

1. Create a new `.md` file inside `website/src/content/blog/` (directly via GitHub Web UI or locally), for example:
   `website/src/content/blog/my-new-article.md`

2. Include frontmatter at the top:
   ```markdown
   ---
   title: "Your SEO-Optimized Article Title"
   description: "A compelling 1-2 sentence meta description for Google snippets."
   pubDate: 2026-10-25
   author: "Not This Time Team"
   category: "Mindful Eating"
   readingTime: "4 min read"
   tags: ["urge-surfing", "habit-loop"]
   ---

   Your markdown content here...
   ```

3. Commit and push to `main` — GitHub Actions will automatically render and publish your article!

---

## ⚙️ GitHub Pages Setup in Repository Settings

To ensure GitHub Actions can deploy your site:
1. Go to your GitHub repository: `https://github.com/feeline03/notthistime`
2. Navigate to **Settings** → **Pages**.
3. Under **Build and deployment** > **Source**, select **GitHub Actions**.
4. Every push to `main` will now build and publish automatically!

---

## 🌐 Switching to Custom Domain (`notthistime.site`)

When ready to link your custom domain:
1. Add your custom domain in GitHub repository **Settings** → **Pages** → **Custom domain** (e.g. `notthistime.site`).
2. Add a `CNAME` file containing `notthistime.site` into `public/CNAME`.
3. Astro will automatically switch from `/notthistime` to `/` for all routes and asset paths.
