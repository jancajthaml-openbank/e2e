#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
import ssl
import urllib.request
import json
import os
from datetime import datetime


@then('snapshot {tenant}/{account} version {version} should be')
def check_account_snapshot(context, tenant, account, version):
  path = '/data/t_{}/account/{}/snapshot/{}'.format(tenant, account, version.zfill(10))
  assert os.path.isfile(path), 'file {} does not exists'.format(path)

  actual = dict()
  with open(path, 'r') as fd:
    lines = fd.readlines()
    lines = [line.strip() for line in lines]

    actual.update({
      'isBalanceCheck': 'true' if lines[0][-1] != "F" else 'false',
      'format': lines[0][4:-2],
      'currency': lines[0][:3],
      'accountName': account,
      'version': version,
      'balance': lines[1],
      'promised': lines[2],
      'promiseBuffer': ' '.join(lines[3:-2])
    })

  for row in context.table:
    assert row['key'] in actual, 'key {} is missing in {}'.format(row['key'], actual)
    assert actual[row['key']] == row['value'], 'expected {} got {}'.format(row['value'], actual[row['key']])


@then('transaction {transaction} state of {tenant} should be {status}')
def check_transaction_state(context, tenant, transaction, status):
  path = '/data/t_{}/transaction/{}'.format(tenant, transaction)
  assert os.path.isfile(path), 'file {} does not exists'.format(path)

  actual = dict()
  with open(path, 'r') as fd:
    lines = fd.readlines()
    lines = [line.strip() for line in lines]
    assert lines[0] == status, 'expected {} but got {}'.format(status, lines[0])


@then('transaction {transaction} of {tenant} should be')
def check_transaction_state(context, tenant, transaction):
  path = '/data/t_{}/transaction/{}'.format(tenant, transaction)
  assert os.path.isfile(path), 'file {} does not exists'.format(path)

  actual = []
  with open(path, 'r') as fd:
    lines = fd.readlines()
    lines = [line.strip() for line in lines]
    state = lines[0]
    for transfer in lines[1:]:
      item = transfer.split(' ')
      actual.append({
        'credit': {
          'name': item[2],
          'tenant': item[1],
        },
        'debit':{
          'name': item[4],
          'tenant': item[3],
        },
        'amount': item[6],
        'currency': item[7],
        #'valueDate': item[5],
      })
  actual = sorted(actual)

  expected = []
  for row in context.table:
    tmp = dict()
    if row.get('credit'):
      (t, a) = row['credit'].split('/')
      tmp['credit'] = {
        'name': a,
        'tenant': t,
      }
    if row.get('debit'):
      (t, a) = row['debit'].split('/')
      tmp['debit'] = {
        'name': a,
        'tenant': t,
      }
    if row.get('amount'):
      tmp['amount'] = row['amount']
    if row.get('currency'):
      tmp['currency'] = row['currency']
    expected.append(tmp)
  expected = sorted(expected)

  assert expected == actual
