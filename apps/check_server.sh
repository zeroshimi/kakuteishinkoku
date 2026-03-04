#!/bin/bash
# サーバーが最新コードか確認
echo "=== サーバー確認 ==="
curl -s http://127.0.0.1:8000/api/config | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    v = d.get('_version', 'なし')
    print(f'バージョン: {v}')
    if v == '2025-03-01-no-kamoku-validation':
        print('OK: 最新コードで動作中')
    else:
        print('NG: 古いコードの可能性。サーバーを完全停止して ./run.sh で再起動')
except Exception as e:
    print(f'エラー: サーバーに接続できません - {e}')
"
