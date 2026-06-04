import time
import gc
from aiohttp import web
from info import ADMINS, MAX_WEB_RESULTS
from utils import temp

# ─────────────────────────────────────────────────────────────────
#  STYLES
# ─────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0a0a0c;--bg2:#111116;--bg3:#1d1d26;--bg4:#2a2a38;
  --accent:#e50914;--accent-hover:#b30710;
  --text:#ffffff;--muted:#a0a0b0;--border:#262636;--card:#14141f;
  --sidebar-w:260px;--primary-p:0%;--cloud-p:0%;--archive-p:0%
}
.light{
  --bg:#f4f5f7;--bg2:#ffffff;--bg3:#eef0f4;--bg4:#dbdee6;
  --text:#0a0a0c;--muted:#62627a;--border:#d2d5df;--card:#ffffff
}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;}
a{color:inherit;text-decoration:none;}

/* ── YOUR EXISTING CSS (sidebar, topbar, dashboard, search, cards, etc.) ── */
/* Paste the rest of your original CSS string here, unchanged.               */

/* ════════════════════════════════════════════════════════════════
   AUTH / LOGIN PAGES  — new additions
   ════════════════════════════════════════════════════════════════ */

/* Page shell */
.login-bg{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:80px 16px 24px;position:relative;overflow:hidden;}
.login-bg::before{content:'';position:fixed;top:-200px;left:50%;transform:translateX(-50%);width:500px;height:500px;border-radius:50%;background:radial-gradient(circle,rgba(229,9,20,.12) 0%,transparent 70%);pointer-events:none;}

/* Card */
.login-wrap{width:100%;max-width:420px;margin:0 auto;}
.login-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:36px 32px;box-shadow:0 24px 64px rgba(0,0,0,.45);}
.light .login-card{box-shadow:0 8px 40px rgba(0,0,0,.1);}
.login-card h2{font-size:22px;font-weight:700;margin-bottom:6px;color:var(--text);}
.login-card .sub{font-size:14px;color:var(--muted);margin-bottom:24px;}

/* Form layout */
.form-group{display:flex;flex-direction:column;gap:14px;}
.field-label{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:6px;}

