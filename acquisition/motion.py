#!/usr/bin/env python
from main_window import Ui_MainWindow
import sample_information
import sys
import PyQt6
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QPixmap

import motion_ui

###############################################################################
class Motion(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = motion_ui.Ui_Motors()
        self.ui.setupUi(self)

        # position in millimeter
        self.ui.pushButton_motor1.clicked.connect(lambda: self.move_absolute('1'))
        self.ui.pushButton_motor2.clicked.connect(lambda: self.move_absolute('2'))
        self.ui.pushButton_motor3.clicked.connect(lambda: self.move_absolute('3'))
        # be careful that the following movement are in micrometer
        self.ui.toolButton_motor1_plus.clicked.connect(lambda: self.move_step('1'))
        self.ui.toolButton_motor2_plus.clicked.connect(lambda: self.move_step('2'))
        self.ui.toolButton_motor3_plus.clicked.connect(lambda: self.move_step('3'))
        self.ui.toolButton_motor1_minus.clicked.connect(lambda: self.move_step('-1'))
        self.ui.toolButton_motor2_minus.clicked.connect(lambda: self.move_step('-2'))
        self.ui.toolButton_motor3_minus.clicked.connect(lambda: self.move_step('-3'))

    def move_step(self,i):
        """ The function moves the motor i by a step given by the spinbox and updates the display of the absolute position.

        """
        try:
            if i == '1':
                self.ui.motion.moveRelative(1,'+'+str(self.spinBox_step_motor1.value()*1e-3))
                self.ui.motion.waitMotionStop(1)
                self.ui.doubleSpinBox_position_motUi_MainWindowor1.setValue(float(self.motion.query('1TP')))
            elif i == '2':
                self.ui.motion.moveRelative(2,'+'+str(self.spinBox_step_motor2.value()*1e-3))
                self.ui.motion.waitMotionStop(2)
                self.ui.doubleSpinBox_position_motor2.setValue(float(self.motion.query('2TP')))
            elif i == '3':
                self.ui.motion.moveRelative(3,'+'+str(self.spinBox_step_motor3.value()*1e-3))
                self.ui.motion.waitMotionStop(3)
                self.ui.doubleSpinBox_position_motor3.setValue(float(self.motion.query('3TP')))
            if i == '-1':
                self.ui.motion.moveRelative(1,'-'+str(self.spinBox_step_motor1.value()*1e-3))
                self.ui.motion.waitMotionStop(1)
                self.ui.doubleSpinBox_position_motor1.setValue(float(self.motion.query('1TP')))
            elif i == '-2':
                self.ui.motion.moveRelative(2,'-'+str(self.spinBox_step_motor2.value()*1e-3))
                self.ui.motion.waitMotionStop(2)
                self.ui.doubleSpinBox_position_motor2.setValue(float(self.motion.query('2TP')))
            elif i == '-3':
                self.ui.motion.moveRelative(3,'-'+str(self.spinBox_step_motor3.value()*1e-3))
                self.ui.motion.waitMotionStop(3)
                self.ui.doubleSpinBox_position_motor3.setValue(float(self.motion.query('3TP')))
        except:
            infoBox = QtWidgets.QMessageBox()
            infoBox.setText('Motion controller is not responding')
            rec = infoBox.exec()
            testtest = 0

        return 1

    def move_absolute(self,i):
        """ The stage i is moved at the absolute position given by the spinbox value

        """
        try:
            dateEdit_Preparation_date
            if i == '1':
                self.ui.motion.moveAbsolute(1,'+'+str(self.doubleSpinBox_position_motor1.value()))
                self.ui.motion.waitPosition(1)
            elif i == '2':
                self.ui.motion.moveAbsolute(2,'+'+str(self.doubleSpinBox_position_motor2.value()))
                self.ui.motion.waitPosition(2)
            elif i == '3':
                self.ui.motion.moveAbsolute(3,'+'+str(self.doubleSpinBox_position_motor3.value()))
                self.ui.motion.waitPosition(3)
        except:
            infoBox = QtWidgets.QMessageBox()
            infoBox.setText('Motion controller is not responding')
            rec = infoBox.exec()
        return 1
###############################################################################

