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
from constants import tenants, site, info, progress, warn, success, took
import api
from http_client import ParallelHttpClient, SerialHttpClient

class StressTest:

  accounts = {
    "max_amount": 100000
  }

  min_accounts = 10
  max_accounts = 20

  min_transactions = 100
  max_transactions = 200

  transfers = {
    "min": 1,
    "max": 10
  }

  g_accounts = {}

  def __init__(self):
    from constants import tenants

    for tenant in tenants:
      self.g_accounts[tenant] = {}

    self.min_accounts = max(len(tenants) * 4, 300)
    self.max_accounts = self.min_accounts * 5

  @staticmethod
  def health_check_spam():
    num_of_requests = 100

    info("preparing creation of {0} health check spams".format(num_of_requests))
    prepared = [ api.prepare_health_check() for x in range(num_of_requests) ]

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    client = ParallelHttpClient()

    #info('sending {0} requests'.format(len(prepared)))

    passed, failed, duration = client.get(prepared, lambda *args: None, on_progress)

    if failed:
      took('{0} health check passed, {1} failed                             '.format(passed, failed), duration, num_of_requests, warn)
    else:
      took('all passed                                                      ', duration, num_of_requests, success)

    ############################################################################

    return True

  def create_random_accounts(self):

    def callback(response, url, request, tenant):
      if response.status_code != 200:
        return None

      #print(tenant, request['accountNumber'], request['isBalanceCheck'])

      self.g_accounts[tenant][request['accountNumber']] = {
        'active': request['isBalanceCheck'],
        'balance': 0,
        'transactions': [],
        'currency': request['currency']
      }
      return response

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    def parallel(num_of_accounts):
      partitions = []
      chunks = len(self.g_accounts)

      for _ in range(chunks):
        division = int(num_of_accounts / chunks)
        partitions.append(division)

      partitions[secure_random.randrange(0, chunks)] += int(num_of_accounts - sum(partitions))
      partitions = list(partitions)

      prepared = []
      counter = 1
      active = True
      for tenant_name in self.g_accounts.keys():
        will_generate_accounts = partitions.pop()

        info("preparing creation of {0} account for tenant {1}".format(will_generate_accounts, tenant_name))
        for x in range(will_generate_accounts):
          prepared.append(api.prepare_create_account(tenant_name, "p_" + str(counter), active))
          counter += 1
          active = not active

      info('in parallel')
      client = ParallelHttpClient()
      passed, failed, duration = client.post(prepared, callback, on_progress)

      if failed:
        took('{0} accounts created, {1} failed                             '.format(passed, failed), duration, num_of_accounts, warn)
      else:
        took('all passed                                                      ', duration, num_of_accounts, success)

    def serial(num_of_accounts):

      partitions = []
      chunks = len(self.g_accounts)

      for _ in range(chunks):
        division = int(num_of_accounts / chunks)
        partitions.append(division)

      partitions[secure_random.randrange(0, chunks)] += int(num_of_accounts - sum(partitions))
      partitions = list(partitions)

      prepared = []
      counter = 1
      active = True
      for tenant_name in self.g_accounts.keys():
        will_generate_accounts = partitions.pop()

        info("preparing creation of {0} account for tenant {1}".format(will_generate_accounts, tenant_name))
        for x in range(will_generate_accounts):
          prepared.append(api.prepare_create_account(tenant_name, "s_" + str(counter), active))
          counter += 1
          active = not active

      info('one by one')
      client = SerialHttpClient()
      passed, failed, duration = client.post(prepared, callback, on_progress)

      if failed:
        took('{0} accounts created, {1} failed                             '.format(passed, failed), duration, num_of_accounts, warn)
      else:
        took('all passed                                                      ', duration, num_of_accounts, success)

    number_of_accounts = secure_random.randrange(self.min_accounts, self.max_accounts)

    serial(number_of_accounts)
    parallel(number_of_accounts)

    return True

  def create_random_transactions(self):

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

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    def parallel(num_of_transactions):
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

        info("preparing creation of {0} transactions for tenant {1}".format(will_generate_transactions, tenant_name))

        prepared.extend(api.prepare_transaction(tenant_name, secure_random.randint(self.transfers["min"], self.transfers["max"]), credit_accounts, debit_account, self.accounts["max_amount"]) for x in range(0, will_generate_transactions, 1))

      info('in parallel')
      client = ParallelHttpClient()
      passed, failed, duration = client.post(prepared, callback, on_progress)

      if failed:
        took('{0} transactions created, {1} failed                             '.format(passed, failed), duration, num_of_transactions, warn)
      else:
        took('all passed                                                      ', duration, num_of_transactions, success)

    def serial(num_of_transactions):
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

      info('one by one')
      client = SerialHttpClient()
      passed, failed, duration = client.post(prepared, callback, on_progress)

      if failed:
        took('{0} transactions created, {1} failed                             '.format(passed, failed), duration, num_of_transactions, warn)
      else:
        took('all passed                                                      ', duration, num_of_transactions, success)

    number_of_transactions = secure_random.randrange(self.min_transactions, self.max_transactions)

    serial(number_of_transactions)
    parallel(number_of_transactions)

    return True

  def check_balances(self):
    num_of_accounts = 0

    prepared = []
    for tenant_name, accounts in self.g_accounts.items():
      for account_name, reference in accounts.items():
        num_of_accounts += 1
        prepared.append(api.prepare_get_balance(tenant_name, account_name, reference))

    info("prepared checking balance of {0} accounts".format(num_of_accounts))

    def callback(response, url, request, tenant_name):
      if response.status_code != 200:
        return None

      content = response.json()
      if content['currency'] == request['currency'] and content['balance'] == request['balance']:
        return response
      else:
        return None

    def on_progress(processed, passed, failed):
      progress('processed: {0}, passed: {1}, failed: {2}'.format(processed, passed, failed))

    def parallel():
      info('in parallel')
      client = ParallelHttpClient()
      passed, failed, duration = client.get(prepared, callback, on_progress)

      if failed:
        took('{0} balance validated, {1} failed                             '.format(passed, failed), duration, num_of_accounts, warn)
      else:
        took('all passed                                                      ', duration, num_of_accounts, success)

    def serial():
      info('one by one')
      client = SerialHttpClient()
      passed, failed, duration = client.get(prepared, callback, on_progress)

      if failed:
        took('{0} balance validated, {1} failed                             '.format(passed, failed), duration, num_of_accounts, warn)
      else:
        took('all passed                                                      ', duration, num_of_accounts, success)

    serial()
    parallel()

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

  def stress_run_health_reference(self):
    # reference throughtput (200 OK empty PING)
    self.health_check_spam()

  def stress_run_accounts_only(self):
    self.create_random_accounts()

    self.check_balances()

    self.balance_cancel_out_check()

  def stress_run(self):
    self.create_random_accounts()

    #import json
    #print(json.dumps(self.g_accounts, indent=4, sort_keys=True))

    self.create_random_transactions()

    self.check_balances()

    #self.balance_cancel_out_check()

    ############################################################################
