FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt



# stage 2

FROM python:3.12-slim


WORKDIR /app

RUN apt-get update && apt-get install -y cron && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

COPY src/ ./src/

COPY supervisord.conf . 

COPY cronjob /etc/cron.d/cronjob  


# Give execution permission to the script if needed
RUN chmod 0644 /etc/cron.d/cronjob && \
    crontab /etc/cron.d/cronjob

EXPOSE 8500

CMD ["/usr/local/bin/supervisord", "-n", "-c", "/app/supervisord.conf"]