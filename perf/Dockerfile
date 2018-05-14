FROM python:3.5.3-alpine

MAINTAINER Jan Cajthaml <jan.cajthaml@gmail.com>

RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
      curl \
      bash \
      git \
      build-base \
      openssh && \
    pip install --upgrade pip && \
    pip install \
    setuptools \
    ujson==1.35 \
    grequests==0.3.0 \
    ujson==1.35

RUN \
  mkdir -p /opt && \
  curl https://get.docker.com/builds/Linux/x86_64/docker-1.12.1.tgz | tar zx -C /opt && \
  ln -s /opt/docker/docker /usr/bin/docker && docker -v

COPY main.py /etc/perf/main.py
COPY stress.py /etc/perf/stress.py
COPY env.py /etc/perf/env.py
COPY constants.py /etc/perf/constants.py
COPY api.py /etc/perf/api.py

WORKDIR /etc/perf

ENTRYPOINT ["python"]
CMD ["main.py"]
