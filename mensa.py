#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import configparser
import bs4
import logging
from re import match
from mensa_db import Base
from mensa_db import User
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import telegram
from telegram import InlineKeyboardButton
from telegram.error import ChatMigrated
from telegram.error import TimedOut
from telegram.error import Unauthorized
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

config = configparser.ConfigParser()
config.read('config.ini')

engine = create_engine('sqlite:///mensausers.sqlite')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
button_list = [[InlineKeyboardButton("Mensa Academica", callback_data="academica"),
                InlineKeyboardButton("Mensa Ahornstr.", callback_data="ahornstrasse")],
               [InlineKeyboardButton("Mensa Bayernallee", callback_data="bayernallee"),
                InlineKeyboardButton("Mensa Goethestr.", callback_data="goethestrasse")],
               [InlineKeyboardButton("Mensa Eupener Str.", callback_data="eupener-strasse"),
                InlineKeyboardButton("Mensa Südpark", callback_data="suedpark")],
               [InlineKeyboardButton("Mensa Vita", callback_data="vita"),
                InlineKeyboardButton("Mensa Jülich", callback_data="juelich")]
               ]
names = dict([("academica", "Academica"), ("ahornstrasse", "Ahornstr."), ("bayernallee", "Bayernallee"),
              ("goethestrasse", "Goethestr."), ("eupener-strasse", "Eupener Str."),
              ("suedpark", "Südpark"), ("vita", "Vita"), ("juelich", "Jülich")])


def getplan(mensa):
    r = requests.get("https://www.studierendenwerk-aachen.de/speiseplaene/"+mensa+"-w.html")
    soup = BeautifulSoup(r.content, "lxml")
    today_meals = soup.select(".active-panel .menue-desc")
    message = ""
    for meal in today_meals:
        mealname = meal.contents[0]
        cleaned_mealname = "".join([t for t in mealname.contents if type(t) == bs4.element.NavigableString])
        cleaned_mealname = " ".join(cleaned_mealname.split()) + " "
        # now get background info
        for img in meal.find_all("image", recursive=True):
            url = img.get("src")
            if url == "resources/images/inhalt/Schwein.png":
                cleaned_mealname += "🐷"
            elif url == "resources/images/inhalt/Geflügel.png":
                cleaned_mealname += "🐤"
            elif url == "resources/images/inhalt/Rind.png":
                cleaned_mealname += "🐄"
            elif url == "resources/images/inhalt/vegan.png":
                cleaned_mealname += "🥑"
            elif url == "resources/images/inhalt/OLV.png":
                cleaned_mealname += "🥕"
        message += cleaned_mealname + "\n"

    message += "\n🥑 = vegan, 🥕 = vegetarisch\n🐷 = Schwein, 🐄 = Rind\n🐤 = Vogel"
    return message


