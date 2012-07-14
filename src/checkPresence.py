__author__ = 'Jeff'

import time
import signal
import sys
import argparse
import urllib.request
import urllib.parse
import urllib.error
import datetime
import json

# Close on ctrl+C
def signal_handler(signal, frame):
    print("Exiting on Ctrl+C")
    ser.close()
    sys.exit(0)

def sendData(data, url):
    try:
        params = json.dumps([{'type': 'rfxcom' + str(data['packetType']),'time': now(), 'data': data}])
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, params.encode('utf-8'), headers)
        result = urllib.request.urlopen(req)
    except urllib.error.URLError as err:
        print(err)

    return

def main():
    global ser
    parser = argparse.ArgumentParser(description='Ping a device periodically')
    parser.add_argument("-i", "--ip", dest="ip", help="IP to ping", metavar="IP", required=True)
    parser.add_argument("-p", "--period", dest="period", help = "Period in minutes", metavar="PERIOD", required=True)
    parser.add_argument("-u", "--url", dest="url", help = "post data to URL", metavar="URL", required=True)

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    while True:




if __name__ == "__main__":
    main()