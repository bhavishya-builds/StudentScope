// Floating particles background
(function() {
  const canvas = document.createElement('canvas');
  canvas.id = 'particleCanvas';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:0.45';
  document.body.prepend(canvas);

  const ctx = canvas.getContext('2d');
  let W = canvas.width = window.innerWidth;
  let H = canvas.height = window.innerHeight;

  const particles = Array.from({length: 70}, () => ({
    x: Math.random() * W, y: Math.random() * H,
    r: Math.random() * 1.8 + 0.4,
    dx: (Math.random() - 0.5) * 0.35,
    dy: (Math.random() - 0.5) * 0.35,
    color: ['#4fa3f7','#a78bfa','#5ddbb4','#fbbf24'][Math.floor(Math.random()*4)],
    alpha: Math.random() * 0.6 + 0.2
  }));

  // Connection lines between nearby particles
  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
    });

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i+1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = '#4fa3f7';
          ctx.globalAlpha = (1 - dist/120) * 0.12;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  draw();
  window.addEventListener('resize', () => {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }, { passive: true });
})();
