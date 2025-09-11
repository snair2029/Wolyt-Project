from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    wallets = relationship("Wallet", back_populates="user")

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="wallets")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    sender_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    receiver_wallet_id = Column(Integer, ForeignKey("wallets.id"))
    amount = Column(Float, nullable=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime, server_default=func.now())
