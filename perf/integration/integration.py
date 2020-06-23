#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
from collections import OrderedDict
from threading import Lock
secure_random = random.SystemRandom()


class Integration(object):

  def __init__(self, manager):
    self.__manager = manager
    self.__accounts = OrderedDict()
    self.__lock = Lock()

  def clear(self):
    with self.__lock:
      self.__accounts = OrderedDict()

  def charge_transactions(self, tenant, transaction, transfers) -> None:
    for transfer in transfers:
      amount = transfer['amount']
      credit = transfer['credit']['name']
      debit = transfer['debit']['name']

      with self.__lock:
        self.__accounts[tenant][credit]['balance'] += float(amount)
        self.__accounts[tenant][debit]['balance'] -= float(amount)

        self.__accounts[tenant][credit]['transactions'].append(transaction)
        self.__accounts[tenant][debit]['transactions'].append(transaction)

  def update_account(self, tenant, account, data) -> None:
    with self.__lock:
      if not tenant in self.__accounts:
        self.__accounts[tenant] = OrderedDict()
    with self.__lock:
      self.__accounts[tenant][account] = OrderedDict(data)

  def get_accounts(self) -> dict:
    with self.__lock:
      clone = self.__accounts.copy()
    return clone

  def get_credit_accounts(self, tenant) -> list:
    with self.__lock:
      clone = self.__accounts[tenant].copy().values()
    return [i['name'] for i in clone if i['active']]

  def get_debit_accounts(self, tenant) -> list:
    with self.__lock:
      clone = self.__accounts[tenant].copy().values()
    return [i['name'] for i in clone if not i['active']]

  @property
  def tenants(self) -> list:
    return [v.tenant for v in self.__manager['vault-unit']]

  @staticmethod
  def prepare_transfer(tenant_name, credit_account_choice, debit_acount_choice) -> dict:
    account_to = secure_random.choice(credit_account_choice)
    account_from = secure_random.choice(debit_acount_choice)

    return {
      "credit": {
        "tenant": tenant_name,
        "name": account_to,
      },
      "debit": {
        "tenant": tenant_name,
        "name": account_from,
      },
      "amount": "1.0",  # fixme random amount
      "currency": "CZK" # fixme there need to be target tenant
    }

  def prepare_transaction(self, tenant_name, number_of_transfers, credit_account_choice, debit_acount_choice):
    transfers = []

    for _ in range(number_of_transfers):
      transfers.append(Integration.prepare_transfer(tenant_name, credit_account_choice, debit_acount_choice))

    url = 'https://127.0.0.1:4401/transaction/' + tenant_name
    body = {
      "transfers": transfers
    }

    return (url, body, json.dumps(body), tenant_name)

  def prepare_get_balance(self, tenant_name, account_name, reference):
    url = 'https://127.0.0.1:4400/account/' + tenant_name + '/' + account_name

    return (url, reference, tenant_name)

  def prepare_create_account(self, tenant_name, account_name, is_ballance_check):
    url = 'https://127.0.0.1:4400/account/' + tenant_name
    body = {
      "name": account_name,
      "format": "perf",
      "currency": "CZK",
      "isBalanceCheck": is_ballance_check
    }

    return (url, body, json.dumps(body), tenant_name)
