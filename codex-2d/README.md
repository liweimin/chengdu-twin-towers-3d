# 成都金融城双塔黄昏

一幅纯二维程序化城市风景。构图采用高于街面的视点。双塔的鱼腹形轮廓、玻璃幕墙和冰裂纹铝合金外网来自公开建筑说明。交子之环、配楼、街道、交通与天色结合这一构图进行了艺术重构。

## 复现

在 Windows 上运行。脚本通过 Windows PowerShell 5.1 调用系统自带的 .NET Framework 与 System.Drawing。可从 PowerShell 7 启动，无需下载依赖或素材。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\render.ps1 -Preview Chengdu-Dusk-preview.png
```

默认输出 `Chengdu-Dusk.png`，尺寸为 **3840 × 2561**，随机种子为 `241125`。`-Output` 可指定其他路径，`-Width` 支持 800 到 4800 像素，`-Seed` 可选用其他整数种子。若省略 `-Preview`，只生成主图。

## 绘画系统

- 天空逐像素计算，用多尺度二维值噪声塑造风切云带，并模拟近地平线的暖色散射。
- 两座塔楼各有一套二维幕墙坐标。鱼腹形轮廓、玻璃分格、楼层光带与不规则冰裂纹外网共享此坐标，使反光与结构贴合塔身。
- 环桥由二维椭圆带、分段金属板、玻璃护栏和桥墩叠绘。街道用收束线布局，再绘制车身、灯光、路面反射、行人和多层点绘树冠。
- 输出阶段加入细颗粒与轻微暗角，增强黄昏的曝光感。所有画面元素均由 `ChengduDusk.cs` 生成，无外部图像资产或模型。

建筑特征的文字参考见 [中建西南院项目说明](https://www.archina.com/index.php?a=show&g=works&id=8820&m=index)、[交子公园金融商务区地标介绍](https://www.cdjrc.com/product/146.html) 和 [交子之环建成报道](https://sc.people.com.cn/n2/2021/0721/c379469-34831019.html)。
