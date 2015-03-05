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
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "bbb_mmio.h"

#define GPIO_LENGTH 4096
#define GPIO0_ADDR 0x44E07000
#define GPIO1_ADDR 0x4804C000
#define GPIO2_ADDR 0x481AC000
#define GPIO3_ADDR 0x481AF000

// Store mapping of GPIO base number to GPIO address.
static uint32_t gpio_addresses[4] = { GPIO0_ADDR, GPIO1_ADDR, GPIO2_ADDR, GPIO3_ADDR };

// Cache memory-mapped GPIO addresses.
static volatile uint32_t* gpio_base[4] = { NULL };

int bbb_mmio_get_gpio(int base, int number, gpio_t* gpio) {
  // Validate input parameters.
  if (gpio == NULL) {
    return MMIO_ERROR_ARGUMENT;
  }
  if (base < 0 || base > 3) {
    return MMIO_ERROR_ARGUMENT;
  }
  if (number < 0 || number > 31) {
    return MMIO_ERROR_ARGUMENT;
  }
  // Map GPIO memory if its hasn't been mapped already.
  if (gpio_base[base] == NULL) {
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd == -1) {
      // Error opening /dev/mem.  Probably not running as root.
      return MMIO_ERROR_DEVMEM;
    }
    // Map GPIO memory to location in process space.
    gpio_base[base] = (uint32_t*)mmap(NULL, GPIO_LENGTH, PROT_READ | PROT_WRITE, MAP_SHARED, fd, gpio_addresses[base]);
    if (gpio_base[base] == MAP_FAILED) {
      // Don't save the result if the memory mapping failed.
      gpio_base[base] = NULL;
      return MMIO_ERROR_MMAP;
    }
  }
  // Initialize and set GPIO fields.
  memset(gpio, 0, sizeof(gpio));
  gpio->base = gpio_base[base];
  gpio->number = number;
  return MMIO_SUCCESS;
}
