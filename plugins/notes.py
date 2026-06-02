import time
import html
import logging
from hydrogram import Client, filters, enums
from database.users_chats_db import db
from utils import is_check_admin

logger = logging.getLogger(__name__)

# =========================================
# 🚀 SMART CACHE SYSTEM (Koyeb RAM Optimized)
# =========================================
NOTES_CACHE = {}
CACHE_TTL = 300  

async def get_notes(chat_id):
    now = time.time()
    
    # ✅ FIX: कोएब रैम ओवरयूज़ (OOM) क्रैश रोकने के लिए एग्रेसिव कैशे क्लीनर लागू
    if len(NOTES_CACHE) > 400:
        NOTES_CACHE.clear()
        logger.info("🧹 RAM Cleaner Triggered: Notes local dictionary cache cleared safely.")

    if chat_id in NOTES_CACHE and (now - NOTES_CACHE[chat_id][1]) < CACHE_TTL:
        return NOTES_CACHE[chat_id][0]
    
    data = await db.get_all_notes(chat_id) or {}
    NOTES_CACHE[chat_id] = (data, now)
    return data

async def is_admin(c, m):
    if m.sender_chat and m.sender_chat.id == m.chat.id: 
        return True 
    if not m.from_user: 
        return False
    return await is_check_admin(c, m.chat.id, m.from_user.id)

# =========================================
# 📝 SAVE, DELETE & LIST
# =========================================

@Client.on_message(filters.group & filters.command(["save", "addnote"]))
async def save_note(c, m):
    if not await is_admin(c, m): return
    if len(m.command) < 2 or not m.reply_to_message:
        return await m.reply("❗ Use: `/save <name>` (Reply to a message)")
    
    name = m.command[1].lower()
    reply = m.reply_to_message
    
    # 🎯 Smart Media Detection
    note_type, file_id = "text", None
    for t in ["photo", "video", "document", "sticker", "animation"]:
        media = getattr(reply, t, None)
        if media:
            note_type, file_id = t, media.file_id
            break
    
    note_data = {
        "type": note_type,
        "file_id": file_id,
        "caption": reply.caption if reply.caption else "", 
        "text": reply.text if reply.text else ""
    }

    data = await get_notes(m.chat.id)
    data[name] = note_data
    NOTES_CACHE[m.chat.id] = (data, time.time())
    await db.save_note(m.chat.id, name, note_data)
    
    await m.reply(f"✅ Note **#{name}** saved!")

@Client.on_message(filters.group & filters.command(["clear", "rmnote"]))
async def delete_note(c, m):
    if not await is_admin(c, m): return
    if len(m.command) < 2: return await m.reply("❗ Use: `/clear <name>`")
    
    name = m.command[1].lower()
    data = await get_notes(m.chat.id)
    
    if name in data:
        del data[name]
        NOTES_CACHE[m.chat.id] = (data, time.time())
        await db.delete_note(m.chat.id, name)
        await m.reply(f"🗑️ Note **#{name}** deleted.")
    else:
        await m.reply(f"❌ Note **#{name}** not found.")

@Client.on_message(filters.group & filters.command("notes"))
async def list_notes(c, m):
    data = await get_notes(m.chat.id)
    if not data: return await m.reply("📭 No notes saved.")
    await m.reply("📝 **Saved Notes:**\n" + "\n".join(f"• `#{n}`" for n in data))

# =========================================
# 🔎 NOTE FETCHER (Smart Filter)
# =========================================

@Client.on_message(filters.group & filters.regex(r"^#[\w]+"), group=11)
async def get_note(c, m):
    msg_text = m.text or m.caption
    if not msg_text: return
    
    name = msg_text.split()[0][1:].lower()
    data = await get_notes(m.chat.id)
    if name not in data: return
    
    note = data[name]
    reply_id = m.reply_to_message.id if m.reply_to_message else m.id
    
    if note["type"] == "text":
        await c.send_message(m.chat.id, note["text"], reply_to_message_id=reply_id, parse_mode=enums.ParseMode.HTML)
    else:
        # ✅ FIX: क्लाइंट ऑब्जेक्ट पर डायनामिक फंक्शन कॉल और सही आर्ग्यूमेंट बाइंडिंग रूटीन सिंक किया गया
        send_method = getattr(c, f"send_{note['type']}") 
        
        # आर्गुमेंट्स डिक्शनरी को सेफली बिल्ड करें
        kwargs = {
            "chat_id": m.chat.id,
            "reply_to_message_id": reply_id
        }
        
        # हाइड्रोग्राम में डायनामिक सेंड करने के लिए फ़ाइल आईडी को सही कीवर्ड नाम (जैसे photo, video) के साथ पास करें
        media_key = "animation" if note["type"] == "animation" else note["type"]
        kwargs[media_key] = note["file_id"]
        
        if note["type"] != "sticker": 
            kwargs["caption"] = note["caption"]
            kwargs["parse_mode"] = enums.ParseMode.HTML
            
        try:
            await send_method(**kwargs)
        except Exception as e:
            logger.error(f"Failed to send note #{name}: {e}")
