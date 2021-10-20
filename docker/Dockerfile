FROM python:3.9-slim

WORKDIR /app

COPY . /app/scrapydweb_pkg

RUN ls -al /app

RUN apt-get update && \ 
  apt-get install -y git gcc && \
  pip3 install -r /app/scrapydweb_pkg/requirements.txt && \ 
  pip3 install /app/scrapydweb_pkg

RUN mkdir /app/scrapyd_server
RUN chmod +x /app/scrapydweb_pkg/launcher.sh 

CMD ["sh", "/app/scrapydweb_pkg/launcher.sh"]


