# 交接文档：Paper A（RAG 投毒公平性）· 从卡住的会话接续

生成时间：2026-09-25。来源会话标题：**LLM安全与RAG安全论文整理**（`session-cce11aab…`，工作目录 `G:\keyan`）。
本文件是**新对话的接续入口**：读这一份即可继续，不需要原会话的上下文。

---

## 1. 一句话现状

论文主体**已经写好并产出 PDF**，4 张数据图**已插入**。卡住的原因**不是论文本身**，
而是会话里混入了一张图片，导致**之后每一轮都失败**。**插图这件事不需要模型"看"图**——用文件路径即可完成。

## 2. 卡住的根因（已定位，不是猜测）

- 第 55 轮：助手调用 `read_image` 读取 `C:\Users\Administrator\Downloads\image.png`；
- 该工具的返回值里包含一个**真正的 image 内容块**，它被写进了会话历史；
- 会话历史在**每次请求时都会被重新序列化**，而 DeepSeek 的 chat-completions 适配器
  （`dsh-llm-deepseek/lib/index.js`，`assertTextOnly()`）是**纯文本**的，遇到图片块直接抛错：
  `The DeepSeek chat-completions adapter does not support image content. (UNSUPPORTED_CONTENT)`
- 于是从那个时刻起，**该会话的每一轮都必然失败**——历史里那张图无法被移除。

**为什么会走到这一步**：此前按"切换多模态"的指示改了模型声明（`settings.yaml` 里给 `deepseek-flash` 加了
`inputModalities: ["text","image"]`）。但**声明改不了适配器**——适配器仍然拒绝图片。声明与能力不一致，
于是前端放行、适配器拒绝。**该错误声明已移除**（2026-09-25 修正，现已与 `settings.yaml.vision-backup` 一致）。

> 结论：**在这台机器当前的 provider 配置下，图片无法进入模型。**
> 只配置了 `deepseek-official` 与 `packyapi`（都走纯文本适配器），能支持视觉的 `llm-pi-ai` 是 `providers: {}`（空）。
> 想真正支持视觉，需要另配一个支持视觉的 provider。

## 3. 产物清单（都已落盘）

项目根目录：`G:\keyan\projects\rag-poison-fairness`

| 文件 | 说明 |
|---|---|
| `paper/manuscript_R1R2_v1.md` | **Paper A 正文源**（138 KB），最后修改 9-24 21:55 |
| `paper/latex/paperA_R1R2.tex` | LaTeX 源（169 KB），最后修改 9-24 21:59 |
| `paper/latex/paperA_R1R2.pdf` | **可投稿 PDF**（391 KB），9-24 22:17 |
| `paper/manuscript_R1R2_v1.docx` | Word 版（577 KB） |
| `paper/manuscript_B_adaptive_v1.md` / `paper/latex/paperB_adaptive.pdf` | Paper B（自适应变体） |
| `paper/figures/` | 4 张数据图（`fig_responsiveness`、`fig_r1_inertness`、`fig_encoder_scale`、`fig_aggregate_vs_pergroup`，各含 .pdf/.png） |
| `paper/stats_tables.md`、`paper/formal_analysis.md` | 统计表与形式化分析 |
| `README.md` | 项目说明 |
| GitHub | `https://github.com/luj00133-dev/rag-poison-fairness` |

另有一份早前的调研产物：`G:\keyan\LLM-RAG安全_最新高分区论文10篇.md`（10 篇论文整理）。

**Paper A 里已有的 4 个图**（`paperA_R1R2.tex` 中的 `\includegraphics`）：
`fig_responsiveness.pdf`(140mm)、`fig_r1_inertness.pdf`(140mm)、`fig_encoder_scale.pdf`(88mm)、`fig_aggregate_vs_pergroup.pdf`(88mm)。

## 4. 卡住的那件事：插图（**现在可以做了，且不需要模型看图**）

ChatGPT 生成的概念图已下载到 `C:\Users\Administrator\Downloads`：

| 文件 | 尺寸 | 比例 |
|---|---|---|
| `image.png` | 2880×1440 | 2:1 |
| `image (1).png` | 2048×2048 | 1:1 |
| `image (2).png` | 2880×1440 | 2:1 |
| `image (3).png` | 2880×1440 | 2:1 |
| `image (4).png` | 2880×1440 | 2:1 |

**做法**（不需要 `read_image`，也不需要视觉模型）：
1. 把这几个 png 复制到 `paper/figures/` 并改成有意义的名字（如 `fig_framework.png`、`fig_threat_model.png`）；
2. 在 `paperA_R1R2.tex` 的相应位置加：
   `\includegraphics[width=140mm]{fig_framework.png}`（2:1 的图用 140mm；1:1 的用 88mm）；
3. 重新编译，或把 tex 交给已有流程重出 PDF。

**模型不需要"看见"这些图**：它们是概念/框架示意图，图注由你或文本层面的描述来定；
若需要核对某张图的内容，**你自己看一眼**比让模型看图更可靠（当前也做不到）。

## 5. 下一步（按优先级）

1. **插图**：按 §4 把概念图插入 `paperA_R1R2.tex`（这是卡住前的最后一件事）。
2. **投稿决策**：原会话讨论过 "Paper A 投稿能中的概率" 与 "提高录用率/加强卖点"。
   若要把这一步做实，建议用**证据驱动**的做法：先确定候选刊（订阅制、分区达标、scope 匹配），
   再针对该刊补实验或改结构——而不是先改稿再找刊。
3. **Paper B 是否并入 Paper A**：原会话问过"并入之后能否提高录用率"，尚未定论。
4. **补实验（可选）**：曾讨论本地 5060 8GB 的 CUDA 环境、更大 checkpoint（E5-large / SPLADE-large）、
   生成层评估等。这些是**加分项**，不是投稿阻塞项。

## 6. 两个必须提醒你的安全问题

1. **原会话里出现过明文密钥**：DeepSeek API key 与**多个 GitHub PAT**（`ghp_…`）都直接写在对话里，
   而该会话已被导出为明文文件。**建议立刻到 GitHub 撤销这几个 PAT 并重新生成**，
   API key 也建议轮换。我在此文档里**没有**复述这些密钥。
2. 我为了分析，把该会话解密导出的临时文件放在 `G:\keyan\`：
   `_session_dump.jsonl`（33 MB）、`_turns_A_target.txt`、`_user_turns.txt`。
   **它们包含对话全文**（即也包含上面的密钥）。看完后建议删除。

## 7. 若要恢复原会话（可选，技术上可行）

原会话卡住的**唯一**原因就是历史里那**一个**图片块。移除它即可让 62 轮上下文全部恢复可用
（该块旁边的文本已包含文件路径、尺寸、字节数，信息不会丢）。
但这属于改写会话存储文件，我会在做之前先备份、并在改后校验。
**你不需要它也能继续**——本文件已经足够开新对话。
