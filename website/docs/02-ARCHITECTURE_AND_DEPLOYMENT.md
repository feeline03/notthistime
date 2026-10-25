# Not This Time 官网架构与自动化部署说明

本文档说明 **Not This Time（我忍住啦）** 官网与博客系统的底层架构、双模路径适配机制以及 GitHub Actions 自动化 CI/CD 流程。

---

## 🛠 技术栈概览

- **框架**：[Astro v4](https://astro.build/)（极速内容驱动型框架，默认预渲染零客户端 JS）
- **样式**：[Tailwind CSS v3](https://tailwindcss.com/) + `@tailwindcss/typography`（专为暗色长文优化）
- **内容管理**：Astro Content Collections（强类型 Frontmatter 校验，支持 Markdown / MDX）
- **SEO 插件**：`@astrojs/sitemap`（全自动生成 `sitemap-index.xml` 和 `sitemap-0.xml`）
- **托管服务**：GitHub Pages（由 GitHub Actions 官方工作流驱动）

---

## 🌐 路径兼容：GitHub Pages 子路径与独立域名双模自适应

为了防止 GitHub Pages 子路径（`/notthistime/`）下的资源 404，同时确保后续一键绑定独立域名（`notthistime.site`），系统实现了智能双模适配：

### 1. `astro.config.mjs` 中的自适应逻辑
```javascript
const hasCNAME = fs.existsSync('./public/CNAME') || fs.existsSync('./CNAME');
const isCustomDomain = process.env.CUSTOM_DOMAIN === 'true' ||
                       process.env.SITE_URL === 'https://notthistime.site' ||
                       hasCNAME;

const site = isCustomDomain 
  ? 'https://notthistime.site' 
  : 'https://feeline03.github.io';

const base = isCustomDomain ? '/' : '/notthistime';
```

- **当前阶段（GitHub Pages 子路径）**：
  - `site` = `https://feeline03.github.io`
  - `base` = `/notthistime`
- **未来切换独立域名（`notthistime.site`）**：
  - 只需在 GitHub 仓库 **Settings ➔ Pages ➔ Custom domain** 绑定域名（或在 `public/CNAME` 写入域名）。
  - 系统自动将 `base` 切换为根路径 `/`，`site` 切换为 `https://notthistime.site`，**零代码修改**。

### 2. 路由与资源辅助函数 `withBase()`
位于 `src/utils/paths.ts`：
所有站内路由（如首页、博客页、隐私政策）、静态资源（Logo、截图、Favicon）均由 `withBase()` 包装，保证无论 base 是 `/notthistime` 还是 `/`，绝不会出现死链。

---

## 🤖 自动化部署工作流 (GitHub Actions)

工作流文件位于 [`.github/workflows/deploy.yml`](file:///Users/wuhangyan/Documents/claude/notthistime/.github/workflows/deploy.yml)。

### 触发条件：
1. **代码推送**：每次执行 `git push origin main` 时触发构建并发布。
2. **定时触发 (Cron)**：配置了 `cron: '0 0 * * *'`（每天 UTC 0:00，即北京时间早 8:00）自动唤醒构建一次，发布到达当天的定时排期文章。
3. **手动触发**：支持在 GitHub 仓库 **Actions** 标签页点击 **Run workflow** 手动重新构建。

### 权限要求：
```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### GitHub 仓库设置要求：
- 进入 `https://github.com/feeline03/notthistime/settings/pages`
- **Build and deployment ➔ Source** 必须保持选择为 **GitHub Actions**。
