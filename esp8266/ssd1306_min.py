# The MIT License (MIT)
# 
# Based on Kenneth Henderick's Micropython drivers: https://github.com/khenderick/micropython-drivers
# and Vladimir Iakovlev's addition of font handling:  https://github.com/nvbn/micropython-drivers/tree/master/ssd1306
# Copyright (c) 2014 Kenneth Henderick
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from machine import Pin, I2C
import font

# Constants
DISPLAYOFF          = 0xAE
SETCONTRAST         = 0x81
DISPLAYALLON_RESUME = 0xA4
DISPLAYALLON        = 0xA5
NORMALDISPLAY       = 0xA6
INVERTDISPLAY       = 0xA7
DISPLAYON           = 0xAF
SETDISPLAYOFFSET    = 0xD3
SETCOMPINS          = 0xDA
SETVCOMDETECT       = 0xDB
SETDISPLAYCLOCKDIV  = 0xD5
SETPRECHARGE        = 0xD9
SETMULTIPLEX        = 0xA8
SETLOWCOLUMN        = 0x00
SETHIGHCOLUMN       = 0x10
SETSTARTLINE        = 0x40
MEMORYMODE          = 0x20
COLUMNADDR          = 0x21
PAGEADDR            = 0x22
COMSCANINC          = 0xC0
COMSCANDEC          = 0xC8
SEGREMAP            = 0xA0
CHARGEPUMP          = 0x8D
EXTERNALVCC         = 0x10
SWITCHCAPVCC        = 0x20
SETPAGEADDR         = 0xB0
SETCOLADDR_LOW      = 0x00
SETCOLADDR_HIGH     = 0x10
ACTIVATE_SCROLL                      = 0x2F
DEACTIVATE_SCROLL                    = 0x2E
SET_VERTICAL_SCROLL_AREA             = 0xA3
RIGHT_HORIZONTAL_SCROLL              = 0x26
LEFT_HORIZONTAL_SCROLL               = 0x27
VERTICAL_AND_RIGHT_HORIZONTAL_SCROLL = 0x29
VERTICAL_AND_LEFT_HORIZONTAL_SCROLL  = 0x2A

class SSD1306(object):

  def __init__(self):
    # assumes height=32, pages=4, columns=128, internal vcc

    self.cbuffer = bytearray(2)
    self.cbuffer[0] = 0x80

    self.i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000) 

  def clear(self):
    self.buffer = bytearray(513)
    self.buffer[0] = 0x40

  def write_command(self, command_byte):
    self.cbuffer[1] = command_byte
    self.i2c.writeto(0x3c, self.cbuffer)

  def invert_display(self, invert):
    self.write_command(INVERTDISPLAY if invert else NORMALDISPLAY)

  def display(self):
    self.write_command(COLUMNADDR)
    self.write_command(0)
    self.write_command(127) #(self.columns - 1)
    self.write_command(PAGEADDR)
    self.write_command(0)
    self.write_command(3) #(self.pages - 1)
    self.i2c.writeto(0x3c, self.buffer)

  def set_pixel(self, x, y, state):
    index = x + (int(y / 8) * 128)
    if state:
      self.buffer[1 + index] |= (1 << (y & 7))
    else:
      self.buffer[1 + index] &= ~(1 << (y & 7))

  def init_display(self):
    chargepump = 0x14
    precharge  = 0xf1
    multiplex  = 0x1f 
    compins    = 0x02 
    contrast   = 0xff # 0x8f if self.height == 32 else (0x9f if self.external_vcc else 0x9f)
    data = [DISPLAYOFF,
            SETDISPLAYCLOCKDIV, 0x80,
            SETMULTIPLEX, multiplex,
            SETDISPLAYOFFSET, 0x00,
            SETSTARTLINE | 0x00,
            CHARGEPUMP, chargepump,
            MEMORYMODE, 0x00,
            SEGREMAP | 0x10,
            COMSCANDEC,
            SETCOMPINS, compins,
            SETCONTRAST, contrast,
            SETPRECHARGE, precharge,
            SETVCOMDETECT, 0x40,
            DISPLAYALLON_RESUME,
            NORMALDISPLAY,
            DISPLAYON]
    for item in data:
      self.write_command(item)
    self.clear()
    self.display()

  def poweron(self):
    pass

  def poweroff(self):
    self.write_command(DISPLAYOFF)

  def contrast(self, contrast):
    self.write_command(SETCONTRAST)
    self.write_command(contrast)

  def draw_text(self, x, y, string, size=1, space=1):
    def pixel_x(char_number, char_column, point_row):
      char_offset = x + char_number * size * font.cols + space * char_number
      pixel_offset = char_offset + char_column * size + point_row
      return 128 - pixel_offset

    def pixel_y(char_row, point_column):
      char_offset = y + char_row * size
      return char_offset + point_column

    def pixel_mask(char, char_column, char_row):
      #char_index_offset = ord(char) * font.cols #original
      char_index_offset = (ord(char)-32) * font.cols
      return font.bytes[char_index_offset + char_column] >> char_row & 0x1

    pixels = (
      (pixel_x(char_number, char_column, point_row),
       pixel_y(char_row, point_column),
       pixel_mask(char, char_column, char_row))
      for char_number, char in enumerate(string)
      for char_column in range(font.cols)
      for char_row in range(font.rows)
      for point_column in range(size)
      for point_row in range(1, size + 1))

    for pixel in pixels:
      self.set_pixel(*pixel)
