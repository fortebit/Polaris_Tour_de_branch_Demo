#   Zerynth - zerynth-libs - texas-ads1015/ads1015.py
#
#   Zerynth library for ADS1015 ADC
#
#
#
# @Author: andreabau
#
# @Date:   2017-11-09 09:45:55
# @Last Modified by:   andreabau
# @Last Modified time: 2018-01-12 16:49:06
"""
.. module:: ads1015

****************
ADS1015 Module
****************

.. _datasheet: http://www.ti.com/lit/ds/symlink/ads1015.pdf

This module contains the Zerynth driver for Texas Instruments ADS101x precision Analog-to-Digital Converters with I2C interface (datasheet_).

Example: ::

        from texas.ads1015 import ADS1015

        ...

        ads = ads1015.ADS1015(I2C0, addr = 0x49, clk=400000)

        ads.set(ch = 4, pga = 1)
        value1 = ads.get_raw_data()

        ads.set(ch = 3, pga = 4)
        value2 = ads.get_raw_data()


"""
import i2c


REG_CONV = 0
REG_CONF = 1
REG_LOTH = 2
REG_HITH = 3


class ADS1015(i2c.I2C):
    timeout = 1000
    """

===============
ADS1015 class
===============

.. class:: ADS1015(i2cdrv, addr = 0x48, clk = 100000)

    Creates an instance of the ADS1015 class. This class allows the control of all ADS1013, ADS1014, and ADS1015 devices.

    :param i2cdrv: I2C Bus used '(I2C0, ...)'
    :param addr: Slave address, default 0x48
    :param clk: Clock speed, default 100 kHz



    """

    def __init__(self, i2cdrv, addr=0x48, clk=100000):
        i2c.I2C.__init__(self, i2cdrv, addr, clk)
        self.register = None
        self.start()

    def _set_register(self, reg):
        reg = reg & 0x03
        if reg != self.register:
            self.write(reg, self.timeout)
            self.register = reg

    def read_register(self, reg, n):
        ex = None
        self.lock()
        try:
            self._set_register(reg)
            res = self.read(n, self.timeout)
        except Exception as e:
            ex = e
        finally:
            self.unlock()
        if ex is not None:
            raise ex
        return res

    def set(self, os=0, ch=4, pga=2, mode=0, sps=4, cmode=0, cpol=0, clat=0, cque=3):
        """
    .. method:: set(os = 0, ch = 4, pga = 2, mode = 0, sps = 4, cmode = 0, cpol = 0, clat = 0, cque = 3)

        Sets the device's configuration register.

        **Parameters:**

        * **os** : sets the Operational Status od the device. It can only be written when in power-down state and has no effect when a conversion is ongoing, available values are:

            * ``0`` : No effect

            * ``1`` : Start a single conversion (when in power-down state)

        * **ch** : (ADS1015 only) Configure the input multiplexer.

            ====== ================= ===================================================
            ch      positive channel   negative channel
            ====== ================= ===================================================
            0      AIN0              AIN1
            1      AIN0              AIN3
            2      AIN1              AIN3
            3      AIN2              AIN3
            4      AIN0              GND
            5      AIN1              GND
            6      AIN2              GND
            7      AIN3              GND
            ====== ================= ===================================================

        * **pga** : (ADS1014 and ADS1015 only) PGA Gain selection.

            ====== ===================  ======================
            pga     Gain                 ADC full-scale range
            ====== ===================  ======================
            0      1/3                     ± 6.144 V
            1      1/2                     ± 4.096 V
            2      1                       ± 2.048 V
            3      2                       ± 1.024 V
            4      4                       ± 0.512 V
            5      8                       ± 0.256 V
            6      8                       ± 0.256 V
            7      8                       ± 0.256 V
            ====== ===================  ======================

        * **mode** : sets the device operating mode. Available values are:

            * ``0`` : Continuous-conversion mode.

            * ``1`` : Single-shot mode or power-down state

        * **sps** : Data rate setting.

            ====== ===================
            sps     Samples per second
            ====== ===================
            0      128
            1      250
            2      490
            3      920
            4      1600
            5      2400
            6      3300
            7      3300
            ====== ===================

        * **cmode** : (ADS1014 and ADS1015 only) Comparator operating mode.

            * ``0`` : Traditional comparator.

            * ``1`` : Window comparator.

        * **cpol** : (ADS1014 and ADS1015 only) Set the polarity of the ALERT/RDY pin.

            * ``0`` : Active low.

            * ``1`` : Active high.

        * **clat** : (ADS1014 and ADS1015 only) Controls whether the ALERT/RDY pin latches.

            * ``0`` : Nonlatching comparator.

            * ``1`` : Latching comparator.

        * **cque** : (ADS1014 and ADS1015 only) Comparator queue and disable.

            ====== ============================================================================
            cque     effect
            ====== ============================================================================
            0      Assert ALERT/RDY pin after one conversion exceeding the threshold
            1      Assert ALERT/RDY pin after two conversion exceeding the threshold
            2      Assert ALERT/RDY pin after four conversion exceeding the threshold
            3      Disable comparator and set ALERT/RDY pin to high-impedance
            ====== ============================================================================


        """

        os = (os & 0x01) << 7
        ch = (ch & 0x07) << 4
        pga = (pga & 0x07) << 1
        mode = mode & 0x01

        sps = (sps & 0x07) << 5
        cmode = (cmode & 0x01) << 4
        cpol = (cpol & 0x01) << 3
        clat = (clat & 0x01) << 2
        cque = cque & 0x03

        cmd = bytearray(3)
        cmd[0] = REG_CONF
        cmd[1] = os | ch | pga | mode
        cmd[2] = sps | cmode | cpol | clat | cque

        ex = None
        self.lock()
        try:
            self.write(cmd, self.timeout)
            self.register = REG_CONF
        except Exception as e:
            ex = e
        finally:
            self.unlock()
        if ex is not None:
            raise ex

    def set_threshold(self, low, high):
        """
    .. method:: set_threshold(low, high)

        Set the upper and lower threshold values used by the comparator. The comparator is implemented as a digital comparator;
        therefore, the valuese must be updated whenever the PGA settings are changed.

        Available values for both *low* and *high* parameters are 12-bit signed intergers, from -2048 to 2047.

        """
        if low < 0:
            tc_low = (~ -(low + 1)) & 0xfff
        else:
            tc_low = low & 0xfff

        if high < 0:
            tc_high = (~ -(high + 1)) & 0xfff
        else:
            tc_high = high & 0xfff

        cmd_lo = bytearray(3)
        cmd_lo[0] = REG_LOTH
        cmd_lo[1] = (tc_low >> 4) & 0xFF
        cmd_lo[2] = (tc_low << 4) & 0xFF

        cmd_hi = bytearray(3)
        cmd_hi[0] = REG_LOTH
        cmd_hi[1] = (tc_high >> 4) & 0xFF
        cmd_hi[2] = (tc_high << 4) & 0xFF

        ex = None
        self.lock()
        try:
            self.write(cmd_lo, self.timeout)
            self.write(cmd_hi, self.timeout)
            self.register = REG_HITH
        except Exception as e:
            ex = e
        finally:
            self.unlock()
        if ex is not None:
            raise ex

    def get_raw_data(self):
        """

    .. method:: get_raw_data()

        Return the conversion result as an 12-bit signed integer.
        A positive full-scale input produces an output of 2047, a negative full-scale input produces an output of -2048.

        """
        r = self.read_register(REG_CONV, 2)

        v = ((r[0] << 8) | r[1]) >> 4

        return -(v & 0x800) + (v & 0x7FF)
