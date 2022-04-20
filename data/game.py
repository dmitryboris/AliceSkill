import sqlalchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from data.frames_to_game import association_table
from data.db_session import SqlAlchemyBase


class Game(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'game'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    hints = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    answered = sqlalchemy.Column(sqlalchemy.Integer)
    end = sqlalchemy.Column(sqlalchemy.Boolean)

    frames = relationship('Frame',
                          secondary=association_table,
                          back_populates='games')

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("user.id"))
    user = relationship("User", back_populates='game')

    def __repr__(self):
        return f'<User> {self.id} {self.name}'
