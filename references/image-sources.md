# 配图来源与授权核实

> 本文件的授权结论均在 **2026-11-22** 打开原始页面核实，不是凭印象写的。
> 授权会变，超过半年的结论要重新打开页面确认。

## 优先级

1. **课件原图**（`figures.csv`）——老师要考的就是这张图，且不涉及外部授权。
2. **开放授权的标准图**（下表）——只在课件缺图/图被截断时使用。
3. **自己画**——用文字描述 + 简笔示意图（Mermaid / SVG），零授权风险。
4. 教材社图、Google 图片直链、Pinterest、ResearchGate 转载图 —— **不用**。

## 已核实的可用来源

### Wikimedia Commons

- 只收录自由授权内容：CC BY、CC BY-SA、CC0、Public Domain 等；
  **禁止** NC（非商业）与 ND（禁止演绎）素材进入。
- 因此 Commons 上的图**可以**用于课程作业/个人复习，商业用途也允许。
- **必须逐图打开 `File:` 描述页**确认四件事：许可标签、来源链接、作者、是否为
  "Own work"。仅看缩略图或搜索结果不算核实。
- 署名方式：作者 + 许可名 + 链接 + 是否修改。
- 核实页面：https://commons.wikimedia.org/wiki/Commons:Licensing

### Cell Image Library (CIL)

- 网址：https://www.cellimagelibrary.org
- **没有统一授权**：提交者从 5 种里选一种——Public Domain / CC BY / CC BY-NC-SA /
  CC BY-NC-ND / 保留版权需申请。
- 所以**必须打开该图的 detail 页面**看它自己的 license；首页或搜索页看不出授权。
- 官方要求引用格式含 accession number，例：`CIL:XXXXX, Cell Image Library (RRID:SCR_003510)`。
- 核实页面：https://www.cellimagelibrary.org/pages/license

### OpenStax（Anatomy & Physiology 等）

- ⚠️ 常被误传为 CC BY，实际核实的结论是
  **CC BY-NC-SA 4.0**（非商业 + 相同方式共享）。
- 含义：个人复习、课堂作业可用；**不能**用于商业产品；若你改动图片再发布，
  衍生作品也要按 CC BY-NC-SA 发布，并署名 OpenStax。
- 核实页面：https://openstax.org/books/anatomy-and-physiology-2e/pages/1-introduction

**校验用术语库（不是图）**

- 术语在线 https://www.termonline.cn —— 全国科学技术名词审定委员会，权威中文译名。
- MeSpEn_Glossaries（GitHub）—— 中英医学词表 93,736 条，2018 年后停更，
  协议标注 NOASSERTION，使用前看清仓库说明。

## 使用前必须核实、本文未背书的来源

以下来源**看起来**适合细胞学配图，但我没有在本轮核实其条款，用前自己打开页面确认：

- NIH / NIGMS Image Gallery（美国政府作品通常属公有领域，但需逐图确认）
- BioRender（免费版有署名要求，且对发表场景有限制）
- 各大学开放课程（OCW）的课件图（多为 CC BY-NC-SA，逐图看）
- Histology Guide、Wikimedia 上的教材扫描图（可能仍是出版社版权）

## 每张图的登记格式

写入 `sources.md`，一行一图：

```markdown
| 用于 | 图片 | 作者 | 协议 | 来源页 | 核实日期 |
|---|---|---|---|---|---|
| Slide 14 紧密连接 | File:Cell junction types.svg | Mariana Ruiz Villarreal | Public domain | https://commons.wikimedia.org/wiki/File:Cell_junction_types.svg | 2026-11-22 |
```

## 双重确认（缺一不可）

1. **授权确认**：描述页的许可标签明确允许你的用途（作业/个人复习）。
2. **内容确认**：用另一个独立来源（教材正文、综述、另一张图）确认这张图画的
   结构与课件讲法一致——很多"漂亮图"画的其实是另一种连接/另一种细胞。

两条都满足才插入。只满足第一条 → 图先放 `sources.md` 的候选区，不进正文。

## 常见错误

- 引用了 Wikipedia **条目页**却当成图片授权页 —— 条目文字是 CC BY-SA，
  条目里嵌的图各有各的许可。
- 把 CC BY-NC（非商业）的图放进要参赛/要商业化的作品。
- 直接贴 `upload.wikimedia.org/...` 直链而不给 `File:` 页面 —— 无法追溯作者与许可。
- 用了一张"看起来像"的图，但图里标的是别的结构（如把微绒毛画成纤毛）。
- 忘了标注"已修改"（裁剪、加箭头、翻译图注都属于修改）。