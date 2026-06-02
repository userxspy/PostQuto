import logging
import re
from hydrogram import Client, filters
from info import PRIMARY_CHANNEL, CLOUD_CHANNEL, ARCHIVE_CHANNEL
from database.ia_filterdb import COLLECTIONS, unpack_new_file_id

logger = logging.getLogger(__name__)

CHANNELS = {}
for cid in PRIMARY_CHANNEL: CHANNELS[cid] = "primary"
for cid in CLOUD_CHANNEL: CHANNELS[cid] = "cloud"
for cid in ARCHIVE_CHANNEL: CHANNELS[cid] = "archive"

INDEX_CHATS = list(CHANNELS.keys())

def get_file_info(message):
    media = message.document or message.video or message.audio
    if not media: return None
    
    file_id = media.file_id
    file_unique_id = media.file_unique_id
    file_size = media.file_size
    
    # ✅ FIX: AttributeError से बचने के लिए सेफ कैप्शन एक्सट्रैक्टर
    caption_text = message.caption if message.caption else None
    file_name = caption_text or getattr(media, 'file_name', None) or "Unknown_File"
    
    # क्लीन नामकरण (Safe Name Cleaning)
    try: 
        file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(file_name)).strip()
    except: 
        pass
        
    file_type = media.__class__.__name__.lower()
    return file_id, file_unique_id, file_size, file_name, file_type

if INDEX_CHATS:
    
    @Client.on_message(filters.chat(INDEX_CHATS) & (filters.document | filters.video | filters.audio))
    async def auto_index_files(client, message):
        file_info = get_file_info(message)
        if not file_info: return
            
        file_id, file_unique_id, file_size, file_name, file_type = file_info
        
        # फ़ाइल की असली शॉर्ट आईडी निकालें
        db_id = unpack_new_file_id(file_id)
        if not db_id: 
            return logger.warning(f"❌ Failed to unpack file ID during auto-index for: {file_name}")

        target_col_name = CHANNELS[message.chat.id]
        collection = COLLECTIONS.get(target_col_name)
        if not collection: return
            
        # ✅ FIX: कोएब डिस्क थ्रॉटलिंग (Write IOPS) से बचने के लिए स्मार्ट डुप्लिकेट चेकिंग
        existing_doc = await collection.find_one({"_id": db_id}, {"file_ref": 1, "thumb_url": 1})
        
        if existing_doc:
            if existing_doc.get("file_ref") == file_id:
                try: await message.react("♻️")
                except: pass
                logger.info(f"➡️ Duplicate skipped (No changes) in {target_col_name.upper()}: {file_name}")
                return
            
            # पुराने थंबनेल को सेफ रखें
            thumb_url = existing_doc.get("thumb_url")
        else:
            thumb_url = None

        doc = {
            "_id": db_id, 
            "file_id": db_id,
            "file_ref": file_id, 
            "file_name": file_name,
            "file_size": file_size, 
            "file_type": file_type,
            "caption": file_name,
            "thumb_url": thumb_url
        }
        
        # डेटाबेस में अपडेट या इंसर्ट करें
        await collection.replace_one({"_id": db_id}, doc, upsert=True)
        
        try:
            await message.react("✅")
            logger.info(f"✅ Indexed new file into {target_col_name.upper()}: {file_name}")
        except: 
            pass

    @Client.on_edited_message(filters.chat(INDEX_CHATS) & (filters.document | filters.video | filters.audio))
    async def update_indexed_files(client, message):
        file_info = get_file_info(message)
        if not file_info: return
            
        file_id, _, _, file_name, _ = file_info
        db_id = unpack_new_file_id(file_id)
        if not db_id: return

        target_col_name = CHANNELS[message.chat.id]
        collection = COLLECTIONS.get(target_col_name)
        if not collection: return
            
        result = await collection.update_one(
            {"_id": db_id}, {"$set": {"file_name": file_name, "caption": file_name}}
        )
        
        try:
            if result.modified_count > 0:
                await message.react("🔄")
                logger.info(f"🔄 Updated caption in {target_col_name.upper()}: {file_name}")
        except: 
            pass
