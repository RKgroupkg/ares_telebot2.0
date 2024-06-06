import logging,telegram
from telegram import Update,ChatAction,InlineKeyboardMarkup, InlineKeyboardButton,ParseMode # version = 12.8
from telegram.error import Conflict
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext,CommandHandler,CallbackQueryHandler
import google.generativeai as genai
import threading
import textwrap
import PIL.Image
import os,json
import format_html
import time,datetime
import config
import html
import psutil
import traceback
import asyncio
from search_engine_parser import GoogleSearch
import wikipedia,requests
from wikipedia.exceptions import DisambiguationError, PageError

from keep_alive import keep_alive

from bing_image_downloader import downloader 
import shutil

import firebase_admin 
from firebase_admin import db, credentials
import jsonpickle # type: ignore

cred = credentials.Certificate(json.loads(os.environ.get('fire_base')))
app = firebase_admin.initialize_app(cred, {"databaseURL": "https://ares-rkbot-default-rtdb.asia-southeast1.firebasedatabase.app/"})

PASSWORD = os.environ.get('password')

chat_histories ={}
DEVELOPER_CHAT_ID = 6258187891
ADMIN_CHAT_ID = -1002182025326
SUPPORT_CHAT_ID = -1002201688413

api_key = os.environ.get('gemnie_api')
genai.configure(api_key=api_key)
telegram_bot_token = os.environ.get('telegram_api')


logger = logging.getLogger()
handler = logging.StreamHandler()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-latest",
  safety_settings=config.safety_settings,
  generation_config=config.generation_config,
  system_instruction=config.system_instruction,)

