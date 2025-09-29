FROM python:3.9.23-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

# Node.js 20 + n8n CLI（importer 需要）
RUN apt-get update && apt-get install -y curl gnupg ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && npm i -g n8n \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 依賴
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 專案（含 workflows/）
COPY . /app

# 先產生分類檔（就算失敗也不中斷）
RUN python create_categories.py || true

# 啟動時：先匯入，再開 API
CMD ["sh", "-c", "python import_workflows.py --force && python create_categories.py || true && python -m uvicorn api_server:app --host 0.0.0.0 --port ${PORT}"]
