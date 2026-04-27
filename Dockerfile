FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    cups-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/config
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY tests/ ./tests/

EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "app", "run", "--host=0.0.0.0"]
