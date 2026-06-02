import asyncio
import time
import logging
import gc
from hydrogram import Client, filters, enums
from hydrogram.types import ChatPermissions
from database.users_chats_db import db
# नो-रिपिटिशन रूल: कैशे और डेटाबेस को एक साथ सिंक रखने के लिए utils के सेव फंक्शन्स का उपयोग
from utils import get_settings, save_group_settings, is_check_admin, get_seconds, get_readable_time

logger = logging.getLogger(__name__)

# =========================================
# 🛡️ LOCAL SECURITY GUARD
# =========================================
async def is_admin(c, m):
    if m.sender_chat and m.sender_chat.id == m.chat.id: 
        return True
    if not m.from_user: 
        return False
    return await is_check_admin(c, m.chat.id, m.from_user.id)

# =========================================
# 🔨 ADMIN ACTIONS (Auto-Ban on 3rd Warn Synced)
# =========================================
@Client.on_message(filters.group & filters.reply & filters.command(["mute", "unmute", "ban", "warn", "resetwarn"]))
async def admin_action(c, m):
    if not await is_admin(c, m): return
    target = m.reply_to_message.from_user
    if not target: 
        return await m.reply("❌ Cannot perform action on anonymous / channel messages.")

    cmd = m.command[0]
    cid, tid, mention = m.chat.id, target.id, target.mention

    try:
        if cmd == "mute":
            # 10 मिनट के लिए यूजर को म्यूट पर लॉक करें
            await c.restrict_chat_member(cid, tid, ChatPermissions(), until_date=int(time.time() + 600))
            await m.reply(f"🔇 {mention} <b>has been muted for 10 minutes.</b>")
            
        elif cmd == "unmute":
            await c.restrict_chat_member(cid, tid, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
            await m.reply(f"🔊 {mention} <b>has been unmuted successfully.</b>")
            
        elif cmd == "ban":
            await c.ban_chat_member(cid, tid)
            await m.reply(f"🚫 {mention} <b>has been permanently banned from the group.</b>")
            
        elif cmd == "warn":
            # सेफ़ डिक्शनरी गेटर पैच ताकि KeyError क्रैश न आए
            res_data = await db.get_warn(tid, cid)
            warn_count = res_data.get("count", 0) if isinstance(res_data, dict) else 0
            warn_count += 1
            
            if warn_count >= 3:
                # 3 चेतावनियाँ पूरी होने पर ऑटो-बैन सुरक्षा कतार ट्रिगर
                await c.ban_chat_member(cid, tid)
                await db.clear_warn(tid, cid)
                await m.reply(f"🚨 {mention} <b>received 3/3 warnings and has been BANNED from the system!</b>")
            else:
                await db.set_warn(tid, cid, {"count": warn_count})
                await m.reply(f"⚠️ {mention} <b>warned ({warn_count}/3). Keep group decorum safe!</b>")
                
        elif cmd == "resetwarn":
            await db.clear_warn(tid, cid)
            await m.reply(f"♻️ <b>Warnings successfully reset for</b> {mention}.")
            
    except Exception as e:
        logger.error(f"Admin action failed: {e}")
        await m.reply("❌ <b>Action execution failed! Verify Bot administrative privileges.</b>")
    finally:
        gc.collect()

# =========================================
# ⚙️ CONFIGURATION (Blacklist & Timed DLink Sync)
# =========================================
@Client.on_message(filters.group & filters.command(["addblacklist", "removeblacklist", "blacklist", "dlink", "removedlink", "dlinklist"]))
async def config_handler(c, m):
    if not await is_admin(c, m): return
    cmd = m.command[0]
    
    # इन-मेमोरी रैम कैशे इंजन से लाइव ग्रुप सेटिंग्स उठाएं
    data = await get_settings(m.chat.id)
    
    try:
        args = m.text.split(maxsplit=1)[1].strip()
    except IndexError:
        args = ""

    # --- View Structural Lists ---
    if cmd in ["blacklist", "dlinklist"]:
        if cmd == "blacklist":
            items = "\n".join(f"• <code>{w}</code>" for w in data.get("blacklist", [])) or "📭 Empty"
            return await m.reply(f"🚫 <b>Group Blacklisted Keywords:</b>\n\n{items}")
            
        dl_dict = data.get("dlink", {})
        items = "\n".join(f"• <code>{k}</code> (⏳ Trigger: {get_readable_time(v)})" for k, v in dl_dict.items()) or "📭 Empty"
        return await m.reply(f"🕒 <b>Timed Persistent DLinks Queue:</b>\n\n{items}")

    if not args: 
        return await m.reply("❗ <b>Please provide a valid text string/keyword trigger.</b>")

    # --- Modify & Sync Bounded Lists (RAM Cache Anchored) ---
    if "blacklist" in cmd:
        bl = data.get("blacklist", [])
        args_lower = args.lower()
        
        if cmd == "addblacklist" and args_lower not in bl: 
            bl.append(args_lower)
        elif cmd == "removeblacklist" and args_lower in bl: 
            bl.remove(args_lower)
        
        # ✅ FIX: डेटाबेस के साथutils.py के इन-मेमोरी रैम कैशे को ऑन-द-फ्लाई सिंक रखें
        await save_group_settings(m.chat.id, "blacklist", bl)
        await m.reply(f"✅ <b>Blacklist library updated for:</b> `<code>{args_lower}</code>`")

    elif "dlink" in cmd:
        dl = data.get("dlink", {})
        args_lower = args.lower()
        
        if cmd == "dlink":
            parts = args.split()
            delay = 300  # डिफ़ॉल्ट 5 मिनट क्युरिंग टाइमर
            
            # 's', 'min', 'hour' फ़ॉर्मेट्स पार्सर सिंक
            if len(parts) > 1 and parts[0][0].isdigit():
                time_string = parts[0].lower()
                parsed_seconds = await get_seconds(time_string)
                if parsed_seconds > 0:
                    delay = parsed_seconds
                    args_lower = " ".join(parts[1:]).lower()
                
            dl[args_lower] = delay
            await save_group_settings(m.chat.id, "dlink", dl)
            # ✅ FIX: थाई भाषा का कचरा साफ़ करके शुद्ध रिडेबल टाइम रेंडर किया गया
            await m.reply(f"🕒 <b>Timed DLink Trigger Set:</b> `<code>{args_lower}</code>`\n⏳ <i>Auto-delete countdown: {get_readable_time(delay)}</i>")
        else:
            dl.pop(args_lower, None)
            await save_group_settings(m.chat.id, "dlink", dl)
            await m.reply(f"🗑️ <b>Timed DLink Trigger removed:</b> `<code>{args_lower}</code>`")
            
    gc.collect() # ओओएम प्रिवेंशन सेफ्टी फ्लश
