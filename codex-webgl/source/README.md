# 成都金融城双塔黄昏

以交子公园隔湖远眺为构图，描绘夕照渐退、室内灯光渐亮的时刻。双塔的截切椭球形体、双层幕墙和冰裂纹铝网参考中建西南院项目资料。配楼、岸线、云层和亮灯分布经过艺术重构。 [双塔设计资料](https://www.thepaper.cn/newsDetail_forward_12833552) · [交子公园取景资料](https://static.cdsb.com/micropub/Articles/202106/49b733189de5491360713dafdb5cead1.html)

## 复现

需要 Node.js 20 或更新版本，以及支持 WebGL 2 和 `EXT_color_buffer_float` 的桌面版 Chrome、Chromium 或 Edge。解压源文件后，在 `render.mjs` 所在目录运行以下命令。无需安装 npm 包，渲染不读取外部纹理或照片。

```sh
node render.mjs --width 4800 --height 3200 --out Chengdu-Financial-City-at-Dusk.png
```

快速预览可改用 `--width 1500`，高度自动按 3∶2 计算。浏览器未被自动找到时，用 `--chrome` 指定可执行文件路径。默认使用 Chromium 的 SwiftShader 软件渲染。可加 `--hardware` 改用浏览器的默认图形后端。不同浏览器版本和图形后端的抗锯齿或像素舍入可能略有差异。

## 源文件

| 文件 | 内容 |
| --- | --- |
| `render.mjs` | 启动无头浏览器并导出 PNG |
| `renderer.js` | 相机、平面反射、线性浮点缓冲和高光处理 |
| `scene.js` | 双塔、城区、岸线、灯具和程序生成植被 |
| `shaders.js` | 冰裂纹、玻璃与窗灯、暮云、湖面及最终调色 |

随机布局使用固定种子。相机位置和移轴量在 `renderer.js` 的 `camera` 中调整，窗灯、天空和湖面参数在对应的着色器中调整。
