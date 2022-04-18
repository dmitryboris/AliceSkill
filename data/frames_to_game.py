import sqlalchemy

from data.db_session import SqlAlchemyBase

association_table = sqlalchemy.Table(
    'frames_to_game',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('frame', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('frame.id')),
    sqlalchemy.Column('game', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('game.id'))
)