class FireBaseDB:
    def __init__(self):
        self.db = db.reference("/users_sessions")
        self.INFO_DB = db.reference("/Blocked_user")
        self.blocked_users_cache = set()
        self._load_blocked_users()
    
    def user_exists(self,userId):

        try:
           return db.reference(f"/users_sessions/{userId}").get()
        except Exception as e:
            raise ValueError(f"error while checking for user :{e}")

    def create_user(self,userId):
        user_data = self.user_exists(userId)
        if user_data:
            raise ValueError(f"User with ID '{userId}' already exists!")
        
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format


        conversation = {
            "chat_session":{},
            "date" : formatted_time,
            "system_instruction" : "default"
        }
        db.reference(f"/users_sessions").update({f"{userId}":conversation })
        
        
    def extract_history(self,userId):
       
        try:
            user_data = self.user_exists(userId)
            if not user_data:
                raise ValueError(f"User with ID '{userId}' not found")

            
            return jsonpickle.decode(user_data.get("chat_session"))

        except (KeyError, AttributeError) as e:
            raise ValueError(f"Error accessing user data or conversation: {e}")

    def chat_history_add(self,userId, history=[]):
        """Adds the provided history to the chat session for the user.

        Args:
            history (list, optional): The list of messages to add to the conversation history. Defaults to [].
            update_all (bool, optional): If True, replaces the entire chat session history. Defaults to true (appends).

        Raises:
            ValueError: If user ID is not found in the database.
        """

        try:
            db.reference(f"/users_sessions/{userId}").update({f"chat_session":jsonpickle.encode(history, True)})

        except (KeyError, AttributeError) as e:
            raise ValueError(f"Error accessing user data or chat session: {e}")
    
    def extract_instruction(self,userId):
        user_data =  self.user_exists(userId)
        if not user_data:
            raise ValueError(f"User with ID '{userId}' not found")

        return user_data["system_instruction"]

    def Update_instruction(self,userId,new_instruction = "default"):
        db.reference(f"/users_sessions/{userId}").update({f"system_instruction":new_instruction })



    def info(self,userId):
            user_data =  self.user_exists(userId)
            if not user_data:
                raise ValueError(f"User with ID '{userId}' not found")
            
            message = f''' 

userID :          {userId}
creation date :   {user_data["date"]}
Prompt :          {user_data["system_instruction"]}

    '''
            return message
    def get_usernames(self):
        """Retrieve all usernames from the users_sessions node in Firebase Realtime Database."""
        try:
            users_sessions = self.db.get()
            if users_sessions:
                usernames = list(users_sessions.keys())
                logger.info(f"Usernames retrieved successfully: {usernames}")
                return usernames
            else:
                logger.info("No user sessions found.")
                return []
        except Exception as e:
            logger.error(f"Error retrieving usernames: {e}")
            return []

    def _load_blocked_users(self):
        """Load blocked users from the cloud database into the local cache."""
        try:
            blocked_users = self.INFO_DB.get()
            if blocked_users:
                self.blocked_users_cache = set(blocked_users.keys())
            logger.info("Blocked users loaded into cache.")
        except Exception as e:
            logger.error(f"Error loading blocked users: {e}")

    def block_user(self, userId):
        """Block a user by adding to both the cloud database and local cache."""
        try:
            self.INFO_DB.update({userId: True})
            self.blocked_users_cache.add(userId)
            logger.info(f"User {userId} has been blocked.")
        except Exception as e:
            logger.error(f"Error blocking user {userId}: {e}")

    def unblock_user(self, userId):
        """Unblock a user by removing from both the cloud database and local cache."""
        try:
            self.INFO_DB.child(userId).delete()
            self.blocked_users_cache.discard(userId)
            logger.info(f"User {userId} has been unblocked.")
        except Exception as e:
            logger.error(f"Error unblocking user {userId}: {e}")

    def is_user_blocked(self, userId):
        """Check if a user is blocked by looking into the local cache."""
        return userId in self.blocked_users_cache

    
     
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
                instruction = config.system_instruction            
            
            model_temp = genai.GenerativeModel(
                model_name="gemini-1.5-pro-latest",
                safety_settings=config.safety_settings,
                generation_config=config.generation_config,
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
            response= f"Error occured while genrating response: {e}"
        
        if not hasattr(response, "text"):
          response = f"*My apologies*, I've reached my _usage limit_ for the moment. ⏳ Please try again in a few minutes. \n\n Response : {response}"
        
        else:
          response = response.text
            
        def update():
            try:
                with lock:  # Use a thread-safe lock for Firebase access
                    DB.chat_history_add(chat_id, chat_history.history)
                return response if input_text else "error"
            except Exception as e:
                logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
                return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}"

        # Create a lock to ensure only one thread updates Firebase at a time
        lock = threading.Lock()

        # Create a thread to update Firebase asynchronously in the background
        thread = threading.Thread(target=update)
        thread.start()
        return response

    except Exception as e:
            logger.error(f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}")
            return f"Sorry, I couldn't generate a response at the moment. Please try again later.\n\nError: {e}"





def change_prompt(update: Update, context: CallbackContext) -> None:
    """Change the prompt for generating responses."""
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    chat_id = update.message.chat_id
    new_promt = " ".join(context.args)
    logger.info(f"chatId({chat_id}) changed its Promt to :'{new_promt}'")
    if new_promt :
        print(f"arg in lower case :{context.args[0].lower()} is it command? :{context.args[0].lower() == 'd'} ")
        if  context.args[0].lower() == 'd' or context.args[0].lower() == 'default' or context.args[0].lower() == 'orignal':
        
           chat_histories[chat_id] = model.start_chat(history=[] )
           update.message.reply_text(f"The prompt has been successfully changed to: <b>'default'</b>", parse_mode='HTML')
           DB.Update_instruction(chat_id)
           
            
        else:
                model_temp = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=config.safety_settings,
                    generation_config=config.generation_config,
                    system_instruction=new_promt )
                chat_histories[chat_id] = model_temp.start_chat(history=[])
    
                update.message.reply_text(f"The prompt has been successfully changed to: <b>'{new_promt}'</b>", parse_mode='HTML')
                DB.Update_instruction(chat_id,new_promt)
        DB.chat_history_add(chat_id,[])
    else:
            update.message.reply_text(f"Error ! un sufficent info provided", parse_mode='HTML')




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
                update.message.reply_text(f"Sorry, I encountered an error while processing your message.\n error:{e}")
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
                html_message = format_html.escape(message)
                send_wrap(html_message)
                
            except Exception as e:
                logger.warning(f"cant parse the response error:{e}")
        else:
            logger.warning("sending unformated message")
            send_wrap(str(message))

        
                
    except Exception as e:
        
        update.message.reply_text(f"woops! an An error occurred while sending the message: {e}", parse_mode='HTML')
        logger.error(f"An error occurred while sending the message:{e}")




