################################################################################
# 
# Polaris Demo at RS Tour De Branch (using Fortebit IoT Cloud)
#
################################################################################

from fortebit.polaris import polaris
from fortebit.iot import iot
from fortebit.iot import mqtt_client

import timestamp
import timers

import mcu
import vm
vm.set_option(vm.VM_OPT_RESET_ON_EXCEPTION, 1)
vm.set_option(vm.VM_OPT_TRACE_ON_EXCEPTION, 1)
vm.set_option(vm.VM_OPT_RESET_ON_HARDFAULT, 1)
vm.set_option(vm.VM_OPT_TRACE_ON_HARDFAULT, 1)

import streams

try:
    sleep(1000)
    print("Starting...")
    polaris.init()

    print("Initializing Air Sensor...")
    import airsensor
    airsensor.start()

    if not polaris.isBatteryBackup():
        polaris.setBatteryCharger(True)
        airsensor.set_lowpower(False)

    print("Initializing Accelerometer...")
    import accel
    accel.start()

    print("Initializing GNSS...")
    from quectel.l76 import l76
    l76.debug = True
    gnss = polaris.GNSS()
    gnss.set_rate(2000)

    print("Initializing MODEM...")
    from wireless import gsm
    modem = polaris.GSM()
    minfo = gsm.mobile_info()
    print(minfo)

    # change APN name as needed
    print("Establishing Link...")
    gsm.attach("mobile.vodafone.it")
    ninfo = gsm.network_info()
    print(ninfo)
    linfo = gsm.link_info()
    print(linfo)

    # Setup network protocols
    from mqtt import mqtt
    mqtt.debug = True
    import json
    import ssl

except Exception as e:
    print("oops, exception!", e)
    mcu.reset()

def decimal(n, v):
    v = float(v)
    s = "%%.%df" % n
    s = s % v
    if len(str(v)) < len(s):
        return s[:-1] + '0'
    return s

def my_log(logstr):
    print(logstr)


try:
    accel.get_sigma()  # discard first

    # attempt connection to Fortebit IoT cloud
    device_token = polaris.getAccessToken(minfo[0], mcu.uid())
    print("Access Token:", device_token)
    device = iot.Device(device_token,mqtt_client.MqttClient)
    
    for retry in range(15):
        try:
            device.connect()
            break
        except Exception as e:
            print("connecting...", e)
    else:
        print("Failed - reset!")
        mcu.reset()
    print("connected.")

    last_time = 0
    last_time_debug = 0
    while True:
        sleep(1000)
        now_time = timers.now()
        if now_time - last_time < 5000:
            continue
        last_time = now_time
        
        sigma = accel.get_sigma()
        if sigma < 0.1:
            low_power = True
        else:
            low_power = False

        if polaris.isBatteryBackup():
            airsensor.set_lowpower(low_power)

        ts = modem.rtc()
        print("modem RTC =", ts)
        telemetry = {}
        
        telemetry['battery'] = decimal(3,polaris.readBattVoltage())
        telemetry['temperature'] = decimal(2,accel.get_temperature())

        pr = accel.get_pitchroll()
        telemetry['pitch'] = decimal(1,pr[0])
        telemetry['roll'] = decimal(1,pr[1])
        telemetry['sigma'] = decimal(3,sigma)

        if not low_power:
            if gnss.has_fix():
                fix = gnss.fix()
                print("gnss FIX =", fix)
                # only transmit position when it's accurate
                if fix[6] < 2.5:
                    telemetry['latitude'] = decimal(6,fix[0])
                    telemetry['longitude'] = decimal(6,fix[1])
                    telemetry['altitude'] = decimal(1,fix[2])
                    telemetry['speed'] = decimal(1,fix[3])
                    telemetry['COG'] = decimal(1,fix[4])
                telemetry['nsat'] = fix[5]
                telemetry['HDOP'] = decimal(2,fix[6])
                telemetry['VDOP'] = decimal(2,fix[7])
                telemetry['PDOP'] = decimal(2,fix[8])
                # replace timestamp
                ts = fix[9]

        if airsensor.is_warmed_up():
            if airsensor.get_resistance(airsensor.GAS_NO2):
                telemetry['res_NO2'] = int(airsensor.get_resistance(airsensor.GAS_NO2))
                telemetry['res_NH3'] = int(airsensor.get_resistance(airsensor.GAS_NH3))
                telemetry['res_CO'] = int(airsensor.get_resistance(airsensor.GAS_CO))
            if airsensor.get_resistance(airsensor.GAS_VOC):
                telemetry['res_VOC'] = int(airsensor.get_resistance(airsensor.GAS_VOC))

        thp = airsensor.get_temp_hum_press()
        if thp is not None and len(thp) == 3 and (thp[0] != 0 or thp[1] != 0 or thp[2] != 0):
            telemetry['air_temperature'] = decimal(2,thp[0])
            telemetry['air_humidity'] = decimal(2,thp[1])
            telemetry['air_pressure'] = decimal(2,thp[2])

        telemetry['vehicleType'] = 'bike'
        
        telemetry['rssi'] = decimal(1,gsm.rssi())
        if now_time - last_time_debug >= 60000:
            last_time_debug = now_time
            ninfo = gsm.network_info()
            print(ninfo)
            telemetry['rat'] = ninfo[0]
            telemetry['mcc'] = ninfo[1]
            telemetry['mnc'] = ninfo[2]
            telemetry['lac'] = ninfo[4]
            telemetry['cid'] = ninfo[5]

        # add timestamp
        epoch_ms = str(timestamp.to_unix(ts)) + "000"
        x = '{"ts":' + epoch_ms + ', "values":' + json.dumps(telemetry) + '}'

        polaris.ledRedOff()
        msg = device.publish_telemetry(x)
        polaris.ledRedOn()
        print("Published telemetry:",msg)

        # debug GPS thread
        if not gnss.is_running():
            print("Restart GNSS thread")
            gnss.stop()
            gnss.start()

except Exception as e:
    print(e)
    mcu.reset()
