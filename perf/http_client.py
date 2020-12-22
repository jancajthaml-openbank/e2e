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
import itertools
from utils import progress


class HttpClient(object):

  def __do(self, reqs, on_work=lambda *args: None, on_result=lambda *args: None, on_panic=lambda *args: None):
    total_success = 0
    total_errors = list()
    total_progress = 0
    total_work = len(reqs)
    chunk_size = 1000

    progress('{1:.2f}% of {0}'.format(total_work, 0))

    for offset in range(0, total_work, chunk_size):
      work = reqs[offset:offset+chunk_size]
      if not work:
        continue

      futures = multiprocessing.Pool(processes=10).map_async(on_work, work).get()
      (results, errors) = functools.reduce(lambda x, y: (x[0] + y[0], x[1] + y[1]), futures)

      total_progress += len(work)

      progress('{1:.2f}% of {0}'.format(total_work, 100 * (total_progress/total_work)))

      total_success += len(results)
      for result in results:
        on_result(*result)

    progress('{1:.2f}% of {0}'.format(total_work, 100))

    return total_success, total_errors

  def post(self, reqs, on_result=lambda *args: None, on_panic=lambda *args: None):
    pool = urllib3.PoolManager()

    global on_post_result

    def on_post_result(args) -> None:
      (url, body, payload, tenant) = args
      try:
        resp = pool.request('POST', url, body=payload, headers={'Content-Type': 'application/json'})
        resp.release_conn()
        if resp and resp.status in [200, 201, 202]:
          return ([(resp.status, resp.data, url, body, tenant)], [])
        else:
          return ([], [(resp.status, resp.data)])
      except urllib3.exceptions.ProtocolError:
        return on_post_result(args)
      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return ([], [])

    return self.__do(reqs, on_post_result, on_result, on_panic)

  def get(self, reqs, on_result=lambda *args: None, on_panic=lambda *args: None):

    pool = urllib3.PoolManager()

    global on_get_result

    def on_get_result(args) -> None:
      (url, body, tenant) = args
      try:
        resp = pool.request('GET', url)
        resp.release_conn()
        if resp and resp.status in [200, 201, 202]:
          return ([(resp.status, resp.data, url, body, tenant)], [])
        else:
          return ([], [(resp.status, resp.data)])
      except urllib3.exceptions.ProtocolError:
        return on_get_result(args)
      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return ([], [])

    return self.__do(reqs, on_get_result, on_result, on_panic)
