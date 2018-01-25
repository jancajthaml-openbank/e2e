#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import randint, getrandbits
import time
import ujson as json
import grequests
import requests
from requests.adapters import HTTPAdapter

from constants import tenant, site, limit, tty, nodes, info, progress, warn, success, took
import api

info("parallelism set to {0}".format(limit))
info("running in tty {0}".format(tty))
info("server running at {0}".format(site + '/v1/sparrow'))
info("tenant set to {0}".format(tenant))

class StressTest:
  accounts = {
    #"min": max(100, int((limit * 20 * nodes) / 10)) * 10,
    #"max": max(1000, int((limit * 200 * nodes) / 10)) * 10,
    "max_amount": 100000
  }

  transactions = {
    "min": limit * 1 * nodes * 10,
    "max": limit * 2 * nodes * 10
  }

  transfers = {
    "min": 1,
    "max": 5
  }

  g_accounts = {}

  @staticmethod
  def health_check_spam():
    num_of_requests = max(1000, limit * 2)

    info("preparing creation of {0} health check spams".format(num_of_requests))
    prepared = [ api.prepare_health_check() for x in range(num_of_requests) ]

    info('sending {0} requests'.format(len(prepared)))

    session = requests.Session()
    session.mount('http://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.get(url, session=session, timeout=10) for url in prepared]
    s_passed = 0
    s_failed = 0
    s_processed = 0

    start = time.time()
    for resp in grequests.imap(reqs, size=limit):
      s_processed += 1
      if resp is None:
        s_failed += 1
      else:
        s_passed += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, s_passed, s_failed))

    ok = s_passed
    fail = num_of_requests - ok

    if fail:
      took('{0} health check passed, {1} failed                             '.format(ok, fail), time.time() - start, num_of_requests, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_requests, success)

    ######

    return True

  def create_random_accounts_parallel(self):
    num_of_accounts = 100

    info("preparing creation of {0} accounts in parallel of {1}".format(num_of_accounts, limit))
    prepared = [ api.prepare_create_account("par_" + str(x + 1), bool(getrandbits(1))) for x in range(num_of_accounts) ]

    def partial(cb, request):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, request)
      return wrapper

    def account_callback(response, req):
      if response.status_code == 200:
        request = json.loads(req)
        self.g_accounts[request['accountNumber']] = {
          'active': request['isBalanceCheck'],
          'balance': 0,
          'transactions': [],
          'currency': request['currency']
        }
        return response
      else:
        return None

    info('sending {0} requests'.format(len(prepared)))

    session = requests.Session()
    session.mount('http://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.post(url, data=body, session=session, hooks={'response': partial(account_callback, body)}) for url, body in prepared]

    ok = 0
    s_processed = 0

    start = time.time()
    for resp in grequests.imap(reqs, size=limit):
      s_processed += 1
      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_accounts - ok

    if fail:
      took('{0} accounts created, {1} failed                             '.format(ok, fail), time.time() - start, num_of_accounts, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_accounts, success)

    ######

    return True

  def create_random_accounts_serial(self):
    num_of_accounts = 10
    info("preparing creation of {0} accounts one by one".format(num_of_accounts))

    prepared = [ api.prepare_create_account("ser_" + str(x + 1), bool(getrandbits(1))) for x in range(num_of_accounts) ]

    #def partial(cb, request):
     # def wrapper(response, *extra_args, **kwargs):
      #  return cb(response, request)
      #return wrapper

    def account_callback(response, req):
      if response.status_code == 200:
        request = json.loads(req)
        self.g_accounts[request['accountNumber']] = {
          'active': request['isBalanceCheck'],
          'balance': 0,
          'transactions': [],
          'currency': request['currency']
        }
        return response
      else:
        return None

    info('sending {0} requests'.format(len(prepared)))

    ok = 0
    s_processed = 0

    start = time.time()

    for url, body in prepared:
      resp = requests.post(url, data=body)
      s_processed += 1
      account_callback(resp, body)

      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_accounts - ok

    if fail:
      took('{0} accounts created, {1} failed                             '.format(ok, fail), time.time() - start, num_of_accounts, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_accounts, success)

    ######

    return True

  def create_random_transactions_parallel(self):
    num_of_transactions = 5000

    all_accounts = list(self.g_accounts.keys())
    credit_accounts = [i for i in all_accounts if self.g_accounts[i]['active']]
    debit_account = [i for i in all_accounts if not self.g_accounts[i]['active']]

    info("preparing creation of {0} transactions in parallel of {1}".format(num_of_transactions, limit))

    prepared = [ api.prepare_transaction(randint(self.transfers["min"], self.transfers["max"]), credit_accounts, debit_account, self.accounts["max_amount"]) for x in range(0, num_of_transactions, 1) ]

    def partial(cb, request):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, request)
      return wrapper

    def transaction_callback(response, request):
      if response.status_code == 200:
        transaction = response.json()['transaction']

        for transfer in request['transfers']:
          amount = transfer['amount']
          credit = transfer['credit']
          debit = transfer['debit']

          self.g_accounts[credit]['balance'] += float(amount)
          self.g_accounts[debit]['balance'] -= float(amount)

          self.g_accounts[credit]['transactions'].append(transaction)
          self.g_accounts[debit]['transactions'].append(transaction)

        return response
      else:
        return None

    ######

    info('sending {0} requests'.format(len(prepared)))

    session = requests.Session()
    session.mount('http://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.post(url, data=body, session=session, hooks={'response': partial(transaction_callback, request)}) for url, request, body in prepared]

    ok = 0
    s_processed = 0

    start = time.time()
    for resp in grequests.imap(reqs, size=limit):
      s_processed += 1
      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_transactions - ok

    if fail:
      took('{0} transactions created, {1} failed                             '.format(ok, fail), time.time() - start, num_of_transactions, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_transactions, success)

    return True

  def create_random_transactions_serial(self):
    num_of_transactions = 50

    all_accounts = list(self.g_accounts.keys())
    credit_accounts = [i for i in all_accounts if self.g_accounts[i]['active']]
    debit_account = [i for i in all_accounts if not self.g_accounts[i]['active']]

    info("preparing creation of {0} transactions one by one".format(num_of_transactions))

    prepared = [ api.prepare_transaction(randint(self.transfers["min"], self.transfers["max"]), credit_accounts, debit_account, self.accounts["max_amount"]) for x in range(0, num_of_transactions, 1) ]

    def transaction_callback(response, request):
      if response.status_code == 200:
        transaction = response.json()['transaction']

        for transfer in request['transfers']:
          amount = transfer['amount']
          credit = transfer['credit']
          debit = transfer['debit']

          self.g_accounts[credit]['balance'] += float(amount)
          self.g_accounts[debit]['balance'] -= float(amount)

          self.g_accounts[credit]['transactions'].append(transaction)
          self.g_accounts[debit]['transactions'].append(transaction)

        return response
      else:
        return None

    ######

    info('sending {0} requests'.format(len(prepared)))

    ok = 0
    s_processed = 0

    start = time.time()
    for url, request, body in prepared:
      resp = requests.post(url, data=body)
      s_processed += 1
      transaction_callback(resp, request)

      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_transactions - ok

    if fail:
      took('{0} transactions created, {1} failed                             '.format(ok, fail), time.time() - start, num_of_transactions, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_transactions, success)

    return True

  def balance_cancel_out_check(self):
    info('checking that sum of all balances is 0.0')


    total = 0

    start = time.time()
    for meta in self.g_accounts.values():
      total += meta['balance']

    if total != 0:
      took('sum of all active and pasive accounts it non-zero: {0}'.format(total), time.time() - start, 0, warn)
    else:
      took('all balances cancels out', time.time() - start, 0, success)


  def check_balances_serial(self):
    num_of_accounts = len(self.g_accounts.keys())
    info("preparing checking balance of {0} accounts one by one".format(num_of_accounts))

    #prepared = [ api.prepare_create_account("ser_" + str(self.accounts["max"] + x + 1), bool(getrandbits(1))) for x in range(num_of_accounts) ]
    prepared = [ api.prepare_get_balance(number, reference) for number, reference in self.g_accounts.items() ]

    #def partial(cb, request):
    #  def wrapper(response, *extra_args, **kwargs):
    #    return cb(response, request)
    #  return wrapper

    def account_callback(response, req):
      content = response.json()

      if response.status_code == 200:
        if content['currency'] == reference['currency'] and content['balance'] == reference['balance']:
          return response
        else:
          return None
      else:
        return None

    info('sending {0} requests'.format(len(prepared)))

    ok = 0
    s_processed = 0
    start = time.time()
    for url, reference in prepared:
      resp = requests.get(url)
      s_processed += 1
      account_callback(resp, reference)

      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_accounts - ok

    if fail:
      took('{0} balance validated, {1} failed                             '.format(ok, fail), time.time() - start, num_of_accounts, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_accounts, success)

    ######

    return True

  def check_balances_parallel(self):
    num_of_accounts = len(self.g_accounts.keys())

    info("preparing checking balance of {0} accountsin parallel of {1}".format(num_of_accounts, limit))
    prepared = [ api.prepare_get_balance(number, reference) for number, reference in self.g_accounts.items() ]

    def partial(cb, reference):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, reference)
      return wrapper

    # fixme does not work as expected
    def account_callback(response, reference):
      content = response.json()

      if response.status_code == 200:
        if content['currency'] == reference['currency'] and content['balance'] == reference['balance']:
          return response
        else:
          return None
      else:
        return None

    info('sending {0} requests'.format(len(prepared)))

    session = requests.Session()
    session.mount('http://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.get(url, session=session, hooks={'response': partial(account_callback, reference)}) for url, reference in prepared]
    ok = 0
    s_processed = 0

    start = time.time()
    for resp in grequests.imap(reqs, size=limit):
      s_processed += 1
      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_accounts - ok

    if fail:
      took('{0} balance validated, {1} failed                             '.format(ok, fail), time.time() - start, num_of_accounts, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_accounts, success)

    ######

    return True

  def stress_run_health_reference(self):
    # reference throughtput (200 OK empty PING)
    self.health_check_spam()

  def stress_run_accounts_only(self):
    self.create_random_accounts_serial()
    self.create_random_accounts_parallel()

  def stress_run(self):
    self.create_random_accounts_serial()
    self.create_random_accounts_parallel()

    # fixme add reset
    # fixme split single vs multitransaction
    # fixme time and measure average
    self.create_random_transactions_serial()
    self.create_random_transactions_parallel()

    self.check_balances_serial()
    self.check_balances_parallel()

    self.balance_cancel_out_check()


#    self.check_balances()
