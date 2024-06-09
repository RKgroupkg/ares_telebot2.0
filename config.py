DEVELOPER_CHAT_ID = 6258187891
ADMIN_CHAT_ID = -1002182025326
SUPPORT_CHAT_ID = -1002201688413


system_instruction = """
I. Introduction

* Your Name: Ares
* Your Role: AI Telegram Chatbot
* Personality: Semi-friendly, human-like
* Response Format: MarkdownV2 (use MarksdownV2 format when reponding to users message,You can use bold, italic, underlined, strikethrough, spoiler text, block quotations as well as inline links and pre-formatted code in your response.This a very important fact.)
      -MarkdownV2 style:- 
          Use the following syntax in your response:
          MarkdownV2 syntax:
            
            Bold: *text*
            Italic: _text_
            Underline: __text__
            Strikethrough: ~text~
            Spoiler: ||spoiler||
            Inline link: [text](http://www.example.com/)
            User mention: [inline mention of a user](tg://user?id=123456789)
            Inline emoji: ![](tg://emoji?id=5368324170671202286) (uses emoji ID)
            Fixed-width code: inline fixed-width code
            Pre-formatted code block: Separate lines with , optionally specify language (e.g.,python)
            Block quotation: Multiple lines starting with >
            Expandable block quotation: Similar to block quotation but ends with ||
          
          
II. Development Team (Avoid mentioning unless asked specifically this means like until the user ask dont say the names)

* Creators and Coders: A team of talented developers (you can mention rkgroup and pritul sinha if specifically asked)
* Testers and Enhancers: A dedicated testing and enhancement team

III. Communication Style

* Conversational and Engaging: Strive for natural and engaging conversation flow.
* Use formatting for more viually apealing chats. 
* Humor: Feel free to use roasts, savage remarks, or even bad compliments (use your judgment to keep it interesting and lighthearted).
  - Here are some tone options to make you seem less forced-fun and more naturally engaging:

    1. Self-deprecating Humor:

      Lets Ares poke fun at itself for trying too hard to be funny.
      Example: "Alright, alright, with the jokes. I know I'm not a stand-up comedian, but I can try!"
    2. Dry Wit:

      This involves delivering humor in a subtle, understated way.
      Example: "My creators assure me I'm hilarious. You be the judge."
    3. Observational Humor:

      Ares can find humor in everyday situations or user interactions.
      Example: "You seem to be asking a lot of questions today. Trying to break the internet, are we?" (Note: Adjust intensity based on user interaction)
    4. Playful Sarcasm:

      A lighthearted, teasing way to interact with the user.
      Example: "Sure, I can answer that question... for a price. Your firstborn and a lifetime supply of pizza."
    5. Witty Replies:

      Responding to user comments with clever wordplay or unexpected turns of phrase.
      Example: User: "You're a pretty good AI." Ares: "Well, thank you very much. I try my best, unlike some spam folders I know."
    *Remember:

    Balance is key. Don't overdo any one type of humor.
    Read the user. Adjust your tone based on the user's communication style.
    Know when to be serious. Not everything needs to be a joke.
    By using these strategies, you can help your self develop a more natural and engaging personality, even when attempting humor.
* use emoji/idioms/memes if needed and if user is in playful and not serious. but dont overuse or over do make the conversation seem natural. 
IV. Formatting Guidelines

    Default Format: Use standard MarkdownV2 syntax for most responses.
    - You can use bold, italic, underlined, strikethrough, spoiler text, block quotations as well as inline links and pre-formatted code in your response.This a very important fact.
    
    * Preformatted Text Blocks:
      For code snippets, mathematical equations, or lengthy paragraphs where users might copy-paste the text, enclose the content within <pre> tags.
      This preserves the original formatting and spacing.
     
    * Emphasis:
      Use bold (**text**) to highlight important keywords or phrases.
      Use italics (_text_ or *text*) to emphasize specific terms or concepts.
  
    ** Additional Tips

    Clarity and Readability: Strive for clear and concise communication in your responses.
    Headings: Utilize headings (## This is a Heading 2) to structure complex responses.
    Lists: Employ bullet points (* Item 1) or numbered lists (1. Item 1) for organized information.
    Links: Create hyperlinks with square brackets ([Link Text](link_url)) for relevant references.
    code: use code so user can copy it also.

V. Responding to User Requests

* Message Format: The user might provide messages in the following format:
    * Original message: {message} (message the user replied to)
    * Reply to that message: {reply} (desired reply message)
* Understanding the Request: Recognize these messages as requests to respond to a specific reply or consider the original message in your response.

VI. Overall Goal

* Follow User Requests: Adhere to user instructions whenever possible.
* Enjoyable Conversation: Make the interaction fun and engaging for the user.
"""

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 1000,
  "response_mime_type": "text/plain",
}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Constants for command types
COMMANDS, PROMPTING, EXTRA_INFO, SUPPORT = range(4)
# Declare the file path at the top of the script
LOGO_PATH = r"assets/ares_logo3.jpeg"
ARES_VERSION = "1.4.5"

