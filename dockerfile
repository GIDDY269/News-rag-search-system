FROM python:3.10-slim

WORKDIR /app

COPY src/ ./src/

COPY supervisord.conf . 

RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8501

CMD [ "supervisord" , "-C","supervisord.conf"]