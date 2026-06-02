import time
import random
import asyncio
import re
import gc
import logging
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS, BIN_CHANNEL
from utils import get_readable_time
from database.ia_filterdb import COLLECTIONS

logger = logging.getLogger(__name__)

# प्रोग्रेस बार बनाने के लिए सुपर-लाइटवेट यूटिलिटी फंक्शन
def make_progress_bar(current, total, length=12):
    if total == 0:
        return "[░░░░░░░░░░░░] 0%"
    percent = float(current) / total
    arrow = "█" * int(round(percent * length))
    spaces = "░" * (length - len(arrow))
    return f"[{arrow}{spaces}] {int(percent * 100)}%"

# ─────────────────────────────────────────────────────────
# 🧠 CORE ENGINE — Centralized Thumbnail Warmup Process
# ─────────────────────────────────────────────────────────
async def start_warmup_engine(client, status_msg, user_id):
    """बिना कोड रिपिटिशन के कमांड और बटन दोनों जगह से चलने वाला मुख्य वार्मअप कोर इंजन"""
    logger.info(f"⚡ [WARMUP] Activating structural warmup engine triggered by: {user_id}")
    
    # सिर्फ उन डॉक्यूमेंट्स को टारगेट करें जिनमें थंबनेल गायब है या 'TG_ID:' फॉर्मेट में लॉक नहीं है
    query = {
        "$or": [
            {"thumb_url": None},
            {"thumb_url": {"$exists": False}},
            {"thumb_url": {"$not": {"$regex": "^TG_ID:"}}}
        ]
    }
    
    total_to_process = 0
    col_counts = {}
    
    # तीनों कलेक्शंस से पेंडिंग काउंट्स का लाइव मैट्रिक्स प्राप्त करें
    for name, collection in COLLECTIONS.items():
        count = await collection.count_documents(query)
        col_counts[name] = count
        total_to_process += count
        
    if total_to_process == 0:
        logger.info("🎉 [WARMUP] All files are already beautifully warmed up in Database.")
        return await status_msg.edit("<b>🎉 Everything is Up to Date!</b>\n\nAll files inside Primary, Cloud, and Archive collections already have verified thumbnail cache locks.")

    await status_msg.edit(f"📊 <b>Found {total_to_process} pending files.</b>\nInitializing single-bot high-speed stream pipeline...")
    
    processed_count = 0
    success_count = 0
    start_time = time.time()

    # मुख्य कलेक्शंस हॉपिंग लूप
    for col_name, collection in COLLECTIONS.items():
        if col_counts[col_name] == 0:
            continue
            
        logger.info(f"📁 [WARMUP] Processing collection cluster: {col_name.upper()}")
        
        # ✅ FIX: कोएब रैम लीक रोकने के लिए केवल आवश्यक फील्ड्स प्रोजेक्ट की गईं (Zero RAM Overload)
        cursor = collection.find(query, {"_id": 1, "file_ref": 1, "file_id": 1, "file_name": 1})
        
        async for doc in cursor:
            fid = doc.get("file_ref") or doc.get("file_id") or doc.get("_id")
            if not fid:
                continue
                
            processed_count += 1
            file_name_log = doc.get('file_name', 'Unknown File')[:35]
            
            try:
                # बोट द्वारा टेलीग्राम चैनल पर फाइल भेजकर थंबनेल आईडी खींचने का मैकेनिज्म
                msg = await client.send_cached_media(chat_id=BIN_CHANNEL, file_id=fid)
                thumb_id = None
                
                if msg.video and msg.video.thumbs and len(msg.video.thumbs) > 0:
                    thumb_id = msg.video.thumbs[0].file_id
                elif msg.document and msg.document.thumbs and len(msg.document.thumbs) > 0:
                    thumb_id = msg.document.thumbs[0].file_id

                # 🛑 सख्त नियम: थंबनेल जनरेट होने पर ही डेटाबेस मॉडिफाई होगा (No Fake Entry)
                if thumb_id:
                    db_save_value = f"TG_ID:{thumb_id}"
                    res = await collection.update_one({"_id": doc["_id"]}, {"$set": {"thumb_url": db_save_value}})
                    if res.modified_count:
                        success_count += 1
                        print(f"💾 [DB LOCK] ({processed_count}/{total_to_process}) -> ✅ SUCCESS: {file_name_log}", flush=True)
                else:
                    print(f"🚫 [NO THUMB EMBED] Skipping database write operation for: {file_name_log}", flush=True)
                
                # टेलीग्राम इनबॉक्स कैश तुरंत उड़ाएं
                asyncio.create_task(msg.delete())
                
                # 🛡️ रेट लिमिट और फ्लडवेट से बचने के लिए 1 से 3 सेकंड का सुरक्षित रैंडम डिले
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                err_text = str(e)
                if "FLOOD_WAIT" in err_text or "420" in err_text:
                    match = re.search(r'wait of (\d+) second', err_text)
                    wait_time = int(match.group(1)) if match else 30
                    print(f"⏳ [FLOOD ACTIVE] Sleeping for {wait_time + 5}s to keep the bot session safe...", flush=True)
                    try: 
                        await status_msg.edit(f"⏳ <b>Telegram Flood Wait Activated!</b>\nSleeping for `{wait_time + 5}` seconds to prevent container ban...")
                    except: pass
                    await asyncio.sleep(wait_time + 5)
                elif "file reference" in err_text.lower() or "bad request" in err_text.lower():
                    print(f"❌ [BROKEN REF] Defective Telegram File Reference ID Skipped: {file_name_log}", flush=True)
                else:
                    print(f"❌ [WARN] Processing failed for target: {err_text[:50]}", flush=True)
                    await asyncio.sleep(2)

            # 📊 प्रोग्रेस बार अपडेट मैकेनिज्म (हर 10 फाइल्स कंप्लीट होने पर एडिट होगा ताकि एपीआई लोड न बढ़े)
            if processed_count % 10 == 0 or processed_count == total_to_process:
                p_bar = make_progress_bar(processed_count, total_to_process, length=12)
                
                elapsed_time = time.time() - start_time
                avg_time_per_file = elapsed_time / processed_count
                eta_seconds = (total_to_process - processed_count) * avg_time_per_file
                
                status_text = (
                    f"⚡ <b>Fast Finder - Thumbnail Warmup Engine</b>\n\n"
                    f"📁 <b>Target Storage:</b> `{col_name.upper()}`\n"
                    f"📊 <b>Progress Status:</b> `{processed_count}/{total_to_process}` Files\n"
                    f"✨ <b>Successfully Locked:</b> `{success_count}` Thumbs\n"
                    f"⏳ <b>Estimated Time Left:</b> `{get_readable_time(eta_seconds)}`\n\n"
                    f"`{p_bar}`\n\n"
                    f"ℹ️ <i>Live status stream logs are running on Koyeb Console!</i>"
                )
                try: await status_msg.edit(status_text)
                except: pass
                
                # ✅ FIX: रैम लीक्स और इन-मेमोरी बफर्स को क्लियर रखने के लिए पीरियोडिक गार्बेज कलेक्शन
                gc.collect()

    # फाइनल कंप्लीशन रिपोर्ट समरी
    final_report = (
        f"🎉 <b>Thumbnail Warmup Finished Successfully!</b>\n\n"
        f"🎯 <b>Total Processed:</b> `{processed_count}` Library Documents\n"
        f"🔒 <b>Cached & Synced in DB:</b> `{success_count}` Live Poster IDs\n\n"
        f"⚡ <i>Web application, Mini App & Bot posters will render instantly now without lag!</i>"
    )
    logger.info("🎉 [WARMUP] Thumbnail warmup lifecycle accomplishes smoothly.")
    try: await status_msg.reply(final_report)
    except: pass


