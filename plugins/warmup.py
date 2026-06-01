import time
import random
import asyncio
import re
import logging
from hydrogram import Client, filters
from info import ADMINS, BIN_CHANNEL
from utils import get_readable_time
from database.ia_filterdb import COLLECTIONS

logger = logging.getLogger(__name__)

# प्रोग्रेस बार बनाने के लिए यूटिलिटी फंक्शन
def make_progress_bar(current, total, length=12):
    if total == 0:
        return "[░░░░░░░░░░░░] 0%"
    percent = float(current) / total
    arrow = "█" * int(round(percent * length))
    spaces = "░" * (length - len(arrow))
    return f"[{arrow}{spaces}] {int(percent * 100)}%"

# ─────────────────────────────────────────────
# 🚀 LIVE THUMBNAIL WARMUP COMMAND (ADMIN ONLY)
# ─────────────────────────────────────────────
@Client.on_message(filters.command("warmup_thumbs") & filters.user(ADMINS))
async def warmup_thumbs_cmd(client, message):
    # 1. बोट चैट में शुरुआती स्टेटस मैसेज भेजें
    status_msg = await message.reply("⚙️ **Thumbnail Warmup Process Starting...**\nFetching document counts from DB...")
    
    logger.info("⚡ [WARMUP] Starting thumbnail warmup process via admin command...")
    
    # सिर्फ उन डॉक्यूमेंट्स को टारगेट करें जिनमें थंबनेल गायब है या 'TG_ID:' फॉर्मेट में नहीं है
    query = {
        "$or": [
            {"thumb_url": None},
            {"thumb_url": {"$exists": False}},
            {"thumb_url": {"$not": {"$regex": "^TG_ID:"}}}
        ]
    }
    
    total_to_process = 0
    col_counts = {}
    
    # तीनों कलेक्शंस से पेंडिंग काउंट्स निकालें
    for name, collection in COLLECTIONS.items():
        count = await collection.count_documents(query)
        col_counts[name] = count
        total_to_process += count
        
    if total_to_process == 0:
        logger.info("🎉 [WARMUP] All files are already warmed up. No pending thumbnails!")
        return await status_msg.edit("🎉 **Everything is up to date!** All 35k+ files already have locked thumbnails.")

    logger.info(f"📊 [WARMUP] Total pending files detected across collections: {total_to_process}")
    await status_msg.edit(f"📊 **Found {total_to_process} pending files.**\nInitializing single-bot stream pipeline...")
    
    processed_count = 0
    success_count = 0
    start_time = time.time()

    # मुख्य कलेक्शंस लूप
    for col_name, collection in COLLECTIONS.items():
        if col_counts[col_name] == 0:
            continue
            
        logger.info(f"📁 [WARMUP] Processing collection library: {col_name.upper()}")
        cursor = collection.find(query)
        
        async for doc in cursor:
            fid = doc.get("file_ref") or doc.get("file_id") or doc.get("_id")
            if not fid:
                continue
                
            processed_count += 1
            file_name_log = doc.get('file_name', 'Unknown File')[:35]  # कोयब लॉग के लिए लिमिटर
            
            try:
                # search_api.py के रूल्स के मुताबिक: पहले टेलीग्राम पर भेजें
                logger.info(f"📥 [TG FETCH] Fetching from Telegram for File ID: {fid} (Warmup Mode)")
                msg = await client.send_cached_media(chat_id=BIN_CHANNEL, file_id=fid)
                thumb_id = None
                
                # वीडियो या डॉक्यूमेंट से ओरिजिनल थंबनेल आईडी एक्सट्रैक्ट करें
                if msg.video and msg.video.thumbs and len(msg.video.thumbs) > 0:
                    thumb_id = msg.video.thumbs[0].file_id
                elif msg.document and msg.document.thumbs and len(msg.document.thumbs) > 0:
                    thumb_id = msg.document.thumbs[0].file_id

                # 🛑 सख्त नियम: थंबनेल जनरेट होने पर ही डेटाबेस मॉडिफाई होगा
                if thumb_id:
                    db_save_value = f"TG_ID:{thumb_id}"
                    
                    # डेटाबेस में सेव करें
                    res = await collection.update_one({"_id": doc["_id"]}, {"$set": {"thumb_url": db_save_value}})
                    if res.modified_count:
                        success_count += 1
                        # कोयब (Koyeb) के लाइव लॉग्स में प्रिंट करें
                        print(f"💾 [NATIVE SAVE] Successfully locked in DB ({processed_count}/{total_to_process}) -> ✅ SUCCESS: {file_name_log}", flush=True)
                else:
                    # अगर थंबनेल नहीं मिला तो DB मॉडिफाई नहीं करेंगे, बस लॉग प्रिंट होगा
                    print(f"🚫 [NO THUMB] Telegram did not return any embedded thumb for: {file_name_log} (Skipping DB lock)", flush=True)
                
                # टेलीग्राम का कैश मैसेज तुरंत डिलीट करें
                asyncio.create_task(msg.delete())
                
                # 🛡️ 1 से 5 सेकंड का रैंडम गैप (Dynamic Delay) - रेट लिमिट से बचने के लिए
                sleep_time = random.uniform(1.0, 5.0)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                err_text = str(e)
                # अगर फिर भी Flood Wait आ जाए तो उसे संभालें
                if "FLOOD_WAIT" in err_text or "420" in err_text:
                    match = re.search(r'wait of (\d+) second', err_text)
                    wait_time = int(match.group(1)) if match else 30
                    print(f"⏳ [FLOOD WAIT] Telegram Rate Limit Hit! Sleeping for {wait_time + 10}s during warmup...", flush=True)
                    
                    try: 
                        await status_msg.edit(f"⏳ **Telegram Flood Wait Active!**\nSleeping for `{wait_time + 10}` seconds to keep the bot session safe...")
                    except: 
                        pass
                    
                    await asyncio.sleep(wait_time + 10)
                elif "file reference" in err_text.lower() or "bad request" in err_text.lower():
                    print(f"❌ [ERROR] Broken/Invalid Telegram File Reference ID: {file_name_log}", flush=True)
                else:
                    print(f"❌ [ERROR] Processing failed for doc: {err_text[:60]}", flush=True)
                    await asyncio.sleep(3)

            # 📊 टेलीग्राम प्रोग्रेस बार अपडेट मैकेनिज्म (हर 10 फाइल्स कंप्लीट होने पर एडिट होगा)
            if processed_count % 10 == 0 or processed_count == total_to_process:
                p_bar = make_progress_bar(processed_count, total_to_process, length=12)
                
                # प्रति फाइल औसतन समय के आधार पर सटीक ETA कैलकुलेशन
                elapsed_time = time.time() - start_time
                avg_time_per_file = elapsed_time / processed_count
                eta_seconds = (total_to_process - processed_count) * avg_time_per_file
                
                status_text = (
                    f"⚡ **Fast Finder Web - Thumbnail Warmup**\n\n"
                    f"📁 **Current Collection:** `{col_name.upper()}`\n"
                    f"📊 **Progress Status:** `{processed_count}/{total_to_process}` Files\n"
                    f"✨ **Successfully Locked:** `{success_count}` Thumbs\n"
                    f"⏳ **Estimated Time Remaining:** `{get_readable_time(eta_seconds)}`\n\n"
                    f"`{p_bar}`\n\n"
                    f"ℹ️ _Logs are streaming live on Koyeb Console!_"
                )
                try: 
                    await status_msg.edit(status_text)
                except: 
                    pass

    # फाइनल कंप्लीशन रिपोर्ट
    final_report = (
        f"🎉 **Thumbnail Warmup Finished Successfully!**\n\n"
        f"🎯 **Total Processed:** `{processed_count}` Documents\n"
        f"🔒 **Locked & Cached in DB:** `{success_count}` Images\n\n"
        f"⚡ Web application search and thumbs will render instantly now!"
    )
    logger.info("🎉 [WARMUP] Thumbnail warmup operation accomplished successfully.")
    await status_msg.reply(final_report)
