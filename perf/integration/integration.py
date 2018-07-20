#!/usr/bin/env python

import json
import random
secure_random = random.SystemRandom()

from collections import OrderedDict
from threading import Lock

class Integration(object):

  def __init__(self, manager):
    self.__manager = manager
    self.__accounts = OrderedDict()
    self.__lock = Lock()

  def charge_transactions(self, tenant, transaction, transfers) -> None:
    for transfer in transfers:
      amount = transfer['amount']
      credit = transfer['credit']
      debit = transfer['debit']

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
    return [i['accountNumber'] for i in clone if i['active']]

  def get_debit_accounts(self, tenant) -> list:
    with self.__lock:
      clone = self.__accounts[tenant].copy().values()
    return [i['accountNumber'] for i in clone if not i['active']]

  @property
  def tenants(self) -> list:
    return [v.tenant for v in self.__manager['vault']]

  @staticmethod
  def prepare_transfer(credit_account_choice, debit_acount_choice) -> dict:
    account_to = secure_random.choice(credit_account_choice)
    account_from = secure_random.choice(debit_acount_choice)

    return {
      "credit": account_to,
      "debit": account_from,
      "valuta": "2016-10-28",
      "amount": "1.0",  # fixme random amount
      "currency": "CZK" # fixme there need to be target tenant
    }

  def prepare_transaction(self, tenant_name, number_of_transfers, credit_account_choice, debit_acount_choice):
    transfers = []

    for _ in range(number_of_transfers):
      transfers.append(Integration.prepare_transfer(credit_account_choice, debit_acount_choice))

    random_wall = secure_random.choice(self.__manager['wall'])

    url = 'https://' + random_wall.hostname + '/transaction/' + tenant_name
    body = {
      "transfers": transfers
    }

    return (url, body, json.dumps(body), tenant_name)

  def prepare_get_balance(self, tenant_name, account_name, reference):
    random_wall = secure_random.choice(self.__manager['wall'])

    url = 'https://' + random_wall.hostname + '/account/' + tenant_name + '/' + account_name

    return (url, reference, tenant_name)

  def prepare_create_account(self, tenant_name, account_name, is_ballance_check):
    random_wall = secure_random.choice(self.__manager['wall'])

    url = 'https://' + random_wall.hostname + '/account/' + tenant_name
    body = {
      "accountNumber": account_name,
      "currency": "CZK",
      "isBalanceCheck": is_ballance_check
    }

    return (url, body, json.dumps(body), tenant_name)