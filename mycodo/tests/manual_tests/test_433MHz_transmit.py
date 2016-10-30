#!/usr/bin/python
# coding=utf-8

import time
from pi_switch import RCSwitchSender

on = 29955
off = 29964

sender = RCSwitchSender()
sender.setProtocol(1)
sender.setPulseLength(189)
sender.enableTransmit(0)

sender.sendDecimal(on, 24)  # switch on
time.sleep(3)
sender.sendDecimal(off, 24)  # switch off
