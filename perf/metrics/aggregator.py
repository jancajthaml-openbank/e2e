#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import time
import re


class MetricsAggregator(threading.Thread):

  def __init__(self, namespace):
    threading.Thread.__init__(self)
    self.__cancel = threading.Event()
    self.__store = dict()
    self.__namespace = namespace
    self.__lock = threading.Lock()

  def start(self):
    self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threading.Thread.start(self)

  def run(self):
    self._sock.bind(('127.0.0.1', 8125))

    while not self.__cancel.is_set():
      data, addr = self._sock.recvfrom(1024)
      try:
        self.__process_change(data.decode('utf-8'))
      except Exception as e:
        print('failed with {}'.format(e))
        return

  def get_metrics(self) -> dict:
    return self.__store

  def clear(self) -> None:
    self.__store = dict()

  def __process_change(self, data) -> None:
    for metric in data.split('\n'):
      match = re.match('\A([^:]+):([^|]+)\|(.+)', metric)
      if match == None:
        continue

      key   = match.group(1)
      value = match.group(2)

      ts = str(int(time.time()))

      with self.__lock:
        if not ts in self.__store:
          self.__store[ts] = {
            'openbank.lake.message.ingress': 0,
            'openbank.lake.message.egress': 0,
            'openbank.lake.message.bytes': 0,
            'openbank.ledger.transaction.promised': 0,
            'openbank.ledger.transaction.rollbacked': 0,
            'openbank.ledger.transaction.committed': 0,
            'openbank.ledger.transfer.promised': 0,
            'openbank.ledger.transfer.rollbacked': 0,
            'openbank.ledger.transfer.committed': 0,
            'openbank.vault.account.created': 0,
            'openbank.vault.account.updated': 0,
            'openbank.vault.promise.accepted': 0,
            'openbank.vault.promise.rollbacked': 0,
            'openbank.vault.promise.committed': 0
          }

        if key == 'openbank.lake.message.ingress':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.lake.message.egress':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.lake.memory.bytes':
          self.__store[ts][key] = int(value)
        elif key == 'openbank.vault.account.created':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.vault.account.updated':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.vault.promise.accepted':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.vault.promise.rollbacked':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.vault.promise.committed':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.ledger.transaction.promised':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.ledger.transaction.rollbacked':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.ledger.transaction.committed':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.ledger.transfer.promised':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.ledger.transfer.rollbacked':
          self.__store[ts][key] += int(value)
        elif key == 'openbank.ledger.transfer.committed':
          self.__store[ts][key] += int(value)
        else:
          print('unknown {}'.format(key))

  def stop(self):
    if self.__cancel.is_set():
      return
    self.__cancel.set()
    try:
      self._sock.shutdown(socket.SHUT_RD)
    except:
      pass
    try:
      self.join()
    except:
      pass
