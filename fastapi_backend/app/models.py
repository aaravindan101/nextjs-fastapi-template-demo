from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from fastapi_users_db_sqlalchemy.generics import GUID
from uuid import uuid4
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")

    # Gmail integration fields
    last_pointer = Column(String, nullable=True)  # Gmail pagination pointer
    onboarding_complete = Column(Integer, default=0)  # Boolean flag for onboarding status
    last_sync = Column(DateTime, nullable=True)  # Last time emails were synced


class Item(Base):
    __tablename__ = "items"

    id = Column(GUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    user_id = Column(GUID, ForeignKey("user.id"), nullable=False)

    user = relationship("User", back_populates="items")
