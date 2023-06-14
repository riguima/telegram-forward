from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    declarative_base,
    Mapped,
    mapped_column,
    relationship,
)

from forward_telegram_bot.database import db


Base = declarative_base()


class Forward(Base):
    __tablename__ = 'forwards'
    id: Mapped[int] = mapped_column(primary_key=True)
    from_chat: Mapped[int]
    to_chat: Mapped[int]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['User'] = relationship(back_populates='forwards')


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    forwards: Mapped[List['Forward']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan',
    )


Base.metadata.create_all(db)
