/* ═══════════════════════════════════════════════════════════════
   ModalitiesQuant — script.js
   ═══════════════════════════════════════════════════════════════ */

"use strict";

// ── Navbar scroll effect ──────────────────────────────────────────────────────
const nav = document.getElementById("nav");
window.addEventListener("scroll", () => {
  nav.classList.toggle("scrolled", window.scrollY > 40);
});

// ── Mobile burger ─────────────────────────────────────────────────────────────
const burger = document.getElementById("navBurger");
const navLinks = document.querySelector(".nav-links");
burger.addEventListener("click", () => {
  navLinks.classList.toggle("open");
});
navLinks.querySelectorAll("a").forEach(a =>
  a.addEventListener("click", () => navLinks.classList.remove("open"))
);

// ── Scroll reveal ─────────────────────────────────────────────────────────────
const revealEls = () => {
  document.querySelectorAll(
    ".feat-card, .pipe-step, .tech-item, .tab-pane, .dl-card, .bridge-node"
  ).forEach(el => el.classList.add("reveal"));

  const io = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        io.unobserve(e.target);
      }
    }),
    { threshold: 0.12 }
  );
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));
};
document.addEventListener("DOMContentLoaded", revealEls);

// ── Tab switcher ──────────────────────────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    const el = document.getElementById(`tab-${target}`);
    if (el) el.classList.add("active");
  });
});

// ── Hero canvas — animated topological network ────────────────────────────────
(function initHeroCanvas() {
  const canvas = document.getElementById("heroCanvas");
  if (!canvas) return;
  const ctx    = canvas.getContext("2d");
  let W, H, nodes, edges, frame;

  const PALETTE = ["#1e88e5", "#00c6ff", "#00e676", "#ffa726", "#ef5350"];
  const NODE_COUNT = 55;
  const EDGE_DIST  = 160;

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
    build();
  }

  function build() {
    nodes = Array.from({ length: NODE_COUNT }, () => ({
      x:  Math.random() * W,
      y:  Math.random() * H,
      vx: (Math.random() - .5) * .35,
      vy: (Math.random() - .5) * .35,
      r:  Math.random() * 2.5 + 1,
      col: PALETTE[Math.floor(Math.random() * PALETTE.length)],
      pulse: Math.random() * Math.PI * 2,
    }));
  }

  function buildEdges() {
    edges = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < EDGE_DIST) edges.push({ i, j, d });
      }
    }
  }

  function tick() {
    nodes.forEach(n => {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
      n.pulse += 0.02;
    });
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    buildEdges();

    // edges
    edges.forEach(({ i, j, d }) => {
      const alpha = (1 - d / EDGE_DIST) * 0.35;
      const ni = nodes[i], nj = nodes[j];
      const grad = ctx.createLinearGradient(ni.x, ni.y, nj.x, nj.y);
      grad.addColorStop(0, ni.col + Math.floor(alpha * 255).toString(16).padStart(2,"0"));
      grad.addColorStop(1, nj.col + Math.floor(alpha * 255).toString(16).padStart(2,"0"));
      ctx.beginPath();
      ctx.moveTo(ni.x, ni.y);
      ctx.lineTo(nj.x, nj.y);
      ctx.strokeStyle = grad;
      ctx.lineWidth = .7;
      ctx.stroke();
    });

    // 2-simplices (shaded triangles for TDA feel)
    for (let k = 0; k < edges.length; k++) {
      const e1 = edges[k];
      for (let m = k + 1; m < edges.length; m++) {
        const e2 = edges[m];
        let shared = -1, a = -1, b = -1;
        if (e1.i === e2.i) { shared = e1.i; a = e1.j; b = e2.j; }
        else if (e1.i === e2.j) { shared = e1.i; a = e1.j; b = e2.i; }
        else if (e1.j === e2.i) { shared = e1.j; a = e1.i; b = e2.j; }
        else if (e1.j === e2.j) { shared = e1.j; a = e1.i; b = e2.i; }
        if (shared === -1) continue;
        const dx = nodes[a].x - nodes[b].x;
        const dy = nodes[a].y - nodes[b].y;
        if (Math.sqrt(dx*dx+dy*dy) < EDGE_DIST) {
          ctx.beginPath();
          ctx.moveTo(nodes[shared].x, nodes[shared].y);
          ctx.lineTo(nodes[a].x, nodes[a].y);
          ctx.lineTo(nodes[b].x, nodes[b].y);
          ctx.closePath();
          ctx.fillStyle = nodes[shared].col + "0d";
          ctx.fill();
        }
      }
    }

    // nodes
    nodes.forEach(n => {
      const pulse = Math.sin(n.pulse) * .5 + .5;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r + pulse * .8, 0, Math.PI * 2);
      ctx.fillStyle = n.col;
      ctx.shadowColor = n.col;
      ctx.shadowBlur  = 8 * pulse;
      ctx.fill();
      ctx.shadowBlur = 0;
    });
  }

  function loop() {
    tick();
    draw();
    frame = requestAnimationFrame(loop);
  }

  window.addEventListener("resize", () => {
    cancelAnimationFrame(frame);
    resize();
    loop();
  });

  resize();
  loop();
})();

