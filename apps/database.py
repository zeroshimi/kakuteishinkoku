"""データベース接続とセットアップ"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """テーブル作成・マイグレーション"""
    from models import Transaction, JournalLine
    Base.metadata.create_all(bind=engine)

    insp = inspect(engine)
    tables = insp.get_table_names()

    # 旧 journal_entries から新テーブルへマイグレーション
    if "journal_entries" in tables and "transactions" in tables:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT COUNT(*) FROM journal_entries"))
            if r.scalar() > 0:
                r2 = conn.execute(text("SELECT COUNT(*) FROM transactions"))
                if r2.scalar() == 0:
                    conn.execute(text("""
                        INSERT INTO transactions (id, year, date, description, side_job_type, receipt_file, created_at)
                        SELECT id, year, date, COALESCE(description,''), side_job_type, receipt_file, created_at
                        FROM journal_entries
                    """))
                    conn.execute(text("""
                        INSERT INTO journal_lines (transaction_id, account, side, amount)
                        SELECT id, debit_account, 'debit', amount FROM journal_entries
                    """))
                    conn.execute(text("""
                        INSERT INTO journal_lines (transaction_id, account, side, amount)
                        SELECT id, credit_account, 'credit', amount FROM journal_entries
                    """))
                    conn.commit()
            conn.execute(text("DROP TABLE IF EXISTS journal_entries"))
            conn.commit()
