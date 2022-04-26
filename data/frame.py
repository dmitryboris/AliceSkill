import sqlalchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.frames_to_game import association_table
from data.db_session import SqlAlchemyBase


class Frame(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'frame'

    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    film_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("movie.id"))
    film = relationship("Movie", back_populates='frame')

    games = relationship('Game',
                         secondary=association_table,
                         back_populates='frames')

    def __repr__(self):
        return f'<Frame> {self.id} {self.film_id}'
