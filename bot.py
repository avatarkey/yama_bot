#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import config
import logging
import telebot
import json
import re
import pickle
import sqlite3
import traceback
import numpy
from telebot import types
from time import sleep
from fuzzywuzzy import process


# ======= Functional variables =======

bot = telebot.TeleBot(config.TOKEN)
BOT_URL = "https://api.telegram.org/bot{}/".format(config.TOKEN)
allowed_ids = config.allowed_ids
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
band_searched = None
band_to_add = None
markup_delete = types.ReplyKeyboardRemove(selective=False)
intr = lambda x1, x2: list(set(x1).intersection(x2))
diff = lambda x1, x2: list(set(x1).difference(x2))


# ======= Bot start =======

@bot.message_handler(commands=['start'])
def send_welcome(message):
	with open('ids.pkl', 'rb') as f:
		id_set = set(pickle.load(f))
		id_set.add(message.chat.id)
	with open('ids.pkl', 'wb') as f:
		pickle.dump(id_set, f)
	conn = sqlite3.connect('yama.db')
	db = conn.cursor()
	db.execute("SELECT * FROM User WHERE user_id=?", 
		(message.chat.id,))
	db_user = db.fetchone()
	db.close()
	conn.close()
	print(db_user)
	if db_user == None:
		markup = types.ReplyKeyboardMarkup()
		male = types.KeyboardButton('Мужской')
		female = types.KeyboardButton('Женский')
		markup.row(male, female)
		msg = bot.send_message(message.chat.id, 
			"Укажите, пожалуйста, ваш пол", 
			reply_markup=markup)
		bot.register_next_step_handler(msg, determine_sex)	
	elif db_user[2] == 1:
		bot.send_message(message.chat.id, "Я уже работаю, господин")
	elif db_user[2] == 2:
		bot.send_message(message.chat.id, "Я уже работаю, госпожа")



def determine_sex(message):
	if message.text == "Мужской":
		try:
			bot.send_message(message.chat.id, 
				"Как вам будет угодно, господин", 
				reply_markup=markup_delete)
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute('INSERT INTO User (user_id, name, sex) VALUES (?,?,?)', 
						(message.chat.id, message.from_user.first_name, 1))
			conn.commit()
			db.close()
			conn.close()
		except:
			print("Была ошибка")
					
	elif message.text == "Женский":
		bot.send_message(message.chat.id, 
			"Как вам будет угодно, госпожа", 
			reply_markup=markup_delete)
		try:
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute('INSERT INTO User (user_id, name, sex) VALUES (?,?,?)', 
				(message.chat.id, message.from_user.first_name, 2))
			conn.commit()
			db.close()
			conn.close()
		except:
			print("Была ошибка")
	else:
		try:
			markup = types.ReplyKeyboardMarkup()
			male = types.KeyboardButton('Мужской')
			female = types.KeyboardButton('Женский')
			markup.row(male, female)
			msg = bot.send_message(message.chat.id, 
				"Пожалуйста, сообщите мне ваш пол", 
				reply_markup=markup)
			bot.register_next_step_handler(msg, determine_sex)
		except:
			print("Была ошибка")			





@bot.message_handler(commands=['help'])
def help_page(message):
	markup = types.ReplyKeyboardRemove(selective=False)
	bot.send_message(message.chat.id, 
		"/help - список команд \n/bands - \
		главное меню бота \n/control - \
		управление базой данных",
		reply_markup=markup)



# ======= Admin panel =======


@bot.message_handler(commands=['gimme_list'])
def send_welcome(message):
	if message.chat.id in allowed_ids:
		with open('ids.pkl', 'rb') as f:
			id_set = set(pickle.load(f))
		bot.send_message(message.chat.id, str(id_set))


@bot.message_handler(commands=['control'])
def control_me(message):
	try:
		if message.chat.id in allowed_ids:
			markup = types.ReplyKeyboardMarkup()
			itembtna = types.KeyboardButton('Список групп')
			itembtnb = types.KeyboardButton('Добавить группу')
			itembtnc = types.KeyboardButton('Отмена')
			markup.row(itembtna, itembtnb)
			markup.row(itembtnc)
			msg = bot.send_message(message.chat.id, 
				"Можно сделать следующее:", 
				reply_markup=markup)
			bot.register_next_step_handler(msg, process_control_choice)
	except Exception as e:
		bot.reply_to(message, str(e))

