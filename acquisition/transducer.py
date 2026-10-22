#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scipy.interpolate
import math
import numpy

###############################################################################
class H101SN140():
    r""" The transducer H101 SN140 has been calibrated by Sonic Concept.
    
    """
    def __init__(self,choice):
        r""" We provide the values for the sensibility :math:`e` 
        at the fundamental frequency (FM) or at the third harmonics (TM).
        An interpolation is performed (using B splines) to provide a values at any frequency resolution
        between 0.75 and 1.35 MHz or between 3.25 and 3.55 MHz.
    
        :param choice: the value is either 'FM' or 'TH'
        :type choice: string        
        
        """
        
        f_FM = numpy.array([0.75,0.76,0.77,0.78,0.79,0.80,0.81,0.82,0.83,0.84,0.85,0.86,0.87,0.88,0.89,0.90,0.91,0.92,0.93,0.94,0.95,0.96,0.97,0.98,0.99,1.00,1.01,1.02,1.03,1.04,1.05,1.06,1.07,1.08,1.09,1.10,1.11,1.12,1.13,1.14,1.15,1.16,1.17,1.18,1.19,1.20,1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28,1.29,1.30,1.31,1.32,1.33,1.34,1.35])
        e_FM = numpy.array([70.1,73.1,75.5,78.1,80.5,82.3,83.5,84.4,84.9,85.2,85.6,85.6,85.4,85.1,85.0,84.7,84.6,84.4,84.4,84.3,84.3,84.2,84.2,84.2,84.2,84.0,83.8,83.3,83.1,82.8,82.4,82.2,81.9,81.8,81.6,81.6,81.6,81.6,81.8,81.9,82.2,82.4,83.0,83.5,83.8,84.0,83.8,83.7,83.1,82.8,82.3,81.9,81.1,80.6,79.8,78.8,77.8,76.5,75.2,73.9,72.8])
        self.spline_FM = scipy.interpolate.UnivariateSpline(f_FM,e_FM,s=0.01)
 
        f_TH = numpy.array([3.25,3.26,3.27,3.28,3.29,3.30,3.31,3.32,3.33,3.34,3.35,3.36,3.37,3.38,3.39,3.40,3.41,3.42,3.43,3.44,3.45,3.46,3.47,3.48,3.49,3.50,3.51,3.52,3.53,3.54,3.55])
        e_TH = numpy.array([42.28,43.29,44.44,45.61,46.60,48.48,50.21,52.52,54.83,57.29,59.59,62.06,64.72,67.01,68.97,69.26,67.96,65.22,62.19,59.16,57.72,57.35,58.01,59.01,59.74,59.30,57.86,55.55,52.91,50.50,47.91])
        self.spline_TH = scipy.interpolate.UnivariateSpline(f_TH,e_TH,s=0.01)
        self.choice = choice
 
    def efficiency(self,frequency):
        r"""
        
        :param frequency: the frequency in Hz
        :type frequency: float
        
        :return: transducer sensibility
        :rtype: float
        
        """
        
        if self.choice == 'FM':
            value = self.spline_FM(frequency*1e-6)*0.01
        elif self.choice == 'TH':
            value = self.spline_TH(frequency*1e-6)*0.01
        return value

    def section(self):
        r"""
        
        :return: transducer section in :math:`\textrm{cm}^2`  at the focus
        :rtype: float
        
        """

        if self.choice == 'FM':
            value = math.pi*(0.19*0.5)**2
        elif self.choice == 'TH':
            value = math.pi*(0.062*0.5)**2
        return value
###############################################################################


