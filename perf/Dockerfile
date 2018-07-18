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
		requests==2.19.1 \
    ujson==1.35 \
    inotify_simple

COPY . /etc/perf/
WORKDIR /etc/perf

ENTRYPOINT ["python3"]
CMD ["main.py"]
