import google.generativeai as genai

class APIClient:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_api_index = 0
        self.last_used_time = {}

    def switch_to_next_api(self):
        self.current_api_index = (self.current_api_index + 1) % len(self.api_keys)

    def use_api(self):
        current_api_key = self.api_keys[self.current_api_index]
        
        # Check if the API key was used recently
        if current_api_key in self.last_used_time:
            last_used_timestamp = self.last_used_time[current_api_key]
            elapsed_time = time.time() - last_used_timestamp
            if elapsed_time < 60:  # 60 seconds interval
                print("Safety system activated: Waiting before using the next API key...")
                raise ValueError(f"Safety system activated: the api is being used to early cant change to next api pls wait 60 sec")

        # Simulate API usage
        genai.configure(api_key=current_api_key)
        print(f"Using API key: {current_api_key}")

        # Update last used time
        self.last_used_time[current_api_key] = time.time()
