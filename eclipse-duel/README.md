# 《蚀影》光剑对决

两支由 Codex 制作的 15 秒动画，均为 1920 × 1080、30 fps、立体声。两版沿用同一套动作、镜头时间线和配乐。

| 版本 | 成片 | 画面 |
| --- | --- | --- |
| 火柴人版 | [下载 MP4](codex/eclipse_sith_vs_jedi.mp4) | 火柴人剪影、双色光剑、日蚀下的悬空平台 |
| 日漫版 | [下载 MP4](codex/eclipse_sith_vs_jedi_anime.mp4) | 重绘人物、赛璐珞阴影、速度线、冲击帧和决胜前的分屏特写 |

## 源码与复现

Pillow 按关键姿势逐帧绘图。NumPy 和 SciPy 合成音乐及音效。FFmpeg 编码视频并合入立体声音轨。

在带有 Python 3、FFmpeg（支持 `libx264` 与 AAC）和 DejaVu 字体的 Linux 环境执行。脚本使用 `/usr/share/fonts/truetype/dejavu/` 下的字体。渲染结果写入项目目录，生成的中间音轨 `sound.wav` 位于 `codex/src/`。

```bash
cd eclipse-duel
python -m pip install pillow numpy scipy
python codex/src/sound.py
python codex/src/duel.py stick-figure-render.mp4
python codex/src/anime_duel.py anime-render.mp4
```
