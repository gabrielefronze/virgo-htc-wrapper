#! /usr/bin/env python3

import argparse
import satel_lite.satellite as satellite

satellite.setLogDir("./logs")

def should_renew_proxy():
    print("Checking for residual proxy validity")
    # TODO: verify proxy with something like voms-proxy-info -file ./vomsproxy.pem
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a process wrapper wich adds a proxyrearm satellite by default.')
    parser.add_argument("main", type=str, help="Provide the main process launch command as a string (surrounded by quotes).")
    parser.add_argument("--name", "-n", type=str, help="Provide a custom name for the pipeline process wrapper.")

    args = parser.parse_args()

    if args.name:
        mainExe = satellite.makeWrapper(args.main, customName = "pipeline")
    else:
        mainExe = satellite.makeWrapper(args.main, customName = args.name)

    hours = 12
    seconds = hours * 3600
    delay = seconds - 200

    def trigger():
        return mainExe.is_alive() and should_renew_proxy()

    sideExes = [satellite.makeWrapper("proxyrearm/proxyrearm-oneclick.sh @ {}".format(delay), trigger, customName = "proxyrearm")]

    satellite.main(mainExe, sideExes)