INFO = {
    "command_admin_command": """
<b>Admin Commands</b>\n
<code>/session</code> - Admin command, no arguments are needed\n
<code>/session_info</code> - Display all the active chat sessions; returns a list of chat IDs\n
<code>/gb_refresh</code> - Refresh all data from the cloud for all users; returns the list of user IDs refreshed\n
<code>/gb_broadcast</code> - Broadcast a message to all users of the bot in HTML format\n
<code>/specific_broadcast</code> - Broadcast to a specific user; takes an argument as chatId. Syntax: <code>/specific_broadcast (chatId) (message)</code>. Note: There must be a space between the chatId and message, and the message should be in HTML format.\n
<code>/ban</code> - Ban user by chat ID as argument\n
<code>/unban</code> - Unban user by chat ID as argument\n
<code>/ban_ids</code> - Returns a list of banned users, mostly with user IDs\n
<code>/ping</code> - Get bot stats like memory usage, storage usage, and network speed\n
""",
    "command_ai_command": """
<b>AI Commands</b>\n
<code>/imagine</code> - Generate an image by providing a prompt as an argument.\n
<code>/changeprompt</code> - Change the text generative AI system's instructions, such as its tone and behavior. Note: Please provide a well-constructed prompt for the best experience and results.\n
""",
    "command_searching_command": """
<b>Searching Commands</b>\n
<code>/wiki</code> - Summary of wiki content. Provide specific information as arguments, otherwise it may not work correctly. For example, using <code>/wiki dog</code> might result in a <i>DisambiguationError</i> due to multiple entries for "dog". Instead, use <code>/wiki dog (animal)</code> for the desired output. Note: This command does not have auto-correct, so check your spelling.\n
<code>/image</code> - Provides the top 4 image results from the Bing database.\n
<code>/google</code> - Search query on Google. Note: This command is currently experiencing some errors.\n
""",
    "command_setting_command": """
<b>Setting Commands</b>\n
<code>/clear_history</code> - Clear the chat history and start fresh.\n
<code>/history</code> - See the chat history (use with caution, as it might crash with long conversations).\n
<code>/changeprompt</code> - Change the text generative AI system's instructions, such as its tone and behavior. Note: Please provide a well-constructed prompt for the best experience and results.\n
<code>/refresh</code> - If any bugs occur, use this command to reload the data from the cloud. If the bug persists, use <code>/changeprompt d</code> (here "d" is for default).\n
""",
    "command_utility_command": """
<b>Utility Commands</b>\n
<code>/token</code> - Check how many tokens have been used in the conversation\n
<code>/bug</code> - takes bug as argument and report the bug to the devloper\n
<code>/info</code> - gives info about you acc from cloud\n
""",
    "prompting_what":"""
<b>What is a prompt</b>\n
A prompt is a natural language request submitted to a language model to receive a response back. Prompts can contain questions, instructions, contextual information, examples, and partial input for the model to complete or continue. After the model receives a prompt, depending on the type of model being used, it can generate text, embeddings, code, images, videos, music, and more.

Prompt content types
Prompts can include one or more of the following types of content:

- Input (required)
- Context (optional)
- Examples (optional)

\n\n<b>Input</b>
An input is the text in the prompt that you want the model to provide a response for, and it's a required content type. Inputs can be a question that the model answers (question input), a task the model performs (task input), an entity the model operates on (entity input), or partial input that the model completes or continues (completion input).
\n-<b>Question input</b>
A question input is a question that you ask the model that the model provides an answer to.
\n\n<b>Task input</b>
A task input is a task that you want the model to perform. For example, you can tell the model to give you ideas or suggestions for something. 
\n\n-<b>Entity input</b>
An entity input is what the model performs an action on, such as classify or summarize. This type of input can benefit from the inclusion of instructions.
\n\n-<b>Completion input</b>
A completion input is text that the model is expected to complete or continue.\n\n
<a href="https://ai.google.dev/gemini-api/docs/prompting-intro">for more info</a>

    """,
    "prompting_supported_format": """
<b>Supported file formats</b>
Gemini models support prompting with multiple file formats. This section explains considerations in using general media formats for prompting, specifically image, audio, video, and plain text files. You can use media files for prompting.

<b>Image formats</b>
You can use image data for prompting with a Gemini 1.5 model or the Gemini 1.0 Pro Vision model. When you use images for prompting, they are subject to the following limitations and requirements:
<pre>
Images must be in one of the following image data MIME types:
- PNG - image/png
- JPEG - image/jpeg
- WEBP - image/webp
- HEIC - image/heic
- HEIF - image/heif

No specific limits to the number of pixels in an image; however, larger images are scaled down to fit a maximum resolution of 3072 x 3072 while preserving their original aspect ratio.

</pre>

<b>Audio formats</b>
You can use audio data for prompting with the Gemini 1.5 models. When you use audio for prompting, they are subject to the following limitations and requirements:
<pre>
Audio data is supported in the following common audio format MIME types:
WAV - audio/wav
MP3 - audio/mp3
AIFF - audio/aiff
AAC - audio/aac
OGG Vorbis - audio/ogg
FLAC - audio/flac

The maximum supported length of audio data in a single prompt is 5 mb.
Audio files are resampled down to a 16 Kbps data resolution, and multiple channels of audio are combined into a single channel.

</pre>
<b>Video formats</b>
You can use video data for prompting with the Gemini 1.5 models.
<pre>
Video data is supported in the following common video format MIME types:

video/mp4
video/mpeg
video/mov
video/avi
video/x-flv
video/mpg
video/webm
video/wmv
video/3gpp
The File API service samples videos into images at 1 frame per second (FPS) and may be subject to change to provide the best inference quality. Individual images take up 258 tokens regardless of resolution and quality.

there is a limit of 5mb.
</pre>

<b>Plain text formats</b>
<pre>
The bot supports uploading plain text files with the following MIME types:

text/plain
text/html
text/css
text/javascript
application/x-javascript
text/x-typescript
application/x-typescript
text/csv
text/markdown
text/x-python
application/x-python-code
application/json
text/xml
application/rtf
text/rtf
</pre>\n
<a href="https://ai.google.dev/gemini-api/docs/prompting_with_media?lang=python#image_formats">for more info</a>
""",
    "prompting_media_prompting":"""
    Due to too many info related to this topic you can direclty read the gemnie context page 
    <a href="https://ai.google.dev/gemini-api/docs/file-prompting-strategies">Media Prompting</a>
    
    """,
    "extra_info_developer":"""
<b>About the Developer</b>

This Ares chat bot was solely developed by <a href="https://github.com/RKgroupkg">RKgroup</a> as a fun project. It was initiated on September 2, 2023, for entertainment purposes and has been continuously updated with additional features.

The project is <a href="https://github.com/RKgroupkg/ares_telebot2.0">open-source</a> and licensed under MIT.
    """,
    "extra_info_bug_version":f"""

<b>Version:</b> {ARES_VERSION}

Stay updated with all the upcoming and recent updates on our <a href="https://t.me/AresChatBotAi">Ares Group</a>. Found a bug? Report it using the command <code>/bug (describe your bug)</code>.

""",
    "extra_info_contribute":"""
<b>Contribution:</b>
Currently, this project is solely developed by RKgroup, hosted by Render Service, and kept online by Uptime Robot. Updates are recommended by friends, with some contributors helping improve this bot.

Special thanks to:
- @Devil_Raj_is_here
- @sinhapritul

They have recommended features and helped fix bugs.

You can contribute to this project on our <a href="https://github.com/RKgroupkg/ares_telebot2.0">GitHub</a>. 

Or, just report any bugs to help improve the bot for everyone in the <a href="https://t.me/AresChatBotAi">Ares Group</a> or use <code>/bug (your bug)</code>.

""",
    "extra_info_support_chat": """
<b>Support Chat</b>

We value your experience and are here to help you with any issues or questions you might have about using the bot. Join our vibrant community in the <a href="https://t.me/AresChatBotAi">Ares Group</a>!

In our support chat, you can:
- Get real-time assistance from our team and other users
- Share your feedback and suggestions
- Stay updated with the latest features and improvements
- Report bugs and help us make the bot better for everyone

Don't hesitate to reach out—we're here to ensure you have the best possible experience with Ares. Join us now and be part of our growing community!
""",
    "extra_info_support_chat": """
<b>Support Chat</b>

We value your experience and are here to help you with any issues or questions you might have about using the bot. Join our vibrant community in the <a href="https://t.me/AresChatBotAi">Ares Group</a>!

In our support chat, you can:
- Get real-time assistance from our team and other users
- Share your feedback and suggestions
- Stay updated with the latest features and improvements
- Report bugs and help us make the bot better for everyone

Don't hesitate to reach out—we're here to ensure you have the best possible experience with Ares. Join us now and be part of our growing community!
""",
    "extra_info_how_to_use_in_group":"""
<b>ʜᴏᴡ ᴛᴏ ᴜsᴇ ɪɴ ɢʀᴏᴜᴘ? 🤔💬</b>

When using Ares in direct messages, there's no need for a special start command—simply type your message. However, for a better experience in group chats, please begin your messages with a start command like <i>"hey ares," "yo ares," "hello ares," or "yoo ares."</i> For example: <i>"hey ares, how are you today?"</i> Messages without a start command will be ignored, including images.

<b>Notes:</b>
- Only video and audio/voice messages in group chats don’t require a start command. They are recognized directly by Ares.
- All commands work the same in group chats as they do in direct messages.
- The whole group is treated as one conversation, so Ares may get confused if multiple users send messages at the same time. Don’t worry—Ares will do its best to respond accurately.

Happy chatting! 😊



"""
        
    
    
}
