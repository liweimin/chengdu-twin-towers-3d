# 引力余晖 · Afterlight

《引力余晖》是一件用 p5.js 绘制的全屏数字作品。星尘在倾斜的螺旋引力场中流动，逐渐消散的光轨勾勒出星云的形状。

直接用浏览器打开 `index.html` 即可运行。p5.js 与字体已放在 `vendor/`，无需联网或安装依赖。

## 交互

- 移动鼠标或拖动手指，卷动指针附近的星尘。
- 点击或轻触画布，释放星爆和向外扩散的冲击波。
- 点击右下角的光谱色点，切换琥珀蓝、极光绿或玫瑰紫。
- 点击暂停按钮或按空格，暂停或继续。开启了系统减少动态效果选项时，作品以静止画面开始。
- 点击全屏按钮或按 `F` 进入全屏。按 `Esc` 返回。

星云、恒星、光轨和星爆均由 `sketch.js` 实时绘制或程序化生成。

第三方许可随 `vendor/` 中对应文件提供。项目内的 p5.js 来自 jsDelivr 的 2.3.3 发布包。[p5.js 源码与发布说明](https://github.com/processing/p5.js/releases/tag/v2.3.3) · [Instrument Serif 源码](https://github.com/google/fonts/tree/main/ofl/instrumentserif)
