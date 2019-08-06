from texas.ads1015 import ads1015
import struct

_CHANNEL_NO2 = 4
_CHANNEL_NH3 = 5
_CHANNEL_CO = 6

_PULLUP_NO2 = 15.0e3
_PULLUP_NH3 = 1.1e6
_PULLUP_CO = 1.1e6

def _saturate(v,min,max):
    if v > max:
        v = max
    if v < min:
        v = min
    return v

class AirQuality5:

    def __init__(self, i2cdrv, address=0x48, clk=100000):
        self.ads = ads1015.ADS1015(i2cdrv, address, clk)
        self.ads.set(os=0, pga=1, mode=1, sps=4)  # standby

    def _read_adc(self):
        r = self.ads.read_register(ads1015.REG_CONV, 2)
        v = struct.unpack(">h",r)[0] >> 4
        return v

    def _read_ch(self, channel):
        # calc average over 64 samples
        self.ads.set(ch=channel, os=0, pga=1, mode=0, sps=4)
        sum = 0.0
        for i in range(0, 64):
            sleep(1)
            sum += self._read_adc()
        self.ads.set(os=0, pga=1, mode=1, sps=4)  # standby
        # adc raw value are 12-bit signed (-2048,+2047), 1 LSB = VDD / 2048
        # pga gain is 0.5, output value is milliVolts
        return sum * (2.0 / 64.0) # max positive value

    def measure(self):
        v = self._read_ch(_CHANNEL_NH3)
        #print(v)
        v = _saturate(v,0,3300)
        r0 = _PULLUP_NH3 * v / (3301 - v)
        v = self._read_ch(_CHANNEL_CO)
        #print(v)
        v = _saturate(v,0,3300)
        r1 = _PULLUP_CO * v / (3301 - v)
        v = self._read_ch(_CHANNEL_NO2)
        #print(v)
        v = _saturate(v,0,3300)
        r2 = _PULLUP_NO2 * v / (3301 - v)
        return (r0, r1, r2)