def process_control_choice(message):
	try:
		if message.text == 'Список групп':			
			bot.send_message(message.chat.id, 
				"На данный момент список групп выглядит так:", 
				reply_markup=markup_delete)
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute("SELECT name FROM Band")
			bands = db.fetchall()
			db.close()
			conn.close()
			bot.send_message(message.chat.id, str(bands))
		elif message.text == 'Добавить группу':
			markup = types.ReplyKeyboardRemove(selective=False)
			msg = bot.send_message(message.chat.id, 
				"Напишите название группы латиницей", 
				reply_markup=markup)
			bot.register_next_step_handler(msg, process_create_band)
		elif message.text == 'Отмена':
			markup = types.ReplyKeyboardRemove(selective=False)
			bot.send_message(message.chat.id, 
				"Как вам будет угодно", reply_markup=markup)

	except Exception as e:
		bot.reply_to(message, str(e))


def process_create_band(message):
	try:
		band = message.text
		band = band.lower()
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		db.execute('UPDATE User SET temp=? WHERE user_id=?', (band, message.chat.id,))
		conn.commit()
		db.close()
		conn.close()
		# if re.match(r'^[a-zA-Z]'):
		markup = types.ReplyKeyboardMarkup()
		itembtna = types.KeyboardButton('Да')
		itembtnv = types.KeyboardButton('Нет')
		markup.row(itembtna, itembtnv)
		msg = bot.send_message(message.chat.id, 
			"Я добавлю "+band+" в список.\nВы уверены?", 
			reply_markup=markup)
		bot.register_next_step_handler(msg, process_add_band)

	except Exception as e:
		bot.reply_to(message, str(e))


def process_add_band(message):
	try:
		if message.text == "Да":
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute('SELECT temp FROM User WHERE user_id=?', (message.chat.id,))
			band = db.fetchone()
			db.execute('INSERT INTO Band(name) VALUES (?)', (band[0],))
			conn.commit()
			db.close()
			conn.close()
			markup = types.ReplyKeyboardMarkup()
			itembtna = types.KeyboardButton('Давай')
			itembtnb = types.KeyboardButton('Лучше потом')
			markup.row(itembtna, itembtnb)
			msg = bot.send_message(message.chat.id, 
				"Группа "+band[0]+" успешно добавлена!\nДавайте добавим к ней одну композицию, которая лучше всего характеризует исполнителя!", 
				reply_markup=markup)
			bot.register_next_step_handler(msg, aftercreate_add_audio)
			
		elif message.text == "Нет":
			markup = types.ReplyKeyboardMarkup()
			itembtna = types.KeyboardButton('Список групп')
			itembtnb = types.KeyboardButton('Добавить группу')
			itembtnc = types.KeyboardButton('Отмена')
			markup.row(itembtna, itembtnb)
			markup.row(itembtnc)
			msg = bot.send_message(message.chat.id, 
				"Возвращаю Вас в главное меню.\nМожно сделать следующее:", 
				reply_markup=markup)
			bot.register_next_step_handler(msg, process_control_choice)

	except Exception as e:
		bot.reply_to(message, str(e))

def aftercreate_add_audio(message):
	if message.text == "Давай":
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		db.execute('SELECT temp FROM User WHERE user_id=?', (message.chat.id,))
		band = db.fetchone()

		db.close()
		conn.close()
		msg = bot.send_message(message.chat.id, "Пожалуйста, загрузите аудио-файл исполнителя "+str(band[0])+"!")
		bot.register_next_step_handler(msg, audio_added)
	elif message.text == "Лучше потом":
		bot.send_message(message.chat.id, "Как вам будет угодно!")
	else:
		pass

