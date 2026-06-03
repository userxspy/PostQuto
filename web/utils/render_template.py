import urllib.parse
import html
import logging
import gc
from info import BIN_CHANNEL, URL
from utils import temp

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# 🎬 FAST FINDER — NEXT LEVEL CINEMATIC PLAYER TEMPLATE
# Dark / Light Mode | Progressive Skip | Native Share
# ─────────────────────────────────────────────────────────
watch_tmplt = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{heading}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#060608; --surface:#0a0a0c; --sb:rgba(255,255,255,.06);
  --txt:#ffffff; --txt-m:rgba(255,255,255,.45); --txt-d:rgba(255,255,255,.25);
  --nav:rgba(6,6,8,.98); --pill:rgba(255,255,255,.06); --pill-b:rgba(255,255,255,.1);
  --btn:rgba(255,255,255,.07); --btn-b:rgba(255,255,255,.1); --sep:rgba(255,255,255,.06);
  --tog:rgba(255,255,255,.08); --tog-b:rgba(255,255,255,.12); --tog-c:rgba(255,255,255,.7);
  --b1:rgba(229,9,20,.12); --b2:rgba(120,40,200,.08);
}}
html.light{{
  --bg:#f0f2f5; --surface:#ffffff; --sb:rgba(0,0,0,.08);
  --txt:#111111; --txt-m:rgba(0,0,0,.5); --txt-d:rgba(0,0,0,.3);
  --nav:rgba(240,242,245,.97); --pill:rgba(0,0,0,.05); --pill-b:rgba(0,0,0,.1);
  --btn:rgba(0,0,0,.05); --btn-b:rgba(0,0,0,.1); --sep:rgba(0,0,0,.07);
  --tog:rgba(0,0,0,.07); --tog-b:rgba(0,0,0,.12); --tog-c:rgba(0,0,0,.6);
  --b1:rgba(229,9,20,.07); --b2:rgba(120,40,200,.04);
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--txt);font-family:'Inter',sans-serif;min-height:100vh;overflow-x:hidden;transition:background .35s,color .35s;}}

/* Blobs */
.blob{{position:fixed;border-radius:50%;pointer-events:none;z-index:0;}}
.b1{{top:-10%;left:-10%;width:600px;height:600px;background:radial-gradient(circle,var(--b1),transparent 70%);animation:pulse 4s ease-in-out infinite;}}
.b2{{top:40%;right:-15%;width:500px;height:500px;background:radial-gradient(circle,var(--b2),transparent 70%);}}
@keyframes pulse{{0%,100%{{transform:scale(1);opacity:.8;}}50%{{transform:scale(1.08);opacity:1;}}}}

