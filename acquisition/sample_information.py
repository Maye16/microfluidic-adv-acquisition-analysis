#!/usr/bin/env python
import sys
import os
import os.path
import time
import ctypes
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QPixmap
import scipy

import sample_information_ui

###############################################################################
class SampleInformationDialog(QtWidgets.QDialog,sample_information_ui.Ui_Dialog):
    """ This window dialog provide the information about the sample, stored in
        the class sample.
        The provided informations are:
        self.sample.operator: the operator, i.e. who is performing the experiments,
        self.sample.temperature: the temperature at which the experiments is performed, in Kelvin
        self.sample.C_Drug: the drug concentration if there is any,
        self.sample.Info: Information about the sample,
        self.sample.Diameter: the diameter of the droplets if there are used
        self.sample.Preparation_date: the date at which the experiments are peformed
        self.sample.Volume_fraction: the volume fraction of droplets
        self.sample.Cells: the type of biological cells that are used
    """

    data_submitted = QtCore.pyqtSignal(dict)

    def __init__(self, sample, parent=None):
        super().__init__(parent)
        self.ui = sample_information_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.sample = sample

        self.ui.dateEdit_Preparation_date.setDateTime(QtCore.QDateTime.currentDateTime())

        self.ui.lineEdit_Operator.setText(self.sample.Operator)
        self.ui.lineEdit_Temperature.setText(str(self.sample.temperature - scipy.constants.zero_Celsius))
        self.ui.lineEdit_Drug_concentration.setText(str(self.sample.C_Drug))
        self.ui.plainTextEdit_Sample_information.setPlainText(self.sample.Info)
        self.ui.lineEdit_diameter.setText(str(self.sample.Diameter))
        self.ui.lineEdit_Volume_fraction.setText(str(self.sample.Volume_fraction))
        self.ui.lineEdit_Cells.setText(self.sample.Cells)

        self.ui.lineEdit_Operator.textChanged.connect(self.updateValues)
        self.ui.plainTextEdit_Sample_information.textChanged.connect(self.updateValues)
        self.ui.dateEdit_Preparation_date.dateChanged.connect(self.updateValues)
        self.ui.lineEdit_Temperature.textChanged.connect(self.updateValues)
        self.ui.lineEdit_Volume_fraction.textChanged.connect(self.updateValues)
        self.ui.lineEdit_diameter.textChanged.connect(self.updateValues)
        self.ui.lineEdit_Drug_concentration.textChanged.connect(self.updateValues)
        self.ui.lineEdit_Cells.textChanged.connect(self.updateValues)
        self.ui.buttonBox.accepted.connect(self.end)


    def updateValues(self):
        infoBox = QtWidgets.QMessageBox()
        try:
            self.sample.temperature = float(self.ui.lineEdit_Temperature.text()) + self.sample.temperature_zero
        except:
            infoBox5 = QtWidgets.QMessageBox()
            infoBox5.setText('error on temperature value')
            rec = infoBox5.exec()
        try:
            self.sample.Volume_fraction = float(self.ui.lineEdit_Volume_fraction.text())
        except:
            infoBox6 = QtWidgets.QMessageBox()
            infoBox6.setText('error on volume fraction value')
            rec = infoBox6.exec()
        try:
            self.sample.Drug_concentration = float(self.ui.lineEdit_Drug_concentration.text())
        except:
            infoBox7 = QtWidgets.QMessageBox()
            infoBox7.setText('error on drug concentration value')
            rec = infoBox7.exec()
            self.sample.Preparation_date = self.ui.dateEdit_Preparation_date.date()
        try:
            self.sample.Diameter = float(self.ui.lineEdit_diameter.text())
        except:
            infoBox8 = QtWidgets.QMessageBox()
            infoBox8.setText('error on diameter value')
            rec = infoBox8.exec()
            self.sample.Operator = self.ui.lineEdit_Operator.text()
            self.sample.Info = self.ui.plainTextEdit_Sample_information.toPlainText()
            self.sample.Cells = self.ui.lineEdit_Cells.text()


    def end(self):
        self.sample.Operator = self.ui.lineEdit_Operator.text()
        self.sample.temperature = float(self.ui.lineEdit_Temperature.text()) + scipy.constants.zero_Celsius
        self.sample.C_Drug = self.ui.lineEdit_Drug_concentration.text()
        self.sample.Info = self.ui.plainTextEdit_Sample_information.toPlainText()
        self.sample.Diameter = self.ui.lineEdit_diameter.text()
        self.sample.Preparation_date = self.ui.dateEdit_Preparation_date.date().toString()
        self.sample.Volume_fraction = self.ui.lineEdit_Volume_fraction.text()
        self.sample.Cells = self.ui.lineEdit_Cells.text()
        self.data_submitted.emit({})
        self.accept()
###############################################################################
