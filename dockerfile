FROM python:3.10-slim

WORKDIR /app


RUN apt-get update && apt-get install -y cron && apt-get clean

COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt --verbose


COPY src/ ./src/

COPY supervisord.conf . 

COPY cronjob /etc/cron.d/cronjob  


# Give execution permission to the script if needed
RUN chmod 0644 /etc/cron.d/cronjob && \
    crontab /etc/cron.d/cronjob

EXPOSE 8500

CMD [ "supervisord" , "-c","supervisord.conf"]