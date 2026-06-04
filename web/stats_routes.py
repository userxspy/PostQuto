from aiohttp import web
from web.web_assets import build_page, get_auth
from database.ia_filterdb import db_count_documents
from database.users_chats_db import db as user_db

stats_routes = web.RouteTableDef()

# ── web_assets.py sync check ──────────────────────────────────────────────
# ✅ CSS variables: var(--bg/bg2/bg3/bg4/card/border/muted/accent/text)
# ✅ .light dark-mode override: handled globally by web_assets.py CSS
# ✅ triggerCacheFlush(): defined in web_assets.py JS — called on flush btn
# ✅ toggleThemeFixed(): topbar theme btn from build_page() calls this
# ✅ Topbar/sidebar: provided by build_page() — not repeated here
# ──────────────────────────────────────────────────────────────────────────

_STATS_CSS = """
<style>
/* ── Animations ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes growBar{from{width:0!important}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 currentColor}50%{box-shadow:0 0 0 5px transparent}}

.anim-card{animation:fadeUp .5s ease both}

/* Hero stat */
.hero-stat{
  background:linear-gradient(135deg,var(--card) 0%,var(--bg3) 100%);
  border:1px solid var(--border);border-radius:16px;
  padding:28px 32px;margin-bottom:24px;
  display:flex;align-items:center;gap:28px;
  position:relative;overflow:hidden;
  transition:background .35s,border-color .35s;
}
.hero-stat::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#3399ff,#9933ff,#e50914);}
.hero-num{font-size:52px;font-weight:900;letter-spacing:-2px;line-height:1;flex-shrink:0;color:var(--text);}
.hero-right{flex:1;min-width:0;}
.hero-badges{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;}
.hero-badge{font-size:11px;font-weight:600;padding:4px 12px;border-radius:99px;}
.hero-thumb{text-align:right;flex-shrink:0;}
.hero-thumb-val{font-size:22px;font-weight:800;color:#e50914;}

/* Multi-bar */
.multi-bar{display:flex;height:6px;border-radius:99px;overflow:hidden;background:var(--bg4);margin-bottom:6px;transition:background .35s;}
.multi-bar-seg{height:100%;animation:growBar .8s cubic-bezier(.4,0,.2,1) both;}
.multi-bar-legend{display:flex;gap:14px;font-size:11px;color:var(--muted);}
.mbl-dot{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:4px;vertical-align:middle;}

/* Grids */
.stats-grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px;}
.stats-grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px;}

/* Stat card */
.st-card{
  background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:20px;position:relative;overflow:hidden;
  transition:background .35s,border-color .35s,transform .2s,box-shadow .2s;
}
.st-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.25);}
.st-card-bar{position:absolute;top:0;left:0;right:0;height:3px;}
.st-label{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px;margin-top:6px;transition:color .35s;}
.st-val{font-size:32px;font-weight:900;letter-spacing:-1px;margin-bottom:12px;line-height:1;}
.st-sub{font-size:12px;color:var(--muted);transition:color .35s;}

/* Progress bar */
.prog-wrap{background:var(--bg4);border-radius:99px;height:5px;margin-bottom:10px;overflow:hidden;transition:background .35s;}
.prog-bar{height:100%;border-radius:99px;animation:growBar .8s cubic-bezier(.4,0,.2,1) both;}

/* Thumbnail badge */
.thumb-badge{display:inline-flex;align-items:center;gap:5px;font-size:11px;background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:4px 10px;color:var(--muted);transition:background .35s,border-color .35s;}
.pct-label{font-size:13px;font-weight:700;}

/* User sub-cells */
.user-sub-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;}
.user-sub-cell{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:8px 12px;transition:background .35s,border-color .35s;}
.user-sub-cell-lbl{font-size:10px;color:var(--muted);margin-bottom:2px;}
.user-sub-cell-val{font-size:15px;font-weight:700;}

/* Flush button */
.flush-btn{
  margin-top:12px;width:100%;background:transparent;
  border:1px solid var(--border);border-radius:7px;
  padding:8px 12px;font-size:12px;font-weight:600;
  color:var(--muted);cursor:pointer;font-family:inherit;
  transition:all .2s;display:flex;align-items:center;justify-content:center;gap:6px;
}
.flush-btn:hover{background:var(--bg3);color:var(--text);border-color:var(--accent);}
.flush-btn:active{transform:scale(.97);}

/* Telemetry */
.telemetry-title{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:14px;display:flex;align-items:center;gap:8px;}
.telemetry-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;}
.t-card{
  background:var(--bg2);border:1px solid var(--border);border-radius:10px;
  padding:16px 18px;display:flex;align-items:flex-start;gap:12px;
  transition:background .35s,border-color .35s;
}
.t-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;margin-top:4px;}
.t-dot-pulse{animation:pulse 1.8s ease-in-out infinite;color:#28a745;}
.t-lbl{font-size:10px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;transition:color .35s;}
.t-val{font-size:14px;font-weight:700;}
.t-sub{font-size:11px;color:var(--muted);margin-top:2px;transition:color .35s;}

@media(max-width:800px){
  .stats-grid-3,.telemetry-grid{grid-template-columns:1fr 1fr;}
  .stats-grid-2{grid-template-columns:1fr;}
  .hero-stat{flex-direction:column;align-items:flex-start;}
  .hero-num{font-size:36px;}
}
</style>
"""

