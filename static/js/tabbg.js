/**
 * OppTrack — Tab Background Engine v2
 * Uses direct DOM injection for distinct, visible backgrounds per tab.
 * No canvas dependency — works immediately and reliably.
 */
(function () {

  // Create the bg layer div (sits between canvas and content)
  const bgLayer = document.createElement('div');
  bgLayer.id = 'tab-bg-layer';
  bgLayer.style.cssText = [
    'position:fixed', 'inset:0', 'z-index:0', 'pointer-events:none',
    'transition:opacity 0.7s ease, background 0.7s ease',
    'opacity:1',
  ].join(';');
  document.body.appendChild(bgLayer);

  // Create particle overlay canvas for extra per-tab particles
  const overlay = document.createElement('canvas');
  overlay.id = 'tab-overlay-canvas';
  overlay.style.cssText = [
    'position:fixed', 'inset:0', 'z-index:0', 'pointer-events:none',
    'transition:opacity 0.6s ease',
    'z-index:1',
  ].join(';');
  document.body.appendChild(overlay);

  const octx = overlay.getContext('2d');
  let OW, OH;
  function resizeOverlay() {
    OW = overlay.width  = window.innerWidth;
    OH = overlay.height = window.innerHeight;
  }
  resizeOverlay();
  window.addEventListener('resize', resizeOverlay, { passive: true });

  // ── Per-tab config ──────────────────────────────────────────
  const TABS = {
    opps: {
      // Warm green-gold gradient body background
      bodyBg: 'radial-gradient(ellipse 120% 60% at 50% -10%, rgba(0,80,0,0.55) 0%, rgba(3,0,8,1) 55%), radial-gradient(ellipse 60% 40% at 80% 80%, rgba(80,50,0,0.30) 0%, transparent 60%), #030008',
      // Overlay gradient on bgLayer
      layerBg: 'radial-gradient(ellipse 90% 50% at 20% 50%, rgba(0,255,100,0.07) 0%, transparent 60%), radial-gradient(ellipse 70% 60% at 80% 20%, rgba(255,184,0,0.06) 0%, transparent 55%)',
      // Navbar tint
      navBorder: 'rgba(0,255,136,0.18)',
      navBg: 'rgba(0,10,3,0.82)',
      // Particle colour for overlay canvas
      particleColor: '0,255,136',
      particleGlow: '255,184,0',
      // Tab bar active underline colour
      tabUnderline: '#00ff88',
      // Body class
      cls: 'tab-bg-opps',
    },
    exams: {
      // Deep blue-violet gradient body background
      bodyBg: 'radial-gradient(ellipse 120% 60% at 50% -10%, rgba(0,0,120,0.60) 0%, rgba(2,0,16,1) 55%), radial-gradient(ellipse 60% 40% at 20% 80%, rgba(80,0,120,0.30) 0%, transparent 60%), #020010',
      layerBg: 'radial-gradient(ellipse 90% 50% at 80% 50%, rgba(0,100,255,0.09) 0%, transparent 60%), radial-gradient(ellipse 70% 60% at 20% 20%, rgba(150,0,255,0.08) 0%, transparent 55%)',
      navBorder: 'rgba(0,212,255,0.22)',
      navBg: 'rgba(2,0,16,0.85)',
      particleColor: '0,180,255',
      particleGlow: '180,0,255',
      tabUnderline: '#00d4ff',
      cls: 'tab-bg-exams',
    },
  };

  // ── Floating particles for overlay ─────────────────────────
  let particles = [];
  let currentConfig = TABS.opps;
  let animFrame;

  function spawnParticles(cfg) {
    particles = [];
    const count = Math.min(40, Math.floor((OW * OH) / 28000));
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * OW,
        y: Math.random() * OH,
        r: 1 + Math.random() * 2.5,
        vx: (Math.random() - 0.5) * 0.4,
        vy: -(0.2 + Math.random() * 0.5),
        alpha: 0.1 + Math.random() * 0.5,
        life: Math.random(),
        maxLife: 0.005 + Math.random() * 0.008,
        glow: Math.random() > 0.5,
      });
    }
  }

  function drawOverlay() {
    octx.clearRect(0, 0, OW, OH);
    const pc = currentConfig.particleColor;
    const pg = currentConfig.particleGlow;

    particles.forEach((p, i) => {
      // Move
      p.x += p.vx;
      p.y += p.vy;
      p.life += p.maxLife;

      // Reset if off screen or life done
      if (p.y < -10 || p.x < -10 || p.x > OW + 10 || p.life > 1) {
        p.x = Math.random() * OW;
        p.y = OH + 5;
        p.life = 0;
      }

      const fade = p.life < 0.2 ? p.life / 0.2 : p.life > 0.8 ? (1 - p.life) / 0.2 : 1;
      const a = p.alpha * fade;
      if (a < 0.01) return;

      if (p.glow) {
        // Glowing orb
        const grad = octx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
        grad.addColorStop(0,   `rgba(${pg},${(a * 0.9).toFixed(3)})`);
        grad.addColorStop(0.4, `rgba(${pc},${(a * 0.4).toFixed(3)})`);
        grad.addColorStop(1,   `rgba(${pc},0)`);
        octx.beginPath();
        octx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
        octx.fillStyle = grad;
        octx.fill();
      } else {
        octx.beginPath();
        octx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        octx.fillStyle = `rgba(${pc},${a.toFixed(3)})`;
        octx.fill();
      }
    });

    animFrame = requestAnimationFrame(drawOverlay);
  }

  // ── Apply a tab config ──────────────────────────────────────
  function applyTab(name) {
    const cfg = TABS[name] || TABS.opps;
    currentConfig = cfg;

    // 1. Body gradient background
    document.body.style.background = cfg.bodyBg;

    // 2. BgLayer overlay gradients
    bgLayer.style.background = cfg.layerBg;

    // 3. Navbar tint
    const nav = document.querySelector('.navbar');
    if (nav) {
      nav.style.background = cfg.navBg;
      nav.style.borderBottomColor = cfg.navBorder;
    }

    // 4. Active tab underline colour
    document.documentElement.style.setProperty('--tab-active-color', cfg.tabUnderline);

    // 5. Body class swap
    document.body.classList.remove('tab-bg-opps', 'tab-bg-exams');
    document.body.classList.add(cfg.cls);

    // 6. Re-spawn overlay particles for this palette
    spawnParticles(cfg);
  }

  // ── Public API ──────────────────────────────────────────────
  window.setTabPalette = applyTab;

  // ── Init on DOM ready ───────────────────────────────────────
  function init() {
    spawnParticles(TABS.opps);
    drawOverlay();
    applyTab('opps');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
