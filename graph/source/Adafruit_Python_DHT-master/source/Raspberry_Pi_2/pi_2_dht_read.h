// Copyright (c) 2014 Adafruit Industries
// Author: Tony DiCola

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
#ifndef PI_2_DHT_READ_H
#define PI_2_DHT_READ_H

#include "../common_dht_read.h"

// Read DHT sensor connected to GPIO pin (using BCM numbering).  Humidity and temperature will be 
// returned in the provided parameters. If a successfull reading could be made a value of 0 
// (DHT_SUCCESS) will be returned.  If there was an error reading the sensor a negative value will
// be returned.  Some errors can be ignored and retried, specifically DHT_ERROR_TIMEOUT or DHT_ERROR_CHECKSUM.
int pi_2_dht_read(int sensor, int pin, float* humidity, float* temperature);

#endif
