import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const dir = path.dirname(fileURLToPath(import.meta.url));
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = {
  black: "#0B0B0D", ink: "#171411", paper: "#F4EDE4", white: "#FFF5EB",
  orange: "#FF7642", rust: "#B63611", muted: "#C4BAB1", gray: "#584E48",
  dim: "#42352D", light: "#D7C8BB", bright: "#FF5C30",
};
const f = "Microsoft YaHei";
const mono = "Bahnschrift";
const none = { fill: "none", width: 0 };

function slide(color = C.black) {
  const s = deck.slides.add();
  s.background.fill = color;
  return s;
}

function text(s, value, x, y, w, h, {
  size = 25, color = C.white, bold = false, font = f, align = "left",
} = {}) {
  const shape = s.shapes.add({
    geometry: "textbox", name: value.slice(0, 44),
    position: { left: x, top: y, width: w, height: h },
    fill: "none", line: none,
  });
  shape.text = value;
  shape.text.style = {
    typeface: font, fontSize: size, color, bold, alignment: align,
    verticalAlignment: "middle", wrap: "none", autoFit: "none", insets: 0,
  };
  return shape;
}

function lines(s, values, x, y, w, size, leading, options = {}) {
  for (const [i, value] of values.entries()) {
    text(s, value, x, y + i * leading, w, leading, { ...options, size });
  }
}

function rect(s, x, y, w, h, fill, name = "色块") {
  return s.shapes.add({
    geometry: "rect", name, fill, line: none,
    position: { left: x, top: y, width: w, height: h },
  });
}

function stroke(s, x1, y1, x2, y2, color, width = 2) {
  const length = Math.hypot(x2 - x1, y2 - y1);
  return s.shapes.add({
    geometry: "rect", name: "图表线", fill: color, line: none,
    position: {
      left: (x1 + x2 - length) / 2, top: (y1 + y2 - width) / 2,
      width: length, height: width,
      rotation: Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI,
    },
  });
}

function dot(s, x, y, d, color) {
  s.shapes.add({
    geometry: "ellipse", name: "数据点", fill: color, line: none,
    position: { left: x - d / 2, top: y - d / 2, width: d, height: d },
  });
}

async function photo(s, name, x, y, w, h, alt) {
  const bytes = await fs.readFile(path.join(dir, name + ".jpg"));
  s.images.add({
    blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
    contentType: "image/jpeg", alt, fit: "cover",
    position: { left: x, top: y, width: w, height: h },
  });
}

function index(s, n, label, light = false) {
  const guide = light ? C.gray : C.muted;
  const accent = light ? C.rust : C.orange;
  text(s, String(n).padStart(2, "0"), 72, 42, 33, 32, { size: 17, color: accent, font: mono });
  text(s, label, 117, 42, 375, 32, { size: 15, color: guide, bold: true });
}

function notes(s, body, sources = []) {
  s.speakerNotes.text = [body, ...sources.map(source => "参考来源　" + source)].join("\n\n");
}

const good = "I. J. Good (1965), Speculations Concerning the First Ultraintelligent Machine. https://doi.org/10.1016/S0065-2458(08)60418-0";
const metr = "METR, Measuring AI Ability to Complete Long Software Tasks. https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/";
const evolve = "Google DeepMind (2025), AlphaEvolve. https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/";
const iea = "IEA (2025), Energy and AI, Executive Summary. https://www.iea.org/reports/energy-and-ai/executive-summary";

// 01 — Cover
{
  const s = slide();
  await photo(s, "cover", 0, 0, 1280, 720, "黑色背景上的橙色引力透镜与弧形光轨");
  rect(s, 0, 0, 1280, 720, {
    type: "gradient", gradientKind: "linear", angleDeg: 0,
    stops: [{ offset: 0, color: "#09090B" }, { offset: 54000, color: "#09090B/33" }, { offset: 100000, color: "#09090B/0" }],
  }, "暗部渐变");
  text(s, "INTELLIGENCE EXPLOSION", 80, 114, 570, 40, { font: mono, size: 22, color: C.orange });
  text(s, "智能爆炸", 72, 244, 685, 153, { size: 125, bold: true });
  text(s, "当 AI 开始加速 AI 研发", 81, 412, 630, 53, { size: 34, color: C.white });
  notes(s, "开场时，停一拍。今天讨论一种未来：AI 变成 AI 研发的一部分，进步的速度因研发本身被加速而改变。");
}

