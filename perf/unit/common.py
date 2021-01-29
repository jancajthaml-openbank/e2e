#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os


class Unit(object):

  def scale(self, size) -> None:
    pass

  def reconfigure(self, params) -> None:
    pass

Unit.FNULL = open(os.devnull, 'w')
