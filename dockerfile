FROM python:3.10-slim

WORKDIR /app

COPY src/ ./src/

COPY supervisord.conf . 


COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8500

CMD [ "supervisord" , "-C","supervisord.conf"]