
command_limit_inline_list = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
        [InlineKeyboardButton("what is command limit rate❓", callback_data="Command_limit_rate")],
    ]   
command_limit_inline = InlineKeyboardMarkup(command_limit_inline_list)

Invalid_arg_list = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
        [InlineKeyboardButton("Help❓", callback_data="command_arg")],
    ]   
Invalid_arg = InlineKeyboardMarkup(Invalid_arg_list)

Admin_error_list = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
        [InlineKeyboardButton("Who are admin❓", callback_data="command_who_are_admin")],
    ]   
Admin_error = InlineKeyboardMarkup(Admin_error_list)
DisambiguationError_list = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
        [InlineKeyboardButton("What is Disambiguation Error❓", callback_data="command_wiki_disambiguationerror")],
    ]   
DisambiguationError = InlineKeyboardMarkup(DisambiguationError_list) 

music_limit_list_error = [
        [InlineKeyboardButton("❌ᴄʟᴏsᴇ", callback_data="close")],
        [InlineKeyboardButton("What is this Error❓", callback_data="command_music_limit_error")],
    ]   
music_limit_error = InlineKeyboardMarkup(music_limit_list_error) # this feature still not added .
