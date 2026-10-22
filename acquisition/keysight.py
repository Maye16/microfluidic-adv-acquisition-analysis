# -*- coding: utf-8 -*-
from time import sleep
import pyvisa
import numpy as np
import struct
import time
#############################################################################
class usb():

    def __init__(self,add,dev):
        self.inst = dev.open_resource(add)

    def write(self,text):
        self.inst.write(text)

    def reset(self):
        r""" Reset the device
        """
        self.inst.write('*RST')

    def output(self,text):
        r""" Enable or disable the output of the waveform function generator.

        When status is *on*, the generator output is enabled and a signal is sent,
        while when the status is *off* no signal is going out from the generator.
        To perform these actions,
        the command OUTP, followed by either ON or OFF,picoscope
        is sent to the generator.

        :param status: is either *on* or *off*'
        :type status: string

        :return: the status of the generator, that is ON or OFF
        :rtype: string

        """
        if text == 'on':
            self.inst.write('OUTP ON')
        elif text == 'off':
            self.inst.write('OUTP OFF')
        value = self.inst.query('OUTP?')
        return value


#############################################################################

#############################################################################
class Oscilloscope():

    def __init__(self, add, dev):
        self.inst = dev.open_resource(add)
        self.identifier = 'None'
        self.model = 'None'
        self.total_time_seconds = 0.001
        self._num_divisions = 10 # there is 10 division on the oscilloscope screen
        self.num_captures = 100
        self.num_samples = 1000
        ################################################################
        self.channel = 3   # which channel we use on the Oscilloscope
        ################################################################
        self.timebase = 4
        self.trigger_channel = 'EXT'

    def write(self,text):
        self.inst.write(text)

    def reset(self):
        r""" Reset the device
        """
        self.inst.write('*RST')

    def initialize(self):
        """Configure channels, trigger, and timebase."""
        # Set trigger
        # External source is used for the trigger, the threshold est mis à 0.020 V
        self.inst.write(':TRIG:EDGE:LEV 0.020')
        self.inst.write(f':TRIG:EDGE:SOUR {self.trigger_channel}')
        # The rising slope is used
        self.inst.write(':TRIG:EDGE:SlOP POS')
        # the coupling is DC
        self.inst.write(':TRIG:COUP: DC')

        # Set channel
        self.inst.write(':CHAN1:DISP OFF') #for our poor broken oscillo at ENS(Channel 1 HS)
        self.inst.write(':CHAN2:DISP OFF')  # for our poor broken oscillo at ENS(Channel 2 HS)
        self.inst.write(f':CHAN{self.channel}:DISP ON')
        ##################################################################
        self.inst.write(f'CHAN{self.channel}:SCAL 10 mV')
        ##################################################################


    def record(self, filename):
        """Enregistre les données de l'oscilloscope dans un fichier .npy."""
        try:
            inst = self.inst

            # Calculate timebase for desired sampling interval
            self.timebase = self.total_time_seconds / self._num_divisions    # 20 μs/div of x axe
            print(f':TIM:SCAL {self.timebase}')
            self.inst.write(f':TIM:SCAL {self.timebase}')


            # --- Optimisation VISA ---
            inst.chunk_size = 1024 * 1024   # 1 MB
            inst.timeout = 20000

            # --- Configuration waveform ---
            inst.write(f':WAV:SOUR CHAN{self.channel}')
            inst.write(':WAV:FORM WORD')
            inst.write(':WAV:BYT MSB')
            inst.write(':WAV:POIN:MODE RAW')

            inst.write('*CLS')
            inst.write(':WAV:RES')

            # --- Mode séquentiel ---
            inst.write(':ACQ:MODE SEQ')
            inst.write(f':ACQ:SEQ:SEGM {self.num_captures}')
            ###### added by DT
            if self.trigger_channel == 'EXT':
                inst.write(':TRIG:SOUR EXT')
                inst.write(':TRIG:EDGE:SOUR EXT')
                inst.write(':TRIG:EDGE:SLOP POS')
                inst.write(':TRIG:LEV EXT,1.0')
                ############################
                #让 trigger 尽量位于屏幕左侧; # Place the trigger at the left edge
                inst.write(':TIM:REF LEFT')
                inst.write(':TIM:POS 0')
                #################################
            else:
                inst.write(f':TRIG:SOUR CHAN{self.trigger_channel}')
                inst.write(f':TRIG:EDGE:SOUR CHAN{self.trigger_channel}')
                inst.write(f':TRIG:LEV CHAN{self.trigger_channel},0.0')


            inst.write(':ACQ:STATE ON')

            # 👉 attendre que TOUT soit acquis
            inst.query('*OPC?')
            inst.write(':ACQ:STATE OFF')

            # --- Paramètres (UNE SEULE FOIS) ---
            y_scale = float(inst.query(':WAV:YINC?'))
            y_offset = float(inst.query(':WAV:YOR?'))
            y_reference = float(inst.query(':WAV:YREF?'))
            print(f"y_scale: {y_scale}, y_offset: {y_offset}, y_reference: {y_reference}")
            x_scale = float(inst.query(':WAV:XINC?'))
            x_offset = float(inst.query(':WAV:XOR?'))

            num_points = int(inst.query(':WAV:POIN?'))

            # --- Pré-calcul du temps ---
            times = np.arange(num_points) * x_scale + x_offset

            # --- Pré-allocation mémoire ---
            signals_array = np.empty((self.num_captures, num_points, 2), dtype=np.float64)

            # --- Boucle acquisition ---
            for i in range(self.num_captures):

                inst.write(f':WAV:SEGM {i+1}')
                inst.query('*OPC?')

                # Lecture rapide binaire
                waveform_data = inst.query_binary_values(
                    ':WAV:DATA?',
                    datatype='H',
                    is_big_endian=True,
                    container=np.array
                )

                if waveform_data.size != num_points:
                    print(f"Warning segment {i}: taille inattendue")
                    continue

                # Conversion vectorisée (TRÈS important)
                voltages = (waveform_data - y_reference) * y_scale + y_offset

                # Stockage direct (pas de liste)
                signals_array[i, :, 0] = times
                signals_array[i, :, 1] = voltages

                if (i + 1) % 10 == 0:
                    print(f"{i+1}/{self.num_captures} segments lus")

            # --- Sauvegarde ---
            np.save(filename, signals_array)

            print("Acquisition terminée.")

        except Exception as e:
            print(f"Error recording data: {e}")
            raise


#############################################################################
