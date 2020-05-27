from behave import *
from helpers.eventually import eventually


@given('appliance is running')
def appliance_running(context):
  @eventually(5)
  def impl():
    assert context.appliance.running()
  impl()