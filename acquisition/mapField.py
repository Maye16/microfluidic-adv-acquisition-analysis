import time
import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps

import newport
import instruments


#install PicoSDK with driver
#instal picosdk-python-wrappers: pip install picosdk

##############################################################################
def mapTest(step):
    """
    """
    (gen,watt,motion) = instruments.initialize()

    t0 = float(time.time())

    motion.send('1SH0')
    motion.send('2SH0')
    motion.send('3SH0')

    motion.send('1OR0')
    motion.waitPosition(1)
    motion.send('2OR0')
    motion.waitPosition(2)
    motion.send('3OR0')
    motion.waitPosition(3)
    time.sleep(5)


    print(motion.query('1TP'))
    print(motion.query('2TP'))
    print(motion.query('3TP'))

    for pos1 in np.arange(-9,9,step):
        motion.moveAbsolute(1,pos1)
        motion.waitPosition(1)
        for pos2 in np.arange(-9,9,step):
            motion.moveAbsolute(2,pos2)
            motion.waitPosition(2)
            for pos3 in np.arange(-9,9,step):
                motion.moveAbsolute(3,pos3)
                motion.waitPosition(3)
                print(motion.readPosition(1),motion.readPosition(2),motion.readPosition(3))
                print(pos1,pos2,pos3)
                time.sleep(1)
    t1 = float(time.time())
    t = t1 - t0
    print(round(t/60,1)+' min')
    motion.close()
    gen.close()
    watt.close()
    return 1
##############################################################################

##############################################################################
def timebase_and_buffer_size(f, t, oversampling = 10):
    """ Calculate sampling rate and time interval.

    For a sinusoidal signal with frequency :math:`f` and oversampling :math:`K`,
    the sampling rate is :math:`F_{s} = K f`.

    The TIMEBASE parameter determines the sampling interval that is
    :math:`T_{s} = \frac{2^{TIMEBASE}}{125 \times 10^{6}}` s.

    We need to find the smallest TIMEBASE value that satisfies :math:`T_{s} < \frac{1}{F_{s}}`.
    The buffer size is simply :math:`BUFFER_SIZE = T F_{s}`


    :param status: frequency f
    :type status: float

    :param status: duration t
    :type status: float

    :param status: oversampling
    :type status: float

    :return: timebase
    :rtype: float

    :return: buffer_size
    :rtype: float

    :return: sampling_rate
    :rtype: float
    """
    sampling_rate = oversampling*f
    time_interval = 1/sampling_rate

    # Find the smallest valid TIMEBASE
    timebase = 1
    while (2**timebase)/(125e6) > time_interval:
        timebase += 1

    # Calculate buffer size
    buffer_size = int(t*sampling_rate)

    return timebase, buffer_size, sampling_rate
##############################################################################

