import logging
import asyncio
import re
import time
import gc
import pytz
from datetime import datetime, timedelta
from hydrogram.errors import FloodWait
from hydrogram import enums

from info import ADMINS, IS_PREMIUM, TIME_ZONE
from database.users_chats_db import db

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🧠 TEMP RUNTIME STORAGE (Central context bucket)
# ─────────────────────────────────────────────
class temp(object):
    START_TIME = 0
    BANNED_USERS, BANNED_CHATS = [], []
    ME, BOT, U_NAME, B_NAME = None, None, None, None
    CANCEL = False 
    ADMIN_TOKENS, ADMIN_SESSIONS, FILES, PM_FILES = {}, {}, {}, {}

# ─────────────────────────────────────────────
# 🛡️ RATE LIMITER UTILITY (Aggressive RAM Flush Sync)
# ─────────────────────────────────────────────
_rate_limits = {}

def is_rate_limited(user_id, action, seconds):
    """हैवी प्रीमियम कमांड्स पर स्पैम रोकता है और रैम को फ़ोर्स फ्लश करता है।"""
    key = f"{user_id}:{action}"
    now = time.time()
    
    # स्मार्ट पीरियोдिक क्लीनअप (Koyeb RAM Safe Protection)
    if len(_rate_limits) > 300: # रैम लीक गार्ड थ्रेशोल्ड लिमिट 300 पर लॉक
        cutoff = now - 60 
        expired_keys = [k for k, v in _rate_limits.items() if v < cutoff]
        for k in expired_keys:
            _rate_limits.pop(k, None)
        # ✅ FIX: अन-रेफ़रेंस्ड ऑब्जेक्ट्स को कोएब की रैम से तुरंत साफ़ करने के लिए गारबेज कलेक्शन
        gc.collect()
            
    if key in _rate_limits and now - _rate_limits[key] < seconds:
        return True
        
    _rate_limits[key] = now
    return False

# ─────────────────────────────────────────────
# 👮 BOT CHAT ADMIN LOOKUP GUARD
# ─────────────────────────────────────────────
async def is_check_admin(bot, chat_id, user_id):
    try:
        return (await bot.get_chat_member(chat_id, user_id)).status in (
            enums.ChatMemberStatus.ADMINISTRATOR, 
            enums.ChatMemberStatus.OWNER
        )
    except: 
        return False

# ─────────────────────────────────────────────
# 💎 PREMIUM AUTO-VALIDATOR (Perfect info.py TIME_ZONE Sync)
# ─────────────────────────────────────────────
async def is_premium(user_id, bot=None):
    # एडमिन को हमेशा लाइफटाइम बाईपास अनलॉक रहेगा
    if not IS_PREMIUM or user_id in ADMINS: 
        return True
        
    mp = await db.get_plan(user_id)
    if not mp.get("premium"): 
        return False
    
    expire = mp.get("expire")
    if expire:
        if isinstance(expire, str):
            try: 
                expire = datetime.strptime(expire, "%Y-%m-%d %H:%M:%S")
            except: 
                expire = None
        
        # ✅ FIX: हार्डकोडिंग हटाकर 'info.py' के कस्टमाइज्ड 'TIME_ZONE' से शुद्ध सिंक कॉम्पैरिजन
        local_tz = pytz.timezone(TIME_ZONE)
        now_local = datetime.now(local_tz).replace(tzinfo=None)
        
        if not expire or expire < now_local:
            if bot:
                try: 
                    await bot.send_message(user_id, f"❌ <b>Your Premium Membership Plan has Expired!</b>\n\nContact Admin or use /plan to activate again.")
                except: 
                    pass
            
            # प्रीमियम ख़त्म होते ही डेटाबेस में सारे रिमाइंडर फ़्लैग्स और स्टेटस को तुरंत रिफ्रेश/रीसेट करें
            await db.update_plan(user_id, {
                "expire": None, 
                "plan": "", 
                "premium": False,
                "reminded_12h": False, 
                "reminded_6h": False, 
                "reminded_3h": False, 
                "reminded_1h": False, 
                "reminded_30m": False, 
                "reminded_10m": False,
                "last_reminder_id": 0
            })
            return False
    return True

# ❌ FIX: 'broadcast_messages' (पुराना भारी ब्रॉडकास्ट इंजन कबाड़) पूरी तरह डिलीटेड। 
# इससे नो-रिपिटिशन रूल और क्लीन आर्किटेक्चर लागू होता है।

# ─────────────────────────────────────────────
# ⚙️ TTL SETTINGS CACHE (Bounded Memory Leak Proof)
# ─────────────────────────────────────────────
_settings_cache = {}
_CACHE_TTL = 300 

async def get_settings(group_id):
    now = time.time()
    if group_id in _settings_cache:
        data, ts = _settings_cache[group_id]
        if now - ts < _CACHE_TTL:
            return data
            
    data = await db.get_settings(group_id)
    
    # ✅ FIX: इन-मेमोरी डिक्शनरी को अनकैप्ड बढ़ने से रोकने के लिए बाउंडेड कैशे गार्ड
    if len(_settings_cache) > 200:
        _settings_cache.clear()
        gc.collect()
        
    _settings_cache[group_id] = (data, now)
    return data

async def save_group_settings(group_id, key, value):
    data = await get_settings(group_id)
    data[key] = value
    _settings_cache[group_id] = (data, time.time())
    await db.update_settings(group_id, data)

# ─────────────────────────────────────────────
# 📦 FORMATTING & RAIN TIME UTILS
# ─────────────────────────────────────────────
def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size, i = float(size), 0
    while size >= 1024 and i < 4:
        size, i = size / 1024, i + 1
    return f"{size:.2f} {units[i]}"

def get_readable_time(seconds):
    res, periods = "", [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    for name, sec in periods:
        if seconds >= sec:
            val, seconds = divmod(seconds, sec)
            res += f"{int(val)}{name} "
    return res.strip() or "0s"

def get_wish():
    # ✅ FIX: कचरा टेक्स्ट और अशुद्धियों को हटाकर कस्टमाइज्ड टाइमज़ोन विश इंजन सिंक किया गया
    tz = pytz.timezone(TIME_ZONE)
    h = datetime.now(tz).hour
    return "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞" if h < 12 else "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ 🌗" if h < 18 else "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"

async def get_seconds(time_string):
    match = re.match(r"(\d+)(s|min|hour|day|month|year)", time_string)
    if not match: 
        return 0
    return int(match.group(1)) * {
        "s": 1, "min": 60, "hour": 3600, "day": 86400,
        "month": 2592000, "year": 31536000
    }.get(match.group(2), 0)

# 🛠️ PREMIUM LIFECYCLE TIME PARSERS
def parse_expire_time(e):
    if isinstance(e, datetime): 
        return e
    try: 
        return datetime.strptime(e, "%Y-%m-%d %H:%M:%S") if e else None
    except: 
        return None

def get_ist_str(dt):
    # ग्लोबल रिफॉर्मेटेड पठनीय स्ट्रिंग रिपॉजिटरी रेंडरर
    return (dt + timedelta(hours=5, minutes=30)).strftime("%d %B %Y, %I:%M %p") if dt else "Unknown"

async def safe_del(c, cid, mids):
    try: 
        await c.delete_messages(cid, mids)
    except: 
        pass
