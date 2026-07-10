// OppTrack FX v6

// ── CURSOR ──
const cr=document.createElement('div'),cd=document.createElement('div');
cr.id='cring';cd.id='cdot';
document.body.appendChild(cr);document.body.appendChild(cd);
let mx=-200,my=-200,rx=-200,ry=-200;
document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY;cd.style.transform=`translate(${mx}px,${my}px)`;});
(function loop(){rx+=(mx-rx)*.11;ry+=(my-ry)*.11;cr.style.transform=`translate(${rx}px,${ry}px)`;requestAnimationFrame(loop);})();
document.addEventListener('mouseover',e=>{if(e.target.closest('a,button,.opp-card,.chip,.exam-card,.cc,.btn-glow,.btn-ghost,.applybtn')){cr.classList.add('big');cd.classList.add('hide');}});
document.addEventListener('mouseout',e=>{if(e.target.closest('a,button,.opp-card,.chip,.exam-card,.cc,.btn-glow,.btn-ghost,.applybtn')){cr.classList.remove('big');cd.classList.remove('hide');}});

// ── TYPEWRITER ──
const tw=document.getElementById('tw');
if(tw){
  const words=['Scholarships','Internships','Hackathons','Competitions','Exam Dates','Counselling','Admissions'];
  let wi=0,ci=0,del=false;
  (function type(){
    const w=words[wi];
    if(!del){tw.textContent=w.slice(0,++ci);if(ci===w.length){del=true;setTimeout(type,2000);return;}setTimeout(type,80);}
    else{tw.textContent=w.slice(0,--ci);if(ci===0){del=false;wi=(wi+1)%words.length;setTimeout(type,300);return;}setTimeout(type,38);}
  })();
}

// ── COUNTER ANIM ──
const animated=new Set();
function animCount(el){
  if(animated.has(el))return;animated.add(el);
  const target=parseInt(el.dataset.count)||0;
  if(!target){el.textContent='0';return;}
  let cur=0;const step=Math.max(1,Math.ceil(target/40));
  const t=setInterval(()=>{cur=Math.min(cur+step,target);el.textContent=cur;if(cur>=target)clearInterval(t);},35);
}

// ── SCROLL REVEAL ──
function reveal(){
  const trigger=window.innerHeight*.91;
  document.querySelectorAll('.reveal,.rev-l,.rev-r').forEach(el=>{
    if(el.getBoundingClientRect().top<trigger)el.classList.add('vis');
  });
  document.querySelectorAll('[data-count]').forEach(el=>{
    if(el.getBoundingClientRect().top<trigger)animCount(el);
  });
}
window.addEventListener('scroll',reveal,{passive:true});
window.addEventListener('load',()=>{reveal();setTimeout(reveal,150);});

// ── HERO PARALLAX ──
const ill=document.getElementById('heroIll');
if(ill){
  document.addEventListener('mousemove',e=>{
    const dx=(e.clientX-window.innerWidth/2)/window.innerWidth;
    const dy=(e.clientY-window.innerHeight/2)/window.innerHeight;
    ill.style.transform=`translate(${dx*24}px,${dy*14}px)`;
  },{passive:true});
}

// ── 3D TILT ──
function applyTilt(card){
  if(card._tilt)return;card._tilt=true;
  card.addEventListener('mousemove',e=>{
    const r=card.getBoundingClientRect();
    const x=e.clientX-r.left,y=e.clientY-r.top;
    const rx2=((y-r.height/2)/r.height)*-12;
    const ry2=((x-r.width/2)/r.width)*12;
    card.style.transform=`perspective(700px) rotateX(${rx2}deg) rotateY(${ry2}deg) translateY(-5px) scale(1.018)`;
    let s=card.querySelector('.card-shine');
    if(!s){s=document.createElement('div');s.className='card-shine';card.appendChild(s);}
    s.style.cssText=`position:absolute;inset:0;border-radius:inherit;pointer-events:none;z-index:2;opacity:1;background:radial-gradient(circle at ${x}px ${y}px,rgba(255,255,255,.08) 0%,transparent 65%)`;
  });
  card.addEventListener('mouseleave',()=>{
    card.style.transform='';
    const s=card.querySelector('.card-shine');if(s)s.style.opacity='0';
  });
}
function initTilt(){document.querySelectorAll('.opp-card,.exam-card,.stat-card').forEach(applyTilt);}
window.addEventListener('load',initTilt);

// ── RIPPLE ──
document.addEventListener('click',e=>{
  const btn=e.target.closest('.btn,.chip,.btn-glow,.btn-ghost,.applybtn,.btn-primary');
  if(!btn)return;
  const r=document.createElement('span');r.className='ripple';
  const rect=btn.getBoundingClientRect(),size=Math.max(rect.width,rect.height)*2;
  r.style.cssText=`width:${size}px;height:${size}px;left:${e.clientX-rect.left-size/2}px;top:${e.clientY-rect.top-size/2}px`;
  btn.style.position='relative';btn.style.overflow='hidden';
  btn.appendChild(r);setTimeout(()=>r.remove(),600);
});

// ── NAVBAR ──
const nav=document.querySelector('.navbar');
window.addEventListener('scroll',()=>{
  nav.style.background=window.scrollY>60?'rgba(1,2,8,.97)':'rgba(2,4,10,.65)';
},{passive:true});

// ── SEARCH ──
const si=document.querySelector('.sinput');
if(si){let t;si.addEventListener('input',()=>{clearTimeout(t);t=setTimeout(()=>si.closest('form').submit(),600);});}

// ── SAVE ──
async function toggleSave(id,btn){
  const d=await(await fetch(`/save/${id}`,{method:'POST'})).json();
  if(d.status==='login_required'){window.location.href='/login';return;}
  btn.classList.toggle('saved',d.saved);
  btn.querySelector('i').className=d.saved?'bi bi-bookmark-fill':'bi bi-bookmark';
}
