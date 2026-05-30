import os
import re
import bs4
import time
import requests
import asyncio
import random
import traceback
import logging
from hydrogram import Client, filters, enums
from info import LOG_CHANNEL as DUMP_GROUP, ADMINS
from database.users_chats_db import db  # डेटाबेस सेटिंग्स के लिए

logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://saveig.app",
    "Connection": "keep-alive",
    "Referer": "https://saveig.app/en",
}

# 🧠 Requests को बिना बोट अटकाए एसिंक्रोनस चलाने के लिए हेल्पर फंक्शन्स
async def async_get(url, headers=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: requests.get(url, headers=headers))

async def async_post(url, data=None, headers=None):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: requests.post(url, data=data, headers=headers))

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
    global headers
    m = None
    downfile = None
    default_caption = "<b>Downloaded By @UncutFlixBot</b>"
    
    try:
        m = await message.reply_sticker("CAACAgUAAxkBAAITAmWEcdiJs9U2WtZXtWJlqVaI8diEAAIBAAPBJDExTOWVairA1m8eBA")
        
        # 🎯 मुख्य फिक्स: SaveIG API का उपयोग करके सीधे वीडियो यूआरएल निकालेंगे ताकि क्रैश न हो
        meta_resp = await async_post("https://saveig.app/api/ajaxSearch", data={"q": link, "t": "media", "lang": "en"}, headers=headers)
        
        if meta_resp.ok:
            res = meta_resp.json()
            meta = re.findall(r'href="(https?://[^"]+)"', res['data'])
            if meta:
                content_value = meta[0]
                try:
                    # सीधे टेलीग्राम सर्वर के ज़रिए वीडियो भेजें
                    dump_file = await message.reply_video(content_value, caption=default_caption)
                    if m: await m.delete()
                    return
                except Exception:
                    # अगर टेलीग्राम डायरेक्ट यूआरएल फेच नहीं कर पाता, तो लोकल रैम में डाउनलोड करके भेजें
                    downfile = f"{os.getcwd()}/{random.randint(1, 10000000)}.mp4"
                    dl_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                    file_resp = await async_get(content_value, headers=dl_headers)
                    with open(downfile, 'wb') as x:
                        x.write(file_resp.content)
                    
                    dump_file = await message.reply_video(downfile, caption=default_caption)
                    if m: await m.delete()
                    return

        # 🎯 बैकअप मेथड: अगर API काम न करे, तब नए वर्किंग डोमेन (igv.com) का उपयोग करें
        url = link.replace("instagram.com", "igv.com").replace("==", "%3D%3D")
        if url.endswith("="): url = url[:-1]
        
        dump_file = await message.reply_video(url, caption=default_caption)
        if m: await m.delete()
        
    except Exception as e:
        if DUMP_GROUP:
            try:
                await Mbot.send_message(DUMP_GROUP, f"⚠️ Instagram Error: {e}\nLink: {link}")
                await Mbot.send_message(DUMP_GROUP, f"<code>{traceback.format_exc()}</code>")
            except:
                pass
        await message.reply("❌ **Sorry, unable to download this media!** सुनिश्चित करें कि रील का अकाउंट पब्लिक है।")

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
