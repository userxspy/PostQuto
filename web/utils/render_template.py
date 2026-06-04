import urllib.parse
import html
import logging
import gc
from info import BIN_CHANNEL, URL
from utils import temp

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# 🎬 FAST FINDER PLAYER v2
# Features: Custom controls | Speed selector | PiP | Fullscreen+Landscape
#           Double-tap skip | Auto-hide controls | Dark/Light theme
#           Toast with animation | Clipboard fallback
# ─────────────────────────────────────────────────────────
watch_tmplt = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>{heading}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;700;900&display=swap" rel="stylesheet">
<style>
:root{{--red:#e50914;--bg1:#000;--bg2:#111;--txt:#fff;--nav:rgba(0,0,0,.95);--box:#000;--bd:rgba(255,255,255,.08);--bc:rgba(255,255,255,.08);--muted:#b3b3b3}}
html.light{{--bg1:#f8f9fa;--bg2:#e9ecef;--txt:#121212;--nav:rgba(255,255,255,.95);--box:#fff;--bd:rgba(0,0,0,.15);--bc:rgba(0,0,0,.06);--muted:#555}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:linear-gradient(to bottom,var(--bg1),var(--bg2));font-family:'DM Sans',sans-serif;color:var(--txt);min-height:100vh;transition:background .3s,color .3s}}
.nav{{width:100%;padding:14px 4%;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;z-index:999;background:var(--nav);backdrop-filter:blur(6px);transition:background .3s}}
.logo{{text-decoration:none;display:flex;align-items:center}}
.lbox{{background:#e50914;color:#fff;font-family:'Bebas Neue',sans-serif;font-size:30px;line-height:1;padding:3px 8px 2px;transform:skewX(-8deg);display:inline-block;box-shadow:2px 0 0 #b00008}}
.ltxt{{font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:3px;color:#e50914;padding-left:8px;line-height:1;user-select:none}}
.tbtn{{background:transparent;border:1px solid var(--bd);color:var(--txt);padding:6px 14px;border-radius:4px;font-family:'DM Sans',sans-serif;font-weight:700;font-size:13px;cursor:pointer;transition:.3s}}
.wrap{{max-width:1350px;margin:auto;padding:90px 20px 40px}}
.pbox{{border-radius:12px;background:#000;border:1px solid var(--bd);box-shadow:0 0 20px rgba(255,0,0,.1),0 20px 60px rgba(0,0,0,.5);overflow:hidden;position:relative;user-select:none}}
video{{width:100%;height:auto;display:block;cursor:pointer}}
.skip{{position:absolute;top:0;bottom:15%;width:40%;z-index:20;display:flex;align-items:center;justify-content:center;cursor:pointer;-webkit-tap-highlight-color:transparent;touch-action:manipulation}}
.skip.L{{left:0}}.skip.R{{right:0}}
.rip{{position:absolute;inset:0;background:rgba(255,255,255,.13);opacity:0;transition:opacity .2s;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;backdrop-filter:blur(2px)}}
.skip.L .rip{{border-radius:0 50% 50% 0/0 100% 100% 0}}
.skip.R .rip{{border-radius:50% 0 0 50%/100% 0 0 100%}}
.skip.act .rip{{opacity:1;animation:pop .3s cubic-bezier(.25,1,.5,1) forwards}}
.sico{{width:28px;height:28px;fill:#fff;filter:drop-shadow(0 2px 6px rgba(0,0,0,.5))}}
.stxt{{color:#fff;font-weight:800;font-size:14px;margin-top:5px;text-shadow:0 2px 8px rgba(0,0,0,.6)}}
.pov{{position:absolute;inset:0;z-index:15;display:flex;align-items:center;justify-content:center;cursor:pointer;background:rgba(0,0,0,.3)}}
.pov.hi{{display:none}}
.pcir{{width:72px;height:72px;border-radius:50%;background:rgba(229,9,20,.9);display:flex;align-items:center;justify-content:center;box-shadow:0 0 30px rgba(229,9,20,.5)}}
.pcir svg{{width:32px;height:32px;fill:#fff}}
.cbar{{position:absolute;bottom:0;left:0;right:0;z-index:30;padding:10px 14px 13px;background:linear-gradient(to top,rgba(0,0,0,.9),transparent);opacity:1;transition:opacity .35s;pointer-events:auto}}
.cbar.hi{{opacity:0;pointer-events:none}}
.seek{{width:100%;height:4px;accent-color:#e50914;cursor:pointer;-webkit-appearance:none;background:rgba(255,255,255,.25);border-radius:4px;outline:none;margin-bottom:9px;display:block}}
.seek::-webkit-slider-thumb{{-webkit-appearance:none;width:14px;height:14px;border-radius:50%;background:#e50914;cursor:pointer}}
.brow{{display:flex;align-items:center;gap:5px}}
.ib{{background:transparent;border:none;cursor:pointer;padding:5px;border-radius:5px;display:flex;align-items:center;justify-content:center;transition:background .2s;flex-shrink:0}}
.ib svg{{fill:#fff;width:20px;height:20px}}
.ib.pon svg{{fill:#e50914}}
.sp{{flex:1}}
.tm{{color:#fff;font-size:13px;font-weight:600;letter-spacing:.3px;user-select:none;margin-left:3px;white-space:nowrap}}
.sb{{background:transparent;border:none;cursor:pointer;padding:4px 8px;border-radius:5px;min-width:42px;color:#fff;font-size:12px;font-weight:700;letter-spacing:.3px;font-family:inherit}}
.sm{{position:absolute;bottom:calc(100% + 8px);right:0;background:rgba(18,18,18,.98);border:1px solid rgba(255,255,255,.12);border-radius:8px;overflow:hidden;min-width:95px;box-shadow:0 8px 32px rgba(0,0,0,.7);animation:mup .18s cubic-bezier(.25,1,.5,1);z-index:50}}
.sm button{{display:block;width:100%;padding:9px 16px;background:transparent;border:none;color:#fff;font-size:13px;font-weight:500;cursor:pointer;text-align:left;font-family:inherit;transition:background .15s}}
.sm button:hover{{background:rgba(255,255,255,.08)}}
.sm button.ac{{color:#e50914;font-weight:700;background:rgba(229,9,20,.12)}}
.sm.hi{{display:none}}
.spos{{position:relative}}
.info{{margin-top:22px}}
.ttl{{font-size:1.7rem;font-weight:700;line-height:1.4;margin-bottom:20px;word-break:break-word}}
.btns{{display:flex;flex-wrap:wrap;gap:14px}}
.btn{{display:inline-flex;align-items:center;gap:10px;padding:12px 24px;border-radius:6px;text-decoration:none;font-size:1rem;font-weight:700;cursor:pointer;transition:.25s;border:none;font-family:inherit}}
.btn svg{{width:20px;height:20px;fill:currentColor;flex-shrink:0}}
.dl{{background:#e50914;color:#fff;box-shadow:0 0 18px rgba(229,9,20,.35)}}
.dl:hover{{transform:translateY(-2px)}}
.cp{{background:var(--bc);color:var(--txt);border:1px solid var(--bd)}}
.cp:hover{{background:var(--bd)}}
#toast{{visibility:hidden;position:fixed;right:28px;bottom:28px;z-index:9999;background:#e50914;color:#fff;padding:14px 22px;border-radius:8px;font-weight:700;font-size:15px;box-shadow:0 10px 30px rgba(0,0,0,.45)}}
#toast.show{{visibility:visible;animation:tin .35s cubic-bezier(.25,1,.5,1)}}
@keyframes pop{{0%{{transform:scaleX(.85)}}100%{{transform:scaleX(1)}}}}
@keyframes tin{{0%{{opacity:0;transform:translateY(14px)}}100%{{opacity:1;transform:translateY(0)}}}}
@keyframes mup{{0%{{opacity:0;transform:translateY(6px)}}100%{{opacity:1;transform:translateY(0)}}}}
@media(max-width:768px){{.wrap{{padding-top:80px}}.ttl{{font-size:1.3rem}}.btns{{flex-direction:column}}.btn{{width:100%;justify-content:center}}}}
</style>
</head>
<body>

<nav class="nav">
  <a href="/" class="logo">
    <span class="lbox">F</span><span class="ltxt">AST FINDER</span>
  </a>
  <button class="tbtn" id="tbtn" onclick="tgTheme()">&#9728;&#65039; Light</button>
</nav>

<div class="wrap">
  <div class="pbox" id="pb">
    <video id="v" playsinline preload="metadata">
      <source src="{src}" type="{mime_type}">
    </video>

    <div class="skip L" id="sl">
      <div class="rip">
        <svg class="sico" viewBox="0 0 24 24"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>
        <span class="stxt" id="slt">10s</span>
      </div>
    </div>
    <div class="skip R" id="sr">
      <div class="rip">
        <svg class="sico" viewBox="0 0 24 24"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6-8.5-6z"/></svg>
        <span class="stxt" id="srt">10s</span>
      </div>
    </div>

    <div class="pov" id="pov" onclick="tgPlay()">
      <div class="pcir">
        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
      </div>
    </div>

    <div class="cbar" id="cb">
      <input type="range" class="seek" id="sk" min="0" max="100" step="0.1" value="0">
      <div class="brow">
        <button class="ib" id="pb2" onclick="tgPlay()" title="Play/Pause">
          <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        </button>
        <button class="ib" id="mb" onclick="tgMute()" title="Mute">
          <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
        </button>
        <span class="tm" id="td">0:00 / 0:00</span>
        <div class="sp"></div>
        <button class="ib" id="pipb" onclick="tgPiP()" title="Picture in Picture">
          <svg viewBox="0 0 24 24"><path d="M19 11h-8v6h8v-6zm4 8V4.98C23 3.88 22.1 3 21 3H3C1.9 3 1 3.88 1 4.98V19c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2zm-2 .02H3V5h18v14.02z"/></svg>
        </button>
        <div class="spos">
          <button class="sb" id="spb" onclick="tgSM()">1&#215;</button>
          <div class="sm hi" id="sm"></div>
        </div>
        <button class="ib" id="fsb" onclick="tgFS()" title="Fullscreen">
          <svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
        </button>
      </div>
    </div>
  </div>

  <div class="info">
    <div class="ttl">{file_name}</div>
    <div class="btns">
      <a href="{src}" class="btn dl">
        <svg viewBox="0 0 24 24"><path d="M12 16L7 11H10V4H14V11H17L12 16ZM5 20V18H19V20H5Z"/></svg>
        Download
      </a>
      <button onclick="cpLink()" class="btn cp">
        <svg viewBox="0 0 24 24"><path d="M16 1H4C2.9 1 2 1.9 2 3V17H4V3H16V1ZM19 5H8C6.9 5 6 5.9 6 7V21C6 22.1 6.9 23 8 23H19C20.1 23 21 22.1 21 21V7C21 5.9 20.1 5 19 5ZM19 21H8V7H19V21Z"/></svg>
        Copy Link
      </button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
// ── Elements ──
var v=document.getElementById('v'),
    pb=document.getElementById('pb'),
    pb2=document.getElementById('pb2'),
    mb=document.getElementById('mb'),
    sk=document.getElementById('sk'),
    td=document.getElementById('td'),
    cb=document.getElementById('cb'),
    pov=document.getElementById('pov'),
    pipb=document.getElementById('pipb'),
    spb=document.getElementById('spb'),
    sm=document.getElementById('sm'),
    fsb=document.getElementById('fsb'),
    sl=document.getElementById('sl'),
    sr=document.getElementById('sr'),
    slt=document.getElementById('slt'),
    srt=document.getElementById('srt'),
    tbtn=document.getElementById('tbtn'),
    toast=document.getElementById('toast');

// ── Theme ──
var docEl=document.documentElement;
if(localStorage.getItem('theme')==='light'){{docEl.classList.add('light');tbtn.innerHTML='&#127769; Dark';}}
function tgTheme(){{
  var l=docEl.classList.toggle('light');
  localStorage.setItem('theme',l?'light':'dark');
  tbtn.innerHTML=l?'&#127769; Dark':'&#9728;&#65039; Light';
}}

// ── Time format ──
function fmt(s){{
  if(!s||isNaN(s)||s<0) return'0:00';
  var m=Math.floor(s/60),sec=Math.floor(s%60);
  return m+':'+(sec<10?'0':'')+sec;
}}

// ── Auto-hide controls ──
var ht=null;
function resetHide(){{
  cb.classList.remove('hi');
  clearTimeout(ht);
  ht=setTimeout(function(){{if(!v.paused)cb.classList.add('hi');}},3000);
}}
pb.addEventListener('pointermove',resetHide);

// ── Play / Pause ──
var PLAY_SVG='<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>';
var PAUSE_SVG='<svg viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
function tgPlay(){{if(v.paused)v.play();else v.pause();resetHide();}}
v.addEventListener('click',tgPlay);
v.addEventListener('play',function(){{
  pov.classList.add('hi');pb2.innerHTML=PAUSE_SVG;resetHide();
}});
v.addEventListener('pause',function(){{
  pov.classList.remove('hi');pb2.innerHTML=PLAY_SVG;cb.classList.remove('hi');
}});

// ── Mute ──
var MUT_SVG='<svg viewBox="0 0 24 24"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>';
var VOL_SVG='<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>';
function tgMute(){{v.muted=!v.muted;mb.innerHTML=v.muted?MUT_SVG:VOL_SVG;}}

// ── Seek ──
var seeking=false;
function setSeeking(s){{seeking=s;}}
sk.addEventListener('mousedown',function(){{setSeeking(true);}});
sk.addEventListener('touchstart',function(){{setSeeking(true);}},{{passive:true}});
sk.addEventListener('mouseup',function(){{setSeeking(false);}});
sk.addEventListener('touchend',function(){{setSeeking(false);}});
sk.addEventListener('input',function(){{if(v.duration)v.currentTime=(sk.value/100)*v.duration;}});
v.addEventListener('loadedmetadata',function(){{td.textContent='0:00 / '+fmt(v.duration);}});
v.addEventListener('timeupdate',function(){{
  if(!seeking&&v.duration){{
    sk.value=(v.currentTime/v.duration)*100;
    td.textContent=fmt(v.currentTime)+' / '+fmt(v.duration);
  }}
}});

// ── Speed menu ──
var SPD=[0.5,0.75,1,1.25,1.5,2],curSpd=1;
SPD.forEach(function(s){{
  var b=document.createElement('button');
  b.textContent=s===1?'Normal  1\u00d7':s+'\u00d7';
  b.dataset.s=s;if(s===1)b.classList.add('ac');
  b.onclick=function(){{setSpd(s);}};
  sm.appendChild(b);
}});
function tgSM(){{sm.classList.toggle('hi');}}
function setSpd(s){{
  v.playbackRate=s;curSpd=s;
  spb.textContent=s===1?'1\u00d7':s+'\u00d7';
  sm.querySelectorAll('button').forEach(function(b){{
    b.classList.toggle('ac',parseFloat(b.dataset.s)===s);
  }});
  sm.classList.add('hi');
}}
document.addEventListener('mousedown',function(e){{
  if(!e.target.closest('.spos'))sm.classList.add('hi');
}});

// ── PiP ──
function tgPiP(){{
  if(document.pictureInPictureElement){{
    document.exitPictureInPicture().catch(function(){{}});
  }}else if(v.requestPictureInPicture){{
    v.requestPictureInPicture().catch(function(){{}});
  }}
}}
v.addEventListener('enterpictureinpicture',function(){{pipb.classList.add('pon');}});
v.addEventListener('leavepictureinpicture',function(){{pipb.classList.remove('pon');}});

// ── Fullscreen + Landscape ──
var FS_IN='<svg viewBox="0 0 24 24"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>';
var FS_OUT='<svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>';
function updFS(inFS){{fsb.innerHTML=inFS?FS_IN:FS_OUT;}}
function tgFS(){{
  var inFS=!!(document.fullscreenElement||document.webkitFullscreenElement);
  if(!inFS){{
    if(v.webkitEnterFullscreen){{v.webkitEnterFullscreen();return;}}
    var req=pb.requestFullscreen||pb.webkitRequestFullscreen;
    if(req){{
      var p=req.call(pb);
      if(p&&p.then)p.then(function(){{
        if(screen.orientation&&screen.orientation.lock)
          screen.orientation.lock('landscape').catch(function(){{}});
      }}).catch(function(){{}});
    }}
  }}else{{
    var ex=document.exitFullscreen||document.webkitExitFullscreen;
    if(ex)ex.call(document);
    if(screen.orientation&&screen.orientation.unlock)screen.orientation.unlock();
  }}
}}
function onFsChg(){{updFS(!!(document.fullscreenElement||document.webkitFullscreenElement));}}
document.addEventListener('fullscreenchange',onFsChg);
document.addEventListener('webkitfullscreenchange',onFsChg);
v.addEventListener('webkitendfullscreen',function(){{updFS(false);}});

// ── Double-tap skip ──
var tap={{side:null,count:0,timer:null}};
function doTap(side){{
  if(tap.side!==side){{tap.count=0;tap.side=side;}}
  tap.count++;clearTimeout(tap.timer);resetHide();
  var zone=side==='l'?sl:sr,lbl=side==='l'?slt:srt;
  if(tap.count===1){{
    tap.timer=setTimeout(function(){{tap.count=0;tap.side=null;}},250);
    return;
  }}
  var secs=(tap.count-1)*10;
  lbl.textContent=secs+'s';
  zone.classList.remove('act');void zone.offsetWidth;zone.classList.add('act');
  tap.timer=setTimeout(function(){{
    v.currentTime+=side==='l'?-secs:secs;
    zone.classList.remove('act');
    tap.count=0;tap.side=null;lbl.textContent='10s';
  }},350);
}}
sl.addEventListener('pointerup',function(e){{e.preventDefault();doTap('l');}});
sr.addEventListener('pointerup',function(e){{e.preventDefault();doTap('r');}});
['click','dblclick'].forEach(function(ev){{
  sl.addEventListener(ev,function(e){{e.preventDefault();e.stopPropagation();}});
  sr.addEventListener(ev,function(e){{e.preventDefault();e.stopPropagation();}});
}});

// ── Copy link ──
function cpLink(){{
  var url="{src}";
  if(navigator.clipboard&&navigator.clipboard.writeText){{
    navigator.clipboard.writeText(url).then(function(){{showToast('\u2705 Copied!');}}).catch(function(){{fbCopy(url);}});
  }}else{{fbCopy(url);}}
}}
function fbCopy(url){{
  var ta=document.createElement('textarea');
  ta.value=url;ta.style.cssText='position:fixed;opacity:0';
  document.body.appendChild(ta);ta.select();
  try{{document.execCommand('copy');showToast('\u2705 Copied!');}}
  catch(e){{showToast('\u274c Copy failed');}}
  document.body.removeChild(ta);
}}

// ── Toast ──
var tt=null;
function showToast(msg){{
  clearTimeout(tt);toast.textContent=msg;
  toast.classList.remove('show');void toast.offsetWidth;
  toast.classList.add('show');
  tt=setTimeout(function(){{toast.classList.remove('show');}},3000);
}}

</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────
# 🎬 MEDIA WATCH CORE ROUTE
# ─────────────────────────────────────────────────────────
async def media_watch(message_id):
    try:
        msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
        media = getattr(msg, msg.media.value, None) if msg and msg.media else None

        if not media:
            return "<h2 style='color:#fff;text-align:center;padding:50px;font-family:sans-serif'>❌ File Not Found</h2>"

        src = urllib.parse.urljoin(URL, f'download/{message_id}')
        mime = getattr(media, 'mime_type', 'video/mp4')

        if mime.split('/')[0].strip() == 'video':
            fn = html.escape(getattr(media, 'file_name', 'Fast Finder Movie'))
            html_content = watch_tmplt.format(
                heading=f"Watch {fn}",
                file_name=fn,
                src=src,
                mime_type=mime
            )
            del msg, media
            gc.collect()
            return html_content

        # Unsupported format — show download page
        del msg, media
        gc.collect()
        return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unsupported Format</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&display=swap" rel="stylesheet">
</head>
<body style="background:#000;color:#fff;display:flex;align-items:center;justify-content:center;
min-height:100vh;font-family:'DM Sans',sans-serif;margin:0">
<div style="text-align:center;background:#141414;padding:40px 36px;border-radius:14px;
border:1px solid rgba(255,255,255,.08);max-width:400px;width:90%">
<div style="font-size:48px;margin-bottom:16px">&#128221;</div>
<h2 style="font-size:1.3rem;font-weight:700;margin-bottom:10px">Unsupported Format</h2>
<p style="color:#808080;font-size:14px;line-height:1.6;margin-bottom:24px">
This file type cannot be streamed online.<br>Please download it to watch locally.</p>
<a href="{src}" style="display:inline-flex;align-items:center;gap:10px;background:#e50914;
color:#fff;padding:13px 28px;border-radius:8px;text-decoration:none;font-weight:700;
font-size:15px;box-shadow:0 0 18px rgba(229,9,20,.35)">
<svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24">
<path d="M12 16L7 11H10V4H14V11H17L12 16ZM5 20V18H19V20H5Z"/></svg>
Download File</a>
</div>
</body></html>"""

    except Exception as e:
        logger.error(f"Watch Error: {e}")
        gc.collect()
        return f"<h2 style='color:red;text-align:center;padding:40px;font-family:sans-serif'>Server Error: {html.escape(str(e))}</h2>"
