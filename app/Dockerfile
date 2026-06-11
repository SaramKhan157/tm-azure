FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser
USER appuser

EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "60", "app:app"]