def send(bot, chat_id, message_id, message, reply_markup):
    try:
        if message_id is None or message_id == 0:
            rep = bot.sendMessage(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            session = DBSession()
            user = session.query(User).filter(User.id == chat_id).first()
            user.message_id = rep.message_id
            session.commit()
            session.close()
            return True
        else:
            rep = bot.editMessageText(chat_id=chat_id, text=message, message_id=message_id, reply_markup=reply_markup, parse_mode=telegram.ParseMode.MARKDOWN)
            session = DBSession()
            user = session.query(User).filter(User.id == chat_id).first()
            user.message_id = rep.message_id
            session.commit()
            session.close()
            return True
    except (Unauthorized, BadRequest):
        session = DBSession()
        user = session.query(User).filter(User.id == chat_id).first()
        user.notifications = -1
        session.commit()
        session.close()
        return True
    except TimedOut:
        import time
        time.sleep(50)  # delays for 5 seconds
        return send(bot, chat_id, message_id, message, reply_markup)
    except ChatMigrated as e:
        session = DBSession()
        user = session.query(User).filter(User.id == chat_id).first()
        user.id = e.new_chat_id
        session.commit()
        session.close()
        return True
    else:
        return False


def checkuser(sel, update):
    session = DBSession()
    try:
        chat = update.message.chat
    except AttributeError:
        chat = update.callback_query.message.chat
    entry = session.query(User).filter(User.id == chat.id).first()
    if not entry:
        # create entry
        new_user = User(id=chat.id, first_name=chat.first_name, last_name=chat.last_name, username=chat.username,
                        title=chat.title, notifications=0, current_selection="0", counter=0)
        session.add(new_user)
        session.commit()
        session.close()
        return [0, 0]
    else:
        entry.current_selection = sel if sel != 0 else entry.current_selection
        presel = entry.current_selection
        entry.counter += 1
        noti = entry.notifications
        session.commit()
        session.close()
        return [noti, presel]


def changenotifications(update, sel, task):
    session = DBSession()
    entry = session.query(User).filter(User.id == update.callback_query.message.chat.id).first()
    if task == "1":
        entry.notifications = sel
        session.commit()
        session.close()
        return True
    else:
        entry.notifications = 0
        session.commit()
        session.close()
        return False


def start(bot, update):
    checkuser(0, update)
    reply_markup = telegram.InlineKeyboardMarkup(button_list)
    send(bot, update.message.chat_id, None,
         "Bitte über das Menü eine Mensa wählen. Informationen über diesen Bot gibt's hier /about.", reply_markup)


def about(bot, update):
    checkuser(0, update)
    reply_markup = telegram.InlineKeyboardMarkup(button_list)
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="Dieser Bot wurde erstellt von @Alwinius. Der Quellcode ist unter "
                         "https://github.com/Alwinius/aachenmensabot verfügbar.\nWeitere interessante Bots: \n - "
                         "@tummoodlebot\n - @mydealz_bot\n - @tumroomsbot\n - @tummensabot",
                    reply_markup=reply_markup)


def AllInline(bot, update):
    args = update.callback_query.data.split("$")
    if len(args[0]) > 4:
        # Speiseplan anzeigen
        user = checkuser(args[0], update)
        msg = getplan(args[0])
        if len(user[0]) < 2 or user[0] != args[0]:
            custom_keyboard = [[InlineKeyboardButton("Auto-Update aktivieren", callback_data="5$1")]] + button_list
        else:
            custom_keyboard = [[InlineKeyboardButton("Auto-Update deaktivieren", callback_data="5$0")]] + button_list
        reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
        send(bot, update.callback_query.message.chat.id, update.callback_query.message.message_id,
             "*Mensa " + names[args[0]] + "*\n " + msg, reply_markup)
    elif int(args[0]) == 5 and len(args) > 1:
        # Benachrichtigungen ändern
        user = checkuser(0, update)
        if changenotifications(update, user[1], args[1]):
            custom_keyboard = [[InlineKeyboardButton("Auto-Update deaktivieren", callback_data="5$0")]] + button_list
            reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
            send(bot, update.callback_query.message.chat.id, update.callback_query.message.message_id,
                 "Auto-Update aktiviert für Mensa " + names[str(user[1])], reply_markup)
        else:
            custom_keyboard = [[InlineKeyboardButton("Auto-Update aktivieren", callback_data="5$1")]] + button_list
            reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
            send(bot, update.callback_query.message.chat.id, update.callback_query.message.message_id,
                 "Auto-Update deaktiviert", reply_markup)
    else:
        reply_markup = telegram.InlineKeyboardMarkup(button_list)
        send(bot, update.callback_query.message.chat.id, update.callback_query.message.message_id,
             "Kommando nicht erkannt", reply_markup)
        bot.sendMessage(text="Inlinekommando nicht erkannt.\n\nData: " + update.callback_query.data + "\n User: " + str(
            update.callback_query.message.chat), chat_id=config['DEFAULT']['AdminId'])


updater = Updater(token=config['DEFAULT']['BotToken'])
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
about_handler = CommandHandler('about', about)
dispatcher.add_handler(about_handler)
inlinehandler = CallbackQueryHandler(AllInline)
dispatcher.add_handler(inlinehandler)

fallbackhandler = MessageHandler(Filters.all, start)
dispatcher.add_handler(fallbackhandler)

updater.start_webhook(listen='localhost', port=4216, webhook_url=config['DEFAULT']['WebhookUrl'])
updater.bot.set_webhook(config['DEFAULT']['WebHookUrl'])
updater.idle()
updater.stop()
