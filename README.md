# cell-bio-ppt-notes

把**全英文的细胞学 / 组织学 / 分子生物学课件（.pptx）**整理成可直接复习的三件套：

1. **中英术语表** —— 每条术语都必须在课件原文里找得到，附页码；
2. **双语知识点讲义** —— 英文写成能直接答题的完整句，中文解释机制；
3. **配图** —— 优先用课件原图，需外补时只从授权可核实的图库取。

这是一个 Agent Skill（Claude Code / Qwen Code / Codex 通用），也可以脱离 Agent 单独用脚本。

Turn English life-science lecture slides into a bilingual study pack: a source-grounded
EN–ZH glossary, bilingual knowledge points, and figures (deck originals first, web
figures only from license-verified sources).

---

## 为什么不是"让 AI 直接总结一下"

模型凭常识写出来的术语表有两个硬伤：**术语可能课件里根本没有**，**中文译名可能是编的**。
这个 skill 用两个脚本把这两件事变成可检查的：

| 问题 | 本仓库的处理 |
|---|---|
| 术语是不是真出自课件？ | `slides.md` 是唯一文本源，术语搜不到就报 `hallucinated` |
| 中文译名准不准？ | 强制 `cross_check` 列，可对接术语在线 / MeSpEn 词表比对 |
| 配图有没有版权问题？ | 逐图登记作者 / 协议 / 来源页 / 核实日期，未核实不进正文 |
| 补充的知识点混进课件内容？ | 课件未提及的内容必须放 `> 补充 (课件未提及)` 引用块 |

---

## 安装

### 作为 skill 使用（推荐）

```bash
git clone https://github.com/Grace243197/cell-bio-ppt-notes.git
```

把整个目录放进你的 skills 目录：

- Qwen Code：`~/.qwen/skills/cell-bio-ppt-notes/`
- Claude Code：`~/.claude/skills/cell-bio-ppt-notes/`

之后在会话里说「用 cell-bio-ppt-notes 整理这份课件」，或直接 `/cell-bio-ppt-notes`。
Agent 会读 `SKILL.md` 按六步执行。

### 只用脚本

```bash
pip install python-pptx
python scripts/extract_pptx.py lecture03.pptx -o out/lecture03
python scripts/check_glossary.py --glossary out/lecture03/glossary.csv \
                                 --slides out/lecture03/slides.md
```

依赖：Python ≥ 3.9、`python-pptx`（仅此一项，无 API key、无联网）。

---

## 用法

### 第 1 步：抽取

```bash
python scripts/extract_pptx.py "D:\course\lecture03.pptx" -o "D:\course\lecture03"
```

| 参数 | 默认 | 说明 |
|---|---|---|
| `--min-px` | 200 | 两个方向都小于此值视为图标丢弃 |
| `--min-bytes` | 12000 | 小于此字节数丢弃（纯色/低熵图容易被误杀，可调低） |
| `--no-notes` | 关 | 不要 speaker notes |
| `--keep-decor` | 关 | 保留每页重复的校徽/模板装饰 |

产出：

```
out/lecture03/
├── slides.md      # 每页正文 + 表格 + notes + 图片引用（后续所有内容的唯一依据）
├── slides.json    # 结构化版本，便于二次处理
├── figures.csv    # 图片清单：slide / 文件 / 尺寸 / alt / 是否装饰
└── images/        # 去重后的图片；重复装饰在 images/_decor/
```

脚本行为：按「从上到下、从左到右」还原阅读顺序；递归展开组合形状；抓表格；
导出 notes；按 sha1 去重；出现在 ≥50% 页面的同一张图判为模板装饰。

### 第 2 步：填术语表

复制 `assets/glossary.template.csv`，按字段填：

| 列 | 要求 |
|---|---|
| `term_en` | 课件原拼写，保留连字符 |
| `term_zh` | 规范译名（术语在线 > 教材附录 > 自译），不要自创 |
| `abbr` | 有缩写才填 |
| `definition_en` | 一句话，≤25 词 |
| `definition_zh` | 一句话，术语中文名自然出现在句内 |
| `slide` | 首次出现的页码 |
| `figure` | 关联图路径，可空 |
| `cross_check` | `Slides` / `TermOnline:匹配` / `MeSpEn:匹配` / `Unverified` |
| `confidence` | `high` / `medium` / `low` |

数量基准：每 10 页 15–30 条。

### 第 3 步：校验（必过）

```bash
python scripts/check_glossary.py --glossary glossary.csv --slides slides.md --strict
```

检查项：缺列 / 缺中英文 / 重复词 / **术语在课件里搜不到** / 页码对不上 /
图片路径不存在 / `high` 却标了 `Unverified` / 哪些页没有收录术语。
有 error 时退出码为 1。

可选 `--mespen refs.tsv` 与中英医学术语底表比对（TSV，前两列为 en / zh），
不一致只报警告，需人工判断。

### 第 4–6 步

知识点六段式写法、配图授权规则、交付前自检清单，都在 [`SKILL.md`](SKILL.md) 里。

---

## 配图授权（重要）

`references/image-sources.md` 记录了 2026-11-22 逐页核实的结论：

- **Wikimedia Commons**：只收自由授权，必须逐图打开 `File:` 页确认许可/作者/来源。
- **Cell Image Library**：无统一授权，每图 5 类许可各不相同，必须开 detail 页；引用带 accession number。
- **OpenStax 解剖生理**：是 **CC BY-NC-SA 4.0**（常被误传为 CC BY）——个人复习可用，商用不行，
  改动后再发布须同协议。

原则：**优先用课件原图**；外补图必须满足「授权明确」+「内容经第二个来源确认」两条。
未能逐图核实的图，不放进交付物。

---

## 已知限制

- 只支持 `.pptx`；旧版 `.ppt` 先 `soffice --headless --convert-to pptx x.ppt`。
- 扫描版课件（整页是图片）抽不出文本，需要先 OCR。
- 图片过滤按尺寸+字节数，低熵图（纯色示意图）可能被误判，调低 `--min-bytes`。
- 术语表是**人机协作**产物：脚本负责"能不能溯源"，译名和机制仍需人工确认。
- 本仓库不包含任何课程课件；请勿把有版权的 PPT 提交进仓库（`.gitignore` 已挡 `*.pptx`）。

## 目录

```
SKILL.md                        Agent 执行规范（六步流程 + 硬规则 + 排错）
scripts/extract_pptx.py         pptx → slides.md / slides.json / figures.csv / images/
scripts/check_glossary.py       术语表质量闸门
assets/glossary.template.csv    术语表表头
assets/study_guide.template.md  讲义骨架
references/image-sources.md     配图来源白名单与授权核实
references/verification.md      高频错译表 + 机制幻觉自查清单
```

## License

MIT，见 [LICENSE](LICENSE)。`references/` 中的授权结论是对第三方站点条款的转述，
引用其内容时请以原始页面为准。