def audio_added(message):
	try:
		if message.content_type == 'audio':
			music = message.audio.file_id
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute('SELECT temp FROM User WHERE user_id=?', (message.chat.id,))
			band = db.fetchone()
			db.execute('UPDATE Band SET audio=? WHERE name=?', (music, band[0]))
			conn.commit()
			db.close()
			conn.close()
			bot.send_message(message.chat.id, "Композиция добавлена!")
	except Exception as e:
		bot.reply_to(message, str(e))


# ======= User panel =======


@bot.message_handler(commands=['bands'])
def start_user_menu(message):
	try:
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()	
		db.execute('SELECT name, sex FROM User WHERE name=?', 
			(message.from_user.first_name,))
		user = db.fetchone()
		db.close()
		conn.close()
		if user[1] == 1:
			bot.send_message(message.chat.id, 
				"Здравствуйте, господин "+user[0])
		elif user[1] == 2:
			bot.send_message(message.chat.id, 
				"Здравствуйте, госпожа "+user[0])
		markup = types.ReplyKeyboardMarkup()
		itembtna = types.KeyboardButton('Жанры')
		itembtnb = types.KeyboardButton('Группы')
		markup.row(itembtna, itembtnb)
		msg = bot.send_message(message.chat.id, 
			"Вот что можно сделать", 
			reply_markup=markup)
		
		bot.register_next_step_handler(msg, show_genres)

	except Exception as e:
		bot.reply_to(message, "Простите, возникла ошибка")


def show_genres(message):
	if message.text == 'Жанры':
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()	
		db.execute('SELECT name FROM Tag')
		genres = db.fetchall()
		db.close()
		conn.close()
		bot.send_message(message.chat.id, 
			str(genres), 
			reply_markup=markup_delete)
		
	elif message.text == 'Группы':
		markup = types.ReplyKeyboardMarkup()
		itembtna = types.KeyboardButton('Список избранных')
		itembtnb = types.KeyboardButton('Добавить группу')
		markup.row(itembtna, itembtnb)
		msg = bot.send_message(message.chat.id, 
			"Что вы желаете дальше?", 
			reply_markup=markup)
		bot.register_next_step_handler(msg, bands_control)

def bands_control(message):
	if message.text == 'Список избранных':
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		db.execute('SELECT band_id FROM Like WHERE user_id=?',(message.chat.id,))
		band_ids = []
		for x in db.fetchall():
			band_ids.append(x[0])
		db.execute('SELECT name FROM Band WHERE band_id IN (%s)' % 
			','.join('?'*len(band_ids)), band_ids)
		band_names = []
		for x in db.fetchall():
			band_names.append(x[0])
		db.close()
		conn.close()
		bot.send_message(message.chat.id, str(band_names), reply_markup=markup_delete)
		
	if message.text == 'Добавить группу':
		msg = bot.send_message(message.chat.id, 
			"Введите название группы, которые вы хотите добавить в список избранных, и я попробую найти что-то похожее",
			reply_markup=markup_delete)
		bot.register_next_step_handler(msg, band_search)

def band_search(message):
	band_entered = message.text
	conn = sqlite3.connect('yama.db')
	db = conn.cursor()
	db.execute('SELECT name FROM Band')		
	band_query = process.extractOne(band_entered, db.fetchall())
	db.execute('UPDATE User SET temp=? WHERE user_id=?', (band_query[0][0], message.chat.id,))
	conn.commit()
	db.close()
	conn.close()
	markup = types.ReplyKeyboardMarkup()
	itembtna = types.KeyboardButton('Да')
	itembtnb = types.KeyboardButton('Нет')
	itembtnc = types.KeyboardButton('Отмена')
	markup.row(itembtna, itembtnb, itembtnc)	

	if band_query[1] >= 60:
		msg = bot.send_message(message.chat.id,
			"Кажется, вы имеете в виду "+band_query[0][0]+"?",
			reply_markup=markup)
		bot.register_next_step_handler(msg, band_search_result)
	else:
		msg = bot.send_message(message.chat.id,
			"Ой, я такой группы не знаю. Может быть "+band_query[0][0]+"?",
			reply_markup=markup)
		bot.register_next_step_handler(msg, band_search_result)

