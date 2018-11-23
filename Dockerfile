# ---------------------------------------------------------------------------- #

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

# ---------------------------------------------------------------------------- #

FROM jancajthaml/bbtest

COPY --from=openbank/lake:master /opt/artifacts /opt/artifacts/lake
COPY --from=openbank/vault:master /opt/artifacts /opt/artifacts/vault
COPY --from=openbank/wall:master /opt/artifacts /opt/artifacts/wall
COPY --from=openbank/search:master /opt/artifacts /opt/artifacts/search

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      haproxy \
      && \
    \
    find /opt/artifacts/lake -type f -name 'lake_*_amd64.deb' -exec \
      apt-get -y install -f \{\} \; && \
    \
    find /opt/artifacts/vault -type f -name 'vault_*_amd64.deb' -exec \
      apt-get -y install -f \{\} \; && \
    \
    find /opt/artifacts/wall -type f -name 'wall_*_amd64.deb' -exec \
      apt-get -y install -f \{\} \; && \
    \
    find /opt/artifacts/search -type f -name 'search*_all.deb' -exec \
      apt-get -y install -f \{\} \; && \
    \
    systemctl enable mongod

COPY etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg

# ---------------------------------------------------------------------------- #

