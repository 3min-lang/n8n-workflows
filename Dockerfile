FROM python:3.9.23-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 把整個專案（包含 workflows/）拷進映像
COPY . /app

# 先匯入 workflows，再啟動 API
# --force：可重建索引（不存在就會建立）
CMD ["sh","-c","python import_workflows.py --force && python create_categories.py || true && python -m uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-${WEB_PORT:-8000}}"]
