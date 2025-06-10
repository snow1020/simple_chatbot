# Node.js 18をベースイメージとして使用
FROM node:18-alpine

# 作業ディレクトリを設定
WORKDIR /app

# npmの設定を最適化（タイムアウト対策）
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-retries 5 && \
    npm config set fetch-retry-factor 2 && \
    npm config set fetch-retry-mintimeout 10000 && \
    npm config set fetch-retry-maxtimeout 60000

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール（エラー回復機能付き）
RUN npm ci --only=production --verbose || \
    (npm cache clean --force && npm ci --only=production --verbose)

# アプリケーションコードをコピー
COPY . .

# Next.jsアプリをビルド
RUN npm run build

# ポート3000を公開
EXPOSE 3000

# 非rootユーザーを作成してセキュリティを向上
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Next.js出力ディレクトリの所有権を変更
RUN chown -R nextjs:nodejs /app/.next

# 非rootユーザーに切り替え
USER nextjs

# アプリケーションを起動
CMD ["npm", "run", "start"] 