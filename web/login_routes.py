import uuid
import random
import time
from aiohttp import web
from web.web_assets import build_page, form_wrapper
from utils import temp
from database.users_chats_db import web_db

login_routes = web.RouteTableDef()


# ───────────────────────────────────────────────
#  LOGIN
# ───────────────────────────────────────────────

@login_routes.get('/login')
async def login_user(req):
    content = '''
<p class="sub">Sign in to your dashboard</p>
<form action="/api/login" method="post">
    <div class="form-group">
        <div>
            <label class="field-label">Email Address</label>
            <div class="input-wrap">
                <span class="inp-icon">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
                    </svg>
                </span>
                <input type="email" name="email" placeholder="you@example.com" required>
            </div>
        </div>
        <div>
            <label class="field-label">Password</label>
            <div class="input-wrap pw-wrap">
                <span class="inp-icon">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                </span>
                <input type="password" name="password" placeholder="&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;"
                    id="loginPw" required style="padding-right:42px;">
                <button type="button" class="pw-toggle"
                    onclick="var f=document.getElementById('loginPw');f.type=f.type==='password'?'text':'password';">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                </button>
            </div>
        </div>
        <div class="forgot-link"><a href="/forgot_password">Forgot password?</a></div>
        <button class="submit-btn" type="submit">Sign In</button>
    </div>
</form>
<hr class="card-divider">
<p class="card-footer">Don\'t have an account? <a href="/register">Create account</a></p>
'''
    err = req.query.get('err', '')
    msg = req.query.get('msg', '')
    return build_page("Sign In", form_wrapper("Welcome back", content, err, msg), "login-bg")


@login_routes.post('/api/login')
async def api_login_user(req):
    d = await req.post()
    user = await web_db.verify_login(d.get('email'), d.get('password'))
    if user:
        s = str(uuid.uuid4())
        if not hasattr(temp, 'USER_SESSIONS'):
            temp.USER_SESSIONS = {}
        temp.USER_SESSIONS[s] = {'tg_id': user['tg_id'], 'expiry': time.time() + 86400 * 7}
        res = web.HTTPFound('/dashboard')
        res.set_cookie('user_session', s, max_age=86400 * 7)
        return res
    return web.HTTPFound('/login?err=Invalid email or password. Please try again.')


# ───────────────────────────────────────────────
#  REGISTER
# ───────────────────────────────────────────────

@login_routes.get('/register')
async def register_user(req):
    content = '''
<p class="sub">Link your Telegram account to get started</p>
<div class="info-banner">
    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    Start the bot on Telegram first. A 6-digit OTP will be sent to your DM.
</div>
<form action="/api/register_step1" method="post">
    <div class="form-group">
        <div>
            <label class="field-label">Telegram ID</label>
            <div class="input-wrap">
                <span class="inp-icon">&#128241;</span>
                <input type="number" name="tg_id" placeholder="e.g. 123456789" required>
            </div>
        </div>
        <div>
            <label class="field-label">Email Address</label>
            <div class="input-wrap">
                <span class="inp-icon">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"/>
                    </svg>
                </span>
                <input type="email" name="email" placeholder="you@example.com" required>
            </div>
        </div>
        <div>
            <label class="field-label">Create Password</label>
            <div class="input-wrap">
                <span class="inp-icon">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                </span>
                <input type="password" name="password" placeholder="&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;&#x2022;" required>
            </div>
        </div>
        <button class="submit-btn" type="submit">Send OTP via Telegram</button>
    </div>
</form>
<hr class="card-divider">
<p class="card-footer">Already have an account? <a href="/login">Sign in</a></p>
'''
    err = req.query.get('err', '')
    return build_page("Create Account", form_wrapper("Create account", content, err), "login-bg")


@login_routes.post('/api/register_step1')
async def api_register_step1(req):
    d = await req.post()
    try:
        tg_id = int(d.get('tg_id'))
    except Exception:
        return web.HTTPFound('/register?err=Invalid Telegram ID')

    email, password = d.get('email'), d.get('password')

    if await web_db.col.find_one({"$or": [{"tg_id": tg_id}, {"email": email}]}, {"_id": 1}):
        return web.HTTPFound('/register?err=Telegram ID or Email is already registered!')

    otp = str(random.randint(100000, 999999))
    now = time.time()
    if not hasattr(temp, 'REG_PENDING'):
        temp.REG_PENDING = {}
    temp.REG_PENDING[tg_id] = {
        'email': email, 'password': password,
        'otp': otp, 'expiry': now + 300
    }
    try:
        await temp.BOT.send_message(
            tg_id,
            f"🔐 **Web Registration Verification**\n\n"
            f"Someone is trying to link your Telegram ID to: `{email}`\n\n"
            f"**Your OTP is:** `{otp}`\n\n_Valid for 5 minutes._"
        )
    except Exception:
        return web.HTTPFound('/register?err=Failed to send OTP. Please start the Bot first in Telegram.')
    return web.HTTPFound(f'/verify_registration?tg_id={tg_id}')


