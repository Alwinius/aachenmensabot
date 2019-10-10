#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
from mensa_db import Base
from mensa_db import User
from meals import get_menu
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import telegram
from telegram import InlineKeyboardButton
from telegram.error import ChatMigrated
from telegram.error import NetworkError
from telegram.error import TimedOut
from telegram.error import Unauthorized
from telegram.error import BadRequest

engine = create_engine('sqlite:///mensausers.sqlite')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
config = configparser.ConfigParser()
config.read('config.ini')
bot = telegram.Bot(token=config['DEFAULT']['BotToken'])


def send(chat_id, message_id, message, reply_markup):	
    try:
        if message_id is None or message_id == 0:
            print("Sending new message")
            rep = bot.sendMessage(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            session = DBSession()
            user = session.query(User).filter(User.id == chat_id).first()
            user.message_id = rep.message_id
            session.commit()
            session.close()
            return True
        else:
            print("Updating message")
            bot.editMessageText(chat_id=chat_id, text=message, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            return True
    except (Unauthorized, BadRequest):
        session = DBSession()
        user = session.query(User).filter(User.id == chat_id).first()
        user.notifications = 0
        bot.sendMessage(chat_id=config["DEFAULT"]["AdminID"], text="Error sending meals to "+user.first_name)
        session.commit()
        session.close()
        return True
    except (TimedOut, NetworkError):
        import time
        time.sleep(5) # delays for 5 seconds
        return send(chat_id, message_id, message, reply_markup)
    except ChatMigrated as e:
        session = DBSession()
        user = session.query(User).filter(User.id == chat_id).first()
        user.id = e.new_chat_id
        session.commit()
        session.close()
        return True
    else:
        return False


names = dict([("academica", "Academica"), ("ahornstrasse", "Ahornstr."), ("bayernallee", "Bayernallee"),
              ("goethestrasse", "Goethestr."), ("eupener-strasse", "Eupener Str."),
              ("suedpark", "Südpark"), ("vita", "Vita"), ("juelich", "Jülich")])
menus = {}
for (mensa_id, mensa_name) in names.items():
    menus[mensa_id] = get_menu(mensa_id, mensa_name)
    print("getting plan for mensa " + mensa_name)

button_list = [[InlineKeyboardButton("Auto-Update deaktivieren", callback_data="5$0")],
                [InlineKeyboardButton("Mensa Academica", callback_data="academica"),
                InlineKeyboardButton("Mensa Ahornstr.", callback_data="ahornstrasse")],
               [InlineKeyboardButton("Mensa Bayernallee", callback_data="bayernallee"),
                InlineKeyboardButton("Mensa Goethestr.", callback_data="goethestrasse")],
               [InlineKeyboardButton("Mensa Eupener Str.", callback_data="eupener-strasse"),
                InlineKeyboardButton("Mensa Südpark", callback_data="suedpark")],
               [InlineKeyboardButton("Mensa Vita", callback_data="vita"),
                InlineKeyboardButton("Mensa Jülich", callback_data="juelich")]
               ]

reply_markup = telegram.InlineKeyboardMarkup(button_list)	

session = DBSession()
entries = session.query(User).filter(User.notifications != 0)

for user in entries:
    user.counter += 1
    session.commit()
    print("Sending plan to " + user.first_name)
    if menus[user.notifications].get_date() != "":
        msg = "*Mensa " + menus[user.notifications].mensa + " am " + menus[user.notifications].date + "*\n" + menus[user.notifications].get_meals_string(user.filter_mode)
    else:
        msg = "Die Mensa " + menus[user.notifications].mensa + " ist heute geschlossen."

    send(user.id, user.message_id, msg, reply_markup)
session.close()
