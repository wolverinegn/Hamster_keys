import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types
import random
import os
import time
import threading
import json
import requests

API_TOKEN = "7226486244:AAE0JphBz8hI6ro7YFnYB0_0vFKq7ajfuSI"
bot = telebot.TeleBot(API_TOKEN)

channels_file = 'channels.txt'
keys_file = 'keys.txt'
used_users_file = 'used_users.txt'
waiting_list_file = 'waiting_list.json'
all_users_file = 'all_users.txt'

def load_channels():
    if os.path.exists(channels_file):
        with open(channels_file, 'r') as file:
            return [line.strip() for line in file.readlines()]
    return []

def save_channels(channels):
    with open(channels_file, 'w') as file:
        file.write('\n'.join(channels))

CHANNELS = load_channels()

def load_keys():
    if os.path.exists(keys_file):
        with open(keys_file, 'r') as file:
            return [line.strip() for line in file.readlines()]
    return []

keys = load_keys()

allowed_admin_ids = [1435580106]

num_keys_per_user = 2

def has_user_received_keys(user_id):
    if not os.path.exists(used_users_file):
        return False
    with open(used_users_file, 'r') as file:
        used_users = file.read().splitlines()
        return str(user_id) in used_users

def mark_user_as_received(user_id):
    with open(used_users_file, 'a') as file:
        file.write(f"{user_id}\n")

def add_user(user_id):
    if not user_exists(user_id):
        with open(all_users_file, 'a') as file:
            file.write(f"{user_id}\n")

def user_exists(user_id):
    if os.path.exists(all_users_file):
        with open(all_users_file, 'r') as file:
            users = file.read().splitlines()
            return str(user_id) in users
    return False

def get_waiting_list():
    if os.path.exists(waiting_list_file):
        with open(waiting_list_file, 'r') as file:
            return json.load(file)
    return []

def save_waiting_list(waiting_list):
    with open(waiting_list_file, 'w') as file:
        json.dump(waiting_list, file)

def get_waiting_list_position(user_id):
    waiting_list = get_waiting_list()
    return waiting_list.index(user_id) + 1 if user_id in waiting_list else -1

def add_to_waiting_list(user_id):
    waiting_list = get_waiting_list()
    if user_id not in waiting_list:
        waiting_list.append(user_id)
        save_waiting_list(waiting_list)

def create_channels_keyboard():
    keyboard = InlineKeyboardMarkup()
    for channel in CHANNELS:
        button_text = f"Subscribe to {channel}"
        keyboard.add(InlineKeyboardButton(text=button_text, url=f"https://t.me/{channel[1:]}"))
    return keyboard

def create_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("Get Keys", callback_data="get_keys"))
    return keyboard

