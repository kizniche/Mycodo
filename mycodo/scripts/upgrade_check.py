# -*- coding: utf-8 -*-
# Perform checks used during install/upgrade
import sys

if __name__ == "__main__":
    try:
        if sys.argv[1] == '--min_python_version':

            if sys.version_info.major < int(sys.argv[2].split('.')[0]):
                sys.exit(1)
            if sys.version_info.major == int(sys.argv[2].split('.')[0]) and sys.version_info.minor < int(sys.argv[2].split('.')[1]):
                sys.exit(1)

    except:
        sys.exit(1)
