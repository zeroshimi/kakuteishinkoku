"""複式簿記アプリ - FastAPI メイン"""
from dotenv import load_dotenv

load_dotenv()

import re
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from config import ACCOUNTS, CREDIT_ACCOUNTS, DEBIT_ACCOUNTS, RECEIPTS_BASE, get_receipts_dir_for_side_job, get_side_job_types
from database import get_db, init_db
from excel_export import export_to_excel
from models import Transaction, JournalLine


class JournalEntryCreate(BaseModel):
    year: int
    date: date
    debit_account: str
    credit_account: str
    debit_amount: float
    credit_amount: float
    description: Optional[str] = None
    side_job_type: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    current_year = datetime.now().year
    for y in (current_year, current_year - 1):
        for sj in get_side_job_types():
            get_receipts_dir_for_side_job(y, sj)
    yield


app = FastAPI(title="複式簿記アプリ", lifespan=lifespan)

# 静的ファイル（フロントエンド）
frontend_path = Path(__file__).parent / "static"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    index_file = frontend_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "複式簿記API", "docs": "/docs"}


# --- API ---

# デバッグ: サーバーが最新コードか確認用
APP_VERSION = "2025-03-01-no-kamoku-validation"


@app.get("/api/config")
def get_config():
    """設定情報（副業種別・勘定科目・領収書パス）を取得"""
    return {
        "_version": APP_VERSION,
        "side_job_types": get_side_job_types(),
        "accounts": [{"name": a[0], "type": a[1], "description": a[2]} for a in DEBIT_ACCOUNTS],
        "credit_accounts": CREDIT_ACCOUNTS,
        "receipts_base": str(RECEIPTS_BASE),
        "receipts_note": "領収書は {年}/領収書/{副業種別}/ に配置（例: 2025/領収書/dentrix/）",
    }


def _entry_to_dict(t: Transaction) -> dict:
    lines = {l.side: l for l in t.lines}
    debit = lines.get("debit")
    credit = lines.get("credit")
    return {
        "id": t.id,
        "year": t.year,
        "date": t.date.isoformat(),
        "debit_account": debit.account if debit else "",
        "credit_account": credit.account if credit else "",
        "debit_amount": debit.amount if debit else 0,
        "credit_amount": credit.amount if credit else 0,
        "amount": debit.amount if debit else credit.amount if credit else 0,
        "description": t.description,
        "side_job_type": t.side_job_type,
        "receipt_file": t.receipt_file,
    }


@app.get("/api/entries")
def list_entries(
    year: Optional[int] = Query(None, description="年度でフィルタ"),
    side_job_type: Optional[str] = Query(None, description="副業種別でフィルタ"),
    db: Session = Depends(get_db),
):
    """仕訳一覧取得"""
    q = db.query(Transaction).options(joinedload(Transaction.lines))
    if year:
        q = q.filter(Transaction.year == year)
    if side_job_type:
        q = q.filter(Transaction.side_job_type == side_job_type)
    entries = q.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    return [_entry_to_dict(e) for e in entries]


@app.post("/api/entries")
def create_entry(entry: JournalEntryCreate, db: Session = Depends(get_db)):
    """仕訳登録"""
    valid_types = get_side_job_types()
    if entry.side_job_type not in valid_types:
        raise HTTPException(400, f"副業種別は {valid_types} のいずれかを指定してください")
    if entry.debit_amount <= 0 or entry.credit_amount <= 0:
        raise HTTPException(400, "借方・貸方の金額は0より大きい値を入力してください")
    if entry.debit_amount != entry.credit_amount:
        raise HTTPException(400, "借方金額と貸方金額は一致させる必要があります")

    t = Transaction(
        year=entry.year,
        date=entry.date,
        description=entry.description,
        side_job_type=entry.side_job_type,
    )
    db.add(t)
    db.flush()
    db.add(JournalLine(transaction_id=t.id, account=entry.debit_account, side="debit", amount=entry.debit_amount))
    db.add(JournalLine(transaction_id=t.id, account=entry.credit_account, side="credit", amount=entry.credit_amount))
    db.commit()
    db.refresh(t)
    return {"id": t.id, "message": "登録しました"}


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}


def _safe_filename(base: str) -> str:
    """ファイル名に使える文字のみ残す"""
    return re.sub(r"[^\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\-\.]", "_", base)[:50]


@app.post("/api/entries/{entry_id}/receipt")
def upload_receipt(
    entry_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """領収書をアップロードし、レコードと紐付け"""
    t = db.get(Transaction, entry_id)
    if not t:
        raise HTTPException(404, "該当する仕訳がありません")
    debit_line = next((l for l in t.lines if l.side == "debit"), None)

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"対応形式: {', '.join(ALLOWED_EXTENSIONS)}")

    date_str = t.date.strftime("%Y-%m-%d")
    account_safe = _safe_filename(debit_line.account if debit_line else "unknown")
    amount_str = str(int(debit_line.amount)) if debit_line else "0"
    unique = str(uuid.uuid4())[:8]
    new_name = f"{date_str}_{account_safe}_{amount_str}_{unique}{ext}"

    receipts_dir = get_receipts_dir_for_side_job(t.year, t.side_job_type)
    file_path = receipts_dir / new_name

    contents = file.file.read()
    file_path.write_bytes(contents)

    rel_path = f"{t.year}/領収書/{t.side_job_type}/{new_name}"
    t.receipt_file = rel_path
    db.commit()

    return {"receipt_file": rel_path, "message": "領収書を保存しました"}


@app.get("/api/receipts/{path:path}")
def get_receipt(path: str):
    """領収書ファイルを返す"""
    if ".." in path or path.startswith("/"):
        raise HTTPException(400, "無効なパスです")
    full_path = RECEIPTS_BASE / path
    if not full_path.exists():
        raise HTTPException(404, "ファイルが見つかりません")
    if not str(full_path.resolve()).startswith(str(RECEIPTS_BASE.resolve())):
        raise HTTPException(403, "アクセスできません")
    return FileResponse(full_path)


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    """仕訳削除（紐づく領収書画像も削除）"""
    t = db.get(Transaction, entry_id)
    if not t:
        raise HTTPException(404, "該当する仕訳がありません")
    if t.receipt_file:
        receipt_path = RECEIPTS_BASE / t.receipt_file
        if receipt_path.exists() and str(receipt_path.resolve()).startswith(str(RECEIPTS_BASE.resolve())):
            receipt_path.unlink()
    db.delete(t)
    db.commit()
    return {"message": "削除しました"}


@app.get("/api/export/excel")
def export_excel(
    year: int = Query(..., description="出力する年度"),
    db: Session = Depends(get_db),
):
    """Excel出力"""
    file_path = export_to_excel(db, year)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"複式簿記_{year}年度.xlsx",
    )
