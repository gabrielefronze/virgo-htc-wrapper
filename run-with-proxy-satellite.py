#! /usr/bin/env python3

import argparse
import satel_lite.satellite as satellite
from proxyrearm.python.shouldrenew import shouldRenew

satellite.setLogDir("./logs")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a process wrapper wich adds a proxyrearm satellite by default.')
    parser.add_argument("main", type=str, help="Provide the main process launch command as a string (surrounded by quotes).")
    parser.add_argument("--name", "-n", type=str, help="Provide a custom name for the pipeline process wrapper.")

    args = parser.parse_args()

    if not args.name:
        mainExe = satellite.makeWrapper(args.main, customName = "pipeline")
    else:
        mainExe = satellite.makeWrapper(args.main, customName = args.name)

    repetitionInterval = 12 * 60 * 60 - 400 # 12 hours minus 400 seconds to have time to renew the proxy...
    renewalThreshold = repetitionInterval/2 # doing it twice just for good measure

    sideExes = [satellite.makeWrapper("proxyrearm/proxyrearm-oneclick.sh -f @ {}".format(repetitionInterval), mainExe.is_alive, customName = "proxyrearm")]

    satellite.main(mainExe, sideExes)
