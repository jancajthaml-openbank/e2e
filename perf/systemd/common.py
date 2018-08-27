#!/usr/bin/env python

import os

class Unit(object):

  def scale(self, size) -> None:
    pass

Unit.FNULL = open(os.devnull, 'w')
