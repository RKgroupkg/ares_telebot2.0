import telegram
import sys
from telegram import Update,ChatAction,InlineKeyboardMarkup, InlineKeyboardButton,ParseMode # version = 12.8
from telegram.error import Conflict
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext,CommandHandler,CallbackQueryHandler
import google.generativeai as genai
import threading
import textwrap
import PIL.Image
import os,json
import time,datetime
import html
import psutil
import secrets
import traceback
import asyncio
from search_engine_parser import GoogleSearch
import wikipedia,requests
from wikipedia.exceptions import DisambiguationError, PageError
from youtube_search import YoutubeSearch
import yt_dlp
from datetime import timedelta
import uuid,math

from keep_alive import keep_alive
from logs import logger
from bing_image_downloader import downloader 
from utils.FireDB import FireBaseDB
from utils import escape,rate_limit
from utils.inline import (
        command_limit_inline,
        Invalid_arg,
        Admin_error,
        DisambiguationError,
        music_limit_error,
        
)

import shutil
import jsonpickle

from config import *


PASSWORD = os.environ.get('password')

chat_histories ={}
api_key = os.environ.get('gemnie_api')
genai.configure(api_key=api_key)
telegram_bot_token = os.environ.get('telegram_api')

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=safety_settings,
  generation_config=generation_config,
  system_instruction= system_instruction)



