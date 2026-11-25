# 成都金融城双塔黄昏 · 笔触重绘版

用 C# 从空白二维画布画出航拍构图。拟合阶段读取 ANTARA 刊载的 1200 × 800 航拍参考照，分析每个像素的颜色和邻域亮度。实际绘制阶段读取二维笔触参数，按顺序合成椭圆笔触。没有三维场景或图像生成模型。

[航拍参考照片](https://cdn.antaranews.com/cache/1200x800/2024/06/13/chengdu.jpg) · [照片刊载页](https://en.antaranews.com/news/315918/chengdus-influence-being-felt-across-the-world)

## 离线复现

Windows 自带的 Windows PowerShell 5.1 和 System.Drawing 即可运行。把 `StrokeStudy.cs`、`render.ps1` 和 `chengdu-brushes.bin.gz` 放在同一目录。压缩文件保存的是按顺序记录的笔触坐标、两个半径、方向、透明度和颜料 RGB。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\render.ps1 -Preview Chengdu-Brushes-preview.png
```

默认输出 `Chengdu-Brushes.png`（3840 × 2560）。可以用 `-Width` 改变渲染尺寸。参考照本身为 1200 × 800，较大输出会以更密的像素网格重采样同一批笔触。

## 从参考图重新拟合

将上方链接中的参考图另存为 `reference.jpg`，再运行以下命令。使用单独的 `-Plan` 路径可保留交付的笔触文件。默认随机种子为 `241125`，拟合宽度为 `1200`。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\render.ps1 -Reference .\reference.jpg -Plan .\refit.brushes.gz -Output .\refit.png
```

程序先用宽笔触铺出天空、塔身和地面的色块，再用小笔触沿亮度边缘补绘细节。每笔用覆盖范围内的多个像素共同求解一个颜料颜色。只有降低该区域整体误差的笔触才会写入文件。拟合过程逐轮打印 RGB PSNR，衡量参考尺寸下的像素误差。
