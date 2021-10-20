FROM python:3.9-slim
ADD . /app
WORKDIR /app

EXPOSE 5000
RUN apt-get update && \ 
  apt-get install -y git && \
  pip3 install -U git+https://github.com/my8100/scrapydweb.git && \
  apt-get remove -y git
CMD scrapydweb