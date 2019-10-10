#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# created by Alwin Ebermann (alwin@alwin.net.au)

from bs4 import BeautifulSoup
from bs4.element import NavigableString
import requests


def meal_from_html(meal_html):
    mealname = meal_html.contents[0]
    cleaned_mealname = "".join([t for t in mealname.contents if type(t) == NavigableString])
    cleaned_mealname = " ".join(cleaned_mealname.split()) + " "
    if cleaned_mealname == "+ ":
        return None
    meal = Meal(cleaned_mealname)
    # now get background info
    for img in meal_html.find_all("image", recursive=True):
        url = img.get("src")
        if url == "resources/images/inhalt/Schwein.png":
            meal.add_to_categorisations("🐷")
        elif url == "resources/images/inhalt/Geflügel.png":
            meal.add_to_categorisations("🐤")
        elif url == "resources/images/inhalt/Rind.png":
            meal.add_to_categorisations("🐄")
        elif url == "resources/images/inhalt/vegan.png":
            meal.add_to_categorisations("🥑")
        elif url == "resources/images/inhalt/OLV.png":
            meal.add_to_categorisations("🥕")
    return meal


class Meal:
    def __init__(self, name: str):
        self.name = name
        self.categorisations = set()

    def add_to_categorisations(self, category):
        self.categorisations.add(category)

    def __str__(self):
        out = self.name
        for cat in self.categorisations:
            out += cat
        out += "\n"
        return out


class Menu:
    def __init__(self, mensa: str, date: str):
        self.mensa = mensa
        self.meals = []
        self.date = date

    def add_meal(self, meal: Meal):
        self.meals.append(meal)

    def get_meals(self, filter_mode: str):
        meals = []
        for meal in self.meals:
            if filter_mode == "none":
                meals.append(meal)
            elif filter_mode == "vegetarian" and ("🥕" in meal.categorisations or "🥑" in meal.categorisations):
                meals.append(meal)
            elif filter_mode == "vegan" and "🥑" in meal.categorisations:
                meals.append(meal)
        return meals

    def get_date(self):
        return self.date

    def get_meals_string(self, filter_mode: str):
        if self.is_closed():
            return "Die Mensa " + self.mensa + " ist heute geschlossen"
        out = ""
        for meal in self.get_meals(filter_mode):
            out += str(meal)
        if out == "":
            return "Keine Essen entsprechen dem gewählten Filter."

        if filter_mode == "none" or filter_mode == "vegetarian":
            out += "\n🥑 = vegan, 🥕 = vegetarisch"
        if filter_mode == "none":
            out += "\n🐷 = Schwein, 🐄 = Rind\n🐤 = Vogel"

        return out

    def is_closed(self):
        return len(self.meals) == 0


def get_menu(mensa_id, mensa_name):
    r = requests.get("https://www.studierendenwerk-aachen.de/speiseplaene/" + mensa_id + "-w.html")
    soup = BeautifulSoup(r.content, "lxml")
    today_date_element = soup.select(" .active-headline a")
    if len(today_date_element) > 0:
        today = today_date_element[0].text
    else:
        today = ""
    menu = Menu(mensa_name, today)
    today_meals = soup.select(".active-panel .menue-desc")
    for meal_html in today_meals:
        meal = meal_from_html(meal_html)
        if meal is not None:
            menu.add_meal(meal)
    return menu
