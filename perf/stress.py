#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

secure_random = random.SystemRandom()

import time
import ujson as json
import grequests
import requests
from requests.adapters import HTTPAdapter
from utils import with_deadline
from constants import tenants, site, limit, tty, info, progress, warn, success, took
import api

info("parallelism set to {0}".format(limit))
info("running in tty {0}".format(tty))

class StressTest:

  accounts = {
    "max_amount": 100000
  }

  transfers = {
    "min": 1,
    "max": 10
  }

  g_accounts = {}

  @staticmethod
  def health_check_spam():
    num_of_requests = max(100, limit * 2)

    info("preparing creation of {0} health check spams".format(num_of_requests))
    prepared = [ api.prepare_health_check() for x in range(num_of_requests) ]

    info('sending {0} requests'.format(len(prepared)))

    session = requests.Session()
    session.verify = False
    session.mount('https://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.get(url, session=session, timeout=2) for url in prepared]
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

    ############################################################################

    return True

  @with_deadline(timeout=120)
  def create_random_accounts_parallel(self):
    num_of_accounts = int(1e2) # fixme to env

    info("preparing creation of {0} accounts in parallel of {1}".format(num_of_accounts, limit))
    prepared = [ api.prepare_create_account("par_" + str(x + 1), bool(secure_random.getrandbits(1))) for x in range(num_of_accounts) ]

    def partial(cb, request, tenant):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, request, tenant)
      return wrapper

    def account_callback(response, req, tenant):
      if response.status_code == 200:
        request = json.loads(req)
        self.g_accounts.setdefault(tenant, {})[request['accountNumber']] = {
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
    session.verify = False
    session.mount('https://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.post(url, data=body, session=session, hooks={'response': partial(account_callback, body, tenant)}) for url, body, tenant in prepared]

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

    ############################################################################

    return True

  @with_deadline(timeout=120)
  def create_random_accounts_serial(self):
    num_of_accounts = int(1e1) # fixme to env

    info("preparing creation of {0} accounts one by one".format(num_of_accounts))
    prepared = [ api.prepare_create_account("ser_" + str(x + 1), bool(secure_random.getrandbits(1))) for x in range(num_of_accounts) ]

    def account_callback(response, req, tenant):
      if response.status_code == 200:
        request = json.loads(req)
        self.g_accounts.setdefault(tenant, {})[request['accountNumber']] = {
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

    for url, body, tenant in prepared:
      resp = requests.post(url, data=body, verify=False)
      s_processed += 1
      account_callback(resp, body, tenant)

      if resp and resp.status_code == 200:
        ok += 1

      progress('processed: {0}, passed: {1}, failed: {2}'.format(s_processed, ok, s_processed - ok))

    fail = num_of_accounts - ok

    if fail:
      took('{0} accounts created, {1} failed                             '.format(ok, fail), time.time() - start, num_of_accounts, warn)
    else:
      took('all passed                                                      ', time.time() - start, num_of_accounts, success)

    ############################################################################

    return True

  @with_deadline(timeout=120)
  def create_random_transactions_parallel(self):
    num_of_transactions = int(3*1e2) # fixme to env
    partitions = []
    chunks = len(self.g_accounts)

    for _ in range(chunks):
      division = int(num_of_transactions / chunks)
      partitions.append(division)

    partitions[secure_random.randrange(0, chunks)] += int(num_of_transactions - sum(partitions))
    partitions = list(partitions)

    prepared = []
    for tenant_name, accounts in self.g_accounts.items():
      will_generate_transactions = partitions.pop()

      all_accounts = accounts.keys()

      credit_accounts = [i for i in all_accounts if self.g_accounts[tenant_name][i]['active']]
      debit_account = [i for i in all_accounts if not self.g_accounts[tenant_name][i]['active']]

      info("preparing creation of {0} transactions one by one for tenant {1}".format(will_generate_transactions, tenant_name))

      prepared.extend(api.prepare_transaction(tenant_name, secure_random.randint(self.transfers["min"], self.transfers["max"]), credit_accounts, debit_account, self.accounts["max_amount"]) for x in range(0, will_generate_transactions, 1))

    def partial(cb, request, tenant_name):
      def wrapper(response, *extra_args, **kwargs):
        return cb(response, request, tenant_name)
      return wrapper

    def transaction_callback(response, request, tenant_name):
      if response.status_code == 200:
        transaction = response.json()['transaction']

        for transfer in request['transfers']:
          amount = transfer['amount']
          credit = transfer['credit']
          debit = transfer['debit']

          self.g_accounts[tenant_name][credit]['balance'] += float(amount)
          self.g_accounts[tenant_name][debit]['balance'] -= float(amount)

          self.g_accounts[tenant_name][credit]['transactions'].append(transaction)
          self.g_accounts[tenant_name][debit]['transactions'].append(transaction)

        return response
      else:
        return None

    ############################################################################

    info('sending {0} requests'.format(len(prepared)))

    session = requests.Session()
    session.verify = False
    session.mount('https://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
    reqs = [grequests.post(url, data=body, session=session, hooks={'response': partial(transaction_callback, request, tenant_name)}) for url, request, body, tenant_name in prepared]

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

  @with_deadline(timeout=120)
  def create_random_transactions_serial(self):
    num_of_transactions = int(3*1e1) # fixme to env
    partitions = []
    chunks = len(self.g_accounts)

    for _ in range(chunks):
      division = int(num_of_transactions / chunks)
      partitions.append(division)

    partitions[secure_random.randrange(0, chunks)] += int(num_of_transactions - sum(partitions))
    partitions = list(partitions)

    prepared = []
    for tenant_name, accounts in self.g_accounts.items():
      will_generate_transactions = partitions.pop()
      all_accounts = accounts.keys()

      credit_accounts = [i for i in all_accounts if self.g_accounts[tenant_name][i]['active']]
      debit_account = [i for i in all_accounts if not self.g_accounts[tenant_name][i]['active']]

      info("preparing creation of {0} transactions one by one for tenant {1}".format(will_generate_transactions, tenant_name))

      prepared.extend(api.prepare_transaction(tenant_name, secure_random.randint(self.transfers["min"], self.transfers["max"]), credit_accounts, debit_account, self.accounts["max_amount"]) for x in range(0, will_generate_transactions, 1))

    def transaction_callback(response, request, tenant_name):
      if response.status_code == 200:
        transaction = response.json()['transaction']

        for transfer in request['transfers']:
          amount = transfer['amount']
          credit = transfer['credit']
          debit = transfer['debit']

          self.g_accounts[tenant_name][credit]['balance'] += float(amount)
          self.g_accounts[tenant_name][debit]['balance'] -= float(amount)

          self.g_accounts[tenant_name][credit]['transactions'].append(transaction)
          self.g_accounts[tenant_name][debit]['transactions'].append(transaction)

        return response
      else:
        return None

    ######

    info('sending {0} requests'.format(len(prepared)))

    ok = 0
    s_processed = 0

    start = time.time()
    for url, request, body, tenant_name in prepared:
      resp = requests.post(url, data=body, verify=False)
      s_processed += 1
      transaction_callback(resp, request, tenant_name)
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
    for accounts in self.g_accounts.values():
      for meta in accounts.values():
        total += meta['balance']

    if total != 0:
      took('sum of all active and pasive accounts it non-zero: {0}'.format(total), time.time() - start, 0, warn)
    else:
      took('all balances cancels out', time.time() - start, 0, success)

  @with_deadline(timeout=120)
  def check_balances_serial(self):
    num_of_accounts = 0

    prepared = []
    for tenant_name, accounts in self.g_accounts.items():
      for account_name, reference in accounts.items():
        num_of_accounts+=1
        prepared.append(api.prepare_get_balance(tenant_name, account_name, reference))

    info("prepared checking balance of {0} accounts one by one".format(num_of_accounts))

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
      resp = requests.get(url, verify=False)
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

    ############################################################################

    return True

  @with_deadline(timeout=120)
  def check_balances_parallel(self):
    num_of_accounts = 0

    prepared = []
    for tenant_name, accounts in self.g_accounts.items():
      for account_name, reference in accounts.items():
        num_of_accounts+=1
        prepared.append(api.prepare_get_balance(tenant_name, account_name, reference))

    info("prepared checking balance of {0} accounts in parallel of {1}".format(num_of_accounts, limit))

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
    session.verify = False
    session.mount('https://', HTTPAdapter(pool_connections=limit, pool_maxsize=limit))
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

    self.check_balances_serial()
    self.check_balances_parallel()

    self.balance_cancel_out_check()

  def stress_run(self):
    self.create_random_accounts_serial()
    self.create_random_accounts_parallel()

    self.create_random_transactions_serial()
    self.create_random_transactions_parallel()

    self.check_balances_serial()
    self.check_balances_parallel()

    self.balance_cancel_out_check()

    ############################################################################
