import math
import io
import gc
import logging
import asyncio
from hydrogram import Client, utils, raw
from hydrogram.types import Message
from hydrogram.session import Session, Auth
from hydrogram.errors import AuthBytesInvalid
from hydrogram.file_id import FileId, FileType, ThumbnailSource
from utils import temp

logger = logging.getLogger(__name__)

async def chunk_size(length): 
    return 2 ** max(min(math.ceil(math.log2(length / 1024)), 10), 2) * 1024

async def offset_fix(offset, chunksize): 
    return offset - (offset % chunksize)

class TGCustomYield:
    def __init__(self):
        self.main_bot = temp.BOT

    @staticmethod
    async def generate_file_properties(msg: Message):
        return FileId.decode(getattr(msg, msg.media.value).file_id)

    async def generate_media_session(self, c: Client, msg: Message):
        d = await self.generate_file_properties(msg)
        ms = c.media_sessions.get(d.dc_id)
        
        if not ms:
            test_mode = await c.storage.test_mode()
            if d.dc_id != await c.storage.dc_id():
                ms = Session(c, d.dc_id, await Auth(c, d.dc_id, test_mode).create(), test_mode, is_media=True)
                await ms.start()
                for _ in range(3):
                    try:
                        ex = await c.invoke(raw.functions.auth.ExportAuthorization(dc_id=d.dc_id))
                        await ms.send(raw.functions.auth.ImportAuthorization(id=ex.id, bytes=ex.bytes))
                        break
                    except AuthBytesInvalid: 
                        continue
                else:
                    # ✅ कोएब सॉकेट/सत्र लीक (Session Leak) रोकने के लिए ग्रेसफुल स्टॉप सिंक
                    await ms.stop()
                    raise AuthBytesInvalid
            else:
                ms = Session(c, d.dc_id, await c.storage.auth_key(), test_mode, is_media=True)
                await ms.start()
            c.media_sessions[d.dc_id] = ms
            
        return ms

    @staticmethod
    async def get_location(f: FileId):
        if f.file_type == FileType.CHAT_PHOTO:
            peer = raw.types.InputPeerUser(user_id=f.chat_id, access_hash=f.chat_access_hash) if f.chat_id > 0 else (raw.types.InputPeerChat(chat_id=-f.chat_id) if f.chat_access_hash == 0 else raw.types.InputPeerChannel(channel_id=utils.get_channel_id(f.chat_id), access_hash=f.chat_access_hash))
            return raw.types.InputPeerPhotoFileLocation(peer=peer, volume_id=f.volume_id, local_id=f.local_id, big=f.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG)
        elif f.file_type == FileType.PHOTO:
            return raw.types.InputPhotoFileLocation(id=f.media_id, access_hash=f.access_hash, file_reference=f.file_reference, thumb_size=f.thumbnail_size)
        return raw.types.InputDocumentFileLocation(id=f.media_id, access_hash=f.access_hash, file_reference=f.file_reference, thumb_size=f.thumbnail_size)

    # ─────────────────────────────────────────────────────────
    # 🍿 ULTRA-SMOOTH STREAMING TUNNEL ENGINE (Zero RAM Lag)
    # ─────────────────────────────────────────────────────────
    async def yield_file(self, msg: Message, offset: int, first_cut: int, last_cut: int, parts: int, chunk_size: int):
        ms = await self.generate_media_session(self.main_bot, msg)
        loc = await self.get_location(await self.generate_file_properties(msg))
        
        # ✅ FIX: कोएब के इन-मेमोरी कचरे को रोकने के लिए फिक्स साइज प्री-एलोकेटेड बफर इंजन ट्यूनिंग
        buffer_pool = bytearray(chunk_size)
        
        try:
            for i in range(1, parts + 1):
                r = await ms.send(raw.functions.upload.GetFile(location=loc, offset=offset, limit=chunk_size))
                if not isinstance(r, raw.types.upload.File) or not r.bytes: 
                    break
                
                chunk = r.bytes
                chunk_len = len(chunk)
                
                # बफर पूल में डेटा कॉपी करें ताकि रैम पर बार-बार नया बकेट न बने
                buffer_pool[:chunk_len] = chunk
                active_chunk = memoryview(buffer_pool)[:chunk_len]
                
                if parts == 1: 
                    yield active_chunk[first_cut:last_cut]
                elif i == 1: 
                    yield active_chunk[first_cut:]
                elif i == parts: 
                    yield active_chunk[:last_cut]
                else: 
                    yield active_chunk
                
                # डायनामिक ऑफसेट कर्सर (Seek/Skip Control Sync)
                offset += chunk_len
                
                # हर 20 चंक्स के बाद अनकैप्ड चंक्स को हवा में उड़ाने के लिए लाइटवेट रैम फ्लश
                if i % 20 == 0:
                    gc.collect()
                    
        except Exception as e:
            logger.error(f"Error during yielding streaming chunk: {e}")
        finally:
            # सॉकेट्स और इन-मेमोरी कचरा साफ करें
            del buffer_pool
            gc.collect()

    # ─────────────────────────────────────────────────────────
    # 📥 BYTESIO PIPELINE (Anti-OOM Protection Sync)
    # ─────────────────────────────────────────────────────────
    async def download_as_bytesio(self, msg: Message):
        """बड़ी फ़ाइलों के कारण कोएब कंटेनर क्रैश होने से रोकने के लिए लाइटवेट कोर डाउनलोडर"""
        ms = await self.generate_media_session(self.main_bot, msg)
        loc = await self.get_location(await self.generate_file_properties(msg))
        limit, offset = 1048576, 0 # 1MB प्रोग्रेसिव ब्लॉक डाउनलोडर
        
        bytes_io = io.BytesIO()
        
        try:
            while True:
                r = await ms.send(raw.functions.upload.GetFile(location=loc, offset=offset, limit=limit))
                if not isinstance(r, raw.types.upload.File) or not r.bytes: 
                    break
                bytes_io.write(r.bytes)
                offset += len(r.bytes)
                
                # हैवी डाउनलोड के समय बैकग्राउंड रैम को फ्री रखें
                if offset % (limit * 10) == 0:
                    gc.collect()
                    
        except Exception as e:
            logger.error(f"Error in download_as_bytesio: {e}")
            
        bytes_io.seek(0)
        gc.collect() # फाइनल सेफ्टी फ्लश
        return bytes_io