def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not check_subscription(message.from_user.id):
        keyboard = create_channels_keyboard()
        bot.reply_to(message, "Please subscribe to the following channels first\nand click /start  ", reply_markup=keyboard)
        return
    add_user(message.from_user.id)
    with open('Hamster.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption="Welcome! Click the button below to get your keys.", reply_markup=create_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "get_keys":
        if not check_subscription(call.from_user.id):
            keyboard = create_channels_keyboard()
            bot.answer_callback_query(call.id, "Please subscribe to the following channels first.", show_alert=True)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            return
        send_keys(call.message)

def send_keys(message):
    user_id = message.chat.id
    if has_user_received_keys(user_id):
        bot.send_message(user_id, "You have already received your keys.")
    else:
        waiting_list = get_waiting_list()
        if user_id in waiting_list:
            position = waiting_list.index(user_id) + 1
            bot.send_message(user_id, f"You are already in the waiting list at position {position}.")
        elif len(keys) < num_keys_per_user:
            if waiting_list:
                bot.send_message(user_id, "There are users in the waiting list. You will be added to the end of the list.")
            add_to_waiting_list(user_id)
            position = get_waiting_list_position(user_id)
            bot.send_message(user_id, f"You have been added to the waiting list at position {position}.")
        else:
            selected_keys = random.sample(keys, num_keys_per_user)
            for key in selected_keys:
                keys.remove(key)
            response = '\n'.join(selected_keys)
            bot.send_message(user_id, f"Here are your keys:\n{response}")
            mark_user_as_received(user_id)
            with open(keys_file, 'w') as file:
                file.write('\n'.join(keys) + '\n')

@bot.message_handler(commands=['available_keys'])
def available_keys(message):
    bot.reply_to(message, f"Number of available keys: {len(keys)}")

@bot.message_handler(commands=['add_channel'])
def add_channel(message):
    if message.from_user.id not in allowed_admin_ids:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    
    bot.reply_to(message, f"Current channels:\n" + "\n".join(CHANNELS))
    
    bot.reply_to(message, "Please enter the channel username (e.g., @channel_name):")
    bot.register_next_step_handler(message, process_add_channel)

def process_add_channel(message):
    channel_username = message.text.strip()
    
    if channel_username not in CHANNELS:
        CHANNELS.append(channel_username)
        save_channels(CHANNELS)
        bot.reply_to(message, f"Channel {channel_username} added successfully!")
    else:
        bot.reply_to(message, f"Channel {channel_username} is already in the list.")

    bot.reply_to(message, f"Current channels:\n" + "\n".join(CHANNELS))

@bot.message_handler(commands=['remove_channel'])
def remove_channel(message):
    if message.from_user.id not in allowed_admin_ids:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    
    bot.reply_to(message, f"Current channels:\n" + "\n".join(CHANNELS))
    
    bot.reply_to(message, "Please enter the channel username you want to remove (e.g., @channel_name):")
    bot.register_next_step_handler(message, process_remove_channel)

def process_remove_channel(message):
    channel_username = message.text.strip()
    
    if channel_username in CHANNELS:
        CHANNELS.remove(channel_username)
        save_channels(CHANNELS)
        bot.reply_to(message, f"Channel {channel_username} removed successfully!")
    else:
        bot.reply_to(message, f"Channel {channel_username} was not found in the list.")
    
    bot.reply_to(message, f"Current channels:\n" + "\n".join(CHANNELS))

@bot.message_handler(commands=['set_num_keys'])
def set_num_keys(message):
    if message.from_user.id not in allowed_admin_ids:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    bot.reply_to(message, "Please enter the number of keys you want to set:")
    bot.register_next_step_handler(message, process_set_num_keys)

def process_set_num_keys(message):
    global num_keys_per_user
    try:
        num_keys_per_user = int(message.text.strip())
        bot.reply_to(message, f"Number of keys per user set to {num_keys_per_user}.")
    except ValueError:
        bot.reply_to(message, "Invalid number. Please enter a valid integer.")

def check_waiting_list():
    while True:
        waiting_list = get_waiting_list()
        if waiting_list and len(keys) >= num_keys_per_user:
            user_id = waiting_list.pop(0)
            save_waiting_list(waiting_list)
            send_keys_to_user(user_id)
        time.sleep(2)

def send_keys_to_user(user_id):
    if len(keys) >= num_keys_per_user:
        selected_keys = random.sample(keys, num_keys_per_user)
        for key in selected_keys:
            keys.remove(key)
        response = '\n'.join(selected_keys)
        bot.send_message(user_id, f"Keys are now available! Here are your keys:\n{response}")
        mark_user_as_received(user_id)
        with open(keys_file, 'w') as file:
            file.write('\n'.join(keys))

def radio(message):
    try:
        mess = message.text
    except:
        return bot.send_message(message.chat.id, text='Send text only!')

    mssg = bot.send_message(message.chat.id, text='''<strong>
Preparing...
</strong>''', parse_mode='html')

    done = 0
    bbad = 0
    total_users = 0

    with open('all_users.txt', "r") as seen:
        all_users = seen.readlines()
        total_users = len(all_users)

        for sen in all_users:
            sen = sen.strip()  # Remove trailing newline
            try:
                bot.send_message(chat_id=sen, text=mess)
                done += 1
            except Exception as e:
                bbad += 1
                print(f"Error sending message to {sen}: {e}")

            d1 = types.InlineKeyboardButton(f'Done : {done}', callback_data='d1')
            d2 = types.InlineKeyboardButton(f'Bad : {bbad}', callback_data='d2')
            d0 = types.InlineKeyboardButton(f'{done + bbad} / {total_users}', callback_data='d0')
            d3 = types.InlineKeyboardMarkup()
            d3.add(d2, d1)
            d3.add(d0)

            if (done + bbad) % 10 == 0 or (done + bbad) == total_users:  # Update every 10 messages or at the end
                bot.edit_message_text(chat_id=message.chat.id, message_id=mssg.message_id,
                                      text=f'''<strong>❖ - Sending in progress ...</strong>''',
                                      parse_mode='html', reply_markup=d3)

    bot.send_message(message.chat.id, text=f'''
❖ - Broadcast sent successfully
Total users: {total_users}
Sent successfully to: {done}
Number blocked by bot: {bbad}
''')

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if message.from_user.id not in allowed_admin_ids:
        return bot.send_message(message.chat.id, "You are not authorized to use this command.")
    bot.send_message(message.chat.id, "Please enter the message you want to broadcast:")
    bot.register_next_step_handler(message, radio)

# File monitoring for changes
file_mod_times = {
    used_users_file: 0,
    waiting_list_file: 0,
    all_users_file: 0,
    keys_file: 0,
    channels_file: 0
}

def get_file_mod_time(filepath):
    try:
        return os.path.getmtime(filepath)
    except FileNotFoundError:
        return 0

def monitor_files():
    while True:
        for filepath in file_mod_times.keys():
            current_mod_time = get_file_mod_time(filepath)
            if current_mod_time > file_mod_times[filepath]:
                file_mod_times[filepath] = current_mod_time
                handle_file_change(filepath)
        time.sleep(1)

def handle_file_change(filepath):
    if filepath == used_users_file:
        print(f"{used_users_file} has been updated.")
    elif filepath == waiting_list_file:
        print(f"{waiting_list_file} has been updated.")
    elif filepath == all_users_file:
        print(f"{all_users_file} has been updated.")
    elif filepath == keys_file:
        print(f"{keys_file} has been updated.")
        global keys
        keys = load_keys()
    elif filepath == channels_file:
        print(f"{channels_file} has been updated.")
        global CHANNELS
        CHANNELS = load_channels()

# Start file monitoring in a separate thread
threading.Thread(target=monitor_files, daemon=True).start()

# Start the waiting list checker in a separate thread
threading.Thread(target=check_waiting_list, daemon=True).start()

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(2)