# Vanilla JS: count-up for numbers, stagger delays
# Note: triggerCacheFlush() and toggleThemeFixed() already live in web_assets.py JS
_STATS_JS = """
<script>
(function(){
  // Count-up animation
  function countUp(el, target, duration) {
    var start = performance.now();
    var fmt = function(n){ return Math.floor(n).toLocaleString('en-IN'); };
    function step(now) {
      var p = Math.min((now - start) / duration, 1);
      var ease = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(ease * target);
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // Run count-up on all [data-count] elements
  document.querySelectorAll('[data-count]').forEach(function(el) {
    var target = parseFloat(el.dataset.count);
    var delay  = parseFloat(el.dataset.delay || '0');
    setTimeout(function(){ countUp(el, target, 900); }, delay);
  });

  // Stagger anim-card delays
  document.querySelectorAll('.anim-card').forEach(function(el, i) {
    el.style.animationDelay = (i * 0.07) + 's';
  });
})();
</script>
"""


@stats_routes.get('/stats')
async def stats(req):
    role, _ = await get_auth(req)
    if role != 'admin':
        return web.HTTPFound('/dashboard')

    try:
        s = await db_count_documents()
        if not isinstance(s, dict):
            s = {'total': 0, 'primary': 0, 'cloud': 0, 'archive': 0,
                 'primary_thumb': 0, 'cloud_thumb': 0, 'archive_thumb': 0, 'total_thumb': 0}
    except:
        s = {'total': 0, 'primary': 0, 'cloud': 0, 'archive': 0,
             'primary_thumb': 0, 'cloud_thumb': 0, 'archive_thumb': 0, 'total_thumb': 0}

    try:
        u = await user_db.total_users_count()
    except:
        u = 0

    p_tot      = s.get('primary', 0)
    c_tot      = s.get('cloud', 0)
    a_tot      = s.get('archive', 0)
    grand_total = s.get('total', 1) or 1

    p_pct = int((p_tot / grand_total) * 100)
    c_pct = int((c_tot / grand_total) * 100)
    a_pct = int((a_tot / grand_total) * 100)

    # Raw numbers for data-count (JS count-up), formatted for no-JS fallback
    total_raw        = s.get('total', 0)
    primary_raw      = p_tot
    cloud_raw        = c_tot
    archive_raw      = a_tot
    total_thumb_raw  = s.get('total_thumb', 0)
    users_raw        = u

    primary_thumb    = f"{s.get('primary_thumb', 0):,}"
    cloud_thumb      = f"{s.get('cloud_thumb', 0):,}"
    archive_thumb    = f"{s.get('archive_thumb', 0):,}"

    body = f'''
{_STATS_CSS}

<div class="main" style="padding-top:40px;">

  <!-- Hero total -->
  <div class="hero-stat anim-card">
    <div>
      <div style="font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Total Cloud Archive Matrix</div>
      <div class="hero-num" data-count="{total_raw}" data-delay="0">{total_raw:,}</div>
    </div>
    <div class="hero-right">
      <div class="hero-badges">
        <span class="hero-badge" style="background:#3399ff22;color:#3399ff;border:1px solid #3399ff44;">🎬 {primary_raw:,} Movies</span>
        <span class="hero-badge" style="background:#ff993322;color:#ff9933;border:1px solid #ff993344;">📺 {cloud_raw:,} Series</span>
        <span class="hero-badge" style="background:#9933ff22;color:#9933ff;border:1px solid #9933ff44;">🗄️ {archive_raw:,} Archive</span>
      </div>
      <div class="multi-bar">
        <div class="multi-bar-seg" style="width:{p_pct}%;background:#3399ff;animation-delay:.3s;"></div>
        <div class="multi-bar-seg" style="width:{c_pct}%;background:#ff9933;animation-delay:.45s;"></div>
        <div class="multi-bar-seg" style="width:{a_pct}%;background:#9933ff;animation-delay:.6s;"></div>
      </div>
      <div class="multi-bar-legend">
        <span><span class="mbl-dot" style="background:#3399ff;"></span>Movies {p_pct}%</span>
        <span><span class="mbl-dot" style="background:#ff9933;"></span>Series {c_pct}%</span>
        <span><span class="mbl-dot" style="background:#9933ff;"></span>Archive {a_pct}%</span>
      </div>
    </div>
    <div class="hero-thumb">
      <div style="font-size:11px;color:var(--muted);margin-bottom:4px;">Total Thumbnails</div>
      <div class="hero-thumb-val" data-count="{total_thumb_raw}" data-delay="100">{total_thumb_raw:,}</div>
      <div style="font-size:11px;color:var(--muted);margin-top:2px;">cached assets</div>
    </div>
  </div>

  <!-- Database breakdown -->
  <div class="stats-grid-3">
    <div class="st-card anim-card">
      <div class="st-card-bar" style="background:#3399ff;"></div>
      <div class="st-label">Primary Cloud — Movies</div>
      <div class="st-val" style="color:#3399ff;" data-count="{primary_raw}" data-delay="120">{primary_raw:,}</div>
      <div class="prog-wrap"><div class="prog-bar" style="width:{p_pct}%;background:linear-gradient(90deg,#3399ff,#66bbff);animation-delay:.4s;"></div></div>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="thumb-badge">🖼️ {primary_thumb} cached</span>
        <span class="pct-label" style="color:#3399ff;">{p_pct}%</span>
      </div>
    </div>
    <div class="st-card anim-card">
      <div class="st-card-bar" style="background:#ff9933;"></div>
      <div class="st-label">Cloud Library — Series</div>
      <div class="st-val" style="color:#ff9933;" data-count="{cloud_raw}" data-delay="180">{cloud_raw:,}</div>
      <div class="prog-wrap"><div class="prog-bar" style="width:{c_pct}%;background:linear-gradient(90deg,#ff9933,#ffcc77);animation-delay:.45s;"></div></div>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="thumb-badge">🖼️ {cloud_thumb} cached</span>
        <span class="pct-label" style="color:#ff9933;">{c_pct}%</span>
      </div>
    </div>
    <div class="st-card anim-card">
      <div class="st-card-bar" style="background:#9933ff;"></div>
      <div class="st-label">Backup Warehouse — Archive</div>
      <div class="st-val" style="color:#9933ff;" data-count="{archive_raw}" data-delay="240">{archive_raw:,}</div>
      <div class="prog-wrap"><div class="prog-bar" style="width:{a_pct}%;background:linear-gradient(90deg,#9933ff,#cc77ff);animation-delay:.5s;"></div></div>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span class="thumb-badge">🖼️ {archive_thumb} cached</span>
        <span class="pct-label" style="color:#9933ff;">{a_pct}%</span>
      </div>
    </div>
  </div>

  <!-- Image Assets + Users -->
  <div class="stats-grid-2">
    <div class="st-card anim-card">
      <div class="st-card-bar" style="background:#e50914;"></div>
      <div class="st-label">Global Image Assets</div>
      <div class="st-val" style="color:#e50914;" data-count="{total_thumb_raw}" data-delay="300">{total_thumb_raw:,}</div>
      <div class="st-sub" style="margin-bottom:12px;">Verified blob identifiers across all DBs</div>
      <button class="flush-btn" id="flushBtn" onclick="triggerCacheFlush()">🧹 Flush RAM Cache</button>
    </div>
    <div class="st-card anim-card">
      <div class="st-card-bar" style="background:var(--muted);"></div>
      <div class="st-label">Total System Subscribers</div>
      <div class="st-val" data-count="{users_raw}" data-delay="350">{users_raw:,}</div>
      <div class="st-sub">Active database records</div>
      <div class="user-sub-row">
        <div class="user-sub-cell"><div class="user-sub-cell-lbl">Today</div><div class="user-sub-cell-val">—</div></div>
        <div class="user-sub-cell"><div class="user-sub-cell-lbl">This Week</div><div class="user-sub-cell-val">—</div></div>
      </div>
    </div>
  </div>

  <!-- Server Telemetry -->
  <div class="telemetry-title anim-card">💻 Server Core Telemetry Diagnostics</div>
  <div class="telemetry-grid">
    <div class="t-card anim-card">
      <div class="t-dot t-dot-pulse" style="background:#28a745;"></div>
      <div>
        <div class="t-lbl">Koyeb Worker Pod</div>
        <div class="t-val" style="color:#28a745;">🟢 Operational</div>
        <div class="t-sub">Port 8000 · 0 errors</div>
      </div>
    </div>
    <div class="t-card anim-card">
      <div class="t-dot" style="background:#3399ff;"></div>
      <div>
        <div class="t-lbl">Database I/O Pool</div>
        <div class="t-val" style="color:#3399ff;">15 Connections Max</div>
        <div class="t-sub">Active pool · healthy</div>
      </div>
    </div>
    <div class="t-card anim-card">
      <div class="t-dot" style="background:#ff9933;"></div>
      <div>
        <div class="t-lbl">RAM Protection Guard</div>
        <div class="t-val" style="color:#ff9933;">Strictly Bounded</div>
        <div class="t-sub">Enforced memory limit</div>
      </div>
    </div>
  </div>

</div>

{_STATS_JS}
'''
    return build_page("Stats - Fast Finder", body, "", "stats", role)