def get_explanation(update: Update, context: CallbackContext, command: str):
    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data=f"back_{command.split('_')[0]}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    command_title = command.replace("_", " ").title()  # Convert to Pascal case
    formatted_text = f"<b>{command_title}</b>\n\n{INFO_help.get(command, 'No information available for this command.')}"
    if len(formatted_text) > 1024:
        keyboard = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
    ]   
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id ,text=formatted_text, reply_markup=reply_markup, parse_mode='HTML',link_preview=False)
    else:
        if update.callback_query.message.photo:
            try:
                update.callback_query.edit_message_caption(formatted_text, reply_markup=reply_markup, parse_mode='HTML',link_preview=False)
                return
            except Exception as e:
                logger.error(f"An error occure while getting explanition of inline and sendit as caption error:{e}")
                    
       
        keyboard = [
                [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
        ]   
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.edit_message_text(formatted_text, reply_markup=reply_markup, parse_mode='HTML',link_preview=False)
           
# Function to handle the initial home command
def home(update: Update, context: CallbackContext):
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        keyboard = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
            ]   
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id ,text="Yᴏᴜ ᴀʀᴇ ʙᴇᴇɴ 🚫ʙʟᴏᴄᴋᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ. ᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴏᴡɴᴇʀ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏ🧐.", reply_markup=reply_markup, parse_mode='HTML',link_preview=False)
        
        return
    keyboard = [
        [InlineKeyboardButton("🛠️ᴄᴏᴍᴍᴀɴᴅs", callback_data="home_commands")],
        [InlineKeyboardButton("✍ᴘʀᴏᴍᴘᴛɪɴɢ", callback_data="home_prompting")],
        [InlineKeyboardButton("📝ᴇxᴛʀᴀ ɪɴғᴏ", callback_data="home_extra_info")],
        [InlineKeyboardButton("💲sᴜᴘᴘᴏʀᴛ", callback_data="home_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = """👋 Wᴇʟᴄᴏᴍᴇ ᴛᴏ Aʀᴇs! Yᴏᴜʀ ᴀʟʟ-ɪɴ-ᴏɴᴇ ᴅɪɢɪᴛᴀʟ ᴀssɪsᴛᴀɴᴛ ʀᴇᴀᴅʏ ᴛᴏ ᴍᴀᴋᴇ ʏᴏᴜʀ ʟɪғᴇ ᴇᴀsɪᴇʀ.\n Wɪᴛʜ ᴘᴏᴡᴇʀғᴜʟ AI ᴄᴀᴘᴀʙɪʟɪᴛɪᴇs, Aʀᴇs ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ᴡɪᴛʜ ᴛᴀsᴋs, ᴘʀᴏᴠɪᴅᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ, ᴀɴᴅ ᴇᴠᴇɴ ᴇɴɢᴀɢᴇ ɪɴ ғʀɪᴇɴᴅʟʏ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ.\n Lᴇᴛ's ɢᴇᴛ sᴛᴀʀᴛᴇᴅ ᴏɴ ᴍᴀᴋɪɴɢ ʏᴏᴜʀ ᴅɪɢɪᴛᴀʟ ᴇxᴘᴇʀɪᴇɴᴄᴇ sᴍᴀʀᴛᴇʀ ᴀɴᴅ ᴍᴏʀᴇ ᴇғғɪᴄɪᴇɴᴛ! 🚀 \n\n <b>ᴘɪᴄᴋ ᴛʜᴇ ᴛᴏᴘɪᴄ ɪɴ ᴡʜɪᴄʜ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ:- </b>"""
    with open(LOGO_PATH, "rb") as photo:
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=photo,
            caption=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )




def _home(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🛠️ᴄᴏᴍᴍᴀɴᴅs", callback_data="home_commands")],
        [InlineKeyboardButton("✍ᴘʀᴏᴍᴘᴛɪɴɢ", callback_data="home_prompting")],
        [InlineKeyboardButton("📝ᴇxᴛʀᴀ ɪɴғᴏ", callback_data="home_extra_info")],
        [InlineKeyboardButton("💲sᴜᴘᴘᴏʀᴛ", callback_data="home_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = """👋 Wᴇʟᴄᴏᴍᴇ ᴛᴏ Aʀᴇs! Yᴏᴜʀ ᴀʟʟ-ɪɴ-ᴏɴᴇ ᴅɪɢɪᴛᴀʟ ᴀssɪsᴛᴀɴᴛ ʀᴇᴀᴅʏ ᴛᴏ ᴍᴀᴋᴇ ʏᴏᴜʀ ʟɪғᴇ ᴇᴀsɪᴇʀ.\n Wɪᴛʜ ᴘᴏᴡᴇʀғᴜʟ AI ᴄᴀᴘᴀʙɪʟɪᴛɪᴇs, Aʀᴇs ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ᴡɪᴛʜ ᴛᴀsᴋs, ᴘʀᴏᴠɪᴅᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ, ᴀɴᴅ ᴇᴠᴇɴ ᴇɴɢᴀɢᴇ ɪɴ ғʀɪᴇɴᴅʟʏ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴ.\n Lᴇᴛ's ɢᴇᴛ sᴛᴀʀᴛᴇᴅ ᴏɴ ᴍᴀᴋɪɴɢ ʏᴏᴜʀ ᴅɪɢɪᴛᴀʟ ᴇxᴘᴇʀɪᴇɴᴄᴇ sᴍᴀʀᴛᴇʀ ᴀɴᴅ ᴍᴏʀᴇ ᴇғғɪᴄɪᴇɴᴛ! 🚀 \n\n <b>ᴘɪᴄᴋ ᴛʜᴇ ᴛᴏᴘɪᴄ ɪɴ ᴡʜɪᴄʜ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ:- </b>"""
    update.callback_query.edit_message_caption(text, reply_markup=reply_markup,parse_mode='HTML')

# Function to handle callback queries
def button_click(update: Update, context: CallbackContext):


    query = update.callback_query
    query.answer()
    query_data = query.data
    if query_data.startswith("home_"):
        handle_home_command(update, context, query_data)
    elif query_data.startswith("command_"):
        get_explanation(update, context ,query_data)
    elif query_data.startswith("prompting_"):
        get_explanation(update, context ,query_data)
    elif query_data.startswith("extra_info_"):
        get_explanation(update, context ,query_data)
    elif query_data.startswith("audio:") or query_data.startswith("video:"):
        Youtube_music(update, context)
    elif query_data == "home_support":
        handle_support(update, context)
    elif query_data.startswith("back"):
        go_back(update, context)
    elif query_data == "close":
        query.message.delete()
    elif query_data == "Clear_history_confirmation":
        handel_clear_history(update, context)
    else:
        get_explanation(update, context ,query_data)



def Youtube_music(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    message_id = query.message.message_id  # Get the ID of the message to delete



    user_name = query.from_user.first_name
    user_id = query.from_user.id
    action, video_uuid = query.data.split(":")
    data = video_urls.get(video_uuid)
    user_info = f"<a href='tg://user?id={str(user_id)}'>{html.escape(user_name)}</a>"

    video_url = f"https://youtube.com{data['url_suffix']}"
    if not video_url:
        update.callback_query.edit_message_caption("Error: Video URL not found.")
        return
    title = html.escape(data["title"][:40])
    duration = data["duration"]
    views = data["views"]
    channel_name = data.get("channel", "Unknown Channel")
    thumbnail = data["thumbnails"][0]
    thumb_name = f"thumb{str(uuid.uuid4())}.jpg"
    keyboard = [[InlineKeyboardButton("Watch Video on YouTube", url=video_url)]]
    inline_keyboard = InlineKeyboardMarkup(keyboard)

    
    rep = (
                    f"<b>Title:</b>        <i>{title}</i>\n"
                    f"<b>Duration:</b>     <i>{duration}</i>\n"
                    f"<b>Views:</b>        <i>{escape.beautify_views(views)}</i>\n"
                    f"<b>Requested by:</b> {user_info}"
                )
    
    update.callback_query.edit_message_caption(f"Downloading {action}... \n\n{rep}",parse_mode='HTML')
    download_progress = {}
    def progress_hook(d):
        if d['status'] == 'downloading':
            video_id = d['info_dict']['id']
            current_progress = d['downloaded_bytes'] / d['total_bytes'] * 100

            
            # Round progress to nearest 10%
            rounded_progress = math.ceil(current_progress / 10) * 10

            total_bars = 20
            filled_bars = int(float(rounded_progress) / 100 * total_bars)
            loading_bar = '█' * filled_bars + '░' * (total_bars - filled_bars)
                    
            # Only send updates if the progress has reached the next 10% increment
            if video_id not in download_progress or rounded_progress >= download_progress[video_id] + 10:
                download_progress[video_id] = rounded_progress
                update.callback_query.edit_message_caption(f"Downloading {action}\n\n {loading_bar} {rounded_progress}%\n\n{rep}",parse_mode='HTML')

    def download_media():
        try:
            ydl_opts = {
            "format": "bestaudio[ext=m4a]" if action == "audio" else "best[ext=mp4]",
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "retries": 2,
            "fragment_retries": 3,
            "continuedl": True,
            "nocheckcertificate": True,
            "http_chunk_size": 10485760,
            "progress_hooks": [progress_hook],
            "external_downloader_args": ["-x", "20", "-k", "1M"]  # 20 connections, 1MB chunks
        }


            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if action == "audio":
                    info_dict = ydl.extract_info(video_url, download=False)
                    file_name = ydl.prepare_filename(info_dict)
                    ydl.process_info(info_dict)  # Download audio now
                    thumb = requests.get(thumbnail, allow_redirects=True)
                    open(thumb_name, "wb").write(thumb.content)
                else:
                    info_dict = ydl.extract_info(video_url, download=True)
                    file_name = ydl.prepare_filename(info_dict)

    
            
                context.bot.send_chat_action(chat_id=query.message.chat_id, action="upload_" + ("audio" if action == "audio" else "video"))
                context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)

                with open(file_name, "rb") as file:
                    if action == "audio":
                        
                        with open(thumb_name, "rb") as thumb_file:
                            context.bot.send_audio(
                                    chat_id=update.effective_chat.id,
                                    audio=file,
                                    thumb=thumb_file,
                                    caption=rep,
                                    parse_mode='HTML',
                                    title=title,
                                    performer=channel_name,
                                    reply_markup=inline_keyboard,
                                    duration=int(duration.split(':')[0]) * 60 + int(duration.split(':')[1])  # Convert duration to seconds
                                )
                    else:
                        context.bot.send_video(chat_id=query.message.chat_id, video=file, caption=rep,parse_mode='HTML',reply_markup=inline_keyboard)

                try:
                    os.remove(file_name)
                except Exception as e:
                    print(f"Error while deleting Audi/video file:{file_name},error:{e}")
                try:
                    if os.path.exists(thumb_name):
                        os.remove(thumb_name)
                except Exception as e:
                    print(f"Error while deleting Thumnail file:{thumb_name},error:{e}")


        except Exception as e:
            update.callback_query.edit_message_caption(f"Error during download: {str(e)}")
            logger.error(f"Error during download: {str(e)}")

    threading.Thread(target=download_media).start()




def handle_home_command(update: Update, context: CallbackContext, query_data: str):
    if query_data == "home_commands":
        commands(update, context)
    elif query_data == "home_prompting":
        prompting(update, context)
    elif query_data == "home_extra_info":
        extra_info(update, context)
    elif query_data == "home_support":
        handle_support(update, context)

def go_back(update: Update, context: CallbackContext):
    # Check if callback query is None, use update.message instead
    if update.callback_query:
        query_data = update.callback_query.data
    elif update.message:
        # Extract callback data from the text of the message
        query_data = update.message.text.split(":")[-1].strip()

    # Default to home menu if unable to determine previous menu
    previous_menu = _home

    if query_data == "back_command":
        previous_menu = commands
    elif query_data == "back_prompting":
        previous_menu = prompting
    elif query_data == "back_extra":
        previous_menu = extra_info

    # Display the previous menu
    previous_menu(update, context)

def commands(update: Update, context: CallbackContext):
    keyboard = [
    [InlineKeyboardButton("👮‍♂️ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅ", callback_data="command_admin_command")],
    [InlineKeyboardButton("🤖ᴀɪ ᴄᴏᴍᴍᴀɴᴅ", callback_data="command_ai_command")],
    [InlineKeyboardButton("🔍sᴇᴀʀᴄʜɪɴɢ ᴄᴏᴍᴍᴀɴᴅ", callback_data="command_searching_command")],
    [InlineKeyboardButton("⚙️sᴇᴛᴛɪɴɢ ᴄᴏᴍᴍᴀɴᴅ", callback_data="command_setting_command")],
    [InlineKeyboardButton("🛠️ᴜᴛɪʟɪᴛʏ ᴄᴏᴍᴍᴀɴᴅ", callback_data="command_utility_command")],
    [InlineKeyboardButton("❓Who are admin?", callback_data="command_who_are_admin")],
    [InlineKeyboardButton("❓what is command limit rate?", callback_data="Command_limit_rate")],
    [InlineKeyboardButton("← ʙᴀᴄᴋ", callback_data="back")],
]

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = """<i>Cᴏᴍᴍᴀɴᴅs ɪɴ Tᴇʟᴇɢʀᴀᴍ ᴀʀᴇ sʜᴏʀᴛᴄᴜᴛs ᴛᴏ ᴘᴇʀғᴏʀᴍ sᴘᴇᴄɪғɪᴄ ᴀᴄᴛɪᴏɴs ᴏʀ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴏ̨ᴜɪᴄᴋʟʏ. Tʜᴇʏ sᴛᴀʀᴛ ᴡɪᴛʜ ᴀ '/' ғᴏʟʟᴏᴡᴇᴅ ʙʏ ᴀ ᴋᴇʏᴡᴏʀᴅ.\n Aʀɢᴜᴍᴇɴᴛs ᴄᴀɴ ʙᴇ ɢɪᴠᴇɴ ᴀғᴛᴇʀ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ɪᴛs ʙᴇʜᴀᴠɪᴏʀ.\n Fᴏʀ ᴇxᴀᴍᴘʟᴇ, "<code>/wiki New York</code>" ғᴇᴛᴄʜᴇs ᴛʜᴇ ɪɴғᴏ ғᴏʀ Nᴇᴡ Yᴏʀᴋ.</i>\n\n <b>Cʜᴏᴏsᴇ ᴡʜɪᴄʜ ᴛʏᴘᴇ ᴏғ ᴄᴏᴍᴍᴀɴᴅs:-</b>"""
    update.callback_query.edit_message_caption(text, reply_markup=reply_markup,parse_mode='HTML')

def handel_clear_history(update: Update, context: CallbackContext):
        # Clear the chat history and start a new one with the default prompt
        chat_id = update.callback_query.message.chat_id
        chat_histories[chat_id] = model.start_chat(history=[])
        DB.chat_history_add(chat_id,[])
        keyboard = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],]   
        keyboard  = InlineKeyboardMarkup(keyboard)

        update.callback_query.edit_message_text("Cʜᴀᴛ ʜɪsᴛᴏʀʏ sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴇᴀʀᴇᴅ.", reply_markup=keyboard, parse_mode='HTML')


def prompting(update: Update, context: CallbackContext):
    keyboard = [
    [InlineKeyboardButton("📜ɪɴᴛʀᴏᴅᴜᴄᴛɪᴏɴ", callback_data="prompting_what")],
    [InlineKeyboardButton("📂ᴍᴇᴅɪᴀ ᴘʀᴏᴍᴘᴛɪɴɢ", callback_data="prompting_media_prompting")],
    [InlineKeyboardButton("💡sᴜᴘᴘᴏʀᴛᴇᴅ ғᴏʀᴍᴀᴛ", callback_data="prompting_supported_format")],
    [InlineKeyboardButton("← ʙᴀᴄᴋ", callback_data="back")]
]

    text = """<b>Introduction to prompt design</b> 
<i>Prompt design is the process of creating prompts that elicit the desired response from language models.
Writing well structured prompts is an essential part of ensuring accurate, high quality responses from a language model. 
This page introduces some basic concepts, strategies, and best practices to get you started in designing prompts.</i>\n\n<b>Choose any sub-topic in prompting:-</b>"""
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_caption(text, reply_markup=reply_markup,parse_mode='HTML')

def extra_info(update: Update, context: CallbackContext):
    keyboard = [
    [InlineKeyboardButton("💻ᴅᴇᴠᴇʟᴏᴘᴇʀ", callback_data="extra_info_developer")],
    [InlineKeyboardButton("🐛ʙᴜɢ/ᴠᴇʀsɪᴏɴ", callback_data="extra_info_bug_version")],
    [InlineKeyboardButton("🤝ᴄᴏɴᴛʀɪʙᴜᴛᴇ", callback_data="extra_info_contribute")],
    [InlineKeyboardButton("💬sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", callback_data="extra_info_support_chat")],
    [InlineKeyboardButton("🤔ʜᴏᴡ ᴛᴏ ᴜsᴇ ɪɴ ɢʀᴏᴜᴘ?", callback_data="extra_info_how_to_use_in_group")],
    [InlineKeyboardButton("← ʙᴀᴄᴋ", callback_data="back")]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_caption("Choose an info type:", reply_markup=reply_markup)





def handle_support(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = """
<b>Support:</b>
You can support me with a small donation 💵 or a cup of coffee ☕ on <a href="https://www.buymeacoffee.com/Rkgroup">Buy Me a Coffee</a>.

<b>Telegram Account:</b> <a href="https://t.me/Rkgroup5316">@Rkgroup5316</a>
<b>Support Chat:</b> Join our official support group on <a href="https://t.me/AresChatBotAi">Telegram</a>.
<b>GitHub:</b> Check out our projects on <a href="https://github.com/RKgroupkg">GitHub</a>.


"""

    update.callback_query.edit_message_caption(text, reply_markup=reply_markup,parse_mode='HTML')

    
     
def get_chat_history(chat_id):
    """Retrieves chat history for the given chat ID.

    Args:
        chat_id (int): The unique identifier of the chat.

    Returns:
        GenerativeModel: The Generative AI model instance with chat history.

    Raises:
        RuntimeError: If there's an error retrieving data from the cloud.
    """
    # Check if chat history exists locally
    if chat_id in chat_histories:
        return chat_histories[chat_id]  # Return existing history

    # If not found locally, try retrieving from cloud
    try:
        userData = DB.user_exists(chat_id)
        if userData:
            instruction = userData['system_instruction']

            if instruction =='default':
                instruction = system_instruction            
            
            model_temp = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",
                safety_settings=safety_settings,
                generation_config=generation_config,
                system_instruction=instruction
            )
            history=jsonpickle.decode(userData['chat_session'])   # decode history and then store
            logger.debug(f"History :{history}")

            chat_histories[chat_id] = model_temp.start_chat(history=history )
            logger.info(f"Chat id:{chat_id} did not exist locally, got previous data from cloud")
            return chat_histories[chat_id]  # Return retrieved history
        else:
            # User doesn't exist in cloud, create a new one
            DB.create_user(chat_id)
            chat_histories[chat_id] = model.start_chat(history=[] )
            logger.info(f"Chat id:{chat_id} did not exist, created one")
            return chat_histories[chat_id]  # Return new model

    except Exception as e:
        # Handle errors during cloud data retrieval
        logger.error(f"Error retrieving chat history for chat_id: {chat_id}, Error: {e}")





# Function to generate response using gemnie
def generate_response(chat_id, input_text: str) -> str:
    chat_history = get_chat_history(chat_id)
    logger.info("Generating response...")
    try:
        try:
            response = chat_history.send_message(input_text)
        except Exception as e:
            logger.error(f"Error occured while genrating response: {e}")
            response= f"Eʀʀᴏʀ🔧 ᴏᴄᴄᴜʀᴇᴅ ᴡʜɪʟᴇ ɢᴇɴʀᴀᴛɪɴɢ ʀᴇsᴘᴏɴsᴇ: {e}"
        
        if not hasattr(response, "text"):
          response = f"*𝑀𝑦 𝑎𝑝𝑜𝑙𝑜𝑔𝑖𝑒𝑠*, I'ᴠᴇ ʀᴇᴀᴄʜᴇᴅ ᴍʏ ᴜsᴀɢᴇ ʟɪᴍɪᴛ ғᴏʀ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ. ⏳ Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ɪɴ ᴀ ғᴇᴡ ᴍɪɴᴜᴛᴇs. \n\n 📡Rᴇsᴘᴏɴsᴇ: {response}"
        
        else:
          response = response.text
            
        def update():
            try:
                with lock:  # Use a thread-safe lock for Firebase access
                    DB.chat_history_add(chat_id, chat_history.history)
                return response if input_text else "error"
            except Exception as e:
                logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
                return f"Sᴏʀʀʏ, I ᴄᴏᴜʟᴅɴ'ᴛ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʀᴇsᴘᴏɴsᴇ ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.\n\n🛑Eʀʀᴏʀ: {e}"

        # Create a lock to ensure only one thread updates Firebase at a time
        lock = threading.Lock()

        # Create a thread to update Firebase asynchronously in the background
        thread = threading.Thread(target=update)
        thread.start()
        return response

    except Exception as e:
            logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
            return f"Sᴏʀʀʏ, I ᴄᴏᴜʟᴅɴ'ᴛ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʀᴇsᴘᴏɴsᴇ ᴀᴛ ᴛʜᴇ ᴍᴏᴍᴇɴᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.\n\n🛑Eʀʀᴏʀ: {e}"



def change_prompt(update: Update, context: CallbackContext) -> None:
    """Change the prompt for generating responses."""
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return

    
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
        
    chat_id = update.message.chat_id
    new_promt = " ".join(context.args)
    logger.info(f"chatId({chat_id}) changed its Promt to :'{new_promt}'")
    if new_promt :
        if  context.args[0].lower() == 'd' or context.args[0].lower() == 'default' or context.args[0].lower() == 'orignal':
        
           chat_histories[chat_id] = model.start_chat(history=[] )
           update.message.reply_text(f"Tʜᴇ ᴘʀᴏᴍᴘᴛ ʜᴀs ʙᴇᴇɴ 🎉sᴜᴄᴄᴇssғᴜʟʟʏ🎉 ᴄʜᴀɴɢᴇᴅ ᴛᴏ: <b>'ᴅᴇғᴀᴜʟᴛ'</b>", parse_mode='HTML')
           DB.Update_instruction(chat_id)
           
            
        else:
                model_temp = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=safety_settings,
                    generation_config=generation_config,
                    system_instruction=new_promt )
                chat_histories[chat_id] = model_temp.start_chat(history=[])
    
                update.message.reply_text(f"Tʜᴇ ᴘʀᴏᴍᴘᴛ ʜᴀs ʙᴇᴇɴ 🎉sᴜᴄᴄᴇssғᴜʟʟʏ🎉 ᴄʜᴀɴɢᴇᴅ ᴛᴏ: <b>'{new_promt}'</b>", parse_mode='HTML')
                DB.Update_instruction(chat_id,new_promt)
        DB.chat_history_add(chat_id,[])
        command_logger.log_command(update.effective_user.id,'/changeprompt')
    else:
            update.message.reply_text(f"Eʀʀᴏʀ 400! ᴘʀᴏᴍᴘᴛ ɴᴏᴛ ᴘʀᴏᴠɪᴅᴇᴅ!", parse_mode='HTML')
    




def process_message(update: Update, context: CallbackContext) -> None:
        
        if not update.message:
          return
        if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
        chat_id = update.message.chat_id
        if update.message.reply_to_message:
            reply_to_bot = (
              update.message.reply_to_message
              and update.message.reply_to_message.from_user.id == context.bot.id )
        
        else:
            reply_to_bot = False

        user_message = update.message.text.lower()
        if user_message.startswith(("hey ares", "hi ares", "ares", "yo ares","hello ares","what's up ares")) or update.message.chat.type == 'private' or reply_to_bot:
            username = update.message.from_user.username

            if update.message.reply_to_message:

                # Extract the text from the replied message
                original_message = update.message.reply_to_message.text
                reply_to_message = update.message.text
                user_message = f"Original message: {original_message}\nReply to that message: {reply_to_message}"
                threading.Thread(target=process_message_thread, args=(update,chat_id, user_message,context)).start()
            else:
                threading.Thread(target=process_message_thread, args=(update,chat_id, user_message,context)).start()

            if username:
                logger.info(f"{username}: {user_message}")
            else:
                logger.info(f"Someone: {user_message}")


def process_message_thread(update: Update,chat_id :str,user_message: str,context: CallbackContext) -> None:
        try:
            # Send the initial "responding..." message
            prompt = f"{user_message}"
            context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

            # Generate the response
            response =generate_response(chat_id,prompt)
            
    
            # Code that might raise the AttributeError (e.g., accessing the 'text' attribute of a variable)
            send_message(update,message = response,format = True,parse_mode ="MarkdownV2") 
            logger.info(f"Prompt({chat_id}): {prompt}\n\n\nResponse: \n{response}")



        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                update.message.reply_text(f"Sᴏʀʀʏ, I ᴇɴᴄᴏᴜɴᴛᴇʀᴇᴅ ᴀɴ ᴇʀʀᴏʀ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ.\n ᴇʀʀᴏʀ:{e}")
            except Exception:  # If the original message couldn't be edited
                logger.error("Error cant send the message")


def send_message(update: Update,message: str,format = True,parse_mode = "HTML") -> None:
    try:

        def send_wrap(message_ :str):
            chunks = textwrap.wrap(message_, width=3500, break_long_words=False, replace_whitespace=False)
            for chunk in chunks:
                update.message.reply_text(chunk, parse_mode= parse_mode)



        if format:
            try:
                html_message = escape.escape(message)
                send_wrap(html_message)
                
            except Exception as e:
                logger.warning(f"cant parse the response error:{e}")
        else:
            logger.warning("sending unformated message")
            send_wrap(str(message))

        
                
    except Exception as e:
        
        update.message.reply_text(f"ᴡᴏᴏᴘs! ᴀɴ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ sᴇɴᴅɪɴɢ ᴛʜᴇ ᴍᴇssᴀɢᴇ: {e}", parse_mode='HTML')
        logger.error(f"An error occurred while sending the message:{e}")



def INFO(update: Update, context: CallbackContext) -> None:
  """Send a well-formatted info message """
  if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
  if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
  logger.info(f"INFO command asked by :{update.message.from_user.username}")
  update.message.reply_text(DB.info(update.message.chat_id), parse_mode='HTML', disable_web_page_preview=True)
  command_logger.log_command(update.effective_user.id,'/info')
  

def GB_REFRESH(update: Update, context: CallbackContext) -> None:
  """REFRESH ALL USERS FROM CLOUD"""
  if not _is_admin_Auth(update.message.chat_id):  
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs .", parse_mode='HTML',reply_markup=Admin_error)
        return 
  users_id = DB.get_usernames()
  if users_id:
    update.message.reply_text("Refreshing....", parse_mode='HTML')
    for chat_id in users_id:
        userData = DB.user_exists(chat_id)
        if userData:
                instruction = userData['system_instruction']
    
                if instruction =='default':
                    instruction = system_instruction            
                
                model_temp = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=safety_settings,
                    generation_config=generation_config,
                    system_instruction=instruction
                )
                history=jsonpickle.decode(userData['chat_session'])   # decode history and then store
                chat_histories[chat_id] = model_temp.start_chat(history=history )
                logger.info(f"Chat id:{chat_id} Refreshed!")
        else:
          update.message.reply_text(f"Some things is very weird with chatId:({chat_id}) the chat id existed on cloud but function did not get the id! ", parse_mode='HTML')
    update.message.reply_text(f"<b> SUCCESSFULLY REFRESHED ALL THE DATA CHATID: <code>{users_id}</code></b>", parse_mode='HTML')
      
  else:
    update.message.reply_text("Cloud data is blank", parse_mode='HTML')
  


def REFRESH(update: Update, context: CallbackContext) -> None:
    """retrive data from cloud and updates current data"""
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
    command_logger.log_command(update.effective_user.id,'/refresh')
    logger.info(f"REFRESH command asked by :{update.message.from_user.username}")
    args = context.args
    if args:
        try:
            chatID = int(args[0])
        except ValueError:
            update.message.reply_text("Iɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀ ID.", parse_mode='HTML')
            return
    else: 
        chatID = update.message.chat_id
   
    try:
        UserCloudeData = DB.user_exists(chatID)
        if UserCloudeData:
            UserCloudeData['system_instruction']
            instruction = UserCloudeData['system_instruction']
            if instruction =='default':
                instruction_local = system_instruction
            else:
                instruction_local = instruction


            model_temp = genai.GenerativeModel(
                        model_name="gemini-1.5-pro-latest",
                        safety_settings=safety_settings,
                        generation_config=generation_config,
                        system_instruction= instruction_local)
            chat_histories[chatID] = model_temp.start_chat(history=jsonpickle.decode(UserCloudeData['chat_session']))
            update.message.reply_text(f"<b> Sᴜᴄᴄᴇsғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ʏᴏᴜʀ ɪɴғᴏ({chatID}) ғʀᴏᴍ ᴄʟᴏᴜᴅ </b> \n ⚙Pʀᴏᴍᴘᴛ: <i>{instruction}</i>\n\n ᴄʜᴀᴛ Hɪsᴛᴏʀʏ ᴀʟsᴏ ᴜᴘᴅᴀᴛᴇᴅ!", parse_mode='HTML')
        else:
            update.message.reply_text(f"error 404! userID({chatID}) not found in cloud!")

    except Exception as e:
        update.message.reply_text(f"An error occurred while clearing the chat history: {e}")
        logger.error(f"An error occurred while clearing the chat history: {e}")


def clear_history(update: Update, context: CallbackContext) -> None:
    """Clear the chat history for the current chat."""
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    args = context.args
    if args:
          if update.message.chat_id == ADMIN_CHAT_ID:
              # If argument is provided, check if it's a valid chat ID
              try:
                  chat_id = int(args[0])
                  chat_id = args[0] # so it remains str 
              except ValueError:
                  update.message.reply_text("Iɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀ ID.", parse_mode='HTML')
                  return
          else:
            update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs .", parse_mode='HTML',reply_markup=Admin_error)
            
    else: 
        chat_id = update.message.chat_id

    try:
        if chat_id in chat_histories:
                conformation = [
                        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
                        [InlineKeyboardButton("🤨Are you confirm ?", callback_data="Clear_history_confirmation")],
                            ]   
                conformation = InlineKeyboardMarkup(conformation)

                update.message.reply_text("This action cannot be reversed or undone. It will delete the entire conversation between you and the recipient. Please note that while the message from Telegram won't be deleted, all other messages exchanged will be permanently removed.",reply_markup=conformation)
        else:
            update.message.reply_text(f"error 404! chatID:{chat_id} not found in local data\n\n try refreshing")
        
    except Exception as e:
        update.message.reply_text(f"An error occurred while clearing the chat history: {e}")
        logger.error(f"An error occurred while clearing the chat history: {e}")


def history(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
    command_logger.log_command(update.effective_user.id,'/history')
    args = context.args
    chat_id = update.message.chat_id

    try:
        if args:
            # If argument is provided, check if it's a valid chat ID
            try:
                arg_chat_id = int(args[0])
            except ValueError:
                update.message.reply_text("Iɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀ ID.", parse_mode='HTML')
                return
            try:
                if arg_chat_id in chat_histories:
                    # If provided chat ID is in active sessions, retrieve its history
                    history_text = f"Chat historyfor chat ID {arg_chat_id}:\n{format_chat_history(chat_histories[arg_chat_id].history)}"
                    send_message(update,message = history_text,format = True,parse_mode ="MarkdownV2") 
                else:
                    update.message.reply_text("Error 404: Chat ID not found.", parse_mode='HTML')
            except Exception as e:
                update.message.reply_text(f"An error occurred while retrieving the chat history of  {chat_id}: {e}", parse_mode='HTML')
                logger.error(f"An error occurred while retrieving the chat history: {e}")
      

        else:
            # If no argument is provided, retrieve history for the current session chat
            if chat_id in chat_histories:
                history_text = f"Chat history:\n{format_chat_history(chat_histories[chat_id].history)}"
                send_message(update,message = history_text,format = True,parse_mode ="MarkdownV2")
            else:
                update.message.reply_text("There is no chat history.")
    except Exception as e:
        update.message.reply_text(f"An error occurred while retrieving the chat history: {e}", parse_mode='HTML')
        logger.error(f"An error occurred while retrieving the chat history: {e}")
      
def format_chat_history(chat_history):
    formatted_history = ""
    for message in chat_history:
        formatted_history += f'*{message.role}*: *{message.parts[0].text}_\n'
    return formatted_history


def process_image(update: Update, context: CallbackContext) -> None:
    if not update.message.photo:
        return  # No message to handle
      
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    
    message = update.message
    chat_type = message.chat.type
    caption = message.caption.lower() if message.caption else ""  # Convert the caption to lowercase for case-insensitive comparison
    chat_id = update.message.chat_id

    if chat_type != 'private' and not caption.startswith(("hey ares", "hi ares", "ares", "yo ares", "hello ares", "what's up ares")):
      return
        


    
    chat_seesion = get_chat_history(chat_id)
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)


    def handle_image():
        try:
            if update.message.photo:
                 

                file_id = update.message.photo[-1].file_id
                file = context.bot.get_file(file_id)
                file_path = file.download()
                img = PIL.Image.open(file_path)



                try:  # Error handling for image processing
                    response = chat_seesion.send_message([caption, img])
                except genai.GenAiException as e:
                    logger.error(f"Gemini Error (Image Processing): {e}")
                    update.message.reply_text("Sorry, I had trouble processing the image.")
                    return

                if hasattr(response, "text"):
                  
                    send_message(update,message = response.text,format = True,parse_mode ="MarkdownV2") 
                    DB.chat_history_add(chat_id,get_chat_history(chat_id).history)
                else:
                  update.message.reply_text(
                      f"<b>My apologies</b>, I've reached my <i>usage limit</i> for the moment. ⏳ Please try again in a few minutes. \n\n<i>Response :</i> {response}",
                      parse_mode='HTML'
                  )
                  logger.error(f"quato error!\n\nreponse:{response}")

                os.remove(file_path)
        except (PIL.UnidentifiedImageError, FileNotFoundError) as e:
            logger.error(f"Image Error: {e}")
            update.message.reply_text("Sorry, there was an issue with the image you sent.")
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            update.message.reply_text("Sorry, something went wrong. Please try again later.")

    threading.Thread(target=handle_image).start()

def Token(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    args = context.args
    chat_id = update.message.chat_id

    if args:
        # If argument is provided, check if it's a valid chat ID
        try:
            arg_chat_id = int(args[0])
        except ValueError:
            update.message.reply_text("Iɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ID. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀ ID.")
            return

        if arg_chat_id in chat_histories:
            # If provided chat ID is in active sessions, retrieve its token count
            chat_session = chat_histories[arg_chat_id]
            if chat_session:
              update.message.reply_text(f'Tᴏᴛᴀʟ 🆔ᴛᴏᴋᴇɴs ᴜsᴇᴅ ғᴏʀ ᴄʜᴀᴛID {arg_chat_id}: {model.count_tokens(chat_session.history)}', parse_mode='HTML')
            else:
              update.message.reply_text(f"Tᴏᴛᴀʟ 🆔ᴛᴏᴋᴇɴs ᴜsᴇᴅ ғᴏʀ ᴄʜᴀᴛID {arg_chat_id}: 00", parse_mode='HTML')
            
        else:
            update.message.reply_text("Eʀʀᴏʀ⚠️ 404: CʜᴀᴛID ɴᴏᴛ ғᴏᴜɴᴅ.",parse_mode='html')
    else:
        # If no argument is provided, retrieve token count for the current session chat
        chat_session = get_chat_history(chat_id)
        if chat_session:
            update.message.reply_text(f'Tᴏᴛᴀʟ ᴛᴏᴋᴇɴs ᴜsᴇᴅ ɪɴ ᴄᴜʀʀᴇɴᴛ sᴇssɪᴏɴ: {model.count_tokens(chat_session.history)}', parse_mode='HTML')
        else:
            update.message.reply_text(f"Tᴏᴛᴀʟ 🆔ᴛᴏᴋᴇɴs ᴜsᴇᴅ ғᴏʀ ᴄʜᴀᴛID {chat_id}(yourself): 00", parse_mode='HTML')

def session_command(update: Update, context: CallbackContext) -> None:
    """Reports the total number of open chat sessions after password check."""

    if not _is_admin_Auth(update.message.chat_id):  
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs .", parse_mode='HTML',reply_markup=Admin_error)
        return 
            

    total_sessions = len(chat_histories)
    if total_sessions == 0:
        update.message.reply_text("Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄʜᴀᴛ sᴇssɪᴏɴs.",parse_mode='html')
    else:
        session_message = f"Tʜᴇʀᴇ ᴀʀᴇ ᴄᴜʀʀᴇɴᴛʟʏ <b>{total_sessions}</b> ᴀᴄᴛɪᴠᴇ ᴄʜᴀᴛ sᴇssɪᴏɴs."
        update.message.reply_text(session_message, parse_mode='HTML')

def session_info_command(update: Update, context: CallbackContext) -> None:
    """Reports the list of chat IDs for active chat sessions after password check."""
    if not _is_admin_Auth(update.message.chat_id):  
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs .", parse_mode='HTML',reply_markup=Admin_error)
        return 

    active_chat_ids = list(chat_histories.keys())  # Get the list of chat IDs for active chat sessions
    if not active_chat_ids:
        update.message.reply_text("There are no active chat sessions.", parse_mode='HTML')
    else:
        session_message = f"The active chat sessions have the following chat IDs: <code>{' '.join(str(chat_id) for chat_id in active_chat_ids)}</code>"
        update.message.reply_text(session_message, parse_mode='HTML')

def media_handler(update: Update, context: CallbackContext) -> None:
        if DB.is_user_blocked(str(update.message.from_user.id)):
            logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
            return
        message = update.message
        if message.video:
            media = message.video

        elif message.audio:
            media = message.audio

        elif message.voice:
            media = message.voice


        file_size = media.file_size  # Size of the audio file in bytes
        file_size_mb = round(file_size / (1024 * 1024), 2)  # Convert bytes to MB, round to 2 decimal places


        # Check if the file size is within the limit (5 MB)
        if file_size_mb <= 5:
            try:
                # Download and process the video file in a separate thread
                threading.Thread(target=download_and_process_video, args=(update, context, media)).start()
            except Exception as e:
                # Handle errors during downloading
                update.message.reply_text("Aɴ 🚫ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇ ᴍᴇᴅɪᴀ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
        else:
            # Inform the user that the video size exceeds the limit
            update.message.reply_text(f"Tʜᴇ ᴍᴇᴅɪᴀ sɪᴢᴇ ({file_size_mb} MB) ᴇxᴄᴇᴇᴅs ᴛʜᴇ ʟɪᴍɪᴛ ᴏғ 5 MB. Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ sᴍᴀʟʟᴇʀ ᴍᴇᴅɪᴀ.")


def download_and_process_video(update: Update, context: CallbackContext, media) -> None:
    try:
        # Download the video file
        chat_id = update.message.chat_id
        if hasattr(update.message, "caption"):
            user_message = update.message.caption if update.message.caption else ""
        else:
            user_message =""


        file = context.bot.get_file(media.file_id)


        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VIDEO)
        file_path = file.download()
        logger.debug(f"Downloaded file to {file_path}")
        # Upload the video file to Gemini

        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        media_file = genai.upload_file(path=file_path)
        logger.debug(f"Uploaded file to Gemini: {media_file}")

        # Wait for Gemini to finish processing the video
        while media_file.state.name == "PROCESSING":
            time.sleep(10)
            media_file = genai.get_file(media_file.name)

        # Check if Gemini failed to process the video
        if media_file.state.name == "FAILED":
            raise ValueError("Gemini failed to process the media_file.")

        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)



        # Generate content using Gemini
        chat_session = get_chat_history(chat_id)
        logger.info(f"genrating response by Gemini on media... media {media_file}")
        response = chat_session.send_message([media_file , user_message])

        # Check and handle the response from Gemini
        if hasattr(response, "text"):
            send_message(update,message = response.text,format = True,parse_mode ="MarkdownV2") 
        else:
            update.message.reply_text(
                    f"<b>𝑀𝑦 𝑎𝑝𝑜𝑙𝑜𝑔𝑖𝑒𝑠</b>, I've reached my <i>usage limit</i> for the moment. ⏳ Please try again in a few minutes. \n\n<i>Response :</i> {response}",
                    parse_mode='HTML'
                )


    except Exception as e:
        # Handle errors during the process
        update.message.reply_text(f"Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {e}")

    finally:
        try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    update.message.reply_text(f"Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴄʟᴇᴀɴɪɴɢ ᴜᴘ:ғɪʟᴇ_ᴘᴀᴛʜ {file_path} ᴅɪᴅ ɴᴏᴛ ᴇxɪsᴛᴇᴅ ")

        except Exception as e:
            # Handle errors during cleanup
            update.message.reply_text(f"An error occurred while cleaning up: {e}")

def extract_chat_info(update: Update, context: CallbackContext) -> None:
  """Extracts and displays information about chats.

  Args:
    update: Update object from the Telegram Bot API.
    context: CallbackContext object from the Telegram Bot SDK.
  """
  if not _is_admin_Auth(update.message.chat_id):  
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs .", parse_mode='HTML',reply_markup=Admin_error)
        return 

  if len(context.args) > 0:
    # Loop through all provided chat IDs
    for chat_id_str in context.args:
      try:
        chat_id = int(chat_id_str)

        # Get chat information and format response
        try:
          chat = context.bot.get_chat(chat_id)
          chat_data = {
              "Cʜᴀᴛ ID": chat.id,
              "Chat Type": chat.type,
              "Tɪᴛʟᴇ": chat.title,
              "Usᴇʀɴᴀᴍᴇ": chat.username,
              "Fɪʀsᴛ Nᴀᴍᴇ": chat.first_name,
              "Lᴀsᴛ Nᴀᴍᴇ": chat.last_name,
              "Dᴇsᴄʀɪᴘᴛɪᴏɴ": chat.description,
              "Iɴᴠɪᴛᴇ Lɪɴᴋ": chat.invite_link,
              "Pɪɴɴᴇᴅ Mᴇssᴀɢᴇ": chat.pinned_message.text if chat.pinned_message else None,
          }
          filtered_data = {k: v for k, v in chat_data.items() if v is not None}
          info_text = "\n".join([f"{key}: {value}" for key, value in filtered_data.items()])

          # Send response for each chat
          update.message.reply_text(f"Cʜᴀᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ:\n{info_text}", parse_mode='HTML')
        except telegram.error.Unauthorized:
          update.message.reply_text(f"Cʜᴀᴛ ID {chat_id}: I ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ᴄʜᴀᴛ.")
        except telegram.error.BadRequest as e:
          update.message.reply_text(f"Cʜᴀᴛ ID {chat_id}: Bᴀᴅ ʀᴇᴏ̨ᴜᴇsᴛ. Eʀʀᴏʀ: {e.message}")
        except Exception as e:
          update.message.reply_text(f"Cʜᴀᴛ ID {chat_id}: Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇᴛ ᴄʜᴀᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ. Eʀʀᴏʀ: {e}")
      except ValueError:
        update.message.reply_text(f"Iɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ID: {chat_id_str}. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ɴᴜᴍᴇʀɪᴄ ᴄʜᴀᴛ IDs.")

  else:
    update.message.reply_text("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴄʜᴀᴛ IDs. Usᴀɢᴇ: /ᴄʜᴀᴛɪɴғᴏ <ᴄʜᴀᴛ_ɪᴅ1> <ᴄʜᴀᴛ_ɪᴅ2> ...")


def download_images(query, limit=4, output_dir="images"):
    """Downloads images from Bing Image Search and handles download errors.

    Args:
        query (str): The search query for images.
        limit (int, optional): The maximum number of images to download. Defaults to 4.
        output_dir (str, optional): The directory to save downloaded images. Defaults to "images".

    Returns:
        list[str]: A list of file paths to downloaded images (or an empty list if none).
    """

    downloaded_images = []

    try:
        path = None
        downloader.download(query, limit=limit, output_dir=output_dir, adult_filter_off=False, force_replace=False, timeout=60)
        path = f"images/{query}"
        downloaded_images = [os.path.join(path, f) for f in os.listdir(path) if f.endswith((".jpg", ".jpeg", ".png", ".gif"))]
    except Exception as e:
        logger.error(f"Error downloading images: {e} path:{path}")

    return downloaded_images


def image_command_handler(update: Update, context: CallbackContext) -> None:
    """Handles the `/image` command to download and send images."""
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.")
        return
    command_logger.log_command(update.effective_user.id,'/image')
    chat_id = update.effective_chat.id
    query_ = " ".join(context.args)
    logger.info(f"chatId:{chat_id} used /image command with this query:{query_}")

    if not query_:
        context.bot.send_message(chat_id, text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ sᴇᴀʀᴄʜ ᴏ̨ᴜᴇʀʏ ғᴏʀ ɪᴍᴀɢᴇs.",reply_markup=Invalid_arg)
        return
    context.bot.send_message(chat_id, text="Sᴇᴀʀᴄʜɪɴɢ...")
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.FIND_LOCATION)
    keyboard = [[InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],]   
    keyboard  = InlineKeyboardMarkup(keyboard)


    def image_pros(update,context,query_):
        start_time = time.time()
        downloaded_images = download_images(query_)
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)

        if downloaded_images:
            for image_path in downloaded_images:
                with open(image_path, 'rb') as image_file:
                    context.bot.send_photo(chat_id, photo=image_file)
                    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
                # Delete the downloaded image after sending
                os.remove(image_path)
            end_time = time.time()
            elapsed_time = end_time - start_time
            text = f"""
❔Qᴜᴇʀʏ: {query_}\n
✨Tᴏᴛᴀʟ ɪᴍᴀɢᴇ : {len(downloaded_images)}\n
🥀Rᴇᴏ̨ᴜᴇsᴛᴇᴅ ʙʏ: {update.effective_user.first_name} {update.effective_user.last_name}\n
⏳Tɪᴍᴇ ᴛᴀᴋᴇɴ: {round(elapsed_time, 2)} Sec\n
🗄Pᴏᴡᴇʀᴇᴅ ʙʏ: 𝑀𝑖𝑐𝑟𝑜𝑠𝑜𝑓𝑡 𝐵𝑖𝑛𝑔
            """
            context.bot.send_message(chat_id, text=text, reply_markup=keyboard)
            shutil.rmtree(f"images/{query_}")
        else:
            context.bot.send_message(chat_id, text="No images found for your search Query.",reply_markup=keyboard)
    
    
    threading.Thread(target=image_pros, args=(update,context,query_)).start()



    
def wiki(update: Update, context: CallbackContext):
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
    command_logger.log_command(update.effective_user.id,'/wiki')
    chat_id = update.effective_chat.id
    search = " ".join(context.args)
    if search:
        try:
            res = wikipedia.summary(search)
        except DisambiguationError as e:
            update.message.reply_text(
                "Dɪsᴀᴍʙɪɢᴜᴀᴛᴇᴅ ᴘᴀɢᴇs ғᴏᴜɴᴅ! Aᴅᴊᴜsᴛ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ ᴀᴄᴄᴏʀᴅɪɴɢʟʏ.\n<i>{}</i>".format(e),
                parse_mode=ParseMode.HTML,
                reply_markup=DisambiguationError
            )
        except PageError as e:
            update.message.reply_text(
                "<code>{}</code>".format(e), parse_mode=ParseMode.HTML
            )
        if res:
            result = f"<b>{search}</b>\n\n"
            result += f"<i>{res}</i>\n"
            result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
            if len(result) > 4000:
                  with open("result.txt", "w") as f:
                      f.write(f"{result}\n\nUwU OwO OmO UmU")
                  with open("result.txt", "rb") as f:
                      context.bot.send_document(
                          document=f,
                          filename=f.name,
                          reply_to_message_id=update.message.message_id,
                          chat_id=chat_id,
                          parse_mode=ParseMode.HTML,
                      )
            else:
                update.message.reply_text(
                    result, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                )
        else:
          update.message.reply_text("Eʀʀᴏʀ 500! sᴇʀᴠᴇʀ ᴇʀʀᴏʀ!", parse_mode=ParseMode.HTML)
        
    else:
       update.message.reply_text("Eʀʀᴏʀ 400! ᴘʟs ᴘʀᴏᴠɪᴅᴇ ᴀ ᴏ̨ᴜᴇʀʏ ᴛᴏ sᴇᴀʀᴄʜ ɪɴ ᴡɪᴋɪ!", parse_mode=ParseMode.HTML,reply_markup=Invalid_arg)

def create_image(prompt: str) -> bytes:
        """Generates an AI-generated image based on the provided prompt.

        Args:
            prompt (str): The input prompt for generating the image.

        Returns:
            bytes: The generated image in bytes format.
            
        Example usage:
      
        >>> generated_image= ai_image("boy image")
        >>> print(generated_image)
        """
        url = "https://ai-api.magicstudio.com/api/ai-art-generator"

        form_data = {
            'prompt': prompt,
            'output_format': 'bytes',
            'request_timestamp': str(int(time.time())),
            'user_is_subscribed': 'false',
        }

        response = requests.post(url, data=form_data)
        if response.status_code == 200:
            try:
                if response.content:
                    return response.content
                else:
                    raise Exception("Failed to get image from the server.")
            except Exception as e:
                raise e
        else:
            raise Exception("Error:", response.status_code)
          
def imagine(update: Update, context: CallbackContext):
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
      
    command_logger.log_command(update.effective_user.id,'/imagine')
    chat_id = update.effective_chat.id
    search = " ".join(context.args)
    if not search:
      update.message.reply_text(f"Eʀʀᴏʀ 404 ɴᴏ ᴘʀᴏᴍᴛ ᴘʀᴏᴠɪᴅᴇᴅ ᴘʟs ᴘʀᴏᴠɪᴅᴇ ᴘʀᴏᴍᴘᴛ",reply_markup=Invalid_arg)
      return 
      
    start_time = time.time()
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.FIND_LOCATION)
    try:
        logger.info(f"requesting for image for chatId:{chat_id}  prompt:{search}")
        x = create_image(search)
        logger.info(f"image created successfully")
        end_time = time.time()
        elapsed_time = end_time - start_time
      
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
        
        try:
          # Attempt to open the file for writing in binary mode
          with open("image.jpg", 'wb') as f:
            # Write content to the file
            f.write(x)
          logger.info("Content written to 'image.jpg' successfully.")
        except Exception as e:
           # Handle any exceptions that may occur
           logger.error(f"Error writing to 'image.jpg': {e}")

        # Now proceed with processing the file
          
        caption = f"""
✨ᴘʀᴏᴍᴘᴛ: {search}\n
🥀ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ: {update.effective_user.first_name} {update.effective_user.last_name}
⏳ᴛɪᴍᴇ ᴛᴀᴋᴇɴ:{round(elapsed_time,2)} Sec
- ɢᴇɴʀᴀᴛᴇᴅ ʙʏ @ᴀʀᴇs_ᴄʜᴀᴛʙᴏᴛ
"""
        keyboard = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
    ]   
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_photo(photo=open("image.jpg", 'rb'), caption=caption, quote=True,reply_markup=reply_markup,parse_mode='HTML')
    except Exception as e:
        update.message.reply_text(f"Eʀʀᴏʀ ᴡʜɪʟᴇ ɢᴇɴᴇʀᴀᴛɪɴɢ ɪᴍᴀɢᴇ ᴇʀʀᴏʀ: {e}")
        logger.error(f"error while generating image error : {e}")

