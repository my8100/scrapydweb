FROM python:3.9-slim

RUN apt-get update && apt-get install -y git gcc 

WORKDIR /app

RUN groupadd -r docker && useradd --no-log-init -r -g docker dockeruser
USER dockeruser

COPY --chown=dockeruser:docker . /app/scrapydweb_pkg


RUN pip3 install -r /app/scrapydweb_pkg/requirements.txt && \ 
  pip3 install /app/scrapydweb_pkg

RUN mkdir /app/scrapyd_server
RUN mkdir /app/scrapyd_server/projects
RUN chmod +x /app/scrapydweb_pkg/launcher.sh 

CMD ["sh", "/app/scrapydweb_pkg/launcher.sh"]


