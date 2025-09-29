FROM python:3.9.23-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# 先安裝 Python 依賴
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案（包含 workflows/ 與 context/）
COPY . /app

# 若沒有分類檔才建立（避免每次重算拖慢部署）
RUN [ -f context/search_categories.json ] || python create_categories.py

# 用專案原生的啟動腳本 run.py 開服務（它會負責建索引/資料庫）
# 一律以 Zeabur 注入的 PORT 監聽；若本機測試沒有 PORT，就用 8000
CMD ["sh","-c","python run.py --host 0.0.0.0 --port ${PORT:-${WEB_PORT:-8000}}"]
