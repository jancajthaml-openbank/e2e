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

COPY --from=library/docker:18.06 /usr/local/bin/docker /usr/bin/docker

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      haproxy \
      mongodb-org>=4.0.3~ \
      nodejs>=10.11~ \
      init-system-helpers>=1.18~ \
      libzmq5>=4.2.1~

COPY etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg

RUN systemctl enable mongod

# ---------------------------------------------------------------------------- #

