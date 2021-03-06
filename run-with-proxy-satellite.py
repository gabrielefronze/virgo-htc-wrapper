#! /usr/bin/env python3

import argparse
import sys, os
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is a process wrapper wich adds a proxyrearm satellite by default.')
    parser.add_argument("main", nargs=argparse.REMAINDER, help="Provide the main process launch command as a string (surrounded by quotes).")
    parser.add_argument("--name", "-n", type=str, help="Provide a custom name for the pipeline process wrapper.")
    parser.add_argument("--interval", "-i", type=int, help="Provide the proxy renewal interval in seconds.")

    args = parser.parse_args()

    main_command = ' '.join(args.main)

    pathname = os.path.dirname(os.path.realpath(sys.argv[0]))
    
    sys.path.append(pathname)

    import satel_lite.satellite as satellite
    from proxyrearm.python.shouldrenew import shouldRenew

    satellite.setLogDir(pathname+"/logs")

    if not args.name:
        mainExe = satellite.makeWrapper(main_command, customName = "pipeline")
    else:
        mainExe = satellite.makeWrapper(main_command, customName = args.name)

    renewalThreshold = 0

    if not args.interval:
        repetitionInterval = 12 * 60 * 60 - 800 # 12 hours minus 400 seconds to have time to renew the proxy...
        renewalThreshold = int(round(repetitionInterval/2)) # doing it twice just for good measure
        firstDelay = random.SystemRandom().randint(0, 400)
    else:
        renewalThreshold = args.interval

    print("Proxy renewal interval set to {}".format(renewalThreshold))

    sideExes = [satellite.makeWrapper("{}/proxyrearm/proxyrearm-oneclick_htc.sh -f @ {}".format(pathname, renewalThreshold), mainExe.is_alive, customName = "proxyrearm", firstDelay = firstDelay)]

    satellite.main(mainExe, sideExes)
