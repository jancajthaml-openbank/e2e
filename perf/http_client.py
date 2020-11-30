#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import http
import signal
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ssl
try:
  _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
  pass
else:
  ssl._create_default_https_context = _create_unverified_https_context

from utils import ProgressCounter
from parallel.pool import Pool


class HttpClient(object):

  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    total = len(reqs)
    counter = ProgressCounter()
    http = urllib3.PoolManager()

    def process_one(url, body, payload, tenant) -> None:
      try:
        resp = http.request('POST', url, body=payload, headers={'Content-Type': 'application/json'})
        if resp and resp.status in [200, 201, 202]:
          counter.ok()
          pre_process(resp, url, body, tenant)
        else:
          counter.fail()
      except (http.client.RemoteDisconnected, socket.timeout):
        counter.fail()
      except Exception as ex:
        print('error {}'.format(ex))
        os.kill(os.getpid(), signal.SIGINT)
      finally:
        on_progress(counter.progress, total)

    p = Pool()
    for item in reqs:
      p.enqueue(process_one, *item)
    p.run()
    p.join()

    return counter.success, counter.failure

  def get(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    total = len(reqs)
    counter = ProgressCounter()
    http = urllib3.PoolManager()

    def process_one(url, body, tenant) -> None:
      try:
        resp = http.request('GET', url)
        if resp and resp.status in [200, 201, 202]:
          counter.ok()
          pre_process(resp, url, body, tenant)
        else:
          counter.fail()
      except (http.client.RemoteDisconnected, socket.timeout):
        counter.fail()
      except Exception as ex:
        print('error {}'.format(ex))
        os.kill(os.getpid(), signal.SIGINT)
      finally:
        on_progress(counter.progress, total)

    p = Pool()
    for item in reqs:
      p.enqueue(process_one, *item)
    p.run()
    p.join()

    return counter.success, counter.failure
