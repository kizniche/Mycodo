# coding=utf-8
#
# Code from https://github.com/Mailblocker/pySmartGadget with modifications.
# Mailblocker/pySmartGadget license, below.
#
# MIT License
#
# Copyright (c) 2018 Mailblocker
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import time

import struct
from bluepy.btle import DefaultDelegate
from bluepy.btle import Peripheral
from bluepy.btle import UUID


class SHT31Delegate(DefaultDelegate):
    def __init__(self, parent):
        DefaultDelegate.__init__(self)
        self.logger = logging.getLogger(
            "mycodo.device.sht31_smart_gadget.delegate")
        self.parent = parent
        self.sustainedNotifications = {'Temp': 0, 'Humi': 0}
        self.offset = 0

    def handleNotification(self, cHandle, data):
        # data format for logging data:
        # runnumber (4 bytes (unsigned int)) + N * value (N * 4 bytes (float32); while: 1 <= N <=4 )
        # data format for non-logging data: value (4 bytes (float32))
        unpackedData = list(struct.unpack(
            'I' + str(int((len(data) - 4) / 4)) + 'f', data))
        runnumber = unpackedData.pop(0)

        typeData = ''
        if cHandle == 55:
            typeData = 'Temp'
        elif cHandle == 50:
            typeData = 'Humi'

        if 0 < len(unpackedData):
            # logging data
            self.sustainedNotifications[typeData] = 0
            for measurement in unpackedData:
                timestamp = self.parent.newestTimeStampMs - (
                        (runnumber - self.offset) * self.parent.loggerInterval)
                self.parent.loggedData[typeData][timestamp] = measurement
                runnumber += 1
        else:
            # Non-logging data
            self.sustainedNotifications[typeData] += 1
            v = (self.sustainedNotifications['Temp'],
                 self.sustainedNotifications['Humi'])
            if all(x > 1 for x in v):
                # End communication
                self.parent.loggingReadout = False
                self.parent.setTemperatureNotification(False)
                self.parent.setHumidityNotification(False)


