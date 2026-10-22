#!/usr/bin/env python
import sys
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QPixmap
import json

import available_devices_ui


###############################################################################
def get_values(devices):
    filename =  "devices.cfg"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Generator
        devices.gen['enabled'] = config["generator"]["enabled"]
        if devices.gen['enabled']:
            devices.gen['identifier'] = config["generator"]["identifier"]
            devices.gen['model'] = config["generator"]["model"]

        # Amplifier
        devices.amp['enable'] = config["amplifier"]["enabled"]
        if devices.amp['enable']:
            devices.amp['identifier']  = config["amplifier"]["identifier"]
            devices.amp['model'] = config["amplifier"]["model"]

        # Oscilloscope
        devices.osc['enabled'] = config["oscilloscope"]["enabled"]
        if devices.osc['enabled']:
            devices.osc['identifier']  = config["oscilloscope"]["identifier"]
            devices.osc['model'] = config["oscilloscope"]["model"]
            devices.osc['Schan'] = config["oscilloscope"]["signal channel"]
            devices.osc['Tchan'] = config["oscilloscope"]["trigger channel"]

        # Wattmeter
        devices.watt['enabled'] = config["wattmeter"]["enabled"]
        if devices.watt['enabled']:
            devices.watt['identifier']  = config["wattmeter"]["identifier"]
            devices.watt['model'] = config["wattmeter"]["model"]

        # Motion controller
        devices.motion['enabled'] = config["motion controller"]["enabled"]
        if devices.motion['enabled']:
            devices.motion['identifier']  = config["motion controller"]["identifier"]
            devices.motion['model'] = config["motion controller"]["model"]

    except FileNotFoundError:
        return False

    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON : {e}")
        print(f"Position : ligne {e.lineno}, colonne {e.colno}")

    except Exception as e:
        print(f"Autre erreur : {e}")
###############################################################################


