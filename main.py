import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytz
TOKEN = '6854903171:AAGoQ5C2FM-YQpuaFZGZxxeGDMlAXgzhIg8'
bot = telebot.TeleBot(TOKEN)
GSPREAD_JSON = 'credentials.json'
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(GSPREAD_JSON, SCOPE)
GSHEET_NAME = 'Biolarisbotusers'
user_data = {}
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_data[user_id]['start_sent_time'] = datetime.now()

    if user_id not in user_data:
        user_data[user_id] = {'start_count': 0}
        user_data[user_id]['start_count'] += 1
    username = message.from_user.username
    user_data[user_id]['username'] = username if username else "Username yo'q"

    bot.send_message(user_id, "Assalomu alaykum! Iltimos ismingizni kiriting:")
    bot.register_next_step_handler(message, handle_name)
    elapsed_time = datetime.now() - user_data[user_id].get('start_sent_time', datetime.now())
    if elapsed_time > timedelta(minutes=1):
        send_all_information(user_id)
def handle_name(message):
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item = types.KeyboardButton("Kontaktni ulashish", request_contact=True)
    markup.add(item)
    bot.send_message(user_id, "Kontaktingizni yuboring:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_contact)
def handle_contact(message):
    user_id = message.from_user.id
    if message.contact:
        user_data[user_id]['phone'] = message.contact.phone_number
        bot.send_message(user_id, "Faylni olish uchun pastdagi tugmani bosing👇:",
                         reply_markup=create_file_button())
    else:
        bot.send_message(user_id, "Iltimos kontaktni ulashish tugmasini bosing.")
        return
def create_file_button():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item = types.KeyboardButton("📥 Yuklab olish", request_location=False)
    markup.add(item)
    return markup
@bot.message_handler(func=lambda message: message.text == "📥 Yuklab olish")
def handle_file(message):
    user_id = message.from_user.id
    user_data[user_id]['file_sent'] = 1
    user_data[user_id]['file_sent_time'] = datetime.now()
    send_all_information(user_id)
    remove_file_button(user_id)
    with open('file.pdf', 'rb') as f:
        bot.send_document(user_id, f)
    bot.send_message(user_id, "Qiziqish bildirganingiz uchun rahmat🙂")
def remove_file_button(user_id):
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(user_id, "Fayl yuborildi!", reply_markup=markup)
def add_to_spreadsheet(user_id):
    gc = gspread.authorize(CREDENTIALS)
    spreadsheet = gc.open(GSHEET_NAME)
    data_sheet = spreadsheet.sheet1
    user_rows = data_sheet.col_values(2)
    if str(user_id) in user_rows:
        user_index = user_rows.index(str(user_id)) + 1
        existing_row = data_sheet.row_values(user_index)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        name = user_data[user_id].get('name', '')
        username = user_data[user_id].get('username', '')
        phone = user_data[user_id].get('phone', '')
        file_sent = str(user_data[user_id].get('file_sent', 0))
        existing_row[0] = str(user_id)
        existing_row[1] = timestamp
        existing_row[2] = name
        existing_row[3] = username
        existing_row[4] = phone
        existing_row[5] = file_sent
        data_sheet.update(str(user_index), existing_row)
        data_sheet.format('B:B', {'numberFormat': {'type': 'DATE_TIME'}})
    else:
        tz = pytz.timezone('Asia/Tashkent')
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        name = user_data[user_id].get('name', '')
        username = user_data[user_id].get('username', '')
        phone = user_data[user_id].get('phone', '')
        file_sent = str(user_data[user_id].get('file_sent', 0))
        new_row = [str(user_id), timestamp, name, username, phone, file_sent]
        data_sheet.append_row(new_row)
        data_sheet.format('B:B', {'numberFormat': {'type': 'DATE_TIME'}})
def send_all_information(user_id):
    add_to_spreadsheet(user_id)
    del user_data[user_id]
bot.polling(none_stop=True)
