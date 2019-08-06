import threading
import math
import spi
from stm.lis2hh12 import lis2hh12

_lock = threading.Lock()
_accel = lis2hh12.LIS2HH12(SPI1, D60)

_ACCEL_LP_COEF = 0.25
_ACCEL_UPDATE = 10
_x = 0.0
_y = 0.0
_z = 0.0
_peak = 0.0

def _update():
    _lock.acquire()
    try:
        global _x,_y,_z,_peak
        a = _accel.acceleration()
        _x = _ACCEL_LP_COEF * a[0] + (1-_ACCEL_LP_COEF) * _x
        _y = _ACCEL_LP_COEF * a[1] + (1-_ACCEL_LP_COEF) * _y
        _z = _ACCEL_LP_COEF * a[2] + (1-_ACCEL_LP_COEF) * _z
        #print("inc: ",_x,_y,_z,a,len(accel))
        # update peak diff
        d_x = a[0] - _x
        d_y = a[1] - _y
        d_z = a[2] - _z
        d2 = d_x*d_x + d_y*d_y + d_z*d_z
        if d2 > _peak:
            _peak = d2
    finally:
        _lock.release()

def _run(arg):
    # discard initial samples (accel filters need time to stabilize)
    _lock.acquire()
    try:
        for n in range(15):
            sleep(10)
            _accel.acceleration()
        _peak = 0.0
    finally:
        _lock.release()
    # refresh
    while True:
        try:
            _update()
        except Exception as e:
            print("Accel task:",e)
        sleep(_ACCEL_UPDATE)

def get_pitchroll():
    _lock.acquire()
    tmp = math.sqrt(_y*_y + _z*_z);
    pitch = math.degrees(math.atan2(-_x, tmp))
    roll = math.degrees(math.atan2(_y, _z))
    _lock.release()
    return (pitch, roll)

def get_temperature():
    _lock.acquire()
    t = _accel.temperature()
    _lock.release()
    return t

def get_sigma():
    _lock.acquire()
    sigma = math.sqrt(_peak)
    _peak = 0.0
    _lock.release()
    return sigma
    
def start():
    thread(_run,"Accel Task")
