#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    notifications = Column(String(255), nullable=False)
    current_selection = Column(String(255), nullable=True)
    user_group = Column(String(255), nullable=True)
    counter = Column(Integer(), nullable=True)
    message_id = Column(Integer(), nullable=True)
    dailymsg = Column(String(5), nullable=True)
    daily_selection = Column(Integer(), nullable=True)
    filter_mode = Column(String(5), nullable=True)

    def __init__(self, id, first_name, last_name, username):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.notifications = "disabled"
        self.current_selection = "0"
        self.counter = 0
        self.filter_mode = "none"


engine = create_engine('sqlite:///mensausers.sqlite')
Base.metadata.create_all(engine)
