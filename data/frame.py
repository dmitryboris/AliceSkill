import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase


class Frame(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'frame'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    film_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("movie.id"))

    film = orm.relation("Movie", back_populates='movie')
    categories = orm.relation("Game",
                              secondary="frames_to_game",
                              backref="frame")

    def __repr__(self):
        return f'<User> {self.id} {self.name}'

