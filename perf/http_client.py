#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import requests
requests.packages.urllib3.disable_warnings()

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from utils import with_deadline, Counter
from async.pool import Pool

class HttpClient(object):

  def __init__(self):
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=0, pool_block=False)
    session = requests.Session()
    session.verify = False
    session.mount('https://', adapter)
    self.session = session

  @with_deadline(5*60)
  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    ok = Counter()
    fails = Counter()
    progress = Counter()

    def try_post(url, payload) -> requests.Response:
      try:
        resp = self.session.post(url, data=payload, verify=False, timeout=(1, 1))
        if resp and resp.status_code == 504:
          return try_post(url, payload)
        return resp
      except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        return try_post(url, payload)

    def process_one(url, body, payload, tenant) -> None:
      try:
        resp = try_post(url, payload)
        if resp and resp.status_code == 200:
          ok.inc()
          pre_process(resp, url, body, tenant)
        else:
          fails.inc()
      except Exception as ex:
        print(ex)
        fails.inc()
      finally:
        progress.inc()
        on_progress(progress.value, ok.value, fails.value)

    p = Pool()

    for item in reqs:
      p.enqueue(process_one, *item)

    start = time.time()

    p.run()
    p.join()

    return ok.value, fails.value, time.time() - start

  @with_deadline(5*60)
  def get(self, reqs, pre_process, on_progress):
    ok = Counter()
    fails = Counter()
    progress = Counter()

    def try_get(url) -> requests.Response:
      try:
        resp = self.session.get(url, verify=False, timeout=(1, 1))
        if resp and resp.status_code == 504:
          return try_get(url)
        return resp
      except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        return try_get(url)

    def process_one(url, *args) -> None:
      try:
        resp = try_get(url)
        if resp and resp.status_code == 200:
          ok.inc()
          pre_process(resp, url, *args)
        else:
          fails.inc()
      except Exception as ex:
        print(ex)
        fails.inc()
      finally:
        progress.inc()
        on_progress(progress.value, ok.value, fails.value)

    p = Pool()

    for item in reqs:
      p.enqueue(process_one, *item)

    start = time.time()

    p.run()
    p.join()

    return ok.value, fails.value, time.time() - start
