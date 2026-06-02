import logging
import re
import base64
import asyncio
from struct import pack
import motor.motor_asyncio
from hydrogram.file_id import FileId
from info import DATABASE_URL, DATABASE_NAME, MAX_BTN, USE_CAPTION_FILTER

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# ⚙️ MOTOR CONNECTION — Koyeb Free Tier Optimized (Fid_Fixed)
# ─────────────────────────────────────────────────────────
client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL,
    maxPoolSize=15,             # हैवी ट्रैफिक संभालने के लिए पर्याप्त है
    minPoolSize=0,              # ✅ FIX: आइडल टाइम पर 0 कनेक्शन (कोएब के लिए बेस्ट)
    maxIdleTimeMS=30000,        # 30 सेकंड तक शांत रहने पर कनेक्शन बंद करें
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=20000,
    retryWrites=True,
    retryReads=True,
)
db = client[DATABASE_NAME]

primary = db["Primary"]
cloud   = db["Cloud"]
archive = db["Archive"]

COLLECTIONS = {
    "primary": primary,
    "cloud":   cloud,
    "archive": archive,
}

# ─────────────────────────────────────────────────────────
# ⚡ INDEXES — Text index
# ─────────────────────────────────────────────────────────
async def ensure_indexes():
    for name, col in COLLECTIONS.items():
        try:
            await col.create_index(
                [("file_name", "text"), ("caption", "text")],
                name=f"{name}_text"
            )
            logger.info(f"✅ Text Index OK: {name}")
        except Exception as e:
            if "already exists" in str(e) or "IndexKeySpecsConflict" in str(e) or "86" in str(e):
                pass
            else:
                logger.warning(f"Index warning [{name}]: {e}")

# ─────────────────────────────────────────────────────────
# 📊 DB STATS
# ─────────────────────────────────────────────────────────
async def db_count_documents():
    try:
        p, c, a = await asyncio.gather(
            primary.estimated_document_count(),
            cloud.estimated_document_count(),
            archive.estimated_document_count(),
        )
        return {"primary": p, "cloud": c, "archive": a, "total": p + c + a}
    except Exception as e:
        logger.error(f"Count error: {e}")
        return {"primary": 0, "cloud": 0, "archive": 0, "total": 0}

# ─────────────────────────────────────────────────────────
# 💾 SAVE FILE (Disk Write IOPS Protected)
# ─────────────────────────────────────────────────────────
async def save_file(media, collection_type="primary"):
    try:
        file_id = unpack_new_file_id(media.file_id)
        if not file_id:
            logger.warning(f"Could not unpack file_id: {media.file_name}")
            return "err"

        f_name  = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name or "")).strip()
        caption = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.caption  or "")).strip()
        file_type = type(media).__name__.lower()

        col = COLLECTIONS.get(collection_type, primary)
        
        # ✅ FIX: अनावश्यक डिस्क राइट्स (Write IOPS Throttling) से बचने के लिए स्मार्ट चेकिंग
        existing_doc = await col.find_one({"_id": file_id}, {"file_ref": 1, "thumb_url": 1})
        
        if existing_doc:
            # अगर फ़ाइल पहले से है और उसका file_ref भी सेम है, तो राइट ऑपरेशन स्किप करें
            if existing_doc.get("file_ref") == media.file_id:
                logger.info(f"➡️ Duplicate skipped (No changes) - {f_name}")
                return "dup"
            
            # अगर सिर्फ थंबनेल 'TG_ID:' प्रोटेक्टेड है, तो उसे नए डॉक में ट्रांसफर करें
            old_thumb = existing_doc.get("thumb_url")
            if old_thumb and "TG_ID:" in old_thumb:
                thumb_url = old_thumb
            else:
                thumb_url = None
        else:
            thumb_url = None

        doc = {
            "_id":       file_id,     
            "file_id":   file_id,     
            "file_ref":  media.file_id, 
            "file_name": f_name,
            "file_size": media.file_size,
            "caption":   caption,
            "file_type": file_type,   
            "thumb_url": thumb_url  
        }

        await col.replace_one({"_id": file_id}, doc, upsert=True)
        logger.info(f"✅ Saved - {f_name}")
        return "suc"

    except Exception as e:
        logger.error(f"save_file error: {e}")
        return "err"

# ─────────────────────────────────────────────────────────
# 🔍 REGEX BUILDER
# ─────────────────────────────────────────────────────────
def _build_regex(query: str):
    query = query.strip()
    if not query:
        raw = r'.'
    elif ' ' not in query:
        raw = r'(\b|[\.\+\-_])' + re.escape(query) + r'(\b|[\.\+\-_])'
    else:
        raw = re.escape(query).replace(r'\ ', r'.*[\s\.\+\-_]')

    try:
        return re.compile(raw, flags=re.IGNORECASE)
    except Exception:
        return re.compile(re.escape(query), flags=re.IGNORECASE)