##############################################################################
def mapPressure(mapFilename, frequency, duration, oversampling, step,  voltage):
    """
    Measure a 3 dimensionnal pressure map using an utrasound wave created from
    an electrical signal having a frequency "frequency", an electrical amplitude "voltage"
    during a time "duration".
    The data are saved in the file "mapFilname.csv"

    """
    gen = 'None'
    watt = 'None'
    motion = 'None'
    (gen,watt,motion) = instruments.initialize()

    filetoSave = open(mapFilename+'.csv','w+')

    timebase, buffer_size, sampling_rate = timebase_and_buffer_size(
        frequency,
        duration,
        oversampling
    )

    # Define constants
    TIMEBASE = timebase
    NUM_SAMPLES = 1000  # Number of samples to capture
    CHANNEL = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
    RESOLUTION = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]  # 12-bit resolution
    VOLTAGE_RANGE = ps.PS5000A_RANGE["PS5000A_500MV"]  # ±5V range
    COUPLING = ps.PS5000A_COUPLING["PS5000A_DC"]

    # Open the device
    chandle = ctypes.c_int16()
    status = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, RESOLUTION)
    # replace None by the number of the oscilloscope,
    # otherwise the first oscilloscope is opened.
    print(status,chandle)
    if status != 0:
        print(f"Unable to open device. Status code: {status}")
        exit()

    status = ps.ps5000aSetChannel(
        chandle,
        CHANNEL,
        1,
        COUPLING,
        VOLTAGE_RANGE,
        0
    )
    print(status)
    if status != 0:
        print(f"Error setting channel: {status}")
        exit()

    # Configure the trigger on Channel D
    TRIGGER_CHANNEL = ps.PS5000A_CHANNEL["PS5000A_EXTERNAL"]
    TRIGGER_THRESHOLD_MV = 20  # Trigger level in millivolts
    TRIGGER_THRESHOLD_ADC = int((TRIGGER_THRESHOLD_MV/voltage)*32767)  # Convert to ADC counts
    TRIGGER_DELAY = 0  # No delay
    TRIGGER_DIRECTION = ps.PS5000A_THRESHOLD_DIRECTION["PS5000A_RISING"]

    status = ps.ps5000aSetSimpleTrigger(
        chandle,
        1,  # Enable the trigger
        TRIGGER_CHANNEL,
        TRIGGER_THRESHOLD_ADC,  # Trigger threshold in ADC counts
        TRIGGER_DIRECTION,
        TRIGGER_DELAY,
        10000  # Auto trigger timeout in milliseconds
    )
    if status != 0:
        print(f"Error setting trigger: {status}")
        return

    t0 = time.time()

    motion.send('1SH0')
    motion.send('2SH0')
    motion.send('3SH0')

    motion.send('1OR0')
    motion.waitPosition(1)
    motion.send('2OR0')
    motion.waitPosition(2)
    motion.send('3OR0')
    motion.waitPosition(3)
    pos1 = motion.query('1TP')
    pos2 = motion.query('2TP')
    pos3 = motion.query('3TP')
    time.sleep(5)
    i = 0
    print(pos1, pos2, pos2)
    for pos1 in np.arange(-9,9,step):
        motion.moveAbsolute(1,pos1)
        motion.waitPosition(1)
        for pos2 in np.arange(-9,9,step):
            motion.moveAbsolute(2,pos2)
            motion.waitPosition(2)
            for pos3 in np.arange(-9,9,0.001):
                motion.moveAbsolute(3,step)
                motion.waitPosition(3)
                print(motion.query('1TP'), motion.query('2TP'), motion.query('3TP'))

                # Set up data buffer
                buffer = (ctypes.c_int16 * buffer_size)()
                status = ps.ps5000aSetDataBuffer(
                    chandle,
                    CHANNEL,
                    ctypes.byref(buffer),
                    buffer_size,
                    0,
                    0
                )
                if status != 0:
                    print(f"Error setting data buffer: {status}")
                    return

                data_list = []
                for dump in range(int(duration*sampling_rate/buffer_size)):
                    ready = ctypes.c_int16(0)
                    j = 0
                    while ready.value == 0:
                        ps.ps5000aIsReady(chandle, ctypes.byref(ready))
                        print(j)
                        j += 1
                    overflow = ctypes.c_int16(0)
                    retrieved = ctypes.c_uint32()
                    status = ps.ps5000aGetValues(
                        chandle,
                        0,
                        ctypes.byref(retrieved),
                        1,
                        0,
                        0,
                        ctypes.byref(overflow)
                    )
                    if status != 0:
                        print(f"Error getting values: {status}")
                        exit()
                    else:
                        data = np.ctypeslib.as_array(buffer)[:retrieved.value]
                        time = np.linspace(0, len(data) / sampling_rate, len(data))
                        data_list.extend(zip(time, data))

                # Save to CSV
                output_file = 'map' + i + '.csv'
                with open(output_file, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([motion.query('1TP'), motion.query('2TP'), motion.query('3TP')])
                    writer.writerow(["Time (s)", "Amplitude (mV)"])
                    writer.writerows(data_list)

    t1 = time.time()
    t = t1 - t0
    print(round(t/60,1)+' min')
    filetoSave.close()
    ps.ps5000aCloseUnit(chandle)
    motion.close()
    gen.close()
    watt.close()
    return 1
###############################################################################

# The original prototype automatically started an instrument-connected 3-D scan
# at import time. This automatic invocation was intentionally removed.
# This prototype has known runtime errors and must not be used to drive hardware
# until it is independently reviewed and validated.
if __name__ == "__main__":
    raise SystemExit(
        "mapField.py is an unvalidated hardware-mapping prototype; "
        "automatic acquisition is intentionally disabled."
    )
