# AGENTS

## Post Naming Rule

- New posts in `_posts` must use: `YYYY-MM-DD-english-short-name.md`.
- Use lowercase English words in kebab-case.
- Keep the short name concise and semantic (avoid long pinyin slugs).

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
