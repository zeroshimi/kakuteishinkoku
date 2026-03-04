"""データベースモデル"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Transaction(Base):
    """取引（仕訳のヘッダー）"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False)
    description = Column(String(500))
    side_job_type = Column(String(100), nullable=False, index=True)
    receipt_file = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("JournalLine", back_populates="transaction", cascade="all, delete-orphan")


class JournalLine(Base):
    """仕訳明細（借方・貸方の各行）"""
    __tablename__ = "journal_lines"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    account = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # "debit" or "credit"
    amount = Column(Float, nullable=False)

    transaction = relationship("Transaction", back_populates="lines")
