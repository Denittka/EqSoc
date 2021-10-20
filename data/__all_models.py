from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class Message(UserMixin, SqlAlchemyBase, SerializerMixin):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(Integer)
    receiver = Column(Integer)
    text = Column(String)
    datetime = Column(DateTime)
    is_read = Column(Boolean, default=False)


class User(UserMixin, SqlAlchemyBase, SerializerMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    pubkey = Column(Text, unique=True)
    description = Column(Text, default="")
    posts = Column(String, default="")
    likes = Column(String, default="")
    follows = Column(String, default="")


class Post(UserMixin, SqlAlchemyBase, SerializerMixin):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(Integer)
    text = Column(Text)
    q_and_a = Column(Boolean)
    anonymous = Column(Boolean)
    datetime = Column(DateTime)
    comments = Column(String, default="")
    refers = Column(Integer, default=-1)
    likes = Column(String, default="")
    dislikes = Column(String, default="")
    ideas = Column(String, default="")
