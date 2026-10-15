# 视频制作指南 ——《百法》系列五讲 + 「佛学图文」系列 提炼

> 这份指南把 V1-V5 五讲视频（slidev）和「佛学图文」系列（cards.html 图卡）的流程、风格、约定 总结成一份可复用的规范。
> 下一次做新视频时，只要引用本文件，就能保持一致的输出。
>
> **配音的模型、音色、API key 一律以 env 为准**（本机 `~/.env`，云端会话的环境变量），本文件和仓库里都不写死具体的 voice id——音色会重新复刻、模型会升级，写死的值很快就过期。见 [TTS 合成约定](#tts-合成约定)。

---

## 目录

1. [项目结构](#项目结构)
2. [完整流程（7 步）](#完整流程)
3. [PPT（slides.md）风格](#ppt风格)
4. [口播稿（notes/）风格](#口播稿风格)
5. [TTS 合成约定](#tts-合成约定)
6. [视频合成约定](#视频合成约定)
7. [字幕约定（ASS）](#字幕约定)
8. [校验规范（佛学经典）](#校验规范)
9. [发布文案约定](#发布文案约定)
10. [git / 提交约定](#git--提交约定)
11. [常见坑 + 修复方法](#常见坑)

---

## 项目结构

现在有两种项目：

- **「佛学图文」系列**（2026-09 起，当前在用）：`videos/<slug>-infographic/`，图卡用一份 `cards.html` 画，headless Chrome 导出 PNG。
- **slidev 系列**（《百法》《八识规矩颂》V1-V5，旧流程）：`videos/<slug>-slidev/`。

### 「佛学图文」项目（当前）

```
videos/<slug>-infographic/
├── cards.html                 # 全部图卡，一张 <section class="card"> 一张卡；?c=N 单独显示第 N 张
├── render.sh                  # 逐张导出 out/card-N.png（1920×1080；张数按 cards.html 自动计算）
├── out/                       # 导出的图卡 PNG
├── scripts/
│   ├── synth.py               # notes/NN.txt → audio/NN.wav（读 env 里的模型和音色）
│   ├── build_video.py         # 图卡 + 配音 → video/，生成字幕；--subs-only 只重做字幕和硬字幕版
│   └── *.py                   # 需要时：用脚本生成的 SVG 图（如思维导图）
├── notes/                     # 口播稿，01.txt..NN.txt，与 out/card-N.png 一一对应
├── script.md                  # 由 notes 拼成，便于通读；开头是读音表
├── sources.md                 # 引文核对记录（CBETA 原卷逐字核对）
├── audio/                     # 配音 WAV（入仓）
├── segments/                  # ffmpeg 中间产物（gitignore）
├── video/                     # <slug>.mp4、<slug>-hard.mp4、<slug>.srt/.ass、<slug>.zh-TW.srt
└── PUBLISH.md                 # 简繁两版发布文案（标题、摘要、正文、章节时间戳、标签）
```

图文同时出一篇网站文章：`_posts/YYYY-MM-DD-<slug>.md`，配图是 `images/YYYY-MM-DD-<slug>-card-N.jpg`（由 out/ 的 PNG 转 JPG）。新项目初始化：复制上一期的 `cards.html`（保留页眉、页脚、署名的样式）、`render.sh`、`scripts/synth.py`、`scripts/build_video.py`，改 `build_video.py` 里的 `SLUG`。

### slidev 项目（旧流程）

每个视频是一个独立的 slidev 项目，放在 `videos/<slug>-slidev/`：

```
videos/
├── <slug>-ppt-outline.md          # 大纲（先写）
├── <slug>-slidev/
│   ├── slides.md                  # PPT 内容（Markdown）
│   ├── style.css                  # 字体 / 字号 / 留白
│   ├── package.json + package-lock.json
│   ├── .bailian_voice_id          # 旧：cosyvoice 克隆音色 ID。新项目不再用，音色以 env 为准
│   ├── notes/                     # 口播稿，01.txt..NN.txt 每页一段
│   ├── preview/                   # slidev 导出的 PNG（1.png..N.png）
│   ├── audio/                     # cosyvoice 合成的 MP3（01.mp3..NN.mp3）
│   ├── segments/                  # ffmpeg 中间产物（gitignore）
│   ├── video/                     # 最终 MP4 + SRT + ASS
│   │   ├── <slug>.mp4             # 无字幕 base
│   │   ├── <slug>-hard.mp4        # 硬字幕版
│   │   ├── <slug>.srt             # 软字幕
│   │   └── <slug>.ass             # ASS 格式
│   ├── scripts/                   # 复用脚本（synth-all / build-video / build-hard-subbed-video）
│   ├── PUBLISH.md                 # 简繁两版发布文案
│   └── PUBLISH-AI.md              # AI 推荐用文案（关键词 + 章节戳）
```

新项目初始化：从最近的项目（V5 jiandao）复制 `package.json` / `package-lock.json` / `style.css` / `scripts/`，然后 `npm install`。配音改用 env 里的模型和音色（见 TTS 一节），不再复制 `.bailian_voice_id`。

---

## 完整流程

「佛学图文」项目的顺序：画图卡（`cards.html` → `render.sh`）→ 写网站文章 → 写口播稿 → 用户 review → 合成配音（`python3 scripts/synth.py`）→ ASR 核对读音 → 合成视频（`python3 scripts/build_video.py`）→ 写 `PUBLISH.md`。下面的表格是 slidev 项目的七步。

**七步走，每步可独立 iterate：**

| # | 步骤 | 文件 / 命令 | 时长 |
|---|---|---|---|
| 1 | **写大纲** | `<slug>-ppt-outline.md` —— 用户 review 后再开始 PPT | 1-2 小时 |
| 2 | **写 slides.md** | 按大纲展开 ~25-32 页 | 1-2 小时 |
| 3 | **导出 PNG** | `./node_modules/.bin/slidev export --format png --output preview` | 1-2 分钟 |
| 4 | **写口播稿** | `notes/01.txt..NN.txt` 每页一段，**口语化** | 2-3 小时 |
| 5 | **合成音频** | `/usr/bin/python3 scripts/synth-all.py` —— 4 并发 cosyvoice | 3-5 分钟 |
| 6 | **合成视频** | `build-video.py` → `build-hard-subbed-video.py` | base 几分钟 + hard 25-30 分钟 |
| 7 | **写发布文案** | `PUBLISH.md` + `PUBLISH-AI.md`（简繁两版）| 30 分钟 |

**每一步用户都要 review。** 不要假设可以一气呵成跑完。

---

## PPT 风格

### 主题 / 字体

- 主题：`@slidev/theme-seriph`
- 字体：思源黑体 / 思源宋体（`Noto Sans SC` / `Noto Serif SC`），通过 Google Fonts
- 背景：米白色（`bg-amber-50` 系列 / `bg-stone-50`）
- 主色调：青灰色 + 棕褐色（佛学典雅风）
- `style.css` 设大字号、宽松行距、移动端友好

### slides.md 写法约定

| 项 | 约定 |
|---|---|
| 加粗 | 用 `<strong>...</strong>` 而不是 `**...**`（CJK 标点附近 markdown 加粗会失败）|
| 列表数字 | 加「个」量词：「8 个」「34 个」「6 个根本烦恼」|
| 公式 | 用中文 加 / 等于 而不是 `+` `=`（TTS 会念「加号」「等号」）|
| 章节标题 | 「章节名 · 子标题」格式，子标题用 `<div class="text-3xl mt-4">...</div>` |
| 内容页标题 | **含章节关键词**，避免「对照颂文」这种孤立标题——改成「五蕴 · 对照颂文」|
| 表格 | 优先 markdown 表格；复杂布局用 `<div class="grid grid-cols-2 gap-3">` |
| 强调框 | `<div class="mt-4 p-3 bg-amber-50 rounded">...</div>` 米黄；`bg-stone-50` 米灰 |
| 经典引用 | 「《XX论》卷 NN：「**XX**」」整段 |
| 多音字 | PPT 上显示规范写法；口播稿用同音字替换让 TTS 读对（见 [TTS 约定](#tts-合成约定)） |
| 数字 | 三十七道品、十六行相 用中文；其他计数用阿拉伯（4+4+4+5+5+7+8）|

### 禁忌

- **不写梵语音译**（删「三摩地」改「定」；删「萨迦耶见」用「身见」即可，第一次出现可以加注）
- **百法**作为专有名词，不要再写「100 法」/「100法」
- 不要在引用大乘 / 唯识独有概念时混入声闻立场（**立场要明确**）
- 不写「开悟」「证悟」这种容易引发歧义的字眼（用「见道」「证果」）
- 标题不用 emoji
- 不在 markdown 里写 `**X**Y` 模式当 X 后跟 CJK 标点 —— 改 `<strong>X</strong>Y`

---

## 口播稿 风格

### 文件命名

- `notes/01.txt`..`notes/NN.txt`，**严格一页一文件**，N == slides.md 页数
- 删页/加页 要相应 `mv` 改 notes 文件名（否则编号错位）
- synth-all.py 按 `notes/*.txt` 字母序读取

### 文风

- **口语化**，不文绉绉
  - 删「所谓 X」/「之所以...就是」/「请注意」/「请记住」/「请特别注意」
  - 用「就是说」/「也就是」/「这里要划一下重点」/「记住一件事」
- 长句拆短，多用「你看」「先说一下」「最后总结一下」
- 自问自答：「为什么呢？」「怎么对应？」「9 地是哪 9 地？」
- 数字加「个」/「条」/「品」量词
- 加号 / 等号 全部用中文
- 数字 + 道品：「三十七道品」用中文，不用「37 道品」

### 经典引用

- 在口播里念出来：「《俱舍论》卷 二十三 说……」（卷数也念中文）
- 长引文不要照搬，改写成口语解释
- 同一概念 俱舍 vs 唯识 不同的，要标出来：「按俱舍 X；按唯识 Y」

### 注音说明

- **不要**在口播稿里加「行 念 xíng」之类的注音段——TTS 念到「加行」时还是会错
- **方法**：用同音字替换让 TTS 自动读对（见下节）；字幕 / PPT 显示原字

### 段长建议

| 类型 | 字数 | 时长（约 4.5 字/秒）|
|---|---|---|
| section divider 章节扉页 | 20-50 汉字 | 5-10 秒 |
| 中等内容页 | 150-300 汉字 | 30-65 秒 |
| 复杂论断页（核心论点） | 500-600 汉字 | 110-130 秒 |
| 总时长目标 | 4500-6000 汉字 | 17-22 分钟 |

---

## TTS 合成约定

### 引擎 / 音色：以 env 为准

模型、音色、API key 都从 env 读，**不写进仓库，也不写进本文件**：

| 变量 | 含义 | 放在哪里 |
|---|---|---|
| `BAILIAN_TTS_MODEL` | 合成模型（如 Qwen-Audio-TTS 系列） | 本机 `~/.env`；云端会话的环境变量 |
| `BAILIAN_TTS_VOICE` | 「愚千一」克隆音色的 voice id | 同上 |
| `DASHSCOPE_API_KEY` | 百炼 API key，**绝不入仓** | 本机 `~/.env`；云端由网络代理自动注入，可不设 |

- 音色重新复刻、模型升级时，**只改 env**，脚本和文档都不用动。voice id 的前缀就是它对应的模型名，两者必须配套（复刻时的 `target_model` 要和合成时的 `model` 一致）。
- `scripts/synth.py` 的读取顺序：先读 `~/.env`，再用进程环境变量覆盖；音色先找 `BAILIAN_TTS_VOICE`，没有时再找旧名 `BAILIAN_QWEN_TTS_VOICE_YUQIANYI`。
- 白板视频（`videos/whiteboard-video/`）用的是同一组变量。
- 旧的 cosyvoice-v2 项目把 voice id 存在 `.bailian_voice_id`；那是旧做法，新项目不要再用。

### 接口

- Qwen-Audio-TTS（`qwen-audio-3.0-tts-*`）和 CosyVoice 非实时合成，走 `POST https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer`，请求体 `{"model", "input": {"text", "voice", "format": "wav", "sample_rate": 24000}}`，返回 `output.audio.url`，再下载 WAV。
- 旧的 multimodal-generation 接口（`/api/v1/services/aigc/multimodal-generation/generation`）对这个模型会报 `InvalidParameter: url error`。换模型时先用一句话试一次接口。
- 单次请求不超过 `MAX_CHARS = 280` 字，按行切块，块间留 0.35 秒静音；并发 `MAX_PARALLEL = 4`，重试 `MAX_RETRIES = 3`。
- 幂等：`audio/NN.wav` 已存在就跳过。要重合成某一段，删掉对应 wav 再跑 `python3 scripts/synth.py 04 07`。

### 合成后用 ASR 核对读音

配音合成完，用 `qwen3-asr-flash`（同一个百炼账号）把每段转写成文字，和口播稿逐句对照，专门看经号、多音字、生僻字。识别结果里的同音字（如「两谛」→「两地」）不算错；真读错的，加替换规则后只重合成那几段。

### 多音字读音修复

**核心技巧**：在合成脚本（图文项目是 `scripts/synth.py`，slidev 项目是 `synth-all.py`）里加 `fix_pronunciation()`，对 TTS 发送的文本做同音字替换。`notes/` 源文件保持原字，字幕和图卡 / PPT 显示原字。

已经用过的替换（新项目从上一期的 `PRONUNCIATION_FIXES` 复制，再按需要加）：

| 原词 | 送给 TTS | 原因 |
|---|---|---|
| 空 | 崆 | 一律读 kōng |
| 俱舍 | 俱社 | shè |
| 般若 | 波惹 | bō rě |
| 〇（经号里） | 零 | 「第三〇五经」会读成「第三五经」 |
| 第八一〇经 | 第八百一十经 | 「八一〇」会读成「八幺零」 |
| 集著 / 染著 | 集灼 / 染灼 | 著读 zhuó |
| 胜鬘 / 拘絺罗 / 毗舍佉 / 猗觉 / 如来藏 | 胜蛮 / 拘痴罗 / 毗舍区 / 依觉 / 如来葬 | 生僻字、多音字 |

```python
PRONUNCIATION_FIXES = [
    ("加行", "加形"),         # xíng — preliminary practice
    ("行舍", "形舍"),         # xíng — equanimity
    ("十六行相", "十六形相"),  # xíng — 16 aspects
    ("行相", "形相"),
    ("行蕴", "形蕴"),
    ("梵行", "梵形"),
    # 加新词遵循: 原词 → 同音字 / 用其他能 TTS 正确发音的字替换
]

def fix_pronunciation(text: str) -> str:
    for orig, repl in PRONUNCIATION_FIXES:
        text = text.replace(orig, repl)
    return text
```

合成时 `synth.call(fix_pronunciation(text))`。

### 增量重 synth

合成脚本都是 idempotent 的——已存在的音频跳过（图文项目 `audio/NN.wav`，slidev 项目 `audio/NN.mp3`）。所以**只删要重 synth 的那几段，重跑脚本即可**。

---

## 视频合成约定

### 工具链

- **ffmpeg**：本机（macOS）用 `~/miniforge3/bin/ffmpeg`（含 libass）— brew 版没 libass；云端 Linux 用系统的 `/usr/bin/ffmpeg`（含 libass）。图文项目的 `build_video.py` 会先找 miniforge3，找不到再用 PATH 里的 ffmpeg。
- 图文项目的脚本只依赖 `requests`，任何 python3 都能跑；slidev 旧脚本要 dashscope SDK（`/usr/bin/python3`）。
- 云端没有宋体、黑体：图卡用 `cards.html` 里的 `PreviewSerif`（Noto Serif SC）回退，字幕由 fontconfig 回退到文泉驿正黑，字形和 Mac 上略有不同。要和以前完全一致，就在 Mac 上重跑 `render.sh` / `build_video.py`。

### 图文项目 build_video.py

- 张数按 `notes/*.txt` 自动计算，`out/card-N.png` 与 `notes/NN.txt` 一一对应，不用改脚本里的数字。
- `python3 scripts/build_video.py`：逐段合成 → 拼接无字幕版 → 生成 srt/ass → 烧硬字幕版。
- `python3 scripts/build_video.py --subs-only`：只改了字幕样式时用，沿用 `segments/` 和无字幕版，只重做字幕和硬字幕版。
- 繁体字幕：`opencc` 的 `s2t`（与 02、03 期一致，用爲、衆、裏），生成 `video/<slug>.zh-TW.srt`。

### slidev 项目 build-video.py 关键变量

```python
N_SLIDES = 28               # 必须等于 notes / preview 文件数
TAIL_SILENCE = 0.4          # 每段音频末尾加 0.4 秒静音（自然换页）
FRAMERATE = 30
OUT = "<slug>.mp4"
```

页数变化时，**同步改 3 个脚本**：build-video.py（`range(1, N+1)`）、build-hard-subbed-video.py（`N_SLIDES`）、build-subbed-video.py（`N_SLIDES`）

### 字幕硬烧 preset

- **`preset = "fast"`**（不是 `medium`）—— 21 分钟视频用 fast 烧约 25-30 分钟；medium 要 50 分钟
- CRF 20 不变，质量损失可忽略
- 字幕字体 **`Heiti SC`**（不是 `PingFang SC`）—— PingFang 在 macOS 私有字体路径，fontconfig 找不到

---

## 字幕约定（ASS）

### 样式（图文项目，当前）

```python
# Style: Default,Heiti SC,34,&H00182430,&H00182430,&H30E5F4FB,&H30E5F4FB,0,0,0,0,100,100,0,0,3,7,0,2,60,60,14,1
"Fontname": "Heiti SC",          # macOS 公开字体路径；云端回退到文泉驿正黑
"Fontsize": 34,
"PrimaryColour": "&H00182430",   # 深棕褐色
"BackColour": "&H30E5F4FB",      # 米白色背景框
"BorderStyle": 3, "Outline": 7,  # 不透明底框
"Alignment": 2,                  # 底部居中
"MarginV": 14,                   # 贴近底边，不挡图卡正文
MAX_LINE = 26                    # 每行最多 26 字，字幕框约 900px，避开左下角页脚和右下角署名
```

图卡的正文、引文都在画面 950px 以上，底边一条留给页脚和署名。字幕放在底边中间，宽度控制在页脚和署名之间。

slidev 项目（旧）用的是 `Fontsize 38`、`MarginV 70`、`Outline 8`：PPT 页面底部留白多，不会挡内容；图卡底部放了出处小字，这个位置会挡住，所以图文项目改成上面的样式。

### 字幕生成原则

- **句号 / 问号 / 感叹号** 一定换行
- **逗号 / 分号** 在当前段 ≥12 字符时换行
- 没有标点的长句，满 `MAX_LINE` 字强制换行
- 单段最短 0.6 秒（`MIN_DURATION`）
- 时长按 `(累计字符数 / 总字符数) × 段 audio 时长` 比例分配

---

## 校验规范

### 主依据经典

| 经典 | 用于 | 立场 |
|---|---|---|
| **《大乘百法明门论》** | 心所体系基础 | 唯识 / 百法（系列基石）|
| **《俱舍论》** | 声闻乘修证、见道、修道、烦恼数 | 说一切有部 |
| **《成唯识论》** | 唯识 八识 / 心所 / 二障 / 转依 | 唯识 / 法相宗 |
| **《八识规矩颂》** | 八识 / 转依 / 业 | 玄奘造，法相宗 |
| **《杂阿含经》** | 阿罗汉、四谛、声闻乘 | 早期佛教 |
| **《大智度论》** | 五根五力 等核心论断 | 龙树 大乘 |
| **《显扬圣教论》** | 唯识 进阶 | 弥勒 / 无著 |

### 立场要明确（重要！）

**不同立场混用是大忌**——一定要在 P2 / P3 标清楚本讲立场：

- 「**唯识 / 法相宗 立场**」：用真见道 / 相见道、烦恼障 / 所知障、八识转依、染污末那、八识规矩颂
- 「**俱舍 / 声闻乘 立场**」：用 16 心见道（前 15 心 + 第 16 心修道）、88 见所断、3 学（戒定慧）、不立第七 / 第八识
- 「**百法心所工具**」：跨立场通用——心所体系本身不偏向某宗

如果讲声闻乘，**就不要混入大乘 / 唯识 独有概念**（真见道、所知障、第七识转依等）；如要提一句作收尾「大乘观点 佛果才究竟」，就清楚标注「本讲不展开」。

### 校验流程

1. 写大纲时列出 **校验依据点**（10 条左右）每条带具体经典 + 卷数
2. 写 slides.md 后，**用户必看 + 用户 review**
3. 写口播稿时把校验依据 **内嵌**（不另开校验段）
4. 用户审听，提出修正后**完整重做受影响段**（不只补字眼）

### 常见校验陷阱

- **真见道 / 相见道** 是菩萨道（《成唯识论》卷 9 通达位），**不是声闻见道**
- **所知障 / 法执** 是大乘独有，**俱舍体系不立**
- **第七识 / 第八识** 只在唯识 八识论中存在，**声闻只立 6 识**
- **「无学」** 指三无漏学圆满（戒定慧），**不是「没有有漏法可学」**
- **「念 / 刹那」** 狭义：1 念 ≈ 1 刹那；广义《仁王经》：90 刹那 = 1 念
- **修惑 81 品**：9 地 × 9 品；俱舍唯识共许
- **见惑 88（俱舍）vs 112（唯识）**：俱舍只算我执起；唯识加法执部分

---

## 发布文案 约定

### 两份文件

**`PUBLISH.md`** —— 给人看的，简体 + 繁体两版，每版包含：
1. 3 个标题候选
2. 简短摘要（100 字，视频号 / 朋友圈用）
3. 完整描述（公众号 / B 站正文）：核心论断 + 图表 + 反常识校验点 + 经典依据 + 系列串接表 + 下一讲预告 / 系列结束语

**`PUBLISH-AI.md`** —— 给算法看的，简繁两版 + 自检表：
1. 主描述（300-500 字 · 关键词高密度）
2. 30+ 个 hashtag（覆盖宽到窄）
3. 章节时间戳（让 YouTube 算法识别为深度内容）
4. AI 推荐底层信号自检（主题词重复、经典名、人物、系列标识、受众明示、长尾词、章节戳、立场标识 等）

### 简繁互转

用 OpenCC 的 `s2t`（与「佛学图文」02、03 期一致：爲、衆、裏）。云端没有 opencc 命令时：`pip install opencc-python-reimplemented`，`opencc.OpenCC('s2t').convert(text)`。中文常用术语手工微调（如「軟件」/「軟體」）。

---

## git / 提交约定

### gitignore

```
node_modules           # 已全局忽略
videos/**/segments/    # 中间产物可重建
*.wav                  # 录音临时文件
!videos/**/audio/*.wav # 例外：视频配音 WAV 入仓
.env                   # API key、模型、音色 — 绝不入仓
!videos/**/package.json     # 撤销根目录的 package.json 忽略规则
!videos/**/package-lock.json
```

**最终视频 MP4 入仓**：方便分享，单文件 < 100MB（GitHub 限制）

### Commit message 风格

中文，按主题分块。模板：

```
videos: V[N] 第[X]讲 [主题] — [本次主要改动一句话]

[本次改动详细列表（3-5 条）]

[新增 / 修订的校验论断（2-3 条）]

最终成片：[时长] / [大小] / [字幕条数]。

Co-Authored-By: <按当前会话提示的署名行>
```

每次小修订也要 commit + push（保持仓库可追溯）。

---

## 常见坑

### 1. ffmpeg 字幕 tofu（方块）

- **症状**：硬字幕版字幕是 ▢▢▢
- **原因**：libass 找不到 ASS Fontname 指定的字体
- **修复**：用 `Heiti SC`（macOS 公开路径）；不用 `PingFang SC`（私有路径）

### 2. P1 副标题里的多音字 TTS 念错

- **症状**：P2 注音说明放进口播稿，P1 还在前 → 听众先听到错误
- **修复**：P1 副标题 **避开多音字**（"从加行到阿罗汉" → "从凡夫到阿罗汉"）

### 3. build-video.py range bug

- **症状**：视频只到中间某页就结束
- **原因**：复制脚本时 `range(1, N+1)` 没改对应当前 N
- **修复**：每次改页数，**同步改 3 个脚本的 N**

### 4. cosyvoice 卡住不超时

- **症状**：synth-all.py 跑半小时只完成部分段
- **原因**：dashscope 单个请求挂住没超时
- **修复**：kill 进程，重跑（idempotent）

### 5. notes / slides 编号错位

- **症状**：删了一页 PPT 但 notes 没改名 → 后面所有页错位
- **修复**：删 PPT 后 **同步 mv notes**：`mv notes/N+1.txt notes/N.txt` ...

### 6. fontconfig 缓存丢字体

- **症状**：之前能用的字体，重启或 `fc-cache` 后找不到
- **修复**：用 fontconfig 一定能找到的字体（Heiti SC / Songti SC）

### 7. 多次 commit 间字幕 / 视频文件变化大

- **症状**：commit diff 显示 SRT / MP4 几乎重写
- **正常**：每次改 audio 长度，所有后续段时间戳都变；MP4 是二进制 binary diff
- **接受这种 diff** ——这是预期的

### 8. CJK 标点附近 markdown 加粗失败

- **症状**：`**X**「Y」` 加粗失效，整个区块变灰
- **修复**：改用 `<strong>X</strong>「Y」`

### 9. 换了 TTS 模型，接口报 url error

- **症状**：`InvalidParameter: url error, please check url`
- **原因**：Qwen-Audio-TTS 不走 multimodal-generation 接口
- **修复**：改用 `/api/v1/services/audio/tts/SpeechSynthesizer`（见 TTS 一节）

### 10. 经号读错

- **症状**：「第三〇五经」读成「第三五经」，「第八一〇经」读成「八幺零」
- **修复**：`〇` → `零`；个别经号写成「第八百一十经」送给 TTS。合成后用 ASR 核对

### 11. 字幕挡住图卡

- **症状**：硬字幕盖住图卡底部的出处小字
- **修复**：`MarginV 14`、`MAX_LINE 26`，改完用 `build_video.py --subs-only` 重做

### 12. 视频文件超过对话发送上限

- **症状**：硬字幕版 70MB+，对话里发不出去（上限 30MB）
- **修复**：给用户完整路径和 GitHub 链接；需要预览就另压一份 720p 放 scratchpad，不入仓

---

## 速查清单（新视频启动 checklist）

### 「佛学图文」项目

- [ ] 复制上一期 `cards.html`、`render.sh`、`scripts/synth.py`、`scripts/build_video.py`，改 `SLUG`
- [ ] 画图卡 → `render.sh` → 用户 review
- [ ] 引文用 CBETA 逐字核对，记进 `sources.md`
- [ ] 写 `_posts` 文章，图卡转 JPG 放 `images/`，跑 `python3 scripts/check_posts.py`
- [ ] 写 `notes/NN.txt`，拼 `script.md` → 用户 review
- [ ] 确认 env 里有 `BAILIAN_TTS_MODEL`、`BAILIAN_TTS_VOICE`（不要把值写进仓库）
- [ ] `python3 scripts/synth.py` → ASR 核对读音 → 修替换规则，重合成受影响的段
- [ ] `python3 scripts/build_video.py` → 抽帧看字幕位置和字体
- [ ] 繁体字幕（`s2t`）、`PUBLISH.md`（章节时间戳按实际段长核对）
- [ ] commit + push；给用户的路径一律写从仓库根目录起的完整路径

### slidev 项目

- [ ] 决定主题，写 outline.md
- [ ] 用户 review outline
- [ ] 复制 slidev 项目（package.json / style.css / scripts）；音色以 env 为准
- [ ] `npm install`
- [ ] 改 scripts/build-video.py range + N_SLIDES (3 个脚本)
- [ ] 改 scripts 文件名 prefix（旧项目 slug → 新 slug）
- [ ] 写 slides.md
- [ ] export PNG → 用户 review
- [ ] 写 notes/*.txt（口语化 + 经典依据内嵌）
- [ ] 加同音字到 fix_pronunciation()（如有新多音字）
- [ ] synth-all.py 跑音频
- [ ] build-video.py → build-hard-subbed-video.py
- [ ] 抽帧验证字幕字体
- [ ] 写 PUBLISH.md 简繁 + PUBLISH-AI.md
- [ ] commit + push
- [ ] 用户校验 → 增量修订（删 audio / segments，重跑）→ 重 build

---

## 系列示例

「佛学图文」系列：

| # | 目录 | 主题 | 时长 / 张数 |
|---|---|---|---|
| 01 | buddhism-overview-infographic | 佛教全景图 | 竖版 8 张 |
| 02 | buddhism-four-systems-infographic | 佛教四大思想体系 | 16:14 / 10 |
| 03 | four-noble-truths-infographic | 四圣谛、十二因缘、八正道、三十七道品 | 17:18 / 10 |

slidev 系列已完成 5 讲，每讲约 15-25 分钟 / 28-37 页：

| # | slug | 主题 | 时长 / 页数 |
|---|---|---|---|
| V1 | baifa | 每一法的基本含义 | 25:40 / 35 |
| V2 | baifa-relations | 心王与心所的相应关系 | 16:55 / 37 |
| V3 | baifa-sanke | 与五蕴 / 十二处 / 十八界 | 15:31 / 33 |
| V4 | baifa-37daopin | 与三十七道品 | 19:01 / 32 |
| V5 | baifa-jiandao | 与见道、证果成阿罗汉 | 21:19 / 28 |

每讲结构 = 引入 (3) + 主体 (N) + 综合 (2) + 收尾 (2) 页。

---

—— 整理：愚千一（with Claude）
