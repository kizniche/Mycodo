#!/usr/bin/python
# coding=utf-8

from pi_switch import RCSwitchReceiver

receiver = RCSwitchReceiver()
receiver.enableReceive(2)

num = 0

while True:
    if receiver.available():
        received_value = receiver.getReceivedValue()
        if received_value:
            num += 1
            print("Received[{}]: {}".format(num, received_value))
            print("Bit Length: {} bit".format(receiver.getReceivedBitlength()))
            print("Delay: {}".format(receiver.getReceivedDelay()))
            print("Protocol: {}\n".format(receiver.getReceivedProtocol()))
        receiver.resetAvailable()
