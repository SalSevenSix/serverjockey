import typing
import abc
from sqlalchemy import Column, ForeignKey, DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio.session import AsyncSession
# TODO ALLOW ???
from core.msg import msgabc


TRANSACTION = 'storeabc.TRANSACTION'
TRANSACTION_RESPONSE = TRANSACTION + '_RESPONSE'


class Transaction(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    async def execute(self, session: AsyncSession) -> typing.Any:
        pass


def execute(mailer: msgabc.Mailer, source: typing.Any, transaction: Transaction):
    mailer.post(source, TRANSACTION, transaction)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Instance(Base):
    __tablename__ = 'instance'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True)
    module = Column(Text)
    created_at = Column(DateTime)
    events = relationship('InstanceEvent', cascade='all,delete')
    players = relationship('Player', cascade='all,delete')


class InstanceEvent(Base):
    __tablename__ = 'instance_event'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(DateTime)
    instance: Mapped[Integer] = mapped_column(ForeignKey('instance.id'))
    name = Column(Text)
    details = Column(Text, nullable=True)


class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    instance: Mapped[Integer] = mapped_column(ForeignKey('instance.id'))
    name = Column(Text)
    steamid = Column(Text, nullable=True)
    events = relationship('PlayerEvent', cascade='all,delete')
    chats = relationship('PlayerChat', cascade='all,delete')


class PlayerEvent(Base):
    __tablename__ = 'player_event'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(DateTime)
    player: Mapped[Integer] = mapped_column(ForeignKey('player.id'))
    name = Column(Text)


class PlayerChat(Base):
    __tablename__ = 'player_chat'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(DateTime)
    player: Mapped[Integer] = mapped_column(ForeignKey('player.id'))
    text = Column(Text)