# ─────────────────────────────────────────────────────────
# 📢 COMMAND ROUTE — /warmup_thumbs (ADMIN ONLY)
# ─────────────────────────────────────────────────────────
@Client.on_message(filters.command("warmup_thumbs") & filters.user(ADMINS))
async def warmup_thumbs_cmd(client, message):
    status_msg = await message.reply("⚙️ <b>Thumbnail Warmup Process Starting...</b>\nFetching document counts from DB...")
    await start_warmup_engine(client, status_msg, message.from_user.id)


# ─────────────────────────────────────────────────────────
# 🔘 BUTTON ROUTE — 🔄 WARMUP THUMBNAILS BUTTON CALLBACK
# ─────────────────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^warmup_trigger_all$"))
async def warmup_callback_handler(client, query):
    # स्ट्रिक्ट एडमिन गेटवे सुरक्षा ताला
    if query.from_user.id not in ADMINS:
        return await query.answer("❌ Verification Access Denied! Only Bot Admins can trigger warmup.", show_alert=True)
    
    await query.answer("⚙️ Thumbnail Warmup Initiated! Starting Background Pipeline...", show_alert=False)
    
    # उसी स्टैट्स वाले मैसेज का टेक्स्ट बदलकर सीधे वार्मअप प्रोग्रेस स्क्रीन में कन्वर्ट कर दें
    await query.message.edit_reply_markup(reply_markup=None) # फालतू बटन्स तुरंत साफ करें
    await start_warmup_engine(client, query.message, query.from_user.id)
