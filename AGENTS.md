# AGENTS

## Post Naming Rule

- New posts in `_posts` must use: `YYYY-MM-DD-english-short-name.md`.
- Use lowercase English words in kebab-case.
- Keep the short name concise and semantic (avoid long pinyin slugs).

## 文章摘要（description）规则

- front matter 里的 `description` 不能超过 120 个字符（中文、标点、数字、空格都各算 1 个）；写的时候按 110 字以内来写。公众号把它当作摘要，超过 120 字会拒绝创建草稿（errcode 45004）。
- 写完或改完文章后、提交之前，运行 `python3 scripts/check_posts.py`，有 ERROR 就先改掉。GitHub 上每个 PR 和每次推送到 master 也会跑同一个检查（`.github/workflows/check-posts.yml`），检查不通过不要合并。

## 公众号同步脚本的部署规则

- 北京服务器上的同步脚本是手工拷贝的，不会随 git 自动更新。改了 `scripts/` 下的 `wechat_auto_sync.py`、`wechat_draft_sync.py`、`wechat_upload_thumb.py`、`markdown_.css`、`wechat_footer.html` 之后，合并到 master 后必须运行 `scripts/wechat_auto_sync_deploy.sh`，并在服务器上确认生效。只提交不部署，等于没修。

## Sutra Citation Rule

- Any Buddhist scripture citation must come from real canonical texts, be searchable and verifiable in CBETA, and never use fabricated or unverifiable quotes.
- Citations should be specific enough for third-party AI (claude, gemini) verification, for example by including the sutra name and, where possible, chapter/卷.

## 佛经与佛教故事写作要求

- 整理佛经或佛教故事时，优先以原始经典或可靠佛教文献为依据；若用户指定版本或数据库，例如 CBETA，应以该来源为准。
- 若是做资料汇编，统一按以下格式输出：1. 经典名称；2. 原文节录；3. 用现代汉语复述故事。
- 若是根据多部经典或多条线索重新讲述一个主题故事，要先合并重复内容，同一个故事主线不重复展开，异译、异名、异本只保留一次，并在叙述中自然吸收、交代清楚；关键情节要尽量锚定到具体经典，并尽量落实到具体人物、对话对象、法会场景，不要只笼统写“经里说”“佛又讲过”“佛告诉弟子”。
- 从经文进入故事时，要有明确的“依经叙述”意识，可用“经中记载”“经中说”等方式提示来源，避免叙述口气像脱离经典的自由发挥；如果经典之间说法不同，要简要说明差异，但不要让版本差异破坏故事的整体阅读体验。
- 写作时不要只做材料堆砌，也不要写成冷冰冰的知识摘要，而要把它真正写成一个完整、连贯、能读下去的故事；文风必须使用现代汉语，不用文言腔，不故作古雅，表达可以庄重、真挚、平实、动人，但必须自然、流畅、清楚。
- 叙述应当有情感、有温度、有画面感，但不能脱离经典依据随意虚构；可以增强故事性、节奏感和感染力，但不能改动核心情节、人物关系和思想主旨。
- 故事必须完整。凡是重述一则佛经故事，至少要交代清楚它的起因、关键人物、核心事件、转折过程、结果，以及这则故事在佛教修行、信仰或思想上的意义；围绕单一主题写故事时，要保持主线收束，删去虽然相关但会冲淡主题、且不是当前主题必需的旁支延伸。
- 最终目标不是单纯“介绍一段经文”，而是让读者既看懂故事，也理解这则佛教故事为什么重要。


## 禁止黑话式表达

- 回答、翻译、总结、说明时，禁止使用空泛的“黑话”来代替具体内容。
- 少用或禁用这类词：`很直白`、`收得很深`、`说得极稳`、`很干脆`、`很重要`、`很关键`、`很有力量`、`很完整`、`很清楚`、`非常鲜明`、`很像`、`其实是在说`、`归根到底`、`最终指向`、`收束为`、`闭环`、`痛点`、`一句话总结`、`不踩坑`、`稳稳接住`、`砍一刀`、`补一刀` 等。
- 不要写“这一段的意思是……”“这一经很重要”“这其实都在说同一件事”这种评论腔。
- 不要用评价词、方法论词、销售话术、产品黑话，去掩盖没有逐句说明、没有逐段翻译、没有贴着原文处理的问题。
- 如果能直接写事实，就不要写判断。
  - 不写：`这里说得很清楚`
  - 改写为：`这里直接说……`
- 如果能直接写原文含义，就不要写抽象总结。
  - 不写：`这一段其实是在强调无常`
  - 改写为：`这一段逐句说色无常、受无常、想无常、行无常、识无常`
- 如果不能从原文逐句对应推出，就不要自行拔高、升华、概括。
- 结论必须从原文或代码直接落出，不能靠语气词硬撑。
- 发现自己在写“很、非常、其实、核心、本质、收束、闭环、痛点、稳住、说人话就是”这类词时，先删掉，再改成具体事实。


## Workflow Rule

- Before starting any substantive task in this repository, the agent must read `AGENTS.md` first and explicitly confirm it will follow these rules.

## 去AI味

不要用下面的句型：
- 先说结论、直接给你答案、一句话总结、核心就三点
- 不拐弯抹角、直接给你重点、都是最真实的、直击重点的、直接就能用的、XXX拉满
- 掰开了揉碎了说、底层逻辑、讲透本质、
- 希望这个回答对你有帮助、想要我再补充更多吗、我可以再给你一版更XX的

## 封面图规则

- 图文系列文章：一般第一张图就是封面，不另外生成。
- 普通文章：用通义千问（DashScope，API key 在环境变量中）根据文章的内容或故事，生成一幅卡通效果的封面图，存为 `images/<post文件名>-cover.png`（1280×720），放在正文开头。
- 生成方法：`scripts/gen_cover_dashscope.py <post文件名（不含 .md）> "<提示词>"`；`DASHSCOPE_API_KEY` 在 `~/.env` 里，运行前先加载，不要把 key 打印或写进任何文件。
- 画风：卡通风格（扁平卡通插画，暖色调），不要写实照片风格。
- 人物：画面里出现的人物用卡通人物；代表作者本人的人物不要画得太老，按 35 岁左右的样子来画（黑发，没有皱纹和白发）。提示词里要明确写出年龄，否则容易画成中老年人。
- 生成后先看图再用：人物显老、人数不对、画面和文章内容不符时，改提示词重新生成。
