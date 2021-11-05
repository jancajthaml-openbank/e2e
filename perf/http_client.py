#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from helpers.http import Request
from utils import progress

import multiprocessing
import functools
import itertools


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
      total_errors += errors

      for result in results:
        on_result(*result)

    progress('{1:.2f}% of {0}'.format(total_work, 100))

    return total_success, total_errors

  def post(self, reqs, on_result=lambda *args: None, on_panic=lambda *args: None):
    global on_post_result

    def on_post_result(args) -> None:
      (url, body, payload, tenant) = args

      request = Request(method='POST', url=url)
      request.data = payload
      request.add_header('Content-Type', 'application/json')

      try:
        resp = request.do()
        if resp and resp.status in [200, 201, 202]:
          return ([(resp.status, resp.read().decode('utf-8'), url, body, tenant)], [])
        else:
          return ([], [(resp.status, resp.read().decode('utf-8'))])

      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return ([], [])

    return self.__do(reqs, on_post_result, on_result, on_panic)

  def get(self, reqs, on_result=lambda *args: None, on_panic=lambda *args: None):

    global on_get_result

    def on_get_result(args) -> None:
      (url, body, tenant) = args
      request = Request(method='GET', url=url)

      try:
        resp = request.do()
        if resp and resp.status in [200, 201, 202]:
          return ([(resp.status, resp.read().decode('utf-8'), url, body, tenant)], [])
        else:
          return ([], [(resp.status, resp.read().decode('utf-8'))])

      except Exception as e:
        print('error {}'.format(e))
        on_panic()
        return ([], [])

    return self.__do(reqs, on_get_result, on_result, on_panic)
