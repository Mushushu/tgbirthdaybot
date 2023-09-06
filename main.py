import telebot
from telebot import types
import sqlite3
import threading
import time
import re
import random

import config

bot = telebot.TeleBot(config.TOKEN)
print("BOT STARTED SUCCESSFULLY\a\n")

conn = sqlite3.connect("data/botbase.db", check_same_thread=False)
cursor = conn.cursor()

@bot.message_handler(commands=['testgif'])
def testgif(message):
	bot.send_animation(message.chat.id, random.choice(config.birthdaygifs))
	bot.send_message(message.chat.id, random.choice(config.birthdaytext))
	#bot.reply_to(message, 'https://media.giphy.com/media/5K3V6RDWry8Cc/giphy.gif')

#Start command
@bot.message_handler(commands=['start'])
def start(message):
	#ANIME GIF
	hellogif = open('media/hellogif.mp4', 'rb')
	#SEND GIF & MESSAGE
	bot.send_animation(message.chat.id, hellogif)
	bot.reply_to(message, "<b>Привіт, <i>{0.first_name}</i>! \nЯ - <i>{1.first_name}</i>. Бот, створений для задовільнення особистих потреб одного збоченого покидька.😊 \nДля отримання розширеної інформації скористайся командою 👉🏿 <i>/help</i></b>".format(message.from_user, bot.get_me()), parse_mode='html')

#HELP
@bot.message_handler(commands=['help'])
def help(message):
#	whatsti = open('media/what.webp', 'rb')
#	bot.send_sticker(message.chat.id, whatsti)
	bot.reply_to(message, config.commandslist + "<i>\n\nНа даний момент бот знаходиться у розробці</i>", parse_mode='html')

#GLOBAL VARIABLES
#to add user to the db
current_name = None
current_date = None
#to check message author
message_author = None
#list to delete all previous INLINEKEYBOARDMARKUP
previous_message_ids = []

#COMMAND TO ADD NEW REMINDER & START THE CHAIN
@bot.message_handler(commands=['new'])
def new_birthday(message):

	#bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)

	global message_author
	message_author = message.from_user.id

	#INLINE BUTTON to cancel the operation
	markup = types.InlineKeyboardMarkup()
	cancel = types.InlineKeyboardButton('✕ Cancel', callback_data='CANCEL')
	markup.add(cancel)

	botreply = bot.reply_to(message, "<b>Введіть ім'я</b> \n\n<i>для коректної роботи команд рекомендовано вводити дані у відповідь на повідомлення бота</i>", parse_mode='html', reply_markup=markup)
	
	#add id of current message to the list
	previous_message_ids.append(botreply.message_id)

	bot.register_next_step_handler(botreply, get_name)
	

#GET NAME FUNCTION
def get_name(message):
	try:
		#if message.reply_to_message is not None:
		if message.from_user.id == message_author:
			#NAME != COMMAND
			if not message.text.startswith('/'):
				#asking a name from user
				global current_name
				current_name = message.text

				markup = types.InlineKeyboardMarkup()
				cancel = types.InlineKeyboardButton('✕ Cancel', callback_data='CANCEL')
				markup.add(cancel)

				botreply = bot.reply_to(message, "Введіть дату у форматі \n• <b>YEAR-MONTH-DAY</b>\n• <b>РІК-МІСЯЦЬ-ДЕНЬ</b> \n\n<i>для коректної роботи команд рекомендовано вводити дані у відповідь на повідомлення бота</i>", parse_mode='html', reply_markup=markup)
				
				#delete markups
				for message_id in previous_message_ids:
					bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
				#CLEAR LIST
				previous_message_ids.clear()
				#add id of current message to the list
				previous_message_ids.append(botreply.message_id)

				bot.register_next_step_handler(botreply, get_date)
			else:
				bot.reply_to(message, f"<b>✕ Операцію скасовано</b>\n\n<i>Ім'я не може бути командою</i>",  parse_mode='html')
				#delete markups
				for message_id in previous_message_ids:
					bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
				#CLEAR LIST
				previous_message_ids.clear()
				#STOP THE CHAIN
				bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
		elif message.from_user.id != message_author or message.text.startswith('/'):
			bot.send_animation(message.chat.id, random.choice(config.nogifs))
			error_reply = bot.reply_to(message, f"<b>✕ Запущений ланцюг команд ще не завершений</b>",  parse_mode='html')
			bot.register_next_step_handler(error_reply, get_name)
	except Exception as e:
		print(e)