async def async_google_search(search: str):
    search_args = (search, 5)
    gsearch = GoogleSearch()
    gresults = await gsearch.async_search(*search_args)
    return gresults

def Google_search(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
    command_logger.log_command(update.effective_user.id,'/google')
    chat_id = update.effective_chat.id
    search = " ".join(context.args)
    if not search:
        update.message.reply_text(f"Eʀʀᴏʀ 404 ɴᴏ ᴏ̨ᴜᴇʀʏ ᴘʀᴏᴠɪᴅᴇᴅ ᴘʟs ᴘʀᴏᴠɪᴅᴇ ᴀ sᴇᴀʀᴄʜ ᴏ̨ᴜᴇʀʏ",reply_markup=Invalid_arg)
        return 

    # Run the async function in the event loop
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    try:
          gresults = asyncio.run(async_google_search(search))
          
          msg = ""
          for i in range(len(gresults["links"])):
              try:
                  title = gresults["titles"][i]
                  link = gresults["links"][i]
                  desc = gresults["descriptions"][i]
                  msg += f"❍[{title}]({link})\n**{desc}**\n\n"
              except IndexError:
                  break
          
          update.message.reply_text(
              escape.escape("**Search Query:**\n`" + search + "`\n\n**Results:**\n" + msg), link_preview=False,parse_mode='MarkdownV2'
          )
    except Exception as e:
        # Handle potential errors sending the result (e.g., network issues)
         update.message.reply_text(f"Sᴏʀʀʏ ᴄᴀɴ'ᴛ sᴇɴᴅ ᴛʜᴇ ʀᴇsᴜʟᴛ ᴇʀʀᴏʀ:{e}")
         logger.error(f"Failed to send google search result on query:{search} error : {e}")
  
def bug(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
      
    chat_id = update.effective_chat.id
    bugs = " ".join(context.args)
    if not bugs:
      update.message.reply_text(f"Tʏᴘᴇ ᴛʜᴇ ʙᴜɢ ᴏʀ ᴇʀʀᴏʀ ʏᴏᴜ ᴀʀᴇ ғᴀᴄɪɴɢ.",reply_markup=Invalid_arg)
      return 
    mention = (
        "[" + update.message.from_user.first_name+ "](tg://user?id=" + str(update.message.from_user.id) + ")"
    )
    datetimes_fmt = "%d-%m-%Y"
    datetimes = datetime.datetime.utcnow().strftime(datetimes_fmt)
    bug_report = f"""
**#ʙᴜɢ : ** **tg://user?id={DEVELOPER_CHAT_ID}**

**ʀᴇᴩᴏʀᴛᴇᴅ ʙʏ : ** **{mention}**
**ᴜsᴇʀ ɪᴅ : ** **{update.message.from_user.id}**
**ᴄʜᴀᴛ : ** **{chat_id}**

**ʙᴜɢ : ** **{bugs}**

**ᴇᴠᴇɴᴛ sᴛᴀᴍᴩ : ** **{datetimes}**"""
    context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID, text=escape.escape(bug_report), parse_mode='MarkdownV2'
        )
    context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=escape.escape(bug_report), parse_mode='MarkdownV2'
        )
    update.message.reply_text(
        f"*ʙᴜɢ ʀᴇᴩᴏʀᴛ* : **{bugs}** \n\n » 🟢ʙᴜɢ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴩᴏʀᴛᴇᴅ  Jᴏɪɴ ᴛʜᴇ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ғᴏʀ ᴇxᴛʀᴀ ʜᴇʟᴘ ᴀɴᴅ ᴅɪʀᴇᴄᴛ ᴄᴏɴᴛᴀᴄᴛ ",parse_mode='MarkdownV2'
    )
    
  










