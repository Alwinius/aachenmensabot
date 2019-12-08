#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# created by Alwin Ebermann (alwin@alwin.net.au)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

button_list = [[InlineKeyboardButton("Mensa Academica", callback_data="academica"),
                InlineKeyboardButton("Mensa Ahornstr.", callback_data="ahornstrasse")],
               [InlineKeyboardButton("Mensa Bayernallee", callback_data="bayernallee"),
                InlineKeyboardButton("Mensa Goethestr.", callback_data="goethestrasse")],
               [InlineKeyboardButton("Mensa Eupener Str.", callback_data="eupener-strasse"),
                InlineKeyboardButton("Mensa Südpark", callback_data="suedpark")],
               [InlineKeyboardButton("Mensa Vita", callback_data="vita"),
                InlineKeyboardButton("Mensa Jülich", callback_data="juelich")]
               ]

def generate_markup(auto_update, filter_state):
    if auto_update:
        auto_update_row = [[InlineKeyboardButton("Auto-Update deaktivieren", callback_data="5$0")]]
    else:
        auto_update_row = [[InlineKeyboardButton("Auto-Update aktivieren", callback_data="5$1")]]

    if filter_state == "none":
        filter_row = [[InlineKeyboardButton("Nur vegetarisch", callback_data="1")]]
    elif filter_state == "vegetarian":
        filter_row = [[InlineKeyboardButton("Nur vegan", callback_data="1")]]
    else:
        filter_row = [[InlineKeyboardButton("Auch Tiere", callback_data="1")]]
    keyboard = auto_update_row + button_list + filter_row
    return InlineKeyboardMarkup(keyboard)
