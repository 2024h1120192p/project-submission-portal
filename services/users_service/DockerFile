FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY libs/ ./libs/
COPY config/ ./config/
COPY services/__init__.py ./services/__init__.py
COPY services/users_service/ ./services/users_service/

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "services.users_service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]