class SHT31:
    def __init__(self, addr=None, iface=None):
        self.logger = logging.getLogger(
            "mycodo.device.sht31_smart_gadget.sht31")
        self.loggedData = {'Temp': {}, 'Humi': {}}
        self.newestTimeStampMs = 0
        self.loggerInterval = 0
        self.loggingReadout = False
        self.characteristics = {}

        self.peripheral = Peripheral(addr, 'random', iface)
        if addr is not None:
            self.peripheral.setDelegate(SHT31Delegate(self))
            self.getCharacteristics()

    def getCharacteristics(self):
        self.characteristics = {
            'SystemId':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A23))[0],
            'ManufacturerNameString':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A29))[0],
            'ModelNumberString':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A24))[0],
            'SerialNumberString':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A25))[0],
            'HardwareRevisionString':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A27))[0],
            'FirmwareRevisionString':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A26))[0],
            'SoftwareRevisionString':  # READ
                self.peripheral.getCharacteristics(uuid=UUID(0x2A28))[0],
            'DeviceName':  # READ WRITE
                self.peripheral.getCharacteristics(
                    uuid=UUID("00002a00-0000-1000-8000-00805f9b34fb"))[0],
            'Battery':  # READ NOTIFY
                self.peripheral.getCharacteristics(
                    uuid=UUID(0x2A19))[0],
            'SyncTimeMs':  # WRITE
                self.peripheral.getCharacteristics(
                    uuid=UUID("0000f235-b38d-4985-720e-0f993a68ee41"))[0],
            'OldestTimeStampMs':  # READ WRITE
                self.peripheral.getCharacteristics(
                    uuid=UUID("0000f236-b38d-4985-720e-0f993a68ee41"))[0],
            'NewestTimeStampMs':  # READ WRITE
                self.peripheral.getCharacteristics(
                    uuid=UUID("0000f237-b38d-4985-720e-0f993a68ee41"))[0],
            'StartLoggerDownload':  # WRITE NOTIFY
                self.peripheral.getCharacteristics(
                    uuid=UUID("0000f238-b38d-4985-720e-0f993a68ee41"))[0],
            'LoggerIntervalMs':  # READ NOTIFY
                self.peripheral.getCharacteristics(
                    uuid=UUID("0000f239-b38d-4985-720e-0f993a68ee41"))[0],
            'Humidity':  # READ NOTIFY
                self.peripheral.getCharacteristics(
                    uuid=UUID("00001235-b38d-4985-720e-0f993a68ee41"))[0],
            'Temperature':  # READ NOTIFY
                self.peripheral.getCharacteristics(
                    uuid=UUID("00002235-b38d-4985-720e-0f993a68ee41"))[0]
        }
        if self.readFirmwareRevisionString() == '1.3':
            # Error in the documentation/firmware of 1.3 runnumber does not start with 0 it starts with 1,
            # therefore insert an offset here
            self.peripheral.delegate.offset = 1

    def connect(self, addr, iface=None):
        self.peripheral.setDelegate(SHT31Delegate(self))
        self.peripheral.connect(addr, 'random', iface)
        self.getCharacteristics()

    def disconnect(self):
        self.peripheral.disconnect()

    def readCharacteristcAscii(self, name):
        return self.characteristics[name].read().decode('ascii')

    def readDeviceName(self):
        return self.characteristics['DeviceName'].read().decode('ascii')

    def setDeviceName(self, name):
        return self.characteristics['DeviceName'].write(name.encode('ascii'))

    def readTemperature(self):
        return struct.unpack(
            'f', self.characteristics['Temperature'].read())[0]

    def setTemperatureNotification(self, enabled):
        if enabled:
            self.peripheral.writeCharacteristic(
                self.characteristics['Temperature'].valHandle + 2,
                int(1).to_bytes(1, byteorder='little'))
        else:
            self.peripheral.writeCharacteristic(
                self.characteristics['Temperature'].valHandle + 2,
                int(0).to_bytes(1, byteorder='little'))

    def readHumidity(self):
        return struct.unpack(
            'f', self.characteristics['Humidity'].read())[0]

    def setHumidityNotification(self, enabled):
        if enabled:
            self.peripheral.writeCharacteristic(
                self.characteristics['Humidity'].valHandle + 2,
                int(1).to_bytes(1, byteorder='little'))
        else:
            self.peripheral.writeCharacteristic(
                self.characteristics['Humidity'].valHandle + 2,
                int(0).to_bytes(1, byteorder='little'))

    def readBattery(self):
        return int.from_bytes(self.characteristics['Battery'].read(),
                              byteorder='little')

    def setSyncTimeMs(self, ts=None):
        timestampMs = ts if ts else int(round(time.time() * 1000))
        self.characteristics['SyncTimeMs'].write(
            timestampMs.to_bytes(8, byteorder='little'))

    def readOldestTimestampMs(self):
        return int.from_bytes(self.characteristics['OldestTimeStampMs'].read(),
                              byteorder='little')

    def setOldestTimestampMs(self, value):
        self.characteristics['OldestTimeStampMs'].write(
            value.to_bytes(8, byteorder='little'))

    def readNewestTimestampMs(self):
        return int.from_bytes(self.characteristics['NewestTimeStampMs'].read(),
                              byteorder='little')

    def setNewestTimestampMs(self, value):
        self.characteristics['NewestTimeStampMs'].write(
            value.to_bytes(8, byteorder='little'))

    def readLoggerIntervalMs(self):
        return int.from_bytes(self.characteristics['LoggerIntervalMs'].read(),
                              byteorder='little')

    def setLoggerIntervalMs(self, milliseconds):
        monthMs = (30 * 24 * 60 * 60 * 1000)

        if milliseconds < 1000:
            milliseconds = 1000
        elif milliseconds > monthMs:
            milliseconds = monthMs
        self.characteristics['LoggerIntervalMs'].write(
            (int(milliseconds)).to_bytes(4, byteorder='little'))

    def readLoggedDataInterval(self, start_ms=None, stop_ms=None):
        self.setSyncTimeMs()
        # Sleep 1s to enable the gadget to set SyncTime,
        # otherwise 0 is read from readNewestTimestampMs()
        time.sleep(1)
        self.setTemperatureNotification(True)
        self.setHumidityNotification(True)

        self.loggerInterval = self.readLoggerIntervalMs()
        if start_ms:
            self.setOldestTimestampMs(start_ms)
        if stop_ms:
            self.setNewestTimestampMs(stop_ms)

        self.newestTimeStampMs = self.readNewestTimestampMs()
        self.loggingReadout = True
        self.characteristics['StartLoggerDownload'].write(
            (1).to_bytes(1, byteorder='little'))

    def waitForNotifications(self, timeout):
        return self.peripheral.waitForNotifications(timeout)

    def isLogReadoutInProgress(self):
        return self.loggingReadout

    def readSystemId(self):
        return self.characteristics['SystemId'].read()

    def readManufacturerNameString(self):
        return self.readCharacteristcAscii('ManufacturerNameString')

    def readModelNumberString(self):
        return self.readCharacteristcAscii('ModelNumberString')

    def readSerialNumberString(self):
        return self.readCharacteristcAscii('SerialNumberString')

    def readHardwareRevisionString(self):
        return self.readCharacteristcAscii('HardwareRevisionString')

    def readFirmwareRevisionString(self):
        return self.readCharacteristcAscii('FirmwareRevisionString')

    def readSoftwareRevisionString(self):
        return self.readCharacteristcAscii('SoftwareRevisionString')

    def clear_logged_data(self):
        self.loggedData = {'Temp': {}, 'Humi': {}}
