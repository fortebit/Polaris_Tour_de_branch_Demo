import threading
import timers
import math
from fortebit.polaris import polaris
import i2c
from bosch.bme680 import bme680
from mikroe import airquality5

GAS_CO = 1
GAS_NO2 = 2
GAS_NH3 = 3
GAS_C3H8 = 4
GAS_C4H10 = 5
GAS_CH4 = 6
GAS_H2 = 7
GAS_C2H5OH = 8
GAS_VOC = 9

_AIR_UPDATE = 800

# RES0 values derived from https://github.com/Seeed-Studio/Mutichannel_Gas_Sensor
# (they use a 56k pull-up on 10-bit ADC channels)
_RES0_NO2 = 56.0e3/(1024-155)*155
_RES0_NH3 = 56.0e3/(1024-860)*860
_RES0_CO = 56.0e3/(1024-950)*950

_lock = threading.Lock()
_air5 = None
_bme680 = None
try:
    _air5 = airquality5.AirQuality5(I2C0)
except Exception as e:
    _air5 = None
    print("Air Quality 5 click not found",e)
try:
    _bme680 = bme680.BME680(I2C0, refresh_rate=1, debug=False)
except Exception as e:
    _bme680 = None
    print("Environment click not found",e)

_ratio0 = 0
_ratio1 = 0
_ratio2 = 0
_voc = 0
_temp = 0
_hum = 0
_press = 0
_since = 0
_lowpower = True

#print("RES0=",(_RES0_NO2,_RES0_NH3,_RES0_CO))

def _update():
    global _ratio0, _ratio1, _ratio2, _voc, _temp, _hum, _press
    if _air5 is not None:
        v = _air5.measure()
        #print("v=",v)
        _ratio0 = v[0] / _RES0_NH3
        _ratio1 = v[1] / _RES0_CO
        _ratio2 = v[2] / _RES0_NO2
    if _bme680 is not None:
        _voc = _bme680.gas()
        _temp = _bme680.temperature()
        _hum = _bme680.humidity()
        _press = _bme680.pressure()

def get_temp_hum_press():
    c = None
    if _bme680 is not None:
        _lock.acquire()
        c = (_temp, _hum, _press)
        _lock.release()
    return c

def get_resistance(gas):
    _lock.acquire()
    if gas == GAS_CO:
        c = _ratio1 * _RES0_CO
    elif gas == GAS_NO2:
        c = _ratio2 * _RES0_NO2
    elif gas == GAS_NH3:
        c = _ratio0 * _RES0_NH3
    elif gas == GAS_VOC:
        c = _voc
    else:
        c = None
    _lock.release()
    return c

def get_ppm(gas):
    # derived from https://github.com/Seeed-Studio/Mutichannel_Gas_Sensor
    _lock.acquire()
    if gas == GAS_CO:
        c = math.pow(_ratio1, -1.179) * 4.385
    elif gas == GAS_NO2:
        c = math.pow(_ratio2, 1.007) / 6.855
    elif gas == GAS_NH3:
        c = math.pow(_ratio0, -1.67) / 1.4
    elif gas == GAS_C3H8:
        c = math.pow(_ratio0, -2.518) * 570.164
    elif gas == GAS_C4H10:
        c = math.pow(_ratio0, -2.138) * 398.107
    elif gas == GAS_CH4:
        c = math.pow(_ratio1, -4.363) * 630.957
    elif gas == GAS_H2:
        c = math.pow(_ratio1, -1.8) * 0.73
    elif gas == GAS_C2H5OH:
        c = math.pow(_ratio1, -1.552) * 1.622
    else:
        c = None
    _lock.release()
    return c

def start():
    thread(_run,"AirQuality Task")
    _since = timers.now()

def set_lowpower(mode):
    global _lowpower
    _lock.acquire()
    if _air5 is not None:
        if mode:
            _lowpower = True
        else:
            _lowpower = False
    else:
        _lowpower = False
    # power control heaters (5V)
    if _lowpower:
        polaris.disable5V()
    else:
        polaris.enable5V()
    _lock.release()


def is_warmed_up():
    _lock.acquire()
    if timers.now() - _since > 60000 and not _lowpower:
        ret = True
    else:
        ret = False
    _lock.release()
    return ret

def _run(arg):
    # refresh
    while True:
        _lock.acquire()
        try:
            if not _lowpower:
                _update()
            else:
                _since = timers.now()
        except Exception as e:
            print("Air Exc:", e)
        finally:
            _lock.release()
        sleep(_AIR_UPDATE)

