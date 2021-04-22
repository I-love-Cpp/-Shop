import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


# Описание полей таблицы users

class Order(SqlAlchemyBase, UserMixin):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    from_user = sqlalchemy.Column(sqlalchemy.Integer)
    to_user = sqlalchemy.Column(sqlalchemy.Integer)
    product = sqlalchemy.Column(sqlalchemy.String)