#GET BIRTH DATE FUNCTION 
def get_date(message):
	if message.from_user.id == message_author:
		#REGULAR EXPRESION

		#YEAR-MONTH-DAY
		date_pattern = r"\d{4}-\d{2}-\d{2}"
		
		#WE NEED TO CHECK IF INPUT IS CORRECT
		if re.match(date_pattern, message.text):
			#REMEMBER INPUTED DATA
			global current_date
			current_date = message.text

			#CHAT ID
			user_id = message.chat.id
			
			try:
				#SQL CODE
				with conn:
					#SELECT ALL CHATS FROM DB
					cursor.execute(f"SELECT * FROM user WHERE id={user_id}")
					#IF CHAT DOES NOT EXIST
					if not cursor.fetchall():
						#ADD IT
						cursor.execute(f"INSERT INTO user (id) VALUES ({user_id}) ")

					cursor.execute(f"INSERT INTO birthday_reminder (user_id, name, date, reminder) VALUES ({user_id}, \"{current_name}\", \"{current_date}\", {0})")
			except Exception as e:
				print(e)
			
			#IF SUCCESS
			bot.reply_to(message, f"✓ Користувача \"<b>{current_name}</b>\" Додано до бази ",  parse_mode='html')

			#STOP THE CHAIN
			bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
		else:
			bot.reply_to(message, "<b>✕ Операцію скасовано</b>\n\n<b>ДАНІ ВВЕДЕНО НЕКОРЕКТНО</b>\n\nДату потрібно вносити у форматі \n• <b>YEAR-MONTH-DAY</b>\n• <b>РІК-МІСЯЦЬ-ДЕНЬ</b> \n\n<i>для коректної роботи команд рекомендовано вводити дані у відповідь на повідомлення бота</i>",  parse_mode='html')
		
		#delete markups
		for message_id in previous_message_ids:
			bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=message_id, reply_markup=None)
		#CLEAR LIST
		previous_message_ids.clear()
	elif message.from_user.id != message_author or message.text.startswith('/'):
		bot.send_animation(message.chat.id, random.choice(config.nogifs))
		error_reply = bot.reply_to(message, f"<b>✕ Запущений ланцюг команд ще не завершений</b>",  parse_mode='html')
		bot.register_next_step_handler(error_reply, get_date)

#CANCEL FUNCTION to end the chain
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
	if call.message:
		if call.data == 'CANCEL':
			if call.from_user.id == message_author:
				bot.reply_to(call.message, text='<b>✕ Операцію скасовано</b>',  parse_mode='html')
				try:
					#delete markups
					for message_id in previous_message_ids:
						bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=message_id, reply_markup=None)
					#CLEAR LIST
					previous_message_ids.clear()
				except Exception as e:
					print(e)

				bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
			else:
				bot.answer_callback_query(call.id, show_alert=False, text="✕ Ви не можете відповісти!")

bot.enable_save_next_step_handlers(delay=2)

bot.load_next_step_handlers()

def do_reminders():
	while True:
		cursor.execute("SELECT * FROM birthday_reminder WHERE strftime('%d', date) = strftime('%d', 'now') AND strftime('%m', date) = strftime('%m', 'now') AND reminder = 0")

		rows = cursor.fetchall()
		for row in rows:
			row_id = row[0]
			name = row[2]
			user_id = row[4]

			#REMIND ABOUT BIRTHDAYS
			bot.send_message(chat_id=user_id, text=f"Сьогодні День народження в 👉🏿 {name}!")
			bot.send_animation(chat_id=user_id, animation=random.choice(config.nogifs))
			bot.send_message(chat_id=user_id, text=random.choice(config.birthdaytext))

			cursor.execute(f"UPDATE birthday_reminder SET reminder = {1} WHERE id = {row_id}")
			conn.commit()

		#sleep for one day
		time.sleep(24 * 60 * 60)
		#time.sleep(10)
		print("ONE DAY GONE")

		cursor.execute(f"SELECT * FROM birthday_reminder WHERE reminder = 1")

		rows = cursor.fetchall()
		for row in rows:
			row_id = row[0]
			name = row[2]
			user_id = row[4]

			cursor.execute(f"UPDATE birthday_reminder SET reminder = {0} WHERE id = {row_id}")
			conn.commit()

#NEW THREAD
threading.Thread(target=do_reminders).start()

#STARTING
bot.infinity_polling()
#bot.polling(none_stop=True)


#OLD FUNCTIONS (FROM 2022)

''' IT WORKS
#ECHO
@bot.message_handler(content_types=['text'])
def send_echo(message):
	bot.send_message(message.chat.id, message.text)
'''

'''
#REPLY (IN PROGRESS)
@bot.message_handler()
def botinsult(message):
	bangif = open('media/bangif.mp4', 'rb')
	gangstgif = open('media/gangstgif.mp4', 'rb')
	if message.text == 'бот':
		bot.send_animation(message.chat.id, gangstgif)
		bot.reply_to(message, "<b>Я 👉🏿/help</b>", parse_mode='html')
	elif message.text == 'бан':
		bot.send_animation(message.chat.id, bangif)
		bot.reply_to(message, "<b>F!</b>", parse_mode='html')
'''
