#!/usr/bin/env python
import sys
import math
import glob
import os
import os.path
import csv
import time
import ctypes
import PyQt6
import picoscope
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QPixmap

import numpy
import scipy.optimize, scipy.constants
import serial
from time import sleep
import datetime
import json
#from picosdk.ps5000a import ps5000a as ps

from main_window import Ui_MainWindow
import sample_information
import motion
import instruments
import measurement
import inout
import agilent
import rohde_schwarz
import newport
import transducer
import keysight
# import picoscope
import available_devices

###############################################################################
class Devices:
    def __init__(self):
        self.gen = {'enabled':False, 'identifier':None, 'model':None, 'inst':None}
        self.amp = {'enabled':False, 'identifier':None, 'model':None, 'inst':None}
        self.watt = {'enabled':False, 'identifier':None, 'model':None, 'inst':None}
        self.osc = {'enabled':False, 'identifier':None, 'model':None, 'inst':None, 'Schan':None, 'Tchan':None}
        self.motion = {'enabled':False, 'identifier':None, 'model':None, 'inst':None}
###############################################################################

###############################################################################
class OscWorker(QtCore.QObject):
    """A worker class to handle data acquisition via an oscilloscope.

    This class inherits from QObject to enable the use of Qt signals.
    It encapsulates the logic for acquiring and recording data from an oscilloscope,
    with error handling via signals.

    Attributes:
        completed (pyqtSignal): Signal emitted when the acquisition completes successfully.
        error (pyqtSignal): Signal emitted in case of an error, with an error message as an argument.
        osc (object): Instance of the oscilloscope used for acquisition.
        filename (str): Path to the file where the acquired data will be saved.
    """
    completed = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, osc,sample):
        """Initializes the worker with the oscilloscope and output file.

        Args:
            osc (object): Configured oscilloscope instance for acquisition.
            sample (object): Object containing acquisition metadata, including the output filename.
        """
        super().__init__()
        self.osc = osc
        self.filename = sample.filename
        self._is_running = True

    def run(self):
        """Starts the acquisition and recording of data.

        Emits a success or error signal based on the operation's outcome.
        Prints a message indicating the start of acquisition with current parameters.

        Raises:
            RuntimeError: If an error occurs during acquisition or recording.
        """
        print(f"Starting capture with num_samples={self.osc.num_samples}, timebase={self.osc.timebase}")
        try:
            self.osc.record(self.filename)
            self.completed.emit()
        except RuntimeError as e:
            self.error.emit(str(e))  # Emit the error message

    def stop(self):
        """Arrête la boucle d'acquisition."""
        # Si votre OscWorker a une boucle, ajoutez un flag similaire
        self._is_running = False

###############################################################################


###############################################################################
class powerMeasurement(QtCore.QObject):
    """A worker class for measuring and recording power and pressure during ultrasound experiments.

    This class inherits from QObject to enable the use of Qt signals for real-time updates,
    error handling, and process control. It manages the acquisition of power data, pressure calculations,
    and configuration saving.

    Attributes:
        signal (pyqtSignal): Signal emitted to update the current progress (float).
        completed (pyqtSignal): Signal emitted when the measurement is complete, with the final pressure value (float).
        display_pressure (pyqtSignal): Signal emitted to display the current pressure (float).
        display_power (pyqtSignal): Signal emitted to display the current power (float).
        start (pyqtSignal): Signal emitted to indicate the start of the measurement process.
        showWarning (pyqtSignal): Signal emitted to display a warning message (str).
        error (pyqtSignal): Signal emitted in case of an error, with an error message (str).
        watt (object): Power meter device instance.
        gen (object): Signal generator device instance.
        transducer (object): Transducer device instance.
        ultrasound (object): Ultrasound configuration and control object.
        sample (object): Sample metadata and configuration object.
        data (object): Data storage and processing object.
        _isRunning (bool): Flag to control the measurement loop.
    """
    
    signal = QtCore.pyqtSignal(float)
    completed = QtCore.pyqtSignal(float)
    display_pressure = QtCore.pyqtSignal(float)
    display_power = QtCore.pyqtSignal(float)
    start = QtCore.pyqtSignal()
    showWarning = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, watt, gen, transducer, ultrasound, sample, data):
        """Initializes the power measurement worker with devices and configuration.

        Args:
            watt (object): Power meter device instance.
            gen (object): Signal generator device instance.
            transducer (object): Transducer device instance.
            ultrasound (object): Ultrasound configuration and control object.
            sample (object): Sample metadata and configuration object.
            data (object): Data storage and processing object.
        """
        super().__init__()
        self.watt = watt
        self.gen = gen
        self.transducer = transducer
        self.ultrasound = ultrasound
        self.sample = sample
        self.data = data
        self._isRunning = True
        
    def stop(self):
        """Stops the measurement loop by setting the running flag to False."""
        self._isRunning = False
        
    def run(self):
        """Executes the power and pressure measurement loop.

        This method runs the main measurement loop, emitting signals for real-time updates,
        and saving the acquired data. It checks for valid duration, saves the configuration,
        and continuously measures power and pressure until the duration is reached or stopped manually.

        Emits:
            signal: Current progress in seconds.
            display_power: Current power value (forward - reverse).
            display_pressure: Current pressure value.
            completed: Final pressure value when the measurement is complete.
            showWarning: Warning if the insonification duration is too short.
            error: Error message if an exception occurs during the loop.

        Raises:
            Exception: If an error occurs during the measurement loop.
        """
        sleep = 0.001 # in second
        period = 1 / self.ultrasound.PRF
        AVER, REV, elapsedTime = [], [], []

        time.sleep(0.1)
        i = 0
        while self._isRunning:
            Power_avg = float(self.watt.query(':SENSe0:DATA? "POW:FORW:AVER"'))
            AVER.append(Power_avg)
            Power_rev = float(self.watt.query(':SENSe0:DATA? "POW:REV"'))
            REV.append(Power_rev)
            tmp_power =  (Power_avg - Power_rev) #round((Power_avg - Power_rev),6)
            self.display_power.emit(tmp_power)
            self.data.AVER = numpy.array(AVER)
            self.data.REV = numpy.array(REV)
            tmp_pressure = self.data.Psapa(
                self.sample.temperature,
                self.ultrasound.DC,
                self.transducer.efficiency(self.ultrasound.frequency),
                self.transducer.section()
            )
            self.display_pressure.emit(tmp_pressure)

        self.data.AVER = numpy.array(AVER)
        self.data.REV = numpy.array(REV)
        self.data.elapsedTime = numpy.array(elapsedTime)
        self.completed.emit(
            self.data.Psapa(
                self.sample.temperature,
                self.ultrasound.DC,
                self.transducer.efficiency(self.ultrasound.frequency),
                self.transducer.section()
            )
        )
