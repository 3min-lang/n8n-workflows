FROM python:3.9.23-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "${PORT}"]
