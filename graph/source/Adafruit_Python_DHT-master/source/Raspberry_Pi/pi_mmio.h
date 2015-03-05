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

// Simple fast memory-mapped GPIO library for the Raspberry Pi.
#ifndef PI_MMIO_H
#define PI_MMIO_H

#include <stdint.h>

#define MMIO_SUCCESS 0
#define MMIO_ERROR_DEVMEM -1
#define MMIO_ERROR_MMAP -2

volatile uint32_t* pi_mmio_gpio;

int pi_mmio_init(void);

static inline void pi_mmio_set_input(const int gpio_number) {
  // Set GPIO register to 000 for specified GPIO number.
  *(pi_mmio_gpio+((gpio_number)/10)) &= ~(7<<(((gpio_number)%10)*3));
}

static inline void pi_mmio_set_output(const int gpio_number) {
  // First set to 000 using input function.
  pi_mmio_set_input(gpio_number);
  // Next set bit 0 to 1 to set output.
  *(pi_mmio_gpio+((gpio_number)/10)) |=  (1<<(((gpio_number)%10)*3));
}

static inline void pi_mmio_set_high(const int gpio_number) {
  *(pi_mmio_gpio+7) = 1 << gpio_number;
}

static inline void pi_mmio_set_low(const int gpio_number) {
  *(pi_mmio_gpio+10) = 1 << gpio_number;
}

static inline uint32_t pi_mmio_input(const int gpio_number) {
  return *(pi_mmio_gpio+13) & (1 << gpio_number);
}

#endif
