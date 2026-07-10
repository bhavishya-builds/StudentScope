// OppTrack — Technical Background Engine
(function(){
  const canvas = document.createElement('canvas');
  canvas.id = 'techCanvas';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:1';
  document.body.prepend(canvas);

  const ctx = canvas.getContext('2d');
  let W, H;

  function resize(){
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize, {passive:true});

  // ── COLOUR PALETTE ──────────────────────────────────
  const C = {
    bg:     '#030008',
    grid:   'rgba(120,0,255,0.06)',
    line:   'rgba(0,220,255,0.12)',
    node:   'rgba(0,220,255,0.55)',
    pulse:  'rgba(0,220,255,0.9)',
    pink:   'rgba(255,0,180,0.5)',
    pinkD:  'rgba(255,0,180,0.15)',
    binary: 'rgba(0,220,255,0.18)',
    data:   'rgba(180,0,255,0.22)',
    // tabbg aliases (mapped in applyPalette)
    accent: 'rgba(255,0,180,0.50)',
    accentD:'rgba(255,0,180,0.15)',
  };
  // Expose to tabbg.js for runtime palette swapping
  window.TC_PALETTE = C;

  // ── GRID ─────────────────────────────────────────────
  const CELL = 60;

  function drawGrid(){
    ctx.strokeStyle = C.grid;
    ctx.lineWidth   = 0.4;
    for(let x=0;x<=W;x+=CELL){ ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke(); }
    for(let y=0;y<=H;y+=CELL){ ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke(); }
  }

  // ── CIRCUIT TRACES ───────────────────────────────────
  const traces = [];
  function genTraces(){
    traces.length = 0;
    const count = Math.floor((W*H)/(200*200));
    for(let i=0;i<count;i++){
      const sx = Math.round(Math.random()*(W/CELL))*CELL;
      const sy = Math.round(Math.random()*(H/CELL))*CELL;
      const segs = [];
      let cx=sx, cy=sy, dir=Math.floor(Math.random()*4);
      for(let s=0;s<6+Math.floor(Math.random()*6);s++){
        const len = (1+Math.floor(Math.random()*4))*CELL;
        let nx=cx, ny=cy;
        if(dir===0) nx+=len;
        else if(dir===1) nx-=len;
        else if(dir===2) ny+=len;
        else ny-=len;
        if(nx>=0&&nx<=W&&ny>=0&&ny<=H){ segs.push({x1:cx,y1:cy,x2:nx,y2:ny}); cx=nx; cy=ny; }
        dir=(dir+[1,3][Math.floor(Math.random()*2)])%4;
      }
      if(segs.length>1) traces.push({segs, nodes:[[sx,sy],[cx,cy]], prog:0, speed:0.003+Math.random()*0.004, pink:Math.random()<0.25});
    }
  }
  genTraces();
  window.addEventListener('resize',genTraces,{passive:true});

  function drawTraces(t){
    traces.forEach(tr=>{
      tr.prog = (tr.prog + tr.speed)%1;
      const col  = tr.pink ? C.accentD : C.line;
      const pcol = tr.pink ? C.accent  : C.pulse;
      // draw all segments
      ctx.strokeStyle=col; ctx.lineWidth=0.8;
      tr.segs.forEach(s=>{ ctx.beginPath();ctx.moveTo(s.x1,s.y1);ctx.lineTo(s.x2,s.y2);ctx.stroke(); });
      // draw nodes
      tr.nodes.forEach(([nx,ny])=>{
        ctx.fillStyle=tr.pink?C.pink:C.node;
        ctx.beginPath();ctx.arc(nx,ny,2.5,0,Math.PI*2);ctx.fill();
      });
      // animated pulse dot
      const total = tr.segs.reduce((a,s)=>a+Math.hypot(s.x2-s.x1,s.y2-s.y1),0);
      let dist = tr.prog*total, rem=dist;
      for(const s of tr.segs){
        const len=Math.hypot(s.x2-s.x1,s.y2-s.y1);
        if(rem<=len){
          const px=s.x1+(s.x2-s.x1)*(rem/len);
          const py=s.y1+(s.y2-s.y1)*(rem/len);
          ctx.fillStyle=pcol;
          ctx.beginPath();ctx.arc(px,py,3,0,Math.PI*2);ctx.fill();
          // glow
          const g=ctx.createRadialGradient(px,py,0,px,py,12);
          g.addColorStop(0,tr.pink?'rgba(255,0,180,0.5)':'rgba(0,220,255,0.5)');
          g.addColorStop(1,'rgba(0,0,0,0)');
          ctx.fillStyle=g;
          ctx.beginPath();ctx.arc(px,py,12,0,Math.PI*2);ctx.fill();
          break;
        }
        rem-=len;
      }
    });
  }

  // ── FLOATING BINARY / HEX ───────────────────────────
  const chars = '01░▒▓╔╗╚╝║═╠╣╦╩╬01010110010101100101011001';
  const drops = Array.from({length: Math.floor(W/45)}, ()=>({
    x: Math.random()*W,
    y: Math.random()*H,
    speed: 0.3+Math.random()*0.5,
    opacity: 0.08+Math.random()*0.12,
    char: chars[Math.floor(Math.random()*chars.length)],
    timer: 0,
    interval: 40+Math.floor(Math.random()*120),
  }));

  function drawBinary(){
    ctx.font = '11px monospace';
    drops.forEach(d=>{
      d.timer++;
      if(d.timer>d.interval){ d.char=chars[Math.floor(Math.random()*chars.length)]; d.timer=0; }
      d.y+=d.speed;
      if(d.y>H){ d.y=-20; d.x=Math.random()*W; }
      ctx.fillStyle=`rgba(0,220,255,${d.opacity})`;
      ctx.fillText(d.char, d.x, d.y);
    });
  }

  // ── SCAN LINE ────────────────────────────────────────
  let scanY = 0;
  function drawScan(){
    scanY = (scanY+0.8)%H;
    const g=ctx.createLinearGradient(0,scanY-30,0,scanY+30);
    g.addColorStop(0,'rgba(0,220,255,0)');
    g.addColorStop(0.5,'rgba(0,220,255,0.03)');
    g.addColorStop(1,'rgba(0,220,255,0)');
    ctx.fillStyle=g;
    ctx.fillRect(0,scanY-30,W,60);
  }

  // ── CORNER BRACKETS ─────────────────────────────────
  function drawBrackets(){
    const s=40, lw=1.5;
    ctx.strokeStyle='rgba(0,220,255,0.25)';
    ctx.lineWidth=lw;
    // top-left
    ctx.beginPath();ctx.moveTo(s,10);ctx.lineTo(10,10);ctx.lineTo(10,s);ctx.stroke();
    // top-right
    ctx.beginPath();ctx.moveTo(W-s,10);ctx.lineTo(W-10,10);ctx.lineTo(W-10,s);ctx.stroke();
    // bottom-left
    ctx.beginPath();ctx.moveTo(s,H-10);ctx.lineTo(10,H-10);ctx.lineTo(10,H-s);ctx.stroke();
    // bottom-right
    ctx.beginPath();ctx.moveTo(W-s,H-10);ctx.lineTo(W-10,H-10);ctx.lineTo(W-10,H-s);ctx.stroke();

    // HUD text
    ctx.fillStyle='rgba(0,220,255,0.3)';
    ctx.font='9px monospace';
    ctx.fillText('OppTrack v1.0 // LIVE', 18, 22);
    ctx.fillText(`SYS:${new Date().toLocaleTimeString()}`, W-115, 22);
    ctx.fillText('STUDENT_HUB_ACTIVE', 18, H-14);
    ctx.fillText('INDIA_EDU_NET:OK', W-120, H-14);
  }

  // ── DATA PACKETS (small squares moving along traces) ─
  function drawDataPackets(){
    // small square overlays at random trace nodes
    traces.filter((_,i)=>i%4===0).forEach(tr=>{
      if(!tr.nodes.length) return;
      const [nx,ny] = tr.nodes[0];
      const b=Math.sin(Date.now()*0.003+nx)*0.5+0.5;
      ctx.strokeStyle=`rgba(180,0,255,${0.15+b*0.25})`;
      ctx.lineWidth=0.8;
      ctx.strokeRect(nx-5,ny-5,10,10);
    });
  }

  // ── MAIN LOOP ────────────────────────────────────────
  function draw(){
    ctx.clearRect(0,0,W,H);
    // deep bg
    ctx.fillStyle=C.bg;
    ctx.fillRect(0,0,W,H);

    drawGrid();
    drawTraces();
    drawBinary();
    drawScan();
    drawDataPackets();
    drawBrackets();

    requestAnimationFrame(draw);
  }
  draw();
})();
