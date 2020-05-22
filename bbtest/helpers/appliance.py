#!/usr/bin/env python
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
    self.units = []
    self.services = [
      "lake",
      "vault",
      "ledger",
      "search",
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

  def download(self):
    try:
      os.mkdir("/tmp/packages")
    except OSError as exc:
      if exc.errno != errno.EEXIST:
        raise
      pass

    scratch_docker_cmd = ['FROM alpine']

    for service in self.services:
      version, meta = self.get_latest_version(service)
      if not version:
        raise RuntimeError('missing version for {}'.format(service))

      if meta:
        scratch_docker_cmd.append('COPY --from=openbank/{0}:v{1}-{2} /opt/artifacts/{0}_{1}+{2}_{3}.deb /tmp/packages/{0}.deb'.format(service, version, meta, self.arch))
      else:
        scratch_docker_cmd.append('COPY --from=openbank/{0}:v{1} /opt/artifacts/{0}_{1}_{2}.deb /tmp/packages/{0}.deb'.format(service, version, self.arch))

    temp = tempfile.NamedTemporaryFile(delete=True)
    try:
      with open(temp.name, 'w') as f:
        for item in scratch_docker_cmd:
          f.write("%s\n" % item)

      for chunk in self.docker.build(fileobj=temp, rm=True, decode=True, tag='bbtest_artifacts-scratch'):
        if 'stream' in chunk:
          for line in chunk['stream'].splitlines():
            if len(line):
              print(line.strip('\r\n'))

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

      self.docker.remove_container(scratch['Id'])
    finally:
      temp.close()
      self.docker.remove_image('bbtest_artifacts-scratch', force=True)

  def install(self):
    for service in self.services:
      (code, result) = execute([
        'apt-get', '-y', 'install', '-qq', '-o=Dpkg::Use-Pty=0', '-f', '/tmp/packages/{}.deb'.format(service)
      ])

      if code != 0:
        raise RuntimeError('code: {}, stdout: {}'.format(code, result))
      self.update_units()

  def running(self):
    (code, result) = execute([
      "systemctl", "list-units", "--no-legend"
    ], silent=True)

    if code != 0:
      return False

    all_running = True
    for service in self.units:
      (code, result) = execute(["systemctl", "show", "-p", "SubState", service], silent=True)
      all_running &= ('SubState=running' in result or 'SubState=exited' in result)

    return all_running

  def update_units(self):
    (code, result) = execute([
      "systemctl", "list-units", "--no-legend"
    ], silent=True)

    if code != 0:
      return False

    services = [item.split(' ')[0].strip() for item in result.split('\n')]
    services = [item for item in services if item.split('-')[0].split('.')[0] in self.services]

    self.units = services

  def cleanup(self):
    for unit in self.units:
      (code, result) = execute([
        'journalctl', '-o', 'short-precise', '-u', '{}.service'.format(unit), '--no-pager'
      ], silent=True)
      if code == 0:
        with open('/tmp/reports/blackbox-tests/logs/{}.log'.format(unit), 'w') as f:
          f.write(result)

  def teardown(self):
    for unit in self.units:
      execute(['systemctl', 'stop', unit], silent=True)

    self.cleanup()