# ───────────────────────────────────────────────
#  VERIFY OTP (Registration)
# ───────────────────────────────────────────────

@login_routes.get('/verify_registration')
async def verify_registration_page(req):
    tg_id = req.query.get('tg_id', '')
    if not tg_id:
        return web.HTTPFound('/register')

    content = f'''
<p class="sub">Check your Telegram DM for a 6-digit code</p>
<form action="/api/register_step2" method="post" id="otpForm">
    <input type="hidden" name="tg_id" value="{tg_id}">
    <div class="otp-row">
        <input class="otp-box" type="text" inputmode="numeric" maxlength="1"
            id="o0" oninput="otpNext(this,0)" onkeydown="otpBack(event,0)">
        <input class="otp-box" type="text" inputmode="numeric" maxlength="1"
            id="o1" oninput="otpNext(this,1)" onkeydown="otpBack(event,1)">
        <input class="otp-box" type="text" inputmode="numeric" maxlength="1"
            id="o2" oninput="otpNext(this,2)" onkeydown="otpBack(event,2)">
        <input class="otp-box" type="text" inputmode="numeric" maxlength="1"
            id="o3" oninput="otpNext(this,3)" onkeydown="otpBack(event,3)">
        <input class="otp-box" type="text" inputmode="numeric" maxlength="1"
            id="o4" oninput="otpNext(this,4)" onkeydown="otpBack(event,4)">
        <input class="otp-box" type="text" inputmode="numeric" maxlength="1"
            id="o5" oninput="otpNext(this,5)" onkeydown="otpBack(event,5)">
    </div>
    <div class="otp-progress">
        <div class="otp-bar">
            <div class="otp-bar-fill" id="otpBar" style="width:0%"></div>
        </div>
        <span class="otp-bar-count" id="otpCount">0/6</span>
    </div>
    <input type="hidden" name="otp" id="otpHidden">
    <button class="submit-btn" type="submit" id="otpBtn"
        disabled style="opacity:.4;cursor:not-allowed;">
        Verify &amp; Create Account
    </button>
</form>
<p style="text-align:center;font-size:12px;color:var(--muted);margin-top:14px;">
    Didn\'t receive OTP?
    <a href="/register" style="color:var(--accent);text-decoration:none;">Resend</a>
    &nbsp;&middot;&nbsp;
    <a href="/register" style="color:var(--muted);text-decoration:none;">Go back</a>
</p>
<p style="text-align:center;font-size:11px;color:var(--bg4);margin-top:6px;">
    OTP expires in 5 minutes
</p>
<script>
function otpNext(el, i) {{
    if (!/^\d?$/.test(el.value)) {{ el.value = ''; return; }}
    el.classList.toggle('filled', el.value !== '');
    updateOtp();
    if (el.value && i < 5) document.getElementById('o' + (i + 1)).focus();
}}
function otpBack(e, i) {{
    if (e.key === 'Backspace' && !document.getElementById('o' + i).value && i > 0)
        document.getElementById('o' + (i - 1)).focus();
}}
function updateOtp() {{
    var val = '', count = 0;
    for (var i = 0; i < 6; i++) {{
        var v = document.getElementById('o' + i).value;
        val += v;
        if (v) count++;
    }}
    document.getElementById('otpHidden').value = val;
    document.getElementById('otpBar').style.width = (count / 6 * 100) + '%';
    document.getElementById('otpCount').innerText = count + '/6';
    var btn = document.getElementById('otpBtn');
    btn.disabled = count < 6;
    btn.style.opacity = count < 6 ? '.4' : '1';
    btn.style.cursor = count < 6 ? 'not-allowed' : 'pointer';
}}
</script>
'''
    err = req.query.get('err', '')
    return build_page(
        "Verify OTP",
        form_wrapper("Verify OTP", content, err),
        "login-bg"
    )


