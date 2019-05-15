#!/usr/bin/env python
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

from utils import with_deadline, ProgressCounter
from parallel.pool import Pool

class HttpClient(object):

  def __init__(self):
    http = urllib3.PoolManager()
    self.http = http

  @with_deadline(20*60)
  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    total = len(reqs)
    counter = ProgressCounter()

    def try_post(url, payload, bounce=0) -> urllib3.HTTPResponse:
      try:
        resp = self.http.request('POST', url, body=payload, headers={'Content-Type': 'application/json'}, retries=urllib3.Retry(3, redirect=2))
        if resp and resp.status in [504, 503] and bounce < 3:
          return try_post(url, payload, bounce + 1)
        #elif resp and resp.status != 200 and bounce < 3:
        #  return try_post(url, payload, bounce + 1)
        else:
          return resp
      except (urllib3.exceptions.ConnectionError, urllib3.exceptions.RequestError):
        return try_post(url, payload, bounce)

    def process_one(url, body, payload, tenant) -> None:
      try:
        resp = try_post(url, payload)
        if resp and resp.status == 200:
          counter.ok()
          pre_process(resp, url, body, tenant)
        else:
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

  @with_deadline(20*60)
  def get(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    total = len(reqs)
    counter = ProgressCounter()

    def try_get(url, bounce=0) -> urllib3.HTTPResponse:
      try:
        resp = self.http.request('GET', url, retries=urllib3.Retry(3, redirect=2))
        if resp and resp.status in [504, 503] and bounce < 3:
          return try_get(url, bounce + 1)
        #elif resp and resp.status != 200 and bounce < 3:
        #  return try_get(url, bounce + 1)
        else:
          return resp
      except (urllib3.exceptions.ConnectionError, urllib3.exceptions.RequestError):
        return try_get(url, bounce)

    def process_one(url, *args) -> None:
      try:
        resp = try_get(url)
        if resp and resp.status == 200:
          counter.ok()
          pre_process(resp, url, *args)
        else:
          counter.fail()
      except Exception as ex:
        print(ex)
      finally:
        on_progress(counter.progress, total)

    p = Pool()

    for item in reqs:
      p.enqueue(process_one, *item)

    p.run()
    p.join()

    return counter.success, counter.failure
