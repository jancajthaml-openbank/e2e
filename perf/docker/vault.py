#!/usr/bin/env python

from docker.common import Container
import subprocess
import string
import requests
import time
import random
secure_random = random.SystemRandom()

class Vault(Container):

  @property
  def hostname(self) -> str:
    return self._hostname

  @property
  def container(self) -> str:
    return self._container

  def __init__(self, tenant = None, options=[]):
    if not tenant:
      tenant = ''.join(secure_random.choice(string.ascii_lowercase + string.digits) for _ in range(10))

    self.tenant = tenant
    self._hostname = "vault-{0}".format(self.tenant)
    self.label = "p-{0}".format(self._hostname)

    args = [
      "/usr/bin/docker", "run", "-d",
      "-h", self._hostname,
      "-e", "VAULT_LAKE_HOSTNAME=lake",
      "-e", "VAULT_STORAGE=/data",
      "-e", "VAULT_LOG_LEVEL={0}".format(Container.get_log_level()),
      "-e", "VAULT_JOURNAL_SATURATION=10000",
      "-e", "VAULT_SNAPSHOT_SCANINTERVAL=1h",
      "-e", "VAULT_TENANT={0}".format(self.tenant),
      "-e", "VAULT_METRICS_REFRESHRATE=1s",
      "-e", "VAULT_METRICS_OUTPUT=/opt/metrics/{0}.json".format(self.label),
      "--volumes-from={0}".format(Container.get_host_id()),
      "--net={0}".format(Container.get_host_network()),
      "--net-alias={0}".format(self._hostname),
      "--name={0}".format(self.label),
      "--publish=8080",
      "openbank/vault:master"
    ] + options

    #"--tmpfs=/data", <- this is ramdisk, this would not survive restart

    self._container = subprocess.check_output(args, stderr=subprocess.STDOUT).decode("utf-8").strip()

  def teardown(self):
    try:
      subprocess.check_call(["/usr/bin/docker", "kill", "--signal=\"TERM\"", self._container], stdout=Container.FNULL, stderr=subprocess.STDOUT)
      logs = subprocess.check_output(["/usr/bin/docker", "logs", self._container], stderr=subprocess.STDOUT).decode("utf-8")

      with open("/logs/{0}.log".format(self.label),'w') as f:
        f.write(logs)

      subprocess.check_call(["/usr/bin/docker", "kill", self._container], stdout=Container.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
      pass
    finally:
      subprocess.call(["/usr/bin/docker", "rm", "-f", self._container], stdout=Container.FNULL, stderr=subprocess.STDOUT)

  def restart(self):
    try:
      subprocess.check_call(["/usr/bin/docker", "restart", self._container], stdout=Container.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to restart container {0} with error {1}".format(self.label, ex))

  @property
  def is_healthy(self) -> bool:
    mustend = time.time() + 10
    while time.time() < mustend:
      try:
        if requests.get('http://' + self._hostname + ':8080' + '/health', timeout=(1, 1), verify=False).status_code == 200:
          return True
      except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        pass
      finally:
        time.sleep(0.1)
    return False
