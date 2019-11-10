# -*- coding: utf-8 -*-
# Perform checks used during install/upgrade

import os
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

from mycodo.config_maintenance import MAINTENANCE_MODE

if __name__ == "__main__":
    try:
        if sys.argv[1] == '--min_python_version':

            if not sys.version_info.major >= int(sys.argv[2].split('.')[0]):
                sys.exit(1)
            if not sys.version_info.minor >= int(sys.argv[2].split('.')[1]):
                sys.exit(1)

        elif sys.argv[1] == '--maintenance_mode':

            if not MAINTENANCE_MODE:
                sys.exit(1)

    except:
        sys.exit(1)
