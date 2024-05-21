from __future__ import annotations
import typing
import abc
from sqlalchemy import Column, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column, relationship
# ALLOW const.* util.* msg.* context.*
from core.msg import msgabc, msgext

TRANSACTION = 'storeabc.TRANSACTION'
TRANSACTION_RESPONSE = TRANSACTION + '_RESPONSE'


class Transaction(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def execute(self, session: Session) -> typing.Any:
        pass


def execute(mailer: msgabc.Mailer, source: typing.Any, transaction: Transaction):
    mailer.post(source, TRANSACTION, transaction)


async def query(mailer: msgabc.MulticastMailer, source: typing.Any, transaction: Transaction):
    response = await msgext.SynchronousMessenger(mailer).request(source, TRANSACTION, transaction)
    return response.data()


class Base(DeclarativeBase):
    pass


class SystemEvent(Base):
    __tablename__ = 'system_event'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    at = Column(Float)
    name = Column(Text)
    details = Column(Text, nullable=True)


class Instance(Base):
    __tablename__ = 'instance'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True)
    at = Column(Float)
    name = Column(Text, unique=True)
    module = Column(Text)
    events: Mapped[typing.List[InstanceEvent]] = relationship(back_populates='instance', cascade='all,delete')
    players: Mapped[typing.List[Player]] = relationship(back_populates='instance', cascade='all,delete')


class InstanceEvent(Base):
    __tablename__ = 'instance_event'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(Float, index=True)
    instance_id: Mapped[Integer] = mapped_column(ForeignKey('instance.id'), index=True)
    instance: Mapped[Instance] = relationship(back_populates='events')
    name = Column(Text)
    details = Column(Text, nullable=True)


class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(Float)
    instance_id: Mapped[Integer] = mapped_column(ForeignKey('instance.id'), index=True)
    instance: Mapped[Instance] = relationship(back_populates='players')
    name = Column(Text, index=True)
    steamid = Column(Text, nullable=True)
    events: Mapped[typing.List[PlayerEvent]] = relationship(back_populates='player', cascade='all,delete')
    chats: Mapped[typing.List[PlayerChat]] = relationship(back_populates='player', cascade='all,delete')


class PlayerEvent(Base):
    __tablename__ = 'player_event'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(Float, index=True)
    player_id: Mapped[Integer] = mapped_column(ForeignKey('player.id'), index=True)
    player: Mapped[Player] = relationship(back_populates='events')
    name = Column(Text)
    details = Column(Text, nullable=True)


class PlayerChat(Base):
    __tablename__ = 'player_chat'
    id = Column(Integer, unique=True, primary_key=True, autoincrement=True, index=True)
    at = Column(Float, index=True)
    player_id: Mapped[Integer] = mapped_column(ForeignKey('player.id'), index=True)
    player: Mapped[Player] = relationship(back_populates='chats')
    text = Column(Text)