// ── TDA visualisation in bio tab ──────────────────────────────────────────────
(function initTdaViz() {
  const el = document.getElementById("tdaViz");
  if (!el) return;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  svg.style.position = "absolute";
  svg.style.inset     = "0";
  el.appendChild(svg);

  const pts = Array.from({ length: 28 }, (_, i) => {
    const a = (i / 28) * Math.PI * 2;
    const r = 38 + Math.sin(i * 1.3) * 14;
    return {
      x: 160 + Math.cos(a) * r + (Math.random() - .5) * 18,
      y: 60  + Math.sin(a) * r + (Math.random() - .5) * 18,
    };
  });

  // edges
  pts.forEach((p, i) => {
    const j = (i + 1) % pts.length;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", p.x); line.setAttribute("y1", p.y);
    line.setAttribute("x2", pts[j].x); line.setAttribute("y2", pts[j].y);
    line.setAttribute("stroke", "#1e88e530");
    line.setAttribute("stroke-width", "1");
    svg.appendChild(line);
    if (Math.random() > .6) {
      const k = (i + 3) % pts.length;
      const l2 = document.createElementNS("http://www.w3.org/2000/svg", "line");
      l2.setAttribute("x1", p.x); l2.setAttribute("y1", p.y);
      l2.setAttribute("x2", pts[k].x); l2.setAttribute("y2", pts[k].y);
      l2.setAttribute("stroke", "#00c6ff20");
      l2.setAttribute("stroke-width", "1");
      svg.appendChild(l2);
    }
  });

  // points
  pts.forEach((p, i) => {
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c.setAttribute("cx", p.x);
    c.setAttribute("cy", p.y);
    c.setAttribute("r", 3);
    c.setAttribute("fill", i % 5 === 0 ? "#00e676" : i % 3 === 0 ? "#ffa726" : "#1e88e5");
    svg.appendChild(c);
  });
})();

// ── Bridge node activation animation ─────────────────────────────────────────
(function animateBridge() {
  const nodes = document.querySelectorAll(".bridge-node");
  let idx = 0;
  setInterval(() => {
    nodes.forEach(n => n.classList.remove("active"));
    nodes[idx % nodes.length].classList.add("active");
    idx++;
  }, 1200);
})();

// ── Counter animation on hero stats ──────────────────────────────────────────
function animateCounter(el, target, suffix = "") {
  const start = 0;
  const duration = 1400;
  const startTime = performance.now();
  const isInfinity = target === Infinity;
  if (isInfinity) { el.textContent = "∞"; return; }
  const step = ts => {
    const p = Math.min((ts - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(start + (target - start) * ease) + suffix;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

const statsObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const nums = document.querySelectorAll(".stat-num");
    const targets = [8, 58, 75, Infinity];
    nums.forEach((el, i) => animateCounter(el, targets[i], targets[i] === 75 ? "+" : ""));
    statsObserver.disconnect();
  });
}, { threshold: .5 });
const statsSection = document.querySelector(".hero-stats");
if (statsSection) statsObserver.observe(statsSection);

// ── Signal box cycling ────────────────────────────────────────────────────────
(function cycleSignal() {
  const box = document.getElementById("signalBox");
  if (!box) return;
  const signals = [
    { text: "STRONG BUY",  color: "#00e676", bg: "linear-gradient(135deg,#0a4a1a,#00e67640)" },
    { text: "BUY",         color: "#66bb6a", bg: "linear-gradient(135deg,#0a3020,#66bb6a30)" },
    { text: "HOLD",        color: "#ffa726", bg: "linear-gradient(135deg,#2a1a00,#ffa72630)" },
    { text: "SELL",        color: "#ef5350", bg: "linear-gradient(135deg,#3a0a0a,#ef535030)" },
    { text: "STRONG SELL", color: "#b71c1c", bg: "linear-gradient(135deg,#4a0a0a,#b71c1c30)" },
  ];
  let i = 0;
  setInterval(() => {
    i = (i + 1) % signals.length;
    const s = signals[i];
    box.textContent = s.text;
    box.style.background = s.bg;
    box.style.borderColor = s.color + "55";
    box.style.color = s.color;
  }, 2500);
})();


// _triggerDownload() lived here to fetch the installer through a blob, because
// the download URL was a one-time token the page held. The download is a plain
// link to a published release now, so the browser handles it — and a 194 MB
// fetch-into-memory was never a good way to serve it anyway.

// The site used to hand out a launch_native.bat that pip-installed the
// dependencies and ran app_native.py from source. That predates the
// packaged build: customers now download a self-contained zip, and the
// generator had already been unreachable from the page. Removed rather
// than left dormant — running from source honours the MQ_ACTIVATION_PUBLIC_KEY
// environment override, which a shipped build deliberately ignores.

// The licence gate that used to live here posted the buyer's key to a
// server, which returned a single-use download link. There is no server
// now: the download is public and the licence is verified inside the
// application against a key compiled into the binary. Downloading it
// without a licence gets you a program that asks for one.

// ── Skill bar animation on scroll into view ───────────────────────────────────
(function initSkillBars() {
  const bars = document.querySelectorAll(".skill-bar-fill");
  if (!bars.length) return;
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add("animate");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.3 });
  bars.forEach(b => io.observe(b));
})();

// ── Plan card reveal ──────────────────────────────────────────────────────────
document.querySelectorAll(".plan-card").forEach(el => el.classList.add("reveal"));

// ── Smooth scroll for anchor links ────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener("click", e => {
    const id = a.getAttribute("href").slice(1);
    const el = document.getElementById(id);
    if (!el) return;
    e.preventDefault();
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
