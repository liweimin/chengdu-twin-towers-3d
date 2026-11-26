# 纸船驶向阳光

12 秒绘本动画，1280 × 720，24 帧/秒。画面和音轨均由代码生成，无需下载任何素材。

## 重新生成

使用带有 .NET Framework 4.x 的 Windows，在 PowerShell 中执行。FFmpeg 需包含 libx264 并可通过 PATH 找到。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

成片输出到脚本同一目录下的 `paper-boat.mp4`。编译产物和中间音轨存放在 `.build`。

## 源文件

- `src/Illustration.cs` 绘制林地、溪岸、水面、石头和植物。
- `src/Characters.cs` 绘制孩子、纸船和小鸭，控制角色姿势和表情。
- `src/Film.cs` 编排分镜、轨迹、水纹、光斑和纸张纹理。
- `src/Sound.cs` 合成原创旋律、分解和弦、溪流、鸟鸣和鸭叫。
- `build.ps1` 编译 C#，并将画面和立体声音轨编码为 H.264/AAC MP4。

单帧预览可在构建后直接调用渲染器。

```powershell
& .\.build\film.exe preview 9.58 .\.build\push.png
```