@login_routes.post('/api/register_step2')
async def api_register_step2(req):
    d = await req.post()
    try:
        tg_id = int(d.get('tg_id'))
    except Exception:
        return web.HTTPFound('/register?err=Invalid Request')

    otp = d.get('otp')
    if tg_id not in getattr(temp, 'REG_PENDING', {}):
        return web.HTTPFound('/register?err=Session expired. Please try again.')

    pending = temp.REG_PENDING[tg_id]
    if time.time() > pending['expiry']:
        del temp.REG_PENDING[tg_id]
        return web.HTTPFound('/register?err=OTP expired. Please restart registration.')
    if pending['otp'] != otp:
        return web.HTTPFound(f'/verify_registration?tg_id={tg_id}&err=Invalid OTP. Please try again.')

    success, msg = await web_db.create_user(tg_id, pending['email'], pending['password'])
    del temp.REG_PENDING[tg_id]
    if success:
        return web.HTTPFound('/login?msg=Account created successfully! Please sign in.')
    return web.HTTPFound(f'/register?err={msg}')


# ───────────────────────────────────────────────
#  FORGOT / RESET PASSWORD
# ───────────────────────────────────────────────

@login_routes.get('/forgot_password')
async def forgot_password(req):
    content = '''
<p class="sub">Enter your Telegram ID to receive an OTP, then reset your password below.</p>

<div class="step-row">
    <div class="step-badge">1</div>
    <span class="step-label">Send OTP to Telegram</span>
</div>
<form action="/api/forgot_password" method="post">
    <div class="split-row" style="margin-bottom:20px;">
        <div class="input-wrap">
            <span class="inp-icon">&#128241;</span>
            <input type="number" name="tg_id" placeholder="Your Telegram ID" required>
        </div>
        <button class="ghost-btn" type="submit">Send OTP</button>
    </div>
</form>

<div class="then-divider"><span>then</span></div>

<div class="step-row">
    <div class="step-badge">2</div>
    <span class="step-label" style="color:var(--bg4);">Enter OTP &amp; New Password</span>
</div>
<form action="/api/reset_password" method="post">
    <div class="form-group">
        <div>
            <div class="input-wrap">
                <span class="inp-icon">&#128241;</span>
                <input type="number" name="tg_id" placeholder="Telegram ID" required>
            </div>
        </div>
        <div>
            <div class="input-wrap">
                <span class="inp-icon">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M9 12h6m-3-3v6"/>
                    </svg>
                </span>
                <input type="text" name="otp" placeholder="6-digit OTP" required>
            </div>
        </div>
        <div>
            <div class="input-wrap pw-wrap">
                <span class="inp-icon">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                </span>
                <input type="password" name="new_password" placeholder="New password"
                    id="resetPw" required style="padding-right:42px;">
                <button type="button" class="pw-toggle"
                    onclick="var f=document.getElementById('resetPw');f.type=f.type==='password'?'text':'password';">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                </button>
            </div>
        </div>
        <button class="submit-btn" type="submit">Reset Password</button>
    </div>
</form>
<hr class="card-divider">
<p class="card-footer">
    <a href="/login" style="color:var(--muted);">&#8592; Back to Sign In</a>
</p>
'''
    err = req.query.get('err', '')
    msg = req.query.get('msg', '')
    return build_page(
        "Reset Password",
        form_wrapper("Reset Password", content, err, msg),
        "login-bg"
    )


@login_routes.post('/api/forgot_password')
async def api_forgot_password(req):
    try:
        tg_id = int((await req.post()).get('tg_id'))
    except Exception:
        return web.HTTPFound('/forgot_password?err=Invalid Telegram ID')

    otp = await web_db.generate_otp(tg_id)
    if otp:
        try:
            await temp.BOT.send_message(
                tg_id,
                f"🔐 **Fast Finder Password Reset**\n\n"
                f"Your OTP is: `{otp}`\n\nValid for 10 minutes. Do not share!"
            )
            return web.HTTPFound('/forgot_password?msg=OTP sent to your Telegram!')
        except Exception:
            return web.HTTPFound('/forgot_password?err=Error sending OTP. Have you started the bot?')
    return web.HTTPFound('/forgot_password?err=Telegram ID not registered!')


@login_routes.post('/api/reset_password')
async def api_reset_password(req):
    d = await req.post()
    try:
        tg_id = int(d.get('tg_id'))
    except Exception:
        return web.HTTPFound('/forgot_password?err=Invalid Input')

    if await web_db.verify_otp_and_reset(tg_id, d.get('otp'), d.get('new_password')):
        return web.HTTPFound('/login?msg=Password updated successfully! Please sign in.')
    return web.HTTPFound('/forgot_password?err=Invalid or expired OTP.')
