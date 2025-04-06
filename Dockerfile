# Dockerfile
FROM python:3.10-alpine

# Install build dependencies for Python packages
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt setup.py README.md ./
RUN pip install -e ".[dev]"
RUN apk del .build-deps

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p logs

# Copy the application code
COPY . .

# Set environment variable for Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["runner"]