#
# This file is part of MicroPython LIS2HH12 driver
# Copyright (c) 2017-2018 Mika Tuupola
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/tuupola/micropython-lis2hh12
#

"""
MicroPython I2C driver for LIS2HH12 3-axis accelerometer
"""

import struct
import spi

_TEMP_L = 0x0b
_TEMP_H = 0x0c
_WHO_AM_I = 0x0f # 0b01000001 = 0x41
_CTRL1 = 0x20
_CTRL2 = 0x21
_CTRL3 = 0x22
_CTRL4 = 0x23
_CTRL5 = 0x24
_CTRL6 = 0x25
_CTRL7 = 0x26
_OUT_X_L = 0x28
_OUT_X_H = 0x29
_OUT_Y_L = 0x2a
_OUT_Y_H = 0x2b
_OUT_Z_L = 0x2c
_OUT_Z_H = 0x2d

# CTRL1
_ODR_MASK = 0b01110000
ODR_OFF = 0b00000000
ODR_10HZ  = 0b00010000
ODR_50HZ  = 0b00100000
ODR_100HZ = 0b00110000
ODR_200HZ = 0b01000000
ODR_400HZ = 0b01010000
ODR_800HZ = 0b01100000

# CTRL4
_FS_MASK = 0b00110000
FS_2G = 0b00000000
FS_4G = 0b00100000
FS_8G = 0b00110000

_SO_2G = 0.061 # 0.061 mg / digit
_SO_4G = 0.122 # 0.122 mg / digit
_SO_8G = 0.244 # 0.244 mg / digit

SF_G = 0.001 # 1 mg = 0.001 g
SF_SI = 0.00980665 # 1 mg = 0.00980665 m/s2

class LIS2HH12(spi.Spi):
    """Class which provides interface to LIS2HH12 3-axis accelerometer."""
    def __init__(self, drvname, pin_cs, clock=5000000, odr=ODR_100HZ, fs=FS_2G, sf=SF_SI):
        spi.Spi.__init__(self,pin_cs,drvname,clock)

        #print(self.whoami())
        if 0x41 != self.whoami():
            raise __builtins__.RuntimeError("LIS2HH12 not found in I2C bus.")

        self._register_char(_CTRL5, 0x43)
        sleep(100)
        self._register_char(_CTRL4, 0x06)
        self._register_char(_CTRL2, 0x40)
        self._register_char(_CTRL1, 0xBF)
        
        self._sf = sf
        self._odr(odr)
        self._fs(fs)

    def acceleration(self):
        """
        Acceleration measured by the sensor. By default will return a
        3-tuple of X, Y, Z axis acceleration values in m/s^2. Will
        return values in g if constructor was provided `sf=SF_G`
        parameter.
        """
        so = self._so
        sf = self._sf

        x = self._register_word(_OUT_X_L) * so * sf
        y = self._register_word(_OUT_Y_L) * so * sf
        z = self._register_word(_OUT_Z_L) * so * sf
        return (x, y, z)

    def temperature(self):
        """
        """
        t = self._register_word(_TEMP_L) / 256.0 + 25.0
        return t

    def whoami(self):
        """ Value of the whoami register. """
        return self._register_char(_WHO_AM_I)

    def _reg_read(self, register, fmt):
        self.select()
        data = struct.pack("<B", register | 0x80)
        self.write(data)
        data = self.read(struct.calcsize(fmt))
        self.unselect()
        return struct.unpack(fmt, data)

    def _reg_write(self, register, fmt, *values):
        self.select()
        data = struct.pack("<B"+fmt, register, *values)
        self.write(data)
        self.unselect()

    def _register_word(self, register, value=None):
        if value is None:
            return self._reg_read(register, "<h")[0]
        return self._reg_write(register, "<h", value)

    def _register_char(self, register, value=None):
        if value is None:
            return self._reg_read(register, "b")[0]
        return self._reg_write(register, "b", value)

    def _fs(self, value):
        char = self._register_char(_CTRL4)
        char &= ~_FS_MASK # clear FS bits
        char |= value
        self._register_char(_CTRL4, char)

        # Store the sensitivity multiplier
        if FS_2G == value:
            self._so = _SO_2G
        elif FS_4G == value:
            self._so = _SO_4G
        elif FS_8G == value:
            self._so = _SO_8G

    def _odr(self, value):
        char = self._register_char(_CTRL1)
        char &= ~_ODR_MASK # clear ODR bits
        char |= value
        self._register_char(_CTRL1, char)
