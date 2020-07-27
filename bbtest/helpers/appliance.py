#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docker
import ssl
import urllib.request
import platform
import tarfile
import tempfile
import errno
import os
import json
import datetime
import subprocess
from .shell import execute


class ApplianceHelper(object):

  def get_arch(self):
    return {
      'x86_64': 'amd64',
      'armv7l': 'armhf',
      'armv8': 'arm64'
    }.get(platform.uname().machine, 'amd64')

  def __init__(self, context):
    self.arch = self.get_arch()
    self.units = list()
    self.services = [
      "lake",
      "vault",
      "ledger",
      "data-warehouse",
    ]
    self.docker = docker.APIClient(base_url='unix://var/run/docker.sock')
    self.context = context

  def get_latest_version(self, service):
    uri = "https://hub.docker.com/v2/repositories/openbank/{}/tags/".format(service)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    request = urllib.request.Request(method='GET', url=uri)
    request.add_header('Accept', 'application/json')
    response = urllib.request.urlopen(request, timeout=10, context=ctx)

    if not response.status == 200:
      return None

    body = json.loads(response.read().decode('utf-8')).get('results', [])

    tags = []

    for entry in body:
      tags.append({
        'ts': datetime.datetime.strptime(entry['last_updated'], "%Y-%m-%dT%H:%M:%S.%fZ"),
        'id': entry['name'],
      })

    latest = max(tags, key=lambda x: x['ts'])
    if not latest:
      return (None, None)

    parts = latest.get('id', '').split('-')

    version = parts[0] or None

    if len(parts) > 1:
      meta = 'master'

    if version and version.startswith('v'):
      version = version[1:]

    return (version, meta)

  def setup(self):
    os.makedirs("/etc/data-warehouse/conf.d", exist_ok=True)

    with open('/etc/data-warehouse/conf.d/init.conf', 'w') as fd:
      fd.write(str(os.linesep).join([
        "DATA_WAREHOUSE_LOG_LEVEL=DEBUG",
        "DATA_WAREHOUSE_HTTP_PORT=8080",
        "DATA_WAREHOUSE_POSTGRES_URL=jdbc:postgresql://postgres:5432/openbank",
        "DATA_WAREHOUSE_PRIMARY_STORAGE_PATH=/data"
      ]))

  def download(self):
    try:
      os.mkdir("/tmp/packages")
    except OSError as exc:
      if exc.errno != errno.EEXIST:
        raise
      pass

    pulls = []
    scratch_docker_cmd = ['FROM alpine']

    for service in self.services:
      version, meta = self.get_latest_version(service)
      if not version:
        raise RuntimeError('missing version for {}'.format(service))

      image = 'openbank/{}:v{}'.format(service, (version+'-'+meta) if meta else version)
      package = '/opt/artifacts/{}_{}_{}.deb'.format(service, version, self.arch)
      target = '/tmp/packages/{}.deb'.format(service)

      scratch_docker_cmd.append('COPY --from={} {} {}'.format(image, package, target))
      pulls.append(image)

    for image in pulls:
      (code, result) = execute(['docker', 'pull', image], silent=False)
      assert code == 0, str(result)

    temp = tempfile.NamedTemporaryFile(delete=True)
    try:
      with open(temp.name, 'w') as fd:
        fd.write(str(os.linesep).join(scratch_docker_cmd))

      for chunk in self.docker.build(fileobj=temp, pull=False, rm=True, decode=True, tag='bbtest_artifacts-scratch'):
        if not 'stream' in chunk:
          continue
        for line in chunk['stream'].splitlines():
          l = line.strip(os.linesep)
          if not len(l):
            continue
          print(l)

      scratch = self.docker.create_container('bbtest_artifacts-scratch', '/bin/true')

      if scratch['Warnings']:
        raise Exception(scratch['Warnings'])

      tar_name = tempfile.NamedTemporaryFile(delete=True)

      for service in self.services:
        tar_stream, stat = self.docker.get_archive(scratch['Id'], '/tmp/packages/{}.deb'.format(service))
        with open(tar_name.name, 'wb') as destination:
          for chunk in tar_stream:
            destination.write(chunk)

        archive = tarfile.TarFile(tar_name.name)
        archive.extract('{}.deb'.format(service), '/tmp/packages')

        (code, result) = execute([
          'dpkg', '-c', '/tmp/packages/{}.deb'.format(service)
        ], silent=True)
        if code != 0:
          raise RuntimeError('code: {}, stdout: [{}]'.format(code, result))
        with open('/tmp/reports/blackbox-tests/meta/debian.{}.txt'.format(service), 'w') as f:
          f.write(result)

        result = [item for item in result.split(os.linesep)]
        result = [item.rsplit('/', 1)[-1].strip() for item in result if "/lib/systemd/system/{}".format(service) in item]
        result = [item for item in result if not item.endswith('@.service')]

        self.units += result

      self.docker.remove_container(scratch['Id'])
    finally:
      temp.close()
      self.docker.remove_image('bbtest_artifacts-scratch', force=True)

  def install(self):
    for service in self.services:
      (code, result) = execute([
        "apt-get", "install", "-f", "-qq", "-o=Dpkg::Use-Pty=0", "-o=Dpkg::Options::=--force-confdef", "-o=Dpkg::Options::=--force-confnew", '/tmp/packages/{}.deb'.format(service)
      ], silent=True)
      if code != 0:
        raise RuntimeError('code: {}, stdout: {}'.format(code, result))

  def running(self):
    (code, result) = execute(["systemctl", "list-units", "--no-legend"], silent=True)
    if code != 0:
      return False

    all_running = True
    for unit in self.units:
      if not unit.endswith('.service'):
        continue
      (code, result) = execute(["systemctl", "show", "-p", "SubState", unit], silent=True)
      all_running &= ('SubState=running' in result or 'SubState=exited' in result)

    return all_running

  def __is_openbank_unit(self, unit):
    for mask in self.services:
      if mask in unit:
        return True
    return False

  def collect_logs(self):
    for unit in set(self.__get_systemd_units() + self.units):
      (code, result) = execute(['journalctl', '-o', 'cat', '-u', unit, '--no-pager'], silent=True)
      if code != 0 or not result:
        continue
      with open('/tmp/reports/blackbox-tests/logs/{}.log'.format(unit), 'w') as fd:
        fd.write(result)

    (code, result) = execute(['journalctl', '-o', 'cat', '--no-pager'], silent=True)
    if code == 0:
      with open('/tmp/reports/blackbox-tests/logs/journal.log', 'w') as fd:
        fd.write(result)

  def __get_systemd_units(self):
    (code, result) = execute(['systemctl', 'list-units', '--no-legend'], silent=True)
    result = [item.split(' ')[0].strip() for item in result.split(os.linesep)]
    result = [item for item in result if not item.endswith('unit.slice')]
    result = [item for item in result if self.__is_openbank_unit(item)]
    return result

  def teardown(self):
    self.collect_logs()
    for unit in self.__get_systemd_units():
      execute(['systemctl', 'stop', unit], silent=True)
    self.collect_logs()
