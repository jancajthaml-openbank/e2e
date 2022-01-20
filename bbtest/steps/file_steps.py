#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
from helpers.eventually import eventually
import os


@then('file {file} should exist')
def file_should_exist(context, file):
  @eventually(2)
  def wait_file_exist():
    assert os.path.isfile(file)
  wait_file_exist()


@then('directory {directory} should exist')
def directory_should_exist(context, directory):
  @eventually(2)
  def wait_directory_exist():
    assert os.path.isdir(directory)
  wait_directory_exist()


@then('directory {directory} should contain {count} files')
def directory_should_contain_len(context, directory, count):
  @eventually(2)
  def wait_files_exists():
    entries = []
    try:
      entries = [file for file in os.listdir(directory) if os.path.isfile('{}/{}'.format(directory, file))]
    except:
      pass
    assert len(entries) == int(count), "expected {} files but found {}".format(count, entries)
  directory_should_exist(context, directory)
  wait_files_exists()