// 02 — The hypothesis
{
  const s = slide(C.paper);
  index(s, 2, "思想起点", true);
  text(s, "1965", 640, 125, 570, 345, { size: 252, font: mono, color: "#DECABB", align: "right" });
  lines(s, ["如果机器也能设计", "更聪明的机器？"], 70, 160, 840, 64, 82, { color: C.ink, bold: true });
  rect(s, 73, 427, 8, 112, C.rust, "引文标记");
  lines(s, ["I. J. Good 的设想：更强的机器能够参与", "设计下一代机器，能力的增益会反馈到研发本身。"], 100, 435, 920, 28, 44, { color: C.ink });
  notes(s, "Good 在 1965 年用“智能爆炸”描述这条反馈路径。他设想的是一种超智能机器；本演示采用更宽的情景，研究团队、工具与模型可以共同构成闭环。", [good]);
}

// 03 — The loop
{
  const s = slide();
  await photo(s, "loop", 540, 88, 740, 575, "橙色纤维闭环，表示研发反馈");
  index(s, 3, "递归自我改进");
  text(s, "研发闭环", 72, 106, 535, 94, { size: 65, bold: true });
  const steps = ["提出改进方案", "并行运行实验", "筛出有效改进", "用更强的 AI 开始下一轮"];
  steps.forEach((label, i) => {
    const y = 233 + i * 79;
    dot(s, 85, y + 23, 12, C.orange);
    if (i < steps.length - 1) rect(s, 84, y + 30, 2, 66, C.dim, "流程连接线");
    text(s, label, 118, y, 495, 48, { size: 30, bold: i === 3, color: i === 3 ? C.orange : C.white });
  });
  text(s, "这一轮的成果，能否缩短下一轮？", 73, 609, 465, 48, { size: 25, color: C.muted });
  notes(s, "改进可以落在工具、算法、数据质量、训练效率或推理效率上。模型、评测器、算力平台和研究团队可以一同形成反馈。闭环加速需要改进可验证、可部署，并能实际影响下一轮研发。", [good]);
}

// 04 — Observed footholds
{
  const s = slide(C.paper);
  index(s, 4, "已经观察到的进展", true);
  text(s, "闭环的局部已经出现", 71, 105, 1140, 82, { size: 55, bold: true, color: C.ink });
  rect(s, 649, 221, 1, 362, C.light, "证据分界线");
  text(s, "1%", 72, 224, 535, 149, { size: 119, font: mono, color: C.rust });
  text(s, "7", 698, 224, 116, 149, { size: 119, font: mono, color: C.ink });
  text(s, "个月", 806, 270, 255, 91, { size: 51, bold: true, color: C.ink });
  text(s, "Gemini 训练时间的降幅", 73, 375, 550, 48, { size: 29, bold: true, color: C.ink });
  text(s, "软件任务时长的历史翻倍周期", 699, 375, 510, 48, { size: 28, bold: true, color: C.ink });
  lines(s, ["据谷歌报告，AlphaEvolve 改进了", "一项计算操作，整体训练时间缩短约 1%。"], 73, 429, 565, 24, 37, { color: C.gray });
  lines(s, ["METR 的 2025 年研究发现，AI 能以 50%", "成功率独立完成的任务时长约每 7 个月翻倍。"], 699, 429, 525, 22, 37, { color: C.gray });
  text(s, "Google DeepMind  /  AlphaEvolve", 73, 564, 560, 34, { font: mono, size: 18, color: C.rust });
  text(s, "METR  /  Time Horizon", 699, 564, 510, 34, { font: mono, size: 18, color: C.rust });
  notes(s, "据谷歌报道，AlphaEvolve 找到更高效的矩阵乘法分解方案，使 Gemini 中的一项关键计算快了 23%，整体训练时间缩短约 1%。METR 的约 7 个月来自对当时约 6 年模型的历史拟合，时长以人类专家完成同一任务所需时间衡量，50% 是任务成功率门槛。相关评测主要覆盖软件任务。", [evolve, metr]);
}

