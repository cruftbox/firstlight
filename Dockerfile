# The same base as the other Python apps on Bandersnatch (Debian 13).
# --no-install-recommends is required, not an optimization: on Debian 13,
# cups recommends systemd, and systemd's post-install script fails inside a
# QNAP Container Station build ("Failed to copy permissions from /etc/group").
# Debian 13 also renamed libgdk-pixbuf2.0-0 to libgdk-pixbuf-2.0-0.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    cups \
    cups-bsd \
    fonts-noto-color-emoji \
    # Came in as a recommendation before. Covers CJK characters in headlines.
    fonts-droid-fallback \
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
