FROM python:3.10-slim

WORKDIR /app


COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt


COPY src/ ./src/

COPY supervisord.conf . 


EXPOSE 8500

CMD [ "supervisord" , "-c","supervisord.conf"]