/* Inputs */
.input-wrap{position:relative;}
.input-wrap .inp-icon{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--muted);pointer-events:none;display:flex;align-items:center;font-size:14px;}
input[type=email],
input[type=password],
input[type=text],
input[type=number]{
  width:100%;background:var(--bg3);border:1px solid var(--border);
  border-radius:10px;padding:11px 14px 11px 38px;
  font-size:14px;color:var(--text);font-family:'DM Sans',sans-serif;
  outline:none;transition:border-color .2s;
  -webkit-appearance:none;appearance:none;
}
input:focus{border-color:var(--accent);}
input::placeholder{color:#4a4a5a;}
.light input::placeholder{color:#9a9aaa;}
input[type=number]::-webkit-inner-spin-button,
input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none;margin:0;}

/* Password show/hide */
.pw-wrap input{padding-right:42px;}
.pw-toggle{
  position:absolute;right:10px;top:50%;transform:translateY(-50%);
  background:none;border:none;color:var(--muted);cursor:pointer;
  padding:4px;border-radius:6px;display:flex;align-items:center;
  transition:transform .12s ease,color .2s;overflow:hidden;
}
.pw-toggle:active{transform:translateY(-50%) scale(0.88);}

/* Forgot password link */
.forgot-link{text-align:right;margin-top:-6px;}
.forgot-link a{font-size:13px;color:var(--muted);text-decoration:none;transition:color .2s;}
.forgot-link a:hover{color:var(--text);}

/* Primary button */
.submit-btn{
  width:100%;padding:12px;border-radius:10px;
  background:var(--accent);border:none;
  color:#fff;font-size:14px;font-weight:700;
  cursor:pointer;font-family:'DM Sans',sans-serif;
  position:relative;overflow:hidden;
  transition:transform .12s ease,background .2s;
  margin-top:4px;
}
.submit-btn:hover{background:var(--accent-hover);}
.submit-btn:active{transform:scale(0.97);}
.submit-btn:disabled{opacity:.4;cursor:not-allowed;transform:none;}

/* Ripple */
.submit-btn .ripple,
.ghost-btn .ripple{
  position:absolute;border-radius:50%;
  background:rgba(255,255,255,.3);
  width:8px;height:8px;
  transform:translate(-50%,-50%) scale(0);
  animation:btn-ripple .6s ease-out forwards;
  pointer-events:none;
}
@keyframes btn-ripple{to{transform:translate(-50%,-50%) scale(30);opacity:0;}}

/* Ghost / outline button */
.ghost-btn{
  padding:11px 16px;border-radius:10px;
  background:rgba(229,9,20,.12);border:1px solid rgba(229,9,20,.28);
  color:var(--accent);font-size:13px;font-weight:700;
  cursor:pointer;font-family:'DM Sans',sans-serif;
  white-space:nowrap;position:relative;overflow:hidden;
  transition:transform .12s ease,background .2s;
}
.ghost-btn:hover{background:rgba(229,9,20,.22);}
.ghost-btn:active{transform:scale(0.97);}

/* Card divider & footer */
.card-divider{border:none;border-top:1px solid var(--border);margin:20px 0;}
.card-footer{text-align:center;font-size:14px;color:var(--muted);}
.card-footer a{color:var(--accent);text-decoration:none;font-weight:600;}

/* Info banner */
.info-banner{
  background:rgba(229,9,20,.08);border:1px solid rgba(229,9,20,.22);
  border-radius:10px;padding:12px 14px;margin-bottom:20px;
  display:flex;gap:10px;align-items:flex-start;
  font-size:12px;color:var(--muted);line-height:1.5;
}
.info-banner svg{flex-shrink:0;margin-top:2px;color:var(--accent);}

/* Step indicator */
.step-row{display:flex;align-items:center;gap:8px;margin-bottom:10px;}
.step-badge{
  width:20px;height:20px;border-radius:50%;
  background:var(--bg3);border:1px solid var(--border);
  display:flex;align-items:center;justify-content:center;
  flex-shrink:0;font-size:10px;font-weight:700;color:var(--muted);
  transition:all .3s;
}
.step-badge.done{background:rgba(229,9,20,.18);border-color:rgba(229,9,20,.5);color:var(--accent);}
.step-label{font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;}
.sent-badge{margin-left:auto;font-size:11px;color:#00b894;font-weight:600;}

/* Split row (input + ghost button side by side) */
.split-row{display:flex;gap:8px;}
.split-row .input-wrap{flex:1;}

/* "then" divider between steps */
.then-divider{display:flex;align-items:center;gap:10px;margin:16px 0;}
.then-divider::before,.then-divider::after{content:'';flex:1;height:1px;background:var(--border);}
.then-divider span{font-size:11px;color:var(--bg4);}

/* OTP boxes */
.otp-row{display:flex;gap:8px;justify-content:center;margin-bottom:16px;}
.otp-box{
  width:44px;height:52px;text-align:center;
  font-size:20px;font-weight:700;
  background:var(--bg3);border:1px solid var(--border);
  border-radius:10px;color:var(--text);
  font-family:'DM Sans',sans-serif;
  outline:none;transition:all .2s;padding:0;
}
.otp-box:focus{border-color:rgba(229,9,20,.6);}
.otp-box.filled{background:rgba(229,9,20,.12);border-color:rgba(229,9,20,.6);color:var(--accent);}

/* OTP progress bar */
.otp-progress{display:flex;align-items:center;gap:8px;margin-bottom:16px;}
.otp-bar{flex:1;height:3px;background:var(--bg3);border-radius:2px;overflow:hidden;}
.otp-bar-fill{height:100%;background:var(--accent);border-radius:2px;transition:width .3s;}
.otp-bar-count{font-size:11px;color:var(--muted);}

/* Error / success boxes */
.err-box{
  background:rgba(229,9,20,.1);border:1px solid rgba(229,9,20,.3);
  border-radius:8px;padding:10px 14px;
  font-size:13px;color:#ff6b6b;margin-bottom:16px;
}
.success-box{
  background:rgba(0,184,148,.1);border:1px solid rgba(0,184,148,.3);
  border-radius:8px;padding:10px 14px;
  font-size:13px;color:#00b894;margin-bottom:16px;
}

/* Theme toggle button (auth topbar) */
.theme-btn{
  background:var(--bg3);border:1px solid var(--border);
  border-radius:8px;width:36px;height:36px;
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;color:var(--muted);
  position:relative;overflow:hidden;
  transition:transform .12s ease,background .2s;
  padding:0;
}
.theme-btn:active{transform:scale(0.90);}
"""

# ─────────────────────────────────────────────────────────────────
#  JAVASCRIPT
# ─────────────────────────────────────────────────────────────────
JS = """
(function(){if(localStorage.getItem('theme')==='light')document.documentElement.classList.add('light')})();

function toggleThemeFixed(){
  var l=document.documentElement.classList.toggle('light');
  localStorage.setItem('theme',l?'light':'dark');
  var icon=document.getElementById('themeIcon');
  if(icon){
    icon.innerHTML=l
      ?'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 7a5 5 0 100 10A5 5 0 0012 7z"/>'
      :'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>';
  }
}

function openSidebar(){
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('sbOverlay').classList.add('open');
  document.getElementById('hamBtn').classList.add('open');
}
function closeSidebar(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sbOverlay').classList.remove('open');
  document.getElementById('hamBtn').classList.remove('open');
}

var curQ='',curOff=0,nextOff='',curCol='all',curPage=1;
var pMode=localStorage.getItem('posterMode')||'tg';
var LIMIT_VAL = __LIMIT_PLACEHOLDER__;
var activeFid='',activeCol='',cropperInstance=null;

function setCol(e){document.querySelectorAll('.ftab').forEach(t=>t.classList.remove('active'));e.classList.add('active');curCol=e.dataset.col;}
function changePosterMode(){pMode=document.getElementById('posterMode').value;localStorage.setItem('posterMode',pMode);if(curQ)doSearch(curOff);}

function handleThumbError(fileId){
  var box=document.getElementById('poster-box-'+fileId);
  if(box){box.innerHTML='<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#1f1f1f;padding:10px;"><span style="font-size:11px;color:var(--muted);text-align:center;">थंबनेल लोड नहीं हुआ</span></div>';}
}
async function reloadThumb(fileId){
  var timestamp=new Date().getTime();
  var box=document.getElementById('poster-box-'+fileId);
  if(box){box.innerHTML='<img src="/api/thumb?file_id='+fileId+'&retry=true&t='+timestamp+'" class="fc-poster" onerror="handleThumbError(\\''+fileId+'\\')">';}
}
async function triggerCacheFlush(){
  var btn=document.getElementById('flushBtn');
  if(btn){btn.innerText="Flushing RAM...";btn.disabled=true;}
  try{
    await fetch('/api/thumb?file_id=all&retry=true');
    alert('🧹 Koyeb In-Memory Buffer & Global Thumb Cache Cleared Successfully!');
  }catch(e){alert('Cache cleared at backend engine layer.');}
  finally{if(btn){btn.innerText="🧹 Flush RAM Cache";btn.disabled=false;}}
}

/* ── YOUR EXISTING JS (doSearch, pagination, edit modal, cropper, etc.) ── */
/* Paste the rest of your original JS string here, unchanged.               */

/* ════════════════════════════════════════════════════════════════
   BUTTON RIPPLE  — new addition (works on .submit-btn and .ghost-btn)
   ════════════════════════════════════════════════════════════════ */
document.addEventListener('click', function(e){
  var btn = e.target.closest('.submit-btn, .ghost-btn, .theme-btn');
  if (!btn || btn.disabled) return;
  var r = document.createElement('span');
  r.className = 'ripple';
  var rect = btn.getBoundingClientRect();
  r.style.left = (e.clientX - rect.left) + 'px';
  r.style.top  = (e.clientY - rect.top)  + 'px';
  btn.appendChild(r);
  setTimeout(function(){ r.remove(); }, 650);
});
""".replace("__LIMIT_PLACEHOLDER__", str(MAX_WEB_RESULTS))


# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

def _h(html):
    return web.Response(
        text=html.encode('utf-8', 'replace').decode('utf-8'),
        content_type='text/html',
        charset='utf-8'
    )


async def get_auth(req):
    s_user = req.cookies.get('user_session')
    if (s_user
            and hasattr(temp, 'USER_SESSIONS')
            and s_user in temp.USER_SESSIONS
            and temp.USER_SESSIONS[s_user]['expiry'] > time.time()):
        tg_id = temp.USER_SESSIONS[s_user]['tg_id']
        if tg_id in ADMINS:
            return 'admin', tg_id
        return 'user', tg_id
    return None, None


# ─────────────────────────────────────────────────────────────────
#  PAGE BUILDER
# ─────────────────────────────────────────────────────────────────

def build_page(title, body, cls="", active_tab="", role=None):

    # ── Sidebar nav links ──────────────────────────────────────────
    if role == 'admin':
        nav_links = (
            f'<a href="/dashboard" class="sb-link {"active" if active_tab=="dash" else ""}">Home</a>'
            f'<a href="/stats"     class="sb-link {"active" if active_tab=="stats" else ""}">Database Stats</a>'
            f'<a href="/profile"   class="sb-link {"active" if active_tab=="profile" else ""}">Profile Settings</a>'
        )
    elif role == 'user':
        nav_links = (
            f'<a href="/dashboard" class="sb-link {"active" if active_tab=="dash" else ""}">Home</a>'
            f'<a href="/profile"   class="sb-link {"active" if active_tab=="profile" else ""}">Profile Settings</a>'
        )
    else:
        nav_links = ""

    # ── Navigation HTML ────────────────────────────────────────────
    if role:
        # Authenticated pages — sidebar + topbar (unchanged from your original)
        nav = (
            f'<div class="sidebar-overlay" id="sbOverlay" onclick="closeSidebar()"></div>'
            f'<div class="sidebar" id="sidebar">'
            f'  <div class="sb-header">'
            f'    <div class="sb-logo"><span class="nf-icon">F</span> FAST FINDER</div>'
            f'    <button class="sb-close" onclick="closeSidebar()">&#10005;</button>'
            f'  </div>'
            f'  <nav class="sb-nav"><div class="sb-section">Menu</div>{nav_links}</nav>'
            f'  <div class="sb-footer"><a href="/logout" class="sb-logout">Sign Out</a></div>'
            f'</div>'
            f'<div class="topbar">'
            f'  <button class="ham-btn" id="hamBtn" onclick="openSidebar()">'
            f'    <span></span><span></span><span></span>'
            f'  </button>'
            f'  <a class="logo" href="/dashboard"><span class="nf-icon">F</span> FAST FINDER</a>'
            f'  <div class="topbar-right">'
            f'    <button class="theme-btn" onclick="toggleThemeFixed()" title="Toggle theme">'
            f'      <svg id="themeIcon" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            f'        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"'
            f'          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>'
            f'      </svg>'
            f'    </button>'
            f'  </div>'
            f'</div>'
        )
    else:
        # Auth pages (login / register / forgot-password) — minimal topbar
        nav = (
            '<div style="position:absolute;width:100%;display:flex;align-items:center;'
            'justify-content:space-between;padding:16px 24px;z-index:10;">'
            '  <a href="/" style="font-size:20px;font-weight:900;letter-spacing:-.5px;'
            '     text-decoration:none;color:var(--text);display:flex;align-items:center;gap:8px;">'
            '    <span class="nf-icon" style="font-size:14px;width:28px;height:28px;border-radius:6px;">F</span>'
            '    FAST FINDER'
            '  </a>'
            '  <button class="theme-btn" onclick="toggleThemeFixed()" title="Toggle theme">'
            '    <svg id="themeIcon" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            '      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"'
            '        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>'
            '    </svg>'
            '  </button>'
            '</div>'
        )

    # ── Admin-only edit modal ──────────────────────────────────────
    modals = (
        """
        <div class="edit-modal" id="editCombinedModal"
             onclick="if(event.target===this)closeCombinedModal()">
          <div class="em-card">
            <button class="em-close" onclick="closeCombinedModal()">&#10005;</button>
            <div class="em-title">✏️ Edit Title Metadata</div>
            <div class="scard-label">File Name</div>
            <input type="text" id="emName" class="em-input">
            <div class="scard-label">Poster Thumbnail (YouTube Studio Mode)</div>
            <div class="thumb-preview-box" id="emPreviewBox"></div>
            <div class="cropper-container-box" id="cropContainer"></div>
            <label class="em-upload-btn">
              📂 Choose New Image / Poster
              <input type="file" id="emFile" accept="image/*" style="display:none;"
                     onchange="handleLocalPreview(this)">
            </label>
            <button class="em-save-btn" id="emSaveBtn" onclick="saveAllChanges()">Save Changes</button>
          </div>
        </div>
        """
        if role == 'admin' else ""
    )

    # ── Full HTML document ─────────────────────────────────────────
    return _h(
        f'<!DOCTYPE html><html lang="en">'
        f'<head>'
        f'  <title>{title}</title>'
        f'  <meta name="viewport" content="width=device-width,initial-scale=1">'
        f'  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">'
        f'  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css">'
        f'  <style>{CSS}</style>'
        f'  <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js"></script>'
        f'  <script>{JS}</script>'
        f'</head>'
        f'<body class="{cls}">'
        f'  {nav}'
        f'  {body}'
        f'  {modals}'
        f'</body>'
        f'</html>'
    )


# ─────────────────────────────────────────────────────────────────
#  FORM WRAPPER  (auth pages)
# ─────────────────────────────────────────────────────────────────

def form_wrapper(title, content, err="", msg=""):
    e = f'<div class="err-box">{err}</div>'     if err else ""
    m = f'<div class="success-box">{msg}</div>' if msg else ""
    return (
        f'<div class="login-bg">'
        f'  <div class="login-wrap">'
        f'    <div class="login-card">'
        f'      <h2>{title}</h2>'
        f'      {e}{m}{content}'
        f'    </div>'
        f'  </div>'
        f'</div>'
    )
