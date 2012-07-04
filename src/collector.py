__author__ = 'Jeff'

import serial
import time
import signal
import sys
import argparse
import urllib.request
import urllib.parse
import urllib.error
import base64


# Close on ctrl+C
def signal_handler(signal, frame):
    print("Exiting on Ctrl+C")
    ser.close()
    sys.exit(0)

def accumulate(buffer, offset, nbr):
    accu = 0
    for i in range(0,nbr):
        accu = accu*256 + buffer[offset + i]
    return accu

def processInterfaceMessage(msg):
    data = {'datetime': time.time() , 'msg': base64.encodebytes(msg)}
    packetLength = msg[0]
    if packetLength != 13:
        print("Message with invalid length, got " + str(packetLength) + " expected 10")
        return data
    subtype = msg[2]
    seqNbr = msg[3]

    type = msg[5]
    fw_version = msg[6]
    operation_mode = msg[7]
    msg4 = msg[8]
    msg5 = msg[9]

    protoRFU = (msg4 & 0x80) != 0
    protoRollerTrol = (msg4 & 0x40) != 0
    protoProGuard = (msg4 & 0x20) != 0
    protoFS20 = (msg4 & 0x10) != 0
    protoLaCrosse = (msg4 & 0x08) != 0
    protoHideki = (msg4 & 0x04) != 0
    protoLightwaveRF = (msg4 & 0x02) != 0
    protoMertik = (msg4 & 0x01) != 0
    protoVisonic = (msg5 & 0x80) != 0
    protoATI = (msg5 & 0x40) != 0
    protoOregonScientific = (msg5 & 0x20) != 0
    protoIkea = (msg5 & 0x10) != 0
    protoHomeEasy = (msg5 & 0x08) != 0
    protoAC = (msg5 & 0x04) != 0
    protoARC = (msg5 & 0x02) != 0
    protoX10 = (msg5 & 0x01) != 0

    print("Firmware version " + str(fw_version))
    print("Operation mode " + str(operation_mode))
    print("Proto RFU " + str(protoRFU))
    print("Proto RollerTrol " + str(protoRollerTrol))
    print("Proto ProGuard " + str(protoProGuard))
    print("Proto FS20 " + str(protoFS20))
    print("Proto LaCrosse " + str(protoLaCrosse))
    print("Proto Hideki " + str(protoHideki))
    print("Proto LightwaveRF " + str(protoLightwaveRF))
    print("Proto Mertik " + str(protoMertik))
    print("Proto Visonic " + str(protoVisonic))
    print("Proto ATI " + str(protoATI))
    print("Proto Oregon Scientific " + str(protoOregonScientific))
    print("Proto Ikea " + str(protoIkea))
    print("Proto HomeEasy " + str(protoHomeEasy))
    print("Proto AC " + str(protoAC))
    print("Proto ARC " + str(protoARC))
    print("Proto X10 " + str(protoX10))
    return data


def processTempHumSensor(msg):
    packetLength = msg[0]
    if packetLength != 10:
        print("Message with invalid length, got " + str(packetLength) + " expected 10")
        return {'datetime': time.time() * 1000 , 'msg': base64.encodebytes(msg)}

    subtype = msg[2]
    seqNbr = msg[3]
    id1 = msg[4]
    id2 = msg[5]
    temperature = accumulate(msg, 6, 2)
    if temperature >= 32768:
        temperature = -(temperature - 32768)
    temperature /= float(10)

    humidity = msg[8]
    humidityStatus = msg[9]
    battery = (msg[10] & 0xF0) >> 4
    rssi = msg[10] & 0x0F

    print("Temperature " + str(temperature) +"C")
    print("Humidity " + str(humidity) +"%")
    print("Humidity status " + str(humidityStatus))
    print("Battery " + str(battery))
    print("RSSI " + str(rssi))
    return {'datetime': time.time()*1000 ,'packetLength': packetLength, 'packetType': msg[1], \
            'subType': subtype, 'seqNbr': seqNbr, 'id1': id1, 'id2': id2, 'temperature': temperature,   \
            'humidity': humidity, 'humidityStatus': humidityStatus, 'battery': battery, 'RSSI': rssi, 'msg': base64.encodebytes(msg)}

def processEnergyUsageSensor(msg):
    packetLength = msg[0]
    if packetLength != 17:
        print("Message with invalid length, got " + str(packetLength) + " expected 17")
        return {'datetime': time.time()*1000 , 'msg': base64.encodebytes(msg)}

    subtype = msg[2]
    seqNbr = msg[3]
    id1 = msg[4]
    id2 = msg[5]
    count = msg[6]
    instant = accumulate(msg, 7,4)
    total = accumulate(msg, 11,6) / float(223666) # To get kWh cf doc from rfxcom
    battery = (msg[17] & 0xF0) >> 4
    rssi = msg[17] & 0x0F

    print("Instant power " + str(instant))
    print("Total power " + str(total))
    print("Battery " + str(battery))
    print("RSSI " + str(rssi))
    return {'datetime': time.time()*1000 ,'packetLength': packetLength, 'packetType': msg[1],\
            'subType': subtype, 'seqNbr': seqNbr, 'id1': id1, 'id2': id2, 'count':count, 'instant': instant, \
            'total': total, 'battery': battery, 'RSSI': rssi, 'msg': base64.encodebytes(msg)}

def parseMessage(msg):
    print('Packet length ' + str(msg[0]))
    packetType = msg[1]

    data = {'datetime': time.time()*1000 ,'msg': base64.encodebytes(msg)}

    if packetType == 1:
        print("Received interface control (0x01) message")
        data = processInterfaceMessage(msg)
    elif packetType == 2:
        print("Received Receiver/Transmitter (0x02) message")
    elif packetType == 3:
        print("Received undecoded RF (0x03) message")
    elif packetType == 80:
        print("Received Temperature sensor (0x50) message")
    elif packetType == 81:
        print("Received Humidy sensor (0x51) message")
    elif packetType == 82:
        print("Received Temp & Humidity sensor (0x52) message")
        data = processTempHumSensor(msg)
    elif packetType == 83:
        print("Received Barometric sensor (0x53) message")
    elif packetType == 84:
        print("Received Temp, Hum, Baro sensor (0x54) message")
    elif packetType == 85:
        print("Received Rain sensor (0x55) message")
    elif packetType == 86:
        print("Received Wind sensor (0x56) message")
    elif packetType == 87:
        print("Received UV sensor (0x57) message")
    elif packetType == 90:
        print("Received Energy usage sensor (0x5A) message")
        data = processEnergyUsageSensor(msg)
    else:
        print("Unsupported packet type " + str(packetType))
    return data

def sendData(data, url):
    try:
        params = urllib.parse.urlencode(data)
        result = urllib.request.urlopen(url, params.encode('ascii'))
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