def band_search_result(message):
	if message.text == 'Да':
		markup = types.ReplyKeyboardMarkup()
		itembtna = types.KeyboardButton('Список избранных')
		itembtnb = types.KeyboardButton('Добавить группу')
		markup.row(itembtna, itembtnb)				
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		db.execute('SELECT temp FROM User WHERE user_id=?', (message.chat.id,))
		band_searched = db.fetchone()[0]
		db.execute('SELECT band_id, name FROM Band WHERE name=?', (band_searched,))
		band_searched = db.fetchone()
		try:
			db.execute('INSERT INTO Like (user_id, band_id) VALUES (?,?)', 
				(message.chat.id, band_searched[0]))
			conn.commit()
			db.close()
			conn.close()
			bot.send_message(message.chat.id,
				"Группа "+band_searched[1]+" добавлена в ваш список любимых групп",
				reply_markup=markup_delete)
			sleep(1)
			msg = bot.send_message(message.chat.id,
				"Возвращаю вас в предыдущее меню",
				reply_markup=markup)
			bot.register_next_step_handler(msg, bands_control)		
		except Exception as e:
			db.close()
			conn.close()
			msg = bot.send_message(message.chat.id, 
				"Такая группа уже добавлена в ваше избранное\nВозвращаю вас в предыдущее меню", 
				reply_markup=markup)
			bot.register_next_step_handler(msg, bands_control)

	elif message.text == 'Нет':
		msg = bot.send_message(message.chat.id, 
			"Тогда введите название еще раз, но по-другому. Я изо всех сил постараюсь найти эту группу!",
			reply_markup=markup_delete)
		bot.register_next_step_handler(msg, band_search)

	elif message.text == 'Отмена':
		bot.send_message(message.chat.id, 
			"Закрываю меню", 
			reply_markup=markup_delete)

# ======= Contribution =======

@bot.message_handler(commands=['con'])
def contribution_start(message):
	markup = types.ReplyKeyboardMarkup()
	itembtna = types.KeyboardButton('Жанры')
	itembtnb = types.KeyboardButton('Группы')
	itembtnc = types.KeyboardButton('Отмена')
	markup.row(itembtna, itembtnb)
	markup.row(itembtnc)
	msg = bot.send_message(message.chat.id, "Спасибо за желание помочь. Благодаря вашей помощи я смогу делать более точные рекомендации для вас и других пользователей. \nЧем бы вы хотели помочь?", reply_markup=markup)
	bot.register_next_step_handler(msg, contribution_options)

def contribution_options(message):
	if message.text == 'Жанры':		
		your_bands = []
		genres = []
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		for row in conn.execute('SELECT band_id FROM Like WHERE user_id=?', (message.chat.id,)):
			your_bands.append(row[0])

		# Сделать сообщение, если групп нет
		keyboard = types.InlineKeyboardMarkup()
		for x in your_bands:
			db.execute('SELECT genre_id FROM Genre WHERE band_id=?', (x,))
			if db.fetchone() == None:
				db.execute('SELECT name FROM Band WHERE band_id=?', (x,))
				band = db.fetchone()[0]

				callback_button = types.InlineKeyboardButton(text=band, callback_data="genre."+str(x))
				keyboard.add(callback_button)
		bot.send_message(message.chat.id, "Я нашла исполнителей без жанров", reply_markup=keyboard)			
		db.close()
		conn.close()
	elif message.text == 'Группы':		
		your_bands = []
		bands = []
		conn = sqlite3.connect('yama.db')
		for row in conn.execute('SELECT band_id FROM Like WHERE user_id=?', (message.chat.id,)):
			your_bands.append(row[0])
		for row in conn.execute('SELECT * FROM Band WHERE band_id IN (%s)' % 
			','.join('?'*len(your_bands)), your_bands):
			bands.append(row)	
		your_bands = []
		conn.close()

		for band in bands:
			if len(your_bands) <= 4:
				if band[2] == None:
					your_bands.append(band)
		keyboard = types.InlineKeyboardMarkup()


		for band in your_bands:
			callback_button = types.InlineKeyboardButton(text=band[1], callback_data="music."+band[1])
			keyboard.add(callback_button)
		bot.send_message(message.chat.id, "Вот несколько групп, у которых в базе данных нет песни.\nВыберите одну из них.", reply_markup=keyboard)		
		pass
	elif message.text == 'Отмена':
		pass
	else:
		pass