// 05 — Quantitative thought experiment
{
  const s = slide();
  index(s, 5, "思想实验");
  text(s, "同样 90 天，能做几轮？", 71, 100, 1130, 82, { size: 60, bold: true });
  text(s, "首轮耗时 21 天，两组仅有一项差异：后续每轮耗时是否缩短 20%。", 74, 188, 1130, 52, { size: 25, color: C.muted });
  const axisX = 73;
  const unit = 10.55;
  const track = (values, y, tint) => {
    let left = axisX;
    values.forEach((v, i) => {
      const width = v * unit;
      rect(s, left, y, width - 4, 42, tint[i % tint.length], "第 " + (i + 1) + " 轮");
      const label = Number.isInteger(v) ? String(v) : v.toFixed(1);
      text(s, label, left, y, width - 4, 42, { size: 18, color: C.ink, font: mono, align: "center" });
      left += width;
    });
  };
  text(s, "每轮都耗时 21 天", 73, 265, 500, 40, { size: 23 });
  text(s, "每轮耗时比上一轮短 20%", 73, 409, 540, 40, { size: 23 });
  rect(s, axisX, 313, 90 * unit, 42, "#322B28", "90 天总窗口");
  rect(s, axisX, 457, 90 * unit, 42, "#322B28", "90 天总窗口");
  track([21, 21, 21, 21], 313, ["#C8B5A5", "#E5D1BD"]);
  track(Array.from({ length: 8 }, (_, i) => 21 * .8 ** i), 457, ["#FF7642", "#FFA373"]);
  text(s, "4 轮", 1050, 299, 160, 75, { size: 47, bold: true });
  text(s, "8 轮", 1050, 443, 160, 75, { size: 47, bold: true, color: C.orange });
  [0, 30, 60, 90].forEach(v => {
    const x = axisX + unit * v;
    rect(s, x, 515, 1, 10, C.gray, "刻度");
    text(s, String(v), x - 27, 530, 54, 32, { size: 16, align: "center", color: C.muted, font: mono });
  });
  text(s, "天", 1050, 525, 80, 41, { size: 18, color: C.muted });
  text(s, "条内数字为每轮耗时，单位为天。", 73, 594, 960, 38, { size: 19, color: C.muted });
  notes(s, "以固定 90 天为窗口，只计算完整轮次。固定耗时完成 4 轮，共 84 天。加速组第 n 轮耗时为 21×0.8^(n−1) 天，前 8 轮共约 87.38 天，第 9 轮会超出窗口。数字用于展示反馈的数学效果，未估计现实中的速度或持续倍数。");
}

// 06 — A deliberate change of pace
{
  const s = slide();
  await photo(s, "warp", 0, 0, 1280, 720, "高速收束的橙色光纤构成的长曝光效果");
  rect(s, 0, 0, 1280, 720, "#0B0B0D/56", "文字对比底");
  index(s, 6, "如果闭环开始加速");
  lines(s, ["一场听不见的", "智能爆炸"], 75, 208, 1130, 90, 112, { bold: true });
  lines(s, ["周五立项。周末并行验证上百个方案。", "周一开会时，最好的方案已经催生了下一代。"], 80, 481, 1140, 30, 48, { bold: true });
  notes(s, "这是一幕假想中的研发场景。这里的下一代可以是更有效的算法或研究工具。一项改进进入下一轮的速度如果超过组织开会的频率，研究员就可能在项目启动后第一次碰头时面对几轮新的结果。");
}

