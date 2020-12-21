#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import os
#import errno
#import http
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ssl
try:
  _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
  pass
else:
  ssl._create_default_https_context = _create_unverified_https_context

import multiprocessing


class HttpClient(object):

  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None, on_panic=lambda *args: None):
    total = len(reqs)

    global counter

    pool = urllib3.PoolManager()

    global process_one

    def process_one(args) -> None:
      (url, body, payload, tenant) = args
      try:
        resp = pool.request('POST', url, body=payload, headers={'Content-Type': 'application/json'})
        resp.release_conn()
        if resp and resp.status in [200, 201, 202]:
          pre_process(resp, url, body, tenant)
          return (1, 0)
        else:
          return (0, 1)
      except urllib3.exceptions.ProtocolError:
        return process_one(url, body, tenant)
      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return (0, 1)

    results = multiprocessing.Pool(processes=4).map_async(process_one, reqs).get()

    (ok, failed) = reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), results)

    return ok, failed

  def get(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None, on_panic=lambda *args: None):
    total = len(reqs)

    global counter

    counter = ProgressCounter()
    pool = urllib3.PoolManager()

    global process_one

    def process_one(args) -> None:
      (url, body, payload, tenant) = args
      try:
        resp = pool.request('GET', url)
        resp.release_conn()
        if resp and resp.status in [200, 201, 202]:
          pre_process(resp, url, body, tenant)
          return (1, 0)
        else:
          return (0, 1)
      except urllib3.exceptions.ProtocolError:
        return process_one(url, body, tenant)
      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return (0, 1)

    results = multiprocessing.Pool(processes=4).map_async(process_one, reqs).get()

    (ok, failed) = reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), results)
    return ok, failed
