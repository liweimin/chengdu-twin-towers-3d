(() => {
  "use strict";

  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const slides = $$(".slide");
  const stage = $(".stage");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const contents = $("#contents-dialog");
  const notes = $("#notes-dialog");
  const notesData = JSON.parse($("#speaker-data").textContent);
  const prev = $("#prev");
  const next = $("#next");
  const formatPage = index => String(index + 1).padStart(2, "0");
  let current = -1;
  let outgoingTimer;
  let loopTimer;
  let profile = 0;
  let frameId;
  let touchStart;

  function slideFromHash() {
    const match = location.hash.match(/^#(\d+)$/);
    return match ? Number(match[1]) - 1 : 0;
  }

  function go(index, { writeHash = true, focusSlide = false } = {}) {
    if (!Number.isInteger(index) || index < 0 || index >= slides.length || index === current) return;
    clearTimeout(outgoingTimer);
    const outgoing = slides[current];
    stage.dataset.dir = index < current ? "back" : "forward";
    for (const slide of slides) slide.classList.remove("is-outgoing");
    if (outgoing) {
      focusSlide = focusSlide || outgoing.contains(document.activeElement);
      outgoing.inert = true;
      outgoing.classList.remove("is-active");
      if (!reduceMotion.matches) {
        outgoing.classList.add("is-outgoing");
        outgoingTimer = setTimeout(() => outgoing.classList.remove("is-outgoing"), 750);
      }
    }

    if (current === 2) stopLoop();
    current = index;
    const active = slides[index];
    active.inert = false;
    active.classList.add("is-active");
    active.scrollTop = 0;
    prev.disabled = index === 0;
    next.disabled = index === slides.length - 1;
    $("#position").textContent = formatPage(index) + " / " + slides.length;
    document.documentElement.style.setProperty("--position", (index + 1) / slides.length);
    document.title = "智能爆炸 · " + active.dataset.title;
    for (const item of $$("#contents-list button")) {
      if (Number(item.dataset.page) === current) item.setAttribute("aria-current", "page");
      else item.removeAttribute("aria-current");
    }
    if (writeHash) history.replaceState(null, "", "#" + formatPage(index));
    if (focusSlide) {
      const heading = active.querySelector("h1, h2");
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
    if (current === 4) renderModel(true);
    if (current === 9) requestAnimationFrame(() => beginChart());
  }

  const stepDescriptions = [
    "AI 读论文、比较方案，提出能被实验检验的改进。",
    "多个候选方案同时进入实验，每条路线独立产出结果。",
    "在统一评测条件下复核结果，保留可重复的改进。",
    "把有效改进投入下一轮研发。闭环由此形成。",
  ];
  const stepButtons = $$("[data-step]");
  const loopPlay = $("#loop-play");

  function showStep(step) {
    for (const button of stepButtons) button.setAttribute("aria-pressed", String(Number(button.dataset.step) === step));
    $("#step-description").textContent = stepDescriptions[step];
    $("#loop-id").textContent = formatPage(step);
  }

  function stopLoop() {
    clearInterval(loopTimer);
    loopTimer = undefined;
    loopPlay.setAttribute("aria-pressed", "false");
    loopPlay.firstElementChild.textContent = "▶";
    loopPlay.lastChild.textContent = " 播放一轮";
  }

  loopPlay.addEventListener("click", () => {
    if (loopTimer !== undefined) {
      stopLoop();
      return;
    }
    let step = 0;
    showStep(step);
    loopPlay.setAttribute("aria-pressed", "true");
    loopPlay.firstElementChild.textContent = "Ⅱ";
    loopPlay.lastChild.textContent = " 暂停";
    loopTimer = setInterval(() => {
      step += 1;
      if (step === stepDescriptions.length) stopLoop();
      else showStep(step);
    }, 1150);
  });

  for (const button of stepButtons) {
    button.addEventListener("click", () => {
      stopLoop();
      showStep(Number(button.dataset.step));
    });
  }

  const gainInput = $("#gain");
  const daysInput = $("#days");

  function roundLengths(days, gain) {
    const cycles = [];
    let remaining = days;
    let duration = 21;
    while (remaining + 1e-9 >= duration) {
      cycles.push(duration);
      remaining -= duration;
      duration = Math.max(2, duration * (1 - gain));
    }
    return cycles;
  }

  function renderTrack(track, durations, days, animate) {
    const blocks = durations.map((duration, index) => {
      const block = document.createElement("span");
      const label = Number(duration.toFixed(1)).toString();
      const fraction = duration / days * 100;
      block.className = "block";
      block.style.setProperty("--size", fraction + "%");
      block.style.setProperty("--delay", Math.min(index * 23, 240) + "ms");
      block.title = "第 " + (index + 1) + " 轮，" + label + " 天";
      if (fraction >= 4.2) block.textContent = label;
      return block;
    });
    track.classList.toggle("is-animated", animate);
    track.replaceChildren(...blocks);
  }

  function renderModel(animate = false) {
    const days = Number(daysInput.value);
    const gain = Number(gainInput.value);
    const baseline = roundLengths(days, 0);
    const improved = roundLengths(days, gain / 100);
    $("#gain-label").value = gain + "%";
    $("#days-label").value = days + " 天";
    $("#question-days").textContent = days;
    $("#middle-day").textContent = days / 2;
    $("#last-day").textContent = days + " 天";
    $("#baseline-count").textContent = baseline.length;
    $("#model-count").textContent = improved.length;
    $("#model-summary").textContent = days + " 天内，固定耗时组完成 " + baseline.length + " 轮，逐轮缩短组完成 " + improved.length + " 轮。";
    renderTrack($("#baseline-track"), baseline, days, animate);
    renderTrack($("#model-track"), improved, days, animate);
  }

  gainInput.addEventListener("input", () => renderModel());
  daysInput.addEventListener("input", () => renderModel());
  $("#reset-model").addEventListener("click", () => {
    gainInput.value = "20";
    daysInput.value = "90";
    renderModel(true);
  });

  const models = [
    { curve: [0.06, 0.08, 0.13, 0.24, 0.46, 0.95], desc: "多轮有效改进互相叠加，研发周期连续缩短。", label: "快速跃升情景，研发产出速率随时间越来越快地上升" },
    { curve: [0.06, 0.06, 0.28, 0.28, 0.28, 0.63, 0.63, 0.83], desc: "算力、验证或部署卡住，瓶颈解除后才继续提速。", label: "阶梯式提速情景，研发产出速率在瓶颈解除后逐阶上升" },
    { curve: [0.06, 0.35, 0.55, 0.61, 0.65, 0.67], desc: "容易取得的收益先耗尽，剩下的难题需要更多投入。", label: "增益趋缓情景，研发产出速率在早期上升后逐渐趋平" },
  ];
  const canvas = $("#profile-chart");

  function drawChart(progress) {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (width <= 0 || height <= 0) return;
    const density = Math.min(devicePixelRatio || 1, 2);
    if (canvas.width !== width * density || canvas.height !== height * density) {
      canvas.width = Math.round(width * density);
      canvas.height = Math.round(height * density);
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(density, 0, 0, density, 0, 0);
    ctx.clearRect(0, 0, width, height);
    const left = 3;
    const bottom = height - 6;
    const w = width - 10;
    const h = height - 15;
    ctx.strokeStyle = "#d6c6b8";
    ctx.lineWidth = 1;
    for (let row = 0; row <= 4; row += 1) {
      const y = bottom - h * row / 4;
      ctx.beginPath();
      ctx.moveTo(left, y);
      ctx.lineTo(left + w, y);
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(left, bottom - h);
    ctx.lineTo(left, bottom);
    ctx.stroke();

    function paintCurve(curve, active) {
      const length = (curve.length - 1) * (active ? progress : 1);
      const all = Math.floor(length);
      const x = node => left + w * node / (curve.length - 1);
      const y = value => bottom - h * value;
      const endValue = all < curve.length - 1
        ? curve[all] + (curve[all + 1] - curve[all]) * (length - all)
        : curve[all];
      ctx.beginPath();
      ctx.moveTo(x(0), y(curve[0]));
      for (let node = 1; node <= all; node += 1) ctx.lineTo(x(node), y(curve[node]));
      ctx.lineTo(x(length), y(endValue));
      ctx.strokeStyle = active ? "#b63611" : "#af8c7760";
      ctx.lineWidth = active ? 3.5 : 1.75;
      ctx.lineJoin = "round";
      ctx.stroke();
      if (active) {
        ctx.beginPath();
        ctx.arc(x(length), y(endValue), 4.4, 0, 2 * Math.PI);
        ctx.fillStyle = "#b63611";
        ctx.fill();
      }
    }

    models.forEach((model, index) => {
      if (index !== profile) paintCurve(model.curve, false);
    });
    paintCurve(models[profile].curve, true);
  }

  function beginChart() {
    cancelAnimationFrame(frameId);
    if (current !== 9) return;
    if (reduceMotion.matches) {
      drawChart(1);
      return;
    }
    const start = performance.now();
    function tick(now) {
      if (current !== 9) return;
      const progress = Math.min(1, (now - start) / 670);
      drawChart(1 - (1 - progress) ** 3);
      if (progress < 1) frameId = requestAnimationFrame(tick);
    }
    frameId = requestAnimationFrame(tick);
  }

  const profileButtons = $$("[data-profile]");
  for (const button of profileButtons) {
    button.addEventListener("click", () => {
      profile = Number(button.dataset.profile);
      for (const option of profileButtons) option.setAttribute("aria-pressed", String(option === button));
      $("#profile-description").textContent = models[profile].desc;
      canvas.setAttribute("aria-label", models[profile].label);
      beginChart();
    });
  }

  new ResizeObserver(() => {
    if (current === 9) drawChart(1);
  }).observe(canvas);

  const entries = slides.map((slide, index) => {
    const row = document.createElement("li");
    const button = document.createElement("button");
    const number = document.createElement("span");
    number.textContent = formatPage(index);
    button.type = "button";
    button.dataset.page = index;
    button.append(number, slide.dataset.title);
    button.addEventListener("click", () => {
      contents.close();
      go(index, { focusSlide: true });
    });
    row.append(button);
    return row;
  });
  $("#contents-list").append(...entries);

  function openNotes() {
    const data = notesData[current];
    $("#notes-title").textContent = "讲者备注 · " + formatPage(current);
    $("#notes-copy").textContent = data.body;
    const links = data.sources.map(source => {
      const row = document.createElement("li");
      const link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = source.title + " ↗";
      row.append(link);
      return row;
    });
    $("#notes-sources").replaceChildren(...links);
    notes.showModal();
  }

  const full = $("#fullscreen");
  if (!document.fullscreenEnabled) full.hidden = true;
  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (document.fullscreenEnabled) await document.documentElement.requestFullscreen();
    } catch (error) {
      console.info("当前浏览器无法切换全屏。", error);
    }
  }
  document.addEventListener("fullscreenchange", () => {
    const label = document.fullscreenElement ? "退出全屏" : "全屏";
    $("#fullscreen-label").textContent = label;
    full.setAttribute("aria-label", label);
  });

  $(".begin").addEventListener("click", () => go(1, { focusSlide: true }));
  prev.addEventListener("click", () => go(current - 1));
  next.addEventListener("click", () => go(current + 1));
  full.addEventListener("click", toggleFullscreen);
  $("#contents-open").addEventListener("click", () => contents.showModal());
  $("#notes-open").addEventListener("click", openNotes);

  window.addEventListener("hashchange", () => go(slideFromHash(), { writeHash: false }));
  document.addEventListener("keydown", event => {
    if (contents.open || notes.open || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.target.closest("input, textarea, select, [contenteditable]")) return;
    const key = event.key.toLowerCase();
    if (key === " " && event.target.closest("button, a")) return;
    const commands = {
      arrowright: () => go(current + 1),
      pagedown: () => go(current + 1),
      " ": () => go(current + (event.shiftKey ? -1 : 1)),
      arrowleft: () => go(current - 1),
      pageup: () => go(current - 1),
      home: () => go(0),
      end: () => go(slides.length - 1),
      f: toggleFullscreen,
      g: () => contents.showModal(),
      n: openNotes,
    };
    if (Object.hasOwn(commands, key)) {
      event.preventDefault();
      commands[key]();
    }
  });

  stage.addEventListener("touchstart", event => {
    if (event.touches.length !== 1 || event.target.closest("button, input, a")) {
      touchStart = undefined;
      return;
    }
    touchStart = [event.touches[0].clientX, event.touches[0].clientY];
  }, { passive: true });

  stage.addEventListener("touchend", event => {
    if (!touchStart) return;
    const touch = event.changedTouches[0];
    const dx = touch.clientX - touchStart[0];
    const dy = touch.clientY - touchStart[1];
    touchStart = undefined;
    if (Math.abs(dx) > 65 && Math.abs(dx) > Math.abs(dy) * 1.55) go(current + (dx < 0 ? 1 : -1));
  }, { passive: true });

  stage.addEventListener("touchcancel", () => { touchStart = undefined; });
  const initial = slideFromHash();
  go(initial >= 0 && initial < slides.length ? initial : 0, { writeHash: false });
})();
