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

COPY main.py /etc/perf/main.py
COPY stress.py /etc/perf/stress.py
COPY env.py /etc/perf/env.py
COPY constants.py /etc/perf/constants.py
COPY api.py /etc/perf/api.py

WORKDIR /etc/perf

ENTRYPOINT ["python"]
CMD ["main.py"]
