#!/usr/bin/env python
# -*- coding: utf-8 -*-


import requests
requests.packages.urllib3.disable_warnings()

import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from utils import with_deadline, ProgressCounter
from async.pool import Pool

class HttpClient(object):

  def __init__(self):
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=0, pool_block=False)
    session = requests.Session()
    session.verify = False
    session.mount('https://', adapter)
    self.session = session

  @with_deadline(10*60)
  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    counter = ProgressCounter()

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
          counter.ok()
          pre_process(resp, url, body, tenant)
        else:
          counter.fail()
      except Exception as ex:
        print(ex)
        counter.fail()
      finally:
        on_progress(counter.progress, counter.success, counter.failure)

    p = Pool()

    for item in reqs:
      p.enqueue(process_one, *item)

    p.run()
    p.join()

    return counter.success, counter.failure

  @with_deadline(10*60)
  def get(self, reqs, pre_process, on_progress):
    counter = ProgressCounter()

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
          counter.ok()
          pre_process(resp, url, *args)
        else:
          counter.fail()
      except Exception as ex:
        print(ex)
      finally:
        on_progress(counter.progress, counter.success, counter.failure)

    p = Pool()

    for item in reqs:
      p.enqueue(process_one, *item)

    p.run()
    p.join()

    return counter.success, counter.failure