# ─────────────────────────────────────────────────────────
# 🚀 SMART SEARCH (CPU-Spike Optimized with Projection)
# ─────────────────────────────────────────────────────────
async def _search(col, raw_query: str, regex, offset: int, limit: int, lang=None):
    clean_query = raw_query.replace('"', '').replace("'", "")
    strict_query = " ".join(f'"{word}"' for word in clean_query.split())

    text_flt = {"$text": {"$search": strict_query}}
    if lang:
        lang_regex = re.compile(lang, re.IGNORECASE)
        text_flt = {"$and": [text_flt, {"file_name": lang_regex}]}

    # कर्सर लोड कम करने के लिए count_documents का उपयोग
    count = await col.count_documents(text_flt)
    
    if count > 0:
        # ✅ FIX: इन-मेमोरी सॉर्टिंग से कोएब CPU ब्लास्ट रोकने के लिए प्रोजेक्शन स्लाइसिंग
        cursor = col.find(text_flt, {"_id": 1, "file_name": 1, "file_size": 1, "file_ref": 1, "caption": 1, "score": {"$meta": "textScore"}})
        cursor.sort([("score", {"$meta": "textScore"})])
        cursor.skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        for doc in docs:
            doc["file_id"] = doc["_id"]
        return docs, count

    if USE_CAPTION_FILTER:
        reg_flt = {"$or": [{"file_name": regex}, {"caption": regex}]}
    else:
        reg_flt = {"file_name": regex}

    if lang:
        lang_regex = re.compile(lang, re.IGNORECASE)
        reg_flt = {"$and": [reg_flt, {"file_name": lang_regex}]}

    # ✅ FIX: अनावश्यक पूरा डॉक्यूमेंट खींचने के बजाय सिर्फ काम के फील्ड्स प्रोजेक्ट करें
    cursor = col.find(reg_flt, {"_id": 1, "file_name": 1, "file_size": 1, "file_ref": 1, "caption": 1}).sort('_id', -1)
    cursor.skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["file_id"] = doc["_id"]

    count = await col.count_documents(reg_flt)
    return docs, count

# ─────────────────────────────────────────────────────────
# 🌐 PUBLIC SEARCH API
# ─────────────────────────────────────────────────────────
async def get_search_results(query, max_results=MAX_BTN, offset=0, lang=None, collection_type="primary"):
    if not query:
        return [], "", 0, collection_type

    raw_query  = str(query).strip()
    regex      = _build_regex(raw_query)
    results    = []
    total      = 0
    actual_src = collection_type

    if collection_type == "all":
        cascade = [("primary", primary), ("cloud", cloud), ("archive", archive)]
        for src, col in cascade:
            docs, cnt = await _search(col, raw_query, regex, offset, max_results, lang)
            if docs:
                results    = docs
                total      = cnt
                actual_src = src
                break  

    elif collection_type in COLLECTIONS:
        col       = COLLECTIONS[collection_type]
        docs, cnt = await _search(col, raw_query, regex, offset, max_results, lang)
        results   = docs
        total     = cnt

    else:
        docs, cnt = await _search(primary, raw_query, regex, offset, max_results, lang)
        results   = docs
        total     = cnt

    next_offset = offset + max_results
    next_offset = "" if next_offset >= total else next_offset

    return results, next_offset, total, actual_src

# ─────────────────────────────────────────────────────────
# 🗑 DELETE FILES (Connection Pool Lock Safe)
# ─────────────────────────────────────────────────────────
async def delete_files(query, collection_type="all"):
    deleted = 0
    try:
        if query == "*":
            cols = [col for name, col in COLLECTIONS.items() if collection_type == "all" or name == collection_type]
            # ✅ FIX: asyncio.gather में एक साथ डिलीट ब्लास्ट करने के बजाय सीक्वेंशियली क्लियर करें ताकि कनेक्शन पूल फ्रीज न हो
            for col in cols:
                res = await col.delete_many({})
                deleted += res.deleted_count
            return deleted

        regex = _build_regex(str(query))
        flt   = {"file_name": regex}
        cols  = [(name, col) for name, col in COLLECTIONS.items() if collection_type == "all" or name == collection_type]

        for name, col in cols:
            res = await col.delete_many(flt)
            deleted += res.deleted_count
            if res.deleted_count:
                logger.info(f"🗑 Deleted {res.deleted_count} from {name}")

        return deleted

    except Exception as e:
        logger.error(f"delete_files error: {e}")
        return deleted

# ─────────────────────────────────────────────
# 📂 GET FILE DETAILS (Projection Added)
# ─────────────────────────────────────────────
async def get_file_details(file_id):
    try:
        # ✅ FIX: पूरे अनकैप्ड डॉक्यूमेंट की जगह प्रोजेक्शन के साथ सुरक्षित रूप से फ़ाइल का विवरण खोजें
        for col in [primary, cloud, archive]:
            doc = await col.find_one(
                {"$or": [{"_id": file_id}, {"file_id": file_id}, {"file_ref": file_id}]},
                {"_id": 1, "file_name": 1, "file_size": 1, "file_ref": 1, "caption": 1, "thumb_url": 1}
            )
            if doc:
                doc["file_id"] = doc["_id"]  
                return doc
        return None
    except Exception as e:
        logger.error(f"get_file_details error: {e}")
        return None

# ─────────────────────────────────────────────────────────
# 🗑 UNPACK/ENCODE UTILS
# ─────────────────────────────────────────────────────────
def encode_file_id(s: bytes) -> str:
    r, n = b"", 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0: n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n  = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def unpack_new_file_id(new_file_id: str):
    try:
        decoded = FileId.decode(new_file_id)
        return encode_file_id(
            pack(
                "<iiqq",
                int(decoded.file_type),
                decoded.dc_id,
                decoded.media_id,
                decoded.access_hash,
            )
        )
    except Exception as e:
        logger.error(f"unpack_new_file_id error: {e}")
        return None