/* Navbar */
.navbar{{
  position:fixed;top:0;left:0;right:0;z-index:99;
  display:flex;align-items:center;justify-content:space-between;
  padding:14px 5%;
  background:linear-gradient(to bottom,var(--nav) 0%,transparent 100%);
  backdrop-filter:blur(10px);transition:background .35s;
}}
.logo{{display:flex;align-items:center;gap:10px;text-decoration:none;}}
.logo-icon{{
  width:36px;height:36px;border-radius:9px;
  background:linear-gradient(135deg,#e50914,#c40812);
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 20px rgba(229,9,20,.45);
  transition:transform .2s,box-shadow .2s;
}}
.logo:hover .logo-icon{{transform:scale(1.07);box-shadow:0 0 28px rgba(229,9,20,.6);}}
.logo-icon svg{{width:16px;height:16px;fill:#fff;}}
.logo-text{{font-size:18px;font-weight:800;letter-spacing:.5px;}}
.logo-text .w{{color:var(--txt);transition:color .35s;}}
.logo-text .r{{color:#e50914;}}
.nav-right{{display:flex;align-items:center;gap:10px;}}
.nav-badge{{
  display:flex;align-items:center;gap:6px;
  background:var(--pill);border:1px solid var(--pill-b);
  border-radius:999px;padding:6px 14px;
  font-size:12px;font-weight:600;color:var(--txt-m);
  transition:background .35s,border-color .35s,color .35s;
}}
.nav-dot{{width:7px;height:7px;border-radius:50%;background:#4ade80;animation:blink 2s ease-in-out infinite;}}
.theme-toggle{{
  width:40px;height:40px;border-radius:50%;
  background:var(--tog);border:1px solid var(--tog-b);
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  color:var(--tog-c);transition:background .3s,border-color .3s,transform .2s;
}}
.theme-toggle:hover{{background:var(--btn);transform:scale(1.1);}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.4;}}}}

/* Layout */
.wrap{{position:relative;z-index:1;max-width:1160px;margin:0 auto;padding:86px 20px 40px;}}

/* Player */
.player-box{{
  position:relative;border-radius:18px;overflow:hidden;
  background:var(--surface);
  box-shadow:0 0 0 1px var(--sb),0 40px 80px rgba(0,0,0,.6),0 0 60px rgba(229,9,20,.06);
  transition:background .35s,box-shadow .35s;
}}
.cinema-bar{{height:3px;background:linear-gradient(to right,#c40812,#e50914,#ff6b35);}}
video{{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;cursor:pointer;}}

/* Controls overlay */
.ctrl-overlay{{
  position:absolute;inset:0;z-index:10;
  display:flex;flex-direction:column;justify-content:space-between;
  background:linear-gradient(to top,rgba(0,0,0,.85) 0%,transparent 40%,rgba(0,0,0,.15) 100%);
  opacity:1;transition:opacity .3s;
}}
.ctrl-overlay.hidden{{opacity:0;}}

/* Top controls */
.ctrl-top{{display:flex;align-items:center;justify-content:space-between;padding:18px 20px 0;}}
.live-badge{{
  display:flex;align-items:center;gap:7px;
  background:rgba(0,0,0,.5);backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.1);
  border-radius:999px;padding:6px 14px;
  font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#fff;
}}
.live-dot{{width:7px;height:7px;border-radius:50%;background:#e50914;animation:blink 1.5s ease-in-out infinite;}}
.skip-btns{{display:flex;gap:8px;}}
.skip-btn{{
  width:34px;height:34px;border-radius:50%;
  background:rgba(0,0,0,.45);backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.1);
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;transition:background .2s,transform .1s;
}}
.skip-btn:hover{{background:rgba(255,255,255,.12);}}
.skip-btn:active{{transform:scale(.9);}}
.skip-btn svg{{width:14px;height:14px;fill:#fff;}}

/* Center play */
.ctrl-center{{display:flex;justify-content:center;}}
.play-btn{{
  width:64px;height:64px;border-radius:50%;border:none;
  background:rgba(229,9,20,.92);
  box-shadow:0 0 40px rgba(229,9,20,.55),0 0 80px rgba(229,9,20,.2);
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;transition:transform .2s,box-shadow .2s;
}}
.play-btn:hover{{transform:scale(1.1);box-shadow:0 0 50px rgba(229,9,20,.7);}}
.play-btn:active{{transform:scale(.95);}}
.play-btn svg{{width:26px;height:26px;fill:#fff;}}

/* Bottom controls */
.ctrl-bottom{{padding:0 18px 16px;}}
.progress-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}
.time{{font-size:11px;font-weight:600;color:rgba(255,255,255,.55);min-width:36px;font-variant-numeric:tabular-nums;}}
.time.r{{text-align:right;}}
.pbar{{flex:1;height:5px;border-radius:5px;background:rgba(255,255,255,.15);cursor:pointer;overflow:hidden;}}
.pfill{{height:100%;border-radius:5px;background:linear-gradient(to right,#e50914,#ff6b35);transition:width .1s linear;pointer-events:none;}}
.vol-row{{display:flex;align-items:center;justify-content:space-between;}}
.vol-left{{display:flex;align-items:center;gap:8px;}}
.mute-btn{{background:none;border:none;cursor:pointer;padding:4px;display:flex;transition:opacity .2s;}}
.mute-btn:hover{{opacity:.7;}}
.mute-btn svg{{width:18px;height:18px;fill:rgba(255,255,255,.55);}}
input[type=range].vol{{-webkit-appearance:none;width:80px;height:4px;border-radius:4px;background:rgba(255,255,255,.18);cursor:pointer;}}
input[type=range].vol::-webkit-slider-thumb{{-webkit-appearance:none;width:12px;height:12px;border-radius:50%;background:#e50914;cursor:pointer;}}
.hd-tag{{font-size:11px;font-weight:700;color:rgba(255,255,255,.3);letter-spacing:.05em;}}
.res-tag{{font-size:11px;color:rgba(255,255,255,.22);}}

/* Skip flash */
.sf{{position:absolute;top:0;bottom:0;width:33%;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;opacity:0;z-index:20;}}
.sf.L{{left:0;background:radial-gradient(ellipse at left,rgba(255,255,255,.1),transparent 70%);border-radius:0 50% 50% 0/0 100% 100% 0;}}
.sf.R{{right:0;background:radial-gradient(ellipse at right,rgba(255,255,255,.1),transparent 70%);border-radius:50% 0 0 50%/100% 0 0 100%;}}
.sf.show{{animation:flashOut .5s ease forwards;}}
@keyframes flashOut{{0%{{opacity:1;}}100%{{opacity:0;}}}}
.sf svg{{width:30px;height:30px;fill:rgba(255,255,255,.85);}}
.sf span{{font-size:12px;font-weight:800;color:rgba(255,255,255,.8);margin-top:4px;}}

/* Info section */
.info{{margin-top:22px;}}
.title{{font-size:clamp(1.3rem,3vw,2rem);font-weight:800;line-height:1.35;word-break:break-word;color:var(--txt);transition:color .35s;}}
.badges{{display:flex;align-items:center;gap:8px;margin-top:10px;flex-wrap:wrap;}}
.badge{{font-size:11px;font-weight:700;border-radius:5px;padding:3px 8px;border:1px solid;}}
.b-red{{color:#f87171;background:rgba(229,9,20,.1);border-color:rgba(229,9,20,.25);}}
.b-ylw{{color:#fbbf24;background:rgba(251,191,36,.1);border-color:rgba(251,191,36,.25);}}
.b-gray{{color:var(--txt-m);background:transparent;border-color:transparent;font-size:12px;font-weight:500;}}

/* Buttons */
.btn-row{{display:flex;flex-wrap:wrap;gap:12px;margin-top:18px;}}
.btn{{display:inline-flex;align-items:center;gap:9px;padding:11px 22px;border-radius:12px;font-family:inherit;font-size:14px;font-weight:700;cursor:pointer;text-decoration:none;border:none;transition:transform .15s,background .2s,color .2s,border-color .2s;}}
.btn:hover{{transform:translateY(-2px);}}
.btn:active{{transform:scale(.97);}}
.btn svg{{width:18px;height:18px;flex-shrink:0;}}
.btn-dl{{background:linear-gradient(135deg,#e50914,#c40812);color:#fff;box-shadow:0 4px 20px rgba(229,9,20,.35),inset 0 1px 0 rgba(255,255,255,.1);}}
.btn-dl:hover{{box-shadow:0 6px 28px rgba(229,9,20,.5);}}
.btn-cp{{background:var(--btn);color:var(--txt);border:1px solid var(--btn-b);}}
.btn-cp.done{{background:rgba(34,197,94,.12);border-color:rgba(34,197,94,.3);color:#4ade80;}}
.btn-sh{{background:var(--btn);color:var(--txt-m);border:1px solid var(--btn-b);}}
.btn-sh:hover{{color:var(--txt);}}

/* Meta strip */
.meta-strip{{display:flex;flex-wrap:wrap;gap:24px;margin-top:20px;padding-top:18px;border-top:1px solid var(--sep);transition:border-color .35s;}}
.meta-item{{display:flex;flex-direction:column;gap:3px;}}
.meta-label{{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.12em;color:var(--txt-d);transition:color .35s;}}
.meta-value{{font-size:13px;font-weight:700;color:var(--txt-m);transition:color .35s;}}

/* Toast */
#toast{{
  position:fixed;right:24px;bottom:24px;z-index:999;
  background:linear-gradient(135deg,#16a34a,#15803d);color:#fff;
  font-size:13px;font-weight:700;
  padding:12px 20px;border-radius:12px;
  box-shadow:0 8px 30px rgba(0,0,0,.4);
  display:flex;align-items:center;gap:8px;
  transform:translateY(80px);opacity:0;
  transition:transform .35s cubic-bezier(.34,1.56,.64,1),opacity .35s;
  pointer-events:none;
}}
#toast.show{{transform:translateY(0);opacity:1;}}
#toast svg{{width:16px;height:16px;fill:#fff;}}

/* Footer */
footer{{position:relative;z-index:1;text-align:center;padding:20px;border-top:1px solid var(--sep);font-size:11px;color:var(--txt-d);letter-spacing:.08em;transition:color .35s,border-color .35s;}}

/* Unsupported */
.no-support{{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}}
.no-card{{text-align:center;background:var(--surface);border:1px solid var(--sb);border-radius:16px;padding:48px 40px;max-width:400px;}}
.no-card h2{{font-size:20px;font-weight:800;margin-bottom:10px;}}
.no-card p{{font-size:14px;color:var(--txt-m);margin-bottom:28px;line-height:1.6;}}

/* Responsive */
@media(max-width:600px){{
  .wrap{{padding-top:78px;}}
  .nav-badge{{display:none;}}
  .btn{{width:100%;justify-content:center;}}
  .btn-row{{flex-direction:column;}}
  .meta-strip{{gap:16px;}}
}}
</style>
</head>
<body>

<div class="blob b1"></div>
<div class="blob b2"></div>

<nav class="navbar">
  <a href="/" class="logo">
    <div class="logo-icon"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></div>
    <div class="logo-text"><span class="w">FAST</span><span class="r"> FINDER</span></div>
  </a>
  <div class="nav-right">
    <div class="nav-badge"><div class="nav-dot"></div>HD Streaming</div>
    <button class="theme-toggle" id="theme-toggle" title="Toggle Theme">
      <svg id="theme-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
    </button>
  </div>
</nav>

<div class="wrap">
  <div class="player-box">
    <div class="cinema-bar"></div>
    <video id="vid" playsinline preload="metadata">
      <source src="{src}" type="{mime_type}">
    </video>

    <div class="sf L" id="sf-l"><svg viewBox="0 0 24 24"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6 8.5 6V6l-8.5 6z"/></svg><span id="sf-l-txt">-10s</span></div>
    <div class="sf R" id="sf-r"><svg viewBox="0 0 24 24"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6-8.5-6z"/></svg><span id="sf-r-txt">+10s</span></div>

    <div class="ctrl-overlay" id="overlay">
      <div class="ctrl-top">
        <div class="live-badge"><div class="live-dot"></div>Live Streaming</div>
        <div class="skip-btns">
          <button class="skip-btn" id="sk-b" title="-10s"><svg viewBox="0 0 24 24"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6 8.5 6V6l-8.5 6z"/></svg></button>
          <button class="skip-btn" id="sk-f" title="+10s"><svg viewBox="0 0 24 24"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6-8.5-6z"/></svg></button>
        </div>
      </div>
      <div class="ctrl-center">
        <button class="play-btn" id="play-btn">
          <svg id="play-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>
      </div>
      <div class="ctrl-bottom">
        <div class="progress-row">
          <span class="time" id="cur">0:00</span>
          <div class="pbar" id="pbar"><div class="pfill" id="pfill" style="width:0%"></div></div>
          <span class="time r" id="dur">0:00</span>
        </div>
        <div class="vol-row">
          <div class="vol-left">
            <button class="mute-btn" id="mute-btn">
              <svg id="vol-icon" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
            </button>
            <input type="range" class="vol" id="vol-sl" min="0" max="1" step="0.05" value="1">
            <span class="hd-tag">HD</span>
          </div>
          <span class="res-tag" id="res-tag"></span>
        </div>
      </div>
    </div>
  </div>

  <div class="info">
    <div class="title">{file_name}</div>
    <div class="badges" id="badges-el"></div>
    <div class="btn-row">
      <a href="{src}" class="btn btn-dl">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 16L7 11h3V4h4v7h3l-5 5zM5 20v-2h14v2H5z"/></svg>Download
      </a>
      <button class="btn btn-cp" id="cp-btn">
        <svg id="cp-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4C2.9 1 2 1.9 2 3v14h2V3h12V1zm3 4H8C6.9 5 6 5.9 6 7v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
        <span id="cp-txt">Copy Link</span>
      </button>
      <button class="btn btn-sh" id="sh-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>Share
      </button>
    </div>
    <div class="meta-strip" id="meta-el"></div>
  </div>
</div>

<footer>FAST FINDER — Ultra Stream Engine</footer>

<div id="toast"><svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg><span id="toast-msg">Done!</span></div>

<script>
const SRC = "{src}";
const FN  = "{file_name}";
const MIME = "{mime_type}";

// ── Theme Toggle ─────────────────────────────────────────
(function(){{
  const html = document.documentElement;
  const btn  = document.getElementById('theme-toggle');
  const icon = document.getElementById('theme-icon');
  const SUN  = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
  const MOON = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
  if(localStorage.getItem('ff_theme')==='light'){{ html.classList.add('light'); icon.innerHTML=MOON; }}
  btn.addEventListener('click',()=>{{
    const l=html.classList.toggle('light');
    icon.innerHTML = l ? MOON : SUN;
    localStorage.setItem('ff_theme', l?'light':'dark');
  }});
}})();

// ── Auto-detect file metadata ─────────────────────────────
(function(){{
  const ba=document.getElementById('badges-el'), ma=document.getElementById('meta-el');
  const q4k=/\b(4k|2160p|uhd)\b/i.test(FN), qhd=/\b(1080p|fhd|full.?hd)\b/i.test(FN);
  const qhdr=/\b(hdr|hdr10|dolby.?vision)\b/i.test(FN), qbr=/\b(bluray|blu.?ray|bdrip)\b/i.test(FN);
  const ext=(FN.split('.').pop()||MIME.split('/')[1]||'').toUpperCase();
  if(q4k)  ba.innerHTML+='<span class="badge b-red">4K UHD</span>';
  if(qhdr) ba.innerHTML+='<span class="badge b-ylw">HDR</span>';
  if(qhd&&!q4k) ba.innerHTML+='<span class="badge b-red">1080p</span>';
  if(qbr)  ba.innerHTML+='<span class="badge b-ylw">BluRay</span>';
  const res = q4k?'3840×2160':qhd?'1920×1080':'';
  document.getElementById('res-tag').textContent=res;
  ma.innerHTML=[
    ['Quality', q4k?'4K UHD':qhd?'Full HD':'HD'],
    ['Format',  ext||'—'],
    ['Codec',   q4k?'H.265':'H.264'],
    ['Audio',   qbr?'DTS-HD':'AAC'],
  ].map(([l,v])=>`<div class="meta-item"><span class="meta-label">${{l}}</span><span class="meta-value">${{v}}</span></div>`).join('');
}})();

// ── Player ────────────────────────────────────────────────
const vid=document.getElementById('vid');
const overlay=document.getElementById('overlay');
const playBtn=document.getElementById('play-btn');
const playIcon=document.getElementById('play-icon');
const cur=document.getElementById('cur'), dur=document.getElementById('dur');
const pbar=document.getElementById('pbar'), pfill=document.getElementById('pfill');
const muteBtn=document.getElementById('mute-btn'), volIcon=document.getElementById('vol-icon');
const volSl=document.getElementById('vol-sl');
const sfL=document.getElementById('sf-l'), sfR=document.getElementById('sf-r');
const sfLT=document.getElementById('sf-l-txt'), sfRT=document.getElementById('sf-r-txt');
let hideTimer;

const PAUSE_SVG='<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
const PLAY_SVG ='<path d="M8 5v14l11-7z"/>';
const VOL_SVG  ='<path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>';
const MUTE_SVG ='<path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>';
const CHECK_SVG='<path d="M16 1H4C2.9 1 2 1.9 2 3v14h2V3h12V1zm3 4H8C6.9 5 6 5.9 6 7v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>';
const DONE_SVG ='<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>';

function fmt(s){{ const m=Math.floor(s/60),ss=String(Math.floor(s%60)).padStart(2,'0'); return m+':'+ss; }}

function showCtrls(){{
  overlay.classList.remove('hidden');
  clearTimeout(hideTimer);
  if(!vid.paused) hideTimer=setTimeout(()=>overlay.classList.add('hidden'),3000);
}}
function togglePlay(){{ vid.paused ? vid.play() : vid.pause(); showCtrls(); }}

vid.addEventListener('play',  ()=>{{ playIcon.innerHTML=PAUSE_SVG; showCtrls(); }});
vid.addEventListener('pause', ()=>{{ playIcon.innerHTML=PLAY_SVG; overlay.classList.remove('hidden'); clearTimeout(hideTimer); }});
vid.addEventListener('ended', ()=>{{ playIcon.innerHTML=PLAY_SVG; overlay.classList.remove('hidden'); }});
vid.addEventListener('timeupdate',()=>{{
  if(!vid.duration) return;
  pfill.style.width=(vid.currentTime/vid.duration*100)+'%';
  cur.textContent=fmt(vid.currentTime);
}});
vid.addEventListener('loadedmetadata',()=>{{ dur.textContent=fmt(vid.duration); }});

playBtn.addEventListener('click', togglePlay);
vid.addEventListener('click', togglePlay);
document.addEventListener('mousemove', showCtrls);
document.addEventListener('touchstart', showCtrls, {{passive:true}});

// Progress seek
pbar.addEventListener('click', e=>{{
  const r=pbar.getBoundingClientRect();
  vid.currentTime=(e.clientX-r.left)/r.width*vid.duration;
}});

// Volume
volSl.addEventListener('input',()=>{{
  vid.volume=parseFloat(volSl.value); vid.muted=vid.volume===0;
  volIcon.innerHTML=vid.muted?MUTE_SVG:VOL_SVG;
}});
muteBtn.addEventListener('click',()=>{{
  vid.muted=!vid.muted; volIcon.innerHTML=vid.muted?MUTE_SVG:VOL_SVG;
  volSl.value=vid.muted?0:vid.volume;
}});

// Skip function
function doSkip(secs, el, txtEl){{
  vid.currentTime=Math.max(0,Math.min(vid.duration||0,vid.currentTime+secs));
  txtEl.textContent=(secs>0?'+':'')+secs+'s';
  el.classList.remove('show'); void el.offsetWidth; el.classList.add('show');
  el.addEventListener('animationend',()=>el.classList.remove('show'),{{once:true}});
  showCtrls();
}}
document.getElementById('sk-b').addEventListener('click',()=>doSkip(-10,sfL,sfLT));
document.getElementById('sk-f').addEventListener('click',()=>doSkip(10,sfR,sfRT));

// Double-tap skip (YouTube style progressive)
(function(){{
  let tc=0, side=null, tmr;
  function tap(e, dir){{
    e.preventDefault(); e.stopPropagation();
    if(side!==dir){{tc=0; side=dir;}}
    tc++; clearTimeout(tmr);
    if(tc===1){{ tmr=setTimeout(()=>{{tc=0;side=null;}},280); }}
    else{{
      const secs=(tc-1)*10*(dir==='r'?1:-1);
      doSkip(secs, dir==='r'?sfR:sfL, dir==='r'?sfRT:sfLT);
      tc=0; side=null;
    }}
  }}
  vid.addEventListener('touchend', e=>{{
    const rect=vid.getBoundingClientRect();
    const x=e.changedTouches[0].clientX-rect.left;
    tap(e, x<rect.width/2?'l':'r');
  }});
}})();

// Fullscreen orientation
vid.addEventListener('webkitbeginfullscreen',()=>{{if(screen.orientation?.lock) screen.orientation.lock('landscape').catch(()=>{{}});}});
vid.addEventListener('webkitendfullscreen',()=>screen.orientation?.unlock?.());

// ── Toast helper ─────────────────────────────────────────
function showToast(msg){{
  const t=document.getElementById('toast');
  document.getElementById('toast-msg').textContent=msg;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2800);
}}

// ── Copy Link ─────────────────────────────────────────────
document.getElementById('cp-btn').addEventListener('click',()=>{{
  navigator.clipboard.writeText(SRC).then(()=>{{
    const btn=document.getElementById('cp-btn');
    const txt=document.getElementById('cp-txt');
    const icon=document.getElementById('cp-icon');
    btn.classList.add('done');
    txt.textContent='Copied!';
    icon.innerHTML=DONE_SVG;
    showToast('Link Copied!');
    setTimeout(()=>{{
      btn.classList.remove('done');
      txt.textContent='Copy Link';
      icon.innerHTML=CHECK_SVG;
    }},2500);
  }}).catch(()=>{{
    // Fallback for older browsers
    const ta=document.createElement('textarea');
    ta.value=SRC; ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.select();
    document.execCommand('copy'); document.body.removeChild(ta);
    showToast('Link Copied!');
  }});
}});

// ── Share ─────────────────────────────────────────────────
document.getElementById('sh-btn').addEventListener('click',()=>{{
  if(navigator.share){{
    navigator.share({{title:FN, url:SRC}}).catch(()=>{{}});
  }}else{{
    document.getElementById('cp-btn').click();
  }}
}});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────
# 🔴 MEDIA WATCH CORE ROUTE (RAM Protected)
# ─────────────────────────────────────────────────────────
async def media_watch(message_id):
    try:
        msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
        media = getattr(msg, msg.media.value, None) if msg and msg.media else None

        if not media:
            return "<h2 style='color:#fff;text-align:center;padding:50px;font-family:Inter,sans-serif'>❌ File Not Found</h2>"

        src = urllib.parse.urljoin(URL, f'download/{message_id}')
        mime = getattr(media, 'mime_type', 'video/mp4')

        if mime.split('/')[0].strip() == 'video':
            fn = html.escape(getattr(media, 'file_name', 'Fast Finder Movie'))
            html_content = watch_tmplt.format(
                heading=f"Watch — {fn}",
                file_name=fn,
                src=src,
                mime_type=mime
            )
            del msg, media
            gc.collect()
            return html_content

        # Unsupported file fallback
        del msg, media
        gc.collect()
        return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unsupported File</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
<style>
body{{background:#060608;color:#fff;font-family:'Inter',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;}}
.card{{text-align:center;background:#0f0f11;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:48px 40px;max-width:400px;}}
.card h2{{font-size:20px;font-weight:800;margin-bottom:10px;}}
.card p{{font-size:14px;color:rgba(255,255,255,.4);margin-bottom:28px;line-height:1.6;}}
.card a{{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#e50914,#c40812);color:#fff;padding:11px 24px;border-radius:12px;text-decoration:none;font-weight:700;font-size:14px;box-shadow:0 4px 20px rgba(229,9,20,.35);}}
</style></head><body>
<div class="card">
  <h2>⚠️ Unsupported Format</h2>
  <p>This file type cannot be streamed in the browser.<br>You can still download it directly.</p>
  <a href="{src}">⬇ Download File</a>
</div></body></html>"""

    except Exception as e:
        logger.error(f"Watch Error: {e}")
        gc.collect()
        return f"<h2 style='color:red;text-align:center;font-family:Inter,sans-serif;padding:50px'>Server Error: {html.escape(str(e))}</h2>"
