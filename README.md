# Simple Chatbot

AIチャットボットアプリケーション（FastAPI + Next.js）

## プロジェクト構成

```
simple_chatbot/
├── backend/           # FastAPI バックエンド
│   ├── app/
│   ├── requirements.txt
│   └── ...
├── frontend/
│   └── chat-app-frontend/ # Next.js フロントエンド
│      
└── README.md
```

## 前提条件

- **Python**: 3.8以上
- **Node.js**: 18.0以上
- **npm**: Node.jsに付属

## 起動手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd simple_chatbot
```

### 2. バックエンドのセットアップと起動

```bash
# バックエンドディレクトリに移動
cd backend

# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化
# Windows の場合:
venv\Scripts\activate
# macOS/Linux の場合:
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# FastAPIサーバーの起動
uvicorn app.main:app --reload --port 8000
```

バックエンドが正常に起動すると、以下のURLでアクセスできます：
- API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws

### 3. フロントエンドのセットアップと起動

**新しいターミナルウィンドウ**を開いて以下を実行：

```bash
# プロジェクトルートから
cd frontend/chat-app-frontend

# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

フロントエンドが正常に起動すると、以下のURLでアクセスできます：
- アプリ: http://localhost:3000

### 4. アプリの利用

1. ブラウザで http://localhost:3000 にアクセス
2. チャット画面が表示されます
3. メッセージを入力して送信すると、AIからのダミー応答が返されます
4. リアルタイムでメッセージのやり取りが可能です

## Dockerを使用した起動（推奨）

### 前提条件
- **Docker**: 20.0以上
- **Docker Compose**: 2.0以上

### プロダクション環境での起動

```bash
# プロジェクトルートで実行
docker-compose up --build

# バックグラウンドで実行
docker-compose up -d --build

# 停止
docker-compose down
```

### 開発環境での起動（ホットリロード対応）

```bash
# 開発環境で起動
docker-compose -f docker-compose.dev.yml up --build

# バックグラウンドで実行
docker-compose -f docker-compose.dev.yml up -d --build

# 停止
docker-compose -f docker-compose.dev.yml down
```

アプリケーションが起動したら：
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000

## 開発コマンド

### バックエンド

```bash
# 開発サーバー起動（リロード付き）
uvicorn app.main:app --reload --port 8000

# テスト実行
pytest

# 特定ホストでの起動
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### フロントエンド

```bash
# 開発サーバー起動
npm run dev

# プロダクションビルド
npm run build

# プロダクションサーバー起動
npm run start

# リンター実行
npm run lint

# テスト実行
npm run test
```

## トラブルシューティング

### ポートが使用中の場合

```bash
# バックエンドのポートを変更
uvicorn app.main:app --reload --port 8001

# フロントエンドのポートを変更
npm run dev -- --port 3001
```

### 依存関係のエラー

```bash
# バックエンド
pip install --upgrade pip
pip install -r requirements.txt

# フロントエンド
rm -rf node_modules package-lock.json
npm install
```

### WebSocket接続エラー

1. バックエンドが正常に起動していることを確認
2. CORS設定を確認（フロントエンドのポートが許可されているか）
3. ファイアウォールの設定を確認

### Docker関連のエラー

```bash
# コンテナとイメージをすべて削除してやり直し
docker-compose down
docker system prune -a
docker-compose up --build

# 個別のサービス再ビルド
docker-compose build --no-cache backend
docker-compose build --no-cache frontend

# ログの確認
docker-compose logs backend
docker-compose logs frontend

# コンテナの状態確認
docker-compose ps
```

### ポート競合（Docker使用時）

```bash
# 使用中のポートを確認
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000

# 既存のコンテナを停止
docker-compose down
```

## 技術スタック

- **バックエンド**: Python, FastAPI, WebSockets, python-socketio
- **フロントエンド**: Next.js, TypeScript, Tailwind CSS, Socket.IO-client
- **通信**: WebSocket（リアルタイム通信）

---

開発に関する質問や問題があれば、Issueを作成してください. 
