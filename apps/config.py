"""アプリケーション設定"""
import os
from pathlib import Path

# 副業の種類（環境変数からカンマ区切りで取得）
def get_side_job_types() -> list[str]:
    types_str = os.getenv("SIDE_JOB_TYPES", "dentrix,shinjuku-joryu,health-tech-hub")
    return [t.strip() for t in types_str.split(",") if t.strip()]

# 勘定科目（確定申告の必要経費科目に準拠）
ACCOUNT_TYPES = {
    "revenue": "収入",
    "expense": "費用",
    "asset": "資産",
    "liability": "負債",
}

# 借方科目（仕訳の借方で使用）
DEBIT_ACCOUNTS = [
    ("立替金", "asset", "取引先や他人のためにお金を立て替えた時"),
    ("事業主貸", "asset", "売上が個人の口座に振り込まれた時、源泉徴収税が引かれた時"),
    ("売掛金", "asset", "12月に働いたが入金が翌年1月になる売上（年またぎのみ）"),
    ("現金", "asset", "財布の中身を管理したい場合のみ（基本は事業主貸/借で処理）"),
    ("接待交際費", "expense", "医師との会食、飲み代、お中元、お土産代、バーのお客さんへの奢りなど"),
    ("会議費", "expense", "カフェでの打ち合わせ代、コワーキングスペース代、5,000円以下の飲食"),
    ("消耗品費", "expense", "10万円未満のPC周辺機器、キーボード、マウス、PCバッグ、文房具"),
    ("旅費交通費", "expense", "電車賃、タクシー代、バス代、出張の宿泊費、現場行き来、通勤"),
    ("地代家賃", "expense", "自宅家賃の按分（20%分）"),
    ("水道光熱費", "expense", "電気代の按分（IT機材稼働分）"),
    ("通信費", "expense", "自宅ネット回線、スマホ代の按分、切手代、郵送費"),
    ("支払手数料", "expense", "AWS/GCP/Azure等のクラウド代、サーバー代、ドメイン代、振込手数料"),
    ("新聞図書費", "expense", "技術書、医学書、Note有料記事、有料ニュース購読料"),
    ("研修費", "expense", "セミナー、勉強会、資格取得のための研修費用"),
    ("雑費", "expense", "上記に当てはまらない少額な経費（クリーニング代、廃棄費用など）"),
    ("租税公課", "expense", "収入印紙代など"),
    ("減価償却費", "expense", "30万円以上の高額な機材を数年に分けて経費にする場合"),
]

# 貸方科目
CREDIT_ACCOUNTS = ["事業主借", "売上高", "売掛金"]

# 全勘定（Excel集計・DB用）
ACCOUNTS = DEBIT_ACCOUNTS + [
    ("事業主借", "liability", "事業主が事業用に立て替えた経費"),
    ("売上高", "revenue", "売上・収入"),
]

# DBは apps ディレクトリに作成（実行時のカレントディレクトリが apps であることを想定）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookkeeping.db")

# 領収書のベースディレクトリ（確定申告フォルダ直下、年別: 2024, 2025 など）
# apps の親ディレクトリ = 確定申告 を想定
RECEIPTS_BASE = Path(__file__).parent.parent


def get_receipts_dir(year: int) -> Path:
    """指定年度の領収書ディレクトリを返す（存在しなければ作成）"""
    path = RECEIPTS_BASE / str(year) / "領収書"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_receipts_dir_for_side_job(year: int, side_job_type: str) -> Path:
    """指定年度・副業種別の領収書ディレクトリを返す（存在しなければ作成）"""
    path = get_receipts_dir(year) / side_job_type
    path.mkdir(parents=True, exist_ok=True)
    return path
