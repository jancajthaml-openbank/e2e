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
from constants import tenants, site, limit, info, progress, warn, success, took
import api
from http_client import ParallelHttpClient

info("parallelism set to {0}".format(limit))

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
    num_of_requests = 100

    info("preparing creation of {0} health check spams".format(num_of_requests))
    prepared = [ api.prepare_health_check() for x in range(num_of_requests) ]

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    client = ParallelHttpClient()

    info('sending {0} requests'.format(len(prepared)))

    passed, failed, duration = client.get(prepared, on_progress)

    if failed:
      took('{0} health check passed, {1} failed                             '.format(passed, failed), duration, num_of_requests, warn)
    else:
      took('all passed                                                      ', duration, num_of_requests, success)

    ############################################################################

    return True

  def create_random_accounts_parallel(self):
    num_of_accounts = 100

    info("preparing creation of {0} accounts in parallel".format(num_of_accounts))
    prepared = [ api.prepare_create_account("par_" + str(x + 1), bool(secure_random.getrandbits(1))) for x in range(num_of_accounts) ]

    def callback(response, url, request, tenant):
      if response.status_code != 200:
        return None

      self.g_accounts.setdefault(tenant, {})[request['accountNumber']] = {
        'active': request['isBalanceCheck'],
        'balance': 0,
        'transactions': [],
        'currency': request['currency']
      }
      return response

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    client = ParallelHttpClient()

    info('sending {0} requests'.format(len(prepared)))

    passed, failed, duration = client.post(prepared, callback, on_progress)

    if failed:
      took('{0} accounts created, {1} failed                             '.format(passed, failed), duration, num_of_accounts, warn)
    else:
      took('all passed                                                      ', duration, num_of_accounts, success)

    return True

  @with_deadline(timeout=120)
  def create_random_accounts_serial(self):
    num_of_accounts = 10

    info("preparing creation of {0} accounts one by one".format(num_of_accounts))
    prepared = [ api.prepare_create_account("ser_" + str(x + 1), bool(secure_random.getrandbits(1))) for x in range(num_of_accounts) ]

    def callback(response, url, request, tenant):
      if response.status_code != 200:
        return None

      self.g_accounts.setdefault(tenant, {})[request['accountNumber']] = {
        'active': request['isBalanceCheck'],
        'balance': 0,
        'transactions': [],
        'currency': request['currency']
      }
      return response

    info('sending {0} requests'.format(len(prepared)))

    ok = 0
    s_processed = 0

    start = time.time()

    for url, body, payload, tenant in prepared:
      resp = requests.post(url, data=payload, verify=False, timeout=1)
      s_processed += 1
      callback(resp, url, body, tenant)

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

  def create_random_transactions_parallel(self):
    num_of_transactions = 100
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

      info("preparing creation of {0} transactions in parallel for tenant {1}".format(will_generate_transactions, tenant_name))

      prepared.extend(api.prepare_transaction(tenant_name, secure_random.randint(self.transfers["min"], self.transfers["max"]), credit_accounts, debit_account, self.accounts["max_amount"]) for x in range(0, will_generate_transactions, 1))

    def callback(response, url, request, tenant_name):
      if response.status_code != 200:
        return None

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

    ############################################################################

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    client = ParallelHttpClient()

    info('sending {0} requests'.format(len(prepared)))

    passed, failed, duration = client.post(prepared, callback, on_progress)

    if failed:
      took('{0} transactions created, {1} failed                             '.format(passed, failed), duration, num_of_transactions, warn)
    else:
      took('all passed                                                      ', duration, num_of_transactions, success)

    return True

  @with_deadline(timeout=120)
  def create_random_transactions_serial(self):
    num_of_transactions = 10
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

    def callback(response, request, tenant_name):
      if response.status_code != 200:
        return None

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

    ######

    info('sending {0} requests'.format(len(prepared)))

    ok = 0
    s_processed = 0

    start = time.time()
    for url, body, payload, tenant_name in prepared:
      resp = requests.post(url, data=payload, verify=False)
      s_processed += 1
      callback(resp, body, tenant_name)
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

    info("prepared checking balance of {0} accounts in parallel".format(num_of_accounts))

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

    # fixme use httpclient

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
