# 智能爆炸 · 两套演示实验

两套演示同题创作，展示 AI 辅助研发如何形成反馈，以及可能出现的加速情景。

| Agent | 成品 | 实现 |
| --- | --- | --- |
| Codex | [单文件互动演示](codex/演示文稿/智能爆炸%20·%20互动演示.html) · [PowerPoint](codex/演示文稿/智能爆炸.pptx) | 互动网页把图片、样式、脚本与讲稿嵌入 HTML。PowerPoint 是独立的 13 页版本，带讲稿与原生换页效果。 |
| AGY | [EVENT HORIZON 网页](agy/index.html) | 12 页原生网页演示，含互动 SVG、Canvas、键盘导航和声音。需和同目录的 CSS、JS 一起下载。字体使用 Google Fonts，离线时会回退到系统字体。 |

[Codex 网页缩略图](previews/codex-web.jpg) · [Codex 手机缩略图](previews/codex-web-mobile.jpg) · [Codex PowerPoint 缩略图](previews/codex-powerpoint.jpg)

Codex 的网页与 PPTX 生成源码和八张图片位于 [codex/.ai-deck-build/](codex/.ai-deck-build/)。在原目录结构下运行 `python codex/.ai-deck-build/package_web.py` 可以用随附 PPTX 重打包网页。PPTX 的构建入口 `deck.mjs` 依赖 Codex 的 `@oai/artifact-tool` 运行环境，`package_deck.py` 为生成的演示添加换页效果。
