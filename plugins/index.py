import re
import time
import asyncio
import logging
from hydrogram import Client, filters, enums
from hydrogram.errors import FloodWait
from info import ADMINS
# मुख्य सिंक इम्पोर्ट
from database.ia_filterdb import save_file
from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time

logger = logging.getLogger(__name__)
lock = asyncio.Lock()

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    data_parts = query.data.split("#")
    ident = data_parts[1]
    
    if ident == 'yes':
        # कलेक्शन सिलेक्शन बटन दिखाएं
        chat = data_parts[2]
        lst_msg_id = data_parts[3]
        skip = data_parts[4]
        
        buttons = [
            [
                InlineKeyboardButton('✅ PRIMARY', callback_data=f'index#start#{chat}#{lst_msg_id}#{skip}#primary'),
                InlineKeyboardButton('📂 CLOUD', callback_data=f'index#start#{chat}#{lst_msg_id}#{skip}#cloud')
            ],
            [
                InlineKeyboardButton('📦 ARCHIVES', callback_data=f'index#start#{chat}#{lst_msg_id}#{skip}#archive')
            ],
            [
                InlineKeyboardButton('❌ CANCEL', callback_data='close_data')
            ]
        ]
        await query.message.edit(
            f"🗂️ <b>Select Collection to Index:</b>\n"
            f"⏭️ Skip: <code>{skip}</code>\n\n"
            "• <b>PRIMARY</b> - Main database\n"
            "• <b>CLOUD</b> - Cloud storage\n"
            "• <b>ARCHIVES</b> - Archive storage",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    elif ident == 'ask_skip':
        # कस्टम स्किप सिलेक्शन
        chat = data_parts[2]
        lst_msg_id = data_parts[3]
        
        await query.message.edit("📝 <b>Send the number of messages to skip:</b>\n\nSend <code>0</code> to start from beginning.")
        
        try:
            msg = await bot.listen(chat_id=query.message.chat.id, user_id=query.from_user.id, timeout=60)
            skip = int(msg.text)
            await msg.delete() # यूज़र का मैसेज डिलीट करें
        except:
            return await query.message.edit("❌ Invalid number or Timeout. Try again.")
            
        buttons = [
            [
                InlineKeyboardButton('✅ PRIMARY', callback_data=f'index#start#{chat}#{lst_msg_id}#{skip}#primary'),
                InlineKeyboardButton('📂 CLOUD', callback_data=f'index#start#{chat}#{lst_msg_id}#{skip}#cloud')
            ],
            [
                InlineKeyboardButton('📦 ARCHIVES', callback_data=f'index#start#{chat}#{lst_msg_id}#{skip}#archive')
            ],
            [
                InlineKeyboardButton('❌ CANCEL', callback_data='close_data')
            ]
        ]
        await query.message.edit(
            f"🗂️ <b>Select Collection to Index:</b>\n"
            f"⏭️ Skip: <code>{skip}</code>\n\n"
            "• <b>PRIMARY</b> - Main database\n"
            "• <b>CLOUD</b> - Cloud storage\n"
            "• <b>ARCHIVES</b> - Archive storage",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif ident == 'start':
        chat = data_parts[2]
        lst_msg_id = data_parts[3]
        skip = data_parts[4]
        collection = data_parts[5]
        
        msg = query.message
        await msg.edit(f"Starting Indexing to <b>{collection.upper()}</b> collection...")
        
        try: chat = int(chat)
        except: pass
        
        await index_files_to_db(int(lst_msg_id), chat, msg, bot, int(skip), collection)
    
    elif ident == 'cancel':
        temp.CANCEL = True
        await query.message.edit("Trying to cancel Indexing...")


# जब कोई फॉरवर्डेड मैसेज या चैनल लिंक भेजा जाए
@Client.on_message(filters.private & filters.user(ADMINS) & (filters.forwarded | filters.text))
async def auto_index(bot, message):
    if message.text and not message.text.startswith("https://t.me"):
        if not message.forward_from_chat:
            return
    
    if lock.locked():
        return await message.reply('⏳ Wait until previous indexing process completes.')
    
    # फॉरवर्डेड मैसेजेस को हैंडल करें
    if message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    
    # चैनल लिंक्स को हैंडल करें
    elif message.text and message.text.startswith("https://t.me"):
        try:
            msg_link = message.text.split("/")
            last_msg_id = int(msg_link[-1])
            chat_id = msg_link[-2]
            if chat_id.isnumeric():
                chat_id = int(("-100" + chat_id))
        except:
            return await message.reply('❌ Invalid message link!')
    else:
        return
    
    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f'❌ Error: {e}')

    if chat.type != enums.ChatType.CHANNEL:
        return await message.reply("⚠️ I can only index channels.")

    buttons = [
        [
            InlineKeyboardButton('⚡ START INDEXING (Skip 0)', callback_data=f'index#yes#{chat_id}#{last_msg_id}#0')
        ],
        [
            InlineKeyboardButton('📝 CUSTOM SKIP', callback_data=f'index#ask_skip#{chat_id}#{last_msg_id}')
        ],
        [
            InlineKeyboardButton('❌ CANCEL', callback_data='close_data')
        ]
    ]
    await message.reply(
        f'🗂️ <b>Ready to Index:</b>\n\n'
        f'📢 Channel: <b>{chat.title}</b>\n'
        f'📨 Total Messages: <code>{last_msg_id}</code>\n\n'
        f'Choose an option:',
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def index_files_to_db(lst_msg_id, chat, msg, bot, skip, collection_type="primary"):
    start_time = time.time()
    last_update_time = time.time() # फ्लडवेट प्रोटेक्शन टाइमर ट्रैकर
    
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    badfiles = 0
    current = skip
    
    async with lock:
        try:
            async for message in bot.iter_messages(chat, lst_msg_id, skip):
                time_taken = get_readable_time(time.time() - start_time)
                
                if temp.CANCEL:
                    temp.CANCEL = False
                    await msg.edit(
                        f"<b>✅ Successfully Cancelled!</b>\n"
                        f"📚 Collection: <code>{collection_type.upper()}</code>\n"
                        f"⏱ Completed in: <code>{time_taken}</code>\n\n"
                        f"📁 Saved Files: <code>{total_files}</code>\n"
                        f"🔄 Duplicates: <code>{duplicate}</code>\n"
                        f"🗑 Deleted: <code>{deleted}</code>\n"
                        f"❌ No Media: <code>{no_media + unsupported}</code>\n"
                        f"⚠️ Unsupported: <code>{unsupported}</code>\n"
                        f"❗ Errors: <code>{errors}</code>\n"
                        f"🚫 Bad Files: <code>{badfiles}</code>"
                    )
                    return
                
                current += 1
                
                # ✅ FIX: टेलीग्राम फ्लड प्रिवेंटर — हर 50 मैसेज + न्यूनतम 4 सेकंड का टाइम इंटरवल गैप अनिवार्य है
                if current % 50 == 0 and (time.time() - last_update_time > 4):
                    last_update_time = time.time()
                    btn = [[
                        InlineKeyboardButton('CANCEL', callback_data=f'index#cancel#{chat}#{lst_msg_id}#{skip}')
                    ]]
                    try:
                        await msg.edit_text(
                            text=f"<b>📊 Indexing Progress</b>\n"
                            f"📚 Collection: <code>{collection_type.upper()}</code>\n"
                            f"⏱ Time: <code>{time_taken}</code>\n\n"
                            f"📨 Total Received: <code>{current}</code>\n"
                            f"📁 Saved: <code>{total_files}</code>\n"
                            f"🔄 Duplicates: <code>{duplicate}</code>\n"
                            f"🗑 Deleted: <code>{deleted}</code>\n"
                            f"❌ No Media: <code>{no_media + unsupported}</code>\n"
                            f"⚠️ Unsupported: <code>{unsupported}</code>\n"
                            f"❗ Errors: <code>{errors}</code>\n"
                            f"🚫 Bad Files: <code>{badfiles}</code>", 
                            reply_markup=InlineKeyboardMarkup(btn)
                        )
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                    except Exception:
                        pass
                
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                
                # फाइल साइज चेक करें - 2 MB से छोटी फाइलों को स्किप करें
                file_size = getattr(media, 'file_size', 0)
                if file_size < 2097152:  # बाइट्स में 2 MB
                    badfiles += 1
                    continue
                
                media.caption = message.caption
                # नाम को साफ़ और स्वच्छ करना (Safe Name Cleaning)
                try:
                    if getattr(media, 'file_name', None):
                        media.file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name)).strip()
                except:
                    pass
                
                # सिलेक्टेड कलेक्शन में सेव करें
                sts = await save_file(media, collection_type=collection_type)
                
                if sts == 'suc':
                    total_files += 1
                elif sts == 'dup':
                    duplicate += 1
                elif sts == 'err':
                    errors += 1
                    
        except Exception as e:
            logger.error(f"Indexing Crash Intercepted: {e}")
            await msg.reply(f'❌ Index canceled due to Error - {e}')
        else:
            time_taken = get_readable_time(time.time() - start_time)
            await msg.edit(
                f'<b>✅ Successfully Indexed!</b>\n'
                f'📚 Collection: <code>{collection_type.upper()}</code>\n'
                f'⏱ Completed in: <code>{time_taken}</code>\n\n'
                f'📁 Saved Files: <code>{total_files}</code>\n'
                f'🔄 Duplicates: <code>{duplicate}</code>\n'
                f'🗑 Deleted: <code>{deleted}</code>\n'
                f'❌ No Media: <code>{no_media + unsupported}</code>\n'
                f'⚠️ Unsupported: <code>{unsupported}</code>\n'
                f'❗ Errors: <code>{errors}</code>\n'
                f'🚫 Bad Files: <code>{badfiles}</code>'
            )
