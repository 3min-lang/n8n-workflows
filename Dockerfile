FROM python:3.9.23-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

# 先裝 Node.js + n8n CLI（importer 需要）
RUN apt-get update && apt-get install -y curl gnupg ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get install -y nodejs \
 && npm i -g n8n \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安裝 Python 依賴
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案（包含 workflows/ 資料夾）
COPY . /app

# 方式一（建議）：在「建置時」先把資料匯入到資料庫
# 這樣部署更快，容器起來就有資料
RUN python import_workflows.py --force || true \
 && python create_categories.py || true

# 方式二（備用）：改成在「啟動時」匯入
# CMD ["sh","-c","python import_workflows.py --force && python create_categories.py || true && python -m uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-${WEB_PORT:-8000}}"]

# 啟動 API（Zeabur 會注入 PORT/WEB_PORT，沒注入時預設 8000 便於本機測試）
CMD ["sh","-c","python -m uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-${WEB_PORT:-8000}}"]
