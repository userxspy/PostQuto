from aiohttp import web
from web.web_assets import build_page, get_auth
from database.users_chats_db import db as user_db, web_db, hash_password

profile_routes = web.RouteTableDef()

@profile_routes.get('/profile')
async def profile_page(req):
    role, tg_id = await get_auth(req)
    if not role: return web.HTTPFound('/login')
    user = await web_db.col.find_one({"tg_id": tg_id}, {"email": 1})
    email = user.get('email', '') if user else ''
    err, msg = req.query.get('err',''), req.query.get('msg','')
    mp = await user_db.get_plan(tg_id)
    if role == 'admin': status_text, exp_text, status_color = "👑 Admin (Lifetime Access)", "Never (Lifetime)", "#e50914" 
    else: status_text, exp_text, status_color = "💎 Premium User", mp.get('expire', 'Unknown'), "#3399ff" 
    
    b = f'''<div class="main" style="padding-top:40px; max-width:700px;"><div class="scard">{f'<div class="err-box">{err}</div>' if err else ""}{f'<div class="success-box">{msg}</div>' if msg else ""}<h2 style="margin-bottom:25px;">Account Settings</h2><div style="background:var(--bg3); padding:15px; border-radius:4px; margin-bottom:25px; border-left:4px solid {status_color};"><div style="font-size:12px; color:var(--muted); margin-bottom:5px;">Account Status</div><div style="font-size:18px; font-weight:700; color:{status_color}; margin-bottom:10px;">{status_text}</div><div style="font-size:12px; color:var(--muted); margin-bottom:2px;">Premium Expires:</div><div style="font-size:15px; font-weight:500;">{exp_text}</div></div><form action="/api/update_profile" method="post"><div class="scard-label">Telegram ID (Non-changeable)</div><input type="text" value="{tg_id}" class="search-input" style="margin-bottom:20px; opacity:0.6" disabled><div class="scard-label">Email Address</div><input type="email" name="new_email" value="{email}" class="search-input" style="margin-bottom:20px;" required><div class="scard-label">New Password (Leave blank to keep current)</div><input type="password" name="new_pass" placeholder="Enter New Password" class="search-input" style="margin-bottom:30px;"><button class="search-btn" style="width:100%" type="submit">Save Changes</button></form></div></div>'''
    return build_page("Profile - Fast Finder", b, "", "profile", role)

@profile_routes.post('/api/update_profile')
async def api_update_profile(req):
    role, tg_id = await get_auth(req)
    if not role: return web.HTTPFound('/login')
    
    d = await req.post()
    new_email = d.get('new_email', '').strip()
    new_pass = d.get('new_pass', '').strip()
    
    if not new_email: return web.HTTPFound('/profile?err=Email cannot be empty!')
        
    existing = await web_db.col.find_one({"email": new_email, "tg_id": {"$ne": tg_id}}, {"_id": 1})
    if existing: return web.HTTPFound('/profile?err=This email is already in use by another account!')

    update_data = {"email": new_email}
    if new_pass: update_data["password"] = hash_password(new_pass)

    try:
        await web_db.col.update_one({"tg_id": tg_id}, {"$set": update_data})
        return web.HTTPFound('/profile?msg=Profile updated successfully!')
    except Exception as e:
        return web.HTTPFound(f'/profile?err=Update failed: {str(e)}')
