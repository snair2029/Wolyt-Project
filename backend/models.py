from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from backend.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    balance = Column(Float, default=0.0)
    user = relationship("User", back_populates="wallets")
    sent = relationship("Transaction", foreign_keys="Transaction.sender_wallet_id", back_populates="sender_wallet")
    received = relationship("Transaction", foreign_keys="Transaction.receiver_wallet_id", back_populates="receiver_wallet")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    sender_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    receiver_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    sender_wallet = relationship("Wallet", foreign_keys=[sender_wallet_id], back_populates="sent")
    receiver_wallet = relationship("Wallet", foreign_keys=[receiver_wallet_id], back_populates="received")