def help_command(update: Update, context: CallbackContext) -> None:
  """Send a well-formatted help message """
  if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          update.message.reply_text(f"You are blocked sorry you message are being ignored contact the owner for more details", parse_mode='HTML', disable_web_page_preview=True)
          return
  logger.info(f"help command asked by :{update.message.from_user.username}")
  update.message.reply_text(config.help_text, parse_mode='HTML', disable_web_page_preview=True)

def INFO(update: Update, context: CallbackContext) -> None:
  """Send a well-formatted info message """
  if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return

  logger.info(f"INFO command asked by :{update.message.from_user.username}")
  update.message.reply_text(DB.info(update.message.chat_id), parse_mode='HTML', disable_web_page_preview=True)

def GB_REFRESH(update: Update, context: CallbackContext) -> None:
  """REFRESH ALL USERS FROM CLOUD"""
  if update.message.chat_id != ADMIN_CHAT_ID:  
        update.message.reply_text("Access denied only admins can do this .", parse_mode='HTML')
        return 
  users_id = DB.get_usernames()
  if users_id:
    update.message.reply_text("Refreshing....", parse_mode='HTML')
    for chat_id in users_id:
        userData = DB.user_exists(chat_id)
        if userData:
                instruction = userData['system_instruction']
    
                if instruction =='default':
                    instruction = config.system_instruction            
                
                model_temp = genai.GenerativeModel(
                    model_name="gemini-1.5-pro-latest",
                    safety_settings=config.safety_settings,
                    generation_config=config.generation_config,
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

    logger.info(f"REFRESH command asked by :{update.message.from_user.username}")
    args = context.args
    if args:
        try:
            chatID = int(args[0])
        except ValueError:
            update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='HTML')
            return
    else: 
        chatID = update.message.chat_id
   
    try:
        UserCloudeData = DB.user_exists(chatID)
        if UserCloudeData:
            UserCloudeData['system_instruction']
            instruction = UserCloudeData['system_instruction']
            if instruction =='default':
                instruction_local = config.system_instruction
            else:
                instruction_local = instruction


            model_temp = genai.GenerativeModel(
                        model_name="gemini-1.5-pro-latest",
                        safety_settings=config.safety_settings,
                        generation_config=config.generation_config,
                        system_instruction= instruction_local)
            chat_histories[chatID] = model_temp.start_chat(history=jsonpickle.decode(UserCloudeData['chat_session']))
            update.message.reply_text(f"<b> Succesfully updated your info({chatID}) from cloud </b> \n\nPrompt : <i>{instruction}</i>\n\n chat History also updated!", parse_mode='HTML')
        else:
            update.message.reply_text(f"error 404! userID({chatID}) not found in cloud!")

    except Exception as e:
        update.message.reply_text(f"An error occurred while clearing the chat history: {e}")
        logger.error(f"An error occurred while clearing the chat history: {e}")

