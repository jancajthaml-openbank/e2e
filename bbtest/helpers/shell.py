#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import threading
import signal
import time
import os


class Deadline(threading.Thread):

  def __init__(self, timeout, callback):
    super().__init__(daemon=True)
    self.__timeout = timeout
    self.__callback = callback
    self.__cancelled = threading.Event()

  def run(self) -> None:
    deadline = time.monotonic() + self.__timeout
    while not self.__cancelled.wait(deadline - time.monotonic()):
      if not self.__cancelled.is_set() and deadline <= time.monotonic():
        return self.__callback()

  def cancel(self) -> None:
    self.__cancelled.set()
    self.join()


def execute(command, timeout=10, silent=False) -> None:
  try:
    p = subprocess.Popen(
      command,
      shell=False,
      stdin=None,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      close_fds=True
    )

    def kill() -> None:
      for sig in [signal.SIGTERM, signal.SIGQUIT, signal.SIGKILL, signal.SIGKILL]:
        if p.poll():
          break
        try:
          os.kill(p.pid, sig)
        except OSError:
          break

    result = ''

    deadline = Deadline(timeout, callback=kill)
    deadline.start()

    for line in p.stdout:
      line = line.decode('utf-8')
      if len(line):
        result += line
        if not silent:
          print(line.strip('\r\n'))

    deadline.cancel()
    p.wait()

    return (p.returncode, result)
  except subprocess.CalledProcessError:
    return (-1, '')
