import asyncio
import io  
import time
import logging
from PIL import Image  
from google import genai
from google.genai import types as genai_types
from hydrogram import Client, filters, enums
from info import GEMINI_API_KEY
from utils import is_rate_limited

logger = logging.getLogger(__name__)

# ==========================================
# 🧠 AI CONFIGURATION & PERSONA
# ==========================================
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = None

AI_SYSTEM_INSTRUCTION = (
    "You are the advanced built-in AI Assistant of Fast Finder Telegram Bot. "
    "Provide clear, concise, and helpful answers. "
    "Format your response using HTML tags only: <b>bold</b>, <i>italic</i>, <code>code</code>, "
    "<pre>code block</pre>. Use bullet points with • character. "
    "Do NOT use Markdown syntax like ** or __. Keep answers under 3800 characters."
)

AI_CHAT_MEMORY = {}
MEMORY_TTL = 600

def get_user_history(user_id):
    now = time.time()
    if len(AI_CHAT_MEMORY) > 300:
        expired = [k for k, (v, ts) in AI_CHAT_MEMORY.items() if now - ts > MEMORY_TTL]
        for k in expired:
            AI_CHAT_MEMORY.pop(k, None)

    if user_id in AI_CHAT_MEMORY and (now - AI_CHAT_MEMORY[user_id][1]) < MEMORY_TTL:
        return AI_CHAT_MEMORY[user_id][0]
    return []


async def call_gemini_with_retry(contents_body, ai_config, max_retries=3):
    """503 errors ke liye retry logic with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                ai_client.models.generate_content,
                model='gemini-2.5-flash',
                contents=contents_body,
                config=ai_config
            )
            return response
        except Exception as e:
            err_str = str(e)
            if "503" in err_str and attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Gemini 503, retrying in {wait}s (attempt {attempt+1})")
                await asyncio.sleep(wait)
                continue
            raise  # last attempt ya non-503 error


# ==========================================
# 🗣️ AI CHAT COMMAND
# ==========================================
@Client.on_message(filters.command(["ask", "ai"]))
async def ask_ai(client, message):
    if not ai_client:
        return await message.reply("❌ <b>AI Error:</b> API Key missing from configuration.", 
                                   parse_mode=enums.ParseMode.HTML)

    if is_rate_limited(message.from_user.id, "cmd_ai", seconds=6):
        return await message.reply("⏳ <b>Too Fast!</b> Please wait a few seconds before asking again.",
                                   parse_mode=enums.ParseMode.HTML)

    if len(message.command) < 2 and not message.reply_to_message:
        return await message.reply(
            "⚡ <b>Gemini 2.5 Flash</b>\n\n"
            "<b>Usage:</b>\n"
            "• <code>/ai Who are you?</code>\n"
            "• Reply to any text/photo with <code>/ai</code>\n\n"
            "<i>💡 Remembers last 10 minutes of conversation!</i>",
            parse_mode=enums.ParseMode.HTML
        )

    question = ""
    image_input = None
    user_id = message.from_user.id

    # Input text processing
    if len(message.command) > 1:
        question = message.text.split(None, 1)[1]
    elif message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        question = message.reply_to_message.text or message.reply_to_message.caption

    # Image processing (Vision)
    if message.reply_to_message and message.reply_to_message.photo:
        status_msg = await message.reply("⬇️ <i>Downloading image...</i>", 
                                         parse_mode=enums.ParseMode.HTML)
        try:
            photo_stream = await client.download_media(message.reply_to_message.photo, in_memory=True)
            image_input = Image.open(io.BytesIO(photo_stream.getbuffer()))
            await status_msg.delete()
        except Exception as e:
            await status_msg.delete()
            return await message.reply(f"❌ <b>Image Error:</b> <code>{e}</code>",
                                       parse_mode=enums.ParseMode.HTML)

    if not question and not image_input:
        return await message.reply("❌ Please ask a question or reply to a photo.",
                                   parse_mode=enums.ParseMode.HTML)

    if image_input and not question:
        question = "Examine this image carefully and describe it in detail."

    # Build contents
    history = get_user_history(user_id)
    contents_body = []

    if image_input:
        # ✅ Fixed: proper Part wrapping for vision
        contents_body = [
            genai_types.Part.from_text(text=question),
            genai_types.Part.from_image(image=image_input)
        ]
    else:
        # Text with history
        for role, text in history:
            contents_body.append(genai_types.Content(
                role=role,
                parts=[genai_types.Part.from_text(text=text)]
            ))
        contents_body.append(genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=question)]
        ))

    status = await message.reply("⚡ <i>Thinking...</i>", parse_mode=enums.ParseMode.HTML)
    await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)

    try:
        ai_config = genai_types.GenerateContentConfig(
            system_instruction=AI_SYSTEM_INSTRUCTION,
            temperature=0.7,
            top_p=0.95
        )

        response = await call_gemini_with_retry(contents_body, ai_config)

        if not response.text:
            return await status.edit("❌ <b>AI Error:</b> Empty response.",
                                     parse_mode=enums.ParseMode.HTML)

        answer = response.text

        # Update history (only for text, not vision)
        if not image_input:
            history.append(("user", question))
            history.append(("model", answer))
            if len(history) > 6:
                history = history[-6:]
            AI_CHAT_MEMORY[user_id] = (history, time.time())

        # Send response (HTML safe splitting)
        if len(answer) > 4000:
            await status.delete()
            chunks = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
            for chunk in chunks:
                await message.reply(chunk, parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(0.5)
        else:
            await status.edit(answer, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        await status.edit(
            f"❌ <b>AI Error:</b> <code>{str(e)[:200]}</code>",
            parse_mode=enums.ParseMode.HTML
        )
