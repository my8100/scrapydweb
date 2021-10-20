FROM python:3.9-slim

WORKDIR /app

COPY . /app/scrapydweb_pkg

RUN apt-get update && apt-get install -y git gcc 

RUN pip3 install -r /app/scrapydweb_pkg/requirements.txt && \ 
  pip3 install /app/scrapydweb_pkg

RUN mkdir /app/scrapyd_server
RUN mkdir /app/scrapyd_server/projects
RUN chmod +x /app/scrapydweb_pkg/launcher.sh 

# RUN groupadd -r docker && useradd --no-log-init -r -g docker dockeruser
# USER dockeruser

CMD ["sh", "/app/scrapydweb_pkg/launcher.sh"]


