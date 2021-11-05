#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
import json
import time
from helpers.eventually import eventually
from helpers.http import Request


@given('{service} {tenant} is onboarded')
def onboard_unit(context, service, tenant):
  assert service in ['vault', 'ledger'], 'unknown service "{}" to onboard'.format(service)

  uri = "https://127.0.0.1:{}/tenant/{}".format({
    'ledger': 4401,
    'vault': 4400,
  }[service], tenant)

  request = Request(method='POST', url=uri)
  request.add_header('Accept', 'application/json')

  response = request.do()
  assert response.status == 200, 'expected status 200 got {}'.format(response.status)

  @eventually(5)
  def wait_for_appliance_up():
    assert context.appliance.running(), 'appliance did not start within 5 seconds'

  wait_for_appliance_up()


@when('GraphQL requested with')
def prepare_graphql_request(context):
  context.http_request = context.text


@then('GraphQL responsed with')
def check_graphql_response(context):
  @eventually(120)
  def wait_for_warehouse_to_be_healthy():
    request = Request(method='GET', url='http://127.0.0.1:8080/health')
    response = request.do()
    assert response.status == 200, 'expected status 200 actual {}'.format(response.status)
    status = json.loads(response.read().decode('utf-8'))
    assert status['healthy'], 'service is not healthy'
    assert status['graphql'], 'graphql is not healthy'

  uri = "http://127.0.0.1:8080/graphql"
  payload = {
    'query': context.http_request,
    'variables': None,
    'operationName': None,
  }

  def diff(path, a, b):
    if type(a) == list:
      assert type(b) == list, 'types differ at {} expected: {} actual: {}'.format(path, list, type(b))
      for idx, item in enumerate(a):
        assert item in b, 'value {} was not found at {}[{}], actual: {}'.format(item, path, idx, b)
        diff('{}[{}]'.format(path, idx), item, b[b.index(item)])
    elif type(b) == dict:
      assert type(b) == dict, 'types differ at {} expected: {} actual: {}'.format(path, dict, type(b))
      for k, v in a.items():
        assert k in b, "value {} was not found in {}".format(k, b)
        diff('{}.{}'.format(path, k), v, b[k])
    else:
      assert type(a) == type(b), 'types differ at {} expected: {} actual: {}'.format(path, type(a), type(b))
      assert a == b, 'values differ at {} expected: {} actual: {}'.format(path, a, b)

  @eventually(120)
  def wait_for_graphql_to_respond():
    request = Request(method='POST', url=uri)
    request.data = json.dumps(payload)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Accept', 'application/json')
    response = request.do()

    assert response.status == 200, 'expected status 200 actual {}'.format(response.status)
    expected = json.loads(context.text)
    actual = json.loads(response.read().decode('utf-8'))
    try:
      diff('', expected, actual)
    except AssertionError as ex:
      raise AssertionError('{} with response {}'.format(ex, actual))

  wait_for_warehouse_to_be_healthy()
  wait_for_graphql_to_respond()


@when('I request HTTP {uri}')
def perform_http_request(context, uri):
  options = dict()
  if context.table:
    for row in context.table:
      options[row['key']] = row['value']

  context.http_response = dict()

  request = Request(method=options['method'], url=uri)
  request.add_header('Accept', 'application/json')

  if context.text:
    request.add_header('Content-Type', 'application/json')
    request.data = context.text

  response = request.do()
  context.http_response['status'] = str(response.status)
  context.http_response['body'] = response.read().decode('utf-8')
  context.http_response['content-type'] = response.content_type


@then('HTTP response is')
def check_http_response(context):
  options = dict()
  if context.table:
    for row in context.table:
      options[row['key']] = row['value']

  assert context.http_response
  response = context.http_response
  del context.http_response

  if 'status' in options:
    assert response['status'] == options['status'], 'expected status {} actual {}'.format(options['status'], response['status'])

  if context.text:
    def diff(path, a, b):
      if type(a) == list:
        assert type(b) == list, 'types differ at {} expected: {} actual: {}'.format(path, list, type(b))
        for idx, item in enumerate(a):
          assert item in b, 'value {} was not found at {}[{}]'.format(item, path, idx)
          diff('{}[{}]'.format(path, idx), item, b[b.index(item)])
      elif type(b) == dict:
        assert type(b) == dict, 'types differ at {} expected: {} actual: {}'.format(path, dict, type(b))
        for k, v in a.items():
          assert k in b
          diff('{}.{}'.format(path, k), v, b[k])
      else:
        assert type(a) == type(b), 'types differ at {} expected: {} actual: {}'.format(path, type(a), type(b))
        assert a == b, 'values differ at {} expected: {} actual: {}'.format(path, a, b)

    stash = list()

    if response['body']:
      for line in response['body'].split('\n'):
        if response['content-type'].startswith('text/plain'):
          stash.append(line)
        else:
          stash.append(json.loads(line))

    try:
      expected = json.loads(context.text)
      if type(expected) == dict:
        stash = stash[0] if len(stash) else dict()
      diff('', expected, stash)
    except AssertionError as ex:
      raise AssertionError('{} with response {}'.format(ex, response['body']))