###############################################################################
class availableDevices(QtWidgets.QDialog):

    def __init__(self, devices, parent=None):
        super().__init__(parent)
        self.ui = available_devices_ui.Ui_devices()
        self.ui.setupUi(self)

        self._filename =  "devices.cfg"
        self.devices = devices

        self.ui.checkBox_generator.stateChanged.connect(self.enable_gen)
        self.ui.checkBox_amplifier.stateChanged.connect(self.enable_amp)
        self.ui.checkBox_oscilloscope.stateChanged.connect(self.enable_osc)
        self.ui.checkBox_wattmeter.stateChanged.connect(self.enable_watt)
        self.ui.checkBox_motion.stateChanged.connect(self.enable_motion)

        self.ui.comboBox_generator.addItem("RS232 Agilent")
        self.ui.comboBox_generator.addItem("USB Agilent")
        self.ui.comboBox_generator.addItem("USB keysight")
        self.ui.comboBox_amplifier.addItem("RS232 RS")
        self.ui.comboBox_oscilloscope.addItem("USB picoscope 5000a series")
        self.ui.comboBox_oscilloscope.addItem("USB keysight")
        self.ui.comboBox_wattmeter.addItem("RS232 Rohde & Schwarz")
        self.ui.comboBox_motion.addItem("RS232 Newport")
        self.ui.comboBox_trigger_channel.addItem("A")
        self.ui.comboBox_trigger_channel.addItem("B")
        self.ui.comboBox_trigger_channel.addItem("C")
        self.ui.comboBox_trigger_channel.addItem("D")
        self.ui.comboBox_signal_channel.addItem("A")
        self.ui.comboBox_signal_channel.addItem("B")
        self.ui.comboBox_signal_channel.addItem("C")
        self.ui.comboBox_signal_channel.addItem("D")
        self.ui.comboBox_signal_channel.addItem("EXT")

        self.ui.comboBox_generator.currentIndexChanged.connect(self.update_gen)
        self.ui.comboBox_amplifier.currentIndexChanged.connect(self.update_amp)
        self.ui.comboBox_oscilloscope.currentIndexChanged.connect(self.update_osc)
        self.ui.comboBox_wattmeter.currentIndexChanged.connect(self.update_watt)
        self.ui.comboBox_motion.currentIndexChanged.connect(self.update_motion)

        self.ui.lineEdit_generator.textChanged.connect(self.update_gen)
        self.ui.lineEdit_amplifier.textChanged.connect(self.update_amp)
        self.ui.lineEdit_oscilloscope.textChanged.connect(self.update_osc)
        self.ui.lineEdit_wattmeter.textChanged.connect(self.update_watt)
        self.ui.lineEdit_motion.textChanged.connect(self.update_motion)

        # check if there is device.cfg
        self.getValues()


    def getValues(self):

        try:
            with open(self._filename, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Generator
            if config["generator"]["enabled"]:
                self.ui.checkBox_generator.setChecked(True)
                self.ui.comboBox_generator.setEnabled(True)
                self.ui.lineEdit_generator.setEnabled(True)
                self.devices.gen['identifier'] = config["generator"]["identifier"]
                self.ui.lineEdit_generator.setText(config["generator"]["identifier"])
                self.devices.gen['model'] = config["generator"]["model"]
                self.ui.comboBox_generator.setCurrentText(config["generator"]["model"])

            # Amplifier
            if config["amplifier"]["enabled"]:
                self.ui.checkBox_amplifier.setChecked(True)
                self.ui.comboBox_amplifier.setEnabled(True)
                self.ui.lineEdit_amplifier.setEnabled(True)
                self.devices.amp['identifier'] = config["amplifier"]["identifier"]
                self.ui.lineEdit_amplifier.setText(config["amplifier"]["identifier"])
                self.devices.amp['model'] = config["amplifier"]["model"]
                self.ui.comboBox_amplifier.setCurrentText(config["amplifier"]["model"])

            # Oscilloscope
            if config["oscilloscope"]["enabled"]:
                self.ui.checkBox_oscilloscope.setChecked(True)
                self.ui.comboBox_oscilloscope.setEnabled(True)
                self.ui.lineEdit_oscilloscope.setEnabled(True)
                self.devices.osc['identifier'] = config["oscilloscope"]["identifier"]
                self.ui.lineEdit_oscilloscope.setText(config["oscilloscope"]["identifier"])
                self.devices.osc['model'] = config["oscilloscope"]["model"]
                self.ui.comboBox_oscilloscope.setCurrentText(config["oscilloscope"]["model"])

            # Wattmeter
            if config["wattmeter"]["enabled"]:
                self.ui.checkBox_wattmeter.setChecked(True)
                self.ui.comboBox_wattmeter.setEnabled(True)
                self.ui.lineEdit_wattmeter.setEnabled(True)
                self.devices.watt['identifier'] = config["wattmeter"]["identifier"]
                self.ui.lineEdit_wattmeter.setText(config["wattmeter"]["identifier"])
                self.devices.watt['model'] = config["wattmeter"]["model"]
                self.ui.comboBox_wattmeter.setCurrentText(config["wattmeter"]["model"])

            # Motion controller
            if config["motion controller"]["enabled"]:
                self.ui.checkBox_motion.setChecked(True)
                self.ui.comboBox_motion.setEnabled(True)
                self.ui.lineEdit_motion.setEnabled(True)
                self.devices.motion['identifier'] = config["motion controller"]["identifier"]
                self.ui.lineEdit_motion.setText(config["motion controller"]["identifier"])
                self.devices.motion['model'] = config["motion controller"]["model"]
                self.ui.comboBox_motion.setCurrentText(config["motion controller"]["model"])

        except FileNotFoundError:
            print("Fichier non trouvé, initialisation par défaut.")
            pass

        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON : {e}")
            print(f"Position : ligne {e.lineno}, colonne {e.colno}")

        except Exception as e:
            print(f"Autre erreur : {e}")

    def update_gen(self):
        self.devices.gen['identifier'] = self.ui.lineEdit_generator.text()
        self.devices.gen['model'] =  self.ui.comboBox_generator.currentText()

    def update_amp(self):
        self.devices.amp['identifier'] = self.ui.lineEdit_amplifier.text()
        self.devices.amp['model'] =  self.ui.comboBox_amplifier.currentText()

    def update_osc(self):
        self.devices.osc['identifier'] = self.ui.lineEdit_oscilloscope.text()
        self.devices.osc['model'] =  self.ui.comboBox_oscilloscope.currentText()

    def update_watt(self):
        self.devices.watt['identifier'] = self.ui.lineEdit_wattmeter.text()
        self.devices.watt['model'] =  self.ui.comboBox_wattmeter.currentText()

    def update_motion(self):
        self.devices.motion['identifier'] = self.ui.lineEdit_motion.text()
        self.devices.motion['model'] =  self.ui.comboBox_motion.currentText()

    def enable_gen(self):
        if self.ui.checkBox_generator.checkState() == QtCore.Qt.CheckState.Checked:
            self.ui.comboBox_generator.setEnabled(True)
            self.ui.lineEdit_generator.setEnabled(True)
        else:
            self.ui.comboBox_generator.setEnabled(False)
            self.ui.lineEdit_generator.setEnabled(False)

    def enable_amp(self):
        if self.ui.checkBox_amplifier.checkState() == QtCore.Qt.CheckState.Checked:
            self.ui.comboBox_amplifier.setEnabled(True)
            self.ui.lineEdit_amplifier.setEnabled(True)
        else:
            self.ui.comboBox_amplifier.setEnabled(False)
            self.ui.lineEdit_amplifier.setEnabled(False)

    def enable_osc(self):
        if self.ui.checkBox_oscilloscope.checkState() == QtCore.Qt.CheckState.Checked:
            self.ui.comboBox_oscilloscope.setEnabled(True)
            self.ui.lineEdit_oscilloscope.setEnabled(True)
        else:
            self.ui.comboBox_oscilloscope.setEnabled(False)
            self.ui.lineEdit_oscilloscope.setEnabled(False)

    def enable_watt(self):
        if self.ui.checkBox_wattmeter.checkState() == QtCore.Qt.CheckState.Checked:
            self.ui.comboBox_wattmeter.setEnabled(True)
            self.ui.lineEdit_wattmeter.setEnabled(True)
        else:
            self.ui.comboBox_wattmeter.setEnabled(False)
            self.ui.lineEdit_wattmeter.setEnabled(False)

    def enable_motion(self):
        if self.ui.checkBox_motion.checkState() == QtCore.Qt.CheckState.Checked:
            self.ui.comboBox_motion.setEnabled(True)
            self.ui.lineEdit_motion.setEnabled(True)
        else:
            self.ui.comboBox_motion.setEnabled(False)
            self.ui.lineEdit_motion.setEnabled(False)

    def on_ok(self):
        config = {
            "generator": {
                "enabled": self.ui.checkBox_generator.isChecked(),
                "identifier": self.ui.lineEdit_generator.text() if self.ui.checkBox_generator.isChecked() else None,
                "model": self.ui.comboBox_generator.currentText() if self.ui.checkBox_generator.isChecked() else None
            },
            "amplifier": {
                "enabled": self.ui.checkBox_amplifier.isChecked(),
                "identifier": self.ui.lineEdit_amplifier.text() if self.ui.checkBox_amplifier.isChecked() else None,
                "model": self.ui.comboBox_amplifier.currentText() if self.ui.checkBox_amplifier.isChecked() else None
            },
            "oscilloscope": {
                "enabled": self.ui.checkBox_oscilloscope.isChecked(),
                "identifier": self.ui.lineEdit_oscilloscope.text() if self.ui.checkBox_oscilloscope.isChecked() else None,
                "model": self.ui.comboBox_oscilloscope.currentText() if self.ui.checkBox_oscilloscope.isChecked() else None
            },
            "wattmeter": {
                "enabled": self.ui.checkBox_wattmeter.isChecked(),
                "identifier": self.ui.lineEdit_wattmeter.text() if self.ui.checkBox_wattmeter.isChecked() else None,
                "model": self.ui.comboBox_wattmeter.currentText() if self.ui.checkBox_wattmeter.isChecked() else None
            },
            "motion controller": {
                "enabled": self.ui.checkBox_motion.isChecked(),
                "identifier": self.ui.lineEdit_motion.text() if self.ui.checkBox_motion.isChecked() else None,
                "model": self.ui.comboBox_motion.currentText() if self.ui.checkBox_motion.isChecked() else None
            }
        }
        with open(self._filename, "w") as f:
            json.dump(config, f, indent=4)
        self.accept() # close the diago with accepted status

    def on_cancel(self):
        self.reject()  # close the dialog with rejected status
###############################################################################
