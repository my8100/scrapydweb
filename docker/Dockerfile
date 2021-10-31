FROM python:3.9-slim

WORKDIR /app

COPY . /app/scrapydweb_pkg

# install the PROD settings 
RUN rm /app/scrapydweb_pkg/scrapydweb/default_settings.py 
RUN mv /app/scrapydweb_pkg/prod_settings.py /app/scrapydweb_pkg/scrapydweb/default_settings.py 

RUN apt-get update && apt-get install -y git gcc && \
  pip3 install --upgrade pip && \
  pip3 install -r /app/scrapydweb_pkg/requirements.txt && \ 
  pip3 install /app/scrapydweb_pkg

RUN mkdir /app/scrapyd_server
RUN mkdir /app/scrapyd_server/projects

RUN chmod +x /app/scrapydweb_pkg/launcher.sh 

CMD ["sh", "/app/scrapydweb_pkg/launcher.sh"]


