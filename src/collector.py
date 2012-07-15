__author__ = 'Jeff'

import serial
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

def now():
    return datetime.datetime.utcnow().isoformat('T')

def accumulate(buffer, offset, nbr):
    accu = 0
    for i in range(0,nbr):
        accu = accu*256 + buffer[offset + i]
    return accu

def processInterfaceMessage(msg, data):
    if data["packetLength"] != 13:
        print("Message with invalid length, got " + str(data["packetLength"]) + " expected 10")
        return data
    data["subType"] = msg[2]
    data["seqNbr"] = msg[3]

    data["deviceType"] = msg[5]
    data["fwVersion"] = msg[6]
    data["operationMode"] = msg[7]
    msg4 = msg[8]
    msg5 = msg[9]

    data["protoRFU"] = (msg4 & 0x80) != 0
    data["protoRollerTrol"] = (msg4 & 0x40) != 0
    data["protoProGuard"] = (msg4 & 0x20) != 0
    data["protoFS20"] = (msg4 & 0x10) != 0
    data["protoLaCrosse"] = (msg4 & 0x08) != 0
    data["protoHideki"] = (msg4 & 0x04) != 0
    data["protoLightwaveRF"] = (msg4 & 0x02) != 0
    data["protoMertik"] = (msg4 & 0x01) != 0
    data["protoVisonic"] = (msg5 & 0x80) != 0
    data["protoATI"] = (msg5 & 0x40) != 0
    data["protoOregonScientific"] = (msg5 & 0x20) != 0
    data["protoIkea"] = (msg5 & 0x10) != 0
    data["protoHomeEasy"] = (msg5 & 0x08) != 0
    data["protoAC"] = (msg5 & 0x04) != 0
    data["protoARC"] = (msg5 & 0x02) != 0
    data["protoX10"] = (msg5 & 0x01) != 0

    print("Firmware version " + str(data["fwVersion"]))
    print("Operation mode " + str(data["operationMode"]))
    print("Proto RFU " + str(data["protoRFU"]))
    print("Proto RollerTrol " + str(data["protoRollerTrol"]))
    print("Proto ProGuard " + str(data["protoProGuard"]))
    print("Proto FS20 " + str(data["protoFS20"]))
    print("Proto LaCrosse " + str(data["protoLaCrosse"]))
    print("Proto Hideki " + str(data["protoHideki"]))
    print("Proto LightwaveRF " + str(data["protoLightwaveRF"]))
    print("Proto Mertik " + str(data["protoMertik"]))
    print("Proto Visonic " + str(data["protoVisonic"]))
    print("Proto ATI " + str(data["protoATI"]))
    print("Proto Oregon Scientific " + str(data["protoOregonScientific"]))
    print("Proto Ikea " + str(data["protoIkea"]))
    print("Proto HomeEasy " + str(data["protoHomeEasy"]))
    print("Proto AC " + str(data["protoAC"]))
    print("Proto ARC " + str(data["protoARC"]))
    print("Proto X10 " + str(data["protoX10"]))
    return data


def processTempHumBaroSensor(msg, data):
    data["subType"] = msg[2]
    data["seqNbr"] = msg[3]
    data["id1"] = msg[4]
    data["id2"] = msg[5]

    position = 6
    if data["packetType"] in [80,82,84]:
        temperature = accumulate(msg, position, 2)
        if temperature >= 32768:
            temperature = -(temperature - 32768)
        temperature /= float(10)
        data["temperature"] = temperature
        print("Temperature " + str(data["temperature"]) +"C")
        position += 2

    if data["packetType"] in [81,82,84]:
        data["humidity"] = msg[position]
        data["humidityStatus"] = msg[position+1]
        print("Humidity " + str(data["humidity"]) +"%")
        print("Humidity status " + str(data["humidityStatus"]))
        position += 2

    if data["packetType"] in [83,84]:
        data["baro"] = accumulate(msg, position, 2)
        data["forecast"] = msg[position+2]
        print("Barometre " + str(data["baro"]) + "hPa")
        print("Forecast " + str(data["forecast"]))
        position += 3

    data["battery"] = (msg[position] & 0xF0) >> 4
    data["RSSI"] = msg[position] & 0x0F
    print("Battery " + str(data["battery"]))
    print("RSSI " + str(data["RSSI"]))
    return data