def start(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    user = update.message.from_user
    username = user.first_name if user.first_name else user.username if user.username else "there"

    welcome_message = f"Hello {username}! I'm Ares, your AI assistant. How can I help you today?"

    keyboard = [
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Contact Owner", callback_data='contact')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'help':
        help_message = config.help_text
        query.edit_message_text(text=help_message, parse_mode='HTML')
    elif query.data == 'contact':
        contact_message = "You can contact the owner at @Rkgroup5316. or join https://t.me/AresChatBotAi for info and bug reports ."
        query.edit_message_text(text=contact_message)

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
                  update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='HTML')
                  return
          else:
            update.message.reply_text("Access denied only admins can do this .", parse_mode='HTML')
            
    else: 
        chat_id = update.message.chat_id

    try:
        if chat_id in chat_histories:
            # Clear the chat history and start a new one with the default prompt
            chat_histories[chat_id] = model.start_chat(history=[])
            DB.chat_history_add(chat_id,[])
            update.message.reply_text("Chat history successfully cleared.")
        else:
            update.message.reply_text(f"error 404! chatID:{chat_id} not found in local data\n\n try refreshing")
        
    except Exception as e:
        update.message.reply_text(f"An error occurred while clearing the chat history: {e}")
        logger.error(f"An error occurred while clearing the chat history: {e}")


def history(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
          logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
          return
    args = context.args
    chat_id = update.message.chat_id

    try:
        if args:
            # If argument is provided, check if it's a valid chat ID
            try:
                arg_chat_id = int(args[0])
            except ValueError:
                update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.", parse_mode='HTML')
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
            update.message.reply_text("Invalid chat ID. Please provide a valid integer ID.")
            return

        if arg_chat_id in chat_histories:
            # If provided chat ID is in active sessions, retrieve its token count
            chat_session = chat_histories[arg_chat_id]
            if chat_session:
              update.message.reply_text(f'Total tokens used for chat ID {arg_chat_id}: {model.count_tokens(chat_session.history)}', parse_mode='HTML')
            else:
              update.message.reply_text(f"Total tokens used for chat ID {arg_chat_id}: 00", parse_mode='HTML')
            
        else:
            update.message.reply_text("Error 404: Chat ID not found.",parse_mode='html')
    else:
        # If no argument is provided, retrieve token count for the current session chat
        chat_session = get_chat_history(chat_id)
        if chat_session:
            update.message.reply_text(f'Total tokens used in current session: {model.count_tokens(chat_session.history)}', parse_mode='HTML')
        else:
            update.message.reply_text(f"Total tokens used for chat ID {chat_id}(yourself): 00", parse_mode='HTML')

def session_command(update: Update, context: CallbackContext) -> None:
    """Reports the total number of open chat sessions after password check."""

    if update.message.chat_id != ADMIN_CHAT_ID:  
        update.message.reply_text("Access denied only admins can do this .", parse_mode='HTML')
        return 
            

    total_sessions = len(chat_histories)
    if total_sessions == 0:
        update.message.reply_text("There are no active chat sessions.",parse_mode='html')
    else:
        session_message = f"There are currently <b>{total_sessions}</b> active chat sessions."
        update.message.reply_text(session_message, parse_mode='HTML')

def session_info_command(update: Update, context: CallbackContext) -> None:
    """Reports the list of chat IDs for active chat sessions after password check."""
    if update.message.chat_id != ADMIN_CHAT_ID:  
        update.message.reply_text("Access denied only admins can do this .", parse_mode='HTML')
        return 

    active_chat_ids = list(chat_histories.keys())  # Get the list of chat IDs for active chat sessions
    if not active_chat_ids:
        update.message.reply_text("There are no active chat sessions.", parse_mode='HTML')
    else:
        session_message = f"The active chat sessions have the following chat IDs: <code>{', '.join(str(chat_id) for chat_id in active_chat_ids)}</code>"
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
                update.message.reply_text("An error occurred while downloading the media. Please try again later.")
        else:
            # Inform the user that the video size exceeds the limit
            update.message.reply_text(f"The media size ({file_size_mb} MB) exceeds the limit of 5 MB. Please send a smaller media.")


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
                    f"<b>My apologies</b>, I've reached my <i>usage limit</i> for the moment. ⏳ Please try again in a few minutes. \n\n<i>Response :</i> {response}",
                    parse_mode='HTML'
                )


    except Exception as e:
        # Handle errors during the process
        update.message.reply_text(f"An error occurred : {e}")

    finally:
        try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    update.message.reply_text(f"An error occurred while cleaning up:file_path {file_path} did not existed ")

        except Exception as e:
            # Handle errors during cleanup
            update.message.reply_text(f"An error occurred while cleaning up: {e}")

def extract_chat_info(update: Update, context: CallbackContext) -> None:
  """Extracts and displays information about chats.

  Args:
    update: Update object from the Telegram Bot API.
    context: CallbackContext object from the Telegram Bot SDK.
  """
  if update.message.chat_id != ADMIN_CHAT_ID:  
        update.message.reply_text("Access denied only admins can do this .", parse_mode='HTML')
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
              "Chat ID": chat.id,
              "Chat Type": chat.type,
              "Title": chat.title,
              "Username": chat.username,
              "First Name": chat.first_name,
              "Last Name": chat.last_name,
              "Description": chat.description,
              "Invite Link": chat.invite_link,
              "Pinned Message": chat.pinned_message.text if chat.pinned_message else None,
          }
          filtered_data = {k: v for k, v in chat_data.items() if v is not None}
          info_text = "\n".join([f"{key}: {value}" for key, value in filtered_data.items()])

          # Send response for each chat
          update.message.reply_text(f"Chat Information:\n{info_text}", parse_mode='HTML')
        except telegram.error.Unauthorized:
          update.message.reply_text(f"Chat ID {chat_id}: I don't have access to this chat.")
        except telegram.error.BadRequest as e:
          update.message.reply_text(f"Chat ID {chat_id}: Bad request. Error: {e.message}")
        except Exception as e:
          update.message.reply_text(f"Chat ID {chat_id}: Failed to get chat information. Error: {e}")
      except ValueError:
        update.message.reply_text(f"Invalid chat ID: {chat_id_str}. Please provide numeric chat IDs.")

  else:
    update.message.reply_text("Please provide chat IDs. Usage: /chatinfo <chat_id1> <chat_id2> ...")


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
    chat_id = update.effective_chat.id
    query_ = " ".join(context.args)
    logger.info(f"chatId:{chat_id} used /image command with this query:{query_}")

    if not query_:
        context.bot.send_message(chat_id, text="Please provide a search query for images.")
        return
    context.bot.send_message(chat_id, text="Please wait for downloading images.")
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.FIND_LOCATION)

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
            
            context.bot.send_message(chat_id, text=f"Sent {len(downloaded_images)} images for your search. time taken {round(elapsed_time, 2)} Sec")
            shutil.rmtree(f"images/{query_}")
        else:
            context.bot.send_message(chat_id, text="No images found for your search.")
    
    threading.Thread(target=image_pros, args=(update,context,query_)).start()
  
