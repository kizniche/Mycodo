// Copyright (c) 2014 Adafruit Industries
// Author: Tony DiCola
// Based on code from Gert van Loo & Dom: http://elinux.org/RPi_Low-level_peripherals#GPIO_Code_examples

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
#include <unistd.h>

#include "pi_mmio.h"

#define BASE 0x20000000
#define GPIO_BASE (BASE + 0x200000)
#define GPIO_LENGTH 4096

volatile uint32_t* pi_mmio_gpio = NULL;

int pi_mmio_init(void) {
  if (pi_mmio_gpio == NULL) {
    int fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (fd == -1) {
      // Error opening /dev/mem.  Probably not running as root.
      return MMIO_ERROR_DEVMEM;
    }
    // Map GPIO memory to location in process space.
    pi_mmio_gpio = (uint32_t*)mmap(NULL, GPIO_LENGTH, PROT_READ | PROT_WRITE, MAP_SHARED, fd, GPIO_BASE);
    close(fd);
    if (pi_mmio_gpio == MAP_FAILED) {
      // Don't save the result if the memory mapping failed.
      pi_mmio_gpio = NULL;
      return MMIO_ERROR_MMAP;
    }
  }
  return MMIO_SUCCESS;
}
