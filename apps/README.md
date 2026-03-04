# 複式簿記アプリ

確定申告用の年毎複式簿記入力アプリです。DBに記録し、Excelで出力できます。

## セットアップ

```bash
cd apps
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 環境変数

`.env` ファイルを作成（`.env.example` をコピー）:

```bash
cp .env.example .env
```

| 変数 | 説明 | 例 |
|------|------|-----|
| SIDE_JOB_TYPES | 副業の種類（カンマ区切り） | dentrix,shinjuku-joryu,health-tech-hub |
| DATABASE_URL | DB接続（省略時は SQLite） | sqlite:///./bookkeeping.db |

## 起動

```bash
cd apps
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで http://localhost:8000 を開く。

## 領収書の配置

領収書は**年別ディレクトリ**に配置します。確定申告フォルダ直下に `2024`、`2025` などの年フォルダを作成し、その中に `領収書` を置きます。

```
確定申告/
├── 2024/
│   └── 領収書/
│       ├── dentrix/        ← PDF等を配置
│       ├── shinjuku-joryu/
│       └── health-tech-hub/
├── 2025/
│   └── 領収書/
│       └── ...
└── apps/
```

アプリ起動時に当年・前年のディレクトリを自動作成します。

## 使い方

1. **仕訳の登録**: 借方科目・貸方科目・金額・副業種別などを入力して登録
2. **一覧表示**: 年度・副業種別でフィルタ可能
3. **Excel出力**: 「Excel出力」で指定年度をダウンロード。**副業種別ごとにシート分け**されます

## 勘定科目

確定申告の「副業に係る雑所得の金額の計算表」に準拠した科目を使用します。

- **収入**: 総収入金額
- **費用**: 旅費交通費、通信費、接待交際費、消耗品費、会議・研修費、事務所経費、雑費 など
- **資産**: 現金

## 複式簿記の例

- 売上計上: 借方 現金 / 貸方 総収入金額
- 経費支出: 借方 消耗品費 / 貸方 現金