// 07 — Software
{
  const s = slide();
  await photo(s, "software", 611, 0, 669, 720, "暗色机房中层叠的橙色光纤");
  index(s, 7, "软件");
  lines(s, ["有自动测试的地方", "迭代可能最先提速"], 69, 144, 605, 52, 72, { bold: true });
  rect(s, 74, 339, 480, 1, C.dim, "案例分界线");
  lines(s, ["同一个性能问题可以同时试几十种改法。", "跑完测试，实测最快的版本留下来。"], 74, 377, 525, 25, 46, { color: C.muted });
  text(s, "瓶颈随之转向测试覆盖与线上验证。", 73, 530, 535, 56, { size: 25, color: C.orange, bold: true });
  notes(s, "这是情景推演。以通用性能优化举例：即使生成候选代码和并行执行很快，基准是否代表生产流量、是否有回归、性能收益是否能延续，仍要验证。AlphaEvolve 提供了以可评估目标搜索算法的真实例子。", [evolve]);
}

// 08 — Experimental science
{
  const s = slide(C.paper);
  await photo(s, "science", 0, 0, 639, 720, "自动化材料实验室里的机械臂和发光样品");
  text(s, "08", 684, 42, 32, 32, { size: 17, font: mono, color: C.rust });
  text(s, "实验科学", 730, 42, 300, 32, { size: 15, color: C.gray, bold: true });
  lines(s, ["假设多到做不完", "实验该先做哪一个？"], 684, 141, 550, 49, 70, { color: C.ink, bold: true });
  lines(s, ["以新材料为例，AI 可以批量提出候选方案，", "再根据实测结果重排下一批实验。"], 687, 327, 540, 23, 40, { color: C.gray });
  rect(s, 688, 461, 496, 1, C.light, "验证阶段分界线");
  lines(s, ["实验设备、测量质量与复现实验", "决定多少想法能变成可靠结果。"], 687, 499, 535, 24, 42, { color: C.rust, bold: true });
  notes(s, "这里讨论通用材料研发情景。候选方案更丰富，会提高筛选与实验编排的价值。模型可以影响实验顺序，材料制备与结果复现仍需实际执行。");
}

// 09 — Physical constraint
{
  const s = slide();
  await photo(s, "physical", 0, 0, 1280, 720, "暮色中的数据中心和变电设施");
  rect(s, 0, 0, 1280, 720, "#0B0B0D/51", "文字对比底");
  index(s, 9, "物理约束");
  text(s, "电网有自己的工期", 71, 112, 1120, 103, { size: 73, bold: true });
  text(s, "415 TWh", 73, 344, 1025, 153, { font: mono, size: 116, color: C.orange });
  text(s, "2024 年全球数据中心用电量，约占全球用电量的 1.5%。", 78, 501, 1130, 55, { size: 28, bold: true });
  text(s, "新机房什么时候能投用，还要看电网什么时候能接入。", 78, 551, 1130, 45, { size: 24 });
  text(s, "来源　国际能源署《Energy and AI》", 80, 625, 1140, 32, { size: 16, color: C.muted });
  notes(s, "415 太瓦时是 2024 年全球数据中心的总用电量，包括非 AI 工作负载。IEA 指出，电网接入排队可能拖慢数据中心建设。即使软件迭代突然加快，芯片制造、供电及基础设施扩建仍有自己的交付周期。", [iea]);
}

// 10 — Qualitative trajectories with editable diagrams
{
  const s = slide(C.paper);
  index(s, 10, "三种可能的速度", true);
  text(s, "闭环会怎样加速？", 71, 104, 1110, 86, { size: 63, bold: true, color: C.ink });
  text(s, "纵轴为研发产出速率，横轴为时间。曲线为情景示意。", 75, 197, 1130, 45, { size: 23, color: C.gray });
  const cards = [
    { name: "快速跃升", body: ["多轮有效改进互相叠加，", "研发周期连续缩短。"], curve: [141, 137, 129, 111, 79, 15] },
    { name: "阶梯式提速", body: ["算力、验证或部署卡住，", "瓶颈解除后才继续提速。"], curve: [141, 139, 109, 107, 107, 58, 58, 24] },
    { name: "增益趋缓", body: ["容易取得的收益先耗尽，", "剩下的难题需要更多投入。"], curve: [141, 105, 78, 64, 59, 56] },
  ];
  cards.forEach((item, i) => {
    const x = 74 + i * 385;
    const y = 275;
    rect(s, x, y + 151, 330, 1, C.light, "时间轴");
    rect(s, x, y, 1, 152, C.light, "产出速率轴");
    const points = item.curve.map((value, j) => [x + 4 + j * 307 / (item.curve.length - 1), y + value]);
    for (let j = 1; j < points.length; j++) stroke(s, ...points[j - 1], ...points[j], C.rust, 4);
    dot(s, ...points[points.length - 1], 9, C.rust);
    text(s, item.name, x, 441, 347, 54, { size: 33, color: C.ink, bold: true });
    lines(s, item.body, x, 508, 330, 23, 37, { color: C.gray });
  });
  notes(s, "这三条曲线是机制示意，不涉及发生概率、日期和行业间排序。一个行业也可能同时经历不同走势，例如软件研发提速，而实体项目在设备排期上形成台阶。");
}