###############################################################################
class H101SN124():
    r""" The transducer H101 SN124 has not been calibrated by Sonic Concept. We used typical values given for this transducer serie
    
    """
    def __init__(self,choice):
        r""" We provide the values for the sensibility :math:`e` 
        at the fundamental frequency (FM) or at the third harmonics (TM).
        An interpolation is performed (using B splines) to provide a values at any frequency resolution
        between 0.75 and 1.35 MHz or between 3.25 and 3.55 MHz.
    
        :param choice: the value is either 'FM' or 'TH'
        :type choice: string        
        
        """
        f_FM =numpy.array([0.70,0.71,0.72,0.73,0.74,0.75,0.76,0.77,0.78,0.79,0.80,0.81,0.82,0.83,0.84,0.85,0.86,0.87,0.88,0.89,0.90,0.91,0.92,0.93,0.94,0.95,0.96,0.97,0.98,0.99,1.00,1.01,1.02,1.03,1.04,1.05,1.06,1.07,1.08,1.09,1.10,1.11,1.12,1.13,1.14,1.15,1.16,1.17,1.18,1.19,1.20,1.21,1.22,1.23,1.24,1.25,1.26,1.27,1.28,1.29,1.30,1.31,1.32,1.33,1.34,1.35,1.36,1.37,1.38,1.39,1.4,1.41,1.42,1.43,1.44,1.45,1.46,1.47,1.48,1.49,1.5])
        e_FM = numpy.array([7.5,12.2,18.9,25.5,32.3,38.4,45.5,52.5,61.2,66.8,71.8,74.2,74.7,74.3,74.4,74.3,74.7,75.1,75.6,76.1,76.2,76.1,75.6,75.1,74.4,74.0,73.5,72.8,72.4,71.8,71.7,72.0,72.7,73.3,73.5,74.5,75.1,75.2,75.9,76.3,77.2,77.2,77.3,77.9,78.1,78.4,78.8,79.2,79.3,79.4,79.8,80,81.4,82.5,83.7,84.5,86.0,87.1,88.5,89.7,89.8,89.9,88.4,87.1,85.3,84.0,83.1,81.9,80.7,79,77.9,75.8,73.5,71.3,69.1,66.9,64.3,62.4,59.4,57.9,55.5])
        self.spline_FM = scipy.interpolate.UnivariateSpline(f_FM,e_FM,s=0.01)
 
        f_TH = numpy.array([2.90,2.91,2.92,2.93,2.94,2.95,2.96,2.97,2.98,2.99,3.00,3.01,3.02,3.03,3.04,3.05,3.06,3.07,3.08,3.09,3.10,3.11,3.12,3.13,3.14,3.15,3.16,3.17,3.18,3.19,3.20,3.21,3.22,3.23,3.24,3.25,3.26,3.27,3.28,3.29,3.30,3.31,3.32,3.33,3.34,3.35,3.36,3.37,3.38,3.39,3.40,3.41,3.42,3.43,3.44,3.45,3.46,3.47,3.48,3.49,3.50,3.51,3.52,3.53,3.54,3.55,3.56,3.57,3.58,3.59,3.60,3.61,3.62,3.63,3.64,3.65,3.66,3.67,3.68,3.69,3.70])
        e_TH = numpy.array([12.8,14.1,15.6,17.5,19.3,20.9,22.7,24.8,27,29.1,30.4,30.7,30.0,29.0,27.8,26.7,25.4,24.0,22.4,21.2,21.5,23.5,26.6,31.0,35.9,42.4,48.9,58.4,69.0,81.4,87.4,90.8,91.8,92.1,92.2,91.9,91.6,90.9,90.0,88.9,88.0,87.7,87.7,87.8,87.4,84.8,81.5,75.3,68.7,63.3,58.3,53.2,49.8,46.3,43.1,40.3,36.7,33.3,29.0,25.4,22.9,20.6,18.8,17.5,16.2,15.0,13.6,11.8,10.2,8.5,7.4,6.9,6.9,7.0,7.1,7.3,7.5,7.6,7.7,7.7,7.7])
        self.spline_TH = scipy.interpolate.UnivariateSpline(f_TH,e_TH,s=0.01)
        self.choice = choice
 
    def efficiency(self,frequency):
        r"""
        
        :param frequency: the frequency in Hz
        :type frequency: float
        
        :return: transducer sensibility
        :rtype: float
        
        """

        if self.choice == 'FM':
            value = self.spline_FM(frequency*1e-6)*0.01
        elif self.choice == 'TH':
            value = self.spline_TH(frequency*1e-6)*0.01
        return value

    def section(self):
        r"""
        
        :return: transducer section in :math:`\textrm{cm}^2`  at the focus
        :rtype: float
        
        """

        if self.choice == 'FM':
            value = math.pi*(0.15*0.5)**2
        elif self.choice == 'TH':
            value = math.pi*(0.05*0.5)**2
        return value
###############################################################################
