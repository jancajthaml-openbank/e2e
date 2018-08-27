# Copyright (c) 2017-2018, Jan Cajthaml <jan.cajthaml@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM debian:stretch

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

MAINTAINER Jan Cajthaml <jan.cajthaml@gmail.com>

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get clean && \
    apt-get -y install \
      libzmq3-dev=4.2.1-4 \
      ruby-all-dev \
      python3-all-dev \
      python3-pip \
      apt-utils \
      lsb-release \
      haproxy \
      git \
      cron \
      at \
      build-essential \
      curl \
      openssl \
      logrotate \
      rsyslog \
      unattended-upgrades \
      ssmtp \
      lsof \
      procps \
      initscripts \
      libsystemd0 \
      libudev1 \
      systemd \
      sysvinit-utils \
      udev \
      util-linux && \
  apt-get clean && \
  sed -i '/imklog/{s/^/#/}' /etc/rsyslog.conf && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

RUN gem install \
    \
      turnip:2.1.1 \
      turnip_formatter:0.5.0 \
      rspec_junit_formatter:0.3.0 \
      rspec-instafail:1.0.0 \
      excon:0.61.0 \
      byebug:10.0.1

RUN pip3 install \
    \
      requests==2.19.1 \
      ujson==1.35 \
      inotify_simple

RUN echo "root:Docker!" | chpasswd

RUN cd /lib/systemd/system/sysinit.target.wants/ && \
    ls | grep -v systemd-tmpfiles-setup.service | xargs rm -f && \
    rm -f /lib/systemd/system/sockets.target.wants/*udev* && \
    systemctl mask -- \
      tmp.mount \
      etc-hostname.mount \
      etc-hosts.mount \
      etc-resolv.conf.mount \
      -.mount \
      swap.target \
      getty.target \
      getty-static.service \
      dev-mqueue.mount \
      cgproxy.service \
      systemd-tmpfiles-setup-dev.service \
      systemd-remount-fs.service \
      systemd-ask-password-wall.path \
      systemd-logind.service && \
    systemctl set-default multi-user.target || :

RUN sed -ri /etc/systemd/journald.conf -e 's!^#?Storage=.*!Storage=volatile!'

COPY etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg

WORKDIR /opt/bbtest

VOLUME [ "/sys/fs/cgroup", "/run", "/run/lock", "/tmp" ]

ENTRYPOINT ["/lib/systemd/systemd"]
