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

class ParallelHttpClient:

  limit = 30

  def __init__(self):
    adapter = requests.adapters.HTTPAdapter(pool_connections=ParallelHttpClient.limit, pool_maxsize=ParallelHttpClient.limit)
    session = requests.Session()
    session.verify = False
    session.mount('https://', adapter)
    self.session = session

  @with_deadline(timeout=120)
  def post(self, reqs, pre_process, on_progress):

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
  def get(self, reqs, on_progress):

    prepared = [grequests.get(
      url,
      timeout=2,
      session=self.session
    ) for url in reqs]

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
