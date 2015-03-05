from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages, Extension
import sys

import Adafruit_DHT.platform_detect as platform_detect


# Check if an explicit platform was chosen with a command line parameter.
# Kind of hacky to manipulate the argument list before calling setup, but it's
# the best simple option for adding optional config to the setup.
platform = platform_detect.UNKNOWN
pi_version = None
if '--force-pi' in sys.argv:
	platform = platform_detect.RASPBERRY_PI
	pi_version = 1
	sys.argv.remove('--force-pi')
elif '--force-pi2' in sys.argv:
	platform = platform_detect.RASPBERRY_PI
	pi_version = 2
	sys.argv.remove('--force-pi2')
elif '--force-bbb' in sys.argv:
	platform = platform_detect.BEAGLEBONE_BLACK
	sys.argv.remove('--force-bbb')
elif '--force-test' in sys.argv:
	platform = 'TEST'
	sys.argv.remove('--force-test')
else:
	# No explicit platform chosen, detect the current platform.
	platform = platform_detect.platform_detect()

# Pick the right extension to compile based on the platform.
extensions = []
if platform == platform_detect.RASPBERRY_PI:
	# Get the Pi version (1 or 2)
	if pi_version is None:
		pi_version = platform_detect.pi_version()
	# Build the right extension depending on the Pi version.
	if pi_version == 1:
		extensions.append(Extension("Adafruit_DHT.Raspberry_Pi_Driver", 
									["source/_Raspberry_Pi_Driver.c", "source/common_dht_read.c", "source/Raspberry_Pi/pi_dht_read.c", "source/Raspberry_Pi/pi_mmio.c"], 
									libraries=['rt'],
									extra_compile_args=['-std=gnu99']))
	elif pi_version == 2:
		extensions.append(Extension("Adafruit_DHT.Raspberry_Pi_2_Driver", 
									["source/_Raspberry_Pi_2_Driver.c", "source/common_dht_read.c", "source/Raspberry_Pi_2/pi_2_dht_read.c", "source/Raspberry_Pi_2/pi_2_mmio.c"], 
									libraries=['rt'],
									extra_compile_args=['-std=gnu99']))
	else:
		raise RuntimeError('Detected Pi version that has no appropriate driver available.')
elif platform == platform_detect.BEAGLEBONE_BLACK:
	extensions.append(Extension("Adafruit_DHT.Beaglebone_Black_Driver",
								["source/_Beaglebone_Black_Driver.c", "source/common_dht_read.c", "source/Beaglebone_Black/bbb_dht_read.c", "source/Beaglebone_Black/bbb_mmio.c"],
								libraries=['rt'],
								extra_compile_args=['-std=gnu99']))
elif platform == 'TEST':
	extensions.append(Extension("Adafruit_DHT.Test_Driver",
								["source/_Test_Driver.c", "source/Test/test_dht_read.c"],
								extra_compile_args=['-std=gnu99']))
else:
	print 'Could not detect if running on the Raspberry Pi or Beaglebone Black.  If this failure is unexpected, you can run again with --force-pi or --force-bbb parameter to force using the Raspberry Pi or Beaglebone Black respectively.'
	sys.exit(1)

# Call setuptools setup function to install package.
setup(name              = 'Adafruit_DHT',
	  version           = '1.1.0',
	  author            = 'Tony DiCola',
	  author_email      = 'tdicola@adafruit.com',
	  description       = 'Library to get readings from the DHT11, DHT22, and AM2302 humidity and temperature sensors on a Raspberry Pi or Beaglebone Black.',
	  license           = 'MIT',
	  url               = 'https://github.com/adafruit/Adafruit_Python_DHT/',
	  packages          = find_packages(),
	  ext_modules       = extensions)