def contribution_upload(message):
	if message.audio:
		music = message.audio.file_id
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		db.execute('SELECT temp FROM User WHERE user_id=?', (message.chat.id,))
		band = db.fetchone()[0]
		conn.execute('UPDATE Band SET audio=? WHERE name=?', (music, band))
		conn.execute('UPDATE User SET temp=? WHERE user_id=?', (None, message.chat.id))
		conn.commit()
		db.close()
		conn.close()		
		bot.send_message(message.chat.id, "Спасибо, композиция загружена",reply_markup=markup_delete)
	else:
		bot.send_message(message.chat.id, "Нет аудио",reply_markup=markup_delete)


def cont_genre_search(message):
	genre = message.text
	conn = sqlite3.connect('yama.db')
	db = conn.cursor()
	db.execute('SELECT name FROM Tag')
	genre_query = process.extractOne(genre, db.fetchall())
	db.execute('UPDATE User SET temp_genre=? WHERE user_id=?', (genre_query[0][0], message.chat.id,))
	conn.commit()
	db.close()
	conn.close()
	markup = types.ReplyKeyboardMarkup()
	itembtna = types.KeyboardButton('Да')
	itembtnb = types.KeyboardButton('Нет')
	itembtnc = types.KeyboardButton('Отмена')
	markup.row(itembtna, itembtnb, itembtnc)	

	if genre_query[1] >= 60:
		msg = bot.send_message(message.chat.id,
			"Вы имеете в виду жанр "+genre_query[0][0]+"?",
			reply_markup=markup)
		bot.register_next_step_handler(msg, cont_genre_search_result)
	else:
		msg = bot.send_message(message.chat.id,
			"Я не знаю такого жанра. Может быть "+genre_query[0][0]+"?",
			reply_markup=markup)
		bot.register_next_step_handler(msg, cont_genre_search_result)

def cont_genre_search_result(message):
	if message.text == 'Да':			
		conn = sqlite3.connect('yama.db')
		db = conn.cursor()
		db.execute('SELECT temp_genre FROM User WHERE user_id=?', (message.chat.id,))
		genre = db.fetchone()[0]
		db.execute('SELECT genre_id FROM Tag WHERE name=?', (genre,))
		genre_id = db.fetchone()[0]
		db.execute('SELECT temp FROM User WHERE user_id=?', (message.chat.id,))
		band_id = db.fetchone()[0]
		print(genre_id)
		print(band_id)
		try:
			db.execute('INSERT INTO Genre (band_id, genre_id) VALUES (?,?)', 
				(band_id, genre_id))
			conn.commit()
			db.close()
			conn.close()
			bot.send_message(message.chat.id,
				"Спасибо, жанр был добавлен",
				reply_markup=markup_delete)
		except Exception as e:
			db.close()
			conn.close()
			msg = bot.send_message(message.chat.id, 
				"Что-то пошло не так, попробуйте снова", 
				reply_markup=markup_delete)

	elif message.text == 'Нет':
		msg = bot.send_message(message.chat.id, 
			"Введите название еще раз. Я изо всех сил постараюсь найти этот жанр!",
			reply_markup=markup_delete)
		bot.register_next_step_handler(msg, cont_genre_search)

	elif message.text == 'Отмена':
		bot.send_message(message.chat.id, 
			"Закрываю меню", 
			reply_markup=markup_delete)




