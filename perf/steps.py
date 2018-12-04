#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
secure_random = random.SystemRandom()

import time
from utils import info, progress, warn, success, Counter, timeit
from http_client import HttpClient

class Steps:

  def __init__(self, integration):
    self.integration = integration
    self.__acc_counter = Counter()

  def random_targeted_accounts(self, tenant_name, number_of_accounts=None):
    with timeit('random_targeted_accounts(_, {0}, {1})'.format(tenant_name, num_of_accounts)):

      def callback(response, url, request, tenant):
        if response.status != 200:
          return None

        self.integration.update_account(tenant, request['accountNumber'], {
          'accountNumber': request['accountNumber'],
          'active': request['isBalanceCheck'],
          'balance': 0,
          'transactions': [],
          'currency': request['currency']
        })

        return response

      def on_progress(processed, passed, failed):
        progress('{0} [ passed: {1}, failed: {2} ]'.format(processed, passed, failed))

      tenants = self.integration.tenants

      if not number_of_accounts:
        min_accounts = max(len(tenants) * 10, 100)
        max_accounts = min_accounts * 4
        number_of_accounts = secure_random.randrange(min_accounts, max_accounts)

      prepared = []
      active = True
      info("preparing creation of {0} account for tenant {1}".format(number_of_accounts, tenant_name))
      for _ in range(number_of_accounts):
        prepared.append(self.integration.prepare_create_account(tenant_name, "s_" + str(self.__acc_counter.inc()), active))
        active = not active

      client = HttpClient()
      passed, failed = client.post(prepared, callback, on_progress)

      if failed:
        warn('{0} accounts created, {1} failed                             '.format(passed, failed))
      else:
        success('all passed                                                      ')

      return True

  def random_uniform_accounts(self, number_of_accounts=None):
    with timeit('random_uniform_accounts(_, {0})'.format(number_of_accounts)):
      #debug("random uniform accounts to all tenants")

      def callback(response, url, request, tenant):
        if response.status != 200:
          return None

        self.integration.update_account(tenant, request['accountNumber'], {
          'accountNumber': request['accountNumber'],
          'active': request['isBalanceCheck'],
          'balance': 0,
          'transactions': [],
          'currency': request['currency']
        })

        return response

      def on_progress(processed, passed, failed):
        progress('{0} [ passed: {1}, failed: {2} ]'.format(processed, passed, failed))

      tenants = self.integration.tenants

      if not number_of_accounts:
        min_accounts = max(len(tenants) * 10, 100)
        max_accounts = min_accounts * 4
        number_of_accounts = secure_random.randrange(min_accounts, max_accounts)

      partitions = []
      chunks = len(tenants)

      for _ in range(chunks):
        division = int(number_of_accounts / chunks)
        partitions.append(division)

      partitions[secure_random.randrange(0, chunks)] += int(number_of_accounts - sum(partitions))
      partitions = list(partitions)

      prepared = []
      active = True
      for tenant_name in tenants:
        will_generate_accounts = partitions.pop()
        info("preparing creation of {0} account for tenant {1}".format(will_generate_accounts, tenant_name))
        for _ in range(will_generate_accounts):
          prepared.append(self.integration.prepare_create_account(tenant_name, "s_" + str(self.__acc_counter.inc()), active))
          active = not active

      client = HttpClient()
      passed, failed = client.post(prepared, callback, on_progress)

      if failed:
        warn('{0} accounts created, {1} failed                             '.format(passed, failed))
      else:
        success('all passed                                                      ')

      return True

  def random_uniform_transactions(self):
    with timeit('random_uniform_transactions(_)'):
      #debug("random uniform transactions to all tenants")

      tenants = self.integration.tenants

      min_transactions = 100
      max_transactions = min_transactions*10

      def callback(response, url, request, tenant_name):
        if response.status != 200:
          return None

        transaction = json.loads(response.data.decode('utf-8'))['transaction']
        self.integration.charge_transactions(tenant_name, transaction, request['transfers'])

        return response

      def on_progress(processed, passed, failed):
        progress('{0} [ passed: {1}, failed: {2} ]'.format(processed, passed, failed))

      number_of_transactions = secure_random.randrange(min_transactions, max_transactions)

      partitions = []
      chunks = len(tenants)

      for _ in range(chunks):
        division = int(number_of_transactions / chunks)
        partitions.append(division)

      partitions[secure_random.randrange(0, chunks)] += int(number_of_transactions - sum(partitions))
      partitions = list(partitions)

      prepared = []
      for tenant_name in self.integration.get_accounts().keys():
        will_generate_transactions = partitions.pop()
        credit_accounts = self.integration.get_credit_accounts(tenant_name)
        debit_account =  self.integration.get_debit_accounts(tenant_name)

        info("preparing creation of {0} transactions for tenant {1}".format(will_generate_transactions, tenant_name))

        prepared.extend(self.integration.prepare_transaction(tenant_name, secure_random.randint(1, 10), credit_accounts, debit_account) for x in range(0, will_generate_transactions, 1))

      client = HttpClient()
      passed, failed = client.post(prepared, callback, on_progress)

      if failed:
        warn('{0} transactions created, {1} failed                             '.format(passed, failed))
      else:
        success('all passed                                                      ')

      return True

  def check_balances(self):
    with timeit('check_balances(_)'):
      #debug("check balances of all tenants")
      num_of_accounts = 0

      prepared = []
      for tenant_name, accounts in self.integration.get_accounts().items():
        for account_name, reference in accounts.items():
          num_of_accounts += 1
          prepared.append(self.integration.prepare_get_balance(tenant_name, account_name, reference))

      info("prepared checking balance of {0} accounts".format(num_of_accounts))

      def callback(response, url, request, tenant_name):
        if response.status != 200:
          return None

        content = json.loads(response.data.decode('utf-8'))
        if content['currency'] == request['currency'] and content['balance'] == request['balance']:
          return response
        else:
          return None

      def on_progress(processed, passed, failed):
        progress('{0} [ passed: {1}, failed: {2} ]'.format(processed, passed, failed))

      client = HttpClient()
      passed, failed = client.get(prepared, callback, on_progress)

      if failed:
        warn('{0} balance validated, {1} failed                             '.format(passed, failed))
      else:
        success('all passed                                                      ')

      return True

  def balance_cancel_out_check(self):
    with timeit('balance_cancel_out_check(_)'):
      #debug("checking that sum of all balances is 0.0")

      total = 0

      #start = time.time()
      for accounts in self.integration.get_accounts().values():
        for meta in accounts.values():
          total += meta['balance']

      if total != 0:
        warn('sum of all active and pasive accounts it non-zero: {0}'.format(total))
      else:
        success('all balances cancels out')

