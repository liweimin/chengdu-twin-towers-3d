# 成都金融城双塔黄昏 · 航拍对照版

取景参照 ANTARA 刊载、图文来源为成都市方面的天府国际金融中心航拍。按照片目测绘制两塔轮廓、屋顶灯带、左侧红冠楼和斜顶建筑、右下金色椭圆建筑，以及天际线和道路走向。窗格疏密、车流、绿化和远景由程序补绘。

[参考航拍所在报道](https://en.antaranews.com/news/315918/chengdus-influence-being-felt-across-the-world) · [参考照片](https://cdn.antaranews.com/cache/1200x800/2024/06/13/chengdu.jpg)

## 从源文件复现

在本目录运行。脚本使用 Windows PowerShell 5.1 与系统自带的 System.Drawing。运行无需网络、照片文件或其它素材。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\render.ps1 -Preview Chengdu-Aerial-preview.png
```

默认生成 `Chengdu-Aerial.png`（3840 × 2560）。可用 `-Width`、`-Seed`、`-Output` 更改尺寸、种子和输出路径。默认随机种子为 `241125`。

核心代码在 `ChengduAerial.cs`。塔身与道路的控制点都在二维画面坐标内，玻璃幕墙和其他建筑立面以二维曲线或四边形插值绘制。云纹、远景、植被、窗光与辉光均在同一次渲染中生成。
