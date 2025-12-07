from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    wallet_address = Column(String, nullable=False)

    resources = relationship("Resource", back_populates="merchant")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    price_qubic = Column(Integer, nullable=False)

    merchant = relationship("Merchant", back_populates="resources")
    sessions = relationship("Session", back_populates="resource")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)  # UUID
    resource_id = Column(Integer, ForeignKey("resources.id"))
    user_wallet = Column(String, nullable=False)
    amount_qubic = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending | paid | expired
    created_at = Column(DateTime, default=datetime.utcnow)

    resource = relationship("Resource", back_populates="sessions")
