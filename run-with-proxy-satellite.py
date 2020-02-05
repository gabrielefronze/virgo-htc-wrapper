#! /usr/bin/env python3

import argparse
import satel_lite.satellite as satellite
from proxyrearm.python.shouldrenew import shouldRenew
from fastlog.python.fastlog import *

satellite.setLogDir("./logs")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a process wrapper wich adds a proxyrearm satellite by default.')
    parser.add_argument("main", nargs=argparse.REMAINDER, help="Provide the main process launch command as a string (surrounded by quotes).")
    parser.add_argument("--name", "-n", type=str, help="Provide a custom name for the pipeline process wrapper.")
    parser.add_argument("--interval", "-i", type=int, help="Provide the proxy renewal interval in seconds.")

    args = parser.parse_args()

    main_command = ' '.join(args.main)

    if not args.name:
        mainExe = satellite.makeWrapper(main_command, customName = "pipeline")
    else:
        mainExe = satellite.makeWrapper(main_command, customName = args.name)

    renewalThreshold = 0

    if not args.interval:
        repetitionInterval = 12 * 60 * 60 - 400 # 12 hours minus 400 seconds to have time to renew the proxy...
        renewalThreshold = repetitionInterval/2 # doing it twice just for good measure
    else:
        renewalThreshold = args.interval


    fastlog(DEBUG, "Proxy renewal interval set to {}".format(renewalThreshold))

    sideExes = [satellite.makeWrapper("proxyrearm/proxyrearm-oneclick.sh -f @ {}".format(renewalThreshold), mainExe.is_alive, customName = "proxyrearm")]

    satellite.main(mainExe, sideExes)
