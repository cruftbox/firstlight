FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    cups \
    cups-bsd \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/config
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY tests/ ./tests/

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Placed last so changes to the version don't invalidate prior layers.
ARG FIRSTLIGHT_VERSION=unknown
ENV FIRSTLIGHT_VERSION=${FIRSTLIGHT_VERSION}

EXPOSE 5000
CMD ["/app/start.sh"]
