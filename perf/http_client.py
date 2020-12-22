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

import multiprocessing
import functools


class HttpClient(object):

  def post(self, reqs, on_panic=lambda *args: None):
    total = len(reqs)

    pool = urllib3.PoolManager()

    global process_one

    def process_one(args) -> None:
      (url, body, payload, tenant) = args
      try:
        resp = pool.request('POST', url, body=payload, headers={'Content-Type': 'application/json'})
        resp.release_conn()
        if resp and resp.status in [200, 201, 202]:
          return ([(resp.status, resp.data.decode('utf-8'), url, body, tenant)], [])
        else:
          return ([], [(resp.status, resp.data.decode('utf-8'))])
      except urllib3.exceptions.ProtocolError:
        return process_one(args)
      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return ([], 1)

    results = multiprocessing.Pool(processes=4).map_async(process_one, reqs).get()

    return functools.reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), results)

  def get(self, reqs, on_panic=lambda *args: None):
    total = len(reqs)

    pool = urllib3.PoolManager()

    global process_one

    def process_one(args) -> None:
      (url, body, tenant) = args
      try:
        resp = pool.request('GET', url)
        resp.release_conn()
        if resp and resp.status in [200, 201, 202]:
          return ([(resp.status, resp.data.decode('utf-8'), url, body, tenant)], [])
        else:
          return ([], [(resp.status, resp.data.decode('utf-8'))])
      except urllib3.exceptions.ProtocolError:
        return process_one(args)
      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return ([], 1)

    results = multiprocessing.Pool(processes=4).map_async(process_one, reqs).get()

    return functools.reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), results)
