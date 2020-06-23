#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from behave import *
import os
from helpers.eventually import eventually


@then('file {file} should exist')
def file_should_exist(context, file):
  @eventually(2)
  def wait_files_exist():
    assert os.path.isfile(file)
  wait_files_exist()


@then('directory {directory} should contain {count} files')
def directory_should_contain_len(context, directory, count):
  @eventually(2)
  def wait_directory_exists():
    assert os.path.isdir(directory)

  @eventually(2)
  def wait_files_exists():
    entries = []
    try:
      entries = [file for file in os.listdir(directory) if os.path.isfile('{}/{}'.format(directory, file))]
    except:
      pass
    assert len(entries) == int(count), "expected {} files but found {}".format(count, entries)

  wait_directory_exists()
  wait_files_exists()
