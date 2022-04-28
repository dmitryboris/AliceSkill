import sqlalchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'user'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    yandex_id = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rating = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    game = relationship('Game')

    def __repr__(self):
        return f'{self.name} {self.rating}'
