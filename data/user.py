import sqlalchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'user'

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    rating = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

    game = relationship('Game')

    def __repr__(self):
        return f'<User> {self.id} {self.name}'
