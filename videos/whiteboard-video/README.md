# 白板讲佛法：愚千一的白板讲解视频

这里只放每期的内容（`episodes/<日期> <标题>/`：scenes.js、场景图、旁白稿、字幕、封面、发布文案、成片）和一份覆盖配置 `config.json`（品牌名、slogan、系列标签、多音字替换）。

画面、配音、渲染的工具本体在 [whiteboard-video-skills](https://github.com/yuqianyi1001/whiteboard-video-skills) 仓库的 `skills/whiteboard-video`，用法、DSL 和出片规范都看那边的 README.md / SKILL.md。

## 用法

```bash
# 一次性：与本仓库并排克隆工具仓库并装依赖
git clone https://github.com/yuqianyi1001/whiteboard-video-skills ../whiteboard-video-skills   # 在本仓库根目录的上一级
(cd ../whiteboard-video-skills/skills/whiteboard-video && npm install)

# 在本目录下，命令与 wb 相同
./wb list
./wb build 人生是苦
./wb tts 人生是苦 03-xxx
```

- 工具不在并排位置时设 `WB_HOME=<whiteboard-video-skills>/skills/whiteboard-video`。
- `./wb` 把本目录 `config.json` 作为 `WB_CONFIG` 传给工具：只写与工具默认值不同的字段，其余（语速 1.1、响度 -16 LUFS、字幕、笔速等）沿用工具仓库的 `config.json`。
- 配音用千问 Qwen-TTS 声音复刻：环境变量 `BAILIAN_TTS_MODEL`、`BAILIAN_TTS_VOICE`，API key `DASHSCOPE_API_KEY`（云端环境由代理注入时可不设）。
- 中间产物与成片在本目录 `build/`（不入库），成片复制到期目录 `成片.mp4`。
