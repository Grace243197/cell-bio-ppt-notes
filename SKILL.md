---
name: cell-bio-ppt-notes
description: >
  Turn English life-science lecture slides (.pptx) into a bilingual study pack:
  a verified EN–ZH glossary, slide-grounded knowledge points with bilingual
  explanations, and figures extracted from the deck (web figures only from
  license-verified sources). Use when the user asks to 整理课件术语 / 做双语知识点笔记 /
  给课件配图 / build a vocabulary list or glossary from English slides, especially
  for cell biology, histology, molecular biology or medicine.
metadata:
  version: "1.0.0"
  license: "MIT"
  requires: "python>=3.9, python-pptx>=0.6.21"
---

# Cell-Bio PPT Notes

把一份**全英文课件**变成可直接复习的三件套：术语表、双语知识点、配图。

## 硬规则（违反即返工）

1. **Grounding（可溯源）**：每条术语、每条知识点都必须能在 `slides.md` 里找到出处，`slide` 列写页码。抓不到原文的概念，只能放进“补充”小节并明确标注“课件未提及”。
2. **双语**：术语给 `term_zh`；定义给 `definition_en` + `definition_zh` 两句，中文不是英文的逐字直译，要能独立读懂。知识点同样中英各一段（英文写成能直接答考卷的句子）。
3. **图优先用课件原图**：课件里的图 = 老师要考的那张图。只有课件缺图、图糊、或被截断时，才去找网络图。
4. **网络图必须过白名单 + 逐图核实 license**：见 `references/image-sources.md`。**禁止**凭记忆写图片 URL，必须实际打开页面确认。
5. **不许编造数字**：star 数、影响因子、发病率一类的外部数据，要么给出可点开的来源，要么不写。
6. **质量闸门**：`scripts/check_glossary.py` 必须 `exit 0` 才算交付。

## 产出目录

```
<course>/
  slides.md          # 由脚本生成，全部原文 + 图片引用（只读，勿手改）
  slides.json        # 结构化数据，脚本后续复用
  figures.csv        # 图片清单：slide / 文件 / 尺寸 / alt
  images/            # 课件原图（去重后）
  glossary.csv       # ★ 术语表（你要填）
  study_guide.md     # ★ 双语复习讲义（你要填）
  sources.md         # 所有外部图片与数据的来源登记
```

---

## 流程

### Step 0 — 定位课件

```bash
python "<SKILL_DIR>/scripts/extract_pptx.py" "D:\course\lecture03.pptx" -o "D:\course\lecture03"
```

参数：`--min-px 200`（小于此尺寸的图视为图标丢弃）、`--min-bytes 12000`、
`--no-notes`（不要备注）、`--keep-decor`（保留每页重复的校徽/模板装饰）。

脚本会：按“从上到下、从左到右”还原阅读顺序；递归展开组合形状；抓表格；
导出 speaker notes；按 sha1 去重图片；把出现在 ≥50% 页面的同一张图判为装饰，
移到 `images/_decor/` 且不入正文。

### Step 1 — 通读，先建“概念骨架”

读 `slides.md`，按课件自带的章节/标题切块，写一份 8–15 行的 `study_guide.md` 大纲
（中文小标题 + 对应 slide 区间）。**先有骨架再抽词**，否则术语表会变成散装单词。

### Step 2 — 抽术语，填 `glossary.csv`

字段（表头见 `assets/glossary.template.csv`）：

| 列 | 要求 |
|---|---|
| `term_en` | 课件原拼写，保留连字符（`tight junction`、`Golgi apparatus`） |
| `term_zh` | **规范译名**，优先与教材/术语在线一致；不要自创 |
| `abbr` | 有缩写才填（`ER`、`MTOC`） |
| `definition_en` | 一句话，≤25 词，用课件里的表述改写 |
| `definition_zh` | 一句话，术语中文名要在句内自然出现 |
| `slide` | 首次出现的页码数字 |
| `figure` | 关联图（`images/xxx.png` 或留空） |
| `cross_check` | `Slides` / `TermOnline:匹配` / `MeSpEn:匹配` / `Unverified` |
| `confidence` | `high` / `medium` / `low` |

数量基准：**每 10 页 15–30 条**，一份 40 页课件约 80–120 条。
只收“这门课会考的名词”，不收 `cell`、`protein` 这种已在高中解决的词，
但**要收**课件反复用的修饰性术语（`apical`、`basolateral`、`lumenal`）。

### Step 3 — 术语交叉校验

```bash
# 1) 结构与 grounding 检查（必过）
python "<SKILL_DIR>/scripts/check_glossary.py" --glossary glossary.csv --slides slides.md

# 2) 有中英术语底表时，再核对译名是否与权威库冲突
python "<SKILL_DIR>/scripts/check_glossary.py" --glossary glossary.csv --slides slides.md \
       --mespen "D:\refs\MeSpEn_zh_en.tsv"
```

