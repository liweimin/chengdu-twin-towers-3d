/* ============================================================================
   EVENT HORIZON — Interactive Presentation Engine
   Generative WebGL-grade Canvas Backdrop + Slide Choreography + Live Widgets + Procedural Audio
   ============================================================================ */

(() => {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const totalSlides = slides.length;
  let currentIndex = 0;
  let isTransitioning = false;

  // DOM References
  const body = document.body;
  const hudPhase = document.getElementById('hud-phase');
  const progressBar = document.getElementById('progress-bar');
  const counterCurrent = document.getElementById('counter-current');
  const counterTotal = document.getElementById('counter-total');
  const navDotsContainer = document.getElementById('nav-dots');
  const notesDrawer = document.getElementById('notes-drawer');
  const notesContent = document.getElementById('notes-content');
  const overviewModal = document.getElementById('overview-modal');
  const overviewGrid = document.getElementById('overview-grid');
  const btnAudio = document.getElementById('btn-audio');
  const audioIcon = document.getElementById('audio-icon');

  counterTotal.textContent = String(totalSlides).padStart(2, '0');

  // Mouse tracking for subtle parallax & canvas gravity
  const mouse = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5 };
  window.addEventListener('mousemove', (e) => {
    mouse.tx = e.clientX / window.innerWidth;
    mouse.ty = e.clientY / window.innerHeight;
  });

  /* --------------------------------------------------------------------------
     1. PROCEDURAL CINEMATIC WEB AUDIO ENGINE (Muted by default, toggle via M)
     -------------------------------------------------------------------------- */
  const audioEngine = (() => {
    let ctx = null;
    let enabled = false;
    let droneGain = null;
    let osc1 = null;
    let osc2 = null;

    function init() {
      if (ctx) return;
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      ctx = new AudioCtx();

      // Deep cinematic sub-bass drone
      droneGain = ctx.createGain();
      droneGain.gain.value = 0.0;

      const filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.value = 140;

      osc1 = ctx.createOscillator();
      osc1.type = 'sine';
      osc1.frequency.value = 46.25; // F#1

      osc2 = ctx.createOscillator();
      osc2.type = 'triangle';
      osc2.frequency.value = 69.3; // C#2

      osc1.connect(filter);
      osc2.connect(filter);
      filter.connect(droneGain);
      droneGain.connect(ctx.destination);

      osc1.start();
      osc2.start();
    }

    function toggle() {
      init();
      if (ctx.state === 'suspended') ctx.resume();
      enabled = !enabled;
      const now = ctx.currentTime;
      droneGain.gain.cancelScheduledValues(now);
      droneGain.gain.setTargetAtTime(enabled ? 0.08 : 0.0, now, 0.35);
      audioIcon.textContent = enabled ? '♪ ON' : '♪ OFF';
      btnAudio.classList.toggle('active', enabled);
      if (enabled) playChime(329.63);
    }

    function playChime(freq = 261.63) {
      if (!enabled || !ctx) return;
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now);
      osc.frequency.exponentialRampToValueAtTime(freq * 1.5, now + 0.45);
      gain.gain.setValueAtTime(0.055, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.75);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.8);
    }

    return { toggle, playChime };
  })();

  /* --------------------------------------------------------------------------
     2. NAVIGATION & SLIDE CHOREOGRAPHY
     -------------------------------------------------------------------------- */
  function buildNavigation() {
    slides.forEach((slide, idx) => {
      // Bottom dots
      const dot = document.createElement('button');
      dot.className = 'nav-dot' + (idx === 0 ? ' active' : '');
      dot.setAttribute('aria-label', `Go to slide ${idx + 1}`);
      dot.addEventListener('click', () => goToSlide(idx));
      navDotsContainer.appendChild(dot);

      // Overview cards
      const card = document.createElement('button');
      const isLight = slide.dataset.theme === 'light';
      card.className = 'ov-card' + (isLight ? ' light-preview' : '') + (idx === 0 ? ' current' : '');
      card.innerHTML = `
        <span class="mono ov-num">${String(idx + 1).padStart(2, '0')} / ${totalSlides}</span>
        <div class="ov-title">${slide.dataset.title || ''}</div>
        <div class="mono ov-phase">${slide.dataset.phase || ''}</div>
      `;
      card.addEventListener('click', () => {
        goToSlide(idx);
        toggleOverview(false);
      });
      overviewGrid.appendChild(card);
    });
  }

  function goToSlide(nextIndex) {
    if (nextIndex < 0 || nextIndex >= totalSlides || nextIndex === currentIndex || isTransitioning) return;
    isTransitioning = true;

    const prevSlide = slides[currentIndex];
    const nextSlide = slides[nextIndex];
    const forward = nextIndex > currentIndex;

    prevSlide.classList.remove('active');
    prevSlide.classList.toggle('prev-exit', forward);

    nextSlide.classList.remove('prev-exit');
    nextSlide.classList.add('active');

    currentIndex = nextIndex;

    // Sync theme, HUD, progress, notes
    const theme = nextSlide.dataset.theme || 'dark';
    body.dataset.theme = theme;
    body.dataset.slide = String(currentIndex);
    hudPhase.textContent = nextSlide.dataset.phase || '';
    counterCurrent.textContent = String(currentIndex + 1).padStart(2, '0');
    progressBar.style.width = `${((currentIndex + 1) / totalSlides) * 100}%`;
    notesContent.textContent = nextSlide.dataset.notes || '';

    // Update dots & overview
    document.querySelectorAll('.nav-dot').forEach((d, i) => d.classList.toggle('active', i === currentIndex));
    document.querySelectorAll('.ov-card').forEach((c, i) => c.classList.toggle('current', i === currentIndex));

    // Audio chime mapped to slide tension
    const freqs = [196, 220, 261.6, 392, 293.7, 329.6, 349.2, 440, 246.9, 233.1, 277.2, 164.8];
    audioEngine.playChime(freqs[currentIndex % freqs.length]);

    // Update URL hash quietly
    history.replaceState(null, '', `#slide-${currentIndex + 1}`);

    setTimeout(() => {
      isTransitioning = false;
    }, 420);
  }

  function toggleOverview(force) {
    const open = typeof force === 'boolean' ? force : !overviewModal.classList.contains('open');
    overviewModal.classList.toggle('open', open);
    overviewModal.setAttribute('aria-hidden', String(!open));
  }

  function toggleNotes(force) {
    const open = typeof force === 'boolean' ? force : !notesDrawer.classList.contains('open');
    notesDrawer.classList.toggle('open', open);
    notesDrawer.setAttribute('aria-hidden', String(!open));
    document.getElementById('btn-notes').classList.toggle('active', open);
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  // Event Listeners
  document.getElementById('btn-prev').addEventListener('click', () => goToSlide(currentIndex - 1));
  document.getElementById('btn-next').addEventListener('click', () => goToSlide(currentIndex + 1));
  document.getElementById('btn-overview').addEventListener('click', () => toggleOverview());
  document.getElementById('btn-close-overview').addEventListener('click', () => toggleOverview(false));
  document.getElementById('btn-notes').addEventListener('click', () => toggleNotes());
  document.getElementById('btn-close-notes').addEventListener('click', () => toggleNotes(false));
  document.getElementById('btn-fullscreen').addEventListener('click', toggleFullscreen);
  btnAudio.addEventListener('click', () => audioEngine.toggle());
  document.getElementById('btn-restart').addEventListener('click', () => goToSlide(0));
  document.getElementById('btn-end-grid').addEventListener('click', () => toggleOverview(true));

  window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'Escape') {
      toggleOverview(false);
      toggleNotes(false);
      return;
    }
    if (overviewModal.classList.contains('open')) return;

    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
      e.preventDefault();
      goToSlide(currentIndex + 1);
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      goToSlide(currentIndex - 1);
    } else if (e.key === 'Home') {
      goToSlide(0);
    } else if (e.key === 'End') {
      goToSlide(totalSlides - 1);
    } else if (e.key.toLowerCase() === 'g') {
      toggleOverview();
    } else if (e.key.toLowerCase() === 'n') {
      toggleNotes();
    } else if (e.key.toLowerCase() === 'f') {
      toggleFullscreen();
    } else if (e.key.toLowerCase() === 'm') {
      audioEngine.toggle();
    }
  });

  // Wheel navigation with debounce
  let wheelLock = false;
  window.addEventListener('wheel', (e) => {
    if (overviewModal.classList.contains('open') || wheelLock) return;
    if (Math.abs(e.deltaY) < 35) return;
    wheelLock = true;
    if (e.deltaY > 0) goToSlide(currentIndex + 1);
    else goToSlide(currentIndex - 1);
    setTimeout(() => { wheelLock = false; }, 650);
  }, { passive: true });

  // Touch swipe
  let touchStartX = 0;
  window.addEventListener('touchstart', (e) => { touchStartX = e.touches[0].clientX; }, { passive: true });
  window.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 55) {
      if (dx < 0) goToSlide(currentIndex + 1);
      else goToSlide(currentIndex - 1);
    }
  }, { passive: true });

  /* --------------------------------------------------------------------------
     3. INTERACTIVE SLIDE WIDGETS
     -------------------------------------------------------------------------- */

  // --- SLIDE 2: Linear Trap Slider ---
  const trapSlider = document.getElementById('trap-slider');
  const trapCursorLine = document.getElementById('trap-cursor-line');
  const trapDotLinear = document.getElementById('trap-dot-linear');
  const trapDotExp = document.getElementById('trap-dot-exp');
  const trapGapLabel = document.getElementById('trap-gap-label');
  const trapYearBadge = document.getElementById('trap-year-badge');
  const trapMultVal = document.getElementById('trap-mult-val');
  const trapCaption = document.getElementById('trap-caption');

  function updateLinearTrap(val) {
    const t = (val - 15) / (96 - 15); // 0 to 1
    const x = 50 + t * 475;
    const yLinear = 305 - t * 66;
    // Super-exponential curve approximation matching SVG path
    const yExp = 306 - Math.pow(t, 4.6) * 278;

    trapCursorLine.setAttribute('x1', x);
    trapCursorLine.setAttribute('x2', x);
    trapDotLinear.setAttribute('cx', x);
    trapDotLinear.setAttribute('cy', yLinear);
    trapDotExp.setAttribute('cx', x);
    trapDotExp.setAttribute('cy', yExp);

    const year = (2020 + t * 10).toFixed(1);
    const ratio = Math.max(1, Math.pow(10, Math.pow(t, 3.2) * 3.1));
    const ratioText = ratio < 10 ? `${ratio.toFixed(1)}×` : ratio < 1000 ? `${Math.round(ratio)}×` : `${(ratio / 1000).toFixed(1)}k×`;

    trapYearBadge.textContent = `T = ${year}`;
    trapMultVal.textContent = `现实 / 直觉: ${ratioText}`;
    const labelX = x > 380 ? x - 72 : x + 10;
    trapGapLabel.setAttribute('x', labelX);
    trapGapLabel.setAttribute('y', Math.max(45, (yLinear + yExp) / 2));
    trapGapLabel.textContent = `Δ = ${ratioText}`;

    if (t < 0.48) {
      trapCaption.textContent = '在早期阶段，真实曲线甚至显得比人类的线性预期还要温和——这制造了致命的「不过如此」错觉。';
    } else if (t < 0.78) {
      trapCaption.textContent = '拐点悄然越过。模型能力开始按季度而非按十年跃升，但大多数机构仍在用线性模型做五年规划。';
    } else {
      trapCaption.textContent = '垂直升空：线性直觉彻底失效。短短几个月内的能力跨度，超过了过去整个计算机史的总和。';
    }
  }
  trapSlider.addEventListener('input', (e) => updateLinearTrap(Number(e.target.value)));
  updateLinearTrap(58);

  // --- SLIDE 3: Recursive Ignition Button ---
  const btnIgnite = document.getElementById('btn-ignite');
  const igniteBtnText = document.getElementById('ignite-btn-text');
  const loopCard = document.querySelector('.loop-card');
  const loopCycle = document.getElementById('loop-cycle');
  const loopGain = document.getElementById('loop-gain');
  const loopStatus = document.getElementById('loop-status');
  const loopCoreLabel = document.getElementById('loop-core-label');
  const loopCoreSub = document.getElementById('loop-core-sub');
  let ignited = false;
  let igniteTimer = null;

  btnIgnite.addEventListener('click', () => {
    ignited = !ignited;
    btnIgnite.classList.toggle('ignited', ignited);
    loopCard.classList.toggle('loop-fast', ignited);
    audioEngine.playChime(ignited ? 523.25 : 220);

    if (ignited) {
      igniteBtnText.textContent = '■ 停止模拟 (RESET LOOP)';
      loopStatus.textContent = 'STATUS: SUPERCRITICAL';
      const stages = [
        { cycle: '6 个月', gain: '4.2×', gen: 'GEN N+1', sub: 'AUTO-CODER' },
        { cycle: '3 周', gain: '28×', gen: 'GEN N+3', sub: 'ARCH DISCOVERY' },
        { cycle: '48 小时', gain: '340×', gen: 'GEN N+8', sub: 'RECURSIVE' },
        { cycle: '实时连续进化', gain: '∞', gen: 'ASI', sub: 'SINGULARITY' }
      ];
      let step = 0;
      clearInterval(igniteTimer);
      igniteTimer = setInterval(() => {
        const s = stages[Math.min(step, stages.length - 1)];
        loopCycle.textContent = s.cycle;
        loopGain.textContent = s.gain;
        loopCoreLabel.textContent = s.gen;
        loopCoreSub.textContent = s.sub;
        step++;
        if (step >= stages.length) clearInterval(igniteTimer);
      }, 650);
    } else {
      clearInterval(igniteTimer);
      igniteBtnText.textContent = '⚡ 启动递归点火 (IGNITE LOOP)';
      loopStatus.textContent = 'STATUS: HUMAN-PACED';
      loopCycle.textContent = '18 个月';
      loopGain.textContent = '1.0×';
      loopCoreLabel.textContent = 'GEN N';
      loopCoreSub.textContent = 'BASELINE';
    }
  });

  // --- SLIDE 5: Parallel Minds Swarm Canvas ---
  const swarmCanvas = document.getElementById('swarm-canvas');
  const swarmCtx = swarmCanvas.getContext('2d');
  const swarmBadge = document.getElementById('swarm-badge');
  const swarmPhds = document.getElementById('swarm-phds');
  const swarmPapers = document.getElementById('swarm-papers');
  let swarmScale = 1;

  const swarmNodes = Array.from({ length: 220 }, () => ({
    x: Math.random() * swarmCanvas.width,
    y: Math.random() * swarmCanvas.height,
    vx: (Math.random() - 0.5) * 1.4,
    vy: (Math.random() - 0.5) * 1.4,
    r: Math.random() * 1.8 + 0.8,
    hot: Math.random() > 0.72
  }));

  document.querySelectorAll('#swarm-controls .pill-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#swarm-controls .pill-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      swarmScale = Number(btn.dataset.scale);
      if (swarmScale === 1) {
        swarmBadge.textContent = '10,000 MINDS · 10× SPEED';
        swarmPhds.textContent = '100,000';
        swarmPapers.textContent = '4,200 / DAY';
      } else if (swarmScale === 2) {
        swarmBadge.textContent = '1,000,000 MINDS · 30× SPEED';
        swarmPhds.textContent = '30,000,000';
        swarmPapers.textContent = '180,000 / DAY';
      } else {
        swarmBadge.textContent = '10,000,000 MINDS · 50× SPEED';
        swarmPhds.textContent = '500,000,000';
        swarmPapers.textContent = '3,600,000 / DAY';
      }
      audioEngine.playChime(280 + swarmScale * 90);
    });
  });

  function renderSwarm() {
    if (currentIndex === 4) {
      const w = swarmCanvas.width;
      const h = swarmCanvas.height;
      swarmCtx.fillStyle = 'rgba(5, 7, 12, 0.28)';
      swarmCtx.fillRect(0, 0, w, h);

      const activeCount = swarmScale === 1 ? 70 : swarmScale === 2 ? 140 : 220;
      const speedMult = swarmScale === 1 ? 0.8 : swarmScale === 2 ? 1.8 : 3.2;
      const linkDist = swarmScale === 1 ? 62 : swarmScale === 2 ? 72 : 84;

      for (let i = 0; i < activeCount; i++) {
        const n = swarmNodes[i];
        n.x += n.vx * speedMult;
        n.y += n.vy * speedMult;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;

        for (let j = i + 1; j < activeCount; j++) {
          const m = swarmNodes[j];
          const dx = n.x - m.x;
          const dy = n.y - m.y;
          const d = Math.hypot(dx, dy);
          if (d < linkDist) {
            const alpha = (1 - d / linkDist) * (swarmScale === 3 ? 0.36 : 0.22);
            swarmCtx.strokeStyle = n.hot ? `rgba(255, 90, 31, ${alpha})` : `rgba(56, 232, 255, ${alpha})`;
            swarmCtx.lineWidth = 0.8;
            swarmCtx.beginPath();
            swarmCtx.moveTo(n.x, n.y);
            swarmCtx.lineTo(m.x, m.y);
            swarmCtx.stroke();
          }
        }

        swarmCtx.fillStyle = n.hot ? '#FF5A1F' : '#38E8FF';
        swarmCtx.beginPath();
        swarmCtx.arc(n.x, n.y, n.r * (swarmScale === 3 ? 1.25 : 1), 0, Math.PI * 2);
        swarmCtx.fill();
      }
    }
    requestAnimationFrame(renderSwarm);
  }
  renderSwarm();

  // --- SLIDE 6: Time Dilation Tabs ---
  const dilationData = {
    2025: { width: '20%', val: '≈ 2 年等效人类科研', text: '早期推理模型开始在数学竞赛、代码合成与文献综述上接管博士生级工作。' },
    2026: { width: '32%', val: '≈ 5 年等效人类科研', text: '自动化实验代理大规模部署，单家实验室的年度产出跃升数倍。' },
    2027: { width: '50%', val: '≈ 15 年等效人类科研', text: '单年内的算法、材料与生物模拟突破，相当于人类顶尖研究院 15 年的集体产出。' },
    2028: { width: '74%', val: '≈ 80 年等效人类科研', text: '递归自我改进全面接管：一年之内走完 20 世纪整个物理与生物学的发现跨度。' },
    2030: { width: '96%', val: '≈ 500+ 年（认知奇点）', text: '日历时间彻底失去参照意义。每一个季度都在诞生全新的科学范式与技术文明。' }
  };

  document.querySelectorAll('#dilation-tabs .year-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('#dilation-tabs .year-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const d = dilationData[tab.dataset.year];
      document.getElementById('dilation-bar').style.width = d.width;
      document.getElementById('dilation-val').textContent = d.val;
      document.getElementById('dilation-text').textContent = d.text;
      audioEngine.playChime(300 + (Number(tab.dataset.year) - 2025) * 45);
    });
  });

  // --- SLIDE 7: Bits to Atoms Domain Switcher ---
  const domainData = {
    bio: {
      code: 'DOMAIN 01 // BIOLOGICAL SINGULARITY',
      eta: 'IMPACT: MORTALITY REWRITE',
      headline: '把「治愈衰老」变成一个工程排期问题',
      desc: '当超级智能能在毫秒级精度上模拟完整人体细胞与蛋白质折叠动力学，临床试验不再需要十年试错。癌症、神经退行性疾病与器官衰竭将成为历史书上的词汇。',
      old: '12 年 · 20 亿美元 / 款新药',
      next: '全细胞数字孪生 · 按周定制分子疗法',
      svg: `
        <g stroke="#38E8FF" fill="none" stroke-width="1.8" opacity="0.9">
          <path d="M 40 110 Q 90 35, 140 110 T 240 110 T 320 110" />
          <path d="M 40 110 Q 90 185, 140 110 T 240 110 T 320 110" stroke="#FF5A1F" />
          <line x1="70" y1="78" x2="70" y2="142" stroke="rgba(255,255,255,0.28)" />
          <line x1="110" y1="78" x2="110" y2="142" stroke="rgba(255,255,255,0.28)" />
          <line x1="170" y1="78" x2="170" y2="142" stroke="rgba(255,255,255,0.28)" />
          <line x1="210" y1="78" x2="210" y2="142" stroke="rgba(255,255,255,0.28)" />
          <line x1="270" y1="78" x2="270" y2="142" stroke="rgba(255,255,255,0.28)" />
        </g>
        <text x="180" y="205" text-anchor="middle" fill="rgba(255,255,255,0.45)" font-size="10" class="mono">CELLULAR SIMULATION · ZERO-SHOT THERAPEUTICS</text>
      `
    },
    energy: {
      code: 'DOMAIN 02 // ENERGY ABUNDANCE',
      eta: 'IMPACT: ZERO MARGINAL ENERGY',
      headline: '驯服恒星之火与室温超导材料',
      desc: '通过微秒级磁场反馈控制托卡马克等离子体，并穷举数亿种晶体结构发现新型超导与高密度储能材料——能源从稀缺地缘资源变成像空气一样廉价的基础设施。',
      old: '化石燃料约束 · 电网瓶颈',
      next: '可控核聚变 + 轨道级太阳能捕获',
      svg: `
        <g transform="translate(180, 102)">
          <circle r="24" fill="rgba(255,90,31,0.35)" stroke="#FF5A1F" stroke-width="2" />
          <ellipse rx="88" ry="32" fill="none" stroke="#FFB347" stroke-width="1.5" transform="rotate(20)" />
          <ellipse rx="88" ry="32" fill="none" stroke="#38E8FF" stroke-width="1.5" transform="rotate(-20)" />
          <ellipse rx="110" ry="44" fill="none" stroke="rgba(255,255,255,0.22)" stroke-dasharray="4 6" />
        </g>
        <text x="180" y="205" text-anchor="middle" fill="rgba(255,255,255,0.45)" font-size="10" class="mono">MAGNETIC CONFINEMENT · MATERIAL DISCOVERY</text>
      `
    },
    nano: {
      code: 'DOMAIN 03 // ATOMIC PRECISION',
      eta: 'IMPACT: MATTER AS SOFTWARE',
      headline: '像编译代码一样逐原子组装物质',
      desc: '今天的制造业本质上是「用高温高压暴力砸碎和重塑材料」。超级智能将解锁分子级机械合成，使超强碳基结构、定制芯片与精密设备的成本暴跌几个数量级。',
      old: '高能耗减材制造 · 漫长供应链',
      next: '原子级增材组装 · 接近物理极限效率',
      svg: `
        <g stroke="#38E8FF" fill="none" stroke-width="1.4" transform="translate(180, 100)">
          <polygon points="0,-58 50,-29 50,29 0,58 -50,29 -50,-29" />
          <polygon points="0,-32 28,-16 28,16 0,32 -28,16 -28,-16" stroke="#FF5A1F" />
          <line x1="0" y1="-58" x2="0" y2="58" stroke="rgba(255,255,255,0.2)" />
          <line x1="-50" y1="-29" x2="50" y2="29" stroke="rgba(255,255,255,0.2)" />
          <line x1="50" y1="-29" x2="-50" y2="29" stroke="rgba(255,255,255,0.2)" />
          <circle cx="0" cy="-58" r="4" fill="#38E8FF" />
          <circle cx="50" cy="29" r="4" fill="#FF5A1F" />
          <circle cx="-50" cy="29" r="4" fill="#FFB347" />
        </g>
        <text x="180" y="205" text-anchor="middle" fill="rgba(255,255,255,0.45)" font-size="10" class="mono">MOLECULAR LATTICE · PROGRAMMABLE MATTER</text>
      `
    },
    robotics: {
      code: 'DOMAIN 04 // EMBODIED LEGION',
      eta: 'IMPACT: SELF-REPLICATING CAPEX',
      headline: '数亿台具身智能体接管实体世界',
      desc: '当通用灵巧操作与超级规划能力结合，机器人将自主建造数据中心、发电厂、火箭与更多机器人。人类历史上第一次出现「自我扩增的物理生产力」。',
      old: '人口老龄化约束 · 蓝领短缺',
      next: '24/7 自我复制的物理基础设施军团',
      svg: `
        <g stroke="rgba(255,255,255,0.28)" fill="none" stroke-width="1.3">
          <rect x="65" y="45" width="46" height="46" rx="4" stroke="#38E8FF" />
          <rect x="157" y="45" width="46" height="46" rx="4" stroke="#FF5A1F" />
          <rect x="249" y="45" width="46" height="46" rx="4" stroke="#FFB347" />
          <rect x="111" y="112" width="46" height="46" rx="4" stroke="#FF5A1F" />
          <rect x="203" y="112" width="46" height="46" rx="4" stroke="#38E8FF" />
          <line x1="111" y1="68" x2="157" y2="68" />
          <line x1="203" y1="68" x2="249" y2="68" />
          <line x1="88" y1="91" x2="134" y2="112" />
          <line x1="180" y1="91" x2="134" y2="112" />
          <line x1="180" y1="91" x2="226" y2="112" />
          <line x1="272" y1="91" x2="226" y2="112" />
        </g>
        <text x="180" y="205" text-anchor="middle" fill="rgba(255,255,255,0.45)" font-size="10" class="mono">AUTONOMOUS SUPPLY CHAINS · EXPONENTIAL BUILD</text>
      `
    }
  };

  function selectDomain(key) {
    const d = domainData[key];
    document.getElementById('domain-code').textContent = d.code;
    document.getElementById('domain-eta').textContent = d.eta;
    document.getElementById('domain-headline').textContent = d.headline;
    document.getElementById('domain-desc').textContent = d.desc;
    document.getElementById('domain-old').textContent = d.old;
    document.getElementById('domain-new').textContent = d.next;
    document.getElementById('domain-svg').innerHTML = d.svg;
  }

  document.querySelectorAll('#domain-list .domain-item').forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelectorAll('#domain-list .domain-item').forEach((i) => i.classList.remove('active'));
      item.classList.add('active');
      selectDomain(item.dataset.domain);
      audioEngine.playChime(340);
    });
  });
  selectDomain('bio');

  // --- SLIDE 10: Alignment Phase-Space Attractor Canvas ---
  const alignCanvas = document.getElementById('align-canvas');
  const alignCtx = alignCanvas.getContext('2d');
  const btnAlignSafe = document.getElementById('btn-align-safe');
  const btnAlignDrift = document.getElementById('btn-align-drift');
  const alignStatus = document.getElementById('align-status');
  const alignFootnote = document.getElementById('align-footnote');
  let alignDrift = false;

  const alignParticles = Array.from({ length: 90 }, (_, i) => ({
    angle: (i / 90) * Math.PI * 2,
    radius: 60 + Math.random() * 140,
    speed: 0.012 + Math.random() * 0.016
  }));

  btnAlignSafe.addEventListener('click', () => {
    alignDrift = false;
    btnAlignSafe.classList.add('active');
    btnAlignDrift.classList.remove('active');
    alignStatus.textContent = 'ATTRACTOR: LOCKED';
    alignFootnote.textContent = '容错率极低：轨迹必须精准收敛至人类价值的狭窄黄金吸引子内。';
    audioEngine.playChime(392);
  });

  btnAlignDrift.addEventListener('click', () => {
    alignDrift = true;
    btnAlignDrift.classList.add('active');
    btnAlignSafe.classList.remove('active');
    alignStatus.textContent = 'WARNING: DIVERGING';
    alignFootnote.textContent = '仅 0.1% 的目标函数偏差，在超人级优化压力下迅速撕裂轨道，演化为不可控的工具趋同。';
    audioEngine.playChime(146.8);
  });

  function renderAlignment() {
    if (currentIndex === 9) {
      const w = alignCanvas.width;
      const h = alignCanvas.height;
      const cx = w / 2;
      const cy = h / 2;

      alignCtx.fillStyle = 'rgba(5, 7, 12, 0.18)';
      alignCtx.fillRect(0, 0, w, h);

      // Safe Basin Ring
      alignCtx.strokeStyle = alignDrift ? 'rgba(255, 59, 31, 0.45)' : 'rgba(56, 232, 255, 0.45)';
      alignCtx.lineWidth = 1.5;
      alignCtx.beginPath();
      alignCtx.arc(cx, cy, 42, 0, Math.PI * 2);
      alignCtx.stroke();

      alignParticles.forEach((p) => {
        p.angle += p.speed * (alignDrift ? 2.4 : 1);
        if (!alignDrift) {
          p.radius += (36 - p.radius) * 0.025;
          if (Math.abs(p.radius - 36) < 2 && Math.random() < 0.02) p.radius = 155;
        } else {
          p.radius += 1.65;
          if (p.radius > 230) p.radius = 28 + Math.random() * 25;
        }

        const x = cx + Math.cos(p.angle) * p.radius * 1.25;
        const y = cy + Math.sin(p.angle) * p.radius * 0.85;

        alignCtx.fillStyle = alignDrift ? '#FF3B1F' : (p.radius < 55 ? '#FFB347' : '#38E8FF');
        alignCtx.beginPath();
        alignCtx.arc(x, y, alignDrift ? 2.2 : 1.7, 0, Math.PI * 2);
        alignCtx.fill();
      });
    }
    requestAnimationFrame(renderAlignment);
  }
  renderAlignment();

  /* --------------------------------------------------------------------------
     4. PERSISTENT 60FPS GENERATIVE COSMIC BACKDROP CANVAS
     Morphs smoothly depending on the active slide (Event Horizon -> Warp Grid -> Shockwave -> Horizon)
     -------------------------------------------------------------------------- */
  const bgCanvas = document.getElementById('bg-canvas');
  const bgCtx = bgCanvas.getContext('2d');
  let bw = 0;
  let bh = 0;

  function resizeBg() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    bw = window.innerWidth;
    bh = window.innerHeight;
    bgCanvas.width = bw * dpr;
    bgCanvas.height = bh * dpr;
    bgCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', resizeBg);
  resizeBg();

  // Persistent orbital particle field
  const starCount = 190;
  const stars = Array.from({ length: starCount }, () => ({
    angle: Math.random() * Math.PI * 2,
    dist: Math.random() * 0.65 + 0.08,
    speed: (Math.random() * 0.002 + 0.0005) * (Math.random() > 0.5 ? 1 : -1),
    size: Math.random() * 1.9 + 0.5,
    hue: Math.random() > 0.72 ? 'warm' : 'cool'
  }));

  let time = 0;
  function animateBackdrop() {
    time += 0.012;
    mouse.x += (mouse.tx - mouse.x) * 0.05;
    mouse.y += (mouse.ty - mouse.y) * 0.05;

    const isLight = body.dataset.theme === 'light';
    if (isLight) {
      // Crisp, solid paper-white canvas for Slide 4 polarity inversion
      bgCtx.fillStyle = '#F4F2EC';
      bgCtx.fillRect(0, 0, bw, bh);
    } else {
      bgCtx.fillStyle = 'rgba(5, 6, 8, 0.28)';
      bgCtx.fillRect(0, 0, bw, bh);
    }

    const cx = bw * (0.5 + (mouse.x - 0.5) * 0.08);
    const cy = bh * (0.5 + (mouse.y - 0.5) * 0.08);
    const maxR = Math.min(bw, bh) * 0.52;

    if (isLight) {
      // Slide 4: Supercritical expanding architectural shockwave rings
      for (let i = 0; i < 4; i++) {
        const phase = (time * 0.35 + i * 0.25) % 1;
        const r = phase * Math.max(bw, bh) * 0.75;
        bgCtx.strokeStyle = `rgba(217, 48, 18, ${(1 - phase) * 0.22})`;
        bgCtx.lineWidth = 1.5;
        bgCtx.beginPath();
        bgCtx.arc(cx, cy, r, 0, Math.PI * 2);
        bgCtx.stroke();
      }
    } else {
      // Subtle gravitational accretion glow on Hero (Slide 0) & Finale (Slide 11)
      if (currentIndex === 0 || currentIndex === 11) {
        const gx = currentIndex === 0 ? bw * 0.76 : cx;
        const gy = currentIndex === 0 ? bh * 0.52 : bh * 0.62;
        const grad = bgCtx.createRadialGradient(gx, gy, 10, gx, gy, maxR * 0.95);
        grad.addColorStop(0, 'rgba(255, 90, 31, 0.22)');
        grad.addColorStop(0.35, 'rgba(255, 179, 71, 0.07)');
        grad.addColorStop(0.7, 'rgba(56, 232, 255, 0.03)');
        grad.addColorStop(1, 'transparent');
        bgCtx.fillStyle = grad;
        bgCtx.beginPath();
        bgCtx.arc(gx, gy, maxR * 0.95, 0, Math.PI * 2);
        bgCtx.fill();

        // Event Horizon Black Core
        bgCtx.fillStyle = '#050608';
        bgCtx.beginPath();
        bgCtx.arc(gx, gy, currentIndex === 0 ? 54 : 36, 0, Math.PI * 2);
        bgCtx.fill();

        bgCtx.strokeStyle = 'rgba(255, 179, 71, 0.55)';
        bgCtx.lineWidth = 1.4;
        bgCtx.beginPath();
        bgCtx.arc(gx, gy, currentIndex === 0 ? 55 : 37, 0, Math.PI * 2);
        bgCtx.stroke();
      }

      // Orbital particles adapting speed to slide intensity
      const intensity = currentIndex === 2 && ignited ? 4.2 : currentIndex === 7 || currentIndex === 9 ? 1.9 : 1.0;
      const originX = currentIndex === 0 ? bw * 0.76 : cx;
      const originY = currentIndex === 0 ? bh * 0.52 : cy;

      stars.forEach((s) => {
        s.angle += s.speed * intensity;
        const r = s.dist * Math.max(bw, bh) * 0.62;
        const x = originX + Math.cos(s.angle) * r;
        const y = originY + Math.sin(s.angle) * r * (currentIndex === 0 ? 0.55 : 0.82);

        bgCtx.fillStyle = s.hue === 'warm'
          ? 'rgba(255, 130, 65, 0.55)'
          : 'rgba(120, 225, 255, 0.42)';
        bgCtx.beginPath();
        bgCtx.arc(x, y, s.size, 0, Math.PI * 2);
        bgCtx.fill();
      });
    }

    requestAnimationFrame(animateBackdrop);
  }

  // Initialize
  buildNavigation();
  notesContent.textContent = slides[0].dataset.notes || '';
  animateBackdrop();

  // Deep link support (#slide-4)
  const hashMatch = window.location.hash.match(/^#slide-(\d+)$/);
  if (hashMatch) {
    const idx = Number(hashMatch[1]) - 1;
    if (idx > 0 && idx < totalSlides) goToSlide(idx);
  }
})();
