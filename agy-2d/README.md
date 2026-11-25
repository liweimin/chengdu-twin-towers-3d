# 《成都金融城双塔黄昏》— 纯二维程序化绘画作品集

本项目完全采用**纯二维程序化绘画（Pure 2D Procedural Painting）**创作《成都金融城双塔黄昏》，完整保留了四个演进版本的源码与高清成图：

- **无三维场景 / 无 3D 渲染引擎**
- **无 AI 图像生成模型 / 无现成照片素材**

---

## 版本四（v4，最新）：100% 纯二维物理笔触逐笔画成版

整幅画面（天空、晚霞云层、远景天际线、弧形天府双子塔与冰花 LED、右侧近景写字楼、交子大道沥青、多笔触柔和黄昏车流、路灯与分形行道树）**全部由 100,000+ 笔物理 2D 多毛笔刷逐笔叠加完成**，彻底告别生硬的贴图拉伸与多边形矢量车体：
- **高清成图**：`output/chengdu_twin_towers_dusk_v4.png`（`2400 × 1800`，4:3 广角画幅）
- **源码目录**：`src_v4/`
  - `src_v4/render_v4.py` — v4 主程序入口
  - `src_v4/brush_engine.py` — 纯 2D 物理多毛笔刷引擎（湿画法多层融合、直线/曲线多毛笔触、旋转笔触点染、线性 HDR 光斑与电影级光学后期）
  - `src_v4/sky_brush.py` — 逐笔铺陈的蓝调黄昏天空底色、斜向卷云与湿画法火烧云层
  - `src_v4/architecture_brush.py` — 逐窗逐肋手绘的远景楼群、天府双塔弧形圆柱笔触与冰花/LED 光栅笔触、右侧近景写字楼逐窗玻璃云影笔触与陶土石材肋
  - `src_v4/street_trees_brush.py` — 透视笔触沥青路面、每辆 40+ 笔柔和光影笔触绘成的黄昏车流、分形树干细枝与约十万笔微叶片笔触

### 复现 v4 高清成品
```powershell
.venv\Scripts\python.exe src_v4\render_v4.py --width 2400 --height 1800 --seed 2026 --out output\chengdu_twin_towers_dusk_v4.png
```

---

## 已完整保留的历史版本
- **v3（混合写实高频纹理 + 9万笔触树木版）**：`output/chengdu_twin_towers_dusk_v3.png`（`src_v3/render_v3.py`）
- **v2（交子大道实拍透视初版）**：`output/chengdu_twin_towers_dusk_v2.png`（`src_v2/render_v2.py`）
- **v1（交子公园湖畔全景倒影版）**：`output/chengdu_twin_towers_dusk.png`（`src/render.py`）

## 环境依赖安装
```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```