`--mespen` 接受 TSV，取前两列为 `en` / `zh`；不一致只报警告（权威库未必覆盖新术语），
但**必须人工判断并在 `cross_check` 里注明**。

`--strict` 会把“页码对不上”“high 置信度却标 Unverified”升级为错误；
封面/目录/纯表格页（正文少于 25 词，或标题含 title/agenda/outline/references）
不计入覆盖率，不会被误判。

译名拿不准时按优先级：课件自带中文 > 术语在线(termonline.cn) > MeSpEn > 教材附录。
`low` 置信度的词，在 `study_guide.md` 里单独列一节“译名待确认”，别混进正文。

### Step 4 — 写知识点（双语）

每个知识块固定六段，缺一段就是没写完：

```markdown
#### 3.2 紧密连接 / Tight junction  — Slide 14

**原文要点**：相邻细胞膜之间形成连续的封闭带，阻断细胞间隙的分子扩散。

**English**：Tight junctions form a continuous sealing band between adjacent
plasma membranes. They block paracellular diffusion, so molecules must cross
the cell membrane instead of slipping between cells.

**中文**：紧密连接是相邻细胞膜之间一圈连续的闭合带，把细胞间隙“封死”。
物质不能从细胞之间漏过去，只能穿过细胞膜，因此它是上皮屏障功能的结构基础。

**为什么重要 / Why it matters**：血脑屏障、肠上皮、肾小管都靠它维持极性
和选择性通透。

**易混 / Common confusion**：紧密连接封的是**细胞间隙(paracellular)**，
不是细胞膜本身；封闭小带(zonula occludens)是它在电镜下的形态名。

**考点 / Exam angle**：能给出血脑屏障的例子；能区分 tight / gap / desmosome。
```

规则：
- **英文段写完整句**，不写关键词堆砌——那是可以直接抄上答卷的句子。
- 中文段解释机制，不复述英文。
- 每条知识点标注 slide 号；课件没讲但必须懂的（如“为什么需要胆固醇”），
  另起 `> 补充 / Supplement (课件未提及)` 引用块，明确区分。

### Step 5 — 配图

**先看 `figures.csv`**，把课件图对上知识点：`figure` 列写上路径即可。
判断“这张图能不能用”的标准：读者只看图能否复述该机制；能，就别换。

确实缺图时才联网补，规则见 `references/image-sources.md`（含已核实的授权状态）。
每一张外部图都要在 `sources.md` 登记：

```markdown
| 用于 | 图片 | 作者 | 协议 | 来源页 | 核实日期 |
|---|---|---|---|---|---|
| Slide 14 紧密连接 | File:Cell junction types.svg | Mariana Ruiz | Public domain | https://commons.wikimedia.org/wiki/File:... | 2026-11-22 |
```

并做**双重确认**：① 图片描述页的 license 明确允许使用；② 再用一个独立来源
（教材正文或综述）确认图示结构与课件讲法不矛盾。两者都满足才插入。

### Step 6 — 交付前自检

- [ ] `check_glossary.py` exit 0
- [ ] `glossary.csv` 里每个 `figure` 指向的文件都存在
- [ ] 每个 `## Slide N` 章节至少 1 条术语（覆盖检查脚本会列出空页）
- [ ] 中英段落都不含“待补充/TODO”
- [ ] `sources.md` 行数 = 外部图片数（课件原图不需要登记）
- [ ] 术语表里没有把 `Unverified` 的词标成 `high`

自检脚本：

```bash
python "<SKILL_DIR>/scripts/check_glossary.py" --glossary glossary.csv --slides slides.md --strict
```

---

## 写作口径

- 面向“三天后要考试的人”：每段先给结论，再给机制。
- 术语第一次出现时写 `中文 (English)`，之后只用中文。
- 不用“众所周知”“显然”。
- 数字只写课件给得起的；课件给了数值就照抄并标 slide。

## 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| `figures: 0` | 课件图是纯色/低熵 PNG，压缩后小于 `--min-bytes` | 降为 `--min-bytes 3000 --min-px 150` 重跑 |
| 文本为空、每页只有一张大图 | 扫描版/图片版课件 | 需要 OCR（先跑一遍 OCR 再拼进 `slides.md`，或直接用原图配知识点） |
| 报 `not a PowerPoint file` | 文件是旧版 `.ppt` | `soffice --headless --convert-to pptx x.ppt` 后重跑 |
| 正文顺序乱 | 形状是组合/自由布局 | 脚本已按 top→left 排序；仍乱则手动调整 `slides.md`（它是只读参考，可以改） |
| 中文在命令行显示为乱码 | cmd 代码页非 UTF-8 | 文件本身是 UTF-8，不影响；用编辑器看即可 |

## 参考文件

- `references/image-sources.md` — 配图来源白名单、逐图核实步骤、已核实的授权结论
- `references/verification.md` — 术语与知识点的交叉校验清单、常见幻觉模式
- `assets/glossary.template.csv` — 术语表表头
- `assets/study_guide.template.md` — 讲义骨架