def error_handler(update: Updater, context: CallbackContext) -> None:
  """Logs the error and sends a notification to the developer using context."""

  if type(context.error) == Conflict:
        logger.warning("Conflict error occurred, not sending notification.")
        return  # Exit the function without sending a notification
    
  # Get essential details from context
  logger.error("Exception while handling an update:", exc_info=context.error)
  
 
  # traceback.format_exception returns the usual python message about an exception, but as a
  # list of strings rather than a single string, so we have to join them together.
  tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
  tb_string = "".join(tb_list)
  # Build the message with some markup and additional information about what happened.
  # You might need to add some logic to deal with messages longer than the 4096 character limit.
  update_str = update.to_dict() if isinstance(update, Update) else str(update)
  message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
  try:
        context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=message, parse_mode=ParseMode.HTML
        )
  except Exception as e:
        # Handle potential errors sending the notification (e.g., network issues)
        logger.error(f"Failed to send error notification: {e}")



def gb_broadcast(update: Update, context: CallbackContext) -> None:
    """Broadcast a message to all users."""
    if not _is_admin_Auth(update.message.chat_id):
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ. Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    # Get the message to broadcast
    message_to_broadcast = ' '.join(context.args)
    if not message_to_broadcast:
        update.message.reply_text("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.", parse_mode=ParseMode.HTML)
        return

    users_id = DB.get_usernames()
    if users_id:
        update.message.reply_text("Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs...", parse_mode=ParseMode.HTML)
        for chat_id in users_id:
            try:
                context.bot.send_message(chat_id=chat_id, text=message_to_broadcast, parse_mode=ParseMode.HTML)
                logger.info(f"Message sent to chat ID {chat_id}")
            except Exception as e:
                logger.error(f"Error sending message to chat ID {chat_id}: {e}")
                if "bot was blocked by the user" in str(e):
                    logger.info(f"Skipping user {chat_id} as they have blocked the bot.")
                else:
                    update.message.reply_text(f"Error sending message to chat ID {chat_id}: {e}", parse_mode=ParseMode.HTML)
        
        update.message.reply_text("Bʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ🎉🎉.", parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("Nᴏ ᴜsᴇʀs ғᴏᴜɴᴅ ɪɴ ᴛʜᴇ ᴄʟᴏᴜᴅ ᴅᴀᴛᴀ.", parse_mode=ParseMode.HTML)


def specific_broadcast(update: Update, context: CallbackContext) -> None:
    """Broadcast a message to a specific user."""
    if not _is_admin_Auth(update.message.chat_id):
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    if len(context.args) < 2:
        update.message.reply_text("Usᴀɢᴇ: /sᴘᴇᴄɪғɪᴄ_ʙʀᴏᴀᴅᴄᴀsᴛ (ᴄʜᴀᴛ_ɪᴅ) (ᴍᴇssᴀɢᴇ)", parse_mode=ParseMode.HTML)
        return

    chat_id = context.args[0]
    message_to_broadcast = ' '.join(context.args[1:])

    try:
        context.bot.send_message(chat_id=chat_id, text=message_to_broadcast, parse_mode=ParseMode.HTML)
        update.message.reply_text(f"Mᴇssᴀɢᴇ sᴇɴᴛ ᴛᴏ ᴄʜᴀᴛID {chat_id} 🎉🎉.", parse_mode=ParseMode.HTML)
        logger.info(f"Message sent to chat ID {chat_id}.")
    except Exception as e:
        logger.error(f"Error sending message to chat ID {chat_id}: {e}")
        if "bot was blocked by the user" in str(e):
            update.message.reply_text(f"Usᴇʀ {chat_id} ʜᴀs ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ.", parse_mode=ParseMode.HTML)
            logger.info(f"User {chat_id} has blocked the bot.")
        else:
            update.message.reply_text(f"Eʀʀᴏʀ sᴇɴᴅɪɴɢ ᴍᴇssᴀɢᴇ ᴛᴏ ᴄʜᴀᴛ ID {chat_id}: {e}", parse_mode=ParseMode.HTML)

def block_user_command(update: Update, context: CallbackContext) -> None:
    """Block a user."""
    if not _is_admin_Auth(update.message.chat_id):
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    if len(context.args) != 1:
        update.message.reply_text("Usᴀɢᴇ: /ʙʟᴏᴄᴋ <ᴜsᴇʀ_ɪᴅ>", parse_mode=ParseMode.HTML)
        return

    user_id_to_block = context.args[0]
    DB.block_user(user_id_to_block)
    update.message.reply_text(f"Usᴇʀ {user_id_to_block} ʜᴀs ʙᴇᴇɴ ʙʟᴏᴄᴋᴇᴅ.", parse_mode=ParseMode.HTML)

def unblock_user_command(update: Update, context: CallbackContext) -> None:
    """Unblock a user."""
    if not _is_admin_Auth(update.message.chat_id):
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ. Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    if len(context.args) != 1:
        update.message.reply_text("Usᴀɢᴇ: /ᴜɴʙʟᴏᴄᴋ <ᴜsᴇʀ_ɪᴅ>", parse_mode=ParseMode.HTML)
        return

    user_id_to_unblock = context.args[0]
    DB.unblock_user(user_id_to_unblock)
    update.message.reply_text(f"Usᴇʀ {user_id_to_unblock} ʜᴀs ʙᴇᴇɴ ᴜɴʙʟᴏᴄᴋᴇᴅ.", parse_mode=ParseMode.HTML)

def all_blocked_users(update: Update, context: CallbackContext) -> None:
  """list of all blocked users"""
  if not _is_admin_Auth(update.message.chat_id):
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ. Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return
  blocked_users = DB.blocked_users_cache
  update.message.reply_text(f"Usᴇʀ ᴛʜᴀᴛ ᴀʀᴇ ᴜɴʙʟᴏᴄᴋᴇᴅ: {blocked_users}", parse_mode=ParseMode.HTML)


def add_admin_command(update: Update, context: CallbackContext) -> None:
    """add admin user."""
    if update.message.chat_id != OWNER_ID:
        update.message.reply_text("Access denied. Oɴʟʏ OWNER ᴄᴀɴ ᴀᴅᴅ ᴀᴅᴍɪɴs.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    if len(context.args) != 1:
        update.message.reply_text("Usᴀɢᴇ: /add_admin <ᴜsᴇʀ_ɪᴅ>", parse_mode=ParseMode.HTML)
        return

    user_id_to_add = context.args[0]
    DB.add_admin(user_id_to_add)
    update.message.reply_text(f"Usᴇʀ {user_id_to_add} ʜᴀs ʙᴇᴇɴ ᴍᴀᴅᴇ ᴀɴ ᴀᴅᴍɪɴ🎉🎉.", parse_mode=ParseMode.HTML)

def unblock_user_command(update: Update, context: CallbackContext) -> None:
    """remove admin user."""
    if update.message.chat_id != OWNER_ID:
        update.message.reply_text("Access denied. Oɴʟʏ OWNER ᴄᴀɴ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴs", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    if len(context.args) != 1:
        update.message.reply_text("Usᴀɢᴇ: /rm_admin <ᴜsᴇʀ_ɪᴅ>", parse_mode=ParseMode.HTML)
        return

    user_id_to_remove = context.args[0]
    DB.remove_admin(user_id_to_remove)
    update.message.reply_text(f"Usᴇʀ {user_id_to_remove} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ᴀs ᴀᴅᴍɪɴ😞😞.\nTʜɪs ᴀᴄᴛɪᴏɴs ᴡᴏᴜʟᴅɴ'ᴛ ʙᴀɴ ʜɪᴍ.", parse_mode=ParseMode.HTML)

def all_admin_users(update: Update, context: CallbackContext) -> None:
  """list of all admin users"""
  if update.message.chat_id != OWNER_ID:
        update.message.reply_text("Access denied. Oɴʟʏ OWNER ᴄᴀɴ sᴇᴇ ᴀᴅᴍɪɴs ʟɪsᴛ.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return
  admin_users = DB.admins_users
  update.message.reply_text(f"Aʟʟ ᴛʜᴇ ᴜsᴇʀs ᴛʜᴀᴛ ᴀʀᴇ ᴀᴅᴍɪɴ🗂: {admin_users}", parse_mode=ParseMode.HTML)



def _is_admin_Auth(id):
    if DB.is_admin(id):
        return True
    else:
        if id == OWNER_ID:
            return True 
        else:
            return False
        
# Define the /ping command handler
def ping(update: Update, context: CallbackContext) -> None:
    if not _is_admin_Auth(update.message.chat_id):
        update.message.reply_text("Aᴄᴄᴇss ᴅᴇɴɪᴇᴅ. Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴅᴏ ᴛʜɪs.", parse_mode=ParseMode.HTML,reply_markup=Admin_error)
        return

    # Get system usage statistics
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    total_memory = memory_info.total / (1024 ** 3)  # Convert bytes to GB
    available_memory = memory_info.available / (1024 ** 3)  # Convert bytes to GB
    used_memory = memory_info.used / (1024 ** 3)  # Convert bytes to GB
    memory_percent = memory_info.percent

    # Create the response message
    response = (
        "<pre>"
        "Pong!\n"
        f"CPU Usage: {cpu_usage}%\n"
        f"Total Memory: {total_memory:.2f} GB\n"
        f"Available Memory: {available_memory:.2f} GB\n"
        f"Used Memory: {used_memory:.2f} GB ({memory_percent}%)\n"
        "</pre>"
    )

    # Send the response message with HTML parsing
    update.message.reply_text(response, parse_mode=ParseMode.HTML)




# Function to handle /yt command and search YouTube
def Youtube(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    if not command_logger.check_rate_limit(update.effective_user.id):
        update.message.reply_text("Yᴏᴜ'ᴠᴇ ᴇxᴄᴇᴇᴅᴇᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ʀᴀᴛᴇ ʟɪᴍɪᴛ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ ᴏɴᴇ ᴍɪɴ.",reply_markup=command_limit_inline)
        return
    command_logger.log_command(update.effective_user.id,'/yt',5)
    search = " ".join(context.args)
    if not search:
        update.message.reply_text("Error: No search query provided.")
        return

    message = update.message.reply_text("Searching, please wait...")

    def time_to_seconds(time_str):
        """Converts a time string in HH:MM:SS format to total seconds.

        Args:
            time_str: The time string in HH:MM:SS format.

        Returns:
            The total number of seconds represented by the time string.
            Returns 0 if the input format is invalid.

        Raises:
            ValueError: If the time string format is invalid (e.g., missing colons).
        """

        try:
            # Split the time string into components and reverse the order
            time = str(time_str).split(":")
            if len(time) == 3:
                hours, minutes, seconds = time
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            elif len(time) == 2:
                minutes,seconds = time
                total_seconds = int(minutes) * 60 + int(seconds)
            else:
                logger.error("error! the hh:mm:ss fomat ha san error")
                return 0
            return total_seconds
        except Exception as e:
            # Handle invalid time string format
            logger.error(f"error while converting hh:mm:ss error:{e}")
            return 0  # Or raise a specific error message


    def search_and_prepare():
        try:
            results = YoutubeSearch(search, max_results=1).to_dict()
            result = results[0]
            video_url = f"https://youtube.com{result['url_suffix']}"
            title = result["title"][:40]
            duration = result["duration"]
            logger.info(f"userId:{update.message.from_user.id} requested /yt {search}")
            logger.info(f"Total time :{time_to_seconds(duration)}")
            if time_to_seconds(duration) > MAX_AUDIO_LIMIT:
                message.edit_text(f"⚠️ Unfortunately, the song duration ({duration}) exceeds our current limit. Try searching with different keywords to find a shorter song.",reply_markup=music_limit_error)
                return
            views = result["views"]
            channel_name = result.get("channel", "Unknown Channel")
            video_uuid = str(uuid.uuid4())
            video_urls[video_uuid] = result
            
            thumbnail = result["thumbnails"][0]
            keyboard = [
                [
                    InlineKeyboardButton("Download Audio 🎵", callback_data=f"audio:{video_uuid}"),
                    InlineKeyboardButton("Download Video 🎥", callback_data=f"video:{video_uuid}")
                ],
                 [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=thumbnail,
                caption=f"<b>Title:</b>     <i>{html.escape(title)}</i>\n"
                        f"<b>Duration:</b>  <i>{duration}</i>\n"
                        f"<b>Views:</b>     <i>{escape.beautify_views(views)}</i>\n"
                        f"<b>Channel:</b>   <i><a href='https://www.youtube.com/@{channel_name}'>{channel_name}</a></i>\n\n"
                        "<b>Select an option to download:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )

        except Exception as e:
            message.edit_text("😴 Song not found on YouTube. Try with different keywords.")
            logger.error(f"Error during YouTube search: {str(e)}")

    threading.Thread(target=search_and_prepare).start()


# Command handler for /off command
def off(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # Check if the user is authorized to shut down the bot
    if user_id == OWNER_ID:
        # Check if the correct special password is provided as an argument
        if len(context.args) > 0 and context.args[0] == SPECIAL_PASSWORD:
            update.message.reply_text(f"Bot is shutting down...\n\nSession info: {SPECIAL_PASSWORD}")
            # Perform any cleanup or final tasks here if needed
            sys.exit(0)  # Exit the script with status code 0 (success)
        else:
            update.message.reply_text("Incorrect password.")
    else:
        update.message.reply_text("You are not authorized to shut down this bot.")

def generate_password():
    return secrets.token_urlsafe(16)

def __init__(update):
        # Get the current time when the bot starts
        START_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        start_message = (
            f"<b>Bot Started</b>\n"
            f"Start Time: <code>{START_TIME}</code>\n"
            f"Your shutdown password is: <code>{SPECIAL_PASSWORD}</code>"
        )
        update.bot.send_message(chat_id=OWNER_ID, text=start_message, parse_mode=ParseMode.HTML)



def main() -> None:
    logger.info("Bot starting!")
    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Register the message handler
    message_handler = MessageHandler(Filters.text & ~Filters.command, process_message)
    dispatcher.add_handler(message_handler)

    # Register the message handler
    dispatcher.add_handler(MessageHandler(Filters.photo, process_image))
    dispatcher.add_handler(MessageHandler(Filters.voice | Filters.audio , media_handler))
    dispatcher.add_handler(MessageHandler(Filters.video, media_handler))


    # Register the help command handler
    dispatcher.add_handler(CommandHandler("help", home))
    dispatcher.add_handler(CommandHandler("start", home))
    dispatcher.add_handler(CommandHandler("bug", bug))
    dispatcher.add_handler(CommandHandler("info", INFO))
    
    dispatcher.add_handler(CommandHandler("history", history))
    dispatcher.add_handler(CommandHandler("refresh", REFRESH))
    # ADMNIN command 
    dispatcher.add_handler(CommandHandler("gb_refresh", GB_REFRESH))
    dispatcher.add_handler(CommandHandler("gb_broad_cast", gb_broadcast))   
    dispatcher.add_handler(CommandHandler("specific_broadcast", specific_broadcast))
    dispatcher.add_handler(CommandHandler("ban", block_user_command, pass_args=True))
    dispatcher.add_handler(CommandHandler("unban", unblock_user_command, pass_args=True))
    dispatcher.add_handler(CommandHandler("ban_ids", all_blocked_users))
    dispatcher.add_handler(CommandHandler("ping", ping))
    dispatcher.add_handler(CommandHandler("off", off))
    #Owner commands
    dispatcher.add_handler(CommandHandler("add_admin", add_admin_command, pass_args=True))
    dispatcher.add_handler(CommandHandler("rm_admin", unblock_user_command, pass_args=True))
    dispatcher.add_handler(CommandHandler("admins", all_blocked_users))
    
    dispatcher.add_handler(CommandHandler("image", image_command_handler))
    dispatcher.add_handler(CommandHandler("wiki", wiki))
    dispatcher.add_handler(CommandHandler("imagine", imagine))
    dispatcher.add_handler(CommandHandler("google", Google_search))
    dispatcher.add_handler(CommandHandler(["yt", "youtube","song","music","audio"], Youtube))
    dispatcher.add_handler(CommandHandler("session", session_command))
    dispatcher.add_handler(CommandHandler("session_info", session_info_command))
    dispatcher.add_handler(CommandHandler("cid_info", extract_chat_info))

    
                                    

    # Register the admin/info command handler
    dispatcher.add_handler(CommandHandler("token", Token))


    # Register the ChangePrompt command handler
    dispatcher.add_handler(CommandHandler("clear_history", clear_history, pass_args=True))
    dispatcher.add_handler(CommandHandler("ChangePrompt", change_prompt, pass_args=True))

    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(CallbackQueryHandler(button_click))



    logger.warning("Bot started!")


    # Start the Bot
    updater.start_polling()
    __init__(updater) # send a special password to the owner 

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    DB = FireBaseDB()
    command_logger =rate_limit.CommandLogger()  # safety limit 
    # Generate a unique password when the bot starts
    SPECIAL_PASSWORD = generate_password()
    keep_alive()
    main()
