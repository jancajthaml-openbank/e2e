FROM python:3.5.3-alpine

MAINTAINER Jan Cajthaml <jan.cajthaml@gmail.com>

RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
      curl \
      bash \
      git \
      build-base \
      docker \
      ca-certificates \
      openssh && \
    pip install --upgrade pip && \
    pip install \
    gevent==1.1rc3 \
		requests \
    ujson==1.35 \
    grequests==0.3.0

COPY . /etc/perf/
WORKDIR /etc/perf

ENTRYPOINT ["python3"]
CMD ["main.py"]
