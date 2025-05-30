FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    jq \
    postgresql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

COPY setup_cron.sh /app/setup_cron.sh
RUN chmod +x /app/setup_cron.sh

CMD ["bash", "/app/setup_cron.sh"]