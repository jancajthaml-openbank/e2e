from behave import *
import ssl
import urllib.request
import json
import time
from helpers.eventually import eventually


@given('{service} {tenant} is onboarded')
def onboard_unit(context, service, tenant):
  assert service in ['vault', 'ledger']

  uri = "https://127.0.0.1:{}/tenant/{}".format({
    'ledger': 4401,
    'vault': 4400,
  }[service], tenant)

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='POST', url=uri)
  request.add_header('Accept', 'application/json')

  response = urllib.request.urlopen(request, timeout=10, context=ctx)

  assert response.status == 200

  context.appliance.update_units()

  @eventually(5)
  def impl():
    assert context.appliance.running()
  impl()


@when('GraphQL requested with')
def prepare_graphql_request(context):
  context.http_request = context.text


@then('GraphQL responsed with')
def check_graphql_response(context):
  uri = "http://127.0.0.1:8080/graphql"
  body = {
    'query': context.http_request,
    'variables': None,
    'operationName': None,
  }

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method='POST', url=uri)
  request.add_header('Accept', 'application/json')
  request.add_header('Content-Type', 'application/json')
  request.data = json.dumps(body).encode('utf-8')

  expected = json.loads(context.text)

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

  @eventually(5)
  def impl():
    response = urllib.request.urlopen(request, timeout=10, context=ctx)
    assert response.status == 200
    diff('', expected, json.loads(response.read().decode('utf-8')))

  impl()


@when('I request HTTP {uri}')
def perform_http_request(context, uri):
  options = dict()
  if context.table:
    for row in context.table:
      options[row['key']] = row['value']

  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE

  request = urllib.request.Request(method=options['method'], url=uri)
  request.add_header('Accept', 'application/json')
  if context.text:
    request.add_header('Content-Type', 'application/json')
    request.data = context.text.encode('utf-8')

  context.http_response = dict()

  try:
    response = urllib.request.urlopen(request, timeout=20, context=ctx)
    context.http_response['status'] = str(response.status)
    context.http_response['body'] = response.read().decode('utf-8')
  except urllib.error.HTTPError as err:
    context.http_response['status'] = str(err.code)
    context.http_response['body'] = err.read().decode('utf-8')


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

    diff('', json.loads(context.text), json.loads(response['body']))