###############################################################################

###############################################################################
class TimeCounter(QtCore.QObject):
    """A simple timer worker that emits time updates at 1-second intervals.

    This class inherits from QObject to enable the use of Qt signals for real-time
    time updates and completion notification. It is designed to run a countdown
    or count-up timer for a specified duration, emitting signals at each second.

    Attributes:
        update_time (pyqtSignal): Signal emitted every second with the elapsed time (int).
        completed (pyqtSignal): Signal emitted when the timer completes its duration.
        duration (int): The total duration of the timer in seconds.
        _is_running (bool): Flag to control the timer loop.
    """
    update_time = QtCore.pyqtSignal(int)
    completed = QtCore.pyqtSignal()

    def __init__(self, duration):
        """Initializes the timer with the specified duration.

        Args:
            duration (int): The total duration of the timer in seconds.
        """
        super().__init__()
        self.duration = duration
        self._is_running = True

    def run(self):
        """Starts the timer loop.

        Emits the `update_time` signal every second with the elapsed time.
        Stops when the duration is reached or if `stop()` is called.
        Emits the `completed` signal when the timer finishes.
        """
        elapsed_time = 0
        while self._is_running and elapsed_time < self.duration:
            QtCore.QThread.msleep(1000)
            elapsed_time += 1
            self.update_time.emit(elapsed_time)
        self.completed.emit()

    def stop(self):
        """Stops the timer loop by setting the running flag to False."""
        self._is_running = False
###############################################################################