@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
	if call.message:
		if "music." in call.data:
			bot.edit_message_text(
				chat_id=call.message.chat.id,
				message_id=call.message.message_id,
				text=call.message.text,
				parse_mode="Markdown")
			band = str(call.data).replace("music.", "")
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute('SELECT audio FROM Band WHERE name=?', (band,))
			if db.fetchone()[0] == None:
				conn.execute('UPDATE User SET temp=? WHERE user_id=?', (band, call.message.chat.id,))
				conn.commit()
				db.close()
				conn.close()
				msg = bot.send_message(call.message.chat.id, "Пожалуйста, отправьте мне одну композицию "+band,reply_markup=markup_delete)
				bot.register_next_step_handler(msg, contribution_upload)
			else:
				db.close()
				conn.close()

		elif "genre." in call.data:
			bot.edit_message_text(
				chat_id=call.message.chat.id,
				message_id=call.message.message_id,
				text=call.message.text,
				parse_mode="Markdown")
			band_id = str(call.data).replace("genre.", "")
			conn = sqlite3.connect('yama.db')
			db = conn.cursor()
			db.execute('SELECT genre_id FROM Genre WHERE band_id=?', (band_id,))
			if db.fetchone() == None:
				conn.execute('UPDATE User SET temp=? WHERE user_id=?', (band_id, call.message.chat.id,))

				conn.commit()
				msg = bot.send_message(call.message.chat.id, 
					"Введите примерное название музыкального жанра для этой группы",
					reply_markup=markup_delete)
				bot.register_next_step_handler(msg, cont_genre_search)
			else:
				bot.send_message(call.message.chat.id, "Извините, для группы уже задан жанр", reply_markup=markup_delete)




# ======= Store music =======

# @bot.message_handler(content_types=['audio'])
# def store_music(message):
# 	if message.chat.id in config.allowed_ids:
# 		music = message.audio.file_id
# 		if message.audio.mime_type == "audio/mpeg3":
# 			bot.send_message(message.chat.id, "Это мп3")
# 		bot.send_message(message.chat.id, str(music))


# ======= Recommender =======



# Надо дописать возможность добавить и послушать
@bot.message_handler(commands=['rec'])
def start_recommender(message):
	# populate dictionary
	all_likes = {}
	all_bands = {}
	conn = sqlite3.connect('yama.db')
	db = conn.cursor()
	db.execute('SELECT * FROM Like')
	for k, v in db.fetchall():
		all_likes.setdefault(k, []).append(v)
	db.execute('SELECT band_id FROM Band')
	for x in db.fetchall():
		all_bands.update({x[0]:float(0)})
	my_likes = all_likes[message.chat.id]
	all_likes_dict = all_likes
	all_likes = list(all_likes.items())
	usrs = []
	usrs_norm_dict = {}
	for x in all_likes:
		if x[0] == message.chat.id:
			continue
		raw_coeff = (len(intr(my_likes, x[1])) / (len(my_likes) + len(x[1]) - len(intr(my_likes, x[1]))))
		coeff = float(format(raw_coeff, '.3f'))
		usrs.append(coeff)
		usrs_norm_dict.update({x[0] : float(coeff)})
	usrs_avg = float(format(numpy.mean(usrs), '.3f'))

	for k, v in usrs_norm_dict.items():
		usr_value = v - usrs_avg
		usrs_norm_dict[k] = float(format(usr_value, '.3f'))
	usrs_norm_dict = dict((k,v) for k,v in usrs_norm_dict.items() if v>0)

	for user in usrs_norm_dict:
		for band in diff(all_likes_dict[user], my_likes):
			score_value = all_bands[band] + usrs_norm_dict[user]
			all_bands[band] = float(format(score_value, '.3f'))
	recommended_band = max(all_bands, key=all_bands.get)
	super_string = 'MY LIKES \n'+str(my_likes)+'\nALL LIKES \n'+str(all_likes)+'\nUSERS NORM DICT \n'+str(usrs_norm_dict)+'\nUSERS\n'+str(usrs)+'\nUSERS AVG \n'+str(usrs_avg)+'\nALL BANDS \n'+str(all_bands)

	conn = sqlite3.connect('yama.db')
	db = conn.cursor()	
	db.execute('SELECT name, audio FROM Band WHERE band_id=?', (recommended_band,))
	recommended_band = db.fetchone()
	db.close()
	conn.close()
	bot.send_message(message.chat.id, "Узнав что слушают люди с похожими вкусами, я рекомендую вам послушать "+str(recommended_band[0]))
	if recommended_band[1] != None:
		bot.send_audio(message.chat.id, recommended_band[1])



if __name__ == '__main__':
	bot.polling(none_stop=True)




