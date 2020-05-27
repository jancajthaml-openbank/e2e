#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

  def __init__(self):
    http = urllib3.PoolManager()
    self.http = http

  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    total = len(reqs)
    counter = ProgressCounter()

    def process_one(url, body, payload, tenant) -> None:
      try:
        resp = self.http.request('POST', url, body=payload, headers={'Content-Type': 'application/json'}, retries=urllib3.Retry(0, redirect=0), timeout=45)
        if resp and resp.status == 200:
          counter.ok()
          pre_process(resp, url, body, tenant)
        else:
          counter.fail()
      except urllib3.exceptions.ProtocolError as ex:
        print('procotol error {}'.format(ex))
        counter.fail()
      except Exception as ex:
        print(ex)
        counter.fail()
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

    def process_one(url, body, tenant) -> None:
      try:
        resp = self.http.request('GET', url, retries=urllib3.Retry(0, redirect=0), timeout=45)
        if resp and resp.status == 200:
          counter.ok()
          pre_process(resp, url, body, tenant)
        else:
          counter.fail()
      except urllib3.exceptions.ProtocolError as ex:
        print('procotol error {}'.format(ex))
        counter.fail()
      except Exception as ex:
        print(ex)
        counter.fail()
      finally:
        on_progress(counter.progress, total)

    p = Pool()
    for item in reqs:
      p.enqueue(process_one, *item)
    p.run()
    p.join()

    return counter.success, counter.failure
