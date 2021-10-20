FROM python:3.9-slim

WORKDIR /app

COPY ../ /app/scrapydweb_pkg

RUN apt-get update && \ 
  apt-get install -y git && \
  pip3 install /app/scrapydweb_pkg && 

CMD scrapydweb