import os
import datetime
import json
import jsonpickle
import logging
import firebase_admin
from firebase_admin import db, credentials
from logs import logger

class FireBaseDB:
    def __init__(self):
        cred = credentials.Certificate(json.loads(os.environ.get('fire_base')))
        app = firebase_admin.initialize_app(cred, {"databaseURL": "https://ares-rkbot-default-rtdb.asia-southeast1.firebasedatabase.app/"})

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
