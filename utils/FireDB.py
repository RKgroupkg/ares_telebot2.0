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
        self.INFO_ADMIN = db.reference("/Admin_users")  # Updated reference for admin users
        self.blocked_users_cache = set()
        self.admins_users = set()
        self._load_blocked_users()
        self._load_admin_users()  # Corrected method name
    
    def user_exists(self, userId):
        try:
            return db.reference(f"/users_sessions/{userId}").get()
        except Exception as e:
            raise ValueError(f"Error while checking for user: {e}")

    def create_user(self, userId):
        user_data = self.user_exists(userId)
        if user_data:
            raise ValueError(f"User with ID '{userId}' already exists!")
        
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format

        conversation = {
            "chat_session": {},
            "date": formatted_time,
            "system_instruction": "default"
        }
        db.reference(f"/users_sessions").update({f"{userId}": conversation })
        
    def extract_history(self, userId):
        try:
            user_data = self.user_exists(userId)
            if not user_data:
                raise ValueError(f"User with ID '{userId}' not found")

            return jsonpickle.decode(user_data.get("chat_session"))
        except (KeyError, AttributeError) as e:
            raise ValueError(f"Error accessing user data or conversation: {e}")

    def chat_history_add(self, userId, history=[]):
        try:
            db.reference(f"/users_sessions/{userId}").update({f"chat_session": jsonpickle.encode(history, True)})
        except (KeyError, AttributeError) as e:
            raise ValueError(f"Error accessing user data or chat session: {e}")
    
    def extract_instruction(self, userId):
        user_data =  self.user_exists(userId)
        if not user_data:
            raise ValueError(f"User with ID '{userId}' not found")

        return user_data["system_instruction"]

    def update_instruction(self, userId, new_instruction="default"):
        db.reference(f"/users_sessions/{userId}").update({f"system_instruction": new_instruction })

    def info(self, userId):
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
        try:
            blocked_users = self.INFO_DB.get()
            if blocked_users:
                self.blocked_users_cache = set(blocked_users.keys())
            logger.info("Blocked users loaded into cache.")
        except Exception as e:
            logger.error(f"Error loading blocked users: {e}")

    def _load_admin_users(self):
        try:
            admin_users = self.INFO_ADMIN.get()  # Corrected reference to INFO_ADMIN
            if admin_users:
                self.admins_users = set(admin_users.keys())
            logger.info("Admin users loaded into cache.")
        except Exception as e:
            logger.error(f"Error loading admin users: {e}")

    def is_admin(self, userId):
        return userId in self.admins_users

    def block_user(self, userId):
        try:
            self.INFO_DB.update({userId: True})
            self.blocked_users_cache.add(userId)
            logger.info(f"User {userId} has been blocked.")
        except Exception as e:
            logger.error(f"Error blocking user {userId}: {e}")

    def unblock_user(self, userId):
        try:
            self.INFO_DB.child(userId).delete()
            self.blocked_users_cache.discard(userId)
            logger.info(f"User {userId} has been unblocked.")
        except Exception as e:
            logger.error(f"Error unblocking user {userId}: {e}")

    def is_user_blocked(self, userId):
        return userId in self.blocked_users_cache
