# -*- coding: utf-8 -*-
#
#  config_maintenance.py - Global Mycodo settings
#

# Maintenance Mode
# Prevents users from installing or upgrading Mycodo
# Used by the developers to test the install/upgrade system for stability prior to release
# Create ~/Mycodo/.maintenance to override maintenance mode and allow an install/upgrade:

MAINTENANCE_MODE = False
