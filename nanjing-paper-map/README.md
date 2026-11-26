# NANJING

55 秒竖屏纸地图动画。Three.js 负责地图折线上的铰链、地标折脚、镜头、照明和地标阴影。片名、地标字幕和烟花由画布逐帧合成。FFmpeg 将顺序帧与原创配乐、纸张声和烟花声合成 H.264/AAC MP4。最终视频为 1080 × 1920、24 fps。

[成片 MP4](outputs/Nanjing.mp4) · [最初的提示词](PROMPT.md)

## 关键帧预览

![南京折叠纸地图动画 6 个关键节点总览](previews/keyframes-overview.jpg)

分镜头单帧：[01 地图展开](previews/01-unfold-title.jpg) · [02 中华门](previews/02-zhonghua-gate.jpg) · [03 夫子庙·秦淮河](previews/03-fuzimiao-qinhuai.jpg) · [04 中山陵](previews/04-sun-yatsen-mausoleum.jpg) · [05 紫峰大厦](previews/05-zifeng-night.jpg) · [06 烟花终幕](previews/06-fireworks-finale.jpg)

## 渲染

安装 Node.js、Chromium 和 FFmpeg。环境需有 Noto Serif CJK SC 字体，用于中文字幕。素材和音轨已随项目提供。

```sh
npm ci
npm run render -- Nanjing.mp4
```

默认按 1080 × 1920 渲染。软件渲染机器可指定工作分辨率，FFmpeg 会将输出合成为 1080 × 1920。用 `CHROMIUM` 指定浏览器路径。

```sh
FILM_WIDTH=720 FILM_FAST=1 npm run render -- Nanjing.mp4
npm run stills -- previews
```

运行本地静态 HTTP 服务后，可用 `index.html?preview&w=540&h=960` 预览动画。

## 时间轴

| 时间 | 镜头 |
| --- | --- |
| 00–07 | 木桌上的同张九折地图逐次展开，片名浮现 |
| 07–15 | 从新街口下潜，抵达中华门，沿城墙转向 |
| 15–23 | 沿秦淮河贴近夫子庙，掠过游船和灯笼 |
| 23–33 | 沿路向东，紫金山山脊与中山陵依次立起，镜头环绕石阶 |
| 33–41 | 转向玄武湖，低角度掠过岛屿和湖面 |
| 41–47 | 紫峰大厦立起，天色转暗，街区亮灯 |
| 47–55 | 镜头拉升，整张地图复现，烟花接连绽放 |

## 地理与素材

站点经纬度见 `landmarks.json`。道路和水系来自 OpenStreetMap 的 Shortbread 矢量瓦片。路线按图上道路网络连接站点，景点入口附近有短接驳。地图采用 Web Mercator 投影。地标纸片为按实景设计的生成图像，尺寸按镜头构图调整。紫金山等高线由 Terrarium 高程瓦片生成。

- [OpenStreetMap 地图数据及许可](https://www.openstreetmap.org/copyright)
- [OpenStreetMap Shortbread 矢量瓦片](https://vector.openstreetmap.org/)
- [AWS Terrain Tiles 高程数据](https://registry.opendata.aws/terrain-tiles/)
- [夫子庙位置](https://en.wikipedia.org/wiki/Nanjing_Fuzimiao)
- [中华门位置](https://en.wikipedia.org/wiki/Gate_of_China,_Nanjing)
- [中山陵位置](https://en.wikipedia.org/wiki/Sun_Yat-sen_Mausoleum)
- [玄武湖位置](https://en.wikipedia.org/wiki/Xuanwu_Lake)
- [紫峰大厦位置](https://en.wikipedia.org/wiki/Zifeng_Tower)
- [新街口位置](https://mapcarta.com/N9164163248)

如需重建底图、裁切或配乐，安装 Python 的 NumPy、SciPy、Pillow 和 Matplotlib。运行 `python download-map.py`、`node geo.mjs`、`python prepare-map.py`、`python prepare-paper.py` 或 `python score.py`。
