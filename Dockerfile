FROM python:3.9.23-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

# 1) 安裝 Node.js 18 + n8n CLI（importer 需要用到 npx n8n）
RUN apt-get update && apt-get install -y curl gnupg ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs \
 && npm i -g n8n \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) 安裝 Python 依賴
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3) 複製專案（包含 workflows/）
COPY . /app

# 4) 先做索引（create_categories）以建立 context 檔案
RUN python create_categories.py || true

# 5) 啟動時做匯入（需要 n8n CLI）；匯入完再開 API
CMD ["sh","-c","python import_workflows.py --force || true && python -m uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-${WEB_PORT:-8000}}"]
