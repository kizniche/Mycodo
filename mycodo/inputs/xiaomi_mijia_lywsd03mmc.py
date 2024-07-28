# coding=utf-8
#
# xiaomi_mijia_lywsd03mmc.py - Xiaomi Mijia LYWSD03MMC Input for Mycodo
#
# From https://github.com/JsBergbau/MiTemperature2 with modification
import array
import copy
import fcntl
import logging
import os
import re
import socket
import struct
import sys
import time
from errno import EALREADY

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.lockfile import LockFile

measurement_values = {}


# Measurements
measurements_dict = {
    0: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    2: {
        'measurement': 'battery',
        'unit': 'percent'
    },
    3: {
        'measurement': 'battery',
        'unit': 'decimal'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MIJIA_LYWSD03MMC',
    'input_manufacturer': 'Xiaomi',
    'input_name': 'Mijia LYWSD03MMC (ATC and non-ATC modes)',
    'input_name_short': 'Mijia LYWSD03MMC',
    'input_library': 'bluepy/bluez',
    'measurements_name': 'Battery/Humidity/Temperature',
    'measurements_dict': measurements_dict,

    'message': 'More information about ATC mode can be found at https://github.com/JsBergbau/MiTemperature2',

    'options_enabled': [
        'bt_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libglib2.0', 'libglib2.0'),
        ('apt', 'bluez', 'bluez'),
        ('apt', 'bluetooth', 'bluetooth'),
        ('apt', 'libbluetooth-dev', 'libbluetooth-dev'),
        ('pip-pypi', 'bluepy', 'bluepy==1.3.0'),
        ('pip-pypi', 'bluetooth', 'git+https://github.com/pybluez/pybluez.git')
    ],

    'interfaces': ['BT'],
    'bt_location': '00:00:00:00:00:00',
    'bt_adapter': '0',

    'custom_options': [
        {
            'id': 'atc',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable ATC Mode',
            'phrase': 'Enable sensor ATC mode'
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.lock_file = None

        self.atc = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.setup_logger(testing=testing, name=__name__, input_dev=input_dev)
            self.try_initialize()

    def initialize(self):
        self.lock_file = '/var/lock/bluetooth_dev_hci{}'.format(self.input_dev.bt_adapter)
        try:
            self.sensor = LYWSD03MMC(
                self.input_dev.location,
                int(self.input_dev.bt_adapter),
                atc=self.atc,
                logger=self.logger)
        except:
            self.logger.exception("Initializing Input")

    def get_measurement(self):
        """Gets the battery. humidity, and temperature."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        lf = LockFile()
        if lf.lock_acquire(self.lock_file, timeout=3600):
            try:
                self.sensor.run()

                global measurement_values
                self.logger.debug("Measurements: {}".format(measurement_values))

                if measurement_values:
                    if self.is_enabled(0):
                        self.value_set(0, measurement_values["hum"])
                    if self.is_enabled(1):
                        self.value_set(1, measurement_values["temp"])
                    if self.is_enabled(2):
                        self.value_set(2, measurement_values["bat_percent"])
                    if self.is_enabled(3):
                        self.value_set(3, measurement_values["bat_volt"])
                return self.return_dict
            except:
                self.logger.exception("Acquiring measurements")
            finally:
                lf.lock_release(self.lock_file)


class LYWSD03MMC:
    # With modifications, from https://github.com/JsBergbau/MiTemperature2
    # MiTemperature2 from:
    # https://github.com/colin-guyon/py-bluetooth-utils
    # inspired from 'iBeacon-Scanner-'
    # https://github.com/switchdoclabs/iBeacon-Scanner-/blob/master/blescan.py
    # and sometimes directly from the Bluez sources.
    #
    # published under MIT License
    # MIT License
    # Copyright (c) 2020 Colin GUYON
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
    try:
        import bluetooth._bluetooth as bluez
        from bluepy import btle

        class MyDelegate(btle.DefaultDelegate):
            def __init__(self, btle_import, logger=logging.getLogger(__name__)):
                btle_import.DefaultDelegate.__init__(self)
                self.logger = logger

            def handleNotification(self, cHandle, data):
                try:
                    temp = int.from_bytes(data[0:2], byteorder='little', signed=True) / 100
                    humidity = int.from_bytes(data[2:3], byteorder='little')
                    voltage = int.from_bytes(data[3:5], byteorder='little') / 1000.
                    batteryLevel = min(int(round((voltage - 2.1), 2) * 100), 100)  # 3.1 or above --> 100% 2.1 --> 0 %

                    self.logger.debug("Temperature: {}".format(temp))
                    self.logger.debug("Humidity: {}".format(humidity))
                    self.logger.debug("Battery: {} volts, {}%".format(voltage, batteryLevel))

                    global measurement_values
                    measurement_values = {
                        "temp": temp,
                        "hum": humidity,
                        "bat_volt": voltage,
                        "bat_percent": batteryLevel
                    }
                except Exception:
                    self.logger.exception("MyDelegate")
    except:
        pass

    LE_META_EVENT = 0x3E
    LE_PUBLIC_ADDRESS = 0x00
    LE_RANDOM_ADDRESS = 0x01

    OGF_LE_CTL = 0x08
    OCF_LE_SET_SCAN_PARAMETERS = 0x000B
    OCF_LE_SET_SCAN_ENABLE = 0x000C
    OCF_LE_CREATE_CONN = 0x000D
    OCF_LE_SET_ADVERTISING_PARAMETERS = 0x0006
    OCF_LE_SET_ADVERTISE_ENABLE = 0x000A
    OCF_LE_SET_ADVERTISING_DATA = 0x0008

    SCAN_TYPE_PASSIVE = 0x00
    SCAN_FILTER_DUPLICATES = 0x01
    SCAN_DISABLE = 0x00
    SCAN_ENABLE = 0x01

    # sub-events of LE_META_EVENT
    EVT_LE_CONN_COMPLETE = 0x01
    EVT_LE_ADVERTISING_REPORT = 0x02
    EVT_LE_CONN_UPDATE_COMPLETE = 0x03
    EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE = 0x04

    # Advertisement event types
    ADV_IND = 0x00
    ADV_DIRECT_IND = 0x01
    ADV_SCAN_IND = 0x02
    ADV_NONCONN_IND = 0x03
    ADV_SCAN_RSP = 0x04

    # Allow Scan Request from Any, Connect Request from Any
    FILTER_POLICY_NO_WHITELIST = 0x00
    # Allow Scan Request from White List Only, Connect Request from Any
    FILTER_POLICY_SCAN_WHITELIST = 0x01
    # Allow Scan Request from Any, Connect Request from White List Only
    FILTER_POLICY_CONN_WHITELIST = 0x02
    # Allow Scan Request from White List Only, Connect Request from White List Only
    FILTER_POLICY_SCAN_AND_CONN_WHITELIST = 0x03

    # Types of bluetooth scan
    SCAN_DISABLED = 0x00
    SCAN_INQUIRY = 0x01
    SCAN_PAGE = 0x02

    def __init__(self, mac_address, bluetooth_device, atc=False, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.device = mac_address
        self.interface = bluetooth_device
        self.atc = atc
        self.bluez = None
        self.btle = None

        try:
            import bluetooth._bluetooth as bluez
            from bluepy import btle
            self.bluez = bluez
            self.btle = btle
        except:
            pass

        self.logger.debug("LYWSD03MMC initialized")

    def run(self):
        if self.atc:
            self.run_mode_atc()
        else:
            self.run_mode_device()

    def toggle_device(self, dev_id, enable):
        """
        Power ON or OFF a bluetooth device.

        :param dev_id: Device id.
        :type dev_id: ``int``
        :param enable: Whether to enable of disable the device.
        :type enable: ``bool``
        """
        hci_sock = socket.socket(socket.AF_BLUETOOTH,
                                 socket.SOCK_RAW,
                                 socket.BTPROTO_HCI)
        self.logger.debug("Power %s bluetooth device %d" % ('ON' if enable else 'OFF', dev_id))
        # di = struct.pack("HbBIBBIIIHHHH10I", dev_id, *((0,) * 22))
        # fcntl.ioctl(hci_sock.fileno(), bluez.HCIGETDEVINFO, di)
        req_str = struct.pack("H", dev_id)
        request = array.array("b", req_str)
        try:
            fcntl.ioctl(hci_sock.fileno(),
                        self.bluez.HCIDEVUP if enable else self.bluez.HCIDEVDOWN,
                        request[0])
        except IOError as e:
            if e.errno == EALREADY:
                self.logger.debug("Bluetooth device %d is already %s" % (
                    dev_id, 'enabled' if enable else 'disabled'))
            else:
                raise
        finally:
            hci_sock.close()

    @staticmethod
    def raw_packet_to_str(pkt):
        """
        Returns the string representation of a raw HCI packet.
        """
        if sys.version_info > (3, 0):
            return ''.join('%02x' % struct.unpack("B", bytes([x]))[0] for x in pkt)
        else:
            return ''.join('%02x' % struct.unpack("B", x)[0] for x in pkt)

    def enable_le_scan(self, sock, interval=0x0800, window=0x0800,
                       filter_policy=FILTER_POLICY_NO_WHITELIST,
                       filter_duplicates=True):
        """
        Enable LE passive scan (with filtering of duplicate packets enabled).

        :param sock: A bluetooth HCI socket (retrieved using the
            ``hci_open_dev`` PyBluez function).
        :param interval: Scan interval.
        :param window: Scan window (must be less or equal than given interval).
        :param filter_policy: One of
            ``FILTER_POLICY_NO_WHITELIST`` (default value)
            ``FILTER_POLICY_SCAN_WHITELIST``
            ``FILTER_POLICY_CONN_WHITELIST``
            ``FILTER_POLICY_SCAN_AND_CONN_WHITELIST``

        .. note:: Scan interval and window are to multiply by 0.625 ms to
            get the real time duration.
        """
        self.logger.debug("Enable LE scan")
        own_bdaddr_type = self.LE_PUBLIC_ADDRESS  # does not work with LE_RANDOM_ADDRESS
        cmd_pkt = struct.pack("<BHHBB", self.SCAN_TYPE_PASSIVE, interval, window,
                              own_bdaddr_type, filter_policy)
        self.bluez.hci_send_cmd(sock, self.OGF_LE_CTL, self.OCF_LE_SET_SCAN_PARAMETERS, cmd_pkt)
        self.logger.debug("scan params: interval=%.3fms window=%.3fms own_bdaddr=%s "
              "whitelist=%s" %
              (interval * 0.625, window * 0.625,
               'public' if own_bdaddr_type == self.LE_PUBLIC_ADDRESS else 'random',
               'yes' if filter_policy in (self.FILTER_POLICY_SCAN_WHITELIST,
                                          self.FILTER_POLICY_SCAN_AND_CONN_WHITELIST)
               else 'no'))
        cmd_pkt = struct.pack("<BB", self.SCAN_ENABLE, self.SCAN_FILTER_DUPLICATES if filter_duplicates else 0x00)
        self.bluez.hci_send_cmd(sock, self.OGF_LE_CTL, self.OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

    def disable_le_scan(self, sock):
        """
        Disable LE scan.

        :param sock: A bluetooth HCI socket (retrieved using the
            ``hci_open_dev`` PyBluez function).
        """
        self.logger.debug("Disable LE scan")
        cmd_pkt = struct.pack("<BB", self.SCAN_DISABLE, 0x00)
        self.bluez.hci_send_cmd(sock, self.OGF_LE_CTL, self.OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

    def parse_le_advertising_events(self, sock, mac_addr=None, packet_length=None,
                                    handler=None, debug=True):
        """
        Parse and report LE advertisements.

        This is a blocking call, an infinite loop is started and the
        given handler will be called each time a new LE advertisement packet
        is detected and corresponds to the given filters.

        :param sock: A bluetooth HCI socket (retrieved using the
            ``hci_open_dev`` PyBluez function).
        :param mac_addr: list of filtered mac address representations
            (uppercase, with ':' separators).
            If not specified, the LE advertisement of any device will be reported.
            Example: mac_addr=('00:2A:5F:FF:25:11', 'DA:FF:12:33:66:12')
        :type mac_addr: ``list`` of ``string``
        :param packet_length: Filter a specific length of LE advertisement packet.
        :type packet_length: ``int``
        :param handler: Handler that will be called each time a LE advertisement
            packet is available (in accordance with the ``mac_addr``
            and ``packet_length`` filters).
        :type handler: ``callable`` taking 4 parameters:
            mac (``str``), adv_type (``int``), data (``bytes``) and rssi (``int``)
        :param debug: Enable debug prints.
        :type debug: ``bool``
        """
        if not debug and handler is None:
            raise ValueError("You must either enable debug or give a handler !")

        old_filter = sock.getsockopt(self.bluez.SOL_HCI, self.bluez.HCI_FILTER, 14)

        flt = self.bluez.hci_filter_new()
        self.bluez.hci_filter_set_ptype(flt, self.bluez.HCI_EVENT_PKT)
        # bluez.hci_filter_all_events(flt)
        self.bluez.hci_filter_set_event(flt, self.LE_META_EVENT)
        sock.setsockopt(self.bluez.SOL_HCI, self.bluez.HCI_FILTER, flt)

        self.logger.debug("socket filter set to ptype=HCI_EVENT_PKT event=LE_META_EVENT")
        self.logger.debug("Listening ...")

        try:
            while True:
                pkt = full_pkt = sock.recv(255)
                ptype, event, plen = struct.unpack("BBB", pkt[:3])

                if event != self.LE_META_EVENT:
                    # Should never occur because we filtered with this type of event
                    self.logger.error("Not a LE_META_EVENT !")
                    continue

                sub_event, = struct.unpack("B", pkt[3:4])
                if sub_event != self.EVT_LE_ADVERTISING_REPORT:
                    if debug:
                        self.logger.debug("Not a EVT_LE_ADVERTISING_REPORT !")
                    continue

                pkt = pkt[4:]
                adv_type = struct.unpack("b", pkt[1:2])[0]
                mac_addr_str = self.bluez.ba2str(pkt[3:9])

                if packet_length and plen != packet_length:
                    # ignore this packet
                    if debug:
                        self.logger.debug("packet with non-matching length: mac=%s adv_type=%02x plen=%s" %
                              (mac_addr_str, adv_type, plen))
                        self.logger.debug(self.raw_packet_to_str(pkt))
                    continue

                data = pkt[9:-1]

                rssi = struct.unpack("b", full_pkt[len(full_pkt) - 1:len(full_pkt)])[0]

                if mac_addr and mac_addr_str not in mac_addr:
                    if debug:
                        self.logger.error("packet with non-matching mac %s adv_type=%02x data=%s RSSI=%s" %
                              (mac_addr_str, adv_type, self.raw_packet_to_str(data), rssi))
                    continue

                if debug:
                    self.logger.debug("LE advertisement: mac=%s adv_type=%02x data=%s RSSI=%d" %
                          (mac_addr_str, adv_type, self.raw_packet_to_str(data), rssi))

                if handler is not None:
                    try:
                        return_val = handler(mac_addr_str, adv_type, data, rssi)
                        if return_val:
                            return
                    except Exception:
                        self.logger.exception("Exception when calling handler with a BLE advertising event")

        except KeyboardInterrupt:
            self.logger.debug("\nRestore previous socket filter")
            sock.setsockopt(self.bluez.SOL_HCI, self.bluez.HCI_FILTER, old_filter)
            raise

    def connect(self):
        p = self.btle.Peripheral(self.device, iface=self.interface)
        val = b'\x01\x00'
        p.writeCharacteristic(0x0038, val, True)  # enable notifications of Temperature, Humidity and Battery voltage
        p.writeCharacteristic(0x0046, b'\xf4\x01\x00', True)
        p.withDelegate(self.MyDelegate(self.btle))
        return p

    def le_advertise_packet_handler(self, mac, adv_type, data, rssi):
        self.logger.debug("Received BLE packet")
        data_str = self.raw_packet_to_str(data)
        ATCPaketMAC = data_str[10:22].upper()
        macStr = mac.replace(":", "").upper()
        atcIdentifier = data_str[6:10].upper()
        if atcIdentifier == "1A18" and ATCPaketMAC == macStr and mac == self.device:  # only Data from ATC devices
            self.logger.debug("BLE packet: %s %02x %s %d" % (mac, adv_type, data_str, rssi))
            temperature = int.from_bytes(bytearray.fromhex(data_str[22:26]), byteorder='big', signed=True) / 10.
            humidity = int(data_str[26:28], 16)
            batteryVoltage = int(data_str[30:34], 16) / 1000
            batteryPercent = int(data_str[28:30], 16)

            self.logger.debug("Temperature: {}".format(temperature))
            self.logger.debug("Humidity: {}".format(humidity))
            self.logger.debug("Battery: {} volts, {} %".format(batteryVoltage, batteryPercent))
            self.logger.debug("RSSI: {} dBm".format(rssi))

            global measurement_values
            measurement_values = {
                "temp": temperature,
                "hum": humidity,
                "bat_volt": batteryVoltage,
                "bat_percent": batteryPercent
            }
            return True

    def run_mode_device(self):
        self.logger.debug("Device mode")
        p = self.btle.Peripheral()
        connected = False
        pid = os.getpid()
        connectionLostCounter = 0

        while True:
            try:
                if not connected:
                    self.logger.debug("Trying to connect to " + self.device)
                    p = self.connect()
                    connected = True

                if p.waitForNotifications(2000):
                    p.disconnect()
                    time.sleep(5)
                    # It seems that sometimes bluepy-helper remains and thus prevents a reconnection,
                    # so we try killing our own bluepy-helper.
                    # we want to kill only bluepy from our own process tree, because other python
                    # scripts have there own bluepy-helper process.
                    pstree = os.popen("pstree -p " + str(pid)).read()
                    bluepypid = 0
                    try:  # Store the bluepypid, to kill it later
                        bluepypid = re.findall(r'bluepy-helper\((.*)\)', pstree)[0]
                    except IndexError:  # Should normally occur because we're disconnected
                        self.logger.debug("Couldn't find pid of bluepy-helper")
                    if bluepypid != 0:
                        os.system("kill " + bluepypid)
                        self.logger.debug("Killed bluepy with pid: " + str(bluepypid))
                    return
            except Exception as e:
                self.logger.debug("Connection lost")
                connectionLostCounter += 1
                if connected is True:  # First connection abort after connected
                    connected = False
                if connectionLostCounter >= 3:
                    self.logger.exception("3 unsuccessful connections. Exiting.")
                    return
                time.sleep(1)

            self.logger.debug("Waiting...")

    def run_mode_atc(self):
        self.logger.debug("ATC mode")
        self.toggle_device(self.interface, True)

        try:
            sock = self.bluez.hci_open_dev(self.interface)
        except:
            self.logger.exception("Cannot open bluetooth device hci{}".format(self.interface))
            return

        self.enable_le_scan(sock, filter_duplicates=False)
        try:
            # Blocking call (the given handler will be called each time a new LE
            # advertisement packet is detected)
            self.parse_le_advertising_events(
                sock,
                handler=self.le_advertise_packet_handler,
                debug=False)
        finally:
            self.disable_le_scan(sock)
