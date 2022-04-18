import sqlalchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Movie(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'movie'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    frame = relationship('Frame')

    def __repr__(self):
        return f'<Movie> {self.id} {self.name}'

