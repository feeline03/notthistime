# Xiaohongshu Copy Adapter

Use for 小红书 text-only output.

## Source Of Truth

Read these before writing when available:

- `docs/竹子账号_内容创作instructions.md`
- `docs/竹子账号_hook库.md`
- `docs/竹子账号_关键词库.md`
- `docs/竹子内容数据总表.md`

## Goal

Optimize for search discovery, cover/title click, recognition, saves, and useful comments. Xiaohongshu is the main Chinese platform.

## Format

Produce:

- 【标题】30 字以内，前 15 字包含一个 matched search keyword.
- 【封面标题】严格不超过 16 字. Include line breaks if useful.
- 【图文分页】Only page copy, not image prompts. Use 5-8 pages when the user asks for carousel copy.
- 【正文】500-800 字 by default, short oral paragraphs.
- 【共鸣句】Mark the strongest concrete recognition sentence.
- 【标签】5-8 tags: main terms + secondary terms + account terms.
- 【结尾问句】Specific scene question.
- 【发布建议】One short note tied to the test.

## Hook Priority

Use this order:

1. 反认知型: user has felt it but does not know why.
2. 场景代入型: place the reader in a specific moment.
3. 体验型: make the reader experience the point.

Avoid:

- 结论型 hook that gives the answer too early.
- 背景交代型 hook about making the app or doing research.
- 预告型 hook.
- 转述型 hook as the first sentence.
- 泛情绪型 cover text.

## Keyword Rule

Pick one primary keyword before writing. The keyword decides the scene, and the scene decides the hook.

Preferred keywords from the current project file include:

- 馋了怎么办
- 抑制食欲
- 减肥坚持不住
- 无痛减肥
- 管住嘴

Do not force academic terms into titles. Users search for what happened to them, not the psychological term.

## Cover Rule

Prefer historically stronger cover structures:

- 结局型: `XX 的人，后来都___了`
- 反常识型: `你以为是___，其实是___`
- 具体场景 + 数字型: `忍了3分钟，那股馋劲儿消失了`

Avoid pure abstract emotion covers.

## Data-Aware Choices

Use `docs/竹子内容数据总表.md` to avoid weak patterns. Current signals:

- Concrete behavior and outcome beats are stronger than abstract emotion.
- "靠意志力减肥的人后来都怎么样了" is a useful winning pattern.
- "你戒不掉的不是糖，是情绪" and "心烦时你会做什么" are weak because they are too abstract.