###############################################################################
class MainWindow(QtWidgets.QMainWindow,Ui_MainWindow):
    """Main application window for managing ultrasound experiments and sample data.

    This class inherits from QMainWindow and Ui_MainWindow, providing a graphical interface
    for configuring, running, and monitoring ultrasound experiments. It manages device connections,
    parameter settings, data acquisition, and user interactions.

    The acoustic parameters are stored in the `ultrasound` class, while sample information
    is stored in the `sample` class.

    Attributes:
        directory (str): Current working directory for file operations.
        devices (Devices): Object containing information about connected devices.
        ultrasound (measurement.ultrasound): Object storing ultrasound parameters and methods.
        sample (measurement.sample): Object storing sample information and methods.
        data (measurement.data): Object for data storage and processing.
        icon_gen_grey (QPixmap): Grey icon for the generator device.
        icon_gen_color (QPixmap): Color icon for the generator device.
        icon_watt_grey (QPixmap): Grey icon for the wattmeter device.
        icon_watt_color (QPixmap): Color icon for the wattmeter device.
        icon_motion_grey (QPixmap): Grey icon for the motion controller device.
        icon_motion_color (QPixmap): Color icon for the motion controller device.
        icon_pico_grey (QPixmap): Grey icon for the oscilloscope device.
        icon_pico_color (QPixmap): Color icon for the oscilloscope device.
        AVER (float): Average power value.
        REV (float): Reverse power value.
        iteration (int): Current iteration count.
        transducer (transducer): Transducer object for the experiment.
        osc (picoscope.Oscilloscope): Oscilloscope device instance.
        watt (object): Wattmeter device instance.
        motion (object): Motion controller device instance.
        gen (object): Generator device instance.
        amp (object): Amplifier device instance.
    """
    def __init__(self):
        """Initializes the main window, devices, and default parameters."""
        super().__init__()
        self.job2 = None
        self.thread2 = None
        self.trigger_channel = None
        self.setupUi(self)

        self.directory = os.getcwd()

        # Define the plugin informations of the various devices
        self.devices = Devices()
        if available_devices.get_values(self.devices) == False:
            results = self.get_devices()

        # read the configuration of the
        self.ultrasound = measurement.ultrasound() # class ultrasound
        self.sample = measurement.sample()         # class sample
        self.readConfiguration()
        self.data =  measurement.data()            # class data

        # Set the icons of the various device
        self.icon_gen_grey = QPixmap("icons/Generator_Agilent_grey.png")
        self.icon_gen_color = QPixmap("icons/Generator_Agilent.png")
        self.label_gen.setPixmap(self.icon_gen_grey)
        self.label_gen.setScaledContents(True)

        self.icon_watt_grey = QPixmap("icons/Wattmeter_RohdeSchwarz_grey.png")
        self.icon_watt_color = QPixmap("icons/Wattmeter_RohdeSchwarz.png")
        self.label_watt.setPixmap(self.icon_watt_grey)
        self.label_watt.setScaledContents(True)

        self.icon_motion_grey = QPixmap("icons/Motion_Controller_grey.png")
        self.icon_motion_color = QPixmap("icons/Motion_Controller.png")
        self.label_motion.setPixmap(self.icon_motion_grey)
        self.label_motion.setScaledContents(True)

        self.icon_pico_grey = QPixmap("icons/Picoscope_grey.png")
        self.icon_pico_color = QPixmap("icons/Picoscope.png")
        self.label_pico.setPixmap(self.icon_watt_grey)
        self.label_pico.setScaledContents(True)


        # Set up various parameters to default values
        self.AVER = 0
        self.REV = 0
        self.iteration = 0
        self.ultrasound.fmth = 'FM'
        self.radioButton_fondamental.setChecked(0)
        self.comboBox_transducer.setCurrentIndex(0)
        self.transducer = transducer.H101SN140(self.ultrasound.fmth)

        self.osc = None
        self.watt = None
        self.motion = None
        self.gen = None
        self.amp = None

        # Initialize the various instruments

        if self.devices.osc['enabled'] == True:
            if self.devices.osc['model'] == "USB picoscope 5000a series":
                from picosdk.ps5000a import ps5000a as ps
                self.osc = picoscope.Oscilloscope()
                self.osc.model = self.devices.osc['model']
                self.gen, self.watt, self.motion, _ = instruments.initialize(self.devices)
            elif self.devices.osc['model'] == "USB keysight":
                self.gen, self.watt, self.motion, self.osc = instruments.initialize(self.devices)
            else:
                self.gen, self.watt, self.motion, _ = instruments.initialize(self.devices)
            self.lineEdit_pulse_number.setEnabled(True)
            self.radioButton_pulse_number.setEnabled(True)
        else:
            self.lineEdit_pulse_number.setEnabled(False)
            self.radioButton_pulse_number.setEnabled(False)
            self.radioButton_pulse_number.setChecked(False)
            self.radioButton_duration.setChecked(True)
        self.set_status()
 
        # Connect buttons and slots
        self.pushButton_scan.clicked.connect(self.rescan)
        self.pushButton_Start.clicked.connect(self.Start)
        self.pushButton_Stop.clicked.connect(self.Stop)
        self.toolButton_motion.clicked.connect(self.motor_positionning)
        self.spinBox_n_cycle.valueChanged.connect(self.updateValues)
        self.lineEdit_frequency.textChanged.connect(self.updateValues)
        self.lineEdit_PRF.textChanged.connect(self.updateValues)
        self.comboBox_function_function.currentTextChanged.connect(self.updateValues)
        self.lineEdit_duration.textChanged.connect(self.updateValues) 
        self.lineEdit_amplitude.textChanged.connect(self.updateValues)
        self.lineEdit_pulse_number.textChanged.connect(self.updateValues)
        self.radioButton_pulse_number.clicked.connect(self.updateValues)
        self.radioButton_duration.clicked.connect(self.updateValues)
        self.pushButton_parameters.clicked.connect(self.get_devices)


    def get_devices(self):
        """Opens a dialog to select and configure available devices.

        Shows a modal dialog for device selection. If the dialog is rejected,
        the application exits.
        """
        # Create and show second window modally
        dlg = available_devices.availableDevices(self.devices, parent = self)
        if dlg.exec():  # exec() shows the dialog modally, blocks here until closed
            # dialog accepted: process inputs if any
            pass
        else:
            QtWidgets.QApplication.quit()
            sys.exit()

    def motor_positionning(self):
        """Opens a dialog for motor positioning.

        Shows a modal dialog for motor positioning. If the dialog is rejected,
        no action is taken.
        """
        # Create and show second window modally
        dlg = motion.Motion(parent = self)
        if dlg.exec():  # exec() shows the dialog modally, blocks here until closed
            # dialog accepted: process inputs if any
            pass
        else:
            # dialog rejected or closed
            pass

    def open_info_window(self):
        """Opens a dialog for sample information.

        Shows a modal dialog for sample information. If the dialog is rejected,
        no action is taken.
        """
        # Create and show second window modally
        dlg = sample_information.SampleInformationDialog(sample, parent=self)
        if dlg.exec():  # exec() shows the dialog modally, blocks here until closed
            # dialog accepted: process inputs if any
            pass
        else:
            # dialog rejected or closed
            pass

    def Choose_filename(self):
        """Prompts the user to choose a filename for saving data.

        If the chosen filename already exists, the user is prompted to choose another name.
        Returns the chosen filename or None if cancelled.

        Returns:
            str: The chosen filename base (without extension) or None if cancelled.
        """
        while True:
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Select filename', '', "Tous les fichiers (*)"
            )

            # Case: user pressed cancel
            if not filename:
                reply = QtWidgets.QMessageBox.question(
                    self, 'Warning',
                    "You have to choose a name !",
                    QtWidgets.QMessageBox.StandardButton.Yes |
                    QtWidgets.QMessageBox.StandardButton.Cancel,
                    QtWidgets.QMessageBox.StandardButton.Cancel
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                    return None
                else:
                    continue  # ask again

            # generate base path (without extension)
            base = os.path.splitext(filename)[0]

            # check for existing files
            if os.path.exists(base + '.csv') or os.path.exists(base + '.npy'):
                reply = QtWidgets.QMessageBox.question(
                    self, 'Warning',
                    "The name already exists. Do you want to choose another one ?",
                    QtWidgets.QMessageBox.StandardButton.Yes |
                    QtWidgets.QMessageBox.StandardButton.Cancel,
                    QtWidgets.QMessageBox.StandardButton.Yes
                )
                if reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                    return None
                else:
                    continue  # ask again
            # valid filename
            print(os.path.splitext(filename)[0])
            return os.path.splitext(filename)[0]

    def Stop(self):
        """Stops all running jobs and updates the UI buttons."""
        print("Stopping all threads and turning off the generator...")

        # Arrêter et déconnecter le timer
        try:
            if hasattr(self, 'timer') and self.timer is not None:
                self.timer.stop()
                try:
                    self.timer.timeout.disconnect(self.on_timer_completed)
                except Exception as e:
                    print(f"Error disconnecting on_timer_completed: {e}")
        except Exception as e:
            print(f"Error stopping timer: {e}")

        # Turn off the generator
        try:
            if hasattr(self, 'gen') and self.gen is not None:
                self.gen.output('off')
                print("Generator turned off.")
        except Exception as e:
            print(f"Error turning off generator: {e}")

        # Stop the power measurement job if it's running
        try:
            if hasattr(self, 'job1') and self.job1 is not None:
                self.job1.stop()
        except Exception as e:
            print(f"Error stopping job1: {e}")

        # Stop the oscilloscope job if it's running
        try:
            if hasattr(self, 'job2') and self.job2 is not None:
                self.job2.stop()
        except Exception as e:
            print(f"Error stopping job2: {e}")

        # Stop the timer thread if it's running
        try:
            if hasattr(self, 'time_counter') and self.time_counter is not None:
                self.time_counter.stop()
        except Exception as e:
            print(f"Error stopping time_counter: {e}")

        # Quit and delete the threads
        for thread_name in ['thread1', 'thread2', 'time_thread']:
            try:
                thread = getattr(self, thread_name, None)
                if thread is not None and thread.isRunning():
                    thread.requestInterruption()
                    thread.quit()
                    if not thread.wait(3000):  # Attendre jusqu'à 3 secondes
                        print(f"Warning: Thread {thread_name} did not stop gracefully.")
                        thread.terminate()
            except RuntimeError as e:
                print(f"Error stopping {thread_name}: {e}")

        # Enable the Start button and disable the Stop button
        self.pushButton_Start.setEnabled(True)
        self.pushButton_Stop.setEnabled(False)



    def closeEvent(self, event):
        """Handles the window close event. Closes all devices and threads safely."""
        print("Closing application. Stopping all threads and devices...")

        # Set a flag to indicate that the application is closing
        self.closing = True

        # Stop all threads and devices (already handled by Stop())
        self.Stop()

        # Close all devices
        try:
            if hasattr(self.gen, 'inst') and self.gen.inst is not None:
                self.gen.inst.close()
        except Exception as e:
            print(f"Error closing generator: {e}")

        try:
            if hasattr(self, 'watt') and self.watt is not None:
                self.watt.close()
        except Exception as e:
            print(f"Error closing wattmeter: {e}")

        try:
            if hasattr(self, 'motion') and self.motion is not None:
                self.motion.close()
        except Exception as e:
            print(f"Error closing motion controller: {e}")

        try:
            if self.devices.osc['model'] == 'usb keysight':
                if (self.osc != None):
                    self.osc.inst.close()
            elif self.devices.osc['model'] == 'USB picoscope 5000a series':
                if hasattr(self, 'osc') and self.osc is not None:
                    self.osc.close()
        except Exception as e:
            print(f"Error closing oscilloscope: {e}")

        event.accept()


    def check_port(self):
        """Checks if all device ports are open.

        Opens any closed ports for the wattmeter and motion controller.

        Returns:
            bool: True if all ports are open, False otherwise.
        """
        check = True
        if (self.watt != None) and (self.motion != None):
            if not self.watt.is_open:
                self.watt.open()
            if not self.motion.is_open:
                self.motion.open()
        else:
            check = False
        return check

        

    def readConfiguration(self):
        """Reads and applies the configuration from 'configuration.cfg'.

        If the configuration file is not found, default values are used.
        Updates the UI with the loaded or default values.
        """
        name = 'configuration.cfg'
        try:
            configFile = open(name,'r')
            lines = configFile.readlines()

            element  = lines[0].split(',')
            print(element)
            self.sample.directory = element[1].strip()

            element  = lines[1].split(',')
            self.ultrasound.frequency = float(element[1].strip())

            element  = lines[2].split(',')
            self.ultrasound.PRF = float(element[1].strip())

            element  = lines[3].split(',')
            self.ultrasound.function = element[1].strip()

            element  = lines[4].split(',')
            self.ultrasound.n_cycle = int(float(element[1].strip()))

            element  = lines[5].split(',')
            self.ultrasound.amplitude = float(element[1].strip())

            element  = lines[6].split(',')
            self.ultrasound.duration = float(element[1].strip())

            self.ultrasound.DC = (self.ultrasound.n_cycle*self.ultrasound.PRF)/self.ultrasound.frequency
            self.pulse_number = self.ultrasound.duration*self.ultrasound.PRF

            element  = lines[7].split(',')
            self.sample.Operator = element[1].strip()

            element  = lines[8].split(',')
            self.sample.Info = element[1].strip()

            element  = lines[9].split(',')
            self.sample.temperature = float(element[1].strip())

            element  = lines[10].split(',')
            self.sample.Volume_fraction = float(element[1].strip())

            element  = lines[11].split(',')
            self.sample.Diameter = float(element[1].strip())

            element  = lines[12].split(',')
            self.sample.C_Drug = float(element[1].strip())

            element  = lines[13].split(',')
            self.sample.Cells = element[1].strip()

            element  = lines[14].split(',')
            self.ultrasound.fmth = element[1].strip()

        except FileNotFoundError:
            print('No configuration file was found.')

        self.lineEdit_frequency.setText(str(round(self.ultrasound.frequency*1e-6,2)))
        self.lineEdit_PRF.setText(str(self.ultrasound.PRF))
        self.comboBox_function_function.setCurrentText(self.ultrasound.function)
        self.spinBox_n_cycle.setValue(self.ultrasound.n_cycle)
        self.lineEdit_amplitude.setText(str(self.ultrasound.amplitude))
        self.lineEdit_duration.setText(str(self.ultrasound.duration))
        self.lineEdit_DC.setText(str(round(self.ultrasound.DC*100,2)))
        self.lineEdit_pulse_number.setText(str(self.ultrasound.pulse_number))

        return 1


    def setGenParameters(self):
        """Reads ultrasound parameters and configures the waveform generator.

        Sets the generator's function, frequency, amplitude, and burst mode based on the ultrasound parameters.
        """
        if self.ultrasound.function != 'USER':
            self.gen.write('FUNC '+str(self.ultrasound.function))
            time.sleep(0.1)
            response = self.gen.inst.query("*OPC?")
            print('FUNC',response)
        elif self.ultrasound.function == 'USER':
            self.userFunction()
            time.sleep(0.1)
            response = self.gen.inst.query("*OPC?")
            print('FUNC',response)

        self.gen.write('FREQ '+str(self.ultrasound.frequency)+' HZ')
        time.sleep(0.1)
        response = self.gen.inst.query("*OPC?")
        print('FREQ',response)

        self.gen.write('VOLT '+str(self.ultrasound.amplitude)+' VPP')
        time.sleep(0.1)
        response = self.gen.inst.query("*OPC?")
        print('VOLT',response)

        if self.ultrasound.DC == 100:
            # the burst mode is set to OFF
            self.gen.write('BURS:STAT OFF')
            response = self.gen.inst.query("*OPC?")
            print('BURS:STAT OFF',response)

        elif self.ultrasound.DC < 100 and self.ultrasound.DC > 0:
            # The burst mode is set to ON
            self.gen.write('BURS:STAT ON')
            response = self.gen.inst.query("*OPC?")
            print('BURS:STAT ON',response)

            # The number of cyle is given
            self.gen.write('BURS:NCYC '+str(self.ultrasound.n_cycle))
            response = self.gen.inst.query("*OPC?")
            print('BURS:NCYC',response)

            # The pulse repetition period is given+
            self.gen.write('BURS:INT:PER '+str(1/self.ultrasound.PRF))
            response = self.gen.inst.query("*OPC?")
            print('BURS:INT:PER',response)

            self.gen.write('OUTP:SYNC ON')
            self.gen.write('OUTP:SYNC:MODE MARK')
        else:
            print('DC value is not correct, either >100 or =0')
        return 1


    def rescan(self):
        """Rescans and reinitializes all connected devices.

        Closes all open devices and reinitializes them.
        """
        if hasattr(self, 'gen') and self.gen is not None:
            if hasattr(self.gen, 'inst') and self.gen.inst is not None:
                try:
                    self.gen.inst.write("*RST")  # Réinitialise le générateur
                    self.gen.inst.close()
                except Exception as e:
                    print(f"Erreur lors de la fermeture du générateur : {e}")

        if hasattr(self, 'watt') and self.watt is not None:
                self.watt.close()

        if hasattr(self, 'motion') and self.motion is not None:
                self.motion.close()

        if hasattr(self, 'amp') and self.amp is not None:
                self.amp.close()

        if hasattr(self, 'osc') and self.osc is not None:
            if self.devices.osc['model'] == 'USB keysight':
                self.osc.inst.close()
            elif self.devices.osc['model'] == 'USB picoscope 5000a series':
                self.osc.close()

        self.osc = None
        self.watt = None
        self.motion = None
        self.gen = None
        self.amp = None
        # A changer !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if self.devices.osc['enabled'] == True:
            self.osc = picoscope.Oscilloscope()
            self.osc.identifier = self.devices.osc['identifier'].encode("utf-8")
            self.osc.model = self.devices.osc['model']
        self.gen, self.watt, self.motion = instruments.initialize(self.devices,self.gen,self.watt,self.motion)
        self.set_status()


    def set_status(self):
        """Verifies that all instruments are connected and updates their status icons.

        Updates the UI icons based on the connection status of each device.
        """
        if (self.gen != None):
            print(f'generator usb : {self.gen.inst.query("*IDN?")}')
            self.label_gen.setPixmap(self.icon_gen_color)
        else:
            print('Generator not connected')
            self.label_gen.setPixmap(self.icon_gen_grey)

        if (self.watt != None):
            print(f'wattmeter {self.watt.port} : {self.watt.info}')
            self.label_watt.setPixmap(self.icon_watt_color)
        else:
            print('Wattmeter not connected')
            self.label_watt.setPixmap(self.icon_watt_grey)

        if (self.motion != None):
            print(f'motion {self.motion.port} : {self.motion.info}')
            self.label_motion.setPixmap(self.icon_motion_color)
            self.toolButton_motion.setEnabled(True)
        else:
            print('Motion controller not connected')
            self.label_motion.setPixmap(self.icon_motion_grey)
            self.toolButton_motion.setEnabled(False)

        if self.devices.osc['enabled']:
            if self.devices.osc['model'] == 'USB keysight':
                if (self.osc != None):
                    print(f'generator usb : {self.osc.inst.query("*IDN?")}')
                    self.label_pico.setPixmap(self.icon_pico_color)
                    self.osc.initialize()
                else:
                    print('Oscilloscope not connected')
                    self.label_pico.setPixmap(self.icon_pico_grey)
            if self.devices.osc['model'] == 'USB picoscope 5000a series':
                if self.osc.check_status():
                    self.label_pico.setPixmap(self.icon_pico_color)
                    self.osc.initialize()
                else:
                    print('Oscilloscope not connected')
                    self.label_pico.setPixmap(self.icon_pico_grey)


    def showWarningMessage(self, message):
        """Displays a warning message to the user.

        Args:
            message (str): The warning message to display.
        """
        infoBox = QtWidgets.QMessageBox()
        infoBox.setText(message)
        infoBox.exec()

    def showErrorMessage(self, message):
        """Displays an error message to the user.

        Args:
            message (str): The error message to display.
        """
        infoBox = QtWidgets.QMessageBox()
        infoBox.setText(message)
        infoBox.exec()

    def showPicoError(self, message):
        """Displays an error message related to the oscilloscope.

        Args:
            message (str): The oscilloscope error message to display.
        """
        infoBox = QtWidgets.QMessageBox()
        infoBox.setText(f"Oscilloscope Error: {message}")
        infoBox.exec()
        
    def on_data_submitted(self,data):
        """Callback for when sample data is submitted.

        Args:
            data (dict): Dictionary containing sample information.
        """
        #self.sample.temperature = data["Temperature"]
        #self.sample.Volume_fraction = data["Volume_fraction"]
        #self.sample.Drug_concentration = data["Drug_concentration"]
        #self.sample.Preparation_date = data["Preparation_date"]
        #self.sample.Diameter = data["Diameter"]
        #self.sample.Operator = data["Operator"]
        #self.sample.Info = data["Sample_information"]
        #self.sample.Cells = data["Cells"]
        print('running as expected')

    def Start(self):
        """Starts the measurement process.

        Updates values, checks device status, and starts the measurement threads.
        """
        self.updateValues()
        self.lcdNumber.display(0)
        period = 1/self.ultrasound.PRF
        infoBox = QtWidgets.QMessageBox() # provides message when a device is not responding

        if self.radioButton_pulse_number.isChecked():
            if self.osc != None: #if self.osc.check_status():
                pass
            else:
                infoBox.setText('Warning : Oscilloscope is off !')
                rec = infoBox.exec()

        sample_dialog = sample_information.SampleInformationDialog(self.sample, parent=self)
        sample_dialog.data_submitted.connect(self.on_data_submitted)
        if not sample_dialog.exec():
            return  # Abort if dialog is rejected

        if self.ultrasound.duration < period:
            self.showWarning.emit(f"The insonification should last longer than {round(period, 2)} s")
            return

        if self.gen != None:
            self.setGenParameters()
            self.saveConfiguration()
            (GO,message) = measurement.checkParameters(self.ultrasound.amplitude,self.ultrasound.DC,self.transducer.choice)
            if GO == True:
                self.sample.filename = self.Choose_filename()
                self.pushButton_Start.setEnabled(False)
                self.pushButton_Stop.setEnabled(True)
                self.gen.output('on') # The generator can sent a signal, take 35 ms

                time.sleep(0.1)
                self.time_thread = QtCore.QThread()
                self.time_counter = TimeCounter(self.ultrasound.duration)
                print(self.ultrasound.duration)
                self.time_counter.moveToThread(self.time_thread)
                self.time_thread.started.connect(self.time_counter.run)
                self.time_counter.update_time.connect(self.lcdNumber.display)
                self.time_counter.completed.connect(self.on_timer_completed)
                self.time_counter.completed.connect(self.time_counter.deleteLater)
                self.time_thread.finished.connect(self.time_thread.deleteLater)
                self.time_thread.start()
                print("start timer")

                if self.watt != None:
                    self.thread1 = QtCore.QThread()
                    self.job1 = powerMeasurement(self.watt,self.gen,self.transducer,self.ultrasound,self.sample,self.data)
                    self.job1.moveToThread(self.thread1)
                    self.thread1.started.connect(self.job1.run)
                    self.job1.display_pressure.connect(self.updatePressure)
                    self.job1.display_power.connect(self.updatePower)
                    self.job1.completed.connect(self.thread1.quit)
                    self.job1.showWarning.connect(self.showWarningMessage)
                    self.job1.error.connect(self.showErrorMessage)
                    self.job1.completed.connect(self.thread1.quit)
                    self.job1.completed.connect(self.job1.deleteLater)
                    self.thread1.finished.connect(self.thread1.deleteLater)
                    self.thread1.start()

                if self.osc != None and self.radioButton_pulse_number.isChecked():
                    self.osc.num_captures = int(self.ultrasound.pulse_number)
                    self.osc.total_time_seconds = float(self.ultrasound.n_cycle/self.ultrasound.frequency) * 4
                    ###########################################################
                    self.osc.total_time_seconds = 200*1e-6
                    ###########################################################
                    self.osc.channel = self.devices.osc['Schan']
                    # self.trigger_channel = self.devices.osc['Tchan']
                    ##change this ligne to 3 new lignes
                    self.osc.trigger_channel = self.devices.osc['Tchan']
                    print("Osc channel:", self.osc.channel)
                    print("Osc trigger channel:", self.osc.trigger_channel)

                    print(f'total time {self.osc.total_time_seconds}')
                    self.thread2 = QtCore.QThread()
                    self.job2 = OscWorker(self.osc,self.sample)
                    self.job2.moveToThread(self.thread2)
                    self.thread2.started.connect(self.job2.run)
                    self.job2.completed.connect(self.thread2.quit)
                    self.job2.completed.connect(self.job2.deleteLater)
                    self.thread2.finished.connect(self.thread2.deleteLater)
                    self.job2.error.connect(self.showPicoError)

                    self.thread2.finished.connect(lambda: setattr(self, "thread2", None))
                    self.job2.completed.connect(lambda: setattr(self, "job2", None))

                    self.thread2.start()
            else:
                return None

        else:
            infoBox.setText('Cannot proceed as no generator is present')
            rec = infoBox.exec()

    def on_timer_completed(self):
        """Called when the timer completes. Stops the generator and threads."""
        print("Timer completed. Stopping generator and threads...")

        if hasattr(self.sample, 'filename') and self.sample.filename:
            success = inout.export_csv(self.sample,self.transducer,self.ultrasound,self.data)
            if not success:
                self.showErrorMessage("Error saving CSV file.")
        else:
            self.showErrorMessage("No file selected for saving.")

        # Turn off the generator
        if hasattr(self, 'gen') and self.gen is not None:
            self.gen.output('off')
            print("Generator turned off.")

        # Stop the power measurement thread if it's running
        if hasattr(self, 'job1') and self.job1 is not None:
            self.job1.stop()  # Arrête la boucle dans powerMeasurement

        # Stop the oscilloscope thread if it's running
        if hasattr(self, 'job2') and self.job2 is not None:
            self.job2.stop()  # Arrête la boucle dans OscWorker si nécessaire

        # Quit and delete the threads
        for thread_name in ['thread1', 'thread2', 'time_thread']:
            try:
                thread = getattr(self, thread_name, None)
                if thread is not None:
                    thread.requestInterruption()
                    thread.quit()
                    if not thread.wait(1000):
                        thread.terminate()
                        thread.wait()
            except RuntimeError as e:
                print(f"Error stopping {thread_name}: {e}")

        # Enable the Start button and disable the Stop button
        self.pushButton_Start.setEnabled(True)
        self.pushButton_Stop.setEnabled(False)

        infoBox = QtWidgets.QMessageBox()
        infoBox.setText('Measurements finished')
        rec = infoBox.exec()


    def saveConfiguration(self):
        """Writes all current parameters to a configuration file.

        The configuration file is saved as 'configuration.cfg' in the current directory.
        It includes ultrasound parameters, sample information, and operator details.

        Raises:
            Exception: If an error occurs while writing the configuration file.
        """
        try:
            with open('configuration.cfg','w+') as configFile:
                configFile.write('directory,' + self.sample.directory + '\n')
                configFile.write('frequency (Hz),' + str(self.ultrasound.frequency) + '\n')
                configFile.write('PRF (Hz),' + str(self.ultrasound.PRF) + '\n')
                configFile.write('function,' + self.ultrasound.function + '\n')
                configFile.write('number of cycles,' + str(self.ultrasound.n_cycle) + '\n')
                configFile.write('amplitude Vpp (V),' + str(self.ultrasound.amplitude) + '\n')
                configFile.write('duration (s),' + str(self.ultrasound.duration) + '\n')
                configFile.write('Operator,' + self.sample.Operator + '\n')
                configFile.write('Sample information,' + self.sample.Info + '\n')
                configFile.write('Temperature (K),' + str(self.sample.temperature) + '\n')
                configFile.write('Volume fraction,' + str(self.sample.Volume_fraction) + '\n')
                configFile.write('Diameter (nm),' + str(self.sample.Diameter) + '\n')
                configFile.write('Drug concentration (mM),' + str(self.sample.C_Drug) + '\n')
                configFile.write('Cells,' + self.sample.Cells + '\n')
                configFile.write('fmth,' + self.ultrasound.fmth + '\n')
                configFile.close()
        except Exception as e:
            self.error.emit(f"Error saving configuration: {e}")


    def updatePressure(self,pressure):
        """Updates the pressure display.

        Args:
            pressure (float): The pressure value to display.
        """
        self.label_pressure.setText(str(round(pressure,2)))

    def updatePower(self,power):
        """Updates the power display.

        Args:
            power (float): The power value to display.
        """
        self.label_power.setText(str(round(power,3)))

    def updateElapseTime(self,time):
        """Updates the elapsed time display.

        Args:
            time (int): The elapsed time in seconds.
        """
        self.lcdNumber.display(time)
        
        
    def updateValues(self):
        """Updates the ultrasound and sample parameters based on UI inputs.

        Validates and updates frequency, PRF, amplitude, and other parameters.
        Handles errors for invalid inputs.
        """

        infoBox = QtWidgets.QMessageBox()


        if self.radioButton_fondamental.isChecked():
            self.ultrasound.fmth = 'FM'
        if self.radioButton_thirdHarmonic.isChecked():
            self.ultrasound.fmth = 'TH'

        if self.comboBox_transducer.currentIndex() == 0:
            self.transducer = transducer.H101SN140(self.ultrasound.fmth)
        elif self.comboBox_transducer.currentIndex() == 1:
            self.transducer = transducer.H101SN124(self.ultrasound.fmth)

        try:
            self.ultrasound.frequency = float(self.lineEdit_frequency.text())*1e6
        except ValueError:
            infoBox1 = QtWidgets.QMessageBox()
            infoBox1.setText('It is not a number')
            rec = infoBox1.exec()

        try:
            self.ultrasound.PRF = float(self.lineEdit_PRF.text())
        except ValueError:
            infoBox2 = QtWidgets.QMessageBox()
            infoBox2.setText('It is not a number')
            rec = infoBox2.exec()

        self.ultrasound.function = self.comboBox_function_function.currentText()
        self.ultrasound.n_cycle = float(self.spinBox_n_cycle.value())
        self.ultrasound.DC = (self.ultrasound.n_cycle*self.ultrasound.PRF)/self.ultrasound.frequency
        self.lineEdit_DC.setText(str(round(self.ultrasound.DC*100,2)))

        try:
            self.ultrasound.amplitude = float(self.lineEdit_amplitude.text())
        except ValueError:
            infoBox4 = QtWidgets.QMessageBox()
            infoBox4.setText('It is not a number')
            rec = infoBox4.exec()

        if self.radioButton_pulse_number.isChecked():
            self.lineEdit_pulse_number.setEnabled(1)
            self.lineEdit_duration.setEnabled(0)
            try:
                self.ultrasound.pulse_number = float(self.lineEdit_pulse_number.text())
                self.ultrasound.duration = self.ultrasound.pulse_number/self.ultrasound.PRF *10##########
                self.lineEdit_duration.setText(str(self.ultrasound.duration))
            except ValueError:
                infoBox9 = QtWidgets.QMessageBox()
                infoBox9.setText('It is not a number')
                rec = infoBox9.exec()


        if self.radioButton_duration.isChecked():
            self.lineEdit_duration.setEnabled(1)
            self.lineEdit_pulse_number.setEnabled(0)
            try:
                self.ultrasound.duration = float(self.lineEdit_duration.text())
                self.ultrasound.pulse_number = self.ultrasound.duration*self.ultrasound.PRF
                self.lineEdit_pulse_number.setText(str(self.ultrasound.pulse_number))
            except ValueError:
                infoBox10 = QtWidgets.QMessageBox()
                infoBox10.setText('It is not a number')
                rec = infoBox10.exec()
        return 1


    def userFunction(self):
        """Defines a custom user function for the waveform generator.

        This method is a placeholder for defining a custom waveform.
        """
        wave = "1,.67, 0, *.33, -.67, -1" #content.readlines()
        self.gen.write('DATA:DEL VOLATILE')
        self.gen.write('DATA VOLATILE,'+wave)
        self.gen.write('FUNC:USER VOLATILE')
        self.gen.write('FUNC USER')
        return 1
###############################################################################        

if __name__ == "__main__":
    try:
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        app = QtWidgets.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        print("=== RAW EXCEPTION ===")
        traceback.print_exc()
        print("=====================")