def processEnergyUsageSensor(msg, data):
    if data["packetLength"] != 17:
        print("Message with invalid length, got " + str(data["packetLength"]) + " expected 17")
        return data

    data["subType"] = msg[2]
    data["seqNbr"] = msg[3]
    data["id1"] = msg[4]
    data["id2"] = msg[5]
    data["count"] = msg[6]
    data["instant"] = accumulate(msg, 7,4)
    data["total"] = float(accumulate(msg, 11,6)) / float(223666) # To get kWh cf doc from rfxcom
    data["battery"] = (msg[17] & 0xF0) >> 4
    data["RSSI"] = msg[17] & 0x0F

    print("Instant power " + str(data["instant"]))
    print("Total power " + str(data["total"]))
    print("Battery " + str(data["battery"]))
    print("RSSI " + str(data["RSSI"]))
    return data

def parseMessage(msg):
    print('Packet length ' + str(msg[0]))
    packetLength = msg[0]
    packetType = msg[1]

    data = {'packetType': packetType, 'packetLength': packetLength}

    if packetType == 1:
        print("Received interface control (0x01) message")
        data = processInterfaceMessage(msg, data)
    elif packetType == 2:
        print("Received Receiver/Transmitter (0x02) message")
    elif packetType == 3:
        print("Received undecoded RF (0x03) message")
    elif packetType == 80:
        print("Received Temperature sensor (0x50) message")
        data = processTempHumBaroSensor(msg, data)
    elif packetType == 81:
        print("Received Humidy sensor (0x51) message")
        data = processTempHumBaroSensor(msg, data)
    elif packetType == 82:
        print("Received Temp & Humidity sensor (0x52) message")
        data = processTempHumBaroSensor(msg, data)
    elif packetType == 83:
        print("Received Barometric sensor (0x53) message")
        data = processTempHumBaroSensor(msg, data)
    elif packetType == 84:
        print("Received Temp, Hum, Baro sensor (0x54) message")
        data = processTempHumBaroSensor(msg, data)
    elif packetType == 85:
        print("Received Rain sensor (0x55) message")
    elif packetType == 86:
        print("Received Wind sensor (0x56) message")
    elif packetType == 87:
        print("Received UV sensor (0x57) message")
    elif packetType == 90:
        print("Received Energy usage sensor (0x5A) message")
        data = processEnergyUsageSensor(msg, data)
    else:
        print("Unsupported packet type " + str(packetType))
    return data

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
    parser = argparse.ArgumentParser(description='Collect home automation events from RFXCOM')
    parser.add_argument("-t", "--tty-port", dest="ttyport", help="open port TTY", metavar="TTY", required=True)
    parser.add_argument("-u", "--url", dest="url", help = "post data to URL", metavar="URL", required=True)

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    ser = serial.Serial(args.ttyport, 38400, timeout = 0.2)
    print(ser)

    # Reset command
    reset = bytearray.fromhex("0D00000000000000000000000000")
    # GetStatus command
    status = bytearray.fromhex("0D00000102000000000000000000")

    ser.write(reset)
    time.sleep(0.1)
    ser.flushInput()
    ser.write(status)

    buffer = bytearray(b'')

    while True:
        data = bytearray(ser.read(32))
        buffer += data
        if len(buffer) > 0:
            packetLength = buffer[0]
            if len(buffer) > packetLength:
                if packetLength == 0:
                    print("Got actual message with length 0 - discarding")
                    del buffer[0:1]
                else:
                    msg = buffer[0:packetLength+1] #size does not include size byte (so actual size is +1)
                    del buffer[0:packetLength+1] #remove message
                    data = parseMessage(msg)
                    sendData(data, args.url)



if __name__ == "__main__":
    main()
