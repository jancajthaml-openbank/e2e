#!/usr/bin/env python
# -*- coding: utf-8 -*-

import grequests
import requests

import time

requests.packages.urllib3.disable_warnings()

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from utils import with_deadline, Counter

class HttpClient:

  limit = 100

  def __init__(self):
    adapter = requests.adapters.HTTPAdapter(pool_connections=HttpClient.limit, pool_maxsize=HttpClient.limit)
    session = requests.Session()
    session.verify = False
    session.mount('https://', adapter)
    self.session = session

class SerialHttpClient(HttpClient):

  @with_deadline(timeout=120)
  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):
    ok = Counter()
    fails = Counter()
    progress = Counter()

    start = time.time()

    for url, body, payload, tenant in reqs:
      try:
        resp = self.session.post(url, data=payload, verify=False, timeout=(1, 1))
        if resp and resp.status_code == 200:
          ok.inc()
          pre_process(resp, url, body, tenant)
        else:
          fails.inc()
      except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        fails.inc()
      finally:
        progress.inc()
        on_progress(progress.value, ok.value, fails.value)

    return ok.value, fails.value, time.time() - start

  @with_deadline(timeout=120)
  def get(self, reqs, pre_process, on_progress):
    ok = Counter()
    fails = Counter()
    progress = Counter()

    start = time.time()

    for url, *args in reqs:
      try:
        resp = self.session.get(url, verify=False, timeout=(1, 1))
        if resp and resp.status_code == 200:
          ok.inc()
          pre_process(resp, url, *args)
        else:
          fails.inc()
      except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
        fails.inc()
      finally:
        progress.inc()
        on_progress(progress.value, ok.value, fails.value)

    return ok.value, fails.value, time.time() - start

class ParallelHttpClient(HttpClient):

  @with_deadline(timeout=120)
  def post(self, reqs, pre_process=lambda *args: None, on_progress=lambda *args: None):

    def partial(cb, url, request, tenant):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, url, request, tenant)
      return wrapper

    prepared = [grequests.post(
      url,
      timeout=2,
      data=payload,
      session=self.session,
      hooks={'response': partial(pre_process, url, body, tenant)}
    ) for url, body, payload, tenant in reqs]

    ok = Counter()
    fails = Counter()
    progress = Counter()

    start = time.time()

    for resp in grequests.imap(prepared, size=10):
      progress.inc()
      if resp and resp.status_code == 200:
        ok.inc()
      else:
        fails.inc()

      on_progress(progress.value, ok.value, fails.value)

    return ok.value, fails.value, time.time() - start

  @with_deadline(timeout=120)
  def get(self, reqs, pre_process, on_progress):

    def partial(cb, url, request, tenant):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, url, request, tenant)
      return wrapper

    prepared = [grequests.get(
      url,
      timeout=2,
      session=self.session,
      hooks={'response': partial(pre_process, url, *args)}
    ) for url, *args in reqs]

    ok = Counter()
    fails = Counter()
    progress = Counter()

    start = time.time()

    for resp in grequests.imap(prepared, size=10):
      progress.inc()
      if resp and resp.status_code == 200:
        ok.inc()
      else:
        fails.inc()
      if on_progress:
        on_progress(progress.value, ok.value, fails.value)

    return ok.value, fails.value, time.time() - start
