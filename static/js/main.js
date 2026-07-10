// OppTrack — main.js

// ── SAVE / UNSAVE ─────────────────────────────────────────
async function toggleSave(oppId, btn) {
  const resp = await fetch(`/save/${oppId}`, { method: 'POST' });
  const data = await resp.json();
  if (data.status === 'login_required') { window.location.href = '/login'; return; }
  const icon = btn.querySelector('i');
  if (data.saved) {
    btn.classList.add('saved');
    icon.className = 'bi bi-bookmark-fill';
  } else {
    btn.classList.remove('saved');
    icon.className = 'bi bi-bookmark';
  }
}

// ── SEARCH DEBOUNCE ───────────────────────────────────────
const searchInput = document.querySelector('.search-input');
if (searchInput) {
  let timer;
  searchInput.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => searchInput.closest('form').submit(), 600);
  });
}

// ── SCROLL REVEAL ─────────────────────────────────────────
function revealOnScroll() {
  const els = document.querySelectorAll('.reveal');
  const trigger = window.innerHeight * 0.92;
  els.forEach(el => {
    const top = el.getBoundingClientRect().top;
    if (top < trigger) el.classList.add('visible');
  });
}

// Run on load (for above-fold elements) + scroll
window.addEventListener('scroll', revealOnScroll, { passive: true });
window.addEventListener('load', () => {
  revealOnScroll();
  // Small delay so animations fire nicely after page load
  setTimeout(revealOnScroll, 100);
});

// ── SMOOTH SCROLL for anchor links ───────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// ── NAVBAR scroll effect ──────────────────────────────────
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 40) {
    navbar.style.background = 'rgba(10,18,30,0.92)';
  } else {
    navbar.style.background = 'rgba(15,27,45,0.75)';
  }
}, { passive: true });
