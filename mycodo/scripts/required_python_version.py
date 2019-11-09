# -*- coding: utf-8 -*-
# Checks if the required Python version (>= 3.7) is installed

import sys

try:
    if not sys.version_info.major == 3 and sys.version_info.minor >= 7:
        sys.exit(1)
except:
    sys.exit(1)