// 11 — Authority
{
  const s = slide();
  await photo(s, "control", 0, 0, 1280, 720, "操作员仰望巨大的工业控制室窗面");
  rect(s, 0, 0, 1280, 720, "#0B0B0D/60", "文字对比底");
  index(s, 11, "控制权");
  lines(s, ["当研发周期短过审批周期，", "谁还有时间叫停？"], 70, 135, 1150, 58, 88, { bold: true });
  const questions = ["谁能发起高成本实验？", "谁独立验证结果？", "谁能暂停部署并回退？"];
  questions.forEach((question, i) => {
    const y = 385 + i * 65;
    dot(s, 82, y + 25, 8, C.orange);
    text(s, question, 109, y, 815, 50, { size: 29, color: C.white });
  });
  notes(s, "速度与权限叠加才会带来行动后果。研究流程可以将候选生成、独立评测、高成本资源授权和上线决策交给不同主体。讨论最后一个问题时可以停顿，让听众想象其所在组织的真实权限配置。");
}

// 12 — Observable indicators
{
  const s = slide(C.paper);
  index(s, 12, "如何判断闭环在加速", true);
  text(s, "下一轮研发真的更快了吗？", 71, 109, 1140, 91, { size: 62, bold: true, color: C.ink });
  const rows = [
    ["周期", "从提出假设到在生产环境中验证改进，用了多久？"],
    ["人工介入", "完成同样难度的任务，需要人工接手多少次？"],
    ["跨代收益", "这轮产生的工具或算法，让下一轮实际快了多少？"],
  ];
  rows.forEach(([label, question], i) => {
    const y = 249 + i * 105;
    rect(s, 74, y, 1128, 1, C.light, "指标分隔线");
    text(s, label, 75, y + 18, 240, 60, { size: 32, color: C.rust, bold: true });
    text(s, question, 327, y + 18, 877, 60, { size: 27, color: C.ink });
  });
  rect(s, 74, 564, 1128, 1, C.light, "指标分隔线");
  notes(s, "这些是用于检验假说的观测问题。比较时固定任务难度和质量标准，记录失败与回滚，并控制算力、人员数量等改变。跨代收益尤其关键，因为它直接检验一次成果是否真的进入下一轮研发。");
}

// 13 — Close
{
  const s = slide();
  await photo(s, "city", 0, 0, 1280, 720, "夜间城市上空辐射开的橙色光轨");
  rect(s, 0, 0, 1280, 720, "#0B0B0D/55", "文字对比底");
  lines(s, ["如果每一代 AI 都能", "更快造出下一代呢？"], 74, 207, 1120, 83, 108, { bold: true });
  text(s, "下一次突破到来时，我们可能还在理解上一次。", 80, 467, 1130, 60, { size: 33, color: C.white });
  notes(s, "回到 Good 的原始问题。智能爆炸假说最值得思考的一点，是推进 AI 研发的能力本身可以变成 AI 研发的产物。如果这个反馈足够快，企业、实验室和治理机构就要在更短间隔内判断该验证什么、谁可以继续，谁有权暂停。", [good]);
}

await (await PresentationFile.exportPptx(deck)).save(path.join(dir, "draft.pptx"));
