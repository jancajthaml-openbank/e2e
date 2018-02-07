#!/usr/bin/env python
# -*- coding: utf-8 -*-

import api
from constants import debug, error, info

import sys

from stress import StressTest

def main():

  containers = None

  try:
    import env

    # fixme delete previous journal

    info("discovering containers")
    containers = env.discover_containers()
    if not containers:
      error('no containers found')
      sys.exit(1)
    else:
      for container, images in containers.items():
        info("found {0}({1}x)".format(container, len(images)))

    # fixme add timeout
    debug("waiting util services are UP")
    api.ping()

    info("start tests")
    st = StressTest()

    debug("reference test of http API")
    st.stress_run_health_reference()

    #debug("random accounts")
    #st.stress_run_accounts_only()

    #if False:
    debug("random accounts from scratch with random transactions")
    st.stress_run()

    debug("reset vault / verify rehydration")
    env.reset_dockers({
      'vault': containers['vault']
    })
    #debug("waiting util service is ready")
    api.ping()
    st.check_balances_parallel()

    #debug("TDB audit from database")
    # fixme audit here

  except KeyboardInterrupt:
    print(" detected, exiting")
  finally:
    #if containers:
      # fixme trap keyboard interupt here
      #info("truncate cassandra tables")
      #env.clean_cassandra(containers['cassandra'])

      #info("truncate mongo tables")
      #env.clean_mongo(containers['mongo'])
    pass

    #info("dumping logs")
    #env.print_logs()

    #info("stop system")
    #env.stop_system()

if __name__ == "__main__":
  debug("starting tests")
  main()
  debug("ending tests")
