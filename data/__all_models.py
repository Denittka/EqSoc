from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean, ForeignKey
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase
from flask_login import UserMixin


class Peer(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "peers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String)
    port = Column(Integer)
    pubkey = Column(String)


class User(UserMixin, SqlAlchemyBase, SerializerMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    pubkey = Column(Text, unique=True)
    description = Column(Text, default="")


class Post(UserMixin, SqlAlchemyBase, SerializerMixin):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(Integer)
    text = Column(Text)
    datetime = Column(DateTime)


class Follow(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "follows"
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower = Column(Integer, ForeignKey("users.id"), nullable=False)
    follower = Column(Integer, ForeignKey("users.id"), nullable=False)
