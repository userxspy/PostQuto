import os
import requests
import asyncio
import random
import traceback
import logging
from hydrogram import Client, filters
from info import LOG_CHANNEL as DUMP_GROUP, ADMINS
from database.users_chats_db import db

logger = logging.getLogger(__name__)

# 🧠 Requests को बिना बोट अटकाए एसिंक्रोनस चलाने के लिए हेल्पर फ़ंक्शन
async def async_get(url, headers=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: requests.get(url, headers=headers, timeout=15))

# ─────────────────────────────────────────────
# ⚙️ INSTA ON/OFF COMMAND (Admin Only)
# ─────────────────────────────────────────────
@Client.on_message(filters.command("insta") & filters.private)
async def toggle_insta(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply("❌ **यह कमांड सिर्फ बोट एडमिन के लिए है!**")
        
    if len(message.command) < 2:
        return await message.reply("⚙️ **सही तरीका:**\n• `/insta on` - डाउनलोडर चालू करें\n• `/insta off` - डाउनलोडर बंद करें")
        
    status = message.command[1].lower()
    if status == "on":
        await db.groups.update_one({"id": "insta_settings"}, {"$set": {"status": True}}, upsert=True)
        await message.reply("✅ **इंस्टाग्राम डाउनलोडर सफलतापूर्वक चालू (ON) कर दिया गया है।**")
    elif status == "off":
        await db.groups.update_one({"id": "insta_settings"}, {"$set": {"status": False}}, upsert=True)
        await message.reply("🔒 **इंस्टाग्राम डाउनलोडर सफलतापूर्वक बंद (OFF) कर दिया गया है।**")
    else:
        await message.reply("❌ गलत इनपुट! सिर्फ `/insta on` या `/insta off` का उपयोग करें।")

# ─────────────────────────────────────────────
# 📥 INSTAGRAM LINK HANDLER (PM Only)
# ─────────────────────────────────────────────
@Client.on_message(filters.regex(r'https?://.*instagram[^\s]+') & filters.private & filters.incoming)
async def link_handler(Mbot, message):
    settings = await db.groups.find_one({"id": "insta_settings"})
    is_active = settings.get("status", True) if settings else True 
    
    if not is_active:
        return await message.reply("🚧 **Sorry!** इंस्टाग्राम डाउनलोडर अभी बोट एडमिन द्वारा बंद (Disabled) किया गया है।")

    link = message.matches[0].group(0)
    m = None
    downfile = None
    default_caption = "<b>Downloaded By @UncutFlixBot</b>"
    
    try:
        m = await message.reply_sticker("CAACAgUAAxkBAAITAmWEcdiJs9U2WtZXtWJlqVaI8diEAAIBAAPBJDExTOWVairA1m8eBA")
        
        # 🎯 मेथड 1: सबसे स्टेबल 'igv.com' डोमेन में कन्वर्ट करो
        video_url = link.replace("instagram.com", "igv.com").replace("==", "%3D%3D")
        if video_url.endswith("="): video_url = video_url[:-1]
        
        try:
            # टेलीग्राम सर्वर के ज़रिए सीधे भेजने की कोशिश करें
            dump_file = await message.reply_video(video_url, caption=default_caption)
            if m: await m.delete()
            return
        except Exception:
            # अगर सीधे नहीं जाता, तो कोएब सर्वर पर बैकएंड में डाउनलोड करके भेजें
            try:
                downfile = f"{os.getcwd()}/{random.randint(1, 10000000)}.mp4"
                dl_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                file_resp = await async_get(video_url, headers=dl_headers)
                
                if file_resp.status_code == 200:
                    with open(downfile, 'wb') as x:
                        x.write(file_resp.content)
                    dump_file = await message.reply_video(downfile, caption=default_caption)
                    if m: await m.delete()
                    return
            except Exception:
                pass

        # 🎯 बैकअप मेथड 2: अगर 'igv.com' फेल हो, तो 'ginnstagram.com' का उपयोग करें
        backup_url = link.replace("instagram.com", "ginnstagram.com").replace("==", "%3D%3D")
        if backup_url.endswith("="): backup_url = backup_url[:-1]
        
        try:
            dump_file = await message.reply_video(backup_url, caption=default_caption)
            if m: await m.delete()
            return
        except Exception:
            # बैकअप डोमेन को भी लोकल डाउनलोड करके भेजने की कोशिश करें
            downfile = f"{os.getcwd()}/{random.randint(1, 10000000)}.mp4"
            dl_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            file_resp = await async_get(backup_url, headers=dl_headers)
            with open(downfile, 'wb') as x:
                x.write(file_resp.content)
            dump_file = await message.reply_video(downfile, caption=default_caption)
            if m: await m.delete()
            return
            
    except Exception as e:
        if DUMP_GROUP:
            try:
                await Mbot.send_message(DUMP_GROUP, f"⚠️ Instagram Critical Error: {e}\nLink: {link}")
                await Mbot.send_message(DUMP_GROUP, f"<code>{traceback.format_exc()}</code>")
            except:
                pass
        await message.reply("❌ **Sorry, unable to download this media!** वेबसाइट डाउन होने के कारण समस्या आ रही है, कृपया कुछ देर बाद प्रयास करें।")

    finally:
        if 'dump_file' in locals() and dump_file and DUMP_GROUP:
            try: await dump_file.forward(DUMP_GROUP)
            except: pass
        if m:
            try: await m.delete()
            except: pass
        if downfile and os.path.exists(downfile):
            try: os.remove(downfile)
            except: pass
