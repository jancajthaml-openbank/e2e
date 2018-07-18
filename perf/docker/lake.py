#!/usr/bin/env python

from docker.common import Container
import subprocess

class Lake(Container):

  @property
  def hostname(self) -> str:
    return self._hostname
  
  @property
  def container(self) -> str:
    return self._container

  def __init__(self):
    self._hostname = "lake"
    self.label = "p-{0}".format(self._hostname)

    args = [
      "/usr/bin/docker", "run", "-d",
      "-h", self._hostname,
      "--privileged",
      "--volumes-from={0}".format(Container.get_host_id()),
      "--net={0}".format(Container.get_host_network()),
      "--net-alias={0}".format(self._hostname),
      "--name={0}".format(self.label),
      "--publish=5562:5562",
      "--publish=5561:5561",
      "openbank/lake:master"
    ]

    self._container = subprocess.check_output(args, stderr=subprocess.STDOUT).decode("utf-8").strip()

  def teardown(self):
    try:
      subprocess.check_call(["/usr/bin/docker", "kill", "--signal=\"TERM\"", self._container], stdout=Container.FNULL, stderr=subprocess.STDOUT)
      # fixme save logs from journalctl
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
      subprocess.check_call(["/usr/bin/docker", "exec", self._container, "systemctl", "restart", "lake.service"], stdout=Container.FNULL, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
      raise RuntimeError("Failed to restart container {0} with error {1}".format(self.label, ex))

  @property
  def is_healthy(self) -> bool:
    # fixme TBD
    return True