def wiki(update: Update, context: CallbackContext):
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
    chat_id = update.effective_chat.id
    search = " ".join(context.args)
    if search:
        try:
            res = wikipedia.summary(search)
        except DisambiguationError as e:
            update.message.reply_text(
                "Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>".format(e),
                parse_mode=ParseMode.HTML,
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
          update.message.reply_text("Error 500! server error!", parse_mode=ParseMode.HTML)
        
    else:
       update.message.reply_text("Error 400! pls provide a query to search in wiki!", parse_mode=ParseMode.HTML)

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
    chat_id = update.effective_chat.id
    search = " ".join(context.args)
    if not search:
      update.message.reply_text(f"error 404 no promt provided pls provide prompt")
      return 
      
      
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.FIND_LOCATION)
    try:
        logger.info(f"requesting for image for chatId:{chat_id}  prompt:{search}")
        x = create_image(search)
        logger.info(f"image created successfully")
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
        prompt: {search}

        chat_id: {chat_id}


"""
  
        update.message.reply_photo(photo=open("image.jpg", 'rb'), caption=caption, quote=True)
    except Exception as e:
        update.message.reply_text(f"error while generating image error : {e}")
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
    chat_id = update.effective_chat.id
    search = " ".join(context.args)
    if not search:
        update.message.reply_text(f"error 404 no query provided pls provide a search query")
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
              format_html.escape("**Search Query:**\n`" + search + "`\n\n**Results:**\n" + msg), link_preview=False,parse_mode='MarkdownV2'
          )
    except Exception as e:
        # Handle potential errors sending the result (e.g., network issues)
         update.message.reply_text(f"Sorry can't send the result error:{e}")
         logger.error(f"Failed to send google search result on query:{search} error : {e}")
  
def bug(update: Update, context: CallbackContext) -> None:
    if DB.is_user_blocked(str(update.message.from_user.id)):
        logger.info(f"Ignoring command from blocked user {str(update.message.from_user.id)}.")
        return
      
    chat_id = update.effective_chat.id
    bugs = " ".join(context.args)
    if not bugs:
      update.message.reply_text(f"Type the bug or error you are facing")
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
            chat_id=SUPPORT_CHAT_ID, text=format_html.escape(bug_report), parse_mode='MarkdownV2'
        )
    context.bot.send_message(
            chat_id=ADMIN_CHAT_ID, text=format_html.escape(bug_report), parse_mode='MarkdownV2'
        )
    update.message.reply_text(
        f"*ʙᴜɢ ʀᴇᴩᴏʀᴛ* : **{bugs}** \n\n » ʙᴜɢ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴩᴏʀᴛᴇᴅ  Join the support group for extra help and direct contact ",parse_mode='MarkdownV2'
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
    if update.message.chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML)
        return

    # Get the message to broadcast
    message_to_broadcast = ' '.join(context.args)
    if not message_to_broadcast:
        update.message.reply_text("Please provide a message to broadcast.", parse_mode=ParseMode.HTML)
        return

    users_id = DB.get_usernames()
    if users_id:
        update.message.reply_text("Broadcasting message to all users...", parse_mode=ParseMode.HTML)
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
        
        update.message.reply_text("Broadcast complete.", parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("No users found in the cloud data.", parse_mode=ParseMode.HTML)


def specific_broadcast(update: Update, context: CallbackContext) -> None:
    """Broadcast a message to a specific user."""
    if update.message.chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML)
        return

    if len(context.args) < 2:
        update.message.reply_text("Usage: /specific_broadcast (chat_id) (message)", parse_mode=ParseMode.HTML)
        return

    chat_id = context.args[0]
    message_to_broadcast = ' '.join(context.args[1:])

    try:
        context.bot.send_message(chat_id=chat_id, text=message_to_broadcast, parse_mode=ParseMode.HTML)
        update.message.reply_text(f"Message sent to chat ID {chat_id}.", parse_mode=ParseMode.HTML)
        logger.info(f"Message sent to chat ID {chat_id}.")
    except Exception as e:
        logger.error(f"Error sending message to chat ID {chat_id}: {e}")
        if "bot was blocked by the user" in str(e):
            update.message.reply_text(f"User {chat_id} has blocked the bot.", parse_mode=ParseMode.HTML)
            logger.info(f"User {chat_id} has blocked the bot.")
        else:
            update.message.reply_text(f"Error sending message to chat ID {chat_id}: {e}", parse_mode=ParseMode.HTML)

def block_user_command(update: Update, context: CallbackContext) -> None:
    """Block a user."""
    if update.message.chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML)
        return

    if len(context.args) != 1:
        update.message.reply_text("Usage: /block <user_id>", parse_mode=ParseMode.HTML)
        return

    user_id_to_block = context.args[0]
    DB.block_user(user_id_to_block)
    update.message.reply_text(f"User {user_id_to_block} has been blocked.", parse_mode=ParseMode.HTML)

def unblock_user_command(update: Update, context: CallbackContext) -> None:
    """Unblock a user."""
    if update.message.chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML)
        return

    if len(context.args) != 1:
        update.message.reply_text("Usage: /unblock <user_id>", parse_mode=ParseMode.HTML)
        return

    user_id_to_unblock = context.args[0]
    DB.unblock_user(user_id_to_unblock)
    update.message.reply_text(f"User {user_id_to_unblock} has been unblocked.", parse_mode=ParseMode.HTML)

def all_blocked_users(update: Update, context: CallbackContext) -> None:
  """list of all blocked users"""
  if update.message.chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML)
        return
  blocked_users = DB.blocked_users_cache
  update.message.reply_text(f"User that are unblocked : {blocked_users}", parse_mode=ParseMode.HTML)


# Function to get network speed
def get_network_speed():
    net_io_1 = psutil.net_io_counters()
    time.sleep(1)  # wait for a second
    net_io_2 = psutil.net_io_counters()

    bytes_sent_per_sec = net_io_2.bytes_sent - net_io_1.bytes_sent
    bytes_recv_per_sec = net_io_2.bytes_recv - net_io_1.bytes_recv

    return bytes_sent_per_sec, bytes_recv_per_sec

# Define the /ping command handler
def ping(update: Update, context: CallbackContext) -> None:
    if update.message.chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("Access denied. Only admins can do this.", parse_mode=ParseMode.HTML)
        return

    # Get system usage statistics
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    total_memory = memory_info.total / (1024 ** 3)  # Convert bytes to GB
    available_memory = memory_info.available / (1024 ** 3)  # Convert bytes to GB
    used_memory = memory_info.used / (1024 ** 3)  # Convert bytes to GB
    memory_percent = memory_info.percent

    # Get network speed
    bytes_sent_per_sec, bytes_recv_per_sec = get_network_speed()

    # Convert bytes per second to Mbps
    bytes_to_mbps = 8 / (1024 ** 2)  # Convert bytes/sec to megabits/sec
    sent_speed_mbps = bytes_sent_per_sec * bytes_to_mbps
    recv_speed_mbps = bytes_recv_per_sec * bytes_to_mbps

    # Create the response message
    response = (
        "<pre>"
        "Pong!\n"
        f"CPU Usage: {cpu_usage}%\n"
        f"Total Memory: {total_memory:.2f} GB\n"
        f"Available Memory: {available_memory:.2f} GB\n"
        f"Used Memory: {used_memory:.2f} GB ({memory_percent}%)\n"
        f"Upload Speed: {sent_speed_mbps:.2f} Mbps\n"
        f"Download Speed: {recv_speed_mbps:.2f} Mbps"
        "</pre>"
    )

    # Send the response message with HTML parsing
    update.message.reply_text(response, parse_mode=ParseMode.HTML)


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
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("bug", bug))
    dispatcher.add_handler(CommandHandler("info", INFO))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
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
    
    dispatcher.add_handler(CommandHandler("image", image_command_handler))
    dispatcher.add_handler(CommandHandler("wiki", wiki))
    dispatcher.add_handler(CommandHandler("imagine", imagine))
    dispatcher.add_handler(CommandHandler("google", Google_search))
    dispatcher.add_handler(CommandHandler("session", session_command))
    dispatcher.add_handler(CommandHandler("session_info", session_info_command))
    dispatcher.add_handler(CommandHandler("cid_info", extract_chat_info))

    
                                    

    # Register the admin/info command handler
    dispatcher.add_handler(CommandHandler("token", Token))


    # Register the ChangePrompt command handler
    dispatcher.add_handler(CommandHandler("clear_history", clear_history, pass_args=True))
    dispatcher.add_handler(CommandHandler("ChangePrompt", change_prompt, pass_args=True))

    dispatcher.add_error_handler(error_handler)



    logger.warning("Bot started!")


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    DB = FireBaseDB()
    keep_alive()
    main()
