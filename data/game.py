import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from data.db_session import SqlAlchemyBase

association_table = sqlalchemy.Table(
    'frames_to_game',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('frame', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('frame.id')),
    sqlalchemy.Column('game', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('game.id'))
)


class Game(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'game'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("user.id"))
    attempts = sqlalchemy.Column(sqlalchemy.Integer, default=3)

    user = orm.relation("User", back_populates='game')

    def __repr__(self):
        return f'<User> {self.id} {self.name}'
