'''
Copyright (C) 2012 Matthew Skolaut

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and 
associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import smbus
from bitstring import *
from time import *

CMD_CLEAR 			= 0x01
CMD_HOME 			= 0x02
CMD_ENTRY_L 		= 0x04
CMD_ENTRY_LS	 	= 0x05
CMD_ENTRY_R 		= 0x06
CMD_ENTRY_RS 		= 0x07
CMD_DISP_OFF 		= 0x08
CMD_DISP_ON 		= 0x0C
CMD_CURS_OFF 		= 0x0C
CMD_CURS_SLD 		= 0x0E
CMD_CURS_BLINK 		= 0x0F
CMD_SHIFT_CURS_L1 	= 0x10
CMD_SHIFT_CURS_R1 	= 0x14
CMD_SHIFT_DISP_L1 	= 0x18
CMD_SHIFT_DISP_R1 	= 0x1C
CMD_4BIT_1L 		= 0x20
CMD_4BIT_2L 		= 0x28
CMD_8BIT_1L 		= 0x30
CMD_8BIT_2L 		= 0x38

ADDR_L1				= 0x80
ADDR_L2				= 0x80 + 0x40
ADDR_L3				= 0x80 + 0x20
ADDR_L4				= 0x80 + 0x60
ADDR_FNT			= 0x40

# General i2c device class so that other devices can be added easily
class i2c_device:
	def __init__(self, addr, port):
		self.debug = 1
		self.current = BitArray(length=8, uint=0)
		self.addr = addr
		if not self.debug:
			self.bus = smbus.SMBus(port)

	def write(self, byte):
		self.current = BitArray(length=8, uint=byte)
		if not self.debug:
			self.bus.write_byte(self.addr, byte)
		else:
			print self.current.bin
		sleep(0.4)


	def read(self):
		if not self.debug:
			return self.bus.read_byte(self.addr)
		else:
			return self.current.uint

	def writereg(self, reg, byte):
		self.current = BitArray(length=8, uint=byte)
		if not self.debug:
			self.bus.write_byte_data(reg, byte)
		else:
			if self.current.uint == 255:
				quit()
			print reg, byte, BitArray(length=8, uint=reg).bin, self.current.bin

	def readreg(self, reg, byte):
		if not self.debug:
			return self.bus.read_byte_data(reg, byte)
		else:
			return self.current.uint

	def read_nbytes_data(self, data, n): # For sequential reads > 1 byte
		# return self.bus.read_i2c_block_data(self.addr, data, n)
		return [31, 2]


class lcd:
	#initializes objects and lcd
	'''
	mode Codes:
	0: lower 4 bits of expander are commands bits
	1: top 4 bits of expander are commands bits AND P0-4 P1-5 P2-6
	2: top 4 bits of expander are commands bits AND P0-6 P1-5 P2-4
	3: Adafruit LCD shield setup
	'''
	def __init__(self, addr, port, mode=0):
		self.mode = mode
		if mode == 3:
			self.lcd_device = MCP23017(addr, port)
		else:
			self.lcd_device = i2c_device(addr, port)
		if self.mode == 1 or self.mode == 2:
			self.lcd_device.write(0x30)
			self.lcd_strobe()
			sleep(0.0005)
			self.lcd_strobe()
			sleep(0.0005)
			self.lcd_strobe()
			sleep(0.0005)
			self.lcd_device.write(0x20)
			self.lcd_strobe()
			sleep(0.0005)
		else:
			self.lcd_device.write(0x03)
			self.lcd_strobe()
			sleep(0.0005)
			self.lcd_strobe()
			sleep(0.0005)
			self.lcd_strobe()
			sleep(0.0005)
			self.lcd_device.write(0x02)
			self.lcd_strobe()
			sleep(0.0005)

		self.lcd_write(CMD_4BIT_2L)
		self.lcd_write(CMD_DISP_OFF)
		self.lcd_write(CMD_CLEAR)
		self.lcd_write(CMD_ENTRY_R)
		self.lcd_write(CMD_CURS_BLINK)

	# clocks EN to latch command
	def lcd_strobe(self):
		if self.mode == 1:
			self.lcd_device.write((self.lcd_device.read() | 0x04))
			self.lcd_device.write((self.lcd_device.read() & 0xFB))
		if self.mode == 2:
			self.lcd_device.write((self.lcd_device.read() | 0x01))
			self.lcd_device.write((self.lcd_device.read() & 0xFE))
		if self.mode == 3:
			self.lcd_device.writeb((self.lcd_device.read() | 0x10))
			self.lcd_device.writeb((self.lcd_device.read() & 0xEF))
		else:
			self.lcd_device.write((self.lcd_device.read() | 0x10))
			self.lcd_device.write((self.lcd_device.read() & 0xEF))

	# write a command to lcd
	def lcd_write(self, cmd):
		if self.mode:
			self.lcd_device.write((cmd >> 4)<<4)
			self.lcd_strobe()
			self.lcd_device.write((cmd & 0x0F)<<4)
			self.lcd_strobe()
			self.lcd_device.write(0x0)
		if self.mode == 3:
			self.lcd_device.write((brev(cmd) & 0x0F))
			self.lcd_strobe()
			self.lcd_device.write((brev(cmd) >> 4))
			self.lcd_strobe()
			self.lcd_device.write(0x0)
		else:
			self.lcd_device.write((cmd >> 4))
			self.lcd_strobe()
			self.lcd_device.write((cmd & 0x0F))
			self.lcd_strobe()
			self.lcd_device.write(0x0)

	# write a character to lcd (or character rom)
	def lcd_write_char(self, charvalue):
		if self.mode == 1:
			self.lcd_device.write((0x01 | (charvalue >> 4)<<4))
			self.lcd_strobe()
			self.lcd_device.write((0x01 | (charvalue & 0x0F)<<4))
			self.lcd_strobe()
			self.lcd_device.write(0x0)
		if self.mode == 2:
			self.lcd_device.write((0x04 | (charvalue >> 4)<<4))
			self.lcd_strobe()
			self.lcd_device.write((0x04 | (charvalue & 0x0F)<<4))
			self.lcd_strobe()
			self.lcd_device.write(0x0)
		else:
			self.lcd_device.write((0x40 | (charvalue >> 4)))
			self.lcd_strobe()
			self.lcd_device.write((0x40 | (charvalue & 0x0F)))
			self.lcd_strobe()
			self.lcd_device.write(0x0)

	# put char function
	def lcd_putc(self, char):
		self.lcd_write_char(ord(char))

	# put string function
	def lcd_puts(self, string, line):
		if line == 1:
			self.lcd_write(ADDR_L1)
		if line == 2:
			self.lcd_write(ADDR_L2)
		if line == 3:
			self.lcd_write(ADDR_L3)
		if line == 4:
			self.lcd_write(ADDR_L4)

		for char in string:
			self.lcd_putc(char)

	# clear lcd and set to home
	def lcd_clear(self):
		self.lcd_write(CMD_CLEAR)
		self.lcd_write(CMD_HOME)

	# add custom characters (0 - 7)
	def lcd_load_custon_chars(self, fontdata):
		self.lcd_write(ADDR_FNT);
		for char in fontdata:
			for line in char:
				self.lcd_write_char(line)

class tmp102:
	def __init__(self, addr, port):
		self.sensor = i2c_device(addr, port)

	# read a register
	def read_reg(self, reg):
		return self.sensor.read_nbytes_data(reg, 2)

	# read the current temp in celsius
	def read_temp(self):
		tempraw = self.read_reg(0)
		return tempraw[0] + (tempraw[1] >> 4) * 0.0625

class MCP23017:
	def __init__(self, addr, port):
		self.expander = i2c_device(addr, port)
		self.expander.writereg(0x1, 0x0)
		self.expander.writereg(0x13, 0x0)

	def writeb(self, byte):
		self.expander.writereg(0x1, 0x0)
		self.expander.writereg(0x13, byte)
		sleep(0.4)

	def write(self, byte): # assumed portb
		self.expander.writereg(0x1, 0x0)
		self.expander.writereg(0x13, byte)
		sleep(0.4)

	def readb(self):
		return self.expander.readreg(0x1, 0x0)

	def read(self): # assumed portb
		return self.expander.readreg(0x1, 0x0)

def brev(x):
    return ((x * 0x0202020202 & 0x010884422010) % 1023)