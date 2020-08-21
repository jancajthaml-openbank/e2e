#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
from helpers.eventually import eventually


@given('appliance is running')
def appliance_running(context):
  @eventually(5)
  def wait_for_appliance_up():
    assert context.appliance.running(), 'appliance did not start within 5 seconds'
  wait_for_appliance_up()
