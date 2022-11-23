import uuid
from .database import Base
from sqlalchemy import (
    TIMESTAMP,
    Column,
    String,
    Boolean,
    text,
    ForeignKey,
    Integer,
    TupleType,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID


class CustomBase(Base):
    __abstract__ = True

    def to_dict(self, fields=[]):
        if not fields:
            return {
                key: value
                for key, value in self.__dict__.items()
                if hasattr(self, key) and not key.startswith("_")
            }
        else:
            return {
                key: value
                for key, value in self.__dict__.items()
                if hasattr(self, key) and not key.startswith("_") and key in fields
            }

    def update(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4
    )
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    verified = Column(Boolean, nullable=False, server_default="False")
    role = Column(String, server_default="user", nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("now()")
    )
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    scopes = Column(String, nullable=True, server_default="me")


class CardType(CustomBase):
    __tablename__ = "types"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    cards = relationship("Card")
    color = Column(String, default=(32, 32, 32))


class CardExtension(CustomBase):
    __tablename__ = "extensions"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    cards = relationship("Card")


class Card(CustomBase):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)
    card_type = Column(Integer, ForeignKey("types.id"), nullable=False)
    extension = Column(Integer, ForeignKey("extensions.id"), nullable=False)
