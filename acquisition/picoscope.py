import time
import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok
from picosdk.errors import PicoSDKCtypesError
from picosdk.constants import PICO_STATUS


###############################################################################
class Oscilloscope():
    """
    A wrapper class for controlling a PicoScope 5000A series oscilloscope.

    This class handles device connection, configuration, triggering, and
    data acquisition using the PicoSDK `ps5000a` driver.
    """
    _VOLTAGE_RANGE_MV = {
        ps.PS5000A_RANGE["PS5000A_10MV"]: 10,
        ps.PS5000A_RANGE["PS5000A_20MV"]: 20,
        ps.PS5000A_RANGE["PS5000A_50MV"]: 50,
        ps.PS5000A_RANGE["PS5000A_100MV"]: 100,
        ps.PS5000A_RANGE["PS5000A_200MV"]: 200,
        ps.PS5000A_RANGE["PS5000A_500MV"]: 500,
        ps.PS5000A_RANGE["PS5000A_1V"]: 1000,
        ps.PS5000A_RANGE["PS5000A_2V"]: 2000,
        ps.PS5000A_RANGE["PS5000A_5V"]: 5000,
        ps.PS5000A_RANGE["PS5000A_10V"]: 10000,
        ps.PS5000A_RANGE["PS5000A_20V"]: 20000,
        ps.PS5000A_RANGE["PS5000A_50V"]: 50000
    }

    _MAX_ADC = {
        ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]: 127,
        ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]: 2047,
        ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_14BIT"]: 8191,
        ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_15BIT"]: 16383,
        ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]: 32767
    }

    def __init__(self):
        """
        The serial number of our picoscope is :
        REDACTED for the 5443D MSO,
        REDACTED for the
        The available resolutions are 8, 10, 12, 14, 16 bits.
        There is 4 channels: A, B, C and D.
        The data are recorded in on of them, usually it is the channel A.
        The available values for the voltage range are
        10, 20, 30 50, 100, 200, 500 MV and 1, 2, 5, 10, 20, 50 V

        Initialize the oscilloscope configuration.

        :param voltageRange: Voltage range constant from ps5000a (e.g., ps.PS5000A_RANGE["PS5000A_5V"])
        :param threshold_mV: Trigger threshold in millivolts
        :param delay: Trigger delay in nanoseconds
        :param timeRange_ns: Desired time range in nanoseconds
        :param num_captures: Number of captures to record
        b'REDACTED' is for 5443D MSO (i.e. in my office)
        b'JREDACTED' is for 5443D (cavitation setup)
        """
        self.identifier = b'REDACTED'
        self.model = 'None'
        #self.identifier = b'JREDACTED'
        self.resolution = 0
        self.channel = 0
        self.voltageRange = 0
        self.coupling = 0
        self.direction = 0
        self.source = 0
        self.threshold_mV = 20
        self.threshold = self.mv_to_adc_counts()
        self.delay = 0 #96e3 nanoseconds. the delay should be determined for each set-up. 96 à 112 microseconds
        self.autoTrigger_ms = 10 # milliseconds
        timeRange_ns = 100
        self.timeRange_ns = max(timeRange_ns, 1) # timeRange_ns - self.delay # 112e3-self.delay
        self.timebase = 4
        self.desired_samples = 1000
        self.num_samples = self.desired_samples
        # Create a variable which values will be given later by the called function.
        self.chandle = ctypes.c_int16()
        self.num_captures = 100
        self.buffer = None
        self.status = {}


    def mv_to_adc_counts(self):
        """
        Convert a voltage in mV into ADC units for the current resolution and voltage range.

        :return: Threshold in ADC counts
        :rtype: int
        """
        max_adc =  self._MAX_ADC.get(self.resolution)
        value = int((self.threshold_mV/self._VOLTAGE_RANGE_MV[self.voltageRange])*max_adc)
        return value


    def check_status(self):
        """Open the oscilloscope device.
        """
        self.status["openunit"] = ps.ps5000aOpenUnit(
            ctypes.byref(self.chandle),
            ctypes.c_char_p(self.identifier),
            self.resolution
        )
        print(f"status unit {self.status['openunit']}")
        try:
            assert_pico_ok(self.status["openunit"])
        except:
            print('problem opening PicoScope')
            return False
        return True

    def initialize(self):
        """Configure channels, trigger, and timebase."""
        # Set channel
        self.resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]
        self.channel = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        self.voltageRange = ps.PS5000A_RANGE["PS5000A_100MV"]
        self.coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
        self.direction = ps.PS5000A_THRESHOLD_DIRECTION["PS5000A_RISING"]
        self.source = ps.PS5000A_CHANNEL["PS5000A_EXTERNAL"]

        if not hasattr(self, 'chandle') or self.chandle.value <= 0:
            if not self.check_status():
                raise RuntimeError("Device not opened correctly")

        print(f"Setting channel {self.channel} with voltage range {self.voltageRange}")


        self.status["setchannel"] = ps.ps5000aSetChannel(
            self.chandle,
            self.channel,
            1,
            self.coupling,
            self.voltageRange,
            0
        )
        print(f"Status after setting channel: {self.status['setchannel']}")
        try:
            assert_pico_ok(self.status["setchannel"])
        except:
            raise RuntimeError(f"Error setting channel: {self.status['setchannel']}")

        # Set trigger
        self.status["trigger"] = ps.ps5000aSetSimpleTrigger(
            self.chandle,
            1,
            self.source,
            self.threshold,
            self.direction,
            self.delay,
            self.autoTrigger_ms
        )
        try:
            assert_pico_ok(self.status["trigger"])
        except:
            raise RuntimeError(f"Error setting trigger: {self.status['trigger']}")

        # Calculate timbase for desired sampling interval
        time_interval_ns = ctypes.c_float()
        max_samples = ctypes.c_int32()


        # Trouver un timebase valide
        found_timebase = False
        for tb in range(1, 10000):
            self.status["timebase"] = ps.ps5000aGetTimebase2(
                self.chandle,
                tb,
                self.desired_samples,
                ctypes.byref(time_interval_ns),
                ctypes.byref(max_samples),
                0
            )
            try:
                assert_pico_ok(self.status["timebase"])
                found_timebase = True
                self.timebase = tb
                print(f"Timebase {tb} valid: {time_interval_ns.value} ns/sample, max samples: {max_samples.value}")
                break
            except PicoSDKCtypesError as e:
                if 'PICO_INVALID_TIMEBASE' in str(e):
                    continue
                else:
                    print(f"Error: {e}")
                    raise RuntimeError(f"Unexpected error: {e}")
        if not found_timebase:
            raise RuntimeError("Could not find a valid timebase. Try reducing desired_samples or increasing timebase range.")


        self.num_samples = min(self.desired_samples, max_samples.value)
        print(f"PicoScope initialized with timebase {self.timebase}, {self.num_samples} samples, {time_interval_ns.value:.2f} ns/sample")

        # Allocate buffer
        self.buffer = (ctypes.c_int16 * self.num_samples)()
        self.status["buffer"] = ps.ps5000aSetDataBuffers(
            self.chandle,
            self.channel,
            self.buffer,
            None, self.num_samples,
            0,
            0
        )
        try:
            assert_pico_ok(self.status["buffer"])
        except:
            raise RuntimeError(f"Error setting data buffer: {self.status['buffer']}")


    def record(self,filename):
        """Run block captures and save data to file."""
        captured_data = []
        for i in range(self.num_captures):
            ps.ps5000aStop(self.chandle) # Stop any previous capture
            print(f"Starting capture with num_samples={self.num_samples}, timebase={self.timebase}")

            self.status["block"] = ps.ps5000aRunBlock(
                self.chandle,
                0,
                self.num_samples,
                self.timebase,
                None,
                0,
                None,
                None
            )
            try:
                assert_pico_ok(self.status["block"])
            except:
                raise RuntimeError(f"Error running block: {self.status['status']}")

            # Wait for ready
            ready = ctypes.c_int16(0)
            while ready.value == 0:
                ps.ps5000aIsReady(
                    self.chandle,
                    ctypes.byref(ready)
                )
            # Retrieve data
            overflow = ctypes.c_int16()
            nSamples = ctypes.c_uint32(self.num_samples)
            self.status["getvalues"] = ps.ps5000aGetValues(
                self.chandle,
                0,
                ctypes.byref(nSamples),
                1,
                0,
                0,
                ctypes.byref(overflow)
            )
            try:
                assert_pico_ok(self.status["getvalues"])
            except:
                raise RuntimeError(f"Error getting values: {self.status['getvalues']}")

            data = np.ctypeslib.as_array(self.buffer)[:nSamples.value]
            captured_data.append(data.copy())
            print(f"Capture {i+1}/{self.num_captures} complete")

        # Save all captured data to a file
        np.save(filename+'.npy', np.array(captured_data))

    def close(self):
        """Close the oscilloscope device."""
        ps.ps5000aCloseUnit(self.chandle)
        self.chandle = None

    def __enter__(self):
        """ to be used as
        with Oscilloscope() as scope:
            scope.initialize()  # must reinitialize because handle isn’t persisted
            scope.record()
        """
        self.check_status()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False  # Don't suppress exceptions
###############################################################################
