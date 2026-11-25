# 《一场对话，四年》源码

`render.py` 包含分镜、逐帧绘图、原创音乐合成和 MP4 导出。它是生成已交付成片时使用的脚本。

## 在 Windows 上复现

需要 Python 3、Pillow、NumPy，以及可在命令行中调用的 FFmpeg（支持 libx264 和 AAC）。脚本使用 `C:/Windows/Fonts` 中的 Arial Narrow、微软雅黑和 Consolas。

在源码目录中打开 PowerShell，运行以下命令。

```powershell
python -m pip install Pillow numpy
python render.py ".\一场对话，四年.mp4"
```

导出时，脚本在源码目录生成 `score.wav`，再把音轨和画面合成为 52.8 秒的 MP4。用 `python render.py preview` 可以先生成一张分镜预览图 `contact.jpg`。

## 从哪里看起

- `SCENES` 记录画面文字和每个镜头的起始拍。
- `visual()` 和 `render_frame()` 绘制图形、文字和镜头动效。
- `score()` 合成鼓、低音和旋律，并在切镜附近加入过渡音和重音。
