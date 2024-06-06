import time

class CommandLogger:
    def __init__(self, cleanup_interval=3600):
        self.command_logs = {}  # Dictionary to store command logs for each user
        self.last_interaction = {}  # Dictionary to store last interaction time for each user
        self.cleanup_interval = cleanup_interval  # Cleanup interval in seconds (default: 1 hour)
        self.last_cleanup_time = time.time()  # Last cleanup time

    def log_command(self, user_id, command_name):
        """Log a command usage."""
        timestamp = time.time()
        self.command_logs.setdefault(user_id, []).append((timestamp, command_name))
        self.last_interaction[user_id] = timestamp

    def check_rate_limit(self, user_id, limit=5, interval=60):
        """Check if the user has exceeded the command rate limit."""
        self.cleanup()
        current_time = time.time()
        if user_id in self.command_logs:
            recent_commands = [log[0] for log in self.command_logs[user_id] if log[0] >= current_time - interval]
            if len(recent_commands) >= limit:
                return False  # Rate limit exceeded
        return True  # User is within the rate limit

    def get_last_interaction(self, user_id):
        """Get the timestamp of the user's last interaction."""
        self.cleanup()
        return self.last_interaction.get(user_id)

    def get_command_history(self, user_id):
        """Get the command history for the user."""
        self.cleanup()
        return self.command_logs.get(user_id, [])

    def cleanup(self):
        """Cleanup old data."""
        current_time = time.time()
        if current_time - self.last_cleanup_time >= self.cleanup_interval:
            for user_id, logs in list(self.command_logs.items()):
                self.command_logs[user_id] = [(ts, cmd) for ts, cmd in logs if ts >= current_time - self.cleanup_interval]
                if not self.command_logs[user_id]:
                    del self.command_logs[user_id]
                    self.last_interaction.pop(user_id, None)
            self.last_cleanup_time = current_time

    def clear_all_logs(self):
        """Clear all command logs and last interaction times."""
        self.command_logs.clear()
        self.last_interaction.clear()

    def get_users_with_logs(self):
        """Get the list of users with command logs."""
        return list(self.command_logs.keys())

    def get_total_commands(self, user_id):
        """Get the total number of commands executed by a user."""
        return len(self.command_logs.get(user_id, []))

    def get_user_commands_within_interval(self, user_id, interval=60):
        """Get the number of commands executed by a user within a specific interval."""
        current_time = time.time()
        if user_id in self.command_logs:
            recent_commands = [log[0] for log in self.command_logs[user_id] if log[0] >= current_time - interval]
            return len(recent_commands)
        return 0

    def remove_user_logs(self, user_id):
        """Remove all command logs and last interaction time for a specific user."""
        if user_id in self.command_logs:
            del self.command_logs[user_id]
            self.last_interaction.pop(user_id, None)

    def set_cleanup_interval(self, interval):
        """Set the cleanup interval."""
        self.cleanup_interval = interval
